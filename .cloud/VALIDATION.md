# Cloud configuration validation

The committed skill runtime was tested in the selected Codex cloud base image.

- Installed from an empty isolated cloud state directory, without the earlier uploaded archives, vendor source tarballs, existing virtual environments or node_modules.
- Cloned the committed repository into another fresh directory, then bootstrapped a second empty state directory from that clone. No Git worktree was used.
- Both dependency installation and the read-only `bootstrap.sh --check` completed successfully. The recovered runtime exposed all ten tracked skill directories.
- Ran `.cloud/smoke.py` against the fresh clone: created Chinese DOCX and editable PPTX; checked ZIP integrity, exported both through LibreOffice, extracted expected PDF text and page counts, and rendered previews through Poppler.
- The same smoke run started a temporary local webpage, filled an input using the recovered agent-browser CLI, clicked the button, checked the resulting text, saved a screenshot and closed the browser and server.
- The newly cloned checkout remained clean after installation and functional checks. Runtime data was written outside the checkout.
- Separately verified a cloud desktop in an isolated state directory and display, including Xorg startup, authenticated status and screenshot. The desktop workflow previously passed mouse input, English/Chinese text entry, application result checks, and stop/restart checks in this cloud instance.

For a future smoke run after installation:

```bash
python3 .cloud/smoke.py --state /workspace/skill-platform
```

This validation demonstrates reconstruction in a fresh checkout on the current cloud machine. It is not a claim that a new managed task has already restored a published snapshot. Environment publication is performed by the platform. Live image generation, every advanced Office feature, and third-party account access were not tested by this setup. The oversized resume-application archive was unavailable and is not installed.
