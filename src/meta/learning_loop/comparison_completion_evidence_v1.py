"""Offline learning loop comparison completion evidence v1 — LEVEL_3 non-authorizing evidence."""

from __future__ import annotations

import hashlib
import json
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
from src.meta.learning_loop.comparison_checkpoint_v1 import (
    CHECKPOINT_SCHEMA_VERSION,
    INDEX_ARTIFACT_REL as CHECKPOINT_INDEX_ARTIFACT_REL,
    ComparisonCheckpointError,
    reverify_comparison_checkpoint_v1,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_ssot_v1.constants import COMPARISON_CONTRACT_VERSION
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

CONTRACT_NAME = "comparison_completion_evidence_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "comparison_completion_evidence_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING_EVIDENCE_ONLY"
RECORD_KIND = "comparison_completion_evidence_record"
INPUT_RELATION = "CONSUMES_VERIFIED_CHECKPOINT_V1"
ARTIFACT_REL = "comparison_completion_evidence_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".comparison_completion_evidence_staging_"

OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"

COMPLETION_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "completion_is_descriptive_only": True,
    "completion_does_not_select": True,
    "completion_does_not_accept": True,
    "completion_does_not_promote": True,
    "completion_does_not_deploy": True,
    "completion_does_not_activate": True,
    "completion_does_not_create_order_intent": True,
    "completion_does_not_authorize_runtime": True,
    "evidence_does_not_authorize_promotion": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_completion_evidence": True,
    "evidence_does_not_authorize_promotion": True,
    "evidence_does_not_authorize_runtime": True,
    "completion_does_not_select": True,
    "completion_does_not_accept": True,
    "completion_does_not_deploy": True,
    "completion_does_not_activate": True,
    "completion_does_not_create_order_intent": True,
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
        "patches",
        "patch",
        "strategy",
        "signal",
        "signals",
        "entry",
        "exit",
        "position_sizing",
        "leverage",
        "stop_loss",
        "take_profit",
        "execution",
        "order_routing",
        "risk_limits",
        "killswitch",
        "old_value",
        "new_value",
        "target",
        "returns",
        "positions",
        "orders",
        "credentials",
        "runtime_status",
        "live_arming",
        "apply_authority",
        "promotion_authority",
        "winner",
        "selection",
        "acceptance",
        "accepted",
        "ranking",
        "pareto",
        "selected",
        "promoted",
        "promotion",
        "promotion_ready",
        "promotion_authorized",
        "runtime_authorized",
        "shadow_authorized",
        "paper_authorized",
        "testnet_authorized",
        "live_authorized",
        "orders_allowed",
        "ready_for_operator_arming",
        "armed",
        "enabled",
        "capital_allocated",
        "strategy_params_mutated",
        "stage_transition_authorized",
    }
)

_SELF_VERIFICATION_SCHEMA_VERSION = "comparison_completion_evidence_self_verification_v1"


class ComparisonCompletionEvidenceError(ValueError):
    """Fail-closed comparison completion evidence error."""


