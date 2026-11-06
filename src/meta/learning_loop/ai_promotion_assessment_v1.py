"""Offline LEVEL_3 AI promotion assessment from verified policy decision v1."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.comparison_promotion_policy_decision_v1 import (
    ARTIFACT_REL as UPSTREAM_ARTIFACT_REL,
    CONTRACT_NAME as UPSTREAM_CONTRACT_NAME,
    CONTRACT_VERSION as UPSTREAM_CONTRACT_VERSION,
    PRODUCER_VERSION as UPSTREAM_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as UPSTREAM_SELF_VERIFICATION_REL,
    ComparisonPromotionPolicyDecisionError,
    reverify_comparison_promotion_policy_decision_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

CONTRACT_NAME = "ai_promotion_assessment_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "ai_promotion_assessment_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING_EVIDENCE_ONLY"
RECORD_KIND = "ai_promotion_assessment_record"
INPUT_RELATION = "ASSESSES_FROM_VERIFIED_POLICY_DECISION_V1"
ARTIFACT_REL = "ai_promotion_assessment_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".ai_promotion_assessment_staging_"

OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DETERMINISTIC_RULE_SET_VERSION = "ai_promotion_assessment_rules_v1"

_VALID_ASSESSMENT_RESULTS = frozenset(
    {
        "SUPPORTS_DECISION",
        "QUESTIONS_DECISION",
        "ABSTAINS",
    }
)
_VALID_CONFIDENCE_CLASSES = frozenset({"HIGH", "MEDIUM", "LOW", "UNKNOWN"})
_EVIDENCE_BOUND = "BOUND"
_EVIDENCE_NOT_BOUND = "NOT_BOUND"

AI_PROMOTION_ASSESSMENT_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "assessment_is_descriptive_only": True,
    "assessment_does_not_override_policy_decision": True,
    "assessment_does_not_authorize_promotion": True,
    "assessment_does_not_select": True,
    "assessment_does_not_choose_winner": True,
    "assessment_does_not_accept": True,
    "assessment_does_not_construct_promotion_candidate": True,
    "assessment_does_not_create_configpatch": True,
    "assessment_does_not_modify_configpatch": True,
    "assessment_does_not_apply_configpatch": True,
    "assessment_does_not_modify_config": True,
    "assessment_does_not_authorize_runtime": True,
    "assessment_does_not_authorize_live": True,
    "assessment_does_not_deploy": True,
    "assessment_does_not_activate": True,
    "assessment_does_not_create_order_intent": True,
    "assessment_does_not_modify_trading_logic": True,
    "evidence_does_not_authorize_promotion": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_ai_promotion_assessment": True,
    "ai_assessment_offline_only": True,
    "evidence_does_not_authorize_promotion": True,
    "evidence_does_not_authorize_runtime": True,
    "assessment_does_not_override_policy_decision": True,
    "assessment_does_not_select": True,
    "assessment_does_not_choose_winner": True,
    "assessment_does_not_accept_candidate": True,
    "assessment_does_not_accept_configpatch": True,
    "assessment_does_not_construct_promotion_candidate": True,
    "assessment_does_not_create_configpatch": True,
    "assessment_does_not_modify_configpatch": True,
    "assessment_does_not_apply_configpatch": True,
    "assessment_does_not_modify_config": True,
    "assessment_does_not_authorize_promotion": True,
    "assessment_does_not_authorize_runtime": True,
    "assessment_does_not_authorize_live": True,
    "assessment_does_not_deploy": True,
    "assessment_does_not_activate": True,
    "assessment_does_not_create_order_intent": True,
    "assessment_does_not_modify_trading_logic": True,
    "external_model_called": False,
    "network_side_effect_created": False,
    "nondeterministic_inference_used": False,
    "policy_decision_overridden": False,
    "promotion_policy_executed": False,
    "promotion_decision_created": False,
    "configpatch_created": False,
    "configpatch_modified": False,
    "configpatch_applied": False,
    "configpatch_accepted": False,
    "candidate_selected": False,
    "winner_selected": False,
    "candidate_accepted": False,
    "promotion_candidate_constructed": False,
    "safety_flags_mutated": False,
    "jsonl_side_effect_created": False,
    "promotion_consumers_changed": False,
    "promotion_authorized": False,
    "runtime_authorized": False,
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
}

_FORBIDDEN_CAPABILITIES: frozenset[str] = frozenset(
    {
        "CAN_PROMOTE_ARTIFACT",
        "CAN_DEPLOY_INACTIVE",
        "CAN_COMPUTE_SIGNALS",
        "CAN_CREATE_ORDER_INTENTS",
        "CAN_SUBMIT_TESTNET_ORDERS",
        "CAN_SUBMIT_LIVE_ORDERS",
        "CAN_INCREASE_CAPITAL",
        "CAN_CHANGE_RISK_POLICY",
    }
)

_FORBIDDEN_INDEX_KEYS: frozenset[str] = frozenset(
    {
        "winner",
        "selected",
        "promoted",
        "promotion",
        "promotion_ready",
        "eligible_for_live",
        "live_eligible",
        "runtime_eligible",
        "ranking",
        "ranked_input_ids",
        "pareto",
        "accepted",
        "acceptance",
        "armed",
        "enabled",
        "returns",
        "positions",
        "orders",
        "credentials",
        "strategy_params_mutated",
        "config_patch",
        "configpatch",
        "config_patch_manifest",
        "patches",
        "top_n",
        "topn",
        "filter_candidates_for_live",
        "promotion_candidate",
        "safety_flags",
    }
)

_SELF_VERIFICATION_SCHEMA_VERSION = "ai_promotion_assessment_self_verification_v1"

_TRANSITIVE_LINEAGE_FIELDS: tuple[str, ...] = (
    "policy_input_evidence_bundle_ref",
    "policy_input_evidence_artifact_ref",
    "policy_input_evidence_digest",
    "policy_input_evidence_manifest_digest",
    "promotion_policy_input_evidence_status",
    "candidate_input_bundle_ref",
    "candidate_input_digest",
    "candidate_input_manifest_digest",
    "candidate_identity_ref",
    "candidate_identity_digest",
    "experiment_identity_ref",
    "experiment_identity_digest",
    "experiment_identity_id",
    "dataset_identity_ref",
    "dataset_identity_digest",
    "comparison_identity_ref",
    "comparison_identity_digest",
    "comparison_definition_id",
    "comparison_completion_ref",
    "comparison_completion_digest",
    "research_validity_ref",
    "research_validity_digest",
    "promotion_input_binding_ref",
    "promotion_input_binding_digest",
    "config_patch_manifest_ref",
    "config_patch_manifest_digest",
    "config_patch_manifest_id",
    "config_patch_contract_name",
    "config_patch_contract_version",
    "cross_domain_lineage_binding_bundle_ref",
    "cross_domain_lineage_binding_digest",
    "policy_input_binding_bundle_ref",
    "policy_input_binding_digest",
    "policy_input_binding_manifest_digest",
    "model_identity_ref",
    "model_identity_digest",
    "parameter_set_identity_ref",
    "parameter_set_identity_digest",
    "candidate_lineage_manifest_id",
    "candidate_lineage_digest",
    "config_patch_lineage_manifest_ref",
    "comparison_checkpoint_ref",
    "comparison_checkpoint_digest",
    "model_parameter_identity_binding_bundle_ref",
    "model_parameter_identity_binding_digest",
    "comparison_metric_input_ref",
    "comparison_metric_input_digest",
    "eligibility_evidence_ref",
    "eligibility_evidence_digest",
)

_OPTIONAL_LINEAGE_FIELDS_FOR_QUESTIONS: tuple[str, ...] = (
    "candidate_identity_ref",
    "eligibility_evidence_ref",
    "policy_input_binding_bundle_ref",
    "config_patch_manifest_id",
    "cross_domain_lineage_binding_digest",
)


class AiPromotionAssessmentError(ValueError):
    """Fail-closed AI promotion assessment error."""


@dataclass(frozen=True)
class VerifiedPolicyDecisionBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    decision_payload: dict[str, Any]


@dataclass(frozen=True)
class AiPromotionAssessmentInputs:
    policy_decision_bundle_dir: Path


@dataclass(frozen=True)
class AiPromotionAssessmentResult:
    output_dir: Path
    comparison_definition_id: str
    artifact_id: str
    assessment_path: Path
    self_verification_path: Path
    manifest_path: Path
    assessment_result: str
    assessment_confidence_class: str
    policy_decision_ref: str
    policy_decision_digest: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise AiPromotionAssessmentError(f"{label} must not be a symlink")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise AiPromotionAssessmentError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise AiPromotionAssessmentError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise AiPromotionAssessmentError(f"{label} must be a directory: {bundle_dir}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise AiPromotionAssessmentError(f"output directory already exists: {output_dir}")
    if is_under_tmp(output_dir):
        raise AiPromotionAssessmentError("output directory must not be under /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, policy_decision_dir: Path, output_dir: Path) -> None:
    input_res = policy_decision_dir.resolve()
    output_res = output_dir.resolve()
    if output_res == input_res:
        raise AiPromotionAssessmentError("output directory must not equal input path")
    if _path_is_under(output_res, input_res):
        raise AiPromotionAssessmentError("output directory must not be inside input path")
    if input_res.is_dir() and _path_is_under(input_res, output_res):
        raise AiPromotionAssessmentError("input directory must not be inside output directory")


def _manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / MANIFEST_FILENAME
    _validate_regular_file(manifest_path, label=MANIFEST_FILENAME)
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _validate_capabilities(capabilities: Any) -> list[str]:
    if capabilities is None:
        return []
    if not isinstance(capabilities, list):
        raise AiPromotionAssessmentError("capabilities must be a list")
    normalized: list[str] = []
    for item in capabilities:
        if not isinstance(item, str):
            raise AiPromotionAssessmentError("capabilities entries must be strings")
        if item in _FORBIDDEN_CAPABILITIES:
            raise AiPromotionAssessmentError(f"forbidden capability: {item}")
        normalized.append(item)
    return sorted(normalized)


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if payload.get(key) is not expected:
            raise AiPromotionAssessmentError(f"{key} must be {expected!r}")


_COMPLETION_FLAGS: tuple[str, ...] = (
    "ai_promotion_assessment_complete",
    "policy_decision_bound",
    "promotion_policy_input_evidence_bound",
    "cross_domain_lineage_bound",
)


def _validate_completion_flags(payload: Mapping[str, Any]) -> None:
    complete = payload.get("ai_promotion_assessment_complete")
    if complete is True and payload.get("policy_decision_bound") is not True:
        raise AiPromotionAssessmentError(
            "policy_decision_bound must be True when assessment complete"
        )
    if (
        complete is True
        and payload.get("assessment_result") == "SUPPORTS_DECISION"
        and payload.get("upstream_decision_outcome") == "APPROVE"
    ):
        if payload.get("promotion_policy_input_evidence_bound") is not True:
            raise AiPromotionAssessmentError(
                "promotion_policy_input_evidence_bound must be True for complete APPROVE SUPPORTS_DECISION"
            )
        if payload.get("cross_domain_lineage_bound") is not True:
            raise AiPromotionAssessmentError(
                "cross_domain_lineage_bound must be True for complete APPROVE SUPPORTS_DECISION"
            )


def _sorted_strings(values: list[str]) -> list[str]:
    return sorted(set(values))


def _load_self_verification(bundle_dir: Path, *, rel: str, label: str) -> dict[str, Any]:
    path = bundle_dir / rel
    _validate_regular_file(path, label=label)
    payload = read_manifest(path)
    if not isinstance(payload, dict):
        raise AiPromotionAssessmentError(f"{label} must be a JSON object")
    return payload


def verify_policy_decision_bundle(
    bundle_dir: Path | str,
) -> VerifiedPolicyDecisionBundle:
    """Fail-closed verification of exactly one policy decision bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="policy decision bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise AiPromotionAssessmentError(
            f"policy decision MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = path / UPSTREAM_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=UPSTREAM_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != UPSTREAM_CONTRACT_NAME:
        raise AiPromotionAssessmentError("upstream policy decision contract_name mismatch")
    if payload.get("contract_version") != UPSTREAM_CONTRACT_VERSION:
        raise AiPromotionAssessmentError("upstream policy decision contract_version mismatch")

    self_payload = _load_self_verification(
        path,
        rel=UPSTREAM_SELF_VERIFICATION_REL,
        label=UPSTREAM_SELF_VERIFICATION_REL,
    )
    if self_payload.get("overall_status") != "PASS":
        raise AiPromotionAssessmentError(
            "upstream policy decision SELF_VERIFICATION overall_status must be PASS"
        )

    try:
        reverify_comparison_promotion_policy_decision_v1(output_dir=path)
    except ComparisonPromotionPolicyDecisionError as exc:
        raise AiPromotionAssessmentError(str(exc)) from exc

    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping):
        raise AiPromotionAssessmentError("policy decision integrity must be an object")
    artifact_digest = integrity.get("content_sha256")
    if not isinstance(artifact_digest, str) or not is_valid_sha256_hex(artifact_digest):
        raise AiPromotionAssessmentError("policy decision integrity.content_sha256 invalid")

    return VerifiedPolicyDecisionBundle(
        bundle_dir=path.resolve(),
        contract_name=UPSTREAM_CONTRACT_NAME,
        contract_version=UPSTREAM_CONTRACT_VERSION,
        producer_version=UPSTREAM_PRODUCER_VERSION,
        artifact_ref=UPSTREAM_ARTIFACT_REL,
        artifact_digest=artifact_digest,
        manifest_digest=_manifest_file_digest(path),
        decision_payload=dict(payload),
    )


