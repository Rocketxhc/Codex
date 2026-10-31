---
name: computer-use-cloud
description: Operate applications in this cloud environment through real desktop screenshots, mouse clicks, keyboard shortcuts, and Unicode text input. Use when a task needs graphical computer interaction rather than only DOM automation.
---

# Cloud computer use

This independent local skill controls an authenticated Xorg dummy desktop at 1280 × 900. It uses X11/XTest input and native UTF-8 clipboard paste. It does not provision a model API, access the user's personal computer, or provide a remote-desktop web preview.

## Start and inspect

Use the existing `/workspace/Codex` checkout. Every cloud task is isolated; do not create a worktree unless the user asks.

1. Run `/workspace/skill-platform/computer-install.sh` if refreshing dependencies is necessary.
2. Start `/workspace/skill-platform/computer-start.sh` through an execution tool with a short yield. The command remains running in its tool session; retain the session until desktop work is done. An ordinary background command can be reclaimed when its execution session finishes. Local X11 sockets may require the tool's standard approval mechanism.
3. Run `/workspace/skill-platform/bin/computer-use status` in a separate execution call. Expect display `:97`, width `1280`, height `900`.
4. Launch the desired GUI application with `DISPLAY=:97` and `XAUTHORITY=/workspace/skill-platform/desktop-tools/Xauthority`, also retaining its tool session. Chromium is available at `/usr/bin/chromium`; use a dedicated profile under `/workspace/skill-platform/desktop-tools/`. Native Chromium does not automatically use HTTP_PROXY/HTTPS_PROXY: the example below is verified only for local fixtures/about:blank. For external websites, use the separately installed `/workspace/skill-platform/bin/agent-browser` integration, which configures the platform proxy and CA, rather than assuming raw Chromium inherits that configuration. Its browser instructions are in the `agent-browser` skill; the GUI external-network route has not been verified by this desktop validation.

Example browser launch for local desktop interaction:

```sh
DISPLAY=:97 XAUTHORITY=/workspace/skill-platform/desktop-tools/Xauthority \
chromium --disable-dev-shm-usage --no-first-run \
  --user-data-dir=/workspace/skill-platform/desktop-tools/chromium-profile \
  --window-size=1280,900 --window-position=0,0 --app=about:blank
```

## Screenshot and action loop

```sh
/workspace/skill-platform/bin/computer-use screenshot /workspace/scratch/desktop.png
/workspace/skill-platform/bin/computer-use click 180 158
/workspace/skill-platform/bin/computer-use type '中文 text'
/workspace/skill-platform/bin/computer-use key ctrl+a
/workspace/skill-platform/bin/computer-use key Return
/workspace/skill-platform/bin/computer-use scroll 3
```

View each screenshot using the platform's image-viewing tool. Choose coordinates from the current screenshot. Take another screenshot after a small group of actions and verify the application result. A click or a successful helper exit alone does not verify the task completed.

`type` pastes into the focused editable control and temporarily owns the desktop clipboard. It supports UTF-8 text up to 60000 bytes per call. Focus the intended input before pasting. `key` accepts `ctrl+a`, `ctrl+v`, `Return`, `Tab`, `Escape`, `BackSpace`, arrow names, and X11 key names.

Use the platform's authorization rules for messages, uploads, purchases, and other external actions. Installing this skill is not authorization to submit applications or send personal data. Supply account credentials through supported environment settings or the service's ordinary authorized login flow, never saved skill text.

## Lifecycle and limitations

- Live Xorg, Chromium, and tool sessions do not survive environment publication/restoration. Start them again in a new task.
- The start script validates PID identity. It never kills a process merely because an old PID file happens to match it.
- The desktop has no window manager by default. Launch a GUI app at explicit coordinates; it can still be operated by real screenshots and X11 input.
- The tested workflow is Chromium on the cloud desktop. Other GUI applications require their own installation and functional verification.
- No inbound VNC/noVNC endpoint is created. Do not present loopback URLs as user-facing previews.
- Source and dependencies: original local helper; system Xorg 1.21.1.16, dummy Xorg driver, X11, XTest, ImageMagick, xauth; python-xlib 0.33 in the dedicated desktop venv.
