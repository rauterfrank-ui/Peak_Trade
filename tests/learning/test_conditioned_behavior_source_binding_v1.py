"""A valid behavior digest does not establish the conditioned original-source join."""

from copy import deepcopy
from dataclasses import asdict, replace
import json

import pytest

from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    loop_a_conditioned_learning_evidence_v1 as conditioned,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    plain_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_ingest_v1 import (
    INGEST_ID,
    MiLearningEvidenceIngestRequestV1,
    ingest_mi_learning_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_learning_export_v1 import (
    export_mi_learning_evidence_onto_learning_path_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_store_v1 import (
    MiLearningEvidenceStoreV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.realized_behavior_v1 import (
    derive_behavior_id_v1,
    validate_realized_behavior_v1,
)
from tests.learning.test_conditioned_learning_exact_clock_v1 import VARIANTS, _case

FAULTS = (
    "instrument",
    "information_set",
    "context_time",
    "n_bars",
    "bar_spec",
    "horizon_start",
    "evaluation_time",
    "horizon_kind",
    "missing_outcome_ref",
    "window_close",
    "window_bar_ref",
    "window_status",
    "window_reason",
)


def reseal_behavior(record):
    excluded = {
        "behavior_id",
        "content_digest",
        "quality_state",
        "realized_behavior_authority",
        "n_bars_outcome_owner",
        "forecast_is_not_decision",
    }
    identity = {key: value for key, value in record.items() if key not in excluded}
    record["behavior_id"] = derive_behavior_id_v1(identity_body=identity)
    record["content_digest"] = compute_content_hash_v0(identity)
    return plain_v1(validate_realized_behavior_v1(record))


def incompatible_inputs(fault):
    inputs = _case()
    record = deepcopy(inputs.realized_behavior)
    if fault == "instrument":
        record["instrument_ref"] = "inst.other.synthetic.future"
    elif fault == "information_set":
        record["information_set_ref"] = "info.other.synthetic"
    elif fault == "context_time":
        record["observed_at"] = "2026-09-01T11:59:59Z"
    elif fault == "n_bars":
        record["horizon_identity"]["n_bars"] = 3
    elif fault == "bar_spec":
        record["horizon_identity"]["bar_spec_ref"] = "PT5M"
    elif fault == "horizon_start":
        record["horizon_identity"]["horizon_start_time_utc"] = "2026-09-01T12:00:00.000000001Z"
    elif fault == "evaluation_time":
        record["horizon_identity"]["evaluation_time_utc"] = "2026-09-01T16:00:00Z"
    elif fault == "horizon_kind":
        record["horizon_identity"]["evaluation_horizon"] = "DEFERRED"
    elif fault == "missing_outcome_ref":
        record["actual_outcome_ref"] = None
    elif fault == "window_close":
        record["outcome_window"]["bar_close_times_utc"][-1] = "2026-09-01T14:00:00.000000001Z"
    elif fault == "window_bar_ref":
        record["outcome_window"]["bar_identity_refs"][0] = "bar.other.synthetic"
    elif fault == "window_status":
        record["outcome_window"]["horizon_observation_status"] = "INSUFFICIENT_BARS"
    else:
        record["outcome_window"]["horizon_observation_reason"] = "OTHER_SOURCE_REASON"
    return replace(inputs, realized_behavior=reseal_behavior(record))


@pytest.mark.parametrize("entry", ["compose", "ingest"])
@pytest.mark.parametrize("fault", FAULTS)
def test_resealed_behavior_cannot_substitute_original_sources(tmp_path, entry, fault):
    inputs = incompatible_inputs(fault)
    original = deepcopy(asdict(inputs))
    root = tmp_path / "never-written"
    with pytest.raises(
        conditioned.LoopAConditionedLearningError, match="REALIZED_BEHAVIOR_.*MISMATCH"
    ):
        if entry == "compose":
            conditioned.compose_conditioned_mi_learning_evidence_v1(inputs)
        else:
            ingest_mi_learning_evidence_v1(
                root, MiLearningEvidenceIngestRequestV1(**asdict(inputs))
            )
    assert asdict(inputs) == original
    assert not root.exists()


@pytest.mark.parametrize("entry", ["compose", "ingest"])
def test_native_later_behavior_cannot_alias_earlier_observation(tmp_path, entry):
    inputs = _case()
    later = _case("later_evaluation")
    assert inputs.market_context == later.market_context
    assert (
        inputs.realized_behavior["actual_outcome_ref"]
        == later.realized_behavior["actual_outcome_ref"]
    )
    inputs = replace(inputs, realized_behavior=later.realized_behavior)
    with pytest.raises(
        conditioned.LoopAConditionedLearningError, match="REALIZED_BEHAVIOR_.*MISMATCH"
    ):
        if entry == "compose":
            conditioned.compose_conditioned_mi_learning_evidence_v1(inputs)
        else:
            ingest_mi_learning_evidence_v1(
                tmp_path / "never-written", MiLearningEvidenceIngestRequestV1(**asdict(inputs))
            )
    assert not (tmp_path / "never-written").exists()


def valid_packet(root, variant):
    inputs = _case(variant)
    record = plain_v1(
        conditioned.compose_conditioned_mi_learning_evidence_v1(
            inputs, provenance={"ingest_id": INGEST_ID}
        )
    )
    request = MiLearningEvidenceIngestRequestV1(**asdict(inputs))
    first = plain_v1(ingest_mi_learning_evidence_v1(root, request))
    replay = plain_v1(ingest_mi_learning_evidence_v1(root, request))
    assert first["ingest_status"] == "APPENDED" and replay["ingest_status"] == "IDEMPOTENT_REPLAY"
    cold = MiLearningEvidenceStoreV1(root)
    assert plain_v1(cold.get(record["mi_learning_evidence_id"])) == record
    assert plain_v1(cold.list_records()) == [record]
    exported = plain_v1(export_mi_learning_evidence_onto_learning_path_v1(record))
    return {
        "inputs": asdict(inputs),
        "record": record,
        "first": first,
        "replay": replay,
        "export": exported,
    }


def test_equivalent_source_clock_representations_remain_valid():
    inputs = _case()
    record = deepcopy(inputs.realized_behavior)
    record["observed_at"] = record["observed_at"][:-1] + ".000000000Z"
    for block in ("horizon_identity", "outcome_window"):
        for key in ("horizon_start_time_utc", "evaluation_time_utc"):
            record[block][key] = record[block][key][:-1] + ".000000000Z"
    record["outcome_window"]["bar_close_times_utc"] = [
        value[:-1] + ".000000000Z" for value in record["outcome_window"]["bar_close_times_utc"]
    ]
    record = reseal_behavior(record)
    result = conditioned.compose_conditioned_mi_learning_evidence_v1(
        replace(inputs, realized_behavior=record)
    )
    assert result["realized_behavior_ref"] == record["behavior_id"]
    assert result["realized_behavior_content_digest"] == record["content_digest"]


def test_optional_observation_is_not_invented_from_behavior():
    inputs = replace(_case(), evaluation_observation=None)
    result = conditioned.compose_conditioned_mi_learning_evidence_v1(inputs)
    assert result["actual_outcome_ref"] is None
    assert result["outcome_finalization_status"] == "INCOMPLETE"
    assert result["evaluability"] == "NOT_EVALUABLE"
    assert result["realized_behavior_ref"] == inputs.realized_behavior["behavior_id"]


@pytest.mark.parametrize("variant", VARIANTS)
def test_original_native_conditioning_remains_valid(tmp_path, variant):
    packet = valid_packet(tmp_path, variant)
    record = packet["record"]
    assert json.loads(json.dumps(record)) == record
    assert record["mi_learning_evidence_authority"] == "NONE"
    assert record["forecast_is_not_decision"] is True
    assert (
        packet["inputs"]["forecast_evidence"]["information_set_ref"]
        != packet["inputs"]["market_context"]["information_set_ref"]
    )
    snapshot = record["behavior_semantics_snapshot"]
    assert (
        snapshot["classical_mfe_mae_status"]
        == snapshot["transition_status"]
        == "SEMANTICALLY_UNRESOLVED"
    )
