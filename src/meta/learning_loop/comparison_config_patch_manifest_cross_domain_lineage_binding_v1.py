"""Offline LEVEL_3 cross-domain lineage binding between comparison chain and ConfigPatch manifest v1."""

from __future__ import annotations

import hashlib
import json
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
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    LineageRefType,
    validate_candidate_lineage_manifest_v1,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.comparison_promotion_candidate_identity_binding_v1 import (
    ARTIFACT_REL as IDENTITY_BINDING_ARTIFACT_REL,
)
from src.meta.learning_loop.comparison_promotion_candidate_model_parameter_identity_binding_v1 import (
    ARTIFACT_REL as MODEL_PARAMETER_BINDING_ARTIFACT_REL,
    CONTRACT_NAME as UPSTREAM_CONTRACT_NAME,
    CONTRACT_VERSION as UPSTREAM_CONTRACT_VERSION,
    PRODUCER_VERSION as UPSTREAM_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as UPSTREAM_SELF_VERIFICATION_REL,
    ComparisonPromotionCandidateModelParameterIdentityBindingError,
    reverify_comparison_promotion_candidate_model_parameter_identity_binding_v1,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.config_patch_manifest_v1 import (
    ConfigPatchManifestError,
    ConfigPatchManifestV1,
    load_config_patch_manifest_v1_from_json_path,
)
from src.meta.learning_loop.contract_safety_v1 import (
    SCHEMA_VERSION_V1,
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
    is_valid_uuid,
)

CONTRACT_NAME = "comparison_config_patch_manifest_cross_domain_lineage_binding_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "comparison_config_patch_manifest_cross_domain_lineage_binding_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING_EVIDENCE_ONLY"
RECORD_KIND = "comparison_config_patch_manifest_cross_domain_lineage_binding_record"
INPUT_RELATION = "BINDS_VERIFIED_MODEL_PARAMETER_IDENTITY_AND_CONFIG_PATCH_MANIFEST"
ARTIFACT_REL = "comparison_config_patch_manifest_cross_domain_lineage_binding_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".comparison_config_patch_manifest_cross_domain_lineage_staging_"

CONFIG_PATCH_CONTRACT_NAME = "config_patch_manifest_v1"
CONFIG_PATCH_CONTRACT_VERSION = "v1"
CANDIDATE_LINEAGE_ARTIFACT_REL = "candidate_lineage_manifest_v1.json"

OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"

_VALID_BINDING_STATUS = frozenset({"PASS", "FAIL", "INCOMPLETE", "NOT_EVALUABLE"})
_IDENTITY_BOUND = "BOUND"
_IDENTITY_NOT_BOUND = "NOT_BOUND"
_CANDIDATE_SELECTION_NOT_SELECTED = "NOT_SELECTED"
_WINNER_SELECTION_NOT_SELECTED = "NOT_SELECTED"
_CANDIDATE_ACCEPTANCE_NOT_ACCEPTED = "NOT_ACCEPTED"

CROSS_DOMAIN_BINDING_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "cross_domain_binding_is_descriptive_only": True,
    "cross_domain_binding_does_not_select": True,
    "cross_domain_binding_does_not_choose_winner": True,
    "cross_domain_binding_does_not_accept": True,
    "cross_domain_binding_does_not_construct_promotion_candidate": True,
    "cross_domain_binding_does_not_execute_operational_filter": True,
    "cross_domain_binding_does_not_execute_policy": True,
    "cross_domain_binding_does_not_create_configpatch": True,
    "cross_domain_binding_does_not_modify_configpatch": True,
    "cross_domain_binding_does_not_apply_configpatch": True,
    "cross_domain_binding_does_not_modify_config": True,
    "cross_domain_binding_does_not_authorize_promotion": True,
    "cross_domain_binding_does_not_authorize_runtime": True,
    "cross_domain_binding_does_not_authorize_live": True,
    "cross_domain_binding_does_not_deploy": True,
    "cross_domain_binding_does_not_activate": True,
    "cross_domain_binding_does_not_create_order_intent": True,
    "cross_domain_binding_does_not_modify_trading_logic": True,
    "evidence_does_not_authorize_promotion": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_comparison_config_patch_manifest_cross_domain_lineage_binding": True,
    "evidence_does_not_authorize_promotion": True,
    "evidence_does_not_authorize_runtime": True,
    "binding_does_not_select_candidate": True,
    "binding_does_not_choose_winner": True,
    "binding_does_not_accept_candidate": True,
    "binding_does_not_accept_configpatch": True,
    "binding_does_not_construct_promotion_candidate": True,
    "binding_does_not_execute_operational_filter": True,
    "binding_does_not_execute_policy": True,
    "binding_does_not_create_configpatch": True,
    "binding_does_not_modify_configpatch": True,
    "binding_does_not_apply_configpatch": True,
    "binding_does_not_modify_config": True,
    "binding_does_not_authorize_promotion": True,
    "binding_does_not_authorize_runtime": True,
    "binding_does_not_authorize_live": True,
    "binding_does_not_deploy": True,
    "binding_does_not_activate": True,
    "binding_does_not_create_order_intent": True,
    "binding_does_not_modify_trading_logic": True,
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
    "comparison_config_patch_manifest_cross_domain_lineage_binding_self_verification_v1"
)


class ComparisonConfigPatchManifestCrossDomainLineageBindingError(ValueError):
    """Fail-closed cross-domain lineage binding error."""


