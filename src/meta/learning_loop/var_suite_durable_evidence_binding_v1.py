"""Offline Package K — durable evidence binding for VAR_SUITE report + LineageRef v1."""

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
    LineageRef,
    LineageRefType,
    LineageRelation,
    lineage_ref_from_mapping,
    lineage_ref_to_mapping,
)
from src.governance.promotion_loop.var_suite_lineage_ref_producer_v1 import (
    VAR_SUITE_OWNER_DOMAIN,
    compute_var_suite_lineage_ref_digest,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)
from src.risk.validation.var_suite_backtest_wiring_v1 import SUITE_REPORT_JSON

BINDING_SCHEMA_VERSION = "var_suite_durable_evidence_binding_v1"
SUITE_REPORT_ARTIFACT_REL = SUITE_REPORT_JSON
LINEAGE_REF_ARTIFACT_REL = "var_suite_lineage_ref_v1.json"
INDEX_ARTIFACT_REL = "var_suite_durable_evidence_binding_index_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".var_suite_durable_evidence_staging_"

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
        "overall_result",
        "observations",
        "breaches",
        "basel_traffic_light",
    }
)


class VarSuiteDurableEvidenceBindingError(ValueError):
    """Fail-closed Package K VAR_SUITE durable evidence binding error."""


@dataclass(frozen=True)
class BoundArtifactRecord:
    artifact_kind: str
    relative_path: str
    content_sha256: str


@dataclass(frozen=True)
class VarSuiteBindingCrossReferences:
    report_ref_id: str
    lineage_ref_digest: str
    lineage_ref_artifact_path: str