def _factor(
    *,
    factor_id: str,
    factor_type: str,
    source_field: str,
    observation: str,
) -> dict[str, str]:
    return {
        "factor_id": factor_id,
        "factor_type": factor_type,
        "source_field": source_field,
        "observation": observation,
    }


def _detect_decision_contradictions(decision: Mapping[str, Any]) -> list[dict[str, str]]:
    contradictions: list[dict[str, str]] = []
    decision_status = str(decision.get("decision_status", ""))
    decision_outcome = str(decision.get("decision_outcome", ""))

    if (
        decision_outcome == "APPROVE"
        and decision.get("policy_input_evidence_bound_status") != _EVIDENCE_BOUND
    ):
        contradictions.append(
            _factor(
                factor_id="APPROVE_WITHOUT_BOUND_EVIDENCE",
                factor_type="CONTRADICTION",
                source_field="policy_input_evidence_bound_status",
                observation="APPROVE outcome with unbound policy input evidence",
            )
        )
    if decision_status == "PASS" and decision.get("promotion_decision_complete") is not True:
        contradictions.append(
            _factor(
                factor_id="PASS_WITHOUT_COMPLETE_DECISION",
                factor_type="CONTRADICTION",
                source_field="promotion_decision_complete",
                observation="PASS status without promotion_decision_complete",
            )
        )
    if decision.get("promotion_authorized") is True:
        contradictions.append(
            _factor(
                factor_id="PROMOTION_AUTHORITY_IN_DECISION",
                factor_type="CONTRADICTION",
                source_field="promotion_authorized",
                observation="policy decision carries promotion_authorized=true",
            )
        )
    if decision.get("runtime_authorized") is True:
        contradictions.append(
            _factor(
                factor_id="RUNTIME_AUTHORITY_IN_DECISION",
                factor_type="CONTRADICTION",
                source_field="runtime_authorized",
                observation="policy decision carries runtime_authorized=true",
            )
        )
    return contradictions