@dataclass(frozen=True)
class VerifiedModelParameterIdentityBindingBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    evidence_payload: dict[str, Any]


@dataclass(frozen=True)
class VerifiedConfigPatchManifestInput:
    manifest_path: Path
    manifest: ConfigPatchManifestV1
    manifest_digest: str
    manifest_id: str
    lineage_manifest_ref: str | None
    schema_version: str


@dataclass(frozen=True)
class ResolvedCandidateLineage:
    lineage_manifest_id: str
    candidate_id: str
    candidate_lineage_digest: str
    experiment_ref_id: str
    experiment_ref_digest: str | None


@dataclass(frozen=True)
class ComparisonConfigPatchManifestCrossDomainLineageBindingInputs:
    model_parameter_identity_binding_bundle_dir: Path
    config_patch_manifest_path: Path


@dataclass(frozen=True)
class ComparisonConfigPatchManifestCrossDomainLineageBindingResult:
    output_dir: Path
    comparison_definition_id: str
    artifact_id: str
    evidence_path: Path
    self_verification_path: Path
    manifest_path: Path
    cross_domain_lineage_binding_status: str
    candidate_identity_ref: str
    config_patch_manifest_id: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            f"{label} must not be a symlink"
        )


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
                f"forbidden index key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            f"{label} must be a regular file: {path}"
        )


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            f"{label} must be a directory: {bundle_dir}"
        )


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            f"output directory already exists: {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "output directory must not be under /tmp"
        )


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(
    *,
    model_parameter_binding_dir: Path,
    config_patch_manifest_path: Path,
    output_dir: Path,
) -> None:
    binding_res = model_parameter_binding_dir.resolve()
    config_res = config_patch_manifest_path.resolve()
    output_res = output_dir.resolve()
    if output_res in {binding_res, config_res}:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "output directory must not equal an input path"
        )
    for src in (binding_res, config_res):
        if _path_is_under(output_res, src):
            raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
                "output directory must not be inside an input path"
            )
        if src.is_dir() and _path_is_under(src, output_res):
            raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
                "input directory must not be inside output directory"
            )
    if _path_is_under(config_res, binding_res) or _path_is_under(binding_res, config_res):
        return


def _manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / MANIFEST_FILENAME
    _validate_regular_file(manifest_path, label=MANIFEST_FILENAME)
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _validate_capabilities(capabilities: Any) -> list[str]:
    if capabilities is None:
        return []
    if not isinstance(capabilities, list):
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "capabilities must be a list"
        )
    normalized: list[str] = []
    for item in capabilities:
        if not isinstance(item, str):
            raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
                "capabilities entries must be strings"
            )
        if item in _FORBIDDEN_CAPABILITIES:
            raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
                f"forbidden capability: {item}"
            )
        normalized.append(item)
    return sorted(normalized)


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if payload.get(key) is not expected:
            raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
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
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            f"{label} must be a JSON object"
        )
    return payload


