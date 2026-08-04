"""Contracts for scripts/webui/local_market_dashboard.sh (LaunchAgent + Chrome tab reuse)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = REPO_ROOT / "scripts" / "webui" / "local_market_dashboard.sh"


def test_local_market_dashboard_script_exists_and_syntax() -> None:
    assert CONTROLLER.is_file()
    subprocess.run(["bash", "-n", str(CONTROLLER)], check=True)


def test_local_market_dashboard_controller_surface_contract() -> None:
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "com.peaktrade.market-dashboard" in text
    assert 'PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"' in text
    assert "market-dashboard.stdout.log" in text
    assert "market-dashboard.stderr.log" in text
    assert "KeepAlive" in text
    assert "cmd_start)" in text or "start) cmd_start" in text
    assert "stop) cmd_stop" in text
    assert "restart) cmd_restart" in text
    assert "status) cmd_status" in text
    assert "open) cmd_open" in text
    assert "logs) cmd_logs" in text
    assert '_run) cmd_run' in text
    assert "SURVIVES_CURSOR_AND_TERMINAL_CLOSE=true" in text
    assert "UNKNOWN_PORT_OWNER_FAIL_CLOSED" in text
    assert "LIVE_AUTHORIZED" in text
    assert "ORDERS_ALLOWED" in text


def test_local_market_dashboard_chrome_open_is_regular_chrome_with_tab_reuse() -> None:
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "chrome_open_reuse_tab" in text
    assert 'Google Chrome' in text
    assert "REUSED_EXISTING_TAB" in text
    assert "OPENED_NEW_TAB_IN_EXISTING_WINDOW" in text
    assert "starts with targetPrefix" in text
    assert "http://127.0.0.1" in text
    assert "/market" in text
    # Forbidden operator command patterns must not be invoked.
    assert not re.search(r'(^|[^#\n])\s*open\s+-na\b', text, re.M)
    assert not re.search(r'(^|[^#\n])[^\n]*--user-data-dir', text, re.M)
    assert not re.search(r'(^|[^#\n])[^\n]*--incognito\b', text, re.M)
    assert not re.search(r'(^|[^#\n])\s*(killall|pkill)\b', text, re.M)
    assert "headless=False" not in text
    assert "PLAYWRIGHT_USED=false" in text
    assert "TEMP_PROFILE_USED=false" in text
    # Must not use the non-reusable open -a path for operator open.
    assert not re.search(r'open\s+-a\s+"Google Chrome"', text)


def test_local_market_dashboard_launchd_uses_foreground_run_not_nohup() -> None:
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "cmd_run()" in text
    assert "exec \"$py\" -m uvicorn" in text
    # Durable path must not rely on nohup for the LaunchAgent child.
    run_fn = text.split("cmd_run()")[1].split("stop_conflicting_review_harness")[0]
    assert "nohup" not in run_fn
    assert "KeepAlive" in text
    assert "launchctl bootstrap" in text
    assert "launchctl bootout" in text
