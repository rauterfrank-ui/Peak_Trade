from __future__ import annotations

import time
from dataclasses import dataclass
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


def _freshness_label(mtime_sec: Optional[float]) -> str:
    """fresh ≤24h, stale ≤7d, older >7d."""
    if mtime_sec is None:
        return "unknown"
    age_sec = time.time() - mtime_sec
    if age_sec <= 86400:  # 24h
        return "fresh"
    if age_sec <= 604800:  # 7d
        return "stale"
    return "older"


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


def discover_truth_docs(repo_root: Path | None = None) -> List[Dict[str, object]]:
    root = repo_root or Path.cwd()
    docs: List[Dict[str, object]] = []
    for doc in TRUTH_DOCS:
        full_path = root / doc.path
        text = _read_text_if_exists(full_path)
        exists = text is not None
        preview = _first_nonempty_lines(text) if text else []
        mtime: Optional[float] = None
        if full_path.exists():
            try:
                mtime = full_path.stat().st_mtime
            except OSError:
                pass
        freshness = _freshness_label(mtime) if exists else "unknown"
        last_modified_utc = (
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(mtime)) if mtime is not None else None
        )
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
                "freshness": freshness,
                "last_modified_utc": last_modified_utc,
            }
        )
    docs.sort(key=lambda d: (int(d["priority_rank"]), str(d["title"])))
    return docs


