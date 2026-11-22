"""Probability meaning must survive native mint, cold validation and learning intake."""

import json

import pytest

from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.calibration_evidence_v1 import (
    build_calibration_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.decision_attribution_query_v1 import (
    query_market_intelligence_decision_attribution_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    derive_forecast_evidence_id_v1,
    validate_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    plain_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_ingest_v1 import (
    INGEST_ID,
    MiLearningEvidenceIngestRequestV1,
    ingest_mi_learning_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_store_v1 import (
    MiLearningEvidenceStoreV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_to_learning_evidence_bridge_v1 import (
    compose_mi_to_learning_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.probabilistic_forecast_payload_v1 import (
    _canonicalize_numeric_tree,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from tests.learning.test_mi_attribution_query_reference_binding_v1 import (
    native_forecast as query_forecast,
    original_result,
)

DIRECTIONAL = "DIRECTIONAL_PROBABILITY"
THRESHOLD = "THRESHOLD_EVENT_PROBABILITY"
PROBABILITY_KEYS = ("p_up", "p_down", "p_flat")


def native_forecast(request, **changes):
    # The Phase-14 selection receipt is not the observation's market instrument ID.
    # Probability admission needs neither reference; retain the legal optional absence.
    return query_forecast(request, selected_instrument_ref=None, **changes)


def directional(values):
    return dict(zip(PROBABILITY_KEYS, values, strict=True))


INVALID_DIRECTIONAL = [
    pytest.param(directional(values), id=label)
    for label, values in (
        ("negative-up", (-0.1, 1.0, 0.1)),
        ("negative-down", (1.0, -0.1, 0.1)),
        ("negative-flat", (1.0, 0.1, -0.1)),
        ("over-one-up", (1.1, -0.1, 0)),
        ("over-one-down", (-0.1, 1.1, 0)),
        ("over-one-flat", (-0.1, 0, 1.1)),
        ("nan-up", (float("nan"), 0.5, 0.5)),
        ("nan-down", (0.5, "NaN", 0.5)),
        ("nan-flat", (0.5, 0.5, "nan")),
        ("cancelled-infinity", (float("inf"), float("-inf"), 1)),
        ("cancelled-infinity-text", ("Infinity", "-Infinity", "1")),
        ("boolean-up", (True, 0, 0)),
        ("boolean-down", (0, True, 0)),
        ("boolean-flat", (0, 0, True)),
        ("negative-below-float-resolution", ("-1e-4000", "1", "0")),
        ("over-one-below-float-resolution", ("1.000000000000000000000001", "0", "0")),
    )
]


def resealed_declaration(request, kind, payload):
    """Legacy/self-consistent envelope, without invoking or bypassing a validator.

    Uses the existing identity/digest owners, not a promise of source authenticity.
    The baseline native factory produces this exact envelope for admitted probes.
    """
    body = plain_v1(native_forecast(request))
    body.update(forecast_kind=kind, probabilistic_payload=payload)
    body["probabilistic_payload_digest"] = compute_content_sha256(
        _canonicalize_numeric_tree({"forecast_kind": kind, "payload": payload})
    )
    keys = (
        "domain",
        "schema_version",
        "information_set_ref",
        "forecast_created_at_utc",
        "outcome_horizon_end_utc",
        "n_bars",
        "bar_spec_ref",
        "forecast_kind",
        "probabilistic_payload_digest",
        "market_state_refs",
        "forecast_model_ref",
        "support_disposition",
        "outcome_binding_mode",
    )
    identity = {key: body[key] for key in keys}
    identity["market_state_refs"] = tuple(sorted(body["market_state_refs"]))
    body["forecast_evidence_id"] = derive_forecast_evidence_id_v1(identity_body=identity)
    body["content_digest"] = compute_content_hash_v0(
        {
            **identity,
            "forecast_evidence_id": body["forecast_evidence_id"],
            "provenance": body["provenance"],
        }
    )
    return body


@pytest.mark.parametrize("payload", INVALID_DIRECTIONAL)
def test_native_mint_rejects_invalid_directional_components(payload):
    request, _ = original_result()
    before = repr(payload)
    with pytest.raises(DdoValidationError, match="PROBABILITY"):
        native_forecast(request, probabilistic_payload=payload)
    assert repr(payload) == before


@pytest.mark.parametrize(
    "value", [float("nan"), "NaN", True, False, "-1e-4000", "1.000000000000000000000001"]
)
def test_native_mint_rejects_invalid_event_probabilities(value):
    request, _ = original_result()
    with pytest.raises(DdoValidationError, match="PROBABILITY"):
        native_forecast(
            request,
            forecast_kind=THRESHOLD,
            probabilistic_payload={"threshold": "0.02", "p_event": value},
        )


@pytest.mark.parametrize("entry", ["validate", "calibration", "query", "bridge", "ingest"])
@pytest.mark.parametrize(
    "values", [(-0.1, 1.0, 0.1), ("NaN", 0.5, 0.5), (True, 0, 0), ("-1e-4000", 1, 0)]
)
def test_resealed_invalid_forecast_cannot_reach_existing_consumers(tmp_path, entry, values):
    request, _ = original_result()
    forecast = resealed_declaration(request, DIRECTIONAL, directional(values))
    # JSON diagnostic text only: no non-finite JSON is written to a native store.
    before = json.dumps(forecast, sort_keys=True)
    args = dict(
        forecast_evidence=forecast,
        evaluation_observation=request.evaluation_observation,
        realized_direction="UP",
    )
    root = tmp_path / "never-created"
    with pytest.raises(DdoValidationError, match="PROBABILITY"):
        if entry == "validate":
            validate_forecast_evidence_v1(forecast)
        elif entry == "calibration":
            build_calibration_evidence_v1(**args)
        elif entry == "query":
            query_market_intelligence_decision_attribution_v1(
                attribution_record=None, forecast_evidence=forecast, calibration_evidence=None
            )
        elif entry == "bridge":
            compose_mi_to_learning_evidence_v1(**args)
        else:
            ingest_mi_learning_evidence_v1(root, MiLearningEvidenceIngestRequestV1(**args))
    assert json.dumps(forecast, sort_keys=True) == before
    assert not root.exists()


@pytest.mark.parametrize("value", [float("nan"), "NaN"])
def test_event_nan_cannot_be_copied_into_native_calibration(value):
    request, _ = original_result()
    forecast = resealed_declaration(request, THRESHOLD, {"threshold": "0.02", "p_event": value})
    with pytest.raises(DdoValidationError, match="PROBABILITY"):
        build_calibration_evidence_v1(
            forecast_evidence=forecast,
            evaluation_observation=request.evaluation_observation,
            threshold_hit=True,
        )


@pytest.mark.parametrize(
    "value", [None, [], {}, "not-a-number", "", "0__._1", float("inf"), -0.1, 1.1]
)
def test_event_already_invalid_controls_remain_rejected(value):
    request, _ = original_result()
    with pytest.raises((DdoValidationError, ValueError, TypeError)):
        native_forecast(
            request,
            forecast_kind=THRESHOLD,
            probabilistic_payload={"threshold": "0.02", "p_event": value},
        )


VALID_VARIANTS = (
    "float",
    "decimal-text",
    "up-certain",
    "down-certain",
    "flat-certain",
    "negative-zero",
    "within-sum-tolerance",
    "insufficient",
    "missing-outcome",
    "event-zero",
    "event-one",
    "event-decimal-text",
)


def valid_packet(root, variant):
    """Full native output packet for original-source before/after byte comparison."""
    request, _ = original_result()
    payload = {"p_up": 0.6, "p_down": 0.3, "p_flat": 0.1}
    if variant == "decimal-text":
        payload = {"p_up": "6e-1", "p_down": "0.30", "p_flat": "0.100"}
    elif variant.endswith("-certain"):
        target = "p_" + variant.split("-", 1)[0]
        payload = {key: int(key == target) for key in PROBABILITY_KEYS}
    elif variant == "negative-zero":
        payload = {"p_up": "-0.0", "p_down": "1", "p_flat": "0"}
    elif variant == "within-sum-tolerance":
        payload["p_up"] = 0.6000000005
    kind = DIRECTIONAL
    if variant.startswith("event-"):
        kind = THRESHOLD
        value = {"event-zero": 0, "event-one": 1, "event-decimal-text": "0.70"}[variant]
        payload = {"threshold": "0.02", "p_event": value}
    forecast = native_forecast(
        request,
        forecast_kind=kind,
        probabilistic_payload=payload,
        support_disposition="INSUFFICIENT_EVIDENCE"
        if variant == "insufficient"
        else "SUFFICIENT_EVIDENCE",
    )
    observation = None if variant == "missing-outcome" else request.evaluation_observation
    calibration = build_calibration_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=observation,
        realized_direction="UP",
        threshold_hit=True,
    )
    # Genuine serialization and native cold revalidation, preserving original types.
    roundtrip = json.loads(json.dumps(plain_v1(forecast), allow_nan=False))
    cold_forecast = validate_forecast_evidence_v1(roundtrip)
    query = query_market_intelligence_decision_attribution_v1(
        attribution_record=None, forecast_evidence=cold_forecast, calibration_evidence=calibration
    )
    packet = dict(
        payload=payload,
        forecast=forecast,
        cold_forecast=cold_forecast,
        calibration=calibration,
        query=query,
    )
    if kind == DIRECTIONAL:
        args = dict(
            forecast_evidence=cold_forecast,
            evaluation_observation=observation,
            realized_direction="UP",
        )
        bridge = compose_mi_to_learning_evidence_v1(**args, provenance={"ingest_id": INGEST_ID})
        ack = ingest_mi_learning_evidence_v1(root, MiLearningEvidenceIngestRequestV1(**args))
        cold_store = MiLearningEvidenceStoreV1(root)
        record = cold_store.get(bridge["mi_learning_evidence_id"])
        files_before = {
            str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*.json")
        }
        replay = ingest_mi_learning_evidence_v1(root, MiLearningEvidenceIngestRequestV1(**args))
        assert ack["ingest_status"] == "APPENDED"
        assert replay == {**ack, "ingest_status": "IDEMPOTENT_REPLAY"}
        assert {
            str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*.json")
        } == files_before
        packet.update(bridge=bridge, ack=ack, readback=record)
    return plain_v1(packet)


@pytest.mark.parametrize("variant", VALID_VARIANTS)
def test_original_probability_meaning_and_native_readback_are_preserved(tmp_path, variant):
    packet = valid_packet(tmp_path / "synthetic-mi", variant)
    assert bytes_v1(packet["forecast"]) == bytes_v1(packet["cold_forecast"])
    assert packet["forecast"]["probabilistic_payload"] == packet["payload"]
    assert packet["forecast"]["forecast_evidence_authority"] == "NONE"
    assert packet["calibration"]["calibration_evidence_authority"] == "NONE"
    if "readback" in packet:
        assert packet["readback"] == packet["bridge"]
    if variant == "missing-outcome":
        assert packet["calibration"]["evaluability"] == "NOT_EVALUABLE"
        assert packet["calibration"]["actual_outcome_ref"] is None
    elif variant == "insufficient":
        assert packet["calibration"]["evaluability"] == "INSUFFICIENT_EVIDENCE"
        assert packet["calibration"]["calibration_method"] == "NONE"


def test_directional_sum_contract_is_not_replaced_by_component_bounds():
    request, _ = original_result()
    with pytest.raises(DdoValidationError, match="MUST_SUM_TO_ONE"):
        native_forecast(request, probabilistic_payload=directional((0.5, 0.3, 0.1)))
