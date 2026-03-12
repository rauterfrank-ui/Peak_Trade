from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class TruthDoc:
    key: str
    title: str
    path: str
    summary: str
    priority: str


TRUTH_DOCS: List[TruthDoc] = [
    TruthDoc(
        key="ai_layer_canonical_spec",
        title="AI Layer Canonical Spec v1",
        path="docs/governance/ai/AI_LAYER_CANONICAL_SPEC_V1.md",
        summary="Canonical AI layer truth and authority boundaries.",
        priority="canonical_boundary",
    ),
    TruthDoc(
        key="critic_proposer_boundary",
        title="Critic / Proposer Boundary Spec v1",
        path="docs/governance/ai/CRITIC_PROPOSER_BOUNDARY_SPEC_V1.md",
        summary="Separates advisory proposer from supervisory critic.",
        priority="canonical_boundary",
    ),
    TruthDoc(
        key="provider_model_binding",
        title="Provider / Model Binding Spec v1",
        path="docs/governance/ai/PROVIDER_MODEL_BINDING_SPEC_V1.md",
        summary="Binding references do not imply runtime or execution authority.",
        priority="canonical_boundary",
    ),
    TruthDoc(
        key="execution_adjacent_boundary",
        title="Execution-Adjacent AI Boundary Spec v1",
        path="docs/governance/ai/EXECUTION_ADJACENT_AI_BOUNDARY_SPEC_V1.md",
        summary="Separates AI-adjacent, execution-adjacent, and execution-authoritative.",
        priority="canonical_boundary",
    ),
    TruthDoc(
        key="runtime_unknown_resolution",
        title="Runtime Unknown Resolution v1",
        path="docs/governance/ai/RUNTIME_UNKNOWN_RESOLUTION_V1.md",
        summary="Repo-near runtime unknown consolidation.",
        priority="runtime_resolution",
    ),
    TruthDoc(
        key="critic_runtime_resolution",
        title="Critic Runtime Resolution v2",
        path="docs/governance/ai/CRITIC_RUNTIME_RESOLUTION_V2.md",
        summary="Critic is runtime-near, supervisory, and not final trade authority.",
        priority="runtime_resolution",
    ),
    TruthDoc(
        key="proposer_runtime_resolution",
        title="Proposer Runtime Resolution v1",
        path="docs/governance/ai/PROPOSER_RUNTIME_RESOLUTION_V1.md",
        summary="Proposer remains advisory and weaker in runtime evidence than critic.",
        priority="runtime_resolution",
    ),
    TruthDoc(
        key="ai_unknown_reduction",
        title="AI Unknown Reduction v1",
        path="docs/governance/ai/AI_UNKNOWN_REDUCTION_V1.md",
        summary="Clarifies unresolved layer/runtime slots without invention.",
        priority="supporting_truth",
    ),
]


