"""A declared behavior horizon must retain the supplied original observation fields."""

from copy import deepcopy
from dataclasses import replace
import json

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    phase_25_dp_attribution_evidence_v1 as attribution,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    plain_v1,
)
from tests.learning.test_conditioned_behavior_source_binding_v1 import reseal_behavior
from tests.learning.test_dp_attribution_original_evidence_binding_v1 import (
    assert_rejected_before_phase14,
    native_request,
)

FIELDS = (
    "evaluation_horizon",
    "n_bars",
    "bar_spec_ref",
    "horizon_start_time_utc",
    "evaluation_time_utc",
)
FAULTS = tuple((operation, field) for operation in ("missing", "null") for field in FIELDS) + (
    ("foreign_kind", "evaluation_horizon"),
    ("text_count", "n_bars"),
)
VARIANTS = ("plain", "missing_quality", "annotation", "earlier_context", "missing_behavior")


def incompatible_request(operation, field):
    request, _ = native_request()
    record = deepcopy(plain_v1(request.realized_behavior))
    if operation == "missing":
        record["horizon_identity"].pop(field)
    elif operation == "null":
        record["horizon_identity"][field] = None
    elif operation == "foreign_kind":
        record["horizon_identity"][field] = "DEFERRED"
    else:
        record["horizon_identity"][field] = str(record["horizon_identity"][field])
    return replace(request, realized_behavior=reseal_behavior(record))


@pytest.mark.parametrize("operation,field", FAULTS)
def test_missing_or_aliased_horizon_stops_before_phase14(monkeypatch, operation, field):
    request = incompatible_request(operation, field)
    assert_rejected_before_phase14(request, f"HORIZON_IDENTITY_MISMATCH:{field}", monkeypatch)


@pytest.mark.parametrize("field,value", [("n_bars", 3), ("bar_spec_ref", "PT5M")])
def test_existing_contradictory_horizon_rejection_remains(monkeypatch, field, value):
    request, _ = native_request()
    record = deepcopy(plain_v1(request.realized_behavior))
    record["horizon_identity"][field] = value
    request = replace(request, realized_behavior=reseal_behavior(record))
    assert_rejected_before_phase14(request, f"HORIZON_IDENTITY_MISMATCH:{field}", monkeypatch)


def valid_packet(root, variant):
    request, _ = native_request(
        context_at="2026-09-01T11:59:59.999999999Z"
        if variant == "earlier_context"
        else "2026-09-01T12:00:00Z"
    )
    if variant == "missing_behavior":
        request = replace(request, realized_behavior=None)
    elif variant in {"missing_quality", "annotation"}:
        record = deepcopy(plain_v1(request.realized_behavior))
        if variant == "missing_quality":
            record.pop("quality_state")
        else:
            record["quality_state"]["source_note"] = "synthetic.original.annotation"
        request = replace(request, realized_behavior=record)
    original_inputs = plain_v1(
        {
            "decision": request.attribution_request.decision_event,
            "observation": request.attribution_request.evaluation_observation,
            "context": request.market_context,
            "behavior": request.realized_behavior,
        }
    )
    result = attribution.compose_dp_attribution_evidence_v1(request)
    assert attribution.replay_dp_attribution_evidence_v1(request, result)
    record = plain_v1(result.attribution_evidence)
    if variant == "missing_behavior":
        assert result.disposition == attribution.DpAttributionDisposition.INSUFFICIENT
        assert record is None
        inspection = None
    else:
        assert result.disposition == attribution.DpAttributionDisposition.ATTRIBUTED
        assert record["horizon_identity"] == original_inputs["behavior"]["horizon_identity"]
        for field in FIELDS:
            assert record["horizon_identity"][field] == original_inputs["observation"][field]
        inspection = plain_v1(
            attribution.inspect_dp_attribution_evidence_v1(json.loads(json.dumps(record)))
        )
        assert inspection["inspect_ok"] is True
    return {
        "inputs": original_inputs,
        "disposition": result.disposition.value,
        "reason_codes": list(result.reason_codes),
        "record": record,
        "inspection": inspection,
        "evidence_digest": result.evidence_digest,
        "phase_14_result_digest": result.phase_14_result_digest,
    }


@pytest.mark.parametrize("variant", VARIANTS)
def test_original_reference_packets_and_missingness_survive(tmp_path, variant):
    packet = valid_packet(tmp_path, variant)
    if packet["record"] is not None:
        assert packet["record"]["attribution_authority"] == "NONE"
        assert packet["record"]["no_trading_gate_from_attribution"] is True
