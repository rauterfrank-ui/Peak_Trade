"""Offline durable evidence binding for comparison_ssot.v1 result manifest."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.meta.learning_loop.comparison_ssot_v1.constants import (
    COMPARISON_CONTRACT_VERSION,
    RESULT_ARTIFACT_FILENAME,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.comparison_ssot_v1.validation import validate_result_manifest_v1
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

BINDING_SCHEMA_VERSION = "comparison_ssot_result_durable_evidence_binding_v1"
BINDING_RELATION = "PRESERVES_RESULT_IDENTITY_AND_DEFINITION_REF"
MANIFEST_ARTIFACT_REL = RESULT_ARTIFACT_FILENAME
INDEX_ARTIFACT_REL = "comparison_ssot_result_durable_evidence_binding_index_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".comparison_ssot_result_durable_evidence_staging_"

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
        "winner",
        "selection",
        "acceptance",
        "ranking",
        "pareto",
        "selected",
        "accepted",
        "promoted",
        "completed",
        "runtime_authorized",
        "shadow_authorized",
        "testnet_authorized",
        "live_authorized",
    }
)


class ComparisonSsotResultDurableEvidenceBindingError(ValueError):
    """Fail-closed comparison result durable evidence binding error."""


@dataclass(frozen=True)
class BoundArtifactRecord:
    artifact_kind: str
    relative_path: str
    content_sha256: str


@dataclass(frozen=True)
class ComparisonResultBindingCrossReferences:
    comparison_definition_id: str
    manifest_content_sha256: str


@dataclass(frozen=True)
class ComparisonSsotResultDurableEvidenceBindingResult:
    output_dir: Path
    comparison_definition_id: str
    binding_index_path: Path
    manifest_path: Path


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ComparisonSsotResultDurableEvidenceBindingError(
            f"{label} must not be a symlink: {path}"
        )


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ComparisonSsotResultDurableEvidenceBindingError(
                f"binding index must not contain forbidden key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise ComparisonSsotResultDurableEvidenceBindingError(f"{label} not found: {path}")
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ComparisonSsotResultDurableEvidenceBindingError(
            f"{label} must be a regular file: {path}"
        )


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ComparisonSsotResultDurableEvidenceBindingError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ComparisonSsotResultDurableEvidenceBindingError(
            "output directory must be outside /tmp"
        )
    parent = output_dir.parent
    if not parent.is_dir():
        raise ComparisonSsotResultDurableEvidenceBindingError(
            f"output parent directory missing: {parent}"
        )
    if is_under_tmp(parent):
        raise ComparisonSsotResultDurableEvidenceBindingError(
            "output parent directory must be outside /tmp"
        )


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _validate_bundle_relative_path(rel: str) -> None:
    candidate = Path(rel)
    if candidate.is_absolute():
        raise ComparisonSsotResultDurableEvidenceBindingError(
            f"bundle relative path must not be absolute: {rel!r}"
        )
    if ".." in candidate.parts:
        raise ComparisonSsotResultDurableEvidenceBindingError(
            f"bundle relative path must not traverse upward: {rel!r}"
        )


def _reject_unsafe_overlap(*, manifest_path: Path, output_dir: Path) -> None:
    manifest_res = manifest_path.resolve()
    output_res = output_dir.resolve()
    if output_res == manifest_res:
        raise ComparisonSsotResultDurableEvidenceBindingError(
            "output directory must not equal manifest path (fail-closed)"
        )
    if _path_is_under(manifest_res, output_res):
        raise ComparisonSsotResultDurableEvidenceBindingError(
            "manifest path must not be inside output directory (fail-closed)"
        )


def _load_validated_manifest(manifest_path: Path) -> tuple[dict[str, Any], bytes]:
    _validate_regular_file(manifest_path, label="comparison result manifest")
    if manifest_path.name != MANIFEST_ARTIFACT_REL:
        raise ComparisonSsotResultDurableEvidenceBindingError(
            f"manifest filename must be {MANIFEST_ARTIFACT_REL!r}, got {manifest_path.name!r}"
        )
    manifest_bytes = manifest_path.read_bytes()
    manifest = read_manifest(manifest_path)
    validate_result_manifest_v1(manifest)
    return manifest, manifest_bytes


def _verbatim_input_snapshots(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    snapshots = manifest.get("input_snapshots")
    if not isinstance(snapshots, list):
        raise ComparisonSsotResultDurableEvidenceBindingError("input_snapshots must be a list")
    preserved: list[dict[str, Any]] = []
    for idx, snap in enumerate(snapshots):
        if not isinstance(snap, Mapping):
            raise ComparisonSsotResultDurableEvidenceBindingError(
                f"input_snapshots[{idx}] must be an object"
            )
        source_ref = snap.get("source_ref")
        if not isinstance(source_ref, Mapping):
            raise ComparisonSsotResultDurableEvidenceBindingError(
                f"input_snapshots[{idx}].source_ref must be an object"
            )
        metrics = snap.get("metrics")
        if not isinstance(metrics, Mapping):
            raise ComparisonSsotResultDurableEvidenceBindingError(
                f"input_snapshots[{idx}].metrics must be an object"
            )
        preserved.append(
            {
                "comparison_metric_input_id": str(snap["comparison_metric_input_id"]),
                "source_ref": {
                    "owner_domain": str(source_ref["owner_domain"]),
                    "ref_type": str(source_ref["ref_type"]),
                    "ref_id": str(source_ref["ref_id"]),
                    "digest": str(source_ref["digest"]),
                },
                "source_digest": str(snap["source_digest"]),
                "metrics": {str(key): metrics[key] for key in metrics},
            }
        )
    return preserved


def _verbatim_result_summary_ref(manifest: Mapping[str, Any]) -> dict[str, Any]:
    ranking_result = manifest.get("ranking_result")
    if not isinstance(ranking_result, Mapping):
        raise ComparisonSsotResultDurableEvidenceBindingError("ranking_result must be an object")
    ref: dict[str, Any] = {
        "overall_comparable": bool(manifest["overall_comparable"]),
        "warnings": list(manifest.get("warnings", [])),
        "ranking_result": deepcopy(dict(ranking_result)),
    }
    pareto_result = manifest.get("pareto_result")
    if pareto_result is not None:
        if not isinstance(pareto_result, Mapping):
            raise ComparisonSsotResultDurableEvidenceBindingError("pareto_result must be an object")
        ref["pareto_result"] = deepcopy(dict(pareto_result))
    return ref


def check_reference_consistency(
    manifest: Mapping[str, Any],
) -> ComparisonResultBindingCrossReferences:
    comparison_definition_id = manifest.get("comparison_definition_id")
    if not isinstance(comparison_definition_id, str) or not comparison_definition_id.strip():
        raise ComparisonSsotResultDurableEvidenceBindingError(
            "comparison_definition_id missing or invalid"
        )
    integrity = manifest.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ComparisonSsotResultDurableEvidenceBindingError("integrity must be an object")
    manifest_content_sha256 = integrity.get("content_sha256")
    if not isinstance(manifest_content_sha256, str) or not manifest_content_sha256.strip():
        raise ComparisonSsotResultDurableEvidenceBindingError(
            "integrity.content_sha256 missing or invalid"
        )
    if not is_valid_sha256_hex(manifest_content_sha256):
        raise ComparisonSsotResultDurableEvidenceBindingError(
            "integrity.content_sha256 must be valid sha256 hex"
        )
    return ComparisonResultBindingCrossReferences(
        comparison_definition_id=comparison_definition_id,
        manifest_content_sha256=manifest_content_sha256,
    )


def build_binding_index_v1(
    *,
    manifest: Mapping[str, Any],
    cross_references: ComparisonResultBindingCrossReferences,
    artifacts: tuple[BoundArtifactRecord, ...],
) -> dict[str, Any]:
    sorted_artifacts = sorted(
        artifacts,
        key=lambda item: (item.artifact_kind, item.relative_path),
    )
    input_snapshots = _verbatim_input_snapshots(manifest)
    payload: dict[str, Any] = {
        "schema_version": BINDING_SCHEMA_VERSION,
        "bound_contract": COMPARISON_CONTRACT_VERSION,
        "comparison_definition_id": cross_references.comparison_definition_id,
        "binding_relation": BINDING_RELATION,
        "result_input_snapshots": input_snapshots,
        "result_summary_ref": _verbatim_result_summary_ref(manifest),
        "cross_references": {
            "comparison_definition_id": cross_references.comparison_definition_id,
            "manifest_content_sha256": cross_references.manifest_content_sha256,
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
        raise ComparisonSsotResultDurableEvidenceBindingError(
            f"byte-identical copy failed for {source.name}"
        )
    return source_digest


def _staging_dir_for(output_dir: Path) -> Path:
    token = uuid.uuid4().hex
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{token}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def reverify_comparison_ssot_result_durable_evidence_bundle_v1(
    *,
    output_dir: Path | str,
) -> None:
    """Replay durable evidence bundle without raw source access."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise ComparisonSsotResultDurableEvidenceBindingError(
            f"bundle directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ComparisonSsotResultDurableEvidenceBindingError(
            f"MANIFEST.sha256 verification failed: {msg}"
        )
    manifest_path = bundle_dir / MANIFEST_ARTIFACT_REL
    index_path = bundle_dir / INDEX_ARTIFACT_REL
    _validate_regular_file(manifest_path, label=MANIFEST_ARTIFACT_REL)
    _validate_regular_file(index_path, label=INDEX_ARTIFACT_REL)
    manifest = _load_validated_manifest(manifest_path)[0]
    cross = check_reference_consistency(manifest)
    index = read_manifest(index_path)
    if index.get("binding_relation") != BINDING_RELATION:
        raise ComparisonSsotResultDurableEvidenceBindingError("binding_relation mismatch")
    if index.get("comparison_definition_id") != cross.comparison_definition_id:
        raise ComparisonSsotResultDurableEvidenceBindingError(
            "binding index comparison_definition_id mismatch"
        )
    index_cross = index.get("cross_references")
    if not isinstance(index_cross, Mapping):
        raise ComparisonSsotResultDurableEvidenceBindingError("cross_references must be object")
    if index_cross.get("comparison_definition_id") != cross.comparison_definition_id:
        raise ComparisonSsotResultDurableEvidenceBindingError(
            "cross_references comparison_definition_id mismatch"
        )
    if index_cross.get("manifest_content_sha256") != cross.manifest_content_sha256:
        raise ComparisonSsotResultDurableEvidenceBindingError("manifest_content_sha256 mismatch")
    if index.get("result_input_snapshots") != _verbatim_input_snapshots(manifest):
        raise ComparisonSsotResultDurableEvidenceBindingError(
            "result_input_snapshots not preserved verbatim"
        )
    if index.get("result_summary_ref") != _verbatim_result_summary_ref(manifest):
        raise ComparisonSsotResultDurableEvidenceBindingError(
            "result_summary_ref not preserved verbatim"
        )
    validate_result_manifest_v1(manifest)


