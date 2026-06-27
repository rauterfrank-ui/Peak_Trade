"""Package J — offline VAR_SUITE LineageRef producer from explicit existing report directory."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    LineageRef,
    LineageRefType,
    LineageRelation,
    lineage_ref_to_mapping,
)
from src.meta.learning_loop.contract_safety_v1 import (
    deterministic_json_dumps,
    is_valid_sha256_hex,
)
from src.risk.validation.var_suite_backtest_wiring_v1 import SUITE_REPORT_JSON

VAR_SUITE_OWNER_DOMAIN = "risk/validation/var_suite_backtest_wiring_v1"
VAR_SUITE_LINEAGE_REF_REQUIRED = False
_FORBIDDEN_REF_IDS = frozenset({".", ".."})


class VarSuiteLineageRefProducerError(ValueError):
    """Fail-closed Package J VAR_SUITE LineageRef production error."""


@dataclass(frozen=True)
class VarSuiteLineageRefProducerResult:
    report_dir: Path
    suite_report_path: Path
    ref: LineageRef


def _resolve_existing_directory(report_dir: Path) -> Path:
    if not report_dir.exists():
        raise VarSuiteLineageRefProducerError(f"report_dir not found: {report_dir}")
    if report_dir.is_symlink():
        raise VarSuiteLineageRefProducerError(
            f"report_dir must not be a symlink (fail-closed): {report_dir}"
        )
    if not report_dir.is_dir():
        raise VarSuiteLineageRefProducerError(f"report_dir is not a directory: {report_dir}")
    return report_dir.resolve()


def _assert_path_under_root(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise VarSuiteLineageRefProducerError(
            f"path escapes report_dir root: {path} (root={root})"
        ) from exc
    return resolved


def _validate_artifact_relative_path(artifact_path: str) -> None:
    if not artifact_path or artifact_path.strip() != artifact_path:
        raise VarSuiteLineageRefProducerError("artifact_path must be non-empty and trimmed")
    if artifact_path.startswith("/") or artifact_path.startswith("\\"):
        raise VarSuiteLineageRefProducerError("artifact_path must be relative")
    if "\\" in artifact_path:
        raise VarSuiteLineageRefProducerError("artifact_path must use forward slashes only")
    if ".." in artifact_path.split("/"):
        raise VarSuiteLineageRefProducerError("artifact_path must not contain '..' segments")


def _validate_ref_id(ref_id: str, *, report_dir: Path) -> str:
    if not ref_id or not ref_id.strip():
        raise VarSuiteLineageRefProducerError(
            f"ref_id missing or empty for report_dir={report_dir}"
        )
    if ref_id in _FORBIDDEN_REF_IDS:
        raise VarSuiteLineageRefProducerError(
            f"ref_id is unsafe for report_dir={report_dir}: {ref_id!r}"
        )
    if "/" in ref_id or "\\" in ref_id:
        raise VarSuiteLineageRefProducerError(
            f"ref_id must be a single directory name for report_dir={report_dir}"
        )
    return ref_id


def _validate_suite_report_structure(data: object, *, report_dir: Path) -> None:
    if not isinstance(data, dict):
        raise VarSuiteLineageRefProducerError(
            f"suite_report.json root must be a JSON object for report_dir={report_dir}"
        )
    if "overall_result" not in data:
        raise VarSuiteLineageRefProducerError(
            f"suite_report.json missing overall_result for report_dir={report_dir}"
        )


def _load_existing_suite_report(report_dir: Path) -> tuple[bytes, Path]:
    report_path = report_dir / SUITE_REPORT_JSON
    if report_path.is_symlink():
        raise VarSuiteLineageRefProducerError(
            f"{SUITE_REPORT_JSON} must not be a symlink (fail-closed): {report_path}"
        )
    if report_path.is_dir():
        raise VarSuiteLineageRefProducerError(
            f"{SUITE_REPORT_JSON} is a directory, expected regular file: {report_path}"
        )
    if not report_path.is_file():
        raise VarSuiteLineageRefProducerError(
            f"{SUITE_REPORT_JSON} not found in report_dir: {report_dir}"
        )
    _assert_path_under_root(report_path, report_dir)

    report_bytes = report_path.read_bytes()
    try:
        data = json.loads(report_bytes)
    except json.JSONDecodeError as exc:
        raise VarSuiteLineageRefProducerError(
            f"invalid {SUITE_REPORT_JSON} in report_dir={report_dir}: {exc}"
        ) from exc

    _validate_suite_report_structure(data, report_dir=report_dir)
    return report_bytes, report_path


def compute_var_suite_lineage_ref_digest(report_bytes: bytes) -> str:
    """Deterministic digest from exact suite_report.json file bytes (payload-free reference)."""
    digest = hashlib.sha256(report_bytes).hexdigest()
    if not is_valid_sha256_hex(digest):
        raise VarSuiteLineageRefProducerError("computed digest is not valid sha256 hex")
    return digest


def build_var_suite_lineage_ref_from_report_dir(
    report_dir: Path,
    *,
    report_bytes: bytes,
    artifact_path: str = SUITE_REPORT_JSON,
) -> LineageRef:
    """Build a validated VAR_SUITE LineageRef from an already validated report directory."""
    _validate_artifact_relative_path(artifact_path)
    ref_id = _validate_ref_id(report_dir.name, report_dir=report_dir)
    digest = compute_var_suite_lineage_ref_digest(report_bytes)
    return LineageRef(
        ref_type=LineageRefType.VAR_SUITE,
        ref_id=ref_id,
        relation=LineageRelation.VALIDATES,
        owner_domain=VAR_SUITE_OWNER_DOMAIN,
        required=VAR_SUITE_LINEAGE_REF_REQUIRED,
        digest=digest,
        artifact_path=artifact_path,
    )


def produce_var_suite_lineage_ref_v1(*, report_dir: Path | str) -> VarSuiteLineageRefProducerResult:
    """Extract a reference-only VAR_SUITE LineageRef from an explicit report directory."""
    resolved_report_dir = _resolve_existing_directory(Path(report_dir))
    report_bytes, report_path = _load_existing_suite_report(resolved_report_dir)
    ref = build_var_suite_lineage_ref_from_report_dir(
        resolved_report_dir,
        report_bytes=report_bytes,
    )
    return VarSuiteLineageRefProducerResult(
        report_dir=resolved_report_dir,
        suite_report_path=report_path,
        ref=ref,
    )


def serialize_var_suite_lineage_ref_v1(ref: LineageRef) -> str:
    """Serialize a VAR_SUITE LineageRef to deterministic canonical JSON."""
    if ref.ref_type != LineageRefType.VAR_SUITE:
        raise VarSuiteLineageRefProducerError(
            f"ref_type must be VAR_SUITE, got {ref.ref_type.value!r}"
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


def write_var_suite_lineage_ref_v1_atomic(
    ref: LineageRef,
    output_path: Path | str,
    *,
    fail_closed_if_exists: bool = True,
) -> Path:
    """Validate and atomically write a VAR_SUITE LineageRef JSON file."""
    out = Path(output_path)
    if fail_closed_if_exists and out.exists():
        raise VarSuiteLineageRefProducerError(f"output path already exists (fail-closed): {out}")
    serialized = serialize_var_suite_lineage_ref_v1(ref)
    _atomic_write_text(out, serialized)
    return out


def produce_var_suite_lineage_ref_v1_to_path(
    *,
    report_dir: Path | str,
    output_path: Path | str,
    fail_closed_if_exists: bool = True,
) -> VarSuiteLineageRefProducerResult:
    """End-to-end offline producer: explicit report_dir -> validated VAR_SUITE LineageRef JSON."""
    result = produce_var_suite_lineage_ref_v1(report_dir=report_dir)
    write_var_suite_lineage_ref_v1_atomic(
        result.ref,
        output_path,
        fail_closed_if_exists=fail_closed_if_exists,
    )
    return result
