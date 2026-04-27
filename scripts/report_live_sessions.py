#!/usr/bin/env python3
"""
Peak_Trade: Live Session Registry Report CLI (Phase 81)
========================================================

Command-Line-Interface zum Generieren von Reports aus der Live-Session-Registry.

Dieses Tool liest Session-Records aus der Registry und erzeugt Markdown-
und/oder HTML-Reports.

Usage:
    # Alle Sessions als Markdown-Report:
    python scripts/report_live_sessions.py

    # Nur Shadow-Sessions:
    python scripts/report_live_sessions.py --run-type live_session_shadow

    # Nur abgeschlossene Sessions:
    python scripts/report_live_sessions.py --status completed

    # Limit auf letzte 10 Sessions:
    python scripts/report_live_sessions.py --limit 10

    # HTML-Report generieren:
    python scripts/report_live_sessions.py --output-format html

    # Beide Formate:
    python scripts/report_live_sessions.py --output-format both

    # Nur Summary (keine Einzel-Reports):
    python scripts/report_live_sessions.py --summary-only

    # Report nach stdout:
    python scripts/report_live_sessions.py --stdout

    # Report in spezifisches Verzeichnis:
    python scripts/report_live_sessions.py --output-dir reports/custom/

    # Read-only Evidence-Pointer (Registry + session-scoped execution_events.jsonl):
    python scripts/report_live_sessions.py --evidence-pointers --session-id <id>
    python scripts/report_live_sessions.py --evidence-pointers --latest-bounded-pilot --json

    # Read-only open sessions (registry status=started; per-artifact paths):
    python scripts/report_live_sessions.py --open-sessions
    python scripts/report_live_sessions.py --open-sessions --bounded-pilot-only --json
    python scripts/report_live_sessions.py --open-sessions --latest-bounded-pilot-open

    # Bounded-pilot readiness + preflight packet + registry focus (read-only snapshot):
    python scripts/report_live_sessions.py --bounded-pilot-readiness-summary
    python scripts/report_live_sessions.py --bounded-pilot-readiness-summary --json

    # Bounded-pilot closeout / final registry status + pointers (read-only; no readiness run;
    # JSON includes abort_triage_hints derived via same lifecycle consistency rules — not authorization):
    python scripts/report_live_sessions.py --bounded-pilot-closeout-status-summary
    python scripts/report_live_sessions.py --bounded-pilot-closeout-status-summary --json

    # Bounded-pilot operator overview (read-only: readiness + packet + session focus + closeout):
    python scripts/report_live_sessions.py --bounded-pilot-operator-overview
    python scripts/report_live_sessions.py --bounded-pilot-operator-overview --json

    # Bounded-pilot gate / enablement index (read-only; overview data + compact index block):
    python scripts/report_live_sessions.py --bounded-pilot-gate-index
    python scripts/report_live_sessions.py --bounded-pilot-gate-index --json

    # Bounded-pilot / first-live frontdoor (read-only; overview + gate index + canonical CLI hints):
    python scripts/report_live_sessions.py --bounded-pilot-first-live-frontdoor
    python scripts/report_live_sessions.py --bounded-pilot-first-live-frontdoor --json

    # Bounded-pilot lifecycle / handoff consistency (read-only; registry + pointers + closeout signals;
    # JSON includes abort_triage_hints derived from existing signals only — not authorization):
    python scripts/report_live_sessions.py --bounded-pilot-lifecycle-consistency
    python scripts/report_live_sessions.py --bounded-pilot-lifecycle-consistency --json

    # Session Review Pack V0 (read-only, non-authorizing post-hoc review bundle; JSON-only in v0):
    python scripts/report_live_sessions.py --session-review-pack --json

    # Pre-Live Package Status V0 (read-only gap signal; stdout JSON-only; registry + bounded-pilot artifacts):
    python scripts/report_live_sessions.py --pre-live-package-status --json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Projekt-Root zum Path hinzufuegen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Logging Setup
# =============================================================================


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Konfiguriert Logging fuer CLI."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    return logging.getLogger("report_live_sessions")


# =============================================================================
# Summary Formatter
# =============================================================================


def format_summary_markdown(summary: dict) -> str:
    """Formatiert Summary als Markdown-String."""
    lines = [
        "# Live-Session Registry Summary",
        "",
        f"**Anzahl Sessions:** {summary.get('num_sessions', 0)}",
        "",
    ]

    # Status-Breakdown
    by_status = summary.get("by_status", {})
    if by_status:
        lines.append("## Sessions nach Status")
        lines.append("")
        for status, count in sorted(by_status.items()):
            lines.append(f"- **{status}:** {count}")
        lines.append("")

    # Metrics
    total_pnl = summary.get("total_realized_pnl")
    avg_dd = summary.get("avg_max_drawdown")

    if total_pnl is not None or avg_dd is not None:
        lines.append("## Aggregierte Metriken")
        lines.append("")
        if total_pnl is not None:
            lines.append(f"- **Total Realized PnL:** {total_pnl:.2f}")
        if avg_dd is not None:
            lines.append(f"- **Avg Max Drawdown:** {avg_dd:.4f}")
        lines.append("")

    # Zeitraum
    first_started = summary.get("first_started_at")
    last_started = summary.get("last_started_at")

    if first_started or last_started:
        lines.append("## Zeitraum")
        lines.append("")
        if first_started:
            lines.append(f"- **Erste Session:** {first_started}")
        if last_started:
            lines.append(f"- **Letzte Session:** {last_started}")
        lines.append("")

    return "\n".join(lines)


def format_summary_html(summary: dict) -> str:
    """Formatiert Summary als HTML-String."""
    num_sessions = summary.get("num_sessions", 0)
    by_status = summary.get("by_status", {})
    total_pnl = summary.get("total_realized_pnl")
    avg_dd = summary.get("avg_max_drawdown")
    first_started = summary.get("first_started_at")
    last_started = summary.get("last_started_at")

    status_rows = ""
    for status, count in sorted(by_status.items()):
        status_rows += f"<tr><td>{status}</td><td>{count}</td></tr>\n"

    metrics_section = ""
    if total_pnl is not None or avg_dd is not None:
        metrics_section = "<h2>Aggregierte Metriken</h2><ul>"
        if total_pnl is not None:
            metrics_section += f"<li><strong>Total Realized PnL:</strong> {total_pnl:.2f}</li>"
        if avg_dd is not None:
            metrics_section += f"<li><strong>Avg Max Drawdown:</strong> {avg_dd:.4f}</li>"
        metrics_section += "</ul>"

    time_section = ""
    if first_started or last_started:
        time_section = "<h2>Zeitraum</h2><ul>"
        if first_started:
            time_section += f"<li><strong>Erste Session:</strong> {first_started}</li>"
        if last_started:
            time_section += f"<li><strong>Letzte Session:</strong> {last_started}</li>"
        time_section += "</ul>"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Live-Session Registry Summary</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; margin-top: 20px; }}
        table {{ border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
        ul {{ list-style-type: none; padding-left: 0; }}
        li {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <h1>Live-Session Registry Summary</h1>
    <p><strong>Anzahl Sessions:</strong> {num_sessions}</p>

    <h2>Sessions nach Status</h2>
    <table>
        <tr><th>Status</th><th>Anzahl</th></tr>
        {status_rows}
    </table>

    {metrics_section}
    {time_section}
</body>
</html>"""
    return html


# =============================================================================
# Evidence pointers (read-only, post-session reconstruction)
# =============================================================================


def _run_evidence_pointers(args: argparse.Namespace, logger: logging.Logger) -> int:
    """
    Print canonical artifact paths for a session. Read-only; never writes under out/.

    Returns:
        0 on success (including missing execution_events JSONL),
        1 if session not found,
        2 on usage errors (handled before this call).
    """
    from src.experiments.live_session_registry import (
        DEFAULT_LIVE_SESSION_DIR,
        find_live_session_registry_json_for_session_id,
        list_session_records,
    )
    from src.observability.execution_events import expected_session_scoped_events_jsonl_path

    base_dir = Path(args.registry_base) if args.registry_base else DEFAULT_LIVE_SESSION_DIR
    cwd = Path.cwd()

    if args.session_id:
        sid = args.session_id.strip()
        resolved = find_live_session_registry_json_for_session_id(sid, base_dir=base_dir)
        if resolved is None:
            print(
                f"ERR: no live session registry entry for session_id={sid!r} "
                f"(registry_dir={base_dir!s})",
                file=sys.stderr,
            )
            return 1
        record, registry_path = resolved
    else:
        records = list_session_records(base_dir=base_dir)
        record = next((r for r in records if r.mode == "bounded_pilot"), None)
        if record is None:
            print(
                "ERR: no live session registry entry with mode=bounded_pilot "
                f"(registry_dir={base_dir!s})",
                file=sys.stderr,
            )
            return 1
        resolved = find_live_session_registry_json_for_session_id(
            record.session_id,
            base_dir=base_dir,
        )
        if resolved is None:
            print(
                f"ERR: registry entry disappeared for session_id={record.session_id!r}",
                file=sys.stderr,
            )
            return 1
        _, registry_path = resolved

    rel_exec = expected_session_scoped_events_jsonl_path(record.session_id)
    abs_registry = registry_path.resolve()
    abs_exec = (cwd / rel_exec).resolve()
    exec_present = abs_exec.is_file()

    payload = {
        "contract": "report_live_sessions.evidence_pointers",
        "session_id": record.session_id,
        "run_id": record.run_id,
        "mode": record.mode,
        "run_type": record.run_type,
        "status": record.status,
        "registry_json": {
            "path": str(registry_path),
            "resolved": str(abs_registry),
            "exists": abs_registry.is_file(),
        },
        "execution_events_session_jsonl": {
            "path": str(rel_exec),
            "resolved": str(abs_exec),
            "present": exec_present,
        },
    }

    logger.info("Evidence pointers (read-only) for session_id=%s", record.session_id)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    lines = [
        "Evidence pointers (read-only)",
        f"  session_id: {record.session_id}",
        f"  run_id: {record.run_id}",
        f"  mode: {record.mode}",
        f"  run_type: {record.run_type}",
        f"  status: {record.status}",
        f"  registry_json: {abs_registry} (exists: {payload['registry_json']['exists']})",
        f"  execution_events_jsonl (session-scoped): {abs_exec}",
        f"    present: {'yes' if exec_present else 'no'}",
    ]
    print("\n".join(lines))
    return 0


# =============================================================================
# Open sessions (read-only, registry status=started)
# =============================================================================


def _open_session_payload_row(record: Any, registry_path: Path, cwd: Path) -> dict[str, Any]:
    """Build one JSON-serializable row; read-only path resolution only."""
    from src.observability.execution_events import expected_session_scoped_events_jsonl_path

    rel_exec = expected_session_scoped_events_jsonl_path(record.session_id)
    abs_registry = registry_path.resolve()
    abs_exec = (cwd / rel_exec).resolve()
    exec_present = abs_exec.is_file()
    closeout_note = None
    if record.status == "started":
        closeout_note = (
            "Registry artifact has non-terminal status=started only; "
            "no completed/failed/aborted in this file. "
            "Does not prove the process is still running."
        )
    return {
        "session_id": record.session_id,
        "registry_status": record.status,
        "operator_lifecycle": "OPEN",
        "mode": record.mode,
        "run_type": record.run_type,
        "run_id": record.run_id,
        "started_at": record.started_at.isoformat() if record.started_at else None,
        "finished_at": record.finished_at.isoformat() if record.finished_at else None,
        "closeout_note": closeout_note,
        "registry_json": {
            "path": str(registry_path),
            "resolved": str(abs_registry),
            "exists": abs_registry.is_file(),
        },
        "execution_events_session_jsonl": {
            "path": str(rel_exec),
            "resolved": str(abs_exec),
            "present": exec_present,
        },
    }


