"""Owner-review accumulation report (no candidate ranking)."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from research.m9_s1_durable_market_session_evidence_accumulation_v1.constants_v1 import (
    ENFORCEMENT_ENABLED,
    EXTERNAL_EFFECT_AUTHORIZED,
    NUMERIC_MAX_AGE_DECIDED,
    OWNER_REVIEW_SCHEMA_VERSION,
    PRODUCTIVE_PARAMETER_MUTATED,
    SELECTION_READINESS_INSUFFICIENT,
    SELECTION_RESULT_UNRESOLVED,
    WORKPACKAGE_ID,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.models_v1 import (
    ObservationSourceClassV1,
    digest_excluding_keys,
)


def _dominant_source_class(source_class_counts: Mapping[str, int]) -> str:
    if not source_class_counts:
        return "MISSING"
    return max(source_class_counts.items(), key=lambda item: item[1])[0]


def _real_market_observation_count(source_class_counts: Mapping[str, int]) -> int:
    real_classes = {
        ObservationSourceClassV1.LIVE_OBSERVED.value,
        ObservationSourceClassV1.TESTNET_OBSERVED.value,
        ObservationSourceClassV1.SHADOW_OBSERVED.value,
    }
    return sum(int(source_class_counts.get(label, 0)) for label in real_classes)


def build_owner_review_accumulation_report_v1(
    *,
    data_quality: Mapping[str, Any],
    counterfactual_replay: Mapping[str, Any],
    source_class_counts: Mapping[str, int],
    repository_sha: str,
    pipeline_flags: Mapping[str, bool],
) -> dict[str, Any]:
    real_obs = _real_market_observation_count(source_class_counts)
    dominant = _dominant_source_class(source_class_counts)
    selection_readiness = SELECTION_READINESS_INSUFFICIENT
    if real_obs > 0:
        selection_readiness = "PARTIAL_REAL_EVIDENCE_ACCUMULATED"

    per_candidate_reports: list[dict[str, Any]] = []
    for row in counterfactual_replay.get("per_candidate") or []:
        if not isinstance(row, dict):
            continue
        per_candidate_reports.append(
            {
                "candidate_max_age_seconds": row.get("candidate_max_age_seconds"),
                "would_be_fresh_count": row.get("would_be_fresh_count"),
                "would_be_fresh_rate": row.get("would_be_fresh_rate"),
                "would_be_stale_count": row.get("would_be_stale_count"),
                "would_be_stale_rate": row.get("would_be_stale_rate"),
                "coverage": {
                    "observation_count": row.get("observation_count"),
                    "valid_age_count": row.get("valid_age_count"),
                    "session_coverage_count": row.get("session_coverage_count"),
                    "temporal_coverage": row.get("temporal_coverage"),
                },
                "reproducibility": {
                    "input_record_digest": counterfactual_replay.get("input_record_digest"),
                    "artifact_digest": counterfactual_replay.get("artifact_digest"),
                },
                "evidence_completeness": {
                    "real_market_observation_count": real_obs,
                    "dominant_source_class": dominant,
                },
                "selection_eligibility": "NOT_ELIGIBLE_FOR_DETERMINISTIC_PROPOSAL",
            }
        )

    report = {
        "schema_version": OWNER_REVIEW_SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "repository_sha": repository_sha,
        "EVIDENCE_SOURCE_CLASS": dominant,
        "SESSION_COUNT": data_quality.get("session_count"),
        "OBSERVATION_COUNT": data_quality.get("observation_count"),
        "TEMPORAL_COVERAGE": data_quality.get("temporal_coverage"),
        "MISSING_DATA": {
            "missing_computed_age_count": data_quality.get("missing_computed_age_count"),
            "missing_estimate_count": data_quality.get("missing_estimate_count"),
        },
        "DATA_QUALITY_RAW_METRICS": data_quality,
        "per_candidate": per_candidate_reports,
        "OOS_EVIDENCE_STATUS": "MISSING" if real_obs == 0 else "UNRESOLVED_CRITERION",
        "ROBUSTNESS_EVIDENCE_STATUS": "MISSING" if real_obs == 0 else "UNRESOLVED_CRITERION",
        "ECONOMIC_EVIDENCE_STATUS": "MISSING_OR_NOT_IN_SCOPE",
        "FAILURE_EVIDENCE_STATUS": "MISSING" if real_obs == 0 else "UNRESOLVED_CRITERION",
        "SELECTION_READINESS": selection_readiness,
        "SELECTION_RESULT": SELECTION_RESULT_UNRESOLVED,
        "numeric_max_age_decided": NUMERIC_MAX_AGE_DECIDED,
        "productive_parameter_mutated": PRODUCTIVE_PARAMETER_MUTATED,
        "enforcement_enabled": ENFORCEMENT_ENABLED,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "pipeline_flags": dict(pipeline_flags),
        "source_class_counts": dict(source_class_counts),
        "real_market_observation_count": real_obs,
        "best_candidate": None,
        "ranking": None,
    }
    report["report_digest"] = digest_excluding_keys(report, exclude=frozenset({"report_digest"}))
    return report
