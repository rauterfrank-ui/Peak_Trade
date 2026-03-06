"""Peak_Trade Ops Cockpit — read-only artifact discovery and rendering."""

from __future__ import annotations

import html
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


OPS_ROOT = Path("out/ops")


@dataclass(frozen=True)
class ArtifactRef:
    label: str
    path: str
    exists: bool


def _latest_dir(pattern: str) -> Path | None:
    matches = [p for p in OPS_ROOT.glob(pattern) if p.is_dir()]
    if not matches:
        return None
    return sorted(matches)[-1]


def _latest_incident_snapshot_dir() -> Path | None:
    """Latest incident snapshot dir, excluding incident_stop."""
    matches = [
        p
        for p in OPS_ROOT.glob("incident_*")
        if p.is_dir() and not p.name.startswith("incident_stop")
    ]
    if not matches:
        return None
    return sorted(matches)[-1]


def _latest_file(root: Path | None, glob_pattern: str) -> Path | None:
    if root is None:
        return None
    matches = sorted(root.glob(glob_pattern))
    return matches[-1] if matches else None


def _safe_read_text(path: Path | None, limit: int = 4000) -> str:
    if path is None or not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def _artifact_ref(label: str, path: Path | None) -> ArtifactRef:
    if path is None:
        return ArtifactRef(label=label, path="", exists=False)
    return ArtifactRef(label=label, path=str(path), exists=path.exists())


def load_ops_cockpit_data() -> dict[str, Any]:
    guarded_exec_dir = _latest_dir("guarded_pilot_execution_*")
    guarded_run_dir = _latest_dir("guarded_pilot_run_*")
    final_go_dir = _latest_dir("final_pilot_go_no_go_*")
    testnet_impl_dir = _latest_dir("testnet_real_session_impl_*")
    incident_stop_dir = _latest_dir("incident_stop_*_abort_pilot")
    pilot_snapshot_dir = _latest_dir("pilot_ready_snapshot_*")
    incident_snapshot_dir = _latest_incident_snapshot_dir()

    guarded_exec_summary = _safe_read_text(
        _latest_file(guarded_exec_dir, "*first_guarded_pilot_execution_summary.md")
    )
    guarded_handoff = _safe_read_text(
        _latest_file(guarded_exec_dir, "*first_guarded_pilot_execution_handoff.md")
    )
    final_go_summary = _safe_read_text(
        _latest_file(final_go_dir, "*final_pilot_go_no_go_corrected.md")
    )
    testnet_impl_summary = _safe_read_text(_latest_file(testnet_impl_dir, "*impl_summary.md"))
    testnet_run_excerpt = _safe_read_text(
        (testnet_impl_dir / "05_testnet_run.txt") if testnet_impl_dir else None
    )
    incident_stop_excerpt = _safe_read_text(_latest_file(incident_stop_dir, "*.md"))
    hash_pilot = _safe_read_text(
        (pilot_snapshot_dir / "SHA256SUMS.txt") if pilot_snapshot_dir else None
    )
    hash_incident = _safe_read_text(
        (incident_snapshot_dir / "SHA256SUMS.txt") if incident_snapshot_dir else None
    )

    current_status = "UNKNOWN"
    if "GO WITH GUARDS" in guarded_exec_summary or "GO WITH GUARDS" in final_go_summary:
        current_status = "GO WITH GUARDS"

    return {
        "system_state": {
            "status": current_status,
            "latest_guarded_execution_dir": str(guarded_exec_dir) if guarded_exec_dir else "",
            "latest_guarded_run_dir": str(guarded_run_dir) if guarded_run_dir else "",
            "latest_final_go_dir": str(final_go_dir) if final_go_dir else "",
        },
        "guard_state": {
            "no_trade_baseline": True,
            "deny_by_default_expected": True,
            "treasury_separation_expected": True,
            "guarded_execution_summary_present": bool(guarded_exec_summary),
        },
        "latest_evidence": {
            "pilot_snapshot": asdict(_artifact_ref("pilot_snapshot", pilot_snapshot_dir)),
            "incident_snapshot": asdict(_artifact_ref("incident_snapshot", incident_snapshot_dir)),
            "incident_stop": asdict(_artifact_ref("incident_stop", incident_stop_dir)),
            "final_go": asdict(_artifact_ref("final_go", final_go_dir)),
            "testnet_impl": asdict(_artifact_ref("testnet_impl", testnet_impl_dir)),
        },
        "latest_testnet_pilot_status": {
            "final_go_summary_excerpt": final_go_summary,
            "testnet_impl_summary_excerpt": testnet_impl_summary,
            "testnet_run_excerpt": testnet_run_excerpt,
        },
        "incidents_abort": {
            "incident_stop_excerpt": incident_stop_excerpt,
            "guarded_handoff_excerpt": guarded_handoff,
        },
        "readiness_routing_health": {
            "guarded_exec_summary_excerpt": guarded_exec_summary,
            "pilot_hash_excerpt": hash_pilot,
            "incident_hash_excerpt": hash_incident,
        },
    }


