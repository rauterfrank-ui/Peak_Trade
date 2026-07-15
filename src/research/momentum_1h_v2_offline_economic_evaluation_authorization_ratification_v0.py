"""Momentum 1h v2 offline economic evaluation authorization ratification v0.

Authorizes a later separate offline economic evaluation execution for momentum_1h/v2
after versioned binding ratification. Does not execute evaluation and has no runtime effect.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.research.momentum_1h_v2_versioned_research_binding_v0 import (
    AUTHORITY_EFFECT,
    BINDING_GENERATION,
    CONFIG_REL_PATH as VERSIONED_BINDING_CONFIG_REL_PATH,
    DECISION_PACKET_DIR,
    DISCOVERY_EVIDENCE_DIR,
    EXPECTED_BINDING_DIGEST,
    GOVERNANCE_REL_PATH,
    HYPOTHESIS_ID,
    ORDER_EFFECT,
    PANEL_DATA_DIGEST,
    POST_PR4921_CLOSEOUT_DIR,
    REPLACES_FAILED_BINDING,
    RESEARCH_SCOPE,
    RUNTIME_EFFECT,
    STRATEGY_ARCHETYPE,
    STRATEGY_ID,
    STRATEGY_VERSION,
    TREND_FOLLOWING_V2_CLOSEOUT_DIR,
    materialize_versioned_research_binding_v0,
    validate_versioned_research_binding_v0,
)

PACKAGE_MARKER = "MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_RATIFICATION_V0=true"

SCHEMA_VERSION = "momentum_1h_v2_offline_economic_evaluation_authorization_ratification.v0"
RATIFICATION_ID = "momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0"
RATIFICATION_VERSION = "v0"
AUTHORIZATION_SCOPE = "OFFLINE_ECONOMIC_EVALUATION"
AUTHORIZATION_VERSION = "v0"
AUTHORIZATION_STATUS = "RATIFIED"
CANONICAL_SERIALIZATION_VERSION = "authorization_ratification_canonical_json_v1"
SCOPE_CLASSIFICATION = (
    "BOUNDED_FUTURES_ONLY_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_RATIFICATION_V0"
)

GO_TOKEN = "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_RATIFICATION_V0"
CONFIRM_GO = GO_TOKEN

CONFIG_REL_PATH = (
    "config/research/momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0.json"
)

NEXT_RECOMMENDED_SCOPE = "MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
NEXT_OPERATOR_GO = "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"

RUNNER_BINDING_REF = "scripts/ops/run_momentum_1h_v2_offline_economic_evaluation_execution_v0.py"
HARNESS_BINDING_REF = "src/research/momentum_1h_v2_offline_economic_evaluation_execution_v0.py"
ENTRY_POINT_STATUS = "PENDING_SEPARATE_EXECUTION_SCOPE"

OFFLINE_ONLY = True
ECONOMIC_EVALUATION_AUTHORIZED_FOR_SEPARATE_EXECUTION = True
ECONOMIC_EVALUATION_EXECUTED = False
ECONOMIC_RESULT = "NOT_EVALUATED"
PARAMETER_OPTIMIZATION_ALLOWED = False
THRESHOLD_REDUCTION_ALLOWED = False
POLICY_RESCUE_ALLOWED = False
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
LIVE_AUTHORIZED = False
ORDERS_ALLOWED = False

NO_NEW_CANDIDATE_HOLD_BEFORE = "ACTIVE"
NO_NEW_CANDIDATE_HOLD_AFTER = "ACTIVE"
GLOBAL_HOLD_RELAXED = False
CANDIDATE_SPECIFIC_AUTHORIZATION = True
AUTHORIZATION_SCOPE_NARROW = True
TREND_FOLLOWING_V2_RETRY_ADMISSIBLE = False
TREND_FOLLOWING_V2_TERMINAL_STATUS_UNCHANGED = True


class RatificationValidationVerdict(str, Enum):
    ACCEPTED_COMPLETE = "ACCEPTED_COMPLETE"
    REJECTED_INCOMPLETE = "REJECTED_INCOMPLETE"


class RatificationMaterializationVerdict(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


@dataclass(frozen=True)
class RatificationMaterializationResultV0:
    verdict: RatificationMaterializationVerdict
    validation_verdict: RatificationValidationVerdict
    ratification: dict[str, Any]
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def serialize_authorization_ratification_json_v0(ratification: Mapping[str, Any]) -> str:
    return json.dumps(ratification, indent=2, sort_keys=True) + "\n"


def compute_ratification_digest_v0(ratification: Mapping[str, Any]) -> str:
    return _stable_digest(
        {
            "authorization_binding_digest": ratification.get("authorization_binding_digest"),
            "config_digest": ratification.get("config_digest"),
            "data_digest": ratification.get("data_digest"),
            "dataset_digest": ratification.get("dataset_digest"),
            "implementation_digest": ratification.get("implementation_digest"),
            "module_implementation_digest": ratification.get("module_implementation_digest"),
        }
    )


def build_authorization_contract_v0(
    *,
    versioned_binding: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "authority_effect": AUTHORITY_EFFECT,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "authorization_status": AUTHORIZATION_STATUS,
        "authorization_version": AUTHORIZATION_VERSION,
        "binding_classification": STRATEGY_ARCHETYPE,
        "binding_generation": BINDING_GENERATION,
        "candidate_specific_authorization": CANDIDATE_SPECIFIC_AUTHORIZATION,
        "cost_policy_unchanged": True,
        "dataset_binding_unchanged": True,
        "economic_evaluation_authorized_for_separate_execution": (
            ECONOMIC_EVALUATION_AUTHORIZED_FOR_SEPARATE_EXECUTION
        ),
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "economic_result": ECONOMIC_RESULT,
        "economic_policy_unchanged": True,
        "execution_without_separate_operator_go_forbidden": True,
        "global_hold_relaxed": GLOBAL_HOLD_RELAXED,
        "later_execution_must_rebind_head_ratification_bindings_and_manifests": True,
        "live_authorized": LIVE_AUTHORIZED,
        "negative_result_may_not_be_rescued_by_parameter_policy_threshold_change": True,
        "next_operator_go": NEXT_OPERATOR_GO,
        "next_recommended_scope": NEXT_RECOMMENDED_SCOPE,
        "no_new_candidate_hold_after": NO_NEW_CANDIDATE_HOLD_AFTER,
        "no_new_candidate_hold_before": NO_NEW_CANDIDATE_HOLD_BEFORE,
        "offline_only": OFFLINE_ONLY,
        "operator_go": GO_TOKEN,
        "order_effect": ORDER_EFFECT,
        "orders_allowed": ORDERS_ALLOWED,
        "parameter_optimization_allowed": PARAMETER_OPTIMIZATION_ALLOWED,
        "policy_rescue_allowed": POLICY_RESCUE_ALLOWED,
        "post_result_selection_allowed": False,
        "runtime_effect": RUNTIME_EFFECT,
        "schema_version": "offline_economic_evaluation_authorization_contract.v0",
        "scope_id": RESEARCH_SCOPE,
        "technical_defect_does_not_authorize_repair_or_retry": True,
        "threshold_reduction_allowed": THRESHOLD_REDUCTION_ALLOWED,
        "trend_following_v2_retry_admissible": TREND_FOLLOWING_V2_RETRY_ADMISSIBLE,
        "trend_following_v2_terminal_status_unchanged": TREND_FOLLOWING_V2_TERMINAL_STATUS_UNCHANGED,
        "versioned_binding_unchanged": True,
    }


def build_canonical_references_v0(
    *,
    versioned_binding: Mapping[str, Any],
) -> dict[str, Any]:
    candidate = versioned_binding["binding"]
    return {
        "schema_version": "canonical_references.v0",
        "source_evidence": {
            "decision_packet_dir": DECISION_PACKET_DIR,
            "discovery_evidence_dir": DISCOVERY_EVIDENCE_DIR,
            "post_pr4921_closeout_dir": POST_PR4921_CLOSEOUT_DIR,
            "trend_following_v2_closeout_dir": TREND_FOLLOWING_V2_CLOSEOUT_DIR,
            "versioned_binding_config": VERSIONED_BINDING_CONFIG_REL_PATH,
        },
        "versioned_binding": {
            "binding_digest": versioned_binding["binding_digest"],
            "binding_generation": BINDING_GENERATION,
            "config_digest": versioned_binding["config_digest"],
            "data_digest": versioned_binding["data_digest"],
            "dataset_digest": versioned_binding["dataset_digest"],
            "dataset_id": versioned_binding["dataset_id"],
            "governance_ref": GOVERNANCE_REL_PATH,
            "hypothesis_id": HYPOTHESIS_ID,
            "mutated": False,
            "owner": "src.research.momentum_1h_v2_versioned_research_binding_v0",
            "strategy_archetype": STRATEGY_ARCHETYPE,
            "strategy_id": STRATEGY_ID,
            "strategy_version": STRATEGY_VERSION,
            "instrument_binding_mode": candidate["instrument_binding"]["binding_mode"],
        },
        "offline_evaluation_entry_point": {
            "execution_authorized_in_this_scope": False,
            "harness_binding_ref": HARNESS_BINDING_REF,
            "runner_binding_ref": RUNNER_BINDING_REF,
            "status": ENTRY_POINT_STATUS,
        },
    }


def build_digest_dependency_graph_v0(
    *,
    versioned_binding: Mapping[str, Any],
    ratification_digest: str,
) -> dict[str, Any]:
    return {
        "component_digests": {
            "authorization_binding_digest": versioned_binding["binding_digest"],
            "config_digest": versioned_binding["config_digest"],
            "data_digest": versioned_binding["data_digest"],
            "dataset_digest": versioned_binding["dataset_digest"],
            "implementation_digest": versioned_binding["implementation_digest"],
            "module_implementation_digest": versioned_binding["module_implementation_digest"],
            "period_digest": versioned_binding["period_digest"],
            "ratification_digest": ratification_digest,
        },
        "schema_version": "digest_dependency_graph.v0",
    }


def validate_go_token_v0(go_token: str | None) -> tuple[bool, tuple[str, ...]]:
    if go_token is None:
        return False, ("GO_TOKEN_MISSING",)
    if go_token != GO_TOKEN:
        return False, ("GO_TOKEN_INVALID",)
    return True, ()


def validate_offline_economic_evaluation_authorization_ratification_v0(
    ratification: Mapping[str, Any],
    *,
    go_token: str | None = GO_TOKEN,
    expected_binding: Mapping[str, Any] | None = None,
) -> tuple[RatificationValidationVerdict, tuple[str, ...]]:
    reasons: list[str] = []
    ok, token_reasons = validate_go_token_v0(go_token)
    reasons.extend(token_reasons)
    if ratification.get("schema_version") != SCHEMA_VERSION:
        reasons.append("SCHEMA_VERSION_MISMATCH")
    if ratification.get("scope_id") != RESEARCH_SCOPE:
        reasons.append("SCOPE_ID_MISMATCH")
    if ratification.get("strategy_version") in (None, ""):
        reasons.append("STRATEGY_VERSION_MISSING")
    elif ratification.get("strategy_version") != STRATEGY_VERSION:
        reasons.append("STRATEGY_VERSION_MISMATCH")
    if ratification.get("go_token") != GO_TOKEN:
        reasons.append("GO_TOKEN_MISMATCH")
    if ratification.get("authorization_status") != AUTHORIZATION_STATUS:
        reasons.append("AUTHORIZATION_STATUS_MISMATCH")
    if ratification.get("authorization_scope") != AUTHORIZATION_SCOPE:
        reasons.append("AUTHORIZATION_SCOPE_MISMATCH")
    if "RUNTIME" in str(ratification.get("authorization_scope", "")).upper():
        reasons.append("AUTHORIZATION_SCOPE_RUNTIME_FORBIDDEN")
    if ratification.get("binding_generation") != BINDING_GENERATION:
        reasons.append("BINDING_GENERATION_MISMATCH")
    if ratification.get("economic_evaluation_executed") is not False:
        reasons.append("ECONOMIC_EVALUATION_EXECUTED_MUST_BE_FALSE")
    if ratification.get("economic_result") not in (None, ECONOMIC_RESULT):
        reasons.append("ECONOMIC_RESULT_MUST_BE_NOT_EVALUATED")
    if ratification.get("economic_evaluation_authorized_for_separate_execution") is not True:
        reasons.append("ECONOMIC_EVALUATION_NOT_AUTHORIZED_FOR_SEPARATE_EXECUTION")
    if ratification.get("dataset_digest") != PANEL_DATA_DIGEST:
        reasons.append("DATASET_DIGEST_MISMATCH")
    if ratification.get("excluded_failed_binding") != REPLACES_FAILED_BINDING:
        reasons.append("EXCLUDED_FAILED_BINDING_MISMATCH")
    if ratification.get("no_new_candidate_hold_after") != NO_NEW_CANDIDATE_HOLD_AFTER:
        reasons.append("NO_NEW_CANDIDATE_HOLD_RELAXED")
    if ratification.get("global_hold_relaxed") is not False:
        reasons.append("GLOBAL_HOLD_RELAXED_FORBIDDEN")
    if ratification.get("orders_allowed") is not False:
        reasons.append("ORDERS_ALLOWED_FORBIDDEN")
    if ratification.get("live_authorized") is not False:
        reasons.append("LIVE_AUTHORIZED_FORBIDDEN")
    if ratification.get("trend_following_v2_retry_admissible") is not False:
        reasons.append("TREND_FOLLOWING_V2_RETRY_ADMISSIBLE_FORBIDDEN")
    refs = ratification.get("canonical_references", {})
    if not isinstance(refs, Mapping):
        reasons.append("CANONICAL_REFERENCES_MISSING")
    else:
        source = refs.get("source_evidence", {})
        if not isinstance(source, Mapping):
            reasons.append("SOURCE_EVIDENCE_MISSING")
        else:
            for key in (
                "decision_packet_dir",
                "discovery_evidence_dir",
                "trend_following_v2_closeout_dir",
            ):
                if not source.get(key):
                    reasons.append(f"SOURCE_EVIDENCE_{key.upper()}_MISSING")
        entry = refs.get("offline_evaluation_entry_point", {})
        if not isinstance(entry, Mapping):
            reasons.append("OFFLINE_EVALUATION_ENTRY_POINT_MISSING")
        elif entry.get("execution_authorized_in_this_scope") is not False:
            reasons.append("EXECUTION_AUTHORIZED_IN_THIS_SCOPE_FORBIDDEN")
    expected_digest = compute_ratification_digest_v0(ratification)
    if ratification.get("ratification_digest") != expected_digest:
        reasons.append("RATIFICATION_DIGEST_MISMATCH")
    binding_digest = ratification.get("binding_digest")
    if binding_digest != EXPECTED_BINDING_DIGEST:
        reasons.append("BINDING_DIGEST_INVALID")
    if expected_binding is not None:
        if binding_digest != expected_binding.get("binding_digest"):
            reasons.append("BINDING_DIGEST_MISMATCH")
    verdict = (
        RatificationValidationVerdict.ACCEPTED_COMPLETE
        if not reasons
        else RatificationValidationVerdict.REJECTED_INCOMPLETE
    )
    return verdict, tuple(reasons)


def materialize_offline_economic_evaluation_authorization_ratification_v0(
    *,
    repo_root: Path | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    binding = (
        dict(versioned_binding)
        if versioned_binding is not None
        else materialize_versioned_research_binding_v0(repo_root=repo_root)
    )
    binding_validation = validate_versioned_research_binding_v0(binding)
    if binding_validation.fail_reasons:
        raise ValueError(f"versioned_binding_invalid:{','.join(binding_validation.fail_reasons)}")

    authorization_contract = build_authorization_contract_v0(versioned_binding=binding)
    canonical_references = build_canonical_references_v0(versioned_binding=binding)
    ratification_body: dict[str, Any] = {
        "artifact_kind": ("momentum_1h_v2_offline_economic_evaluation_authorization_ratification"),
        "artifact_version": RATIFICATION_VERSION,
        "authorization_binding_digest": binding["binding_digest"],
        "authorization_contract": authorization_contract,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "authorization_scope_narrow": AUTHORIZATION_SCOPE_NARROW,
        "authorization_status": AUTHORIZATION_STATUS,
        "authorization_version": AUTHORIZATION_VERSION,
        "authority_effect": AUTHORITY_EFFECT,
        "binding_classification": STRATEGY_ARCHETYPE,
        "binding_config_ref": VERSIONED_BINDING_CONFIG_REL_PATH,
        "binding_digest": binding["binding_digest"],
        "binding_generation": BINDING_GENERATION,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "candidate_specific_authorization": CANDIDATE_SPECIFIC_AUTHORIZATION,
        "canonical_references": canonical_references,
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "config_digest": binding["config_digest"],
        "cost_policy_unchanged": True,
        "data_digest": binding["data_digest"],
        "dataset_binding_unchanged": True,
        "dataset_digest": binding["dataset_digest"],
        "decision_packet_dir": DECISION_PACKET_DIR,
        "discovery_evidence_dir": DISCOVERY_EVIDENCE_DIR,
        "economic_evaluation_authorized_for_separate_execution": (
            ECONOMIC_EVALUATION_AUTHORIZED_FOR_SEPARATE_EXECUTION
        ),
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "economic_result": ECONOMIC_RESULT,
        "economic_policy_unchanged": True,
        "excluded_failed_binding": REPLACES_FAILED_BINDING,
        "futures_only": FUTURES_ONLY,
        "global_hold_relaxed": GLOBAL_HOLD_RELAXED,
        "go_token": GO_TOKEN,
        "governance_ref": GOVERNANCE_REL_PATH,
        "hypothesis_id": HYPOTHESIS_ID,
        "implementation_digest": binding["implementation_digest"],
        "live_authorized": LIVE_AUTHORIZED,
        "next_operator_go": NEXT_OPERATOR_GO,
        "next_recommended_scope": NEXT_RECOMMENDED_SCOPE,
        "no_new_candidate_hold_after": NO_NEW_CANDIDATE_HOLD_AFTER,
        "no_new_candidate_hold_before": NO_NEW_CANDIDATE_HOLD_BEFORE,
        "offline_only": OFFLINE_ONLY,
        "orders_allowed": ORDERS_ALLOWED,
        "parameter_optimization_allowed": PARAMETER_OPTIMIZATION_ALLOWED,
        "policy_rescue_allowed": POLICY_RESCUE_ALLOWED,
        "post_pr4921_closeout_dir": POST_PR4921_CLOSEOUT_DIR,
        "promotion_granted": False,
        "ratification_id": RATIFICATION_ID,
        "ratification_version": RATIFICATION_VERSION,
        "research_scope": RESEARCH_SCOPE,
        "runtime_effect": RUNTIME_EFFECT,
        "schema_version": SCHEMA_VERSION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_id": RESEARCH_SCOPE,
        "status": "AUTHORIZATION_RATIFICATION_COMPLETE",
        "strategy_archetype": STRATEGY_ARCHETYPE,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "threshold_reduction_allowed": THRESHOLD_REDUCTION_ALLOWED,
        "trend_following_v2_closeout_dir": TREND_FOLLOWING_V2_CLOSEOUT_DIR,
        "trend_following_v2_retry_admissible": TREND_FOLLOWING_V2_RETRY_ADMISSIBLE,
        "trend_following_v2_terminal_status_unchanged": (
            TREND_FOLLOWING_V2_TERMINAL_STATUS_UNCHANGED
        ),
        "unchanged_retry_allowed": False,
        "verdict": "PASS",
        "versioned_binding_unchanged": True,
    }
    ratification_body["module_implementation_digest"] = binding["module_implementation_digest"]
    ratification_body["ratification_digest"] = compute_ratification_digest_v0(ratification_body)
    ratification_body["digest_dependency_graph"] = build_digest_dependency_graph_v0(
        versioned_binding=binding,
        ratification_digest=ratification_body["ratification_digest"],
    )
    return ratification_body


def materialize_and_validate_authorization_ratification_v0(
    *,
    go_token: str = GO_TOKEN,
    repo_root: Path | None = None,
) -> RatificationMaterializationResultV0:
    versioned_binding = materialize_versioned_research_binding_v0(repo_root=repo_root)
    ratification = materialize_offline_economic_evaluation_authorization_ratification_v0(
        repo_root=repo_root,
        versioned_binding=versioned_binding,
    )
    validation_verdict, fail_reasons = (
        validate_offline_economic_evaluation_authorization_ratification_v0(
            ratification,
            go_token=go_token,
            expected_binding=versioned_binding,
        )
    )
    materialization_verdict = (
        RatificationMaterializationVerdict.COMPLETE
        if validation_verdict is RatificationValidationVerdict.ACCEPTED_COMPLETE
        else RatificationMaterializationVerdict.INCOMPLETE
    )
    return RatificationMaterializationResultV0(
        verdict=materialization_verdict,
        validation_verdict=validation_verdict,
        ratification=deepcopy(ratification),
        fail_reasons=fail_reasons,
    )


def materializer_to_binder_roundtrip_v0(ratification: Mapping[str, Any]) -> dict[str, Any]:
    rematerialized = materialize_offline_economic_evaluation_authorization_ratification_v0()
    return {
        "materializer_to_binder_roundtrip_pass": rematerialized == dict(ratification),
        "original_ratification_digest": ratification.get("ratification_digest"),
        "rematerialized_ratification_digest": rematerialized.get("ratification_digest"),
    }


__all__ = [
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_STATUS",
    "AUTHORIZATION_VERSION",
    "BINDING_GENERATION",
    "CANDIDATE_SPECIFIC_AUTHORIZATION",
    "CONFIRM_GO",
    "CONFIG_REL_PATH",
    "ECONOMIC_RESULT",
    "ENTRY_POINT_STATUS",
    "EXPECTED_BINDING_DIGEST",
    "GLOBAL_HOLD_RELAXED",
    "GO_TOKEN",
    "GOVERNANCE_REL_PATH",
    "NEXT_OPERATOR_GO",
    "NEXT_RECOMMENDED_SCOPE",
    "NO_NEW_CANDIDATE_HOLD_AFTER",
    "NO_NEW_CANDIDATE_HOLD_BEFORE",
    "PANEL_DATA_DIGEST",
    "RATIFICATION_ID",
    "RESEARCH_SCOPE",
    "RatificationMaterializationResultV0",
    "RatificationMaterializationVerdict",
    "RatificationValidationVerdict",
    "build_authorization_contract_v0",
    "build_canonical_references_v0",
    "compute_ratification_digest_v0",
    "materialize_and_validate_authorization_ratification_v0",
    "materialize_offline_economic_evaluation_authorization_ratification_v0",
    "materializer_to_binder_roundtrip_v0",
    "serialize_authorization_ratification_json_v0",
    "validate_go_token_v0",
    "validate_offline_economic_evaluation_authorization_ratification_v0",
]
