"""Atomic IO for comparison_metric_input.v1 manifests."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.primary_evidence_retention_v0 import is_under_tmp
from src.meta.learning_loop.comparison_metric_input_v1.constants import (
    ARTIFACT_FILENAME,
    STAGING_DIRNAME_PREFIX,
)
from src.meta.learning_loop.comparison_metric_input_v1.identity import (
    attach_identity_and_integrity,
    verify_manifest_identity_and_integrity,
)
from src.meta.learning_loop.comparison_metric_input_v1.models import ComparisonMetricInputError
from src.meta.learning_loop.comparison_metric_input_v1.validation import (
    validate_comparison_metric_input_manifest_v1,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps


def _staging_dir_for(output_dir: Path) -> Path:
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def _validate_output_target(output_dir: Path) -> None:
    if is_under_tmp(output_dir):
        raise ComparisonMetricInputError("output directory must be outside /tmp")
    parent = output_dir.parent
    if not parent.is_dir():
        raise ComparisonMetricInputError(f"output parent directory missing: {parent}")
    if is_under_tmp(parent):
        raise ComparisonMetricInputError("output parent directory must be outside /tmp")


def serialize_manifest(manifest: Mapping[str, Any]) -> str:
    return deterministic_json_dumps(manifest) + "\n"


def read_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ComparisonMetricInputError(f"invalid manifest JSON: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ComparisonMetricInputError(f"manifest root must be object: {path}")
    return payload


def _self_verify_manifest_file(path: Path) -> None:
    manifest = read_manifest(path)
    validate_comparison_metric_input_manifest_v1(manifest)
    verify_manifest_identity_and_integrity(manifest)


def publish_manifest_atomic(*, output_root: Path, manifest_body: Mapping[str, Any]) -> Path:
    manifest = attach_identity_and_integrity(manifest_body)
    validate_comparison_metric_input_manifest_v1(manifest)
    comparison_metric_input_id = str(manifest["comparison_metric_input_id"])
    output_dir = output_root / comparison_metric_input_id
    manifest_path = output_dir / ARTIFACT_FILENAME

    if manifest_path.is_file():
        existing = read_manifest(manifest_path)
        if existing != manifest:
            raise ComparisonMetricInputError(
                "existing manifest content differs under canonical identity (fail-closed)"
            )
        _self_verify_manifest_file(manifest_path)
        return manifest_path

    if output_dir.exists():
        raise ComparisonMetricInputError(
            f"output directory exists without manifest (fail-closed): {output_dir}"
        )

    _validate_output_target(output_dir)
    staging = _staging_dir_for(output_dir)
    staging.mkdir(parents=True, exist_ok=False)
    try:
        staged_manifest = staging / ARTIFACT_FILENAME
        staged_manifest.write_text(serialize_manifest(manifest), encoding="utf-8")
        _self_verify_manifest_file(staged_manifest)
        staging.replace(output_dir)
    except Exception:
        _cleanup_staging(staging)
        raise
    finally:
        if staging.exists():
            _cleanup_staging(staging)

    _self_verify_manifest_file(manifest_path)
    return manifest_path