def render_ops_cockpit_html(data: dict[str, Any]) -> str:
    def esc(value: Any) -> str:
        return html.escape(str(value))

    def card(title: str, body: str) -> str:
        return (
            f"<section style='border:1px solid #ddd;padding:12px;border-radius:8px;margin:12px 0;'>"
            f"<h2>{esc(title)}</h2>{body}</section>"
        )

    def pre_block(text: str) -> str:
        if not text:
            return "<p>Not available.</p>"
        return f"<pre style='white-space:pre-wrap;overflow:auto;'>{esc(text)}</pre>"

    system = data["system_state"]
    guards = data["guard_state"]
    evidence = data["latest_evidence"]
    status = data["latest_testnet_pilot_status"]
    incidents = data["incidents_abort"]
    readiness = data["readiness_routing_health"]

    evidence_rows = "".join(
        f"<tr><td>{esc(k)}</td><td>{esc(v['path'])}</td><td>{esc(v['exists'])}</td></tr>"
        for k, v in evidence.items()
    )

    system_body = (
        "<ul>"
        f"<li>Status: {esc(system['status'])}</li>"
        f"<li>Latest guarded execution dir: {esc(system['latest_guarded_execution_dir'])}</li>"
        f"<li>Latest guarded run dir: {esc(system['latest_guarded_run_dir'])}</li>"
        f"<li>Latest final go dir: {esc(system['latest_final_go_dir'])}</li>"
        "</ul>"
    )
    guards_body = (
        "<ul>"
        f"<li>NO_TRADE baseline expected: {esc(guards['no_trade_baseline'])}</li>"
        f"<li>deny-by-default expected: {esc(guards['deny_by_default_expected'])}</li>"
        f"<li>treasury separation expected: {esc(guards['treasury_separation_expected'])}</li>"
        f"<li>guarded execution summary present: {esc(guards['guarded_execution_summary_present'])}</li>"
        "</ul>"
    )
    evidence_body = (
        "<table border='1' cellpadding='6' cellspacing='0'>"
        "<tr><th>Artifact</th><th>Path</th><th>Exists</th></tr>"
        f"{evidence_rows}"
        "</table>"
    )
    status_body = pre_block(
        status["final_go_summary_excerpt"]
        + "\n\n"
        + status["testnet_impl_summary_excerpt"]
        + "\n\n"
        + status["testnet_run_excerpt"]
    )
    incidents_body = pre_block(
        incidents["incident_stop_excerpt"] + "\n\n" + incidents["guarded_handoff_excerpt"]
    )
    readiness_body = pre_block(
        readiness["guarded_exec_summary_excerpt"]
        + "\n\n"
        + readiness["pilot_hash_excerpt"]
        + "\n\n"
        + readiness["incident_hash_excerpt"]
    )

    html_doc = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Peak_Trade Ops Cockpit</title></head>"
        "<body style='font-family:Arial,sans-serif;max-width:1200px;margin:20px auto;padding:0 16px;'>"
        "<h1>Peak_Trade Ops Cockpit</h1>"
        "<p>Read-only operational overview from local artifacts.</p>"
        + card("System State", system_body)
        + card("Guard State", guards_body)
        + card("Latest Evidence", evidence_body)
        + card("Latest Testnet / Pilot Status", status_body)
        + card("Incidents / Abort", incidents_body)
        + card("Readiness / Routing / Health Summary", readiness_body)
        + "</body></html>"
    )
    return html_doc


def render_ops_cockpit_json() -> dict[str, Any]:
    return load_ops_cockpit_data()
