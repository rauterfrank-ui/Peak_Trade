"""Offline LEVEL_3 versioned strategy/model/parameter artifact owner v1."""

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
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME as EXPERIMENT_IDENTITY_ARTIFACT_REL,
    ExperimentIdentityManifestError,
    validate_experiment_identity_manifest_v1,
)
from src.meta.learning_loop.ai_promotion_assessment_v1 import (
    ARTIFACT_REL as AI_ASSESSMENT_ARTIFACT_REL,
    CONTRACT_NAME as AI_ASSESSMENT_CONTRACT_NAME,
    CONTRACT_VERSION as AI_ASSESSMENT_CONTRACT_VERSION,
    PRODUCER_VERSION as AI_ASSESSMENT_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as AI_ASSESSMENT_SELF_VERIFICATION_REL,
    AiPromotionAssessmentError,
    reverify_ai_promotion_assessment_v1,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.comparison_promotion_candidate_identity_binding_v1 import (
    ARTIFACT_REL as CANDIDATE_IDENTITY_ARTIFACT_REL,
    CONTRACT_NAME as CANDIDATE_IDENTITY_CONTRACT_NAME,
    CONTRACT_VERSION as CANDIDATE_IDENTITY_CONTRACT_VERSION,
    PRODUCER_VERSION as CANDIDATE_IDENTITY_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as CANDIDATE_IDENTITY_SELF_VERIFICATION_REL,
    ComparisonPromotionCandidateIdentityBindingError,
    reverify_comparison_promotion_candidate_identity_binding_v1,
)
from src.meta.learning_loop.comparison_promotion_candidate_model_parameter_identity_binding_v1 import (
    ARTIFACT_REL as MODEL_PARAMETER_ARTIFACT_REL,
    CONTRACT_NAME as MODEL_PARAMETER_CONTRACT_NAME,
    CONTRACT_VERSION as MODEL_PARAMETER_CONTRACT_VERSION,
    PRODUCER_VERSION as MODEL_PARAMETER_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as MODEL_PARAMETER_SELF_VERIFICATION_REL,
    ComparisonPromotionCandidateModelParameterIdentityBindingError,
    reverify_comparison_promotion_candidate_model_parameter_identity_binding_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

CONTRACT_NAME = "versioned_strategy_model_parameter_artifact_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "versioned_strategy_model_parameter_artifact_v1"
CREATION_CONTRACT_VERSION = "versioned_strategy_model_parameter_artifact_v1"
ARTIFACT_SCHEMA_VERSION = "v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "versioned_strategy_model_parameter_artifact_record"
INPUT_RELATION = "BINDS_VERIFIED_STRATEGY_MODEL_PARAMETER_IDENTITIES_V1"
ARTIFACT_REL = "versioned_strategy_model_parameter_artifact_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".versioned_strategy_model_parameter_artifact_staging_"

STRATEGY_IDENTITY_SOURCE_CONTRACT = "experiment_identity_manifest_v1"
STRATEGY_IDENTITY_SOURCE_VERSION = "v1"

OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"

_VALID_BINDING_STATUS = frozenset({"PASS", "FAIL", "INCOMPLETE", "NOT_EVALUABLE"})
_IDENTITY_BOUND = "BOUND"

VERSIONED_ARTIFACT_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "artifact_is_descriptive_only": True,
    "artifact_does_not_execute_strategy": True,
    "artifact_does_not_infer_model": True,
    "artifact_does_not_optimize_parameters": True,
    "artifact_does_not_authorize_promotion": True,
    "artifact_does_not_construct_promotion_candidate": True,
    "artifact_does_not_create_configpatch": True,
    "artifact_does_not_modify_config": True,
    "artifact_does_not_authorize_runtime": True,
    "artifact_does_not_authorize_live": True,
    "artifact_does_not_create_order_intent": True,
    "artifact_is_immutable": True,
    "artifact_is_offline_only": True,
    "evidence_does_not_authorize_promotion": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_versioned_strategy_model_parameter_artifact": True,
    "artifact_offline_only": True,
    "artifact_immutable": True,
    "evidence_does_not_authorize_promotion": True,
    "evidence_does_not_authorize_runtime": True,
    "artifact_does_not_execute_strategy": True,
    "artifact_does_not_infer_model": True,
    "artifact_does_not_optimize_parameters": True,
    "artifact_does_not_modify_parameters": True,
    "artifact_does_not_authorize_promotion": True,
    "artifact_does_not_construct_promotion_candidate": True,
    "artifact_does_not_create_configpatch": True,
    "artifact_does_not_modify_configpatch": True,
    "artifact_does_not_apply_configpatch": True,
    "artifact_does_not_accept_configpatch": True,
    "artifact_does_not_modify_config": True,
    "artifact_does_not_authorize_runtime": True,
    "artifact_does_not_authorize_live": True,
    "artifact_does_not_create_order_intent": True,
    "strategy_executed": False,
    "signals_computed": False,
    "backtest_executed": False,
    "model_trained": False,
    "model_inference_executed": False,
    "parameters_optimized": False,
    "parameters_modified": False,
    "promotion_policy_executed": False,
    "promotion_authorized": False,
    "promotion_candidate_constructed": False,
    "candidate_selected": False,
    "candidate_accepted": False,
    "configpatch_created": False,
    "configpatch_modified": False,
    "configpatch_applied": False,
    "configpatch_accepted": False,
    "promotion_consumers_changed": False,
    "runtime_configuration_created": False,
    "runtime_authorized": False,
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
    "network_side_effect_created": False,
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

_SELF_VERIFICATION_SCHEMA_VERSION = (
    "versioned_strategy_model_parameter_artifact_self_verification_v1"
)

_TRANSITIVE_LINEAGE_FIELDS: tuple[str, ...] = (
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
    "policy_input_evidence_bundle_ref",
    "policy_input_evidence_artifact_ref",
    "policy_input_evidence_digest",
    "policy_input_evidence_manifest_digest",
    "promotion_policy_input_evidence_status",
    "policy_input_binding_bundle_ref",
    "policy_input_binding_digest",
    "policy_input_binding_manifest_digest",
    "policy_decision_ref",
    "policy_decision_digest",
    "policy_decision_manifest_digest",
    "config_patch_manifest_ref",
    "config_patch_manifest_digest",
    "config_patch_manifest_id",
    "config_patch_contract_name",
    "config_patch_contract_version",
    "cross_domain_lineage_binding_bundle_ref",
    "cross_domain_lineage_binding_digest",
    "candidate_lineage_manifest_id",
    "candidate_lineage_digest",
    "config_patch_lineage_manifest_ref",
    "comparison_checkpoint_ref",
    "comparison_checkpoint_digest",
    "comparison_metric_input_ref",
    "comparison_metric_input_digest",
    "eligibility_evidence_ref",
    "eligibility_evidence_digest",
)


class VersionedStrategyModelParameterArtifactError(ValueError):
    """Fail-closed versioned strategy/model/parameter artifact error."""


@dataclass(frozen=True)
class VerifiedCandidateIdentityBindingBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    evidence_payload: dict[str, Any]


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
class VerifiedAiPromotionAssessmentBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    evidence_payload: dict[str, Any]


@dataclass(frozen=True)
class VersionedStrategyModelParameterArtifactInputs:
    candidate_identity_binding_bundle_dir: Path
    model_parameter_identity_binding_bundle_dir: Path
    ai_promotion_assessment_bundle_dir: Path | None = None


@dataclass(frozen=True)
class VersionedStrategyModelParameterArtifactResult:
    output_dir: Path
    comparison_definition_id: str
    artifact_id: str
    artifact_path: Path
    self_verification_path: Path
    manifest_path: Path
    versioned_artifact_binding_status: str
    strategy_identity_ref: str
    model_identity_ref: str
    parameter_set_identity_ref: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise VersionedStrategyModelParameterArtifactError(f"{label} must not be a symlink")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise VersionedStrategyModelParameterArtifactError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise VersionedStrategyModelParameterArtifactError(
            f"{label} must be a regular file: {path}"
        )


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise VersionedStrategyModelParameterArtifactError(
            f"{label} must be a directory: {bundle_dir}"
        )


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise VersionedStrategyModelParameterArtifactError(
            f"output directory already exists: {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise VersionedStrategyModelParameterArtifactError(
            "output directory must not be under /tmp"
        )


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, input_dirs: tuple[Path, ...], output_dir: Path) -> None:
    output_res = output_dir.resolve()
    for input_dir in input_dirs:
        input_res = input_dir.resolve()
        if output_res == input_res:
            raise VersionedStrategyModelParameterArtifactError(
                "output directory must not equal input path"
            )
        if _path_is_under(output_res, input_res):
            raise VersionedStrategyModelParameterArtifactError(
                "output directory must not be inside input path"
            )
        if _path_is_under(input_res, output_res):
            raise VersionedStrategyModelParameterArtifactError(
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
        raise VersionedStrategyModelParameterArtifactError("capabilities must be a list")
    normalized: list[str] = []
    for item in capabilities:
        if not isinstance(item, str):
            raise VersionedStrategyModelParameterArtifactError(
                "capabilities entries must be strings"
            )
        if item in _FORBIDDEN_CAPABILITIES:
            raise VersionedStrategyModelParameterArtifactError(f"forbidden capability: {item}")
        normalized.append(item)
    return sorted(normalized)


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if payload.get(key) is not expected:
            raise VersionedStrategyModelParameterArtifactError(f"{key} must be {expected!r}")


def _load_self_verification(bundle_dir: Path, *, rel: str, label: str) -> dict[str, Any]:
    path = bundle_dir / rel
    _validate_regular_file(path, label=label)
    payload = read_manifest(path)
    if not isinstance(payload, dict):
        raise VersionedStrategyModelParameterArtifactError(f"{label} must be a JSON object")
    if payload.get("overall_status") != "PASS":
        raise VersionedStrategyModelParameterArtifactError(f"{label} overall_status must be PASS")
    return payload


def _artifact_digest_from_payload(payload: Mapping[str, Any]) -> str:
    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping):
        raise VersionedStrategyModelParameterArtifactError("integrity must be an object")
    digest = integrity.get("content_sha256")
    if not isinstance(digest, str) or not is_valid_sha256_hex(digest):
        raise VersionedStrategyModelParameterArtifactError("integrity.content_sha256 invalid")
    return digest


def _non_empty_ref(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normalized_comparison_definition_id(payload: Mapping[str, Any]) -> str:
    for key in (
        "comparison_definition_id",
        "comparison_definition_ref",
        "comparison_definition_digest",
    ):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _resolve_strategy_version(*, experiment_identity_ref: str) -> str:
    manifest_path = Path(experiment_identity_ref) / EXPERIMENT_IDENTITY_ARTIFACT_REL
    if not manifest_path.is_file():
        raise VersionedStrategyModelParameterArtifactError(
            "experiment identity manifest missing for strategy version resolution"
        )
    manifest = read_manifest(manifest_path)
    try:
        validate_experiment_identity_manifest_v1(manifest)
    except ExperimentIdentityManifestError as exc:
        raise VersionedStrategyModelParameterArtifactError(str(exc)) from exc
    identity_config = manifest.get("identity_config")
    if isinstance(identity_config, Mapping):
        version = identity_config.get("identity_schema_version")
        if isinstance(version, str) and version.strip():
            return version.strip()
    version = manifest.get("identity_schema_version")
    if isinstance(version, str) and version.strip():
        return version.strip()
    raise VersionedStrategyModelParameterArtifactError(
        "identity_schema_version missing in experiment identity manifest"
    )


def verify_candidate_identity_binding_bundle(
    bundle_dir: Path | str,
) -> VerifiedCandidateIdentityBindingBundle:
    """Fail-closed verification of exactly one candidate identity binding bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="candidate identity binding bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise VersionedStrategyModelParameterArtifactError(
            f"candidate identity binding MANIFEST.sha256 verification failed: {msg}"
        )
    try:
        reverify_comparison_promotion_candidate_identity_binding_v1(output_dir=path)
    except ComparisonPromotionCandidateIdentityBindingError as exc:
        raise VersionedStrategyModelParameterArtifactError(str(exc)) from exc

    artifact_path = path / CANDIDATE_IDENTITY_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=CANDIDATE_IDENTITY_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != CANDIDATE_IDENTITY_CONTRACT_NAME:
        raise VersionedStrategyModelParameterArtifactError(
            "candidate identity binding contract_name mismatch"
        )
    if payload.get("contract_version") != CANDIDATE_IDENTITY_CONTRACT_VERSION:
        raise VersionedStrategyModelParameterArtifactError(
            "candidate identity binding contract_version mismatch"
        )
    _load_self_verification(
        path,
        rel=CANDIDATE_IDENTITY_SELF_VERIFICATION_REL,
        label=CANDIDATE_IDENTITY_SELF_VERIFICATION_REL,
    )
    return VerifiedCandidateIdentityBindingBundle(
        bundle_dir=path.resolve(),
        contract_name=CANDIDATE_IDENTITY_CONTRACT_NAME,
        contract_version=CANDIDATE_IDENTITY_CONTRACT_VERSION,
        producer_version=CANDIDATE_IDENTITY_PRODUCER_VERSION,
        artifact_ref=CANDIDATE_IDENTITY_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_payload(payload),
        manifest_digest=_manifest_file_digest(path),
        evidence_payload=dict(payload),
    )


def verify_model_parameter_identity_binding_bundle(
    bundle_dir: Path | str,
) -> VerifiedModelParameterIdentityBindingBundle:
    """Fail-closed verification of exactly one model/parameter identity binding bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="model parameter identity binding bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise VersionedStrategyModelParameterArtifactError(
            f"model parameter identity binding MANIFEST.sha256 verification failed: {msg}"
        )
    try:
        reverify_comparison_promotion_candidate_model_parameter_identity_binding_v1(output_dir=path)
    except ComparisonPromotionCandidateModelParameterIdentityBindingError as exc:
        raise VersionedStrategyModelParameterArtifactError(str(exc)) from exc

    artifact_path = path / MODEL_PARAMETER_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=MODEL_PARAMETER_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != MODEL_PARAMETER_CONTRACT_NAME:
        raise VersionedStrategyModelParameterArtifactError(
            "model parameter identity binding contract_name mismatch"
        )
    if payload.get("contract_version") != MODEL_PARAMETER_CONTRACT_VERSION:
        raise VersionedStrategyModelParameterArtifactError(
            "model parameter identity binding contract_version mismatch"
        )
    _load_self_verification(
        path,
        rel=MODEL_PARAMETER_SELF_VERIFICATION_REL,
        label=MODEL_PARAMETER_SELF_VERIFICATION_REL,
    )
    return VerifiedModelParameterIdentityBindingBundle(
        bundle_dir=path.resolve(),
        contract_name=MODEL_PARAMETER_CONTRACT_NAME,
        contract_version=MODEL_PARAMETER_CONTRACT_VERSION,
        producer_version=MODEL_PARAMETER_PRODUCER_VERSION,
        artifact_ref=MODEL_PARAMETER_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_payload(payload),
        manifest_digest=_manifest_file_digest(path),
        evidence_payload=dict(payload),
    )


def verify_ai_promotion_assessment_bundle(
    bundle_dir: Path | str,
) -> VerifiedAiPromotionAssessmentBundle:
    """Fail-closed verification of exactly one AI promotion assessment bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="ai promotion assessment bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise VersionedStrategyModelParameterArtifactError(
            f"ai promotion assessment MANIFEST.sha256 verification failed: {msg}"
        )
    try:
        reverify_ai_promotion_assessment_v1(output_dir=path)
    except AiPromotionAssessmentError as exc:
        raise VersionedStrategyModelParameterArtifactError(str(exc)) from exc

    artifact_path = path / AI_ASSESSMENT_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=AI_ASSESSMENT_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != AI_ASSESSMENT_CONTRACT_NAME:
        raise VersionedStrategyModelParameterArtifactError(
            "ai promotion assessment contract_name mismatch"
        )
    if payload.get("contract_version") != AI_ASSESSMENT_CONTRACT_VERSION:
        raise VersionedStrategyModelParameterArtifactError(
            "ai promotion assessment contract_version mismatch"
        )
    _load_self_verification(
        path,
        rel=AI_ASSESSMENT_SELF_VERIFICATION_REL,
        label=AI_ASSESSMENT_SELF_VERIFICATION_REL,
    )
    return VerifiedAiPromotionAssessmentBundle(
        bundle_dir=path.resolve(),
        contract_name=AI_ASSESSMENT_CONTRACT_NAME,
        contract_version=AI_ASSESSMENT_CONTRACT_VERSION,
        producer_version=AI_ASSESSMENT_PRODUCER_VERSION,
        artifact_ref=AI_ASSESSMENT_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_payload(payload),
        manifest_digest=_manifest_file_digest(path),
        evidence_payload=dict(payload),
    )


def _input_artifact_ref_mapping(
    *,
    bundle: VerifiedCandidateIdentityBindingBundle
    | VerifiedModelParameterIdentityBindingBundle
    | VerifiedAiPromotionAssessmentBundle,
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


def _cross_validate_identity_bindings(
    *,
    candidate: VerifiedCandidateIdentityBindingBundle,
    model_parameter: VerifiedModelParameterIdentityBindingBundle,
    ai_assessment: VerifiedAiPromotionAssessmentBundle | None,
) -> tuple[str, list[str], dict[str, bool]]:
    candidate_payload = candidate.evidence_payload
    model_payload = model_parameter.evidence_payload
    reason_codes: list[str] = []
    completion_flags = {
        "versioned_strategy_model_parameter_artifact_complete": False,
        "strategy_identity_bound": False,
        "model_identity_bound": False,
        "parameter_set_identity_bound": False,
        "cross_domain_lineage_bound": False,
    }

    if candidate_payload.get("candidate_identity_binding_status") != "PASS":
        reason_codes.append("CANDIDATE_IDENTITY_BINDING_NOT_PASS")
        return "FAIL", reason_codes, completion_flags
    if model_payload.get("model_parameter_identity_binding_status") != "PASS":
        reason_codes.append("MODEL_PARAMETER_IDENTITY_BINDING_NOT_PASS")
        return "FAIL", reason_codes, completion_flags

    strategy_ref = str(candidate_payload.get("strategy_identity_ref", ""))
    strategy_digest = str(candidate_payload.get("experiment_identity_digest", ""))
    model_ref = str(model_payload.get("model_identity_ref", ""))
    model_digest = str(model_payload.get("model_identity_digest", ""))
    parameter_ref = str(model_payload.get("parameter_set_identity_ref", ""))
    parameter_digest = str(model_payload.get("parameter_set_identity_digest", ""))

    if not _non_empty_ref(strategy_ref):
        reason_codes.append("STRATEGY_IDENTITY_MISSING")
    if not is_valid_sha256_hex(strategy_digest):
        reason_codes.append("STRATEGY_IDENTITY_DIGEST_MISSING")
    if not _non_empty_ref(model_ref):
        reason_codes.append("MODEL_IDENTITY_MISSING")
    if not is_valid_sha256_hex(model_digest):
        reason_codes.append("MODEL_IDENTITY_DIGEST_MISSING")
    if not _non_empty_ref(parameter_ref):
        reason_codes.append("PARAMETER_SET_IDENTITY_MISSING")
    if not is_valid_sha256_hex(parameter_digest):
        reason_codes.append("PARAMETER_SET_IDENTITY_DIGEST_MISSING")

    candidate_experiment_ref = str(candidate_payload.get("experiment_identity_ref", ""))
    model_experiment_ref = str(model_payload.get("experiment_identity_ref", ""))
    candidate_experiment_digest = str(candidate_payload.get("experiment_identity_digest", ""))
    model_experiment_digest = str(model_payload.get("experiment_identity_digest", ""))
    if candidate_experiment_ref != model_experiment_ref:
        reason_codes.append("EXPERIMENT_IDENTITY_REF_MISMATCH")
    if candidate_experiment_digest != model_experiment_digest:
        reason_codes.append("EXPERIMENT_IDENTITY_DIGEST_MISMATCH")

    candidate_comparison_id = _normalized_comparison_definition_id(candidate_payload)
    model_comparison_id = _normalized_comparison_definition_id(model_payload)
    if candidate_comparison_id != model_comparison_id:
        reason_codes.append("COMPARISON_DEFINITION_ID_MISMATCH")

    model_experiment_id = str(model_payload.get("experiment_identity_id", ""))
    if strategy_ref and model_experiment_id and strategy_ref != model_experiment_id:
        reason_codes.append("STRATEGY_IDENTITY_REF_MISMATCH")

    if ai_assessment is not None:
        ai_payload = ai_assessment.evidence_payload
        ai_model_ref = str(ai_payload.get("model_identity_ref", ""))
        ai_parameter_ref = str(ai_payload.get("parameter_set_identity_ref", ""))
        if ai_model_ref and ai_model_ref != model_ref:
            reason_codes.append("AI_ASSESSMENT_MODEL_IDENTITY_MISMATCH")
        if ai_parameter_ref and ai_parameter_ref != parameter_ref:
            reason_codes.append("AI_ASSESSMENT_PARAMETER_SET_IDENTITY_MISMATCH")
        ai_comparison_id = _normalized_comparison_definition_id(ai_payload)
        if (
            ai_comparison_id
            and candidate_comparison_id
            and ai_comparison_id != candidate_comparison_id
        ):
            reason_codes.append("AI_ASSESSMENT_COMPARISON_DEFINITION_MISMATCH")

    if reason_codes:
        return "FAIL", sorted(set(reason_codes)), completion_flags

    reason_codes.extend(
        [
            "STRATEGY_IDENTITY_BOUND",
            "MODEL_IDENTITY_BOUND",
            "PARAMETER_SET_IDENTITY_BOUND",
            "CROSS_DOMAIN_LINEAGE_BOUND",
            "VERSIONED_STRATEGY_MODEL_PARAMETER_ARTIFACT_COMPLETE",
        ]
    )
    completion_flags = {
        "versioned_strategy_model_parameter_artifact_complete": True,
        "strategy_identity_bound": True,
        "model_identity_bound": True,
        "parameter_set_identity_bound": True,
        "cross_domain_lineage_bound": True,
    }
    return "PASS", sorted(set(reason_codes)), completion_flags


def _compute_output_digest(body: Mapping[str, Any]) -> str:
    excluded = frozenset(
        {
            "output_digest",
            "manifest_digest",
            "integrity",
            "created_at",
            "artifact_id",
        }
    )
    digest_body = {key: body[key] for key in sorted(body) if key not in excluded}
    return compute_content_sha256(digest_body)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in body.items() if key not in {"integrity", "manifest_digest"}
    }


def build_versioned_strategy_model_parameter_artifact_v1(
    *,
    candidate: VerifiedCandidateIdentityBindingBundle,
    model_parameter: VerifiedModelParameterIdentityBindingBundle,
    ai_assessment: VerifiedAiPromotionAssessmentBundle | None,
) -> dict[str, Any]:
    candidate_payload = candidate.evidence_payload
    model_payload = model_parameter.evidence_payload
    binding_status, reason_codes, completion_flags = _cross_validate_identity_bindings(
        candidate=candidate,
        model_parameter=model_parameter,
        ai_assessment=ai_assessment,
    )

    input_refs = [
        _input_artifact_ref_mapping(bundle=candidate),
        _input_artifact_ref_mapping(bundle=model_parameter),
    ]
    if ai_assessment is not None:
        input_refs.append(_input_artifact_ref_mapping(bundle=ai_assessment))
    input_refs.sort(key=lambda item: (item["contract_name"], item["artifact_digest"]))

    parent_artifact_refs: list[dict[str, Any]] = []
    for source in (candidate_payload, model_payload):
        refs = source.get("parent_artifact_refs")
        if isinstance(refs, list):
            parent_artifact_refs.extend(dict(item) for item in refs if isinstance(item, Mapping))
    if ai_assessment is not None:
        refs = ai_assessment.evidence_payload.get("parent_artifact_refs")
        if isinstance(refs, list):
            parent_artifact_refs.extend(dict(item) for item in refs if isinstance(item, Mapping))
    parent_artifact_refs.sort(
        key=lambda item: (str(item.get("ref_type", "")), str(item.get("digest", "")))
    )

    strategy_ref = str(candidate_payload.get("strategy_identity_ref", ""))
    strategy_digest = str(candidate_payload.get("experiment_identity_digest", ""))
    experiment_ref = str(candidate_payload.get("experiment_identity_ref", ""))
    comparison_definition_id = _normalized_comparison_definition_id(candidate_payload) or (
        _normalized_comparison_definition_id(model_payload)
    )
    strategy_version = ""
    if binding_status == "PASS" and _non_empty_ref(experiment_ref):
        strategy_version = _resolve_strategy_version(experiment_identity_ref=experiment_ref)

    payload: dict[str, Any] = {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "creation_contract_version": CREATION_CONTRACT_VERSION,
        "artifact_id": "",
        "artifact_version": CONTRACT_VERSION,
        "created_at": OFFLINE_DETERMINISTIC_CREATED_AT,
        "producer_version": PRODUCER_VERSION,
        "record_kind": RECORD_KIND,
        "input_relation": INPUT_RELATION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "capabilities": [],
        "is_versioned_strategy_model_parameter_artifact": True,
        "artifact_offline_only": True,
        "artifact_immutable": True,
        "artifact_authority_invariants": dict(VERSIONED_ARTIFACT_AUTHORITY_INVARIANTS),
        "versioned_artifact_binding_status": binding_status,
        "versioned_artifact_binding_reason_codes": reason_codes,
        "candidate_identity_binding_bundle_ref": candidate.bundle_dir.as_posix(),
        "candidate_identity_binding_artifact_ref": candidate.artifact_ref,
        "candidate_identity_binding_digest": candidate.artifact_digest,
        "candidate_identity_binding_manifest_digest": candidate.manifest_digest,
        "model_parameter_identity_binding_bundle_ref": model_parameter.bundle_dir.as_posix(),
        "model_parameter_identity_binding_artifact_ref": model_parameter.artifact_ref,
        "model_parameter_identity_binding_digest": model_parameter.artifact_digest,
        "model_parameter_identity_binding_manifest_digest": model_parameter.manifest_digest,
        "strategy_identity_ref": strategy_ref,
        "strategy_identity_digest": strategy_digest,
        "strategy_version": strategy_version,
        "strategy_identity_source_contract": STRATEGY_IDENTITY_SOURCE_CONTRACT,
        "strategy_identity_source_version": STRATEGY_IDENTITY_SOURCE_VERSION,
        "model_identity_ref": str(model_payload.get("model_identity_ref", "")),
        "model_identity_digest": str(model_payload.get("model_identity_digest", "")),
        "model_version": str(model_payload.get("model_identity_source_version", "")),
        "model_identity_source_contract": str(
            model_payload.get("model_identity_source_contract", "")
        ),
        "model_identity_source_version": str(
            model_payload.get("model_identity_source_version", "")
        ),
        "model_identity_source_projection": str(
            model_payload.get("model_identity_source_projection", "")
        ),
        "parameter_set_identity_ref": str(model_payload.get("parameter_set_identity_ref", "")),
        "parameter_set_identity_digest": str(
            model_payload.get("parameter_set_identity_digest", "")
        ),
        "parameter_schema_version": str(
            model_payload.get("parameter_set_identity_source_version", "")
        ),
        "parameter_set_identity_source_contract": str(
            model_payload.get("parameter_set_identity_source_contract", "")
        ),
        "parameter_set_identity_source_version": str(
            model_payload.get("parameter_set_identity_source_version", "")
        ),
        "parameter_set_identity_source_projection": str(
            model_payload.get("parameter_set_identity_source_projection", "")
        ),
        "comparison_definition_id": comparison_definition_id,
        "experiment_identity_id": str(model_payload.get("experiment_identity_id", "")),
        "upstream_candidate_identity_contract_name": candidate.contract_name,
        "upstream_candidate_identity_contract_version": candidate.contract_version,
        "upstream_model_parameter_contract_name": model_parameter.contract_name,
        "upstream_model_parameter_contract_version": model_parameter.contract_version,
        "input_artifact_refs": input_refs,
        "parent_artifact_refs": parent_artifact_refs,
        "input_digest": "",
        "output_digest": "",
        "manifest_digest": "",
    }
    payload.update(completion_flags)

    if ai_assessment is not None:
        ai_payload = ai_assessment.evidence_payload
        payload.update(
            {
                "ai_promotion_assessment_bundle_ref": ai_assessment.bundle_dir.as_posix(),
                "ai_promotion_assessment_artifact_ref": ai_assessment.artifact_ref,
                "ai_promotion_assessment_digest": ai_assessment.artifact_digest,
                "ai_promotion_assessment_manifest_digest": ai_assessment.manifest_digest,
                "ai_promotion_assessment_ref": ai_assessment.bundle_dir.as_posix(),
                "upstream_ai_assessment_contract_name": ai_assessment.contract_name,
                "upstream_ai_assessment_contract_version": ai_assessment.contract_version,
            }
        )
        for field in _TRANSITIVE_LINEAGE_FIELDS:
            value = ai_payload.get(field)
            if value is not None and str(value):
                payload[field] = str(value)
    else:
        for field in _TRANSITIVE_LINEAGE_FIELDS:
            value = model_payload.get(field) or candidate_payload.get(field)
            if value is not None and str(value):
                payload[field] = str(value)

    payload["candidate_identity_binding_bundle_ref"] = candidate.bundle_dir.as_posix()
    payload["model_parameter_identity_binding_bundle_ref"] = model_parameter.bundle_dir.as_posix()

    for key, value in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        payload[key] = value
    payload.update(completion_flags)

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    _validate_capabilities(payload["capabilities"])
    if binding_status not in _VALID_BINDING_STATUS:
        raise VersionedStrategyModelParameterArtifactError(
            "versioned_artifact_binding_status invalid"
        )

    payload["input_digest"] = compute_content_sha256({"input_artifact_refs": input_refs})
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    return payload


def serialize_versioned_strategy_model_parameter_artifact_v1(
    artifact: Mapping[str, Any],
) -> str:
    _reject_forbidden_index_keys(artifact)
    _validate_non_authorizing_flags(artifact)
    _validate_capabilities(artifact.get("capabilities"))
    binding_status = artifact.get("versioned_artifact_binding_status")
    if binding_status not in _VALID_BINDING_STATUS:
        raise VersionedStrategyModelParameterArtifactError(
            f"versioned_artifact_binding_status must be one of {sorted(_VALID_BINDING_STATUS)}"
        )
    reason_codes = artifact.get("versioned_artifact_binding_reason_codes")
    if isinstance(reason_codes, list) and reason_codes != sorted(reason_codes):
        raise VersionedStrategyModelParameterArtifactError(
            "versioned_artifact_binding_reason_codes must be sorted deterministically"
        )
    if artifact.get("artifact_schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise VersionedStrategyModelParameterArtifactError("artifact_schema_version mismatch")
    if artifact.get("creation_contract_version") != CREATION_CONTRACT_VERSION:
        raise VersionedStrategyModelParameterArtifactError("creation_contract_version mismatch")
    if artifact.get("artifact_version") != CONTRACT_VERSION:
        raise VersionedStrategyModelParameterArtifactError("artifact_version mismatch")
    return deterministic_json_dumps(artifact)


def _artifact_bytes_for_manifest_digest(artifact: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in artifact.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_versioned_strategy_model_parameter_artifact_v1(body).encode("utf-8")


def _compute_output_manifest_digest(artifact: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(artifact)).hexdigest()


def _validate_artifact_integrity(artifact: Mapping[str, Any]) -> None:
    if artifact.get("contract_name") != CONTRACT_NAME:
        raise VersionedStrategyModelParameterArtifactError("contract_name mismatch")
    if artifact.get("contract_version") != CONTRACT_VERSION:
        raise VersionedStrategyModelParameterArtifactError("contract_version mismatch")
    integrity = artifact.get("integrity")
    if not isinstance(integrity, Mapping):
        raise VersionedStrategyModelParameterArtifactError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(artifact))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise VersionedStrategyModelParameterArtifactError("integrity.content_sha256 mismatch")
    output_digest = artifact.get("output_digest")
    if output_digest != _compute_output_digest(artifact):
        raise VersionedStrategyModelParameterArtifactError("output_digest mismatch")
    if artifact.get("artifact_id") != output_digest:
        raise VersionedStrategyModelParameterArtifactError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    artifact: Mapping[str, Any],
    candidate: VerifiedCandidateIdentityBindingBundle,
    model_parameter: VerifiedModelParameterIdentityBindingBundle,
    ai_assessment: VerifiedAiPromotionAssessmentBundle | None,
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "artifact_schema_version", "status": "PASS"},
        {"check_id": "creation_contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_two_required_inputs", "status": "PASS"},
        {"check_id": "candidate_identity_binding_verified", "status": "PASS"},
        {"check_id": "model_parameter_identity_binding_verified", "status": "PASS"},
        {"check_id": "strategy_identity_bound_on_pass", "status": "PASS"},
        {"check_id": "model_identity_bound_on_pass", "status": "PASS"},
        {"check_id": "parameter_set_identity_bound_on_pass", "status": "PASS"},
        {"check_id": "cross_domain_lineage_bound_on_pass", "status": "PASS"},
        {"check_id": "offline_only_no_execution", "status": "PASS"},
        {"check_id": "no_promotion_authority", "status": "PASS"},
        {"check_id": "no_configpatch_mutation", "status": "PASS"},
        {"check_id": "non_authorizing_semantics", "status": "PASS"},
        {"check_id": "forbidden_capabilities_absent", "status": "PASS"},
        {"check_id": "output_digest", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
        {"check_id": "deterministic_reverification", "status": "PASS"},
    ]

    input_refs = artifact.get("input_artifact_refs")
    expected_inputs = 3 if ai_assessment is not None else 2
    if not isinstance(input_refs, list) or len(input_refs) != expected_inputs:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "exactly_two_required_inputs" else c
            for c in checks
        ]

    if artifact.get("manifest_digest") != manifest_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "manifest_verification" else c
            for c in checks
        ]

    if artifact.get("versioned_artifact_binding_status") == "PASS":
        for check_id, field in (
            ("strategy_identity_bound_on_pass", "strategy_identity_bound"),
            ("model_identity_bound_on_pass", "model_identity_bound"),
            ("parameter_set_identity_bound_on_pass", "parameter_set_identity_bound"),
            ("cross_domain_lineage_bound_on_pass", "cross_domain_lineage_bound"),
        ):
            if artifact.get(field) is not True:
                checks = [
                    {**c, "status": "FAIL"} if c["check_id"] == check_id else c for c in checks
                ]

    structural_failures = [
        check
        for check in checks
        if check["status"] != "PASS"
        and check["check_id"]
        not in {
            "strategy_identity_bound_on_pass",
            "model_identity_bound_on_pass",
            "parameter_set_identity_bound_on_pass",
            "cross_domain_lineage_bound_on_pass",
        }
    ]
    if structural_failures:
        raise VersionedStrategyModelParameterArtifactError("self-verification checks failed")

    payload: dict[str, Any] = {
        "self_verification_schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": "PASS",
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "verified_output_digest": artifact.get("output_digest"),
        "verified_manifest_digest": manifest_digest,
        "verified_candidate_identity_binding_bundle_ref": candidate.bundle_dir.as_posix(),
        "verified_model_parameter_identity_binding_bundle_ref": model_parameter.bundle_dir.as_posix(),
        "verified_versioned_artifact_binding_status": artifact.get(
            "versioned_artifact_binding_status"
        ),
    }
    if ai_assessment is not None:
        payload["verified_ai_promotion_assessment_bundle_ref"] = ai_assessment.bundle_dir.as_posix()
    digest = compute_content_sha256(payload)
    payload["integrity"] = {"content_sha256": digest}
    return payload


def _finalize_artifact_with_manifest_digest(
    artifact: Mapping[str, Any], *, manifest_digest: str
) -> dict[str, Any]:
    body = dict(artifact)
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


def verify_artifact_inputs(
    inputs: VersionedStrategyModelParameterArtifactInputs,
) -> tuple[
    VerifiedCandidateIdentityBindingBundle,
    VerifiedModelParameterIdentityBindingBundle,
    VerifiedAiPromotionAssessmentBundle | None,
]:
    """Verify required identity binding bundles and optional AI assessment bundle."""
    candidate = verify_candidate_identity_binding_bundle(
        inputs.candidate_identity_binding_bundle_dir
    )
    model_parameter = verify_model_parameter_identity_binding_bundle(
        inputs.model_parameter_identity_binding_bundle_dir
    )
    ai_assessment: VerifiedAiPromotionAssessmentBundle | None = None
    if inputs.ai_promotion_assessment_bundle_dir is not None:
        ai_assessment = verify_ai_promotion_assessment_bundle(
            inputs.ai_promotion_assessment_bundle_dir
        )
    return candidate, model_parameter, ai_assessment


def reverify_versioned_strategy_model_parameter_artifact_v1(*, output_dir: Path | str) -> None:
    """Replay versioned strategy/model/parameter artifact bundle without upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise VersionedStrategyModelParameterArtifactError(
            f"versioned artifact directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise VersionedStrategyModelParameterArtifactError(
            f"MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    artifact = read_manifest(artifact_path)
    _validate_artifact_integrity(artifact)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise VersionedStrategyModelParameterArtifactError(
            "SELF_VERIFICATION overall_status must be PASS"
        )

    manifest_digest = _compute_output_manifest_digest(artifact)
    if artifact.get("manifest_digest") != manifest_digest:
        raise VersionedStrategyModelParameterArtifactError("manifest_digest mismatch on replay")

    candidate = verify_candidate_identity_binding_bundle(
        Path(str(artifact["candidate_identity_binding_bundle_ref"]))
    )
    if artifact.get("candidate_identity_binding_digest") != candidate.artifact_digest:
        raise VersionedStrategyModelParameterArtifactError(
            "candidate_identity_binding_digest mismatch on replay"
        )

    model_parameter = verify_model_parameter_identity_binding_bundle(
        Path(str(artifact["model_parameter_identity_binding_bundle_ref"]))
    )
    if artifact.get("model_parameter_identity_binding_digest") != model_parameter.artifact_digest:
        raise VersionedStrategyModelParameterArtifactError(
            "model_parameter_identity_binding_digest mismatch on replay"
        )

    ai_ref = artifact.get("ai_promotion_assessment_bundle_ref")
    ai_assessment: VerifiedAiPromotionAssessmentBundle | None = None
    if ai_ref:
        ai_assessment = verify_ai_promotion_assessment_bundle(Path(str(ai_ref)))
        if artifact.get("ai_promotion_assessment_digest") != ai_assessment.artifact_digest:
            raise VersionedStrategyModelParameterArtifactError(
                "ai_promotion_assessment_digest mismatch on replay"
            )

    status, _, _ = _cross_validate_identity_bindings(
        candidate=candidate,
        model_parameter=model_parameter,
        ai_assessment=ai_assessment,
    )
    if artifact.get("versioned_artifact_binding_status") != status:
        raise VersionedStrategyModelParameterArtifactError(
            "versioned_artifact_binding_status mismatch on replay"
        )


def produce_versioned_strategy_model_parameter_artifact_v1(
    *,
    inputs: VersionedStrategyModelParameterArtifactInputs,
    output_dir: Path | str,
) -> VersionedStrategyModelParameterArtifactResult:
    """Produce offline LEVEL_3 versioned strategy/model/parameter artifact evidence."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    input_dirs = (
        inputs.candidate_identity_binding_bundle_dir,
        inputs.model_parameter_identity_binding_bundle_dir,
    )
    if inputs.ai_promotion_assessment_bundle_dir is not None:
        input_dirs = (*input_dirs, inputs.ai_promotion_assessment_bundle_dir)
    _reject_unsafe_overlap(input_dirs=input_dirs, output_dir=final_dir)

    candidate, model_parameter, ai_assessment = verify_artifact_inputs(inputs)
    artifact_body = build_versioned_strategy_model_parameter_artifact_v1(
        candidate=candidate,
        model_parameter=model_parameter,
        ai_assessment=ai_assessment,
    )
    if artifact_body.get("versioned_artifact_binding_status") != "PASS":
        raise VersionedStrategyModelParameterArtifactError(
            "identity bindings must PASS before versioned artifact production"
        )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise VersionedStrategyModelParameterArtifactError(
            f"staging directory collision: {staging}"
        )

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(artifact_body)
        finalized = _finalize_artifact_with_manifest_digest(
            artifact_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_versioned_strategy_model_parameter_artifact_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            artifact=finalized,
            candidate=candidate,
            model_parameter=model_parameter,
            ai_assessment=ai_assessment,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise VersionedStrategyModelParameterArtifactError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_versioned_strategy_model_parameter_artifact_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise VersionedStrategyModelParameterArtifactError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return VersionedStrategyModelParameterArtifactResult(
        output_dir=final_dir,
        comparison_definition_id=str(finalized.get("comparison_definition_id", "")),
        artifact_id=str(finalized["artifact_id"]),
        artifact_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        versioned_artifact_binding_status=str(finalized["versioned_artifact_binding_status"]),
        strategy_identity_ref=str(finalized["strategy_identity_ref"]),
        model_identity_ref=str(finalized["model_identity_ref"]),
        parameter_set_identity_ref=str(finalized["parameter_set_identity_ref"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "ARTIFACT_SCHEMA_VERSION",
    "AUTHORITY_LEVEL",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "CREATION_CONTRACT_VERSION",
    "EVIDENCE_LEVEL",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "SELF_VERIFICATION_REL",
    "VERSIONED_ARTIFACT_AUTHORITY_INVARIANTS",
    "VersionedStrategyModelParameterArtifactError",
    "VersionedStrategyModelParameterArtifactInputs",
    "VersionedStrategyModelParameterArtifactResult",
    "VerifiedAiPromotionAssessmentBundle",
    "VerifiedCandidateIdentityBindingBundle",
    "VerifiedModelParameterIdentityBindingBundle",
    "build_self_verification_v1",
    "build_versioned_strategy_model_parameter_artifact_v1",
    "produce_versioned_strategy_model_parameter_artifact_v1",
    "reverify_versioned_strategy_model_parameter_artifact_v1",
    "serialize_versioned_strategy_model_parameter_artifact_v1",
    "verify_ai_promotion_assessment_bundle",
    "verify_artifact_inputs",
    "verify_candidate_identity_binding_bundle",
    "verify_model_parameter_identity_binding_bundle",
]