PRIORITY_ORDER = {
    "canonical_boundary": 0,
    "runtime_resolution": 1,
    "supporting_truth": 2,
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _read_text_if_exists(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="ignore")


def _first_nonempty_lines(text: str, limit: int = 6) -> List[str]:
    out: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        out.append(stripped)
        if len(out) >= limit:
            break
    return out


def _coverage_label(available_count: int, total_count: int) -> str:
    if total_count <= 0:
        return "no_truth_sources"
    ratio = available_count / total_count
    if ratio >= 0.95:
        return "high"
    if ratio >= 0.60:
        return "partial"
    return "low"


def _priority_counts(truth_docs: List[Dict[str, object]]) -> Dict[str, int]:
    counts = {"canonical_boundary": 0, "runtime_resolution": 0, "supporting_truth": 0}
    for doc in truth_docs:
        priority = str(doc["priority"])
        counts[priority] = counts.get(priority, 0) + 1
    return counts


def _freshness_label(path: Path) -> str:
    if not path.exists():
        return "unavailable"
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    age_hours = (_utc_now() - modified).total_seconds() / 3600
    if age_hours <= 24:
        return "fresh"
    if age_hours <= 24 * 7:
        return "stale"
    return "older"


def _iso_mtime(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return modified.isoformat()


def discover_truth_docs(repo_root: Path | None = None) -> List[Dict[str, object]]:
    root = repo_root or Path.cwd()
    docs: List[Dict[str, object]] = []
    for doc in TRUTH_DOCS:
        full_path = root / doc.path
        text = _read_text_if_exists(full_path)
        exists = text is not None
        preview = _first_nonempty_lines(text) if text else []
        docs.append(
            {
                "key": doc.key,
                "title": doc.title,
                "path": doc.path,
                "summary": doc.summary,
                "exists": exists,
                "preview": preview,
                "status": "available" if exists else "unavailable",
                "priority": doc.priority,
                "priority_rank": PRIORITY_ORDER.get(doc.priority, 99),
                "freshness": _freshness_label(full_path),
                "last_modified_utc": _iso_mtime(full_path),
            }
        )
    docs.sort(key=lambda d: (int(d["priority_rank"]), str(d["title"])))
    return docs


def build_truth_state(truth_docs: List[Dict[str, object]]) -> Dict[str, object]:
    available = [d for d in truth_docs if d["exists"]]
    unavailable = [d for d in truth_docs if not d["exists"]]
    return {
        "available_count": len(available),
        "unavailable_count": len(unavailable),
        "truth_first_positioning": "enabled",
        "truth_coverage": _coverage_label(len(available), len(truth_docs)),
        "priority_counts": _priority_counts(truth_docs),
        "final_trade_authority": "not_evidenced_as_model_final",
        "live_autonomy": "not_evidenced_as_self_improving_live",
        "last_verified_utc": _utc_now().isoformat(),
    }


def build_ai_boundary_state() -> Dict[str, object]:
    return {
        "proposer_authority": "advisory_only",
        "critic_authority": "supervisory_only",
        "provider_binding_authority": "not_execution_authority",
        "execution_boundary": "deterministic_gated",
        "closest_to_trade": "not_evidenced_as_llm_final",
    }


def build_runtime_unknown_state() -> Dict[str, object]:
    return {
        "critic_runtime_path": "partial",
        "proposer_runtime_path": "partial_or_unknown",
        "provider_model_runtime_slots": "partial_or_unknown",
        "execution_adjacent_contracts": "documented_without_overclaiming",
    }


def _grouped_sources(truth_docs: List[Dict[str, object]]) -> Dict[str, List[Dict[str, object]]]:
    grouped: Dict[str, List[Dict[str, object]]] = {
        "canonical_boundary": [],
        "runtime_resolution": [],
        "supporting_truth": [],
    }
    for doc in truth_docs:
        grouped.setdefault(str(doc["priority"]), []).append(doc)
    return grouped


def _group_summary(group_docs: List[Dict[str, object]]) -> Dict[str, int]:
    summary = {
        "total": len(group_docs),
        "available": 0,
        "unavailable": 0,
        "fresh": 0,
        "stale": 0,
        "older": 0,
    }
    for doc in group_docs:
        if doc["exists"]:
            summary["available"] += 1
        else:
            summary["unavailable"] += 1
        freshness = str(doc["freshness"])
        if freshness in ("fresh", "stale", "older"):
            summary[freshness] += 1
    return summary


def _status_obj(level: str, label: str, detail: str) -> Dict[str, object]:
    """Build status object with level, label, detail. Defensive."""
    return {"level": level, "label": label, "detail": detail}


def _build_v3_executive_summary(
    truth_state: Dict[str, object],
    source_group_summary: Dict[str, Dict[str, int]],
) -> Dict[str, object]:
    """Build v3 executive summary with nested status objects. Read-only, defensive defaults."""
    coverage = str(truth_state.get("truth_coverage", "unknown"))
    available = int(truth_state.get("available_count", 0))
    unavailable = int(truth_state.get("unavailable_count", 0))
    total = available + unavailable
    truth_posture = str(truth_state.get("truth_first_positioning", "enabled"))

    # Heuristic: ok | warn | critical | unknown
    # truth_status
    if coverage == "high":
        truth_status = _status_obj("ok", "high", "Truth-first, read-only. Source groups present.")
    elif coverage == "partial":
        truth_status = _status_obj(
            "warn", "partial", "Partial source coverage. Review missing anchors."
        )
    elif coverage == "no_truth_sources":
        truth_status = _status_obj(
            "critical", "no_truth_sources", "No truth sources found. Unknown state."
        )
    else:
        truth_status = _status_obj(
            "critical", "low", "Low truth coverage. Missing canonical anchors."
        )

    # freshness_status
    total_stale = 0
    total_older = 0
    for s in (source_group_summary or {}).values():
        if isinstance(s, dict):
            total_stale += int(s.get("stale", 0))
            total_older += int(s.get("older", 0))
    if total_older > 0:
        freshness_status = _status_obj(
            "critical", "older", "Sources older than 7 days. Stale evidence."
        )
    elif total_stale > 0:
        freshness_status = _status_obj(
            "warn", "stale", "Some sources stale (≤7d). Partial freshness."
        )
    elif available == 0 and total > 0:
        freshness_status = _status_obj(
            "unknown", "unknown", "No available sources. Unresolved state."
        )
    else:
        freshness_status = _status_obj("ok", "fresh", "Sources fresh (≤24h). Evidence current.")

    # source_coverage_status
    if coverage == "high":
        source_status = _status_obj("ok", "high", f"{available}/{total} sources available.")
    elif coverage == "partial":
        source_status = _status_obj(
            "warn", "partial", f"{available}/{total} sources. Partial coverage."
        )
    elif coverage == "no_truth_sources":
        source_status = _status_obj("critical", "no_truth_sources", "No truth sources. No data.")
    else:
        source_status = _status_obj(
            "critical", "low", f"{available}/{total} sources. Low coverage."
        )

    # critical_flags / unknown_flags
    critical_flags: List[str] = []
    unknown_flags: List[str] = []
    if coverage in ("low", "no_truth_sources"):
        critical_flags.append("low_truth_coverage")
    if total_older > 0:
        critical_flags.append("older_sources")
    if total_stale > 0:
        critical_flags.append("stale_sources")
    if unavailable > 0:
        unknown_flags.append("unavailable_sources")

    executive_summary: Dict[str, object] = {
        "mode": "truth_first_ops_cockpit_v3",
        "truth_posture": truth_posture,
        "truth_status": truth_status,
        "freshness_status": freshness_status,
        "source_coverage_status": source_status,
        "critical_flags": critical_flags,
        "unknown_flags": unknown_flags,
    }

    # Flat keys for backward compatibility (additive, nicht umbenennen)
    return {
        "executive_summary": executive_summary,
        "truth_status": truth_status["level"],
        "freshness_status": freshness_status["level"],
        "source_coverage_status": source_status["level"],
        "critical_flags": critical_flags,
        "unknown_flags": unknown_flags,
    }


def build_ops_cockpit_payload(repo_root: Path | None = None) -> Dict[str, object]:
    truth_docs = discover_truth_docs(repo_root=repo_root)
    groups = _grouped_sources(truth_docs)
    group_summaries = {name: _group_summary(items) for name, items in groups.items()}
    truth_state = build_truth_state(truth_docs)
    v3_summary = _build_v3_executive_summary(truth_state, group_summaries)
    guard_state = {
        "no_trade_baseline": "reference",
        "deny_by_default": "active",
        "treasury_separation": "enforced",
        "enabled": False,
        "armed": False,
        "dry_run": True,
        "confirm_token_required": True,
        "kill_switch_active": False,
    }
    policy_state = {
        "action": "NO_TRADE",
        "confirm_token_required": guard_state["confirm_token_required"],
        "enabled": guard_state["enabled"],
        "armed": guard_state["armed"],
        "dry_run": guard_state["dry_run"],
        "blocked": (not guard_state["enabled"]) or (not guard_state["armed"]),
        "summary": (
            "blocked" if (not guard_state["enabled"] or not guard_state["armed"]) else "armed"
        ),
    }
    operator_state = {
        "disabled": not guard_state["enabled"],
        "enabled": guard_state["enabled"],
        "armed": guard_state["armed"],
        "dry_run": guard_state["dry_run"],
        "blocked": (not guard_state["enabled"]) or (not guard_state["armed"]),
        "kill_switch_active": guard_state["kill_switch_active"],
    }
    return {
        "system_state": {
            "mode": "truth_first_ops_cockpit_v3",
            "execution_model": "guarded_execution",
        },
        "guard_state": {
            "no_trade_baseline": guard_state["no_trade_baseline"],
            "deny_by_default": guard_state["deny_by_default"],
            "treasury_separation": guard_state["treasury_separation"],
        },
        "policy_state": policy_state,
        "operator_state": operator_state,
        "truth_state": truth_state,
        "ai_boundary_state": build_ai_boundary_state(),
        "runtime_unknown_state": build_runtime_unknown_state(),
        "source_groups": groups,
        "source_group_summary": group_summaries,
        "canonical_sources": truth_docs,
        "executive_summary": v3_summary["executive_summary"],
        "truth_status": v3_summary["truth_status"],
        "freshness_status": v3_summary["freshness_status"],
        "source_coverage_status": v3_summary["source_coverage_status"],
        "critical_flags": v3_summary["critical_flags"],
        "unknown_flags": v3_summary["unknown_flags"],
    }


def _render_doc_card(doc: Dict[str, object]) -> str:
    preview_items = "".join(f"<li>{escape(str(line))}</li>" for line in doc["preview"])
    preview_html = (
        f"<ul>{preview_items}</ul>" if preview_items else "<p>No preview (read-only).</p>"
    )
    return (
        '<div class="card truth-card">'
        f"<h3>{escape(str(doc['title']))}</h3>"
        f'<p><strong>Status:</strong> <span class="chip"><code>{escape(str(doc["status"]))}</code></span></p>'
        f'<p><strong>Priority:</strong> <span class="chip"><code>{escape(str(doc["priority"]))}</code></span></p>'
        f'<p><strong>Freshness:</strong> <span class="chip"><code>{escape(str(doc["freshness"]))}</code></span></p>'
        f"<p><strong>Path:</strong> <code>{escape(str(doc['path']))}</code></p>"
        f"<p>{escape(str(doc['summary']))}</p>"
        f"{preview_html}"
        "</div>"
    )


def _render_group_chip(name: str, count: int) -> str:
    return f'<span class="chip"><code>{escape(name)}={count}</code></span>'


def _render_group_summary_block(name: str, summary: Dict[str, int]) -> str:
    return (
        '<div class="card">'
        f"<h3>{escape(name)}</h3>"
        f"<p><strong>Total:</strong> {summary['total']}</p>"
        f"<p><strong>Available / unavailable:</strong> {summary['available']} / {summary['unavailable']}</p>"
        f"<p><strong>Fresh / stale / older:</strong> {summary['fresh']} / {summary['stale']} / {summary['older']}</p>"
        "</div>"
    )


def _status_badge_class(status: str) -> str:
    """Map status/level to CSS modifier. unknown/stale/no-data stronger than ok."""
    if status in ("critical", "no_truth_sources"):
        return "status-badge--critical"
    if status in ("warn", "low", "stale", "older", "partial"):
        return "status-badge--warn"
    if status in ("unknown", "unavailable"):
        return "status-badge--unknown"
    return "status-badge--ok"


def _render_exec_summary_status_grid(payload: Dict[str, object]) -> str:
    """Render compact v3 Executive Summary. 4 status cards, flags only if present. Read-only."""
    exec_sum = payload.get("executive_summary") or {}
    t_obj = exec_sum.get("truth_status") or {}
    f_obj = exec_sum.get("freshness_status") or {}
    s_obj = exec_sum.get("source_coverage_status") or {}
    truth_level = str(t_obj.get("level", payload.get("truth_status", "unknown")))
    freshness_level = str(f_obj.get("level", payload.get("freshness_status", "unknown")))
    source_level = str(s_obj.get("level", payload.get("source_coverage_status", "unknown")))
    truth_label = str(t_obj.get("label", truth_level))
    freshness_label = str(f_obj.get("label", freshness_level))
    source_label = str(s_obj.get("label", source_level))
    truth_detail = str(t_obj.get("detail", ""))
    freshness_detail = str(f_obj.get("detail", ""))
    source_detail = str(s_obj.get("detail", ""))
    sys_state = payload.get("system_state") or {}
    mode = str(sys_state.get("mode", "unknown"))
    critical = payload.get("critical_flags") or []
    unknown = payload.get("unknown_flags") or []

    t_class = _status_badge_class(truth_level)
    f_class = _status_badge_class(freshness_level)
    s_class = _status_badge_class(source_level)
    mode_class = "status-badge--ok" if mode != "unknown" else "status-badge--unknown"

    def _card(label: str, badge_class: str, value: str, detail: str) -> str:
        d = f'<p class="status-detail">{escape(detail)}</p>' if detail else ""
        return (
            f'<div class="status-card">'
            f'<span class="status-label">{escape(label)}</span> '
            f'<span class="status-badge {badge_class} status-value">{escape(value)}</span>'
            f"{d}"
            "</div>"
        )

    mode_detail = "" if mode != "unknown" else "Unknown state."
    cards = (
        _card("Mode", mode_class, mode, mode_detail),
        _card("Truth", t_class, truth_label, truth_detail),
        _card("Freshness", f_class, freshness_label, freshness_detail),
        _card("Sources", s_class, source_label, source_detail),
    )

    flags_html = ""
    if critical or unknown:
        parts = []
        if critical:
            parts.append(
                f'<span class="status-badge status-badge--critical">Critical: {", ".join(escape(str(f)) for f in critical)}</span>'
            )
        if unknown:
            parts.append(
                f'<span class="status-badge status-badge--unknown">Unknown: {", ".join(escape(str(f)) for f in unknown)}</span>'
            )
        flags_html = f'<p class="status-flags">{" ".join(parts)}</p>'

    return (
        '<div class="exec-summary">'
        "<h2>Executive Summary</h2>"
        "<p><strong>Read-only.</strong> No write actions. Operator snapshot.</p>"
        '<div class="status-grid">'
        f"{''.join(cards)}"
        "</div>"
        '<p class="status-attribution"><strong>Sources:</strong> operator snapshot, system state, truth sections</p>'
        f"{flags_html}"
        "</div>"
    )


def render_ops_cockpit_html(repo_root: Path | None = None) -> str:
    payload = build_ops_cockpit_payload(repo_root=repo_root)
    truth_state = payload["truth_state"]
    boundary = payload["ai_boundary_state"]
    runtime = payload["runtime_unknown_state"]
    counts = truth_state["priority_counts"]
    groups = payload["source_groups"]
    summaries = payload["source_group_summary"]

    group_chips = " ".join(
        [
            _render_group_chip("canonical_boundary", len(groups["canonical_boundary"])),
            _render_group_chip("runtime_resolution", len(groups["runtime_resolution"])),
            _render_group_chip("supporting_truth", len(groups["supporting_truth"])),
        ]
    )

    summary_blocks = "".join(
        [
            _render_group_summary_block("canonical_boundary", summaries["canonical_boundary"]),
            _render_group_summary_block("runtime_resolution", summaries["runtime_resolution"]),
            _render_group_summary_block("supporting_truth", summaries["supporting_truth"]),
        ]
    )

    canonical_cards = "".join(_render_doc_card(doc) for doc in groups["canonical_boundary"])
    runtime_cards = "".join(_render_doc_card(doc) for doc in groups["runtime_resolution"])
    supporting_cards = "".join(_render_doc_card(doc) for doc in groups["supporting_truth"])
    exec_summary_html = _render_exec_summary_status_grid(payload)

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Peak_Trade Ops Cockpit v3</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }}
    .card {{ border: 1px solid #ddd; border-radius: 12px; padding: 16px; }}
    .hero {{ border: 1px solid #ddd; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
    .truth-card {{ border-left: 6px solid #6b8e6b; }}
    .priority-inline {{ display: inline-block; margin-right: 10px; }}
    .legend {{ border: 1px solid #ddd; border-radius: 12px; padding: 14px; margin-bottom: 20px; }}
    .chip {{ display: inline-block; margin-left: 4px; margin-right: 6px; }}
    .group-block {{ margin-top: 22px; }}
    code {{ background: #f5f5f5; padding: 2px 4px; border-radius: 4px; }}
    .exec-summary {{ border: 1px solid #333; border-radius: 12px; padding: 16px; margin-bottom: 20px; background: #fafafa; }}
    .status-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin: 12px 0; }}
    .status-card {{ padding: 10px; border-radius: 8px; border: 1px solid #e0e0e0; }}
    .status-label {{ display: block; font-size: 0.85em; color: #555; margin-bottom: 4px; }}
    .status-value {{ margin-left: 0; }}
    .status-detail {{ font-size: 0.8em; color: #666; margin: 6px 0 0 0; line-height: 1.3; }}
    .status-attribution {{ font-size: 0.85em; color: #555; margin-top: 12px; }}
    .status-flags {{ margin-top: 12px; }}
    .status-badge {{ display: inline-block; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.9em; }}
    .status-badge--critical {{ background: #d32f2f; color: #fff; }}
    .status-badge--warn {{ background: #f57c00; color: #fff; }}
    .status-badge--ok {{ background: #388e3c; color: #fff; }}
    .status-badge--unknown {{ background: #616161; color: #fff; }}
  </style>
</head>
<body>
  {exec_summary_html}
  <div class="hero">
    <h1>Ops Cockpit v3 — Truth-First</h1>
    <p>Read-only. No write actions.</p>
    <p>Read-only operations cockpit aligned to the current canonical truth model.</p>
    <p><strong>Last verified:</strong> {escape(str(truth_state["last_verified_utc"]))}</p>
    <p><strong>Truth coverage:</strong> {escape(str(truth_state["truth_coverage"]))}</p>
    <p><strong>Available / unavailable:</strong> {escape(str(truth_state["available_count"]))} / {escape(str(truth_state["unavailable_count"]))}</p>
    <p>
      <span class="priority-inline"><strong>canonical</strong>={escape(str(counts["canonical_boundary"]))}</span>
      <span class="priority-inline"><strong>runtime</strong>={escape(str(counts["runtime_resolution"]))}</span>
      <span class="priority-inline"><strong>supporting</strong>={escape(str(counts["supporting_truth"]))}</span>
    </p>
    <p><strong>Execution model:</strong> {escape(str(payload["system_state"]["execution_model"]))}</p>
    <p><strong>Final trade authority:</strong> {escape(str(truth_state["final_trade_authority"]))}</p>
  </div>

  <div class="legend">
    <h2>Read-only legends</h2>
    <p><strong>Visual emphasis only.</strong> No semantic or execution changes.</p>
    <p><strong>Availability:</strong> <code>available</code> = source found, <code>unavailable</code> = source missing.</p>
    <p><strong>Freshness:</strong> <code>fresh</code> ≤ 24h, <code>stale</code> ≤ 7d, <code>older</code> > 7d.</p>
    <p><strong>Source groups:</strong> {group_chips}</p>
  </div>

  <div class="group-block">
    <h2>Compact Source Summary</h2>
    <p><strong>At-a-glance grouped counts.</strong></p>
    <div class="grid">
      {summary_blocks}
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>Truth State</h2>
      <p><strong>Read-only canonical truth</strong></p>
      <p><strong>Truth-first positioning:</strong> {escape(str(truth_state["truth_first_positioning"]))}</p>
      <p><strong>Truth coverage:</strong> {escape(str(truth_state["truth_coverage"]))}</p>
      <p><strong>Live autonomy:</strong> {escape(str(truth_state["live_autonomy"]))}</p>
    </div>

    <div class="card">
      <h2>AI Boundary State</h2>
      <p><strong>Authority boundaries (read-only)</strong></p>
      <p><strong>Proposer:</strong> {escape(str(boundary["proposer_authority"]))}</p>
      <p><strong>Critic:</strong> {escape(str(boundary["critic_authority"]))}</p>
      <p><strong>Provider binding authority:</strong> {escape(str(boundary["provider_binding_authority"]))}</p>
      <p><strong>Execution boundary:</strong> {escape(str(boundary["execution_boundary"]))}</p>
      <p><strong>Closest to trade:</strong> {escape(str(boundary["closest_to_trade"]))}</p>
    </div>

    <div class="card">
      <h2>Runtime Unknown State</h2>
      <p><strong>Unknown / partial slots (read-only)</strong></p>
      <p><strong>Critic runtime path:</strong> {escape(str(runtime["critic_runtime_path"]))}</p>
      <p><strong>Proposer runtime path:</strong> {escape(str(runtime["proposer_runtime_path"]))}</p>
      <p><strong>Provider/model runtime slots:</strong> {escape(str(runtime["provider_model_runtime_slots"]))}</p>
      <p><strong>Execution-adjacent contracts:</strong> {escape(str(runtime["execution_adjacent_contracts"]))}</p>
    </div>
  </div>

  <div class="group-block">
    <h2>Canonical Boundary Sources</h2>
    <p><strong>Highest-priority canonical boundary references.</strong></p>
    <div class="grid">
      {canonical_cards}
    </div>
  </div>

  <div class="group-block">
    <h2>Runtime Resolution Sources</h2>
    <p><strong>Runtime-near clarifications and partial resolutions.</strong></p>
    <div class="grid">
      {runtime_cards}
    </div>
  </div>

  <div class="group-block">
    <h2>Supporting Truth Sources</h2>
    <p><strong>Supporting context with lower direct authority weight.</strong></p>
    <div class="grid">
      {supporting_cards}
    </div>
  </div>
</body>
</html>"""


__all__ = [
    "TRUTH_DOCS",
    "discover_truth_docs",
    "build_truth_state",
    "build_ai_boundary_state",
    "build_runtime_unknown_state",
    "build_ops_cockpit_payload",
    "render_ops_cockpit_html",
]
