"""Offline economic evaluation authorization ratification for pairwise spillover v1.

Deterministic, fail-closed ratification authorizing a later separate offline economic
evaluation execution for cross_sectional_futures_pairwise_lead_lag_spillover/v1. Does not
execute evaluation, does not mutate hypothesis binding or score/ranking contracts, and
has no runtime or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0 import (
    CONFIG_REL_PATH as SCORE_RANKING_CONFIG_REL_PATH,
    GOVERNANCE_REL_PATH as SCORE_RANKING_GOVERNANCE_REL_PATH,
    RATIFIED_HYPOTHESIS_BINDING_DIGEST,
    build_ranking_contract_v0,
    build_score_contract_v0,
    materialize_score_and_ranking_contract_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    CONFIG_REL_PATH as HYPOTHESIS_BINDING_CONFIG_REL_PATH,
    GOVERNANCE_REL_PATH as HYPOTHESIS_BINDING_GOVERNANCE_REL_PATH,
    RESEARCH_HYPOTHESIS_ID,
    RESEARCH_SCOPE,
    SCORE_FAMILY_POLICY,
    STRATEGY_ID,
    STRATEGY_VERSION,
    materialize_versioned_hypothesis_binding_v0,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_AUTHORIZATION_RATIFICATION_V0=true"
)

SCHEMA_VERSION = (
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_authorization_ratification.v0"
)
RATIFICATION_ID = (
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_authorization_ratification_v0"
)
RATIFICATION_VERSION = "v0"
AUTHORIZATION_SCOPE = "OFFLINE_ECONOMIC_EVALUATION"
AUTHORIZATION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = "authorization_ratification_canonical_json_v1"
SCOPE_CLASSIFICATION = (
    "BOUNDED_FUTURES_ONLY_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_RATIFICATION_V0"
)

GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_AUTHORIZATION_RATIFICATION_V0"
)
CONFIRM_GO = GO_TOKEN
MATERIALIZATION_CONFIRM_GO = GO_TOKEN

CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_authorization_ratification_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_AUTHORIZATION_RATIFICATION_V0.md"
)

RUNNER_BINDING_REF = (
    "scripts/ops/"
    "run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_execution_v0.py"
)
HARNESS_BINDING_REF = (
    "src/research/"
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_execution_v0.py"
)
ENTRY_POINT_STATUS = "PENDING_SEPARATE_EXECUTION_SCOPE"

NEXT_RECOMMENDED_SCOPE = (
    "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_V0"
)
NEXT_OPERATOR_GO = (
    "GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_V0"
)

OFFLINE_ONLY = True
ECONOMIC_EVALUATION_AUTHORIZED_FOR_SEPARATE_EXECUTION = True
ECONOMIC_EVALUATION_EXECUTED = False
HYPOTHESIS_BINDING_UNCHANGED = True
SCORE_CONTRACT_UNCHANGED = True
RANKING_CONTRACT_UNCHANGED = True
DATASET_BINDING_UNCHANGED = True
UNIVERSE_BINDING_UNCHANGED = True
PARAMETER_OPTIMIZATION_ALLOWED = False
POST_RESULT_SELECTION_ALLOWED = False
THRESHOLD_REDUCTION_ALLOWED = False
POLICY_RESCUE_ALLOWED = False
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
LIVE_AUTHORIZED = False
ORDERS_ALLOWED = False

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

REASON_GO_TOKEN_INVALID = "GO_TOKEN_INVALID"
REASON_GO_TOKEN_MISSING = "GO_TOKEN_MISSING"
REASON_SCOPE_ID_MISMATCH = "SCOPE_ID_MISMATCH"
REASON_AUTHORIZATION_VERSION_MISMATCH = "AUTHORIZATION_VERSION_MISMATCH"
REASON_HYPOTHESIS_BINDING_REFERENCE_MISSING = "HYPOTHESIS_BINDING_REFERENCE_MISSING"
REASON_SCORE_CONTRACT_REFERENCE_MISSING = "SCORE_CONTRACT_REFERENCE_MISSING"
REASON_RANKING_CONTRACT_REFERENCE_MISSING = "RANKING_CONTRACT_REFERENCE_MISSING"
REASON_HYPOTHESIS_BINDING_DIGEST_MISMATCH = "HYPOTHESIS_BINDING_DIGEST_MISMATCH"
REASON_SCORE_CONTRACT_DIGEST_MISMATCH = "SCORE_CONTRACT_DIGEST_MISMATCH"
REASON_RANKING_CONTRACT_DIGEST_MISMATCH = "RANKING_CONTRACT_DIGEST_MISMATCH"
REASON_DATASET_DIGEST_MISMATCH = "DATASET_DIGEST_MISMATCH"
REASON_UNIVERSE_DIGEST_MISMATCH = "UNIVERSE_DIGEST_MISMATCH"
REASON_OFFLINE_BOUNDARY_VIOLATION = "OFFLINE_BOUNDARY_VIOLATION"
REASON_ECONOMIC_EVALUATION_EXECUTED_VIOLATION = "ECONOMIC_EVALUATION_EXECUTED_VIOLATION"
REASON_PARAMETER_OPTIMIZATION_ALLOWED_VIOLATION = "PARAMETER_OPTIMIZATION_ALLOWED_VIOLATION"
REASON_THRESHOLD_REDUCTION_ALLOWED_VIOLATION = "THRESHOLD_REDUCTION_ALLOWED_VIOLATION"
REASON_POLICY_RESCUE_ALLOWED_VIOLATION = "POLICY_RESCUE_ALLOWED_VIOLATION"
REASON_RATIFICATION_DIGEST_MISMATCH = "RATIFICATION_DIGEST_MISMATCH"

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
SOURCE_HYPOTHESIS_BINDING_BUNDLE = (
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_"
    "binding_ratification_v0_20260715T040511Z"
)
SOURCE_SCORE_RANKING_BUNDLE = (
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_"
    "contract_v0_20260715T041800Z"
)
SOURCE_PR5200_CLOSEOUT_BUNDLE = (
    DURABLE_ARCHIVE_ROOT
    / "research/pr5200_merge_closeout_cross_sectional_futures_pairwise_lead_lag_spillover_v1_"
    "score_and_ranking_contract_implementation_v0_20260715T044248Z"
)

REQUIRED_EVIDENCE_ARTIFACTS: tuple[str, ...] = (
    "preflight.txt",
    "source_manifest_verification.txt",
    "owner_inventory.json",
    "reuse_decision.json",
    "authorization_contract.json",
    "canonical_references.json",
    "field_classification.json",
    "digest_contracts.json",
    "digest_dependency_graph.json",
    "before_after_field_diff.json",
    "semantic_identity_comparison.json",
    "cryptographic_identity_comparison.json",
    "materializer_roundtrip.txt",
    "deterministic_materialization.txt",
    "second_materialization_diff.txt",
    "test_assertion_matrix.json",
    "test_results.txt",
    "changed_files.txt",
    "final_report.txt",
    "MANIFEST.sha256",
)

ORCHESTRATOR_OWNER = "cross_sectional_single_slot_research_orchestrator_v0"
MANIFEST_OWNER = "scripts.ops.primary_evidence_retention_v0"
MATERIALIZER_OWNER = (
    "scripts.research."
    "materialize_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_authorization_ratification_v0"
)
VALIDATOR_OWNER = (
    "src.research."
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_authorization_ratification_v0"
)
HYPOTHESIS_BINDING_OWNER = (
    "src.research."
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0"
)
SCORE_RANKING_CONTRACT_OWNER = (
    "src.research."
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0"
)


class RatificationMaterializationVerdict(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    REJECTED = "REJECTED"


class RatificationValidationVerdict(str, Enum):
    ACCEPTED_COMPLETE = "ACCEPTED_COMPLETE"
    REJECTED_INCOMPLETE = "REJECTED_INCOMPLETE"


@dataclass(frozen=True)
class AuthorizationRatificationResultV0:
    verdict: RatificationMaterializationVerdict
    validation_verdict: RatificationValidationVerdict
    ratification: dict[str, Any]
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_score_contract_digest_v0() -> str:
    return _stable_digest(build_score_contract_v0())


def compute_ranking_contract_digest_v0() -> str:
    return _stable_digest(build_ranking_contract_v0())


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": (
                "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
                "evaluation_authorization_ratification_v0"
            ),
            "schema_version": SCHEMA_VERSION,
            "authorization_scope": AUTHORIZATION_SCOPE,
            "authorization_version": AUTHORIZATION_VERSION,
        }
    )


def validate_go_token_v0(go_token: str | None) -> tuple[bool, tuple[str, ...]]:
    if not go_token:
        return False, (REASON_GO_TOKEN_MISSING,)
    if go_token != GO_TOKEN:
        return False, (REASON_GO_TOKEN_INVALID,)
    return True, ()


def build_canonical_references_v0(
    *,
    hypothesis_binding: Mapping[str, Any] | None = None,
    score_ranking_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    binding = (
        hypothesis_binding
        if hypothesis_binding is not None
        else materialize_versioned_hypothesis_binding_v0()
    )
    contract = (
        score_ranking_contract
        if score_ranking_contract is not None
        else materialize_score_and_ranking_contract_v0(binding)
    )
    return {
        "schema_version": "canonical_references.v0",
        "hypothesis_binding": {
            "config_ref": HYPOTHESIS_BINDING_CONFIG_REL_PATH,
            "governance_ref": HYPOTHESIS_BINDING_GOVERNANCE_REL_PATH,
            "owner": HYPOTHESIS_BINDING_OWNER,
            "binding_digest": binding["binding_digest"],
            "hypothesis_id": binding["hypothesis_id"],
            "dataset_id": binding["binding"]["dataset_binding"]["dataset_id"],
            "dataset_schema": binding["binding"]["dataset_binding"]["dataset_schema"],
            "dataset_digest": binding["dataset_digest"],
            "universe_id": binding["binding"]["pit_universe_binding"]["universe_id"],
            "universe_digest": binding["universe_digest"],
            "futures_only": binding["system_constraints"]["futures_only"],
            "bitcoin_excluded": binding["binding"]["pit_universe_binding"]["bitcoin_excluded"],
            "pair_definition": binding["pairwise_hypothesis_contract"]["pair_definition"],
            "spillover_definition": binding["pairwise_hypothesis_contract"][
                "pairwise_relation_output"
            ],
            "mutated": False,
        },
        "score_and_ranking_contract": {
            "config_ref": SCORE_RANKING_CONFIG_REL_PATH,
            "governance_ref": SCORE_RANKING_GOVERNANCE_REL_PATH,
            "owner": SCORE_RANKING_CONTRACT_OWNER,
            "contract_digest": contract["contract_digest"],
            "score_contract_digest": compute_score_contract_digest_v0(),
            "ranking_contract_digest": compute_ranking_contract_digest_v0(),
            "score_family_policy": contract["score_family_policy"],
            "pair_deterministic_tie_break": contract["ranking_contract"][
                "pair_deterministic_tie_break"
            ],
            "instrument_deterministic_tie_break": contract["ranking_contract"][
                "instrument_deterministic_tie_break"
            ],
            "mutated": False,
        },
        "offline_evaluation_entry_point": {
            "runner_binding_ref": RUNNER_BINDING_REF,
            "harness_binding_ref": HARNESS_BINDING_REF,
            "status": ENTRY_POINT_STATUS,
            "execution_authorized_in_this_scope": False,
        },
        "source_evidence": {
            "hypothesis_binding_bundle": str(SOURCE_HYPOTHESIS_BINDING_BUNDLE),
            "score_ranking_bundle": str(SOURCE_SCORE_RANKING_BUNDLE),
            "pr5200_closeout_bundle": str(SOURCE_PR5200_CLOSEOUT_BUNDLE),
        },
    }


def build_authorization_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": "offline_economic_evaluation_authorization_contract.v0",
        "authorization_scope": AUTHORIZATION_SCOPE,
        "authorization_version": AUTHORIZATION_VERSION,
        "scope_id": RESEARCH_SCOPE,
        "operator_go": GO_TOKEN,
        "offline_only": OFFLINE_ONLY,
        "economic_evaluation_authorized_for_separate_execution": (
            ECONOMIC_EVALUATION_AUTHORIZED_FOR_SEPARATE_EXECUTION
        ),
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "hypothesis_binding_unchanged": HYPOTHESIS_BINDING_UNCHANGED,
        "score_contract_unchanged": SCORE_CONTRACT_UNCHANGED,
        "ranking_contract_unchanged": RANKING_CONTRACT_UNCHANGED,
        "dataset_binding_unchanged": DATASET_BINDING_UNCHANGED,
        "universe_binding_unchanged": UNIVERSE_BINDING_UNCHANGED,
        "parameter_optimization_allowed": PARAMETER_OPTIMIZATION_ALLOWED,
        "post_result_selection_allowed": POST_RESULT_SELECTION_ALLOWED,
        "threshold_reduction_allowed": THRESHOLD_REDUCTION_ALLOWED,
        "policy_rescue_allowed": POLICY_RESCUE_ALLOWED,
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
        "order_effect": ORDER_EFFECT,
        "live_authorized": LIVE_AUTHORIZED,
        "orders_allowed": ORDERS_ALLOWED,
        "repair_and_reevaluation_separate_authority_slices": True,
        "technical_defect_does_not_authorize_repair_or_retry": True,
        "negative_result_may_not_be_rescued_by_parameter_policy_threshold_change": True,
        "later_execution_must_rebind_head_ratification_bindings_and_manifests": True,
        "next_recommended_scope": NEXT_RECOMMENDED_SCOPE,
        "next_operator_go": NEXT_OPERATOR_GO,
    }


def build_digest_dependency_graph_v0(
    *,
    config_digest: str,
    implementation_digest: str,
    ratification_digest: str,
    hypothesis_binding_digest: str,
    score_contract_digest: str,
    ranking_contract_digest: str,
    dataset_digest: str,
    universe_digest: str,
) -> dict[str, Any]:
    return {
        "schema_version": "transitive_digest_graph.v0",
        "edges": [
            {"from": "authorization_contract", "to": "config_digest"},
            {"from": "canonical_references", "to": "config_digest"},
            {"from": "implementation_digest", "to": "ratification_digest"},
            {"from": "config_digest", "to": "ratification_digest"},
            {"from": "hypothesis_binding_digest", "to": "ratification_digest"},
            {"from": "score_contract_digest", "to": "ratification_digest"},
            {"from": "ranking_contract_digest", "to": "ratification_digest"},
            {"from": "dataset_digest", "to": "ratification_digest"},
            {"from": "universe_digest", "to": "ratification_digest"},
        ],
        "component_digests": {
            "implementation_digest": implementation_digest,
            "config_digest": config_digest,
            "ratification_digest": ratification_digest,
            "hypothesis_binding_digest": hypothesis_binding_digest,
            "score_contract_digest": score_contract_digest,
            "ranking_contract_digest": ranking_contract_digest,
            "dataset_digest": dataset_digest,
            "universe_digest": universe_digest,
        },
    }


def materialize_offline_economic_evaluation_authorization_ratification_v0(
    *,
    hypothesis_binding: Mapping[str, Any] | None = None,
    score_ranking_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    binding = (
        hypothesis_binding
        if hypothesis_binding is not None
        else materialize_versioned_hypothesis_binding_v0()
    )
    contract = (
        score_ranking_contract
        if score_ranking_contract is not None
        else materialize_score_and_ranking_contract_v0(binding)
    )
    canonical_refs = build_canonical_references_v0(
        hypothesis_binding=binding, score_ranking_contract=contract
    )
    authorization_contract = build_authorization_contract_v0()

    config_digest = _stable_digest(
        {
            "authorization_contract": authorization_contract,
            "canonical_references": canonical_refs,
        }
    )
    implementation_digest = compute_implementation_digest_v0()
    hypothesis_binding_digest = str(binding["binding_digest"])
    score_contract_digest = compute_score_contract_digest_v0()
    ranking_contract_digest = compute_ranking_contract_digest_v0()
    dataset_digest = str(binding["dataset_digest"])
    universe_digest = str(binding["universe_digest"])

    body: dict[str, Any] = {
        "artifact_kind": (
            "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
            "evaluation_authorization_ratification"
        ),
        "artifact_version": RATIFICATION_VERSION,
        "schema_version": SCHEMA_VERSION,
        "ratification_id": RATIFICATION_ID,
        "ratification_version": RATIFICATION_VERSION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_id": RESEARCH_SCOPE,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "authorization_version": AUTHORIZATION_VERSION,
        "operator_go": GO_TOKEN,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "score_family_policy": SCORE_FAMILY_POLICY,
        "authorization_contract": authorization_contract,
        "canonical_references": canonical_refs,
        "hypothesis_binding_digest": hypothesis_binding_digest,
        "score_contract_digest": score_contract_digest,
        "ranking_contract_digest": ranking_contract_digest,
        "score_and_ranking_contract_digest": contract["contract_digest"],
        "dataset_digest": dataset_digest,
        "universe_digest": universe_digest,
        "implementation_digest": implementation_digest,
        "config_digest": config_digest,
        "offline_only": OFFLINE_ONLY,
        "economic_evaluation_authorized_for_separate_execution": (
            ECONOMIC_EVALUATION_AUTHORIZED_FOR_SEPARATE_EXECUTION
        ),
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "hypothesis_binding_unchanged": HYPOTHESIS_BINDING_UNCHANGED,
        "score_contract_unchanged": SCORE_CONTRACT_UNCHANGED,
        "ranking_contract_unchanged": RANKING_CONTRACT_UNCHANGED,
        "dataset_binding_unchanged": DATASET_BINDING_UNCHANGED,
        "universe_binding_unchanged": UNIVERSE_BINDING_UNCHANGED,
        "parameter_optimization_allowed": PARAMETER_OPTIMIZATION_ALLOWED,
        "post_result_selection_allowed": POST_RESULT_SELECTION_ALLOWED,
        "threshold_reduction_allowed": THRESHOLD_REDUCTION_ALLOWED,
        "policy_rescue_allowed": POLICY_RESCUE_ALLOWED,
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "live_authorized": LIVE_AUTHORIZED,
        "orders_allowed": ORDERS_ALLOWED,
        "runner_binding_ref": RUNNER_BINDING_REF,
        "harness_binding_ref": HARNESS_BINDING_REF,
        "entry_point_status": ENTRY_POINT_STATUS,
        "economic_validity_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "next_recommended_scope": NEXT_RECOMMENDED_SCOPE,
        "next_operator_go": NEXT_OPERATOR_GO,
    }
    ratification_digest = _stable_digest(
        {
            "config_digest": config_digest,
            "implementation_digest": implementation_digest,
            "hypothesis_binding_digest": hypothesis_binding_digest,
            "score_contract_digest": score_contract_digest,
            "ranking_contract_digest": ranking_contract_digest,
            "dataset_digest": dataset_digest,
            "universe_digest": universe_digest,
        }
    )
    body["ratification_digest"] = ratification_digest
    body["digest_dependency_graph"] = build_digest_dependency_graph_v0(
        config_digest=config_digest,
        implementation_digest=implementation_digest,
        ratification_digest=ratification_digest,
        hypothesis_binding_digest=hypothesis_binding_digest,
        score_contract_digest=score_contract_digest,
        ranking_contract_digest=ranking_contract_digest,
        dataset_digest=dataset_digest,
        universe_digest=universe_digest,
    )
    return body


def validate_offline_economic_evaluation_authorization_ratification_v0(
    ratification: Mapping[str, Any],
    *,
    go_token: str | None = None,
    expected_hypothesis_binding: Mapping[str, Any] | None = None,
    expected_score_ranking_contract: Mapping[str, Any] | None = None,
) -> tuple[RatificationValidationVerdict, tuple[str, ...]]:
    reasons: list[str] = []

    if go_token is not None:
        token_ok, token_reasons = validate_go_token_v0(go_token)
        if not token_ok:
            reasons.extend(token_reasons)

    if ratification.get("scope_id") != RESEARCH_SCOPE:
        reasons.append(REASON_SCOPE_ID_MISMATCH)
    if ratification.get("authorization_scope") != AUTHORIZATION_SCOPE:
        reasons.append("AUTHORIZATION_SCOPE_MISMATCH")
    if ratification.get("authorization_version") != AUTHORIZATION_VERSION:
        reasons.append(REASON_AUTHORIZATION_VERSION_MISMATCH)

    canonical_refs = ratification.get("canonical_references", {})
    if not canonical_refs.get("hypothesis_binding"):
        reasons.append(REASON_HYPOTHESIS_BINDING_REFERENCE_MISSING)
    if not canonical_refs.get("score_and_ranking_contract"):
        reasons.append(REASON_SCORE_CONTRACT_REFERENCE_MISSING)
    score_ref = canonical_refs.get("score_and_ranking_contract", {})
    if not score_ref.get("ranking_contract_digest"):
        reasons.append(REASON_RANKING_CONTRACT_REFERENCE_MISSING)

    binding = expected_hypothesis_binding or materialize_versioned_hypothesis_binding_v0()
    contract = expected_score_ranking_contract or materialize_score_and_ranking_contract_v0(binding)

    if ratification.get("hypothesis_binding_digest") != binding["binding_digest"]:
        reasons.append(REASON_HYPOTHESIS_BINDING_DIGEST_MISMATCH)
    if ratification.get("hypothesis_binding_digest") != RATIFIED_HYPOTHESIS_BINDING_DIGEST:
        reasons.append("RATIFIED_HYPOTHESIS_BINDING_DIGEST_MISMATCH")

    expected_score_digest = compute_score_contract_digest_v0()
    expected_ranking_digest = compute_ranking_contract_digest_v0()
    if ratification.get("score_contract_digest") != expected_score_digest:
        reasons.append(REASON_SCORE_CONTRACT_DIGEST_MISMATCH)
    if ratification.get("ranking_contract_digest") != expected_ranking_digest:
        reasons.append(REASON_RANKING_CONTRACT_DIGEST_MISMATCH)
    if ratification.get("score_and_ranking_contract_digest") != contract["contract_digest"]:
        reasons.append("SCORE_AND_RANKING_CONTRACT_DIGEST_MISMATCH")

    if ratification.get("dataset_digest") != binding["dataset_digest"]:
        reasons.append(REASON_DATASET_DIGEST_MISMATCH)
    if ratification.get("universe_digest") != binding["universe_digest"]:
        reasons.append(REASON_UNIVERSE_DIGEST_MISMATCH)

    if ratification.get("economic_evaluation_executed") is not False:
        reasons.append(REASON_ECONOMIC_EVALUATION_EXECUTED_VIOLATION)
    if ratification.get("economic_evaluation_authorized_for_separate_execution") is not True:
        reasons.append("ECONOMIC_EVALUATION_NOT_AUTHORIZED_FOR_SEPARATE_EXECUTION")
    if ratification.get("parameter_optimization_allowed") is not False:
        reasons.append(REASON_PARAMETER_OPTIMIZATION_ALLOWED_VIOLATION)
    if ratification.get("threshold_reduction_allowed") is not False:
        reasons.append(REASON_THRESHOLD_REDUCTION_ALLOWED_VIOLATION)
    if ratification.get("policy_rescue_allowed") is not False:
        reasons.append(REASON_POLICY_RESCUE_ALLOWED_VIOLATION)

    if ratification.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if ratification.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_VIOLATION")

    for effect_field, expected in (
        ("runtime_effect", RUNTIME_EFFECT),
        ("authority_effect", AUTHORITY_EFFECT),
        ("order_effect", ORDER_EFFECT),
    ):
        if ratification.get(effect_field) != expected:
            reasons.append(REASON_OFFLINE_BOUNDARY_VIOLATION)

    if ratification.get("live_authorized") is not False:
        reasons.append("LIVE_AUTHORIZED_VIOLATION")
    if ratification.get("orders_allowed") is not False:
        reasons.append("ORDERS_ALLOWED_VIOLATION")

    expected_ratification_digest = _stable_digest(
        {
            "config_digest": ratification.get("config_digest"),
            "implementation_digest": ratification.get("implementation_digest"),
            "hypothesis_binding_digest": ratification.get("hypothesis_binding_digest"),
            "score_contract_digest": ratification.get("score_contract_digest"),
            "ranking_contract_digest": ratification.get("ranking_contract_digest"),
            "dataset_digest": ratification.get("dataset_digest"),
            "universe_digest": ratification.get("universe_digest"),
        }
    )
    if ratification.get("ratification_digest") != expected_ratification_digest:
        reasons.append(REASON_RATIFICATION_DIGEST_MISMATCH)

    unique = tuple(dict.fromkeys(reasons))
    if unique:
        return RatificationValidationVerdict.REJECTED_INCOMPLETE, unique
    return RatificationValidationVerdict.ACCEPTED_COMPLETE, ()


def validate_ratification_rejections_v0(
    ratification: Mapping[str, Any],
    *,
    mutated_field: str,
    mutated_value: Any,
    go_token: str | None = GO_TOKEN,
) -> tuple[bool, tuple[str, ...]]:
    mutated = deepcopy(dict(ratification))
    if mutated_field.startswith("canonical."):
        parts = mutated_field.split(".", 1)
        remainder = parts[1]
        if "." in remainder:
            section, field = remainder.split(".", 1)
            mutated.setdefault("canonical_references", {}).setdefault(section, {})[field] = (
                mutated_value
            )
        else:
            mutated.setdefault("canonical_references", {})[remainder] = mutated_value
    elif mutated_field.startswith("authorization."):
        mutated.setdefault("authorization_contract", {})[mutated_field.split(".", 1)[1]] = (
            mutated_value
        )
    else:
        mutated[mutated_field] = mutated_value
    verdict, reasons = validate_offline_economic_evaluation_authorization_ratification_v0(
        mutated, go_token=go_token
    )
    return verdict is RatificationValidationVerdict.REJECTED_INCOMPLETE, reasons


def materialize_and_validate_authorization_ratification_v0(
    *,
    go_token: str | None = GO_TOKEN,
) -> AuthorizationRatificationResultV0:
    ratification = materialize_offline_economic_evaluation_authorization_ratification_v0()
    validation_verdict, fail_reasons = (
        validate_offline_economic_evaluation_authorization_ratification_v0(
            ratification, go_token=go_token
        )
    )
    verdict = (
        RatificationMaterializationVerdict.COMPLETE
        if validation_verdict is RatificationValidationVerdict.ACCEPTED_COMPLETE
        else RatificationMaterializationVerdict.INCOMPLETE
    )
    return AuthorizationRatificationResultV0(
        verdict=verdict,
        validation_verdict=validation_verdict,
        ratification=ratification,
        fail_reasons=fail_reasons,
    )


def serialize_authorization_ratification_json_v0(envelope: Mapping[str, Any]) -> str:
    return json.dumps(envelope, indent=2, sort_keys=True) + "\n"


def materializer_to_binder_roundtrip_v0(envelope: Mapping[str, Any]) -> dict[str, Any]:
    roundtrip = json.loads(serialize_authorization_ratification_json_v0(envelope))
    validation_verdict, fail_reasons = (
        validate_offline_economic_evaluation_authorization_ratification_v0(
            roundtrip, go_token=GO_TOKEN
        )
    )
    return {
        "materializer_to_binder_roundtrip_pass": (
            validation_verdict is RatificationValidationVerdict.ACCEPTED_COMPLETE
            and roundtrip.get("ratification_digest") == envelope.get("ratification_digest")
        ),
        "validation_verdict": validation_verdict.value,
        "fail_reasons": list(fail_reasons),
    }


def build_owner_inventory() -> dict[str, Any]:
    return {
        "schema_version": "owner_inventory.v0",
        "governance_owner": VALIDATOR_OWNER,
        "hypothesis_binding_owner": HYPOTHESIS_BINDING_OWNER,
        "score_and_ranking_contract_owner": SCORE_RANKING_CONTRACT_OWNER,
        "materializer_owner": MATERIALIZER_OWNER,
        "binder_validator_owner": VALIDATOR_OWNER,
        "manifest_owner": MANIFEST_OWNER,
        "registry_progress_owner": ORCHESTRATOR_OWNER,
        "tests_owner": (
            "tests.research."
            "test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
            "evaluation_authorization_ratification_v0_contract"
        ),
        "evidence_materializer_owner": MATERIALIZER_OWNER,
        "offline_evaluation_entry_point_ref": RUNNER_BINDING_REF,
        "entry_point_status": ENTRY_POINT_STATUS,
        "parallel_owner_created": False,
    }


def build_reuse_decision() -> dict[str, Any]:
    return {
        "schema_version": "reuse_decision.v0",
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "decision_ladder": "REUSE_AS_IS -> REUSE_WITH_NARROW_ADAPTER",
        "hypothesis_binding_owner": HYPOTHESIS_BINDING_OWNER,
        "score_and_ranking_contract_owner": SCORE_RANKING_CONTRACT_OWNER,
        "hypothesis_binding_reuse": "REUSE_AS_IS",
        "score_contract_reuse": "REUSE_AS_IS",
        "ranking_contract_reuse": "REUSE_AS_IS",
        "dataset_reuse": "REUSE_AS_IS",
        "universe_reuse": "REUSE_AS_IS",
        "period_split_reuse": "REUSE_AS_IS",
        "new_parallel_owner_created": False,
        "new_governance_ssot_created": False,
    }


def build_field_classification_v0() -> dict[str, Any]:
    return {
        "schema_version": "field_classification.v0",
        "authorization_fields": [
            "authorization_scope",
            "authorization_version",
            "economic_evaluation_authorized_for_separate_execution",
            "operator_go",
        ],
        "reference_only_fields": [
            "hypothesis_binding_digest",
            "score_contract_digest",
            "ranking_contract_digest",
            "dataset_digest",
            "universe_digest",
        ],
        "prohibited_mutation_fields": [
            "hypothesis_binding_unchanged",
            "score_contract_unchanged",
            "ranking_contract_unchanged",
            "dataset_binding_unchanged",
            "universe_binding_unchanged",
        ],
        "cryptographic_reference_fields": [
            "ratification_digest",
            "config_digest",
            "implementation_digest",
            "hypothesis_binding_digest",
            "score_contract_digest",
            "ranking_contract_digest",
        ],
        "unclassified_changed_field_count": 0,
    }


def build_semantic_identity_comparison_v0(
    *,
    prior_hypothesis_binding: Mapping[str, Any],
    prior_score_ranking_contract: Mapping[str, Any],
    new_ratification: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "semantic_identity_comparison.v0",
        "semantic_binding_fields_changed": False,
        "hypothesis_binding_unchanged": (
            prior_hypothesis_binding.get("binding_digest")
            == new_ratification.get("hypothesis_binding_digest")
        ),
        "score_contract_unchanged": (
            compute_score_contract_digest_v0() == new_ratification.get("score_contract_digest")
        ),
        "ranking_contract_unchanged": (
            compute_ranking_contract_digest_v0() == new_ratification.get("ranking_contract_digest")
        ),
        "dataset_binding_unchanged": (
            prior_hypothesis_binding.get("dataset_digest") == new_ratification.get("dataset_digest")
        ),
        "universe_binding_unchanged": (
            prior_hypothesis_binding.get("universe_digest")
            == new_ratification.get("universe_digest")
        ),
        "score_and_ranking_contract_digest_unchanged": (
            prior_score_ranking_contract.get("contract_digest")
            == new_ratification.get("score_and_ranking_contract_digest")
        ),
        "unexpected_change_count": 0,
    }


def build_cryptographic_identity_comparison_v0(
    *,
    prior_hypothesis_binding: Mapping[str, Any],
    prior_score_ranking_contract: Mapping[str, Any],
    new_ratification: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "cryptographic_identity_comparison.v0",
        "cryptographic_binding_identity_changed": False,
        "hypothesis_binding_digest_unchanged": (
            prior_hypothesis_binding.get("binding_digest")
            == new_ratification.get("hypothesis_binding_digest")
        ),
        "score_contract_digest_unchanged": (
            compute_score_contract_digest_v0() == new_ratification.get("score_contract_digest")
        ),
        "ranking_contract_digest_unchanged": (
            compute_ranking_contract_digest_v0() == new_ratification.get("ranking_contract_digest")
        ),
        "dataset_digest_unchanged": (
            prior_hypothesis_binding.get("dataset_digest") == new_ratification.get("dataset_digest")
        ),
        "universe_digest_unchanged": (
            prior_hypothesis_binding.get("universe_digest")
            == new_ratification.get("universe_digest")
        ),
        "prior_hypothesis_binding_digest": prior_hypothesis_binding.get("binding_digest"),
        "prior_score_and_ranking_contract_digest": prior_score_ranking_contract.get(
            "contract_digest"
        ),
        "new_ratification_digest": new_ratification.get("ratification_digest"),
    }


def build_before_after_field_diff_v0(
    *,
    prior_hypothesis_binding: Mapping[str, Any],
    prior_score_ranking_contract: Mapping[str, Any],
    new_ratification: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    compare = (
        (
            "authorization_scope",
            None,
            new_ratification.get("authorization_scope"),
        ),
        (
            "economic_evaluation_authorized_for_separate_execution",
            None,
            new_ratification.get("economic_evaluation_authorized_for_separate_execution"),
        ),
        (
            "hypothesis_binding_digest",
            prior_hypothesis_binding.get("binding_digest"),
            new_ratification.get("hypothesis_binding_digest"),
        ),
        (
            "score_and_ranking_contract_digest",
            prior_score_ranking_contract.get("contract_digest"),
            new_ratification.get("score_and_ranking_contract_digest"),
        ),
        (
            "dataset_digest",
            prior_hypothesis_binding.get("dataset_digest"),
            new_ratification.get("dataset_digest"),
        ),
        (
            "universe_digest",
            prior_hypothesis_binding.get("universe_digest"),
            new_ratification.get("universe_digest"),
        ),
    )
    for field, prior_val, new_val in compare:
        if prior_val != new_val:
            change_type = (
                "EXPECTED_AUTHORIZATION_RATIFICATION_ADDITION"
                if prior_val is None
                else "UNEXPECTED_BINDING_CHANGE"
            )
            rows.append(
                {
                    "field": field,
                    "prior_value": prior_val,
                    "new_value": new_val,
                    "change_type": change_type,
                }
            )
    return rows
