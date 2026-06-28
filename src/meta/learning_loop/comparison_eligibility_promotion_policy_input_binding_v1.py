"""Offline LEVEL_3 eligibility promotion policy input binding from verified candidate input v1."""

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
from src.meta.learning_loop.comparison_promotion_candidate_input_v1 import (
    ARTIFACT_REL as UPSTREAM_ARTIFACT_REL,
    CONTRACT_NAME as UPSTREAM_CONTRACT_NAME,
    CONTRACT_VERSION as UPSTREAM_CONTRACT_VERSION,
    PRODUCER_VERSION as UPSTREAM_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as UPSTREAM_SELF_VERIFICATION_REL,
    ComparisonPromotionCandidateInputError,
    reverify_comparison_promotion_candidate_input_v1,
)
from src.meta.learning_loop.comparison_promotion_candidate_model_parameter_identity_binding_v1 import (
    verify_eligibility_evidence_bundle,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

CONTRACT_NAME = "comparison_eligibility_promotion_policy_input_binding_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "comparison_eligibility_promotion_policy_input_binding_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING_EVIDENCE_ONLY"
RECORD_KIND = "comparison_eligibility_promotion_policy_input_binding_record"
INPUT_RELATION = "BINDS_VERIFIED_CANDIDATE_INPUT_V1"
ARTIFACT_REL = "comparison_eligibility_promotion_policy_input_binding_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".comparison_eligibility_promotion_policy_input_binding_staging_"

OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"

_VALID_BINDING_STATUS = frozenset({"PASS", "FAIL", "INCOMPLETE", "NOT_EVALUABLE"})
_IDENTITY_BOUND = "BOUND"
_IDENTITY_NOT_BOUND = "NOT_BOUND"
_ELIGIBILITY_VERIFIED = "VERIFIED"
_ELIGIBILITY_NOT_VERIFIED = "NOT_VERIFIED"
_CANDIDATE_SELECTION_NOT_SELECTED = "NOT_SELECTED"
_WINNER_SELECTION_NOT_SELECTED = "NOT_SELECTED"
_CANDIDATE_ACCEPTANCE_NOT_ACCEPTED = "NOT_ACCEPTED"
_CONFIG_PATCH_ACCEPTANCE_NOT_ACCEPTED = "NOT_ACCEPTED"

POLICY_INPUT_BINDING_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "policy_input_binding_is_descriptive_only": True,
    "policy_input_binding_does_not_select": True,
    "policy_input_binding_does_not_choose_winner": True,
    "policy_input_binding_does_not_accept": True,
    "policy_input_binding_does_not_construct_promotion_candidate": True,
    "policy_input_binding_does_not_execute_operational_filter": True,
    "policy_input_binding_does_not_execute_policy": True,
    "policy_input_binding_does_not_recompute_eligibility": True,
    "policy_input_binding_does_not_create_configpatch": True,
    "policy_input_binding_does_not_modify_configpatch": True,
    "policy_input_binding_does_not_apply_configpatch": True,
    "policy_input_binding_does_not_modify_config": True,
    "policy_input_binding_does_not_authorize_promotion": True,
    "policy_input_binding_does_not_authorize_runtime": True,
    "policy_input_binding_does_not_authorize_live": True,
    "policy_input_binding_does_not_deploy": True,
    "policy_input_binding_does_not_activate": True,
    "policy_input_binding_does_not_create_order_intent": True,
    "policy_input_binding_does_not_modify_trading_logic": True,
    "evidence_does_not_authorize_promotion": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_comparison_eligibility_promotion_policy_input_binding": True,
    "evidence_does_not_authorize_promotion": True,
    "evidence_does_not_authorize_runtime": True,
    "policy_input_binding_does_not_select": True,
    "policy_input_binding_does_not_choose_winner": True,
    "policy_input_binding_does_not_accept_candidate": True,
    "policy_input_binding_does_not_accept_configpatch": True,
    "policy_input_binding_does_not_construct_promotion_candidate": True,
    "policy_input_binding_does_not_execute_operational_filter": True,
    "policy_input_binding_does_not_execute_policy": True,
    "policy_input_binding_does_not_recompute_eligibility": True,
    "policy_input_binding_does_not_create_configpatch": True,
    "policy_input_binding_does_not_modify_configpatch": True,
    "policy_input_binding_does_not_apply_configpatch": True,
    "policy_input_binding_does_not_modify_config": True,
    "policy_input_binding_does_not_authorize_promotion": True,
    "policy_input_binding_does_not_authorize_runtime": True,
    "policy_input_binding_does_not_authorize_live": True,
    "policy_input_binding_does_not_deploy": True,
    "policy_input_binding_does_not_activate": True,
    "policy_input_binding_does_not_create_order_intent": True,
    "policy_input_binding_does_not_modify_trading_logic": True,
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
    "promotion_policy_executed": False,
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
    "comparison_eligibility_promotion_policy_input_binding_self_verification_v1"
)


