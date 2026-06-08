"""Offline builder: archive run bundles → workflow_pipeline_aggregate.v1."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .paths import safe_read_path
from .types import PIPELINE_READMODEL_ID, RunStageCardV1, WorkflowPipelineAggregateV1

CANONICAL_STAGES: tuple[tuple[str, str, str | None, str | None], ...] = (
    ("P1", "P1 Short Bounded Paper", "p1_short_bounded_paper_20260607T231152Z", None),
    ("P2", "P2 Longer Bounded Paper", "p2_longer_bounded_paper_20260607T233758Z", None),
    ("S1", "S1 Shadow No Orders", "s1_shadow_no_orders_20260608T001320Z", None),
    (
        "T1_ORIGINAL",
        "T1 Short Testnet (Original)",
        "t1_short_testnet_20260608T002732Z",
        "RECLASSIFIED_STAGING_ONLY",
    ),
    (
        "T1_REPAIR",
        "T1 Short Testnet 300s Observation Repair",
        "t1_short_testnet_300s_observation_repair_20260608T003535Z",
        None,
    ),
    ("T2", "T2 Medium Testnet Observation", "t2_medium_testnet_20260608T113545Z", None),
    ("T3", "T3 Longer Testnet (Planned)", None, None),
)

T3_PLANNED_VERDICT = "PLANNED_PARKED"


def _load_json(path: Path) -> tuple[dict | None, str | None]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None, "os_read_error"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, "json_decode_error"
    if not isinstance(data, dict):
        return None, "json_invalid_shape"
    return data, None


def _parse_machine_lines(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"')
    return out


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("true", "1", "yes")


def _parse_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_verdict_from_md(text: str) -> str | None:
    m = re.search(r"\*\*Verdict:\*\*\s*(\S+)", text)
    if m:
        return m.group(1).strip()
    return None


def _read_killswitch_summary(bundle_root: Path) -> str | None:
    path = bundle_root / "KILLSWITCH_RECOVERY_OBSERVATIONS.md"
    if not path.is_file():
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "|" in stripped:
            return stripped[:200]
    return "observations present" if lines else None


def _resolve_mode_label(stage_key: str, machine_lines: dict[str, str]) -> str | None:
    if stage_key == "T3":
        return "planned"
    if _parse_bool(machine_lines.get("PAPER_ONLY")):
        return "paper"
    if _parse_bool(machine_lines.get("SHADOW_ONLY")):
        return "shadow"
    if _parse_bool(machine_lines.get("TESTNET_ONLY")):
        return "testnet"
    if _parse_bool(machine_lines.get("STAGING_ONLY")):
        return "staging_only"
    return None


def _load_run_stage(
    stage_key: str,
    stage_label: str,
    bundle_basename: str | None,
    reclassification: str | None,
    runs_root: Path,
    errors: list[str],
) -> RunStageCardV1:
    if bundle_basename is None:
        return RunStageCardV1(
            stage_key=stage_key,
            stage_label=stage_label,
            bundle_basename=None,
            verdict=T3_PLANNED_VERDICT,
            reclassification=None,
            utc_start=None,
            utc_end=None,
            duration_actual_seconds=None,
            duration_cap_seconds=None,
            hard_stop_enforced=None,
            job_accepted=None,
            real_orders_executed=0,
            fills_count=None,
            manifest_verify_rc=None,
            post_run_review_status=None,
            closeout_status=None,
            operator=None,
            execute_go_token=None,
            mode_label="planned",
            heartbeat_count=None,
            evidence_status="planned",
            killswitch_summary=None,
        )

    bundle_root = runs_root / bundle_basename
    if not bundle_root.is_dir():
        errors.append(f"bundle_missing:{stage_key}")
        return RunStageCardV1(
            stage_key=stage_key,
            stage_label=stage_label,
            bundle_basename=bundle_basename,
            verdict="MISSING",
            reclassification=reclassification,
            utc_start=None,
            utc_end=None,
            duration_actual_seconds=None,
            duration_cap_seconds=None,
            hard_stop_enforced=None,
            job_accepted=None,
            real_orders_executed=0,
            fills_count=None,
            manifest_verify_rc=None,
            post_run_review_status=None,
            closeout_status=None,
            operator=None,
            execute_go_token=None,
            mode_label=None,
            heartbeat_count=None,
            evidence_status="missing",
            killswitch_summary=None,
        )

    meta_path = safe_read_path(bundle_root, "RUN_METADATA.json")
    run_meta: dict = {}
    if meta_path and meta_path.is_file():
        loaded, err = _load_json(meta_path)
        if err or loaded is None:
            errors.append(f"run_metadata_unreadable:{stage_key}")
        else:
            run_meta = loaded

    machine_lines = _parse_machine_lines(bundle_root / "machine_lines.env")

    verdict = (
        run_meta.get("review_verdict")
        or run_meta.get("verdict")
        or machine_lines.get(f"{stage_key.split('_')[0]}_SHORT_BOUNDED_PAPER_EXECUTE_VERDICT")
        or next(
            (v for k, v in machine_lines.items() if k.endswith("_VERDICT") and v),
            None,
        )
        or "UNKNOWN"
    )
    if isinstance(verdict, str):
        verdict = verdict.strip()
    else:
        verdict = str(verdict)

    post_run_status = None
    post_path = bundle_root / "POST_RUN_REVIEW.md"
    if post_path.is_file():
        try:
            post_run_status = _extract_verdict_from_md(post_path.read_text(encoding="utf-8"))
        except OSError:
            errors.append(f"post_run_unreadable:{stage_key}")

    closeout_status = None
    close_path = bundle_root / "CLOSEOUT.md"
    if close_path.is_file():
        try:
            closeout_status = _extract_verdict_from_md(close_path.read_text(encoding="utf-8"))
        except OSError:
            errors.append(f"closeout_unreadable:{stage_key}")

    adapter_rc = _parse_int(run_meta.get("adapter_rc"))
    go_provided = _parse_bool(machine_lines.get("OPERATOR_EXECUTE_GO_PROVIDED"))
    job_accepted: bool | None
    if adapter_rc is not None:
        job_accepted = go_provided and adapter_rc == 0
    elif go_provided:
        job_accepted = True
    else:
        job_accepted = None

    real_executed = _parse_int(machine_lines.get("REAL_ORDERS_EXECUTED"))
    if real_executed is None:
        real_executed = 0

    primary_captured = _parse_bool(machine_lines.get("PRIMARY_EVIDENCE_CAPTURED"))
    evidence_status = "captured" if primary_captured else "partial"

    duration_actual = run_meta.get("duration_seconds_actual") or run_meta.get("actual_duration_seconds")
    if duration_actual is not None:
        try:
            duration_actual = float(duration_actual)
        except (TypeError, ValueError):
            duration_actual = None

    return RunStageCardV1(
        stage_key=stage_key,
        stage_label=stage_label,
        bundle_basename=bundle_basename,
        verdict=verdict,
        reclassification=reclassification,
        utc_start=str(run_meta.get("utc_start") or run_meta.get("utc")) if run_meta.get("utc_start") or run_meta.get("utc") else None,
        utc_end=str(run_meta.get("utc_end")) if run_meta.get("utc_end") else None,
        duration_actual_seconds=duration_actual,
        duration_cap_seconds=_parse_int(
            run_meta.get("duration_cap_seconds") or machine_lines.get("RUN_DURATION_CAP_SECONDS")
        ),
        hard_stop_enforced=run_meta.get("hard_stop_enforced")
        if isinstance(run_meta.get("hard_stop_enforced"), bool)
        else _parse_bool(machine_lines.get("HARD_STOP_ENFORCED")),
        job_accepted=job_accepted,
        real_orders_executed=real_executed,
        fills_count=_parse_int(run_meta.get("fills_count") or machine_lines.get("FILLS_COUNT")),
        manifest_verify_rc=machine_lines.get("MANIFEST_VERIFY_RC")
        or machine_lines.get("PRIMARY_MANIFEST_VERIFY_RC"),
        post_run_review_status=post_run_status,
        closeout_status=closeout_status,
        operator=str(run_meta.get("operator")) if run_meta.get("operator") else None,
        execute_go_token=str(run_meta.get("go_token")) if run_meta.get("go_token") else None,
        mode_label=_resolve_mode_label(stage_key, machine_lines),
        heartbeat_count=_parse_int(run_meta.get("heartbeat_count")),
        evidence_status=evidence_status,
        killswitch_summary=_read_killswitch_summary(bundle_root),
    )


def build_workflow_pipeline_aggregate_v1(
    archive_root: Path,
) -> tuple[WorkflowPipelineAggregateV1, list[str]]:
    """Load canonical pipeline stages from archive_root/runs/."""

    root = archive_root.expanduser().resolve()
    runs_root = root / "runs"
    errors: list[str] = []

    if not runs_root.is_dir():
        errors.append("runs_directory_missing")
        runs_root = root

    stages: list[RunStageCardV1] = []
    for stage_key, stage_label, bundle_basename, reclass in CANONICAL_STAGES:
        stages.append(
            _load_run_stage(stage_key, stage_label, bundle_basename, reclass, runs_root, errors)
        )

    aggregate = WorkflowPipelineAggregateV1(
        readmodel_id=PIPELINE_READMODEL_ID,
        stage_count=len(stages),
        stages=tuple(stages),
    )
    return aggregate, errors
