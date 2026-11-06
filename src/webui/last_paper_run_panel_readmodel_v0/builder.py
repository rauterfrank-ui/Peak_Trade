"""Offline-Builder: durable Paper-Run-Bundle → display-only Last Paper Run panel readmodel."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from .paths import path_is_under_root, safe_read_path
from .types import (
    READMODEL_ID,
    SCHEMA_VERSION,
    EvidenceBlockV0,
    InstrumentBlockV0,
    LastPaperRunPanelReadModelV0,
    LastRunBlockV0,
    NextTokenBlockV0,
    OrdersFillsBlockV0,
    SafetyBlockV0,
)

_FIXED_GEN_ENV = "PEAK_TRADE_FIXED_GENERATED_AT_UTC"

_INSTRUMENT_KEYS = (
    "selected_instrument",
    "selected_future",
    "selected_symbol",
    "instrument_id",
    "future_instrument",
)


def _now_iso() -> str:
    fixed = os.environ.get(_FIXED_GEN_ENV)
    if fixed:
        return fixed
    return datetime.now(tz=timezone.utc).isoformat()


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


def _extract_job_name_from_config_snapshot(text: str) -> str | None:
    m = re.search(r"\|\s*Job name\s*\|\s*([^\|\n]+?)\s*\|", text)
    if m:
        return m.group(1).strip()
    return None


def _extract_runtime_fixture_from_config_snapshot(text: str) -> str | None:
    m = re.search(r'spec\s*=\s*"([^"]+paper_run[^"]+\.json)"', text)
    if m:
        return m.group(1).strip()
    return None


def _extract_verdict_from_md(text: str) -> str | None:
    m = re.search(r"\*\*Verdict:\*\*\s*(\S+)", text)
    if m:
        return m.group(1).strip()
    return None


def _parse_bool_env(value: str | None, *, default: bool = False) -> bool:
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


def _basename_only(path_value: object) -> str | None:
    if path_value is None:
        return None
    text = str(path_value).strip()
    if not text:
        return None
    return Path(text).name


def _first_instrument_from_dict(
    data: dict,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Return (instrument, future, symbol, source_field) from explicit keys only."""
    for key in _INSTRUMENT_KEYS:
        val = data.get(key)
        if val is not None and str(val).strip():
            text = str(val).strip()
            if key in ("selected_instrument", "instrument_id"):
                return text, None, None, key
            if key in ("selected_future", "future_instrument"):
                return None, text, None, key
            if key == "selected_symbol":
                return None, None, text, key
    return None, None, None, None


def _resolve_instrument_block(
    run_meta: dict,
    adapter_meta: dict | None,
    runtime_fixture_ref: str | None,
) -> InstrumentBlockV0:
    inst, fut, sym, field = _first_instrument_from_dict(run_meta)
    source_file = "RUN_METADATA.json" if field else None
    if field is None and adapter_meta:
        inst, fut, sym, field = _first_instrument_from_dict(adapter_meta)
        if field:
            source_file = "adapter_primary_evidence/RUN_METADATA.json"

    if field:
        return InstrumentBlockV0(
            instrument_truth_status="PERSISTED",
            selected_instrument=inst,
            selected_future=fut,
            selected_symbol=sym,
            runtime_fixture_ref=runtime_fixture_ref,
            source_of_truth_file=source_file,
            source_of_truth_field=field,
        )

    return InstrumentBlockV0(
        instrument_truth_status="NOT_PERSISTED",
        selected_instrument=None,
        selected_future=None,
        selected_symbol=None,
        runtime_fixture_ref=runtime_fixture_ref,
        source_of_truth_file=None,
        source_of_truth_field=None,
    )


def _count_paper_orders(fills_path: Path | None) -> int | None:
    if fills_path is None or not fills_path.is_file():
        return None
    data, err = _load_json(fills_path)
    if err or data is None:
        return None
    fills = data.get("fills")
    if isinstance(fills, list):
        return len(fills)
    return None


