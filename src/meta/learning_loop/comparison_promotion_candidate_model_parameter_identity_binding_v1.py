"""Offline LEVEL_3 model/parameter identity binding from verified eligibility evidence v1."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME as EXPERIMENT_IDENTITY_ARTIFACT_REL,
    ExperimentIdentityManifestError,
    validate_experiment_identity_manifest_v1,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.comparison_promotion_candidate_eligibility_evidence_v1 import (
    ARTIFACT_REL as ELIGIBILITY_ARTIFACT_REL,
    CONTRACT_NAME as ELIGIBILITY_CONTRACT_NAME,
    CONTRACT_VERSION as ELIGIBILITY_CONTRACT_VERSION,
    PRODUCER_VERSION as ELIGIBILITY_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as ELIGIBILITY_SELF_VERIFICATION_REL,
    ComparisonPromotionCandidateEligibilityEvidenceError,
    reverify_comparison_promotion_candidate_eligibility_evidence_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

CONTRACT_NAME = "comparison_promotion_candidate_model_parameter_identity_binding_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "comparison_promotion_candidate_model_parameter_identity_binding_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING_EVIDENCE_ONLY"
RECORD_KIND = "comparison_promotion_candidate_model_parameter_identity_binding_record"
INPUT_RELATION = "BINDS_VERIFIED_ELIGIBILITY_EVIDENCE_MODEL_PARAMETER_IDENTITY"
ARTIFACT_REL = "comparison_promotion_candidate_model_parameter_identity_binding_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".comparison_promotion_candidate_model_parameter_identity_binding_staging_"

MODEL_IDENTITY_SOURCE_CONTRACT = "experiment_identity_manifest_v1"
MODEL_IDENTITY_SOURCE_VERSION = "v1"
MODEL_IDENTITY_PROJECTION = "comparison_model_identity_projection_v1"
PARAMETER_SET_IDENTITY_SOURCE_CONTRACT = "experiment_identity_manifest_v1"
PARAMETER_SET_IDENTITY_SOURCE_VERSION = "v1"
PARAMETER_SET_IDENTITY_PROJECTION = "comparison_parameter_set_identity_projection_v1"

OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"

_VALID_BINDING_STATUS = frozenset({"PASS", "FAIL", "INCOMPLETE", "NOT_EVALUABLE"})
_CANDIDATE_IDENTITY_BOUND = "BOUND"
_IDENTITY_BOUND = "BOUND"
_IDENTITY_NOT_BOUND = "NOT_BOUND"
_CANDIDATE_SELECTION_NOT_SELECTED = "NOT_SELECTED"
_WINNER_SELECTION_NOT_SELECTED = "NOT_SELECTED"
_CANDIDATE_ACCEPTANCE_NOT_ACCEPTED = "NOT_ACCEPTED"

MODEL_PARAMETER_BINDING_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "model_parameter_binding_is_descriptive_only": True,
    "model_parameter_binding_does_not_select": True,
    "model_parameter_binding_does_not_choose_winner": True,
    "model_parameter_binding_does_not_accept": True,
    "model_parameter_binding_does_not_construct_promotion_candidate": True,
    "model_parameter_binding_does_not_execute_operational_filter": True,
    "model_parameter_binding_does_not_execute_policy": True,
    "model_parameter_binding_does_not_create_configpatch": True,
    "model_parameter_binding_does_not_modify_config": True,
    "model_parameter_binding_does_not_authorize_promotion": True,
    "model_parameter_binding_does_not_authorize_runtime": True,
    "model_parameter_binding_does_not_authorize_live": True,
    "model_parameter_binding_does_not_deploy": True,
    "model_parameter_binding_does_not_activate": True,
    "model_parameter_binding_does_not_create_order_intent": True,
    "model_parameter_binding_does_not_modify_trading_logic": True,
    "evidence_does_not_authorize_promotion": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_comparison_promotion_candidate_model_parameter_identity_binding": True,
    "evidence_does_not_authorize_promotion": True,
    "evidence_does_not_authorize_runtime": True,
    "binding_does_not_select_candidate": True,
    "binding_does_not_choose_winner": True,
    "binding_does_not_accept_candidate": True,
    "binding_does_not_construct_promotion_candidate": True,
    "binding_does_not_execute_operational_filter": True,
    "binding_does_not_execute_policy": True,
    "binding_does_not_create_configpatch": True,
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
    "comparison_promotion_candidate_model_parameter_identity_binding_self_verification_v1"
)


class ComparisonPromotionCandidateModelParameterIdentityBindingError(ValueError):
    """Fail-closed model/parameter identity binding error."""


@dataclass(frozen=True)
class VerifiedEligibilityEvidenceBundle:
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
class ResolvedModelParameterIdentity:
    model_identity_ref: str
    model_identity_digest: str
    model_identity_source_contract: str
    model_identity_source_version: str
    model_identity_source_projection: str
    parameter_set_identity_ref: str
    parameter_set_identity_digest: str
    parameter_set_identity_source_contract: str
    parameter_set_identity_source_version: str
    parameter_set_identity_source_projection: str
    experiment_identity_ref: str
    experiment_identity_digest: str
    experiment_identity_id: str


@dataclass(frozen=True)
class ComparisonPromotionCandidateModelParameterIdentityBindingInputs:
    eligibility_evidence_bundle_dir: Path


@dataclass(frozen=True)
class ComparisonPromotionCandidateModelParameterIdentityBindingResult:
    output_dir: Path
    comparison_definition_id: str
    artifact_id: str
    evidence_path: Path
    self_verification_path: Path
    manifest_path: Path
    model_parameter_identity_binding_status: str
    model_identity_status: str
    parameter_set_identity_status: str
    candidate_identity_ref: str
    model_identity_ref: str
    parameter_set_identity_ref: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            f"{label} must not be a symlink"
        )


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
                f"forbidden index key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            f"{label} must be a regular file: {path}"
        )


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            f"{label} must be a directory: {bundle_dir}"
        )


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            f"output directory already exists: {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "output directory must not be under /tmp"
        )


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, input_dir: Path, output_dir: Path) -> None:
    input_resolved = input_dir.resolve()
    output_resolved = output_dir.resolve()
    if input_resolved == output_resolved:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "output directory must not equal input directory"
        )
    if _path_is_under(output_resolved, input_resolved):
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "output directory must not be inside input directory"
        )
    if _path_is_under(input_resolved, output_resolved):
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
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
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "capabilities must be a list"
        )
    normalized: list[str] = []
    for item in capabilities:
        if not isinstance(item, str):
            raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
                "capabilities entries must be strings"
            )
        if item in _FORBIDDEN_CAPABILITIES:
            raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
                f"forbidden capability: {item}"
            )
        normalized.append(item)
    return sorted(normalized)


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if payload.get(key) is not expected:
            raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
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
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            f"{label} must be a JSON object"
        )
    return payload


def _validate_eligibility_input_payload(payload: Mapping[str, Any]) -> None:
    if payload.get("contract_name") != ELIGIBILITY_CONTRACT_NAME:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "upstream eligibility contract_name mismatch"
        )
    if payload.get("contract_version") != ELIGIBILITY_CONTRACT_VERSION:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "upstream eligibility contract_version mismatch"
        )


def _compute_model_identity_ref(identity_config: Mapping[str, Any]) -> str:
    strategy_name = identity_config.get("strategy_name")
    if not isinstance(strategy_name, str) or not strategy_name.strip():
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "strategy_name missing for model identity projection"
        )
    schema_version = identity_config.get("identity_schema_version")
    identity_domain = identity_config.get("identity_domain")
    if not isinstance(schema_version, str) or not schema_version.strip():
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "identity_schema_version missing for model identity projection"
        )
    if not isinstance(identity_domain, str) or not identity_domain.strip():
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "identity_domain missing for model identity projection"
        )
    payload = {
        "identity_projection": MODEL_IDENTITY_PROJECTION,
        "strategy_name": strategy_name,
        "identity_schema_version": schema_version,
        "identity_domain": identity_domain,
    }
    return compute_content_sha256(payload)


def _compute_parameter_set_identity_ref(identity_config: Mapping[str, Any]) -> str:
    param_sweeps = identity_config.get("param_sweeps")
    base_params = identity_config.get("base_params")
    if not isinstance(param_sweeps, list):
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "param_sweeps must be a list for parameter set identity projection"
        )
    if not isinstance(base_params, Mapping):
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "base_params must be an object for parameter set identity projection"
        )
    payload = {
        "identity_projection": PARAMETER_SET_IDENTITY_PROJECTION,
        "param_sweeps": deepcopy(param_sweeps),
        "base_params": deepcopy(dict(base_params)),
    }
    return compute_content_sha256(payload)


def _resolve_model_parameter_identity(
    *,
    experiment_identity_ref: str,
    experiment_identity_digest: str,
) -> tuple[ResolvedModelParameterIdentity | None, list[str]]:
    reason_codes: list[str] = []
    if not _non_empty_ref(experiment_identity_ref):
        reason_codes.append("EXPERIMENT_IDENTITY_MISSING")
        return None, reason_codes
    if not is_valid_sha256_hex(experiment_identity_digest):
        reason_codes.append("EXPERIMENT_IDENTITY_MISSING")
        return None, reason_codes

    manifest_path = Path(experiment_identity_ref) / EXPERIMENT_IDENTITY_ARTIFACT_REL
    if not manifest_path.is_file():
        reason_codes.append("EXPERIMENT_IDENTITY_INVALID")
        return None, reason_codes

    manifest = read_manifest(manifest_path)
    try:
        validate_experiment_identity_manifest_v1(manifest)
    except ExperimentIdentityManifestError:
        reason_codes.append("EXPERIMENT_IDENTITY_INVALID")
        return None, reason_codes

    integrity = manifest.get("integrity")
    if not isinstance(integrity, Mapping):
        reason_codes.append("EXPERIMENT_IDENTITY_INVALID")
        return None, reason_codes
    manifest_digest = integrity.get("content_sha256")
    if manifest_digest != experiment_identity_digest:
        reason_codes.append("EXPERIMENT_IDENTITY_DIGEST_MISMATCH")
        return None, reason_codes

    identity_config = manifest.get("identity_config")
    if not isinstance(identity_config, Mapping):
        reason_codes.append("EXPERIMENT_IDENTITY_INVALID")
        return None, reason_codes

    experiment_identity_id = manifest.get("experiment_identity_id")
    if not isinstance(experiment_identity_id, str) or not is_valid_sha256_hex(
        experiment_identity_id
    ):
        reason_codes.append("EXPERIMENT_IDENTITY_INVALID")
        return None, reason_codes

    try:
        model_identity_ref = _compute_model_identity_ref(identity_config)
        parameter_set_identity_ref = _compute_parameter_set_identity_ref(identity_config)
    except ComparisonPromotionCandidateModelParameterIdentityBindingError as exc:
        message = str(exc)
        if "strategy_name" in message:
            reason_codes.append("MODEL_IDENTITY_MISSING")
        elif "param_sweeps" in message or "base_params" in message:
            reason_codes.append("PARAMETER_SET_IDENTITY_MISSING")
        elif "ambiguous" in message:
            reason_codes.append("PARAMETER_SET_IDENTITY_AMBIGUOUS")
        else:
            reason_codes.append("EXPERIMENT_IDENTITY_INVALID")
        return None, reason_codes

    if not param_sweeps_present(identity_config):
        reason_codes.append("PARAMETER_SET_IDENTITY_MISSING")
        return None, reason_codes

    reason_codes.extend(
        [
            "MODEL_IDENTITY_BOUND",
            "PARAMETER_SET_IDENTITY_BOUND",
            "EXPERIMENT_LINEAGE_MATCH",
        ]
    )
    return (
        ResolvedModelParameterIdentity(
            model_identity_ref=model_identity_ref,
            model_identity_digest=model_identity_ref,
            model_identity_source_contract=MODEL_IDENTITY_SOURCE_CONTRACT,
            model_identity_source_version=MODEL_IDENTITY_SOURCE_VERSION,
            model_identity_source_projection=MODEL_IDENTITY_PROJECTION,
            parameter_set_identity_ref=parameter_set_identity_ref,
            parameter_set_identity_digest=parameter_set_identity_ref,
            parameter_set_identity_source_contract=PARAMETER_SET_IDENTITY_SOURCE_CONTRACT,
            parameter_set_identity_source_version=PARAMETER_SET_IDENTITY_SOURCE_VERSION,
            parameter_set_identity_source_projection=PARAMETER_SET_IDENTITY_PROJECTION,
            experiment_identity_ref=experiment_identity_ref,
            experiment_identity_digest=experiment_identity_digest,
            experiment_identity_id=experiment_identity_id,
        ),
        reason_codes,
    )


def param_sweeps_present(identity_config: Mapping[str, Any]) -> bool:
    param_sweeps = identity_config.get("param_sweeps")
    base_params = identity_config.get("base_params")
    if isinstance(param_sweeps, list) and len(param_sweeps) > 0:
        return True
    if isinstance(base_params, Mapping) and len(base_params) > 0:
        return True
    return False


def verify_eligibility_evidence_bundle(
    bundle_dir: Path | str,
) -> VerifiedEligibilityEvidenceBundle:
    """Fail-closed verification of exactly one eligibility evidence bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="eligibility evidence bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            f"eligibility evidence MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = path / ELIGIBILITY_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ELIGIBILITY_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    _validate_eligibility_input_payload(payload)

    self_payload = _load_self_verification(
        path, rel=ELIGIBILITY_SELF_VERIFICATION_REL, label=ELIGIBILITY_SELF_VERIFICATION_REL
    )
    if self_payload.get("overall_status") != "PASS":
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "upstream eligibility SELF_VERIFICATION overall_status must be PASS"
        )

    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "eligibility evidence integrity must be an object"
        )
    artifact_digest = integrity.get("content_sha256")
    if not isinstance(artifact_digest, str) or not is_valid_sha256_hex(artifact_digest):
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "eligibility evidence integrity.content_sha256 invalid"
        )

    parent_refs_raw = payload.get("parent_artifact_refs")
    if not isinstance(parent_refs_raw, list):
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "eligibility evidence parent_artifact_refs must be a list"
        )
    parent_artifact_refs = tuple(
        dict(item) for item in parent_refs_raw if isinstance(item, Mapping)
    )

    return VerifiedEligibilityEvidenceBundle(
        bundle_dir=path.resolve(),
        contract_name=ELIGIBILITY_CONTRACT_NAME,
        contract_version=ELIGIBILITY_CONTRACT_VERSION,
        producer_version=ELIGIBILITY_PRODUCER_VERSION,
        artifact_ref=ELIGIBILITY_ARTIFACT_REL,
        artifact_digest=artifact_digest,
        manifest_digest=_manifest_file_digest(path),
        evidence_level=str(payload.get("evidence_level", "")),
        parent_artifact_refs=parent_artifact_refs,
        evidence_payload=dict(payload),
    )