def produce_comparison_ssot_result_durable_evidence_bundle_v1(
    *,
    manifest_path: Path | str,
    output_dir: Path | str,
) -> ComparisonSsotResultDurableEvidenceBindingResult:
    """Bind validated comparison result manifest into offline durable evidence."""
    manifest_file = Path(manifest_path)
    final_dir = Path(output_dir)

    _validate_output_target(final_dir)
    _reject_unsafe_overlap(manifest_path=manifest_file, output_dir=final_dir)

    manifest, _manifest_bytes = _load_validated_manifest(manifest_file)
    cross = check_reference_consistency(manifest)
    comparison_definition_id = cross.comparison_definition_id

    for rel in (MANIFEST_ARTIFACT_REL, INDEX_ARTIFACT_REL):
        _validate_bundle_relative_path(rel)

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ComparisonSsotResultDurableEvidenceBindingError(
            f"staging directory collision: {staging}"
        )

    try:
        staging.mkdir(parents=True, exist_ok=False)

        manifest_dest = staging / MANIFEST_ARTIFACT_REL
        manifest_file_digest = _copy_byte_identical(manifest_file, manifest_dest)

        artifacts = (
            BoundArtifactRecord(
                artifact_kind="comparison_result_manifest_v1",
                relative_path=MANIFEST_ARTIFACT_REL,
                content_sha256=manifest_file_digest,
            ),
        )
        index_payload = build_binding_index_v1(
            manifest=manifest,
            cross_references=cross,
            artifacts=artifacts,
        )
        index_path = staging / INDEX_ARTIFACT_REL
        index_path.write_text(serialize_binding_index_v1(index_payload), encoding="utf-8")

        write_manifest_sha256(staging)
        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ComparisonSsotResultDurableEvidenceBindingError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ComparisonSsotResultDurableEvidenceBindingError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return ComparisonSsotResultDurableEvidenceBindingResult(
        output_dir=final_dir,
        comparison_definition_id=comparison_definition_id,
        binding_index_path=final_dir / INDEX_ARTIFACT_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
    )


__all__ = [
    "BINDING_RELATION",
    "BINDING_SCHEMA_VERSION",
    "INDEX_ARTIFACT_REL",
    "MANIFEST_ARTIFACT_REL",
    "BoundArtifactRecord",
    "ComparisonResultBindingCrossReferences",
    "ComparisonSsotResultDurableEvidenceBindingError",
    "ComparisonSsotResultDurableEvidenceBindingResult",
    "build_binding_index_v1",
    "check_reference_consistency",
    "produce_comparison_ssot_result_durable_evidence_bundle_v1",
    "reverify_comparison_ssot_result_durable_evidence_bundle_v1",
    "serialize_binding_index_v1",
]
