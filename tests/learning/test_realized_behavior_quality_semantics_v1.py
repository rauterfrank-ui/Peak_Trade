"""Declared behavior quality is consumed by attribution outside the behavior hash."""

from copy import deepcopy
from dataclasses import asdict, replace
import json

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    phase_25_dp_attribution_evidence_v1 as attribution,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    plain_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.loop_a_conditioned_learning_evidence_v1 import (
    compose_conditioned_mi_learning_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_ingest_v1 import (
    MiLearningEvidenceIngestRequestV1,
    ingest_mi_learning_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_store_v1 import (
    MiLearningEvidenceStoreV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.realized_behavior_v1 import (
    validate_realized_behavior_v1,
    RealizedBehaviorError,
)
from tests.learning.test_conditioned_learning_exact_clock_v1 import _case
from tests.learning.test_dp_attribution_original_evidence_binding_v1 import native_request

FAULTS = (
    "join_status",
    "market_context_authority",
    "realized_behavior_authority",
    "n_bars_backbone_semantics",
    "no_duplicate_outcome_truth",
    "outcome_fields_mutated",
    "numeric_true",
    "numeric_false",
    "partial_quality",
    "malformed_quality",
)
VARIANTS = ("plain", "missing_quality", "null_quality", "annotation")


def quality_variant(record, variant):
    record = deepcopy(plain_v1(record))
    if variant == "missing_quality":
        record.pop("quality_state")
    elif variant == "null_quality":
        record["quality_state"] = None
    elif variant == "annotation":
        record["quality_state"]["source_note"] = "synthetic.original.annotation"
    return record


def contradictory_quality(record, fault):
    record = quality_variant(record, "plain")
    if fault == "partial_quality":
        record["quality_state"].pop("outcome_fields_mutated")
    elif fault == "malformed_quality":
        record["quality_state"] = "PASS"
    else:
        key, value = {
            "join_status": ("join_status", "OUTCOME_INCOMPLETE"),
            "market_context_authority": ("market_context_authority", "TRADING"),
            "realized_behavior_authority": ("realized_behavior_authority", "TRADING"),
            "n_bars_backbone_semantics": ("n_bars_backbone_semantics", "CLOCK_TIME"),
            "no_duplicate_outcome_truth": ("no_duplicate_outcome_truth", False),
            "outcome_fields_mutated": ("outcome_fields_mutated", True),
            "numeric_true": ("no_duplicate_outcome_truth", 1),
            "numeric_false": ("outcome_fields_mutated", 0),
        }[fault]
        record["quality_state"][key] = value
    return record


@pytest.mark.parametrize("fault", FAULTS)
@pytest.mark.parametrize("entry", ["validate", "ingest", "attribution"])
def test_inconsistent_quality_cannot_reach_consumer(tmp_path, monkeypatch, fault, entry):
    inputs = _case()
    request, _ = native_request()
    original = request.realized_behavior if entry == "attribution" else inputs.realized_behavior
    record = contradictory_quality(original, fault)
    assert record["behavior_id"] == original["behavior_id"]
    assert record["content_digest"] == original["content_digest"]
    before = deepcopy(record)
    calls = []
    native = attribution.build_decision_attribution_evidence_v1

    def phase14(*args, **kwargs):
        calls.append("phase14")
        return native(*args, **kwargs)

    monkeypatch.setattr(attribution, "build_decision_attribution_evidence_v1", phase14)
    if entry == "attribution":
        result = attribution.compose_dp_attribution_evidence_v1(
            replace(request, realized_behavior=record)
        )
        assert result.disposition == attribution.DpAttributionDisposition.REJECTED
        assert result.attribution_evidence is None
        assert result.phase_14_result_digest is None
        assert len(result.reason_codes) == 1
        assert result.reason_codes[0].startswith("REALIZED_BEHAVIOR_QUALITY_")
        assert calls == []
    else:
        with pytest.raises(RealizedBehaviorError, match="REALIZED_BEHAVIOR_QUALITY_"):
            if entry == "validate":
                validate_realized_behavior_v1(record)
            else:
                ingest_mi_learning_evidence_v1(
                    tmp_path / "never-written",
                    MiLearningEvidenceIngestRequestV1(
                        **asdict(replace(inputs, realized_behavior=record))
                    ),
                )
    assert record == before
    assert not (tmp_path / "never-written").exists()


def valid_packet(root, variant):
    request, _ = native_request()
    behavior = quality_variant(request.realized_behavior, variant)
    request = replace(request, realized_behavior=behavior)
    validated = plain_v1(validate_realized_behavior_v1(json.loads(json.dumps(behavior))))
    result = attribution.compose_dp_attribution_evidence_v1(request)
    assert result.disposition == attribution.DpAttributionDisposition.ATTRIBUTED
    assert attribution.replay_dp_attribution_evidence_v1(request, result)
    inspection = attribution.inspect_dp_attribution_evidence_v1(result.attribution_evidence)
    quality = result.attribution_evidence["quality_refs"]["realized_behavior_quality_state"]
    assert quality == behavior.get("quality_state")
    assert result.attribution_evidence["quality_missing_explicit"][
        "realized_behavior_quality_state"
    ] == (quality is None)
    inputs = _case()
    inputs = replace(inputs, realized_behavior=quality_variant(inputs.realized_behavior, variant))
    ingest = ingest_mi_learning_evidence_v1(
        root, MiLearningEvidenceIngestRequestV1(**asdict(inputs))
    )
    stored = MiLearningEvidenceStoreV1(root).get(ingest["mi_learning_evidence_id"])
    assert (
        compose_conditioned_mi_learning_evidence_v1(inputs)["behavior_semantics_snapshot"]
        == stored["behavior_semantics_snapshot"]
    )
    return plain_v1(
        {
            "behavior": validated,
            "attribution": dict(result.attribution_evidence),
            "inspection": inspection,
            "ingest": ingest,
            "stored": stored,
        }
    )


@pytest.mark.parametrize("variant", VARIANTS)
def test_original_quality_and_explicit_missingness_survive(tmp_path, variant):
    packet = valid_packet(tmp_path, variant)
    assert packet["behavior"]["realized_behavior_authority"] == "NONE"
    assert packet["attribution"]["attribution_authority"] == "NONE"
    assert (
        packet["stored"]["behavior_semantics_snapshot"]["classical_mfe_mae_status"]
        == "SEMANTICALLY_UNRESOLVED"
    )


def incomplete_behavior():
    from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _decision, _snapshot
    from tests.learning.test_market_context_realized_behavior_join_v1 import (
        _context_for_observation,
    )
    from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
        run_offline_n_bars_horizon_pipeline_v1,
    )
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.realized_behavior_v1 import (
        RealizedBehaviorJoinInputsV1,
        join_market_context_to_realized_behavior_v1,
    )

    decision = _decision()
    snapshot = _snapshot()
    snapshot["decision_event_ref"] = decision["record_id"]
    snapshot["o4_bars"][1]["finalization_state"] = "IN_PROGRESS_BAR"
    pipe = run_offline_n_bars_horizon_pipeline_v1(
        decision, snapshot, outcome_scalar_kind="LOG_RETURN"
    )
    observation = pipe["evaluation_observation"]
    return plain_v1(
        join_market_context_to_realized_behavior_v1(
            RealizedBehaviorJoinInputsV1(
                market_context=_context_for_observation(observation),
                evaluation_observation=observation,
                measurement_evidence=None,
                o4_bars_for_path=snapshot["o4_bars"],
            )
        )
    )


def test_native_incomplete_quality_remains_incomplete():
    behavior = incomplete_behavior()
    assert plain_v1(validate_realized_behavior_v1(behavior)) == behavior
    assert behavior["quality_state"]["join_status"] == "OUTCOME_INCOMPLETE"
    assert behavior["forward_behavior"]["status"] == "UNAVAILABLE"
