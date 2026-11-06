"""Offline LEVEL_3 sibling binding joining completion and research validity evidence v1."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_completion_evidence_v1 import (
    ARTIFACT_REL as COMPLETION_ARTIFACT_REL,
    CONTRACT_NAME as COMPLETION_CONTRACT_NAME,
    CONTRACT_VERSION as COMPLETION_CONTRACT_VERSION,
    PRODUCER_VERSION as COMPLETION_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as COMPLETION_SELF_VERIFICATION_REL,
    ComparisonCompletionEvidenceError,
    reverify_comparison_completion_evidence_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)
from src.meta.learning_loop.research_validity_evidence_v1 import (
    ARTIFACT_REL as VALIDITY_ARTIFACT_REL,
    CONTRACT_NAME as VALIDITY_CONTRACT_NAME,
    CONTRACT_VERSION as VALIDITY_CONTRACT_VERSION,
    PRODUCER_VERSION as VALIDITY_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as VALIDITY_SELF_VERIFICATION_REL,
    ResearchValidityEvidenceError,
    reverify_research_validity_evidence_v1,
)

CONTRACT_NAME = "comparison_completion_research_validity_binding_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "comparison_completion_research_validity_binding_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING_EVIDENCE_ONLY"
RECORD_KIND = "comparison_completion_research_validity_binding_record"
INPUT_RELATION = "BINDS_VERIFIED_COMPLETION_AND_RESEARCH_VALIDITY_V1"
ARTIFACT_REL = "comparison_completion_research_validity_binding_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".comparison_completion_research_validity_binding_staging_"

OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"

_VALID_BINDING_STATUS = frozenset({"PASS", "FAIL", "INCOMPLETE", "NOT_EVALUABLE"})
_VALID_COMPLETION_STATUS = frozenset({"COMPLETE", "FAIL", "INCOMPLETE", "NOT_EVALUABLE"})

BINDING_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "binding_is_descriptive_only": True,
    "binding_does_not_select": True,
    "binding_does_not_accept": True,
    "binding_does_not_promote": True,
    "binding_does_not_deploy": True,
    "binding_does_not_activate": True,
    "binding_does_not_create_order_intent": True,
    "binding_does_not_modify_trading_logic": True,
    "binding_does_not_authorize_runtime": True,
    "evidence_does_not_authorize_promotion": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_completion_research_validity_binding": True,
    "evidence_does_not_authorize_promotion": True,
    "evidence_does_not_authorize_runtime": True,
    "binding_does_not_select": True,
    "binding_does_not_accept": True,
    "binding_does_not_promote": True,
    "binding_does_not_deploy": True,
    "binding_does_not_activate": True,
    "binding_does_not_create_order_intent": True,
    "binding_does_not_modify_trading_logic": True,
    "binding_does_not_authorize_runtime": True,
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
        "promotion_input",
        "is_promotion_input",
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

_SELF_VERIFICATION_SCHEMA_VERSION = (
    "comparison_completion_research_validity_binding_self_verification_v1"
)


class ComparisonCompletionResearchValidityBindingError(ValueError):
    """Fail-closed completion/research validity binding error."""


@dataclass(frozen=True)
class VerifiedEvidenceBundle:
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
class SharedLineageResult:
    status: str
    reason_codes: tuple[str, ...]
    comparison_checkpoint_ref: str
    comparison_checkpoint_digest: str
    experiment_identity_ref: str
    experiment_identity_digest: str
    dataset_identity_ref: str
    dataset_identity_digest: str
    comparison_definition_id: str


@dataclass(frozen=True)
class ComparisonCompletionResearchValidityBindingInputs:
    completion_evidence_bundle_dir: Path
    research_validity_evidence_bundle_dir: Path


@dataclass(frozen=True)
class ComparisonCompletionResearchValidityBindingResult:
    output_dir: Path
    comparison_definition_id: str
    artifact_id: str
    evidence_path: Path
    self_verification_path: Path
    manifest_path: Path
    binding_status: str
    shared_lineage_status: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ComparisonCompletionResearchValidityBindingError(
            f"{label} must not be a symlink: {path}"
        )


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ComparisonCompletionResearchValidityBindingError(
                f"binding artifact must not contain forbidden key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise ComparisonCompletionResearchValidityBindingError(f"{label} not found: {path}")
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ComparisonCompletionResearchValidityBindingError(
            f"{label} must be a regular file: {path}"
        )


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    if not bundle_dir.is_dir():
        raise ComparisonCompletionResearchValidityBindingError(
            f"{label} must be a directory: {bundle_dir}"
        )
    _reject_symlink(bundle_dir, label=label)


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ComparisonCompletionResearchValidityBindingError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ComparisonCompletionResearchValidityBindingError(
            "output directory must be outside /tmp"
        )
    parent = output_dir.parent
    if not parent.is_dir():
        raise ComparisonCompletionResearchValidityBindingError(
            f"output parent directory missing: {parent}"
        )
    if is_under_tmp(parent):
        raise ComparisonCompletionResearchValidityBindingError(
            "output parent directory must be outside /tmp"
        )


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(
    *,
    completion_bundle_dir: Path,
    validity_bundle_dir: Path,
    output_dir: Path,
) -> None:
    output_res = output_dir.resolve()
    for label, bundle_dir in (
        ("completion evidence bundle", completion_bundle_dir),
        ("research validity evidence bundle", validity_bundle_dir),
    ):
        bundle_res = bundle_dir.resolve()
        if output_res == bundle_res:
            raise ComparisonCompletionResearchValidityBindingError(
                f"output directory must not equal {label} path (fail-closed)"
            )
        if _path_is_under(bundle_res, output_res):
            raise ComparisonCompletionResearchValidityBindingError(
                f"{label} must not be inside output directory (fail-closed)"
            )
        if _path_is_under(output_res, bundle_res):
            raise ComparisonCompletionResearchValidityBindingError(
                f"output directory must not be inside {label} path (fail-closed)"
            )


def _manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / MANIFEST_FILENAME
    _validate_regular_file(manifest_path, label=MANIFEST_FILENAME)
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _artifact_digest_from_evidence(evidence: Mapping[str, Any]) -> str:
    stored = evidence.get("output_digest")
    if isinstance(stored, str) and is_valid_sha256_hex(stored):
        return stored
    integrity = evidence.get("integrity")
    if isinstance(integrity, Mapping):
        digest = integrity.get("content_sha256")
        if isinstance(digest, str) and is_valid_sha256_hex(digest):
            return digest
    raise ComparisonCompletionResearchValidityBindingError("evidence digest missing or invalid")


def _validate_capabilities(capabilities: Any) -> list[str]:
    if not isinstance(capabilities, list):
        raise ComparisonCompletionResearchValidityBindingError("capabilities must be a list")
    normalized: list[str] = []
    for idx, item in enumerate(capabilities):
        if not isinstance(item, str) or not item.strip():
            raise ComparisonCompletionResearchValidityBindingError(
                f"capabilities[{idx}] must be a non-empty string"
            )
        if item in _FORBIDDEN_CAPABILITIES:
            raise ComparisonCompletionResearchValidityBindingError(
                f"forbidden capability present: {item}"
            )
        normalized.append(item)
    return normalized


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if payload.get(key) is not expected:
            raise ComparisonCompletionResearchValidityBindingError(
                f"{key} must be {expected!r} (fail-closed)"
            )
    if payload.get("evidence_level") != EVIDENCE_LEVEL:
        raise ComparisonCompletionResearchValidityBindingError(
            f"evidence_level must be {EVIDENCE_LEVEL!r} (fail-closed)"
        )


def _validate_completion_evidence_payload(payload: Mapping[str, Any]) -> None:
    if payload.get("contract_name") != COMPLETION_CONTRACT_NAME:
        raise ComparisonCompletionResearchValidityBindingError("completion contract_name mismatch")
    if payload.get("contract_version") != COMPLETION_CONTRACT_VERSION:
        raise ComparisonCompletionResearchValidityBindingError(
            "completion contract_version not supported"
        )
    if payload.get("producer_version") != COMPLETION_PRODUCER_VERSION:
        raise ComparisonCompletionResearchValidityBindingError(
            "completion producer_version mismatch"
        )
    if payload.get("evidence_level") != EVIDENCE_LEVEL:
        raise ComparisonCompletionResearchValidityBindingError(
            "completion evidence_level must be LEVEL_3"
        )
    if payload.get("is_completion_evidence") is not True:
        raise ComparisonCompletionResearchValidityBindingError(
            "is_completion_evidence must be true"
        )
    for flag in (
        "evidence_does_not_authorize_promotion",
        "evidence_does_not_authorize_runtime",
        "completion_does_not_select",
        "completion_does_not_accept",
        "completion_does_not_deploy",
        "completion_does_not_activate",
        "completion_does_not_create_order_intent",
    ):
        if payload.get(flag) is not True:
            raise ComparisonCompletionResearchValidityBindingError(
                f"completion {flag} must be true"
            )
    _validate_capabilities(payload.get("capabilities"))


def _validate_research_validity_evidence_payload(payload: Mapping[str, Any]) -> None:
    if payload.get("contract_name") != VALIDITY_CONTRACT_NAME:
        raise ComparisonCompletionResearchValidityBindingError(
            "research validity contract_name mismatch"
        )
    if payload.get("contract_version") != VALIDITY_CONTRACT_VERSION:
        raise ComparisonCompletionResearchValidityBindingError(
            "research validity contract_version not supported"
        )
    if payload.get("producer_version") != VALIDITY_PRODUCER_VERSION:
        raise ComparisonCompletionResearchValidityBindingError(
            "research validity producer_version mismatch"
        )
    if payload.get("evidence_level") != EVIDENCE_LEVEL:
        raise ComparisonCompletionResearchValidityBindingError(
            "research validity evidence_level must be LEVEL_3"
        )
    if payload.get("is_research_validity_evidence") is not True:
        raise ComparisonCompletionResearchValidityBindingError(
            "is_research_validity_evidence must be true"
        )
    for flag in (
        "evidence_does_not_authorize_promotion",
        "evidence_does_not_authorize_runtime",
        "research_validity_does_not_select",
        "research_validity_does_not_accept",
        "research_validity_does_not_deploy",
        "research_validity_does_not_activate",
        "research_validity_does_not_create_order_intent",
        "research_validity_does_not_modify_trading_logic",
    ):
        if payload.get(flag) is not True:
            raise ComparisonCompletionResearchValidityBindingError(
                f"research validity {flag} must be true"
            )
    _validate_capabilities(payload.get("capabilities"))


def _load_self_verification(bundle_dir: Path, *, rel: str, label: str) -> dict[str, Any]:
    path = bundle_dir / rel
    _validate_regular_file(path, label=label)
    payload = read_manifest(path)
    if payload.get("overall_status") != "PASS":
        raise ComparisonCompletionResearchValidityBindingError(
            f"{label} overall_status must be PASS"
        )
    return payload


def _normalize_parent_refs(value: Any, *, label: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise ComparisonCompletionResearchValidityBindingError(
            f"{label} parent_artifact_refs must be a list"
        )
    refs: list[dict[str, Any]] = []
    for idx, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ComparisonCompletionResearchValidityBindingError(
                f"{label} parent_artifact_refs[{idx}] must be an object"
            )
        refs.append(dict(item))
    return tuple(refs)


def verify_completion_evidence_bundle(bundle_dir: Path | str) -> VerifiedEvidenceBundle:
    """Fail-closed verification of exactly one completion evidence bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="completion evidence bundle")
    try:
        reverify_comparison_completion_evidence_v1(output_dir=path)
    except ComparisonCompletionEvidenceError as exc:
        raise ComparisonCompletionResearchValidityBindingError(str(exc)) from exc

    evidence_path = path / COMPLETION_ARTIFACT_REL
    if not evidence_path.is_file():
        raise ComparisonCompletionResearchValidityBindingError(
            f"completion artifact not found: {COMPLETION_ARTIFACT_REL}"
        )
    evidence = read_manifest(evidence_path)
    _validate_completion_evidence_payload(evidence)
    _load_self_verification(
        path, rel=COMPLETION_SELF_VERIFICATION_REL, label="completion SELF_VERIFICATION"
    )
    manifest_digest = _manifest_file_digest(path)
    return VerifiedEvidenceBundle(
        bundle_dir=path.resolve(),
        contract_name=str(evidence["contract_name"]),
        contract_version=str(evidence["contract_version"]),
        producer_version=str(evidence["producer_version"]),
        artifact_ref=COMPLETION_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_evidence(evidence),
        manifest_digest=manifest_digest,
        evidence_level=str(evidence["evidence_level"]),
        parent_artifact_refs=_normalize_parent_refs(
            evidence.get("parent_artifact_refs"), label="completion"
        ),
        evidence_payload=dict(evidence),
    )


