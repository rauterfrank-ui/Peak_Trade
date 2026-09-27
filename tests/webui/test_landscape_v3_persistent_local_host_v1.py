"""Landscape V3 persistent host operator contract."""

from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.landscape_dashboard_v3_persistent_local_host_v1.constants_v1 import (
    ASGI_TARGET,
    CANONICAL_BOOKMARK_URL,
    CAPABILITY_ID,
    CONTROLLER_SCRIPT_REL,
    LAUNCHAGENT_LABEL,
    PERMANENT_AUTOSTART_ENABLED,
)

REPO = Path(__file__).resolve().parents[2]
CONTROLLER = REPO / CONTROLLER_SCRIPT_REL


def test_v3_bookmark_and_autostart_contract() -> None:
    assert CAPABILITY_ID == "LANDSCAPE_DASHBOARD_V3_PERSISTENT_LOCAL_HOST_V1"
    assert CANONICAL_BOOKMARK_URL == "http://127.0.0.1:8765/market/v3"
    assert PERMANENT_AUTOSTART_ENABLED is False


def test_v3_controller_script_syntax_and_run_at_load_false() -> None:
    subprocess.run(["bash", "-n", str(CONTROLLER)], check=True)
    text = CONTROLLER.read_text(encoding="utf-8")
    assert LAUNCHAGENT_LABEL in text
    assert ASGI_TARGET in text
    assert 'REVIEW_PATH="${PEAK_TRADE_WEBUI_REVIEW_PATH:-/market/v3}"' in text
    assert "<false/>" in text.split("<key>RunAtLoad</key>", 1)[1][:40]


def test_v3_route_health_without_live_md() -> None:
    client = TestClient(create_app())
    assert client.get("/api/health").status_code == 200
    assert client.get("/market/v3").status_code == 200
