"""Offline Package E21 — durable evidence binding for EXPERIMENT identity + LineageRef v1."""

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
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME,
    ExperimentIdentityManifestError,
    validate_experiment_identity_manifest_v1,
)
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    CandidateLineageManifestError,
    LineageRef,
    LineageRefType,
    LineageRelation,
    lineage_ref_from_mapping,
    lineage_ref_to_mapping,
)
from src.governance.promotion_loop.experiment_lineage_ref_producer_v1 import (
    EXPERIMENT_OWNER_DOMAIN,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

BINDING_SCHEMA_VERSION = "experiment_durable_evidence_binding_v1"
MANIFEST_ARTIFACT_REL = ARTIFACT_FILENAME
LINEAGE_REF_ARTIFACT_REL = "experiment_lineage_ref_v1.json"
INDEX_ARTIFACT_REL = "experiment_durable_evidence_binding_index_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".experiment_durable_evidence_staging_"

FUTURES_SCOPE_REF: dict[str, bool] = {
    "futures_only": True,
    "bitcoin_direction_allowed": False,
}
TRADING_LOGIC_IMMUTABILITY_REF: dict[str, bool] = {
    "trading_logic_immutability": True,
}

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
        "completion",
        "checkpoint",
        "params",
        "metrics",
        "tags",
    }
)


class ExperimentDurableEvidenceBindingError(ValueError):
    """Fail-closed Package E21 EXPERIMENT durable evidence binding error."""


@dataclass(frozen=True)
class BoundArtifactRecord:
    artifact_kind: str
    relative_path: str
    content_sha256: str


@dataclass(frozen=True)
class ExperimentBindingCrossReferences:
    experiment_identity_id: str
    lineage_ref_digest: str
    lineage_ref_artifact_path: str


