#!/usr/bin/env bash
# Source this file in each new shell; no live processes are restored by a snapshot.
cloud_skills_state=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export CLOUD_SKILLS_STATE_DIR="$cloud_skills_state"
export CLOUD_SKILLS_REPO="$(cat "$cloud_skills_state/repository-path")"
case ":$PATH:" in
  *":$cloud_skills_state/bin:"*) ;;
  *) export PATH="$cloud_skills_state/bin:$PATH" ;;
esac
unset cloud_skills_state
