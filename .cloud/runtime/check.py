#!/usr/bin/env python3
"""Check installed runtime without installing packages or starting processes."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

repo=Path(sys.argv[1]).resolve()
state=Path(sys.argv[2]).resolve()
for name in ('python3','node','npm','chromium','certutil','soffice','pdftoppm','fc-match','Xorg','xauth','xdpyinfo','import'):
    if not shutil.which(name):
        raise SystemExit(f'Required cloud-image tool missing: {name}')
if not Path('/usr/lib/xorg/modules/drivers/dummy_drv.so').is_file():
    raise SystemExit('The cloud image needs the Xorg dummy display driver')
assets={
    'bin/agent-browser':'runtime/agent-browser',
    'bin/computer-use':'runtime/computer-use',
    'computer-start.sh':'runtime/computer-start.sh',
    'activate.sh':'runtime/activate.sh',
    'desktop-tools/xorg.conf':'runtime/xorg.conf',
    'browser-tools/package.json':'browser/package.json',
    'browser-tools/package-lock.json':'browser/package-lock.json',
}
for destination,source in assets.items():
    target=state/destination
    if not target.is_file() or target.read_bytes()!=(repo/'.cloud'/source).read_bytes():
        raise SystemExit(f'Runtime needs bootstrap: {target}')
if not (state/'repository-path').is_file() or (state/'repository-path').read_text().strip()!=str(repo):
    raise SystemExit('Runtime belongs to another checkout; choose a separate CLOUD_SKILLS_STATE_DIR.')
dependencies=[]
for line in (repo/'.cloud/requirements.txt').read_text().splitlines():
    if line.strip() and not line.startswith('#'): dependencies.append(line.strip().split('==',1))
code='import importlib.metadata,json,sys\nfor n,v in json.loads(sys.argv[1]):\n assert importlib.metadata.version(n)==v,(n,v)\nfrom docx import Document\nfrom pptx import Presentation\nfrom pypdf import PdfReader\nimport Xlib,pdfplumber\n'
for relative in ('documents-venv/bin/python','desktop-tools/venv/bin/python'):
    interpreter=state/relative
    if not interpreter.is_file(): raise SystemExit(f'Missing interpreter: {interpreter}')
    subprocess.run([str(interpreter),'-c',code,json.dumps(dependencies)],check=True)
package=state/'browser-tools/node_modules/agent-browser/package.json'
if not package.is_file() or json.loads(package.read_text()).get('version')!='0.41.0':
    raise SystemExit('agent-browser 0.41.0 is not installed')
subprocess.run(['node','-e','if(Number(process.versions.node.split(".")[0])<24) process.exit(1)'],check=True)
subprocess.run([str(state/'bin/agent-browser'),'--version'],check=True)
skills=sorted(p.parent.name for p in (repo/'.agents/skills').glob('*/SKILL.md'))
if not skills: raise SystemExit('No repository skills found')
print(f'Cloud runtime ready; {len(skills)} repository skills available; services start on demand.')