def _evaluate_model_parameter_binding(
    eligibility: Mapping[str, Any],
    resolved: ResolvedModelParameterIdentity | None,
    resolution_reason_codes: list[str],
) -> tuple[str, str, str, str, list[str]]:
    reason_codes = list(resolution_reason_codes)

    if eligibility.get("candidate_selection_status") != _CANDIDATE_SELECTION_NOT_SELECTED:
        reason_codes.append("CANDIDATE_SELECTION_DETECTED")
    if eligibility.get("winner_selection_status") != _WINNER_SELECTION_NOT_SELECTED:
        reason_codes.append("WINNER_SELECTION_DETECTED")
    if eligibility.get("candidate_acceptance_status") != _CANDIDATE_ACCEPTANCE_NOT_ACCEPTED:
        reason_codes.append("CANDIDATE_ACCEPTANCE_DETECTED")

    candidate_identity_ref = str(eligibility.get("candidate_identity_ref", ""))
    candidate_identity_digest = str(eligibility.get("candidate_identity_digest", ""))
    if not _non_empty_ref(candidate_identity_ref):
        reason_codes.append("CANDIDATE_IDENTITY_NOT_BOUND")
    if not is_valid_sha256_hex(candidate_identity_digest):
        reason_codes.append("CANDIDATE_DIGEST_MISMATCH")

    experiment_ref = str(eligibility.get("experiment_identity_ref", ""))
    experiment_digest = str(eligibility.get("experiment_identity_digest", ""))
    if not _non_empty_ref(experiment_ref) or not is_valid_sha256_hex(experiment_digest):
        reason_codes.append("EXPERIMENT_IDENTITY_MISSING")
    dataset_ref = str(eligibility.get("dataset_identity_ref", ""))
    dataset_digest = str(eligibility.get("dataset_identity_digest", ""))
    if not _non_empty_ref(dataset_ref) or not is_valid_sha256_hex(dataset_digest):
        reason_codes.append("LINEAGE_INCOMPLETE")

    comparison_ref = str(eligibility.get("comparison_definition_ref", ""))
    comparison_digest = str(
        eligibility.get("comparison_definition_digest")
        or eligibility.get("comparison_definition_id", "")
    )
    if not _non_empty_ref(comparison_ref) or not is_valid_sha256_hex(comparison_digest):
        reason_codes.append("COMPARISON_LINEAGE_MISMATCH")

    upstream_status = str(eligibility.get("candidate_eligibility_status", ""))
    if upstream_status == "NOT_EVALUABLE":
        return (
            "NOT_EVALUABLE",
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
            _sorted_reason_codes(reason_codes + ["UPSTREAM_ELIGIBILITY_INCOMPLETE"]),
        )
    if upstream_status == "FAIL":
        return (
            "FAIL",
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _sorted_reason_codes(reason_codes + ["UPSTREAM_ELIGIBILITY_FAIL"]),
        )

    if resolved is None:
        return (
            "FAIL",
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _IDENTITY_NOT_BOUND,
            _sorted_reason_codes(reason_codes),
        )

    model_status = _IDENTITY_BOUND
    parameter_status = _IDENTITY_BOUND
    binding_status = "PASS"
    if "MODEL_IDENTITY_MISSING" in reason_codes or "MODEL_IDENTITY_AMBIGUOUS" in reason_codes:
        model_status = _IDENTITY_NOT_BOUND
        binding_status = "FAIL"
    if (
        "PARAMETER_SET_IDENTITY_MISSING" in reason_codes
        or "PARAMETER_SET_IDENTITY_AMBIGUOUS" in reason_codes
    ):
        parameter_status = _IDENTITY_NOT_BOUND
        binding_status = "FAIL"
    if any(
        code in reason_codes
        for code in (
            "CANDIDATE_IDENTITY_NOT_BOUND",
            "CANDIDATE_DIGEST_MISMATCH",
            "EXPERIMENT_IDENTITY_DIGEST_MISMATCH",
            "EXPERIMENT_IDENTITY_INVALID",
            "CANDIDATE_SELECTION_DETECTED",
            "WINNER_SELECTION_DETECTED",
            "CANDIDATE_ACCEPTANCE_DETECTED",
            "COMPARISON_LINEAGE_MISMATCH",
            "LINEAGE_INCOMPLETE",
        )
    ):
        binding_status = "FAIL"
        model_status = _IDENTITY_NOT_BOUND
        parameter_status = _IDENTITY_NOT_BOUND

    if binding_status == "PASS":
        reason_codes.append("MODEL_PARAMETER_IDENTITY_BINDING_COMPLETE")

    return (
        binding_status,
        model_status,
        parameter_status,
        _CANDIDATE_IDENTITY_BOUND,
        _sorted_reason_codes(reason_codes),
    )