def verify_model_parameter_identity_binding_bundle(
    bundle_dir: Path | str,
) -> VerifiedModelParameterIdentityBindingBundle:
    """Fail-closed verification of exactly one Step-1 model/parameter identity binding bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="model parameter identity binding bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            f"model parameter identity binding MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = path / MODEL_PARAMETER_BINDING_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=MODEL_PARAMETER_BINDING_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != UPSTREAM_CONTRACT_NAME:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "upstream model parameter identity binding contract_name mismatch"
        )
    if payload.get("contract_version") != UPSTREAM_CONTRACT_VERSION:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "upstream model parameter identity binding contract_version mismatch"
        )

    self_payload = _load_self_verification(
        path,
        rel=UPSTREAM_SELF_VERIFICATION_REL,
        label=UPSTREAM_SELF_VERIFICATION_REL,
    )
    if self_payload.get("overall_status") != "PASS":
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "upstream model parameter identity binding SELF_VERIFICATION overall_status must be PASS"
        )

    try:
        reverify_comparison_promotion_candidate_model_parameter_identity_binding_v1(
            output_dir=path
        )
    except ComparisonPromotionCandidateModelParameterIdentityBindingError as exc:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(str(exc)) from exc

    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "model parameter identity binding integrity must be an object"
        )
    artifact_digest = integrity.get("content_sha256")
    if not isinstance(artifact_digest, str) or not is_valid_sha256_hex(artifact_digest):
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "model parameter identity binding integrity.content_sha256 invalid"
        )

    return VerifiedModelParameterIdentityBindingBundle(
        bundle_dir=path.resolve(),
        contract_name=UPSTREAM_CONTRACT_NAME,
        contract_version=UPSTREAM_CONTRACT_VERSION,
        producer_version=UPSTREAM_PRODUCER_VERSION,
        artifact_ref=MODEL_PARAMETER_BINDING_ARTIFACT_REL,
        artifact_digest=artifact_digest,
        manifest_digest=_manifest_file_digest(path),
        evidence_payload=dict(payload),
    )


def verify_config_patch_manifest_input(
    manifest_path: Path | str,
) -> VerifiedConfigPatchManifestInput:
    """Fail-closed verification of exactly one ConfigPatch manifest JSON artifact."""
    path = Path(manifest_path)
    _validate_regular_file(path, label="config patch manifest")
    try:
        manifest = load_config_patch_manifest_v1_from_json_path(path)
    except ConfigPatchManifestError as exc:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(str(exc)) from exc
    if manifest.integrity is None:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "config patch manifest integrity missing"
        )
    return VerifiedConfigPatchManifestInput(
        manifest_path=path.resolve(),
        manifest=manifest,
        manifest_digest=manifest.integrity.content_sha256,
        manifest_id=manifest.manifest_id,
        lineage_manifest_ref=manifest.lineage_manifest_ref,
        schema_version=manifest.schema_version,
    )


def _resolve_candidate_lineage_from_step1(
    step1: Mapping[str, Any],
) -> tuple[ResolvedCandidateLineage | None, list[str]]:
    reason_codes: list[str] = []
    binding_ref = step1.get("candidate_identity_binding_bundle_ref")
    if not _non_empty_ref(binding_ref):
        reason_codes.append("CANDIDATE_LINEAGE_MANIFEST_UNRESOLVABLE")
        return None, reason_codes

    identity_path = Path(str(binding_ref)) / IDENTITY_BINDING_ARTIFACT_REL
    if not identity_path.is_file():
        reason_codes.append("CANDIDATE_LINEAGE_MANIFEST_UNRESOLVABLE")
        return None, reason_codes

    identity_payload = read_manifest(identity_path)
    candidate_bundle_ref = identity_payload.get("candidate_identity_bundle_ref")
    if not _non_empty_ref(candidate_bundle_ref):
        reason_codes.append("CANDIDATE_LINEAGE_MANIFEST_UNRESOLVABLE")
        return None, reason_codes

    lineage_path = Path(str(candidate_bundle_ref)) / CANDIDATE_LINEAGE_ARTIFACT_REL
    if not lineage_path.is_file():
        reason_codes.append("CANDIDATE_LINEAGE_MANIFEST_UNRESOLVABLE")
        return None, reason_codes

    lineage_payload = json.loads(lineage_path.read_text(encoding="utf-8"))
    valid, phase, errors, verdict = validate_candidate_lineage_manifest_v1(lineage_payload)
    if not valid:
        reason_codes.append("CANDIDATE_LINEAGE_MANIFEST_INVALID")
        return None, reason_codes

    lineage_manifest_id = lineage_payload.get("lineage_manifest_id")
    candidate_id = lineage_payload.get("candidate_id")
    integrity = lineage_payload.get("integrity")
    if not isinstance(lineage_manifest_id, str) or not is_valid_uuid(lineage_manifest_id):
        reason_codes.append("CANDIDATE_LINEAGE_MANIFEST_INVALID")
        return None, reason_codes
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        reason_codes.append("CANDIDATE_LINEAGE_MANIFEST_INVALID")
        return None, reason_codes
    if not isinstance(integrity, Mapping):
        reason_codes.append("CANDIDATE_LINEAGE_MANIFEST_INVALID")
        return None, reason_codes
    lineage_digest = integrity.get("content_sha256")
    if not isinstance(lineage_digest, str) or not is_valid_sha256_hex(lineage_digest):
        reason_codes.append("CANDIDATE_LINEAGE_MANIFEST_INVALID")
        return None, reason_codes

    experiment_ref_id = ""
    experiment_ref_digest: str | None = None
    refs = lineage_payload.get("refs")
    if isinstance(refs, list):
        for ref in refs:
            if not isinstance(ref, Mapping):
                continue
            if ref.get("ref_type") == LineageRefType.EXPERIMENT.value:
                ref_id = ref.get("ref_id")
                if isinstance(ref_id, str) and ref_id.strip():
                    experiment_ref_id = ref_id
                digest = ref.get("digest")
                if isinstance(digest, str) and is_valid_sha256_hex(digest):
                    experiment_ref_digest = digest
                break

    return (
        ResolvedCandidateLineage(
            lineage_manifest_id=lineage_manifest_id,
            candidate_id=candidate_id,
            candidate_lineage_digest=lineage_digest,
            experiment_ref_id=experiment_ref_id,
            experiment_ref_digest=experiment_ref_digest,
        ),
        reason_codes,
    )


def _evaluate_cross_domain_binding(
    *,
    step1: Mapping[str, Any],
    config_patch: VerifiedConfigPatchManifestInput,
    candidate_lineage: ResolvedCandidateLineage | None,
    resolution_reason_codes: list[str],
) -> tuple[str, str, str, str, str, str, list[str]]:
    reason_codes = list(resolution_reason_codes)

    if step1.get("candidate_selection_status") != _CANDIDATE_SELECTION_NOT_SELECTED:
        reason_codes.append("CANDIDATE_SELECTION_DETECTED")
    if step1.get("winner_selection_status") != _WINNER_SELECTION_NOT_SELECTED:
        reason_codes.append("WINNER_SELECTION_DETECTED")
    if step1.get("candidate_acceptance_status") != _CANDIDATE_ACCEPTANCE_NOT_ACCEPTED:
        reason_codes.append("CANDIDATE_ACCEPTANCE_DETECTED")
    if step1.get("configpatch_created") is not False:
        reason_codes.append("CONFIGPATCH_CREATION_DETECTED")
    if step1.get("promotion_candidate_constructed") is not False:
        reason_codes.append("PROMOTION_CANDIDATE_CONSTRUCTION_DETECTED")

    upstream_status = str(step1.get("model_parameter_identity_binding_status", ""))
    if upstream_status == "NOT_EVALUABLE":
        return (
            "NOT_EVALUABLE",
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
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
            _IDENTITY_NOT_BOUND,
            _sorted_reason_codes(reason_codes + ["UPSTREAM_MODEL_PARAMETER_IDENTITY_INCOMPLETE"]),
        )
    if upstream_status == "FAIL":
        return (
            "FAIL",
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _sorted_reason_codes(reason_codes + ["UPSTREAM_MODEL_PARAMETER_IDENTITY_FAIL"]),
        )

    if config_patch.schema_version != SCHEMA_VERSION_V1:
        reason_codes.append("UNSUPPORTED_CONFIG_PATCH_CONTRACT_VERSION")

    candidate_ref = str(step1.get("candidate_identity_ref", ""))
    candidate_digest = str(step1.get("candidate_identity_digest", ""))
    if not _non_empty_ref(candidate_ref):
        reason_codes.append("CANDIDATE_IDENTITY_NOT_BOUND")
    elif candidate_lineage is not None and candidate_ref != candidate_lineage.candidate_id:
        reason_codes.append("CANDIDATE_LINEAGE_MISMATCH")
    if not is_valid_sha256_hex(candidate_digest):
        reason_codes.append("CANDIDATE_DIGEST_MISMATCH")
    elif (
        candidate_lineage is not None
        and candidate_digest != candidate_lineage.candidate_lineage_digest
    ):
        reason_codes.append("CANDIDATE_DIGEST_MISMATCH")

    model_ref = str(step1.get("model_identity_ref", ""))
    model_digest = str(step1.get("model_identity_digest", ""))
    if not _non_empty_ref(model_ref) or not is_valid_sha256_hex(model_digest):
        reason_codes.append("MODEL_IDENTITY_NOT_BOUND")
    elif model_ref != model_digest:
        reason_codes.append("MODEL_IDENTITY_DIGEST_MISMATCH")

    parameter_ref = str(step1.get("parameter_set_identity_ref", ""))
    parameter_digest = str(step1.get("parameter_set_identity_digest", ""))
    if not _non_empty_ref(parameter_ref) or not is_valid_sha256_hex(parameter_digest):
        reason_codes.append("PARAMETER_SET_IDENTITY_NOT_BOUND")
    elif parameter_ref != parameter_digest:
        reason_codes.append("PARAMETER_SET_IDENTITY_DIGEST_MISMATCH")

    experiment_ref = str(step1.get("experiment_identity_ref", ""))
    experiment_digest = str(step1.get("experiment_identity_digest", ""))
    experiment_id = str(step1.get("experiment_identity_id", ""))
    if not _non_empty_ref(experiment_ref) or not is_valid_sha256_hex(experiment_digest):
        reason_codes.append("EXPERIMENT_IDENTITY_MISSING")
    elif candidate_lineage is not None:
        if experiment_id and candidate_lineage.experiment_ref_id != experiment_id:
            reason_codes.append("EXPERIMENT_LINEAGE_CROSS_DOMAIN_MISMATCH")
        elif (
            candidate_lineage.experiment_ref_digest is not None
            and candidate_lineage.experiment_ref_digest != experiment_digest
        ):
            reason_codes.append("EXPERIMENT_LINEAGE_CROSS_DOMAIN_MISMATCH")
        else:
            reason_codes.append("EXPERIMENT_LINEAGE_CROSS_DOMAIN_MATCH")

    dataset_ref = str(step1.get("dataset_identity_ref", ""))
    dataset_digest = str(step1.get("dataset_identity_digest", ""))
    if not _non_empty_ref(dataset_ref) or not is_valid_sha256_hex(dataset_digest):
        reason_codes.append("DATASET_LINEAGE_CROSS_DOMAIN_MISMATCH")
    else:
        reason_codes.append("DATASET_LINEAGE_CROSS_DOMAIN_MATCH")

    comparison_ref = str(step1.get("comparison_definition_ref", ""))
    comparison_digest = str(
        step1.get("comparison_definition_digest") or step1.get("comparison_definition_id", "")
    )
    if not _non_empty_ref(comparison_ref) or not is_valid_sha256_hex(comparison_digest):
        reason_codes.append("COMPARISON_LINEAGE_CROSS_DOMAIN_MISMATCH")
    else:
        reason_codes.append("COMPARISON_LINEAGE_CROSS_DOMAIN_MATCH")

    if not is_valid_uuid(config_patch.manifest_id):
        reason_codes.append("CONFIG_PATCH_MANIFEST_INVALID")
    if not is_valid_sha256_hex(config_patch.manifest_digest):
        reason_codes.append("CONFIG_PATCH_MANIFEST_DIGEST_MISMATCH")

    if config_patch.lineage_manifest_ref is None:
        reason_codes.append("LINEAGE_MANIFEST_REF_MISSING")
    elif candidate_lineage is None:
        reason_codes.append("LINEAGE_MANIFEST_REF_MISMATCH")
    elif config_patch.lineage_manifest_ref != candidate_lineage.lineage_manifest_id:
        reason_codes.append("LINEAGE_MANIFEST_REF_MISMATCH")
    else:
        reason_codes.append("LINEAGE_MANIFEST_REF_BOUND")

    for patch in config_patch.manifest.patches:
        source_experiment_id = patch.source_experiment_id
        if source_experiment_id is not None and experiment_id:
            if source_experiment_id != experiment_id:
                reason_codes.append("CONFIG_PATCH_STRATEGY_LINEAGE_MISMATCH")

    fail_codes = {
        "CANDIDATE_SELECTION_DETECTED",
        "WINNER_SELECTION_DETECTED",
        "CANDIDATE_ACCEPTANCE_DETECTED",
        "CONFIGPATCH_CREATION_DETECTED",
        "PROMOTION_CANDIDATE_CONSTRUCTION_DETECTED",
        "UNSUPPORTED_CONFIG_PATCH_CONTRACT_VERSION",
        "CANDIDATE_IDENTITY_NOT_BOUND",
        "CANDIDATE_DIGEST_MISMATCH",
        "CANDIDATE_LINEAGE_MISMATCH",
        "MODEL_IDENTITY_NOT_BOUND",
        "MODEL_IDENTITY_DIGEST_MISMATCH",
        "PARAMETER_SET_IDENTITY_NOT_BOUND",
        "PARAMETER_SET_IDENTITY_DIGEST_MISMATCH",
        "EXPERIMENT_IDENTITY_MISSING",
        "EXPERIMENT_LINEAGE_CROSS_DOMAIN_MISMATCH",
        "DATASET_LINEAGE_CROSS_DOMAIN_MISMATCH",
        "COMPARISON_LINEAGE_CROSS_DOMAIN_MISMATCH",
        "CONFIG_PATCH_MANIFEST_INVALID",
        "CONFIG_PATCH_MANIFEST_DIGEST_MISMATCH",
        "LINEAGE_MANIFEST_REF_MISSING",
        "LINEAGE_MANIFEST_REF_MISMATCH",
        "CONFIG_PATCH_STRATEGY_LINEAGE_MISMATCH",
        "CANDIDATE_LINEAGE_MANIFEST_INVALID",
        "CANDIDATE_LINEAGE_MANIFEST_UNRESOLVABLE",
    }

    binding_status = "PASS"
    candidate_status = _IDENTITY_BOUND
    model_status = _IDENTITY_BOUND
    parameter_status = _IDENTITY_BOUND
    config_patch_status = _IDENTITY_BOUND
    cross_domain_status = _IDENTITY_BOUND

    if any(code in reason_codes for code in fail_codes):
        binding_status = "FAIL"
        candidate_status = (
            _IDENTITY_NOT_BOUND
            if "CANDIDATE_IDENTITY_NOT_BOUND" in reason_codes
            else candidate_status
        )
        model_status = (
            _IDENTITY_NOT_BOUND if "MODEL_IDENTITY_NOT_BOUND" in reason_codes else model_status
        )
        parameter_status = (
            _IDENTITY_NOT_BOUND
            if "PARAMETER_SET_IDENTITY_NOT_BOUND" in reason_codes
            else parameter_status
        )
        config_patch_status = (
            _IDENTITY_NOT_BOUND
            if any(
                c in reason_codes
                for c in (
                    "CONFIG_PATCH_MANIFEST_INVALID",
                    "CONFIG_PATCH_MANIFEST_DIGEST_MISMATCH",
                    "LINEAGE_MANIFEST_REF_MISSING",
                    "LINEAGE_MANIFEST_REF_MISMATCH",
                )
            )
            else config_patch_status
        )
        cross_domain_status = _IDENTITY_NOT_BOUND

    if binding_status == "PASS":
        reason_codes.extend(
            [
                "CANDIDATE_IDENTITY_CROSS_DOMAIN_BOUND",
                "MODEL_IDENTITY_CROSS_DOMAIN_BOUND",
                "PARAMETER_SET_IDENTITY_CROSS_DOMAIN_BOUND",
                "CONFIG_PATCH_MANIFEST_IDENTITY_BOUND",
                "CONFIG_PATCH_MANIFEST_CROSS_DOMAIN_LINEAGE_BINDING_COMPLETE",
            ]
        )

    return (
        binding_status,
        candidate_status,
        model_status,
        parameter_status,
        config_patch_status,
        cross_domain_status,
        _sorted_reason_codes(reason_codes),
    )


def _input_artifact_ref_mapping(
    *,
    bundle: VerifiedModelParameterIdentityBindingBundle,
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


def _config_patch_input_ref_mapping(
    *,
    config_patch: VerifiedConfigPatchManifestInput,
) -> dict[str, Any]:
    return {
        "artifact_type": CONFIG_PATCH_CONTRACT_NAME,
        "contract_name": CONFIG_PATCH_CONTRACT_NAME,
        "contract_version": CONFIG_PATCH_CONTRACT_VERSION,
        "artifact_ref": config_patch.manifest_path.name,
        "artifact_digest": config_patch.manifest_digest,
        "manifest_id": config_patch.manifest_id,
        "manifest_path": config_patch.manifest_path.as_posix(),
        "schema_version": config_patch.schema_version,
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


def build_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
    *,
    model_parameter_binding: VerifiedModelParameterIdentityBindingBundle,
    config_patch: VerifiedConfigPatchManifestInput,
) -> dict[str, Any]:
    step1 = model_parameter_binding.evidence_payload
    candidate_lineage, resolution_codes = _resolve_candidate_lineage_from_step1(step1)
    (
        binding_status,
        candidate_identity_status,
        model_identity_status,
        parameter_set_identity_status,
        config_patch_manifest_identity_status,
        cross_domain_lineage_status,
        reason_codes,
    ) = _evaluate_cross_domain_binding(
        step1=step1,
        config_patch=config_patch,
        candidate_lineage=candidate_lineage,
        resolution_reason_codes=resolution_codes,
    )

    input_refs = [
        _input_artifact_ref_mapping(bundle=model_parameter_binding),
        _config_patch_input_ref_mapping(config_patch=config_patch),
    ]
    parent_artifact_refs = list(step1.get("parent_artifact_refs", []))
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
        "is_comparison_config_patch_manifest_cross_domain_lineage_binding": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "binding_does_not_select_candidate": True,
        "binding_does_not_choose_winner": True,
        "binding_does_not_accept_candidate": True,
        "binding_does_not_accept_configpatch": True,
        "binding_does_not_construct_promotion_candidate": True,
        "binding_does_not_execute_operational_filter": True,
        "binding_does_not_execute_policy": True,
        "binding_does_not_create_configpatch": True,
        "binding_does_not_modify_configpatch": True,
        "binding_does_not_apply_configpatch": True,
        "binding_does_not_modify_config": True,
        "binding_does_not_authorize_promotion": True,
        "binding_does_not_authorize_runtime": True,
        "binding_does_not_authorize_live": True,
        "binding_does_not_deploy": True,
        "binding_does_not_activate": True,
        "binding_does_not_create_order_intent": True,
        "binding_does_not_modify_trading_logic": True,
        "cross_domain_binding_authority_invariants": dict(
            CROSS_DOMAIN_BINDING_AUTHORITY_INVARIANTS
        ),
        "model_parameter_identity_binding_bundle_ref": model_parameter_binding.bundle_dir.as_posix(),
        "model_parameter_identity_binding_digest": model_parameter_binding.artifact_digest,
        "model_parameter_identity_binding_manifest_digest": model_parameter_binding.manifest_digest,
        "upstream_contract_name": model_parameter_binding.contract_name,
        "upstream_contract_version": model_parameter_binding.contract_version,
        "upstream_producer_version": model_parameter_binding.producer_version,
        "upstream_model_parameter_identity_binding_status": str(
            step1.get("model_parameter_identity_binding_status", "")
        ),
        "config_patch_manifest_ref": config_patch.manifest_path.as_posix(),
        "config_patch_manifest_digest": config_patch.manifest_digest,
        "config_patch_manifest_id": config_patch.manifest_id,
        "config_patch_contract_name": CONFIG_PATCH_CONTRACT_NAME,
        "config_patch_contract_version": CONFIG_PATCH_CONTRACT_VERSION,
        "config_patch_schema_version": config_patch.schema_version,
        "config_patch_lineage_manifest_ref": config_patch.lineage_manifest_ref,
        "candidate_identity_ref": str(step1.get("candidate_identity_ref", "")),
        "candidate_identity_digest": str(step1.get("candidate_identity_digest", "")),
        "candidate_identity_status": candidate_identity_status,
        "candidate_selection_status": _CANDIDATE_SELECTION_NOT_SELECTED,
        "winner_selection_status": _WINNER_SELECTION_NOT_SELECTED,
        "candidate_acceptance_status": _CANDIDATE_ACCEPTANCE_NOT_ACCEPTED,
        "promotion_candidate_constructed": False,
        "operational_filter_executed": False,
        "promotion_policy_executed": False,
        "configpatch_created": False,
        "configpatch_modified": False,
        "configpatch_applied": False,
        "configpatch_accepted": False,
        "experiment_identity_ref": str(step1.get("experiment_identity_ref", "")),
        "experiment_identity_digest": str(step1.get("experiment_identity_digest", "")),
        "experiment_identity_id": str(step1.get("experiment_identity_id", "")),
        "dataset_identity_ref": str(step1.get("dataset_identity_ref", "")),
        "dataset_identity_digest": str(step1.get("dataset_identity_digest", "")),
        "comparison_identity_ref": str(step1.get("comparison_definition_ref", "")),
        "comparison_identity_digest": str(
            step1.get("comparison_definition_digest") or step1.get("comparison_definition_id", "")
        ),
        "comparison_definition_id": str(step1.get("comparison_definition_id", "")),
        "comparison_completion_ref": str(step1.get("comparison_completion_ref", "")),
        "comparison_completion_digest": str(step1.get("comparison_completion_digest", "")),
        "research_validity_ref": str(step1.get("research_validity_ref", "")),
        "research_validity_digest": str(step1.get("research_validity_digest", "")),
        "comparison_checkpoint_ref": str(step1.get("comparison_checkpoint_ref", "")),
        "comparison_checkpoint_digest": str(step1.get("comparison_checkpoint_digest", "")),
        "model_identity_status": model_identity_status,
        "parameter_set_identity_status": parameter_set_identity_status,
        "config_patch_manifest_identity_status": config_patch_manifest_identity_status,
        "cross_domain_lineage_status": cross_domain_lineage_status,
        "cross_domain_lineage_binding_status": binding_status,
        "cross_domain_lineage_binding_reason_codes": reason_codes,
        "input_artifact_refs": input_refs,
        "parent_artifact_refs": parent_artifact_refs,
        "input_digest": "",
        "output_digest": "",
        "manifest_digest": "",
    }

    if candidate_lineage is not None:
        payload["candidate_lineage_manifest_id"] = candidate_lineage.lineage_manifest_id
        payload["candidate_lineage_digest"] = candidate_lineage.candidate_lineage_digest

    for field in (
        "model_identity_ref",
        "model_identity_digest",
        "parameter_set_identity_ref",
        "parameter_set_identity_digest",
    ):
        value = step1.get(field)
        if value is not None:
            payload[field] = str(value)

    metric_ref = step1.get("comparison_metric_input_ref")
    metric_digest = step1.get("comparison_metric_input_digest")
    if metric_ref is not None:
        payload["comparison_metric_input_ref"] = str(metric_ref)
    if metric_digest is not None:
        payload["comparison_metric_input_digest"] = str(metric_digest)

    policy_version = config_patch.manifest.metadata.get("policy_version")
    if isinstance(policy_version, str) and policy_version.strip():
        payload["config_patch_policy_version"] = policy_version

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    _validate_capabilities(payload["capabilities"])

    payload["input_digest"] = compute_content_sha256({"input_artifact_refs": input_refs})
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    return payload


def serialize_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
    evidence: Mapping[str, Any],
) -> str:
    _reject_forbidden_index_keys(evidence)
    _validate_non_authorizing_flags(evidence)
    _validate_capabilities(evidence.get("capabilities"))
    binding_status = evidence.get("cross_domain_lineage_binding_status")
    if binding_status not in _VALID_BINDING_STATUS:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            f"cross_domain_lineage_binding_status must be one of {sorted(_VALID_BINDING_STATUS)}"
        )
    reason_codes = evidence.get("cross_domain_lineage_binding_reason_codes")
    if isinstance(reason_codes, list) and reason_codes != sorted(reason_codes):
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "cross_domain_lineage_binding_reason_codes must be sorted deterministically"
        )
    return deterministic_json_dumps(evidence)


def _evidence_bytes_for_manifest_digest(evidence: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in evidence.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(body).encode(
        "utf-8"
    )


def _compute_output_manifest_digest(evidence: Mapping[str, Any]) -> str:
    return hashlib.sha256(_evidence_bytes_for_manifest_digest(evidence)).hexdigest()


def _validate_evidence_integrity(evidence: Mapping[str, Any]) -> None:
    if evidence.get("contract_name") != CONTRACT_NAME:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError("contract_name mismatch")
    if evidence.get("contract_version") != CONTRACT_VERSION:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "contract_version mismatch"
        )
    integrity = evidence.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "integrity must be an object"
        )
    expected = compute_content_sha256(_integrity_body(evidence))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "integrity.content_sha256 mismatch"
        )
    output_digest = evidence.get("output_digest")
    if output_digest != _compute_output_digest(evidence):
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError("output_digest mismatch")
    if evidence.get("artifact_id") != output_digest:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "artifact_id must equal output_digest"
        )


def build_self_verification_v1(
    *,
    evidence: Mapping[str, Any],
    model_parameter_binding: VerifiedModelParameterIdentityBindingBundle,
    config_patch: VerifiedConfigPatchManifestInput,
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_two_direct_inputs", "status": "PASS"},
        {"check_id": "upstream_contract_and_version", "status": "PASS"},
        {"check_id": "model_parameter_binding_manifest_verified", "status": "PASS"},
        {"check_id": "model_parameter_binding_self_verification_pass", "status": "PASS"},
        {"check_id": "config_patch_manifest_validated", "status": "PASS"},
        {"check_id": "candidate_identity_bound_on_pass", "status": "PASS"},
        {"check_id": "model_identity_bound_on_pass", "status": "PASS"},
        {"check_id": "parameter_set_identity_bound_on_pass", "status": "PASS"},
        {"check_id": "config_patch_manifest_identity_bound_on_pass", "status": "PASS"},
        {"check_id": "cross_domain_lineage_bound_on_pass", "status": "PASS"},
        {"check_id": "no_candidate_selection", "status": "PASS"},
        {"check_id": "no_winner_selection", "status": "PASS"},
        {"check_id": "no_candidate_acceptance", "status": "PASS"},
        {"check_id": "no_configpatch_creation", "status": "PASS"},
        {"check_id": "no_configpatch_mutation", "status": "PASS"},
        {"check_id": "no_configpatch_application", "status": "PASS"},
        {"check_id": "no_promotion_candidate_construction", "status": "PASS"},
        {"check_id": "non_authorizing_semantics", "status": "PASS"},
        {"check_id": "forbidden_capabilities_absent", "status": "PASS"},
        {"check_id": "output_digest", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
        {"check_id": "deterministic_reverification", "status": "PASS"},
    ]

    input_refs = evidence.get("input_artifact_refs")
    if not isinstance(input_refs, list) or len(input_refs) != 2:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "exactly_two_direct_inputs" else c
            for c in checks
        ]

    if evidence.get("manifest_digest") != manifest_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "manifest_verification" else c
            for c in checks
        ]

    binding_status = evidence.get("cross_domain_lineage_binding_status")
    if binding_status == "PASS":
        for check_id, field in (
            ("candidate_identity_bound_on_pass", "candidate_identity_status"),
            ("model_identity_bound_on_pass", "model_identity_status"),
            ("parameter_set_identity_bound_on_pass", "parameter_set_identity_status"),
            (
                "config_patch_manifest_identity_bound_on_pass",
                "config_patch_manifest_identity_status",
            ),
            ("cross_domain_lineage_bound_on_pass", "cross_domain_lineage_status"),
        ):
            if evidence.get(field) != _IDENTITY_BOUND:
                checks = [
                    {**c, "status": "FAIL"} if c["check_id"] == check_id else c for c in checks
                ]

    structural_failures = [
        check
        for check in checks
        if check["status"] != "PASS"
        and check["check_id"]
        not in {
            "candidate_identity_bound_on_pass",
            "model_identity_bound_on_pass",
            "parameter_set_identity_bound_on_pass",
            "config_patch_manifest_identity_bound_on_pass",
            "cross_domain_lineage_bound_on_pass",
        }
    ]
    if structural_failures:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
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
        "verified_model_parameter_identity_binding_bundle_ref": (
            model_parameter_binding.bundle_dir.as_posix()
        ),
        "verified_config_patch_manifest_ref": config_patch.manifest_path.as_posix(),
        "verified_cross_domain_lineage_binding_status": binding_status,
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
    inputs: ComparisonConfigPatchManifestCrossDomainLineageBindingInputs,
) -> tuple[VerifiedModelParameterIdentityBindingBundle, VerifiedConfigPatchManifestInput]:
    """Verify exactly one Step-1 bundle and one ConfigPatch manifest input."""
    return (
        verify_model_parameter_identity_binding_bundle(
            inputs.model_parameter_identity_binding_bundle_dir
        ),
        verify_config_patch_manifest_input(inputs.config_patch_manifest_path),
    )


def reverify_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
    *,
    output_dir: Path | str,
) -> None:
    """Replay cross-domain lineage binding bundle without producer or upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            f"cross-domain lineage binding directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
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
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "SELF_VERIFICATION overall_status must be PASS"
        )

    manifest_digest = _compute_output_manifest_digest(evidence)
    if evidence.get("manifest_digest") != manifest_digest:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "manifest_digest mismatch on replay"
        )

    model_parameter_binding = verify_model_parameter_identity_binding_bundle(
        Path(str(evidence["model_parameter_identity_binding_bundle_ref"]))
    )
    if (
        evidence.get("model_parameter_identity_binding_digest")
        != model_parameter_binding.artifact_digest
    ):
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "model_parameter_identity_binding_digest mismatch on replay"
        )

    config_patch = verify_config_patch_manifest_input(
        Path(str(evidence["config_patch_manifest_ref"]))
    )
    if evidence.get("config_patch_manifest_digest") != config_patch.manifest_digest:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
            "config_patch_manifest_digest mismatch on replay"
        )


