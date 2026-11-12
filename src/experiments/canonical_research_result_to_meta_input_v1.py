"""Bind existing Search/Phase-10 evidence to the existing Phase-11 analyzer.

No metrics, outcomes, stability values, thresholds or research policy are invented.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from src.experiments.canonical_advanced_search_v1 import (
    CanonicalAdvancedSearchRequestV1,
    build_canonical_advanced_search_v1,
    validate_canonical_advanced_search_v1,
)
from src.experiments.canonical_automated_offline_research_loop_v1 import (
    canonical_record_payload_v1,
    validate_canonical_automated_offline_research_loop_v1,
)
from src.experiments.canonical_comparison_ssot_v1 import (
    CanonicalComparisonRequestV1,
    ComparisonCandidateV1,
    ComparisonCompatibilityContractV1,
    build_canonical_comparison_result_v1,
    validate_canonical_comparison_result_v1,
)
from src.experiments.canonical_experiment_memory_v1 import (
    validate_canonical_experiment_memory_record_v1,
)
from src.experiments.canonical_meta_learning_v1 import (
    CanonicalMetaLearningRequestV1,
    MetaLearningExperimentUnitV1,
    MetaLearningPolicyV1,
    build_canonical_meta_learning_v1,
)
from src.experiments.canonical_robustness_suite_v1 import (
    validate_canonical_robustness_evidence_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION = "canonical_research_result_to_meta_input_v1"


class ResearchResultMetaBindingError(ValueError):
    """Existing evidence cannot support the claimed Meta input binding."""


@dataclass(frozen=True)
class ResearchResultMetaInputV1:
    search_record: Mapping[str, Any]
    research_loop_record: Mapping[str, Any]
    # Values cannot be recovered from the comparison owner's opaque digests.
    time_horizon: Mapping[str, str]
    market_universe: Sequence[str]


def _require_equal(actual: Any, expected: Any, field: str) -> None:
    if actual != expected:
        raise ResearchResultMetaBindingError(f"RESEARCH_META_BINDING_MISMATCH:{field}")


def _created_at_key(value: str) -> tuple[str, str]:
    # Both owners already validate UTC-Z timestamps, including nanosecond text.
    whole, _, fraction = value[:-1].partition(".")
    return whole, fraction.ljust(9, "0")


def _bind_unit(request: ResearchResultMetaInputV1):
    search = canonical_record_payload_v1(request.search_record)
    loop = canonical_record_payload_v1(request.research_loop_record)
    validate_canonical_advanced_search_v1(search)
    validate_canonical_automated_offline_research_loop_v1(loop)
    if _created_at_key(search["created_at"]) > _created_at_key(loop["created_at"]):
        raise ResearchResultMetaBindingError("SEARCH_AFTER_RESEARCH_EVIDENCE")
    memory = loop["experiment_record"]
    robustness = loop["robustness_evidence"]
    comparison = loop["comparison_result"]
    validate_canonical_experiment_memory_record_v1(memory)
    validate_canonical_robustness_evidence_v1(robustness)
    validate_canonical_comparison_result_v1(comparison)
    experiment_id = loop["selected_experiment_id"]
    matches = [row for row in search["candidates"] if row.get("experiment_id") == experiment_id]
    if len(matches) != 1 or matches[0].get("status") != "PROPOSED":
        raise ResearchResultMetaBindingError("SELECTED_SEARCH_CANDIDATE_UNBOUND")
    candidate = matches[0]
    identity = memory["experiment_identity"]
    for owner, payload in (("memory", memory), ("robustness", robustness)):
        _require_equal(payload["experiment_id"], experiment_id, f"{owner}.experiment_id")
        _require_equal(payload["experiment_identity"], identity, f"{owner}.identity")
        _require_equal(
            payload["hypothesis_id"], loop["selected_hypothesis_id"], f"{owner}.hypothesis_id"
        )
        _require_equal(payload["created_at"], loop["created_at"], f"{owner}.created_at")
    _require_equal(candidate["experiment_identity"], identity, "candidate.identity")
    _require_equal(
        candidate["hypothesis_id"], loop["selected_hypothesis_id"], "candidate.hypothesis_id"
    )
    _require_equal(candidate["strategy_family"], memory["strategy_family"], "strategy_family")
    _require_equal(
        candidate["parameter_region"], robustness["parameter_region"], "parameter_region"
    )
    _require_equal(comparison["right_experiment_id"], experiment_id, "comparison.experiment_id")
    _require_equal(
        comparison["right_identity_digest"], identity["identity_digest"], "comparison.identity"
    )
    _require_equal(
        candidate["offline_experiment_request"]["regime"], robustness["regime"], "regime"
    )

    # Ask Phase 5 to bind supplied values; never reinterpret its hash domains here.
    context = ComparisonCandidateV1(
        experiment_identity=identity,
        robustness_suite_version=robustness["robustness_suite_version"],
        metric_definitions=robustness["metric_definition_version"],
        time_horizon=dict(request.time_horizon),
        market_universe=list(request.market_universe),
        experiment_id=experiment_id,
    )
    expected = build_canonical_comparison_result_v1(
        CanonicalComparisonRequestV1(left=context, right=context, created_at=loop["created_at"])
    )
    actual_dimensions = {
        row["dimension"]: row["right_value"] for row in comparison["dimension_results"]
    }
    for row in expected["dimension_results"]:
        value = row["right_value"]
        if value is None:
            raise ResearchResultMetaBindingError(f"COMPARISON_CONTEXT_MISSING:{row['dimension']}")
        _require_equal(actual_dimensions[row["dimension"]], value, f"comparison.{row['dimension']}")

    unit = MetaLearningExperimentUnitV1(
        experiment_identity=identity,
        evidence_created_at=loop["created_at"],
        strategy_family=memory["strategy_family"],
        hypothesis_id=loop["selected_hypothesis_id"],
        hypothesis_kind=candidate["hypothesis_kind"],
        search_space_id=candidate["search_space_id"],
        parameter_region=dict(robustness["parameter_region"]),
        regime=robustness["regime"],
        time_horizon=dict(request.time_horizon),
        market_universe=list(request.market_universe),
        robustness_test_statuses={
            row["test_id"]: row["status"] for row in robustness["test_results"]
        },
        backtest_metrics=dict(memory["metrics"]),
        # No source-independent stability formula or later-outcome attribution.
        parameter_stability=None,
        later_outcome=None,
        metric_definitions=robustness["metric_definition_version"],
        robustness_suite_version=robustness["robustness_suite_version"],
    )
    binding = {
        "experiment_id": experiment_id,
        "search_identity": search["search_identity"],
        "search_content_sha256": search["integrity"]["content_sha256"],
        "research_loop_identity": loop["loop_identity"],
        "research_loop_content_sha256": loop["integrity"]["content_sha256"],
        "observation_binding": dict(loop["observation_binding"]),
        "robustness_content_sha256": robustness["integrity"]["content_sha256"],
        "comparison_identity": comparison["comparison_identity"],
    }
    return unit, loop["failure_records"], [loop["reality_gap_record"]], binding


def build_meta_learning_from_research_results_v1(
    inputs: Sequence[ResearchResultMetaInputV1],
    *,
    created_at: str,
    policy: MetaLearningPolicyV1,
    compatibility_contract: ComparisonCompatibilityContractV1 | None = None,
) -> Mapping[str, Any]:
    """Consume bound results, including failed research; do not execute research."""
    bound = [_bind_unit(item) for item in inputs]
    meta = build_canonical_meta_learning_v1(
        CanonicalMetaLearningRequestV1(
            units=tuple(row[0] for row in bound),
            created_at=created_at,
            policy=policy,
            failure_records=tuple(record for row in bound for record in row[1]),
            reality_gap_records=tuple(record for row in bound for record in row[2]),
            compatibility_contract=compatibility_contract,
        )
    )
    body = {
        "schema_version": SCHEMA_VERSION,
        "source_bindings": sorted((row[3] for row in bound), key=lambda row: row["experiment_id"]),
        "meta_learning_record": canonical_record_payload_v1(meta),
        "productive_apply_authorized": False,
        "research_execution_performed": False,
        "missing_parameter_stability_inferred": False,
        "missing_later_outcome_inferred": False,
    }
    body["content_digest"] = compute_content_sha256(body)
    return MappingProxyType(body)


def run_research_result_meta_search_feedback_v1(
    inputs: Sequence[ResearchResultMetaInputV1],
    *,
    created_at: str,
    policy: MetaLearningPolicyV1,
    next_search_request: CanonicalAdvancedSearchRequestV1,
    compatibility_contract: ComparisonCompatibilityContractV1 | None = None,
    archived_experiment_artifacts: Mapping[str, str] | None = None,
) -> Mapping[str, Any]:
    """One bounded feedback step into existing Search; never runs an experiment."""
    if next_search_request.meta_learning_signals or next_search_request.meta_learning_identity:
        raise ResearchResultMetaBindingError("NEXT_SEARCH_META_INPUT_ALREADY_BOUND")
    binding = build_meta_learning_from_research_results_v1(
        inputs, created_at=created_at, policy=policy, compatibility_contract=compatibility_contract
    )
    meta = binding["meta_learning_record"]
    search = build_canonical_advanced_search_v1(
        replace(
            next_search_request,
            meta_learning_signals=tuple(meta["research_proposals"]),
            meta_learning_identity=(
                meta["meta_learning_identity"] if meta["research_proposals"] else None
            ),
        ),
        archived_experiment_artifacts=archived_experiment_artifacts,
    )
    if _created_at_key(search["created_at"]) < _created_at_key(meta["created_at"]):
        raise ResearchResultMetaBindingError("NEXT_SEARCH_PRECEDES_META_EVIDENCE")
    body = {
        "schema_version": "canonical_research_result_meta_search_feedback_v1",
        "meta_input_binding": dict(binding),
        "next_search_record": canonical_record_payload_v1(search),
        "experiment_execution_performed": False,
        "productive_apply_authorized": False,
    }
    body["content_digest"] = compute_content_sha256(body)
    return MappingProxyType(body)
