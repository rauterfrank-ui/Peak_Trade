"""Package I — offline BACKTEST LineageRef producer from explicit completed run directory."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.experiments.tracking.run_summary import RunSummary
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    LineageRef,
    LineageRefType,
    LineageRelation,
    lineage_ref_to_mapping,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

RUN_SUMMARY_REL_PATH = "run_summary.json"
BACKTEST_OWNER_DOMAIN = "experiments/tracking"
BACKTEST_LINEAGE_REF_REQUIRED = False
COMPLETED_RUN_STATUS = "FINISHED"


class BacktestLineageRefProducerError(ValueError):
    """Fail-closed Package I BACKTEST LineageRef production error."""


@dataclass(frozen=True)
class BacktestLineageRefProducerResult:
    run_dir: Path
    run_summary_path: Path
    ref: LineageRef


def _resolve_existing_directory(run_dir: Path) -> Path:
    if not run_dir.exists():
        raise BacktestLineageRefProducerError(f"run_dir not found: {run_dir}")
    if run_dir.is_symlink():
        raise BacktestLineageRefProducerError(
            f"run_dir must not be a symlink (fail-closed): {run_dir}"
        )
    if not run_dir.is_dir():
        raise BacktestLineageRefProducerError(f"run_dir is not a directory: {run_dir}")
    return run_dir.resolve()


def _assert_path_under_root(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise BacktestLineageRefProducerError(
            f"path escapes run_dir root: {path} (root={root})"
        ) from exc
    return resolved


def _validate_run_summary_relative_path(artifact_path: str) -> None:
    if not artifact_path or artifact_path.strip() != artifact_path:
        raise BacktestLineageRefProducerError("artifact_path must be non-empty and trimmed")
    if artifact_path.startswith("/") or artifact_path.startswith("\\"):
        raise BacktestLineageRefProducerError("artifact_path must be relative")
    if "\\" in artifact_path:
        raise BacktestLineageRefProducerError("artifact_path must use forward slashes only")
    if ".." in artifact_path.split("/"):
        raise BacktestLineageRefProducerError("artifact_path must not contain '..' segments")


def _load_completed_run_summary(run_dir: Path) -> tuple[RunSummary, Path]:
    summary_path = run_dir / RUN_SUMMARY_REL_PATH
    if summary_path.is_symlink():
        raise BacktestLineageRefProducerError(
            f"{RUN_SUMMARY_REL_PATH} must not be a symlink (fail-closed): {summary_path}"
        )
    if not summary_path.is_file():
        raise BacktestLineageRefProducerError(
            f"{RUN_SUMMARY_REL_PATH} not found in run_dir: {run_dir}"
        )
    _assert_path_under_root(summary_path, run_dir)

    try:
        summary = RunSummary.read_json(summary_path)
    except FileNotFoundError as exc:
        raise BacktestLineageRefProducerError(
            f"{RUN_SUMMARY_REL_PATH} not found in run_dir: {run_dir}"
        ) from exc
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise BacktestLineageRefProducerError(
            f"invalid {RUN_SUMMARY_REL_PATH} in run_dir={run_dir}: {exc}"
        ) from exc

    errors = summary.validate_contract(strict=True)
    if errors:
        raise BacktestLineageRefProducerError(
            f"RunSummary contract validation failed for run_dir={run_dir}: " + "; ".join(errors)
        )

    if not summary.run_id or not str(summary.run_id).strip():
        raise BacktestLineageRefProducerError(
            f"run_id missing or empty in {RUN_SUMMARY_REL_PATH} for run_dir={run_dir}"
        )

    if summary.status != COMPLETED_RUN_STATUS:
        raise BacktestLineageRefProducerError(
            f"run is not completed (status={summary.status!r}); "
            f"expected {COMPLETED_RUN_STATUS!r} for run_dir={run_dir}"
        )

    return summary, summary_path


def compute_backtest_lineage_ref_digest(summary: RunSummary) -> str:
    """Deterministic digest from stable RunSummary identity fields (payload-free reference)."""
    payload = {
        "run_id": summary.run_id,
        "started_at_utc": summary.started_at_utc,
        "finished_at_utc": summary.finished_at_utc,
        "status": summary.status,
        "tracking_backend": summary.tracking_backend,
    }
    digest = compute_content_sha256(payload)
    if not is_valid_sha256_hex(digest):
        raise BacktestLineageRefProducerError("computed digest is not valid sha256 hex")
    return digest


def build_backtest_lineage_ref_from_run_summary(
    summary: RunSummary,
    *,
    artifact_path: str = RUN_SUMMARY_REL_PATH,
) -> LineageRef:
    """Build a validated BACKTEST LineageRef from an already validated RunSummary."""
    _validate_run_summary_relative_path(artifact_path)
    digest = compute_backtest_lineage_ref_digest(summary)
    return LineageRef(
        ref_type=LineageRefType.BACKTEST,
        ref_id=str(summary.run_id),
        relation=LineageRelation.EVALUATES,
        owner_domain=BACKTEST_OWNER_DOMAIN,
        required=BACKTEST_LINEAGE_REF_REQUIRED,
        digest=digest,
        artifact_path=artifact_path,
    )


def produce_backtest_lineage_ref_v1(*, run_dir: Path | str) -> BacktestLineageRefProducerResult:
    """Extract a reference-only BACKTEST LineageRef from an explicit completed run directory."""
    resolved_run_dir = _resolve_existing_directory(Path(run_dir))
    summary, summary_path = _load_completed_run_summary(resolved_run_dir)
    ref = build_backtest_lineage_ref_from_run_summary(summary)
    return BacktestLineageRefProducerResult(
        run_dir=resolved_run_dir,
        run_summary_path=summary_path,
        ref=ref,
    )


def serialize_backtest_lineage_ref_v1(ref: LineageRef) -> str:
    """Serialize a BACKTEST LineageRef to deterministic canonical JSON."""
    if ref.ref_type != LineageRefType.BACKTEST:
        raise BacktestLineageRefProducerError(
            f"ref_type must be BACKTEST, got {ref.ref_type.value!r}"
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


def write_backtest_lineage_ref_v1_atomic(
    ref: LineageRef,
    output_path: Path | str,
    *,
    fail_closed_if_exists: bool = True,
) -> Path:
    """Validate and atomically write a BACKTEST LineageRef JSON file."""
    out = Path(output_path)
    if fail_closed_if_exists and out.exists():
        raise BacktestLineageRefProducerError(f"output path already exists (fail-closed): {out}")
    serialized = serialize_backtest_lineage_ref_v1(ref)
    _atomic_write_text(out, serialized)
    return out


def produce_backtest_lineage_ref_v1_to_path(
    *,
    run_dir: Path | str,
    output_path: Path | str,
    fail_closed_if_exists: bool = True,
) -> BacktestLineageRefProducerResult:
    """End-to-end offline producer: explicit run_dir -> validated BACKTEST LineageRef JSON."""
    result = produce_backtest_lineage_ref_v1(run_dir=run_dir)
    write_backtest_lineage_ref_v1_atomic(
        result.ref,
        output_path,
        fail_closed_if_exists=fail_closed_if_exists,
    )
    return result
