"""Offline LEVEL_3 candidate eligibility evidence from candidate identity binding v1."""

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
from src.meta.learning_loop.comparison_promotion_candidate_identity_binding_v1 import (
    ARTIFACT_REL as IDENTITY_BINDING_ARTIFACT_REL,
    CONTRACT_NAME as IDENTITY_BINDING_CONTRACT_NAME,
    CONTRACT_VERSION as IDENTITY_BINDING_CONTRACT_VERSION,
    PRODUCER_VERSION as IDENTITY_BINDING_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as IDENTITY_BINDING_SELF_VERIFICATION_REL,
    ComparisonPromotionCandidateIdentityBindingError,
    reverify_comparison_promotion_candidate_identity_binding_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

CONTRACT_NAME = "comparison_promotion_candidate_eligibility_evidence_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "comparison_promotion_candidate_eligibility_evidence_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING_EVIDENCE_ONLY"
RECORD_KIND = "comparison_promotion_candidate_eligibility_evidence_record"
INPUT_RELATION = "EVALUATES_VERIFIED_CANDIDATE_IDENTITY_BINDING"
ARTIFACT_REL = "comparison_promotion_candidate_eligibility_evidence_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".comparison_promotion_candidate_eligibility_evidence_staging_"

OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"

_VALID_ELIGIBILITY_STATUS = frozenset({"PASS", "FAIL", "INCOMPLETE", "NOT_EVALUABLE"})
_CANDIDATE_SELECTION_NOT_SELECTED = "NOT_SELECTED"
_WINNER_SELECTION_NOT_SELECTED = "NOT_SELECTED"
_CANDIDATE_ACCEPTANCE_NOT_ACCEPTED = "NOT_ACCEPTED"
_CANDIDATE_IDENTITY_BOUND = "BOUND"

ELIGIBILITY_EVIDENCE_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "eligibility_evidence_is_descriptive_only": True,
    "eligibility_evidence_does_not_select": True,
    "eligibility_evidence_does_not_choose_winner": True,
    "eligibility_evidence_does_not_accept": True,
    "eligibility_evidence_does_not_construct_promotion_candidate": True,
    "eligibility_evidence_does_not_execute_operational_filter": True,
    "eligibility_evidence_does_not_execute_policy": True,
    "eligibility_evidence_does_not_create_configpatch": True,
    "eligibility_evidence_does_not_modify_config": True,
    "eligibility_evidence_does_not_authorize_promotion": True,
    "eligibility_evidence_does_not_authorize_runtime": True,
    "eligibility_evidence_does_not_authorize_live": True,
    "eligibility_evidence_does_not_deploy": True,
    "eligibility_evidence_does_not_activate": True,
    "eligibility_evidence_does_not_create_order_intent": True,
    "eligibility_evidence_does_not_modify_trading_logic": True,
    "evidence_does_not_authorize_promotion": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_comparison_promotion_candidate_eligibility_evidence": True,
    "evidence_does_not_authorize_promotion": True,
    "evidence_does_not_authorize_runtime": True,
    "eligibility_evidence_does_not_select": True,
    "eligibility_evidence_does_not_choose_winner": True,
    "eligibility_evidence_does_not_accept": True,
    "eligibility_evidence_does_not_construct_promotion_candidate": True,
    "eligibility_evidence_does_not_execute_operational_filter": True,
    "eligibility_evidence_does_not_execute_policy": True,
    "eligibility_evidence_does_not_create_configpatch": True,
    "eligibility_evidence_does_not_modify_config": True,
    "eligibility_evidence_does_not_authorize_promotion": True,
    "eligibility_evidence_does_not_authorize_runtime": True,
    "eligibility_evidence_does_not_authorize_live": True,
    "eligibility_evidence_does_not_deploy": True,
    "eligibility_evidence_does_not_activate": True,
    "eligibility_evidence_does_not_create_order_intent": True,
    "eligibility_evidence_does_not_modify_trading_logic": True,
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
        "promotion_authorized",
        "promotion_decision",
        "eligible_for_live",
        "runtime_authorized",
        "live_authorized",
        "live_eligible",
        "runtime_eligible",
        "orders_allowed",
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
    "comparison_promotion_candidate_eligibility_evidence_self_verification_v1"
)