def _run_open_sessions(args: argparse.Namespace, logger: logging.Logger) -> int:
    """
    List registry artifacts with status=started (operator: OPEN). Read-only.

    Returns:
        0 always (including empty list); usage errors return 2 from main().
    """
    from src.experiments.live_session_registry import (
        DEFAULT_LIVE_SESSION_DIR,
        STATUS_STARTED,
        iter_live_session_registry_entries,
    )

    base_dir = Path(args.registry_base) if args.registry_base else DEFAULT_LIVE_SESSION_DIR
    cwd = Path.cwd()

    rows_raw = [
        (r, p)
        for r, p in iter_live_session_registry_entries(base_dir=base_dir)
        if r.status == STATUS_STARTED
    ]

    if args.bounded_pilot_only or args.latest_bounded_pilot_open:
        rows_raw = [(r, p) for r, p in rows_raw if r.mode == "bounded_pilot"]

    if args.latest_bounded_pilot_open:
        rows_raw.sort(
            key=lambda t: t[0].started_at or datetime(1970, 1, 1),
            reverse=True,
        )
        rows_raw = rows_raw[:1]

    sessions = [_open_session_payload_row(r, p, cwd) for r, p in rows_raw]
    payload: dict[str, Any] = {
        "contract": "report_live_sessions.open_sessions",
        "registry_dir": str(base_dir),
        "count": len(sessions),
        "sessions": sessions,
    }

    logger.info("Open sessions (read-only) count=%s", len(sessions))

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if not sessions:
        print(
            "Open sessions (read-only): none "
            "(no registry rows with status=started for the selected filters)."
        )
        return 0

    lines = ["Open sessions (read-only)"]
    for item in sessions:
        lines.append(f"  session_id: {item['session_id']}")
        lines.append(
            f"    operator_lifecycle: {item['operator_lifecycle']} (registry_status={item['registry_status']})"
        )
        lines.append(
            f"    mode: {item['mode']}  run_type: {item['run_type']}  run_id: {item['run_id']}"
        )
        if item.get("closeout_note"):
            lines.append(f"    note: {item['closeout_note']}")
        lines.append(f"    registry_json: {item['registry_json']['resolved']}")
        ej = item["execution_events_session_jsonl"]
        lines.append(
            f"    execution_events_jsonl: {ej['resolved']}  present: {'yes' if ej['present'] else 'no'}"
        )
    print("\n".join(lines))
    return 0


# =============================================================================
# Bounded-pilot readiness + packet + session focus (read-only snapshot)
# =============================================================================


def _registry_base_dir(args: argparse.Namespace) -> Path:
    from src.experiments.live_session_registry import DEFAULT_LIVE_SESSION_DIR

    return Path(args.registry_base) if args.registry_base else DEFAULT_LIVE_SESSION_DIR


def _pointers_for_session_id(
    session_id: str,
    *,
    base_dir: Path,
    cwd: Path,
) -> dict[str, Any] | None:
    """Registry + execution_events paths for one session_id (read-only)."""
    from src.experiments.live_session_registry import find_live_session_registry_json_for_session_id

    resolved = find_live_session_registry_json_for_session_id(session_id, base_dir=base_dir)
    if resolved is None:
        return None
    record, path = resolved
    row = _open_session_payload_row(record, path, cwd)
    return {
        "session_id": session_id,
        "registry_json": row["registry_json"],
        "execution_events_session_jsonl": row["execution_events_session_jsonl"],
    }


def _collect_bounded_pilot_session_focus(
    *,
    base_dir: Path,
    cwd: Path,
) -> dict[str, Any]:
    """Reuse open-sessions + latest-registry logic; no writes."""
    from src.experiments.live_session_registry import (
        STATUS_STARTED,
        iter_live_session_registry_entries,
        list_session_records,
    )

    open_rows = [
        (r, p)
        for r, p in iter_live_session_registry_entries(base_dir=base_dir)
        if r.status == STATUS_STARTED and r.mode == "bounded_pilot"
    ]
    open_rows.sort(
        key=lambda t: t[0].started_at or datetime(1970, 1, 1),
        reverse=True,
    )
    open_payloads = [_open_session_payload_row(r, p, cwd) for r, p in open_rows]

    records = list_session_records(base_dir=base_dir)
    latest_rec = next((r for r in records if r.mode == "bounded_pilot"), None)
    latest_compact: dict[str, Any] | None = None
    if latest_rec is not None:
        latest_compact = {
            "session_id": latest_rec.session_id,
            "registry_status": latest_rec.status,
            "run_id": latest_rec.run_id,
            "started_at": latest_rec.started_at.isoformat() if latest_rec.started_at else None,
            "finished_at": latest_rec.finished_at.isoformat() if latest_rec.finished_at else None,
        }

    primary_source = "none"
    primary_session_id: str | None = None
    if open_payloads:
        primary_source = "open_bounded_pilot"
        primary_session_id = open_payloads[0]["session_id"]
    elif latest_rec is not None:
        primary_source = "latest_bounded_pilot_registry"
        primary_session_id = latest_rec.session_id

    pointers = None
    if primary_session_id is not None:
        pointers = _pointers_for_session_id(
            primary_session_id,
            base_dir=base_dir,
            cwd=cwd,
        )

    return {
        "primary_session_id": primary_session_id,
        "primary_source": primary_source,
        "open_bounded_pilot_sessions": [
            {"session_id": x["session_id"], "registry_status": x["registry_status"]}
            for x in open_payloads
        ],
        "open_bounded_pilot_detail": open_payloads,
        "latest_bounded_pilot_registry": latest_compact,
        "pointers": pointers,
    }


def _build_bounded_pilot_closeout_analysis(
    session_focus: dict[str, Any],
    *,
    base_dir: Path,
    cwd: Path,
) -> dict[str, Any]:
    """
    Read-only closeout / final-status view from registry artifacts + pointers.

    Uses the newest registry JSON per session_id (filename order) as authoritative for
    terminal vs non-terminal; scans all bounded_pilot rows for the same session_id to
    detect started-vs-terminal conflicts across artifacts.
    """
    from src.experiments.live_session_registry import (
        STATUS_COMPLETED,
        STATUS_FAILED,
        STATUS_ABORTED,
        STATUS_STARTED,
        iter_live_session_registry_entries,
    )

    terminal = {STATUS_COMPLETED, STATUS_FAILED, STATUS_ABORTED}
    sid = session_focus.get("primary_session_id")
    primary_source = session_focus.get("primary_source")

    if sid is None:
        return {
            "primary_session_id": None,
            "primary_source": primary_source,
            "registry_bounded_pilot_artifacts_for_session": [],
            "newest_registry_status": None,
            "statuses_seen_across_artifacts": [],
            "closeout_signal_summary": "NO_BOUNDED_PILOT_SESSION_IN_REGISTRY",
            "registry_terminal_in_newest_artifact": False,
            "any_terminal_artifact_exists": False,
            "open_vs_terminal_artifact_conflict": False,
            "execution_events_jsonl_present": False,
            "pointers": None,
            "operator_notes": [
                "No bounded_pilot session_id resolved from registry (empty or no matching rows).",
            ],
        }

    matches = [
        (r, p)
        for r, p in iter_live_session_registry_entries(base_dir=base_dir)
        if r.session_id == sid and r.mode == "bounded_pilot"
    ]
    matches.sort(key=lambda t: t[1].name, reverse=True)

    if not matches:
        return {
            "primary_session_id": sid,
            "primary_source": primary_source,
            "registry_bounded_pilot_artifacts_for_session": [],
            "newest_registry_status": None,
            "statuses_seen_across_artifacts": [],
            "closeout_signal_summary": "REGISTRY_ROWS_MISSING_AFTER_SELECTION",
            "registry_terminal_in_newest_artifact": False,
            "any_terminal_artifact_exists": False,
            "open_vs_terminal_artifact_conflict": False,
            "execution_events_jsonl_present": False,
            "pointers": _pointers_for_session_id(sid, base_dir=base_dir, cwd=cwd),
            "operator_notes": [
                "primary_session_id was resolved but no bounded_pilot registry rows "
                "matched during scan; registry may have changed since selection.",
            ],
        }

    artifacts_min = [
        {
            "registry_status": r.status,
            "path": str(p),
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        }
        for r, p in matches
    ]

    any_terminal = any(r.status in terminal for r, _ in matches)
    newest = matches[0] if matches else None
    newest_status = newest[0].status if newest else None
    newest_terminal = bool(newest and newest[0].status in terminal)
    conflict = bool(newest and newest[0].status == STATUS_STARTED and any_terminal)

    pointers = _pointers_for_session_id(sid, base_dir=base_dir, cwd=cwd)
    exec_present = (
        bool(pointers["execution_events_session_jsonl"]["present"]) if pointers else False
    )

    if newest_terminal:
        summary_code = "REGISTRY_TERMINAL_IN_NEWEST_ARTIFACT"
    elif conflict:
        summary_code = "AMBIGUOUS_NEWEST_STARTED_WITH_OLDER_TERMINAL"
    elif newest_status == STATUS_STARTED:
        summary_code = "REGISTRY_NON_TERMINAL_NEWEST_ONLY"
    else:
        summary_code = "REGISTRY_STATUS_NON_STANDARD"

    notes: list[str] = []
    if conflict:
        notes.append(
            "Newest registry artifact has status=started but an older terminal "
            "(completed/failed/aborted) artifact exists for the same session_id; "
            "inspect every registry JSON path listed below."
        )
    if newest_status == STATUS_STARTED and not conflict:
        notes.append(
            "Newest registry artifact is non-terminal (started only in newest file); "
            "no completed/failed/aborted there — does not prove a process is still running."
        )
    if newest_terminal:
        notes.append(
            "Newest registry artifact has a terminal status; registry-only signal "
            "(not a handoff-success or business-outcome verdict)."
        )

    statuses_seen = sorted({r.status for r, _ in matches})

    return {
        "primary_session_id": sid,
        "primary_source": primary_source,
        "registry_bounded_pilot_artifacts_for_session": artifacts_min,
        "newest_registry_status": newest_status,
        "statuses_seen_across_artifacts": statuses_seen,
        "closeout_signal_summary": summary_code,
        "registry_terminal_in_newest_artifact": newest_terminal,
        "any_terminal_artifact_exists": any_terminal,
        "open_vs_terminal_artifact_conflict": conflict,
        "execution_events_jsonl_present": exec_present,
        "pointers": pointers,
        "operator_notes": notes,
    }


