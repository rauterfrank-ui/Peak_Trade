"""Operator-started one-shot GHOSV Execution bounded offline observer."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.ghosv_bounded_context_v1.constants_v1 import (
    ADAPTER_MODE,
    EXTERNAL_POST_COUNT,
    SAFETY_ESCALATION_ENABLED,
    TRAFFIC_GREEN,
)
from src.ops.ghosv_bounded_context_v1.current_execution_evidence_reader_v1 import (
    CurrentExecutionEvidenceSourcesV1,
    observe_current_execution_via_ghosv_v1,
    read_current_execution_evidence_v1,
)
from src.ops.ghosv_bounded_context_v1.execution_offline_consistency_guard_v1 import (
    BoundedInputError,
    ConsistencyGuardResultV1,
    MAX_OBSERVER_WALL_SECONDS,
    run_consistency_guard_v1,
)
from src.ops.ghosv_bounded_context_v1.s01_evidence_ingest_v1 import GhosvEvidenceIngestError
from src.ops.ghosv_bounded_context_v1.types_v1 import (
    GhosvBoundedContextResultV1,
    GhosvEvidenceKind,
    GhosvIntegrityFindingV1,
)

OBSERVER_CONTRACT = "ghosv_execution_bounded_offline_observer.v1"
OBSERVER_MODE = "OPERATOR_STARTED_ONE_SHOT"
REPORT_FILENAME = "GHOSV_EXECUTION_BOUNDED_OFFLINE_OBSERVER_REPORT_V1.json"


@dataclass(frozen=True)
class ExecutionOfflineObserverPathsV1:
    trade_id: str
    output_dir: Path
    recon_dir: Path | None = None
    pre_external_report: Path | None = None
    final_order_envelope: Path | None = None
    governed_cycle_evidence_dir: Path | None = None
    g004_post_attempt_store_root: Path | None = None
    current_baseline_sha: str = ""


class OutputPathSafetyError(ValueError):
    pass


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def assert_output_dir_safe_v1(*, output_dir: Path, source_paths: tuple[Path | None, ...]) -> None:
    """Fail closed on canonical path overlap (includes symlink-resolved aliases)."""
    out = Path(output_dir).expanduser().resolve()
    for raw in source_paths:
        if raw is None:
            continue
        src = Path(raw).expanduser().resolve()
        if out == src:
            raise OutputPathSafetyError(f"OUTPUT_EQUALS_SOURCE:{src}")
        if src.is_dir():
            if _path_is_under(out, src):
                raise OutputPathSafetyError(f"OUTPUT_INSIDE_SOURCE_DIR:{out}:{src}")
            if _path_is_under(src, out):
                raise OutputPathSafetyError(f"SOURCE_DIR_INSIDE_OUTPUT:{src}:{out}")
        elif src.is_file():
            parent = src.parent
            if _path_is_under(out, parent):
                raise OutputPathSafetyError(f"OUTPUT_INSIDE_SOURCE_PARENT:{out}:{src}")
            if _path_is_under(parent, out):
                raise OutputPathSafetyError(f"SOURCE_FILE_INSIDE_OUTPUT:{src}:{out}")
    out.mkdir(parents=True, exist_ok=True)


def _source_presence_map(paths: ExecutionOfflineObserverPathsV1) -> dict[str, str]:
    def _one(label: str, p: Path | None) -> str:
        if p is None:
            return "NOT_SELECTED"
        path = Path(p)
        if path.is_file() or path.is_dir():
            return "PRESENT"
        return "PATH_MISSING"

    return {
        "recon_dir": _one("recon_dir", paths.recon_dir),
        "pre_external_report": _one("pre_external_report", paths.pre_external_report),
        "final_order_envelope": _one("final_order_envelope", paths.final_order_envelope),
        "governed_cycle_evidence_dir": _one(
            "governed_cycle_evidence_dir", paths.governed_cycle_evidence_dir
        ),
        "g004_post_attempt_store_root": _one(
            "g004_post_attempt_store_root", paths.g004_post_attempt_store_root
        ),
    }


def _missing_evidence_classes(records_kinds: set[str]) -> list[str]:
    optional_gaps = []
    expected = {
        "EXECUTION_PREPARATION": GhosvEvidenceKind.ORDER_ENVELOPE.value,
        "PRE_EXTERNAL_WITNESS": GhosvEvidenceKind.PRE_EXTERNAL_REPORT.value,
        "POST_SUBMISSION_WITNESS": GhosvEvidenceKind.EXECUTION_ATTEMPT.value,
        "VENUE_ACK": GhosvEvidenceKind.ORDER_ACK.value,
        "FILL": GhosvEvidenceKind.FILL.value,
        "FULL_FILL": GhosvEvidenceKind.FULL_FILL.value,
        "PARTIAL_FILL": GhosvEvidenceKind.PARTIAL_FILL.value,
        "EXECUTION_RECON": GhosvEvidenceKind.RECONCILIATION_GATE.value,
        "POSITION": GhosvEvidenceKind.POSITION_SNAPSHOT.value,
    }
    for label, kind in expected.items():
        if kind not in records_kinds:
            optional_gaps.append(label)
    return optional_gaps


def _lifecycle_completeness(
    *,
    records_kinds: set[str],
    guard: ConsistencyGuardResultV1,
    post_submission_witnessed: bool,
    pre_external_witnessed: bool,
) -> str:
    if guard.evidence_consistency == "FAIL":
        return "INCONSISTENT_SOURCES"
    has_pre = pre_external_witnessed
    has_post = post_submission_witnessed
    has_ack = GhosvEvidenceKind.ORDER_ACK.value in records_kinds
    has_fill = bool(
        records_kinds
        & {
            GhosvEvidenceKind.FILL.value,
            GhosvEvidenceKind.FULL_FILL.value,
            GhosvEvidenceKind.PARTIAL_FILL.value,
        }
    )
    if has_fill:
        return "FILL_WITNESSED"
    if has_ack:
        return "VENUE_ACK_WITNESSED"
    if has_post:
        return "POST_SUBMISSION_WITNESSED"
    if has_pre:
        return "PRE_EXTERNAL_ONLY"
    if records_kinds:
        return "PARTIAL_WITNESSED"
    return "UNKNOWN"


def _serialize_finding(f: GhosvIntegrityFindingV1) -> dict[str, Any]:
    return {
        "check_id": f.check_id,
        "outcome": f.outcome,
        "traffic": f.traffic,
        "reason": f.reason,
        "evidence_refs": list(f.evidence_refs),
    }


def _serialize_ghosv_result(result: GhosvBoundedContextResultV1) -> dict[str, Any]:
    return {
        "package_id": result.package_id,
        "schema_version": result.schema_version,
        "traffic_overall": result.traffic_overall,
        "traffic_by_trade": list(result.traffic_by_trade),
        "findings": [_serialize_finding(f) for f in result.findings],
        "incidents": [
            {
                "incident_id": i.incident_id,
                "incident_type": i.incident_type,
                "severity": i.severity,
                "trade_id": i.trade_id,
                "instrument_id": i.instrument_id,
                "order_id": i.order_id,
            }
            for i in result.incidents
        ],
        "adapter_mode": result.adapter_decision.adapter_mode,
        "adapter_productive_side_effects": result.adapter_decision.productive_side_effects,
        "ingest_rejected": list(result.ingest_rejected),
    }


def _serialize_source_check(check: Any) -> dict[str, Any]:
    return {
        "source_id": check.source_id,
        "selected": check.selected,
        "presence": check.presence,
        "consistency": check.consistency,
        "reason_codes": list(check.reason_codes),
        "details": dict(check.details),
    }


def run_execution_bounded_offline_observer_v1(
    paths: ExecutionOfflineObserverPathsV1,
    *,
    detected_at: str | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    detected = detected_at or _utc_now_iso()
    assert_output_dir_safe_v1(
        output_dir=paths.output_dir,
        source_paths=(
            paths.recon_dir,
            paths.pre_external_report,
            paths.final_order_envelope,
            paths.governed_cycle_evidence_dir,
            paths.g004_post_attempt_store_root,
        ),
    )

    guard = run_consistency_guard_v1(
        recon_dir=paths.recon_dir,
        pre_external_report=paths.pre_external_report,
        final_order_envelope=paths.final_order_envelope,
        governed_cycle_evidence_dir=paths.governed_cycle_evidence_dir,
        g004_post_attempt_store_root=paths.g004_post_attempt_store_root,
    )

    ghosv_error: str | None = None
    ghosv_result: GhosvBoundedContextResultV1 | None = None
    record_kinds: set[str] = set()
    post_submission_witnessed = False
    pre_external_witnessed = False
    sources = CurrentExecutionEvidenceSourcesV1(
        trade_id=paths.trade_id,
        recon_dir=paths.recon_dir,
        final_order_envelope_json=paths.final_order_envelope,
        pre_external_convergence_report_json=paths.pre_external_report,
        governed_cycle_evidence_dir=paths.governed_cycle_evidence_dir,
        g004_post_attempt_store_root=paths.g004_post_attempt_store_root,
    )
    try:
        records = read_current_execution_evidence_v1(sources)
        record_kinds = {r.kind for r in records}
        pre_external_witnessed = any(
            r.kind == GhosvEvidenceKind.PRE_EXTERNAL_REPORT.value for r in records
        )
        post_submission_witnessed = any(
            r.kind == GhosvEvidenceKind.EXECUTION_ATTEMPT.value
            and r.payload.get("post_submission_witness") is True
            for r in records
        )
        ghosv_result = observe_current_execution_via_ghosv_v1(sources, detected_at=detected)
    except (GhosvEvidenceIngestError, BoundedInputError) as exc:
        ghosv_error = str(exc)

    if time.monotonic() - started > MAX_OBSERVER_WALL_SECONDS:
        raise TimeoutError("OBSERVER_WALL_TIME_EXCEEDED")

    traffic = ghosv_result.traffic_overall if ghosv_result else TRAFFIC_GREEN
    if ghosv_error:
        traffic = "UNKNOWN"
    if guard.evidence_consistency in {"FAIL", "PARTIAL"} and traffic == TRAFFIC_GREEN:
        traffic = "YELLOW"

    lifecycle = _lifecycle_completeness(
        records_kinds=record_kinds,
        guard=guard,
        post_submission_witnessed=post_submission_witnessed,
        pre_external_witnessed=pre_external_witnessed,
    )

    report: dict[str, Any] = {
        "contract": OBSERVER_CONTRACT,
        "observer_run_success": ghosv_error is None,
        "observer_run_status": "OBSERVER_RUN_SUCCESS"
        if ghosv_error is None
        else "OBSERVER_RUN_FAILED",
        "current_baseline_sha": paths.current_baseline_sha,
        "observer_invocation_mode": OBSERVER_MODE,
        "observer_entrypoint": "src.ops.ghosv_bounded_context_v1.execution_bounded_offline_observer_v1",
        "selected_evidence_sources": _source_presence_map(paths),
        "source_consistency": {
            "evidence_consistency": guard.evidence_consistency,
            "recon_manifest_validation": guard.recon.consistency
            if guard.recon.selected
            else "NOT_SELECTED",
            "ledger_read_consistency": guard.ledger.consistency
            if guard.ledger.selected
            else "NOT_SELECTED",
            "transitions_consistency": guard.transitions.consistency
            if guard.transitions.selected
            else "NOT_SELECTED",
            "g004_consistency": guard.g004.consistency if guard.g004.selected else "NOT_SELECTED",
            "cross_file": _serialize_source_check(guard.cross_file),
            "cross_file_snapshot_guarantee": guard.cross_file_snapshot_guarantee,
            "guard_details": {
                "recon": _serialize_source_check(guard.recon),
                "ledger": _serialize_source_check(guard.ledger),
                "transitions": _serialize_source_check(guard.transitions),
                "g004": _serialize_source_check(guard.g004),
            },
        },
        "identity_provenance_coverage": {
            "trade_id": paths.trade_id,
            "input_file_count": guard.input_file_count,
            "input_bytes_total": guard.input_bytes_total,
        },
        "ghosv_pipeline_error": ghosv_error,
        "ghosv_result": _serialize_ghosv_result(ghosv_result) if ghosv_result else None,
        "ghosv_traffic_light": traffic,
        "execution_lifecycle_completeness": lifecycle,
        "missing_evidence_classes": _missing_evidence_classes(record_kinds),
        "safety_adapter_status": {
            "adapter_mode": ADAPTER_MODE,
            "safety_escalation_enabled": SAFETY_ESCALATION_ENABLED,
            "productive_runtime_activation": False,
            "external_post_count": EXTERNAL_POST_COUNT,
        },
        "evidence_consistency": guard.evidence_consistency,
        "detected_at": detected,
        "disclaimer": {
            "cli_exit_not_traffic_green": True,
            "observer_run_success_not_execution_green": True,
        },
    }

    out_path = Path(paths.output_dir).resolve() / REPORT_FILENAME
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report["report_path"] = str(out_path)
    return report


def _parse_args(argv: list[str] | None = None) -> ExecutionOfflineObserverPathsV1:
    parser = argparse.ArgumentParser(
        description="GHOSV Execution bounded offline observer (read-only, one-shot).",
    )
    parser.add_argument("--trade-id", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--recon-dir", type=Path, default=None)
    parser.add_argument("--pre-external-report", type=Path, default=None)
    parser.add_argument("--final-order-envelope", type=Path, default=None)
    parser.add_argument("--governed-cycle-evidence-dir", type=Path, default=None)
    parser.add_argument("--g004-post-attempt-store-root", type=Path, default=None)
    parser.add_argument(
        "--current-baseline-sha",
        default="5f41d425c7f5b0b810d28cd3fc8b5af34113702c",
    )
    args = parser.parse_args(argv)
    if not any(
        [
            args.recon_dir,
            args.pre_external_report,
            args.final_order_envelope,
            args.governed_cycle_evidence_dir,
            args.g004_post_attempt_store_root,
        ]
    ):
        parser.error("At least one evidence source path is required.")
    return ExecutionOfflineObserverPathsV1(
        trade_id=str(args.trade_id).strip(),
        output_dir=args.output_dir,
        recon_dir=args.recon_dir,
        pre_external_report=args.pre_external_report,
        final_order_envelope=args.final_order_envelope,
        governed_cycle_evidence_dir=args.governed_cycle_evidence_dir,
        g004_post_attempt_store_root=args.g004_post_attempt_store_root,
        current_baseline_sha=str(args.current_baseline_sha).strip(),
    )


def main(argv: list[str] | None = None) -> int:
    try:
        paths = _parse_args(argv)
        if not paths.trade_id:
            raise SystemExit("MISSING_TRADE_ID")
        report = run_execution_bounded_offline_observer_v1(paths)
        print(
            json.dumps(
                {"report_path": report["report_path"], "status": report["observer_run_status"]}
            )
        )
        return 0 if report["observer_run_success"] else 2
    except OutputPathSafetyError as exc:
        print(json.dumps({"error": str(exc), "status": "OUTPUT_PATH_UNSAFE"}))
        return 2
    except BoundedInputError as exc:
        print(json.dumps({"error": str(exc), "status": "INPUT_BOUNDS_EXCEEDED"}))
        return 2
    except TimeoutError as exc:
        print(json.dumps({"error": str(exc), "status": "OBSERVER_TIMEOUT"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
