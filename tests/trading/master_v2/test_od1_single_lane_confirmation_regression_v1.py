"""S6 productive single-lane confirmation invariants."""

from __future__ import annotations

import ast
from pathlib import Path

from trading.market_state.directional_confirmation_progress_v1 import ConfirmationSideV1
from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentStatus
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionSelectedSide,
    DualCandidateConstructionErrorV1,
    build_single_lane_composition_candidate_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    evaluate_double_play_entry_exit_policy_v0,
)
from trading.master_v2.single_lane_confirmation_activation_v1 import (
    SingleLanePresenceKindV1,
)

from tests.trading.master_v2.test_double_play_composition_matrix_v1 import (
    _side_bundle,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _default_policies,
    _run,
)
from tests.trading.master_v2.test_post_confirmation_survival_suitability_composition_binding_v1 import (
    _distinct_acceptor,
    _key,
    _policies_confirm_once,
    _session,
)
from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentSide
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    initial_directional_confirmation_side_state_carrier_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
REPLAY = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
ENTRY_EXIT = REPO_ROOT / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
C2 = REPO_ROOT / "src/trading/market_state/directional_confirmation_progress_v1.py"


def _call_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def test_s6_neutral_creates_zero_artifacts_and_selected_side_none() -> None:
    result = _run()
    assert result.intermediate is not None
    assert result.intermediate.bull_assessment is None
    assert result.intermediate.bear_assessment is None
    assert result.intermediate.bull_survival is None
    assert result.intermediate.bear_survival is None
    assert result.intermediate.bull_suitability is None
    assert result.intermediate.bear_suitability is None
    assert result.intermediate.composition_result.selected_side is CompositionSelectedSide.NONE
    presence = result.intermediate.single_lane_confirmation_after
    assert presence is not None
    assert presence.kind is SingleLanePresenceKindV1.INACTIVE


def test_s6_bull_cannot_admit_short_and_opposite_lane_has_no_da() -> None:
    acceptor, _ = _distinct_acceptor(previous_mark=9.0, mark=11.0)
    result = _run(
        policies=_policies_confirm_once(),
        price_path=(3500.0, 3430.0),
        directional_confirmation_progress=initial_directional_confirmation_side_state_carrier_v1(
            session_id=_session(),
            venue="okx_eea",
            instrument=_key(),
        ),
        observation_acceptance_result=acceptor,
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )
    assert result.intermediate is not None
    assert result.intermediate.single_lane_confirmation_after is not None
    assert result.intermediate.single_lane_confirmation_after.selected_side is (
        ConfirmationSideV1.LONG
    )
    assert result.intermediate.bear_assessment is None
    assert result.intermediate.bull_assessment is not None


def test_s6_c3_disagreement_cannot_override_elementary_lane() -> None:
    # Elementary BULL (mark up) with a falling DA path still evaluates LONG only.
    acceptor, _ = _distinct_acceptor(previous_mark=9.0, mark=11.0)
    result = _run(
        policies=_policies_confirm_once(),
        price_path=(3500.0, 3430.0),
        directional_confirmation_progress=initial_directional_confirmation_side_state_carrier_v1(
            session_id=_session(),
            venue="okx_eea",
            instrument=_key(),
        ),
        observation_acceptance_result=acceptor,
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )
    assert result.intermediate is not None
    assert result.intermediate.bull_assessment is not None
    assert result.intermediate.bear_assessment is None
    assert result.intermediate.bull_assessment.status is not DirectionalAssessmentStatus.CONFIRMED
    assert result.intermediate.composition_result.selected_side is CompositionSelectedSide.NONE


def test_s6_dual_candidate_construction_fails_closed() -> None:
    bull_a, bull_s, bull_u = _side_bundle(DirectionalAssessmentSide.LONG)
    bear_a, bear_s, bear_u = _side_bundle(DirectionalAssessmentSide.SHORT)
    try:
        build_single_lane_composition_candidate_v1(
            long_assessment=bull_a,
            long_survival=bull_s,
            long_suitability=bull_u,
            short_assessment=bear_a,
            short_survival=bear_s,
            short_suitability=bear_u,
        )
    except DualCandidateConstructionErrorV1:
        return
    raise AssertionError("expected DualCandidateConstructionErrorV1")


def test_s6_entry_exit_owner_and_c2_table_unchanged() -> None:
    replay_calls = _call_names(REPLAY)
    assert "evaluate_double_play_entry_exit_policy_v0" in replay_calls
    assert "evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1" not in (
        replay_calls
    )
    assert "evaluate_directional_assessment_with_confirmation_progress_v1" in replay_calls
    entry_src = ENTRY_EXIT.read_text(encoding="utf-8")
    assert "def evaluate_double_play_entry_exit_policy_v0" in entry_src
    c2_src = C2.read_text(encoding="utf-8")
    assert "if delta > 1:" in c2_src
    assert "EPOCH_GAP" in c2_src
    assert "ACCEPTED_DISTINCT_HOLD_CONFIRMED" in c2_src


def test_s6_entry_exit_symbol_is_unchanged_owner() -> None:
    assert evaluate_double_play_entry_exit_policy_v0.__module__.endswith(
        "double_play_entry_exit_policy_v0"
    )
    policies = _default_policies()
    assert policies.entry_exit.policy_version == "double_play_entry_exit_policy_v0"
