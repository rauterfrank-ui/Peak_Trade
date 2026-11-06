"""Machine-readable Owner policy record for persistent Selected-Future confirmation."""

from __future__ import annotations

import json
from pathlib import Path

from trading.market_state.directional_confirmation_progress_v1 import (
    ConfirmationAssessmentStateV1,
    ConfirmationProgressStateV1,
    ConfirmationSideV1,
    initial_confirmation_progress_state_v1,
)
from trading.market_state.observation_identity_v1 import MarketObservationEpoch
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    DirectionalConfirmationSideStateCarrierV1,
)

from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run
from tests.trading.master_v2.test_post_confirmation_survival_suitability_composition_binding_v1 import (
    _distinct_acceptor,
    _key,
    _policies_confirm_once,
    _session,
)

_REPO = Path(__file__).resolve().parents[2]
_RECORD = (
    _REPO / "config/governance/selected_future_persistent_scope_confirmation_authority_v1.json"
)
_SPEC = _REPO / "docs/ops/specs/SELECTED_FUTURE_PERSISTENT_SCOPE_CONFIRMATION_AUTHORITY_V1.md"


def test_authority_record_fail_closed_flags() -> None:
    payload = json.loads(_RECORD.read_text(encoding="utf-8"))
    assert payload["SELECTED_FUTURE_PERSISTENCE"] is True
    assert payload["ELEMENTARY_DIRECTION_CHANGE_RESELECTS_FUTURE"] is False
    assert payload["ELEMENTARY_DIRECTION_CHANGE_INVALIDATES_OPPOSITE_CANDIDATE"] is False
    assert (
        payload[
            "OD1_SINGLE_LANE_ACTIVATION_IS_CARRIER_ROUTING_NOT_CANDIDATE_INVALIDATION_AUTHORITY"
        ]
        is True
    )
    assert payload["DUAL_CARRIER_PADDING_MUST_NOT_DESTROY_PERSISTENT_CANDIDATE"] is True
    assert payload["external_effect_authorized"] is False
    assert payload["CANDIDATE_INVALIDATION_AUTHORITY_PROVEN"] is False
    assert payload["CONFIRMATION_COUNT_SEMANTICS_AUTHORITY_BLOCKER"] is False
    assert _SPEC.is_file()


def _bear_candidate_one() -> ConfirmationProgressStateV1:
    key = _key()
    return ConfirmationProgressStateV1(
        session_id=_session(),
        venue="okx_eea",
        instrument=key,
        side=ConfirmationSideV1.SHORT,
        assessment_state=ConfirmationAssessmentStateV1.CANDIDATE,
        latest_accepted_market_observation_epoch=MarketObservationEpoch(value=2),
        candidate_started_at_epoch=MarketObservationEpoch(value=2),
        distinct_confirmation_observation_count=1,
        last_processed_acceptor_result_fingerprint="bear-cand-1",
    )


def test_integrated_replay_preserves_inactive_bear_candidate_on_elementary_bull() -> None:
    """Productive-binding proof for SELECTED_FUTURE_PERSISTENCE after #6933 dual-carrier merge."""
    key = _key()
    carrier = DirectionalConfirmationSideStateCarrierV1(
        bull_confirmation_state=initial_confirmation_progress_state_v1(
            session_id=_session(),
            venue="okx_eea",
            instrument=key,
            side=ConfirmationSideV1.LONG,
        ),
        bear_confirmation_state=_bear_candidate_one(),
    )
    acceptor, _ = _distinct_acceptor(previous_mark=11.0, mark=13.0)
    result = _run(
        policies=_policies_confirm_once(),
        price_path=(3500.0, 3570.0),
        directional_confirmation_progress=carrier,
        observation_acceptance_result=acceptor,
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=key,
    )
    assert result.replay_pass is True
    assert result.intermediate is not None
    after = result.intermediate.directional_confirmation_progress_after
    assert after is not None
    assert after.bear_confirmation_state.assessment_state is ConfirmationAssessmentStateV1.CANDIDATE
    assert after.bear_confirmation_state.distinct_confirmation_observation_count == 1
    assert result.intermediate.bull_assessment is not None
    assert result.intermediate.bear_assessment is None