def produce_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
    *,
    inputs: ComparisonConfigPatchManifestCrossDomainLineageBindingInputs,
    output_dir: Path | str,
) -> ComparisonConfigPatchManifestCrossDomainLineageBindingResult:
    """Produce offline LEVEL_3 cross-domain lineage binding evidence."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        model_parameter_binding_dir=inputs.model_parameter_identity_binding_bundle_dir,
        config_patch_manifest_path=inputs.config_patch_manifest_path,
        output_dir=final_dir,
    )

    model_parameter_binding, config_patch = verify_binding_inputs(inputs)
    try:
        reverify_comparison_promotion_candidate_model_parameter_identity_binding_v1(
            output_dir=model_parameter_binding.bundle_dir
        )
    except ComparisonPromotionCandidateModelParameterIdentityBindingError as exc:
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(str(exc)) from exc

    evidence_body = build_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
        model_parameter_binding=model_parameter_binding,
        config_patch=config_patch,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
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
            serialize_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            evidence=finalized,
            model_parameter_binding=model_parameter_binding,
            config_patch=config_patch,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
            output_dir=staging
        )
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ComparisonConfigPatchManifestCrossDomainLineageBindingError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return ComparisonConfigPatchManifestCrossDomainLineageBindingResult(
        output_dir=final_dir,
        comparison_definition_id=str(finalized.get("comparison_definition_id", "")),
        artifact_id=str(finalized["artifact_id"]),
        evidence_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        cross_domain_lineage_binding_status=str(finalized["cross_domain_lineage_binding_status"]),
        candidate_identity_ref=str(finalized["candidate_identity_ref"]),
        config_patch_manifest_id=str(finalized["config_patch_manifest_id"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "AUTHORITY_LEVEL",
    "CONFIG_PATCH_CONTRACT_NAME",
    "CONFIG_PATCH_CONTRACT_VERSION",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "CROSS_DOMAIN_BINDING_AUTHORITY_INVARIANTS",
    "EVIDENCE_LEVEL",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "SELF_VERIFICATION_REL",
    "ComparisonConfigPatchManifestCrossDomainLineageBindingError",
    "ComparisonConfigPatchManifestCrossDomainLineageBindingInputs",
    "ComparisonConfigPatchManifestCrossDomainLineageBindingResult",
    "ResolvedCandidateLineage",
    "VerifiedConfigPatchManifestInput",
    "VerifiedModelParameterIdentityBindingBundle",
    "build_comparison_config_patch_manifest_cross_domain_lineage_binding_v1",
    "build_self_verification_v1",
    "produce_comparison_config_patch_manifest_cross_domain_lineage_binding_v1",
    "reverify_comparison_config_patch_manifest_cross_domain_lineage_binding_v1",
    "serialize_comparison_config_patch_manifest_cross_domain_lineage_binding_v1",
    "verify_binding_inputs",
    "verify_config_patch_manifest_input",
    "verify_model_parameter_identity_binding_bundle",
]
