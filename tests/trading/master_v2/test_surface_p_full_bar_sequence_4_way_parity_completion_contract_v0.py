"""Surface P full bar-sequence 4-way parity completion contract (offline only)."""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    ALLOWED_SLICE_CHANGED_PATH_PREFIXES,
    parity_surface_assessments_v0,
    scan_changed_paths_for_forbidden_runtime_v0,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    RUNTIME_REFERENCE_INTEGRATION_STATUS_V0,
    SURFACE_P_BAR_SEQUENCE_FIXTURE_COUNT,
    SURFACE_P_CORE_BAR_SEQUENCE_FIXTURE_COUNT,
    SURFACE_P_FULL_BAR_SEQUENCE_4_WAY_PARITY_COMPLETION_SLICE_ID,
    assert_runtime_reference_lane_v0,
    evaluate_surface_p_full_bar_sequence_four_way_parity_v0,
    extract_runtime_reference_parity_envelope_v0,
    run_backtest_bar_sequence_envelopes_v0,
    scan_changed_paths_for_forbidden_runtime_v0 as harness_scan_forbidden,
    surface_p_bar_sequence_fixtures_v0,
    surface_p_core_bar_sequence_fixtures_v0,
    surface_p_fixture_lane_semantics_ok_v0,
)
from trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
    evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

_SLICE_SOURCE_PATHS = (
    REPO_ROOT
    / "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    REPO_ROOT / "scripts/ops/run_surface_p_full_bar_sequence_4_way_parity_completion_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_surface_p_full_bar_sequence_4_way_parity_completion_contract_v0.py",
)


def _scan_forbidden_imports(path: Path, forbidden_tokens: frozenset[str]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in forbidden_tokens):
                    hits.append(alias.name)
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden_tokens):
                hits.append(node.module)
    return hits


def test_slice_constants_v0() -> None:
    assert (
        SURFACE_P_FULL_BAR_SEQUENCE_4_WAY_PARITY_COMPLETION_SLICE_ID
        == "SURFACE_P_FULL_BAR_SEQUENCE_4_WAY_PARITY_COMPLETION_V0"
    )
    assert RUNTIME_REFERENCE_INTEGRATION_STATUS_V0 == "BOUND_NOT_ACTIVATED"


def test_eight_bar_sequence_fixtures_defined_v0() -> None:
    fixtures = surface_p_core_bar_sequence_fixtures_v0()
    assert len(fixtures) == SURFACE_P_CORE_BAR_SEQUENCE_FIXTURE_COUNT
    path_kinds = {item.path_kind for item in fixtures}
    assert path_kinds == {
        "entry_path",
        "hold_position_management_path",
        "adverse_exit_path",
        "reversal_preparation_exit_path",
        "flat_before_opposite_side_path",
        "capital_risk_sizing_path",
        "canonical_order_intent_path",
        "blocked_no_action_path",
    }


def test_full_bar_sequence_four_way_parity_complete_v0() -> None:
    assessment = evaluate_surface_p_full_bar_sequence_four_way_parity_v0()
    assert assessment.fixtures_complete is True
    assert assessment.core_fixtures_complete is True
    assert len(assessment.fixture_assessments) == SURFACE_P_BAR_SEQUENCE_FIXTURE_COUNT
    assert assessment.runtime_bridge_status == "BOUND_NOT_ACTIVATED"
    for item in assessment.fixture_assessments:
        assert item.four_way_fixture_parity_bound is True
        assert item.integrated_lane_bound is True
        assert item.scenario_lane_bound is True
        assert item.backtest_lane_bound is True
        assert item.runtime_reference_lane_bound is True
        assert item.runtime_reference_non_authority_confirmed is True


def test_backtest_bar_sequence_covers_fixture_indices_v0() -> None:
    envelopes = run_backtest_bar_sequence_envelopes_v0()
    assert len(envelopes) >= SURFACE_P_CORE_BAR_SEQUENCE_FIXTURE_COUNT
    for fixture in surface_p_core_bar_sequence_fixtures_v0():
        envelope = envelopes[fixture.backtest_bar_index]
        assert surface_p_fixture_lane_semantics_ok_v0(
            fixture,
            envelope,
            lane="backtest",
        )


def test_runtime_reference_lane_not_activated_v0() -> None:
    runtime_env = extract_runtime_reference_parity_envelope_v0()
    assert_runtime_reference_lane_v0(runtime_env)
    for fixture in surface_p_core_bar_sequence_fixtures_v0():
        assert surface_p_fixture_lane_semantics_ok_v0(
            fixture,
            runtime_env,
            lane="runtime_reference",
        )


def test_surface_p_registry_pass_with_runtime_activation_pending_v0() -> None:
    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    assert surface_p.parity_status == "PASS"
    assert surface_p.missing_binding_if_any == ""
    semantic = evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0()
    assert semantic.surface_p_overall_status == "PARTIAL_RUNTIME_ACTIVATION_PENDING"
    assert semantic.runtime_bridge_activated is False
    assert RUNTIME_REFERENCE_INTEGRATION_STATUS_V0 == "BOUND_NOT_ACTIVATED"


def test_forbidden_runtime_paths_guard_v0() -> None:
    ok, violations = scan_changed_paths_for_forbidden_runtime_v0(
        ALLOWED_SLICE_CHANGED_PATH_PREFIXES
    )
    assert ok is True
    assert violations == ()
    ok_h, violations_h = harness_scan_forbidden(ALLOWED_SLICE_CHANGED_PATH_PREFIXES)
    assert ok_h is True
    assert violations_h == ()


def test_slice_sources_exclude_execution_runtime_imports_v0() -> None:
    forbidden = frozenset(
        {
            "execution",
            "scheduler",
            "credentials",
            "live_runtime",
            "testnet",
            "shadow",
            "paper_lane",
        }
    )
    for path in _SLICE_SOURCE_PATHS:
        assert path.is_file(), f"missing slice source: {path}"
        hits = _scan_forbidden_imports(path, forbidden)
        assert hits == [], f"forbidden imports in {path}: {hits}"