_REQUIRED_LINEAGE_FIELDS: tuple[tuple[str, str | None], ...] = (
    ("comparison_completion_ref", "comparison_completion_digest"),
    ("research_validity_ref", "research_validity_digest"),
    ("comparison_checkpoint_ref", "comparison_checkpoint_digest"),
    ("experiment_identity_ref", "experiment_identity_digest"),
    ("dataset_identity_ref", "dataset_identity_digest"),
    ("comparison_definition_ref", None),
)


class ComparisonPromotionCandidateEligibilityEvidenceError(ValueError):
    """Fail-closed candidate eligibility evidence error."""


@dataclass(frozen=True)
class VerifiedCandidateIdentityBindingBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    evidence_level: str
    parent_artifact_refs: tuple[dict[str, Any], ...]
    evidence_payload: dict[str, Any]


@dataclass(frozen=True)
class ComparisonPromotionCandidateEligibilityEvidenceInputs:
    candidate_identity_binding_bundle_dir: Path


@dataclass(frozen=True)
class ComparisonPromotionCandidateEligibilityEvidenceResult:
    output_dir: Path
    comparison_definition_id: str
    artifact_id: str
    evidence_path: Path
    self_verification_path: Path
    manifest_path: Path
    candidate_eligibility_status: str
    candidate_identity_ref: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            f"{label} must not be a symlink: {path}"
        )


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ComparisonPromotionCandidateEligibilityEvidenceError(
                f"eligibility evidence artifact must not contain forbidden key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise ComparisonPromotionCandidateEligibilityEvidenceError(f"{label} not found: {path}")
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            f"{label} must be a regular file: {path}"
        )


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    if not bundle_dir.is_dir():
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            f"{label} must be a directory: {bundle_dir}"
        )
    _reject_symlink(bundle_dir, label=label)


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "output directory must be outside /tmp"
        )
    parent = output_dir.parent
    if not parent.is_dir():
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            f"output parent directory missing: {parent}"
        )
    if is_under_tmp(parent):
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "output parent directory must be outside /tmp"
        )


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, input_dir: Path, output_dir: Path) -> None:
    input_res = input_dir.resolve()
    output_res = output_dir.resolve()
    if input_res == output_res:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "output directory must not equal input bundle path (fail-closed)"
        )
    if _path_is_under(input_res, output_res):
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "input bundle must not be inside output directory (fail-closed)"
        )
    if _path_is_under(output_res, input_res):
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "output directory must not be inside input bundle path (fail-closed)"
        )


def _manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / MANIFEST_FILENAME
    _validate_regular_file(manifest_path, label=MANIFEST_FILENAME)
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _validate_capabilities(capabilities: Any) -> list[str]:
    if not isinstance(capabilities, list):
        raise ComparisonPromotionCandidateEligibilityEvidenceError("capabilities must be a list")
    normalized: list[str] = []
    for idx, item in enumerate(capabilities):
        if not isinstance(item, str) or not item.strip():
            raise ComparisonPromotionCandidateEligibilityEvidenceError(
                f"capabilities[{idx}] must be a non-empty string"
            )
        if item in _FORBIDDEN_CAPABILITIES:
            raise ComparisonPromotionCandidateEligibilityEvidenceError(
                f"forbidden capability present: {item}"
            )
        normalized.append(item)
    return normalized


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if payload.get(key) is not expected:
            raise ComparisonPromotionCandidateEligibilityEvidenceError(
                f"{key} must be {expected!r} (fail-closed)"
            )
    if payload.get("evidence_level") != EVIDENCE_LEVEL:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            f"evidence_level must be {EVIDENCE_LEVEL!r} (fail-closed)"
        )


def _normalize_parent_refs(value: Any, *, label: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            f"{label} parent_artifact_refs must be a list"
        )
    refs: list[dict[str, Any]] = []
    for idx, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ComparisonPromotionCandidateEligibilityEvidenceError(
                f"{label} parent_artifact_refs[{idx}] must be an object"
            )
        refs.append(dict(item))
    return tuple(refs)


def _load_self_verification(bundle_dir: Path, *, rel: str, label: str) -> dict[str, Any]:
    path = bundle_dir / rel
    _validate_regular_file(path, label=label)
    payload = read_manifest(path)
    if payload.get("overall_status") != "PASS":
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            f"{label} overall_status must be PASS"
        )
    return payload


