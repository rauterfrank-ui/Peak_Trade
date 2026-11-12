"""Address the measured B1/B0 representation question to Learning Research."""

from src.experiments.canonical_learning_representation_research_adaptation_plan_v1 import (
    LearningRepresentationResearchAdaptationPlanRequestV1,
    build_learning_representation_research_adaptation_plan_v1,
)
from src.experiments.canonical_meta_evidence_dual_router_v1 import (
    ROUTE_LEARNING_RESEARCH,
    ROUTE_NONE_FAIL_CLOSED,
    MetaEvidenceDualRouterRequestV1,
    run_meta_evidence_dual_routing_cycle_v1,
)
from src.experiments.canonical_meta_to_learning_research_adaptation_input_v1 import (
    MetaToLearningResearchAdaptationInputRequestV1,
    validate_meta_to_learning_research_adaptation_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.meta_evidence_v1 import (
    PROVENANCE_LINEAGE_REF_KEY,
    SemanticRoutingClass,
)
from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    EVIDENCE_CLASS_META_LEARNING,
    META_LEARNING_EVIDENCE_DOMAIN,
    SCHEMA_VERSION as META_SCHEMA,
    UNKNOWN_UNAVAILABLE,
    UNIVERSE_CLASS_SELF_LEARNING,
    derive_meta_evidence_id_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    assert_offline_v1,
    bytes_v1,
    digest_v1,
    require_v1,
    seal_v1,
    validate_seal_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.phase_22_paired_market_research_v1 import (
    PROXY_FEATURE,
    SCHEMA as COMPARISON_SCHEMA,
    compare_paired_market_b1_to_b0_v1,
)

SCHEMA = "paired_market_representation_meta_handoff_v1"
MEASURED_PATTERN = "MEASURED_B1_PROXY_HOLDOUT_COMPARISON"


def _meta_learning_evidence(*, evidence, comparison, lineage_ref):
    provenance = {
        "producer": "paired_market_representation_meta_v1",
        "original_comparison_digest": evidence["original_comparison_digest"],
        "question_digest": evidence["exact_content_digest"],
        "measured_representation_question": evidence["question"],
    }
    if lineage_ref is not None:
        provenance[PROVENANCE_LINEAGE_REF_KEY] = lineage_ref
    metrics = evidence["measurement"]
    # The existing Meta envelope hashes only JSON values without floats.
    numeric = (
        {
            "codec": "exact-json-values-v1",
            "utf8": bytes_v1(metrics).decode("utf-8"),
            "sha256": digest_v1(metrics),
        }
        if metrics is not None
        else UNKNOWN_UNAVAILABLE
    )
    body = {
        "schema_version": META_SCHEMA,
        "domain": META_LEARNING_EVIDENCE_DOMAIN,
        "universe_class": UNIVERSE_CLASS_SELF_LEARNING,
        "evidence_class": EVIDENCE_CLASS_META_LEARNING,
        "source_experiment_ids": [],
        "source_envelope_versions": {"paired_market_comparison_schema": COMPARISON_SCHEMA},
        "observed_regime_or_context_ref": "mi.paired.comparison."
        + evidence["exact_content_digest"],
        "optimization_family": UNKNOWN_UNAVAILABLE,
        "search_method": UNKNOWN_UNAVAILABLE,
        "repeated_success_or_failure_pattern": (
            MEASURED_PATTERN if lineage_ref is not None else UNKNOWN_UNAVAILABLE
        ),
        "oos_robustness_pattern": {
            "observation_kind": (
                "SINGLE_CHRONOLOGICAL_HOLDOUT" if lineage_ref is not None else UNKNOWN_UNAVAILABLE
            ),
            "holdout_case_count": comparison["walk_forward_summary"]["holdout_rows"]
            if comparison
            else 0,
            "independent_quality_proven": False,
        },
        "cost_slippage_failure_pattern": UNKNOWN_UNAVAILABLE,
        "predictive_evidence_features": numeric,
        "uncertainty": UNKNOWN_UNAVAILABLE,
        "support_count": 0,
        "provenance": provenance,
        "source_optimization_experiment_evidence_record_id": None,
        "source_optimization_experiment_evidence_digest": None,
        "meta_evidence_authority": "NONE",
        "learning_state_mutation": False,
        "search_execution_performed": False,
        "promotion_performed": False,
        "external_effect_authorized": False,
        "proposal_not_authority": True,
    }
    reproducibility_digest = digest_v1(body)
    return {
        **body,
        "reproducibility_digest": reproducibility_digest,
        "meta_evidence_id": derive_meta_evidence_id_v1(
            reproducibility_digest=reproducibility_digest
        ),
    }


def route_paired_market_representation_v1(
    *,
    stored_comparison,
    fit_jobs,
    holdout_jobs,
    fit_cutoff_utc,
    evaluated_at_utc,
    validation_fraction,
):
    """Reproduce the supplied comparison from its original cases before routing."""
    assert_offline_v1()
    stored = validate_seal_v1(stored_comparison, COMPARISON_SCHEMA)
    original = compare_paired_market_b1_to_b0_v1(
        fit_jobs=fit_jobs,
        holdout_jobs=holdout_jobs,
        fit_cutoff_utc=fit_cutoff_utc,
        evaluated_at_utc=evaluated_at_utc,
        validation_fraction=validation_fraction,
    )
    require_v1(stored == original, "PAIRED_META_ORIGINAL_COMPARISON_MISMATCH")
    measured = original["status"] == "MEASURED_CHRONOLOGICAL_HOLDOUT"
    comparison = original["stage_comparison"]
    lineage, lineage_ref, metrics = None, None, None
    if measured:
        require_v1(
            comparison["stage_id"] == "B1" and comparison["predecessor_stage_id"] == "B0",
            "PAIRED_META_STAGE_MISMATCH",
        )
        lineage = {
            "baseline_information_set_id": comparison["predecessor_information_set_id"],
            "challenger_information_set_id": comparison["stage_information_set_id"],
            "additional_feature": PROXY_FEATURE,
            "additional_feature_unit": original["feature_units"][PROXY_FEATURE],
            "target_contract": original["target_contract"],
        }
        lineage_ref = "mi.learning_representation." + digest_v1(lineage)
        metrics = {
            **comparison["calibration_summary"],
            "delta_b0_minus_b1": comparison["challenger_delta"],
            "split": comparison["walk_forward_summary"],
            "declared_case_count": original["declared_case_count"],
            "paired_case_count": original["paired_case_count"],
        }
    evidence = seal_v1(
        {
            "schema_version": "paired_market_representation_question_v1",
            "authority": "NONE",
            "question": "INCREMENTAL_OOS_USEFULNESS_OF_B1_OHLCV_PROXY",
            "original_comparison_digest": original["exact_content_digest"],
            "comparison_status": original["status"],
            "comparison_reason": original.get("reason"),
            "representation_lineage_ref": lineage_ref,
            "representation_lineage": lineage,
            "target_contract": original["target_contract"],
            "fit_cutoff_utc": original["fit_cutoff_utc"],
            "evaluated_at_utc": original["evaluated_at_utc"],
            "declared_case_count": original["declared_case_count"],
            "paired_case_count": original["paired_case_count"],
            "measurement": metrics,
            "independent_quality_proven": False,
        }
    )
    nested = _meta_learning_evidence(
        evidence=evidence, comparison=comparison, lineage_ref=lineage_ref
    )
    routing_class = (
        SemanticRoutingClass.LEARNING_REPRESENTATION if measured else SemanticRoutingClass.UNKNOWN
    )
    cycle = run_meta_evidence_dual_routing_cycle_v1(
        MetaEvidenceDualRouterRequestV1(
            meta_learning_evidence=nested,
            semantic_routing_class=routing_class.value,
            classification_provenance={
                "classifier": "paired_market_representation_meta_v1",
                "original_comparison_digest": original["exact_content_digest"],
                "question_digest": evidence["exact_content_digest"],
                "classification_basis": "REPLAYED_PAIRED_REPRESENTATION_COMPARISON",
            },
        )
    )
    route = cycle["routing_result"]
    decision, plan = None, None
    if measured:
        decision = validate_meta_to_learning_research_adaptation_input_v1(
            MetaToLearningResearchAdaptationInputRequestV1(
                meta_learning_evidence=nested, expected_meta_evidence_id=nested["meta_evidence_id"]
            )
        )
        require_v1(
            route["route"] == ROUTE_LEARNING_RESEARCH
            and route["learning_consumer_result_digest"] == decision["result_digest"]
            and route["optimization_consumer_invoked"] is False,
            "PAIRED_META_LEARNING_ADMISSION_MISMATCH",
        )
        plan = build_learning_representation_research_adaptation_plan_v1(
            LearningRepresentationResearchAdaptationPlanRequestV1(
                adaptation_input_decision=decision
            )
        )
        require_v1(
            plan["learning_representation_lineage_ref"] == lineage_ref,
            "PAIRED_META_PLAN_LINEAGE_MISMATCH",
        )
    else:
        require_v1(
            route["route"] == ROUTE_NONE_FAIL_CLOSED
            and not route["learning_consumer_invoked"]
            and not route["optimization_consumer_invoked"],
            "PAIRED_META_UNKNOWN_ROUTE_MISMATCH",
        )
    return seal_v1(
        {
            "schema_version": SCHEMA,
            "authority": "NONE",
            "status": "LEARNING_RESEARCH_PLAN_READY"
            if measured
            else "UNRESOLVED_REPRESENTATION_QUESTION",
            "evidence": evidence,
            "routing_cycle": cycle,
            "learning_adaptation_decision": decision,
            "research_plan": plan,
            "productive_apply_authorized": False,
        }
    )
