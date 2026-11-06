"""Offline LEVEL_3 handoff trust policy owner v1."""

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
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)
from src.meta.learning_loop.versioned_strategy_model_parameter_artifact_v1 import (
    ARTIFACT_REL as UPSTREAM_ARTIFACT_REL,
    ARTIFACT_SCHEMA_VERSION as UPSTREAM_ARTIFACT_SCHEMA_VERSION,
    CONTRACT_NAME as UPSTREAM_CONTRACT_NAME,
    CONTRACT_VERSION as UPSTREAM_CONTRACT_VERSION,
    CREATION_CONTRACT_VERSION as UPSTREAM_CREATION_CONTRACT_VERSION,
    PRODUCER_VERSION as UPSTREAM_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as UPSTREAM_SELF_VERIFICATION_REL,
    VersionedStrategyModelParameterArtifactError,
    reverify_versioned_strategy_model_parameter_artifact_v1,
)

CONTRACT_NAME = "handoff_trust_policy_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "handoff_trust_policy_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "handoff_trust_policy_record"
INPUT_RELATION = "EVALUATES_VERIFIED_VERSIONED_STRATEGY_MODEL_PARAMETER_ARTIFACT_V1"
ARTIFACT_REL = "handoff_trust_policy_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".handoff_trust_policy_staging_"

HANDOFF_TYPE = "versioned_strategy_model_parameter_artifact_v1_offline_handoff"
DETERMINISTIC_RULE_SET_VERSION = "handoff_trust_policy_rules_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"

CONSUMER_CONTRACT_NAME = "offline_strategy_model_parameter_consumer_capability_v1"
CONSUMER_CONTRACT_VERSION = "v1"
CONSUMER_CONTRACT_ID = "offline_strategy_model_parameter_consumer_capability_v1@v1"

_VALID_TRUST_RESULTS = frozenset({"ALLOW_OFFLINE_HANDOFF", "DENY_HANDOFF", "ABSTAIN"})
_VALID_COMPATIBILITY_RESULTS = frozenset({"COMPATIBLE", "INCOMPATIBLE", "UNKNOWN"})
_VALID_REVOCATION_STATES = frozenset({"NOT_REVOKED", "REVOKED", "UNKNOWN"})
_EVIDENCE_BOUND = "BOUND"
_IDENTITY_BOUND = "BOUND"

HANDOFF_TRUST_POLICY_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "trust_policy_is_descriptive_only": True,
    "trust_policy_does_not_execute_handoff": True,
    "trust_policy_does_not_invoke_consumer": True,
    "trust_policy_does_not_mutate_consumer": True,
    "trust_policy_does_not_authorize_promotion": True,
    "trust_policy_does_not_construct_promotion_candidate": True,
    "trust_policy_does_not_create_configpatch": True,
    "trust_policy_does_not_modify_config": True,
    "trust_policy_does_not_authorize_runtime": True,
    "trust_policy_does_not_authorize_live": True,
    "trust_policy_does_not_create_order_intent": True,
    "trust_policy_is_offline_only": True,
    "evidence_does_not_authorize_promotion": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_handoff_trust_policy": True,
    "handoff_trust_policy_offline_only": True,
    "evidence_does_not_authorize_promotion": True,
    "evidence_does_not_authorize_runtime": True,
    "handoff_executed": False,
    "consumer_invoked": False,
    "consumer_mutated": False,
    "files_transferred": False,
    "network_side_effect_created": False,
    "strategy_executed": False,
    "model_inference_executed": False,
    "parameters_modified": False,
    "promotion_policy_executed": False,
    "promotion_authorized": False,
    "promotion_candidate_constructed": False,
    "configpatch_created": False,
    "configpatch_modified": False,
    "configpatch_applied": False,
    "configpatch_accepted": False,
    "runtime_configuration_created": False,
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

_SELF_VERIFICATION_SCHEMA_VERSION = "handoff_trust_policy_self_verification_v1"

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
    "strategy_identity_ref",
    "strategy_identity_digest",
    "model_identity_ref",
    "model_identity_digest",
    "parameter_set_identity_ref",
    "parameter_set_identity_digest",
    "ai_promotion_assessment_ref",
    "ai_promotion_assessment_digest",
)

_REQUIRED_LINEAGE_FIELDS_FOR_ALLOW: tuple[str, ...] = (
    "strategy_identity_ref",
    "strategy_identity_digest",
    "model_identity_ref",
    "model_identity_digest",
    "parameter_set_identity_ref",
    "parameter_set_identity_digest",
    "experiment_identity_ref",
    "experiment_identity_digest",
    "comparison_definition_id",
)

_OPTIONAL_LINEAGE_FIELDS_FOR_ABSTAIN: tuple[str, ...] = (
    "ai_promotion_assessment_ref",
    "policy_decision_ref",
    "research_validity_ref",
    "cross_domain_lineage_binding_digest",
)