def _input_artifact_ref_mapping(
    *,
    bundle: VerifiedEligibilityEvidenceBundle,
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


def build_comparison_promotion_candidate_model_parameter_identity_binding_v1(
    *,
    eligibility: VerifiedEligibilityEvidenceBundle,
) -> dict[str, Any]:
    evidence = eligibility.evidence_payload
    experiment_ref = str(evidence.get("experiment_identity_ref", ""))
    experiment_digest = str(evidence.get("experiment_identity_digest", ""))
    resolved, resolution_codes = _resolve_model_parameter_identity(
        experiment_identity_ref=experiment_ref,
        experiment_identity_digest=experiment_digest,
    )
    (
        binding_status,
        model_identity_status,
        parameter_set_identity_status,
        candidate_identity_status,
        reason_codes,
    ) = _evaluate_model_parameter_binding(evidence, resolved, resolution_codes)

    input_ref = _input_artifact_ref_mapping(bundle=eligibility)
    input_refs = [input_ref]
    parent_artifact_refs = list(eligibility.parent_artifact_refs)
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
        "is_comparison_promotion_candidate_model_parameter_identity_binding": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "binding_does_not_select_candidate": True,
        "binding_does_not_choose_winner": True,
        "binding_does_not_accept_candidate": True,
        "binding_does_not_construct_promotion_candidate": True,
        "binding_does_not_execute_operational_filter": True,
        "binding_does_not_execute_policy": True,
        "binding_does_not_create_configpatch": True,
        "binding_does_not_modify_config": True,
        "binding_does_not_authorize_promotion": True,
        "binding_does_not_authorize_runtime": True,
        "binding_does_not_authorize_live": True,
        "binding_does_not_deploy": True,
        "binding_does_not_activate": True,
        "binding_does_not_create_order_intent": True,
        "binding_does_not_modify_trading_logic": True,
        "model_parameter_binding_authority_invariants": dict(
            MODEL_PARAMETER_BINDING_AUTHORITY_INVARIANTS
        ),
        "eligibility_evidence_bundle_ref": eligibility.bundle_dir.as_posix(),
        "eligibility_evidence_artifact_ref": eligibility.artifact_ref,
        "eligibility_evidence_digest": eligibility.artifact_digest,
        "eligibility_evidence_manifest_digest": eligibility.manifest_digest,
        "candidate_identity_binding_bundle_ref": str(
            evidence.get("candidate_identity_binding_bundle_ref", "")
        ),
        "candidate_identity_binding_digest": str(
            evidence.get("candidate_identity_binding_digest", "")
        ),
        "candidate_identity_ref": str(evidence.get("candidate_identity_ref", "")),
        "candidate_identity_digest": str(evidence.get("candidate_identity_digest", "")),
        "candidate_identity_source_type": str(evidence.get("candidate_identity_source_type", "")),
        "candidate_identity_status": candidate_identity_status,
        "candidate_selection_status": _CANDIDATE_SELECTION_NOT_SELECTED,
        "winner_selection_status": _WINNER_SELECTION_NOT_SELECTED,
        "candidate_acceptance_status": _CANDIDATE_ACCEPTANCE_NOT_ACCEPTED,
        "promotion_candidate_constructed": False,
        "operational_filter_executed": False,
        "promotion_policy_executed": False,
        "configpatch_created": False,
        "experiment_identity_ref": experiment_ref,
        "experiment_identity_digest": experiment_digest,
        "dataset_identity_ref": str(evidence.get("dataset_identity_ref", "")),
        "dataset_identity_digest": str(evidence.get("dataset_identity_digest", "")),
        "comparison_definition_ref": str(evidence.get("comparison_definition_ref", "")),
        "comparison_definition_digest": str(
            evidence.get("comparison_definition_digest")
            or evidence.get("comparison_definition_id", "")
        ),
        "comparison_definition_id": str(evidence.get("comparison_definition_id", "")),
        "comparison_completion_ref": str(evidence.get("comparison_completion_ref", "")),
        "comparison_completion_digest": str(evidence.get("comparison_completion_digest", "")),
        "research_validity_ref": str(evidence.get("research_validity_ref", "")),
        "research_validity_digest": str(evidence.get("research_validity_digest", "")),
        "comparison_checkpoint_ref": str(evidence.get("comparison_checkpoint_ref", "")),
        "comparison_checkpoint_digest": str(evidence.get("comparison_checkpoint_digest", "")),
        "model_identity_status": model_identity_status,
        "parameter_set_identity_status": parameter_set_identity_status,
        "model_parameter_identity_binding_status": binding_status,
        "model_parameter_identity_binding_reason_codes": reason_codes,
        "upstream_contract_name": eligibility.contract_name,
        "upstream_contract_version": eligibility.contract_version,
        "upstream_producer_version": eligibility.producer_version,
        "upstream_candidate_eligibility_status": str(
            evidence.get("candidate_eligibility_status", "")
        ),
        "input_artifact_refs": input_refs,
        "parent_artifact_refs": parent_artifact_refs,
        "input_digest": "",
        "output_digest": "",
        "manifest_digest": "",
    }

    if resolved is not None:
        payload.update(
            {
                "model_identity_ref": resolved.model_identity_ref,
                "model_identity_digest": resolved.model_identity_digest,
                "model_identity_source_contract": resolved.model_identity_source_contract,
                "model_identity_source_version": resolved.model_identity_source_version,
                "model_identity_source_projection": resolved.model_identity_source_projection,
                "parameter_set_identity_ref": resolved.parameter_set_identity_ref,
                "parameter_set_identity_digest": resolved.parameter_set_identity_digest,
                "parameter_set_identity_source_contract": resolved.parameter_set_identity_source_contract,
                "parameter_set_identity_source_version": resolved.parameter_set_identity_source_version,
                "parameter_set_identity_source_projection": resolved.parameter_set_identity_source_projection,
                "experiment_identity_id": resolved.experiment_identity_id,
            }
        )

    metric_ref = evidence.get("comparison_metric_input_ref")
    metric_digest = evidence.get("comparison_metric_input_digest")
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


