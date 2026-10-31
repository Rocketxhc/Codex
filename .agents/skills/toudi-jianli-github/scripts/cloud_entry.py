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
    parser.add_argument('command', choices=['prepare', 'status', 'read', 'resolve', 'run', 'state'])
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = bootstrap()
    if args.command in ('prepare', 'status'):
        if args.arguments:
            parser.error('prepare/status take no additional arguments')
        result = subprocess.run([*command, args.command], text=True, capture_output=True)
        if result.returncode:
            # A normal failure message does not need personal package metadata.
            raise SystemExit('Private resume setup check failed; inspect the private package locally without publishing its contents.')
        report = json.loads(result.stdout)
        print(json.dumps({k: report[k] for k in ('ready', 'created', 'runtimeRoot', 'verifiedFiles', 'expandedBytes', 'windowsEncryptedVaultNeedsOriginalWindowsUser') if k in report}, ensure_ascii=False, indent=2))
        return 0
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