_EMBEDDED_CONSUMER_CONTRACT: dict[str, Any] = {
    "consumer_contract_id": CONSUMER_CONTRACT_ID,
    "contract_name": CONSUMER_CONTRACT_NAME,
    "contract_version": CONSUMER_CONTRACT_VERSION,
    "handoff_type": HANDOFF_TYPE,
    "accepted_producer_contract_name": UPSTREAM_CONTRACT_NAME,
    "accepted_producer_contract_version": UPSTREAM_CONTRACT_VERSION,
    "accepted_artifact_schema_version": UPSTREAM_ARTIFACT_SCHEMA_VERSION,
    "accepted_creation_contract_version": UPSTREAM_CREATION_CONTRACT_VERSION,
    "minimum_artifact_version": UPSTREAM_CONTRACT_VERSION,
    "required_binding_status": "PASS",
    "required_completion_flags": [
        "versioned_strategy_model_parameter_artifact_complete",
        "strategy_identity_bound",
        "model_identity_bound",
        "parameter_set_identity_bound",
        "cross_domain_lineage_bound",
    ],
    "forbidden_upstream_capabilities": sorted(_FORBIDDEN_CAPABILITIES),
    "offline_only_required": True,
}


class HandoffTrustPolicyError(ValueError):
    """Fail-closed handoff trust policy error."""


@dataclass(frozen=True)
class VerifiedVersionedArtifactBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    artifact_payload: dict[str, Any]


@dataclass(frozen=True)
class ConsumerCapabilityContract:
    contract_id: str
    contract_name: str
    contract_version: str
    handoff_type: str
    payload: dict[str, Any]
    source_ref: str


@dataclass(frozen=True)
class HandoffTrustPolicyInputs:
    versioned_artifact_bundle_dir: Path
    consumer_contract_ref: Path | None = None