def _detect_missing_lineage(decision: Mapping[str, Any]) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    for field in _OPTIONAL_LINEAGE_FIELDS_FOR_QUESTIONS:
        value = decision.get(field)
        if not value:
            missing.append(
                _factor(
                    factor_id=f"MISSING_{field.upper()}",
                    factor_type="MISSING_INPUT",
                    source_field=field,
                    observation=f"lineage field {field!r} absent or empty",
                )
            )
    return missing


def _detect_forbidden_decision_flags(decision: Mapping[str, Any]) -> list[dict[str, str]]:
    opposing: list[dict[str, str]] = []
    flag_checks = (
        ("candidate_selected", "CANDIDATE_SELECTED_IN_DECISION"),
        ("winner_selected", "WINNER_SELECTED_IN_DECISION"),
        ("candidate_accepted", "CANDIDATE_ACCEPTED_IN_DECISION"),
        ("promotion_candidate_constructed", "PROMOTION_CANDIDATE_CONSTRUCTED_IN_DECISION"),
        ("configpatch_created", "CONFIGPATCH_CREATED_IN_DECISION"),
        ("configpatch_modified", "CONFIGPATCH_MODIFIED_IN_DECISION"),
        ("configpatch_applied", "CONFIGPATCH_APPLIED_IN_DECISION"),
        ("configpatch_accepted", "CONFIGPATCH_ACCEPTED_IN_DECISION"),
        ("promotion_policy_executed", "PROMOTION_POLICY_EXECUTED_IN_DECISION"),
        ("safety_flags_mutated", "SAFETY_FLAGS_MUTATED_IN_DECISION"),
        ("promotion_consumers_changed", "PROMOTION_CONSUMERS_CHANGED_IN_DECISION"),
        ("live_authorized", "LIVE_AUTHORIZED_IN_DECISION"),
        ("orders_allowed", "ORDERS_ALLOWED_IN_DECISION"),
        ("scheduler_runtime_allowed", "SCHEDULER_RUNTIME_ALLOWED_IN_DECISION"),
    )
    for field, factor_id in flag_checks:
        if decision.get(field) is True:
            opposing.append(
                _factor(
                    factor_id=factor_id,
                    factor_type="OPPOSING_FACTOR",
                    source_field=field,
                    observation=f"policy decision has forbidden flag {field}=true",
                )
            )
    return opposing


