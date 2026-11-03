"""Preservation tests with synthetic, non-personal resource packages."""
import importlib.util
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/update_private_package.py'
spec = importlib.util.spec_from_file_location('private_updater', SCRIPT)
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


def package(root, identity, files):
    root.mkdir(parents=True)
    records = {k:{'sha256': hashlib.sha256(v.encode()).hexdigest(), 'bytes': len(v.encode())} for k,v in files.items()}
    (root/'resources-manifest.json').write_text(json.dumps({'packageId': identity, 'files': records, 'requiredRuntimeFiles':['SKILL.md']}))
    (root/'payload.json').write_text(json.dumps(files))
    (root/'scripts').mkdir()
    (root/'scripts/bootstrap.py').write_text('''import json,sys\nfrom pathlib import Path\np=Path(__file__).resolve().parents[1]\nr=Path(sys.argv[sys.argv.index('--runtime-dir')+1]);r.mkdir()\nfor k,v in json.loads((p/'payload.json').read_text()).items():\n t=r/k;t.parent.mkdir(parents=True,exist_ok=True);t.write_text(v)\n(r/'.toudi-runtime.json').write_text(json.dumps({'packageId':json.loads((p/'resources-manifest.json').read_text())['packageId']}))\n''')
    return root


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root/'state'

    def initial(self, files):
        old = package(self.root/'old', 'old', files)
        result = updater.update(old, self.state, apply=True)
        self.assertTrue(result['freshInstall'])
        return self.state/'resume-data'

    def test_fresh_install_and_dry_run(self):
        incoming = package(self.root/'incoming', 'new', {'SKILL.md':'rules', 'references/history.json':'[]'})
        report = updater.update(incoming, self.state)
        self.assertFalse(report['applied'])
        self.assertFalse((self.state/'resume-data').exists())
        report = updater.update(incoming, self.state, apply=True)
        self.assertTrue(report['applied'])
        self.assertTrue(report['freshInstall'])
        self.assertEqual((self.state/'resume-data/SKILL.md').read_text(), 'rules')
        if os.name == 'posix':
            for directory in (self.state/'resume-private', self.state/'resume-private/package', self.state/'resume-data'):
                self.assertEqual(directory.stat().st_mode & 0o777, 0o700)

    def test_preserves_new_user_state_and_omitted_material(self):
        runtime = self.initial({'SKILL.md':'old rules', 'references/ledger.json':'baseline', 'assets/old.pdf':'original bytes'})
        (runtime/'references/ledger.json').write_text('new user entry')
        (runtime/'references/cloud-only.json').write_text('cloud extra')
        incoming = package(self.root/'incoming', 'new', {'SKILL.md':'new rules', 'references/ledger.json':'baseline'})
        reviewed = self.root/'reviewed'; reviewed.mkdir()
        (reviewed/'SKILL.md').write_text('new rules')
        report = updater.update(incoming, self.state, apply=True, resolution_dir=reviewed)
        self.assertEqual(report['retainedOmittedFiles'], 2)
        self.assertEqual((runtime/'SKILL.md').read_text(), 'new rules')
        self.assertEqual((runtime/'references/ledger.json').read_text(), 'new user entry')
        self.assertEqual((runtime/'assets/old.pdf').read_text(), 'original bytes')
        self.assertEqual((runtime/'references/cloud-only.json').read_text(), 'cloud extra')
        saved = Path(report['backupRoot'])
        self.assertEqual((saved/'runtime/SKILL.md').read_text(), 'old rules')
        self.assertEqual((saved/'runtime/references/ledger.json').read_text(), 'new user entry')
        self.assertTrue((saved/'package/resources-manifest.json').exists())

    def test_conflicting_ledger_cannot_be_blindly_replaced(self):
        runtime = self.initial({'SKILL.md':'rules', 'references/ledger.json':'baseline'})
        (runtime/'references/ledger.json').write_text('cloud application')
        incoming = package(self.root/'incoming', 'new', {'SKILL.md':'rules', 'references/ledger.json':'incoming application'})
        before = updater.inventory(runtime)
        report = updater.update(incoming, self.state)
        self.assertEqual(report['unresolvedConflicts'], ['references/ledger.json'])
        with self.assertRaisesRegex(ValueError, 'Unresolved state or concurrent edits'):
            updater.update(incoming, self.state, apply=True)
        self.assertEqual(updater.inventory(runtime), before)
        resolutions = self.root/'reviewed'
        (resolutions/'references').mkdir(parents=True)
        (resolutions/'references/ledger.json').write_text('cloud application + incoming application')
        updater.update(incoming, self.state, apply=True, resolution_dir=resolutions)
        self.assertEqual((runtime/'references/ledger.json').read_text(), 'cloud application + incoming application')

    def test_factory_baseline_ledger_and_rules_require_review_before_replacement(self):
        runtime = self.initial({'SKILL.md':'existing operating rules',
                                'references/ledger.json':'old unique application',
                                'private/vault.json':'existing private metadata'})
        incoming = package(self.root/'incoming', 'new', {'SKILL.md':'new shorter rules',
                         'references/ledger.json':'different application',
                         'private/vault.json':'different private metadata'})
        report = updater.update(incoming, self.state)
        self.assertEqual(report['unresolvedConflicts'],
                         ['SKILL.md', 'private/vault.json', 'references/ledger.json'])
        before = updater.inventory(runtime)
        with self.assertRaisesRegex(ValueError, 'Unresolved state or concurrent edits'):
            updater.update(incoming, self.state, apply=True)
        self.assertEqual(updater.inventory(runtime), before)

    def test_changed_script_can_update_without_business_state_conflict(self):
        runtime = self.initial({'SKILL.md':'rules', 'scripts/helper.py':'old implementation'})
        incoming = package(self.root/'incoming', 'new', {'SKILL.md':'rules', 'scripts/helper.py':'new implementation'})
        report = updater.update(incoming, self.state, apply=True)
        self.assertEqual(report['conflicts'], [])
        self.assertEqual((runtime/'scripts/helper.py').read_text(), 'new implementation')

    def test_failed_second_swap_restores_both_originals(self):
        package_target, runtime_target = self.root/'package', self.root/'runtime'
        new_package, new_runtime = self.root/'new-package', self.root/'new-runtime'
        for directory, text in [(package_target,'old package'),(runtime_target,'old runtime'),(new_package,'new package'),(new_runtime,'new runtime')]:
            directory.mkdir(); (directory/'value').write_text(text)
        backup = self.root/'backup'; backup.mkdir()
        def failing_rename(source, destination):
            if source == new_runtime:
                raise OSError('simulated second activation failure')
            os.rename(source, destination)
        with self.assertRaisesRegex(OSError, 'simulated'):
            updater.activate([('package',new_package,package_target),('runtime',new_runtime,runtime_target)], backup, rename=failing_rename)
        self.assertEqual((package_target/'value').read_text(), 'old package')
        self.assertEqual((runtime_target/'value').read_text(), 'old runtime')
        self.assertEqual((backup/'failed-new-package/value').read_text(), 'new package')

    def test_rejects_symlinks_and_unpaired_runtime(self):
        incoming = package(self.root/'incoming', 'new', {'SKILL.md':'rules'})
        (incoming/'link').symlink_to(incoming/'SKILL.md')
        with self.assertRaisesRegex(ValueError,'Symlinks'):
            updater.update(incoming,self.state)
        (incoming/'link').unlink()
        (self.state/'resume-data').mkdir()
        with self.assertRaisesRegex(ValueError,'pair is incomplete'):
            updater.update(incoming,self.state,apply=True)

    def test_standalone_copy_installs_from_shallow_private_directory(self):
        standalone = self.root/'updater.py'
        shutil.copy2(SCRIPT, standalone)
        incoming = package(self.root/'incoming', 'new', {'SKILL.md':'rules'})
        result = subprocess.run([sys.executable, str(standalone), '--package-dir', str(incoming),
                                 '--state-dir', str(self.state), '--apply'], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['applied'])
        self.assertEqual((self.state/'resume-data/SKILL.md').read_text(), 'rules')

    def test_rejects_other_git_checkout_as_destination(self):
        incoming = package(self.root/'incoming', 'new', {'SKILL.md':'rules'})
        other = self.root/'other-checkout'; other.mkdir(); (other/'.git').mkdir()
        with self.assertRaisesRegex(ValueError,'outside Git checkouts'):
            updater.update(incoming, other/'private-state', apply=True)

    def test_source_change_prevents_activation(self):
        runtime = self.initial({'SKILL.md':'rules'})
        incoming = package(self.root/'incoming', 'new', {'SKILL.md':'rules', 'assets/new.pdf':'new asset'})
        original = updater.inventory
        count = 0
        def changed_inventory(root):
            nonlocal count
            if root == runtime:
                count += 1
                if count == 2:
                    (runtime/'concurrent.txt').write_text('written concurrently')
            return original(root)
        with patch.object(updater,'inventory',side_effect=changed_inventory):
            with self.assertRaisesRegex(ValueError,'Existing state changed'):
                updater.update(incoming,self.state,apply=True)
        self.assertEqual((runtime/'SKILL.md').read_text(),'rules')
        self.assertEqual((runtime/'concurrent.txt').read_text(),'written concurrently')


if __name__ == '__main__':
    unittest.main()