class ComparisonEligibilityPromotionPolicyInputBindingError(ValueError):
    """Fail-closed eligibility promotion policy input binding error."""


@dataclass(frozen=True)
class VerifiedCandidateInputBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    evidence_payload: dict[str, Any]


@dataclass(frozen=True)
class ResolvedEligibilityEvidence:
    bundle_dir: Path
    artifact_digest: str
    evidence_payload: dict[str, Any]


@dataclass(frozen=True)
class ComparisonEligibilityPromotionPolicyInputBindingInputs:
    candidate_input_bundle_dir: Path


@dataclass(frozen=True)
class ComparisonEligibilityPromotionPolicyInputBindingResult:
    output_dir: Path
    comparison_definition_id: str
    artifact_id: str
    evidence_path: Path
    self_verification_path: Path
    manifest_path: Path
    eligibility_policy_input_binding_status: str
    candidate_identity_ref: str
    config_patch_manifest_id: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            f"{label} must not be a symlink"
        )


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ComparisonEligibilityPromotionPolicyInputBindingError(
                f"forbidden index key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            f"{label} must be a regular file: {path}"
        )


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            f"{label} must be a directory: {bundle_dir}"
        )


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            f"output directory already exists: {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            "output directory must not be under /tmp"
        )


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, candidate_input_dir: Path, output_dir: Path) -> None:
    input_res = candidate_input_dir.resolve()
    output_res = output_dir.resolve()
    if output_res == input_res:
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            "output directory must not equal input path"
        )
    if _path_is_under(output_res, input_res):
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            "output directory must not be inside input path"
        )
    if input_res.is_dir() and _path_is_under(input_res, output_res):
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
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
        raise ComparisonEligibilityPromotionPolicyInputBindingError("capabilities must be a list")
    normalized: list[str] = []
    for item in capabilities:
        if not isinstance(item, str):
            raise ComparisonEligibilityPromotionPolicyInputBindingError(
                "capabilities entries must be strings"
            )
        if item in _FORBIDDEN_CAPABILITIES:
            raise ComparisonEligibilityPromotionPolicyInputBindingError(
                f"forbidden capability: {item}"
            )
        normalized.append(item)
    return sorted(normalized)


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if payload.get(key) is not expected:
            raise ComparisonEligibilityPromotionPolicyInputBindingError(
                f"{key} must be {expected!r}"
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
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            f"{label} must be a JSON object"
        )
    return payload