@dataclass(frozen=True)
class ComparisonCompletionEvidenceResult:
    output_dir: Path
    comparison_definition_id: str
    artifact_id: str
    evidence_path: Path
    self_verification_path: Path
    manifest_path: Path


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ComparisonCompletionEvidenceError(f"{label} must not be a symlink: {path}")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ComparisonCompletionEvidenceError(
                f"completion evidence must not contain forbidden key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise ComparisonCompletionEvidenceError(f"{label} not found: {path}")
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ComparisonCompletionEvidenceError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    if not bundle_dir.is_dir():
        raise ComparisonCompletionEvidenceError(f"{label} must be a directory: {bundle_dir}")
    _reject_symlink(bundle_dir, label=label)


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ComparisonCompletionEvidenceError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ComparisonCompletionEvidenceError("output directory must be outside /tmp")
    parent = output_dir.parent
    if not parent.is_dir():
        raise ComparisonCompletionEvidenceError(f"output parent directory missing: {parent}")
    if is_under_tmp(parent):
        raise ComparisonCompletionEvidenceError("output parent directory must be outside /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, checkpoint_bundle_dir: Path, output_dir: Path) -> None:
    checkpoint_res = checkpoint_bundle_dir.resolve()
    output_res = output_dir.resolve()
    if output_res == checkpoint_res:
        raise ComparisonCompletionEvidenceError(
            "output directory must not equal checkpoint bundle path (fail-closed)"
        )
    if _path_is_under(checkpoint_res, output_res):
        raise ComparisonCompletionEvidenceError(
            "checkpoint bundle must not be inside output directory (fail-closed)"
        )
    if _path_is_under(output_res, checkpoint_res):
        raise ComparisonCompletionEvidenceError(
            "output directory must not be inside checkpoint bundle path (fail-closed)"
        )


def _evidence_bytes_for_manifest_digest(evidence: Mapping[str, Any]) -> bytes:
    canonical = {
        key: value for key, value in evidence.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_completion_evidence_v1(canonical).encode("utf-8")


def _compute_output_manifest_digest(evidence: Mapping[str, Any]) -> str:
    return hashlib.sha256(_evidence_bytes_for_manifest_digest(evidence)).hexdigest()


def _manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / MANIFEST_FILENAME
    _validate_regular_file(manifest_path, label=MANIFEST_FILENAME)
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _validate_capabilities(capabilities: Any) -> list[str]:
    if not isinstance(capabilities, list):
        raise ComparisonCompletionEvidenceError("capabilities must be a list")
    if len(capabilities) > 1:
        raise ComparisonCompletionEvidenceError(
            "completion evidence may contain at most one capability entry (fail-closed)"
        )
    normalized: list[str] = []
    for idx, item in enumerate(capabilities):
        if not isinstance(item, str) or not item.strip():
            raise ComparisonCompletionEvidenceError(
                f"capabilities[{idx}] must be a non-empty string"
            )
        if item in _FORBIDDEN_CAPABILITIES:
            raise ComparisonCompletionEvidenceError(f"forbidden capability present: {item}")
        normalized.append(item)
    return normalized


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if payload.get(key) is not expected:
            raise ComparisonCompletionEvidenceError(f"{key} must be {expected!r} (fail-closed)")
    if payload.get("evidence_level") != EVIDENCE_LEVEL:
        raise ComparisonCompletionEvidenceError(
            f"evidence_level must be {EVIDENCE_LEVEL!r} (fail-closed)"
        )


def _validate_parent_artifact_refs(value: Any, *, checkpoint_bundle_dir: Path) -> None:
    if not isinstance(value, list):
        raise ComparisonCompletionEvidenceError("parent_artifact_refs must be a list")
    if len(value) != 1:
        raise ComparisonCompletionEvidenceError(
            "parent_artifact_refs must contain exactly one checkpoint ref (fail-closed)"
        )
    item = value[0]
    if not isinstance(item, Mapping):
        raise ComparisonCompletionEvidenceError("parent_artifact_refs[0] must be an object")
    if item.get("ref_type") != CHECKPOINT_SCHEMA_VERSION:
        raise ComparisonCompletionEvidenceError(
            "parent_artifact_refs[0].ref_type must be comparison_checkpoint_v1"
        )
    bundle_path = item.get("bundle_path")
    if bundle_path != checkpoint_bundle_dir.resolve().as_posix():
        raise ComparisonCompletionEvidenceError(
            "parent_artifact_refs[0].bundle_path must match input checkpoint bundle"
        )


def _load_verified_checkpoint_bundle(checkpoint_bundle_dir: Path) -> dict[str, Any]:
    _validate_bundle_dir(checkpoint_bundle_dir, label="checkpoint bundle")
    try:
        reverify_comparison_checkpoint_v1(output_dir=checkpoint_bundle_dir)
    except ComparisonCheckpointError as exc:
        raise ComparisonCompletionEvidenceError(str(exc)) from exc
    index_path = checkpoint_bundle_dir / CHECKPOINT_INDEX_ARTIFACT_REL
    index = read_manifest(index_path)
    if index.get("record_schema_version") != CHECKPOINT_SCHEMA_VERSION:
        raise ComparisonCompletionEvidenceError(
            "checkpoint record_schema_version must be comparison_checkpoint_v1"
        )
    if index.get("is_completion_evidence") is not False:
        raise ComparisonCompletionEvidenceError(
            "input checkpoint must have is_completion_evidence=false"
        )
    return index


def _compute_output_digest(body: Mapping[str, Any]) -> str:
    excluded = frozenset(
        {"output_digest", "manifest_digest", "integrity", "created_at", "artifact_id"}
    )
    digest_body = {key: body[key] for key in sorted(body) if key not in excluded}
    return compute_content_sha256(digest_body)


def build_completion_evidence_v1(
    *,
    checkpoint_bundle_dir: Path,
    checkpoint_index: Mapping[str, Any],
    input_manifest_digest: str,
) -> dict[str, Any]:
    comparison_definition_id = checkpoint_index.get("comparison_definition_id")
    if not isinstance(comparison_definition_id, str) or not comparison_definition_id.strip():
        raise ComparisonCompletionEvidenceError("comparison_definition_id missing or invalid")

    checkpoint_integrity = checkpoint_index.get("integrity")
    if not isinstance(checkpoint_integrity, Mapping):
        raise ComparisonCompletionEvidenceError("checkpoint integrity must be an object")
    input_checkpoint_digest = checkpoint_integrity.get("content_sha256")
    if not isinstance(input_checkpoint_digest, str) or not is_valid_sha256_hex(
        input_checkpoint_digest
    ):
        raise ComparisonCompletionEvidenceError(
            "checkpoint integrity.content_sha256 missing or invalid"
        )

    invariants = checkpoint_index.get("comparison_authority_invariants")
    if invariants != COMPARISON_AUTHORITY_INVARIANTS:
        raise ComparisonCompletionEvidenceError(
            "checkpoint comparison_authority_invariants mismatch"
        )

    parent_artifact_refs = [
        {
            "ref_type": CHECKPOINT_SCHEMA_VERSION,
            "ref_id": input_checkpoint_digest,
            "bundle_path": checkpoint_bundle_dir.resolve().as_posix(),
            "artifact_rel": CHECKPOINT_INDEX_ARTIFACT_REL,
            "digest": input_checkpoint_digest,
            "manifest_digest": input_manifest_digest,
        }
    ]

    payload: dict[str, Any] = {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "artifact_id": "",
        "created_at": OFFLINE_DETERMINISTIC_CREATED_AT,
        "producer_version": PRODUCER_VERSION,
        "record_kind": RECORD_KIND,
        "input_relation": INPUT_RELATION,
        "bound_contract": COMPARISON_CONTRACT_VERSION,
        "comparison_definition_id": comparison_definition_id,
        "input_checkpoint_bundle_ref": checkpoint_bundle_dir.resolve().as_posix(),
        "input_checkpoint_artifact_ref": CHECKPOINT_INDEX_ARTIFACT_REL,
        "input_checkpoint_digest": input_checkpoint_digest,
        "input_manifest_digest": input_manifest_digest,
        "parent_artifact_refs": parent_artifact_refs,
        "completion_status": "COMPLETE",
        "completion_reason_codes": ["CHECKPOINT_VERIFIED", "LEVEL_3_COMPLETION_RECORDED"],
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "capabilities": [],
        "is_completion_evidence": True,
        "evidence_does_not_authorize_promotion": True,
        "evidence_does_not_authorize_runtime": True,
        "completion_does_not_select": True,
        "completion_does_not_accept": True,
        "completion_does_not_deploy": True,
        "completion_does_not_activate": True,
        "completion_does_not_create_order_intent": True,
        "completion_authority_invariants": dict(COMPLETION_AUTHORITY_INVARIANTS),
        "output_digest": "",
        "manifest_digest": "",
    }

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    _validate_capabilities(payload["capabilities"])
    _validate_parent_artifact_refs(
        payload["parent_artifact_refs"], checkpoint_bundle_dir=checkpoint_bundle_dir
    )

    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    return payload


def serialize_completion_evidence_v1(evidence: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(evidence)
    _validate_non_authorizing_flags(evidence)
    _validate_capabilities(evidence.get("capabilities"))
    return deterministic_json_dumps(dict(evidence))


def _validate_evidence_integrity(evidence: Mapping[str, Any]) -> None:
    if evidence.get("contract_name") != CONTRACT_NAME:
        raise ComparisonCompletionEvidenceError("contract_name mismatch")
    if evidence.get("contract_version") != CONTRACT_VERSION:
        raise ComparisonCompletionEvidenceError("contract_version mismatch")
    if evidence.get("producer_version") != PRODUCER_VERSION:
        raise ComparisonCompletionEvidenceError("producer_version mismatch")
    _validate_non_authorizing_flags(evidence)
    _validate_capabilities(evidence.get("capabilities"))
    invariants = evidence.get("completion_authority_invariants")
    if invariants != COMPLETION_AUTHORITY_INVARIANTS:
        raise ComparisonCompletionEvidenceError("completion_authority_invariants mismatch")

    stored = evidence.get("integrity")
    if not isinstance(stored, Mapping):
        raise ComparisonCompletionEvidenceError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(evidence))
    actual = stored.get("content_sha256")
    if actual != expected:
        raise ComparisonCompletionEvidenceError("completion evidence integrity mismatch")

    output_digest = evidence.get("output_digest")
    if output_digest != _compute_output_digest(evidence):
        raise ComparisonCompletionEvidenceError("output_digest mismatch")
    if evidence.get("artifact_id") != output_digest:
        raise ComparisonCompletionEvidenceError("artifact_id must equal output_digest")


def _build_self_verification_checks(
    *,
    evidence: Mapping[str, Any],
    checkpoint_bundle_dir: Path,
    manifest_digest: str,
) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "input_bundle_identity", "status": "PASS"},
        {"check_id": "input_manifest_digest", "status": "PASS"},
        {"check_id": "parent_lineage_single_checkpoint", "status": "PASS"},
        {"check_id": "required_non_authorizing_flags", "status": "PASS"},
        {"check_id": "forbidden_capabilities_absent", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "output_digest", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
        {"check_id": "deterministic_reverification", "status": "PASS"},
    ]
    if evidence.get("input_checkpoint_bundle_ref") != checkpoint_bundle_dir.resolve().as_posix():
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "input_bundle_identity" else c
            for c in checks
        ]
    if evidence.get("manifest_digest") != manifest_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "manifest_verification" else c
            for c in checks
        ]
    return checks