def verify_research_validity_evidence_bundle(bundle_dir: Path | str) -> VerifiedEvidenceBundle:
    """Fail-closed verification of exactly one research validity evidence bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="research validity evidence bundle")
    try:
        reverify_research_validity_evidence_v1(output_dir=path)
    except ResearchValidityEvidenceError as exc:
        raise ComparisonCompletionResearchValidityBindingError(str(exc)) from exc

    evidence_path = path / VALIDITY_ARTIFACT_REL
    if not evidence_path.is_file():
        raise ComparisonCompletionResearchValidityBindingError(
            f"research validity artifact not found: {VALIDITY_ARTIFACT_REL}"
        )
    evidence = read_manifest(evidence_path)
    _validate_research_validity_evidence_payload(evidence)
    _load_self_verification(
        path, rel=VALIDITY_SELF_VERIFICATION_REL, label="research validity SELF_VERIFICATION"
    )
    manifest_digest = _manifest_file_digest(path)
    return VerifiedEvidenceBundle(
        bundle_dir=path.resolve(),
        contract_name=str(evidence["contract_name"]),
        contract_version=str(evidence["contract_version"]),
        producer_version=str(evidence["producer_version"]),
        artifact_ref=VALIDITY_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_evidence(evidence),
        manifest_digest=manifest_digest,
        evidence_level=str(evidence["evidence_level"]),
        parent_artifact_refs=_normalize_parent_refs(
            evidence.get("parent_artifact_refs"), label="research validity"
        ),
        evidence_payload=dict(evidence),
    )


def check_shared_lineage(
    *,
    completion: VerifiedEvidenceBundle,
    validity: VerifiedEvidenceBundle,
) -> SharedLineageResult:
    """Fail-closed shared lineage lock across completion and research validity evidence."""
    completion_payload = completion.evidence_payload
    validity_payload = validity.evidence_payload

    reason_codes: list[str] = []

    completion_checkpoint_ref = str(completion_payload.get("input_checkpoint_bundle_ref", ""))
    completion_checkpoint_digest = str(completion_payload.get("input_checkpoint_digest", ""))
    validity_checkpoint_ref = str(validity_payload.get("comparison_checkpoint_ref", ""))
    validity_checkpoint_digest = str(validity_payload.get("comparison_checkpoint_digest", ""))

    experiment_ref = str(validity_payload.get("experiment_identity_ref", ""))
    experiment_digest = str(validity_payload.get("experiment_identity_digest", ""))
    dataset_ref = str(validity_payload.get("dataset_identity_ref", ""))
    dataset_digest = str(validity_payload.get("dataset_identity_digest", ""))

    completion_definition_id = str(completion_payload.get("comparison_definition_id", ""))
    validity_definition_id = str(validity_payload.get("comparison_definition_id", ""))

    if not completion_checkpoint_ref or not validity_checkpoint_ref:
        raise ComparisonCompletionResearchValidityBindingError(
            "comparison checkpoint ref missing on input evidence"
        )
    if completion_checkpoint_ref != validity_checkpoint_ref:
        raise ComparisonCompletionResearchValidityBindingError(
            "completion and research validity comparison_checkpoint_ref mismatch (fail-closed)"
        )
    if completion_checkpoint_digest != validity_checkpoint_digest:
        raise ComparisonCompletionResearchValidityBindingError(
            "completion and research validity comparison_checkpoint_digest mismatch (fail-closed)"
        )
    if completion_definition_id != validity_definition_id:
        raise ComparisonCompletionResearchValidityBindingError(
            "comparison_definition_id mismatch between completion and research validity"
        )
    if not experiment_ref or not is_valid_sha256_hex(experiment_digest):
        raise ComparisonCompletionResearchValidityBindingError(
            "experiment identity ref/digest missing or invalid on research validity evidence"
        )
    if not dataset_ref or not is_valid_sha256_hex(dataset_digest):
        raise ComparisonCompletionResearchValidityBindingError(
            "dataset identity ref/digest missing or invalid on research validity evidence"
        )

    if len(completion.parent_artifact_refs) != 1 or len(validity.parent_artifact_refs) != 1:
        raise ComparisonCompletionResearchValidityBindingError(
            "parent_artifact_refs must contain exactly one checkpoint ref on each input"
        )

    completion_parent = completion.parent_artifact_refs[0]
    validity_parent = validity.parent_artifact_refs[0]
    if completion_parent.get("ref_type") != validity_parent.get("ref_type"):
        raise ComparisonCompletionResearchValidityBindingError(
            "parent checkpoint ref_type mismatch"
        )
    if str(completion_parent.get("digest", "")) != str(validity_parent.get("digest", "")):
        raise ComparisonCompletionResearchValidityBindingError(
            "parent checkpoint digest mismatch (fail-closed)"
        )
    if str(completion_parent.get("bundle_path", "")) != str(validity_parent.get("bundle_path", "")):
        raise ComparisonCompletionResearchValidityBindingError(
            "parent checkpoint bundle_path mismatch (fail-closed)"
        )
    if str(completion_parent.get("digest", "")) != completion_checkpoint_digest:
        raise ComparisonCompletionResearchValidityBindingError(
            "completion parent checkpoint digest inconsistent with input_checkpoint_digest"
        )
    if str(validity_parent.get("digest", "")) != validity_checkpoint_digest:
        raise ComparisonCompletionResearchValidityBindingError(
            "validity parent checkpoint digest inconsistent with comparison_checkpoint_digest"
        )

    reason_codes.extend(
        [
            "CHECKPOINT_REF_MATCH",
            "CHECKPOINT_DIGEST_MATCH",
            "EXPERIMENT_IDENTITY_BOUND",
            "DATASET_IDENTITY_BOUND",
            "COMPARISON_DEFINITION_ID_MATCH",
            "PARENT_REFS_CONSISTENT",
        ]
    )

    return SharedLineageResult(
        status="PASS",
        reason_codes=tuple(reason_codes),
        comparison_checkpoint_ref=completion_checkpoint_ref,
        comparison_checkpoint_digest=completion_checkpoint_digest,
        experiment_identity_ref=experiment_ref,
        experiment_identity_digest=experiment_digest,
        dataset_identity_ref=dataset_ref,
        dataset_identity_digest=dataset_digest,
        comparison_definition_id=completion_definition_id,
    )


def _derive_binding_status(
    *,
    shared_lineage_status: str,
    completion_status: str,
    research_validity_status: str,
) -> tuple[str, list[str]]:
    reason_codes: list[str] = []
    if shared_lineage_status != "PASS":
        return "FAIL", ["SHARED_LINEAGE_FAIL"]

    if completion_status not in _VALID_COMPLETION_STATUS:
        return "FAIL", ["COMPLETION_STATUS_UNKNOWN"]
    if research_validity_status not in _VALID_BINDING_STATUS:
        return "FAIL", ["RESEARCH_VALIDITY_STATUS_UNKNOWN"]

    if completion_status != "COMPLETE":
        reason_codes.append("COMPLETION_STATUS_NOT_COMPLETE")
        return "FAIL", reason_codes

    if research_validity_status == "FAIL":
        reason_codes.append("UPSTREAM_RESEARCH_VALIDITY_FAIL")
        return "FAIL", reason_codes
    if research_validity_status == "INCOMPLETE":
        reason_codes.append("UPSTREAM_RESEARCH_VALIDITY_INCOMPLETE")
        return "INCOMPLETE", reason_codes
    if research_validity_status == "NOT_EVALUABLE":
        reason_codes.append("UPSTREAM_RESEARCH_VALIDITY_NOT_EVALUABLE")
        return "NOT_EVALUABLE", reason_codes

    reason_codes.extend(["COMPLETION_COMPLETE", "RESEARCH_VALIDITY_PASS"])
    return "PASS", reason_codes


def _input_artifact_ref_mapping(bundle: VerifiedEvidenceBundle) -> dict[str, Any]:
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


def build_comparison_completion_research_validity_binding_v1(
    *,
    completion: VerifiedEvidenceBundle,
    validity: VerifiedEvidenceBundle,
    shared_lineage: SharedLineageResult,
) -> dict[str, Any]:
    completion_payload = completion.evidence_payload
    validity_payload = validity.evidence_payload

    completion_status = str(completion_payload.get("completion_status", ""))
    research_validity_status = str(validity_payload.get("research_validity_status", ""))
    binding_status, binding_reason_codes = _derive_binding_status(
        shared_lineage_status=shared_lineage.status,
        completion_status=completion_status,
        research_validity_status=research_validity_status,
    )

    input_refs = [
        _input_artifact_ref_mapping(completion),
        _input_artifact_ref_mapping(validity),
    ]
    input_refs.sort(key=lambda item: (item["artifact_type"], item["artifact_digest"]))

    parent_artifact_refs = list(validity.parent_artifact_refs)
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
        "is_completion_research_validity_binding": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "binding_does_not_select": True,
        "binding_does_not_accept": True,
        "binding_does_not_promote": True,
        "binding_does_not_deploy": True,
        "binding_does_not_activate": True,
        "binding_does_not_create_order_intent": True,
        "binding_does_not_modify_trading_logic": True,
        "binding_does_not_authorize_runtime": True,
        "binding_authority_invariants": dict(BINDING_AUTHORITY_INVARIANTS),
        "completion_evidence_bundle_ref": completion.bundle_dir.as_posix(),
        "completion_evidence_artifact_ref": completion.artifact_ref,
        "completion_evidence_digest": completion.artifact_digest,
        "completion_manifest_digest": completion.manifest_digest,
        "research_validity_bundle_ref": validity.bundle_dir.as_posix(),
        "research_validity_artifact_ref": validity.artifact_ref,
        "research_validity_digest": validity.artifact_digest,
        "research_validity_manifest_digest": validity.manifest_digest,
        "comparison_checkpoint_ref": shared_lineage.comparison_checkpoint_ref,
        "comparison_checkpoint_digest": shared_lineage.comparison_checkpoint_digest,
        "experiment_identity_ref": shared_lineage.experiment_identity_ref,
        "experiment_identity_digest": shared_lineage.experiment_identity_digest,
        "dataset_identity_ref": shared_lineage.dataset_identity_ref,
        "dataset_identity_digest": shared_lineage.dataset_identity_digest,
        "comparison_definition_id": shared_lineage.comparison_definition_id,
        "completion_status": completion_status,
        "research_validity_status": research_validity_status,
        "shared_lineage_status": shared_lineage.status,
        "shared_lineage_reason_codes": list(shared_lineage.reason_codes),
        "binding_status": binding_status,
        "binding_reason_codes": binding_reason_codes,
        "completion_contract_name": completion.contract_name,
        "completion_contract_version": completion.contract_version,
        "completion_producer_version": completion.producer_version,
        "research_validity_contract_name": validity.contract_name,
        "research_validity_contract_version": validity.contract_version,
        "research_validity_producer_version": validity.producer_version,
        "input_artifact_refs": input_refs,
        "parent_artifact_refs": parent_artifact_refs,
        "input_digest": "",
        "output_digest": "",
        "manifest_digest": "",
    }

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    _validate_capabilities(payload["capabilities"])

    payload["input_digest"] = compute_content_sha256({"input_artifact_refs": input_refs})
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    return payload


def serialize_comparison_completion_research_validity_binding_v1(
    evidence: Mapping[str, Any],
) -> str:
    _reject_forbidden_index_keys(evidence)
    _validate_non_authorizing_flags(evidence)
    _validate_capabilities(evidence.get("capabilities"))
    binding_status = evidence.get("binding_status")
    if binding_status not in _VALID_BINDING_STATUS:
        raise ComparisonCompletionResearchValidityBindingError(
            f"binding_status must be one of {sorted(_VALID_BINDING_STATUS)}"
        )
    return deterministic_json_dumps(dict(evidence))


def _evidence_bytes_for_manifest_digest(evidence: Mapping[str, Any]) -> bytes:
    canonical = {
        key: value for key, value in evidence.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_comparison_completion_research_validity_binding_v1(canonical).encode("utf-8")


def _compute_output_manifest_digest(evidence: Mapping[str, Any]) -> str:
    return hashlib.sha256(_evidence_bytes_for_manifest_digest(evidence)).hexdigest()


def _validate_evidence_integrity(evidence: Mapping[str, Any]) -> None:
    if evidence.get("contract_name") != CONTRACT_NAME:
        raise ComparisonCompletionResearchValidityBindingError("contract_name mismatch")
    if evidence.get("contract_version") != CONTRACT_VERSION:
        raise ComparisonCompletionResearchValidityBindingError("contract_version mismatch")
    if evidence.get("producer_version") != PRODUCER_VERSION:
        raise ComparisonCompletionResearchValidityBindingError("producer_version mismatch")
    _validate_non_authorizing_flags(evidence)
    _validate_capabilities(evidence.get("capabilities"))
    invariants = evidence.get("binding_authority_invariants")
    if invariants != BINDING_AUTHORITY_INVARIANTS:
        raise ComparisonCompletionResearchValidityBindingError(
            "binding_authority_invariants mismatch"
        )

    stored = evidence.get("integrity")
    if not isinstance(stored, Mapping):
        raise ComparisonCompletionResearchValidityBindingError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(evidence))
    actual = stored.get("content_sha256")
    if actual != expected:
        raise ComparisonCompletionResearchValidityBindingError(
            "binding evidence integrity mismatch"
        )

    output_digest = evidence.get("output_digest")
    if output_digest != _compute_output_digest(evidence):
        raise ComparisonCompletionResearchValidityBindingError("output_digest mismatch")
    if evidence.get("artifact_id") != output_digest:
        raise ComparisonCompletionResearchValidityBindingError(
            "artifact_id must equal output_digest"
        )


def build_self_verification_v1(
    *,
    evidence: Mapping[str, Any],
    completion: VerifiedEvidenceBundle,
    validity: VerifiedEvidenceBundle,
    shared_lineage: SharedLineageResult,
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_two_direct_inputs", "status": "PASS"},
        {"check_id": "completion_contract_and_version", "status": "PASS"},
        {"check_id": "research_validity_contract_and_version", "status": "PASS"},
        {"check_id": "input_manifests_verified", "status": "PASS"},
        {"check_id": "input_self_verifications_pass", "status": "PASS"},
        {"check_id": "shared_checkpoint_lineage", "status": "PASS"},
        {"check_id": "shared_experiment_lineage", "status": "PASS"},
        {"check_id": "shared_dataset_lineage", "status": "PASS"},
        {"check_id": "parent_and_input_refs", "status": "PASS"},
        {"check_id": "required_fields", "status": "PASS"},
        {"check_id": "binding_status_present", "status": "PASS"},
        {"check_id": "non_authorizing_semantics", "status": "PASS"},
        {"check_id": "forbidden_capabilities_absent", "status": "PASS"},
        {"check_id": "canonical_serialization", "status": "PASS"},
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

    if shared_lineage.status != "PASS":
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "shared_checkpoint_lineage" else c
            for c in checks
        ]

    if evidence.get("completion_evidence_bundle_ref") != completion.bundle_dir.as_posix():
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "input_manifests_verified" else c
            for c in checks
        ]
    if evidence.get("research_validity_bundle_ref") != validity.bundle_dir.as_posix():
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "input_manifests_verified" else c
            for c in checks
        ]

    if any(check["status"] != "PASS" for check in checks):
        raise ComparisonCompletionResearchValidityBindingError("self-verification checks failed")

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


def verify_binding_inputs(
    inputs: ComparisonCompletionResearchValidityBindingInputs,
) -> tuple[VerifiedEvidenceBundle, VerifiedEvidenceBundle, SharedLineageResult]:
    """Verify exactly one completion and one research validity bundle with shared lineage."""
    completion = verify_completion_evidence_bundle(inputs.completion_evidence_bundle_dir)
    validity = verify_research_validity_evidence_bundle(
        inputs.research_validity_evidence_bundle_dir
    )
    shared_lineage = check_shared_lineage(completion=completion, validity=validity)
    return completion, validity, shared_lineage


def reverify_comparison_completion_research_validity_binding_v1(
    *,
    output_dir: Path | str,
) -> None:
    """Replay binding bundle without producer or upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise ComparisonCompletionResearchValidityBindingError(
            f"binding directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ComparisonCompletionResearchValidityBindingError(
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
        raise ComparisonCompletionResearchValidityBindingError(
            "SELF_VERIFICATION overall_status must be PASS"
        )

    manifest_digest = _compute_output_manifest_digest(evidence)
    if evidence.get("manifest_digest") != manifest_digest:
        raise ComparisonCompletionResearchValidityBindingError("manifest_digest mismatch on replay")

    completion_dir = Path(str(evidence["completion_evidence_bundle_ref"]))
    validity_dir = Path(str(evidence["research_validity_bundle_ref"]))
    completion = verify_completion_evidence_bundle(completion_dir)
    validity = verify_research_validity_evidence_bundle(validity_dir)
    shared_lineage = check_shared_lineage(completion=completion, validity=validity)

    if evidence.get("shared_lineage_status") != shared_lineage.status:
        raise ComparisonCompletionResearchValidityBindingError(
            "shared_lineage_status mismatch on replay"
        )
    if evidence.get("comparison_checkpoint_digest") != shared_lineage.comparison_checkpoint_digest:
        raise ComparisonCompletionResearchValidityBindingError(
            "comparison_checkpoint_digest mismatch on replay"
        )


def produce_comparison_completion_research_validity_binding_v1(
    *,
    inputs: ComparisonCompletionResearchValidityBindingInputs,
    output_dir: Path | str,
) -> ComparisonCompletionResearchValidityBindingResult:
    """Bind exactly one verified completion bundle and one verified research validity bundle."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        completion_bundle_dir=inputs.completion_evidence_bundle_dir,
        validity_bundle_dir=inputs.research_validity_evidence_bundle_dir,
        output_dir=final_dir,
    )

    completion, validity, shared_lineage = verify_binding_inputs(inputs)
    evidence_body = build_comparison_completion_research_validity_binding_v1(
        completion=completion,
        validity=validity,
        shared_lineage=shared_lineage,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ComparisonCompletionResearchValidityBindingError(
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
            serialize_comparison_completion_research_validity_binding_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            evidence=finalized,
            completion=completion,
            validity=validity,
            shared_lineage=shared_lineage,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ComparisonCompletionResearchValidityBindingError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_comparison_completion_research_validity_binding_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ComparisonCompletionResearchValidityBindingError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    artifact_id = str(finalized["artifact_id"])
    return ComparisonCompletionResearchValidityBindingResult(
        output_dir=final_dir,
        comparison_definition_id=str(finalized["comparison_definition_id"]),
        artifact_id=artifact_id,
        evidence_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        binding_status=str(finalized["binding_status"]),
        shared_lineage_status=str(finalized["shared_lineage_status"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "AUTHORITY_LEVEL",
    "BINDING_AUTHORITY_INVARIANTS",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "EVIDENCE_LEVEL",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "SELF_VERIFICATION_REL",
    "ComparisonCompletionResearchValidityBindingError",
    "ComparisonCompletionResearchValidityBindingInputs",
    "ComparisonCompletionResearchValidityBindingResult",
    "SharedLineageResult",
    "VerifiedEvidenceBundle",
    "build_comparison_completion_research_validity_binding_v1",
    "build_self_verification_v1",
    "check_shared_lineage",
    "produce_comparison_completion_research_validity_binding_v1",
    "reverify_comparison_completion_research_validity_binding_v1",
    "serialize_comparison_completion_research_validity_binding_v1",
    "verify_binding_inputs",
    "verify_completion_evidence_bundle",
    "verify_research_validity_evidence_bundle",
]
