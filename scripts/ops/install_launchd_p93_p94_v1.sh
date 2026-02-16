#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(git rev-parse --show-toplevel)" && pwd)"
DST_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$DST_DIR"

require_file() { [ -f "$1" ] || { echo "ERROR missing: $1" >&2; exit 2; }; }

T_P93="$ROOT/docs/ops/services/launchd_p93_status_dashboard_v1.template.plist"
T_P94="$ROOT/docs/ops/services/launchd_p94_p93_status_dashboard_retention_v1.template.plist"
require_file "$T_P93"
require_file "$T_P94"

P93="$DST_DIR/com.peaktrade.p93_status_dashboard_v1.plist"
P94="$DST_DIR/com.peaktrade.p94_p93_status_dashboard_retention_v1.plist"

render() {
  local src="$1" dst="$2"
  sed "s|@REPO_ROOT@|$ROOT|g" "$src" > "$dst"
  plutil -lint "$dst" >/dev/null
}

render "$T_P93" "$P93"
render "$T_P94" "$P94"

uid="$(id -u)"
bootout_one() { launchctl bootout "gui/$uid" "$1" 2>/dev/null || true; }

bootout_one "$P93"
bootout_one "$P94"

launchctl bootstrap "gui/$uid" "$P93"
launchctl bootstrap "gui/$uid" "$P94"

launchctl kickstart -k "gui/$uid/com.peaktrade.p93-status-dashboard" || true
launchctl kickstart -k "gui/$uid/com.peaktrade.p94-p93-status-dashboard-retention" || true

echo "INSTALL_OK p93=$P93 p94=$P94 root=$ROOT"