def verify_candidate_input_bundle(bundle_dir: Path | str) -> VerifiedCandidateInputBundle:
    """Fail-closed verification of exactly one Step-3 candidate input bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="candidate input bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            f"candidate input MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = path / UPSTREAM_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=UPSTREAM_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != UPSTREAM_CONTRACT_NAME:
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            "upstream candidate input contract_name mismatch"
        )
    if payload.get("contract_version") != UPSTREAM_CONTRACT_VERSION:
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            "upstream candidate input contract_version mismatch"
        )

    self_payload = _load_self_verification(
        path,
        rel=UPSTREAM_SELF_VERIFICATION_REL,
        label=UPSTREAM_SELF_VERIFICATION_REL,
    )
    if self_payload.get("overall_status") != "PASS":
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            "upstream candidate input SELF_VERIFICATION overall_status must be PASS"
        )

    try:
        reverify_comparison_promotion_candidate_input_v1(output_dir=path)
    except ComparisonPromotionCandidateInputError as exc:
        raise ComparisonEligibilityPromotionPolicyInputBindingError(str(exc)) from exc

    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            "candidate input integrity must be an object"
        )
    artifact_digest = integrity.get("content_sha256")
    if not isinstance(artifact_digest, str) or not is_valid_sha256_hex(artifact_digest):
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            "candidate input integrity.content_sha256 invalid"
        )

    return VerifiedCandidateInputBundle(
        bundle_dir=path.resolve(),
        contract_name=UPSTREAM_CONTRACT_NAME,
        contract_version=UPSTREAM_CONTRACT_VERSION,
        producer_version=UPSTREAM_PRODUCER_VERSION,
        artifact_ref=UPSTREAM_ARTIFACT_REL,
        artifact_digest=artifact_digest,
        manifest_digest=_manifest_file_digest(path),
        evidence_payload=dict(payload),
    )


def _resolve_eligibility_evidence(
    step3: Mapping[str, Any],
) -> tuple[ResolvedEligibilityEvidence | None, list[str]]:
    reason_codes: list[str] = []
    eligibility_ref = step3.get("eligibility_evidence_ref")
    eligibility_digest = step3.get("eligibility_evidence_digest")
    if not _non_empty_ref(eligibility_ref) or not is_valid_sha256_hex(
        str(eligibility_digest or "")
    ):
        reason_codes.append("ELIGIBILITY_EVIDENCE_NOT_BOUND")
        return None, reason_codes

    try:
        eligibility = verify_eligibility_evidence_bundle(Path(str(eligibility_ref)))
    except Exception:
        reason_codes.append("ELIGIBILITY_EVIDENCE_NOT_BOUND")
        return None, reason_codes

    if eligibility_digest != eligibility.artifact_digest:
        reason_codes.append("ELIGIBILITY_EVIDENCE_DIGEST_MISMATCH")

    return (
        ResolvedEligibilityEvidence(
            bundle_dir=eligibility.bundle_dir,
            artifact_digest=eligibility.artifact_digest,
            evidence_payload=eligibility.evidence_payload,
        ),
        reason_codes,
    )


def _evaluate_policy_input_binding(
    *,
    step3: Mapping[str, Any],
    eligibility: ResolvedEligibilityEvidence | None,
    resolution_reason_codes: list[str],
) -> tuple[str, str, str, str, str, str, str, list[str]]:
    reason_codes = list(resolution_reason_codes)

    upstream_status = str(step3.get("candidate_input_status", ""))
    if upstream_status == "NOT_EVALUABLE":
        return (
            "NOT_EVALUABLE",
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _ELIGIBILITY_NOT_VERIFIED,
            _IDENTITY_NOT_BOUND,
            _sorted_reason_codes(reason_codes + ["NOT_EVALUABLE_INSUFFICIENT_EVIDENCE"]),
        )
    if upstream_status == "INCOMPLETE":
        return (
            "INCOMPLETE",
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _ELIGIBILITY_NOT_VERIFIED,
            _IDENTITY_NOT_BOUND,
            _sorted_reason_codes(reason_codes + ["UPSTREAM_CANDIDATE_INPUT_INCOMPLETE"]),
        )
    if upstream_status == "FAIL":
        return (
            "FAIL",
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _ELIGIBILITY_NOT_VERIFIED,
            _IDENTITY_NOT_BOUND,
            _sorted_reason_codes(reason_codes + ["UPSTREAM_CANDIDATE_INPUT_FAIL"]),
        )

    if step3.get("candidate_selection_status") != _CANDIDATE_SELECTION_NOT_SELECTED:
        reason_codes.append("CANDIDATE_SELECTION_DETECTED")
    if step3.get("winner_selection_status") != _WINNER_SELECTION_NOT_SELECTED:
        reason_codes.append("WINNER_SELECTION_DETECTED")
    if step3.get("candidate_acceptance_status") != _CANDIDATE_ACCEPTANCE_NOT_ACCEPTED:
        reason_codes.append("CANDIDATE_ACCEPTANCE_DETECTED")
    if step3.get("config_patch_acceptance_status") != _CONFIG_PATCH_ACCEPTANCE_NOT_ACCEPTED:
        reason_codes.append("CONFIG_PATCH_ACCEPTANCE_DETECTED")
    if step3.get("promotion_candidate_constructed") is not False:
        reason_codes.append("PROMOTION_CANDIDATE_CONSTRUCTION_DETECTED")
    if step3.get("operational_filter_executed") is not False:
        reason_codes.append("OPERATIONAL_FILTER_DETECTED")
    if step3.get("promotion_policy_executed") is not False:
        reason_codes.append("PROMOTION_POLICY_DETECTED")
    if step3.get("configpatch_created") is not False:
        reason_codes.append("CONFIGPATCH_CREATION_DETECTED")
    if step3.get("configpatch_modified") is not False:
        reason_codes.append("CONFIGPATCH_MUTATION_DETECTED")
    if step3.get("configpatch_applied") is not False:
        reason_codes.append("CONFIGPATCH_APPLICATION_DETECTED")

    candidate_ref = str(step3.get("candidate_identity_ref", ""))
    candidate_digest = str(step3.get("candidate_identity_digest", ""))
    if not _non_empty_ref(candidate_ref) or not is_valid_sha256_hex(candidate_digest):
        reason_codes.append("CANDIDATE_IDENTITY_NOT_BOUND")
    if step3.get("candidate_identity_status") != _IDENTITY_BOUND:
        reason_codes.append("CANDIDATE_LINEAGE_MISMATCH")

    model_ref = str(step3.get("model_identity_ref", ""))
    model_digest = str(step3.get("model_identity_digest", ""))
    if not _non_empty_ref(model_ref) or not is_valid_sha256_hex(model_digest):
        reason_codes.append("MODEL_IDENTITY_NOT_BOUND")
    if step3.get("model_identity_status") != _IDENTITY_BOUND:
        reason_codes.append("MODEL_LINEAGE_MISMATCH")

    parameter_ref = str(step3.get("parameter_set_identity_ref", ""))
    parameter_digest = str(step3.get("parameter_set_identity_digest", ""))
    if not _non_empty_ref(parameter_ref) or not is_valid_sha256_hex(parameter_digest):
        reason_codes.append("PARAMETER_SET_IDENTITY_NOT_BOUND")
    if step3.get("parameter_set_identity_status") != _IDENTITY_BOUND:
        reason_codes.append("PARAMETER_SET_LINEAGE_MISMATCH")

    config_patch_id = str(step3.get("config_patch_manifest_id", ""))
    config_patch_digest = str(step3.get("config_patch_manifest_digest", ""))
    if not _non_empty_ref(config_patch_id) or not is_valid_sha256_hex(config_patch_digest):
        reason_codes.append("CONFIG_PATCH_MANIFEST_NOT_BOUND")
    if step3.get("config_patch_manifest_identity_status") != _IDENTITY_BOUND:
        reason_codes.append("CONFIG_PATCH_LINEAGE_MISMATCH")

    experiment_ref = str(step3.get("experiment_identity_ref", ""))
    experiment_digest = str(step3.get("experiment_identity_digest", ""))
    if not _non_empty_ref(experiment_ref) or not is_valid_sha256_hex(experiment_digest):
        reason_codes.append("EXPERIMENT_LINEAGE_MISMATCH")

    dataset_ref = str(step3.get("dataset_identity_ref", ""))
    dataset_digest = str(step3.get("dataset_identity_digest", ""))
    if not _non_empty_ref(dataset_ref) or not is_valid_sha256_hex(dataset_digest):
        reason_codes.append("DATASET_LINEAGE_MISMATCH")

    comparison_ref = str(step3.get("comparison_identity_ref", ""))
    comparison_digest = str(step3.get("comparison_identity_digest", ""))
    if not _non_empty_ref(comparison_ref) or not is_valid_sha256_hex(comparison_digest):
        reason_codes.append("COMPARISON_LINEAGE_MISMATCH")

    completion_ref = str(step3.get("comparison_completion_ref", ""))
    completion_digest = str(step3.get("comparison_completion_digest", ""))
    if not _non_empty_ref(completion_ref) or not is_valid_sha256_hex(completion_digest):
        reason_codes.append("COMPLETION_EVIDENCE_MISSING")

    research_ref = str(step3.get("research_validity_ref", ""))
    research_digest = str(step3.get("research_validity_digest", ""))
    if not _non_empty_ref(research_ref) or not is_valid_sha256_hex(research_digest):
        reason_codes.append("RESEARCH_VALIDITY_MISSING")

    promotion_ref = str(step3.get("promotion_input_binding_ref", ""))
    promotion_digest = str(step3.get("promotion_input_binding_digest", ""))
    if not _non_empty_ref(promotion_ref) or not is_valid_sha256_hex(promotion_digest):
        reason_codes.append("PROMOTION_INPUT_BINDING_MISSING")

    if step3.get("cross_domain_lineage_status") != _IDENTITY_BOUND:
        reason_codes.append("CROSS_DOMAIN_LINEAGE_NOT_BOUND")
    if step3.get("eligibility_evidence_status") != _ELIGIBILITY_VERIFIED:
        reason_codes.append("ELIGIBILITY_EVIDENCE_NOT_BOUND")

    if eligibility is None:
        reason_codes.append("ELIGIBILITY_EVIDENCE_NOT_BOUND")
    else:
        eligibility_payload = eligibility.evidence_payload
        if eligibility_payload.get("promotion_input_binding_ref") != promotion_ref:
            reason_codes.append("PROMOTION_INPUT_BINDING_MISMATCH")
        if eligibility_payload.get("promotion_input_binding_digest") != promotion_digest:
            reason_codes.append("PROMOTION_INPUT_BINDING_MISMATCH")
        if eligibility_payload.get("candidate_identity_ref") != candidate_ref:
            reason_codes.append("CANDIDATE_LINEAGE_MISMATCH")

    fail_codes = {
        "CANDIDATE_SELECTION_DETECTED",
        "WINNER_SELECTION_DETECTED",
        "CANDIDATE_ACCEPTANCE_DETECTED",
        "CONFIG_PATCH_ACCEPTANCE_DETECTED",
        "PROMOTION_CANDIDATE_CONSTRUCTION_DETECTED",
        "OPERATIONAL_FILTER_DETECTED",
        "PROMOTION_POLICY_DETECTED",
        "CONFIGPATCH_CREATION_DETECTED",
        "CONFIGPATCH_MUTATION_DETECTED",
        "CONFIGPATCH_APPLICATION_DETECTED",
        "CANDIDATE_IDENTITY_NOT_BOUND",
        "CANDIDATE_LINEAGE_MISMATCH",
        "MODEL_IDENTITY_NOT_BOUND",
        "MODEL_LINEAGE_MISMATCH",
        "PARAMETER_SET_IDENTITY_NOT_BOUND",
        "PARAMETER_SET_LINEAGE_MISMATCH",
        "CONFIG_PATCH_MANIFEST_NOT_BOUND",
        "CONFIG_PATCH_LINEAGE_MISMATCH",
        "EXPERIMENT_LINEAGE_MISMATCH",
        "DATASET_LINEAGE_MISMATCH",
        "COMPARISON_LINEAGE_MISMATCH",
        "COMPLETION_EVIDENCE_MISSING",
        "RESEARCH_VALIDITY_MISSING",
        "PROMOTION_INPUT_BINDING_MISSING",
        "PROMOTION_INPUT_BINDING_MISMATCH",
        "CROSS_DOMAIN_LINEAGE_NOT_BOUND",
        "ELIGIBILITY_EVIDENCE_NOT_BOUND",
        "ELIGIBILITY_EVIDENCE_DIGEST_MISMATCH",
    }

    binding_status = "PASS"
    candidate_input_bound = _IDENTITY_BOUND
    candidate_bound = _IDENTITY_BOUND
    eligibility_bound = _ELIGIBILITY_VERIFIED
    cross_domain_bound = _IDENTITY_BOUND
    config_patch_bound = _IDENTITY_BOUND
    policy_input_bound = _IDENTITY_BOUND

    if any(code in reason_codes for code in fail_codes):
        binding_status = "FAIL"
        if (
            "CANDIDATE_IDENTITY_NOT_BOUND" in reason_codes
            or "CANDIDATE_LINEAGE_MISMATCH" in reason_codes
        ):
            candidate_bound = _IDENTITY_NOT_BOUND
        if "MODEL_IDENTITY_NOT_BOUND" in reason_codes or "MODEL_LINEAGE_MISMATCH" in reason_codes:
            pass
        if (
            "CONFIG_PATCH_MANIFEST_NOT_BOUND" in reason_codes
            or "CONFIG_PATCH_LINEAGE_MISMATCH" in reason_codes
        ):
            config_patch_bound = _IDENTITY_NOT_BOUND
        if (
            "ELIGIBILITY_EVIDENCE_NOT_BOUND" in reason_codes
            or "ELIGIBILITY_EVIDENCE_DIGEST_MISMATCH" in reason_codes
        ):
            eligibility_bound = _ELIGIBILITY_NOT_VERIFIED
        if "CROSS_DOMAIN_LINEAGE_NOT_BOUND" in reason_codes:
            cross_domain_bound = _IDENTITY_NOT_BOUND
        if binding_status == "FAIL":
            policy_input_bound = _IDENTITY_NOT_BOUND
            candidate_input_bound = _IDENTITY_NOT_BOUND

    if binding_status == "PASS":
        reason_codes.extend(
            [
                "ELIGIBILITY_POLICY_INPUT_BOUND",
                "CANDIDATE_INPUT_BOUND",
                "ELIGIBILITY_EVIDENCE_BOUND",
                "CROSS_DOMAIN_LINEAGE_BOUND",
                "CONFIG_PATCH_MANIFEST_BOUND",
                "COMPARISON_ELIGIBILITY_PROMOTION_POLICY_INPUT_BINDING_COMPLETE",
            ]
        )

    return (
        binding_status,
        candidate_input_bound,
        candidate_bound,
        eligibility_bound,
        cross_domain_bound,
        config_patch_bound,
        policy_input_bound,
        _sorted_reason_codes(reason_codes),
    )


def _input_artifact_ref_mapping(*, bundle: VerifiedCandidateInputBundle) -> dict[str, Any]:
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


def build_comparison_eligibility_promotion_policy_input_binding_v1(
    *,
    candidate_input: VerifiedCandidateInputBundle,
) -> dict[str, Any]:
    step3 = candidate_input.evidence_payload
    eligibility, resolution_codes = _resolve_eligibility_evidence(step3)
    (
        binding_status,
        candidate_input_bound_status,
        candidate_bound_status,
        eligibility_bound_status,
        cross_domain_bound_status,
        config_patch_bound_status,
        policy_input_bound_status,
        reason_codes,
    ) = _evaluate_policy_input_binding(
        step3=step3,
        eligibility=eligibility,
        resolution_reason_codes=resolution_codes,
    )

    input_refs = [_input_artifact_ref_mapping(bundle=candidate_input)]
    parent_artifact_refs = list(step3.get("parent_artifact_refs", []))
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
        "is_comparison_eligibility_promotion_policy_input_binding": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "policy_input_binding_does_not_select": True,
        "policy_input_binding_does_not_choose_winner": True,
        "policy_input_binding_does_not_accept_candidate": True,
        "policy_input_binding_does_not_accept_configpatch": True,
        "policy_input_binding_does_not_construct_promotion_candidate": True,
        "policy_input_binding_does_not_execute_operational_filter": True,
        "policy_input_binding_does_not_execute_policy": True,
        "policy_input_binding_does_not_recompute_eligibility": True,
        "policy_input_binding_does_not_create_configpatch": True,
        "policy_input_binding_does_not_modify_configpatch": True,
        "policy_input_binding_does_not_apply_configpatch": True,
        "policy_input_binding_does_not_modify_config": True,
        "policy_input_binding_does_not_authorize_promotion": True,
        "policy_input_binding_does_not_authorize_runtime": True,
        "policy_input_binding_does_not_authorize_live": True,
        "policy_input_binding_does_not_deploy": True,
        "policy_input_binding_does_not_activate": True,
        "policy_input_binding_does_not_create_order_intent": True,
        "policy_input_binding_does_not_modify_trading_logic": True,
        "policy_input_binding_authority_invariants": dict(
            POLICY_INPUT_BINDING_AUTHORITY_INVARIANTS
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
        "promotion_policy_executed": False,
        "promotion_consumers_changed": False,
        "promotion_authorized": False,
        "runtime_authorized": False,
        "live_authorized": False,
        "orders_allowed": False,
        "scheduler_runtime_allowed": False,
        "candidate_input_bundle_ref": candidate_input.bundle_dir.as_posix(),
        "candidate_input_artifact_ref": candidate_input.artifact_ref,
        "candidate_input_digest": candidate_input.artifact_digest,
        "candidate_input_manifest_digest": candidate_input.manifest_digest,
        "upstream_contract_name": candidate_input.contract_name,
        "upstream_contract_version": candidate_input.contract_version,
        "upstream_producer_version": candidate_input.producer_version,
        "upstream_candidate_input_status": str(step3.get("candidate_input_status", "")),
        "eligibility_policy_input_binding_status": binding_status,
        "eligibility_policy_input_binding_reason_codes": reason_codes,
        "candidate_input_bound_status": candidate_input_bound_status,
        "candidate_identity_bound_status": candidate_bound_status,
        "eligibility_evidence_bound_status": eligibility_bound_status,
        "cross_domain_lineage_bound_status": cross_domain_bound_status,
        "config_patch_manifest_bound_status": config_patch_bound_status,
        "eligibility_policy_input_bound_status": policy_input_bound_status,
        "candidate_selection_status": _CANDIDATE_SELECTION_NOT_SELECTED,
        "winner_selection_status": _WINNER_SELECTION_NOT_SELECTED,
        "candidate_acceptance_status": _CANDIDATE_ACCEPTANCE_NOT_ACCEPTED,
        "config_patch_acceptance_status": _CONFIG_PATCH_ACCEPTANCE_NOT_ACCEPTED,
        "candidate_identity_ref": str(step3.get("candidate_identity_ref", "")),
        "candidate_identity_digest": str(step3.get("candidate_identity_digest", "")),
        "experiment_identity_ref": str(step3.get("experiment_identity_ref", "")),
        "experiment_identity_digest": str(step3.get("experiment_identity_digest", "")),
        "experiment_identity_id": str(step3.get("experiment_identity_id", "")),
        "dataset_identity_ref": str(step3.get("dataset_identity_ref", "")),
        "dataset_identity_digest": str(step3.get("dataset_identity_digest", "")),
        "comparison_identity_ref": str(step3.get("comparison_identity_ref", "")),
        "comparison_identity_digest": str(step3.get("comparison_identity_digest", "")),
        "comparison_definition_id": str(step3.get("comparison_definition_id", "")),
        "comparison_completion_ref": str(step3.get("comparison_completion_ref", "")),
        "comparison_completion_digest": str(step3.get("comparison_completion_digest", "")),
        "research_validity_ref": str(step3.get("research_validity_ref", "")),
        "research_validity_digest": str(step3.get("research_validity_digest", "")),
        "promotion_input_binding_ref": str(step3.get("promotion_input_binding_ref", "")),
        "promotion_input_binding_digest": str(step3.get("promotion_input_binding_digest", "")),
        "config_patch_manifest_ref": str(step3.get("config_patch_manifest_ref", "")),
        "config_patch_manifest_digest": str(step3.get("config_patch_manifest_digest", "")),
        "config_patch_manifest_id": str(step3.get("config_patch_manifest_id", "")),
        "config_patch_contract_name": str(step3.get("config_patch_contract_name", "")),
        "config_patch_contract_version": str(step3.get("config_patch_contract_version", "")),
        "cross_domain_lineage_binding_bundle_ref": str(
            step3.get("cross_domain_lineage_binding_bundle_ref", "")
        ),
        "cross_domain_lineage_binding_digest": str(
            step3.get("cross_domain_lineage_binding_digest", "")
        ),
        "input_artifact_refs": input_refs,
        "parent_artifact_refs": parent_artifact_refs,
        "input_digest": "",
        "output_digest": "",
        "manifest_digest": "",
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
    ):
        value = step3.get(field)
        if value is not None:
            payload[field] = str(value)

    if eligibility is not None:
        payload["eligibility_evidence_ref"] = eligibility.bundle_dir.as_posix()
        payload["eligibility_evidence_digest"] = eligibility.artifact_digest

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    _validate_capabilities(payload["capabilities"])

    payload["input_digest"] = compute_content_sha256({"input_artifact_refs": input_refs})
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    return payload


def serialize_comparison_eligibility_promotion_policy_input_binding_v1(
    evidence: Mapping[str, Any],
) -> str:
    _reject_forbidden_index_keys(evidence)
    _validate_non_authorizing_flags(evidence)
    _validate_capabilities(evidence.get("capabilities"))
    binding_status = evidence.get("eligibility_policy_input_binding_status")
    if binding_status not in _VALID_BINDING_STATUS:
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            f"eligibility_policy_input_binding_status must be one of {sorted(_VALID_BINDING_STATUS)}"
        )
    reason_codes = evidence.get("eligibility_policy_input_binding_reason_codes")
    if isinstance(reason_codes, list) and reason_codes != sorted(reason_codes):
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            "eligibility_policy_input_binding_reason_codes must be sorted deterministically"
        )
    return deterministic_json_dumps(evidence)


def _evidence_bytes_for_manifest_digest(evidence: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in evidence.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_comparison_eligibility_promotion_policy_input_binding_v1(body).encode("utf-8")


def _compute_output_manifest_digest(evidence: Mapping[str, Any]) -> str:
    return hashlib.sha256(_evidence_bytes_for_manifest_digest(evidence)).hexdigest()


def _validate_evidence_integrity(evidence: Mapping[str, Any]) -> None:
    if evidence.get("contract_name") != CONTRACT_NAME:
        raise ComparisonEligibilityPromotionPolicyInputBindingError("contract_name mismatch")
    if evidence.get("contract_version") != CONTRACT_VERSION:
        raise ComparisonEligibilityPromotionPolicyInputBindingError("contract_version mismatch")
    integrity = evidence.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ComparisonEligibilityPromotionPolicyInputBindingError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(evidence))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            "integrity.content_sha256 mismatch"
        )
    output_digest = evidence.get("output_digest")
    if output_digest != _compute_output_digest(evidence):
        raise ComparisonEligibilityPromotionPolicyInputBindingError("output_digest mismatch")
    if evidence.get("artifact_id") != output_digest:
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            "artifact_id must equal output_digest"
        )


def build_self_verification_v1(
    *,
    evidence: Mapping[str, Any],
    candidate_input: VerifiedCandidateInputBundle,
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_one_direct_input", "status": "PASS"},
        {"check_id": "upstream_contract_and_version", "status": "PASS"},
        {"check_id": "candidate_input_manifest_verified", "status": "PASS"},
        {"check_id": "candidate_input_self_verification_pass", "status": "PASS"},
        {"check_id": "candidate_input_bound_on_pass", "status": "PASS"},
        {"check_id": "eligibility_evidence_bound_on_pass", "status": "PASS"},
        {"check_id": "cross_domain_lineage_bound_on_pass", "status": "PASS"},
        {"check_id": "config_patch_manifest_bound_on_pass", "status": "PASS"},
        {"check_id": "policy_input_bound_on_pass", "status": "PASS"},
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

    binding_status = evidence.get("eligibility_policy_input_binding_status")
    if binding_status == "PASS":
        for check_id, field in (
            ("candidate_input_bound_on_pass", "candidate_input_bound_status"),
            ("eligibility_evidence_bound_on_pass", "eligibility_evidence_bound_status"),
            ("cross_domain_lineage_bound_on_pass", "cross_domain_lineage_bound_status"),
            ("config_patch_manifest_bound_on_pass", "config_patch_manifest_bound_status"),
            ("policy_input_bound_on_pass", "eligibility_policy_input_bound_status"),
        ):
            expected = (
                _ELIGIBILITY_VERIFIED
                if field == "eligibility_evidence_bound_status"
                else _IDENTITY_BOUND
            )
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
            "candidate_input_bound_on_pass",
            "eligibility_evidence_bound_on_pass",
            "cross_domain_lineage_bound_on_pass",
            "config_patch_manifest_bound_on_pass",
            "policy_input_bound_on_pass",
        }
    ]
    if structural_failures:
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            "self-verification checks failed"
        )

    payload: dict[str, Any] = {
        "self_verification_schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": "PASS",
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "verified_output_digest": evidence.get("output_digest"),
        "verified_manifest_digest": manifest_digest,
        "verified_candidate_input_bundle_ref": candidate_input.bundle_dir.as_posix(),
        "verified_eligibility_policy_input_binding_status": binding_status,
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


def verify_binding_inputs(
    inputs: ComparisonEligibilityPromotionPolicyInputBindingInputs,
) -> VerifiedCandidateInputBundle:
    """Verify exactly one Step-3 candidate input bundle."""
    return verify_candidate_input_bundle(inputs.candidate_input_bundle_dir)


def reverify_comparison_eligibility_promotion_policy_input_binding_v1(
    *, output_dir: Path | str
) -> None:
    """Replay policy input binding bundle without producer or upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            f"policy input binding directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
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
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            "SELF_VERIFICATION overall_status must be PASS"
        )

    manifest_digest = _compute_output_manifest_digest(evidence)
    if evidence.get("manifest_digest") != manifest_digest:
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            "manifest_digest mismatch on replay"
        )

    candidate_input = verify_candidate_input_bundle(
        Path(str(evidence["candidate_input_bundle_ref"]))
    )
    if evidence.get("candidate_input_digest") != candidate_input.artifact_digest:
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            "candidate_input_digest mismatch on replay"
        )


