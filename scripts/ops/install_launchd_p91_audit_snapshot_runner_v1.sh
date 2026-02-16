#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

TPL="docs/ops/services/launchd_p91_audit_snapshot_runner_v1.template.plist"
DST="$HOME/Library/LaunchAgents/com.peaktrade.p91_audit_snapshot_runner_v1.plist"
LABEL="com.peaktrade.p91-audit-snapshot-runner"
MY_UID="$(id -u)"

test -f "$TPL"

mkdir -p "$(dirname "$DST")"
rendered="$(cat "$TPL" | sed "s|@REPO_ROOT@|$ROOT|g")"
printf "%s\n" "$rendered" > "$DST"

plutil -lint "$DST" >/dev/null

launchctl bootout "gui/$MY_UID" "$DST" 2>/dev/null || true
launchctl bootstrap "gui/$MY_UID" "$DST"
launchctl kickstart -k "gui/$MY_UID/$LABEL"

echo "INSTALL_P91_OK plist=$DST label=$LABEL repo_root=$ROOT"
