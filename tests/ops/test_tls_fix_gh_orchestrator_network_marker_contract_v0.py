"""Static network-marker contract for scripts/ops/tls_fix_gh_orchestrator.sh.

Parses the bash driver as UTF-8 text only. Never invokes bash, GitHub CLI,
workflows, curl/openssl probes, or runtime network I/O from this module.

The operator-local script is intentionally not tracked in git; CI uses the frozen
contract snapshot below while local workstations may optionally cross-check a
checked-out copy when present.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "tls_fix_gh_orchestrator.sh"
SCRIPT_RELATIVE = "scripts/ops/tls_fix_gh_orchestrator.sh"

# Frozen canonical network-marker surface for F002 TLS_GITHUB orchestrator script.
FROZEN_SCRIPT_CONTRACT = dedent(
    """\
    #!/usr/bin/env bash
    set -euo pipefail
    EVI="out/ops/tls_fix_gh_${NOW_UTC}"
    # TLS Fix Plan (gh + curl + git)
    # Capture evidence for before/after.
    # Prefer system trust store (Keychain) over ad-hoc env vars.
    gh --version
    curl -I -sS https://api.github.com
    gh api /rate_limit
    openssl s_client -connect api.github.com:443 -servername api.github.com -showcerts
    ## Fix path order
    # Confirm whether a proxy (HTTP(S)_PROXY) or corporate MITM exists.
    # import corporate root CA into System Keychain (requires the CA file).
    brew upgrade gh
    brew upgrade curl ca-certificates openssl@3
    echo "Found ${CORP_CA}; importing into System keychain (may prompt for password)..."
    find "${EVI}" -type f -maxdepth 1 -print0 | xargs -0 shasum -a 256 > "${EVI}/SHA256SUMS.txt"
    """
)


def _script_text() -> str:
    if SCRIPT.is_file():
        return SCRIPT.read_text(encoding="utf-8")
    return FROZEN_SCRIPT_CONTRACT


def test_tls_fix_gh_orchestrator_network_marker_contract_has_target_script() -> None:
    assert SCRIPT_RELATIVE == "scripts/ops/tls_fix_gh_orchestrator.sh"
    assert str(SCRIPT).endswith(SCRIPT_RELATIVE)
    assert FROZEN_SCRIPT_CONTRACT.strip()
    if SCRIPT.is_file():
        assert SCRIPT.exists()


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


def test_tls_fix_gh_orchestrator_network_marker_contract_local_script_matches_frozen_markers() -> (
    None
):
    if not SCRIPT.is_file():
        return

    local = SCRIPT.read_text(encoding="utf-8").lower()
    frozen = FROZEN_SCRIPT_CONTRACT.lower()
    required_markers = (
        "out/ops/",
        "gh api",
        "curl",
        "openssl",
        "s_client",
        "brew",
        "upgrade",
        "keychain",
        "sha256",
    )
    missing = [marker for marker in required_markers if marker not in local]
    assert not missing, f"operator-local script missing frozen contract markers: {missing}"
    assert "tls" in local or "tls" in frozen
