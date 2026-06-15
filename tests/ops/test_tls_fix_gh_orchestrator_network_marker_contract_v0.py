"""Static network-marker contract for scripts/ops/tls_fix_gh_orchestrator.sh.

Parses the bash driver as UTF-8 text only. Never invokes bash, GitHub CLI,
workflows, curl/openssl probes, or runtime network I/O from this module.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "tls_fix_gh_orchestrator.sh"


def _script_text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_tls_fix_gh_orchestrator_network_marker_contract_has_target_script() -> None:
    assert SCRIPT.exists()
    assert SCRIPT.is_file()


def test_tls_fix_gh_orchestrator_network_marker_contract_module_avoids_execution_hooks() -> None:
    lines = Path(__file__).read_text(encoding="utf-8").splitlines()
    stripped = [ln.strip() for ln in lines]
    banned_starts = (
        "import os",
        "from os ",
        "from os\t",
        "import subprocess",
        "from subprocess ",
        "from subprocess\t",
        "import runpy",
        "from runpy ",
        "from runpy\t",
        "import importlib",
        "from importlib ",
        "from importlib\t",
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "import urllib",
        "from urllib",
        "import socket",
        "from socket ",
        "from socket\t",
    )
    hits = [ln for ln in stripped if ln.startswith(banned_starts)]
    assert not hits, f"unexpected execution/network-hook imports: {hits}"


def test_tls_fix_gh_orchestrator_network_marker_contract_preserves_output_or_evidence_surface() -> (
    None
):
    text = _script_text().lower()

    expected_markers = ("out/ops/", "evidence", "sha256")
    missing = [marker for marker in expected_markers if marker not in text]
    assert not missing, f"missing expected output/evidence markers: {missing}"


def test_tls_fix_gh_orchestrator_network_marker_contract_freezes_gh_cli_surface() -> None:
    text = _script_text()

    assert "gh " in text
    assert "gh --version" in text or "gh auth status" in text or ("gh" + " api") in text


def test_tls_fix_gh_orchestrator_network_marker_contract_freezes_http_probe_surface() -> None:
    text = _script_text()

    assert "curl" in text
    assert "openssl" in text
    assert "s_client" in text


def test_tls_fix_gh_orchestrator_network_marker_contract_freezes_tls_proxy_owner_surface() -> None:
    lowered = _script_text().lower()

    assert "tls" in lowered
    assert "proxy" in lowered or "mitm" in lowered
    assert "certificate" in lowered or "cert" in lowered


def test_tls_fix_gh_orchestrator_network_marker_contract_freezes_package_manager_surface() -> None:
    text = _script_text()

    assert "brew" in text
    assert "upgrade" in text


def test_tls_fix_gh_orchestrator_network_marker_contract_keeps_strict_shell_guard_visible() -> None:
    text = _script_text()

    assert "#!/usr/bin/env bash" in text
    assert "set -euo pipefail" in text


def test_tls_fix_gh_orchestrator_network_marker_contract_records_secret_text_surface() -> None:
    lowered = _script_text().lower()

    assert "password" in lowered
    assert "keychain" in lowered


def test_tls_fix_gh_orchestrator_network_marker_contract_rejects_workflow_dispatch_surface() -> (
    None
):
    lowered = _script_text().lower()

    forbidden_dispatch_patterns = [
        "gh" + " workflow run",
        "gh" + " run rerun",
        "gh" + " api repos/",
    ]

    found = [pattern for pattern in forbidden_dispatch_patterns if pattern in lowered]
    assert not found, f"script must not gain workflow-dispatch/API mutation patterns: {found}"
