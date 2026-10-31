#!/usr/bin/env bash
# Retain this command's execution session while graphical work is running.
set -euo pipefail
cloud_state=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
base="$cloud_state/desktop-tools"
mkdir -p "$base" /tmp/.X11-unix
export DISPLAY="${CLOUD_SKILLS_DISPLAY:-:97}"
if [[ ! "$DISPLAY" =~ ^:[0-9]+$ ]]; then
  echo 'CLOUD_SKILLS_DISPLAY must be a local display such as :97.' >&2
  exit 1
fi
display_number=${DISPLAY#:}
export XAUTHORITY="$base/Xauthority"
lock="/tmp/.X$display_number-lock"
socket="/tmp/.X11-unix/X$display_number"
if [[ -f "$base/Xorg.pid" ]]; then
  desktop_pid=$(cat "$base/Xorg.pid")
  if python3 - "$desktop_pid" "$base/xorg.conf" "$DISPLAY" <<'PY'
import pathlib,sys
try:
    pid=int(sys.argv[1])
    assert pid>0
    parts=pathlib.Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
    assert pathlib.Path(parts[0].decode()).name=='Xorg'
    assert sys.argv[2].encode() in parts and sys.argv[3].encode() in parts
except (OSError,ValueError,AssertionError):
    raise SystemExit(1)
PY
  then
    if xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
      echo "Cloud desktop $DISPLAY already ready"
      exit 0
    fi
    echo 'Owned Xorg exists but is not accepting authenticated clients; inspect its log.' >&2
    exit 1
  fi
  if [[ "$desktop_pid" =~ ^[1-9][0-9]*$ ]]; then
    desktop_state=$(ps -o stat= -p "$desktop_pid" 2>/dev/null || true)
    if { [[ -z "$desktop_state" ]] || [[ "$desktop_state" = Z* ]]; } && [[ -f "$lock" ]] && [[ "$(tr -d '[:space:]' < "$lock")" = "$desktop_pid" ]]; then
      rm -f "$lock" "$socket"
    fi
  fi
fi
if [[ -e "$lock" ]]; then
  echo "Display $DISPLAY has an unverified lock; do not stop an unrelated server." >&2
  exit 1
fi
umask 077
desktop_cookie=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
touch "$XAUTHORITY"
xauth -f "$XAUTHORITY" add "$DISPLAY" . "$desktop_cookie"
unset desktop_cookie
Xorg "$DISPLAY" -config "$base/xorg.conf" -auth "$XAUTHORITY" -logfile "$base/Xorg.log" -nolisten tcp -noreset >"$base/Xorg.stdout.log" 2>&1 </dev/null &
desktop_pid=$!
echo "$desktop_pid" > "$base/Xorg.pid"
trap 'kill "$desktop_pid" 2>/dev/null || true' EXIT INT TERM
for attempt in $(seq 1 50); do
  if xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
    echo "Cloud desktop $DISPLAY ready (1280x900, local X11 only)"
    wait "$desktop_pid"
    exit $?
  fi
  sleep .1
done
cat "$base/Xorg.stdout.log" >&2
exit 1