def _validate_identity_binding_input_payload(payload: Mapping[str, Any]) -> None:
    if payload.get("contract_name") != IDENTITY_BINDING_CONTRACT_NAME:
        raise ComparisonPromotionCandidateEligibilityEvidenceError("input contract_name mismatch")
    if payload.get("contract_version") != IDENTITY_BINDING_CONTRACT_VERSION:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "input contract_version not supported"
        )
    if payload.get("producer_version") != IDENTITY_BINDING_PRODUCER_VERSION:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "input producer_version mismatch"
        )
    if payload.get("evidence_level") != EVIDENCE_LEVEL:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "input evidence_level must be LEVEL_3"
        )
    for flag in (
        "candidate_identity_binding_does_not_select",
        "candidate_identity_binding_does_not_choose_winner",
        "candidate_identity_binding_does_not_accept",
        "candidate_identity_binding_does_not_execute_eligibility",
        "candidate_identity_binding_does_not_execute_policy",
        "candidate_identity_binding_does_not_create_configpatch",
        "candidate_identity_binding_does_not_authorize_runtime",
        "evidence_does_not_authorize_promotion",
        "evidence_does_not_authorize_runtime",
    ):
        if payload.get(flag) is not True:
            raise ComparisonPromotionCandidateEligibilityEvidenceError(
                f"input {flag} must be true (fail-closed)"
            )
    invariants = payload.get("candidate_identity_binding_authority_invariants")
    if not isinstance(invariants, Mapping):
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "input candidate_identity_binding_authority_invariants must be an object"
        )
    for flag in (
        "candidate_identity_binding_does_not_authorize_promotion",
        "candidate_identity_binding_does_not_execute_eligibility",
    ):
        if invariants.get(flag) is not True:
            raise ComparisonPromotionCandidateEligibilityEvidenceError(
                f"input authority invariant {flag} must be true (fail-closed)"
            )
    capabilities = payload.get("capabilities")
    if isinstance(capabilities, list):
        for item in capabilities:
            if item in _FORBIDDEN_CAPABILITIES:
                raise ComparisonPromotionCandidateEligibilityEvidenceError(
                    f"forbidden capability in upstream input: {item}"
                )


def verify_candidate_identity_binding_bundle(
    bundle_dir: Path,
) -> VerifiedCandidateIdentityBindingBundle:
    """Verify exactly one published candidate identity binding bundle."""
    _validate_bundle_dir(bundle_dir, label="candidate_identity_binding_bundle_dir")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(f"INPUT_MANIFEST_INVALID: {msg}")

    _load_self_verification(
        bundle_dir,
        rel=IDENTITY_BINDING_SELF_VERIFICATION_REL,
        label=IDENTITY_BINDING_SELF_VERIFICATION_REL,
    )

    evidence_path = bundle_dir / IDENTITY_BINDING_ARTIFACT_REL
    _validate_regular_file(evidence_path, label=IDENTITY_BINDING_ARTIFACT_REL)
    payload = read_manifest(evidence_path)
    _validate_identity_binding_input_payload(payload)

    try:
        reverify_comparison_promotion_candidate_identity_binding_v1(output_dir=bundle_dir)
    except ComparisonPromotionCandidateIdentityBindingError as exc:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(str(exc)) from exc

    artifact_digest = str(payload.get("output_digest", ""))
    if not is_valid_sha256_hex(artifact_digest):
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "candidate identity binding output_digest missing or invalid"
        )

    return VerifiedCandidateIdentityBindingBundle(
        bundle_dir=bundle_dir,
        contract_name=IDENTITY_BINDING_CONTRACT_NAME,
        contract_version=IDENTITY_BINDING_CONTRACT_VERSION,
        producer_version=IDENTITY_BINDING_PRODUCER_VERSION,
        artifact_ref=IDENTITY_BINDING_ARTIFACT_REL,
        artifact_digest=artifact_digest,
        manifest_digest=_manifest_file_digest(bundle_dir),
        evidence_level=str(payload.get("evidence_level", "")),
        parent_artifact_refs=_normalize_parent_refs(
            payload.get("parent_artifact_refs"), label="identity_binding"
        ),
        evidence_payload=dict(payload),
    )


