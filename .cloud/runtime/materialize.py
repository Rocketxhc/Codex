#!/usr/bin/env python3
"""Materialize owned runtime helpers; preserve differing user configuration."""
from pathlib import Path
import hashlib
import json
import os
import sys

repo = Path(sys.argv[1]).resolve()
state = Path(sys.argv[2]).resolve()
source = repo / '.cloud'
legacy = json.loads((source / 'runtime/legacy-hashes.json').read_text())
assets = {
    'bin/agent-browser': 'runtime/agent-browser',
    'bin/computer-use': 'runtime/computer-use',
    'computer-start.sh': 'runtime/computer-start.sh',
    'activate.sh': 'runtime/activate.sh',
    'desktop-tools/xorg.conf': 'runtime/xorg.conf',
    'browser-tools/package.json': 'browser/package.json',
    'browser-tools/package-lock.json': 'browser/package-lock.json',
}
desired = {name:(source/path).read_bytes() for name,path in assets.items()}
desired['repository-path'] = (str(repo)+'\n').encode()
for name,data in desired.items():
    destination=state/name
    if destination.is_symlink():
        raise SystemExit(f'Refusing to overwrite a runtime symlink: {destination}')
    if destination.exists():
        current=destination.read_bytes()
        if current!=data and hashlib.sha256(current).hexdigest() not in legacy.get(name,[]):
            raise SystemExit(f'Preserving changed runtime file: {destination}; choose a separate CLOUD_SKILLS_STATE_DIR.')
for name,data in desired.items():
    destination=state/name
    destination.parent.mkdir(parents=True,exist_ok=True)
    if not destination.exists() or destination.read_bytes()!=data:
        destination.write_bytes(data)
    if name.startswith('bin/') or name.endswith('.sh'):
        destination.chmod(0o700)
(state/'validation').mkdir(exist_ok=True)
print(f'Runtime helpers prepared in {state}')