def serialize_comparison_promotion_candidate_model_parameter_identity_binding_v1(
    evidence: Mapping[str, Any],
) -> str:
    _reject_forbidden_index_keys(evidence)
    _validate_non_authorizing_flags(evidence)
    _validate_capabilities(evidence.get("capabilities"))
    binding_status = evidence.get("model_parameter_identity_binding_status")
    if binding_status not in _VALID_BINDING_STATUS:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            f"model_parameter_identity_binding_status must be one of {sorted(_VALID_BINDING_STATUS)}"
        )
    if evidence.get("candidate_selection_status") != _CANDIDATE_SELECTION_NOT_SELECTED:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "candidate_selection_status must be NOT_SELECTED"
        )
    if evidence.get("winner_selection_status") != _WINNER_SELECTION_NOT_SELECTED:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "winner_selection_status must be NOT_SELECTED"
        )
    if evidence.get("candidate_acceptance_status") != _CANDIDATE_ACCEPTANCE_NOT_ACCEPTED:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "candidate_acceptance_status must be NOT_ACCEPTED"
        )
    if evidence.get("promotion_candidate_constructed") is not False:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "promotion_candidate_constructed must be false"
        )
    reason_codes = evidence.get("model_parameter_identity_binding_reason_codes")
    if isinstance(reason_codes, list) and reason_codes != sorted(reason_codes):
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "model_parameter_identity_binding_reason_codes must be sorted deterministically"
        )
    return deterministic_json_dumps(evidence)


