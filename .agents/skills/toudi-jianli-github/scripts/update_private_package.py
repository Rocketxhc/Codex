#!/usr/bin/env python3
"""Plan or apply a private resource update without deleting existing material.

Stop all application writers first. This performs a file-level three-way merge;
conflicting files require reviewed replacements in --resolution-dir. Existing
business rules, references and private state always require review when the new
snapshot changes them, even if they match the old factory baseline. Neither an
incoming snapshot nor modification times determine which user state is newer.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid

REPO = next((parent for parent in Path(__file__).resolve().parents if (parent / '.git').exists()), None)
MARKER = '.toudi-runtime.json'


def private_path(value):
    path = Path(value).expanduser().absolute()
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise ValueError('Symlink paths are refused')
    path = path.resolve()
    if (REPO is not None and (path == REPO or REPO in path.parents)) or any((parent / '.git').exists() for parent in (path, *path.parents)):
        raise ValueError('Personal resources must remain outside Git checkouts')
    return path


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inventory(root):
    """Hash ordinary files; reject links and ambiguous cross-platform paths."""
    if not root.exists():
        return {}
    if not root.is_dir() or root.is_symlink():
        raise ValueError('Expected an ordinary directory')
    result, folded = {}, set()
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            key = path.relative_to(root).as_posix()
            if path.is_symlink():
                raise ValueError('Symlinks are refused: ' + key)
            if key.casefold() in folded or any(c in name for c in ('\\', ':')) or name.rstrip(' .') != name:
                raise ValueError('Ambiguous resource path: ' + key)
            folded.add(key.casefold())
            if not (path.is_dir() or stat.S_ISREG(path.stat().st_mode)):
                raise ValueError('Special files are refused: ' + key)
            if path.is_file():
                result[key] = sha(path)
    return result


def baseline(package):
    data = load(package / 'resources-manifest.json')
    if not isinstance(data.get('packageId'), str) or not data['packageId'] or not isinstance(data.get('files'), dict):
        raise ValueError('Invalid package manifest')
    for key, info in data['files'].items():
        path = PurePosixPath(key)
        if not key or path.is_absolute() or any(p in ('', '.', '..') for p in key.split('/')) or '\\' in key or ':' in key or key == MARKER:
            raise ValueError('Invalid manifest path')
        digest = info.get('sha256', '')
        if len(digest) != 64 or any(c not in '0123456789abcdefABCDEF' for c in digest):
            raise ValueError('Invalid baseline hash')
    return data


@contextmanager
def locked(private):
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = private / '.package-update-lock'
    try:
        lock.mkdir(mode=0o700)
    except FileExistsError:
        raise ValueError('Another update is active; inspect the retained update lock before retrying') from None
    try:
        yield
    finally:
        lock.rmdir()


def protected_state(key):
    path = PurePosixPath(key)
    return path.parts[0] in ('references', 'private') or (
        len(path.parts) == 1 and path.suffix.casefold() in ('.md', '.json', '.yaml', '.yml', '.txt')
        and path.name not in (MARKER, 'resources-manifest.json'))


def choices(base, current, incoming):
    """Protect all existing business state, plus conflicting concurrent edits."""
    selected, conflicts = {}, []
    for key in sorted(set(current) | set(incoming)):
        if key == MARKER:
            continue
        b, c, n = base.get(key), current.get(key), incoming.get(key)
        if n is None:
            selected[key] = 'current'  # No update ever deletes omitted material.
        elif c == n:
            selected[key] = 'current'
        elif n == b:
            selected[key] = 'current'  # Includes a deliberate user deletion.
        elif c is not None and protected_state(key):
            conflicts.append(key)  # A newer snapshot may omit an older valid record or rule.
        elif c == b:
            selected[key] = 'incoming'
        else:
            conflicts.append(key)
    return selected, conflicts


def activate(pairs, backup, rename=os.rename):
    """Swap directories, retaining originals; roll back every completed swap."""
    moved, installed = [], []
    try:
        for name, candidate, target in pairs:
            saved = backup / name
            if target.exists():
                rename(target, saved)
                moved.append((saved, target))
            rename(candidate, target)
            installed.append(target)
    except BaseException:
        for target in reversed(installed):
            if target.exists():
                # Preserve the failed new candidate as evidence; do not delete it.
                os.rename(target, backup / ('failed-new-' + target.name))
        for saved, target in reversed(moved):
            os.rename(saved, target)
        raise


def update(package_dir, state_dir, apply=False, resolution_dir=None):
    package_dir, state_dir = private_path(package_dir), private_path(state_dir)
    resolution_dir = private_path(resolution_dir) if resolution_dir else None
    private = state_dir / 'resume-private'
    target_package, target_runtime = private / 'package', state_dir / 'resume-data'
    for path in (target_package, target_runtime):
        private_path(path)
        if path == package_dir or path in package_dir.parents or package_dir in path.parents:
            raise ValueError('Incoming package must be separate from installed paths')
    if resolution_dir and (resolution_dir == target_runtime or target_runtime in resolution_dir.parents):
        raise ValueError('Reviewed resolutions must be separate from the live runtime')
    with locked(private):
        old_package_files, current = inventory(target_package), inventory(target_runtime)
        if bool(target_package.exists()) != bool(target_runtime.exists()):
            raise ValueError('Existing package/runtime pair is incomplete; restore the matching baseline before updating')
        fresh = not target_runtime.exists()
        old = baseline(target_package) if not fresh else {'files': {}}
        if not fresh and load(target_runtime / MARKER).get('packageId') != old.get('packageId'):
            raise ValueError('Existing runtime does not match its installed baseline package')
        incoming_package_files = inventory(package_dir)
        new = baseline(package_dir)
        resolutions = inventory(resolution_dir) if resolution_dir else {}
        with tempfile.TemporaryDirectory(prefix='.package-update-', dir=private) as temporary:
            work = Path(temporary)
            candidate_package, unpacked, candidate_runtime = work / 'package', work / 'unpacked', work / 'runtime'
            shutil.copytree(package_dir, candidate_package)
            candidate_package.chmod(0o700)
            result = subprocess.run([sys.executable, str(candidate_package / 'scripts/bootstrap.py'),
                                     '--runtime-dir', str(unpacked), 'prepare'], capture_output=True, text=True)
            if result.returncode:
                raise ValueError('Incoming package failed offline preparation; existing installation is unchanged')
            incoming = inventory(unpacked)
            if set(incoming) != set(new['files']) | {MARKER}:
                raise ValueError('Prepared incoming resources differ from the declared inventory')
            for key, record in new['files'].items():
                if incoming.get(key) != record['sha256'].lower():
                    raise ValueError('Incoming resource verification failed: ' + key)
            if load(unpacked / MARKER).get('packageId') != new['packageId']:
                raise ValueError('Prepared incoming runtime has a mismatched marker')
            selected, conflicts = choices({k:v['sha256'].lower() for k,v in old['files'].items()}, current, incoming)
            unresolved = [key for key in conflicts if key not in resolutions]
            for key in conflicts:
                if key in resolutions:
                    selected[key] = 'resolution'
            retained = [k for k in current if k not in incoming and k != MARKER]
            report = {'applied': False, 'freshInstall': fresh, 'conflicts': conflicts,
                      'unresolvedConflicts': unresolved, 'retainedOmittedFiles': len(retained),
                      'incomingResources': len(new['files']), 'runtimeRoot': str(target_runtime)}
            if not apply:
                return report
            if unresolved:
                raise ValueError('Unresolved state or concurrent edits; run without --apply and review every conflict first')
            if not fresh:
                shutil.copytree(target_runtime, candidate_runtime)
            else:
                candidate_runtime.mkdir(mode=0o700)
            candidate_runtime.chmod(0o700)
            for key, source in selected.items():
                root = {'current': target_runtime, 'incoming': unpacked, 'resolution': resolution_dir}[source]
                if source == 'current':
                    continue
                destination = candidate_runtime / key
                if destination.exists() and destination.is_dir():
                    raise ValueError('File/directory collision: ' + key)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(root / key, destination)
            shutil.copy2(unpacked / MARKER, candidate_runtime / MARKER)
            # Every source remains stable through preparation and candidate creation.
            if inventory(target_runtime) != current or inventory(target_package) != old_package_files:
                raise ValueError('Existing state changed during planning; stop application writers and retry')
            if inventory(package_dir) != incoming_package_files or (resolution_dir and inventory(resolution_dir) != resolutions):
                raise ValueError('Update sources changed during planning; retry after review')
            for required in new.get('requiredRuntimeFiles', []):
                if not (candidate_runtime / required).is_file():
                    raise ValueError('Merged runtime is missing a required file: ' + required)
            inventory(candidate_runtime)  # Reject any invalid retained shape before activation.
            backup = private / 'update-backups' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
            backup.mkdir(parents=True, mode=0o700)
            activate([('package', candidate_package, target_package), ('runtime', candidate_runtime, target_runtime)], backup)
            report.update(applied=True, backupRoot=str(backup))
            try:
                (backup / 'update-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            except OSError:
                report['reportFileSaved'] = False  # Activation already succeeded; do not misreport failure.
            return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-dir', required=True, type=Path)
    parser.add_argument('--state-dir', type=Path, default=Path(os.environ.get('CLOUD_SKILLS_STATE_DIR', '/workspace/skill-platform')))
    parser.add_argument('--resolution-dir', type=Path)
    parser.add_argument('--apply', action='store_true', help='Activate only after every conflict has been reviewed')
    args = parser.parse_args()
    try:
        print(json.dumps(update(args.package_dir, args.state_dir, args.apply, args.resolution_dir), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(json.dumps({'applied': False, 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