def _collect_bounded_pilot_readiness_and_packet(
    *,
    repo_root: Path,
    config_path: Path,
    logger: logging.Logger,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Shared read-only readiness + operator preflight packet blocks (no registry I/O)."""
    from scripts.ops.bounded_pilot_operator_preflight_packet import build_operator_preflight_packet
    from scripts.ops.check_bounded_pilot_readiness import run_bounded_pilot_readiness

    ok, bundle = run_bounded_pilot_readiness(repo_root, config_path, run_tests=False)
    readiness_block: dict[str, Any] = {
        "evaluated": True,
        "ok": ok,
        "blocked_at": bundle.get("blocked_at"),
        "message": bundle.get("message"),
        "go_no_go": bundle.get("go_no_go"),
        "live_readiness": bundle.get("live_readiness"),
    }

    try:
        packet, packet_code = build_operator_preflight_packet(
            repo_root,
            config_path,
            run_tests=False,
        )
        summary = (packet or {}).get("summary") or {}
        blocked_list = list(summary.get("blocked") or [])
        packet_out: dict[str, Any] = {
            "evaluated": True,
            "packet_code": packet_code,
            "packet_ok": bool(summary.get("packet_ok")),
            "blocked_lines_preview": blocked_list[:12],
            "blocked_lines_total": len(blocked_list),
        }
    except Exception as e:
        logger.warning("operator preflight packet build failed: %s", e)
        packet_out = {
            "evaluated": False,
            "packet_code": 2,
            "error": f"{type(e).__name__}: {e}",
        }

    return readiness_block, packet_out


def _collect_bounded_pilot_overview_data(
    args: argparse.Namespace,
    logger: logging.Logger,
) -> tuple[Path, Path, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Shared blocks for operator overview and gate-index read-models (read-only)."""
    from scripts.ops.check_bounded_pilot_readiness import resolve_bounded_pilot_config_path

    repo_root = PROJECT_ROOT
    explicit_cfg = Path(args.config_path) if getattr(args, "config_path", None) else None
    config_path = resolve_bounded_pilot_config_path(repo_root, explicit_cfg)
    base_dir = _registry_base_dir(args)
    cwd = Path.cwd()

    readiness_block, packet_out = _collect_bounded_pilot_readiness_and_packet(
        repo_root=repo_root,
        config_path=config_path,
        logger=logger,
    )
    session_focus = _collect_bounded_pilot_session_focus(base_dir=base_dir, cwd=cwd)
    closeout = _build_bounded_pilot_closeout_analysis(
        session_focus,
        base_dir=base_dir,
        cwd=cwd,
    )
    return config_path, base_dir, readiness_block, packet_out, session_focus, closeout


def _canonical_bounded_pilot_read_only_subcommands() -> dict[str, str]:
    """Stable operator hints for existing read-only report_live_sessions modes (no execution)."""
    return {
        "evidence_pointers_session": (
            "python scripts/report_live_sessions.py --evidence-pointers "
            "--session-id <SESSION_ID> [--json]"
        ),
        "evidence_pointers_latest_bounded_pilot": (
            "python scripts/report_live_sessions.py --evidence-pointers "
            "--latest-bounded-pilot [--json]"
        ),
        "open_sessions": (
            "python scripts/report_live_sessions.py --open-sessions "
            "[--bounded-pilot-only] [--latest-bounded-pilot-open] [--json]"
        ),
        "readiness_summary": (
            "python scripts/report_live_sessions.py --bounded-pilot-readiness-summary "
            "[--json] [--config-path <path>] [--registry-base <dir>]"
        ),
        "closeout_status_summary": (
            "python scripts/report_live_sessions.py --bounded-pilot-closeout-status-summary "
            "[--json] [--registry-base <dir>]"
        ),
        "operator_overview": (
            "python scripts/report_live_sessions.py --bounded-pilot-operator-overview "
            "[--json] [--config-path <path>] [--registry-base <dir>]"
        ),
        "gate_index": (
            "python scripts/report_live_sessions.py --bounded-pilot-gate-index "
            "[--json] [--config-path <path>] [--registry-base <dir>]"
        ),
        "first_live_frontdoor": (
            "python scripts/report_live_sessions.py --bounded-pilot-first-live-frontdoor "
            "[--json] [--config-path <path>] [--registry-base <dir>]"
        ),
        "lifecycle_consistency": (
            "python scripts/report_live_sessions.py --bounded-pilot-lifecycle-consistency "
            "[--json] [--registry-base <dir>]"
        ),
    }


_ABORT_TRIAGE_HINT_STATIC_DISCLAIMER = (
    "Navigation aid derived only from existing lifecycle/closeout read-model signals. "
    "Read-only; not live authorization, not eligibility, not a policy or go/no-go decision. "
    "See docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md."
)


def _abort_triage_hints_for_lifecycle(
    *,
    lifecycle_consistency_summary: str,
    mismatch_signals: list[str],
) -> list[dict[str, Any]]:
    """
    Non-authorizing triage hints from lifecycle_consistency_summary + mismatch_signals only.

    Aligns with RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md; does not add new
    incident categories or runtime semantics.
    """
    if lifecycle_consistency_summary == "ALIGNED_TERMINAL_REGISTRY_WITH_EXEC_JSONL":
        return []

    def _one_hint(
        *,
        primary_runbook: str,
        primary_runbook_docs_token: str,
        section_5_keywords: list[str],
        extra_matched_signals: list[str],
    ) -> dict[str, Any]:
        matched: list[str] = [
            f"lifecycle_consistency_summary={lifecycle_consistency_summary}",
            *extra_matched_signals,
        ]
        for m in mismatch_signals:
            matched.append(f"mismatch_signal={m}")
        return {
            "disclaimer": _ABORT_TRIAGE_HINT_STATIC_DISCLAIMER,
            "primary_runbook": primary_runbook,
            "primary_runbook_docs_token": primary_runbook_docs_token,
            "section_5_keywords": section_5_keywords,
            "matched_signals": matched,
        }

    if lifecycle_consistency_summary == "REGISTRY_ARTIFACT_CONFLICT_STARTED_VS_TERMINAL":
        return [
            _one_hint(
                primary_runbook="docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md",
                primary_runbook_docs_token="DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH",
                section_5_keywords=[
                    "session-end mismatch is unresolved",
                    "stale state is unresolved",
                    "ambiguity => NO_TRADE / safe stop",
                ],
                extra_matched_signals=["derived_from=open_vs_terminal_artifact_conflict"],
            )
        ]
    if lifecycle_consistency_summary == "PARTIAL_TERMINAL_REGISTRY_WITHOUT_EXEC_JSONL":
        return [
            _one_hint(
                primary_runbook="docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md",
                primary_runbook_docs_token="DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED",
                section_5_keywords=[
                    "evidence or dependency posture is degraded beyond acceptable pilot tolerance",
                    "operator cannot clearly determine the current bounded posture",
                    "ambiguity => NO_TRADE / safe stop",
                ],
                extra_matched_signals=[
                    "derived_from=terminal_registry_without_execution_events_jsonl",
                ],
            )
        ]
    if lifecycle_consistency_summary == "PARTIAL_NON_TERMINAL_REGISTRY_OPEN_OR_STARTED":
        return [
            _one_hint(
                primary_runbook="docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md",
                primary_runbook_docs_token="DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH",
                section_5_keywords=[
                    "stale state is unresolved",
                    "operator cannot clearly determine the current bounded posture",
                    "ambiguity => NO_TRADE / safe stop",
                ],
                extra_matched_signals=["derived_from=registry_non_terminal_newest_only"],
            )
        ]
    if lifecycle_consistency_summary == "NO_BOUNDED_PILOT_SESSION":
        return [
            _one_hint(
                primary_runbook=(
                    "docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md"
                ),
                primary_runbook_docs_token="DOCS_TOKEN_RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS",
                section_5_keywords=[
                    "operator cannot clearly determine the current bounded posture",
                    "any ambiguity exists about whether trading is allowed",
                ],
                extra_matched_signals=["derived_from=no_bounded_pilot_session_in_focus"],
            )
        ]
    if lifecycle_consistency_summary in (
        "REGISTRY_SCAN_MISMATCH",
        "UNKNOWN_CLOSEOUT_SIGNAL",
        "NON_STANDARD_REGISTRY_STATUS_IN_NEWEST_ARTIFACT",
    ):
        return [
            _one_hint(
                primary_runbook="docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md",
                primary_runbook_docs_token="DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH",
                section_5_keywords=[
                    "stale state is unresolved",
                    "ambiguity => NO_TRADE / safe stop",
                ],
                extra_matched_signals=[
                    f"derived_from=lifecycle_code_{lifecycle_consistency_summary}",
                ],
            )
        ]
    return []


def _build_bounded_pilot_lifecycle_consistency_block(
    session_focus: dict[str, Any],
    closeout: dict[str, Any],
) -> dict[str, Any]:
    """
    Read-only lifecycle/handoff *consistency* view from existing session_focus + closeout only.

    Does not infer runner/handoff success; flags partial or mismatched artifact sets only.
    """
    sid = session_focus.get("primary_session_id")
    primary_source = session_focus.get("primary_source")
    co_sum = closeout.get("closeout_signal_summary")
    conflict = bool(closeout.get("open_vs_terminal_artifact_conflict"))
    exec_present = bool(closeout.get("execution_events_jsonl_present"))
    newest_terminal = bool(closeout.get("registry_terminal_in_newest_artifact"))
    newest_status = closeout.get("newest_registry_status")
    pointers = closeout.get("pointers")

    mismatch: list[str] = []
    partial = False
    notes: list[str] = [
        "Operational handoff or runner success is not inferable from registry and pointer "
        "artifacts alone; this block only compares available read-only signals.",
    ]

    signals_present: dict[str, Any] = {
        "primary_session_id_resolved": sid is not None,
        "registry_json_pointer_resolvable": bool(pointers),
        "execution_events_jsonl_present": exec_present,
        "registry_newest_status": newest_status,
        "registry_terminal_in_newest_artifact": newest_terminal,
        "registry_artifact_started_vs_terminal_conflict": conflict,
    }

    if sid is None:
        lifecycle_code = "NO_BOUNDED_PILOT_SESSION"
        partial = True
        notes.append("No bounded_pilot session_id resolved from registry.")
    elif conflict:
        lifecycle_code = "REGISTRY_ARTIFACT_CONFLICT_STARTED_VS_TERMINAL"
        partial = True
        mismatch.append("newest_artifact_started_coexists_with_older_terminal_artifact")
    elif co_sum == "REGISTRY_TERMINAL_IN_NEWEST_ARTIFACT":
        if exec_present:
            lifecycle_code = "ALIGNED_TERMINAL_REGISTRY_WITH_EXEC_JSONL"
            partial = False
        else:
            lifecycle_code = "PARTIAL_TERMINAL_REGISTRY_WITHOUT_EXEC_JSONL"
            partial = True
            mismatch.append("terminal_newest_artifact_but_execution_events_jsonl_missing")
    elif co_sum == "REGISTRY_NON_TERMINAL_NEWEST_ONLY":
        lifecycle_code = "PARTIAL_NON_TERMINAL_REGISTRY_OPEN_OR_STARTED"
        partial = True
        mismatch.append("newest_registry_artifact_non_terminal_only")
    elif co_sum == "NO_BOUNDED_PILOT_SESSION_IN_REGISTRY":
        lifecycle_code = "NO_BOUNDED_PILOT_SESSION"
        partial = True
    elif co_sum == "REGISTRY_ROWS_MISSING_AFTER_SELECTION":
        lifecycle_code = "REGISTRY_SCAN_MISMATCH"
        partial = True
        mismatch.append("primary_session_id_resolved_but_no_bounded_pilot_rows_on_scan")
    elif co_sum == "REGISTRY_STATUS_NON_STANDARD":
        lifecycle_code = "NON_STANDARD_REGISTRY_STATUS_IN_NEWEST_ARTIFACT"
        partial = True
        mismatch.append("non_terminal_non_started_status_in_newest_artifact")
    else:
        lifecycle_code = "UNKNOWN_CLOSEOUT_SIGNAL"
        partial = True
        mismatch.append(f"unhandled_closeout_signal_summary={co_sum!r}")

    abort_triage_hints = _abort_triage_hints_for_lifecycle(
        lifecycle_consistency_summary=lifecycle_code,
        mismatch_signals=mismatch,
    )

    return {
        "contract": "report_live_sessions.lifecycle_consistency_v1",
        "lifecycle_consistency_summary": lifecycle_code,
        "primary_source": primary_source,
        "partial_status": partial,
        "signals_present": signals_present,
        "mismatch_signals": mismatch,
        "closeout_signal_summary": co_sum,
        "operator_notes": notes,
        "abort_triage_hints": abort_triage_hints,
    }


def _build_bounded_pilot_gate_enablement_index(
    readiness_block: dict[str, Any],
    packet_out: dict[str, Any],
    session_focus: dict[str, Any],
    closeout: dict[str, Any],
) -> dict[str, Any]:
    """
    Compact read-only index from existing overview signals only (no new semantics).
    """
    gng = readiness_block.get("go_no_go") or {}
    verdict = gng.get("verdict") if isinstance(gng, dict) else None
    lr = readiness_block.get("live_readiness") or {}
    lr_all = lr.get("all_passed") if isinstance(lr, dict) else None

    open_rows = session_focus.get("open_bounded_pilot_sessions") or []
    pkt_ok = packet_out.get("packet_ok") if packet_out.get("evaluated") else None

    return {
        "contract": "report_live_sessions.gate_enablement_index_v1",
        "readiness_repository_ok": readiness_block.get("ok"),
        "readiness_blocked_at": readiness_block.get("blocked_at"),
        "go_no_go_verdict": verdict,
        "live_readiness_all_passed": lr_all,
        "preflight_packet_evaluated": packet_out.get("evaluated"),
        "preflight_packet_ok": pkt_ok,
        "preflight_packet_code": packet_out.get("packet_code"),
        "primary_session_id": session_focus.get("primary_session_id"),
        "primary_source": session_focus.get("primary_source"),
        "bounded_pilot_open_started_count": len(open_rows),
        "closeout_signal_summary": closeout.get("closeout_signal_summary"),
        "registry_newest_status": closeout.get("newest_registry_status"),
        "registry_terminal_in_newest_artifact": closeout.get(
            "registry_terminal_in_newest_artifact"
        ),
        "execution_events_jsonl_present": closeout.get("execution_events_jsonl_present"),
        "registry_artifact_open_vs_terminal_conflict": closeout.get(
            "open_vs_terminal_artifact_conflict"
        ),
        "index_notes": [
            "Indexed fields are read-only derivatives of existing signals only; "
            "not a live authorization, not gate closure, not operational handoff success.",
        ],
    }


def _run_bounded_pilot_readiness_summary(args: argparse.Namespace, logger: logging.Logger) -> int:
    """
    One-shot read-only snapshot: current readiness + operator preflight packet + registry focus.

    Does not authorize live trading or assert gate closure; see payload disclaimer.
    """
    from scripts.ops.check_bounded_pilot_readiness import resolve_bounded_pilot_config_path

    repo_root = PROJECT_ROOT
    explicit_cfg = Path(args.config_path) if getattr(args, "config_path", None) else None
    config_path = resolve_bounded_pilot_config_path(repo_root, explicit_cfg)
    base_dir = _registry_base_dir(args)
    cwd = Path.cwd()

    readiness_block, packet_out = _collect_bounded_pilot_readiness_and_packet(
        repo_root=repo_root,
        config_path=config_path,
        logger=logger,
    )

    session_focus = _collect_bounded_pilot_session_focus(base_dir=base_dir, cwd=cwd)

    payload: dict[str, Any] = {
        "contract": "report_live_sessions.bounded_pilot_readiness_summary",
        "disclaimer": (
            "Read-only repo snapshot of current bounded-pilot readiness/preflight evaluation "
            "plus registry pointers. Not a live authorization, not a gate-closure verdict, "
            "not a claim that a historical session was packet-GREEN."
        ),
        "config_path": str(config_path),
        "registry_dir": str(base_dir),
        "bounded_pilot_readiness": readiness_block,
        "operator_preflight_packet": packet_out,
        "session_focus": session_focus,
    }

    logger.info(
        "Bounded-pilot readiness summary (read-only) primary=%s",
        session_focus["primary_session_id"],
    )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    r = readiness_block
    p = packet_out
    sf = session_focus
    lines = [
        "Bounded-pilot readiness summary (read-only)",
        f"  disclaimer: {payload['disclaimer']}",
        f"  config_path: {config_path}",
        "",
        "  Current evaluation (repository state now):",
        f"    readiness evaluated: {r.get('evaluated')}",
        f"    readiness ok: {r.get('ok')}",
        f"    blocked_at: {r.get('blocked_at')}",
        f"    message: {r.get('message')}",
    ]
    gng = r.get("go_no_go") or {}
    if gng:
        lines.append(f"    go_no_go verdict: {gng.get('verdict')}")
    lines.append("")
    lines.append("  Operator preflight packet (build attempt):")
    lines.append(f"    evaluated: {p.get('evaluated')}")
    lines.append(f"    packet_code: {p.get('packet_code')}")
    if p.get("evaluated"):
        lines.append(f"    packet_ok: {p.get('packet_ok')}")
        lines.append(
            f"    blocked_lines: {p.get('blocked_lines_total')} "
            f"(showing up to {len(p.get('blocked_lines_preview') or [])})"
        )
        for b in p.get("blocked_lines_preview") or []:
            lines.append(f"      - {b}")
    else:
        lines.append(f"    error: {p.get('error')}")
    lines.append("")
    lines.append("  Session / registry focus (bounded_pilot):")
    lines.append(f"    primary_session_id: {sf['primary_session_id']}")
    lines.append(f"    primary_source: {sf['primary_source']}")
    if sf["open_bounded_pilot_sessions"]:
        lines.append(f"    open started rows: {sf['open_bounded_pilot_sessions']}")
    else:
        lines.append("    open started rows: []")
    if sf.get("latest_bounded_pilot_registry"):
        lines.append(f"    latest registry row: {sf['latest_bounded_pilot_registry']}")
    else:
        lines.append("    latest registry row: none")
    ptr = sf.get("pointers")
    if ptr:
        ej = ptr["execution_events_session_jsonl"]
        lines.append(f"    pointers session_id: {ptr['session_id']}")
        lines.append(f"    registry_json: {ptr['registry_json']['resolved']}")
        lines.append(
            f"    execution_events_jsonl: {ej['resolved']}  present: {'yes' if ej['present'] else 'no'}"
        )
    else:
        lines.append("    pointers: none (no primary session_id resolved in registry)")
    print("\n".join(lines))
    return 0


def _bounded_pilot_readiness_summary_flag_conflicts(args: argparse.Namespace) -> str | None:
    if args.session_id is not None:
        return "--session-id is only for --evidence-pointers"
    if args.latest_bounded_pilot:
        return "--latest-bounded-pilot is only for --evidence-pointers"
    if args.bounded_pilot_only or args.latest_bounded_pilot_open:
        return "--bounded-pilot-only / --latest-bounded-pilot-open require --open-sessions"
    if args.run_type is not None:
        return "--run-type is not compatible with --bounded-pilot-readiness-summary"
    if args.status is not None:
        return "--status is not compatible with --bounded-pilot-readiness-summary"
    if args.limit is not None:
        return "--limit is not compatible with --bounded-pilot-readiness-summary"
    if args.summary_only:
        return "--summary-only is not compatible with --bounded-pilot-readiness-summary"
    if args.output_dir is not None:
        return "--output-dir is not compatible with --bounded-pilot-readiness-summary"
    if args.stdout:
        return "--stdout is not compatible with --bounded-pilot-readiness-summary"
    return None


def _bounded_pilot_closeout_status_summary_flag_conflicts(args: argparse.Namespace) -> str | None:
    if args.session_id is not None:
        return "--session-id is only for --evidence-pointers"
    if args.latest_bounded_pilot:
        return "--latest-bounded-pilot is only for --evidence-pointers"
    if args.bounded_pilot_only or args.latest_bounded_pilot_open:
        return "--bounded-pilot-only / --latest-bounded-pilot-open require --open-sessions"
    if args.run_type is not None:
        return "--run-type is not compatible with --bounded-pilot-closeout-status-summary"
    if args.status is not None:
        return "--status is not compatible with --bounded-pilot-closeout-status-summary"
    if args.limit is not None:
        return "--limit is not compatible with --bounded-pilot-closeout-status-summary"
    if args.summary_only:
        return "--summary-only is not compatible with --bounded-pilot-closeout-status-summary"
    if args.output_dir is not None:
        return "--output-dir is not compatible with --bounded-pilot-closeout-status-summary"
    if args.stdout:
        return "--stdout is not compatible with --bounded-pilot-closeout-status-summary"
    if getattr(args, "config_path", None):
        return (
            "--config-path is only for --bounded-pilot-readiness-summary, "
            "--bounded-pilot-operator-overview, --bounded-pilot-gate-index, "
            "or --bounded-pilot-first-live-frontdoor"
        )
    return None


def _bounded_pilot_operator_overview_flag_conflicts(args: argparse.Namespace) -> str | None:
    """Same incompatibility surface as readiness summary (optional --config-path)."""
    if args.session_id is not None:
        return "--session-id is only for --evidence-pointers"
    if args.latest_bounded_pilot:
        return "--latest-bounded-pilot is only for --evidence-pointers"
    if args.bounded_pilot_only or args.latest_bounded_pilot_open:
        return "--bounded-pilot-only / --latest-bounded-pilot-open require --open-sessions"
    if args.run_type is not None:
        return "--run-type is not compatible with --bounded-pilot-operator-overview"
    if args.status is not None:
        return "--status is not compatible with --bounded-pilot-operator-overview"
    if args.limit is not None:
        return "--limit is not compatible with --bounded-pilot-operator-overview"
    if args.summary_only:
        return "--summary-only is not compatible with --bounded-pilot-operator-overview"
    if args.output_dir is not None:
        return "--output-dir is not compatible with --bounded-pilot-operator-overview"
    if args.stdout:
        return "--stdout is not compatible with --bounded-pilot-operator-overview"
    return None


def _bounded_pilot_gate_index_flag_conflicts(args: argparse.Namespace) -> str | None:
    """Same incompatibility surface as operator overview (optional --config-path)."""
    if args.session_id is not None:
        return "--session-id is only for --evidence-pointers"
    if args.latest_bounded_pilot:
        return "--latest-bounded-pilot is only for --evidence-pointers"
    if args.bounded_pilot_only or args.latest_bounded_pilot_open:
        return "--bounded-pilot-only / --latest-bounded-pilot-open require --open-sessions"
    if args.run_type is not None:
        return "--run-type is not compatible with --bounded-pilot-gate-index"
    if args.status is not None:
        return "--status is not compatible with --bounded-pilot-gate-index"
    if args.limit is not None:
        return "--limit is not compatible with --bounded-pilot-gate-index"
    if args.summary_only:
        return "--summary-only is not compatible with --bounded-pilot-gate-index"
    if args.output_dir is not None:
        return "--output-dir is not compatible with --bounded-pilot-gate-index"
    if args.stdout:
        return "--stdout is not compatible with --bounded-pilot-gate-index"
    return None


def _run_bounded_pilot_operator_overview(
    args: argparse.Namespace,
    logger: logging.Logger,
) -> int:
    """Read-only single view: readiness + packet + session focus + closeout (reuses helpers)."""
    config_path, base_dir, readiness_block, packet_out, session_focus, closeout = (
        _collect_bounded_pilot_overview_data(args, logger)
    )

    payload: dict[str, Any] = {
        "contract": "report_live_sessions.bounded_pilot_operator_overview",
        "disclaimer": (
            "Read-only consolidated bounded_pilot snapshot: current readiness/preflight evaluation, "
            "registry session focus, closeout/final-status signals, and pointers. "
            "Not a live authorization, not gate closure, not proof of handoff or session outcome."
        ),
        "config_path": str(config_path),
        "registry_dir": str(base_dir),
        "bounded_pilot_readiness": readiness_block,
        "operator_preflight_packet": packet_out,
        "session_focus": session_focus,
        "closeout": closeout,
    }

    logger.info(
        "Bounded-pilot operator overview (read-only) primary=%s closeout=%s",
        session_focus.get("primary_session_id"),
        closeout.get("closeout_signal_summary"),
    )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    r = readiness_block
    p = packet_out
    sf = session_focus
    co = closeout
    lines = [
        "Bounded-pilot operator overview (read-only)",
        f"  disclaimer: {payload['disclaimer']}",
        f"  config_path: {config_path}",
        "",
        "  Readiness (repository state now):",
        f"    readiness ok: {r.get('ok')}  blocked_at: {r.get('blocked_at')}",
        f"    message: {r.get('message')}",
        "",
        "  Operator preflight packet:",
        f"    evaluated: {p.get('evaluated')}  packet_ok: {p.get('packet_ok')}",
        f"    packet_code: {p.get('packet_code')}",
        "",
        "  Session focus (bounded_pilot):",
        f"    primary_session_id: {sf['primary_session_id']}",
        f"    primary_source: {sf['primary_source']}",
        f"    open started rows: {sf['open_bounded_pilot_sessions'] or []}",
        f"    latest registry row: {sf.get('latest_bounded_pilot_registry')}",
        "",
        "  Closeout / registry:",
        f"    closeout_signal_summary: {co['closeout_signal_summary']}",
        f"    newest_registry_status: {co['newest_registry_status']}",
        f"    execution_events_jsonl_present: {co['execution_events_jsonl_present']}",
    ]
    ptr = co.get("pointers") or sf.get("pointers")
    if ptr:
        ej = ptr["execution_events_session_jsonl"]
        lines.append("")
        lines.append("  Pointers:")
        lines.append(f"    registry_json: {ptr['registry_json']['resolved']}")
        lines.append(
            f"    execution_events_jsonl: {ej['resolved']}  present: "
            f"{'yes' if ej['present'] else 'no'}"
        )
    else:
        lines.append("")
        lines.append("  Pointers: none")
    if co.get("operator_notes"):
        lines.append("")
        lines.append("  Closeout notes:")
        for n in co["operator_notes"]:
            lines.append(f"    - {n}")
    print("\n".join(lines))
    return 0


def _run_bounded_pilot_gate_index(
    args: argparse.Namespace,
    logger: logging.Logger,
) -> int:
    """Read-only gate/enablement index plus full overview context (same data as operator overview)."""
    config_path, base_dir, readiness_block, packet_out, session_focus, closeout = (
        _collect_bounded_pilot_overview_data(args, logger)
    )
    gate_index = _build_bounded_pilot_gate_enablement_index(
        readiness_block,
        packet_out,
        session_focus,
        closeout,
    )

    payload: dict[str, Any] = {
        "contract": "report_live_sessions.bounded_pilot_gate_index",
        "disclaimer": (
            "Read-only bounded_pilot gate/enablement index plus full overview context. "
            "The gate_enablement_index block normalizes existing readiness/packet/session/closeout "
            "signals only. Not a live authorization, not gate closure, not proof of handoff."
        ),
        "config_path": str(config_path),
        "registry_dir": str(base_dir),
        "gate_enablement_index": gate_index,
        "bounded_pilot_readiness": readiness_block,
        "operator_preflight_packet": packet_out,
        "session_focus": session_focus,
        "closeout": closeout,
    }

    logger.info(
        "Bounded-pilot gate index (read-only) primary=%s index_contract=%s",
        session_focus.get("primary_session_id"),
        gate_index.get("contract"),
    )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    gi = gate_index
    r = readiness_block
    p = packet_out
    sf = session_focus
    co = closeout
    lines = [
        "Bounded-pilot gate / enablement index (read-only)",
        f"  disclaimer: {payload['disclaimer']}",
        f"  config_path: {config_path}",
        "",
        "  Gate / enablement index (normalized from existing signals):",
        f"    readiness_repository_ok: {gi['readiness_repository_ok']}",
        f"    readiness_blocked_at: {gi['readiness_blocked_at']}",
        f"    go_no_go_verdict: {gi['go_no_go_verdict']}",
        f"    live_readiness_all_passed: {gi['live_readiness_all_passed']}",
        f"    preflight_packet_evaluated: {gi['preflight_packet_evaluated']}",
        f"    preflight_packet_ok: {gi['preflight_packet_ok']}",
        f"    preflight_packet_code: {gi['preflight_packet_code']}",
        f"    primary_session_id: {gi['primary_session_id']}",
        f"    primary_source: {gi['primary_source']}",
        f"    bounded_pilot_open_started_count: {gi['bounded_pilot_open_started_count']}",
        f"    closeout_signal_summary: {gi['closeout_signal_summary']}",
        f"    registry_newest_status: {gi['registry_newest_status']}",
        f"    registry_terminal_in_newest_artifact: {gi['registry_terminal_in_newest_artifact']}",
        f"    execution_events_jsonl_present: {gi['execution_events_jsonl_present']}",
        f"    registry_artifact_open_vs_terminal_conflict: "
        f"{gi['registry_artifact_open_vs_terminal_conflict']}",
    ]
    for n in gi.get("index_notes") or []:
        lines.append(f"    note: {n}")
    lines.extend(
        [
            "",
            "  Context — readiness (repository state now):",
            f"    readiness ok: {r.get('ok')}  blocked_at: {r.get('blocked_at')}",
            f"    message: {r.get('message')}",
            "",
            "  Context — operator preflight packet:",
            f"    evaluated: {p.get('evaluated')}  packet_ok: {p.get('packet_ok')}",
            f"    packet_code: {p.get('packet_code')}",
            "",
            "  Context — session focus (bounded_pilot):",
            f"    primary_session_id: {sf['primary_session_id']}",
            f"    primary_source: {sf['primary_source']}",
            f"    open started rows: {sf['open_bounded_pilot_sessions'] or []}",
            f"    latest registry row: {sf.get('latest_bounded_pilot_registry')}",
            "",
            "  Context — closeout / registry:",
            f"    closeout_signal_summary: {co['closeout_signal_summary']}",
            f"    newest_registry_status: {co['newest_registry_status']}",
            f"    execution_events_jsonl_present: {co['execution_events_jsonl_present']}",
        ]
    )
    ptr = co.get("pointers") or sf.get("pointers")
    if ptr:
        ej = ptr["execution_events_session_jsonl"]
        lines.append("")
        lines.append("  Pointers:")
        lines.append(f"    registry_json: {ptr['registry_json']['resolved']}")
        lines.append(
            f"    execution_events_jsonl: {ej['resolved']}  present: "
            f"{'yes' if ej['present'] else 'no'}"
        )
    else:
        lines.append("")
        lines.append("  Pointers: none")
    if co.get("operator_notes"):
        lines.append("")
        lines.append("  Closeout notes:")
        for n in co["operator_notes"]:
            lines.append(f"    - {n}")
    print("\n".join(lines))
    return 0


def _bounded_pilot_first_live_frontdoor_flag_conflicts(args: argparse.Namespace) -> str | None:
    """Same incompatibility surface as gate index (optional --config-path)."""
    if args.session_id is not None:
        return "--session-id is only for --evidence-pointers"
    if args.latest_bounded_pilot:
        return "--latest-bounded-pilot is only for --evidence-pointers"
    if args.bounded_pilot_only or args.latest_bounded_pilot_open:
        return "--bounded-pilot-only / --latest-bounded-pilot-open require --open-sessions"
    if args.run_type is not None:
        return "--run-type is not compatible with --bounded-pilot-first-live-frontdoor"
    if args.status is not None:
        return "--status is not compatible with --bounded-pilot-first-live-frontdoor"
    if args.limit is not None:
        return "--limit is not compatible with --bounded-pilot-first-live-frontdoor"
    if args.summary_only:
        return "--summary-only is not compatible with --bounded-pilot-first-live-frontdoor"
    if args.output_dir is not None:
        return "--output-dir is not compatible with --bounded-pilot-first-live-frontdoor"
    if args.stdout:
        return "--stdout is not compatible with --bounded-pilot-first-live-frontdoor"
    return None


def _run_bounded_pilot_first_live_frontdoor(
    args: argparse.Namespace,
    logger: logging.Logger,
) -> int:
    """
    Read-only single frontdoor: overview data + gate index + canonical CLI hints for sub-views.

    Reuses _collect_bounded_pilot_overview_data and _build_bounded_pilot_gate_enablement_index;
    does not add new semantics beyond composition.
    """
    config_path, base_dir, readiness_block, packet_out, session_focus, closeout = (
        _collect_bounded_pilot_overview_data(args, logger)
    )
    gate_index = _build_bounded_pilot_gate_enablement_index(
        readiness_block,
        packet_out,
        session_focus,
        closeout,
    )
    canonical = _canonical_bounded_pilot_read_only_subcommands()

    payload: dict[str, Any] = {
        "contract": "report_live_sessions.bounded_pilot_first_live_frontdoor_v1",
        "disclaimer": (
            "Read-only bounded_pilot / first-live operator frontdoor: aggregates existing "
            "readiness, preflight packet, session focus, closeout, and gate/enablement index "
            "signals plus canonical CLI hints for deeper read-only sub-views. "
            "Not a live authorization, not gate closure, not proof of handoff or session outcome."
        ),
        "config_path": str(config_path),
        "registry_dir": str(base_dir),
        "canonical_read_only_subcommands": canonical,
        "gate_enablement_index": gate_index,
        "bounded_pilot_readiness": readiness_block,
        "operator_preflight_packet": packet_out,
        "session_focus": session_focus,
        "closeout": closeout,
    }

    logger.info(
        "Bounded-pilot first-live frontdoor (read-only) primary=%s closeout=%s",
        session_focus.get("primary_session_id"),
        closeout.get("closeout_signal_summary"),
    )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    r = readiness_block
    p = packet_out
    sf = session_focus
    co = closeout
    gi = gate_index
    lines = [
        "Bounded-pilot / first-live frontdoor (read-only)",
        f"  disclaimer: {payload['disclaimer']}",
        f"  config_path: {config_path}",
        "",
        "  Canonical read-only subcommands (deeper views; same contracts as dedicated flags):",
    ]
    for key in sorted(canonical.keys()):
        lines.append(f"    {key}: {canonical[key]}")
    lines.extend(
        [
            "",
            "  Gate / enablement index (normalized from existing signals):",
            f"    readiness_repository_ok: {gi['readiness_repository_ok']}",
            f"    readiness_blocked_at: {gi['readiness_blocked_at']}",
            f"    go_no_go_verdict: {gi['go_no_go_verdict']}",
            f"    live_readiness_all_passed: {gi['live_readiness_all_passed']}",
            f"    preflight_packet_evaluated: {gi['preflight_packet_evaluated']}",
            f"    preflight_packet_ok: {gi['preflight_packet_ok']}",
            f"    primary_session_id: {gi['primary_session_id']}",
            f"    primary_source: {gi['primary_source']}",
            f"    bounded_pilot_open_started_count: {gi['bounded_pilot_open_started_count']}",
            f"    closeout_signal_summary: {gi['closeout_signal_summary']}",
            f"    registry_newest_status: {gi['registry_newest_status']}",
            f"    execution_events_jsonl_present: {gi['execution_events_jsonl_present']}",
        ]
    )
    for n in gi.get("index_notes") or []:
        lines.append(f"    note: {n}")
    lines.extend(
        [
            "",
            "  Readiness (repository state now):",
            f"    readiness ok: {r.get('ok')}  blocked_at: {r.get('blocked_at')}",
            f"    message: {r.get('message')}",
            "",
            "  Operator preflight packet:",
            f"    evaluated: {p.get('evaluated')}  packet_ok: {p.get('packet_ok')}",
            f"    packet_code: {p.get('packet_code')}",
            "",
            "  Session focus (bounded_pilot):",
            f"    primary_session_id: {sf['primary_session_id']}",
            f"    primary_source: {sf['primary_source']}",
            f"    open started rows: {sf['open_bounded_pilot_sessions'] or []}",
            f"    latest registry row: {sf.get('latest_bounded_pilot_registry')}",
            "",
            "  Closeout / registry:",
            f"    closeout_signal_summary: {co['closeout_signal_summary']}",
            f"    newest_registry_status: {co['newest_registry_status']}",
            f"    execution_events_jsonl_present: {co['execution_events_jsonl_present']}",
        ]
    )
    ptr = co.get("pointers") or sf.get("pointers")
    if ptr:
        ej = ptr["execution_events_session_jsonl"]
        lines.append("")
        lines.append("  Pointers:")
        lines.append(f"    registry_json: {ptr['registry_json']['resolved']}")
        lines.append(
            f"    execution_events_jsonl: {ej['resolved']}  present: "
            f"{'yes' if ej['present'] else 'no'}"
        )
    else:
        lines.append("")
        lines.append("  Pointers: none")
    if co.get("operator_notes"):
        lines.append("")
        lines.append("  Closeout notes:")
        for n in co["operator_notes"]:
            lines.append(f"    - {n}")
    print("\n".join(lines))
    return 0


def _bounded_pilot_lifecycle_consistency_flag_conflicts(args: argparse.Namespace) -> str | None:
    """Same incompatibility surface as closeout status summary (registry-only; no --config-path)."""
    if args.session_id is not None:
        return "--session-id is only for --evidence-pointers"
    if args.latest_bounded_pilot:
        return "--latest-bounded-pilot is only for --evidence-pointers"
    if args.bounded_pilot_only or args.latest_bounded_pilot_open:
        return "--bounded-pilot-only / --latest-bounded-pilot-open require --open-sessions"
    if args.run_type is not None:
        return "--run-type is not compatible with --bounded-pilot-lifecycle-consistency"
    if args.status is not None:
        return "--status is not compatible with --bounded-pilot-lifecycle-consistency"
    if args.limit is not None:
        return "--limit is not compatible with --bounded-pilot-lifecycle-consistency"
    if args.summary_only:
        return "--summary-only is not compatible with --bounded-pilot-lifecycle-consistency"
    if args.output_dir is not None:
        return "--output-dir is not compatible with --bounded-pilot-lifecycle-consistency"
    if args.stdout:
        return "--stdout is not compatible with --bounded-pilot-lifecycle-consistency"
    if getattr(args, "config_path", None):
        return (
            "--config-path is only for --bounded-pilot-readiness-summary, "
            "--bounded-pilot-operator-overview, --bounded-pilot-gate-index, "
            "or --bounded-pilot-first-live-frontdoor"
        )
    return None


def _run_bounded_pilot_lifecycle_consistency(
    args: argparse.Namespace,
    logger: logging.Logger,
) -> int:
    """
    Read-only bounded_pilot lifecycle/handoff consistency: session focus + closeout + compact signals.

    Reuses _collect_bounded_pilot_session_focus and _build_bounded_pilot_closeout_analysis only.
    """
    base_dir = _registry_base_dir(args)
    cwd = Path.cwd()
    session_focus = _collect_bounded_pilot_session_focus(base_dir=base_dir, cwd=cwd)
    closeout = _build_bounded_pilot_closeout_analysis(
        session_focus,
        base_dir=base_dir,
        cwd=cwd,
    )
    lifecycle = _build_bounded_pilot_lifecycle_consistency_block(session_focus, closeout)

    payload: dict[str, Any] = {
        "contract": "report_live_sessions.bounded_pilot_lifecycle_consistency",
        "disclaimer": (
            "Read-only bounded_pilot lifecycle/handoff *consistency* view: compares registry "
            "selection, closeout/final-status signals, and session-scoped pointer presence. "
            "Not a live authorization, not proof of successful handoff, session completion, or "
            "that a process is or is not running."
        ),
        "registry_dir": str(base_dir),
        "lifecycle_consistency": lifecycle,
        "session_focus": session_focus,
        "closeout": closeout,
    }

    logger.info(
        "Bounded-pilot lifecycle consistency (read-only) primary=%s summary=%s",
        session_focus.get("primary_session_id"),
        lifecycle.get("lifecycle_consistency_summary"),
    )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    lc = lifecycle
    sf = session_focus
    co = closeout
    lines = [
        "Bounded-pilot lifecycle / handoff consistency (read-only)",
        f"  disclaimer: {payload['disclaimer']}",
        "",
        "  Lifecycle consistency (from existing registry + closeout signals):",
        f"    lifecycle_consistency_summary: {lc['lifecycle_consistency_summary']}",
        f"    primary_source: {lc['primary_source']}",
        f"    partial_status: {lc['partial_status']}",
    ]
    if lc.get("mismatch_signals"):
        lines.append(f"    mismatch_signals: {lc['mismatch_signals']}")
    else:
        lines.append("    mismatch_signals: []")
    hints = lc.get("abort_triage_hints") or []
    if hints:
        lines.append("    abort_triage_hints (read-only; not authorization):")
        for i, h in enumerate(hints):
            lines.append(f"      [{i}] primary_runbook: {h.get('primary_runbook')}")
            lines.append(f"      [{i}] section_5_keywords: {h.get('section_5_keywords')}")
    for n in lc.get("operator_notes") or []:
        lines.append(f"    note: {n}")
    lines.extend(
        [
            "",
            "  Session focus (bounded_pilot):",
            f"    primary_session_id: {sf['primary_session_id']}",
            f"    primary_source: {sf['primary_source']}",
            f"    open started rows: {sf['open_bounded_pilot_sessions'] or []}",
            f"    latest registry row: {sf.get('latest_bounded_pilot_registry')}",
            "",
            "  Closeout / registry:",
            f"    closeout_signal_summary: {co['closeout_signal_summary']}",
            f"    newest_registry_status: {co['newest_registry_status']}",
            f"    execution_events_jsonl_present: {co['execution_events_jsonl_present']}",
            f"    open_vs_terminal_artifact_conflict: {co['open_vs_terminal_artifact_conflict']}",
        ]
    )
    ptr = co.get("pointers")
    if ptr:
        ej = ptr["execution_events_session_jsonl"]
        lines.append("")
        lines.append("  Pointers:")
        lines.append(f"    registry_json: {ptr['registry_json']['resolved']}")
        lines.append(
            f"    execution_events_jsonl: {ej['resolved']}  present: "
            f"{'yes' if ej['present'] else 'no'}"
        )
    else:
        lines.append("")
        lines.append("  Pointers: none")
    if co.get("operator_notes"):
        lines.append("")
        lines.append("  Closeout notes:")
        for n in co["operator_notes"]:
            lines.append(f"    - {n}")
    print("\n".join(lines))
    return 0


def _run_bounded_pilot_closeout_status_summary(
    args: argparse.Namespace,
    logger: logging.Logger,
) -> int:
    """Read-only bounded_pilot closeout / final registry status + pointers (no readiness/packet run)."""
    base_dir = _registry_base_dir(args)
    cwd = Path.cwd()
    session_focus = _collect_bounded_pilot_session_focus(base_dir=base_dir, cwd=cwd)
    closeout = _build_bounded_pilot_closeout_analysis(
        session_focus,
        base_dir=base_dir,
        cwd=cwd,
    )
    lifecycle_for_hints = _build_bounded_pilot_lifecycle_consistency_block(
        session_focus,
        closeout,
    )
    abort_triage_hints = lifecycle_for_hints["abort_triage_hints"]

    payload: dict[str, Any] = {
        "contract": "report_live_sessions.bounded_pilot_closeout_status_summary",
        "disclaimer": (
            "Read-only registry and pointer snapshot for bounded_pilot closeout/final-status "
            "visibility. Terminal status is derived from the newest registry JSON per session_id "
            "(filename order). Not a live authorization, not proof of handoff success, not proof "
            "that a process is or is not running."
        ),
        "registry_dir": str(base_dir),
        "abort_triage_hints": abort_triage_hints,
        "session_focus": session_focus,
        "closeout": closeout,
    }

    logger.info(
        "Bounded-pilot closeout status summary (read-only) primary=%s summary=%s",
        session_focus.get("primary_session_id"),
        closeout.get("closeout_signal_summary"),
    )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    co = closeout
    sf = session_focus
    lines = [
        "Bounded-pilot closeout / final-status summary (read-only)",
        f"  disclaimer: {payload['disclaimer']}",
        "",
        "  Session selection (same rules as readiness summary):",
        f"    primary_session_id: {sf['primary_session_id']}",
        f"    primary_source: {sf['primary_source']}",
        "",
        "  Closeout / registry signals:",
        f"    closeout_signal_summary: {co['closeout_signal_summary']}",
        f"    newest_registry_status: {co['newest_registry_status']}",
        f"    registry_terminal_in_newest_artifact: {co['registry_terminal_in_newest_artifact']}",
        f"    any_terminal_artifact_exists: {co['any_terminal_artifact_exists']}",
        f"    open_vs_terminal_artifact_conflict: {co['open_vs_terminal_artifact_conflict']}",
        f"    execution_events_jsonl_present: {co['execution_events_jsonl_present']}",
        f"    statuses_seen_across_artifacts: {co['statuses_seen_across_artifacts']}",
    ]
    arts = co.get("registry_bounded_pilot_artifacts_for_session") or []
    if arts:
        lines.append("    registry artifacts (newest first):")
        for a in arts:
            lines.append(f"      - {a['registry_status']}: {a['path']}")
    ptr = co.get("pointers")
    if ptr:
        ej = ptr["execution_events_session_jsonl"]
        lines.append("")
        lines.append("  Pointers (session-scoped):")
        lines.append(f"    registry_json: {ptr['registry_json']['resolved']}")
        lines.append(
            f"    execution_events_jsonl: {ej['resolved']}  present: "
            f"{'yes' if ej['present'] else 'no'}"
        )
    else:
        lines.append("")
        lines.append("  Pointers: none")
    if co.get("operator_notes"):
        lines.append("")
        lines.append("  Operator notes:")
        for n in co["operator_notes"]:
            lines.append(f"    - {n}")
    hints = payload.get("abort_triage_hints") or []
    if hints:
        lines.append("")
        lines.append("  Abort triage hints (read-only; not authorization):")
        for i, h in enumerate(hints):
            lines.append(f"    hint[{i}].primary_runbook: {h.get('primary_runbook')}")
            lines.append(f"    hint[{i}].section_5_keywords: {h.get('section_5_keywords')}")
    print("\n".join(lines))
    return 0


# =============================================================================
# Pre-Live Package Status V0 (read-only aggregated gap signal; stdout JSON)
# =============================================================================

PRE_LIVE_PACKAGE_STATUS_AUTHORITY_BOUNDARY = {
    "live_authorization": False,
    "bounded_pilot_approval": False,
    "closeout_approval": False,
    "gate_passage": False,
    "strategy_readiness": False,
    "autonomy_readiness": False,
    "external_authority_completion": False,
}


def _derive_closeout_lifecycle_label_pre_live(
    n_open_bounded: int,
    closeout: dict[str, Any],
) -> str:
    """Map bounded-pilot closeout read-model to characterization lifecycle strings."""
    if n_open_bounded > 0:
        return "PARTIAL_NON_TERMINAL"
    summary = closeout.get("closeout_signal_summary")
    terminalish_codes = {
        "NO_BOUNDED_PILOT_SESSION_IN_REGISTRY",
        "REGISTRY_TERMINAL_IN_NEWEST_ARTIFACT",
    }
    partialish_codes = {
        "REGISTRY_ROWS_MISSING_AFTER_SELECTION",
        "AMBIGUOUS_NEWEST_STARTED_WITH_OLDER_TERMINAL",
        "REGISTRY_NON_TERMINAL_NEWEST_ONLY",
        "REGISTRY_STATUS_NON_STANDARD",
    }
    if summary in terminalish_codes:
        return "TERMINAL_CLEAN"
    if summary in partialish_codes:
        return "PARTIAL_NON_TERMINAL"
    return "PARTIAL_NON_TERMINAL"


def _compute_pre_live_package_status_semantics_v0(
    *,
    open_bounded_pilot_sessions: int,
    closeout_lifecycle_status: str,
    evidence_package_complete: bool,
    blocker_states: dict[str, str],
    external_decision_present: bool,
) -> tuple[str, list[str], list[str]]:
    """
    Mirrors tests/ops/test_report_live_sessions_pre_live_package_status_v0.py semantics.

    This function does not close blockers automatically; blocker_states is empty in v0 slices.
    """
    missing_or_open_items: list[str] = []
    blockers: list[str] = []

    if open_bounded_pilot_sessions:
        missing_or_open_items.append("bounded_pilot.open_sessions_present")
        blockers.append("GLB-018")

    if closeout_lifecycle_status != "TERMINAL_CLEAN":
        missing_or_open_items.append("closeout_lifecycle.non_terminal_or_partial")
        blockers.append("GLB-018")

    if not evidence_package_complete:
        missing_or_open_items.append("evidence_package.incomplete")
        blockers.append("GLB-003")

    for blocker_id, state in sorted(blocker_states.items()):
        if state in {"OPEN", "BLOCKED"}:
            missing_or_open_items.append(f"blockers.{blocker_id}.{state.lower()}")
            blockers.append(blocker_id)

    unique_blockers = sorted(set(blockers))
    unique_missing = sorted(set(missing_or_open_items))

    if unique_blockers:
        status = "BLOCKED"
    elif not evidence_package_complete:
        status = "NOT_READY"
    elif not external_decision_present:
        status = "READY_FOR_EXTERNAL_REVIEW"
    else:
        status = "REVIEW_ONLY"

    return status, unique_missing, unique_blockers


def _pre_live_package_status_flag_conflicts(args: argparse.Namespace) -> str | None:
    """--pre-live-package-status aggregates registry bounded-pilot posture; no readiness/packet run."""
    if args.session_id is not None:
        return "--session-id is only for --evidence-pointers"
    if args.latest_bounded_pilot:
        return "--latest-bounded-pilot is only for --evidence-pointers"
    if args.bounded_pilot_only or args.latest_bounded_pilot_open:
        return "--bounded-pilot-only / --latest-bounded-pilot-open require --open-sessions"
    if args.run_type is not None:
        return "--run-type is not compatible with --pre-live-package-status"
    if args.status is not None:
        return "--status is not compatible with --pre-live-package-status"
    if args.limit is not None:
        return "--limit is not compatible with --pre-live-package-status"
    if args.summary_only:
        return "--summary-only is not compatible with --pre-live-package-status"
    if args.output_dir is not None:
        return "--output-dir is not compatible with --pre-live-package-status"
    if args.stdout:
        return "--stdout is not compatible with --pre-live-package-status"
    if args.config_path is not None:
        return "--config-path is not compatible with --pre-live-package-status"
    if not args.json:
        return "--pre-live-package-status requires --json (stdout JSON-only v0 slice)"
    return None


def _run_pre_live_package_status(
    args: argparse.Namespace,
    logger: logging.Logger,
) -> int:
    """Read-only aggregated status JSON; registry + bounded_pilot artifact signals only."""
    if not args.json:
        print(
            "ERR: --pre-live-package-status requires --json",
            file=sys.stderr,
        )
        return 2

    base_dir = _registry_base_dir(args)
    cwd = Path.cwd()
    session_focus = _collect_bounded_pilot_session_focus(base_dir=base_dir, cwd=cwd)
    closeout = _build_bounded_pilot_closeout_analysis(
        session_focus,
        base_dir=base_dir,
        cwd=cwd,
    )

    open_rows = session_focus["open_bounded_pilot_sessions"]
    n_open = len(open_rows)

    lifecycle = _derive_closeout_lifecycle_label_pre_live(n_open, closeout)

    # v0 slice: do not imply external authority or evidence automation; blocker_states empty here.
    status, missing, bloc = _compute_pre_live_package_status_semantics_v0(
        open_bounded_pilot_sessions=n_open,
        closeout_lifecycle_status=lifecycle,
        evidence_package_complete=True,
        blocker_states={},
        external_decision_present=False,
    )

    logger.info(
        "Pre-Live Package Status V0 read-only posture (status=%s open_bounded=%s)",
        status,
        n_open,
    )

    payload = {
        "contract": "pre_live_package_status_v0",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": "pre_live_package_status",
        "registry_dir": str(base_dir.resolve()),
        "non_authorizing": True,
        "json_only": True,
        "stdout_only": True,
        "authority_boundary": dict(PRE_LIVE_PACKAGE_STATUS_AUTHORITY_BOUNDARY),
        "status": status,
        "open_bounded_pilot_sessions": n_open,
        "closeout_lifecycle_status": lifecycle,
        "closeout_signal_summary": closeout.get("closeout_signal_summary"),
        "primary_session_id": session_focus.get("primary_session_id"),
        "evidence_package_complete": True,
        "external_decision_present": False,
        "disclaimer_slices": (
            "This JSON is a read-only gap signal combining registry-derived bounded-pilot posture. "
            "It does not run readiness/preflight/cockpit checks in v0, does not close GLB rows automatically, "
            "and evidence_package_complete is not asserted by external attestations in this slice."
        ),
        "blocker_states": {},
        "missing_or_open_items": missing,
        "blockers": bloc,
        "signals": {
            "open_bounded_pilot_session_ids": [x["session_id"] for x in open_rows],
            "closeout_registry_terminal_in_newest": closeout.get(
                "registry_terminal_in_newest_artifact"
            ),
            "closeout_conflict": closeout.get("open_vs_terminal_artifact_conflict"),
        },
    }

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


# =============================================================================
# Session Review Pack V0 (read-only, non-authorizing; docs contract mapping)
# =============================================================================


def _session_review_pack_flag_conflicts(args: argparse.Namespace) -> str | None:
    """--session-review-pack is a static JSON pack in v0; no registry or report filters."""
    if args.session_id is not None:
        return "--session-id is only for --evidence-pointers"
    if args.latest_bounded_pilot:
        return "--latest-bounded-pilot is only for --evidence-pointers"
    if args.bounded_pilot_only or args.latest_bounded_pilot_open:
        return "--bounded-pilot-only / --latest-bounded-pilot-open require --open-sessions"
    if args.run_type is not None:
        return "--run-type is not compatible with --session-review-pack"
    if args.status is not None:
        return "--status is not compatible with --session-review-pack"
    if args.limit is not None:
        return "--limit is not compatible with --session-review-pack"
    if args.summary_only:
        return "--summary-only is not compatible with --session-review-pack"
    if args.output_dir is not None:
        return "--output-dir is not compatible with --session-review-pack"
    if args.stdout:
        return "--stdout is not compatible with --session-review-pack"
    if args.config_path is not None:
        return "--config-path is not compatible with --session-review-pack"
    if args.registry_base is not None:
        return "--registry-base is not compatible with --session-review-pack (v0 is static JSON)"
    if not args.json:
        return "--session-review-pack requires --json (read-only pack output; v0 JSON-only)"
    return None


def _build_session_review_pack_v0_payload() -> dict[str, Any]:
    """Build static v0 pack shape; session/reference fields are unpopulated until future slices."""
    session: dict[str, Any] = {
        "session_id": None,
        "run_timestamp": None,
        "mode_or_environment": None,
    }
    references: dict[str, Any] = {
        "provenance_reference": None,
        "evidence_references": [],
        "readiness_summary_reference": None,
        "handoff_reference": None,
        "registry_reference": None,
        "operator_notes": None,
        "risk_kill_switch_summary_reference": None,
        "execution_gate_summary_reference": None,
        "strategy_context_summary_reference": None,
        "dashboard_observer_summary_reference": None,
        "learning_loop_feedback_reference": None,
        "artifacts_manifest_reference": None,
    }
    missing: list[str] = []
    for k, v in session.items():
        if v is None:
            missing.append(f"session.{k}")
    for k, v in references.items():
        if k == "evidence_references":
            if not v:
                missing.append("references.evidence_references")
        elif v is None:
            missing.append(f"references.{k}")
    missing = sorted(missing)
    return {
        "contract": "report_live_sessions.session_review_pack_v0",
        "schema_version": "master_v2/session_review_pack/v0",
        "non_authorizing": True,
        "disclaimer": (
            "Read-only Session Review Pack V0: post-hoc review bundle shape; not live authorization, "
            "not signoff, not gate pass, not strategy or autonomy readiness."
        ),
        "authority_boundary": {
            "live_authorization": False,
            "signoff_complete": False,
            "gate_passed": False,
            "autonomy_ready": False,
            "strategy_ready": False,
        },
        "mode": "session_review_pack",
        "session": session,
        "references": references,
        "source_contract": "docs/ops/specs/MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md",
        "missing_fields": missing,
    }


def _run_session_review_pack(
    args: argparse.Namespace,
    logger: logging.Logger,
) -> int:
    """Emit static Session Review Pack V0 JSON (read-only, no registry I/O in v0)."""
    if not args.json:
        print(
            "ERR: --session-review-pack requires --json (read-only pack output; v0 JSON-only)",
            file=sys.stderr,
        )
        return 2
    logger.info("Session Review Pack V0 (read-only, static shape)")
    payload = _build_session_review_pack_v0_payload()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> int:
    """
    Haupteinstiegspunkt fuer Live Session Report CLI.

    Returns:
        Exit-Code (0 = Success, 1 = Error)
    """
    parser = argparse.ArgumentParser(
        description="Generate reports from Peak_Trade Live Session Registry (Phase 81).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Alle Sessions als Markdown-Report:
  python scripts/report_live_sessions.py

  # Nur Shadow-Sessions:
  python scripts/report_live_sessions.py --run-type live_session_shadow

  # Nur abgeschlossene Sessions:
  python scripts/report_live_sessions.py --status completed

  # Limit auf letzte 10 Sessions:
  python scripts/report_live_sessions.py --limit 10

  # HTML-Report generieren:
  python scripts/report_live_sessions.py --output-format html

  # Nur Summary:
  python scripts/report_live_sessions.py --summary-only

  # Report nach stdout:
  python scripts/report_live_sessions.py --stdout
        """,
    )

    # Filter-Optionen
    parser.add_argument(
        "--run-type",
        type=str,
        default=None,
        help="Filter nach Run-Type (z.B. live_session_shadow, live_session_testnet)",
    )
    parser.add_argument(
        "--status",
        type=str,
        default=None,
        help="Filter nach Status (z.B. completed, failed, aborted)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit auf N neueste Sessions",
    )

    # Output-Optionen
    parser.add_argument(
        "--output-format",
        type=str,
        default="markdown",
        choices=["markdown", "html", "both"],
        help="Output-Format: markdown, html, oder both (default: markdown)",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Nur Summary generieren (keine Einzel-Session-Reports)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Verzeichnis fuer Output-Dateien (default: reports/experiments/live_sessions/)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Report nach stdout ausgeben (keine Datei schreiben)",
    )

    # Read-only evidence pointers (post-session / reconstruction)
    parser.add_argument(
        "--evidence-pointers",
        action="store_true",
        help=(
            "Read-only: print registry + session-scoped execution_events.jsonl paths "
            "(use with --session-id or --latest-bounded-pilot)"
        ),
    )
    parser.add_argument(
        "--session-id",
        type=str,
        default=None,
        help="Session id for --evidence-pointers",
    )
    parser.add_argument(
        "--latest-bounded-pilot",
        action="store_true",
        help="Use newest registry entry with mode=bounded_pilot for --evidence-pointers",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help=(
            "JSON output for --evidence-pointers, --open-sessions, "
            "--bounded-pilot-readiness-summary, --bounded-pilot-closeout-status-summary, "
            "--bounded-pilot-operator-overview, --bounded-pilot-gate-index, "
            "--bounded-pilot-first-live-frontdoor, --bounded-pilot-lifecycle-consistency, "
            "--session-review-pack, or --pre-live-package-status"
        ),
    )
    parser.add_argument(
        "--registry-base",
        type=str,
        default=None,
        help=(
            "Override live session registry directory "
            "(default: reports/experiments/live_sessions; used by read-only subcommands)"
        ),
    )

    # Read-only open sessions (registry status=started)
    parser.add_argument(
        "--open-sessions",
        action="store_true",
        help="Read-only: list registry artifacts with status=started (operator: OPEN)",
    )
    parser.add_argument(
        "--bounded-pilot-only",
        action="store_true",
        dest="bounded_pilot_only",
        help="With --open-sessions: only rows where mode=bounded_pilot",
    )
    parser.add_argument(
        "--latest-bounded-pilot-open",
        action="store_true",
        dest="latest_bounded_pilot_open",
        help=(
            "With --open-sessions: single newest started row with mode=bounded_pilot "
            "(by started_at)"
        ),
    )

    # Bounded-pilot readiness + packet + registry focus (read-only)
    parser.add_argument(
        "--bounded-pilot-readiness-summary",
        action="store_true",
        help=(
            "Read-only: current bounded_pilot readiness + operator preflight packet "
            "+ registry session focus in one view"
        ),
    )
    parser.add_argument(
        "--bounded-pilot-closeout-status-summary",
        action="store_true",
        help=(
            "Read-only: bounded_pilot registry closeout/final-status + pointers "
            "(reuses session-focus selection; no readiness/packet evaluation)"
        ),
    )
    parser.add_argument(
        "--bounded-pilot-operator-overview",
        action="store_true",
        help=(
            "Read-only: readiness + preflight packet + session focus + closeout signals in one view"
        ),
    )
    parser.add_argument(
        "--bounded-pilot-gate-index",
        action="store_true",
        dest="bounded_pilot_gate_index",
        help=(
            "Read-only: gate/enablement index plus full overview context "
            "(readiness, packet, session focus, closeout)"
        ),
    )
    parser.add_argument(
        "--bounded-pilot-first-live-frontdoor",
        action="store_true",
        dest="bounded_pilot_first_live_frontdoor",
        help=(
            "Read-only: bounded_pilot / first-live operator frontdoor "
            "(overview + gate index + canonical CLI hints for sub-views)"
        ),
    )
    parser.add_argument(
        "--bounded-pilot-lifecycle-consistency",
        action="store_true",
        dest="bounded_pilot_lifecycle_consistency",
        help=(
            "Read-only: bounded_pilot lifecycle/handoff consistency from registry + closeout "
            "(no readiness/packet run)"
        ),
    )
    parser.add_argument(
        "--session-review-pack",
        action="store_true",
        dest="session_review_pack",
        help=(
            "Read-only: Session Review Pack V0 (non-authorizing post-hoc review bundle; "
            "use with --json; see docs/ops/specs/MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md)"
        ),
    )
    parser.add_argument(
        "--pre-live-package-status",
        action="store_true",
        dest="pre_live_package_status",
        help=(
            "Read-only: Pre-Live package status gap summary (bounded_pilot registry + closeout posture; "
            "use with --json; v0 excludes readiness/preflight/cockpit evaluation)"
        ),
    )
    parser.add_argument(
        "--config-path",
        type=str,
        default=None,
        help=(
            "Optional config.toml for --bounded-pilot-readiness-summary / "
            "--bounded-pilot-operator-overview / --bounded-pilot-gate-index / "
            "--bounded-pilot-first-live-frontdoor (else env/default)"
        ),
    )

    # Logging
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log-Level (default: INFO)",
    )

    args = parser.parse_args()

    # Logging setup
    logger = setup_logging(args.log_level)

    _mode_n = (
        int(bool(args.bounded_pilot_readiness_summary))
        + int(bool(args.bounded_pilot_closeout_status_summary))
        + int(bool(args.bounded_pilot_operator_overview))
        + int(bool(args.bounded_pilot_gate_index))
        + int(bool(args.bounded_pilot_first_live_frontdoor))
        + int(bool(args.bounded_pilot_lifecycle_consistency))
        + int(bool(args.evidence_pointers))
        + int(bool(args.open_sessions))
        + int(bool(args.session_review_pack))
        + int(bool(args.pre_live_package_status))
    )
    if _mode_n > 1:
        print(
            "ERR: use only one of --bounded-pilot-readiness-summary, "
            "--bounded-pilot-closeout-status-summary, --bounded-pilot-operator-overview, "
            "--bounded-pilot-gate-index, --bounded-pilot-first-live-frontdoor, "
            "--bounded-pilot-lifecycle-consistency, "
            "--evidence-pointers, --open-sessions, --session-review-pack, "
            "--pre-live-package-status",
            file=sys.stderr,
        )
        return 2

    if args.pre_live_package_status:
        conflict = _pre_live_package_status_flag_conflicts(args)
        if conflict is not None:
            print(f"ERR: {conflict}", file=sys.stderr)
            return 2
        return _run_pre_live_package_status(args, logger)

    if args.session_review_pack:
        conflict = _session_review_pack_flag_conflicts(args)
        if conflict is not None:
            print(f"ERR: {conflict}", file=sys.stderr)
            return 2
        return _run_session_review_pack(args, logger)

    if args.bounded_pilot_readiness_summary:
        conflict = _bounded_pilot_readiness_summary_flag_conflicts(args)
        if conflict is not None:
            print(f"ERR: {conflict}", file=sys.stderr)
            return 2
        return _run_bounded_pilot_readiness_summary(args, logger)

    if args.bounded_pilot_operator_overview:
        conflict = _bounded_pilot_operator_overview_flag_conflicts(args)
        if conflict is not None:
            print(f"ERR: {conflict}", file=sys.stderr)
            return 2
        return _run_bounded_pilot_operator_overview(args, logger)

    if args.bounded_pilot_gate_index:
        conflict = _bounded_pilot_gate_index_flag_conflicts(args)
        if conflict is not None:
            print(f"ERR: {conflict}", file=sys.stderr)
            return 2
        return _run_bounded_pilot_gate_index(args, logger)

    if args.bounded_pilot_first_live_frontdoor:
        conflict = _bounded_pilot_first_live_frontdoor_flag_conflicts(args)
        if conflict is not None:
            print(f"ERR: {conflict}", file=sys.stderr)
            return 2
        return _run_bounded_pilot_first_live_frontdoor(args, logger)

    if args.bounded_pilot_lifecycle_consistency:
        conflict = _bounded_pilot_lifecycle_consistency_flag_conflicts(args)
        if conflict is not None:
            print(f"ERR: {conflict}", file=sys.stderr)
            return 2
        return _run_bounded_pilot_lifecycle_consistency(args, logger)

    if args.bounded_pilot_closeout_status_summary:
        conflict = _bounded_pilot_closeout_status_summary_flag_conflicts(args)
        if conflict is not None:
            print(f"ERR: {conflict}", file=sys.stderr)
            return 2
        return _run_bounded_pilot_closeout_status_summary(args, logger)

    if args.evidence_pointers and args.open_sessions:
        print(
            "ERR: use either --evidence-pointers or --open-sessions, not both",
            file=sys.stderr,
        )
        return 2

    if args.open_sessions:
        if args.session_id is not None:
            print(
                "ERR: --session-id applies only to --evidence-pointers",
                file=sys.stderr,
            )
            return 2
        if args.latest_bounded_pilot:
            print(
                "ERR: --latest-bounded-pilot applies only to --evidence-pointers; "
                "use --latest-bounded-pilot-open with --open-sessions",
                file=sys.stderr,
            )
            return 2
        return _run_open_sessions(args, logger)

    if args.evidence_pointers:
        if args.session_id and args.latest_bounded_pilot:
            print(
                "ERR: use either --session-id or --latest-bounded-pilot, not both",
                file=sys.stderr,
            )
            return 2
        if not args.session_id and not args.latest_bounded_pilot:
            print(
                "ERR: --evidence-pointers requires --session-id or --latest-bounded-pilot",
                file=sys.stderr,
            )
            return 2
        return _run_evidence_pointers(args, logger)

    # Imports hier um Startup-Zeit zu optimieren
    from src.experiments.live_session_registry import (
        list_session_records,
        get_session_summary,
        render_sessions_markdown,
        render_sessions_html,
        DEFAULT_LIVE_SESSION_DIR,
    )

    logger.info("=" * 60)
    logger.info("Peak_Trade: Live Session Registry Report (Phase 81)")
    logger.info("=" * 60)

    # Output-Verzeichnis bestimmen
    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_LIVE_SESSION_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sessions laden
    logger.info("Lade Sessions aus Registry...")
    logger.info(f"  Filter: run_type={args.run_type}, status={args.status}, limit={args.limit}")

    records = list_session_records(
        run_type=args.run_type,
        status=args.status,
        limit=args.limit,
    )

    logger.info(f"  {len(records)} Sessions gefunden")

    # Keine Sessions gefunden?
    if not records:
        msg = "Keine Sessions gefunden mit den angegebenen Filtern."
        logger.warning(msg)

        if args.stdout:
            print(f"\n{msg}\n")
        else:
            # Leeren Report schreiben
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
            if args.output_format in ("markdown", "both"):
                empty_md = f"# Live-Session Report\n\n{msg}\n"
                md_path = output_dir / f"{timestamp}_sessions_report.md"
                md_path.write_text(empty_md, encoding="utf-8")
                logger.info(f"Leerer Report geschrieben: {md_path}")

        return 0

    # Summary generieren?
    if args.summary_only:
        logger.info("Generiere Summary...")
        summary = get_session_summary(run_type=args.run_type)

        if args.stdout:
            if args.output_format in ("markdown", "both"):
                print(format_summary_markdown(summary))
            if args.output_format == "html":
                print(format_summary_html(summary))
        else:
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
            if args.output_format in ("markdown", "both"):
                md_content = format_summary_markdown(summary)
                md_path = output_dir / f"{timestamp}_sessions_summary.md"
                md_path.write_text(md_content, encoding="utf-8")
                logger.info(f"Summary (Markdown) geschrieben: {md_path}")

            if args.output_format in ("html", "both"):
                html_content = format_summary_html(summary)
                html_path = output_dir / f"{timestamp}_sessions_summary.html"
                html_path.write_text(html_content, encoding="utf-8")
                logger.info(f"Summary (HTML) geschrieben: {html_path}")

        return 0

    # Vollstaendige Reports generieren
    logger.info("Generiere Reports...")

    if args.stdout:
        if args.output_format in ("markdown", "both"):
            md_content = render_sessions_markdown(records)
            print(md_content)
        if args.output_format == "html":
            html_content = render_sessions_html(records)
            print(html_content)
    else:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

        if args.output_format in ("markdown", "both"):
            md_content = render_sessions_markdown(records)
            md_path = output_dir / f"{timestamp}_sessions_report.md"
            md_path.write_text(md_content, encoding="utf-8")
            logger.info(f"Report (Markdown) geschrieben: {md_path}")
            print(f"Markdown-Report: {md_path}")

        if args.output_format in ("html", "both"):
            html_content = render_sessions_html(records)
            html_path = output_dir / f"{timestamp}_sessions_report.html"
            html_path.write_text(html_content, encoding="utf-8")
            logger.info(f"Report (HTML) geschrieben: {html_path}")
            print(f"HTML-Report: {html_path}")

    logger.info("=" * 60)
    logger.info("Report-Generierung abgeschlossen")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