def produce_comparison_eligibility_promotion_policy_input_binding_v1(
    *,
    inputs: ComparisonEligibilityPromotionPolicyInputBindingInputs,
    output_dir: Path | str,
) -> ComparisonEligibilityPromotionPolicyInputBindingResult:
    """Produce offline LEVEL_3 eligibility promotion policy input binding evidence."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        candidate_input_dir=inputs.candidate_input_bundle_dir,
        output_dir=final_dir,
    )

    candidate_input = verify_binding_inputs(inputs)
    try:
        reverify_comparison_promotion_candidate_input_v1(output_dir=candidate_input.bundle_dir)
    except ComparisonPromotionCandidateInputError as exc:
        raise ComparisonEligibilityPromotionPolicyInputBindingError(str(exc)) from exc

    evidence_body = build_comparison_eligibility_promotion_policy_input_binding_v1(
        candidate_input=candidate_input,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ComparisonEligibilityPromotionPolicyInputBindingError(
            f"staging directory collision: {staging}"
        )

    try:
        staging.mkdir(parents=True, exist_ok=False)
        evidence_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(evidence_body)
        finalized = _finalize_evidence_with_manifest_digest(
            evidence_body, manifest_digest=manifest_digest
        )
        evidence_path.write_text(
            serialize_comparison_eligibility_promotion_policy_input_binding_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            evidence=finalized,
            candidate_input=candidate_input,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ComparisonEligibilityPromotionPolicyInputBindingError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_comparison_eligibility_promotion_policy_input_binding_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ComparisonEligibilityPromotionPolicyInputBindingError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return ComparisonEligibilityPromotionPolicyInputBindingResult(
        output_dir=final_dir,
        comparison_definition_id=str(finalized.get("comparison_definition_id", "")),
        artifact_id=str(finalized["artifact_id"]),
        evidence_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        eligibility_policy_input_binding_status=str(
            finalized["eligibility_policy_input_binding_status"]
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
    "POLICY_INPUT_BINDING_AUTHORITY_INVARIANTS",
    "PRODUCER_VERSION",
    "SELF_VERIFICATION_REL",
    "ComparisonEligibilityPromotionPolicyInputBindingError",
    "ComparisonEligibilityPromotionPolicyInputBindingInputs",
    "ComparisonEligibilityPromotionPolicyInputBindingResult",
    "ResolvedEligibilityEvidence",
    "VerifiedCandidateInputBundle",
    "build_comparison_eligibility_promotion_policy_input_binding_v1",
    "build_self_verification_v1",
    "produce_comparison_eligibility_promotion_policy_input_binding_v1",
    "reverify_comparison_eligibility_promotion_policy_input_binding_v1",
    "serialize_comparison_eligibility_promotion_policy_input_binding_v1",
    "verify_binding_inputs",
    "verify_candidate_input_bundle",
]