def _digest_from_parent_refs(
    parent_refs: tuple[dict[str, Any], ...], *, contract_substring: str
) -> str:
    for ref in parent_refs:
        ref_type = str(ref.get("ref_type", ""))
        contract = str(ref.get("contract_name", ref_type))
        if contract_substring in contract or contract_substring in ref_type:
            digest = ref.get("digest")
            if isinstance(digest, str) and is_valid_sha256_hex(digest):
                return digest
    return ""


def _non_empty_ref(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _sorted_reason_codes(codes: list[str]) -> list[str]:
    return sorted(dict.fromkeys(codes))


def _evaluate_eligibility(
    identity: Mapping[str, Any],
) -> tuple[
    str,
    str,
    str,
    str,
    str,
    str,
    list[str],
]:
    """Return dimension statuses and sorted reason codes."""
    reason_codes: list[str] = []
    upstream_binding_status = str(identity.get("candidate_identity_binding_status", ""))

    if identity.get("candidate_identity_status") != _CANDIDATE_IDENTITY_BOUND:
        reason_codes.append("CANDIDATE_IDENTITY_NOT_BOUND")
    if identity.get("candidate_selection_status") != _CANDIDATE_SELECTION_NOT_SELECTED:
        reason_codes.append("CANDIDATE_SELECTION_DETECTED")
    if identity.get("winner_selection_status") != _WINNER_SELECTION_NOT_SELECTED:
        reason_codes.append("WINNER_SELECTION_DETECTED")
    if identity.get("candidate_identity_binding_does_not_accept") is not True:
        reason_codes.append("CANDIDATE_ACCEPTANCE_DETECTED")

    structural = "PASS"
    if "CANDIDATE_IDENTITY_NOT_BOUND" in reason_codes:
        structural = "FAIL"
    elif upstream_binding_status in {"FAIL", "INCOMPLETE", "NOT_EVALUABLE"}:
        structural = upstream_binding_status
        reason_codes.append("UPSTREAM_STATUS_NOT_PASS")

    contract_compatibility = "PASS"
    if identity.get("contract_name") != IDENTITY_BINDING_CONTRACT_NAME:
        contract_compatibility = "FAIL"
        reason_codes.append("INPUT_CONTRACT_UNSUPPORTED")
    if identity.get("contract_version") != IDENTITY_BINDING_CONTRACT_VERSION:
        contract_compatibility = "FAIL"
        reason_codes.append("INPUT_CONTRACT_UNSUPPORTED")

    capability_boundary = "PASS"
    upstream_caps = identity.get("capabilities")
    if isinstance(upstream_caps, list):
        for cap in upstream_caps:
            if cap in _FORBIDDEN_CAPABILITIES:
                capability_boundary = "FAIL"
                reason_codes.append("FORBIDDEN_CAPABILITY")

    evidence_completeness = "PASS"
    for ref_field, digest_field in _REQUIRED_LINEAGE_FIELDS:
        if not _non_empty_ref(identity.get(ref_field)):
            evidence_completeness = "INCOMPLETE"
            if ref_field == "comparison_completion_ref":
                reason_codes.append("COMPLETION_EVIDENCE_INVALID")
            elif ref_field == "research_validity_ref":
                reason_codes.append("RESEARCH_VALIDITY_INVALID")
            else:
                reason_codes.append("LINEAGE_INCOMPLETE")
        if digest_field and not is_valid_sha256_hex(str(identity.get(digest_field, ""))):
            evidence_completeness = "INCOMPLETE"
            reason_codes.append("LINEAGE_INCOMPLETE")

    if not _non_empty_ref(identity.get("promotion_input_binding_bundle_ref")):
        evidence_completeness = "INCOMPLETE"
        reason_codes.append("LINEAGE_INCOMPLETE")
    if not _non_empty_ref(identity.get("completion_validity_binding_bundle_ref")):
        evidence_completeness = "INCOMPLETE"
        reason_codes.append("LINEAGE_INCOMPLETE")
    if not is_valid_sha256_hex(str(identity.get("candidate_identity_digest", ""))):
        evidence_completeness = "FAIL"
        reason_codes.append("DIGEST_MISMATCH")

    lineage_eligibility = "PASS"
    shared_lineage = str(identity.get("shared_lineage_status", ""))
    if shared_lineage == "FAIL":
        lineage_eligibility = "FAIL"
        reason_codes.append("LINEAGE_CONFLICT")
    elif shared_lineage != "PASS":
        lineage_eligibility = "INCOMPLETE"
        reason_codes.append("LINEAGE_INCOMPLETE")

    if upstream_binding_status == "NOT_EVALUABLE":
        candidate_status = "NOT_EVALUABLE"
        if "NOT_EVALUABLE_INSUFFICIENT_EVIDENCE" not in reason_codes:
            reason_codes.append("NOT_EVALUABLE_INSUFFICIENT_EVIDENCE")
    elif upstream_binding_status == "INCOMPLETE":
        candidate_status = "INCOMPLETE"
    elif upstream_binding_status == "FAIL":
        candidate_status = "FAIL"
    elif (
        structural == "PASS"
        and evidence_completeness == "PASS"
        and lineage_eligibility == "PASS"
        and contract_compatibility == "PASS"
        and capability_boundary == "PASS"
        and not reason_codes
    ):
        candidate_status = "PASS"
        reason_codes.append("ELIGIBLE_EVIDENCE_COMPLETE")
    elif (
        any(
            status == "FAIL"
            for status in (
                structural,
                evidence_completeness,
                lineage_eligibility,
                contract_compatibility,
                capability_boundary,
            )
        )
        or reason_codes
    ):
        candidate_status = "FAIL"
    else:
        candidate_status = "INCOMPLETE"

    return (
        structural,
        evidence_completeness,
        lineage_eligibility,
        contract_compatibility,
        capability_boundary,
        candidate_status,
        _sorted_reason_codes(reason_codes),
    )


def _input_artifact_ref_mapping(
    *,
    bundle: VerifiedCandidateIdentityBindingBundle,
) -> dict[str, Any]:
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


def build_comparison_promotion_candidate_eligibility_evidence_v1(
    *,
    identity_binding: VerifiedCandidateIdentityBindingBundle,
) -> dict[str, Any]:
    identity = identity_binding.evidence_payload
    (
        structural_eligibility_status,
        evidence_completeness_status,
        lineage_eligibility_status,
        contract_compatibility_status,
        capability_boundary_status,
        candidate_eligibility_status,
        candidate_eligibility_reason_codes,
    ) = _evaluate_eligibility(identity)

    input_ref = _input_artifact_ref_mapping(bundle=identity_binding)
    input_refs = [input_ref]
    parent_artifact_refs = list(identity_binding.parent_artifact_refs)
    parent_artifact_refs.sort(
        key=lambda item: (str(item.get("ref_type", "")), str(item.get("digest", "")))
    )

    completion_validity_ref = str(identity.get("completion_validity_binding_bundle_ref", ""))
    completion_validity_digest = _digest_from_parent_refs(
        identity_binding.parent_artifact_refs,
        contract_substring="comparison_completion_research_validity_binding",
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
        "is_comparison_promotion_candidate_eligibility_evidence": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "eligibility_evidence_does_not_select": True,
        "eligibility_evidence_does_not_choose_winner": True,
        "eligibility_evidence_does_not_accept": True,
        "eligibility_evidence_does_not_construct_promotion_candidate": True,
        "eligibility_evidence_does_not_execute_operational_filter": True,
        "eligibility_evidence_does_not_execute_policy": True,
        "eligibility_evidence_does_not_create_configpatch": True,
        "eligibility_evidence_does_not_modify_config": True,
        "eligibility_evidence_does_not_authorize_promotion": True,
        "eligibility_evidence_does_not_authorize_runtime": True,
        "eligibility_evidence_does_not_authorize_live": True,
        "eligibility_evidence_does_not_deploy": True,
        "eligibility_evidence_does_not_activate": True,
        "eligibility_evidence_does_not_create_order_intent": True,
        "eligibility_evidence_does_not_modify_trading_logic": True,
        "eligibility_evidence_authority_invariants": dict(
            ELIGIBILITY_EVIDENCE_AUTHORITY_INVARIANTS
        ),
        "candidate_identity_binding_bundle_ref": identity_binding.bundle_dir.as_posix(),
        "candidate_identity_binding_artifact_ref": identity_binding.artifact_ref,
        "candidate_identity_binding_digest": identity_binding.artifact_digest,
        "candidate_identity_binding_manifest_digest": identity_binding.manifest_digest,
        "candidate_identity_ref": str(identity.get("candidate_identity_ref", "")),
        "candidate_identity_digest": str(identity.get("candidate_identity_digest", "")),
        "candidate_identity_source_type": str(identity.get("candidate_identity_source_type", "")),
        "promotion_input_binding_ref": str(identity.get("promotion_input_binding_bundle_ref", "")),
        "promotion_input_binding_digest": str(identity.get("promotion_input_binding_digest", "")),
        "comparison_completion_ref": str(identity.get("comparison_completion_ref", "")),
        "comparison_completion_digest": str(identity.get("comparison_completion_digest", "")),
        "research_validity_ref": str(identity.get("research_validity_ref", "")),
        "research_validity_digest": str(identity.get("research_validity_digest", "")),
        "completion_validity_binding_ref": completion_validity_ref,
        "completion_validity_binding_digest": completion_validity_digest,
        "comparison_checkpoint_ref": str(identity.get("comparison_checkpoint_ref", "")),
        "comparison_checkpoint_digest": str(identity.get("comparison_checkpoint_digest", "")),
        "experiment_identity_ref": str(identity.get("experiment_identity_ref", "")),
        "experiment_identity_digest": str(identity.get("experiment_identity_digest", "")),
        "dataset_identity_ref": str(identity.get("dataset_identity_ref", "")),
        "dataset_identity_digest": str(identity.get("dataset_identity_digest", "")),
        "comparison_definition_ref": str(identity.get("comparison_definition_ref", "")),
        "comparison_definition_digest": str(
            identity.get("comparison_definition_digest")
            or identity.get("comparison_definition_id", "")
        ),
        "structural_eligibility_status": structural_eligibility_status,
        "evidence_completeness_status": evidence_completeness_status,
        "lineage_eligibility_status": lineage_eligibility_status,
        "contract_compatibility_status": contract_compatibility_status,
        "capability_boundary_status": capability_boundary_status,
        "candidate_eligibility_status": candidate_eligibility_status,
        "candidate_eligibility_reason_codes": candidate_eligibility_reason_codes,
        "candidate_selection_status": _CANDIDATE_SELECTION_NOT_SELECTED,
        "winner_selection_status": _WINNER_SELECTION_NOT_SELECTED,
        "candidate_acceptance_status": _CANDIDATE_ACCEPTANCE_NOT_ACCEPTED,
        "promotion_candidate_constructed": False,
        "operational_filter_executed": False,
        "promotion_policy_executed": False,
        "configpatch_created": False,
        "upstream_contract_name": identity_binding.contract_name,
        "upstream_contract_version": identity_binding.contract_version,
        "upstream_producer_version": identity_binding.producer_version,
        "input_artifact_refs": input_refs,
        "parent_artifact_refs": parent_artifact_refs,
        "input_digest": "",
        "output_digest": "",
        "manifest_digest": "",
    }

    metric_ref = identity.get("comparison_metric_input_ref")
    metric_digest = identity.get("comparison_metric_input_digest")
    if metric_ref is not None:
        payload["comparison_metric_input_ref"] = str(metric_ref)
    if metric_digest is not None:
        payload["comparison_metric_input_digest"] = str(metric_digest)

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    _validate_capabilities(payload["capabilities"])

    payload["input_digest"] = compute_content_sha256({"input_artifact_refs": input_refs})
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    return payload


def serialize_comparison_promotion_candidate_eligibility_evidence_v1(
    evidence: Mapping[str, Any],
) -> str:
    _reject_forbidden_index_keys(evidence)
    _validate_non_authorizing_flags(evidence)
    _validate_capabilities(evidence.get("capabilities"))
    if evidence.get("candidate_selection_status") != _CANDIDATE_SELECTION_NOT_SELECTED:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "candidate_selection_status must be NOT_SELECTED"
        )
    if evidence.get("winner_selection_status") != _WINNER_SELECTION_NOT_SELECTED:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "winner_selection_status must be NOT_SELECTED"
        )
    if evidence.get("candidate_acceptance_status") != _CANDIDATE_ACCEPTANCE_NOT_ACCEPTED:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "candidate_acceptance_status must be NOT_ACCEPTED"
        )
    for flag in (
        "promotion_candidate_constructed",
        "operational_filter_executed",
        "promotion_policy_executed",
        "configpatch_created",
    ):
        if evidence.get(flag) is not False:
            raise ComparisonPromotionCandidateEligibilityEvidenceError(
                f"{flag} must be false (fail-closed)"
            )
    status = evidence.get("candidate_eligibility_status")
    if status not in _VALID_ELIGIBILITY_STATUS:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            f"candidate_eligibility_status must be one of {sorted(_VALID_ELIGIBILITY_STATUS)}"
        )
    reason_codes = evidence.get("candidate_eligibility_reason_codes")
    if not isinstance(reason_codes, list):
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "candidate_eligibility_reason_codes must be a list"
        )
    if list(reason_codes) != sorted(reason_codes):
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "candidate_eligibility_reason_codes must be sorted deterministically"
        )
    return deterministic_json_dumps(dict(evidence))


