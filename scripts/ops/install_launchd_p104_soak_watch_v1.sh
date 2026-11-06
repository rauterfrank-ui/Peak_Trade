#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(git rev-parse --show-toplevel)" && pwd)"
DST_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$DST_DIR"

require_file() { [ -f "$1" ] || { echo "ERROR missing: $1" >&2; exit 2; }; }

T_P104="$ROOT/docs/ops/services/launchd_p104_soak_watch_v1.template.plist"
require_file "$T_P104"

P104="$DST_DIR/com.peaktrade.p104_soak_watch_v1.plist"

sed "s|@REPO_ROOT@|$ROOT|g" "$T_P104" > "$P104"
plutil -lint "$P104" >/dev/null

uid="$(id -u)"
launchctl bootout "gui/$uid" "$P104" 2>/dev/null || true

launchctl bootstrap "gui/$uid" "$P104"
launchctl kickstart -k "gui/$uid/com.peaktrade.p104-soak-watch" || true

echo "INSTALL_OK p104=$P104 root=$ROOT"