def build_truth_state(truth_docs: List[Dict[str, object]]) -> Dict[str, object]:
    available = [d for d in truth_docs if d["exists"]]
    unavailable = [d for d in truth_docs if not d["exists"]]
    last_utcs = [d["last_modified_utc"] for d in available if d.get("last_modified_utc")]
    last_verified_utc = max(last_utcs) if last_utcs else None
    return {
        "available_count": len(available),
        "unavailable_count": len(unavailable),
        "truth_first_positioning": "enabled",
        "truth_coverage": _coverage_label(len(available), len(truth_docs)),
        "priority_counts": _priority_counts(truth_docs),
        "final_trade_authority": "not_evidenced_as_model_final",
        "live_autonomy": "not_evidenced_as_self_improving_live",
        "last_verified_utc": last_verified_utc or "—",
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


def build_ops_cockpit_payload(repo_root: Path | None = None) -> Dict[str, object]:
    truth_docs = discover_truth_docs(repo_root=repo_root)
    return {
        "system_state": {
            "mode": "truth_first_ops_cockpit_v2_6",
            "execution_model": "guarded_execution",
        },
        "guard_state": {
            "no_trade_baseline": "reference",
            "deny_by_default": "active",
            "treasury_separation": "enforced",
        },
        "truth_state": build_truth_state(truth_docs),
        "ai_boundary_state": build_ai_boundary_state(),
        "runtime_unknown_state": build_runtime_unknown_state(),
        "canonical_sources": truth_docs,
    }


def _render_doc_card(doc: Dict[str, object]) -> str:
    preview_items = "".join(f"<li>{escape(str(line))}</li>" for line in doc["preview"])
    preview_html = (
        f"<ul>{preview_items}</ul>"
        if preview_items
        else '<p class="empty-preview">No preview (read-only).</p>'
    )
    status_val = str(doc.get("status", "available" if doc["exists"] else "unavailable"))
    priority_val = str(doc["priority"])
    freshness_val = str(doc.get("freshness", "unknown"))
    return (
        '<div class="card truth-card">'
        f"<h3>{escape(str(doc['title']))}</h3>"
        f'<p><strong>Status:</strong> <span class="chip"><code>{escape(status_val)}</code></span></p>'
        f'<p><strong>Priority:</strong> <span class="chip"><code>{escape(priority_val)}</code></span></p>'
        f'<p><strong>Freshness:</strong> <span class="chip"><code>{escape(freshness_val)}</code></span></p>'
        f"<p><strong>Path:</strong> <code>{escape(str(doc['path']))}</code></p>"
        f"<p>{escape(str(doc['summary']))}</p>"
        f"{preview_html}"
        "</div>"
    )


def render_ops_cockpit_html(repo_root: Path | None = None) -> str:
    payload = build_ops_cockpit_payload(repo_root=repo_root)
    truth_state = payload["truth_state"]
    boundary = payload["ai_boundary_state"]
    runtime = payload["runtime_unknown_state"]
    counts = truth_state["priority_counts"]
    doc_cards = "".join(_render_doc_card(doc) for doc in payload["canonical_sources"])

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Peak_Trade Ops Cockpit v2.6</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }}
    .card {{ border: 1px solid #ddd; border-radius: 12px; padding: 16px; }}
    .card.truth-section {{ border-left: 4px solid #6b8e6b; }}
    .truth-card {{ border-left: 6px solid #6b8e6b; }}
    .hero {{ border: 1px solid #ddd; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
    .section-head {{ margin-top: 0; margin-bottom: 8px; font-size: 0.9em; color: #555; }}
    .legend {{ border: 1px solid #ddd; border-radius: 12px; padding: 14px; margin-bottom: 20px; }}
    .chip {{ display: inline-block; margin-left: 4px; }}
    code {{ background: #f5f5f5; padding: 2px 4px; border-radius: 4px; }}
    .priority-inline {{ display: inline-block; margin-right: 10px; font-size: 0.95em; }}
  </style>
</head>
<body>
  <div class="hero">
    <h1>Ops Cockpit v2.6 — Truth-First</h1>
    <p><em>Read-only. No write actions.</em></p>
    <p><strong>Truth coverage:</strong> {escape(str(truth_state["truth_coverage"]))}</p>
    <p><strong>Available / unavailable:</strong> {escape(str(truth_state["available_count"]))} / {escape(str(truth_state["unavailable_count"]))}</p>
    <p class="priority-inline"><strong>Priority buckets:</strong> canonical={escape(str(counts["canonical_boundary"]))}, runtime={escape(str(counts["runtime_resolution"]))}, supporting={escape(str(counts["supporting_truth"]))}</p>
    <p><strong>Execution model:</strong> {escape(str(payload["system_state"]["execution_model"]))}</p>
    <p><strong>Final trade authority:</strong> {escape(str(truth_state["final_trade_authority"]))}</p>
    <p><strong>Last verified:</strong> <code>{escape(str(truth_state.get("last_verified_utc", "—")))}</code></p>
  </div>

  <div class="legend">
    <h2>Read-only legends</h2>
    <p><strong>Availability:</strong> <code>available</code> = source found, <code>unavailable</code> = source missing.</p>
    <p><strong>Freshness:</strong> <code>fresh</code> ≤ 24h, <code>stale</code> ≤ 7d, <code>older</code> > 7d.</p>
  </div>

  <div class="grid">
    <div class="card truth-section">
      <h2>Truth State</h2>
      <p class="section-head">Read-only canonical truth</p>
      <p><strong>Truth-first positioning:</strong> {escape(str(truth_state["truth_first_positioning"]))}</p>
      <p><strong>Truth coverage:</strong> {escape(str(truth_state["truth_coverage"]))}</p>
      <p><strong>Live autonomy:</strong> {escape(str(truth_state["live_autonomy"]))}</p>
    </div>

    <div class="card truth-section">
      <h2>AI Boundary State</h2>
      <p class="section-head">Authority boundaries (read-only)</p>
      <p><strong>Proposer:</strong> {escape(str(boundary["proposer_authority"]))}</p>
      <p><strong>Critic:</strong> {escape(str(boundary["critic_authority"]))}</p>
      <p><strong>Provider binding authority:</strong> {escape(str(boundary["provider_binding_authority"]))}</p>
      <p><strong>Execution boundary:</strong> {escape(str(boundary["execution_boundary"]))}</p>
      <p><strong>Closest to trade:</strong> {escape(str(boundary["closest_to_trade"]))}</p>
    </div>

    <div class="card truth-section">
      <h2>Runtime Unknown State</h2>
      <p class="section-head">Unknown / partial slots (read-only)</p>
      <p><strong>Critic runtime path:</strong> {escape(str(runtime["critic_runtime_path"]))}</p>
      <p><strong>Proposer runtime path:</strong> {escape(str(runtime["proposer_runtime_path"]))}</p>
      <p><strong>Provider/model runtime slots:</strong> {escape(str(runtime["provider_model_runtime_slots"]))}</p>
      <p><strong>Execution-adjacent contracts:</strong> {escape(str(runtime["execution_adjacent_contracts"]))}</p>
    </div>
  </div>

  <h2>Canonical Sources</h2>
  <p>Read-only source cards with availability, priority, and freshness chips.</p>
  <p class="section-head">Truth docs (read-only)</p>
  <div class="grid">
    {doc_cards}
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