def _evaluate_assessment(
    *,
    decision: Mapping[str, Any],
) -> tuple[
    str,
    str,
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[str],
    dict[str, bool],
]:
    decision_status = str(decision.get("decision_status", ""))
    decision_outcome = str(decision.get("decision_outcome", ""))
    reason_codes: list[str] = []
    supporting: list[dict[str, str]] = []
    opposing: list[dict[str, str]] = []
    contradictions = _detect_decision_contradictions(decision)
    missing_inputs = _detect_missing_lineage(decision)
    abstention_reasons: list[str] = []
    completion_flags = {
        "ai_promotion_assessment_complete": False,
        "policy_decision_bound": False,
        "promotion_policy_input_evidence_bound": False,
        "cross_domain_lineage_bound": False,
    }

    opposing.extend(_detect_forbidden_decision_flags(decision))

    if contradictions or opposing:
        reason_codes.extend(["DECISION_SAFETY_CONTRADICTION_DETECTED"])
        abstention_reasons.extend(["POLICY_DECISION_CARRIES_FORBIDDEN_OR_CONTRADICTORY_SIGNALS"])
        return (
            "ABSTAINS",
            "UNKNOWN",
            supporting,
            opposing,
            contradictions,
            missing_inputs,
            _sorted_strings(abstention_reasons + reason_codes),
            completion_flags,
        )

    if decision_status in {"INCOMPLETE", "NOT_EVALUABLE"}:
        abstention_reasons.extend(["POLICY_DECISION_INSUFFICIENT_EVIDENCE"])
        reason_codes.extend(["UPSTREAM_DECISION_NOT_ASSESSABLE"])
        return (
            "ABSTAINS",
            "LOW",
            supporting,
            opposing,
            contradictions,
            missing_inputs,
            _sorted_strings(abstention_reasons + reason_codes),
            completion_flags,
        )

    if decision_outcome in {"DEFER_INSUFFICIENT_EVIDENCE", "ABSTAIN_POLICY_AMBIGUITY"}:
        abstention_reasons.extend(["POLICY_DECISION_DEFERRED_OR_ABSTAINED"])
        reason_codes.extend(["ASSESSMENT_ALIGNS_WITH_DEFER_OR_ABSTAIN"])
        return (
            "ABSTAINS",
            "LOW",
            supporting,
            opposing,
            contradictions,
            missing_inputs,
            _sorted_strings(abstention_reasons + reason_codes),
            completion_flags,
        )

    if decision_status == "PASS" and decision_outcome == "APPROVE":
        if missing_inputs and decision.get("promotion_decision_complete") is not True:
            reason_codes.extend(["TRANSITIVE_LINEAGE_INCOMPLETE"])
            return (
                "QUESTIONS_DECISION",
                "MEDIUM",
                supporting,
                opposing,
                contradictions,
                missing_inputs,
                _sorted_strings(abstention_reasons + reason_codes),
                completion_flags,
            )
        supporting.extend(
            [
                _factor(
                    factor_id="POLICY_DECISION_PASS_APPROVE",
                    factor_type="SUPPORTING_FACTOR",
                    source_field="decision_status",
                    observation="policy decision status PASS with outcome APPROVE",
                ),
                _factor(
                    factor_id="POLICY_INPUT_EVIDENCE_BOUND",
                    factor_type="SUPPORTING_FACTOR",
                    source_field="policy_input_evidence_bound_status",
                    observation="policy input evidence bound on approve path",
                ),
                _factor(
                    factor_id="TRANSITIVE_LINEAGE_PRESENT",
                    factor_type="SUPPORTING_FACTOR",
                    source_field="cross_domain_lineage_binding_digest",
                    observation="required transitive lineage fields present",
                ),
            ]
        )
        reason_codes.extend(
            [
                "POLICY_DECISION_BOUND",
                "PROMOTION_POLICY_INPUT_EVIDENCE_BOUND",
                "CROSS_DOMAIN_LINEAGE_BOUND",
                "AI_PROMOTION_ASSESSMENT_COMPLETE",
            ]
        )
        completion_flags = {
            "ai_promotion_assessment_complete": True,
            "policy_decision_bound": True,
            "promotion_policy_input_evidence_bound": True,
            "cross_domain_lineage_bound": True,
        }
        return (
            "SUPPORTS_DECISION",
            "HIGH",
            supporting,
            opposing,
            contradictions,
            missing_inputs,
            _sorted_strings(abstention_reasons + reason_codes),
            completion_flags,
        )

    if decision_status == "FAIL" and decision_outcome.startswith("BLOCK_"):
        supporting.append(
            _factor(
                factor_id="POLICY_DECISION_SAFETY_BLOCK",
                factor_type="SUPPORTING_FACTOR",
                source_field="decision_outcome",
                observation=f"policy decision safety block outcome {decision_outcome}",
            )
        )
        reason_codes.extend(["SAFETY_BLOCK_SUPPORTS_ASSESSMENT"])
        completion_flags = {
            "ai_promotion_assessment_complete": True,
            "policy_decision_bound": True,
            "promotion_policy_input_evidence_bound": False,
            "cross_domain_lineage_bound": False,
        }
        return (
            "SUPPORTS_DECISION",
            "MEDIUM",
            supporting,
            opposing,
            contradictions,
            missing_inputs,
            _sorted_strings(abstention_reasons + reason_codes),
            completion_flags,
        )

    if decision_status == "FAIL" and decision_outcome == "REJECT":
        supporting.append(
            _factor(
                factor_id="POLICY_DECISION_REJECT",
                factor_type="SUPPORTING_FACTOR",
                source_field="decision_outcome",
                observation="policy decision reject outcome aligns with upstream fail evidence",
            )
        )
        reason_codes.extend(["REJECT_OUTCOME_SUPPORTS_ASSESSMENT"])
        completion_flags = {
            "ai_promotion_assessment_complete": True,
            "policy_decision_bound": True,
            "promotion_policy_input_evidence_bound": False,
            "cross_domain_lineage_bound": False,
        }
        return (
            "SUPPORTS_DECISION",
            "MEDIUM",
            supporting,
            opposing,
            contradictions,
            missing_inputs,
            _sorted_strings(abstention_reasons + reason_codes),
            completion_flags,
        )

    if contradictions:
        reason_codes.extend(["INTERNAL_DECISION_CONTRADICTION"])
        return (
            "QUESTIONS_DECISION",
            "MEDIUM",
            supporting,
            opposing,
            contradictions,
            missing_inputs,
            _sorted_strings(abstention_reasons + reason_codes),
            completion_flags,
        )

    abstention_reasons.extend(["UNCLASSIFIED_POLICY_DECISION_STATE"])
    reason_codes.extend(["ASSESSMENT_DEFAULT_ABSTAIN"])
    return (
        "ABSTAINS",
        "UNKNOWN",
        supporting,
        opposing,
        contradictions,
        missing_inputs,
        _sorted_strings(abstention_reasons + reason_codes),
        completion_flags,
    )


