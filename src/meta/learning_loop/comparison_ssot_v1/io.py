"""Atomic IO for comparison_ssot.v1 manifests."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.primary_evidence_retention_v0 import is_under_tmp
from src.meta.learning_loop.comparison_ssot_v1.constants import (
    DEFINITION_ARTIFACT_FILENAME,
    RESULT_ARTIFACT_FILENAME,
    STAGING_DIRNAME_PREFIX,
)
from src.meta.learning_loop.comparison_ssot_v1.identity import (
    attach_definition_identity_and_integrity,
    attach_result_integrity,
    verify_definition_identity_and_integrity,
)
from src.meta.learning_loop.comparison_ssot_v1.models import ComparisonSsotError
from src.meta.learning_loop.comparison_ssot_v1.validation import (
    validate_definition_manifest_v1,
    validate_result_manifest_v1,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps


def _staging_dir_for(output_dir: Path) -> Path:
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def _validate_output_target(output_dir: Path) -> None:
    if is_under_tmp(output_dir):
        raise ComparisonSsotError("output directory must be outside /tmp")
    parent = output_dir.parent
    if not parent.is_dir():
        raise ComparisonSsotError(f"output parent directory missing: {parent}")
    if is_under_tmp(parent):
        raise ComparisonSsotError("output parent directory must be outside /tmp")


def serialize_manifest(manifest: Mapping[str, Any]) -> str:
    return deterministic_json_dumps(manifest) + "\n"


def read_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ComparisonSsotError(f"invalid manifest JSON: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ComparisonSsotError(f"manifest root must be object: {path}")
    return payload


def _self_verify_definition(path: Path) -> None:
    manifest = read_manifest(path)
    validate_definition_manifest_v1(manifest)
    verify_definition_identity_and_integrity(manifest)


def _self_verify_result(path: Path) -> None:
    manifest = read_manifest(path)
    validate_result_manifest_v1(manifest)


def publish_comparison_manifests_atomic(
    *,
    output_root: Path,
    definition_body: Mapping[str, Any],
    result_body: Mapping[str, Any],
) -> tuple[Path, Path]:
    definition = attach_definition_identity_and_integrity(definition_body)
    validate_definition_manifest_v1(definition)
    comparison_definition_id = str(definition["comparison_definition_id"])

    result = attach_result_integrity(dict(result_body))
    if result.get("comparison_definition_id") != comparison_definition_id:
        raise ComparisonSsotError("result comparison_definition_id mismatch")
    validate_result_manifest_v1(result)

    output_dir = output_root / comparison_definition_id
    definition_path = output_dir / DEFINITION_ARTIFACT_FILENAME
    result_path = output_dir / RESULT_ARTIFACT_FILENAME

    if definition_path.is_file() and result_path.is_file():
        existing_def = read_manifest(definition_path)
        existing_res = read_manifest(result_path)
        if existing_def != definition or existing_res != result:
            raise ComparisonSsotError(
                "existing manifests differ under canonical identity (fail-closed)"
            )
        _self_verify_definition(definition_path)
        _self_verify_result(result_path)
        return definition_path, result_path

    if output_dir.exists():
        raise ComparisonSsotError(
            f"output directory exists without complete manifests (fail-closed): {output_dir}"
        )

    _validate_output_target(output_dir)
    staging = _staging_dir_for(output_dir)
    staging.mkdir(parents=True, exist_ok=False)
    try:
        staged_def = staging / DEFINITION_ARTIFACT_FILENAME
        staged_res = staging / RESULT_ARTIFACT_FILENAME
        staged_def.write_text(serialize_manifest(definition), encoding="utf-8")
        staged_res.write_text(serialize_manifest(result), encoding="utf-8")
        _self_verify_definition(staged_def)
        _self_verify_result(staged_res)
        staging.replace(output_dir)
    except Exception:
        _cleanup_staging(staging)
        raise
    finally:
        if staging.exists():
            _cleanup_staging(staging)

    _self_verify_definition(definition_path)
    _self_verify_result(result_path)
    return definition_path, result_path
