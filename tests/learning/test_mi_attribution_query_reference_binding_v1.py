"""Native MI references must not silently contradict each other at the query seam."""

from dataclasses import replace
import itertools
import json

import pytest

from src.governance.unified_blueprint_decision_attribution_evidence_v1 import (
    build_decision_attribution_evidence_v1,
    replay_decision_attribution_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    decision_attribution_query_v1 as query,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.calibration_evidence_v1 import (
    _calibration_digest,
    build_calibration_evidence_v1,
    derive_calibration_evidence_id_v1,
    validate_calibration_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    mint_forecast_evidence_v1,
    validate_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    plain_v1,
)
from tests.governance.test_decision_attribution_learning_binding_v1 import (
    ingest,
    ledger_with_originals,
    original_result,
    result_json,
)


def native_forecast(request, **changes):
    observation = request.evaluation_observation
    values = {
        "information_set_ref": request.decision_event["decision_time_information_set_ref"],
        "forecast_created_at_utc": "2026-09-01T12:00:00Z",
        "outcome_horizon_end_utc": observation["bar_close_times_utc"][-1],
        "n_bars": observation["n_bars"],
        "bar_spec_ref": observation["bar_spec_ref"],
        "forecast_kind": "DIRECTIONAL_PROBABILITY",
        "probabilistic_payload": {"p_up": "0.6", "p_down": "0.3", "p_flat": "0.1"},
        "market_state_refs": ["mi.state.query.original"],
        "forecast_model_ref": "mi.model.query.original",
        "support_disposition": "SUFFICIENT_EVIDENCE",
        "provenance": {"source": "synthetic-native-query-fixture"},
        "decision_event_ref": request.decision_event["record_id"],
        "selected_instrument_ref": request.decision_event["selected_instrument_ref"],
    }
    values.update(changes)
    return mint_forecast_evidence_v1(**values)


def native_inputs():
    request, result = original_result()
    forecast = native_forecast(request)
    calibration = build_calibration_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=request.evaluation_observation,
        realized_direction="UP",
    )
    return request, {
        "attribution_record": result.offline_evaluation_bundle["attribution_record"],
        "forecast_evidence": forecast,
        "calibration_evidence": calibration,
        "selected_instrument_ref": request.decision_event["selected_instrument_ref"],
        "side_state_ref": request.side_state_ref,
        "regime_ref": request.bull_bear_state_ref,
    }


def reseal_calibration(calibration, **changes):
    body = {
        key: value
        for key, value in dict(calibration).items()
        if key
        not in {
            "calibration_evidence_id",
            "content_digest",
            "calibration_evidence_authority",
            "evidence_class",
        }
    }
    body.update(changes)
    identity = derive_calibration_evidence_id_v1(body=body)
    result = {
        **body,
        "calibration_evidence_id": identity,
        "content_digest": _calibration_digest({**body, "calibration_evidence_id": identity}),
        "calibration_evidence_authority": "NONE",
        "evidence_class": "CALIBRATION_EVIDENCE",
    }
    validate_calibration_evidence_v1(result)
    return result


def rejected(inputs, reason):
    before = bytes_v1(inputs)
    with pytest.raises(ValueError, match=reason):
        query.query_market_intelligence_decision_attribution_v1(**inputs)
    assert bytes_v1(inputs) == before


@pytest.mark.parametrize("field", ["decision_event_ref", "selected_instrument_ref"])
def test_conflicting_native_forecast_references_are_not_overridden(field):
    request, inputs = native_inputs()
    inputs["forecast_evidence"] = native_forecast(
        request, **{field: "different-original-reference"}
    )
    validate_forecast_evidence_v1(inputs["forecast_evidence"])
    rejected(inputs, "QUERY_.*MISMATCH")


def test_optional_reference_edit_with_same_forecast_digest_is_still_a_conflict():
    _, inputs = native_inputs()
    original = inputs["forecast_evidence"]
    edited = dict(original)
    edited["decision_event_ref"] = "different-decision-with-same-forecast-digest"
    assert edited["content_digest"] == original["content_digest"]
    validate_forecast_evidence_v1(edited)
    inputs["forecast_evidence"] = edited
    rejected(inputs, "QUERY_DECISION_EVENT_REF_MISMATCH")


