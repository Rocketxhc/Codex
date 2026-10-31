# Cloud skills

This repository stores reusable skills and their cloud runtime configuration. Tasks already have an isolated checkout: use this checkout and do not create worktrees unless the user explicitly requests one.

## Prepare the cloud runtime

- At the start of a task that needs these skills, run `bash .cloud/bootstrap.sh --check` from the repository root. If it reports missing runtime assets or dependencies, run `bash .cloud/bootstrap.sh`, then repeat the check. Preserve platform proxies, CA trust and injected authentication; do not disable verification.
- Source `/workspace/skill-platform/activate.sh` in execution shells. If `CLOUD_SKILLS_STATE_DIR` selects another cloud location, source that location's `activate.sh` instead. All execution happens in the cloud machine; the user's phone or computer does not need these dependencies.
- Skill source files are tracked in `.agents/skills`. Read the relevant `SKILL.md` before using a skill. Use the files directly even if the current session's skill menu does not refresh. User-level discovery links may be rebuilt with `python3 .cloud/register-skills.py`; preserve existing unrelated skills.
- Do not reinstall on every command. The read-only bootstrap check establishes whether the retained cloud runtime can be reused. Live browser or desktop processes must be started again after cloud restoration.

## Choose the relevant skill

| User request | Skill file |
| --- | --- |
| Visit websites, read pages, fill forms, click or take web screenshots | `.agents/skills/agent-browser/SKILL.md` |
| Operate the cloud graphical desktop with screenshots, mouse and keyboard | `.agents/skills/computer-use-cloud/SKILL.md` |
| Create or edit Word documents | `.agents/skills/document-creator/SKILL.md` |
| Create, read or edit PDFs | `.agents/skills/pdf/SKILL.md` |
| Create editable PowerPoint slides | `.agents/skills/presentation-creator/SKILL.md` |
| Personal job search, role screening, resume preparation, application deduplication or continuing saved application work | `.agents/skills/toudi-jianli-github/SKILL.md` |
| Generate or edit images | `.agents/skills/imagegen/SKILL.md` |
| Explicitly request an architecture review | `.agents/skills/improve-codebase-architecture/SKILL.md` |
| Architecture vocabulary, design, decision discussion or domain modeling | `.agents/skills/codebase-design/SKILL.md`, `.agents/skills/grilling/SKILL.md`, `.agents/skills/domain-modeling/SKILL.md` |

Match ordinary user requests to these installed skills automatically; do not ask the user to install the skills again. The architecture review skill remains explicit-only. Its references to a separate Skill tool mean reading the named local skill and references here. Deliver architecture reports as files, with self-contained CSS/SVG when remote CDN access is unavailable; `xdg-open` is not a user-facing cloud delivery mechanism.

For browser work, use the configured `agent-browser` wrapper, read `agent-browser skills get core`, use a task-specific `--session`, and close it when done. The wrapper preserves the cloud proxy and CA trust. For local webpage checks, use a temporary loopback HTTP server because this platform blocks `file://`; do not offer localhost preview links to the user.

For desktop work, start the state directory's `computer-start.sh` in a retained execution-tool session, check `computer-use status`, and inspect screenshots before acting. Start only services needed by the current task. Do not assume live processes or account sessions survive a snapshot.

For documents/PPT, use the state directory's `documents-venv/bin/python` and inspect rendered pages before delivery. For images, prefer the platform's built-in image tool; this skill does not install a local model or select a specific Image 2 model.

## Persistence and personal data

Commit skill source, licenses, and `.cloud` configuration. Keep dependency installations, `.env` values, login state, Chromium profiles, Xauthority, logs, resumes and other personal application material in private cloud runtime storage outside the checkout. Never commit these to GitHub merely because they are available locally.

The personal resume skill is installed in the prepared cloud environment. Run `resume-skill status` and read its private runtime `SKILL.md` before using it. The public repository contains only a generic entrypoint; the uploaded package, identifying manifests, personal materials and mutable ledgers stay outside Git. A clone in an unrelated environment requires privately provisioned resources; select the prepared environment instead of asking the user to install tools on their phone.

The original Windows DPAPI vault is not decryptable in this Linux environment, and recruitment-site login/submission has not been validated. Installation is not a request to submit applications. Use the existing verified cloud browser, the current conversation's task scope, and real website results when performing a later authorized task. After state-changing work, save a private incremental checkpoint with `resume-skill state export`; never push it to the public repository. New independent tasks must restore the latest authoritative private checkpoint before continuing; do not assume a published initial snapshot includes changes made in other tasks.