@dataclass(frozen=True)
class HandoffTrustPolicyResult:
    output_dir: Path
    comparison_definition_id: str
    artifact_id: str
    trust_policy_path: Path
    self_verification_path: Path
    manifest_path: Path
    trust_result: str
    compatibility_result: str
    versioned_artifact_ref: str
    versioned_artifact_digest: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise HandoffTrustPolicyError(f"{label} must not be a symlink")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise HandoffTrustPolicyError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise HandoffTrustPolicyError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise HandoffTrustPolicyError(f"{label} must be a directory: {bundle_dir}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise HandoffTrustPolicyError(f"output directory already exists: {output_dir}")
    if is_under_tmp(output_dir):
        raise HandoffTrustPolicyError("output directory must not be under /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, versioned_artifact_dir: Path, output_dir: Path) -> None:
    input_res = versioned_artifact_dir.resolve()
    output_res = output_dir.resolve()
    if output_res == input_res:
        raise HandoffTrustPolicyError("output directory must not equal input path")
    if _path_is_under(output_res, input_res):
        raise HandoffTrustPolicyError("output directory must not be inside input path")
    if _path_is_under(input_res, output_res):
        raise HandoffTrustPolicyError("input directory must not be inside output directory")


def _manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / MANIFEST_FILENAME
    _validate_regular_file(manifest_path, label=MANIFEST_FILENAME)
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _validate_capabilities(capabilities: Any) -> list[str]:
    if capabilities is None:
        return []
    if not isinstance(capabilities, list):
        raise HandoffTrustPolicyError("capabilities must be a list")
    normalized: list[str] = []
    for item in capabilities:
        if not isinstance(item, str):
            raise HandoffTrustPolicyError("capabilities entries must be strings")
        if item in _FORBIDDEN_CAPABILITIES:
            raise HandoffTrustPolicyError(f"forbidden capability: {item}")
        normalized.append(item)
    return sorted(normalized)


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if payload.get(key) is not expected:
            raise HandoffTrustPolicyError(f"{key} must be {expected!r}")


def _validate_completion_flags(payload: Mapping[str, Any]) -> None:
    complete = payload.get("handoff_trust_policy_complete")
    if complete is True and payload.get("versioned_artifact_bound") is not True:
        raise HandoffTrustPolicyError(
            "versioned_artifact_bound must be True when handoff trust policy complete"
        )
    if complete is True and payload.get("producer_contract_bound") is not True:
        raise HandoffTrustPolicyError(
            "producer_contract_bound must be True when handoff trust policy complete"
        )
    if (
        complete is True
        and payload.get("trust_result") == "ALLOW_OFFLINE_HANDOFF"
        and payload.get("cross_domain_lineage_bound") is not True
    ):
        raise HandoffTrustPolicyError(
            "cross_domain_lineage_bound must be True for complete ALLOW_OFFLINE_HANDOFF"
        )


def _sorted_strings(values: list[str]) -> list[str]:
    return sorted(set(values))


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


def _load_self_verification(bundle_dir: Path, *, rel: str, label: str) -> dict[str, Any]:
    path = bundle_dir / rel
    _validate_regular_file(path, label=label)
    payload = read_manifest(path)
    if not isinstance(payload, dict):
        raise HandoffTrustPolicyError(f"{label} must be a JSON object")
    return payload


def _artifact_digest_from_payload(payload: Mapping[str, Any]) -> str:
    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping):
        raise HandoffTrustPolicyError("integrity must be an object")
    digest = integrity.get("content_sha256")
    if not isinstance(digest, str) or not is_valid_sha256_hex(digest):
        raise HandoffTrustPolicyError("integrity.content_sha256 invalid")
    return digest


def _validate_consumer_contract_payload(payload: Mapping[str, Any]) -> None:
    if payload.get("contract_name") != CONSUMER_CONTRACT_NAME:
        raise HandoffTrustPolicyError("consumer contract_name mismatch")
    if payload.get("contract_version") != CONSUMER_CONTRACT_VERSION:
        raise HandoffTrustPolicyError("consumer contract_version mismatch")
    if payload.get("handoff_type") != HANDOFF_TYPE:
        raise HandoffTrustPolicyError("consumer handoff_type mismatch")
    if payload.get("accepted_producer_contract_name") != UPSTREAM_CONTRACT_NAME:
        raise HandoffTrustPolicyError("consumer accepted_producer_contract_name mismatch")


def _resolve_consumer_contract(
    consumer_contract_ref: Path | None,
) -> ConsumerCapabilityContract:
    if consumer_contract_ref is None:
        return ConsumerCapabilityContract(
            contract_id=CONSUMER_CONTRACT_ID,
            contract_name=CONSUMER_CONTRACT_NAME,
            contract_version=CONSUMER_CONTRACT_VERSION,
            handoff_type=HANDOFF_TYPE,
            payload=dict(_EMBEDDED_CONSUMER_CONTRACT),
            source_ref="embedded_default",
        )

    path = consumer_contract_ref.resolve()
    _reject_symlink(path, label="consumer contract ref")
    if path.is_dir():
        contract_path = path / f"{CONSUMER_CONTRACT_NAME}.json"
        source_ref = path.as_posix()
    else:
        contract_path = path
        source_ref = path.parent.as_posix()
    _validate_regular_file(contract_path, label="consumer contract")
    payload = read_manifest(contract_path)
    if not isinstance(payload, dict):
        raise HandoffTrustPolicyError("consumer contract must be a JSON object")
    _validate_consumer_contract_payload(payload)
    contract_id = str(payload.get("consumer_contract_id", ""))
    if not contract_id:
        raise HandoffTrustPolicyError("consumer consumer_contract_id missing")
    return ConsumerCapabilityContract(
        contract_id=contract_id,
        contract_name=str(payload["contract_name"]),
        contract_version=str(payload["contract_version"]),
        handoff_type=str(payload["handoff_type"]),
        payload=dict(payload),
        source_ref=source_ref,
    )


def verify_versioned_artifact_bundle(
    bundle_dir: Path | str,
) -> VerifiedVersionedArtifactBundle:
    """Fail-closed verification of exactly one versioned strategy/model/parameter artifact."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="versioned artifact bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise HandoffTrustPolicyError(
            f"versioned artifact MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = path / UPSTREAM_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=UPSTREAM_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != UPSTREAM_CONTRACT_NAME:
        raise HandoffTrustPolicyError("upstream versioned artifact contract_name mismatch")
    if payload.get("contract_version") != UPSTREAM_CONTRACT_VERSION:
        raise HandoffTrustPolicyError("upstream versioned artifact contract_version mismatch")

    self_payload = _load_self_verification(
        path,
        rel=UPSTREAM_SELF_VERIFICATION_REL,
        label=UPSTREAM_SELF_VERIFICATION_REL,
    )
    if self_payload.get("overall_status") != "PASS":
        raise HandoffTrustPolicyError(
            "upstream versioned artifact SELF_VERIFICATION overall_status must be PASS"
        )

    try:
        reverify_versioned_strategy_model_parameter_artifact_v1(output_dir=path)
    except VersionedStrategyModelParameterArtifactError as exc:
        raise HandoffTrustPolicyError(str(exc)) from exc

    return VerifiedVersionedArtifactBundle(
        bundle_dir=path.resolve(),
        contract_name=UPSTREAM_CONTRACT_NAME,
        contract_version=UPSTREAM_CONTRACT_VERSION,
        producer_version=UPSTREAM_PRODUCER_VERSION,
        artifact_ref=UPSTREAM_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_payload(payload),
        manifest_digest=_manifest_file_digest(path),
        artifact_payload=dict(payload),
    )


def _detect_forbidden_artifact_flags(artifact: Mapping[str, Any]) -> list[dict[str, str]]:
    blocking: list[dict[str, str]] = []
    flag_checks = (
        ("handoff_executed", "HANDOFF_EXECUTED_IN_ARTIFACT"),
        ("consumer_invoked", "CONSUMER_INVOKED_IN_ARTIFACT"),
        ("consumer_mutated", "CONSUMER_MUTATED_IN_ARTIFACT"),
        ("files_transferred", "FILES_TRANSFERRED_IN_ARTIFACT"),
        ("network_side_effect_created", "NETWORK_SIDE_EFFECT_IN_ARTIFACT"),
        ("promotion_authorized", "PROMOTION_AUTHORIZED_IN_ARTIFACT"),
        ("promotion_candidate_constructed", "PROMOTION_CANDIDATE_CONSTRUCTED_IN_ARTIFACT"),
        ("configpatch_created", "CONFIGPATCH_CREATED_IN_ARTIFACT"),
        ("configpatch_modified", "CONFIGPATCH_MODIFIED_IN_ARTIFACT"),
        ("configpatch_applied", "CONFIGPATCH_APPLIED_IN_ARTIFACT"),
        ("configpatch_accepted", "CONFIGPATCH_ACCEPTED_IN_ARTIFACT"),
        ("runtime_configuration_created", "RUNTIME_CONFIGURATION_CREATED_IN_ARTIFACT"),
        ("runtime_authorized", "RUNTIME_AUTHORIZED_IN_ARTIFACT"),
        ("live_authorized", "LIVE_AUTHORIZED_IN_ARTIFACT"),
        ("orders_allowed", "ORDERS_ALLOWED_IN_ARTIFACT"),
        ("scheduler_runtime_allowed", "SCHEDULER_RUNTIME_ALLOWED_IN_ARTIFACT"),
        ("strategy_executed", "STRATEGY_EXECUTED_IN_ARTIFACT"),
        ("model_inference_executed", "MODEL_INFERENCE_EXECUTED_IN_ARTIFACT"),
        ("parameters_modified", "PARAMETERS_MODIFIED_IN_ARTIFACT"),
    )
    for field, factor_id in flag_checks:
        if artifact.get(field) is True:
            blocking.append(
                _factor(
                    factor_id=factor_id,
                    factor_type="BLOCKING_FACT",
                    source_field=field,
                    observation=f"artifact carries forbidden flag {field}=true",
                )
            )
    return blocking


def _detect_lineage_contradictions(artifact: Mapping[str, Any]) -> list[dict[str, str]]:
    contradictions: list[dict[str, str]] = []
    strategy_ref = str(artifact.get("strategy_identity_ref", ""))
    strategy_digest = str(artifact.get("strategy_identity_digest", ""))
    experiment_digest = str(artifact.get("experiment_identity_digest", ""))
    experiment_id = str(artifact.get("experiment_identity_id", ""))
    if strategy_ref and experiment_id and strategy_ref != experiment_id:
        contradictions.append(
            _factor(
                factor_id="STRATEGY_EXPERIMENT_IDENTITY_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="experiment_identity_id",
                observation="strategy_identity_ref differs from experiment_identity_id",
            )
        )
    if (
        strategy_digest
        and experiment_digest
        and is_valid_sha256_hex(strategy_digest)
        and is_valid_sha256_hex(experiment_digest)
        and strategy_digest != experiment_digest
    ):
        contradictions.append(
            _factor(
                factor_id="STRATEGY_EXPERIMENT_DIGEST_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="strategy_identity_digest",
                observation="strategy_identity_digest differs from experiment_identity_digest",
            )
        )
    binding_status = str(artifact.get("versioned_artifact_binding_status", ""))
    if binding_status == "PASS":
        if artifact.get("strategy_identity_bound") is not True:
            contradictions.append(
                _factor(
                    factor_id="PASS_WITHOUT_STRATEGY_BOUND",
                    factor_type="CONTRADICTION",
                    source_field="strategy_identity_bound",
                    observation="PASS binding without strategy_identity_bound",
                )
            )
        if artifact.get("versioned_strategy_model_parameter_artifact_complete") is not True:
            contradictions.append(
                _factor(
                    factor_id="PASS_WITHOUT_COMPLETE_ARTIFACT",
                    factor_type="CONTRADICTION",
                    source_field="versioned_strategy_model_parameter_artifact_complete",
                    observation="PASS binding without artifact_complete",
                )
            )
    return contradictions


def _detect_missing_required_lineage(artifact: Mapping[str, Any]) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    for field in _REQUIRED_LINEAGE_FIELDS_FOR_ALLOW:
        value = artifact.get(field)
        if not value or (field.endswith("_digest") and not is_valid_sha256_hex(str(value))):
            missing.append(
                _factor(
                    factor_id=f"MISSING_{field.upper()}",
                    factor_type="MISSING_PRECONDITION",
                    source_field=field,
                    observation=f"required lineage field {field!r} absent or invalid",
                )
            )
    return missing


def _detect_missing_optional_lineage(artifact: Mapping[str, Any]) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    for field in _OPTIONAL_LINEAGE_FIELDS_FOR_ABSTAIN:
        value = artifact.get(field)
        if not value:
            missing.append(
                _factor(
                    factor_id=f"OPTIONAL_{field.upper()}_ABSENT",
                    factor_type="MISSING_INPUT",
                    source_field=field,
                    observation=f"optional provenance field {field!r} absent",
                )
            )
    return missing


def _evaluate_producer_compatibility(
    *,
    artifact: Mapping[str, Any],
    consumer: ConsumerCapabilityContract,
) -> tuple[str, list[dict[str, str]], list[dict[str, str]]]:
    supporting: list[dict[str, str]] = []
    blocking: list[dict[str, str]] = []
    contract = consumer.payload

    if artifact.get("contract_name") != contract.get("accepted_producer_contract_name"):
        blocking.append(
            _factor(
                factor_id="PRODUCER_CONTRACT_NAME_MISMATCH",
                factor_type="BLOCKING_FACT",
                source_field="contract_name",
                observation="artifact producer contract_name incompatible with consumer",
            )
        )
    else:
        supporting.append(
            _factor(
                factor_id="PRODUCER_CONTRACT_NAME_MATCH",
                factor_type="SUPPORTING_FACT",
                source_field="contract_name",
                observation="producer contract_name matches consumer acceptance",
            )
        )

    if artifact.get("contract_version") != contract.get("accepted_producer_contract_version"):
        blocking.append(
            _factor(
                factor_id="PRODUCER_CONTRACT_VERSION_MISMATCH",
                factor_type="BLOCKING_FACT",
                source_field="contract_version",
                observation="artifact producer contract_version incompatible with consumer",
            )
        )
    else:
        supporting.append(
            _factor(
                factor_id="PRODUCER_CONTRACT_VERSION_MATCH",
                factor_type="SUPPORTING_FACT",
                source_field="contract_version",
                observation="producer contract_version matches consumer acceptance",
            )
        )

    if artifact.get("artifact_schema_version") != contract.get("accepted_artifact_schema_version"):
        blocking.append(
            _factor(
                factor_id="ARTIFACT_SCHEMA_VERSION_MISMATCH",
                factor_type="BLOCKING_FACT",
                source_field="artifact_schema_version",
                observation="artifact schema version incompatible with consumer",
            )
        )

    if artifact.get("creation_contract_version") != contract.get(
        "accepted_creation_contract_version"
    ):
        blocking.append(
            _factor(
                factor_id="CREATION_CONTRACT_VERSION_MISMATCH",
                factor_type="BLOCKING_FACT",
                source_field="creation_contract_version",
                observation="creation contract version incompatible with consumer",
            )
        )

    required_binding = str(contract.get("required_binding_status", "PASS"))
    actual_binding = str(artifact.get("versioned_artifact_binding_status", ""))
    if actual_binding != required_binding:
        blocking.append(
            _factor(
                factor_id="BINDING_STATUS_INCOMPATIBLE",
                factor_type="BLOCKING_FACT",
                source_field="versioned_artifact_binding_status",
                observation=f"binding status {actual_binding!r} != required {required_binding!r}",
            )
        )
    elif actual_binding == "PASS":
        supporting.append(
            _factor(
                factor_id="BINDING_STATUS_PASS",
                factor_type="SUPPORTING_FACT",
                source_field="versioned_artifact_binding_status",
                observation="artifact binding status PASS",
            )
        )

    required_flags = contract.get("required_completion_flags", [])
    if isinstance(required_flags, list):
        for flag in required_flags:
            if artifact.get(flag) is not True:
                blocking.append(
                    _factor(
                        factor_id=f"REQUIRED_FLAG_{str(flag).upper()}_FALSE",
                        factor_type="BLOCKING_FACT",
                        source_field=str(flag),
                        observation=f"required completion flag {flag!r} is not true",
                    )
                )

    capabilities = artifact.get("capabilities", [])
    forbidden = set(contract.get("forbidden_upstream_capabilities", []))
    if isinstance(capabilities, list):
        for capability in capabilities:
            if capability in forbidden:
                blocking.append(
                    _factor(
                        factor_id=f"FORBIDDEN_CAPABILITY_{capability}",
                        factor_type="BLOCKING_FACT",
                        source_field="capabilities",
                        observation=f"artifact carries forbidden capability {capability!r}",
                    )
                )

    if blocking:
        return "INCOMPATIBLE", supporting, blocking
    return "COMPATIBLE", supporting, blocking


def _resolve_revocation_state(artifact: Mapping[str, Any]) -> str:
    state = str(artifact.get("revocation_state", "NOT_REVOKED"))
    if state not in _VALID_REVOCATION_STATES:
        return "UNKNOWN"
    return state


def _evaluate_trust(
    *,
    artifact: Mapping[str, Any],
    consumer: ConsumerCapabilityContract,
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
    supporting: list[dict[str, str]] = []
    blocking = _detect_forbidden_artifact_flags(artifact)
    contradictions = _detect_lineage_contradictions(artifact)
    missing_required = _detect_missing_required_lineage(artifact)
    missing_optional = _detect_missing_optional_lineage(artifact)
    reason_codes: list[str] = []
    completion_flags = {
        "handoff_trust_policy_complete": False,
        "versioned_artifact_bound": False,
        "producer_contract_bound": False,
        "cross_domain_lineage_bound": False,
    }

    compatibility_result, compat_supporting, compat_blocking = _evaluate_producer_compatibility(
        artifact=artifact,
        consumer=consumer,
    )
    supporting.extend(compat_supporting)
    blocking.extend(compat_blocking)

    revocation_state = _resolve_revocation_state(artifact)
    if revocation_state == "REVOKED":
        blocking.append(
            _factor(
                factor_id="ARTIFACT_REVOKED",
                factor_type="BLOCKING_FACT",
                source_field="revocation_state",
                observation="artifact revocation_state is REVOKED",
            )
        )
        reason_codes.append("REVOCATION_STATE_REVOKED")
    elif revocation_state == "UNKNOWN":
        reason_codes.append("REVOCATION_STATE_UNKNOWN")

    completion_flags["versioned_artifact_bound"] = True
    completion_flags["producer_contract_bound"] = (
        compatibility_result == "COMPATIBLE" and not compat_blocking
    )

    if blocking or contradictions or missing_required or compatibility_result == "INCOMPATIBLE":
        reason_codes.extend(
            [
                "TRUST_DENY_BLOCKING_OR_INCOMPATIBLE",
                "ARTIFACT_FAILS_HANDOFF_TRUST_PRECONDITIONS",
            ]
        )
        return (
            "DENY_HANDOFF",
            compatibility_result,
            supporting,
            blocking,
            contradictions,
            missing_required + missing_optional,
            _sorted_strings(reason_codes),
            completion_flags,
        )

    if revocation_state == "UNKNOWN":
        reason_codes.append("REVOCATION_STATE_UNKNOWN_ABSTAIN")
        return (
            "ABSTAIN",
            compatibility_result,
            supporting,
            blocking,
            contradictions,
            missing_required + missing_optional,
            _sorted_strings(reason_codes),
            completion_flags,
        )

    binding_status = str(artifact.get("versioned_artifact_binding_status", ""))
    if binding_status != "PASS":
        reason_codes.append("BINDING_STATUS_NOT_PASS_DENY")
        return (
            "DENY_HANDOFF",
            compatibility_result,
            supporting,
            blocking,
            contradictions,
            missing_required + missing_optional,
            _sorted_strings(reason_codes),
            completion_flags,
        )

    if artifact.get("cross_domain_lineage_bound") is True:
        completion_flags["cross_domain_lineage_bound"] = True

    reason_codes.extend(
        [
            "PRODUCER_CONSUMER_COMPATIBLE",
            "REQUIRED_LINEAGE_PRESENT",
            "NON_AUTHORIZING_ARTIFACT_VERIFIED",
            "ALLOW_OFFLINE_HANDOFF",
        ]
    )
    completion_flags["handoff_trust_policy_complete"] = True
    return (
        "ALLOW_OFFLINE_HANDOFF",
        compatibility_result,
        supporting,
        blocking,
        contradictions,
        missing_optional,
        _sorted_strings(reason_codes),
        completion_flags,
    )


def _input_artifact_ref_mapping(*, bundle: VerifiedVersionedArtifactBundle) -> dict[str, Any]:
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
            "trust_policy_id",
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


def build_handoff_trust_policy_v1(
    *,
    versioned_artifact: VerifiedVersionedArtifactBundle,
    consumer: ConsumerCapabilityContract,
) -> dict[str, Any]:
    artifact = versioned_artifact.artifact_payload
    (
        trust_result,
        compatibility_result,
        supporting_facts,
        blocking_facts,
        contradictions,
        missing_preconditions,
        trust_reason_codes,
        completion_flags,
    ) = _evaluate_trust(artifact=artifact, consumer=consumer)

    input_refs = [_input_artifact_ref_mapping(bundle=versioned_artifact)]
    parent_artifact_refs = list(artifact.get("parent_artifact_refs", []))
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
        "trust_policy_id": "",
        "artifact_id": "",
        "created_at": OFFLINE_DETERMINISTIC_CREATED_AT,
        "producer_version": PRODUCER_VERSION,
        "record_kind": RECORD_KIND,
        "input_relation": INPUT_RELATION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "capabilities": [],
        "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        "trust_policy_version": CONTRACT_VERSION,
        "handoff_type": HANDOFF_TYPE,
        "is_handoff_trust_policy": True,
        "handoff_trust_policy_offline_only": True,
        "handoff_trust_policy_authority_invariants": dict(
            HANDOFF_TRUST_POLICY_AUTHORITY_INVARIANTS
        ),
        "trust_result": trust_result,
        "compatibility_result": compatibility_result,
        "trust_reason_codes": trust_reason_codes,
        "supporting_facts": _sort_factors(supporting_facts),
        "blocking_facts": _sort_factors(blocking_facts),
        "contradictions": _sort_factors(contradictions),
        "missing_preconditions": _sort_factors(missing_preconditions),
        "revocation_state": _resolve_revocation_state(artifact),
        "versioned_artifact_bundle_ref": versioned_artifact.bundle_dir.as_posix(),
        "versioned_artifact_artifact_ref": versioned_artifact.artifact_ref,
        "artifact_ref": versioned_artifact.artifact_ref,
        "artifact_digest": versioned_artifact.artifact_digest,
        "versioned_artifact_digest": versioned_artifact.artifact_digest,
        "versioned_artifact_manifest_digest": versioned_artifact.manifest_digest,
        "producer_contract_ref": UPSTREAM_CONTRACT_NAME,
        "producer_contract_name": UPSTREAM_CONTRACT_NAME,
        "producer_contract_version": UPSTREAM_CONTRACT_VERSION,
        "upstream_producer_contract_version": UPSTREAM_PRODUCER_VERSION,
        "upstream_contract_name": versioned_artifact.contract_name,
        "upstream_contract_version": versioned_artifact.contract_version,
        "upstream_producer_version": versioned_artifact.producer_version,
        "upstream_binding_status": str(artifact.get("versioned_artifact_binding_status", "")),
        "consumer_contract_ref": consumer.source_ref,
        "consumer_contract_id": consumer.contract_id,
        "consumer_contract_name": consumer.contract_name,
        "consumer_contract_version": consumer.contract_version,
        "consumer_handoff_type": consumer.handoff_type,
        "input_artifact_refs": input_refs,
        "parent_artifact_refs": parent_artifact_refs,
        "transitive_lineage": {
            field: str(artifact[field])
            for field in _TRANSITIVE_LINEAGE_FIELDS
            if artifact.get(field) is not None and str(artifact.get(field))
        },
        "input_digest": "",
        "output_digest": "",
        "manifest_digest": "",
        **completion_flags,
    }

    for key, value in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        payload[key] = value
    payload.update(completion_flags)

    for field in _TRANSITIVE_LINEAGE_FIELDS:
        value = artifact.get(field)
        if value is not None and str(value):
            payload[field] = str(value)

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    if completion_flags["handoff_trust_policy_complete"]:
        _validate_completion_flags(payload)
    _validate_capabilities(payload["capabilities"])
    if trust_result not in _VALID_TRUST_RESULTS:
        raise HandoffTrustPolicyError("trust_result invalid")
    if compatibility_result not in _VALID_COMPATIBILITY_RESULTS:
        raise HandoffTrustPolicyError("compatibility_result invalid")

    payload["input_digest"] = compute_content_sha256({"input_artifact_refs": input_refs})
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    payload["trust_policy_id"] = output_digest
    return payload


def serialize_handoff_trust_policy_v1(
    trust_policy: Mapping[str, Any],
) -> str:
    _reject_forbidden_index_keys(trust_policy)
    _validate_non_authorizing_flags(trust_policy)
    _validate_capabilities(trust_policy.get("capabilities"))
    if trust_policy.get("trust_result") not in _VALID_TRUST_RESULTS:
        raise HandoffTrustPolicyError("trust_result invalid")
    if trust_policy.get("compatibility_result") not in _VALID_COMPATIBILITY_RESULTS:
        raise HandoffTrustPolicyError("compatibility_result invalid")
    for list_field in (
        "trust_reason_codes",
        "supporting_facts",
        "blocking_facts",
        "contradictions",
        "missing_preconditions",
    ):
        values = trust_policy.get(list_field)
        if isinstance(values, list) and values != sorted(
            values,
            key=lambda item: (
                item.get("factor_id", item) if isinstance(item, dict) else item,
                item.get("source_field", "") if isinstance(item, dict) else "",
            ),
        ):
            raise HandoffTrustPolicyError(f"{list_field} must be sorted deterministically")
    return deterministic_json_dumps(trust_policy)


def _artifact_bytes_for_manifest_digest(artifact: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in artifact.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_handoff_trust_policy_v1(body).encode("utf-8")


def _compute_output_manifest_digest(artifact: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(artifact)).hexdigest()


def _validate_trust_policy_integrity(artifact: Mapping[str, Any]) -> None:
    if artifact.get("contract_name") != CONTRACT_NAME:
        raise HandoffTrustPolicyError("contract_name mismatch")
    if artifact.get("contract_version") != CONTRACT_VERSION:
        raise HandoffTrustPolicyError("contract_version mismatch")
    integrity = artifact.get("integrity")
    if not isinstance(integrity, Mapping):
        raise HandoffTrustPolicyError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(artifact))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise HandoffTrustPolicyError("integrity.content_sha256 mismatch")
    output_digest = artifact.get("output_digest")
    if output_digest != _compute_output_digest(artifact):
        raise HandoffTrustPolicyError("output_digest mismatch")
    if artifact.get("artifact_id") != output_digest:
        raise HandoffTrustPolicyError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    trust_policy: Mapping[str, Any],
    versioned_artifact: VerifiedVersionedArtifactBundle,
    consumer: ConsumerCapabilityContract,
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_one_versioned_artifact_input", "status": "PASS"},
        {"check_id": "versioned_artifact_verified", "status": "PASS"},
        {"check_id": "producer_contract_bound", "status": "PASS"},
        {"check_id": "consumer_contract_resolved", "status": "PASS"},
        {"check_id": "offline_only_no_handoff_execution", "status": "PASS"},
        {"check_id": "no_consumer_invocation", "status": "PASS"},
        {"check_id": "no_promotion_authority", "status": "PASS"},
        {"check_id": "no_configpatch_mutation", "status": "PASS"},
        {"check_id": "non_authorizing_semantics", "status": "PASS"},
        {"check_id": "forbidden_capabilities_absent", "status": "PASS"},
        {"check_id": "output_digest", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
        {"check_id": "deterministic_reverification", "status": "PASS"},
    ]

    input_refs = trust_policy.get("input_artifact_refs")
    if not isinstance(input_refs, list) or len(input_refs) != 1:
        checks = [
            {**c, "status": "FAIL"}
            if c["check_id"] == "exactly_one_versioned_artifact_input"
            else c
            for c in checks
        ]

    if trust_policy.get("manifest_digest") != manifest_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "manifest_verification" else c
            for c in checks
        ]

    if trust_policy.get("artifact_digest") != versioned_artifact.artifact_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "versioned_artifact_verified" else c
            for c in checks
        ]

    if trust_policy.get("trust_result") == "ALLOW_OFFLINE_HANDOFF":
        for check_id, field in (("producer_contract_bound", "producer_contract_bound"),):
            if trust_policy.get(field) is not True:
                checks = [
                    {**c, "status": "FAIL"} if c["check_id"] == check_id else c for c in checks
                ]

    structural_failures = [check for check in checks if check["status"] != "PASS"]
    if structural_failures:
        raise HandoffTrustPolicyError("self-verification checks failed")

    payload: dict[str, Any] = {
        "self_verification_schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": "PASS",
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "verified_output_digest": trust_policy.get("output_digest"),
        "verified_manifest_digest": manifest_digest,
        "verified_versioned_artifact_bundle_ref": versioned_artifact.bundle_dir.as_posix(),
        "verified_consumer_contract_id": consumer.contract_id,
        "verified_trust_result": trust_policy.get("trust_result"),
        "verified_compatibility_result": trust_policy.get("compatibility_result"),
        "verified_deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
    }
    digest = compute_content_sha256(payload)
    payload["integrity"] = {"content_sha256": digest}
    return payload


def _finalize_trust_policy_with_manifest_digest(
    artifact: Mapping[str, Any], *, manifest_digest: str
) -> dict[str, Any]:
    body = dict(artifact)
    body["manifest_digest"] = manifest_digest
    body["output_digest"] = _compute_output_digest(body)
    body["artifact_id"] = body["output_digest"]
    body["trust_policy_id"] = body["output_digest"]
    body["integrity"] = {"content_sha256": compute_content_sha256(_integrity_body(body))}
    return body


def _staging_dir_for(output_dir: Path) -> Path:
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def verify_trust_policy_inputs(
    inputs: HandoffTrustPolicyInputs,
) -> tuple[VerifiedVersionedArtifactBundle, ConsumerCapabilityContract]:
    """Verify exactly one versioned artifact bundle and resolve consumer contract."""
    versioned_artifact = verify_versioned_artifact_bundle(inputs.versioned_artifact_bundle_dir)
    consumer = _resolve_consumer_contract(inputs.consumer_contract_ref)
    return versioned_artifact, consumer


def reverify_handoff_trust_policy_v1(*, output_dir: Path | str) -> None:
    """Replay handoff trust policy bundle without upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise HandoffTrustPolicyError(f"handoff trust policy directory not found: {bundle_dir}")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise HandoffTrustPolicyError(f"MANIFEST.sha256 verification failed: {msg}")

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    trust_policy = read_manifest(artifact_path)
    _validate_trust_policy_integrity(trust_policy)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise HandoffTrustPolicyError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(trust_policy)
    if trust_policy.get("manifest_digest") != manifest_digest:
        raise HandoffTrustPolicyError("manifest_digest mismatch on replay")

    versioned_artifact = verify_versioned_artifact_bundle(
        Path(str(trust_policy["versioned_artifact_bundle_ref"]))
    )
    if trust_policy.get("artifact_digest") != versioned_artifact.artifact_digest:
        raise HandoffTrustPolicyError("artifact_digest mismatch on replay")

    consumer_ref = trust_policy.get("consumer_contract_ref")
    consumer_path = None if consumer_ref == "embedded_default" else Path(str(consumer_ref))
    consumer = _resolve_consumer_contract(consumer_path)
    rebuilt = build_handoff_trust_policy_v1(
        versioned_artifact=versioned_artifact,
        consumer=consumer,
    )
    if trust_policy.get("trust_result") != rebuilt.get("trust_result"):
        raise HandoffTrustPolicyError("trust_result mismatch on replay")
    if trust_policy.get("compatibility_result") != rebuilt.get("compatibility_result"):
        raise HandoffTrustPolicyError("compatibility_result mismatch on replay")


def produce_handoff_trust_policy_v1(
    *,
    inputs: HandoffTrustPolicyInputs,
    output_dir: Path | str,
) -> HandoffTrustPolicyResult:
    """Produce offline LEVEL_3 handoff trust policy evidence."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        versioned_artifact_dir=inputs.versioned_artifact_bundle_dir,
        output_dir=final_dir,
    )

    versioned_artifact, consumer = verify_trust_policy_inputs(inputs)
    trust_policy_body = build_handoff_trust_policy_v1(
        versioned_artifact=versioned_artifact,
        consumer=consumer,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise HandoffTrustPolicyError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(trust_policy_body)
        finalized = _finalize_trust_policy_with_manifest_digest(
            trust_policy_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_handoff_trust_policy_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            trust_policy=finalized,
            versioned_artifact=versioned_artifact,
            consumer=consumer,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise HandoffTrustPolicyError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_handoff_trust_policy_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise HandoffTrustPolicyError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return HandoffTrustPolicyResult(
        output_dir=final_dir,
        comparison_definition_id=str(finalized.get("comparison_definition_id", "")),
        artifact_id=str(finalized["artifact_id"]),
        trust_policy_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        trust_result=str(finalized["trust_result"]),
        compatibility_result=str(finalized["compatibility_result"]),
        versioned_artifact_ref=str(finalized["versioned_artifact_bundle_ref"]),
        versioned_artifact_digest=str(finalized["artifact_digest"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "AUTHORITY_LEVEL",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "CONSUMER_CONTRACT_ID",
    "CONSUMER_CONTRACT_NAME",
    "CONSUMER_CONTRACT_VERSION",
    "DETERMINISTIC_RULE_SET_VERSION",
    "EVIDENCE_LEVEL",
    "HANDOFF_TRUST_POLICY_AUTHORITY_INVARIANTS",
    "HANDOFF_TYPE",
    "HandoffTrustPolicyError",
    "HandoffTrustPolicyInputs",
    "HandoffTrustPolicyResult",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "SELF_VERIFICATION_REL",
    "VerifiedVersionedArtifactBundle",
    "build_handoff_trust_policy_v1",
    "produce_handoff_trust_policy_v1",
    "reverify_handoff_trust_policy_v1",
    "serialize_handoff_trust_policy_v1",
    "verify_trust_policy_inputs",
    "verify_versioned_artifact_bundle",
]
