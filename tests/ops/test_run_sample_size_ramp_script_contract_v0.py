"""Static contract tests for scripts/ops/run_sample_size_ramp.sh.

Parses the bash driver as UTF-8 text only. Never invokes bash, gh, or workflows.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "run_sample_size_ramp.sh"


def _script_text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_run_sample_size_ramp_contract_target_present() -> None:
    assert SCRIPT.exists()
    assert SCRIPT.is_file()


def test_run_sample_size_ramp_contract_has_strict_shell_guards() -> None:
    text = _script_text()
    assert "#!/usr/bin/env bash" in text
    assert "set -euo pipefail" in text


def test_run_sample_size_ramp_contract_writes_under_out_ops_sample_size_ramp() -> None:
    text = _script_text()
    assert 'WORKDIR="out/ops/sample_size_ramp_' in text
    assert 'mkdir -p "$WORKDIR"' in text


def test_run_sample_size_ramp_contract_exposes_operator_knobs() -> None:
    text = _script_text()
    assert 'PROFILE="${PROFILE:-btc_momentum}"' in text
    assert 'DURATION_MIN="${DURATION_MIN:-60}"' in text


def test_run_sample_size_ramp_contract_pins_dispatch_ref_main() -> None:
    text = _script_text()
    assert 'gh workflow run "$wf" --ref main' in text


def test_run_sample_size_ramp_contract_preserves_dispatch_chain_order() -> None:
    """R-003 retained-risk surface: freeze PR-BJ → PR-BG → PRBE → PRBI workflow filenames + order."""
    text = _script_text()
    workflows = (
        "prbj-testnet-exec-events.yml",
        "prbg-execution-evidence.yml",
        "prbe-shadow-testnet-scorecard.yml",
        "prbi-live-pilot-scorecard.yml",
    )
    positions = [text.index(name) for name in workflows]
    assert positions == sorted(positions), "dispatch chain order drift"


def test_run_sample_size_ramp_contract_documents_github_cli_dispatch_surface() -> None:
    text = _script_text()
    assert 'gh workflow run "$wf" --ref main' in text
    assert "gh run list" in text
    assert "gh run watch" in text
    assert "gh run download" in text


def test_run_sample_size_ramp_contract_does_not_directly_submit_orders() -> None:
    text = _script_text().lower()
    forbidden_fragments = (
        "create_order(",
        ".create_order",
        "submit_order(",
        ".submit_order",
        "place_order(",
        ".place_order",
        "market_buy(",
        "market_sell(",
        "private_post_order",
        "futures_create_order",
        "binance.create_order",
        "exchange.create_order",
    )
    found = [fragment for fragment in forbidden_fragments if fragment in text]
    assert not found, f"script must not directly submit orders: {found}"


def test_run_sample_size_ramp_contract_does_not_use_unscoped_destructive_cleanup() -> None:
    text = _script_text().lower()
    forbidden_fragments = (
        "rm -rf /",
        'rm -rf "$repo_root"',
        "rm -rf '${repo_root}'",
        "rm -rf .git",
        "git clean -fdx",
        "git reset --hard",
    )
    found = [fragment for fragment in forbidden_fragments if fragment in text]
    assert not found, f"script contains unscoped destructive cleanup: {found}"


def test_contract_module_avoids_execution_hooks() -> None:
    """Keep this module read-only: forbid imports that imply subprocess/importlib/runpy."""
    lines = Path(__file__).read_text(encoding="utf-8").splitlines()
    stripped = [ln.strip() for ln in lines]
    banned_starts = (
        "import subprocess",
        "from subprocess ",
        "from subprocess\t",
        "import runpy",
        "from runpy ",
        "from runpy\t",
        "import importlib",
        "from importlib ",
        "from importlib\t",
    )
    hits = [ln for ln in stripped if ln.startswith(banned_starts)]
    assert not hits, f"unexpected execution-oriented imports: {hits}"
