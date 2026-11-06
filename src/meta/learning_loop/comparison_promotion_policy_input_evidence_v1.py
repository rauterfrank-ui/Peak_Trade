"""Offline LEVEL_3 promotion policy input evidence from verified policy input binding v1."""

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
from src.meta.learning_loop.comparison_eligibility_promotion_policy_input_binding_v1 import (
    ARTIFACT_REL as UPSTREAM_ARTIFACT_REL,
    CONTRACT_NAME as UPSTREAM_CONTRACT_NAME,
    CONTRACT_VERSION as UPSTREAM_CONTRACT_VERSION,
    PRODUCER_VERSION as UPSTREAM_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as UPSTREAM_SELF_VERIFICATION_REL,
    ComparisonEligibilityPromotionPolicyInputBindingError,
    reverify_comparison_eligibility_promotion_policy_input_binding_v1,
    verify_candidate_input_bundle,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.comparison_promotion_candidate_model_parameter_identity_binding_v1 import (
    verify_eligibility_evidence_bundle,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

CONTRACT_NAME = "comparison_promotion_policy_input_evidence_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "comparison_promotion_policy_input_evidence_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING_EVIDENCE_ONLY"
RECORD_KIND = "comparison_promotion_policy_input_evidence_record"
INPUT_RELATION = "EVIDENCES_VERIFIED_POLICY_INPUT_BINDING_V1"
ARTIFACT_REL = "comparison_promotion_policy_input_evidence_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".comparison_promotion_policy_input_evidence_staging_"

OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"

_VALID_EVIDENCE_STATUS = frozenset({"PASS", "FAIL", "INCOMPLETE", "NOT_EVALUABLE"})
_IDENTITY_BOUND = "BOUND"
_IDENTITY_NOT_BOUND = "NOT_BOUND"
_ELIGIBILITY_VERIFIED = "VERIFIED"
_ELIGIBILITY_NOT_VERIFIED = "NOT_VERIFIED"
_CANDIDATE_SELECTION_NOT_SELECTED = "NOT_SELECTED"
_WINNER_SELECTION_NOT_SELECTED = "NOT_SELECTED"
_CANDIDATE_ACCEPTANCE_NOT_ACCEPTED = "NOT_ACCEPTED"
_CONFIG_PATCH_ACCEPTANCE_NOT_ACCEPTED = "NOT_ACCEPTED"

PROMOTION_POLICY_INPUT_EVIDENCE_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "promotion_policy_input_evidence_is_descriptive_only": True,
    "promotion_policy_input_evidence_does_not_select": True,
    "promotion_policy_input_evidence_does_not_choose_winner": True,
    "promotion_policy_input_evidence_does_not_accept": True,
    "promotion_policy_input_evidence_does_not_construct_promotion_candidate": True,
    "promotion_policy_input_evidence_does_not_execute_operational_filter": True,
    "promotion_policy_input_evidence_does_not_execute_policy": True,
    "promotion_policy_input_evidence_does_not_recompute_eligibility": True,
    "promotion_policy_input_evidence_does_not_create_configpatch": True,
    "promotion_policy_input_evidence_does_not_modify_configpatch": True,
    "promotion_policy_input_evidence_does_not_apply_configpatch": True,
    "promotion_policy_input_evidence_does_not_modify_config": True,
    "promotion_policy_input_evidence_does_not_authorize_promotion": True,
    "promotion_policy_input_evidence_does_not_authorize_runtime": True,
    "promotion_policy_input_evidence_does_not_authorize_live": True,
    "promotion_policy_input_evidence_does_not_deploy": True,
    "promotion_policy_input_evidence_does_not_activate": True,
    "promotion_policy_input_evidence_does_not_create_order_intent": True,
    "promotion_policy_input_evidence_does_not_modify_trading_logic": True,
    "evidence_does_not_authorize_promotion": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_comparison_promotion_policy_input_evidence": True,
    "evidence_does_not_authorize_promotion": True,
    "evidence_does_not_authorize_runtime": True,
    "promotion_policy_input_evidence_does_not_select": True,
    "promotion_policy_input_evidence_does_not_choose_winner": True,
    "promotion_policy_input_evidence_does_not_accept_candidate": True,
    "promotion_policy_input_evidence_does_not_accept_configpatch": True,
    "promotion_policy_input_evidence_does_not_construct_promotion_candidate": True,
    "promotion_policy_input_evidence_does_not_execute_operational_filter": True,
    "promotion_policy_input_evidence_does_not_execute_policy": True,
    "promotion_policy_input_evidence_does_not_recompute_eligibility": True,
    "promotion_policy_input_evidence_does_not_create_configpatch": True,
    "promotion_policy_input_evidence_does_not_modify_configpatch": True,
    "promotion_policy_input_evidence_does_not_apply_configpatch": True,
    "promotion_policy_input_evidence_does_not_modify_config": True,
    "promotion_policy_input_evidence_does_not_authorize_promotion": True,
    "promotion_policy_input_evidence_does_not_authorize_runtime": True,
    "promotion_policy_input_evidence_does_not_authorize_live": True,
    "promotion_policy_input_evidence_does_not_deploy": True,
    "promotion_policy_input_evidence_does_not_activate": True,
    "promotion_policy_input_evidence_does_not_create_order_intent": True,
    "promotion_policy_input_evidence_does_not_modify_trading_logic": True,
    "configpatch_created": False,
    "configpatch_modified": False,
    "configpatch_applied": False,
    "configpatch_accepted": False,
    "candidate_selected": False,
    "winner_selected": False,
    "candidate_accepted": False,
    "promotion_candidate_constructed": False,
    "operational_filter_executed": False,
    "eligibility_recomputed": False,
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
        "promotion_decision",
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

_SELF_VERIFICATION_SCHEMA_VERSION = (
    "comparison_promotion_policy_input_evidence_self_verification_v1"
)


class ComparisonPromotionPolicyInputEvidenceError(ValueError):
    """Fail-closed promotion policy input evidence error."""


@dataclass(frozen=True)
class VerifiedPolicyInputBindingBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    evidence_payload: dict[str, Any]


@dataclass(frozen=True)
class ComparisonPromotionPolicyInputEvidenceInputs:
    policy_input_binding_bundle_dir: Path


@dataclass(frozen=True)
class ComparisonPromotionPolicyInputEvidenceResult:
    output_dir: Path
    comparison_definition_id: str
    artifact_id: str
    evidence_path: Path
    self_verification_path: Path
    manifest_path: Path
    promotion_policy_input_evidence_status: str
    candidate_identity_ref: str
    config_patch_manifest_id: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ComparisonPromotionPolicyInputEvidenceError(f"{label} must not be a symlink")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ComparisonPromotionPolicyInputEvidenceError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ComparisonPromotionPolicyInputEvidenceError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise ComparisonPromotionPolicyInputEvidenceError(
            f"{label} must be a directory: {bundle_dir}"
        )


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ComparisonPromotionPolicyInputEvidenceError(
            f"output directory already exists: {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ComparisonPromotionPolicyInputEvidenceError("output directory must not be under /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, policy_input_binding_dir: Path, output_dir: Path) -> None:
    input_res = policy_input_binding_dir.resolve()
    output_res = output_dir.resolve()
    if output_res == input_res:
        raise ComparisonPromotionPolicyInputEvidenceError(
            "output directory must not equal input path"
        )
    if _path_is_under(output_res, input_res):
        raise ComparisonPromotionPolicyInputEvidenceError(
            "output directory must not be inside input path"
        )
    if input_res.is_dir() and _path_is_under(input_res, output_res):
        raise ComparisonPromotionPolicyInputEvidenceError(
            "input directory must not be inside output directory"
        )


def _manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / MANIFEST_FILENAME
    _validate_regular_file(manifest_path, label=MANIFEST_FILENAME)
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _validate_capabilities(capabilities: Any) -> list[str]:
    if capabilities is None:
        return []
    if not isinstance(capabilities, list):
        raise ComparisonPromotionPolicyInputEvidenceError("capabilities must be a list")
    normalized: list[str] = []
    for item in capabilities:
        if not isinstance(item, str):
            raise ComparisonPromotionPolicyInputEvidenceError(
                "capabilities entries must be strings"
            )
        if item in _FORBIDDEN_CAPABILITIES:
            raise ComparisonPromotionPolicyInputEvidenceError(f"forbidden capability: {item}")
        normalized.append(item)
    return sorted(normalized)


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if payload.get(key) is not expected:
            raise ComparisonPromotionPolicyInputEvidenceError(f"{key} must be {expected!r}")


_COMPLETION_FLAGS: tuple[str, ...] = (
    "promotion_policy_input_evidence_complete",
    "eligibility_policy_input_bound",
    "candidate_input_bound",
    "eligibility_evidence_bound",
    "cross_domain_lineage_bound",
    "config_patch_manifest_bound",
)


def _validate_completion_flags(payload: Mapping[str, Any], *, status: str) -> None:
    expected = status == "PASS"
    for key in _COMPLETION_FLAGS:
        if payload.get(key) is not expected:
            raise ComparisonPromotionPolicyInputEvidenceError(
                f"{key} must be {expected!r} when promotion_policy_input_evidence_status is {status!r}"
            )


def _sorted_reason_codes(codes: list[str]) -> list[str]:
    return sorted(set(codes))


def _non_empty_ref(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _load_self_verification(bundle_dir: Path, *, rel: str, label: str) -> dict[str, Any]:
    path = bundle_dir / rel
    _validate_regular_file(path, label=label)
    payload = read_manifest(path)
    if not isinstance(payload, dict):
        raise ComparisonPromotionPolicyInputEvidenceError(f"{label} must be a JSON object")
    return payload


def verify_policy_input_binding_bundle(
    bundle_dir: Path | str,
) -> VerifiedPolicyInputBindingBundle:
    """Fail-closed verification of exactly one Step-4 policy input binding bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="policy input binding bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise ComparisonPromotionPolicyInputEvidenceError(
            f"policy input binding MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = path / UPSTREAM_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=UPSTREAM_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != UPSTREAM_CONTRACT_NAME:
        raise ComparisonPromotionPolicyInputEvidenceError(
            "upstream policy input binding contract_name mismatch"
        )
    if payload.get("contract_version") != UPSTREAM_CONTRACT_VERSION:
        raise ComparisonPromotionPolicyInputEvidenceError(
            "upstream policy input binding contract_version mismatch"
        )

    self_payload = _load_self_verification(
        path,
        rel=UPSTREAM_SELF_VERIFICATION_REL,
        label=UPSTREAM_SELF_VERIFICATION_REL,
    )
    if self_payload.get("overall_status") != "PASS":
        raise ComparisonPromotionPolicyInputEvidenceError(
            "upstream policy input binding SELF_VERIFICATION overall_status must be PASS"
        )

    try:
        reverify_comparison_eligibility_promotion_policy_input_binding_v1(output_dir=path)
    except ComparisonEligibilityPromotionPolicyInputBindingError as exc:
        raise ComparisonPromotionPolicyInputEvidenceError(str(exc)) from exc

    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ComparisonPromotionPolicyInputEvidenceError(
            "policy input binding integrity must be an object"
        )
    artifact_digest = integrity.get("content_sha256")
    if not isinstance(artifact_digest, str) or not is_valid_sha256_hex(artifact_digest):
        raise ComparisonPromotionPolicyInputEvidenceError(
            "policy input binding integrity.content_sha256 invalid"
        )

    return VerifiedPolicyInputBindingBundle(
        bundle_dir=path.resolve(),
        contract_name=UPSTREAM_CONTRACT_NAME,
        contract_version=UPSTREAM_CONTRACT_VERSION,
        producer_version=UPSTREAM_PRODUCER_VERSION,
        artifact_ref=UPSTREAM_ARTIFACT_REL,
        artifact_digest=artifact_digest,
        manifest_digest=_manifest_file_digest(path),
        evidence_payload=dict(payload),
    )


def _verify_transitive_lineage(
    step4: Mapping[str, Any],
) -> tuple[list[str], dict[str, Any] | None]:
    reason_codes: list[str] = []
    eligibility_payload: dict[str, Any] | None = None

    eligibility_ref = step4.get("eligibility_evidence_ref")
    eligibility_digest = step4.get("eligibility_evidence_digest")
    if not _non_empty_ref(eligibility_ref) or not is_valid_sha256_hex(
        str(eligibility_digest or "")
    ):
        reason_codes.append("ELIGIBILITY_EVIDENCE_NOT_BOUND")
    else:
        try:
            eligibility = verify_eligibility_evidence_bundle(Path(str(eligibility_ref)))
        except Exception:
            reason_codes.append("ELIGIBILITY_EVIDENCE_NOT_BOUND")
        else:
            if eligibility_digest != eligibility.artifact_digest:
                reason_codes.append("ELIGIBILITY_EVIDENCE_DIGEST_MISMATCH")
            else:
                eligibility_payload = eligibility.evidence_payload
                if eligibility_payload.get("candidate_identity_ref") != step4.get(
                    "candidate_identity_ref"
                ):
                    reason_codes.append("CANDIDATE_LINEAGE_MISMATCH")

    candidate_input_ref = step4.get("candidate_input_bundle_ref")
    candidate_input_digest = step4.get("candidate_input_digest")
    if not _non_empty_ref(candidate_input_ref) or not is_valid_sha256_hex(
        str(candidate_input_digest or "")
    ):
        reason_codes.append("CANDIDATE_INPUT_NOT_BOUND")
    else:
        try:
            candidate_input = verify_candidate_input_bundle(Path(str(candidate_input_ref)))
        except Exception:
            reason_codes.append("CANDIDATE_INPUT_NOT_BOUND")
        else:
            if candidate_input_digest != candidate_input.artifact_digest:
                reason_codes.append("CANDIDATE_INPUT_DIGEST_MISMATCH")
            elif candidate_input.evidence_payload.get("candidate_identity_ref") != step4.get(
                "candidate_identity_ref"
            ):
                reason_codes.append("CANDIDATE_INPUT_MISMATCH")

    for field, code in (
        ("model_identity_ref", "MODEL_IDENTITY_MISMATCH"),
        ("model_identity_digest", "MODEL_IDENTITY_MISMATCH"),
        ("parameter_set_identity_ref", "PARAMETER_SET_IDENTITY_MISMATCH"),
        ("parameter_set_identity_digest", "PARAMETER_SET_IDENTITY_MISMATCH"),
        ("config_patch_manifest_ref", "CONFIG_PATCH_MANIFEST_MISMATCH"),
        ("config_patch_manifest_digest", "CONFIG_PATCH_MANIFEST_MISMATCH"),
        ("cross_domain_lineage_binding_bundle_ref", "CROSS_DOMAIN_LINEAGE_MISMATCH"),
        ("cross_domain_lineage_binding_digest", "CROSS_DOMAIN_LINEAGE_MISMATCH"),
        ("experiment_identity_ref", "EXPERIMENT_LINEAGE_MISMATCH"),
        ("experiment_identity_digest", "EXPERIMENT_LINEAGE_MISMATCH"),
        ("dataset_identity_ref", "DATASET_LINEAGE_MISMATCH"),
        ("dataset_identity_digest", "DATASET_LINEAGE_MISMATCH"),
        ("comparison_identity_ref", "COMPARISON_LINEAGE_MISMATCH"),
        ("comparison_identity_digest", "COMPARISON_LINEAGE_MISMATCH"),
        ("comparison_completion_ref", "COMPLETION_EVIDENCE_MISSING"),
        ("comparison_completion_digest", "COMPLETION_EVIDENCE_MISSING"),
        ("research_validity_ref", "RESEARCH_VALIDITY_MISSING"),
        ("research_validity_digest", "RESEARCH_VALIDITY_MISSING"),
        ("promotion_input_binding_ref", "PROMOTION_INPUT_BINDING_MISSING"),
        ("promotion_input_binding_digest", "PROMOTION_INPUT_BINDING_MISSING"),
    ):
        value = step4.get(field)
        if field.endswith("_digest"):
            if not is_valid_sha256_hex(str(value or "")):
                reason_codes.append(code)
        elif not _non_empty_ref(value):
            reason_codes.append(code)

    return reason_codes, eligibility_payload


def _evaluate_policy_input_evidence(
    *,
    step4: Mapping[str, Any],
    transitive_reason_codes: list[str],
) -> tuple[str, str, str, str, str, str, str, list[str], dict[str, bool]]:
    reason_codes = list(transitive_reason_codes)
    completion_flags = {
        "promotion_policy_input_evidence_complete": False,
        "eligibility_policy_input_bound": False,
        "candidate_input_bound": False,
        "eligibility_evidence_bound": False,
        "cross_domain_lineage_bound": False,
        "config_patch_manifest_bound": False,
    }

    upstream_status = str(step4.get("eligibility_policy_input_binding_status", ""))
    if upstream_status == "NOT_EVALUABLE":
        return (
            "NOT_EVALUABLE",
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _ELIGIBILITY_NOT_VERIFIED,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _sorted_reason_codes(reason_codes + ["NOT_EVALUABLE_INSUFFICIENT_EVIDENCE"]),
            completion_flags,
        )
    if upstream_status == "INCOMPLETE":
        return (
            "INCOMPLETE",
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _ELIGIBILITY_NOT_VERIFIED,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _sorted_reason_codes(reason_codes + ["UPSTREAM_POLICY_INPUT_BINDING_INCOMPLETE"]),
            completion_flags,
        )
    if upstream_status == "FAIL":
        return (
            "FAIL",
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _ELIGIBILITY_NOT_VERIFIED,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _sorted_reason_codes(reason_codes + ["UPSTREAM_POLICY_INPUT_BINDING_FAIL"]),
            completion_flags,
        )

    if step4.get("candidate_selection_status") != _CANDIDATE_SELECTION_NOT_SELECTED:
        reason_codes.append("CANDIDATE_SELECTION_DETECTED")
    if step4.get("winner_selection_status") != _WINNER_SELECTION_NOT_SELECTED:
        reason_codes.append("WINNER_SELECTION_DETECTED")
    if step4.get("candidate_acceptance_status") != _CANDIDATE_ACCEPTANCE_NOT_ACCEPTED:
        reason_codes.append("CANDIDATE_ACCEPTANCE_DETECTED")
    if step4.get("config_patch_acceptance_status") != _CONFIG_PATCH_ACCEPTANCE_NOT_ACCEPTED:
        reason_codes.append("CONFIG_PATCH_ACCEPTANCE_DETECTED")
    if step4.get("promotion_candidate_constructed") is True:
        reason_codes.append("PROMOTION_CANDIDATE_CONSTRUCTION_DETECTED")
    if step4.get("operational_filter_executed") is True:
        reason_codes.append("OPERATIONAL_FILTER_DETECTED")
    if step4.get("eligibility_recomputed") is True:
        reason_codes.append("ELIGIBILITY_RECOMPUTATION_DETECTED")
    if step4.get("promotion_policy_executed") is True:
        reason_codes.append("PROMOTION_POLICY_DETECTED")
    if step4.get("promotion_decision_created") is True:
        reason_codes.append("PROMOTION_DECISION_DETECTED")
    if step4.get("configpatch_created") is True:
        reason_codes.append("CONFIGPATCH_CREATION_DETECTED")
    if step4.get("configpatch_modified") is True:
        reason_codes.append("CONFIGPATCH_MUTATION_DETECTED")
    if step4.get("configpatch_applied") is True:
        reason_codes.append("CONFIGPATCH_APPLICATION_DETECTED")
    if step4.get("configpatch_accepted") is True:
        reason_codes.append("CONFIGPATCH_ACCEPTANCE_DETECTED")
    if step4.get("safety_flags_mutated") is True:
        reason_codes.append("SAFETY_FLAGS_MUTATED_DETECTED")
    if step4.get("jsonl_side_effect_created") is True:
        reason_codes.append("JSONL_SIDE_EFFECT_DETECTED")
    if step4.get("promotion_consumers_changed") is True:
        reason_codes.append("PROMOTION_CONSUMERS_CHANGED_DETECTED")
    if step4.get("promotion_authorized") is True:
        reason_codes.append("PROMOTION_AUTHORITY_DETECTED")
    if step4.get("runtime_authorized") is True:
        reason_codes.append("RUNTIME_AUTHORITY_DETECTED")
    if step4.get("live_authorized") is True:
        reason_codes.append("LIVE_AUTHORITY_DETECTED")
    if step4.get("orders_allowed") is True:
        reason_codes.append("ORDERS_ALLOWED_DETECTED")
    if step4.get("scheduler_runtime_allowed") is True:
        reason_codes.append("SCHEDULER_RUNTIME_ALLOWED_DETECTED")

    if step4.get("candidate_input_bound_status") != _IDENTITY_BOUND:
        reason_codes.append("CANDIDATE_INPUT_NOT_BOUND")
    if step4.get("eligibility_evidence_bound_status") != _ELIGIBILITY_VERIFIED:
        reason_codes.append("ELIGIBILITY_EVIDENCE_NOT_BOUND")
    if step4.get("cross_domain_lineage_bound_status") != _IDENTITY_BOUND:
        reason_codes.append("CROSS_DOMAIN_LINEAGE_NOT_BOUND")
    if step4.get("config_patch_manifest_bound_status") != _IDENTITY_BOUND:
        reason_codes.append("CONFIG_PATCH_MANIFEST_NOT_BOUND")
    if step4.get("eligibility_policy_input_bound_status") != _IDENTITY_BOUND:
        reason_codes.append("ELIGIBILITY_POLICY_INPUT_NOT_BOUND")

    fail_codes = {
        "CANDIDATE_SELECTION_DETECTED",
        "WINNER_SELECTION_DETECTED",
        "CANDIDATE_ACCEPTANCE_DETECTED",
        "CONFIG_PATCH_ACCEPTANCE_DETECTED",
        "PROMOTION_CANDIDATE_CONSTRUCTION_DETECTED",
        "OPERATIONAL_FILTER_DETECTED",
        "ELIGIBILITY_RECOMPUTATION_DETECTED",
        "PROMOTION_POLICY_DETECTED",
        "PROMOTION_DECISION_DETECTED",
        "CONFIGPATCH_CREATION_DETECTED",
        "CONFIGPATCH_MUTATION_DETECTED",
        "CONFIGPATCH_APPLICATION_DETECTED",
        "CONFIGPATCH_ACCEPTANCE_DETECTED",
        "SAFETY_FLAGS_MUTATED_DETECTED",
        "JSONL_SIDE_EFFECT_DETECTED",
        "PROMOTION_CONSUMERS_CHANGED_DETECTED",
        "PROMOTION_AUTHORITY_DETECTED",
        "RUNTIME_AUTHORITY_DETECTED",
        "LIVE_AUTHORITY_DETECTED",
        "ORDERS_ALLOWED_DETECTED",
        "SCHEDULER_RUNTIME_ALLOWED_DETECTED",
        "CANDIDATE_INPUT_NOT_BOUND",
        "CANDIDATE_INPUT_DIGEST_MISMATCH",
        "CANDIDATE_INPUT_MISMATCH",
        "ELIGIBILITY_EVIDENCE_NOT_BOUND",
        "ELIGIBILITY_EVIDENCE_DIGEST_MISMATCH",
        "CANDIDATE_LINEAGE_MISMATCH",
        "MODEL_IDENTITY_MISMATCH",
        "PARAMETER_SET_IDENTITY_MISMATCH",
        "CONFIG_PATCH_MANIFEST_MISMATCH",
        "CROSS_DOMAIN_LINEAGE_MISMATCH",
        "EXPERIMENT_LINEAGE_MISMATCH",
        "DATASET_LINEAGE_MISMATCH",
        "COMPARISON_LINEAGE_MISMATCH",
        "COMPLETION_EVIDENCE_MISSING",
        "RESEARCH_VALIDITY_MISSING",
        "PROMOTION_INPUT_BINDING_MISSING",
        "ELIGIBILITY_POLICY_INPUT_NOT_BOUND",
        "CONFIG_PATCH_MANIFEST_NOT_BOUND",
        "CROSS_DOMAIN_LINEAGE_NOT_BOUND",
    }

    evidence_status = "PASS"
    policy_input_bound = _IDENTITY_BOUND
    candidate_input_bound = _IDENTITY_BOUND
    eligibility_bound = _ELIGIBILITY_VERIFIED
    cross_domain_bound = _IDENTITY_BOUND
    config_patch_bound = _IDENTITY_BOUND
    candidate_bound = _IDENTITY_BOUND

    if any(code in reason_codes for code in fail_codes):
        evidence_status = "FAIL"
        if (
            "CANDIDATE_INPUT_NOT_BOUND" in reason_codes
            or "CANDIDATE_INPUT_MISMATCH" in reason_codes
        ):
            candidate_input_bound = _IDENTITY_NOT_BOUND
        if (
            "ELIGIBILITY_EVIDENCE_NOT_BOUND" in reason_codes
            or "ELIGIBILITY_EVIDENCE_DIGEST_MISMATCH" in reason_codes
        ):
            eligibility_bound = _ELIGIBILITY_NOT_VERIFIED
        if (
            "CROSS_DOMAIN_LINEAGE_NOT_BOUND" in reason_codes
            or "CROSS_DOMAIN_LINEAGE_MISMATCH" in reason_codes
        ):
            cross_domain_bound = _IDENTITY_NOT_BOUND
        if (
            "CONFIG_PATCH_MANIFEST_NOT_BOUND" in reason_codes
            or "CONFIG_PATCH_MANIFEST_MISMATCH" in reason_codes
        ):
            config_patch_bound = _IDENTITY_NOT_BOUND
        if "ELIGIBILITY_POLICY_INPUT_NOT_BOUND" in reason_codes:
            policy_input_bound = _IDENTITY_NOT_BOUND
        if "CANDIDATE_LINEAGE_MISMATCH" in reason_codes:
            candidate_bound = _IDENTITY_NOT_BOUND

    if evidence_status == "PASS":
        reason_codes.extend(
            [
                "ELIGIBILITY_POLICY_INPUT_BOUND",
                "CANDIDATE_INPUT_BOUND",
                "ELIGIBILITY_EVIDENCE_BOUND",
                "CROSS_DOMAIN_LINEAGE_BOUND",
                "CONFIG_PATCH_MANIFEST_BOUND",
                "COMPARISON_PROMOTION_POLICY_INPUT_EVIDENCE_COMPLETE",
            ]
        )
        completion_flags = {
            "promotion_policy_input_evidence_complete": True,
            "eligibility_policy_input_bound": True,
            "candidate_input_bound": True,
            "eligibility_evidence_bound": True,
            "cross_domain_lineage_bound": True,
            "config_patch_manifest_bound": True,
        }

    return (
        evidence_status,
        policy_input_bound,
        candidate_input_bound,
        eligibility_bound,
        cross_domain_bound,
        config_patch_bound,
        candidate_bound,
        _sorted_reason_codes(reason_codes),
        completion_flags,
    )


def _input_artifact_ref_mapping(*, bundle: VerifiedPolicyInputBindingBundle) -> dict[str, Any]:
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
        {"output_digest", "manifest_digest", "integrity", "created_at", "artifact_id"}
    )
    digest_body = {key: body[key] for key in sorted(body) if key not in excluded}
    return compute_content_sha256(digest_body)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in body.items() if key not in {"integrity", "manifest_digest"}
    }


def build_comparison_promotion_policy_input_evidence_v1(
    *,
    policy_input_binding: VerifiedPolicyInputBindingBundle,
) -> dict[str, Any]:
    step4 = policy_input_binding.evidence_payload
    transitive_codes, _eligibility = _verify_transitive_lineage(step4)
    (
        evidence_status,
        policy_input_bound_status,
        candidate_input_bound_status,
        eligibility_bound_status,
        cross_domain_bound_status,
        config_patch_bound_status,
        candidate_bound_status,
        reason_codes,
        completion_flags,
    ) = _evaluate_policy_input_evidence(step4=step4, transitive_reason_codes=transitive_codes)

    input_refs = [_input_artifact_ref_mapping(bundle=policy_input_binding)]
    parent_artifact_refs = list(step4.get("parent_artifact_refs", []))
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
        "created_at": OFFLINE_DETERMINISTIC_CREATED_AT,
        "producer_version": PRODUCER_VERSION,
        "record_kind": RECORD_KIND,
        "input_relation": INPUT_RELATION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "capabilities": [],
        "is_comparison_promotion_policy_input_evidence": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "promotion_policy_input_evidence_does_not_select": True,
        "promotion_policy_input_evidence_does_not_choose_winner": True,
        "promotion_policy_input_evidence_does_not_accept_candidate": True,
        "promotion_policy_input_evidence_does_not_accept_configpatch": True,
        "promotion_policy_input_evidence_does_not_construct_promotion_candidate": True,
        "promotion_policy_input_evidence_does_not_execute_operational_filter": True,
        "promotion_policy_input_evidence_does_not_execute_policy": True,
        "promotion_policy_input_evidence_does_not_recompute_eligibility": True,
        "promotion_policy_input_evidence_does_not_create_configpatch": True,
        "promotion_policy_input_evidence_does_not_modify_configpatch": True,
        "promotion_policy_input_evidence_does_not_apply_configpatch": True,
        "promotion_policy_input_evidence_does_not_modify_config": True,
        "promotion_policy_input_evidence_does_not_authorize_promotion": True,
        "promotion_policy_input_evidence_does_not_authorize_runtime": True,
        "promotion_policy_input_evidence_does_not_authorize_live": True,
        "promotion_policy_input_evidence_does_not_deploy": True,
        "promotion_policy_input_evidence_does_not_activate": True,
        "promotion_policy_input_evidence_does_not_create_order_intent": True,
        "promotion_policy_input_evidence_does_not_modify_trading_logic": True,
        "promotion_policy_input_evidence_authority_invariants": dict(
            PROMOTION_POLICY_INPUT_EVIDENCE_AUTHORITY_INVARIANTS
        ),
        "configpatch_created": False,
        "configpatch_modified": False,
        "configpatch_applied": False,
        "configpatch_accepted": False,
        "candidate_selected": False,
        "winner_selected": False,
        "candidate_accepted": False,
        "promotion_candidate_constructed": False,
        "operational_filter_executed": False,
        "eligibility_recomputed": False,
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
        "policy_input_binding_bundle_ref": policy_input_binding.bundle_dir.as_posix(),
        "policy_input_binding_artifact_ref": policy_input_binding.artifact_ref,
        "policy_input_binding_digest": policy_input_binding.artifact_digest,
        "policy_input_binding_manifest_digest": policy_input_binding.manifest_digest,
        "upstream_contract_name": policy_input_binding.contract_name,
        "upstream_contract_version": policy_input_binding.contract_version,
        "upstream_producer_version": policy_input_binding.producer_version,
        "upstream_eligibility_policy_input_binding_status": str(
            step4.get("eligibility_policy_input_binding_status", "")
        ),
        "promotion_policy_input_evidence_status": evidence_status,
        "promotion_policy_input_evidence_reason_codes": reason_codes,
        "eligibility_policy_input_bound_status": policy_input_bound_status,
        "candidate_input_bound_status": candidate_input_bound_status,
        "eligibility_evidence_bound_status": eligibility_bound_status,
        "cross_domain_lineage_bound_status": cross_domain_bound_status,
        "config_patch_manifest_bound_status": config_patch_bound_status,
        "candidate_identity_bound_status": candidate_bound_status,
        "candidate_selection_status": _CANDIDATE_SELECTION_NOT_SELECTED,
        "winner_selection_status": _WINNER_SELECTION_NOT_SELECTED,
        "candidate_acceptance_status": _CANDIDATE_ACCEPTANCE_NOT_ACCEPTED,
        "config_patch_acceptance_status": _CONFIG_PATCH_ACCEPTANCE_NOT_ACCEPTED,
        "candidate_input_bundle_ref": str(step4.get("candidate_input_bundle_ref", "")),
        "candidate_input_digest": str(step4.get("candidate_input_digest", "")),
        "candidate_input_manifest_digest": str(step4.get("candidate_input_manifest_digest", "")),
        "candidate_identity_ref": str(step4.get("candidate_identity_ref", "")),
        "candidate_identity_digest": str(step4.get("candidate_identity_digest", "")),
        "experiment_identity_ref": str(step4.get("experiment_identity_ref", "")),
        "experiment_identity_digest": str(step4.get("experiment_identity_digest", "")),
        "experiment_identity_id": str(step4.get("experiment_identity_id", "")),
        "dataset_identity_ref": str(step4.get("dataset_identity_ref", "")),
        "dataset_identity_digest": str(step4.get("dataset_identity_digest", "")),
        "comparison_identity_ref": str(step4.get("comparison_identity_ref", "")),
        "comparison_identity_digest": str(step4.get("comparison_identity_digest", "")),
        "comparison_definition_id": str(step4.get("comparison_definition_id", "")),
        "comparison_completion_ref": str(step4.get("comparison_completion_ref", "")),
        "comparison_completion_digest": str(step4.get("comparison_completion_digest", "")),
        "research_validity_ref": str(step4.get("research_validity_ref", "")),
        "research_validity_digest": str(step4.get("research_validity_digest", "")),
        "promotion_input_binding_ref": str(step4.get("promotion_input_binding_ref", "")),
        "promotion_input_binding_digest": str(step4.get("promotion_input_binding_digest", "")),
        "config_patch_manifest_ref": str(step4.get("config_patch_manifest_ref", "")),
        "config_patch_manifest_digest": str(step4.get("config_patch_manifest_digest", "")),
        "config_patch_manifest_id": str(step4.get("config_patch_manifest_id", "")),
        "config_patch_contract_name": str(step4.get("config_patch_contract_name", "")),
        "config_patch_contract_version": str(step4.get("config_patch_contract_version", "")),
        "cross_domain_lineage_binding_bundle_ref": str(
            step4.get("cross_domain_lineage_binding_bundle_ref", "")
        ),
        "cross_domain_lineage_binding_digest": str(
            step4.get("cross_domain_lineage_binding_digest", "")
        ),
        "input_artifact_refs": input_refs,
        "parent_artifact_refs": parent_artifact_refs,
        "input_digest": "",
        "output_digest": "",
        "manifest_digest": "",
        **completion_flags,
    }

    for field in (
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
    ):
        value = step4.get(field)
        if value is not None:
            payload[field] = str(value)

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    _validate_completion_flags(payload, status=evidence_status)
    _validate_capabilities(payload["capabilities"])

    payload["input_digest"] = compute_content_sha256({"input_artifact_refs": input_refs})
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    return payload


def serialize_comparison_promotion_policy_input_evidence_v1(
    evidence: Mapping[str, Any],
) -> str:
    _reject_forbidden_index_keys(evidence)
    status = evidence.get("promotion_policy_input_evidence_status")
    _validate_non_authorizing_flags(evidence)
    if status in _VALID_EVIDENCE_STATUS:
        _validate_completion_flags(evidence, status=str(status))
    _validate_capabilities(evidence.get("capabilities"))
    if status not in _VALID_EVIDENCE_STATUS:
        raise ComparisonPromotionPolicyInputEvidenceError(
            f"promotion_policy_input_evidence_status must be one of {sorted(_VALID_EVIDENCE_STATUS)}"
        )
    reason_codes = evidence.get("promotion_policy_input_evidence_reason_codes")
    if isinstance(reason_codes, list) and reason_codes != sorted(reason_codes):
        raise ComparisonPromotionPolicyInputEvidenceError(
            "promotion_policy_input_evidence_reason_codes must be sorted deterministically"
        )
    return deterministic_json_dumps(evidence)


def _evidence_bytes_for_manifest_digest(evidence: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in evidence.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_comparison_promotion_policy_input_evidence_v1(body).encode("utf-8")


def _compute_output_manifest_digest(evidence: Mapping[str, Any]) -> str:
    return hashlib.sha256(_evidence_bytes_for_manifest_digest(evidence)).hexdigest()


def _validate_evidence_integrity(evidence: Mapping[str, Any]) -> None:
    if evidence.get("contract_name") != CONTRACT_NAME:
        raise ComparisonPromotionPolicyInputEvidenceError("contract_name mismatch")
    if evidence.get("contract_version") != CONTRACT_VERSION:
        raise ComparisonPromotionPolicyInputEvidenceError("contract_version mismatch")
    integrity = evidence.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ComparisonPromotionPolicyInputEvidenceError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(evidence))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise ComparisonPromotionPolicyInputEvidenceError("integrity.content_sha256 mismatch")
    output_digest = evidence.get("output_digest")
    if output_digest != _compute_output_digest(evidence):
        raise ComparisonPromotionPolicyInputEvidenceError("output_digest mismatch")
    if evidence.get("artifact_id") != output_digest:
        raise ComparisonPromotionPolicyInputEvidenceError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    evidence: Mapping[str, Any],
    policy_input_binding: VerifiedPolicyInputBindingBundle,
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_one_direct_input", "status": "PASS"},
        {"check_id": "upstream_contract_and_version", "status": "PASS"},
        {"check_id": "policy_input_binding_manifest_verified", "status": "PASS"},
        {"check_id": "policy_input_binding_self_verification_pass", "status": "PASS"},
        {"check_id": "eligibility_policy_input_bound_on_pass", "status": "PASS"},
        {"check_id": "candidate_input_bound_on_pass", "status": "PASS"},
        {"check_id": "eligibility_evidence_bound_on_pass", "status": "PASS"},
        {"check_id": "cross_domain_lineage_bound_on_pass", "status": "PASS"},
        {"check_id": "config_patch_manifest_bound_on_pass", "status": "PASS"},
        {"check_id": "promotion_policy_input_evidence_complete_on_pass", "status": "PASS"},
        {"check_id": "no_candidate_selection", "status": "PASS"},
        {"check_id": "no_winner_selection", "status": "PASS"},
        {"check_id": "no_candidate_acceptance", "status": "PASS"},
        {"check_id": "no_configpatch_acceptance", "status": "PASS"},
        {"check_id": "no_configpatch_creation", "status": "PASS"},
        {"check_id": "no_configpatch_mutation", "status": "PASS"},
        {"check_id": "no_configpatch_application", "status": "PASS"},
        {"check_id": "no_promotion_candidate_construction", "status": "PASS"},
        {"check_id": "no_eligibility_recomputation", "status": "PASS"},
        {"check_id": "no_promotion_policy_execution", "status": "PASS"},
        {"check_id": "no_promotion_decision", "status": "PASS"},
        {"check_id": "non_authorizing_semantics", "status": "PASS"},
        {"check_id": "forbidden_capabilities_absent", "status": "PASS"},
        {"check_id": "output_digest", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
        {"check_id": "deterministic_reverification", "status": "PASS"},
    ]

    input_refs = evidence.get("input_artifact_refs")
    if not isinstance(input_refs, list) or len(input_refs) != 1:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "exactly_one_direct_input" else c
            for c in checks
        ]

    if evidence.get("manifest_digest") != manifest_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "manifest_verification" else c
            for c in checks
        ]

    evidence_status = evidence.get("promotion_policy_input_evidence_status")
    if evidence_status == "PASS":
        for check_id, field, expected in (
            (
                "eligibility_policy_input_bound_on_pass",
                "eligibility_policy_input_bound_status",
                _IDENTITY_BOUND,
            ),
            ("candidate_input_bound_on_pass", "candidate_input_bound_status", _IDENTITY_BOUND),
            (
                "eligibility_evidence_bound_on_pass",
                "eligibility_evidence_bound_status",
                _ELIGIBILITY_VERIFIED,
            ),
            (
                "cross_domain_lineage_bound_on_pass",
                "cross_domain_lineage_bound_status",
                _IDENTITY_BOUND,
            ),
            (
                "config_patch_manifest_bound_on_pass",
                "config_patch_manifest_bound_status",
                _IDENTITY_BOUND,
            ),
            (
                "promotion_policy_input_evidence_complete_on_pass",
                "promotion_policy_input_evidence_complete",
                True,
            ),
        ):
            if evidence.get(field) != expected:
                checks = [
                    {**c, "status": "FAIL"} if c["check_id"] == check_id else c for c in checks
                ]

    structural_failures = [
        check
        for check in checks
        if check["status"] != "PASS"
        and check["check_id"]
        not in {
            "eligibility_policy_input_bound_on_pass",
            "candidate_input_bound_on_pass",
            "eligibility_evidence_bound_on_pass",
            "cross_domain_lineage_bound_on_pass",
            "config_patch_manifest_bound_on_pass",
            "promotion_policy_input_evidence_complete_on_pass",
        }
    ]
    if structural_failures:
        raise ComparisonPromotionPolicyInputEvidenceError("self-verification checks failed")

    payload: dict[str, Any] = {
        "self_verification_schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": "PASS",
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "verified_output_digest": evidence.get("output_digest"),
        "verified_manifest_digest": manifest_digest,
        "verified_policy_input_binding_bundle_ref": policy_input_binding.bundle_dir.as_posix(),
        "verified_promotion_policy_input_evidence_status": evidence_status,
    }
    digest = compute_content_sha256(payload)
    payload["integrity"] = {"content_sha256": digest}
    return payload


def _finalize_evidence_with_manifest_digest(
    evidence: Mapping[str, Any], *, manifest_digest: str
) -> dict[str, Any]:
    body = dict(evidence)
    body["manifest_digest"] = manifest_digest
    body["output_digest"] = _compute_output_digest(body)
    body["artifact_id"] = body["output_digest"]
    body["integrity"] = {"content_sha256": compute_content_sha256(_integrity_body(body))}
    return body


def _staging_dir_for(output_dir: Path) -> Path:
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def verify_evidence_inputs(
    inputs: ComparisonPromotionPolicyInputEvidenceInputs,
) -> VerifiedPolicyInputBindingBundle:
    """Verify exactly one Step-4 policy input binding bundle."""
    return verify_policy_input_binding_bundle(inputs.policy_input_binding_bundle_dir)


def reverify_comparison_promotion_policy_input_evidence_v1(*, output_dir: Path | str) -> None:
    """Replay promotion policy input evidence bundle without producer or upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise ComparisonPromotionPolicyInputEvidenceError(
            f"promotion policy input evidence directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ComparisonPromotionPolicyInputEvidenceError(
            f"MANIFEST.sha256 verification failed: {msg}"
        )

    evidence_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(evidence_path, label=ARTIFACT_REL)
    evidence = read_manifest(evidence_path)
    _validate_evidence_integrity(evidence)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise ComparisonPromotionPolicyInputEvidenceError(
            "SELF_VERIFICATION overall_status must be PASS"
        )

    manifest_digest = _compute_output_manifest_digest(evidence)
    if evidence.get("manifest_digest") != manifest_digest:
        raise ComparisonPromotionPolicyInputEvidenceError("manifest_digest mismatch on replay")

    policy_input_binding = verify_policy_input_binding_bundle(
        Path(str(evidence["policy_input_binding_bundle_ref"]))
    )
    if evidence.get("policy_input_binding_digest") != policy_input_binding.artifact_digest:
        raise ComparisonPromotionPolicyInputEvidenceError(
            "policy_input_binding_digest mismatch on replay"
        )


def produce_comparison_promotion_policy_input_evidence_v1(
    *,
    inputs: ComparisonPromotionPolicyInputEvidenceInputs,
    output_dir: Path | str,
) -> ComparisonPromotionPolicyInputEvidenceResult:
    """Produce offline LEVEL_3 promotion policy input evidence."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        policy_input_binding_dir=inputs.policy_input_binding_bundle_dir,
        output_dir=final_dir,
    )

    policy_input_binding = verify_evidence_inputs(inputs)
    try:
        reverify_comparison_eligibility_promotion_policy_input_binding_v1(
            output_dir=policy_input_binding.bundle_dir
        )
    except ComparisonEligibilityPromotionPolicyInputBindingError as exc:
        raise ComparisonPromotionPolicyInputEvidenceError(str(exc)) from exc

    evidence_body = build_comparison_promotion_policy_input_evidence_v1(
        policy_input_binding=policy_input_binding,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ComparisonPromotionPolicyInputEvidenceError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        evidence_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(evidence_body)
        finalized = _finalize_evidence_with_manifest_digest(
            evidence_body, manifest_digest=manifest_digest
        )
        evidence_path.write_text(
            serialize_comparison_promotion_policy_input_evidence_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            evidence=finalized,
            policy_input_binding=policy_input_binding,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ComparisonPromotionPolicyInputEvidenceError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_comparison_promotion_policy_input_evidence_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ComparisonPromotionPolicyInputEvidenceError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return ComparisonPromotionPolicyInputEvidenceResult(
        output_dir=final_dir,
        comparison_definition_id=str(finalized.get("comparison_definition_id", "")),
        artifact_id=str(finalized["artifact_id"]),
        evidence_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        promotion_policy_input_evidence_status=str(
            finalized["promotion_policy_input_evidence_status"]
        ),
        candidate_identity_ref=str(finalized["candidate_identity_ref"]),
        config_patch_manifest_id=str(finalized["config_patch_manifest_id"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "AUTHORITY_LEVEL",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "EVIDENCE_LEVEL",
    "MANIFEST_FILENAME",
    "PROMOTION_POLICY_INPUT_EVIDENCE_AUTHORITY_INVARIANTS",
    "PRODUCER_VERSION",
    "SELF_VERIFICATION_REL",
    "ComparisonPromotionPolicyInputEvidenceError",
    "ComparisonPromotionPolicyInputEvidenceInputs",
    "ComparisonPromotionPolicyInputEvidenceResult",
    "VerifiedPolicyInputBindingBundle",
    "build_comparison_promotion_policy_input_evidence_v1",
    "build_self_verification_v1",
    "produce_comparison_promotion_policy_input_evidence_v1",
    "reverify_comparison_promotion_policy_input_evidence_v1",
    "serialize_comparison_promotion_policy_input_evidence_v1",
    "verify_evidence_inputs",
    "verify_policy_input_binding_bundle",
]