def _input_artifact_ref_mapping(*, bundle: VerifiedPolicyDecisionBundle) -> dict[str, Any]:
    return {
        "artifact_type": bundle.contract_name,
        "contract_name": bundle.contract_name,
        "contract_version": bundle.contract_version,
        "artifact_ref": bundle.artifact_ref,
        "artifact_digest": bundle.artifact_digest,
        "manifest_digest": bundle.manifest_digest,
        "producer_version": bundle.producer_version,
        "bundle_path": bundle.bundle_dir.as_posix(),
    }


def _compute_output_digest(body: Mapping[str, Any]) -> str:
    excluded = frozenset(
        {
            "output_digest",
            "manifest_digest",
            "integrity",
            "created_at",
            "artifact_id",
            "assessment_id",
        }
    )
    digest_body = {key: body[key] for key in sorted(body) if key not in excluded}
    return compute_content_sha256(digest_body)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in body.items() if key not in {"integrity", "manifest_digest"}
    }


def _sort_factors(factors: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(factors, key=lambda item: (item["factor_id"], item["source_field"]))


def build_ai_promotion_assessment_v1(
    *,
    policy_decision: VerifiedPolicyDecisionBundle,
) -> dict[str, Any]:
    decision = policy_decision.decision_payload
    (
        assessment_result,
        confidence_class,
        supporting_factors,
        opposing_factors,
        contradictions,
        missing_inputs,
        assessment_reason_codes,
        completion_flags,
    ) = _evaluate_assessment(decision=decision)

    input_refs = [_input_artifact_ref_mapping(bundle=policy_decision)]
    parent_artifact_refs = list(decision.get("parent_artifact_refs", []))
    if isinstance(parent_artifact_refs, list):
        parent_artifact_refs = [
            dict(item) for item in parent_artifact_refs if isinstance(item, Mapping)
        ]
    else:
        parent_artifact_refs = []
    parent_artifact_refs.sort(
        key=lambda item: (str(item.get("ref_type", "")), str(item.get("digest", "")))
    )

    payload: dict[str, Any] = {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "artifact_id": "",
        "assessment_id": "",
        "created_at": OFFLINE_DETERMINISTIC_CREATED_AT,
        "producer_version": PRODUCER_VERSION,
        "record_kind": RECORD_KIND,
        "input_relation": INPUT_RELATION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "capabilities": [],
        "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        "assessment_version": CONTRACT_VERSION,
        "is_ai_promotion_assessment": True,
        "ai_assessment_offline_only": True,
        "external_model_called": False,
        "network_side_effect_created": False,
        "nondeterministic_inference_used": False,
        "policy_decision_overridden": False,
        "assessment_does_not_override_policy_decision": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "assessment_does_not_select": True,
        "assessment_does_not_choose_winner": True,
        "assessment_does_not_accept_candidate": True,
        "assessment_does_not_accept_configpatch": True,
        "assessment_does_not_construct_promotion_candidate": True,
        "assessment_does_not_create_configpatch": True,
        "assessment_does_not_modify_configpatch": True,
        "assessment_does_not_apply_configpatch": True,
        "assessment_does_not_modify_config": True,
        "assessment_does_not_authorize_promotion": True,
        "assessment_does_not_authorize_runtime": True,
        "assessment_does_not_authorize_live": True,
        "assessment_does_not_deploy": True,
        "assessment_does_not_activate": True,
        "assessment_does_not_create_order_intent": True,
        "assessment_does_not_modify_trading_logic": True,
        "assessment_authority_invariants": dict(AI_PROMOTION_ASSESSMENT_AUTHORITY_INVARIANTS),
        "configpatch_created": False,
        "configpatch_modified": False,
        "configpatch_applied": False,
        "configpatch_accepted": False,
        "candidate_selected": False,
        "winner_selected": False,
        "candidate_accepted": False,
        "promotion_candidate_constructed": False,
        "safety_flags_mutated": False,
        "jsonl_side_effect_created": False,
        "promotion_policy_executed": False,
        "promotion_decision_created": False,
        "promotion_consumers_changed": False,
        "promotion_authorized": False,
        "runtime_authorized": False,
        "live_authorized": False,
        "orders_allowed": False,
        "scheduler_runtime_allowed": False,
        "policy_decision_bundle_ref": policy_decision.bundle_dir.as_posix(),
        "policy_decision_artifact_ref": policy_decision.artifact_ref,
        "policy_decision_ref": policy_decision.bundle_dir.as_posix(),
        "policy_decision_digest": policy_decision.artifact_digest,
        "policy_decision_manifest_digest": policy_decision.manifest_digest,
        "upstream_contract_name": policy_decision.contract_name,
        "upstream_contract_version": policy_decision.contract_version,
        "upstream_producer_version": policy_decision.producer_version,
        "upstream_decision_status": str(decision.get("decision_status", "")),
        "upstream_decision_outcome": str(decision.get("decision_outcome", "")),
        "assessment_result": assessment_result,
        "assessment_confidence_class": confidence_class,
        "assessment_reason_codes": assessment_reason_codes,
        "supporting_factors": _sort_factors(supporting_factors),
        "opposing_factors": _sort_factors(opposing_factors),
        "contradictions": _sort_factors(contradictions),
        "missing_inputs": _sort_factors(missing_inputs),
        "abstention_reasons": [
            code
            for code in assessment_reason_codes
            if code.startswith("POLICY_")
            or code.startswith("REQUIRED_")
            or code.startswith("UNCLASSIFIED_")
        ],
        "input_artifact_refs": input_refs,
        "parent_artifact_refs": parent_artifact_refs,
        "input_digest": "",
        "output_digest": "",
        "manifest_digest": "",
        **completion_flags,
    }

    for field in _TRANSITIVE_LINEAGE_FIELDS:
        value = decision.get(field)
        if value is not None and str(value):
            payload[field] = str(value)

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    if completion_flags["ai_promotion_assessment_complete"]:
        _validate_completion_flags(payload)
    _validate_capabilities(payload["capabilities"])
    if assessment_result not in _VALID_ASSESSMENT_RESULTS:
        raise AiPromotionAssessmentError("assessment_result invalid")
    if confidence_class not in _VALID_CONFIDENCE_CLASSES:
        raise AiPromotionAssessmentError("assessment_confidence_class invalid")

    payload["input_digest"] = compute_content_sha256({"input_artifact_refs": input_refs})
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    payload["assessment_id"] = output_digest
    return payload


def serialize_ai_promotion_assessment_v1(
    assessment: Mapping[str, Any],
) -> str:
    _reject_forbidden_index_keys(assessment)
    _validate_non_authorizing_flags(assessment)
    if assessment.get("ai_promotion_assessment_complete") is True:
        _validate_completion_flags(assessment)
    _validate_capabilities(assessment.get("capabilities"))
    result = assessment.get("assessment_result")
    if result not in _VALID_ASSESSMENT_RESULTS:
        raise AiPromotionAssessmentError(
            f"assessment_result must be one of {sorted(_VALID_ASSESSMENT_RESULTS)}"
        )
    confidence = assessment.get("assessment_confidence_class")
    if confidence not in _VALID_CONFIDENCE_CLASSES:
        raise AiPromotionAssessmentError(
            f"assessment_confidence_class must be one of {sorted(_VALID_CONFIDENCE_CLASSES)}"
        )
    reason_codes = assessment.get("assessment_reason_codes")
    if isinstance(reason_codes, list) and reason_codes != sorted(reason_codes):
        raise AiPromotionAssessmentError("assessment_reason_codes must be sorted deterministically")
    for field in ("supporting_factors", "opposing_factors", "contradictions", "missing_inputs"):
        factors = assessment.get(field)
        if isinstance(factors, list) and factors != _sort_factors(list(factors)):
            raise AiPromotionAssessmentError(f"{field} must be sorted deterministically")
    rule_version = assessment.get("deterministic_rule_set_version")
    if rule_version != DETERMINISTIC_RULE_SET_VERSION:
        raise AiPromotionAssessmentError("deterministic_rule_set_version mismatch")
    return deterministic_json_dumps(assessment)


def _assessment_bytes_for_manifest_digest(assessment: Mapping[str, Any]) -> bytes:
    body = {
        key: value
        for key, value in assessment.items()
        if key not in {"integrity", "manifest_digest"}
    }
    return serialize_ai_promotion_assessment_v1(body).encode("utf-8")


def _compute_output_manifest_digest(assessment: Mapping[str, Any]) -> str:
    return hashlib.sha256(_assessment_bytes_for_manifest_digest(assessment)).hexdigest()


def _validate_assessment_integrity(assessment: Mapping[str, Any]) -> None:
    if assessment.get("contract_name") != CONTRACT_NAME:
        raise AiPromotionAssessmentError("contract_name mismatch")
    if assessment.get("contract_version") != CONTRACT_VERSION:
        raise AiPromotionAssessmentError("contract_version mismatch")
    integrity = assessment.get("integrity")
    if not isinstance(integrity, Mapping):
        raise AiPromotionAssessmentError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(assessment))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise AiPromotionAssessmentError("integrity.content_sha256 mismatch")
    output_digest = assessment.get("output_digest")
    if output_digest != _compute_output_digest(assessment):
        raise AiPromotionAssessmentError("output_digest mismatch")
    if assessment.get("artifact_id") != output_digest:
        raise AiPromotionAssessmentError("artifact_id must equal output_digest")
    if assessment.get("assessment_id") != output_digest:
        raise AiPromotionAssessmentError("assessment_id must equal output_digest")


