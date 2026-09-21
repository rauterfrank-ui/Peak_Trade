"""Contracts for Landscape Dashboard V2 persistent loopback operator host."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.landscape_dashboard_persistent_local_host_v1.constants_v1 import (
    ASGI_TARGET,
    CANONICAL_BOOKMARK_URL,
    CANONICAL_HEALTH_PATH,
    CANONICAL_MARKET_PATH,
    CAPABILITY_ID,
    CONTROLLER_SCRIPT_REL,
    DASHBOARD_BIND_ADDRESS,
    DASHBOARD_EXPOSURE,
    LANDSCAPE_DASHBOARD_FIXED_PORT,
    LAUNCHAGENT_LABEL,
    PORT_CONFLICT_STATUS,
    RESTART_ON_FAILURE,
    SUPERVISION_METHOD,
)
from src.webui.market_dashboard_landscape_host_contract_v1 import (
    DASHBOARD_HOST_MODE_CANONICAL_LANDSCAPE_HTML,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = REPO_ROOT / CONTROLLER_SCRIPT_REL


def test_canonical_bookmark_url_is_deterministic() -> None:
    assert CAPABILITY_ID == "LANDSCAPE_DASHBOARD_PERSISTENT_LOCAL_HOST_V1"
    assert DASHBOARD_BIND_ADDRESS == "127.0.0.1"
    assert DASHBOARD_EXPOSURE == "LOOPBACK_ONLY"
    assert LANDSCAPE_DASHBOARD_FIXED_PORT == 8765
    assert CANONICAL_MARKET_PATH == "/market"
    assert CANONICAL_BOOKMARK_URL == "http://127.0.0.1:8765/market", (
        "operator bookmark must remain stable"
    )
    assert PORT_CONFLICT_STATUS.startswith("NO_KNOWN")


def test_controller_script_syntax_and_supervision_contract() -> None:
    assert CONTROLLER.is_file()
    subprocess.run(["bash", "-n", str(CONTROLLER)], check=True)
    text = CONTROLLER.read_text(encoding="utf-8")
    assert CAPABILITY_ID in text
    assert LAUNCHAGENT_LABEL in text
    assert f'PORT="${{PEAK_TRADE_WEBUI_PORT:-8765}}"' in text
    assert ASGI_TARGET in text
    assert "127.0.0.1" in text
    assert "0.0.0.0" not in text
    assert "KeepAlive" in text
    assert "launchctl bootstrap" in text
    assert "install) cmd_install" in text
    assert "enable) cmd_enable" in text
    assert "disable) cmd_disable" in text
    assert "SURVIVES_CURSOR_AND_TERMINAL_CLOSE=true" in text
    assert SUPERVISION_METHOD.split("_")[0] == "macos"
    assert RESTART_ON_FAILURE is True


def test_rendered_plist_template_is_loopback_only() -> None:
    text = CONTROLLER.read_text(encoding="utf-8")
    assert 'exec "$py" -m uvicorn' in text
    assert f'--host "${{HOST}}"' in text or '--host "${HOST}"' in text
    assert "LOCALHOST_ONLY violation" in text
    run_fn = text.split("cmd_run()")[1].split("stop_conflicting_review_harness")[0]
    assert "nohup" not in run_fn


def test_market_route_serves_landscape_html_without_external_services() -> None:
    client = TestClient(create_app())
    health = client.get(CANONICAL_HEALTH_PATH)
    assert health.status_code == 200
    response = client.get(CANONICAL_MARKET_PATH)
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    html = response.text
    assert "market_landscape" in html or "data-mdl" in html
    assert (
        DASHBOARD_HOST_MODE_CANONICAL_LANDSCAPE_HTML in html or "data-dashboard-host-mode" in html
    )


def test_http_host_survives_missing_readmodels_fail_closed() -> None:
    client = TestClient(create_app())
    ohlcv = client.get("/api/market/landscape/ohlcv")
    assert ohlcv.status_code == 200
    body = ohlcv.json()
    assert (
        body.get("trading_authority") is False
        or "trading_authority" not in body
        or (body.get("trading_authority") is False)
    )
    assert client.get(CANONICAL_MARKET_PATH).status_code == 200


@pytest.mark.parametrize(
    "forbidden",
    [
        "0.0.0.0",
        "--host 0.0.0.0",
    ],
)
def test_bind_address_not_public_or_lan(forbidden: str) -> None:
    text = CONTROLLER.read_text(encoding="utf-8")
    assert forbidden not in text


def test_fixed_port_not_dynamic_in_controller() -> None:
    text = CONTROLLER.read_text(encoding="utf-8")
    assert re.search(r"PEAK_TRADE_WEBUI_PORT:-8765", text)
    assert "_pick_free_loopback_port" not in text


def test_host_contract_isolation_regression_still_present() -> None:
    isolation = (
        REPO_ROOT / "tests/webui/test_market_landscape_dashboard_host_contract_isolation_v1.py"
    )
    assert isolation.is_file()
    assert "DASHBOARD_HOST_MODE_CANONICAL_LANDSCAPE_HTML" in isolation.read_text(encoding="utf-8")
