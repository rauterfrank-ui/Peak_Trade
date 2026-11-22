"""Phase-25 joins preserve original outcome identity and exact declared PIT clocks."""

from dataclasses import replace
import socket

import pytest

from src.governance.unified_blueprint_decision_attribution_evidence_v1 import (
    DecisionAttributionEvidenceRequestV1,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    run_offline_n_bars_horizon_pipeline_v1,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    phase_25_dp_attribution_evidence_v1 as attribution,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    plain_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.realized_behavior_v1 import (
    RealizedBehaviorJoinInputsV1,
    derive_behavior_id_v1,
    join_market_context_to_realized_behavior_v1,
    validate_realized_behavior_v1,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _decision, _snapshot
from tests.learning.test_market_context_realized_behavior_join_v1 import _context_for_observation
from tests.learning.test_phase_25_dp_attribution_evidence_v1 import _identity


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("DP attribution counterexamples must remain offline")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def native_request(*, context_at="2026-09-01T12:00:00Z", decision_at="2026-09-01T12:00:00Z"):
    """Original O4/Decision/context/behavior owners; future horizon avoids aliasing clocks."""
    raw = _decision(event_time_utc=decision_at)
    decision = build_decision_event_v0(raw)
    snap = _snapshot(horizon_start_time_utc="2026-09-01T13:00:00Z")
    for bar in snap["o4_bars"]:
        bar["bar_open_time"] += 3600
        bar["bar_close_time"] += 3600
        bar["last_observation_identity"]["venue_event_time"] += 3600
    pipe = run_offline_n_bars_horizon_pipeline_v1(decision, snap, outcome_scalar_kind="LOG_RETURN")
    observation = pipe["evaluation_observation"]
    context = _context_for_observation(observation, observed_at=context_at)
    raw["decision_time_information_set_ref"] = context["information_set_ref"]
    raw["selected_instrument_ref"] = "selected.future.original.attribution.fixture"
    decision = build_decision_event_v0(raw)
    behavior = join_market_context_to_realized_behavior_v1(
        RealizedBehaviorJoinInputsV1(
            market_context=context,
            evaluation_observation=observation,
            measurement_evidence=pipe["materialization"].measurement_evidence_artifact,
            o4_bars_for_path=snap["o4_bars"],
        )
    )
    request = attribution.DpAttributionEvidenceRequestV1(
        attribution_request=DecisionAttributionEvidenceRequestV1(
            decision_event=decision,
            evaluation_observation=observation,
            evaluation_identity=_identity(event_time_utc=observation["evaluation_time_utc"]),
            side_state_ref="side-state-original-attribution-fixture",
            bull_bear_state_ref="bull-bear-original-attribution-fixture",
        ),
        market_context=context,
        realized_behavior=behavior,
    )
    return request, snap


def request_bytes(request):
    return bytes_v1(
        {
            "decision": request.attribution_request.decision_event,
            "observation": request.attribution_request.evaluation_observation,
            "context": request.market_context,
            "behavior": request.realized_behavior,
        }
    )


def assert_rejected_before_phase14(request, reason, monkeypatch):
    original = request_bytes(request)
    calls = []
    native = attribution.build_decision_attribution_evidence_v1

    def phase14(*args, **kwargs):
        calls.append("phase14")
        return native(*args, **kwargs)

    monkeypatch.setattr(attribution, "build_decision_attribution_evidence_v1", phase14)
    result = attribution.compose_dp_attribution_evidence_v1(request)
    assert result.disposition == attribution.DpAttributionDisposition.REJECTED
    assert result.reason_codes == (reason,)
    assert result.attribution_evidence is None and result.evidence_digest is None
    assert result.phase_14_result_digest is None and result.phase_14_disposition is None
    assert calls == []
    assert request_bytes(request) == original


def other_original_measurement(request, snap, kind):
    if kind == "opposite_return":
        snap["o4_bars"][-1]["close"] = 90.0
    elif kind == "same_return_other_prices":
        snap["o4_bars"][0]["close"] = 200.0
        snap["o4_bars"][-1]["close"] = 220.0
    else:
        for bar in snap["o4_bars"]:
            bar["session_id"] = "different-original-measurement-session"
    pipe = run_offline_n_bars_horizon_pipeline_v1(
        request.attribution_request.decision_event, snap, outcome_scalar_kind="LOG_RETURN"
    )
    other = join_market_context_to_realized_behavior_v1(
        RealizedBehaviorJoinInputsV1(
            market_context=request.market_context,
            evaluation_observation=pipe["evaluation_observation"],
            measurement_evidence=pipe["materialization"].measurement_evidence_artifact,
            o4_bars_for_path=snap["o4_bars"],
        )
    )
    validate_realized_behavior_v1(other)
    return pipe["evaluation_observation"], other


@pytest.mark.parametrize(
    "kind", ["opposite_return", "same_return_other_prices", "same_prices_other_source"]
)
def test_other_original_measurement_cannot_supply_the_attributed_behavior(monkeypatch, kind):
    request, snap = native_request()
    _, other = other_original_measurement(request, snap, kind)
    assert other["horizon_identity"] == request.realized_behavior["horizon_identity"]
    assert other["market_context_ref"] == request.realized_behavior["market_context_ref"]
    assert (
        other["actual_outcome_ref"]
        != request.attribution_request.evaluation_observation["actual_outcome_ref"]
    )
    if kind != "opposite_return":
        assert (
            other["forward_behavior"]["forward_return"]
            == request.realized_behavior["forward_behavior"]["forward_return"]
        )
    assert_rejected_before_phase14(
        replace(request, realized_behavior=other),
        "REALIZED_BEHAVIOR_OUTCOME_REF_MISMATCH",
        monkeypatch,
    )


@pytest.mark.parametrize(
    "kind", ["opposite_return", "same_return_other_prices", "same_prices_other_source"]
)
def test_matching_original_measurement_remains_admissible(kind):
    request, snap = native_request()
    observation, behavior = other_original_measurement(request, snap, kind)
    matched = replace(
        request,
        realized_behavior=behavior,
        attribution_request=replace(
            request.attribution_request, evaluation_observation=observation
        ),
    )
    original = request_bytes(matched)
    result = attribution.compose_dp_attribution_evidence_v1(matched)
    assert result.disposition == attribution.DpAttributionDisposition.ATTRIBUTED
    assert result.attribution_evidence["realized_behavior_ref"] == behavior["behavior_id"]
    assert (
        result.attribution_evidence["realized_behavior_content_digest"]
        == behavior["content_digest"]
    )
    assert attribution.inspect_dp_attribution_evidence_v1(result.attribution_evidence)["inspect_ok"]
    assert attribution.replay_dp_attribution_evidence_v1(matched, result)
    assert request_bytes(matched) == original


FUTURE_CONTEXTS = [
    ("2026-09-01T12:00:00Z", "2026-09-01T12:00:00.000000001Z"),
    ("2026-09-01T12:00:00Z", "2026-09-01T12:00:00.000000999Z"),
    ("2026-09-01T12:00:00.000000001Z", "2026-09-01T12:00:00.000000002Z"),
    ("2026-09-01T12:00:00.000000001Z", "2026-09-01T12:00:00.000000999Z"),
]


@pytest.mark.parametrize("decision_at,context_at", FUTURE_CONTEXTS)
@pytest.mark.parametrize("has_behavior", [True, False])
def test_future_context_stops_before_attribution_even_without_behavior(
    monkeypatch, decision_at, context_at, has_behavior
):
    request, _ = native_request(context_at=context_at, decision_at=decision_at)
    if not has_behavior:
        request = replace(request, realized_behavior=None)
    assert_rejected_before_phase14(request, "MARKET_CONTEXT_AFTER_DECISION_TIME", monkeypatch)


def declared_after_horizon_request(fraction):
    """Rehashed contradictory serialized declaration; no claim the native producer emitted it."""
    request, _ = native_request()
    observation = request.attribution_request.evaluation_observation
    stamp = f"2026-09-01T13:00:00.{fraction}Z"
    context = _context_for_observation(observation, observed_at=stamp)
    decision_body = dict(request.attribution_request.decision_event)
    decision_body.pop("content_hash")
    decision_body.update(
        event_time_utc=stamp,
        decision_time_information_set_ref=context["information_set_ref"],
    )
    decision = build_decision_event_v0(decision_body)
    body = plain_v1(request.realized_behavior)
    body.update(
        market_context_ref=context["context_id"],
        information_set_ref=context["information_set_ref"],
        observed_at=stamp,
    )
    body["provenance_refs"] = sorted(
        {context["context_id"], context["information_set_ref"], body["actual_outcome_ref"]}
    )
    excluded = {
        "behavior_id",
        "content_digest",
        "quality_state",
        "realized_behavior_authority",
        "n_bars_outcome_owner",
        "forecast_is_not_decision",
    }
    identity = {key: value for key, value in body.items() if key not in excluded}
    body["behavior_id"] = derive_behavior_id_v1(identity_body=identity)
    body["content_digest"] = compute_content_hash_v0(identity)
    validate_realized_behavior_v1(body)
    return replace(
        request,
        market_context=context,
        realized_behavior=body,
        attribution_request=replace(request.attribution_request, decision_event=decision),
    )


@pytest.mark.parametrize("fraction", ["000000001", "000000999"])
def test_rehashed_context_after_horizon_stops_before_phase14(monkeypatch, fraction):
    assert_rejected_before_phase14(
        declared_after_horizon_request(fraction), "LOOKAHEAD_HORIZON_BEFORE_CONTEXT", monkeypatch
    )


VALID_CLOCKS = [
    ("2026-09-01T11:59:59.999999999Z", "2026-09-01T12:00:00Z"),
    ("2026-09-01T12:00:00Z", "2026-09-01T12:00:00Z"),
    ("2026-09-01T12:00:00.000000000Z", "2026-09-01T12:00:00Z"),
    ("2026-09-01T12:00:00Z", "2026-09-01T12:00:00.000000000Z"),
    ("2026-09-01T12:00:00.000000001Z", "2026-09-01T12:00:00.000000001Z"),
    ("2026-09-01T12:00:00.000000001Z", "2026-09-01T12:00:00.000000999Z"),
    ("2026-09-01T12:00:00.000000998Z", "2026-09-01T12:00:00.000000999Z"),
    ("2026-09-01T12:00:00.000000999Z", "2026-09-01T12:00:00.000001Z"),
    ("2026-09-01T13:00:00Z", "2026-09-01T13:00:00Z"),
    ("2026-09-01T13:00:00.000000000Z", "2026-09-01T13:00:00.000000000Z"),
]


@pytest.mark.parametrize("context_at,decision_at", VALID_CLOCKS)
def test_original_valid_composition_reader_and_replay_preserve_semantics(context_at, decision_at):
    request, _ = native_request(context_at=context_at, decision_at=decision_at)
    original = request_bytes(request)
    first = attribution.compose_dp_attribution_evidence_v1(request)
    second = attribution.compose_dp_attribution_evidence_v1(request)
    assert first.disposition == attribution.DpAttributionDisposition.ATTRIBUTED
    assert bytes_v1(first.attribution_evidence) == bytes_v1(second.attribution_evidence)
    assert attribution.replay_dp_attribution_evidence_v1(request, first)
    inspected = attribution.inspect_dp_attribution_evidence_v1(first.attribution_evidence)
    assert inspected["inspect_ok"] and inspected["provenance_preserved"]
    evidence = first.attribution_evidence
    assert evidence["decision_time_utc"] == decision_at
    assert (
        evidence["selected_future_ref"]
        == request.attribution_request.decision_event["selected_instrument_ref"]
    )
    assert (
        evidence["disposition"] == "EVIDENCE_ONLY" and evidence["attribution_authority"] == "NONE"
    )
    assert evidence["no_trading_gate_from_attribution"] is True
    assert request.realized_behavior["transition"]["status"] == "SEMANTICALLY_UNRESOLVED"
    assert (
        request.realized_behavior["excursion"]["classical_mfe_mae"]["status"]
        == "SEMANTICALLY_UNRESOLVED"
    )
    assert request_bytes(request) == original


def test_valid_missing_behavior_remains_insufficient():
    request, _ = native_request()
    result = attribution.compose_dp_attribution_evidence_v1(
        replace(request, realized_behavior=None)
    )
    assert result.disposition == attribution.DpAttributionDisposition.INSUFFICIENT
    assert result.reason_codes == ("REALIZED_BEHAVIOR_REQUIRED_FOR_OK_HORIZON",)


@pytest.mark.parametrize("suffix", ["+00:00", "+01:00", "", ".0000000001Z"])
def test_original_native_utc_syntax_is_not_broadened(suffix):
    with pytest.raises(DdoValidationError):
        native_request(context_at="2026-09-01T12:00:00" + suffix)