def _evidence_bytes_for_manifest_digest(evidence: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in evidence.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        body
    ).encode("utf-8")


def _compute_output_manifest_digest(evidence: Mapping[str, Any]) -> str:
    return hashlib.sha256(_evidence_bytes_for_manifest_digest(evidence)).hexdigest()


def _validate_evidence_integrity(evidence: Mapping[str, Any]) -> None:
    if evidence.get("contract_name") != CONTRACT_NAME:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "contract_name mismatch"
        )
    if evidence.get("contract_version") != CONTRACT_VERSION:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "contract_version mismatch"
        )
    integrity = evidence.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "integrity must be an object"
        )
    expected = compute_content_sha256(_integrity_body(evidence))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "integrity.content_sha256 mismatch"
        )
    output_digest = evidence.get("output_digest")
    if output_digest != _compute_output_digest(evidence):
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "output_digest mismatch"
        )
    if evidence.get("artifact_id") != output_digest:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "artifact_id must equal output_digest"
        )


def build_self_verification_v1(
    *,
    evidence: Mapping[str, Any],
    eligibility: VerifiedEligibilityEvidenceBundle,
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_one_direct_input", "status": "PASS"},
        {"check_id": "eligibility_contract_and_version", "status": "PASS"},
        {"check_id": "input_manifest_verified", "status": "PASS"},
        {"check_id": "eligibility_self_verification_pass", "status": "PASS"},
        {"check_id": "model_identity_bound_on_pass", "status": "PASS"},
        {"check_id": "parameter_set_identity_bound_on_pass", "status": "PASS"},
        {"check_id": "no_candidate_selection", "status": "PASS"},
        {"check_id": "no_winner_selection", "status": "PASS"},
        {"check_id": "no_candidate_acceptance", "status": "PASS"},
        {"check_id": "no_promotion_candidate_construction", "status": "PASS"},
        {"check_id": "non_authorizing_semantics", "status": "PASS"},
        {"check_id": "forbidden_capabilities_absent", "status": "PASS"},
        {"check_id": "no_configpatch_semantics", "status": "PASS"},
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

    binding_status = evidence.get("model_parameter_identity_binding_status")
    if binding_status == "PASS":
        if evidence.get("model_identity_status") != _IDENTITY_BOUND:
            checks = [
                {**c, "status": "FAIL"} if c["check_id"] == "model_identity_bound_on_pass" else c
                for c in checks
            ]
        if evidence.get("parameter_set_identity_status") != _IDENTITY_BOUND:
            checks = [
                {
                    **c,
                    "status": "FAIL",
                }
                if c["check_id"] == "parameter_set_identity_bound_on_pass"
                else c
                for c in checks
            ]
        if not _non_empty_ref(evidence.get("model_identity_ref")):
            checks = [
                {**c, "status": "FAIL"} if c["check_id"] == "model_identity_bound_on_pass" else c
                for c in checks
            ]
        if not _non_empty_ref(evidence.get("parameter_set_identity_ref")):
            checks = [
                {
                    **c,
                    "status": "FAIL",
                }
                if c["check_id"] == "parameter_set_identity_bound_on_pass"
                else c
                for c in checks
            ]

    if evidence.get("candidate_selection_status") != _CANDIDATE_SELECTION_NOT_SELECTED:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "no_candidate_selection" else c
            for c in checks
        ]

    structural_failures = [
        check
        for check in checks
        if check["status"] != "PASS"
        and check["check_id"]
        not in {
            "model_identity_bound_on_pass",
            "parameter_set_identity_bound_on_pass",
        }
    ]
    if structural_failures:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
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
        "verified_eligibility_evidence_bundle_ref": eligibility.bundle_dir.as_posix(),
        "verified_model_parameter_identity_binding_status": binding_status,
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
    inputs: ComparisonPromotionCandidateModelParameterIdentityBindingInputs,
) -> VerifiedEligibilityEvidenceBundle:
    """Verify exactly one eligibility evidence bundle."""
    return verify_eligibility_evidence_bundle(inputs.eligibility_evidence_bundle_dir)


