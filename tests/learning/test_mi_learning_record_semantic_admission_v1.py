"""Native MI learning receipts must retain coherent outcome and abstention states."""

from copy import deepcopy
from dataclasses import asdict, replace
import json

import pytest

from src.experiments.canonical_optimization_universe_mi_enriched_m4_intake_v1 import (
    INTAKE_STATUS_ACCEPTED,
    INTAKE_STATUS_REJECTED_MI_INPUT,
    validate_mi_enriched_m4_intake_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1 import (
    terminate_learning_conditioned_evaluative_at_a_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.adapters_v1 import (
    adapt_learning_conditioned_evaluative_v1,
    default_termination_context_from_market_context_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    plain_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.loop_a_conditioned_learning_evidence_v1 import (
    ConditionedLearningComposeInputsV1,
    compose_conditioned_mi_learning_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_learning_export_v1 import (
    export_mi_learning_evidence_onto_learning_path_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_record_v1 import (
    compute_mi_learning_reproducibility_digest_v1,
    derive_mi_learning_evidence_id_v1,
    validate_mi_learning_evidence_record_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_store_v1 import (
    RECORD_FILENAME,
    MiLearningEvidenceStoreV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_to_learning_evidence_bridge_v1 import (
    compose_mi_to_learning_evidence_v1,
)
from tests.experiments.test_canonical_optimization_universe_mi_enriched_m4_intake_v1 import (
    _intake_request,
)
from tests.learning.test_loop_a_conditioned_learning_evidence_v1 import _realized_behavior
from tests.learning.test_market_context_realized_behavior_join_v1 import _context_for_observation
from tests.learning.test_mi_learning_exact_clock_admission_v1 import _case

VARIANTS = (
    "plain",
    "missing",
    "insufficient",
    "supplied",
    "zero_fraction",
    "later_evaluation",
    "conditioned",
    "conditioned_missing",
)
FAULTS = (
    "finalized_without_outcome",
    "finalized_without_observation",
    "finalized_missing_status",
    "incomplete_with_measurement",
    "unknown_finalization",
    "unknown_evaluability",
    "sufficient_without_method",
    "unknown_method",
    "missing_but_sufficient",
    "missing_but_method",
    "insufficient_but_method",
    "bool_n_bars",
    "zero_n_bars",
    "missing_information_set",
    "created_at_horizon",
    "created_after_horizon_by_nanosecond",
    "invalid_calendar",
)


def native_record(variant="plain"):
    conditioned = variant.startswith("conditioned")
    args, _ = _case(variant="missing" if variant == "conditioned_missing" else variant)
    if conditioned:
        source_args, _ = _case()
        obs = source_args["evaluation_observation"]
        context = _context_for_observation(obs)
        record = compose_conditioned_mi_learning_evidence_v1(
            ConditionedLearningComposeInputsV1(
                forecast_evidence=args["forecast_evidence"],
                evaluation_observation=args["evaluation_observation"],
                market_context=context,
                realized_behavior=None
                if args["evaluation_observation"] is None
                else _realized_behavior(obs=obs, ctx=context),
                realized_direction="UP",
            )
        )
        return plain_v1(record), context
    return plain_v1(compose_mi_to_learning_evidence_v1(**args)), None


def contradictory_record(fault, record=None):
    record = deepcopy(record if record is not None else native_record()[0])
    changes = {
        "finalized_without_outcome": {"actual_outcome_ref": None},
        "finalized_without_observation": {"evaluation_observation_ref": None},
        "finalized_missing_status": {"horizon_observation_status": "OUTCOME_MISSING"},
        "incomplete_with_measurement": {"outcome_finalization_status": "INCOMPLETE"},
        "unknown_finalization": {"outcome_finalization_status": "UNKNOWN"},
        "unknown_evaluability": {"evaluability": "UNKNOWN"},
        "sufficient_without_method": {"calibration_method": "NONE"},
        "unknown_method": {"calibration_method": "INVENTED_SCORE_V1"},
        "insufficient_but_method": {"evaluability": "INSUFFICIENT_EVIDENCE"},
        "bool_n_bars": {"n_bars": True},
        "zero_n_bars": {"n_bars": 0},
        "missing_information_set": {"information_set_ref": None},
        "created_at_horizon": {"forecast_created_at_utc": record["outcome_horizon_end_utc"]},
        "created_after_horizon_by_nanosecond": {
            "forecast_created_at_utc": record["outcome_horizon_end_utc"][:-1] + ".000000001Z"
        },
        "invalid_calendar": {"forecast_created_at_utc": "2026-02-30T12:00:00Z"},
    }
    if fault.startswith("missing_but_"):
        record, _ = native_record("conditioned_missing" if context_bound(record) else "missing")
        record["evaluability" if fault == "missing_but_sufficient" else "calibration_method"] = (
            "SUFFICIENT_EVIDENCE" if fault == "missing_but_sufficient" else "BRIER_SCORE_V1"
        )
    else:
        record.update(changes[fault])
    # A self-consistent checksum is not proof of a coherent measurement state.
    digest = compute_mi_learning_reproducibility_digest_v1(record)
    record["reproducibility_digest"] = digest
    record["mi_learning_evidence_id"] = derive_mi_learning_evidence_id_v1(
        reproducibility_digest=digest
    )
    return record


def context_bound(record):
    return record.get("conditioned_binding_schema") is not None


@pytest.mark.parametrize("entry", ["validate", "export", "append", "cold_get", "cold_list"])
@pytest.mark.parametrize("fault", FAULTS)
def test_native_admission_rejects_resealed_contradiction(tmp_path, entry, fault):
    record = contradictory_record(fault)
    before = deepcopy(record)
    store = MiLearningEvidenceStoreV1(tmp_path / "synthetic-store")
    if entry.startswith("cold_"):
        path = store.store_root / record["mi_learning_evidence_id"] / RECORD_FILENAME
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(record))
        stored_before = path.read_bytes()
    with pytest.raises(ValueError):
        if entry == "validate":
            validate_mi_learning_evidence_record_v1(record)
        elif entry == "export":
            export_mi_learning_evidence_onto_learning_path_v1(record)
        elif entry == "append":
            store.append(record)
        elif entry == "cold_get":
            MiLearningEvidenceStoreV1(store.store_root).get(record["mi_learning_evidence_id"])
        else:
            MiLearningEvidenceStoreV1(store.store_root).list_records()
    assert record == before
    if entry == "append":
        assert not store.store_root.exists()
    if entry.startswith("cold_"):
        assert path.read_bytes() == stored_before


@pytest.mark.parametrize("fault", ["finalized_without_outcome", "unknown_evaluability"])
def test_conditioned_contradiction_cannot_terminate_at_adjudicator(tmp_path, fault):
    original, context = native_record("conditioned")
    record = contradictory_record(fault, original)
    termination = default_termination_context_from_market_context_v1(
        context, market_observation_epoch=0
    )
    with pytest.raises(ValueError):
        terminate_learning_conditioned_evaluative_at_a_v1(record, termination=termination)


@pytest.mark.parametrize("fault", ["finalized_without_outcome", "unknown_evaluability"])
def test_existing_optional_m4_export_rejects_incoherent_receipt(tmp_path, fault):
    request = _intake_request(tmp_path / "native-ddo")
    original, _ = native_record()
    exported = plain_v1(
        export_mi_learning_evidence_onto_learning_path_v1(
            original, legacy_learning_evidence=request.legacy_learning_evidence
        )
    )
    assert (
        validate_mi_enriched_m4_intake_v1(replace(request, mi_learning_evidence_export=exported))[
            "status"
        ]
        == INTAKE_STATUS_ACCEPTED
    )
    record = contradictory_record(fault, original)
    exported["mi_learning_evidence"] = record
    exported["consumer_route"]["mi_learning_evidence_id"] = record["mi_learning_evidence_id"]
    result = validate_mi_enriched_m4_intake_v1(
        replace(request, mi_learning_evidence_export=exported)
    )
    assert result["status"] == INTAKE_STATUS_REJECTED_MI_INPUT
    assert str(result["reason"]).startswith("MI_LEARNING_EXPORT_INVALID:")


def valid_packet(root, variant):
    record, context = native_record(variant)
    store = MiLearningEvidenceStoreV1(root)
    stored = plain_v1(store.append(record))
    cold = MiLearningEvidenceStoreV1(root)
    loaded = plain_v1(cold.get(record["mi_learning_evidence_id"]))
    replay = plain_v1(cold.append(json.loads(json.dumps(record))))
    assert record == stored == loaded == replay == plain_v1(cold.list_records()[0])
    packet = {
        "record": record,
        "export": plain_v1(export_mi_learning_evidence_onto_learning_path_v1(loaded)),
    }
    if context is not None:
        termination = default_termination_context_from_market_context_v1(
            context, market_observation_epoch=0
        )
        packet["p5_adapter"] = asdict(
            adapt_learning_conditioned_evaluative_v1(loaded, termination=termination)
        )
    return packet


@pytest.mark.parametrize("variant", VARIANTS)
def test_original_receipts_retain_readback_replay_and_abstention(tmp_path, variant):
    packet = valid_packet(tmp_path / "synthetic-store", variant)
    record = packet["record"]
    assert record["mi_learning_evidence_authority"] == "NONE"
    assert record["productive_ddo_reducer_mutated"] is False
    if "missing" in variant:
        assert record["outcome_finalization_status"] == "INCOMPLETE"
        assert record["actual_outcome_ref"] is None
        assert record["evaluability"] == "NOT_EVALUABLE"
        assert record["calibration_method"] == "NONE"
    elif variant == "insufficient":
        assert record["outcome_finalization_status"] == "FINALIZED"
        assert record["actual_outcome_ref"]
        assert record["evaluability"] == "INSUFFICIENT_EVIDENCE"
        assert record["calibration_method"] == "NONE"