def test_valid_calibration_for_another_original_forecast_is_rejected():
    request, inputs = native_inputs()
    other = native_forecast(request, forecast_model_ref="mi.model.query.other")
    inputs["calibration_evidence"] = build_calibration_evidence_v1(
        forecast_evidence=other,
        evaluation_observation=request.evaluation_observation,
        realized_direction="UP",
    )
    validate_calibration_evidence_v1(inputs["calibration_evidence"])
    rejected(inputs, "QUERY_CALIBRATION_FORECAST_MISMATCH")


@pytest.mark.parametrize(
    "field,value",
    [
        ("n_bars", 3),
        ("bar_spec_ref", "other:bar-spec"),
        ("forecast_kind", "RETURN_DISTRIBUTION_SUMMARY"),
        ("domain", "OTHER_UNIVERSE"),
    ],
)
def test_resealed_calibration_declaration_does_not_establish_the_join(field, value):
    _, inputs = native_inputs()
    inputs["calibration_evidence"] = reseal_calibration(
        inputs["calibration_evidence"], **{field: value}
    )
    rejected(inputs, "QUERY_CALIBRATION_.*MISMATCH")


@pytest.mark.parametrize(
    "fault", ["schema", "authority", "class", "id", "digest", "missing", "score"]
)
def test_calibration_is_revalidated_before_query_projection(fault):
    _, inputs = native_inputs()
    calibration = plain_v1(inputs["calibration_evidence"])
    if fault == "missing":
        calibration.pop("n_bars")
    elif fault == "score":
        calibration["calibration_result"]["score"] = 0.99
    else:
        key = {
            "schema": "schema_version",
            "authority": "calibration_evidence_authority",
            "class": "evidence_class",
            "id": "calibration_evidence_id",
            "digest": "content_digest",
        }[fault]
        calibration[key] = "OTHER"
    inputs["calibration_evidence"] = calibration
    rejected(inputs, "CALIBRATION_")


def test_calibration_only_cannot_be_relabelled_from_another_domain():
    _, inputs = native_inputs()
    inputs["calibration_evidence"] = reseal_calibration(
        inputs["calibration_evidence"], domain="OTHER_UNIVERSE"
    )
    inputs["forecast_evidence"] = inputs["attribution_record"] = None
    rejected(inputs, "QUERY_CALIBRATION_DOMAIN_MISMATCH")


@pytest.mark.parametrize("fault", ["decision", "instrument", "calibration"])
def test_phase14_caller_cannot_publish_a_mixed_query(fault):
    request, inputs = native_inputs()
    if fault in {"decision", "instrument"}:
        key = "decision_event_ref" if fault == "decision" else "selected_instrument_ref"
        inputs["forecast_evidence"] = native_forecast(request, **{key: "other-original-reference"})
    else:
        other = native_forecast(request, forecast_model_ref="mi.model.query.other")
        inputs["calibration_evidence"] = build_calibration_evidence_v1(
            forecast_evidence=other,
            evaluation_observation=request.evaluation_observation,
            realized_direction="UP",
        )
    request = replace(
        request,
        forecast_evidence=inputs["forecast_evidence"],
        calibration_evidence=inputs["calibration_evidence"],
    )
    with pytest.raises(ValueError, match="QUERY_.*MISMATCH"):
        build_decision_attribution_evidence_v1(request)


@pytest.mark.parametrize("kind", ["opposite_return", "same_return_other_provenance"])
def test_phase14_binds_calibration_to_its_original_outcome_not_just_forecast(kind):
    request, inputs = native_inputs()
    other_request, _ = original_result(kind)
    calibration = build_calibration_evidence_v1(
        forecast_evidence=inputs["forecast_evidence"],
        evaluation_observation=other_request.evaluation_observation,
        realized_direction="DOWN" if kind == "opposite_return" else "UP",
    )
    validate_calibration_evidence_v1(calibration)
    assert (
        calibration["forecast_evidence_id"] == inputs["forecast_evidence"]["forecast_evidence_id"]
    )
    assert calibration["actual_outcome_ref"] != request.evaluation_observation["actual_outcome_ref"]
    request = replace(
        request, forecast_evidence=inputs["forecast_evidence"], calibration_evidence=calibration
    )
    with pytest.raises(ValueError, match="QUERY_CALIBRATION_OUTCOME_MISMATCH"):
        build_decision_attribution_evidence_v1(request)