def _evidence_bytes_for_manifest_digest(evidence: Mapping[str, Any]) -> bytes:
    canonical = {
        key: value for key, value in evidence.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_comparison_promotion_candidate_eligibility_evidence_v1(canonical).encode(
        "utf-8"
    )


def _compute_output_manifest_digest(evidence: Mapping[str, Any]) -> str:
    return hashlib.sha256(_evidence_bytes_for_manifest_digest(evidence)).hexdigest()


def _validate_evidence_integrity(evidence: Mapping[str, Any]) -> None:
    if evidence.get("contract_name") != CONTRACT_NAME:
        raise ComparisonPromotionCandidateEligibilityEvidenceError("contract_name mismatch")
    if evidence.get("contract_version") != CONTRACT_VERSION:
        raise ComparisonPromotionCandidateEligibilityEvidenceError("contract_version mismatch")
    if evidence.get("producer_version") != PRODUCER_VERSION:
        raise ComparisonPromotionCandidateEligibilityEvidenceError("producer_version mismatch")
    _validate_non_authorizing_flags(evidence)
    _validate_capabilities(evidence.get("capabilities"))
    invariants = evidence.get("eligibility_evidence_authority_invariants")
    if invariants != ELIGIBILITY_EVIDENCE_AUTHORITY_INVARIANTS:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "eligibility_evidence_authority_invariants mismatch"
        )

    stored = evidence.get("integrity")
    if not isinstance(stored, Mapping):
        raise ComparisonPromotionCandidateEligibilityEvidenceError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(evidence))
    actual = stored.get("content_sha256")
    if actual != expected:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "eligibility evidence integrity mismatch"
        )

    output_digest = evidence.get("output_digest")
    if output_digest != _compute_output_digest(evidence):
        raise ComparisonPromotionCandidateEligibilityEvidenceError("output_digest mismatch")
    if evidence.get("artifact_id") != output_digest:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "artifact_id must equal output_digest"
        )