def build_last_paper_run_panel_readmodel_v0(bundle_root: Path) -> LastPaperRunPanelReadModelV0:
    """Materialize display-only panel readmodel from a durable run bundle directory."""

    root = bundle_root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError("bundle_root_not_directory")

    errors: list[str] = []
    load_status = "ready"

    run_meta_path = safe_read_path(root, "RUN_METADATA.json")
    if run_meta_path is None or not run_meta_path.is_file():
        raise ValueError("run_metadata_missing")

    run_meta, run_err = _load_json(run_meta_path)
    if run_err or run_meta is None:
        raise ValueError("run_metadata_unreadable")

    machine_lines = _parse_machine_lines(root / "machine_lines.env")

    config_snapshot_text = ""
    config_path = root / "CONFIG_SNAPSHOT.md"
    if config_path.is_file():
        try:
            config_snapshot_text = config_path.read_text(encoding="utf-8")
        except OSError:
            errors.append("config_snapshot_unreadable")

    job_name = _extract_job_name_from_config_snapshot(config_snapshot_text) or "UNKNOWN"
    runtime_fixture_ref = _extract_runtime_fixture_from_config_snapshot(config_snapshot_text)

    post_run_status = None
    post_path = root / "POST_RUN_REVIEW.md"
    if post_path.is_file():
        try:
            post_run_status = _extract_verdict_from_md(post_path.read_text(encoding="utf-8"))
        except OSError:
            errors.append("post_run_review_unreadable")

    closeout_status = None
    close_path = root / "CLOSEOUT.md"
    if close_path.is_file():
        try:
            closeout_status = _extract_verdict_from_md(close_path.read_text(encoding="utf-8"))
        except OSError:
            errors.append("closeout_unreadable")

    adapter_meta: dict | None = None
    adapter_path = safe_read_path(root, "adapter_primary_evidence/RUN_METADATA.json")
    if adapter_path and adapter_path.is_file():
        adapter_meta, adapter_err = _load_json(adapter_path)
        if adapter_err:
            errors.append("adapter_run_metadata_unreadable")
            adapter_meta = None

    fills_path = safe_read_path(root, "adapter_primary_evidence/runtime_out/fills.json")
    paper_orders_count = _count_paper_orders(fills_path)

    run_id = ""
    if adapter_meta and adapter_meta.get("run_id"):
        run_id = str(adapter_meta["run_id"])
    elif run_meta.get("run_id"):
        run_id = str(run_meta["run_id"])
    else:
        run_id = "UNKNOWN"
        errors.append("run_id_missing")

    adapter_rc = _parse_int(run_meta.get("adapter_rc"))
    if adapter_rc is None and adapter_meta:
        adapter_rc = _parse_int(adapter_meta.get("adapter_rc"))

    go_provided = _parse_bool_env(machine_lines.get("OPERATOR_EXECUTE_GO_PROVIDED"))
    job_accepted: bool | None
    if adapter_rc is not None:
        job_accepted = go_provided and adapter_rc == 0
    elif go_provided:
        job_accepted = True
    else:
        job_accepted = None

    stage = str(run_meta.get("stage") or machine_lines.get("P1_STAGE") or "UNKNOWN")
    mode = "paper" if _parse_bool_env(machine_lines.get("PAPER_ONLY"), default=True) else "unknown"
    status = str(
        run_meta.get("review_verdict")
        or machine_lines.get("P1_SHORT_BOUNDED_PAPER_EXECUTE_VERDICT")
        or "UNKNOWN"
    )

    instrument = _resolve_instrument_block(run_meta, adapter_meta, runtime_fixture_ref)

    max_real = _parse_int(machine_lines.get("MAX_REAL_ORDERS"))
    if max_real is None:
        max_real = 0
    real_executed = _parse_int(machine_lines.get("REAL_ORDERS_EXECUTED"))
    if real_executed is None:
        real_executed = 0
    fills_count = _parse_int(run_meta.get("fills_count"))
    live_orders = _parse_int(machine_lines.get("LIVE_ORDERS_EXECUTED"))

    manifest_rc = machine_lines.get("MANIFEST_VERIFY_RC") or str(
        run_meta.get("manifest_verify_rc") or ""
    )

    last_run = LastRunBlockV0(
        run_id=run_id,
        job_name=job_name,
        stage=stage,
        mode=mode,
        status=status,
        job_accepted=job_accepted,
        duration_actual_seconds=_parse_int(run_meta.get("duration_seconds_actual")),
        duration_cap_seconds=_parse_int(
            run_meta.get("duration_cap_seconds") or machine_lines.get("RUN_DURATION_CAP_SECONDS")
        ),
        hard_stop_enforced=run_meta.get("hard_stop_enforced")
        if isinstance(run_meta.get("hard_stop_enforced"), bool)
        else _parse_bool_env(machine_lines.get("HARD_STOP_ENFORCED")),
        utc_start=str(run_meta.get("utc_start")) if run_meta.get("utc_start") else None,
        utc_end=str(run_meta.get("utc_end")) if run_meta.get("utc_end") else None,
        adapter_rc=adapter_rc,
        operator=str(run_meta.get("operator")) if run_meta.get("operator") else None,
        execute_go_token=str(run_meta.get("go_token")) if run_meta.get("go_token") else None,
        repo_head=str(run_meta.get("head")) if run_meta.get("head") else None,
    )

    orders_fills = OrdersFillsBlockV0(
        max_real_orders=max_real,
        real_orders_executed=real_executed,
        live_orders_executed=live_orders,
        fills_count=fills_count,
        paper_orders_count=paper_orders_count,
    )

    evidence = EvidenceBlockV0(
        durable_evidence_root_basename=root.name,
        primary_evidence_captured=_parse_bool_env(machine_lines.get("PRIMARY_EVIDENCE_CAPTURED")),
        manifest_verify_rc=manifest_rc or None,
        post_run_review_status=post_run_status,
        closeout_status=closeout_status,
        adapter_primary_evidence_basename="adapter_primary_evidence",
        paper_archive_basename=_basename_only(run_meta.get("paper_archive")),
    )

    safety = SafetyBlockV0(
        LIVE_AUTHORIZED=_parse_bool_env(machine_lines.get("LIVE_AUTHORIZED")),
        READY_FOR_OPERATOR_ARMING=_parse_bool_env(machine_lines.get("READY_FOR_OPERATOR_ARMING")),
        PREFLIGHT_LIFT=_parse_bool_env(machine_lines.get("PREFLIGHT_LIFT_AUTHORIZED")),
        GAP7=_parse_bool_env(machine_lines.get("GAP7_RISK_BOUNDARY_VERIFIED")),
        evidence_not_approval=True,
    )

    next_token = machine_lines.get("SELECTED_NEXT_GO_TOKEN")
    next_token_block = NextTokenBlockV0(
        selected_next_go_token=next_token,
        next_stage_requires_operator_go=bool(next_token and "GO_REQUIRED" in next_token),
        next_stage_label="P2 longer bounded paper" if "P2" in (next_token or "") else None,
    )

    if errors:
        load_status = "ready_with_warnings"

    return LastPaperRunPanelReadModelV0(
        schema_version=SCHEMA_VERSION,
        readmodel_id=READMODEL_ID,
        generated_at_utc=_now_iso(),
        source_kind="durable_run_bundle",
        source_label=root.name,
        stale=True,
        stale_reason="archive_snapshot",
        non_authorizing=True,
        load_status=load_status,
        load_errors=tuple(errors),
        last_run=last_run,
        instrument=instrument,
        orders_fills=orders_fills,
        evidence=evidence,
        safety=safety,
        next_token=next_token_block,
    )
