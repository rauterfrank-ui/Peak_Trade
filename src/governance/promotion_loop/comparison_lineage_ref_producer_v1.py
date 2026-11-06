"""Offline COMPARISON LineageRef producer from explicit result manifest directory."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    LineageRef,
    LineageRefType,
    LineageRelation,
    lineage_ref_from_mapping,
    lineage_ref_to_mapping,
)
from src.meta.learning_loop.comparison_ssot_v1.constants import RESULT_ARTIFACT_FILENAME
from src.meta.learning_loop.comparison_ssot_v1.models import ComparisonSsotError
from src.meta.learning_loop.comparison_ssot_v1.validation import validate_result_manifest_v1
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps

COMPARISON_OWNER_DOMAIN = "meta/learning_loop/comparison_ssot_v1"
COMPARISON_LINEAGE_REF_REQUIRED = False


class ComparisonLineageRefProducerError(ValueError):
    """Fail-closed COMPARISON LineageRef production error."""


@dataclass(frozen=True)
class ComparisonLineageRefProducerResult:
    manifest_dir: Path
    manifest_path: Path
    ref: LineageRef


def _resolve_existing_directory(manifest_dir: Path) -> Path:
    if not manifest_dir.exists():
        raise ComparisonLineageRefProducerError(f"manifest_dir not found: {manifest_dir}")
    if manifest_dir.is_symlink():
        raise ComparisonLineageRefProducerError(
            f"manifest_dir must not be a symlink (fail-closed): {manifest_dir}"
        )
    if not manifest_dir.is_dir():
        raise ComparisonLineageRefProducerError(f"manifest_dir is not a directory: {manifest_dir}")
    return manifest_dir.resolve()


def _assert_path_under_root(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ComparisonLineageRefProducerError(
            f"path escapes manifest_dir root: {path} (root={root})"
        ) from exc
    return resolved


def _validate_artifact_relative_path(artifact_path: str) -> None:
    if not artifact_path or artifact_path.strip() != artifact_path:
        raise ComparisonLineageRefProducerError("artifact_path must be non-empty and trimmed")
    if artifact_path.startswith("/") or artifact_path.startswith("\\"):
        raise ComparisonLineageRefProducerError("artifact_path must be relative")
    if "\\" in artifact_path:
        raise ComparisonLineageRefProducerError("artifact_path must use forward slashes only")
    if ".." in artifact_path.split("/"):
        raise ComparisonLineageRefProducerError("artifact_path must not contain '..' segments")


def _load_validated_result_manifest(manifest_dir: Path) -> tuple[dict[str, Any], Path]:
    manifest_path = manifest_dir / RESULT_ARTIFACT_FILENAME
    if manifest_path.is_symlink():
        raise ComparisonLineageRefProducerError(
            f"{RESULT_ARTIFACT_FILENAME} must not be a symlink (fail-closed): {manifest_path}"
        )
    if manifest_path.is_dir():
        raise ComparisonLineageRefProducerError(
            f"{RESULT_ARTIFACT_FILENAME} is a directory, expected regular file: {manifest_path}"
        )
    if not manifest_path.is_file():
        raise ComparisonLineageRefProducerError(
            f"{RESULT_ARTIFACT_FILENAME} not found in manifest_dir: {manifest_dir}"
        )
    _assert_path_under_root(manifest_path, manifest_dir)

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ComparisonLineageRefProducerError(
            f"invalid {RESULT_ARTIFACT_FILENAME} in manifest_dir={manifest_dir}: {exc}"
        ) from exc

    if not isinstance(raw, dict):
        raise ComparisonLineageRefProducerError(
            f"{RESULT_ARTIFACT_FILENAME} root must be a JSON object for manifest_dir={manifest_dir}"
        )

    try:
        validate_result_manifest_v1(raw)
    except ComparisonSsotError as exc:
        raise ComparisonLineageRefProducerError(
            f"comparison result manifest validation failed for manifest_dir={manifest_dir}: {exc}"
        ) from exc

    return raw, manifest_path


def build_comparison_lineage_ref_from_result_manifest(
    manifest: Mapping[str, Any],
    *,
    artifact_path: str = RESULT_ARTIFACT_FILENAME,
) -> LineageRef:
    """Build a validated COMPARISON LineageRef from an already validated result manifest."""
    _validate_artifact_relative_path(artifact_path)

    comparison_definition_id = manifest.get("comparison_definition_id")
    if not isinstance(comparison_definition_id, str) or not comparison_definition_id.strip():
        raise ComparisonLineageRefProducerError("comparison_definition_id missing or invalid")

    integrity = manifest.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ComparisonLineageRefProducerError("integrity must be an object")
    content_sha256 = integrity.get("content_sha256")
    if not isinstance(content_sha256, str) or not content_sha256.strip():
        raise ComparisonLineageRefProducerError("integrity.content_sha256 missing or invalid")

    return LineageRef(
        ref_type=LineageRefType.COMPARISON,
        ref_id=comparison_definition_id,
        relation=LineageRelation.DERIVES_FROM_RESULT_MANIFEST,
        owner_domain=COMPARISON_OWNER_DOMAIN,
        required=COMPARISON_LINEAGE_REF_REQUIRED,
        digest=content_sha256,
        artifact_path=artifact_path,
    )


def produce_comparison_lineage_ref_v1(
    *,
    manifest_dir: Path | str,
) -> ComparisonLineageRefProducerResult:
    """Extract a reference-only COMPARISON LineageRef from an explicit result manifest directory."""
    resolved_manifest_dir = _resolve_existing_directory(Path(manifest_dir))
    manifest, manifest_path = _load_validated_result_manifest(resolved_manifest_dir)
    ref = build_comparison_lineage_ref_from_result_manifest(manifest)
    return ComparisonLineageRefProducerResult(
        manifest_dir=resolved_manifest_dir,
        manifest_path=manifest_path,
        ref=ref,
    )


def serialize_comparison_lineage_ref_v1(ref: LineageRef) -> str:
    """Serialize a COMPARISON LineageRef to deterministic canonical JSON."""
    if ref.ref_type != LineageRefType.COMPARISON:
        raise ComparisonLineageRefProducerError(
            f"ref_type must be COMPARISON, got {ref.ref_type.value!r}"
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
        raise ComparisonLineageRefProducerError(
            f"self-verification failed: output is not valid JSON: {output_path}"
        ) from exc
    if not isinstance(payload, dict):
        raise ComparisonLineageRefProducerError(
            f"self-verification failed: output root must be object: {output_path}"
        )
    try:
        roundtrip = lineage_ref_from_mapping(payload)
    except Exception as exc:
        raise ComparisonLineageRefProducerError(
            f"self-verification failed: output LineageRef invalid: {output_path}: {exc}"
        ) from exc
    if roundtrip != ref:
        raise ComparisonLineageRefProducerError(
            f"self-verification failed: output LineageRef mismatch for {output_path}"
        )


def write_comparison_lineage_ref_v1_atomic(
    ref: LineageRef,
    output_path: Path | str,
    *,
    fail_closed_if_exists: bool = True,
) -> Path:
    """Validate, atomically write, and self-verify a COMPARISON LineageRef JSON file."""
    out = Path(output_path)
    if fail_closed_if_exists and out.exists():
        raise ComparisonLineageRefProducerError(f"output path already exists (fail-closed): {out}")
    serialized = serialize_comparison_lineage_ref_v1(ref)
    _atomic_write_text(out, serialized)
    _self_verify_written_ref(ref, out)
    return out


def produce_comparison_lineage_ref_v1_to_path(
    *,
    manifest_dir: Path | str,
    output_path: Path | str,
    fail_closed_if_exists: bool = True,
) -> ComparisonLineageRefProducerResult:
    """End-to-end offline producer: explicit manifest_dir -> validated COMPARISON LineageRef JSON."""
    result = produce_comparison_lineage_ref_v1(manifest_dir=manifest_dir)
    write_comparison_lineage_ref_v1_atomic(
        result.ref,
        output_path,
        fail_closed_if_exists=fail_closed_if_exists,
    )
    return result
