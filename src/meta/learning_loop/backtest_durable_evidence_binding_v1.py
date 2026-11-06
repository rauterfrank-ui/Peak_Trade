"""Offline Package L — durable evidence binding for BACKTEST run + LineageRef v1."""

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
from src.experiments.tracking.run_summary import RunSummary
from src.governance.promotion_loop.backtest_lineage_ref_producer_v1 import (
    BACKTEST_OWNER_DOMAIN,
    RUN_SUMMARY_REL_PATH,
    compute_backtest_lineage_ref_digest,
)
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    CandidateLineageManifestError,
    LineageRef,
    LineageRefType,
    LineageRelation,
    lineage_ref_from_mapping,
    lineage_ref_to_mapping,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

BINDING_SCHEMA_VERSION = "backtest_durable_evidence_binding_v1"
RUN_SUMMARY_ARTIFACT_REL = RUN_SUMMARY_REL_PATH
LINEAGE_REF_ARTIFACT_REL = "backtest_lineage_ref_v1.json"
INDEX_ARTIFACT_REL = "backtest_durable_evidence_binding_index_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".backtest_durable_evidence_staging_"
COMPLETED_RUN_STATUS = "FINISHED"

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
        "params",
        "metrics",
        "tags",
    }
)


class BacktestDurableEvidenceBindingError(ValueError):
    """Fail-closed Package L BACKTEST durable evidence binding error."""


@dataclass(frozen=True)
class BoundArtifactRecord:
    artifact_kind: str
    relative_path: str
    content_sha256: str


@dataclass(frozen=True)
class BacktestBindingCrossReferences:
    run_ref_id: str
    lineage_ref_digest: str
    lineage_ref_artifact_path: str