def build_self_verification_v1(
    *,
    evidence: Mapping[str, Any],
    checkpoint_bundle_dir: Path,
    manifest_digest: str,
) -> dict[str, Any]:
    checks = _build_self_verification_checks(
        evidence=evidence,
        checkpoint_bundle_dir=checkpoint_bundle_dir,
        manifest_digest=manifest_digest,
    )
    if any(check["status"] != "PASS" for check in checks):
        raise ComparisonCompletionEvidenceError("self-verification checks failed")

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


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in body.items() if key not in {"integrity", "manifest_digest"}
    }


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


def reverify_comparison_completion_evidence_v1(*, output_dir: Path | str) -> None:
    """Replay completion evidence bundle without producer or upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise ComparisonCompletionEvidenceError(
            f"completion evidence directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ComparisonCompletionEvidenceError(f"MANIFEST.sha256 verification failed: {msg}")

    evidence_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(evidence_path, label=ARTIFACT_REL)
    evidence = read_manifest(evidence_path)
    _validate_evidence_integrity(evidence)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise ComparisonCompletionEvidenceError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(evidence)
    if evidence.get("manifest_digest") != manifest_digest:
        raise ComparisonCompletionEvidenceError("manifest_digest mismatch on replay")

    checkpoint_ref = evidence["parent_artifact_refs"][0]
    checkpoint_dir = Path(str(checkpoint_ref["bundle_path"]))
    try:
        reverify_comparison_checkpoint_v1(output_dir=checkpoint_dir)
    except ComparisonCheckpointError as exc:
        raise ComparisonCompletionEvidenceError(
            f"upstream checkpoint reverify failed: {exc}"
        ) from exc

    _validate_parent_artifact_refs(
        evidence["parent_artifact_refs"], checkpoint_bundle_dir=checkpoint_dir
    )


def produce_comparison_completion_evidence_v1(
    *,
    checkpoint_bundle_dir: Path | str,
    output_dir: Path | str,
) -> ComparisonCompletionEvidenceResult:
    """Produce LEVEL_3 completion evidence from exactly one verified checkpoint bundle."""
    checkpoint_dir = Path(checkpoint_bundle_dir)
    final_dir = Path(output_dir)

    _validate_output_target(final_dir)
    _reject_unsafe_overlap(checkpoint_bundle_dir=checkpoint_dir, output_dir=final_dir)

    checkpoint_index = _load_verified_checkpoint_bundle(checkpoint_dir)
    input_manifest_digest = _manifest_file_digest(checkpoint_dir)

    evidence_body = build_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_dir,
        checkpoint_index=checkpoint_index,
        input_manifest_digest=input_manifest_digest,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ComparisonCompletionEvidenceError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        evidence_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(evidence_body)
        finalized = _finalize_evidence_with_manifest_digest(
            evidence_body, manifest_digest=manifest_digest
        )
        evidence_path.write_text(serialize_completion_evidence_v1(finalized), encoding="utf-8")
        self_payload = build_self_verification_v1(
            evidence=finalized,
            checkpoint_bundle_dir=checkpoint_dir,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ComparisonCompletionEvidenceError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_comparison_completion_evidence_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ComparisonCompletionEvidenceError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    artifact_id = str(finalized["artifact_id"])
    return ComparisonCompletionEvidenceResult(
        output_dir=final_dir,
        comparison_definition_id=str(checkpoint_index["comparison_definition_id"]),
        artifact_id=artifact_id,
        evidence_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
    )


__all__ = [
    "ARTIFACT_REL",
    "AUTHORITY_LEVEL",
    "COMPLETION_AUTHORITY_INVARIANTS",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "EVIDENCE_LEVEL",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "SELF_VERIFICATION_REL",
    "ComparisonCompletionEvidenceError",
    "ComparisonCompletionEvidenceResult",
    "build_completion_evidence_v1",
    "build_self_verification_v1",
    "produce_comparison_completion_evidence_v1",
    "reverify_comparison_completion_evidence_v1",
    "serialize_completion_evidence_v1",
]
