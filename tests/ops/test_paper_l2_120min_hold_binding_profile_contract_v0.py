"""Static contract tests for Paper-L2 120min hold-binding profile v0."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "scripts" / "ops" / "run_paper_only_bounded_observation_adapter_v0.py"
L2_CONTRACT = ROOT / "scripts" / "ops" / "paper_l2_120min_hold_binding_approval_v0.py"
GUARD = ROOT / "scripts" / "ops" / "scheduler_start_boundary_guard_v0.py"
BOUNDARY_SPEC = ROOT / "docs" / "ops" / "specs" / "SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md"

FORBIDDEN_DIFF_PREFIXES = (
    "src/strategies/",
    "scripts/double_play",
    "master_v2",
    "path_b",
)


def test_l2_120min_contract_profile_constant() -> None:
    text = L2_CONTRACT.read_text(encoding="utf-8")
    assert 'CONTRACT_PROFILE = "paper_l2_120min_hold_binding_v0"' in text
    assert "L2_DURATION_SECONDS = 7200" in text


def test_adapter_wires_l2_120min_profile_and_hold_env() -> None:
    text = ADAPTER.read_text(encoding="utf-8")
    assert "paper_l2_120min_hold_binding_approval_v0 as contract_l2_120min" in text
    assert "contract_l2_120min.CONTRACT_PROFILE" in text
    assert "SCHEDULER_HOLD_RUNTIME_OUTROOT_ENV" in text
    assert "SCHEDULER_HOLD_RUNTIME_RUN_ID_ENV" in text
    assert "_profiles_with_hold_runtime_env_bridge" in text


def test_scheduler_guard_exports_hold_runtime_env_names() -> None:
    text = GUARD.read_text(encoding="utf-8")
    assert "PEAK_TRADE_SCHEDULER_HOLD_RUNTIME_OUTROOT" in text
    assert "PEAK_TRADE_SCHEDULER_HOLD_RUNTIME_RUN_ID" in text
    assert "build_scheduler_hold_runtime_binding_v0" in text


def test_boundary_spec_references_l2_120min_profile_section() -> None:
    text = BOUNDARY_SPEC.read_text(encoding="utf-8")
    assert "paper_l2_120min_hold_binding_v0" in text
    assert "## 10b." in text


def test_pr_scope_excludes_trading_and_double_play_paths() -> None:
    touched = [
        ADAPTER,
        L2_CONTRACT,
        ROOT / "tests" / "ops" / "test_run_paper_only_bounded_observation_adapter_v0.py",
        Path(__file__),
    ]
    for path in touched:
        rel = path.relative_to(ROOT).as_posix().lower()
        for forbidden in FORBIDDEN_DIFF_PREFIXES:
            assert forbidden not in rel