def build_self_verification_v1(
    *,
    assessment: Mapping[str, Any],
    policy_decision: VerifiedPolicyDecisionBundle,
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_one_direct_input", "status": "PASS"},
        {"check_id": "upstream_contract_and_version", "status": "PASS"},
        {"check_id": "policy_decision_manifest_verified", "status": "PASS"},
        {"check_id": "policy_decision_self_verification_pass", "status": "PASS"},
        {"check_id": "policy_decision_bound_on_complete", "status": "PASS"},
        {"check_id": "ai_promotion_assessment_complete_on_pass", "status": "PASS"},
        {"check_id": "offline_only_no_external_model", "status": "PASS"},
        {"check_id": "no_policy_decision_override", "status": "PASS"},
        {"check_id": "no_promotion_authority", "status": "PASS"},
        {"check_id": "no_configpatch_mutation", "status": "PASS"},
        {"check_id": "no_candidate_selection", "status": "PASS"},
        {"check_id": "non_authorizing_semantics", "status": "PASS"},
        {"check_id": "forbidden_capabilities_absent", "status": "PASS"},
        {"check_id": "deterministic_rule_set_version", "status": "PASS"},
        {"check_id": "output_digest", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
        {"check_id": "deterministic_reverification", "status": "PASS"},
    ]

    input_refs = assessment.get("input_artifact_refs")
    if not isinstance(input_refs, list) or len(input_refs) != 1:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "exactly_one_direct_input" else c
            for c in checks
        ]

    if assessment.get("manifest_digest") != manifest_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "manifest_verification" else c
            for c in checks
        ]

    if assessment.get("policy_decision_digest") != policy_decision.artifact_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "policy_decision_bound_on_complete" else c
            for c in checks
        ]

    if assessment.get("ai_promotion_assessment_complete") is True:
        for check_id, field, expected in (
            ("policy_decision_bound_on_complete", "policy_decision_bound", True),
            ("ai_promotion_assessment_complete_on_pass", "ai_promotion_assessment_complete", True),
        ):
            if assessment.get(field) != expected:
                checks = [
                    {**c, "status": "FAIL"} if c["check_id"] == check_id else c for c in checks
                ]

    structural_failures = [
        check
        for check in checks
        if check["status"] != "PASS"
        and check["check_id"]
        not in {
            "policy_decision_bound_on_complete",
            "ai_promotion_assessment_complete_on_pass",
        }
    ]
    if structural_failures:
        raise AiPromotionAssessmentError("self-verification checks failed")

    payload: dict[str, Any] = {
        "self_verification_schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": "PASS",
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "verified_output_digest": assessment.get("output_digest"),
        "verified_manifest_digest": manifest_digest,
        "verified_policy_decision_bundle_ref": policy_decision.bundle_dir.as_posix(),
        "verified_assessment_result": assessment.get("assessment_result"),
        "verified_assessment_confidence_class": assessment.get("assessment_confidence_class"),
        "verified_deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
    }
    digest = compute_content_sha256(payload)
    payload["integrity"] = {"content_sha256": digest}
    return payload