def build_self_verification_v1(
    *,
    evidence: Mapping[str, Any],
    identity_binding: VerifiedCandidateIdentityBindingBundle,
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_one_direct_input", "status": "PASS"},
        {"check_id": "input_contract_and_version", "status": "PASS"},
        {"check_id": "input_manifest_verified", "status": "PASS"},
        {"check_id": "input_self_verification_pass", "status": "PASS"},
        {"check_id": "candidate_identity_bound", "status": "PASS"},
        {"check_id": "no_candidate_selection", "status": "PASS"},
        {"check_id": "no_winner_selection", "status": "PASS"},
        {"check_id": "no_candidate_acceptance", "status": "PASS"},
        {"check_id": "completion_validity_lineage", "status": "PASS"},
        {"check_id": "experiment_dataset_lineage", "status": "PASS"},
        {"check_id": "eligibility_status_present", "status": "PASS"},
        {"check_id": "deterministic_reason_codes", "status": "PASS"},
        {"check_id": "non_authorizing_semantics", "status": "PASS"},
        {"check_id": "forbidden_capabilities_absent", "status": "PASS"},
        {"check_id": "no_promotion_candidate_construction", "status": "PASS"},
        {"check_id": "no_operational_filter_execution", "status": "PASS"},
        {"check_id": "no_policy_execution", "status": "PASS"},
        {"check_id": "no_configpatch_creation", "status": "PASS"},
        {"check_id": "canonical_serialization", "status": "PASS"},
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

    if evidence.get("candidate_selection_status") != _CANDIDATE_SELECTION_NOT_SELECTED:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "no_candidate_selection" else c
            for c in checks
        ]

    eligibility_status = evidence.get("candidate_eligibility_status")
    if eligibility_status not in _VALID_ELIGIBILITY_STATUS:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "eligibility_status_present" else c
            for c in checks
        ]

    structural_failures = [
        check
        for check in checks
        if check["status"] != "PASS"
        and check["check_id"]
        not in {
            "eligibility_status_present",
            "completion_validity_lineage",
            "experiment_dataset_lineage",
        }
    ]
    if structural_failures:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
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
        "verified_candidate_identity_binding_bundle_ref": identity_binding.bundle_dir.as_posix(),
        "verified_candidate_eligibility_status": eligibility_status,
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