@dataclass(frozen=True)
class VarSuiteDurableEvidenceBindingResult:
    output_dir: Path
    report_ref_id: str
    binding_index_path: Path
    manifest_path: Path


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise VarSuiteDurableEvidenceBindingError(f"{label} must not be a symlink: {path}")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise VarSuiteDurableEvidenceBindingError(
                f"binding index must not contain forbidden key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise VarSuiteDurableEvidenceBindingError(f"{label} not found: {path}")
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise VarSuiteDurableEvidenceBindingError(f"{label} must be a regular file: {path}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise VarSuiteDurableEvidenceBindingError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise VarSuiteDurableEvidenceBindingError("output directory must be outside /tmp")
    parent = output_dir.parent
    if not parent.is_dir():
        raise VarSuiteDurableEvidenceBindingError(f"output parent directory missing: {parent}")
    if is_under_tmp(parent):
        raise VarSuiteDurableEvidenceBindingError("output parent directory must be outside /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _resolve_existing_report_dir(report_dir: Path) -> Path:
    if not report_dir.exists():
        raise VarSuiteDurableEvidenceBindingError(f"report_dir not found: {report_dir}")
    _reject_symlink(report_dir, label="report_dir")
    if not report_dir.is_dir():
        raise VarSuiteDurableEvidenceBindingError(f"report_dir is not a directory: {report_dir}")
    return report_dir.resolve()


def _validate_suite_report_structure(data: object, *, report_dir: Path) -> None:
    if not isinstance(data, dict):
        raise VarSuiteDurableEvidenceBindingError(
            f"suite_report.json root must be a JSON object for report_dir={report_dir}"
        )
    if "overall_result" not in data:
        raise VarSuiteDurableEvidenceBindingError(
            f"suite_report.json missing overall_result for report_dir={report_dir}"
        )


def _load_suite_report_bytes(report_dir: Path) -> tuple[bytes, Path]:
    report_path = report_dir / SUITE_REPORT_JSON
    _validate_regular_file(report_path, label=SUITE_REPORT_JSON)
    resolved = report_path.resolve()
    if not _path_is_under(resolved, report_dir.resolve()):
        raise VarSuiteDurableEvidenceBindingError(
            f"{SUITE_REPORT_JSON} escapes report_dir root: {report_path}"
        )
    report_bytes = report_path.read_bytes()
    try:
        data = json.loads(report_bytes)
    except json.JSONDecodeError as exc:
        raise VarSuiteDurableEvidenceBindingError(
            f"invalid {SUITE_REPORT_JSON} in report_dir={report_dir}: {exc}"
        ) from exc
    _validate_suite_report_structure(data, report_dir=report_dir)
    return report_bytes, report_path


def _load_lineage_ref_from_json_path(path: Path) -> LineageRef:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise VarSuiteDurableEvidenceBindingError(
            f"failed to read lineage ref file: {path}"
        ) from exc
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise VarSuiteDurableEvidenceBindingError(
            f"invalid JSON in lineage ref file: {path}"
        ) from exc
    if not isinstance(data, Mapping):
        raise VarSuiteDurableEvidenceBindingError("lineage ref root must be a JSON object")
    try:
        return lineage_ref_from_mapping(data)
    except CandidateLineageManifestError as exc:
        raise VarSuiteDurableEvidenceBindingError(str(exc)) from exc


def _reject_unsafe_overlap(
    *,
    report_dir: Path,
    lineage_ref_path: Path,
    output_dir: Path,
) -> None:
    report_res = report_dir.resolve()
    lineage_res = lineage_ref_path.resolve()
    output_res = output_dir.resolve()

    if output_res == report_res or output_res == lineage_res:
        raise VarSuiteDurableEvidenceBindingError(
            "output directory must not equal a source path (fail-closed)"
        )

    if _path_is_under(report_res, output_res) or _path_is_under(lineage_res, output_res):
        raise VarSuiteDurableEvidenceBindingError(
            "source path must not be inside output directory (fail-closed)"
        )

    if _path_is_under(output_res, report_res) or _path_is_under(output_res, lineage_res):
        raise VarSuiteDurableEvidenceBindingError(
            "output directory must not be inside a source path (fail-closed)"
        )


def _validate_bundle_relative_path(rel: str) -> None:
    candidate = Path(rel)
    if candidate.is_absolute():
        raise VarSuiteDurableEvidenceBindingError(
            f"bundle relative path must not be absolute: {rel!r}"
        )
    if ".." in candidate.parts:
        raise VarSuiteDurableEvidenceBindingError(
            f"bundle relative path must not traverse upward: {rel!r}"
        )


def check_reference_consistency(
    *,
    report_dir: Path,
    report_bytes: bytes,
    ref: LineageRef,
) -> VarSuiteBindingCrossReferences:
    if ref.ref_type != LineageRefType.VAR_SUITE:
        raise VarSuiteDurableEvidenceBindingError(
            f"ref_type must be VAR_SUITE, got {ref.ref_type.value!r}"
        )
    if ref.relation != LineageRelation.VALIDATES:
        raise VarSuiteDurableEvidenceBindingError(
            f"relation must be VALIDATES, got {ref.relation.value!r}"
        )
    if ref.artifact_path != SUITE_REPORT_JSON:
        raise VarSuiteDurableEvidenceBindingError(
            f"artifact_path must be {SUITE_REPORT_JSON!r}, got {ref.artifact_path!r}"
        )
    if ref.owner_domain != VAR_SUITE_OWNER_DOMAIN:
        raise VarSuiteDurableEvidenceBindingError(
            f"owner_domain must be {VAR_SUITE_OWNER_DOMAIN!r}, got {ref.owner_domain!r}"
        )
    if ref.ref_id != report_dir.name:
        raise VarSuiteDurableEvidenceBindingError(
            f"ref_id must match report_dir.name: {ref.ref_id!r} != {report_dir.name!r}"
        )
    if ref.digest is None:
        raise VarSuiteDurableEvidenceBindingError("lineage ref digest is required")
    if not is_valid_sha256_hex(ref.digest):
        raise VarSuiteDurableEvidenceBindingError("lineage ref digest must be valid sha256 hex")
    expected_digest = compute_var_suite_lineage_ref_digest(report_bytes)
    if ref.digest != expected_digest:
        raise VarSuiteDurableEvidenceBindingError(
            "lineage ref digest does not match suite_report.json file bytes"
        )
    return VarSuiteBindingCrossReferences(
        report_ref_id=report_dir.name,
        lineage_ref_digest=ref.digest,
        lineage_ref_artifact_path=ref.artifact_path,
    )


def _build_var_suite_lineage_ref_payload(ref: LineageRef) -> dict[str, Any]:
    payload = lineage_ref_to_mapping(ref)
    for forbidden in ("overall_result", "observations", "breaches"):
        if forbidden in payload:
            raise VarSuiteDurableEvidenceBindingError(
                f"lineage ref must not contain report payload key: {forbidden}"
            )
    return payload


def build_binding_index_v1(
    *,
    report_ref_id: str,
    cross_references: VarSuiteBindingCrossReferences,
    ref: LineageRef,
    artifacts: tuple[BoundArtifactRecord, ...],
) -> dict[str, Any]:
    sorted_artifacts = sorted(
        artifacts,
        key=lambda item: (item.artifact_kind, item.relative_path),
    )
    payload: dict[str, Any] = {
        "schema_version": BINDING_SCHEMA_VERSION,
        "report_ref_id": report_ref_id,
        "var_suite_lineage_ref": _build_var_suite_lineage_ref_payload(ref),
        "cross_references": {
            "report_ref_id": cross_references.report_ref_id,
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
        raise VarSuiteDurableEvidenceBindingError(f"byte-identical copy failed for {source.name}")
    return source_digest


def _staging_dir_for(output_dir: Path) -> Path:
    token = uuid.uuid4().hex
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{token}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def produce_var_suite_durable_evidence_bundle_v1(
    *,
    report_dir: Path | str,
    var_suite_lineage_ref_path: Path | str,
    output_dir: Path | str,
) -> VarSuiteDurableEvidenceBindingResult:
    """Bind validated VAR_SUITE report + LineageRef artifacts into offline durable evidence."""
    resolved_report_dir = _resolve_existing_report_dir(Path(report_dir))
    lineage_ref_file = Path(var_suite_lineage_ref_path)
    final_dir = Path(output_dir)

    _validate_regular_file(lineage_ref_file, label="var suite lineage ref")
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        report_dir=resolved_report_dir,
        lineage_ref_path=lineage_ref_file,
        output_dir=final_dir,
    )

    report_bytes, report_path = _load_suite_report_bytes(resolved_report_dir)
    ref = _load_lineage_ref_from_json_path(lineage_ref_file)
    cross = check_reference_consistency(
        report_dir=resolved_report_dir,
        report_bytes=report_bytes,
        ref=ref,
    )

    for rel in (SUITE_REPORT_ARTIFACT_REL, LINEAGE_REF_ARTIFACT_REL, INDEX_ARTIFACT_REL):
        _validate_bundle_relative_path(rel)

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise VarSuiteDurableEvidenceBindingError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)

        report_dest = staging / SUITE_REPORT_ARTIFACT_REL
        ref_dest = staging / LINEAGE_REF_ARTIFACT_REL
        report_digest = _copy_byte_identical(report_path, report_dest)
        ref_digest = _copy_byte_identical(lineage_ref_file, ref_dest)

        artifacts = (
            BoundArtifactRecord(
                artifact_kind="var_suite_report",
                relative_path=SUITE_REPORT_ARTIFACT_REL,
                content_sha256=report_digest,
            ),
            BoundArtifactRecord(
                artifact_kind="var_suite_lineage_ref_v1",
                relative_path=LINEAGE_REF_ARTIFACT_REL,
                content_sha256=ref_digest,
            ),
        )
        index_payload = build_binding_index_v1(
            report_ref_id=resolved_report_dir.name,
            cross_references=cross,
            ref=ref,
            artifacts=artifacts,
        )
        index_path = staging / INDEX_ARTIFACT_REL
        index_path.write_text(serialize_binding_index_v1(index_payload), encoding="utf-8")

        write_manifest_sha256(staging)
        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise VarSuiteDurableEvidenceBindingError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise VarSuiteDurableEvidenceBindingError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return VarSuiteDurableEvidenceBindingResult(
        output_dir=final_dir,
        report_ref_id=resolved_report_dir.name,
        binding_index_path=final_dir / INDEX_ARTIFACT_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
    )


__all__ = [
    "BINDING_SCHEMA_VERSION",
    "INDEX_ARTIFACT_REL",
    "LINEAGE_REF_ARTIFACT_REL",
    "SUITE_REPORT_ARTIFACT_REL",
    "BoundArtifactRecord",
    "VarSuiteBindingCrossReferences",
    "VarSuiteDurableEvidenceBindingError",
    "VarSuiteDurableEvidenceBindingResult",
    "build_binding_index_v1",
    "check_reference_consistency",
    "produce_var_suite_durable_evidence_bundle_v1",
    "serialize_binding_index_v1",
]