@dataclass(frozen=True)
class BacktestDurableEvidenceBindingResult:
    output_dir: Path
    run_ref_id: str
    binding_index_path: Path
    manifest_path: Path


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise BacktestDurableEvidenceBindingError(f"{label} must not be a symlink: {path}")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise BacktestDurableEvidenceBindingError(
                f"binding index must not contain forbidden key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise BacktestDurableEvidenceBindingError(f"{label} not found: {path}")
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise BacktestDurableEvidenceBindingError(f"{label} must be a regular file: {path}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise BacktestDurableEvidenceBindingError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise BacktestDurableEvidenceBindingError("output directory must be outside /tmp")
    parent = output_dir.parent
    if not parent.is_dir():
        raise BacktestDurableEvidenceBindingError(f"output parent directory missing: {parent}")
    if is_under_tmp(parent):
        raise BacktestDurableEvidenceBindingError("output parent directory must be outside /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _resolve_existing_directory(run_dir: Path) -> Path:
    if not run_dir.exists():
        raise BacktestDurableEvidenceBindingError(f"run_dir not found: {run_dir}")
    _reject_symlink(run_dir, label="run_dir")
    if not run_dir.is_dir():
        raise BacktestDurableEvidenceBindingError(f"run_dir is not a directory: {run_dir}")
    return run_dir.resolve()


def _load_completed_run_summary(run_dir: Path) -> tuple[RunSummary, Path, bytes]:
    summary_path = run_dir / RUN_SUMMARY_REL_PATH
    _validate_regular_file(summary_path, label=RUN_SUMMARY_REL_PATH)
    resolved = summary_path.resolve()
    if not _path_is_under(resolved, run_dir.resolve()):
        raise BacktestDurableEvidenceBindingError(
            f"{RUN_SUMMARY_REL_PATH} escapes run_dir root: {summary_path}"
        )

    summary_bytes = summary_path.read_bytes()
    try:
        summary = RunSummary.read_json(summary_path)
    except (json.JSONDecodeError, TypeError, ValueError, FileNotFoundError) as exc:
        raise BacktestDurableEvidenceBindingError(
            f"invalid {RUN_SUMMARY_REL_PATH} in run_dir={run_dir}: {exc}"
        ) from exc

    errors = summary.validate_contract(strict=True)
    if errors:
        raise BacktestDurableEvidenceBindingError(
            f"RunSummary contract validation failed for run_dir={run_dir}: " + "; ".join(errors)
        )
    if not summary.run_id or not str(summary.run_id).strip():
        raise BacktestDurableEvidenceBindingError(
            f"run_id missing or empty in {RUN_SUMMARY_REL_PATH} for run_dir={run_dir}"
        )
    if summary.status != COMPLETED_RUN_STATUS:
        raise BacktestDurableEvidenceBindingError(
            f"run is not completed (status={summary.status!r}); "
            f"expected {COMPLETED_RUN_STATUS!r} for run_dir={run_dir}"
        )
    return summary, summary_path, summary_bytes


def _load_lineage_ref_from_json_path(path: Path) -> LineageRef:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BacktestDurableEvidenceBindingError(
            f"failed to read lineage ref file: {path}"
        ) from exc
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise BacktestDurableEvidenceBindingError(
            f"invalid JSON in lineage ref file: {path}"
        ) from exc
    if not isinstance(data, Mapping):
        raise BacktestDurableEvidenceBindingError("lineage ref root must be a JSON object")
    try:
        return lineage_ref_from_mapping(data)
    except CandidateLineageManifestError as exc:
        raise BacktestDurableEvidenceBindingError(str(exc)) from exc


def _reject_unsafe_overlap(
    *,
    run_dir: Path,
    lineage_ref_path: Path,
    output_dir: Path,
) -> None:
    run_res = run_dir.resolve()
    lineage_res = lineage_ref_path.resolve()
    output_res = output_dir.resolve()

    if output_res == run_res or output_res == lineage_res:
        raise BacktestDurableEvidenceBindingError(
            "output directory must not equal a source path (fail-closed)"
        )

    if _path_is_under(run_res, output_res) or _path_is_under(lineage_res, output_res):
        raise BacktestDurableEvidenceBindingError(
            "source path must not be inside output directory (fail-closed)"
        )

    if _path_is_under(output_res, run_res) or _path_is_under(output_res, lineage_res):
        raise BacktestDurableEvidenceBindingError(
            "output directory must not be inside a source path (fail-closed)"
        )


def _validate_bundle_relative_path(rel: str) -> None:
    candidate = Path(rel)
    if candidate.is_absolute():
        raise BacktestDurableEvidenceBindingError(
            f"bundle relative path must not be absolute: {rel!r}"
        )
    if ".." in candidate.parts:
        raise BacktestDurableEvidenceBindingError(
            f"bundle relative path must not traverse upward: {rel!r}"
        )


def check_reference_consistency(
    *,
    summary: RunSummary,
    ref: LineageRef,
) -> BacktestBindingCrossReferences:
    if ref.ref_type != LineageRefType.BACKTEST:
        raise BacktestDurableEvidenceBindingError(
            f"ref_type must be BACKTEST, got {ref.ref_type.value!r}"
        )
    if ref.relation != LineageRelation.EVALUATES:
        raise BacktestDurableEvidenceBindingError(
            f"relation must be EVALUATES, got {ref.relation.value!r}"
        )
    if ref.artifact_path != RUN_SUMMARY_REL_PATH:
        raise BacktestDurableEvidenceBindingError(
            f"artifact_path must be {RUN_SUMMARY_REL_PATH!r}, got {ref.artifact_path!r}"
        )
    if ref.owner_domain != BACKTEST_OWNER_DOMAIN:
        raise BacktestDurableEvidenceBindingError(
            f"owner_domain must be {BACKTEST_OWNER_DOMAIN!r}, got {ref.owner_domain!r}"
        )
    if ref.ref_id != summary.run_id:
        raise BacktestDurableEvidenceBindingError(
            f"ref_id must match RunSummary.run_id: {ref.ref_id!r} != {summary.run_id!r}"
        )
    if ref.digest is None:
        raise BacktestDurableEvidenceBindingError("lineage ref digest is required")
    if not is_valid_sha256_hex(ref.digest):
        raise BacktestDurableEvidenceBindingError("lineage ref digest must be valid sha256 hex")
    expected_digest = compute_backtest_lineage_ref_digest(summary)
    if ref.digest != expected_digest:
        raise BacktestDurableEvidenceBindingError(
            "lineage ref digest does not match RunSummary identity digest contract"
        )
    return BacktestBindingCrossReferences(
        run_ref_id=summary.run_id,
        lineage_ref_digest=ref.digest,
        lineage_ref_artifact_path=ref.artifact_path,
    )


def _build_backtest_lineage_ref_payload(ref: LineageRef) -> dict[str, Any]:
    payload = lineage_ref_to_mapping(ref)
    for forbidden in ("params", "metrics", "returns", "trades", "equity", "tags"):
        if forbidden in payload:
            raise BacktestDurableEvidenceBindingError(
                f"lineage ref must not contain run payload key: {forbidden}"
            )
    return payload


def build_binding_index_v1(
    *,
    run_ref_id: str,
    cross_references: BacktestBindingCrossReferences,
    ref: LineageRef,
    artifacts: tuple[BoundArtifactRecord, ...],
) -> dict[str, Any]:
    sorted_artifacts = sorted(
        artifacts,
        key=lambda item: (item.artifact_kind, item.relative_path),
    )
    payload: dict[str, Any] = {
        "schema_version": BINDING_SCHEMA_VERSION,
        "run_ref_id": run_ref_id,
        "backtest_lineage_ref": _build_backtest_lineage_ref_payload(ref),
        "cross_references": {
            "run_ref_id": cross_references.run_ref_id,
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
        raise BacktestDurableEvidenceBindingError(f"byte-identical copy failed for {source.name}")
    return source_digest


def _staging_dir_for(output_dir: Path) -> Path:
    token = uuid.uuid4().hex
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{token}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def produce_backtest_durable_evidence_bundle_v1(
    *,
    run_dir: Path | str,
    backtest_lineage_ref_path: Path | str,
    output_dir: Path | str,
) -> BacktestDurableEvidenceBindingResult:
    """Bind validated BACKTEST run summary + LineageRef artifacts into offline durable evidence."""
    resolved_run_dir = _resolve_existing_directory(Path(run_dir))
    lineage_ref_file = Path(backtest_lineage_ref_path)
    final_dir = Path(output_dir)

    _validate_regular_file(lineage_ref_file, label="backtest lineage ref")
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        run_dir=resolved_run_dir,
        lineage_ref_path=lineage_ref_file,
        output_dir=final_dir,
    )

    summary, summary_path, _summary_bytes = _load_completed_run_summary(resolved_run_dir)
    ref = _load_lineage_ref_from_json_path(lineage_ref_file)
    cross = check_reference_consistency(summary=summary, ref=ref)

    for rel in (RUN_SUMMARY_ARTIFACT_REL, LINEAGE_REF_ARTIFACT_REL, INDEX_ARTIFACT_REL):
        _validate_bundle_relative_path(rel)

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise BacktestDurableEvidenceBindingError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)

        summary_dest = staging / RUN_SUMMARY_ARTIFACT_REL
        ref_dest = staging / LINEAGE_REF_ARTIFACT_REL
        summary_digest = _copy_byte_identical(summary_path, summary_dest)
        ref_digest = _copy_byte_identical(lineage_ref_file, ref_dest)

        artifacts = (
            BoundArtifactRecord(
                artifact_kind="backtest_run_summary",
                relative_path=RUN_SUMMARY_ARTIFACT_REL,
                content_sha256=summary_digest,
            ),
            BoundArtifactRecord(
                artifact_kind="backtest_lineage_ref_v1",
                relative_path=LINEAGE_REF_ARTIFACT_REL,
                content_sha256=ref_digest,
            ),
        )
        index_payload = build_binding_index_v1(
            run_ref_id=summary.run_id,
            cross_references=cross,
            ref=ref,
            artifacts=artifacts,
        )
        index_path = staging / INDEX_ARTIFACT_REL
        index_path.write_text(serialize_binding_index_v1(index_payload), encoding="utf-8")

        write_manifest_sha256(staging)
        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise BacktestDurableEvidenceBindingError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise BacktestDurableEvidenceBindingError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return BacktestDurableEvidenceBindingResult(
        output_dir=final_dir,
        run_ref_id=summary.run_id,
        binding_index_path=final_dir / INDEX_ARTIFACT_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
    )


__all__ = [
    "BINDING_SCHEMA_VERSION",
    "INDEX_ARTIFACT_REL",
    "LINEAGE_REF_ARTIFACT_REL",
    "RUN_SUMMARY_ARTIFACT_REL",
    "BacktestBindingCrossReferences",
    "BacktestDurableEvidenceBindingError",
    "BacktestDurableEvidenceBindingResult",
    "BoundArtifactRecord",
    "build_binding_index_v1",
    "check_reference_consistency",
    "produce_backtest_durable_evidence_bundle_v1",
    "serialize_binding_index_v1",
]