def reverify_comparison_promotion_candidate_model_parameter_identity_binding_v1(
    *,
    output_dir: Path | str,
) -> None:
    """Replay model/parameter identity binding bundle without producer or upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            f"model/parameter identity binding directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
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
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "SELF_VERIFICATION overall_status must be PASS"
        )

    manifest_digest = _compute_output_manifest_digest(evidence)
    if evidence.get("manifest_digest") != manifest_digest:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "manifest_digest mismatch on replay"
        )

    eligibility = verify_eligibility_evidence_bundle(
        Path(str(evidence["eligibility_evidence_bundle_ref"]))
    )
    if evidence.get("eligibility_evidence_digest") != eligibility.artifact_digest:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
            "eligibility_evidence_digest mismatch on replay"
        )


def produce_comparison_promotion_candidate_model_parameter_identity_binding_v1(
    *,
    inputs: ComparisonPromotionCandidateModelParameterIdentityBindingInputs,
    output_dir: Path | str,
) -> ComparisonPromotionCandidateModelParameterIdentityBindingResult:
    """Produce offline LEVEL_3 model/parameter identity binding from eligibility evidence."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        input_dir=inputs.eligibility_evidence_bundle_dir,
        output_dir=final_dir,
    )

    eligibility = verify_binding_inputs(inputs)
    try:
        reverify_comparison_promotion_candidate_eligibility_evidence_v1(
            output_dir=eligibility.bundle_dir
        )
    except ComparisonPromotionCandidateEligibilityEvidenceError as exc:
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(str(exc)) from exc

    evidence_body = build_comparison_promotion_candidate_model_parameter_identity_binding_v1(
        eligibility=eligibility,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
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
            serialize_comparison_promotion_candidate_model_parameter_identity_binding_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            evidence=finalized,
            eligibility=eligibility,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_comparison_promotion_candidate_model_parameter_identity_binding_v1(
            output_dir=staging
        )
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ComparisonPromotionCandidateModelParameterIdentityBindingError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return ComparisonPromotionCandidateModelParameterIdentityBindingResult(
        output_dir=final_dir,
        comparison_definition_id=str(finalized.get("comparison_definition_id", "")),
        artifact_id=str(finalized["artifact_id"]),
        evidence_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        model_parameter_identity_binding_status=str(
            finalized["model_parameter_identity_binding_status"]
        ),
        model_identity_status=str(finalized["model_identity_status"]),
        parameter_set_identity_status=str(finalized["parameter_set_identity_status"]),
        candidate_identity_ref=str(finalized["candidate_identity_ref"]),
        model_identity_ref=str(finalized.get("model_identity_ref", "")),
        parameter_set_identity_ref=str(finalized.get("parameter_set_identity_ref", "")),
    )


compute_model_identity_ref = _compute_model_identity_ref
compute_parameter_set_identity_ref = _compute_parameter_set_identity_ref

__all__ = [
    "ARTIFACT_REL",
    "AUTHORITY_LEVEL",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "EVIDENCE_LEVEL",
    "MANIFEST_FILENAME",
    "MODEL_IDENTITY_PROJECTION",
    "MODEL_IDENTITY_SOURCE_CONTRACT",
    "MODEL_IDENTITY_SOURCE_VERSION",
    "MODEL_PARAMETER_BINDING_AUTHORITY_INVARIANTS",
    "PARAMETER_SET_IDENTITY_PROJECTION",
    "PARAMETER_SET_IDENTITY_SOURCE_CONTRACT",
    "PARAMETER_SET_IDENTITY_SOURCE_VERSION",
    "PRODUCER_VERSION",
    "SELF_VERIFICATION_REL",
    "ComparisonPromotionCandidateModelParameterIdentityBindingError",
    "ComparisonPromotionCandidateModelParameterIdentityBindingInputs",
    "ComparisonPromotionCandidateModelParameterIdentityBindingResult",
    "ResolvedModelParameterIdentity",
    "VerifiedEligibilityEvidenceBundle",
    "build_comparison_promotion_candidate_model_parameter_identity_binding_v1",
    "build_self_verification_v1",
    "compute_model_identity_ref",
    "compute_parameter_set_identity_ref",
    "param_sweeps_present",
    "produce_comparison_promotion_candidate_model_parameter_identity_binding_v1",
    "reverify_comparison_promotion_candidate_model_parameter_identity_binding_v1",
    "serialize_comparison_promotion_candidate_model_parameter_identity_binding_v1",
    "verify_binding_inputs",
    "verify_eligibility_evidence_bundle",
]
