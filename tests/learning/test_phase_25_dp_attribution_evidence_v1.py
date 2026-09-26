"""Phase 25 DP Attribution evidence — PIT join, horizon, replay, authority."""

from __future__ import annotations

import pytest

from src.governance.unified_blueprint_decision_attribution_evidence_v1 import (
    DecisionAttributionEvidenceRequestV1,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    run_offline_n_bars_horizon_pipeline_v1,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_engine_v1 import (
    supply_n_bars_evaluation_observation_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.phase_25_dp_attribution_evidence_v1 import (
    DpAttributionDisposition,
    DpAttributionEvidenceRequestV1,
    Phase25DpAttributionError,
    assert_phase_25_dp_attribution_authority_invariants_v1,
    compose_dp_attribution_evidence_v1,
    inspect_dp_attribution_evidence_v1,
    replay_dp_attribution_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.realized_behavior_v1 import (
    RealizedBehaviorJoinInputsV1,
    join_market_context_to_realized_behavior_v1,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _decision, _snapshot
from tests.learning.test_market_context_realized_behavior_join_v1 import (
    _context_for_observation,
    _minimal_market_context,
)


def _identity(**overrides) -> dict:
    payload = {
        "outcome_record_id": "out-p25-0001",
        "attribution_record_id": "attr-p25-0001",
        "counterfactual_record_id": "cf-p25-0001",
        "correlation_id": "cor-p25-0001",
        "event_time_utc": "2026-09-01T13:00:00Z",
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
    }
    payload.update(overrides)
    return payload


def _n_bars_supplier(**overrides) -> dict:
    payload = {
        "horizon_start_time_utc": "2026-09-01T12:00:00Z",
        "instrument_ref": "inst:btc-usdt",
        "bar_spec_ref": "bar:1h",
        "n_bars": 2,
        "horizon_observation_status": "OK",
        "outcome_scalar_kind": "LOG_RETURN",
        "bar_close_times_utc": ["2026-09-01T13:00:00Z", "2026-09-01T14:00:00Z"],
        "bar_identity_refs": ["bar-close-1", "bar-close-2"],
        "evaluation_time_information_set_ref": "eval-info-set-p25",
        "actual_outcome_ref": "evidence/outcome-measurement-p25",
        "economic_score": "LABEL_OPAQUE_P25",
    }
    payload.update(overrides)
    return payload


def _pipeline_bundle():
    decision_raw = _decision()
    decision_raw["event_time_utc"] = "2026-09-01T12:00:00Z"
    decision_raw["record_id"] = "dec-p25-0001"
    decision_raw["event_id"] = "evt-p25-0001"
    decision_raw["correlation_id"] = "cor-p25-0001"
    decision = build_decision_event_v0(decision_raw)
    snap = _snapshot()
    snap["decision_event_ref"] = decision["record_id"]
    pipe = run_offline_n_bars_horizon_pipeline_v1(decision, snap, outcome_scalar_kind="LOG_RETURN")
    obs = pipe["evaluation_observation"]
    ctx = _context_for_observation(obs, observed_at="2026-09-01T12:00:00Z")
    decision_raw["decision_time_information_set_ref"] = str(ctx["information_set_ref"])
    decision_raw["selected_instrument_ref"] = "sel-future-ref-p25"
    decision = build_decision_event_v0(decision_raw)
    rb = join_market_context_to_realized_behavior_v1(
        RealizedBehaviorJoinInputsV1(
            market_context=ctx,
            evaluation_observation=obs,
            measurement_evidence=pipe["materialization"].measurement_evidence_artifact,
            o4_bars_for_path=snap["o4_bars"],
        )
    )
    return decision, obs, ctx, rb


def _attributed_request(**overrides):
    decision, obs, ctx, rb = _pipeline_bundle()
    attr_req = DecisionAttributionEvidenceRequestV1(
        decision_event=decision,
        evaluation_observation=obs,
        evaluation_identity=_identity(),
        side_state_ref="side-state-p25",
        bull_bear_state_ref="bull-bear-p25",
    )
    req = DpAttributionEvidenceRequestV1(
        attribution_request=attr_req,
        market_context=ctx,
        realized_behavior=rb,
    )
    if overrides:
        req = DpAttributionEvidenceRequestV1(**{**req.__dict__, **overrides})
    return compose_dp_attribution_evidence_v1(req), req


def test_authority_invariants() -> None:
    inv = assert_phase_25_dp_attribution_authority_invariants_v1()
    assert inv["ATTRIBUTION_EVIDENCE_ONLY"] is True
    assert inv["MV2_DP_UNCHANGED"] is True
    assert inv["NO_TRADING_GATE_FROM_ATTRIBUTION"] is True
    assert inv["PHASE_26_STARTED"] is False


def test_compose_reference_bundle_and_deterministic_identity() -> None:
    first, req = _attributed_request()
    second = compose_dp_attribution_evidence_v1(req)
    assert first.disposition == DpAttributionDisposition.ATTRIBUTED
    assert first.attribution_evidence is not None
    ev = first.attribution_evidence
    assert ev["market_context_ref"] is not None
    assert ev["selected_future_ref"] is not None
    assert (
        ev["mv2_dp_decision_ref"]["decision_event_ref"]
        == req.attribution_request.decision_event["record_id"]
    )
    assert ev["realized_behavior_ref"] != UNKNOWN
    assert ev["horizon_identity"] is not None
    assert ev["pit_join_proven"] is True
    assert first.attribution_evidence.get(
        "attribution_evidence_id"
    ) == second.attribution_evidence.get("attribution_evidence_id")
    assert replay_dp_attribution_evidence_v1(req, first)


def test_lookahead_context_after_decision_rejected() -> None:
    decision, obs, ctx, rb = _pipeline_bundle()
    bad_ctx = _minimal_market_context(observed_at="2026-09-01T13:00:00Z")
    result = compose_dp_attribution_evidence_v1(
        DpAttributionEvidenceRequestV1(
            attribution_request=DecisionAttributionEvidenceRequestV1(
                decision_event=decision,
                evaluation_observation=obs,
                evaluation_identity=_identity(),
            ),
            market_context=bad_ctx,
            realized_behavior=rb,
        )
    )
    assert result.disposition == DpAttributionDisposition.REJECTED
    assert "MARKET_CONTEXT_AFTER_DECISION_TIME" in result.reason_codes


def test_realized_behavior_context_mismatch_rejected() -> None:
    decision, obs, ctx, rb = _pipeline_bundle()
    rb_bad = dict(rb)
    rb_bad["market_context_ref"] = "mi.context.other"
    result = compose_dp_attribution_evidence_v1(
        DpAttributionEvidenceRequestV1(
            attribution_request=DecisionAttributionEvidenceRequestV1(
                decision_event=decision,
                evaluation_observation=obs,
                evaluation_identity=_identity(),
            ),
            market_context=ctx,
            realized_behavior=rb_bad,
        )
    )
    assert result.disposition == DpAttributionDisposition.REJECTED


def test_inspect_reader_path_preserves_provenance() -> None:
    result, _ = _attributed_request()
    assert result.attribution_evidence is not None
    inspected = inspect_dp_attribution_evidence_v1(result.attribution_evidence)
    assert inspected["inspect_ok"] is True
    assert inspected["provenance_preserved"] is True


def test_missing_realized_behavior_insufficient_for_ok_horizon() -> None:
    decision_raw = _decision()
    decision_raw["event_time_utc"] = "2026-09-01T12:00:00Z"
    obs = supply_n_bars_evaluation_observation_v1(
        build_decision_event_v0(decision_raw), _n_bars_supplier()
    )
    ctx = _context_for_observation(obs, observed_at="2026-09-01T12:00:00Z")
    decision_raw["decision_time_information_set_ref"] = str(ctx["information_set_ref"])
    decision = build_decision_event_v0(decision_raw)
    result = compose_dp_attribution_evidence_v1(
        DpAttributionEvidenceRequestV1(
            attribution_request=DecisionAttributionEvidenceRequestV1(
                decision_event=decision,
                evaluation_observation=obs,
                evaluation_identity=_identity(),
            ),
            market_context=ctx,
            realized_behavior=None,
        )
    )
    assert result.disposition == DpAttributionDisposition.INSUFFICIENT


def test_tampered_evidence_digest_fails_inspect() -> None:
    result, _ = _attributed_request()
    assert result.attribution_evidence is not None
    tampered = dict(result.attribution_evidence)
    tampered["side_state_ref"] = "tampered"
    with pytest.raises(Phase25DpAttributionError):
        inspect_dp_attribution_evidence_v1(tampered)
