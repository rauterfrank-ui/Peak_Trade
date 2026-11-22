"""M6 namespace and self-processing declarations precede bounded research routing."""

from copy import deepcopy
import json

import pytest

from src.experiments.canonical_meta_evidence_dual_router_v1 import (
    MetaEvidenceDualRouterRequestV1,
    run_meta_evidence_dual_routing_cycle_v1,
)
from src.experiments.canonical_meta_to_learning_research_adaptation_input_v1 import (
    MetaToLearningResearchAdaptationInputRequestV1,
    validate_meta_to_learning_research_adaptation_input_v1,
)
from src.experiments.canonical_meta_to_optimization_feedback_v1 import (
    MetaToOptimizationFeedbackInputRequestV1,
    validate_meta_to_optimization_feedback_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    MetaLearningEvidenceValidationError,
    validate_meta_learning_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    plain_v1,
)
from tests.experiments.test_canonical_meta_evidence_dual_router_v1 import (
    _learning_representation_meta,
)

FAULTS = {
    "domain": "foreign.learning.namespace.v1",
    "universe_class": "OPTIMIZATION_UNIVERSE",
    "evidence_class": "OPTIMIZATION_EXPERIMENT_EVIDENCE",
    "support_count": True,
    "learning_state_mutation": 0,
    "search_execution_performed": 1,
    "promotion_performed": "false",
    "external_effect_authorized": True,
    "proposal_not_authority": False,
}
OPTIONAL = (
    "universe_class",
    "evidence_class",
    "learning_state_mutation",
    "search_execution_performed",
    "promotion_performed",
    "external_effect_authorized",
    "proposal_not_authority",
)
VARIANTS = (
    "plain",
    "missing_optional",
    "null_optional",
    "annotation",
    "unknown_route",
    "mixed_route",
)


def native_meta(root):
    return plain_v1(_learning_representation_meta(root))


@pytest.mark.parametrize("field", FAULTS)
@pytest.mark.parametrize("entry", ["validate", "learning", "optimization", "router"])
def test_incoherent_typed_metadata_stops_at_native_admission(tmp_path, entry, field):
    meta = native_meta(tmp_path)
    assert meta["support_count"] == 1
    meta[field] = FAULTS[field]
    before = deepcopy(meta)
    if entry in {"validate", "router"}:
        with pytest.raises(MetaLearningEvidenceValidationError):
            if entry == "validate":
                validate_meta_learning_evidence_v1(meta)
            else:
                run_meta_evidence_dual_routing_cycle_v1(
                    MetaEvidenceDualRouterRequestV1(
                        meta_learning_evidence=meta,
                        semantic_routing_class="LEARNING_REPRESENTATION",
                    )
                )
    else:
        if entry == "learning":
            result = validate_meta_to_learning_research_adaptation_input_v1(
                MetaToLearningResearchAdaptationInputRequestV1(meta_learning_evidence=meta)
            )
        else:
            result = validate_meta_to_optimization_feedback_input_v1(
                MetaToOptimizationFeedbackInputRequestV1(meta_learning_evidence=meta)
            )
        assert result["overall_disposition"] == "NO_ACTION_FAIL_CLOSED"
        assert result["overall_reason"] == "META_LEARNING_EVIDENCE_MALFORMED"
        assert result["source_meta_evidence_id"] is None
    assert meta == before


@pytest.mark.parametrize(
    "field", ["learning_state_mutation", "search_execution_performed", "promotion_performed"]
)
def test_existing_true_processing_claim_rejection_is_preserved(tmp_path, field):
    meta = native_meta(tmp_path)
    meta[field] = True
    with pytest.raises(
        MetaLearningEvidenceValidationError, match=f"{field.upper()}_FORBIDDEN_TRUE"
    ):
        validate_meta_learning_evidence_v1(meta)


def valid_packet(root, variant):
    meta = native_meta(root)
    if variant == "missing_optional":
        for field in OPTIONAL:
            meta.pop(field)
    if variant == "null_optional":
        for field in OPTIONAL:
            meta[field] = None
    if variant == "annotation":
        meta["provenance"]["source_note"] = "synthetic.original.annotation"
    routing = {"unknown_route": "UNKNOWN", "mixed_route": "MIXED"}.get(
        variant, "LEARNING_REPRESENTATION"
    )
    original = deepcopy(meta)
    validated = plain_v1(validate_meta_learning_evidence_v1(json.loads(json.dumps(meta))))
    learning = plain_v1(
        validate_meta_to_learning_research_adaptation_input_v1(
            MetaToLearningResearchAdaptationInputRequestV1(meta_learning_evidence=meta)
        )
    )
    optimization = plain_v1(
        validate_meta_to_optimization_feedback_input_v1(
            MetaToOptimizationFeedbackInputRequestV1(meta_learning_evidence=meta)
        )
    )
    request = MetaEvidenceDualRouterRequestV1(
        meta_learning_evidence=meta, semantic_routing_class=routing
    )
    cycle = plain_v1(run_meta_evidence_dual_routing_cycle_v1(request))
    assert plain_v1(run_meta_evidence_dual_routing_cycle_v1(request)) == cycle
    assert validated == meta == original
    assert learning["learning_state_mutation_performed"] is False
    assert optimization["authorized_productive_surfaces"] == 0
    if variant in {"unknown_route", "mixed_route"}:
        assert cycle["routing_result"]["route"] == "NONE_FAIL_CLOSED"
        assert cycle["routing_result"]["learning_consumer_invoked"] is False
    else:
        assert cycle["routing_result"]["learning_consumer_invoked"] is True
    return {"meta": meta, "learning": learning, "optimization": optimization, "cycle": cycle}


@pytest.mark.parametrize("variant", VARIANTS)
def test_original_unknowns_optional_metadata_and_routing_survive(tmp_path, variant):
    packet = valid_packet(tmp_path, variant)
    assert packet["meta"]["uncertainty"] == "UNKNOWN_UNAVAILABLE"
    assert packet["meta"]["predictive_evidence_features"] == "UNKNOWN_UNAVAILABLE"
    assert packet["meta"]["provenance"]["canonical_analyzer_invoked"] is False
