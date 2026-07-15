"""Versioned score-and-ranking contract for cross_sectional_futures_pairwise_lead_lag_spillover/v1.

Binds the canonical pairwise directed spillover score formula and deterministic ranking
semantics to the ratified versioned hypothesis binding. Research-only; no runtime,
authority, selection-policy, or economic evaluation effect.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_v0 import (
    DEFAULT_FORWARD_LAG_BARS,
    DEFAULT_LAG_WINDOW_L,
    DEFAULT_SIGNAL_LAG_BARS,
    MIN_ELIGIBLE_MEMBERS,
    SCORE_FORMULA_EXPRESSION,
    SCORE_FORMULA_VERSION,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    CONFIG_REL_PATH as HYPOTHESIS_BINDING_CONFIG_REL_PATH,
    GOVERNANCE_REL_PATH as HYPOTHESIS_BINDING_GOVERNANCE_REL_PATH,
    PRIOR_LEAD_LAG_SCORE_FAMILY,
    RESEARCH_HYPOTHESIS_ID,
    RESEARCH_SCOPE,
    SCORE_FAMILY_POLICY,
    STRATEGY_FAMILY,
    STRATEGY_ID,
    STRATEGY_VERSION,
    materialize_versioned_hypothesis_binding_v0,
)

RATIFIED_HYPOTHESIS_BINDING_DIGEST = (
    "6b2a74392eda2bf1a672682aa27da3873bc25666c5d9bb34d269f785afc2b438"
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_SCORE_AND_RANKING_CONTRACT_V0=true"
)
CONTRACT_ARTIFACT_VERSION = "v0"
CONTRACT_SCHEMA_VERSION = (
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract.v0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_SCORE_AND_RANKING_CONTRACT_V0.md"
)
CONFIRM_GO = (
    "GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_SCORE_AND_RANKING_CONTRACT_"
    "IMPLEMENTATION_V0"
)
MATERIALIZATION_CONFIRM_GO = CONFIRM_GO

REQUIRED_EVIDENCE_ARTIFACTS: tuple[str, ...] = (
    "preflight.txt",
    "source_manifest_verification.txt",
    "owner_inventory.json",
    "reuse_decision.json",
    "field_classification.json",
    "score_contract.json",
    "ranking_contract.json",
    "hypothesis_binding_reference.json",
    "digest_contracts.json",
    "digest_dependency_graph.json",
    "before_after_field_diff.json",
    "semantic_identity_comparison.json",
    "cryptographic_identity_comparison.json",
    "materializer_roundtrip.txt",
    "deterministic_materialization.txt",
    "test_assertion_matrix.json",
    "test_results.txt",
    "final_report.txt",
    "MANIFEST.sha256",
)

PAIR_RANKING_FORMULA = "rank_directed_pairwise_spillover_by_strength_desc_v1"
INSTRUMENT_RANKING_FORMULA = "rank_instruments_by_net_inbound_spillover_desc_v1"
PAIR_DETERMINISTIC_TIE_BREAK = "score_desc_then_leader_id_asc_then_follower_id_asc"
INSTRUMENT_DETERMINISTIC_TIE_BREAK = "score_desc_then_instrument_id_asc"
TIE_BREAK_SCORE_SOURCE = "unrounded_internal_score"
RANKING_ENTITY_PRIMARY = "directed_pair"
RANKING_ENTITY_SECONDARY = "instrument_net_inbound_spillover"
PENDING_SELECTION_POLICY_STATUS = "PENDING_SEPARATE_IMPLEMENTATION_BINDING"

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
SOURCE_HYPOTHESIS_BINDING_BUNDLE_PREFIX = (
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_"
    "ratification_v0"
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

NEXT_RECOMMENDED_SCOPE = (
    "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_BINDING_COMPLETION_V0"
)
NEXT_OPERATOR_GO = "GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_BINDING_COMPLETION_V0"

ORCHESTRATOR_OWNER = "cross_sectional_single_slot_research_orchestrator_v0"
MANIFEST_OWNER = "scripts.ops.primary_evidence_retention_v0"
MATERIALIZER_OWNER = (
    "scripts.research."
    "materialize_cross_sectional_futures_pairwise_lead_lag_spillover_v1_"
    "score_and_ranking_contract_v0"
)
VALIDATOR_OWNER = (
    "src.research."
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0"
)
SCORE_OWNER = "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_v0"
HYPOTHESIS_BINDING_OWNER = (
    "src.research."
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0"
)


class ContractMaterializationVerdict(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    REJECTED = "REJECTED"


class ContractValidationVerdict(str, Enum):
    ACCEPTED_COMPLETE = "ACCEPTED_COMPLETE"
    REJECTED_INCOMPLETE = "REJECTED_INCOMPLETE"


@dataclass(frozen=True)
class ScoreAndRankingContractResultV0:
    verdict: ContractMaterializationVerdict
    validation_verdict: ContractValidationVerdict
    contract: dict[str, Any]
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": (
                "cross_sectional_futures_pairwise_lead_lag_spillover_v1_"
                "score_and_ranking_contract_v0"
            ),
            "score_owner": SCORE_OWNER,
            "score_formula_version": SCORE_FORMULA_VERSION,
            "schema_version": CONTRACT_SCHEMA_VERSION,
        }
    )


def build_score_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": "pairwise_spillover_score_contract.v0",
        "score_formula_version": SCORE_FORMULA_VERSION,
        "score_formula_expression": SCORE_FORMULA_EXPRESSION,
        "score_family_policy": SCORE_FAMILY_POLICY,
        "pair_definition": "ordered_directed_pairs_i_to_j_with_i_not_equal_j",
        "leader_feature_family": "lagged_return_only_v1",
        "follower_target_family": "strictly_future_return_v1",
        "pairwise_relation_output": "directed_spillover_strength",
        "graph_output": "directed_weighted_pairwise_spillover_graph",
        "lag_window_L": DEFAULT_LAG_WINDOW_L,
        "signal_lag_bars": DEFAULT_SIGNAL_LAG_BARS,
        "forward_lag_bars": DEFAULT_FORWARD_LAG_BARS,
        "minimum_eligible_members": MIN_ELIGIBLE_MEMBERS,
        "self_pair_i_equals_j_forbidden": True,
        "panel_median_benchmark_semantics_forbidden": True,
        "lead_lag_v0_score_family_reuse_forbidden": True,
        "feature_time_lt_decision_time_required": True,
        "target_time_gt_decision_time_required": True,
        "contemporaneous_target_leakage_forbidden": True,
        "forward_fill_forbidden": True,
        "unfinalized_bars_forbidden": True,
        "parameter_search_forbidden": True,
        "lag_optimization_forbidden": True,
        "threshold_optimization_forbidden": True,
    }


def build_ranking_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": "pairwise_spillover_ranking_contract.v0",
        "score_family_policy": SCORE_FAMILY_POLICY,
        "primary_ranking_entity": RANKING_ENTITY_PRIMARY,
        "secondary_ranking_entity": RANKING_ENTITY_SECONDARY,
        "pair_ranking_formula": PAIR_RANKING_FORMULA,
        "instrument_ranking_formula": INSTRUMENT_RANKING_FORMULA,
        "pair_deterministic_tie_break": PAIR_DETERMINISTIC_TIE_BREAK,
        "instrument_deterministic_tie_break": INSTRUMENT_DETERMINISTIC_TIE_BREAK,
        "tie_break_score_source": TIE_BREAK_SCORE_SOURCE,
        "minimum_rankable_pair_count_required": True,
        "minimum_eligible_members_for_rank": MIN_ELIGIBLE_MEMBERS,
        "missing_pair_policy": "exclude_non_finite_pair_for_epoch",
        "insufficient_panel_policy": "FAIL_CLOSED_EMPTY_RANKING",
        "finalized_bar_only": True,
        "selection_policy_binding_status": PENDING_SELECTION_POLICY_STATUS,
        "aggregation_policy_binding_status": PENDING_SELECTION_POLICY_STATUS,
        "holding_policy_binding_status": PENDING_SELECTION_POLICY_STATUS,
        "exit_policy_binding_status": PENDING_SELECTION_POLICY_STATUS,
        "portfolio_weighting_policy_binding_status": PENDING_SELECTION_POLICY_STATUS,
        "panel_median_benchmark_ranking_forbidden": True,
        "lead_lag_v0_ranking_formula_reuse_forbidden": True,
    }


def build_hypothesis_binding_reference_v0(
    hypothesis_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    binding = (
        hypothesis_binding
        if hypothesis_binding is not None
        else materialize_versioned_hypothesis_binding_v0()
    )
    return {
        "schema_version": "hypothesis_binding_reference.v0",
        "research_scope": binding["research_scope"],
        "hypothesis_id": binding["hypothesis_id"],
        "hypothesis_binding_digest": binding["binding_digest"],
        "hypothesis_binding_config_ref": HYPOTHESIS_BINDING_CONFIG_REL_PATH,
        "hypothesis_binding_governance_ref": HYPOTHESIS_BINDING_GOVERNANCE_REL_PATH,
        "hypothesis_binding_owner": HYPOTHESIS_BINDING_OWNER,
        "hypothesis_binding_mutated": False,
        "dataset_digest": binding["dataset_digest"],
        "universe_digest": binding["universe_digest"],
        "period_binding_digest": binding["period_binding_digest"],
    }


def build_digest_dependency_graph_v0(
    *,
    config_digest: str,
    implementation_digest: str,
    contract_digest: str,
    hypothesis_binding_digest: str,
) -> dict[str, Any]:
    return {
        "schema_version": "transitive_digest_graph.v0",
        "edges": [
            {"from": "score_contract", "to": "config_digest"},
            {"from": "ranking_contract", "to": "config_digest"},
            {"from": "hypothesis_binding_reference", "to": "config_digest"},
            {"from": "implementation_digest", "to": "contract_digest"},
            {"from": "config_digest", "to": "contract_digest"},
            {"from": "hypothesis_binding_digest", "to": "contract_digest"},
        ],
        "component_digests": {
            "implementation_digest": implementation_digest,
            "config_digest": config_digest,
            "hypothesis_binding_digest": hypothesis_binding_digest,
            "contract_digest": contract_digest,
        },
    }


def materialize_score_and_ranking_contract_v0(
    hypothesis_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    binding = (
        hypothesis_binding
        if hypothesis_binding is not None
        else materialize_versioned_hypothesis_binding_v0()
    )
    score_contract = build_score_contract_v0()
    ranking_contract = build_ranking_contract_v0()
    hypothesis_reference = build_hypothesis_binding_reference_v0(binding)

    config_digest = _stable_digest(
        {
            "score_contract": score_contract,
            "ranking_contract": ranking_contract,
            "hypothesis_binding_reference": hypothesis_reference,
        }
    )
    implementation_digest = compute_implementation_digest_v0()
    contract_digest = _stable_digest(
        {
            "config_digest": config_digest,
            "implementation_digest": implementation_digest,
            "hypothesis_binding_digest": hypothesis_reference["hypothesis_binding_digest"],
        }
    )

    return {
        "artifact_kind": (
            "cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract"
        ),
        "artifact_version": CONTRACT_ARTIFACT_VERSION,
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "strategy_family": STRATEGY_FAMILY,
        "research_hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "research_scope": RESEARCH_SCOPE,
        "score_family_policy": SCORE_FAMILY_POLICY,
        "score_contract": score_contract,
        "ranking_contract": ranking_contract,
        "hypothesis_binding_reference": hypothesis_reference,
        "implementation_digest": implementation_digest,
        "config_digest": config_digest,
        "contract_digest": contract_digest,
        "hypothesis_binding_digest": hypothesis_reference["hypothesis_binding_digest"],
        "digest_dependency_graph": build_digest_dependency_graph_v0(
            config_digest=config_digest,
            implementation_digest=implementation_digest,
            contract_digest=contract_digest,
            hypothesis_binding_digest=hypothesis_reference["hypothesis_binding_digest"],
        ),
        "system_constraints": {
            "futures_only": True,
            "bitcoin_direction_allowed": False,
            "spot_allowed": False,
            "synthetic_spot_allowed": False,
            "offline_only": True,
            "no_runtime": True,
            "no_economic_evaluation": True,
            "hypothesis_binding_mutated": False,
            "dataset_mutated": False,
            "selection_policy_deferred": True,
            "aggregation_policy_deferred": True,
        },
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "economic_evaluation_executed": False,
        "orchestrator_owner": ORCHESTRATOR_OWNER,
        "runner_decision": {
            "schema_version": "runner_decision.v0",
            "runner_required": True,
            "runner_action": "DEFER_TO_BINDING_COMPLETION_SCOPE",
            "evaluation_executed": False,
            "economic_evaluation_executed": False,
            "next_recommended_scope": NEXT_RECOMMENDED_SCOPE,
            "next_operator_go": NEXT_OPERATOR_GO,
        },
    }


def validate_score_contract_v0(score_contract: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if score_contract.get("score_formula_version") != SCORE_FORMULA_VERSION:
        reasons.append("SCORE_FORMULA_VERSION_MISMATCH")
    if score_contract.get("score_family_policy") != SCORE_FAMILY_POLICY:
        reasons.append("SCORE_FAMILY_POLICY_MISMATCH")
    if score_contract.get("panel_median_benchmark_semantics_forbidden") is not True:
        reasons.append("PANEL_MEDIAN_BENCHMARK_NOT_FORBIDDEN")
    if score_contract.get("lead_lag_v0_score_family_reuse_forbidden") is not True:
        reasons.append("LEAD_LAG_V0_SCORE_FAMILY_REUSE_NOT_FORBIDDEN")
    if score_contract.get("self_pair_i_equals_j_forbidden") is not True:
        reasons.append("SELF_PAIR_NOT_FORBIDDEN")
    if score_contract.get("feature_time_lt_decision_time_required") is not True:
        reasons.append("FEATURE_TIME_ORDERING_NOT_REQUIRED")
    if score_contract.get("target_time_gt_decision_time_required") is not True:
        reasons.append("TARGET_TIME_ORDERING_NOT_REQUIRED")
    if score_contract.get("forward_fill_forbidden") is not True:
        reasons.append("FORWARD_FILL_NOT_FORBIDDEN")
    if score_contract.get("unfinalized_bars_forbidden") is not True:
        reasons.append("UNFINALIZED_BARS_NOT_FORBIDDEN")
    if score_contract.get("lag_optimization_forbidden") is not True:
        reasons.append("LAG_OPTIMIZATION_NOT_FORBIDDEN")
    return not reasons, tuple(dict.fromkeys(reasons))


def validate_ranking_contract_v0(
    ranking_contract: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if ranking_contract.get("pair_ranking_formula") != PAIR_RANKING_FORMULA:
        reasons.append("PAIR_RANKING_FORMULA_MISMATCH")
    if ranking_contract.get("instrument_ranking_formula") != INSTRUMENT_RANKING_FORMULA:
        reasons.append("INSTRUMENT_RANKING_FORMULA_MISMATCH")
    if ranking_contract.get("pair_deterministic_tie_break") != PAIR_DETERMINISTIC_TIE_BREAK:
        reasons.append("PAIR_TIE_BREAK_MISMATCH")
    if (
        ranking_contract.get("instrument_deterministic_tie_break")
        != INSTRUMENT_DETERMINISTIC_TIE_BREAK
    ):
        reasons.append("INSTRUMENT_TIE_BREAK_MISMATCH")
    if ranking_contract.get("tie_break_score_source") != TIE_BREAK_SCORE_SOURCE:
        reasons.append("TIE_BREAK_SCORE_SOURCE_MISMATCH")
    if ranking_contract.get("panel_median_benchmark_ranking_forbidden") is not True:
        reasons.append("PANEL_MEDIAN_BENCHMARK_RANKING_NOT_FORBIDDEN")
    if ranking_contract.get("lead_lag_v0_ranking_formula_reuse_forbidden") is not True:
        reasons.append("LEAD_LAG_V0_RANKING_FORMULA_REUSE_NOT_FORBIDDEN")
    for field in (
        "selection_policy_binding_status",
        "aggregation_policy_binding_status",
        "holding_policy_binding_status",
        "exit_policy_binding_status",
        "portfolio_weighting_policy_binding_status",
    ):
        if ranking_contract.get(field) != PENDING_SELECTION_POLICY_STATUS:
            reasons.append(f"PENDING_POLICY_NOT_EXPLICIT:{field}")
    return not reasons, tuple(dict.fromkeys(reasons))


def validate_score_and_ranking_contract_v0(
    envelope: Mapping[str, Any],
) -> tuple[ContractValidationVerdict, tuple[str, ...]]:
    reasons: list[str] = []
    if envelope.get("contract_digest") != _stable_digest(
        {
            "config_digest": envelope.get("config_digest"),
            "implementation_digest": envelope.get("implementation_digest"),
            "hypothesis_binding_digest": envelope.get("hypothesis_binding_digest"),
        }
    ):
        reasons.append("CONTRACT_DIGEST_MISMATCH")

    score_ok, score_reasons = validate_score_contract_v0(envelope.get("score_contract", {}))
    if not score_ok:
        reasons.extend(score_reasons)

    ranking_ok, ranking_reasons = validate_ranking_contract_v0(envelope.get("ranking_contract", {}))
    if not ranking_ok:
        reasons.extend(ranking_reasons)

    hypothesis_ref = envelope.get("hypothesis_binding_reference", {})
    if hypothesis_ref.get("hypothesis_binding_digest") != RATIFIED_HYPOTHESIS_BINDING_DIGEST:
        reasons.append("HYPOTHESIS_BINDING_DIGEST_MISMATCH")
    if hypothesis_ref.get("hypothesis_binding_mutated") is not False:
        reasons.append("HYPOTHESIS_BINDING_MUTATED")
    if envelope.get("hypothesis_binding_digest") != RATIFIED_HYPOTHESIS_BINDING_DIGEST:
        reasons.append("ENVELOPE_HYPOTHESIS_BINDING_DIGEST_MISMATCH")

    if envelope.get("score_family_policy") != SCORE_FAMILY_POLICY:
        reasons.append("SCORE_FAMILY_POLICY_MISMATCH")
    if envelope.get("research_scope") != RESEARCH_SCOPE:
        reasons.append("RESEARCH_SCOPE_MISMATCH")

    constraints = envelope.get("system_constraints", {})
    if constraints.get("hypothesis_binding_mutated") is not False:
        reasons.append("HYPOTHESIS_BINDING_MUTATION_FLAG_FALSE")
    if constraints.get("dataset_mutated") is not False:
        reasons.append("DATASET_MUTATION_FLAG_FALSE")
    if constraints.get("selection_policy_deferred") is not True:
        reasons.append("SELECTION_POLICY_NOT_DEFERRED")

    if envelope.get("economic_evaluation_executed") is not False:
        reasons.append("ECONOMIC_EVALUATION_EXECUTED")
    if envelope.get("runtime_effect") != "NONE":
        reasons.append("RUNTIME_EFFECT_NOT_NONE")
    if envelope.get("authority_effect") != "NONE":
        reasons.append("AUTHORITY_EFFECT_NOT_NONE")

    unique = tuple(dict.fromkeys(reasons))
    if unique:
        return ContractValidationVerdict.REJECTED_INCOMPLETE, unique
    return ContractValidationVerdict.ACCEPTED_COMPLETE, ()


def validate_contract_rejections_v0(
    envelope: Mapping[str, Any],
    *,
    mutated_field: str,
    mutated_value: Any,
) -> tuple[bool, tuple[str, ...]]:
    mutated = deepcopy(dict(envelope))
    if mutated_field.startswith("score."):
        mutated.setdefault("score_contract", {})[mutated_field.split(".", 1)[1]] = mutated_value
    elif mutated_field.startswith("ranking."):
        mutated.setdefault("ranking_contract", {})[mutated_field.split(".", 1)[1]] = mutated_value
    else:
        mutated[mutated_field] = mutated_value
    verdict, reasons = validate_score_and_ranking_contract_v0(mutated)
    return verdict is ContractValidationVerdict.REJECTED_INCOMPLETE, reasons


def validate_lead_lag_v0_score_family_not_reused_v0(
    envelope: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    score_contract = envelope.get("score_contract", {})
    if score_contract.get("score_formula_version") == PRIOR_LEAD_LAG_SCORE_FAMILY:
        reasons.append("LEAD_LAG_V0_SCORE_FAMILY_REUSED")
    if score_contract.get("score_family_policy") == PRIOR_LEAD_LAG_SCORE_FAMILY:
        reasons.append("LEAD_LAG_V0_SCORE_FAMILY_POLICY_REUSED")
    return not reasons, tuple(dict.fromkeys(reasons))


def materialize_and_validate_score_and_ranking_contract_v0() -> ScoreAndRankingContractResultV0:
    contract = materialize_score_and_ranking_contract_v0()
    validation_verdict, fail_reasons = validate_score_and_ranking_contract_v0(contract)
    verdict = (
        ContractMaterializationVerdict.COMPLETE
        if validation_verdict is ContractValidationVerdict.ACCEPTED_COMPLETE
        else ContractMaterializationVerdict.INCOMPLETE
    )
    return ScoreAndRankingContractResultV0(
        verdict=verdict,
        validation_verdict=validation_verdict,
        contract=contract,
        fail_reasons=fail_reasons,
    )


def serialize_score_and_ranking_contract_json_v0(envelope: Mapping[str, Any]) -> str:
    return json.dumps(envelope, indent=2, sort_keys=True) + "\n"


def materializer_to_binder_roundtrip_v0(envelope: Mapping[str, Any]) -> dict[str, Any]:
    roundtrip = json.loads(serialize_score_and_ranking_contract_json_v0(envelope))
    validation_verdict, fail_reasons = validate_score_and_ranking_contract_v0(roundtrip)
    return {
        "materializer_to_binder_roundtrip_pass": (
            validation_verdict is ContractValidationVerdict.ACCEPTED_COMPLETE
            and roundtrip.get("contract_digest") == envelope.get("contract_digest")
        ),
        "validation_verdict": validation_verdict.value,
        "fail_reasons": list(fail_reasons),
    }


def build_owner_inventory() -> dict[str, Any]:
    return {
        "schema_version": "owner_inventory.v0",
        "hypothesis_binding_owner": HYPOTHESIS_BINDING_OWNER,
        "score_owner": SCORE_OWNER,
        "score_and_ranking_contract_owner": VALIDATOR_OWNER,
        "ranking_contract_owner": VALIDATOR_OWNER,
        "materializer_owner": MATERIALIZER_OWNER,
        "binder_validator_owner": VALIDATOR_OWNER,
        "manifest_owner": MANIFEST_OWNER,
        "registry_progress_owner": ORCHESTRATOR_OWNER,
        "tests_owner": (
            "tests.research."
            "test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_"
            "score_and_ranking_contract_v0_contract"
        ),
        "evidence_materializer_owner": MATERIALIZER_OWNER,
        "downstream_canonical_entry_point": VALIDATOR_OWNER,
        "parallel_owner_created": False,
    }


def build_reuse_decision() -> dict[str, Any]:
    return {
        "schema_version": "reuse_decision.v0",
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "decision_ladder": "REUSE_AS_IS -> REUSE_WITH_NARROW_ADAPTER",
        "hypothesis_binding_owner": HYPOTHESIS_BINDING_OWNER,
        "score_owner": SCORE_OWNER,
        "hypothesis_binding_reuse": "REUSE_AS_IS",
        "hypothesis_binding_mutated": False,
        "dataset_reuse": "REUSE_AS_IS",
        "universe_reuse": "REUSE_AS_IS",
        "period_split_reuse": "REUSE_AS_IS",
        "lead_lag_v0_score_family_reuse_forbidden": True,
        "new_parallel_owner_created": False,
    }


def build_field_classification_v0() -> dict[str, Any]:
    return {
        "schema_version": "field_classification.v0",
        "semantic_score_fields": [
            "score_formula_version",
            "score_formula_expression",
            "leader_feature_family",
            "follower_target_family",
            "pairwise_relation_output",
        ],
        "semantic_ranking_fields": [
            "pair_ranking_formula",
            "instrument_ranking_formula",
            "pair_deterministic_tie_break",
            "instrument_deterministic_tie_break",
        ],
        "pending_implementation_fields": [
            "selection_policy_binding_status",
            "aggregation_policy_binding_status",
            "holding_policy_binding_status",
            "exit_policy_binding_status",
            "portfolio_weighting_policy_binding_status",
        ],
        "cryptographic_reference_fields": [
            "hypothesis_binding_digest",
            "contract_digest",
            "config_digest",
            "implementation_digest",
        ],
        "unclassified_changed_field_count": 0,
    }


def build_semantic_identity_comparison_v0(
    *,
    prior_envelope: Mapping[str, Any],
    new_envelope: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "semantic_identity_comparison.v0",
        "prior_scope": prior_envelope.get("research_scope"),
        "new_scope": new_envelope.get("research_scope"),
        "prior_score_family": prior_envelope.get("score_family_policy"),
        "new_score_family": new_envelope.get("score_family_policy"),
        "score_contract_added": True,
        "ranking_contract_added": True,
        "hypothesis_binding_unchanged": (
            prior_envelope.get("binding_digest") == new_envelope.get("hypothesis_binding_digest")
        ),
    }


def build_cryptographic_identity_comparison_v0(
    *,
    prior_envelope: Mapping[str, Any],
    new_envelope: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "cryptographic_identity_comparison.v0",
        "prior_hypothesis_binding_digest": prior_envelope.get("binding_digest"),
        "new_hypothesis_binding_digest": new_envelope.get("hypothesis_binding_digest"),
        "hypothesis_binding_identity_unchanged": (
            prior_envelope.get("binding_digest") == new_envelope.get("hypothesis_binding_digest")
        ),
        "new_contract_digest": new_envelope.get("contract_digest"),
        "contract_identity_independent": True,
    }


def build_before_after_field_diff_v0(
    *,
    prior_envelope: Mapping[str, Any],
    new_envelope: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    compare = (
        (
            "score_contract",
            None,
            new_envelope.get("score_contract", {}).get("score_formula_version"),
        ),
        (
            "ranking_contract",
            None,
            new_envelope.get("ranking_contract", {}).get("pair_ranking_formula"),
        ),
        (
            "hypothesis_binding_digest",
            prior_envelope.get("binding_digest"),
            new_envelope.get("hypothesis_binding_digest"),
        ),
    )
    for field, prior_val, new_val in compare:
        if prior_val != new_val:
            rows.append(
                {
                    "field": field,
                    "prior_value": prior_val,
                    "new_value": new_val,
                    "change_type": "EXPECTED_SCORE_AND_RANKING_CONTRACT_ADDITION",
                }
            )
    return rows
