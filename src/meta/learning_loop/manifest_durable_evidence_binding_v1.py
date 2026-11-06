"""Offline Package G — durable evidence binding for learning manifest artifacts v1."""

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
    CandidateLineageManifestError,
    CandidateLineageManifestValidationError,
    CandidateLineageManifestV1,
    deserialize_candidate_lineage_manifest_v1,
    validate_candidate_lineage_manifest_v1,
)
from src.meta.learning_loop.config_patch_manifest_v1 import (
    ConfigPatchManifestError,
    ConfigPatchManifestValidationError,
    load_config_patch_manifest_v1_from_json_path,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_uuid,
)

BINDING_SCHEMA_VERSION = "learning_manifest_durable_evidence_binding_v1"
CONFIG_PATCH_ARTIFACT_REL = "config_patch_manifest_v1.json"
LINEAGE_ARTIFACT_REL = "candidate_lineage_manifest_v1.json"
INDEX_ARTIFACT_REL = "learning_manifest_durable_evidence_binding_index_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".learning_manifest_durable_evidence_staging_"

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
    }
)


class ManifestDurableEvidenceBindingError(ValueError):
    """Fail-closed Package G durable evidence binding error."""


@dataclass(frozen=True)
class BindingCrossReferences:
    lineage_manifest_ref_bound: bool
    config_patch_lineage_manifest_ref: str | None
    candidate_lineage_manifest_id: str


@dataclass(frozen=True)
class BoundArtifactRecord:
    artifact_kind: str
    relative_path: str
    content_sha256: str


