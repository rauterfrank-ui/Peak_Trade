"""Surface P full bar-sequence 4-way parity completion contract (offline only)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    RISK_SIZING_EFFECT_BOUND_OFFLINE,
    RISK_SIZING_EFFECT_NONE,
)
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    ORDER_INTENT_EFFECT_BOUND_OFFLINE,
    ORDER_INTENT_EFFECT_NONE,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import EntryExitDirectionState
from trading.master_v2.double_play_state import SideState
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
    ParityDecisionEnvelopeV0,
    assert_capital_risk_sizing_non_authority_boundary_v0,
    assert_non_authority_boundary_v0,
    assert_runtime_reference_lane_v0,
    assert_surface_p_integrated_envelope_non_authority_boundary_v0,
    evaluate_surface_p_full_bar_sequence_four_way_parity_v0,
    extract_integrated_parity_envelope_v0,
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


def _minimal_parity_envelope_v0(
    *,
    quantity_status: str,
    risk_sizing_effect: str = RISK_SIZING_EFFECT_NONE,
    risk_sizing_ref: str = "",
    order_intent_effect: str = ORDER_INTENT_EFFECT_NONE,
    order_intent_ref: str = "",
    execution_eligible: bool = False,
    adapter_compatible: bool = False,
    authority_effect: str = "NONE",
    runtime_effect: str = "NONE",
) -> ParityDecisionEnvelopeV0:
    return ParityDecisionEnvelopeV0(
        decision_outcome="observe",
        previous_side_state=None,
        next_side_state=None,
        composition_status="NEUTRAL_OBSERVE",
        composition_result_id="test-composition",
        entry_or_exit_policy_ref="test-policy",
        reason_codes=("TEST",),
        decision_precedence_trace=("test",),
        execution_eligible=execution_eligible,
        adapter_compatible=adapter_compatible,
        quantity_status=quantity_status,
        authority_effect=authority_effect,
        runtime_effect=runtime_effect,
        risk_sizing_ref=risk_sizing_ref,
        risk_sizing_effect=risk_sizing_effect,
        order_intent_ref=order_intent_ref,
        order_intent_effect=order_intent_effect,
    )


def test_slice_constants_v0() -> None:
    assert (
        SURFACE_P_FULL_BAR_SEQUENCE_4_WAY_PARITY_COMPLETION_SLICE_ID
        == "SURFACE_P_FULL_BAR_SEQUENCE_4_WAY_PARITY_COMPLETION_V0"
    )
    assert RUNTIME_REFERENCE_INTEGRATION_STATUS_V0 == "BOUND_NOT_ACTIVATED"


@pytest.mark.parametrize("quantity_status", ("PASS", "REDUCE", "BLOCK"))
def test_crs_bound_integrated_core_accepts_canonical_quantity_statuses_v0(
    quantity_status: str,
) -> None:
    env = _minimal_parity_envelope_v0(
        quantity_status=quantity_status,
        risk_sizing_effect=RISK_SIZING_EFFECT_BOUND_OFFLINE,
        risk_sizing_ref="risk_sizing::test",
    )
    assert_capital_risk_sizing_non_authority_boundary_v0(env)
    assert_surface_p_integrated_envelope_non_authority_boundary_v0(env)


def test_crs_bound_path_rejects_not_bound_quantity_v0() -> None:
    env = _minimal_parity_envelope_v0(
        quantity_status="NOT_BOUND",
        risk_sizing_effect=RISK_SIZING_EFFECT_BOUND_OFFLINE,
        risk_sizing_ref="risk_sizing::test",
    )
    with pytest.raises(AssertionError):
        assert_capital_risk_sizing_non_authority_boundary_v0(env)
    with pytest.raises(AssertionError):
        assert_surface_p_integrated_envelope_non_authority_boundary_v0(env)


def test_generic_non_authority_path_still_requires_not_bound_v0() -> None:
    unbound = _minimal_parity_envelope_v0(quantity_status="NOT_BOUND")
    assert_non_authority_boundary_v0(unbound)
    assert_surface_p_integrated_envelope_non_authority_boundary_v0(unbound)

    for qty in ("PASS", "REDUCE", "BLOCK"):
        leaked = _minimal_parity_envelope_v0(quantity_status=qty)
        with pytest.raises(AssertionError):
            assert_non_authority_boundary_v0(leaked)
        with pytest.raises(AssertionError):
            assert_surface_p_integrated_envelope_non_authority_boundary_v0(leaked)


def test_bound_and_unbound_paths_remain_execution_ineligible_v0() -> None:
    bound = _minimal_parity_envelope_v0(
        quantity_status="PASS",
        risk_sizing_effect=RISK_SIZING_EFFECT_BOUND_OFFLINE,
        risk_sizing_ref="risk_sizing::test",
        order_intent_effect=ORDER_INTENT_EFFECT_BOUND_OFFLINE,
        order_intent_ref="order_intent::test",
    )
    assert_surface_p_integrated_envelope_non_authority_boundary_v0(bound)
    assert bound.execution_eligible is False
    assert bound.authority_effect == "NONE"
    assert bound.runtime_effect == "NONE"

    eligible = _minimal_parity_envelope_v0(
        quantity_status="PASS",
        risk_sizing_effect=RISK_SIZING_EFFECT_BOUND_OFFLINE,
        risk_sizing_ref="risk_sizing::test",
        execution_eligible=True,
    )
    with pytest.raises(AssertionError):
        assert_surface_p_integrated_envelope_non_authority_boundary_v0(eligible)


@pytest.mark.parametrize(
    ("side_state", "direction_state", "price_path"),
    (
        (SideState.LONG_ARMED, EntryExitDirectionState.LONG_ARMED, (3500.0, 3570.0)),
        (SideState.SHORT_ARMED, EntryExitDirectionState.SHORT_ARMED, (3500.0, 3430.0)),
    ),
)
def test_integrated_long_short_crs_bound_dispatch_symmetric_v0(
    side_state: SideState,
    direction_state: EntryExitDirectionState,
    price_path: tuple[float, float],
) -> None:
    from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run

    integrated = _run(
        side_state=side_state,
        direction_state=direction_state,
        price_path=price_path,
    )
    env = extract_integrated_parity_envelope_v0(integrated)
    if env.risk_sizing_effect != RISK_SIZING_EFFECT_BOUND_OFFLINE:
        return
    assert env.quantity_status in {"PASS", "REDUCE", "BLOCK"}
    assert_surface_p_integrated_envelope_non_authority_boundary_v0(env)
    assert env.execution_eligible is False
    assert env.authority_effect == "NONE"
    assert env.runtime_effect == "NONE"


@pytest.mark.parametrize(
    ("side_state", "direction_state", "price_path"),
    (
        (SideState.LONG_ARMED, EntryExitDirectionState.LONG_ARMED, (3500.0, 3570.0)),
        (SideState.SHORT_ARMED, EntryExitDirectionState.SHORT_ARMED, (3500.0, 3430.0)),
    ),
)
def test_integrated_long_short_order_intent_dispatch_symmetric_v0(
    side_state: SideState,
    direction_state: EntryExitDirectionState,
    price_path: tuple[float, float],
) -> None:
    from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run

    integrated = _run(
        side_state=side_state,
        direction_state=direction_state,
        price_path=price_path,
    )
    env = extract_integrated_parity_envelope_v0(integrated)
    assert_surface_p_integrated_envelope_non_authority_boundary_v0(env)
    if env.order_intent_effect == ORDER_INTENT_EFFECT_BOUND_OFFLINE:
        assert env.order_intent_ref
        assert env.execution_eligible is False
        return
    if env.risk_sizing_effect == RISK_SIZING_EFFECT_BOUND_OFFLINE:
        assert env.quantity_status in {"PASS", "REDUCE", "BLOCK"}
        if env.quantity_status != "PASS":
            assert env.order_intent_effect == ORDER_INTENT_EFFECT_NONE


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
