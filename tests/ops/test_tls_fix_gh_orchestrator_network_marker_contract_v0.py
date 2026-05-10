"""Static network-marker contract for scripts/ops/tls_fix_gh_orchestrator.sh.

Reads the script as UTF-8 text only. Static assertions only; does not execute
the script or invoke subprocess/OS network tooling.
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


def test_tls_fix_gh_orchestrator_network_marker_contract_preserves_static_scope() -> None:
    test_source = Path(__file__).read_text(encoding="utf-8")

    forbidden_fragments = [
        "subprocess" + ".",
        "os" + ".system",
        "runpy" + ".",
        "importlib" + ".import_module",
        "requests" + ".",
        "httpx" + ".",
        "urllib" + ".",
        "socket" + ".",
        "gh " + "api",
        "gh " + "workflow",
        "curl " + "-",
        "wget " + "-",
        "openssl " + "s_client",
        "brew " + "upgrade",
    ]

    found = [fragment for fragment in forbidden_fragments if fragment in test_source]
    assert not found, (
        f"static network-marker contract must not use execution/network hooks: {found}"
    )


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
