#!/usr/bin/env python3
"""Register this checkout's skills without overwriting existing installations."""
import os
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
source = repo / '.agents/skills'
destination = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'skills'
skills = sorted(p for p in source.iterdir() if (p / 'SKILL.md').is_file())
if not skills:
    raise SystemExit('No tracked skills found in this checkout')
# Check all conflicts before changing any links.
for skill in skills:
    target = destination / skill.name
    if target.is_symlink() and target.resolve() == skill.resolve():
        continue
    if target.exists() or target.is_symlink():
        raise SystemExit(f'Preserving another installation: {target}. Read this checkout skill directly or resolve the conflict.')
destination.mkdir(parents=True, exist_ok=True)
for skill in skills:
    target = destination / skill.name
    if not target.is_symlink():
        target.symlink_to(skill, target_is_directory=True)
    print(f'Registered {skill.name}')
