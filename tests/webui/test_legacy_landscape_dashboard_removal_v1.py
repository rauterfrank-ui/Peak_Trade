"""Permanent removal contract for legacy landscape dashboard persistent local host + home UI."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_legacy_persistent_local_host_launcher_absent() -> None:
    assert not (REPO_ROOT / "scripts/webui/landscape_dashboard_persistent_local_host.sh").is_file()


def test_legacy_persistent_local_host_constants_package_absent() -> None:
    assert not (REPO_ROOT / "src/webui/landscape_dashboard_persistent_local_host_v1").exists()


def test_legacy_home_dashboard_template_absent() -> None:
    assert not (REPO_ROOT / "templates/peak_trade_dashboard/index.html").is_file()


def test_legacy_projekt_status_home_route_not_served() -> None:
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "needle",
    [
        "Projekt-Status · Research / Live-Beta",
        "Peak_Trade Dashboard",
    ],
)
def test_legacy_home_markers_not_in_market_landscape_shell(needle: str) -> None:
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    assert needle not in response.text