def test_phase14_preserves_an_earlier_native_receipt_without_an_outcome():
    request, inputs = native_inputs()
    calibration = build_calibration_evidence_v1(
        forecast_evidence=inputs["forecast_evidence"],
        evaluation_observation=None,
    )
    result = build_decision_attribution_evidence_v1(
        replace(
            request,
            forecast_evidence=inputs["forecast_evidence"],
            calibration_evidence=calibration,
        )
    )
    assert result.mi_attribution_query["actual_outcome_ref"] is None
    assert (
        result.decision_attribution_evidence["realized_outcome_ref"]
        == request.evaluation_observation["actual_outcome_ref"]
    )
    assert calibration["evaluability"] == "NOT_EVALUABLE"


@pytest.mark.parametrize("present", list(itertools.product([False, True], repeat=3)))
def test_optional_inputs_stay_optional_without_inventing_missing_relationships(present):
    request, inputs = native_inputs()
    originals = dict(inputs)
    for key, exists in zip(
        ("attribution_record", "forecast_evidence", "calibration_evidence"), present
    ):
        if not exists:
            inputs[key] = None
    before = bytes_v1(inputs)
    result = query.query_market_intelligence_decision_attribution_v1(**inputs)
    assert result["decision_event_ref"] == (
        request.decision_event["record_id"] if any(present[:2]) else None
    )
    assert result["forecast_evidence_id"] == (
        originals["forecast_evidence"]["forecast_evidence_id"] if present[1] else None
    )
    assert result["calibration_evidence_id"] == (
        originals["calibration_evidence"]["calibration_evidence_id"] if present[2] else None
    )
    assert result["missing_context_explicit"]["attribution_record"] is (not present[0])
    assert result["is_evidence_only"] and result["trading_authority"] == "NONE"
    assert bytes_v1(inputs) == before


def test_unbound_forecast_does_not_claim_original_decision_consumption():
    request, inputs = native_inputs()
    inputs["forecast_evidence"] = native_forecast(
        request, decision_event_ref=None, selected_instrument_ref=None
    )
    inputs["selected_instrument_ref"] = None
    result = query.query_market_intelligence_decision_attribution_v1(**inputs)
    assert result["decision_event_ref"] == request.decision_event["record_id"]
    assert result["selected_instrument_ref"] is None
    assert inputs["forecast_evidence"]["decision_event_ref"] is None


@pytest.mark.parametrize(
    "support,outcome", [("INSUFFICIENT_EVIDENCE", True), ("SUFFICIENT_EVIDENCE", False)]
)
def test_native_abstention_and_missing_outcome_are_preserved(support, outcome):
    request, inputs = native_inputs()
    forecast = native_forecast(request, support_disposition=support)
    inputs["forecast_evidence"] = forecast
    calibration = build_calibration_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=request.evaluation_observation if outcome else None,
        realized_direction="UP",
    )
    inputs["calibration_evidence"] = calibration
    result = query.query_market_intelligence_decision_attribution_v1(**inputs)
    assert result["actual_outcome_ref"] == calibration["actual_outcome_ref"]
    assert calibration["calibration_method"] == "NONE"
    assert calibration["evaluability"] == ("INSUFFICIENT_EVIDENCE" if outcome else "NOT_EVALUABLE")


@pytest.mark.parametrize("roundtrip", [False, True])
def test_matching_phase14_query_reaches_original_learning_and_cold_read(tmp_path, roundtrip):
    request, inputs = native_inputs()
    if roundtrip:
        inputs = json.loads(bytes_v1(inputs))
    request = replace(
        request,
        forecast_evidence=inputs["forecast_evidence"],
        calibration_evidence=inputs["calibration_evidence"],
    )
    result = build_decision_attribution_evidence_v1(request)
    assert replay_decision_attribution_evidence_v1(request, result)
    packet = result_json(result)
    ledger = ledger_with_originals(tmp_path / "ledger.jsonl", request, result)
    first = ingest(ledger, result)
    assert first["ok"] and not first["external_effect_authorized"]
    state = first["learning_state_record"]
    assert state["last_actual_outcome_ref"] == inputs["calibration_evidence"]["actual_outcome_ref"]
    assert (
        state["last_economic_score"]
        == result.offline_evaluation_bundle["outcome_record"]["economic_score"]
    )
    assert state["outcome_scalar_kind"] == "LOG_RETURN"
    before = ledger.ledger_path.read_bytes()
    assert ingest(type(ledger)(ledger.ledger_path), result)["idempotent_replay"]
    assert ledger.ledger_path.read_bytes() == before and result_json(result) == packet