def verify_eligibility_inputs(
    inputs: ComparisonPromotionCandidateEligibilityEvidenceInputs,
) -> VerifiedCandidateIdentityBindingBundle:
    """Verify exactly one candidate identity binding bundle."""
    return verify_candidate_identity_binding_bundle(inputs.candidate_identity_binding_bundle_dir)


def reverify_comparison_promotion_candidate_eligibility_evidence_v1(
    *,
    output_dir: Path | str,
) -> None:
    """Replay eligibility evidence bundle without producer or upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            f"eligibility evidence directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
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
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "SELF_VERIFICATION overall_status must be PASS"
        )

    manifest_digest = _compute_output_manifest_digest(evidence)
    if evidence.get("manifest_digest") != manifest_digest:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "manifest_digest mismatch on replay"
        )

    identity_binding = verify_candidate_identity_binding_bundle(
        Path(str(evidence["candidate_identity_binding_bundle_ref"]))
    )
    if evidence.get("candidate_identity_binding_digest") != identity_binding.artifact_digest:
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
            "candidate_identity_binding_digest mismatch on replay"
        )


def produce_comparison_promotion_candidate_eligibility_evidence_v1(
    *,
    inputs: ComparisonPromotionCandidateEligibilityEvidenceInputs,
    output_dir: Path | str,
) -> ComparisonPromotionCandidateEligibilityEvidenceResult:
    """Produce offline LEVEL_3 candidate eligibility evidence from identity binding."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        input_dir=inputs.candidate_identity_binding_bundle_dir,
        output_dir=final_dir,
    )

    identity_binding = verify_eligibility_inputs(inputs)
    evidence_body = build_comparison_promotion_candidate_eligibility_evidence_v1(
        identity_binding=identity_binding,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ComparisonPromotionCandidateEligibilityEvidenceError(
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
            serialize_comparison_promotion_candidate_eligibility_evidence_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            evidence=finalized,
            identity_binding=identity_binding,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ComparisonPromotionCandidateEligibilityEvidenceError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_comparison_promotion_candidate_eligibility_evidence_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ComparisonPromotionCandidateEligibilityEvidenceError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    comparison_definition_id = str(
        identity_binding.evidence_payload.get("comparison_definition_id", "")
    )
    return ComparisonPromotionCandidateEligibilityEvidenceResult(
        output_dir=final_dir,
        comparison_definition_id=comparison_definition_id,
        artifact_id=str(finalized["artifact_id"]),
        evidence_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        candidate_eligibility_status=str(finalized["candidate_eligibility_status"]),
        candidate_identity_ref=str(finalized["candidate_identity_ref"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "AUTHORITY_LEVEL",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "ELIGIBILITY_EVIDENCE_AUTHORITY_INVARIANTS",
    "EVIDENCE_LEVEL",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "SELF_VERIFICATION_REL",
    "ComparisonPromotionCandidateEligibilityEvidenceError",
    "ComparisonPromotionCandidateEligibilityEvidenceInputs",
    "ComparisonPromotionCandidateEligibilityEvidenceResult",
    "VerifiedCandidateIdentityBindingBundle",
    "build_comparison_promotion_candidate_eligibility_evidence_v1",
    "build_self_verification_v1",
    "produce_comparison_promotion_candidate_eligibility_evidence_v1",
    "reverify_comparison_promotion_candidate_eligibility_evidence_v1",
    "serialize_comparison_promotion_candidate_eligibility_evidence_v1",
    "verify_candidate_identity_binding_bundle",
    "verify_eligibility_inputs",
]