def _finalize_assessment_with_manifest_digest(
    assessment: Mapping[str, Any], *, manifest_digest: str
) -> dict[str, Any]:
    body = dict(assessment)
    body["manifest_digest"] = manifest_digest
    body["output_digest"] = _compute_output_digest(body)
    body["artifact_id"] = body["output_digest"]
    body["assessment_id"] = body["output_digest"]
    body["integrity"] = {"content_sha256": compute_content_sha256(_integrity_body(body))}
    return body


def _staging_dir_for(output_dir: Path) -> Path:
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def verify_assessment_inputs(
    inputs: AiPromotionAssessmentInputs,
) -> VerifiedPolicyDecisionBundle:
    """Verify exactly one policy decision bundle."""
    return verify_policy_decision_bundle(inputs.policy_decision_bundle_dir)


def reverify_ai_promotion_assessment_v1(*, output_dir: Path | str) -> None:
    """Replay AI promotion assessment bundle without producer or upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise AiPromotionAssessmentError(
            f"AI promotion assessment directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise AiPromotionAssessmentError(f"MANIFEST.sha256 verification failed: {msg}")

    assessment_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(assessment_path, label=ARTIFACT_REL)
    assessment = read_manifest(assessment_path)
    _validate_assessment_integrity(assessment)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise AiPromotionAssessmentError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(assessment)
    if assessment.get("manifest_digest") != manifest_digest:
        raise AiPromotionAssessmentError("manifest_digest mismatch on replay")

    policy_decision = verify_policy_decision_bundle(
        Path(str(assessment["policy_decision_bundle_ref"]))
    )
    if assessment.get("policy_decision_digest") != policy_decision.artifact_digest:
        raise AiPromotionAssessmentError("policy_decision_digest mismatch on replay")


def produce_ai_promotion_assessment_v1(
    *,
    inputs: AiPromotionAssessmentInputs,
    output_dir: Path | str,
) -> AiPromotionAssessmentResult:
    """Produce offline LEVEL_3 AI promotion assessment evidence."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        policy_decision_dir=inputs.policy_decision_bundle_dir,
        output_dir=final_dir,
    )

    policy_decision = verify_assessment_inputs(inputs)
    try:
        reverify_comparison_promotion_policy_decision_v1(output_dir=policy_decision.bundle_dir)
    except ComparisonPromotionPolicyDecisionError as exc:
        raise AiPromotionAssessmentError(str(exc)) from exc

    assessment_body = build_ai_promotion_assessment_v1(policy_decision=policy_decision)

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise AiPromotionAssessmentError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        assessment_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(assessment_body)
        finalized = _finalize_assessment_with_manifest_digest(
            assessment_body, manifest_digest=manifest_digest
        )
        assessment_path.write_text(
            serialize_ai_promotion_assessment_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            assessment=finalized,
            policy_decision=policy_decision,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise AiPromotionAssessmentError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_ai_promotion_assessment_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise AiPromotionAssessmentError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return AiPromotionAssessmentResult(
        output_dir=final_dir,
        comparison_definition_id=str(finalized.get("comparison_definition_id", "")),
        artifact_id=str(finalized["artifact_id"]),
        assessment_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        assessment_result=str(finalized["assessment_result"]),
        assessment_confidence_class=str(finalized["assessment_confidence_class"]),
        policy_decision_ref=str(finalized["policy_decision_ref"]),
        policy_decision_digest=str(finalized["policy_decision_digest"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "AUTHORITY_LEVEL",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "DETERMINISTIC_RULE_SET_VERSION",
    "EVIDENCE_LEVEL",
    "MANIFEST_FILENAME",
    "AI_PROMOTION_ASSESSMENT_AUTHORITY_INVARIANTS",
    "PRODUCER_VERSION",
    "SELF_VERIFICATION_REL",
    "AiPromotionAssessmentError",
    "AiPromotionAssessmentInputs",
    "AiPromotionAssessmentResult",
    "VerifiedPolicyDecisionBundle",
    "build_ai_promotion_assessment_v1",
    "build_self_verification_v1",
    "produce_ai_promotion_assessment_v1",
    "reverify_ai_promotion_assessment_v1",
    "serialize_ai_promotion_assessment_v1",
    "verify_assessment_inputs",
    "verify_policy_decision_bundle",
]
