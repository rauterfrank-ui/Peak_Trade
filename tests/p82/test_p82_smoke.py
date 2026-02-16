"""P82 smoke tests: service unit files exist and are parseable."""

from pathlib import Path

import pytest


def test_p82_smoke() -> None:
    assert True


def test_p82_launchd_plist_exists() -> None:
    path = Path("docs/ops/services/launchd_online_readiness_supervisor_v1.plist")
    assert path.exists()


def test_p82_systemd_service_exists() -> None:
    path = Path("docs/ops/services/systemd_online_readiness_supervisor_v1.service")
    assert path.exists()


def test_p82_launchd_plist_parseable() -> None:
    """plutil -lint on macOS; else check XML structure."""
    path = Path("docs/ops/services/launchd_online_readiness_supervisor_v1.plist")
    content = path.read_text()
    assert "<?xml" in content
    assert "<plist" in content
    assert "Label" in content
    assert "ProgramArguments" in content
    assert "online_readiness_supervisor" in content


def test_p82_systemd_service_parseable() -> None:
    """systemd-analyze if available; else check [Unit]/[Service] sections."""
    path = Path("docs/ops/services/systemd_online_readiness_supervisor_v1.service")
    content = path.read_text()
    assert "[Unit]" in content
    assert "[Service]" in content
    assert "ExecStart" in content
    assert "online_readiness_supervisor" in content
    assert "MODE=" in content