@dataclass(frozen=True)
class ExperimentDurableEvidenceBindingResult:
    output_dir: Path
    experiment_identity_id: str
    binding_index_path: Path
    manifest_path: Path


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ExperimentDurableEvidenceBindingError(f"{label} must not be a symlink: {path}")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ExperimentDurableEvidenceBindingError(
                f"binding index must not contain forbidden key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise ExperimentDurableEvidenceBindingError(f"{label} not found: {path}")
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ExperimentDurableEvidenceBindingError(f"{label} must be a regular file: {path}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ExperimentDurableEvidenceBindingError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ExperimentDurableEvidenceBindingError("output directory must be outside /tmp")
    parent = output_dir.parent
    if not parent.is_dir():
        raise ExperimentDurableEvidenceBindingError(f"output parent directory missing: {parent}")
    if is_under_tmp(parent):
        raise ExperimentDurableEvidenceBindingError("output parent directory must be outside /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _resolve_existing_directory(path: Path, *, label: str) -> Path:
    if not path.exists():
        raise ExperimentDurableEvidenceBindingError(f"{label} not found: {path}")
    _reject_symlink(path, label=label)
    if not path.is_dir():
        raise ExperimentDurableEvidenceBindingError(f"{label} is not a directory: {path}")
    return path.resolve()


def _load_validated_identity_manifest(
    manifest_dir: Path,
) -> tuple[dict[str, Any], Path, bytes]:
    manifest_path = manifest_dir / ARTIFACT_FILENAME
    _validate_regular_file(manifest_path, label=ARTIFACT_FILENAME)
    resolved = manifest_path.resolve()
    if not _path_is_under(resolved, manifest_dir.resolve()):
        raise ExperimentDurableEvidenceBindingError(
            f"{ARTIFACT_FILENAME} escapes manifest_dir root: {manifest_path}"
        )

    manifest_bytes = manifest_path.read_bytes()
    try:
        data = json.loads(manifest_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ExperimentDurableEvidenceBindingError(
            f"invalid {ARTIFACT_FILENAME} in manifest_dir={manifest_dir}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise ExperimentDurableEvidenceBindingError(
            f"{ARTIFACT_FILENAME} root must be a JSON object for manifest_dir={manifest_dir}"
        )
    try:
        validate_experiment_identity_manifest_v1(data)
    except ExperimentIdentityManifestError as exc:
        raise ExperimentDurableEvidenceBindingError(
            f"experiment identity manifest validation failed for manifest_dir={manifest_dir}: {exc}"
        ) from exc
    return data, manifest_path, manifest_bytes


def _load_lineage_ref_from_json_path(path: Path) -> LineageRef:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ExperimentDurableEvidenceBindingError(
            f"failed to read lineage ref file: {path}"
        ) from exc
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ExperimentDurableEvidenceBindingError(
            f"invalid JSON in lineage ref file: {path}"
        ) from exc
    if not isinstance(data, Mapping):
        raise ExperimentDurableEvidenceBindingError("lineage ref root must be a JSON object")
    try:
        return lineage_ref_from_mapping(data)
    except CandidateLineageManifestError as exc:
        raise ExperimentDurableEvidenceBindingError(str(exc)) from exc


def _reject_unsafe_overlap(
    *,
    manifest_dir: Path,
    lineage_ref_path: Path,
    output_dir: Path,
) -> None:
    manifest_res = manifest_dir.resolve()
    lineage_res = lineage_ref_path.resolve()
    output_res = output_dir.resolve()

    if output_res in {manifest_res, lineage_res}:
        raise ExperimentDurableEvidenceBindingError(
            "output directory must not equal a source path (fail-closed)"
        )

    if _path_is_under(manifest_res, output_res) or _path_is_under(lineage_res, output_res):
        raise ExperimentDurableEvidenceBindingError(
            "source path must not be inside output directory (fail-closed)"
        )

    if _path_is_under(output_res, manifest_res) or _path_is_under(output_res, lineage_res):
        raise ExperimentDurableEvidenceBindingError(
            "output directory must not be inside a source path (fail-closed)"
        )


def _validate_bundle_relative_path(rel: str) -> None:
    candidate = Path(rel)
    if candidate.is_absolute():
        raise ExperimentDurableEvidenceBindingError(
            f"bundle relative path must not be absolute: {rel!r}"
        )
    if ".." in candidate.parts:
        raise ExperimentDurableEvidenceBindingError(
            f"bundle relative path must not traverse upward: {rel!r}"
        )


def check_reference_consistency(
    *,
    manifest: Mapping[str, Any],
    ref: LineageRef,
) -> ExperimentBindingCrossReferences:
    if ref.ref_type != LineageRefType.EXPERIMENT:
        raise ExperimentDurableEvidenceBindingError(
            f"ref_type must be EXPERIMENT, got {ref.ref_type.value!r}"
        )
    if ref.relation != LineageRelation.SOURCES:
        raise ExperimentDurableEvidenceBindingError(
            f"relation must be SOURCES, got {ref.relation.value!r}"
        )
    if ref.artifact_path != ARTIFACT_FILENAME:
        raise ExperimentDurableEvidenceBindingError(
            f"artifact_path must be {ARTIFACT_FILENAME!r}, got {ref.artifact_path!r}"
        )
    if ref.owner_domain != EXPERIMENT_OWNER_DOMAIN:
        raise ExperimentDurableEvidenceBindingError(
            f"owner_domain must be {EXPERIMENT_OWNER_DOMAIN!r}, got {ref.owner_domain!r}"
        )

    experiment_identity_id = manifest.get("experiment_identity_id")
    if not isinstance(experiment_identity_id, str) or not experiment_identity_id.strip():
        raise ExperimentDurableEvidenceBindingError("experiment_identity_id missing or invalid")

    integrity = manifest.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ExperimentDurableEvidenceBindingError("integrity must be an object")
    content_sha256 = integrity.get("content_sha256")
    if not isinstance(content_sha256, str) or not content_sha256.strip():
        raise ExperimentDurableEvidenceBindingError("integrity.content_sha256 missing or invalid")
    if not is_valid_sha256_hex(content_sha256):
        raise ExperimentDurableEvidenceBindingError(
            "integrity.content_sha256 must be valid sha256 hex"
        )

    if ref.ref_id != experiment_identity_id:
        raise ExperimentDurableEvidenceBindingError(
            f"ref_id must match experiment_identity_id: {ref.ref_id!r} != {experiment_identity_id!r}"
        )
    if ref.digest is None:
        raise ExperimentDurableEvidenceBindingError("lineage ref digest is required")
    if not is_valid_sha256_hex(ref.digest):
        raise ExperimentDurableEvidenceBindingError("lineage ref digest must be valid sha256 hex")
    if ref.digest != content_sha256:
        raise ExperimentDurableEvidenceBindingError(
            "lineage ref digest must match integrity.content_sha256 verbatim"
        )

    return ExperimentBindingCrossReferences(
        experiment_identity_id=experiment_identity_id,
        lineage_ref_digest=ref.digest,
        lineage_ref_artifact_path=ref.artifact_path,
    )


def _build_experiment_lineage_ref_payload(ref: LineageRef) -> dict[str, Any]:
    payload = lineage_ref_to_mapping(ref)
    for forbidden in ("params", "metrics", "returns", "trades", "equity", "tags"):
        if forbidden in payload:
            raise ExperimentDurableEvidenceBindingError(
                f"lineage ref must not contain run payload key: {forbidden}"
            )
    return payload


def build_binding_index_v1(
    *,
    experiment_identity_id: str,
    cross_references: ExperimentBindingCrossReferences,
    ref: LineageRef,
    artifacts: tuple[BoundArtifactRecord, ...],
) -> dict[str, Any]:
    sorted_artifacts = sorted(
        artifacts,
        key=lambda item: (item.artifact_kind, item.relative_path),
    )
    payload: dict[str, Any] = {
        "schema_version": BINDING_SCHEMA_VERSION,
        "experiment_identity_id": experiment_identity_id,
        "experiment_lineage_ref": _build_experiment_lineage_ref_payload(ref),
        "cross_references": {
            "experiment_identity_id": cross_references.experiment_identity_id,
            "lineage_ref_digest": cross_references.lineage_ref_digest,
            "lineage_ref_artifact_path": cross_references.lineage_ref_artifact_path,
        },
        "artifacts": [
            {
                "artifact_kind": item.artifact_kind,
                "relative_path": item.relative_path,
                "content_sha256": item.content_sha256,
            }
            for item in sorted_artifacts
        ],
        "futures_scope_ref": dict(FUTURES_SCOPE_REF),
        "trading_logic_immutability_ref": dict(TRADING_LOGIC_IMMUTABILITY_REF),
        "evidence_does_not_authorize_runtime": True,
    }
    _reject_forbidden_index_keys(payload)
    digest = compute_content_sha256(payload)
    payload["integrity"] = {"content_sha256": digest}
    return payload


def serialize_binding_index_v1(index: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(index)
    return deterministic_json_dumps(dict(index))


def _copy_byte_identical(source: Path, dest: Path) -> str:
    _validate_regular_file(source, label="source artifact")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
    source_digest = _sha256_file(source)
    dest_digest = _sha256_file(dest)
    if source_digest != dest_digest:
        raise ExperimentDurableEvidenceBindingError(f"byte-identical copy failed for {source.name}")
    return source_digest


def _staging_dir_for(output_dir: Path) -> Path:
    token = uuid.uuid4().hex
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{token}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def produce_experiment_durable_evidence_bundle_v1(
    *,
    manifest_dir: Path | str,
    experiment_lineage_ref_path: Path | str,
    output_dir: Path | str,
) -> ExperimentDurableEvidenceBindingResult:
    """Bind validated EXPERIMENT identity manifest + LineageRef into offline durable evidence."""
    resolved_manifest_dir = _resolve_existing_directory(Path(manifest_dir), label="manifest_dir")
    lineage_ref_file = Path(experiment_lineage_ref_path)
    final_dir = Path(output_dir)

    _validate_regular_file(lineage_ref_file, label="experiment lineage ref")
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        manifest_dir=resolved_manifest_dir,
        lineage_ref_path=lineage_ref_file,
        output_dir=final_dir,
    )

    manifest, manifest_path, _manifest_bytes = _load_validated_identity_manifest(
        resolved_manifest_dir
    )
    ref = _load_lineage_ref_from_json_path(lineage_ref_file)
    cross = check_reference_consistency(manifest=manifest, ref=ref)
    experiment_identity_id = cross.experiment_identity_id

    for rel in (MANIFEST_ARTIFACT_REL, LINEAGE_REF_ARTIFACT_REL, INDEX_ARTIFACT_REL):
        _validate_bundle_relative_path(rel)

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ExperimentDurableEvidenceBindingError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)

        manifest_dest = staging / MANIFEST_ARTIFACT_REL
        ref_dest = staging / LINEAGE_REF_ARTIFACT_REL
        manifest_digest = _copy_byte_identical(manifest_path, manifest_dest)
        ref_digest = _copy_byte_identical(lineage_ref_file, ref_dest)

        artifacts = (
            BoundArtifactRecord(
                artifact_kind="experiment_identity_manifest_v1",
                relative_path=MANIFEST_ARTIFACT_REL,
                content_sha256=manifest_digest,
            ),
            BoundArtifactRecord(
                artifact_kind="experiment_lineage_ref_v1",
                relative_path=LINEAGE_REF_ARTIFACT_REL,
                content_sha256=ref_digest,
            ),
        )
        index_payload = build_binding_index_v1(
            experiment_identity_id=experiment_identity_id,
            cross_references=cross,
            ref=ref,
            artifacts=artifacts,
        )
        index_path = staging / INDEX_ARTIFACT_REL
        index_path.write_text(serialize_binding_index_v1(index_payload), encoding="utf-8")

        write_manifest_sha256(staging)
        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ExperimentDurableEvidenceBindingError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ExperimentDurableEvidenceBindingError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return ExperimentDurableEvidenceBindingResult(
        output_dir=final_dir,
        experiment_identity_id=experiment_identity_id,
        binding_index_path=final_dir / INDEX_ARTIFACT_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
    )


__all__ = [
    "BINDING_SCHEMA_VERSION",
    "INDEX_ARTIFACT_REL",
    "LINEAGE_REF_ARTIFACT_REL",
    "MANIFEST_ARTIFACT_REL",
    "ExperimentBindingCrossReferences",
    "ExperimentDurableEvidenceBindingError",
    "ExperimentDurableEvidenceBindingResult",
    "BoundArtifactRecord",
    "build_binding_index_v1",
    "check_reference_consistency",
    "produce_experiment_durable_evidence_bundle_v1",
    "serialize_binding_index_v1",
]
