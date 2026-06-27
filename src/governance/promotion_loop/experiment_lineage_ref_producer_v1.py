"""Package M — offline EXPERIMENT LineageRef producer from explicit manifest directory."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME,
    ExperimentIdentityManifestError,
    validate_experiment_identity_manifest_v1,
)
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    LineageRef,
    LineageRefType,
    LineageRelation,
    lineage_ref_from_mapping,
    lineage_ref_to_mapping,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps

EXPERIMENT_OWNER_DOMAIN = "experiments/base"
EXPERIMENT_LINEAGE_REF_REQUIRED = False


class ExperimentLineageRefProducerError(ValueError):
    """Fail-closed Package M EXPERIMENT LineageRef production error."""


@dataclass(frozen=True)
class ExperimentLineageRefProducerResult:
    manifest_dir: Path
    manifest_path: Path
    ref: LineageRef


def _resolve_existing_directory(manifest_dir: Path) -> Path:
    if not manifest_dir.exists():
        raise ExperimentLineageRefProducerError(f"manifest_dir not found: {manifest_dir}")
    if manifest_dir.is_symlink():
        raise ExperimentLineageRefProducerError(
            f"manifest_dir must not be a symlink (fail-closed): {manifest_dir}"
        )
    if not manifest_dir.is_dir():
        raise ExperimentLineageRefProducerError(f"manifest_dir is not a directory: {manifest_dir}")
    return manifest_dir.resolve()


def _assert_path_under_root(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ExperimentLineageRefProducerError(
            f"path escapes manifest_dir root: {path} (root={root})"
        ) from exc
    return resolved


def _validate_artifact_relative_path(artifact_path: str) -> None:
    if not artifact_path or artifact_path.strip() != artifact_path:
        raise ExperimentLineageRefProducerError("artifact_path must be non-empty and trimmed")
    if artifact_path.startswith("/") or artifact_path.startswith("\\"):
        raise ExperimentLineageRefProducerError("artifact_path must be relative")
    if "\\" in artifact_path:
        raise ExperimentLineageRefProducerError("artifact_path must use forward slashes only")
    if ".." in artifact_path.split("/"):
        raise ExperimentLineageRefProducerError("artifact_path must not contain '..' segments")


def _load_validated_manifest(manifest_dir: Path) -> tuple[dict[str, Any], Path]:
    manifest_path = manifest_dir / ARTIFACT_FILENAME
    if manifest_path.is_symlink():
        raise ExperimentLineageRefProducerError(
            f"{ARTIFACT_FILENAME} must not be a symlink (fail-closed): {manifest_path}"
        )
    if manifest_path.is_dir():
        raise ExperimentLineageRefProducerError(
            f"{ARTIFACT_FILENAME} is a directory, expected regular file: {manifest_path}"
        )
    if not manifest_path.is_file():
        raise ExperimentLineageRefProducerError(
            f"{ARTIFACT_FILENAME} not found in manifest_dir: {manifest_dir}"
        )
    _assert_path_under_root(manifest_path, manifest_dir)

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExperimentLineageRefProducerError(
            f"invalid {ARTIFACT_FILENAME} in manifest_dir={manifest_dir}: {exc}"
        ) from exc

    if not isinstance(raw, dict):
        raise ExperimentLineageRefProducerError(
            f"{ARTIFACT_FILENAME} root must be a JSON object for manifest_dir={manifest_dir}"
        )

    try:
        validate_experiment_identity_manifest_v1(raw)
    except ExperimentIdentityManifestError as exc:
        raise ExperimentLineageRefProducerError(
            f"experiment identity manifest validation failed for manifest_dir={manifest_dir}: {exc}"
        ) from exc

    return raw, manifest_path


def build_experiment_lineage_ref_from_manifest(
    manifest: Mapping[str, Any],
    *,
    artifact_path: str = ARTIFACT_FILENAME,
) -> LineageRef:
    """Build a validated EXPERIMENT LineageRef from an already validated Package N manifest."""
    _validate_artifact_relative_path(artifact_path)

    experiment_identity_id = manifest.get("experiment_identity_id")
    if not isinstance(experiment_identity_id, str) or not experiment_identity_id.strip():
        raise ExperimentLineageRefProducerError("experiment_identity_id missing or invalid")

    integrity = manifest.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ExperimentLineageRefProducerError("integrity must be an object")
    content_sha256 = integrity.get("content_sha256")
    if not isinstance(content_sha256, str) or not content_sha256.strip():
        raise ExperimentLineageRefProducerError("integrity.content_sha256 missing or invalid")

    return LineageRef(
        ref_type=LineageRefType.EXPERIMENT,
        ref_id=experiment_identity_id,
        relation=LineageRelation.SOURCES,
        owner_domain=EXPERIMENT_OWNER_DOMAIN,
        required=EXPERIMENT_LINEAGE_REF_REQUIRED,
        digest=content_sha256,
        artifact_path=artifact_path,
    )


def produce_experiment_lineage_ref_v1(
    *,
    manifest_dir: Path | str,
) -> ExperimentLineageRefProducerResult:
    """Extract a reference-only EXPERIMENT LineageRef from an explicit manifest directory."""
    resolved_manifest_dir = _resolve_existing_directory(Path(manifest_dir))
    manifest, manifest_path = _load_validated_manifest(resolved_manifest_dir)
    ref = build_experiment_lineage_ref_from_manifest(manifest)
    return ExperimentLineageRefProducerResult(
        manifest_dir=resolved_manifest_dir,
        manifest_path=manifest_path,
        ref=ref,
    )


def serialize_experiment_lineage_ref_v1(ref: LineageRef) -> str:
    """Serialize an EXPERIMENT LineageRef to deterministic canonical JSON."""
    if ref.ref_type != LineageRefType.EXPERIMENT:
        raise ExperimentLineageRefProducerError(
            f"ref_type must be EXPERIMENT, got {ref.ref_type.value!r}"
        )
    return deterministic_json_dumps(lineage_ref_to_mapping(ref))


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
    except OSError:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise
    try:
        tmp.replace(path)
    except OSError:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise


def _self_verify_written_ref(ref: LineageRef, output_path: Path) -> None:
    try:
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExperimentLineageRefProducerError(
            f"self-verification failed: output is not valid JSON: {output_path}"
        ) from exc
    if not isinstance(payload, dict):
        raise ExperimentLineageRefProducerError(
            f"self-verification failed: output root must be object: {output_path}"
        )
    try:
        roundtrip = lineage_ref_from_mapping(payload)
    except Exception as exc:
        raise ExperimentLineageRefProducerError(
            f"self-verification failed: output LineageRef invalid: {output_path}: {exc}"
        ) from exc
    if roundtrip != ref:
        raise ExperimentLineageRefProducerError(
            f"self-verification failed: output LineageRef mismatch for {output_path}"
        )


def write_experiment_lineage_ref_v1_atomic(
    ref: LineageRef,
    output_path: Path | str,
    *,
    fail_closed_if_exists: bool = True,
) -> Path:
    """Validate, atomically write, and self-verify an EXPERIMENT LineageRef JSON file."""
    out = Path(output_path)
    if fail_closed_if_exists and out.exists():
        raise ExperimentLineageRefProducerError(f"output path already exists (fail-closed): {out}")
    serialized = serialize_experiment_lineage_ref_v1(ref)
    _atomic_write_text(out, serialized)
    _self_verify_written_ref(ref, out)
    return out


def produce_experiment_lineage_ref_v1_to_path(
    *,
    manifest_dir: Path | str,
    output_path: Path | str,
    fail_closed_if_exists: bool = True,
) -> ExperimentLineageRefProducerResult:
    """End-to-end offline producer: explicit manifest_dir -> validated EXPERIMENT LineageRef JSON."""
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    write_experiment_lineage_ref_v1_atomic(
        result.ref,
        output_path,
        fail_closed_if_exists=fail_closed_if_exists,
    )
    return result
