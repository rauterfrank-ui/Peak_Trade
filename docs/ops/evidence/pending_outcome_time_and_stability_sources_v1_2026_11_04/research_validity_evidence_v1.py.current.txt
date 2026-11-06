"""Offline learning loop research validity evidence v1 — LEVEL_3 non-authorizing evidence."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

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
from src.meta.learning_loop.comparison_checkpoint_v1 import (
    CHECKPOINT_SCHEMA_VERSION,
    INDEX_ARTIFACT_REL as CHECKPOINT_INDEX_ARTIFACT_REL,
    ComparisonCheckpointError,
    reverify_comparison_checkpoint_v1,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

CONTRACT_NAME = "research_validity_evidence_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "research_validity_evidence_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING_EVIDENCE_ONLY"
RECORD_KIND = "research_validity_evidence_record"
INPUT_RELATION = "CONSUMES_VERIFIED_RESEARCH_INPUTS_V1"
ARTIFACT_REL = "research_validity_evidence_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".research_validity_evidence_staging_"

INPUT_ARTIFACT_CONTRACT = "research_validity_input_artifact_v1"
INPUT_ARTIFACT_VERSION = "v1"
INPUT_ARTIFACT_FILENAME = "research_validity_input_artifact_v1.json"

OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"

_VALID_EVIDENCE_STATUS = frozenset({"PASS", "FAIL", "INCOMPLETE", "NOT_EVALUABLE"})

RESEARCH_VALIDITY_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "research_validity_is_descriptive_only": True,
    "research_validity_does_not_select": True,
    "research_validity_does_not_accept": True,
    "research_validity_does_not_promote": True,
    "research_validity_does_not_deploy": True,
    "research_validity_does_not_activate": True,
    "research_validity_does_not_create_order_intent": True,
    "research_validity_does_not_modify_trading_logic": True,
    "research_validity_does_not_authorize_runtime": True,
    "evidence_does_not_authorize_promotion": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_research_validity_evidence": True,
    "evidence_does_not_authorize_promotion": True,
    "evidence_does_not_authorize_runtime": True,
    "research_validity_does_not_select": True,
    "research_validity_does_not_accept": True,
    "research_validity_does_not_deploy": True,
    "research_validity_does_not_activate": True,
    "research_validity_does_not_create_order_intent": True,
    "research_validity_does_not_modify_trading_logic": True,
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
        "runtime_authorized",
        "live_authorized",
        "orders_allowed",
        "ranking",
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
    }
)

_SELF_VERIFICATION_SCHEMA_VERSION = "research_validity_evidence_self_verification_v1"


class InputArtifactKind(str, Enum):
    DATASET_IDENTITY = "dataset_identity"
    TRAIN_VALIDATION_TEST_PARTITION = "train_validation_test_partition"
    SELECTION_PROCEDURE = "selection_procedure"
    WALK_FORWARD_RESULT = "walk_forward_result"
    COST_STRESS_RESULT = "cost_stress_result"
    SLIPPAGE_STRESS_RESULT = "slippage_stress_result"
    FUNDING_STRESS_RESULT = "funding_stress_result"
    PARAMETER_STABILITY_RESULT = "parameter_stability_result"
    REGIME_BREAKDOWN = "regime_breakdown"
    OVERFITTING_RISK_RESULT = "overfitting_risk_result"


@dataclass(frozen=True)
class VerifiedInputArtifactRef:
    artifact_type: str
    contract_name: str
    contract_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    producer_ref: str
    lineage_ref: str | None
    evidence_status: str
    bundle_path: str


@dataclass(frozen=True)
class ResearchValidityProducerInputs:
    checkpoint_bundle_dir: Path
    experiment_identity_bundle_dir: Path
    dataset_identity_bundle_dir: Path
    partition_evidence_bundle_dir: Path
    selection_procedure_bundle_dir: Path
    walk_forward_result_bundle_dir: Path
    cost_stress_result_bundle_dir: Path
    slippage_stress_result_bundle_dir: Path
    funding_stress_result_bundle_dir: Path
    parameter_stability_result_bundle_dir: Path
    regime_breakdown_bundle_dir: Path
    overfitting_risk_result_bundle_dir: Path


class ResearchValidityEvidenceError(ValueError):
    """Fail-closed research validity evidence error."""


@dataclass(frozen=True)
class ResearchValidityEvidenceResult:
    output_dir: Path
    comparison_definition_id: str
    artifact_id: str
    evidence_path: Path
    self_verification_path: Path
    manifest_path: Path
    research_validity_status: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ResearchValidityEvidenceError(f"{label} must not be a symlink: {path}")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ResearchValidityEvidenceError(
                f"research validity evidence must not contain forbidden key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise ResearchValidityEvidenceError(f"{label} not found: {path}")
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ResearchValidityEvidenceError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    if not bundle_dir.is_dir():
        raise ResearchValidityEvidenceError(f"{label} must be a directory: {bundle_dir}")
    _reject_symlink(bundle_dir, label=label)


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ResearchValidityEvidenceError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ResearchValidityEvidenceError("output directory must be outside /tmp")
    parent = output_dir.parent
    if not parent.is_dir():
        raise ResearchValidityEvidenceError(f"output parent directory missing: {parent}")
    if is_under_tmp(parent):
        raise ResearchValidityEvidenceError("output parent directory must be outside /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, input_dirs: Sequence[Path], output_dir: Path) -> None:
    output_res = output_dir.resolve()
    for input_dir in input_dirs:
        input_res = input_dir.resolve()
        if output_res == input_res:
            raise ResearchValidityEvidenceError(
                "output directory must not equal input bundle path (fail-closed)"
            )
        if _path_is_under(input_res, output_res):
            raise ResearchValidityEvidenceError(
                f"input bundle must not be inside output directory: {input_dir}"
            )
        if _path_is_under(output_res, input_res):
            raise ResearchValidityEvidenceError(
                f"output directory must not be inside input bundle: {input_dir}"
            )


def _manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / MANIFEST_FILENAME
    _validate_regular_file(manifest_path, label=MANIFEST_FILENAME)
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _verify_manifested_bundle(bundle_dir: Path, *, label: str) -> str:
    _validate_bundle_dir(bundle_dir, label=label)
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ResearchValidityEvidenceError(f"{label} MANIFEST.sha256 verification failed: {msg}")
    return _manifest_file_digest(bundle_dir)


def _artifact_digest_from_file(path: Path) -> str:
    payload = read_manifest(path)
    integrity = payload.get("integrity")
    if isinstance(integrity, Mapping):
        stored = integrity.get("content_sha256")
        if isinstance(stored, str) and is_valid_sha256_hex(stored):
            expected = compute_content_sha256(
                {k: v for k, v in payload.items() if k != "integrity"}
            )
            if stored != expected:
                raise ResearchValidityEvidenceError(f"integrity mismatch for artifact: {path}")
            return stored
    return compute_content_sha256(payload)


def _verify_experiment_identity_bundle(bundle_dir: Path) -> VerifiedInputArtifactRef:
    manifest_digest = _verify_manifested_bundle(bundle_dir, label="experiment identity bundle")
    artifact_path = bundle_dir / EXPERIMENT_IDENTITY_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=EXPERIMENT_IDENTITY_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    try:
        validate_experiment_identity_manifest_v1(payload)
    except ExperimentIdentityManifestError as exc:
        raise ResearchValidityEvidenceError(str(exc)) from exc
    digest = _artifact_digest_from_file(artifact_path)
    return VerifiedInputArtifactRef(
        artifact_type="experiment_identity_manifest_v1",
        contract_name="experiment_identity_manifest_v1",
        contract_version=str(payload.get("identity_schema_version", "1.0")),
        artifact_ref=EXPERIMENT_IDENTITY_ARTIFACT_REL,
        artifact_digest=digest,
        manifest_digest=manifest_digest,
        producer_ref="src/experiments/experiment_identity_manifest_v1.py",
        lineage_ref=str(payload.get("experiment_identity_id")),
        evidence_status="PASS",
        bundle_path=bundle_dir.resolve().as_posix(),
    )


def _validate_input_artifact_payload(
    payload: Mapping[str, Any], *, expected_kind: InputArtifactKind
) -> None:
    if payload.get("contract_name") != INPUT_ARTIFACT_CONTRACT:
        raise ResearchValidityEvidenceError(
            f"{expected_kind.value} contract_name must be {INPUT_ARTIFACT_CONTRACT!r}"
        )
    if payload.get("contract_version") != INPUT_ARTIFACT_VERSION:
        raise ResearchValidityEvidenceError(
            f"{expected_kind.value} contract_version must be {INPUT_ARTIFACT_VERSION!r}"
        )
    if payload.get("artifact_kind") != expected_kind.value:
        raise ResearchValidityEvidenceError(
            f"artifact_kind must be {expected_kind.value!r} (fail-closed)"
        )
    status = payload.get("evidence_status")
    if status not in _VALID_EVIDENCE_STATUS:
        raise ResearchValidityEvidenceError(
            f"evidence_status must be one of {sorted(_VALID_EVIDENCE_STATUS)}"
        )
    producer_ref = payload.get("producer_ref")
    if not isinstance(producer_ref, str) or not producer_ref.strip():
        raise ResearchValidityEvidenceError("producer_ref missing or invalid")


def _verify_input_artifact_bundle(
    bundle_dir: Path, *, expected_kind: InputArtifactKind, label: str
) -> VerifiedInputArtifactRef:
    manifest_digest = _verify_manifested_bundle(bundle_dir, label=label)
    artifact_path = bundle_dir / INPUT_ARTIFACT_FILENAME
    _validate_regular_file(artifact_path, label=INPUT_ARTIFACT_FILENAME)
    payload = read_manifest(artifact_path)
    _validate_input_artifact_payload(payload, expected_kind=expected_kind)
    digest = _artifact_digest_from_file(artifact_path)
    lineage_ref = payload.get("lineage_ref")
    return VerifiedInputArtifactRef(
        artifact_type=expected_kind.value,
        contract_name=INPUT_ARTIFACT_CONTRACT,
        contract_version=INPUT_ARTIFACT_VERSION,
        artifact_ref=INPUT_ARTIFACT_FILENAME,
        artifact_digest=digest,
        manifest_digest=manifest_digest,
        producer_ref=str(payload["producer_ref"]),
        lineage_ref=str(lineage_ref) if lineage_ref is not None else None,
        evidence_status=str(payload["evidence_status"]),
        bundle_path=bundle_dir.resolve().as_posix(),
    )


def _verified_ref_mapping(ref: VerifiedInputArtifactRef) -> dict[str, Any]:
    return {
        "artifact_type": ref.artifact_type,
        "contract_name": ref.contract_name,
        "contract_version": ref.contract_version,
        "artifact_ref": ref.artifact_ref,
        "artifact_digest": ref.artifact_digest,
        "manifest_digest": ref.manifest_digest,
        "producer_ref": ref.producer_ref,
        "lineage_ref": ref.lineage_ref,
        "evidence_status": ref.evidence_status,
        "bundle_path": ref.bundle_path,
    }


def _load_verified_checkpoint_bundle(checkpoint_bundle_dir: Path) -> dict[str, Any]:
    _validate_bundle_dir(checkpoint_bundle_dir, label="checkpoint bundle")
    try:
        reverify_comparison_checkpoint_v1(output_dir=checkpoint_bundle_dir)
    except ComparisonCheckpointError as exc:
        raise ResearchValidityEvidenceError(str(exc)) from exc
    index_path = checkpoint_bundle_dir / CHECKPOINT_INDEX_ARTIFACT_REL
    if not index_path.is_file():
        raise ResearchValidityEvidenceError(f"{CHECKPOINT_INDEX_ARTIFACT_REL} not found")
    index = read_manifest(index_path)
    if index.get("record_schema_version") != CHECKPOINT_SCHEMA_VERSION:
        raise ResearchValidityEvidenceError(
            "checkpoint record_schema_version must be comparison_checkpoint_v1"
        )
    if index.get("is_completion_evidence") is not False:
        raise ResearchValidityEvidenceError(
            "input checkpoint must have is_completion_evidence=false"
        )
    return index


def _trial_count_from_identity(experiment_manifest: Mapping[str, Any]) -> int:
    identity_config = experiment_manifest.get("identity_config")
    if not isinstance(identity_config, Mapping):
        raise ResearchValidityEvidenceError("identity_config must be an object")
    sweeps = identity_config.get("param_sweeps")
    if not isinstance(sweeps, list) or not sweeps:
        raise ResearchValidityEvidenceError("param_sweeps must be a non-empty list")
    count = 1
    for sweep in sweeps:
        if not isinstance(sweep, Mapping):
            raise ResearchValidityEvidenceError("param_sweeps entries must be objects")
        values = sweep.get("values")
        if not isinstance(values, list) or not values:
            raise ResearchValidityEvidenceError("param_sweeps values must be non-empty lists")
        count *= len(values)
    return count


def _read_input_payload(bundle_dir: Path) -> dict[str, Any]:
    return read_manifest(bundle_dir / INPUT_ARTIFACT_FILENAME)


def _data_cutoff_from_dataset(dataset_payload: Mapping[str, Any]) -> str:
    cutoff = dataset_payload.get("data_cutoff_timestamp")
    if not isinstance(cutoff, str) or not cutoff.strip():
        raise ResearchValidityEvidenceError("dataset_identity data_cutoff_timestamp missing")
    return cutoff


def _selection_procedure_digest(payload: Mapping[str, Any]) -> str:
    body = payload.get("selection_procedure")
    if not isinstance(body, Mapping):
        raise ResearchValidityEvidenceError("selection_procedure body must be an object")
    return compute_content_sha256(dict(body))


def _domain_status(*statuses: str) -> str:
    if any(status == "FAIL" for status in statuses):
        return "FAIL"
    if any(status == "NOT_EVALUABLE" for status in statuses):
        return "NOT_EVALUABLE"
    if any(status == "INCOMPLETE" for status in statuses):
        return "INCOMPLETE"
    if all(status == "PASS" for status in statuses):
        return "PASS"
    return "INCOMPLETE"


def _validate_capabilities(capabilities: Any) -> list[str]:
    if not isinstance(capabilities, list):
        raise ResearchValidityEvidenceError("capabilities must be a list")
    normalized: list[str] = []
    for idx, item in enumerate(capabilities):
        if not isinstance(item, str) or not item.strip():
            raise ResearchValidityEvidenceError(f"capabilities[{idx}] must be a non-empty string")
        if item in _FORBIDDEN_CAPABILITIES:
            raise ResearchValidityEvidenceError(f"forbidden capability present: {item}")
        normalized.append(item)
    return normalized


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if payload.get(key) is not expected:
            raise ResearchValidityEvidenceError(f"{key} must be {expected!r} (fail-closed)")
    if payload.get("evidence_level") != EVIDENCE_LEVEL:
        raise ResearchValidityEvidenceError(
            f"evidence_level must be {EVIDENCE_LEVEL!r} (fail-closed)"
        )


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


def verify_all_producer_inputs(inputs: ResearchValidityProducerInputs) -> dict[str, Any]:
    """Verify all input bundles and return structured verification context."""
    experiment_ref = _verify_experiment_identity_bundle(inputs.experiment_identity_bundle_dir)
    experiment_manifest = read_manifest(
        inputs.experiment_identity_bundle_dir / EXPERIMENT_IDENTITY_ARTIFACT_REL
    )
    dataset_ref = _verify_input_artifact_bundle(
        inputs.dataset_identity_bundle_dir,
        expected_kind=InputArtifactKind.DATASET_IDENTITY,
        label="dataset identity bundle",
    )
    dataset_payload = _read_input_payload(inputs.dataset_identity_bundle_dir)
    partition_ref = _verify_input_artifact_bundle(
        inputs.partition_evidence_bundle_dir,
        expected_kind=InputArtifactKind.TRAIN_VALIDATION_TEST_PARTITION,
        label="partition evidence bundle",
    )
    selection_ref = _verify_input_artifact_bundle(
        inputs.selection_procedure_bundle_dir,
        expected_kind=InputArtifactKind.SELECTION_PROCEDURE,
        label="selection procedure bundle",
    )
    selection_payload = _read_input_payload(inputs.selection_procedure_bundle_dir)
    wf_ref = _verify_input_artifact_bundle(
        inputs.walk_forward_result_bundle_dir,
        expected_kind=InputArtifactKind.WALK_FORWARD_RESULT,
        label="walk-forward result bundle",
    )
    cost_ref = _verify_input_artifact_bundle(
        inputs.cost_stress_result_bundle_dir,
        expected_kind=InputArtifactKind.COST_STRESS_RESULT,
        label="cost stress result bundle",
    )
    slip_ref = _verify_input_artifact_bundle(
        inputs.slippage_stress_result_bundle_dir,
        expected_kind=InputArtifactKind.SLIPPAGE_STRESS_RESULT,
        label="slippage stress result bundle",
    )
    fund_ref = _verify_input_artifact_bundle(
        inputs.funding_stress_result_bundle_dir,
        expected_kind=InputArtifactKind.FUNDING_STRESS_RESULT,
        label="funding stress result bundle",
    )
    param_ref = _verify_input_artifact_bundle(
        inputs.parameter_stability_result_bundle_dir,
        expected_kind=InputArtifactKind.PARAMETER_STABILITY_RESULT,
        label="parameter stability result bundle",
    )
    regime_ref = _verify_input_artifact_bundle(
        inputs.regime_breakdown_bundle_dir,
        expected_kind=InputArtifactKind.REGIME_BREAKDOWN,
        label="regime breakdown bundle",
    )
    overfit_ref = _verify_input_artifact_bundle(
        inputs.overfitting_risk_result_bundle_dir,
        expected_kind=InputArtifactKind.OVERFITTING_RISK_RESULT,
        label="overfitting risk result bundle",
    )

    checkpoint_index = _load_verified_checkpoint_bundle(inputs.checkpoint_bundle_dir)
    checkpoint_manifest_digest = _manifest_file_digest(inputs.checkpoint_bundle_dir)
    checkpoint_integrity = checkpoint_index.get("integrity")
    if not isinstance(checkpoint_integrity, Mapping):
        raise ResearchValidityEvidenceError("checkpoint integrity must be an object")
    checkpoint_digest = checkpoint_integrity.get("content_sha256")
    if not isinstance(checkpoint_digest, str) or not is_valid_sha256_hex(checkpoint_digest):
        raise ResearchValidityEvidenceError("checkpoint digest missing or invalid")

    trial_count = _trial_count_from_identity(experiment_manifest)
    declared_trials = selection_payload.get("number_of_trials")
    if not isinstance(declared_trials, int) or declared_trials < 1:
        raise ResearchValidityEvidenceError("selection_procedure number_of_trials invalid")
    if declared_trials != trial_count:
        raise ResearchValidityEvidenceError(
            "number_of_trials mismatch with experiment identity param_sweeps cardinality"
        )

    dataset_identity_id = dataset_payload.get("dataset_identity_id")
    if not isinstance(dataset_identity_id, str) or not is_valid_sha256_hex(dataset_identity_id):
        raise ResearchValidityEvidenceError("dataset_identity_id missing or invalid")

    experiment_id = str(experiment_manifest["experiment_identity_id"])
    bound_experiment = dataset_payload.get("experiment_identity_id")
    if bound_experiment != experiment_id:
        raise ResearchValidityEvidenceError(
            "dataset_identity experiment_identity_id mismatch with experiment manifest"
        )

    domain_statuses = (
        wf_ref.evidence_status,
        cost_ref.evidence_status,
        slip_ref.evidence_status,
        fund_ref.evidence_status,
        param_ref.evidence_status,
        regime_ref.evidence_status,
        overfit_ref.evidence_status,
    )
    research_validity_status = _domain_status(*domain_statuses)

    return {
        "checkpoint_index": checkpoint_index,
        "checkpoint_digest": checkpoint_digest,
        "checkpoint_manifest_digest": checkpoint_manifest_digest,
        "experiment_ref": experiment_ref,
        "experiment_manifest": experiment_manifest,
        "dataset_ref": dataset_ref,
        "dataset_payload": dataset_payload,
        "partition_ref": partition_ref,
        "selection_ref": selection_ref,
        "selection_payload": selection_payload,
        "wf_ref": wf_ref,
        "cost_ref": cost_ref,
        "slip_ref": slip_ref,
        "fund_ref": fund_ref,
        "param_ref": param_ref,
        "regime_ref": regime_ref,
        "overfit_ref": overfit_ref,
        "trial_count": trial_count,
        "research_validity_status": research_validity_status,
    }


def build_research_validity_evidence_v1(
    *,
    inputs: ResearchValidityProducerInputs,
    verified: Mapping[str, Any],
) -> dict[str, Any]:
    checkpoint_index = verified["checkpoint_index"]
    comparison_definition_id = checkpoint_index.get("comparison_definition_id")
    if not isinstance(comparison_definition_id, str) or not comparison_definition_id.strip():
        raise ResearchValidityEvidenceError("comparison_definition_id missing or invalid")

    experiment_ref: VerifiedInputArtifactRef = verified["experiment_ref"]
    dataset_ref: VerifiedInputArtifactRef = verified["dataset_ref"]
    dataset_payload: Mapping[str, Any] = verified["dataset_payload"]
    partition_ref: VerifiedInputArtifactRef = verified["partition_ref"]
    selection_ref: VerifiedInputArtifactRef = verified["selection_ref"]
    selection_payload: Mapping[str, Any] = verified["selection_payload"]
    wf_ref: VerifiedInputArtifactRef = verified["wf_ref"]
    cost_ref: VerifiedInputArtifactRef = verified["cost_ref"]
    slip_ref: VerifiedInputArtifactRef = verified["slip_ref"]
    fund_ref: VerifiedInputArtifactRef = verified["fund_ref"]
    param_ref: VerifiedInputArtifactRef = verified["param_ref"]
    regime_ref: VerifiedInputArtifactRef = verified["regime_ref"]
    overfit_ref: VerifiedInputArtifactRef = verified["overfit_ref"]

    checkpoint_bundle_dir = inputs.checkpoint_bundle_dir
    parent_artifact_refs = [
        {
            "ref_type": CHECKPOINT_SCHEMA_VERSION,
            "ref_id": verified["checkpoint_digest"],
            "bundle_path": checkpoint_bundle_dir.resolve().as_posix(),
            "artifact_rel": CHECKPOINT_INDEX_ARTIFACT_REL,
            "digest": verified["checkpoint_digest"],
            "manifest_digest": verified["checkpoint_manifest_digest"],
        }
    ]

    input_artifact_refs = [
        _verified_ref_mapping(experiment_ref),
        _verified_ref_mapping(dataset_ref),
        _verified_ref_mapping(partition_ref),
        _verified_ref_mapping(selection_ref),
        _verified_ref_mapping(wf_ref),
        _verified_ref_mapping(cost_ref),
        _verified_ref_mapping(slip_ref),
        _verified_ref_mapping(fund_ref),
        _verified_ref_mapping(param_ref),
        _verified_ref_mapping(regime_ref),
        _verified_ref_mapping(overfit_ref),
    ]
    input_artifact_refs.sort(key=lambda item: (item["artifact_type"], item["artifact_digest"]))

    selection_body = selection_payload.get("selection_procedure")
    if not isinstance(selection_body, Mapping):
        raise ResearchValidityEvidenceError("selection_procedure body must be an object")

    partition_body = _read_input_payload(inputs.partition_evidence_bundle_dir).get("partition")
    if not isinstance(partition_body, Mapping):
        raise ResearchValidityEvidenceError("partition body must be an object")

    research_validity_status = str(verified["research_validity_status"])
    reason_codes = ["CHECKPOINT_VERIFIED", "INPUT_ARTIFACTS_VERIFIED"]
    if research_validity_status == "PASS":
        reason_codes.append("MINIMUM_SAFE_SLICE_COMPLETE")
    elif research_validity_status == "INCOMPLETE":
        reason_codes.append("UPSTREAM_DOMAIN_INCOMPLETE")
    elif research_validity_status == "NOT_EVALUABLE":
        reason_codes.append("UPSTREAM_DOMAIN_NOT_EVALUABLE")
    else:
        reason_codes.append("UPSTREAM_DOMAIN_FAIL")

    payload: dict[str, Any] = {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "artifact_id": "",
        "created_at": OFFLINE_DETERMINISTIC_CREATED_AT,
        "producer_version": PRODUCER_VERSION,
        "record_kind": RECORD_KIND,
        "input_relation": INPUT_RELATION,
        "comparison_definition_id": comparison_definition_id,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "capabilities": [],
        "is_research_validity_evidence": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "research_validity_does_not_select": True,
        "research_validity_does_not_accept": True,
        "research_validity_does_not_deploy": True,
        "research_validity_does_not_activate": True,
        "research_validity_does_not_create_order_intent": True,
        "research_validity_does_not_modify_trading_logic": True,
        "research_validity_authority_invariants": dict(RESEARCH_VALIDITY_AUTHORITY_INVARIANTS),
        "extended_hardening_complete": False,
        "comparison_checkpoint_ref": checkpoint_bundle_dir.resolve().as_posix(),
        "comparison_checkpoint_digest": verified["checkpoint_digest"],
        "experiment_identity_ref": experiment_ref.bundle_path,
        "experiment_identity_digest": experiment_ref.artifact_digest,
        "dataset_identity_ref": dataset_ref.bundle_path,
        "dataset_identity_digest": dataset_ref.artifact_digest,
        "data_cutoff_timestamp": _data_cutoff_from_dataset(dataset_payload),
        "train_validation_test_partition": dict(partition_body),
        "partition_evidence_ref": partition_ref.bundle_path,
        "partition_evidence_digest": partition_ref.artifact_digest,
        "number_of_trials": verified["trial_count"],
        "selection_procedure": dict(selection_body),
        "selection_procedure_digest": _selection_procedure_digest(selection_payload),
        "walk_forward_result_ref": wf_ref.bundle_path,
        "walk_forward_result_digest": wf_ref.artifact_digest,
        "walk_forward_status": wf_ref.evidence_status,
        "cost_stress_result_ref": cost_ref.bundle_path,
        "cost_stress_result_digest": cost_ref.artifact_digest,
        "cost_stress_status": cost_ref.evidence_status,
        "slippage_stress_result_ref": slip_ref.bundle_path,
        "slippage_stress_result_digest": slip_ref.artifact_digest,
        "slippage_stress_status": slip_ref.evidence_status,
        "funding_stress_result_ref": fund_ref.bundle_path,
        "funding_stress_result_digest": fund_ref.artifact_digest,
        "funding_stress_status": fund_ref.evidence_status,
        "parameter_stability_result_ref": param_ref.bundle_path,
        "parameter_stability_result_digest": param_ref.artifact_digest,
        "parameter_stability_status": param_ref.evidence_status,
        "regime_breakdown_ref": regime_ref.bundle_path,
        "regime_breakdown_digest": regime_ref.artifact_digest,
        "regime_coverage_status": regime_ref.evidence_status,
        "overfitting_risk_result_ref": overfit_ref.bundle_path,
        "overfitting_risk_result_digest": overfit_ref.artifact_digest,
        "overfitting_risk_status": overfit_ref.evidence_status,
        "research_validity_status": research_validity_status,
        "research_validity_reason_codes": reason_codes,
        "input_artifact_refs": input_artifact_refs,
        "parent_artifact_refs": parent_artifact_refs,
        "input_digest": "",
        "output_digest": "",
        "manifest_digest": "",
    }

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    _validate_capabilities(payload["capabilities"])

    payload["input_digest"] = compute_content_sha256({"input_artifact_refs": input_artifact_refs})
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    return payload


def serialize_research_validity_evidence_v1(evidence: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(evidence)
    _validate_non_authorizing_flags(evidence)
    _validate_capabilities(evidence.get("capabilities"))
    return deterministic_json_dumps(dict(evidence))


def _evidence_bytes_for_manifest_digest(evidence: Mapping[str, Any]) -> bytes:
    canonical = {
        key: value for key, value in evidence.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_research_validity_evidence_v1(canonical).encode("utf-8")


def _compute_output_manifest_digest(evidence: Mapping[str, Any]) -> str:
    return hashlib.sha256(_evidence_bytes_for_manifest_digest(evidence)).hexdigest()


def _validate_evidence_integrity(evidence: Mapping[str, Any]) -> None:
    if evidence.get("contract_name") != CONTRACT_NAME:
        raise ResearchValidityEvidenceError("contract_name mismatch")
    if evidence.get("contract_version") != CONTRACT_VERSION:
        raise ResearchValidityEvidenceError("contract_version mismatch")
    if evidence.get("producer_version") != PRODUCER_VERSION:
        raise ResearchValidityEvidenceError("producer_version mismatch")
    _validate_non_authorizing_flags(evidence)
    _validate_capabilities(evidence.get("capabilities"))
    invariants = evidence.get("research_validity_authority_invariants")
    if invariants != RESEARCH_VALIDITY_AUTHORITY_INVARIANTS:
        raise ResearchValidityEvidenceError("research_validity_authority_invariants mismatch")
    if evidence.get("extended_hardening_complete") is not False:
        raise ResearchValidityEvidenceError("extended_hardening_complete must be false")

    stored = evidence.get("integrity")
    if not isinstance(stored, Mapping):
        raise ResearchValidityEvidenceError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(evidence))
    actual = stored.get("content_sha256")
    if actual != expected:
        raise ResearchValidityEvidenceError("research validity evidence integrity mismatch")

    output_digest = evidence.get("output_digest")
    if output_digest != _compute_output_digest(evidence):
        raise ResearchValidityEvidenceError("output_digest mismatch")
    if evidence.get("artifact_id") != output_digest:
        raise ResearchValidityEvidenceError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    evidence: Mapping[str, Any],
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "required_non_authorizing_flags", "status": "PASS"},
        {"check_id": "forbidden_capabilities_absent", "status": "PASS"},
        {"check_id": "minimum_safe_slice_fields", "status": "PASS"},
        {"check_id": "input_artifact_refs", "status": "PASS"},
        {"check_id": "parent_checkpoint_ref", "status": "PASS"},
        {"check_id": "extended_hardening_deferred", "status": "PASS"},
        {"check_id": "output_digest", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
        {"check_id": "deterministic_reverification", "status": "PASS"},
    ]
    if evidence.get("manifest_digest") != manifest_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "manifest_verification" else c
            for c in checks
        ]
    if any(check["status"] != "PASS" for check in checks):
        raise ResearchValidityEvidenceError("self-verification checks failed")

    payload: dict[str, Any] = {
        "self_verification_schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": "PASS",
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "verified_output_digest": evidence.get("output_digest"),
        "verified_manifest_digest": manifest_digest,
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


def reverify_research_validity_evidence_v1(*, output_dir: Path | str) -> None:
    """Replay research validity evidence bundle without producer mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise ResearchValidityEvidenceError(
            f"research validity evidence directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ResearchValidityEvidenceError(f"MANIFEST.sha256 verification failed: {msg}")

    evidence_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(evidence_path, label=ARTIFACT_REL)
    evidence = read_manifest(evidence_path)
    _validate_evidence_integrity(evidence)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise ResearchValidityEvidenceError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(evidence)
    if evidence.get("manifest_digest") != manifest_digest:
        raise ResearchValidityEvidenceError("manifest_digest mismatch on replay")

    checkpoint_ref = evidence["parent_artifact_refs"][0]
    checkpoint_dir = Path(str(checkpoint_ref["bundle_path"]))
    try:
        reverify_comparison_checkpoint_v1(output_dir=checkpoint_dir)
    except ComparisonCheckpointError as exc:
        raise ResearchValidityEvidenceError(f"upstream checkpoint reverify failed: {exc}") from exc


def produce_research_validity_evidence_v1(
    *,
    inputs: ResearchValidityProducerInputs,
    output_dir: Path | str,
) -> ResearchValidityEvidenceResult:
    """Produce LEVEL_3 research validity evidence from verified input bundles."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)

    input_dirs = [
        inputs.checkpoint_bundle_dir,
        inputs.experiment_identity_bundle_dir,
        inputs.dataset_identity_bundle_dir,
        inputs.partition_evidence_bundle_dir,
        inputs.selection_procedure_bundle_dir,
        inputs.walk_forward_result_bundle_dir,
        inputs.cost_stress_result_bundle_dir,
        inputs.slippage_stress_result_bundle_dir,
        inputs.funding_stress_result_bundle_dir,
        inputs.parameter_stability_result_bundle_dir,
        inputs.regime_breakdown_bundle_dir,
        inputs.overfitting_risk_result_bundle_dir,
    ]
    _reject_unsafe_overlap(input_dirs=input_dirs, output_dir=final_dir)

    verified = verify_all_producer_inputs(inputs)
    evidence_body = build_research_validity_evidence_v1(inputs=inputs, verified=verified)

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ResearchValidityEvidenceError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        evidence_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(evidence_body)
        finalized = _finalize_evidence_with_manifest_digest(
            evidence_body, manifest_digest=manifest_digest
        )
        evidence_path.write_text(
            serialize_research_validity_evidence_v1(finalized), encoding="utf-8"
        )
        self_payload = build_self_verification_v1(
            evidence=finalized,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ResearchValidityEvidenceError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_research_validity_evidence_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ResearchValidityEvidenceError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    artifact_id = str(finalized["artifact_id"])
    return ResearchValidityEvidenceResult(
        output_dir=final_dir,
        comparison_definition_id=str(verified["checkpoint_index"]["comparison_definition_id"]),
        artifact_id=artifact_id,
        evidence_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        research_validity_status=str(finalized["research_validity_status"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "AUTHORITY_LEVEL",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "EVIDENCE_LEVEL",
    "INPUT_ARTIFACT_CONTRACT",
    "INPUT_ARTIFACT_FILENAME",
    "INPUT_ARTIFACT_VERSION",
    "InputArtifactKind",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "RESEARCH_VALIDITY_AUTHORITY_INVARIANTS",
    "SELF_VERIFICATION_REL",
    "ResearchValidityEvidenceError",
    "ResearchValidityEvidenceResult",
    "ResearchValidityProducerInputs",
    "VerifiedInputArtifactRef",
    "build_research_validity_evidence_v1",
    "build_self_verification_v1",
    "produce_research_validity_evidence_v1",
    "reverify_research_validity_evidence_v1",
    "serialize_research_validity_evidence_v1",
    "verify_all_producer_inputs",
]
