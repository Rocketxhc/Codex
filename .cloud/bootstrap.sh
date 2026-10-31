#!/usr/bin/env bash
# Reproduce the skill runtime from this repository in a Codex cloud machine.
# Does not install a desktop on arbitrary operating systems or start services.
set -euo pipefail
cloud_repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cloud_state=${CLOUD_SKILLS_STATE_DIR:-/workspace/skill-platform}
cloud_register=false
case "${1:-}" in
  --check)
    [[ $# = 1 ]] || { echo 'Usage: bootstrap.sh [--check|--register]' >&2; exit 2; }
    exec python3 "$cloud_repo/.cloud/runtime/check.py" "$cloud_repo" "$cloud_state"
    ;;
  --register) cloud_register=true ;;
  '') ;;
  *) echo 'Usage: bootstrap.sh [--check|--register]' >&2; exit 2 ;;
esac
[[ $# -le 1 ]] || { echo 'Usage: bootstrap.sh [--check|--register]' >&2; exit 2; }
for tool in python3 node npm chromium certutil soffice pdftoppm fc-match Xorg xauth xdpyinfo import; do
  command -v "$tool" >/dev/null || { echo "Required cloud-image tool missing: $tool" >&2; exit 1; }
done
node -e 'if(Number(process.versions.node.split(".")[0])<24) { console.error("Node >=24 is required"); process.exit(1); }'
python3 - "$cloud_repo" <<'PY'
from pathlib import Path
import ctypes.util,sys
repo=Path(sys.argv[1])
assert (repo/'.agents/skills').is_dir(), 'Missing tracked .agents/skills directory'
assert Path('/usr/lib/xorg/modules/drivers/dummy_drv.so').is_file(), 'Cloud image needs the Xorg dummy display driver'
for name in ('X11','Xtst'):
    assert ctypes.util.find_library(name), f'Cloud image library missing: {name}'
PY
python3 "$cloud_repo/.cloud/runtime/materialize.py" "$cloud_repo" "$cloud_state"
for cloud_venv in "$cloud_state/documents-venv" "$cloud_state/desktop-tools/venv"; do
  if [[ ! -x "$cloud_venv/bin/python" ]]; then
    python3 -m venv --system-site-packages "$cloud_venv"
  fi
  "$cloud_venv/bin/python" - "$cloud_repo/.cloud/requirements.txt" <<'PY'
import importlib.metadata,subprocess,sys
from pathlib import Path
needed=[]
for line in Path(sys.argv[1]).read_text().splitlines():
    line=line.strip()
    if not line or line.startswith('#'): continue
    package,version=line.split('==',1)
    try: installed=importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError: installed=None
    if installed!=version: needed.append(line)
if needed:
    subprocess.run([sys.executable,'-m','pip','install','--no-input','--disable-pip-version-check',*needed],check=True)
from docx import Document
from pptx import Presentation
from pypdf import PdfReader
from reportlab.pdfgen import canvas
import pdfplumber,Xlib
print('Pinned Python dependencies verified')
PY
done
npm ci --prefix "$cloud_state/browser-tools" --no-audit --no-fund
"$cloud_state/bin/agent-browser" --version
"$cloud_state/bin/agent-browser" skills get core > "$cloud_state/validation/agent-browser-core.md"
fc-match 'Noto Sans CJK SC'
soffice --version
if [[ -f "${TOUDI_GITHUB_PACKAGE_DIR:-$cloud_state/resume-private/package}/scripts/bootstrap.py" ]]; then
  CLOUD_SKILLS_STATE_DIR="$cloud_state" CLOUD_SKILLS_REPO="$cloud_repo" "$cloud_state/bin/resume-skill" prepare
fi
python3 "$cloud_repo/.cloud/runtime/check.py" "$cloud_repo" "$cloud_state"
if [[ "$cloud_register" = true ]]; then
  python3 "$cloud_repo/.cloud/register-skills.py"
fi
printf 'Cloud skill runtime ready. Source %s/activate.sh in each new shell.\n' "$cloud_state"
printf '%s\n' 'No services started. Generic skill sources are in Git; personal resume resources stay in the prepared private cloud environment.'