@dataclass(frozen=True)
class DurableEvidenceBindingResult:
    output_dir: Path
    config_patch_manifest_id: str
    candidate_lineage_manifest_id: str
    binding_index_path: Path
    manifest_path: Path


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_candidate_lineage_manifest_v1_from_json_path(path: Path) -> CandidateLineageManifestV1:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CandidateLineageManifestError(f"failed to read manifest file: {path}") from exc
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise CandidateLineageManifestError(f"invalid JSON in manifest file: {path}") from exc
    if not isinstance(data, Mapping):
        raise CandidateLineageManifestError("manifest root must be a JSON object")
    valid, phase, errors, verdict = validate_candidate_lineage_manifest_v1(data)
    if not valid:
        raise CandidateLineageManifestValidationError(
            f"CandidateLineageManifest v1 validation failed for {path}",
            phase=phase,
            errors=errors,
            verdict=verdict,
        )
    return deserialize_candidate_lineage_manifest_v1(data)


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ManifestDurableEvidenceBindingError(f"{label} must not be a symlink: {path}")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ManifestDurableEvidenceBindingError(
                f"binding index must not contain forbidden key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise ManifestDurableEvidenceBindingError(f"{label} not found: {path}")
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ManifestDurableEvidenceBindingError(f"{label} must be a regular file: {path}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ManifestDurableEvidenceBindingError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ManifestDurableEvidenceBindingError("output directory must be outside /tmp")
    parent = output_dir.parent
    if not parent.is_dir():
        raise ManifestDurableEvidenceBindingError(f"output parent directory missing: {parent}")
    if is_under_tmp(parent):
        raise ManifestDurableEvidenceBindingError("output parent directory must be outside /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(
    *,
    config_patch_path: Path,
    candidate_lineage_path: Path,
    output_dir: Path,
) -> None:
    config_res = config_patch_path.resolve()
    lineage_res = candidate_lineage_path.resolve()
    output_res = output_dir.resolve()

    if output_res in {config_res, lineage_res}:
        raise ManifestDurableEvidenceBindingError(
            "output directory must not equal a source manifest path (fail-closed)"
        )

    for src in (config_res, lineage_res):
        if _path_is_under(src, output_res):
            raise ManifestDurableEvidenceBindingError(
                "source manifest must not be inside output directory (fail-closed)"
            )

    for src in (config_res, lineage_res):
        if src.is_file() and _path_is_under(output_res, src):
            raise ManifestDurableEvidenceBindingError(
                "output directory must not be inside a source manifest path (fail-closed)"
            )


def _verify_manifest_id_matches_integrity(
    *,
    manifest_id: str,
    integrity_digest: str,
    label: str,
) -> None:
    if not is_valid_uuid(manifest_id):
        raise ManifestDurableEvidenceBindingError(f"{label} manifest_id must be a UUID")


def check_reference_consistency(
    *,
    config_patch_manifest_id: str,
    config_patch_lineage_manifest_ref: str | None,
    candidate_lineage_manifest_id: str,
) -> BindingCrossReferences:
    _verify_manifest_id_matches_integrity(
        manifest_id=config_patch_manifest_id,
        integrity_digest="",
        label="config_patch",
    )
    _verify_manifest_id_matches_integrity(
        manifest_id=candidate_lineage_manifest_id,
        integrity_digest="",
        label="candidate_lineage",
    )
    if config_patch_lineage_manifest_ref is None:
        return BindingCrossReferences(
            lineage_manifest_ref_bound=False,
            config_patch_lineage_manifest_ref=None,
            candidate_lineage_manifest_id=candidate_lineage_manifest_id,
        )
    if not is_valid_uuid(config_patch_lineage_manifest_ref):
        raise ManifestDurableEvidenceBindingError(
            "config patch lineage_manifest_ref must be a UUID when present"
        )
    if config_patch_lineage_manifest_ref != candidate_lineage_manifest_id:
        raise ManifestDurableEvidenceBindingError(
            "config patch lineage_manifest_ref does not match candidate lineage manifest_id"
        )
    return BindingCrossReferences(
        lineage_manifest_ref_bound=True,
        config_patch_lineage_manifest_ref=config_patch_lineage_manifest_ref,
        candidate_lineage_manifest_id=candidate_lineage_manifest_id,
    )


def _build_cross_references_payload(cross: BindingCrossReferences) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "lineage_manifest_ref_bound": cross.lineage_manifest_ref_bound,
        "candidate_lineage_manifest_id": cross.candidate_lineage_manifest_id,
    }
    if cross.config_patch_lineage_manifest_ref is not None:
        payload["config_patch_lineage_manifest_ref"] = cross.config_patch_lineage_manifest_ref
    return payload


def build_binding_index_v1(
    *,
    config_patch_manifest_id: str,
    candidate_lineage_manifest_id: str,
    cross_references: BindingCrossReferences,
    artifacts: tuple[BoundArtifactRecord, ...],
    futures_scope_ref: Mapping[str, Any],
    trading_logic_immutability_ref: Mapping[str, Any],
) -> dict[str, Any]:
    sorted_artifacts = sorted(
        artifacts,
        key=lambda item: (item.artifact_kind, item.relative_path),
    )
    payload: dict[str, Any] = {
        "schema_version": BINDING_SCHEMA_VERSION,
        "config_patch_manifest_id": config_patch_manifest_id,
        "candidate_lineage_manifest_id": candidate_lineage_manifest_id,
        "cross_references": _build_cross_references_payload(cross_references),
        "artifacts": [
            {
                "artifact_kind": item.artifact_kind,
                "relative_path": item.relative_path,
                "content_sha256": item.content_sha256,
            }
            for item in sorted_artifacts
        ],
        "futures_scope_ref": dict(futures_scope_ref),
        "trading_logic_immutability_ref": dict(trading_logic_immutability_ref),
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
        raise ManifestDurableEvidenceBindingError(f"byte-identical copy failed for {source.name}")
    return source_digest


def _staging_dir_for(output_dir: Path) -> Path:
    token = uuid.uuid4().hex
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{token}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def _validate_bundle_relative_path(rel: str) -> None:
    candidate = Path(rel)
    if candidate.is_absolute():
        raise ManifestDurableEvidenceBindingError(
            f"bundle relative path must not be absolute: {rel!r}"
        )
    if ".." in candidate.parts:
        raise ManifestDurableEvidenceBindingError(
            f"bundle relative path must not traverse upward: {rel!r}"
        )


def produce_learning_manifest_durable_evidence_bundle_v1(
    *,
    config_patch_manifest_path: Path | str,
    candidate_lineage_manifest_path: Path | str,
    output_dir: Path | str,
) -> DurableEvidenceBindingResult:
    """Bind validated manifest artifacts into an offline durable evidence bundle."""
    config_path = Path(config_patch_manifest_path)
    lineage_path = Path(candidate_lineage_manifest_path)
    final_dir = Path(output_dir)

    _validate_regular_file(config_path, label="config patch manifest")
    _validate_regular_file(lineage_path, label="candidate lineage manifest")
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        config_patch_path=config_path,
        candidate_lineage_path=lineage_path,
        output_dir=final_dir,
    )

    try:
        config_manifest = load_config_patch_manifest_v1_from_json_path(config_path)
    except ConfigPatchManifestValidationError as exc:
        raise ManifestDurableEvidenceBindingError(str(exc)) from exc
    except ConfigPatchManifestError as exc:
        raise ManifestDurableEvidenceBindingError(str(exc)) from exc

    try:
        lineage_manifest = _load_candidate_lineage_manifest_v1_from_json_path(lineage_path)
    except CandidateLineageManifestValidationError as exc:
        raise ManifestDurableEvidenceBindingError(str(exc)) from exc
    except CandidateLineageManifestError as exc:
        raise ManifestDurableEvidenceBindingError(str(exc)) from exc

    if config_manifest.integrity is None:
        raise ManifestDurableEvidenceBindingError("config patch manifest integrity missing")
    if lineage_manifest.integrity is None:
        raise ManifestDurableEvidenceBindingError("candidate lineage manifest integrity missing")

    cross = check_reference_consistency(
        config_patch_manifest_id=config_manifest.manifest_id,
        config_patch_lineage_manifest_ref=config_manifest.lineage_manifest_ref,
        candidate_lineage_manifest_id=lineage_manifest.lineage_manifest_id,
    )

    for rel in (CONFIG_PATCH_ARTIFACT_REL, LINEAGE_ARTIFACT_REL, INDEX_ARTIFACT_REL):
        _validate_bundle_relative_path(rel)

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ManifestDurableEvidenceBindingError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)

        config_dest = staging / CONFIG_PATCH_ARTIFACT_REL
        lineage_dest = staging / LINEAGE_ARTIFACT_REL
        config_digest = _copy_byte_identical(config_path, config_dest)
        lineage_digest = _copy_byte_identical(lineage_path, lineage_dest)

        artifacts = (
            BoundArtifactRecord(
                artifact_kind="config_patch_manifest_v1",
                relative_path=CONFIG_PATCH_ARTIFACT_REL,
                content_sha256=config_digest,
            ),
            BoundArtifactRecord(
                artifact_kind="candidate_lineage_manifest_v1",
                relative_path=LINEAGE_ARTIFACT_REL,
                content_sha256=lineage_digest,
            ),
        )
        index_payload = build_binding_index_v1(
            config_patch_manifest_id=config_manifest.manifest_id,
            candidate_lineage_manifest_id=lineage_manifest.lineage_manifest_id,
            cross_references=cross,
            artifacts=artifacts,
            futures_scope_ref=config_manifest.source_scope,
            trading_logic_immutability_ref=config_manifest.trading_logic_immutability_ref,
        )
        index_path = staging / INDEX_ARTIFACT_REL
        index_path.write_text(serialize_binding_index_v1(index_payload), encoding="utf-8")

        write_manifest_sha256(staging)
        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ManifestDurableEvidenceBindingError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        staging.replace(final_dir)

        final_index = final_dir / INDEX_ARTIFACT_REL
        final_manifest = final_dir / MANIFEST_FILENAME
        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ManifestDurableEvidenceBindingError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return DurableEvidenceBindingResult(
        output_dir=final_dir,
        config_patch_manifest_id=config_manifest.manifest_id,
        candidate_lineage_manifest_id=lineage_manifest.lineage_manifest_id,
        binding_index_path=final_dir / INDEX_ARTIFACT_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
    )


__all__ = [
    "BINDING_SCHEMA_VERSION",
    "CONFIG_PATCH_ARTIFACT_REL",
    "INDEX_ARTIFACT_REL",
    "LINEAGE_ARTIFACT_REL",
    "BoundArtifactRecord",
    "BindingCrossReferences",
    "DurableEvidenceBindingResult",
    "ManifestDurableEvidenceBindingError",
    "build_binding_index_v1",
    "check_reference_consistency",
    "produce_learning_manifest_durable_evidence_bundle_v1",
    "serialize_binding_index_v1",
]
