#!/usr/bin/env python3
"""Invoke a privately provisioned job-application package without publishing its data."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[4]
STATE = Path(os.environ.get('CLOUD_SKILLS_STATE_DIR', '/workspace/skill-platform')).expanduser().resolve()
PACKAGE = Path(os.environ.get('TOUDI_GITHUB_PACKAGE_DIR', str(STATE / 'resume-private/package'))).expanduser().resolve()
RUNTIME = Path(os.environ.get('TOUDI_GITHUB_DATA_DIR', str(STATE / 'resume-data'))).expanduser().resolve()


def require_private(path):
    if path == REPO or REPO in path.parents:
        raise SystemExit('Personal job-application data must remain outside the Git checkout.')


def bootstrap():
    require_private(PACKAGE)
    require_private(RUNTIME)
    script = PACKAGE / 'scripts/bootstrap.py'
    if not script.is_file() or not (PACKAGE / 'resources-manifest.json').is_file():
        raise SystemExit('Private resume resources are unavailable. Select the prepared cloud environment or restore its private package; the public repository intentionally contains no personal data.')
    interpreter = STATE / 'documents-venv/bin/python'
    if not interpreter.is_file():
        raise SystemExit('Cloud document dependencies are missing. Run bash .cloud/bootstrap.sh first.')
    return [str(interpreter), str(script), '--runtime-dir', str(RUNTIME)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'status', 'verify', 'update', 'read', 'resolve', 'run', 'state'])
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command == 'update':
        if PACKAGE != STATE / 'resume-private/package' or RUNTIME != STATE / 'resume-data':
            raise SystemExit('Automatic update requires the standard private layout; custom TOUDI_GITHUB paths must be reconciled explicitly before updating.')
        script = Path(__file__).with_name('update_private_package.py')
        return subprocess.run([sys.executable, str(script), '--state-dir', str(STATE), *args.arguments]).returncode
    command = bootstrap()
    if args.command in ('prepare', 'status'):
        if args.arguments:
            parser.error('prepare/status take no additional arguments')
        result = subprocess.run([*command, args.command], text=True, capture_output=True)
        if result.returncode:
            # A normal failure message does not need personal package metadata.
            raise SystemExit('Private resume setup check failed; inspect the private package locally without publishing its contents.')
        report = json.loads(result.stdout)
        summary = {k: report[k] for k in ('ready', 'created', 'runtimeRoot', 'verifiedFiles', 'expandedBytes', 'windowsEncryptedVaultNeedsOriginalWindowsUser') if k in report}
        installation = RUNTIME / 'references/cloud-installation-state.json'
        if not installation.is_file():
            installation = STATE / 'resume-private/installation.json'
        if installation.is_file():
            metadata = json.loads(installation.read_text(encoding='utf-8'))
            if 'stateReconciliationRequired' in metadata:
                summary['stateReconciliationRequired'] = metadata['stateReconciliationRequired']
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if args.command == 'verify' and args.arguments:
        parser.error('verify takes no additional arguments')
    if args.command == 'state':
        if not args.arguments or args.arguments[0] not in ('export', 'import'):
            parser.error('state requires export or import followed by its options')
        # State archives contain personal information and may never be placed in this checkout.
        for position, value in enumerate(args.arguments):
            if value == '--output' and position + 1 < len(args.arguments):
                require_private(Path(args.arguments[position + 1]).expanduser().resolve())
            elif value.startswith('--output='):
                require_private(Path(value.split('=', 1)[1]).expanduser().resolve())
        script = PACKAGE / 'scripts/cloud_state.py'
        return subprocess.run([command[0], str(script), '--package-manifest', str(PACKAGE / 'resources-manifest.json'), '--runtime-dir', str(RUNTIME), *args.arguments]).returncode
    return subprocess.run([*command, args.command, *args.arguments]).returncode


if __name__ == '__main__':
    raise SystemExit(main())
