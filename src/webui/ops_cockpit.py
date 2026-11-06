from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

from src.ops.update_officer_consumer import (
    build_update_officer_source_trace,
    build_update_officer_ui_model,
    build_update_officer_ui_route_conflict,
)


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

# Truth-doc freshness thresholds (Evidence Continuity / Row 12)
FRESHNESS_FRESH_HOURS = 24
FRESHNESS_OLDER_DAYS = 30


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
    if age_hours <= FRESHNESS_FRESH_HOURS:
        return "fresh"
    if age_hours <= 24 * FRESHNESS_OLDER_DAYS:
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
            "critical", "older", f"Sources older than {FRESHNESS_OLDER_DAYS} days. Stale evidence."
        )
    elif total_stale > 0:
        freshness_status = _status_obj(
            "warn", "stale", f"Some sources stale (≤{FRESHNESS_OLDER_DAYS}d). Partial freshness."
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


def _detect_incident_stop(repo_root: Path | None) -> tuple[bool, str]:
    """Detect if incident-stop was invoked. Returns (invoked, source)."""
    root = repo_root or Path.cwd()
    out_ops = root / "out" / "ops"
    if out_ops.exists():
        for d in sorted(out_ops.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if d.is_dir() and d.name.startswith("incident_stop_"):
                state_file = d / "incident_stop_state.env"
                if state_file.exists():
                    return True, str(state_file.relative_to(root))
    # Fallback: check PT_INCIDENT_STOP env
    val = os.environ.get("PT_INCIDENT_STOP", "").strip()
    if val and val not in ("0", "false", "False", ""):
        return True, "env:PT_INCIDENT_STOP"
    return False, "unknown"


def _build_caps_configured_from_config(config_path: Path) -> List[Dict[str, object]]:
    """
    Read-only. Build caps_configured from live_risk config.
    When bounded_live is enabled, uses bounded_live.limits overrides (aligned with
    LiveRiskLimits.from_config) so cockpit displays the same caps as runtime enforces.
    Returns [] on any error. Aligned with strategy_risk_telemetry limit_ids.
    """
    caps: List[Dict[str, object]] = []
    try:
        from src.core.peak_config import load_config_with_bounded_live

        cfg = load_config_with_bounded_live(config_path)
        base_ccy = str(cfg.get("live_risk.base_currency", "EUR") or "EUR")

        # (live_risk config_key, limit_id, optional bounded_live.limits key for override)
        mappings = [
            ("live_risk.max_total_exposure_notional", "max_total_exposure", "max_total_notional"),
            ("live_risk.max_symbol_exposure_notional", "max_symbol_exposure", None),
            ("live_risk.max_order_notional", "max_order_notional", "max_order_notional"),
            ("live_risk.max_open_positions", "max_open_positions", "max_open_positions"),
            ("live_risk.max_daily_loss_abs", "max_daily_loss_abs", "max_daily_loss_abs"),
            ("live_risk.max_daily_loss_pct", "max_daily_loss_pct", "max_daily_loss_pct"),
        ]
        bl = cfg.get("bounded_live")
        limits_bl: dict = {}
        if isinstance(bl, dict) and bl.get("enabled"):
            _limits = bl.get("limits", {})
            if isinstance(_limits, dict):
                limits_bl = _limits

        for config_key, limit_id, bl_key in mappings:
            val = None
            if bl_key and bl_key in limits_bl:
                try:
                    val = limits_bl[bl_key]
                except (TypeError, ValueError):
                    pass
            if val is None:
                val = cfg.get(config_key)
            if val is None:
                continue
            try:
                if limit_id == "max_open_positions":
                    cap_val = float(int(val))
                else:
                    cap_val = float(val)
                if cap_val > 0:
                    caps.append(
                        {
                            "limit_id": limit_id,
                            "cap_value": cap_val,
                            "ccy": base_ccy,
                            "source": "config",
                        }
                    )
            except (TypeError, ValueError):
                continue
    except Exception:
        pass
    return caps


def resolve_update_officer_route_inputs(
    notifier_path: str | Path | None,
    run_dir: str | Path | None,
) -> tuple[str | Path | None, str | Path | None, bool]:
    """
    Normalize optional query parameters for Update Officer.
    Returns (notifier_path, run_dir, conflict). On conflict both paths are None.
    """
    n_raw = "" if notifier_path is None else str(notifier_path).strip()
    r_raw = "" if run_dir is None else str(run_dir).strip()
    if n_raw and r_raw:
        return None, None, True
    return (n_raw or None, r_raw or None, False)


def normalize_update_officer_source_preset(raw: str | None) -> str:
    """
    v9: normalize optional query preset for Update Officer source ergonomics.
    Returns one of: manual, notifier_path, run_dir. Unknown values map to manual.
    """
    v = "" if raw is None else str(raw).strip().lower().replace("-", "_")
    if v == "notifier_path":
        return "notifier_path"
    if v == "run_dir":
        return "run_dir"
    return "manual"


def _uo_ops_preset_href(*, link_kind: str, form_np: str, form_rd: str) -> str:
    """Build GET /ops href for read-only preset toolbar (v9)."""
    if link_kind == "clear":
        return "/ops"
    if link_kind == "manual_keep":
        q: dict[str, str] = {"update_officer_source_preset": "manual"}
        np = form_np.strip()
        rd = form_rd.strip()
        if np:
            q["update_officer_notifier_path"] = np
        if rd:
            q["update_officer_run_dir"] = rd
        return "/ops?" + urlencode(q)
    if link_kind == "notifier_path":
        q = {"update_officer_source_preset": "notifier_path"}
        np = form_np.strip()
        if np:
            q["update_officer_notifier_path"] = np
        return "/ops?" + urlencode(q)
    if link_kind == "run_dir":
        q = {"update_officer_source_preset": "run_dir"}
        rd = form_rd.strip()
        if rd:
            q["update_officer_run_dir"] = rd
        return "/ops?" + urlencode(q)
    return "/ops"


def _uo_preset_display_label(preset: str) -> str:
    if preset == "notifier_path":
        return "notifier path"
    if preset == "run_dir":
        return "run directory"
    return "manual"


_U10_SOURCE_MODE_LABELS = {
    "conflict": "conflict",
    "explicit_notifier_path": "explicit notifier path",
    "run_directory": "run directory",
    "none": "none (omitted)",
}


def build_update_officer_validation_aids(
    *,
    conflict: bool,
    effective_notifier_path: Path | str | None,
    effective_run_dir: Path | str | None,
    source_preset: str,
) -> dict[str, str]:
    """
    v10: deterministic read-only explanations derived only from resolved route state and preset.
    """
    if conflict:
        mode = "conflict"
        resolution = (
            "After trimming, both update_officer_notifier_path and update_officer_run_dir were "
            "non-empty. Resolution stops until only one source remains in the query string."
        )
        conflict_explanation = (
            "No notifier payload is loaded while inputs conflict. Use preset focus links or "
            "clear one field, then Apply (GET)."
        )
        safe_default = ""
    elif effective_notifier_path:
        mode = "explicit_notifier_path"
        resolution = (
            "The consumer reads notifier_payload.json from the explicit path shown under "
            "Active source (read-only; no latest-run or hidden discovery)."
        )
        conflict_explanation = ""
        safe_default = ""
    elif effective_run_dir:
        mode = "run_directory"
        resolution = (
            "The consumer resolves notifier_payload.json inside the run directory shown under "
            "Active source (read-only; no latest-run or hidden discovery)."
        )
        conflict_explanation = ""
        safe_default = ""
    else:
        mode = "none"
        resolution = (
            "No source parameter resolved after trim — Update Officer uses the standard "
            "empty/unavailable state."
        )
        conflict_explanation = ""
        safe_default = (
            "Safe default: nothing is inferred automatically; operators must supply an explicit "
            "path or run directory."
        )

    if source_preset == "notifier_path":
        preset_explanation = (
            "Active preset notifier path: preset links omit run_dir from the URL to nudge a "
            "single-source query; v7 conflict rules still apply if both fields are submitted."
        )
    elif source_preset == "run_dir":
        preset_explanation = (
            "Active preset run directory: preset links omit notifier path from the URL to nudge "
            "a single-source query; v7 conflict rules still apply if both fields are submitted."
        )
    else:
        preset_explanation = (
            "Active preset manual: both fields are allowed in the form; supply at most one "
            "non-empty source for resolution (v7)."
        )

    return {
        "source_mode": mode,
        "source_mode_label": _U10_SOURCE_MODE_LABELS.get(mode, mode),
        "preset_explanation": preset_explanation,
        "resolution_explanation": resolution,
        "conflict_explanation": conflict_explanation,
        "safe_default_explanation": safe_default,
    }


def _render_update_officer_validation_aids_html(aids: dict[str, str]) -> str:
    """v10: read-only validation/explainability block (HTML fragment)."""
    mode = escape(aids["source_mode"])
    mode_label = escape(aids["source_mode_label"])
    preset_explanation = escape(aids["preset_explanation"])
    resolution_explanation = escape(aids["resolution_explanation"])
    conflict_explanation = escape(aids["conflict_explanation"])
    safe_default = escape(aids["safe_default_explanation"])
    conflict_row = ""
    if aids["conflict_explanation"]:
        conflict_row = f"<dt>Conflict</dt><dd>{conflict_explanation}</dd>"
    safe_row = ""
    if aids["safe_default_explanation"]:
        safe_row = f"<dt>Safe default</dt><dd>{safe_default}</dd>"
    return (
        f'<div class="uo-validation-aids" data-u10-source-mode="{mode}">'
        "<h3>Validation / explainability (read-only)</h3>"
        "<p>Derived only from the current query and normalized inputs. No POST, no writes.</p>"
        "<dl>"
        f"<dt>Source mode</dt><dd><code>{mode_label}</code></dd>"
        f"<dt>Preset meaning</dt><dd>{preset_explanation}</dd>"
        f"<dt>Resolution interpretation</dt><dd>{resolution_explanation}</dd>"
        f"{conflict_row}"
        f"{safe_row}"
        "</dl>"
        "</div>"
    )


def _render_update_officer_operator_trace_html(trace: dict[str, str]) -> str:
    """v11: read-only operator trace aligned with build_update_officer_source_trace."""
    sm = escape(trace["source_mode"])
    so = escape(trace["source_origin"])
    ap = escape(trace["active_preset"])
    sc = escape(trace["source_conflict"])
    ert = escape(trace["effective_resolution_target"])
    sda = escape(trace["safe_default_active"])
    return (
        f'<div class="uo-operator-trace" data-u11-source-mode="{sm}">'
        "<h3>Operator trace (read-only)</h3>"
        "<p>Deterministic fields shared with the Update Officer consumer; explicit query inputs "
        "only. No POST, no writes.</p>"
        "<dl>"
        f"<dt>source_mode</dt><dd><code>{sm}</code></dd>"
        f"<dt>source_origin</dt><dd><code>{so}</code></dd>"
        f"<dt>active_preset</dt><dd><code>{ap}</code></dd>"
        f"<dt>source_conflict</dt><dd><code>{sc}</code></dd>"
        f"<dt>effective_resolution_target</dt><dd><code>{ert}</code></dd>"
        f"<dt>safe_default_active</dt><dd><code>{sda}</code></dd>"
        "</dl>"
        "</div>"
    )


PHASE83_ELIGIBILITY_MAX_STRATEGIES = 24


def _toml_load_table(path: Path) -> dict:
    """Load TOML (tomllib on 3.11+, tomli on older)."""
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

    with open(path, "rb") as f:
        return tomllib.load(f)


def _list_core_aux_strategy_ids_from_toml(tiering_path: Path, *, limit: int) -> List[str]:
    """Strategy IDs with tier core or aux, sorted, capped."""
    if not tiering_path.exists():
        return []
    try:
        data = _toml_load_table(tiering_path)
    except Exception:
        return []
    block = data.get("strategy") or {}
    ids: List[str] = []
    for sid, meta in block.items():
        if not isinstance(meta, dict):
            continue
        tier = str(meta.get("tier", "")).lower()
        if tier in ("core", "aux"):
            ids.append(str(sid))
    ids.sort()
    return ids[:limit]


def _build_phase83_eligibility_snapshot(repo_root: Path | None) -> Dict[str, object]:
    """
    Read-only Phase 83 eligibility rows via ``check_strategy_live_eligibility``.

    Does not change gate semantics; surfaces observed outcomes only.
    """
    root = repo_root if repo_root is not None else Path.cwd()
    tiering_path = root / "config" / "strategy_tiering.toml"
    policies_path = root / "config" / "live_policies.toml"
    base: Dict[str, object] = {
        "mode": "phase83_eligibility_snapshot_v1",
        "source": "src.live.live_gates.check_strategy_live_eligibility",
        "read_only": True,
        "truth_posture": "observation_only",
    }
    if not tiering_path.exists():
        return {
            **base,
            "status": "unavailable",
            "detail": "config/strategy_tiering.toml not found for this repo root",
            "strategies_checked": 0,
            "eligible_count": 0,
            "not_eligible_count": 0,
            "require_allow_live_flag": None,
            "items": [],
        }
    try:
        from src.live.live_gates import check_strategy_live_eligibility, load_live_policies
    except ImportError as e:
        return {
            **base,
            "status": "unavailable",
            "detail": f"live_gates import failed: {e}",
            "strategies_checked": 0,
            "eligible_count": 0,
            "not_eligible_count": 0,
            "require_allow_live_flag": None,
            "items": [],
        }

    policies = load_live_policies(policies_path)
    require_flag = bool(getattr(policies, "require_allow_live_flag", False))
    strategies = _list_core_aux_strategy_ids_from_toml(
        tiering_path, limit=PHASE83_ELIGIBILITY_MAX_STRATEGIES
    )
    if not strategies:
        return {
            **base,
            "status": "empty_selection",
            "detail": "no core/aux entries found in strategy tiering file",
            "strategies_checked": 0,
            "eligible_count": 0,
            "not_eligible_count": 0,
            "require_allow_live_flag": require_flag,
            "items": [],
        }

    items: List[Dict[str, object]] = []
    eligible_n = 0
    not_eligible_n = 0
    for sid in strategies:
        try:
            res = check_strategy_live_eligibility(
                sid,
                policies=policies,
                tiering_config_path=tiering_path,
            )
            row: Dict[str, object] = {
                "entity_id": res.entity_id,
                "entity_type": res.entity_type,
                "is_eligible": res.is_eligible,
                "reasons": list(res.reasons)[:8],
                "tier": res.tier,
                "allow_live_flag": res.allow_live_flag,
            }
        except Exception as e:
            row = {
                "entity_id": sid,
                "entity_type": "strategy",
                "is_eligible": False,
                "reasons": [f"evaluation_error:{type(e).__name__}"],
                "tier": None,
                "allow_live_flag": None,
            }
        items.append(row)
        if row.get("is_eligible") is True:
            eligible_n += 1
        else:
            not_eligible_n += 1

    try:
        tier_rel = tiering_path.relative_to(root)
    except ValueError:
        tier_rel = tiering_path

    return {
        **base,
        "status": "ok",
        "detail": None,
        "tiering_path": str(tier_rel),
        "strategies_checked": len(strategies),
        "eligible_count": eligible_n,
        "not_eligible_count": not_eligible_n,
        "require_allow_live_flag": require_flag,
        "items": items,
    }


def _render_phase83_eligibility_card(snapshot: Dict[str, object]) -> str:
    """HTML block: Phase 83 eligibility snapshot (read-only, truth-first wording)."""
    status = escape(str(snapshot.get("status", "unknown")))
    mode = escape(str(snapshot.get("mode", "")))
    detail_raw = snapshot.get("detail")
    detail = escape(str(detail_raw)) if detail_raw else ""
    src = escape(str(snapshot.get("source", "")))
    chk = int(snapshot.get("strategies_checked") or 0)
    eli = int(snapshot.get("eligible_count") or 0)
    nel = int(snapshot.get("not_eligible_count") or 0)
    rflag = snapshot.get("require_allow_live_flag")
    rflag_s = escape(str(rflag)) if rflag is not None else "n/a"
    tier_path = snapshot.get("tiering_path")
    tier_path_s = escape(str(tier_path)) if tier_path else ""

    rows_html: List[str] = []
    for it in snapshot.get("items") or []:
        if not isinstance(it, dict):
            continue
        eid = escape(str(it.get("entity_id", "")))
        elig = it.get("is_eligible")
        if elig is True:
            elig_s = escape("yes")
        elif elig is False:
            elig_s = escape("no")
        else:
            elig_s = escape("?")
        tier = escape(str(it.get("tier") or ""))
        reasons = it.get("reasons") or []
        rtext = escape("; ".join(str(r) for r in list(reasons)[:6]))
        rows_html.append(
            f"<tr><td><code>{eid}</code></td><td>{elig_s}</td><td>{tier}</td><td>{rtext}</td></tr>"
        )
    table_html = ""
    if rows_html:
        table_html = (
            "<table style='width:100%;border-collapse:collapse;font-size:0.9em;'>"
            "<thead><tr><th align='left'>Strategy</th>"
            "<th>Observed eligible</th><th>Tier</th><th align='left'>Notes (truncated)</th></tr></thead>"
            f"<tbody>{''.join(rows_html)}</tbody></table>"
        )

    intro = (
        "Observation only from the existing Phase 83 eligibility check. "
        "Does not grant live access or change enforcement."
    )
    detail_block = f"<p><strong>Detail:</strong> {detail}</p>" if detail else ""
    path_block = (
        f"<p><strong>Tiering path:</strong> <code>{tier_path_s}</code></p>" if tier_path_s else ""
    )

    return (
        f'<div class="card truth-card" id="phase83-strategy-eligibility-card" '
        f'style="margin-bottom:20px;">'
        f"<h2>Phase 83 — Strategy eligibility</h2>"
        f"<p><strong>Read-only.</strong> {intro}</p>"
        f"<p><strong>Snapshot mode:</strong> <code>{mode}</code> · "
        f"<strong>Status:</strong> <code>{status}</code> · "
        f"<strong>Source:</strong> <code>{src}</code></p>"
        f"{path_block}"
        f"<p><strong>Strategies evaluated (cap {PHASE83_ELIGIBILITY_MAX_STRATEGIES}):</strong> {chk} · "
        f"<strong>Observed eligible / not eligible:</strong> {eli} / {nel} · "
        f"<strong>Policy require_allow_live_flag:</strong> <code>{rflag_s}</code></p>"
        f"{detail_block}"
        f"{table_html}"
        f"</div>"
    )


def _fmt_observation_cell(val: object) -> str:
    if val is True:
        return "true"
    if val is False:
        return "false"
    if val is None:
        return "n/a"
    return str(val)


def _policy_guard_observation_table_html(payload: Dict[str, object]) -> str:
    """Table body rows for ``policy_state`` / ``guard_state`` (existing keys only)."""
    ps_raw = payload.get("policy_state")
    gs_raw = payload.get("guard_state")
    ps = ps_raw if isinstance(ps_raw, dict) else {}
    gs = gs_raw if isinstance(gs_raw, dict) else {}

    rows_html: List[str] = []
    for label, key in (
        ("policy_state.action", "action"),
        ("policy_state.summary", "summary"),
        ("policy_state.enabled", "enabled"),
        ("policy_state.armed", "armed"),
        ("policy_state.dry_run", "dry_run"),
        ("policy_state.blocked", "blocked"),
        ("policy_state.kill_switch_active", "kill_switch_active"),
        ("policy_state.confirm_token_required", "confirm_token_required"),
    ):
        if key not in ps:
            continue
        v = escape(_fmt_observation_cell(ps.get(key)))
        rows_html.append(
            f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'><code>{escape(label)}</code></td>"
            f"<td style='padding:4px 0;'><code>{v}</code></td></tr>"
        )
    for label, key in (
        ("guard_state.no_trade_baseline", "no_trade_baseline"),
        ("guard_state.deny_by_default", "deny_by_default"),
        ("guard_state.treasury_separation", "treasury_separation"),
    ):
        if key not in gs:
            continue
        v = escape(_fmt_observation_cell(gs.get(key)))
        rows_html.append(
            f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'><code>{escape(label)}</code></td>"
            f"<td style='padding:4px 0;'><code>{v}</code></td></tr>"
        )

    return (
        "<table style='width:100%;border-collapse:collapse;font-size:0.9em;'>"
        "<tbody>"
        f"{''.join(rows_html)}"
        "</tbody></table>"
    )


def _render_ai_boundary_observation_table(boundary: Dict[str, object]) -> str:
    """Compact table for ``ai_boundary_state`` (Critic/Proposer/boundary labels, read-only)."""
    rows_html: List[str] = []
    for label, key in (
        ("ai_boundary_state.proposer_authority", "proposer_authority"),
        ("ai_boundary_state.critic_authority", "critic_authority"),
        ("ai_boundary_state.provider_binding_authority", "provider_binding_authority"),
        ("ai_boundary_state.execution_boundary", "execution_boundary"),
        ("ai_boundary_state.closest_to_trade", "closest_to_trade"),
    ):
        if key not in boundary:
            continue
        v = escape(_fmt_observation_cell(boundary.get(key)))
        rows_html.append(
            f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'><code>{escape(label)}</code></td>"
            f"<td style='padding:4px 0;'><code>{v}</code></td></tr>"
        )
    return (
        "<table style='width:100%;border-collapse:collapse;font-size:0.9em;'>"
        "<tbody>"
        f"{''.join(rows_html)}"
        "</tbody></table>"
    )


def _render_human_supervision_observation_table(hs: Dict[str, object]) -> str:
    """Compact table for ``human_supervision_state``."""
    rows_html: List[str] = []
    for label, key in (
        ("human_supervision_state.status", "status"),
        ("human_supervision_state.mode", "mode"),
        ("human_supervision_state.summary", "summary"),
    ):
        if key not in hs:
            continue
        v = escape(_fmt_observation_cell(hs.get(key)))
        rows_html.append(
            f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'><code>{escape(label)}</code></td>"
            f"<td style='padding:4px 0;'><code>{v}</code></td></tr>"
        )
    return (
        "<table style='width:100%;border-collapse:collapse;font-size:0.9em;'>"
        "<tbody>"
        f"{''.join(rows_html)}"
        "</tbody></table>"
    )


def _render_evidence_governance_cross_ref(evidence: Dict[str, object]) -> str:
    """Short governance cross-surface block for ``evidence_state``; full fields stay in Evidence card."""
    ev = evidence if isinstance(evidence, dict) else {}
    summ = escape(str(ev.get("summary", "unknown")))
    fs = escape(str(ev.get("freshness_status", "unknown")))
    audit = escape(str(ev.get("audit_trail", "unknown")))
    lv = escape(str(ev.get("last_verified_utc", "n/a")))
    return (
        "<p><strong>Read-only.</strong> Rollup fields from <code>evidence_state</code> on this page. "
        "<strong>Observation only</strong> — <strong>not approval</strong>, <strong>not unlock</strong>. "
        "Confirm-token requirement is reported under <code>policy_state.confirm_token_required</code> above.</p>"
        f"<p><strong>evidence_state.summary</strong> (observation): <code>{summ}</code></p>"
        f"<p><strong>evidence_state.freshness_status</strong> (observation): <code>{fs}</code></p>"
        f"<p><strong>evidence_state.audit_trail</strong> (observation): <code>{audit}</code></p>"
        f"<p><strong>evidence_state.last_verified_utc</strong> (observation): <code>{lv}</code></p>"
        '<p style="font-size:0.95em;">Full <code>evidence_state</code> fields (including '
        '<code>source_freshness</code>) appear in the <a href="#evidence-state-card">Evidence State</a> '
        "card below.</p>"
    )


def _render_policy_governance_observation_surface(payload: Dict[str, object]) -> str:
    """vNext Required View 6 — Policy / Governance: bundle existing payload slices, read-only wording."""
    boundary_raw = payload.get("ai_boundary_state")
    boundary = boundary_raw if isinstance(boundary_raw, dict) else {}
    hs_raw = payload.get("human_supervision_state")
    hs = hs_raw if isinstance(hs_raw, dict) else {}
    ev_raw = payload.get("evidence_state")
    evidence = ev_raw if isinstance(ev_raw, dict) else {}

    policy_table = _policy_guard_observation_table_html(payload)
    pg_intro = (
        "Same fields as <code>policy_state</code> / <code>guard_state</code> in the JSON payload for "
        "this page. <strong>Observation only</strong> — not a control surface; does not grant live "
        "access or change enforcement."
    )
    surface_intro = (
        "<p><strong>Read-only.</strong> OPS Suite Dashboard vNext <strong>Required View 6 — Policy / "
        "Governance</strong>: quoted labels from this page&apos;s JSON only. "
        "<strong>Not approval, not unlock,</strong> not a substitute for your governance process.</p>"
        "<p>Critic/Proposer and AI-boundary posture: <code>ai_boundary_state</code>. Policy and guard "
        "rails: <code>policy_state</code>, <code>guard_state</code>. Human supervision intent: "
        "<code>human_supervision_state</code>. Evidence/audit rollups: <code>evidence_state</code> "
        "(detail in the Evidence State card).</p>"
    )
    b_intro = (
        "<p><strong>Read-only.</strong> Advisory/supervisory boundary labels from <code>ai_boundary_state"
        "</code> — observation only; not execution authority.</p>"
    )
    hs_intro = (
        "<p><strong>Read-only.</strong> Design-intent supervision mode from <code>human_supervision_state"
        "</code> (see PILOT_GO_NO_GO_CHECKLIST row 55 in repo docs). Observation only.</p>"
    )
    return (
        f'<div class="group-block policy-governance-observation-surface" '
        f'id="policy-governance-observation-surface" style="margin-bottom:20px;">'
        f'<div class="card truth-card">'
        f"<h2>Policy / Governance observation (vNext RV6)</h2>"
        f"{surface_intro}"
        f"<h3>Policy / guard rails — observed state</h3>"
        f"<p><strong>Read-only.</strong> {pg_intro}</p>"
        f"{policy_table}"
        f"<h3>Critic / Proposer / AI boundary (payload)</h3>"
        f"{b_intro}"
        f"{_render_ai_boundary_observation_table(boundary)}"
        f"<h3>Human Supervision (payload)</h3>"
        f"{hs_intro}"
        f"{_render_human_supervision_observation_table(hs)}"
        f"<h3>Evidence / audit (governance cross-surface)</h3>"
        f"{_render_evidence_governance_cross_ref(evidence)}"
        f"</div></div>"
    )


def _render_operator_summary_policy_governance_rv6(payload: Dict[str, object]) -> str:
    """Compact RV6 mirror for operator summary; same payload objects as main-page RV6 surface."""
    ps_raw = payload.get("policy_state")
    ps = ps_raw if isinstance(ps_raw, dict) else {}
    gs_raw = payload.get("guard_state")
    gs = gs_raw if isinstance(gs_raw, dict) else {}
    boundary_raw = payload.get("ai_boundary_state")
    boundary = boundary_raw if isinstance(boundary_raw, dict) else {}
    hs_raw = payload.get("human_supervision_state")
    hs = hs_raw if isinstance(hs_raw, dict) else {}
    ev_raw = payload.get("evidence_state")
    ev = ev_raw if isinstance(ev_raw, dict) else {}

    pa = escape(str(ps.get("action", "n/a")))
    psu = escape(str(ps.get("summary", "n/a")))
    pb = escape(str(ps.get("blocked", "n/a")))
    pct = escape(str(ps.get("confirm_token_required", "n/a")))
    gts = escape(str(gs.get("treasury_separation", "n/a")))
    gdb = escape(str(gs.get("deny_by_default", "n/a")))
    ppa = escape(str(boundary.get("proposer_authority", "n/a")))
    cca = escape(str(boundary.get("critic_authority", "n/a")))
    eb = escape(str(boundary.get("execution_boundary", "n/a")))
    hss = escape(str(hs.get("status", "n/a")))
    hsm = escape(str(hs.get("mode", "n/a")))
    evs = escape(str(ev.get("summary", "n/a")))
    evf = escape(str(ev.get("freshness_status", "n/a")))

    return (
        '<section class="operator-summary-policy-governance-rv6" '
        'id="operator-summary-policy-governance-rv6">'
        "<h3>Policy / Governance (vNext RV6) — compact observation</h3>"
        "<p><strong>Observation only.</strong> Compact mirror of the same top-level JSON objects as "
        '<a href="#policy-governance-observation-surface">Policy / Governance observation (vNext RV6)</a> '
        "below — <strong>not approval,</strong> <strong>not unlock,</strong> "
        "not a substitute for external governance or <code>policy_go_no_go_observation</code>.</p>"
        "<p><strong>policy_state.action</strong> (observation): <code>"
        f"{pa}</code> · <strong>policy_state.summary</strong>: <code>{psu}</code> · "
        f"<strong>policy_state.blocked</strong>: <code>{pb}</code> · "
        f"<strong>policy_state.confirm_token_required</strong>: <code>{pct}</code></p>"
        "<p><strong>guard_state.treasury_separation</strong> (observation): <code>"
        f"{gts}</code> · <strong>guard_state.deny_by_default</strong>: <code>{gdb}</code></p>"
        "<p><strong>ai_boundary_state</strong> — <strong>proposer_authority</strong> / "
        "<strong>critic_authority</strong> / <strong>execution_boundary</strong> (observation): "
        f"<code>{ppa}</code> / <code>{cca}</code> / <code>{eb}</code></p>"
        "<p><strong>human_supervision_state.status</strong> / <strong>mode</strong> (observation): "
        f"<code>{hss}</code> / <code>{hsm}</code></p>"
        "<p><strong>evidence_state.summary</strong> / <strong>freshness_status</strong> (observation): "
        f"<code>{evs}</code> / <code>{evf}</code></p>"
        '<p style="font-size:0.95em;">Detail tables: '
        '<a href="#policy-governance-observation-surface">RV6 observation surface</a> · '
        '<a href="#evidence-state-card">Evidence State</a> card.</p>'
        "</section>"
    )


def _render_operator_summary_operator_state(payload: Dict[str, object]) -> str:
    """Compact ``operator_state`` snapshot for operator summary (payload object only; read-only)."""
    os_raw = payload.get("operator_state")
    if not isinstance(os_raw, dict):
        return ""
    rows: List[str] = []
    for label, key in (
        ("operator_state.disabled", "disabled"),
        ("operator_state.enabled", "enabled"),
        ("operator_state.armed", "armed"),
        ("operator_state.dry_run", "dry_run"),
        ("operator_state.blocked", "blocked"),
        ("operator_state.kill_switch_active", "kill_switch_active"),
    ):
        if key not in os_raw:
            continue
        v = escape(_fmt_observation_cell(os_raw.get(key)))
        rows.append(f"<p><strong>{label}</strong> (observation): <code>{v}</code></p>")
    if not rows:
        return ""
    return (
        '<section class="operator-summary-operator-state" id="operator-summary-operator-state">'
        "<h3>Operator state (payload)</h3>"
        "<p><strong>Observation only.</strong> Local operator state snapshot from <code>operator_state</code> "
        "in this page&apos;s JSON — <strong>not approval,</strong> <strong>not unlock,</strong> "
        "not a substitute for <code>policy_go_no_go_observation</code> (separate aggregate). "
        'See also <a href="#policy-governance-observation-surface">Policy / Governance (vNext RV6)</a>.</p>'
        f"{''.join(rows)}"
        "</section>"
    )


def _render_phase57_snapshot_discoverability_card() -> str:
    """HTML block: discoverability links to existing Phase 57 snapshot API (read-only, no new semantics)."""
    return (
        f'<div class="card truth-card" id="phase57-live-snapshot-endpoints-card" '
        f'style="margin-bottom:20px;">'
        f"<h2>Live status snapshot (Phase 57) — endpoints</h2>"
        f"<p><strong>Read-only.</strong> Same JSON/HTML feeds as the home dashboard; observation only — "
        f"not operational approval or go-live implication.</p>"
        f"<p style='font-size:0.95em;'>"
        f'<a href="/api/live/status/snapshot.json">/api/live/status/snapshot.json</a>'
        f" · "
        f'<a href="/api/live/status/snapshot.html">/api/live/status/snapshot.html</a>'
        f"</p>"
        f"</div>"
    )


def _render_operator_summary_phase57_snapshot_discoverability() -> str:
    """Compact Phase 57 live snapshot endpoint discoverability for operator summary (GET links only)."""
    return (
        '<section class="operator-summary-phase57-snapshot" '
        'id="operator-summary-phase57-snapshot-discoverability">'
        "<h3>Live status snapshot (Phase 57) — endpoints</h3>"
        "<p><strong>Read-only discoverability.</strong> Same JSON/HTML feeds as the home dashboard and the "
        "<strong>Live status snapshot (Phase 57) — endpoints</strong> card on this page — "
        "<strong>not</strong> operational approval, <strong>not</strong> go-live, "
        "<strong>not</strong> a substitute for governance or <code>policy_go_no_go_observation</code>.</p>"
        '<p style="font-size:0.95em;">'
        '<a href="/api/live/status/snapshot.json">/api/live/status/snapshot.json</a>'
        " · "
        '<a href="/api/live/status/snapshot.html">/api/live/status/snapshot.html</a>'
        "</p>"
        "</section>"
    )


def _render_operator_summary_truth_state(payload: Dict[str, object]) -> str:
    """Compact ``truth_state`` snapshot for operator summary (truth doc pipeline; read-only)."""
    ts_raw = payload.get("truth_state")
    if not isinstance(ts_raw, dict):
        return ""
    rows: List[str] = []
    for label, key in (
        ("truth_state.last_verified_utc", "last_verified_utc"),
        ("truth_state.truth_coverage", "truth_coverage"),
        ("truth_state.available_count", "available_count"),
        ("truth_state.unavailable_count", "unavailable_count"),
        ("truth_state.truth_first_positioning", "truth_first_positioning"),
        ("truth_state.final_trade_authority", "final_trade_authority"),
        ("truth_state.live_autonomy", "live_autonomy"),
    ):
        if key not in ts_raw:
            continue
        v = escape(_fmt_observation_cell(ts_raw.get(key)))
        rows.append(f"<p><strong>{label}</strong> (observation): <code>{v}</code></p>")
    if not rows:
        return ""
    return (
        '<section class="operator-summary-truth-state" id="operator-summary-truth-state">'
        "<h3>Truth pipeline (payload)</h3>"
        "<p><strong>Observation only.</strong> Local truth-document pipeline snapshot from <code>truth_state</code> "
        "in this page&apos;s JSON — <strong>not approval,</strong> <strong>not go-live,</strong> "
        "not broker or exchange truth, not a substitute for governance or "
        "<code>policy_go_no_go_observation</code>. "
        "<strong>Status at a glance</strong> below shows v3 executive rollups; "
        "<code>health_drift_observation</code> is the separate service/drift aggregate.</p>"
        f"{''.join(rows)}"
        "</section>"
    )


def _render_operator_summary_truth_sources_runtime(payload: Dict[str, object]) -> str:
    """Compact truth sources & runtime snapshot for operator summary (grouping + labels; read-only)."""
    rows: List[str] = []
    ru = payload.get("runtime_unknown_state")
    if isinstance(ru, dict):
        for label, key in (
            ("runtime_unknown_state.critic_runtime_path", "critic_runtime_path"),
            ("runtime_unknown_state.proposer_runtime_path", "proposer_runtime_path"),
            (
                "runtime_unknown_state.provider_model_runtime_slots",
                "provider_model_runtime_slots",
            ),
            (
                "runtime_unknown_state.execution_adjacent_contracts",
                "execution_adjacent_contracts",
            ),
        ):
            if key not in ru:
                continue
            v = escape(_fmt_observation_cell(ru.get(key)))
            rows.append(f"<p><strong>{label}</strong> (observation): <code>{v}</code></p>")

    cs = payload.get("canonical_sources")
    if isinstance(cs, list):
        rows.append(
            "<p><strong>canonical_sources</strong> (observation): "
            f"<code>{len(cs)}</code> truth-doc entries in this payload inventory "
            "(count only; <strong>not</strong> broker or exchange truth).</p>"
        )

    sg = payload.get("source_groups")
    group_order = ("canonical_boundary", "runtime_resolution", "supporting_truth")
    if isinstance(sg, dict):
        bits: List[str] = []
        for name in group_order:
            if name not in sg:
                continue
            g = sg.get(name)
            if isinstance(g, list):
                bits.append(f"{escape(name)}: {len(g)}")
        if bits:
            rows.append(
                "<p><strong>source_groups</strong> (observation) — group sizes: "
                f"<code>{', '.join(bits)}</code></p>"
            )

    sgs = payload.get("source_group_summary")
    if isinstance(sgs, dict):
        summ_bits: List[str] = []
        for name in group_order:
            if name not in sgs:
                continue
            sm = sgs.get(name)
            if not isinstance(sm, dict):
                continue
            t = sm.get("total", "?")
            a = sm.get("available", "?")
            u = sm.get("unavailable", "?")
            summ_bits.append(f"{escape(str(name))} total={t} avail={a} unavail={u}")
        if summ_bits:
            rows.append(
                "<p><strong>source_group_summary</strong> (observation): "
                f"<code>{'; '.join(summ_bits)}</code></p>"
            )

    if not rows:
        return ""
    return (
        '<section class="operator-summary-truth-sources-runtime" '
        'id="operator-summary-truth-sources-runtime">'
        "<h3>Truth sources &amp; runtime (payload)</h3>"
        "<p><strong>Observation only.</strong> Local truth-source and runtime-label snapshot from "
        "<code>runtime_unknown_state</code>, <code>source_groups</code>, <code>source_group_summary</code>, "
        "and <code>canonical_sources</code> in this page&apos;s JSON — "
        "<strong>not approval,</strong> <strong>not go-live,</strong> "
        "not broker or exchange truth, not a substitute for governance or "
        "<code>policy_go_no_go_observation</code>. Does not replace "
        "<strong>Status at a glance</strong> or <code>health_drift_observation</code>.</p>"
        f"{''.join(rows)}"
        "</section>"
    )


def _render_incident_observation_card(payload: Dict[str, object]) -> str:
    """HTML block: compact incident rollup from existing ``incident_state`` keys only (read-only wording)."""
    inc_raw = payload.get("incident_state")
    inc = inc_raw if isinstance(inc_raw, dict) else {}

    def _fmt_val(val: object) -> str:
        if val is True:
            return "true"
        if val is False:
            return "false"
        if val is None:
            return "n/a"
        return str(val)

    rows_html: List[str] = []
    for label, key in (
        ("incident_state.status", "status"),
        ("incident_state.summary", "summary"),
        ("incident_state.blocked", "blocked"),
        ("incident_state.degraded", "degraded"),
        ("incident_state.requires_operator_attention", "requires_operator_attention"),
    ):
        if key not in inc:
            continue
        v = escape(_fmt_val(inc.get(key)))
        rows_html.append(
            f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'><code>{escape(label)}</code></td>"
            f"<td style='padding:4px 0;'><code>{v}</code></td></tr>"
        )

    if not rows_html:
        return ""

    table_html = (
        "<table style='width:100%;border-collapse:collapse;font-size:0.9em;'>"
        "<tbody>"
        f"{''.join(rows_html)}"
        "</tbody></table>"
    )
    intro = (
        "Subset of <code>incident_state</code> already present in this page’s JSON payload (rollup fields "
        "only). Observation only — not a control surface; does not grant live access or change enforcement. "
        "Further incident fields appear under Incident-state read model below."
    )
    return (
        f'<div class="card truth-card" id="incident-observed-rollup-observation-card" style="margin-bottom:20px;">'
        f"<h2>Incident — observed rollup</h2>"
        f"<p><strong>Read-only.</strong> {intro}</p>"
        f"{table_html}"
        f"</div>"
    )


# Same labels and payload keys as ``_render_run_state_observation_card`` / operator-summary run_state block.
_RUN_STATE_OBSERVATION_FIELD_ROWS: Tuple[Tuple[str, str], ...] = (
    ("run_state.status", "status"),
    ("run_state.active", "active"),
    ("run_state.last_run_status", "last_run_status"),
    ("run_state.session_active", "session_active"),
    ("run_state.registry_session_count", "registry_session_count"),
    ("run_state.registry_last_started_at", "registry_last_started_at"),
    ("run_state.generated_at", "generated_at"),
    ("run_state.freshness_status", "freshness_status"),
)


def _format_run_state_observation_value(val: object) -> str:
    if val is True:
        return "true"
    if val is False:
        return "false"
    if val is None:
        return "n/a"
    return str(val)


def _render_run_state_observation_card(payload: Dict[str, object]) -> str:
    """HTML block: compact run-state rollup from existing ``run_state`` keys only (read-only wording)."""
    rs_raw = payload.get("run_state")
    rs = rs_raw if isinstance(rs_raw, dict) else {}

    rows_html: List[str] = []
    for label, key in _RUN_STATE_OBSERVATION_FIELD_ROWS:
        if key not in rs:
            continue
        v = escape(_format_run_state_observation_value(rs.get(key)))
        rows_html.append(
            f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'><code>{escape(label)}</code></td>"
            f"<td style='padding:4px 0;'><code>{v}</code></td></tr>"
        )

    if not rows_html:
        return ""

    table_html = (
        "<table style='width:100%;border-collapse:collapse;font-size:0.9em;'>"
        "<tbody>"
        f"{''.join(rows_html)}"
        "</tbody></table>"
    )
    intro = (
        "Subset of <code>run_state</code> already present in this page’s JSON payload (same object as "
        "<code>GET /api/ops-cockpit</code>). Observation only — not a control surface; does not start or "
        "stop runs or change execution semantics."
    )
    return (
        f'<div class="card truth-card" id="run-state-observation-card" style="margin-bottom:20px;">'
        f"<h2>Run state — observed rollup</h2>"
        f"<p><strong>Read-only.</strong> {intro}</p>"
        f"{table_html}"
        f"</div>"
    )


def _render_workflow_officer_observation_surface(payload: Dict[str, object]) -> str:
    """vNext Phase 4: latest Workflow Officer dashboard view — ``workflow_officer_state`` only (read-only)."""
    wo_raw = payload.get("workflow_officer_state")
    wo = wo_raw if isinstance(wo_raw, dict) else {}
    present = wo.get("present") is True
    intro = (
        "<p><strong>Read-only.</strong> Same object as <code>workflow_officer_state</code> in this "
        "page&apos;s JSON payload — from <code>build_workflow_officer_panel_context</code> "
        "(latest <code>report.json</code> under <code>out/ops/workflow_officer</code> when present). "
        "<strong>Observation and visibility only</strong> — <strong>not approval</strong>, "
        "<strong>not unlock</strong>, <strong>not execution authority</strong>, "
        "<strong>not a release go-signal</strong>; does not start or run Workflow Officer from this page. "
        "Compact policy posture remains <code>policy_go_no_go_observation</code> (separate payload aggregate; "
        "not implied here).</p>"
    )
    head = (
        f'<div class="group-block operator-workflow-observation-surface" '
        f'id="operator-workflow-observation-surface" style="margin-bottom:20px;">'
        f'<div class="card truth-card">'
        f"<h2>Operator workflow observation (vNext Phase 4)</h2>"
        f"{intro}"
    )
    if not present:
        er = wo.get("empty_reason")
        er_s = escape(str(er)) if er is not None else "unknown"
        return (
            f"{head}"
            f"<p><strong>workflow_officer_state.present</strong> (observation): <code>false</code></p>"
            f"<p><strong>workflow_officer_state.empty_reason</strong> (observation): <code>{er_s}</code></p>"
            "<p>No Workflow Officer artifacts observed at this repo root (or report not readable). "
            "Filesystem observation only — not guidance to skip governance checks.</p>"
            f"</div></div>"
        )

    rollup = wo.get("rollup") if isinstance(wo.get("rollup"), dict) else {}
    ex = wo.get("executive") if isinstance(wo.get("executive"), dict) else {}
    pf_raw = wo.get("primary_followup")
    pf = pf_raw if isinstance(pf_raw, dict) else None

    def _cell(val: object) -> str:
        return escape(_fmt_observation_cell(val))

    rows_html: List[str] = []
    for label, key in (
        ("workflow_officer_state.run_dir_name", "run_dir_name"),
        ("workflow_officer_state.report_rel_path", "report_rel_path"),
        ("workflow_officer_state.officer_version", "officer_version"),
        ("workflow_officer_state.profile", "profile"),
        ("workflow_officer_state.mode", "mode"),
        ("workflow_officer_state.success", "success"),
        ("workflow_officer_state.finished_at", "finished_at"),
    ):
        if key not in wo:
            continue
        rows_html.append(
            f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'><code>{escape(label)}</code></td>"
            f"<td style='padding:4px 0;'><code>{_cell(wo.get(key))}</code></td></tr>"
        )
    for label, key in (
        ("workflow_officer_state.rollup.total_checks", "total_checks"),
        ("workflow_officer_state.rollup.hard_failures", "hard_failures"),
        ("workflow_officer_state.rollup.warnings", "warnings"),
        ("workflow_officer_state.rollup.infos", "infos"),
        ("workflow_officer_state.rollup.strict", "strict"),
    ):
        if key not in rollup:
            continue
        rows_html.append(
            f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'><code>{escape(label)}</code></td>"
            f"<td style='padding:4px 0;'><code>{_cell(rollup.get(key))}</code></td></tr>"
        )
    for label, key in (
        ("workflow_officer_state.executive.urgency_label", "urgency_label"),
        ("workflow_officer_state.executive.attention_rationale", "attention_rationale"),
    ):
        if key not in ex:
            continue
        rows_html.append(
            f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'><code>{escape(label)}</code></td>"
            f"<td style='padding:4px 0;'><code>{_cell(ex.get(key))}</code></td></tr>"
        )

    snap = str(wo.get("operator_snapshot_line") or "").strip()
    snap_p = (
        f"<p><strong>operator_snapshot_line</strong> (observation): <code>{escape(snap)}</code></p>"
        if snap
        else ""
    )

    pf_block = ""
    if pf:
        pf_lines: List[str] = []
        for label, key in (
            ("workflow_officer_state.primary_followup.check_id", "check_id"),
            (
                "workflow_officer_state.primary_followup.recommended_priority",
                "recommended_priority",
            ),
            ("workflow_officer_state.primary_followup.effective_level", "effective_level"),
            (
                "workflow_officer_state.primary_followup.recommended_action_excerpt",
                "recommended_action_excerpt",
            ),
        ):
            if key not in pf:
                continue
            pf_lines.append(
                f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'><code>{escape(label)}</code></td>"
                f"<td style='padding:4px 0;'><code>{_cell(pf.get(key))}</code></td></tr>"
            )
        if pf_lines:
            pf_block = (
                "<h3>Primary follow-up (payload)</h3>"
                "<p><em>From the operator report excerpt in the same artifact — visibility hint; "
                "not approval.</em></p>"
                "<table style='width:100%;border-collapse:collapse;font-size:0.9em;'>"
                "<tbody>"
                f"{''.join(pf_lines)}"
                "</tbody></table>"
            )

    top_raw = wo.get("top_followups")
    top_ul = ""
    if isinstance(top_raw, list) and top_raw:
        items: List[str] = []
        for row in top_raw[:3]:
            if not isinstance(row, dict):
                continue
            cid = str(row.get("check_id", "")).strip()
            if not cid:
                continue
            items.append(
                "<li>"
                f"<code>{escape(cid)}</code> "
                f"(priority {_cell(row.get('recommended_priority'))}, "
                f"level {_cell(row.get('effective_level'))})"
                "</li>"
            )
        if items:
            top_ul = (
                "<h3>Top follow-ups (bounded preview)</h3>"
                "<p><em>Up to three rows from the report — ordering hints only; not approval.</em></p>"
                "<ul>"
                f"{''.join(items)}"
                "</ul>"
            )

    ho_raw = wo.get("handoff_observation")
    ho = ho_raw if isinstance(ho_raw, dict) else {}
    ncpo_raw = wo.get("next_chat_preview_observation")
    ncpo = ncpo_raw if isinstance(ncpo_raw, dict) else {}

    hp_intro = (
        '<h3 id="operator-workflow-handoff-preview-observation">'
        "Handoff &amp; next-step preview (bounded observation)</h3>"
        "<p><em>Excerpts from the same report <code>summary</code> JSON — read-only. "
        "Not approval, not unlock, not launch authority, not a release go-signal; "
        "not a substitute for <code>policy_go_no_go_observation</code>.</em></p>"
    )
    ho_rows: List[str] = []
    if ho.get("present") is True:
        for label, key in (
            (
                "workflow_officer_state.handoff_observation.handoff_observation_schema_version",
                "handoff_observation_schema_version",
            ),
            (
                "workflow_officer_state.handoff_observation.handoff_schema_version",
                "handoff_schema_version",
            ),
            (
                "workflow_officer_state.handoff_observation.primary_followup_check_id",
                "primary_followup_check_id",
            ),
            (
                "workflow_officer_state.handoff_observation.top_followups_count",
                "top_followups_count",
            ),
            (
                "workflow_officer_state.handoff_observation.registry_pointer_count",
                "registry_pointer_count",
            ),
            (
                "workflow_officer_state.handoff_observation.merge_log_latest_pr_number",
                "merge_log_latest_pr_number",
            ),
        ):
            if key not in ho:
                continue
            ho_rows.append(
                f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'><code>{escape(label)}</code></td>"
                f"<td style='padding:4px 0;'><code>{_cell(ho.get(key))}</code></td></tr>"
            )
    else:
        ar = ho.get("absent_reason")
        ho_rows.append(
            f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'>"
            f"<code>workflow_officer_state.handoff_observation.absent_reason</code></td>"
            f"<td style='padding:4px 0;'><code>{_cell(ar)}</code></td></tr>"
        )
        ho_rows.append(
            f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'>"
            f"<code>workflow_officer_state.handoff_observation.present</code></td>"
            f"<td style='padding:4px 0;'><code>false</code></td></tr>"
        )
    ho_table = (
        "<h4>Handoff observation</h4>"
        "<table style='width:100%;border-collapse:collapse;font-size:0.9em;'>"
        "<tbody>"
        f"{''.join(ho_rows)}"
        "</tbody></table>"
    )

    ncp_rows: List[str] = []
    if ncpo.get("present") is True:
        for label, key in (
            (
                "workflow_officer_state.next_chat_preview_observation."
                "next_chat_preview_observation_schema_version",
                "next_chat_preview_observation_schema_version",
            ),
            (
                "workflow_officer_state.next_chat_preview_observation.preview_schema_version",
                "preview_schema_version",
            ),
            (
                "workflow_officer_state.next_chat_preview_observation.provenance_schema_version",
                "provenance_schema_version",
            ),
            (
                "workflow_officer_state.next_chat_preview_observation.primary_followup_check_id",
                "primary_followup_check_id",
            ),
            (
                "workflow_officer_state.next_chat_preview_observation.latest_pr_number",
                "latest_pr_number",
            ),
            (
                "workflow_officer_state.next_chat_preview_observation.registry_pointer_count",
                "registry_pointer_count",
            ),
        ):
            if key not in ncpo:
                continue
            ncp_rows.append(
                f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'><code>{escape(label)}</code></td>"
                f"<td style='padding:4px 0;'><code>{_cell(ncpo.get(key))}</code></td></tr>"
            )
        qids = ncpo.get("queued_followup_check_ids")
        if isinstance(qids, list) and qids:
            joined = ", ".join(escape(str(x)) for x in qids[:3])
            ncp_rows.append(
                "<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'><code>"
                "workflow_officer_state.next_chat_preview_observation.queued_followup_check_ids"
                "</code></td>"
                f"<td style='padding:4px 0;'><code>{joined}</code></td></tr>"
            )
        re_echo = ncpo.get("rollup_echo")
        if isinstance(re_echo, dict):
            for label, key in (
                (
                    "workflow_officer_state.next_chat_preview_observation.rollup_echo.total_checks",
                    "total_checks",
                ),
                (
                    "workflow_officer_state.next_chat_preview_observation.rollup_echo.hard_failures",
                    "hard_failures",
                ),
                (
                    "workflow_officer_state.next_chat_preview_observation.rollup_echo.warnings",
                    "warnings",
                ),
            ):
                if key not in re_echo:
                    continue
                ncp_rows.append(
                    f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'><code>{escape(label)}</code></td>"
                    f"<td style='padding:4px 0;'><code>{_cell(re_echo.get(key))}</code></td></tr>"
                )
    else:
        arn = ncpo.get("absent_reason")
        ncp_rows.append(
            f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'>"
            f"<code>workflow_officer_state.next_chat_preview_observation.absent_reason</code></td>"
            f"<td style='padding:4px 0;'><code>{_cell(arn)}</code></td></tr>"
        )
        ncp_rows.append(
            f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'>"
            f"<code>workflow_officer_state.next_chat_preview_observation.present</code></td>"
            f"<td style='padding:4px 0;'><code>false</code></td></tr>"
        )
    ncp_table = (
        "<h4>Next-step preview observation</h4>"
        "<table style='width:100%;border-collapse:collapse;font-size:0.9em;'>"
        "<tbody>"
        f"{''.join(ncp_rows)}"
        "</tbody></table>"
    )

    hp_block = f"{hp_intro}{ho_table}{ncp_table}"

    table_html = (
        "<h3>Workflow Officer snapshot (payload)</h3>"
        "<table style='width:100%;border-collapse:collapse;font-size:0.9em;'>"
        "<tbody>"
        f"{''.join(rows_html)}"
        "</tbody></table>"
    )
    return f"{head}{snap_p}{table_html}{pf_block}{top_ul}{hp_block}</div></div>"


def _render_operator_summary_dependencies_artifact_observations(
    dependencies_state: object,
) -> str:
    """Compact P85 and market-data-cache artifact lines for operator summary (read-only)."""
    if not isinstance(dependencies_state, dict):
        return ""
    p85 = dependencies_state.get("p85_exchange_observation")
    mdc = dependencies_state.get("market_data_cache_observation")
    subsections: List[str] = []
    p85_keys = (
        "data_source",
        "stale",
        "observation_reason",
        "reader_schema_version",
        "last_updated_utc",
        "artifact_path",
    )
    if isinstance(p85, dict):
        p85_lines = [
            "<h4>P85 exchange artifact</h4>",
            "<p><em>Persisted ingest-readiness artifact (newest <code>P85_RESULT.json</code> under "
            "search base) — <strong>not</strong> a live connectivity check from this page, "
            "<strong>not</strong> exchange execution truth, <strong>not</strong> governance approval.</em></p>",
        ]
        for key in p85_keys:
            if key in p85:
                p85_lines.append(
                    f"<p><strong>p85_exchange_observation.{key}</strong>: "
                    f"<code>{escape(str(p85.get(key)))}</code></p>"
                )
        subsections.append("".join(p85_lines))
    mdc_keys = (
        "data_source",
        "observation_reason",
        "reader_schema_version",
        "last_updated_utc",
        "market_data_cache",
    )
    if isinstance(mdc, dict):
        mdc_lines = [
            "<h4>Market data cache (local QC)</h4>",
            "<p><em>Offline parquet / filesystem QC — <strong>not</strong> a live feed check, "
            "<strong>not</strong> broker truth.</em></p>",
        ]
        for key in mdc_keys:
            if key in mdc:
                mdc_lines.append(
                    f"<p><strong>market_data_cache_observation.{key}</strong>: "
                    f"<code>{escape(str(mdc.get(key)))}</code></p>"
                )
        subsections.append("".join(mdc_lines))
    if not subsections:
        return ""
    return (
        '<section class="operator-summary-dependencies-artifacts" '
        'id="operator-summary-dependencies-artifact-observations">'
        "<h3>Dependencies — artifact observations (read-only)</h3>"
        "<p><strong>Observation only.</strong> Nested objects already under "
        "<code>dependencies_state</code> in this payload — same semantics as the "
        "<strong>Dependencies State</strong> card below. "
        "<strong>Not an approval,</strong> <strong>not an unlock,</strong> not a substitute for "
        "external governance. Compact aggregate line: <code>health_drift_observation</code> "
        "does not replace these artifact rows.</p>"
        f"{''.join(subsections)}"
        "</section>"
    )


def _render_operator_summary_update_officer_observation(uo_raw: object) -> str:
    """Compact Update Officer notifier lines for operator summary (read-only)."""
    if not isinstance(uo_raw, dict):
        return ""
    uo = uo_raw
    avail = bool(uo.get("available"))
    intro = (
        "<p><strong>Observation only.</strong> Same <code>update_officer_ui</code> payload as the "
        "<strong>Update Officer</strong> card below — notifier / local artifact visibility. "
        "<strong>Read-only tooling;</strong> <strong>not approval,</strong> <strong>not unlock,</strong> "
        "<strong>not a release go-signal;</strong> does not start Workflow Officer from this page. "
        "GET-only source ergonomics remain on the full page. "
        "<code>policy_go_no_go_observation</code> remains the compact policy aggregate "
        "(separate object).</p>"
    )
    parts: List[str] = [
        intro,
        f"<p><strong>update_officer_ui.available</strong>: <code>{escape(str(avail))}</code></p>",
    ]
    if not avail:
        msg = uo.get("empty_state_message")
        parts.append(
            f"<p><strong>empty_state_message</strong>: "
            f"{escape(str(msg if msg is not None else ''))}</p>"
        )
    else:
        for key in ("headline", "status", "next_topic", "severity", "reminder_class"):
            val = uo.get(key)
            if val is None:
                continue
            s = str(val).strip()
            if not s and key in ("headline", "next_topic"):
                continue
            parts.append(
                f"<p><strong>update_officer_ui.{key}</strong>: <code>{escape(s)}</code></p>"
            )
        rmr = uo.get("requires_manual_review")
        if rmr is not None:
            parts.append(
                f"<p><strong>update_officer_ui.requires_manual_review</strong>: "
                f"<code>{escape(str(rmr))}</code></p>"
            )
    return (
        '<section class="operator-summary-update-officer" '
        'id="operator-summary-update-officer">'
        "<h3>Update Officer (observation)</h3>"
        f"{''.join(parts)}"
        "</section>"
    )


def _render_operator_summary_stale_signals_observation(stale_raw: object) -> str:
    """Scalar stale_state lines for operator summary (read-only)."""
    if not isinstance(stale_raw, dict):
        return ""
    st = stale_raw
    row_parts: List[str] = []
    for key in ("summary", "balance", "position", "order", "exposure"):
        if key in st:
            row_parts.append(
                f"<p><strong>stale_state.{key}</strong>: "
                f"<code>{escape(str(st.get(key)))}</code></p>"
            )
    if not row_parts:
        return ""
    order_note = (
        "<p><em><strong>stale_state.order</strong> reflects local <code>live_runs</code> event-log "
        "recency when derivable — <strong>not</strong> exchange order-book state, "
        "<strong>not</strong> execution truth.</em></p>"
    )
    return (
        '<section class="operator-summary-stale-signals" '
        'id="operator-summary-stale-signals">'
        "<h3>Stale signals (observation)</h3>"
        "<p><strong>Observation only.</strong> Scalar fields from <code>stale_state</code> in this "
        "payload — same semantics as the <strong>Stale State</strong> card below. "
        "<strong>Not an approval,</strong> <strong>not an unlock,</strong> not broker or exchange "
        "reconciliation truth; local reconciliation / recency context only.</p>"
        f"{order_note}"
        f"{''.join(row_parts)}"
        "</section>"
    )


def _render_operator_summary_health_drift_observation(hdo_raw: object) -> str:
    """Compact ``health_drift_observation`` block for operator summary (read-only)."""
    if not isinstance(hdo_raw, dict):
        return ""
    hdo_status = escape(str(hdo_raw.get("status", "unknown")))
    hdo_summary = escape(str(hdo_raw.get("summary", "")))
    hdo_ds = escape(str(hdo_raw.get("data_source", "")))
    hdo_ver = escape(str(hdo_raw.get("reader_schema_version", "")))
    inner = (
        "<h3>Health / drift (observation)</h3>"
        "<p><strong>Observation only.</strong> Aggregate from top-level truth/freshness/coverage "
        "rollups, <code>evidence_state</code>, <code>dependencies_state</code>, and "
        "<code>stale_state</code> — <strong>not a live service health guarantee,</strong> "
        "<strong>not an approval,</strong> not broker truth.</p>"
        f"<p><strong>health_drift_observation.status</strong>: <code>{hdo_status}</code></p>"
        f"<p><strong>Summary:</strong> {hdo_summary}</p>"
        f"<p><strong>data_source:</strong> <code>{hdo_ds}</code> · "
        f"<strong>reader_schema_version:</strong> <code>{hdo_ver}</code></p>"
    )
    return (
        '<section class="operator-summary-health-drift-observation" '
        'id="operator-summary-health-drift-observation">'
        f"{inner}"
        "</section>"
    )


def _render_operator_summary_exposure_risk_observation(ero_raw: object) -> str:
    """Compact ``exposure_risk_observation`` block for operator summary (read-only)."""
    if not isinstance(ero_raw, dict):
        return ""
    ero_status = escape(str(ero_raw.get("status", "unknown")))
    ero_summary = escape(str(ero_raw.get("summary", "")))
    ero_ds = escape(str(ero_raw.get("data_source", "")))
    ero_ver = escape(str(ero_raw.get("reader_schema_version", "")))
    inner = (
        "<h3>Exposure / risk (observation)</h3>"
        "<p><strong>Observation only.</strong> Aggregate from <code>exposure_state</code>, "
        "<code>transfer_ambiguity_state</code>, <code>stale_state</code>, and "
        "<code>guard_state</code> treasury separation — <strong>not broker or exchange truth,</strong> "
        "<strong>not a risk approval,</strong> not a cap or limit unlock.</p>"
        f"<p><strong>exposure_risk_observation.status</strong>: <code>{ero_status}</code></p>"
        f"<p><strong>Summary:</strong> {ero_summary}</p>"
        f"<p><strong>data_source:</strong> <code>{ero_ds}</code> · "
        f"<strong>reader_schema_version:</strong> <code>{ero_ver}</code></p>"
    )
    return (
        '<section class="operator-summary-exposure-risk-observation" '
        'id="operator-summary-exposure-risk-observation">'
        f"{inner}"
        "</section>"
    )


def _render_operator_summary_incident_safety_observation(iso_raw: object) -> str:
    """Compact ``incident_safety_observation`` block for operator summary (read-only)."""
    if not isinstance(iso_raw, dict):
        return ""
    iso_status = escape(str(iso_raw.get("status", "unknown")))
    iso_summary = escape(str(iso_raw.get("summary", "")))
    iso_ds = escape(str(iso_raw.get("data_source", "")))
    iso_ver = escape(str(iso_raw.get("reader_schema_version", "")))
    inner = (
        "<h3>Incident / safety (observation)</h3>"
        "<p><strong>Observation only.</strong> Narrow aggregate from <code>incident_state</code> and "
        "<code>dependencies_state</code> (optional consistency hints from <code>policy_state</code> / "
        "<code>operator_state</code>) — <strong>not incident resolution,</strong> "
        "<strong>not an approval or unlock,</strong> not exchange truth. Overall gating posture: "
        "<code>safety_posture_observation</code>.</p>"
        f"<p><strong>incident_safety_observation.status</strong>: <code>{iso_status}</code></p>"
        f"<p><strong>Summary:</strong> {iso_summary}</p>"
        f"<p><strong>data_source:</strong> <code>{iso_ds}</code> · "
        f"<strong>reader_schema_version:</strong> <code>{iso_ver}</code></p>"
    )
    return (
        '<section class="operator-summary-incident-safety-observation" '
        'id="operator-summary-incident-safety-observation">'
        f"{inner}"
        "</section>"
    )


def _render_operator_summary_incident_observation_read_only(incident_observation_lines: str) -> str:
    """Detail ``incident_state`` / ``dependencies_state`` lines for operator summary (read-only)."""
    return (
        '<section class="operator-summary-incident-observation-read-only" '
        'id="operator-summary-incident-observation-read-only">'
        "<h3>Incident observation (read-only)</h3>"
        "<p>Existing incident/dependency rollups from this page&apos;s JSON payload.</p>"
        f"{incident_observation_lines}"
        "</section>"
    )


def _render_operator_summary_evidence_freshness_observation_read_only(
    evidence_observation_lines: str,
) -> str:
    """Detail ``evidence_state`` freshness lines for operator summary (read-only)."""
    return (
        '<section class="operator-summary-evidence-freshness-observation-read-only" '
        'id="operator-summary-evidence-freshness-observation-read-only">'
        "<h3>Evidence freshness observation (read-only)</h3>"
        "<p>Existing evidence freshness and audit rollups from this page&apos;s JSON payload.</p>"
        f"{evidence_observation_lines}"
        "</section>"
    )


def _render_operator_summary_system_status(system_status_lines: str) -> str:
    """Inline ``system_state`` scalar lines for operator summary (read-only)."""
    return (
        '<section class="operator-summary-system-status" '
        'id="operator-summary-system-status">'
        f"{system_status_lines}"
        "</section>"
    )


def _render_operator_summary_go_no_go_not_approval(go_no_go_inline: str) -> str:
    """Inline ``policy_state`` / ``incident_state`` go-no-go lines for operator summary (read-only)."""
    return (
        '<section class="operator-summary-go-no-go-not-approval" '
        'id="operator-summary-go-no-go-not-approval">'
        f"{go_no_go_inline}"
        "</section>"
    )


def _render_operator_summary_status_at_a_glance(glance_intro: str, glance_inner: str) -> str:
    """v3 executive rollup cards for operator summary (read-only)."""
    return (
        '<section class="operator-summary-status-at-a-glance" '
        'id="operator-summary-status-at-a-glance">'
        "<h3>Status at a glance</h3>"
        f"{glance_intro}"
        f"{glance_inner}"
        "</section>"
    )


def _render_operator_summary_system_state_observation(sso_raw: object) -> str:
    """Compact ``system_state_observation`` block for operator summary (read-only)."""
    if not isinstance(sso_raw, dict):
        return ""
    sso_status = escape(str(sso_raw.get("status", "unknown")))
    sso_summary = escape(str(sso_raw.get("summary", "")))
    sso_ds = escape(str(sso_raw.get("data_source", "")))
    sso_ver = escape(str(sso_raw.get("reader_schema_version", "")))
    inner = (
        "<h3>System / environment (observation)</h3>"
        "<p><strong>Observation only.</strong> Aggregate from <code>system_state</code> in this "
        "payload — <strong>not broker or exchange truth,</strong> "
        "<strong>not an environment guarantee.</strong> Truth/freshness posture: "
        "<code>health_drift_observation</code>; holistic gating: "
        "<code>safety_posture_observation</code>; policy/go-no-go: "
        "<code>policy_go_no_go_observation</code>.</p>"
        f"<p><strong>system_state_observation.status</strong>: <code>{sso_status}</code></p>"
        f"<p><strong>Summary:</strong> {sso_summary}</p>"
        f"<p><strong>data_source:</strong> <code>{sso_ds}</code> · "
        f"<strong>reader_schema_version:</strong> <code>{sso_ver}</code></p>"
    )
    return (
        '<section class="operator-summary-system-state-observation" '
        'id="operator-summary-system-state-observation">'
        f"{inner}"
        "</section>"
    )


def _render_operator_summary_policy_go_no_go_observation(pgngo_raw: object) -> str:
    """Compact ``policy_go_no_go_observation`` block for operator summary (read-only)."""
    if not isinstance(pgngo_raw, dict):
        return ""
    pgngo_status = escape(str(pgngo_raw.get("status", "unknown")))
    pgngo_summary = escape(str(pgngo_raw.get("summary", "")))
    pgngo_ds = escape(str(pgngo_raw.get("data_source", "")))
    pgngo_ver = escape(str(pgngo_raw.get("reader_schema_version", "")))
    inner = (
        "<h3>Policy / go-no-go (observation)</h3>"
        "<p><strong>Observation only.</strong> Compact aggregate from <code>policy_state</code>, "
        "<code>incident_state</code>, and <code>operator_state</code> in this payload — "
        "<strong>not a live go decision,</strong> <strong>not approval or unlock,</strong> "
        "not broker truth. Holistic gating posture: <code>safety_posture_observation</code> "
        "(separate snapshot).</p>"
        f"<p><strong>policy_go_no_go_observation.status</strong>: <code>{pgngo_status}</code></p>"
        f"<p><strong>Summary:</strong> {pgngo_summary}</p>"
        f"<p><strong>data_source:</strong> <code>{pgngo_ds}</code> · "
        f"<strong>reader_schema_version:</strong> <code>{pgngo_ver}</code></p>"
    )
    return (
        '<section class="operator-summary-policy-go-no-go-observation" '
        'id="operator-summary-policy-go-no-go-observation">'
        f"{inner}"
        "</section>"
    )


def _render_operator_summary_safety_posture_observation(spo_raw: object) -> str:
    """Compact ``safety_posture_observation`` block for operator summary (read-only)."""
    if not isinstance(spo_raw, dict):
        return ""
    spo_status = escape(str(spo_raw.get("status", "unknown")))
    spo_summary = escape(str(spo_raw.get("summary", "")))
    spo_ds = escape(str(spo_raw.get("data_source", "")))
    spo_ver = escape(str(spo_raw.get("reader_schema_version", "")))
    inner = (
        "<h3>Safety / gating posture (observation)</h3>"
        "<p><strong>Observation only.</strong> Single aggregate from existing "
        "<code>policy_state</code>, <code>guard_state</code>, <code>incident_state</code>, "
        "<code>stale_state</code>, and <code>dependencies_state</code> rollups in this "
        "payload — <strong>not an approval, not an unlock,</strong> not broker or exchange "
        "truth.</p>"
        f"<p><strong>safety_posture_observation.status</strong>: <code>{spo_status}</code></p>"
        f"<p><strong>Summary:</strong> {spo_summary}</p>"
        f"<p><strong>data_source:</strong> <code>{spo_ds}</code> · "
        f"<strong>reader_schema_version:</strong> <code>{spo_ver}</code></p>"
    )
    return (
        '<section class="operator-summary-safety-posture-observation" '
        'id="operator-summary-safety-posture-observation">'
        f"{inner}"
        "</section>"
    )


def _render_operator_summary_governance_boundary_observation(gbo_raw: object) -> str:
    """Compact ``governance_boundary_observation`` block for operator summary (read-only)."""
    if not isinstance(gbo_raw, dict):
        return ""
    gbo_status = escape(str(gbo_raw.get("status", "unknown")))
    gbo_summary = escape(str(gbo_raw.get("summary", "")))
    gbo_ds = escape(str(gbo_raw.get("data_source", "")))
    gbo_ver = escape(str(gbo_raw.get("reader_schema_version", "")))
    inner = (
        "<h3>Governance / AI boundary (observation)</h3>"
        "<p><strong>Observation only.</strong> Aggregate from <code>ai_boundary_state</code> and "
        "<code>human_supervision_state</code> (optional hints from <code>guard_state</code> / "
        "<code>evidence_state</code>) — <strong>not governance or AI approval,</strong> "
        "<strong>not a supervision waiver,</strong> not broker truth. Holistic gating: "
        "<code>safety_posture_observation</code>; evidence: <code>evidence_audit_observation</code>.</p>"
        f"<p><strong>governance_boundary_observation.status</strong>: <code>{gbo_status}</code></p>"
        f"<p><strong>Summary:</strong> {gbo_summary}</p>"
        f"<p><strong>data_source:</strong> <code>{gbo_ds}</code> · "
        f"<strong>reader_schema_version:</strong> <code>{gbo_ver}</code></p>"
    )
    return (
        '<section class="operator-summary-governance-boundary-observation" '
        'id="operator-summary-governance-boundary-observation">'
        f"{inner}"
        "</section>"
    )


def _render_operator_summary_run_session_observation(rso_raw: object) -> str:
    """Compact ``run_session_observation`` block for operator summary (read-only)."""
    if not isinstance(rso_raw, dict):
        return ""
    rso_status = escape(str(rso_raw.get("status", "unknown")))
    rso_summary = escape(str(rso_raw.get("summary", "")))
    rso_ds = escape(str(rso_raw.get("data_source", "")))
    rso_ver = escape(str(rso_raw.get("reader_schema_version", "")))
    inner = (
        "<h3>Run / session (observation)</h3>"
        "<p><strong>Observation only.</strong> Aggregate from <code>run_state</code>, "
        "<code>session_end_mismatch_state</code>, <code>stale_state</code>, and "
        "<code>operator_state</code> in this payload — <strong>not a session guarantee,</strong> "
        "<strong>not an approval,</strong> not live exchange session truth.</p>"
        f"<p><strong>run_session_observation.status</strong>: <code>{rso_status}</code></p>"
        f"<p><strong>Summary:</strong> {rso_summary}</p>"
        f"<p><strong>data_source:</strong> <code>{rso_ds}</code> · "
        f"<strong>reader_schema_version:</strong> <code>{rso_ver}</code></p>"
    )
    return (
        '<section class="operator-summary-run-session-observation" '
        'id="operator-summary-run-session-observation">'
        f"{inner}"
        "</section>"
    )


def _render_operator_summary_evidence_audit_observation(eao_raw: object) -> str:
    """Compact ``evidence_audit_observation`` block for operator summary (read-only)."""
    if not isinstance(eao_raw, dict):
        return ""
    eao_status = escape(str(eao_raw.get("status", "unknown")))
    eao_summary = escape(str(eao_raw.get("summary", "")))
    eao_ds = escape(str(eao_raw.get("data_source", "")))
    eao_ver = escape(str(eao_raw.get("reader_schema_version", "")))
    inner = (
        "<h3>Evidence / audit (observation)</h3>"
        "<p><strong>Observation only.</strong> Aggregate from <code>evidence_state</code> in this "
        "payload — <strong>not audit clearance,</strong> <strong>not a compliance pass/fail,</strong> "
        "not broker truth. Service/drift posture stays in "
        "<code>health_drift_observation</code> (separate snapshot).</p>"
        f"<p><strong>evidence_audit_observation.status</strong>: <code>{eao_status}</code></p>"
        f"<p><strong>Summary:</strong> {eao_summary}</p>"
        f"<p><strong>data_source:</strong> <code>{eao_ds}</code> · "
        f"<strong>reader_schema_version:</strong> <code>{eao_ver}</code></p>"
    )
    return (
        '<section class="operator-summary-evidence-audit-observation" '
        'id="operator-summary-evidence-audit-observation">'
        f"{inner}"
        "</section>"
    )


def _render_operator_summary_session_end_mismatch(sem_raw: object) -> str:
    """Compact ``session_end_mismatch_state`` lines for operator summary (read-only)."""
    if not isinstance(sem_raw, dict):
        return ""
    sem = sem_raw
    keys = (
        "status",
        "summary",
        "blocked_next_session",
        "data_source",
        "observation_reason",
        "reader_schema_version",
        "runbook",
    )
    parts: List[str] = []
    for k in keys:
        if k in sem:
            parts.append(
                f"<p><strong>session_end_mismatch_state.{k}</strong>: "
                f"<code>{escape(str(sem.get(k)))}</code></p>"
            )
    if not parts:
        return ""
    return (
        '<section class="operator-summary-session-end-mismatch" '
        'id="operator-summary-session-end-mismatch">'
        "<h3>Session end mismatch (observation)</h3>"
        "<p><strong>Observation only.</strong> Local session registry / <code>live_runs</code> "
        "artifact read model — <strong>not</strong> broker enforcement, <strong>not</strong> approval, "
        "<strong>not</strong> unlock. Same semantics as the <strong>Session End Mismatch</strong> card. "
        "<code>blocked_next_session</code> is a hint only, not a gate. "
        "<code>policy_go_no_go_observation</code> remains the compact policy aggregate.</p>"
        f"{''.join(parts)}"
        "</section>"
    )


def _render_operator_summary_transfer_ambiguity(ta_raw: object) -> str:
    """Compact ``transfer_ambiguity_state`` lines for operator summary (read-only)."""
    if not isinstance(ta_raw, dict):
        return ""
    ta = ta_raw
    keys = (
        "status",
        "summary",
        "data_source",
        "observation_reason",
        "runbook_ref",
        "operator_attention_hint",
        "reader_schema_version",
    )
    parts: List[str] = []
    for k in keys:
        if k in ta:
            parts.append(
                f"<p><strong>transfer_ambiguity_state.{k}</strong>: "
                f"<code>{escape(str(ta.get(k)))}</code></p>"
            )
    if not parts:
        return ""
    return (
        '<section class="operator-summary-transfer-ambiguity" '
        'id="operator-summary-transfer-ambiguity">'
        "<h3>Transfer / treasury ambiguity (observation)</h3>"
        "<p><strong>Observation only.</strong> Local cockpit signals only — "
        "<strong>not</strong> exchange transfer truth, <strong>not</strong> approval, "
        "<strong>not</strong> all-clear. Same semantics as the "
        "<strong>Transfer / Treasury ambiguity</strong> card. "
        "<code>operator_attention_hint</code> is a nudge only, not a gate.</p>"
        f"{''.join(parts)}"
        "</section>"
    )


def _render_operator_summary_run_state(rs_raw: object) -> str:
    """Compact ``run_state`` lines for operator summary (read-only; same fields as main-page card)."""
    if not isinstance(rs_raw, dict):
        return ""
    rs = rs_raw
    parts: List[str] = []
    for label, key in _RUN_STATE_OBSERVATION_FIELD_ROWS:
        if key not in rs:
            continue
        parts.append(
            f"<p><strong>{escape(label)}</strong>: "
            f"<code>{escape(_format_run_state_observation_value(rs.get(key)))}</code></p>"
        )
    if not parts:
        return ""
    return (
        '<section class="operator-summary-run-state" '
        'id="operator-summary-run-state">'
        "<h3>Run state (observation)</h3>"
        "<p><strong>Observation only.</strong> Same <code>run_state</code> object as "
        "<code>GET /api/ops-cockpit</code> and the <strong>Run state — observed rollup</strong> card "
        "below — local snapshot, <strong>not</strong> start/stop control, <strong>not</strong> execution "
        "authority, <strong>not</strong> governance or go/no-go. "
        "<code>run_session_observation</code> remains the compact aggregate line above.</p>"
        f"{''.join(parts)}"
        "</section>"
    )


def _render_operator_summary_exposure_state(exp_raw: object) -> str:
    """Compact ``exposure_state`` lines for operator summary (read-only; scalars + tiny list counts)."""
    if not isinstance(exp_raw, dict):
        return ""
    ex = exp_raw
    scalar_rows: Tuple[Tuple[str, str], ...] = (
        ("exposure_state.summary", "summary"),
        ("exposure_state.treasury_separation", "treasury_separation"),
        ("exposure_state.risk_status", "risk_status"),
        ("exposure_state.observed_exposure", "observed_exposure"),
        ("exposure_state.observed_ccy", "observed_ccy"),
        ("exposure_state.data_source", "data_source"),
        ("exposure_state.last_updated_utc", "last_updated_utc"),
        ("exposure_state.stale", "stale"),
    )
    parts: List[str] = []
    for label, key in scalar_rows:
        if key not in ex:
            continue
        parts.append(
            f"<p><strong>{escape(label)}</strong>: "
            f"<code>{escape(_format_run_state_observation_value(ex.get(key)))}</code></p>"
        )
    caps = ex.get("caps_configured")
    if isinstance(caps, list) and caps:
        parts.append(
            "<p><strong>exposure_state.caps_configured</strong> (count): "
            f"<code>{len(caps)}</code></p>"
        )
    ebs = ex.get("exposure_by_symbol")
    if isinstance(ebs, dict) and ebs:
        parts.append(
            "<p><strong>exposure_state.exposure_by_symbol</strong> (count): "
            f"<code>{len(ebs)}</code></p>"
        )
    if not parts:
        return ""
    return (
        '<section class="operator-summary-exposure-state" '
        'id="operator-summary-exposure-state">'
        "<h3>Exposure state (observation)</h3>"
        "<p><strong>Observation only.</strong> Same <code>exposure_state</code> object as "
        "<code>GET /api/ops-cockpit</code> and the <strong>Exposure State</strong> card below — "
        "local read-model snapshot, <strong>not</strong> broker or exchange truth, "
        "<strong>not</strong> approval or unlock, <strong>not</strong> cap/risk mandate. "
        "<code>exposure_risk_observation</code> remains the compact aggregate above.</p>"
        f"{''.join(parts)}"
        "</section>"
    )


def _render_dependencies_state_card_body(dependencies: Dict[str, object]) -> str:
    """HTML inner block for Dependencies State — ``dependencies_state`` keys (read-only)."""
    dep = dependencies if isinstance(dependencies, dict) else {}
    deg_raw = dep.get("degraded")
    degraded_rows: List[str] = []
    if isinstance(deg_raw, list):
        degraded_rows = [str(item) for item in deg_raw]
    elif deg_raw is not None:
        degraded_rows = [str(deg_raw)]
    degraded_ul = (
        "".join(f"<li><code>{escape(item)}</code></li>" for item in degraded_rows[:12])
        or "<li>none</li>"
    )
    mdc = dep.get("market_data_cache")
    mdc_display = "n/a" if mdc is None else str(mdc)
    p85 = dep.get("p85_exchange_observation")
    p85_block = ""
    if isinstance(p85, dict):
        p85_block = (
            "<p><em>P85 exchange label: artifact observation only (newest "
            f"<code>{escape(str(p85.get('provenance', {}).get('selected_artifact', 'P85_RESULT.json')))}</code> "
            "under search base). Not a live connectivity check from this page; not broker truth.</em></p>"
            f"<p><strong>P85 observation reason:</strong> <code>"
            f"{escape(str(p85.get('observation_reason', 'n/a')))}</code></p>"
            f"<p><strong>P85 artifact (path hint):</strong> <code>"
            f"{escape(str(p85.get('artifact_path') or 'n/a'))}</code></p>"
            f"<p><strong>P85 last_updated_utc (artifact mtime):</strong> "
            f"{escape(str(p85.get('last_updated_utc') or 'n/a'))}</p>"
            f"<p><strong>P85 stale (age threshold):</strong> "
            f"{escape(str(p85.get('stale', 'n/a')))}</p>"
            f"<p><strong>P85 reader schema:</strong> <code>"
            f"{escape(str(p85.get('reader_schema_version', 'n/a')))}</code></p>"
        )
    mdc_obs = dep.get("market_data_cache_observation")
    mdc_obs_block = ""
    if isinstance(mdc_obs, dict):
        mdc_obs_block = (
            "<p><em>Market data cache label: <strong>local parquet / filesystem observation only</strong> "
            "(offline QC via <code>check_data_health_only</code>). Not a live feed check; "
            "not broker truth; not approval.</em></p>"
            f"<p><strong>Cache observation reason:</strong> <code>"
            f"{escape(str(mdc_obs.get('observation_reason', 'n/a')))}</code></p>"
            f"<p><strong>Cache data_source:</strong> <code>"
            f"{escape(str(mdc_obs.get('data_source', 'n/a')))}</code></p>"
            f"<p><strong>Cache last_updated_utc (data end hint):</strong> "
            f"{escape(str(mdc_obs.get('last_updated_utc') or 'n/a'))}</p>"
            f"<p><strong>Cache reader schema:</strong> <code>"
            f"{escape(str(mdc_obs.get('reader_schema_version', 'n/a')))}</code></p>"
        )
    return (
        "<p><strong>Read-only dependencies / health-drift observation.</strong> "
        "Existing payload fields only; not approval, not unlock.</p>"
        f'<p><strong>Summary:</strong> <span class="chip"><code>{escape(str(dep.get("summary", "unknown")))}'
        f"</code></span></p>"
        f"<p><strong>Exchange:</strong> {escape(str(dep.get('exchange', 'unknown')))}</p>"
        "<p><em>Exchange rollup may include persisted P85 ingest-readiness artifacts; "
        "see P85 block below — not a live check performed by the Cockpit build.</em></p>"
        f"{p85_block}"
        f"{mdc_obs_block}"
        f"<p><strong>Telemetry:</strong> {escape(str(dep.get('telemetry', 'unknown')))}</p>"
        f"<p><strong>market_data_cache:</strong> <code>{escape(mdc_display)}</code></p>"
        "<p><em>Rollup above mirrors local cache QC when config and cache path exist; "
        "see cache observation block — not live market data.</em></p>"
        "<p><strong>Degraded signals (preview):</strong></p>"
        f"<ul>{degraded_ul}</ul>"
    )


def _render_evidence_state_card_body(evidence: Dict[str, object]) -> str:
    """HTML inner block for Evidence State — existing ``evidence_state`` keys only (read-only)."""
    ev = evidence if isinstance(evidence, dict) else {}
    sf_raw = ev.get("source_freshness")
    if isinstance(sf_raw, dict):
        sf_block = (
            "<p><strong>source_freshness (counts):</strong></p><ul>"
            f"<li><code>fresh</code>: {escape(str(sf_raw.get('fresh', 'n/a')))}</li>"
            f"<li><code>stale</code>: {escape(str(sf_raw.get('stale', 'n/a')))}</li>"
            f"<li><code>older</code>: {escape(str(sf_raw.get('older', 'n/a')))}</li>"
            "</ul>"
        )
    else:
        sf_block = (
            f"<p><strong>source_freshness:</strong> <code>"
            f"{escape(str(sf_raw if sf_raw is not None else 'unknown'))}</code></p>"
        )
    tel = ev.get("telemetry_evidence")
    tel_display = "n/a" if tel is None else str(tel)
    return (
        "<p><strong>Read-only evidence / audit observation.</strong> "
        "Existing payload fields only; not approval, not unlock.</p>"
        f'<p><strong>Summary:</strong> <span class="chip"><code>{escape(str(ev.get("summary", "unknown")))}'
        f"</code></span></p>"
        f"<p><strong>freshness_status:</strong> {escape(str(ev.get('freshness_status', 'unknown')))}</p>"
        f"<p><strong>audit_trail:</strong> {escape(str(ev.get('audit_trail', 'unknown')))}</p>"
        f"<p><strong>last_verified_utc:</strong> {escape(str(ev.get('last_verified_utc', 'n/a')))}</p>"
        f"{sf_block}"
        f"<p><strong>telemetry_evidence:</strong> <code>{escape(tel_display)}</code></p>"
    )


def build_workflow_officer_panel_context(repo_root: Path | None = None) -> Dict[str, object]:
    """Read-only WebUI slice: latest Workflow Officer ``report.json`` (no writes)."""
    from src.ops.workflow_officer import build_workflow_officer_dashboard_view

    root = repo_root if repo_root is not None else Path.cwd()
    return build_workflow_officer_dashboard_view(root)


def build_ops_cockpit_payload(
    repo_root: Path | None = None,
    telemetry_root: Path | None = None,
    live_runs_root: Path | None = None,
    config_path: Path | None = None,
    update_officer_notifier_path: Path | str | None = None,
    update_officer_run_dir: Path | str | None = None,
    update_officer_source_conflict: bool = False,
) -> Dict[str, object]:
    truth_docs = discover_truth_docs(repo_root=repo_root)
    groups = _grouped_sources(truth_docs)
    group_summaries = {name: _group_summary(items) for name, items in groups.items()}
    truth_state = build_truth_state(truth_docs)
    v3_summary = _build_v3_executive_summary(truth_state, group_summaries)
    _config_path = config_path or (repo_root / "config" / "config.toml" if repo_root else None)
    _config_load_status = "not_loaded"
    _trading_environment: Optional[str] = None
    _bounded_pilot_mode: Optional[bool] = None
    _config_enabled = False
    _config_armed = False
    _config_dry_run = True
    _config_confirm_token_required = True
    if _config_path and _config_path.exists():
        try:
            from src.core.environment import get_environment_from_config
            from src.core.peak_config import load_config

            peak_config = load_config(_config_path)
            env_config = get_environment_from_config(peak_config)
            _config_enabled = bool(env_config.enable_live_trading)
            _config_armed = bool(env_config.live_mode_armed)
            _config_dry_run = bool(env_config.live_dry_run_mode)
            _config_confirm_token_required = bool(env_config.require_confirm_token)
            _trading_environment = str(env_config.environment.value)
            _bounded_pilot_mode = bool(env_config.bounded_pilot_mode)
            _config_load_status = "loaded"
        except Exception:
            _config_load_status = "unavailable"
    _kill_switch_active = False
    _ks_path = (
        repo_root / "data" / "kill_switch" / "state.json"
        if repo_root
        else Path("data/kill_switch/state.json")
    )
    if _ks_path.exists():
        try:
            import json

            with open(_ks_path, encoding="utf-8") as f:
                _ks_data = json.load(f)
            _ks_state = str(_ks_data.get("state", "")).upper()
            _kill_switch_active = _ks_state in ("KILLED", "RECOVERING")
        except Exception:
            pass
    guard_state = {
        "no_trade_baseline": "reference",
        "deny_by_default": "active",
        "treasury_separation": "enforced",
        "enabled": _config_enabled,
        "armed": _config_armed,
        "dry_run": _config_dry_run,
        "confirm_token_required": _config_confirm_token_required,
        "kill_switch_active": _kill_switch_active,
    }
    _policy_blocked = (
        (not guard_state["enabled"])
        or (not guard_state["armed"])
        or guard_state["kill_switch_active"]
    )
    policy_state = {
        "action": "NO_TRADE" if _policy_blocked else "TRADE_READY",
        "confirm_token_required": guard_state["confirm_token_required"],
        "enabled": guard_state["enabled"],
        "armed": guard_state["armed"],
        "dry_run": guard_state["dry_run"],
        "blocked": _policy_blocked,
        "summary": "blocked" if _policy_blocked else "armed",
        "kill_switch_active": guard_state["kill_switch_active"],
    }
    operator_state = {
        "disabled": not guard_state["enabled"],
        "enabled": guard_state["enabled"],
        "armed": guard_state["armed"],
        "dry_run": guard_state["dry_run"],
        "blocked": (not guard_state["enabled"]) or (not guard_state["armed"]),
        "kill_switch_active": guard_state["kill_switch_active"],
    }
    _last_run_status = "unknown"
    _session_active = False
    _sessions_root = (
        repo_root / "reports" / "experiments" / "live_sessions"
        if repo_root
        else Path("reports/experiments/live_sessions")
    )
    _registry_session_count: Optional[int] = None
    _registry_last_started_at: Optional[str] = None
    if _sessions_root.exists():
        try:
            from src.experiments.live_session_registry import (
                get_session_summary,
                list_session_records,
            )

            records = list_session_records(base_dir=_sessions_root, limit=1)
            if records:
                _last_run_status = str(records[0].status or "unknown")
            summary = get_session_summary(base_dir=_sessions_root)
            _session_active = (summary.get("by_status", {}).get("started", 0) or 0) > 0
            _registry_session_count = int(summary.get("num_sessions", 0) or 0)
            las = summary.get("last_started_at")
            if isinstance(las, str) and las.strip():
                _registry_last_started_at = las.strip()
        except Exception:
            pass
    run_state: Dict[str, object] = {
        "status": "active" if _session_active else "idle",
        "active": _session_active,
        "last_run_status": _last_run_status,
        "session_active": _session_active,
        "generated_at": truth_state["last_verified_utc"],
        "freshness_status": v3_summary["freshness_status"],
    }
    if _registry_session_count is not None:
        run_state["registry_session_count"] = _registry_session_count
    if _registry_last_started_at is not None:
        run_state["registry_last_started_at"] = _registry_last_started_at
    freshness_ok = v3_summary["freshness_status"] == "ok"
    _tel_root = (
        telemetry_root
        if telemetry_root is not None
        else (repo_root / "logs" / "execution" if repo_root else Path("logs/execution"))
    )
    _exec_events_root = repo_root / "out" / "ops" / "execution_events" if repo_root else None
    _tel_status = "unknown"
    _degraded: List[str] = []
    _reports: List[object] = []
    if _tel_root.exists():
        try:
            from src.execution.telemetry_health import run_health_checks

            _reports.append(run_health_checks(_tel_root))
        except Exception:
            pass
    if _exec_events_root and _exec_events_root.exists():
        try:
            from src.execution.telemetry_health import run_health_checks

            _reports.append(run_health_checks(_exec_events_root))
        except Exception:
            pass
    if _reports:
        _tel_status = (
            "critical"
            if any(r.status == "critical" for r in _reports)
            else ("warn" if any(r.status == "warn" for r in _reports) else "ok")
        )
        for r in _reports:
            _degraded.extend(c.name for c in r.checks if c.status in ("warn", "critical"))
        _degraded = list(dict.fromkeys(_degraded))
    _degraded_incident = not freshness_ok or _tel_status in ("warn", "critical")
    _incident_stop_invoked, _incident_stop_source = _detect_incident_stop(repo_root)
    _pt_force_no_trade = os.environ.get("PT_FORCE_NO_TRADE")
    _pt_enabled = os.environ.get("PT_ENABLED")
    _pt_armed = os.environ.get("PT_ARMED")
    _entry_permitted = not _policy_blocked
    _ks_source = "data/kill_switch/state.json" if _ks_path.exists() else "unavailable"
    _op_auth = (
        "kill_switch_active"
        if _kill_switch_active
        else "blocked"
        if operator_state["blocked"]
        else "degraded"
        if _degraded_incident
        else "normal"
    )
    _op_reason = (
        "Kill switch state from data/kill_switch/state.json"
        if _kill_switch_active
        else "Operator gates not armed (enabled/armed)"
        if operator_state["blocked"]
        else "Degraded telemetry or freshness"
        if _degraded_incident
        else "No operator-critical incident-state signal mapped"
    )
    incident_state = {
        "status": ("blocked" if operator_state["blocked"] or _kill_switch_active else "normal"),
        "blocked": operator_state["blocked"],
        "kill_switch_active": _kill_switch_active,
        "degraded": _degraded_incident,
        "requires_operator_attention": (
            operator_state["blocked"] or _kill_switch_active or _degraded_incident
        ),
        "summary": (
            "blocked"
            if operator_state["blocked"] or _kill_switch_active
            else "degraded"
            if _degraded_incident
            else "normal"
        ),
        "incident_stop_invoked": _incident_stop_invoked,
        "incident_stop_source": _incident_stop_source,
        "pt_force_no_trade": _pt_force_no_trade,
        "pt_enabled": _pt_enabled,
        "pt_armed": _pt_armed,
        "kill_switch_source": _ks_source,
        "entry_permitted": _entry_permitted,
        "risk_gate_kill_switch_active": _kill_switch_active,
        "operator_authoritative_state": _op_auth,
        "operator_state_reason": _op_reason,
    }
    caps_configured = (
        _build_caps_configured_from_config(_config_path)
        if _config_path and _config_path.exists()
        else []
    )
    exposure_state = {
        "summary": "no_live_context",
        "treasury_separation": guard_state["treasury_separation"],
        "caps_configured": caps_configured,
        "risk_status": "unknown",
    }
    _live_runs = (
        live_runs_root
        if live_runs_root is not None
        else (repo_root / "live_runs" if repo_root else Path("live_runs"))
    )
    if _live_runs.exists():
        try:
            from src.live.exposure_reader import get_live_runs_exposure_summary

            _exp = get_live_runs_exposure_summary(_live_runs)
            if _exp.get("observed_exposure") is not None:
                exposure_state["observed_exposure"] = _exp["observed_exposure"]
                exposure_state["observed_ccy"] = _exp.get("observed_ccy", "unknown")
                exposure_state["last_updated_utc"] = _exp.get("last_updated_utc")
                exposure_state["data_source"] = "live_runs"
                if _exp.get("stale"):
                    exposure_state["summary"] = "unknown"
                    exposure_state["stale"] = True
                else:
                    exposure_state["summary"] = "ok"
                    exposure_state["stale"] = False
                if _exp.get("exposure_by_symbol"):
                    exposure_state["exposure_by_symbol"] = _exp["exposure_by_symbol"]
        except Exception:
            pass
    # Derived risk_status heuristic: observed vs max_total_exposure, then symbol-level
    _obs = exposure_state.get("observed_exposure")
    _cap_total = next(
        (c for c in caps_configured if c.get("limit_id") == "max_total_exposure"),
        None,
    )
    _cap_symbol = next(
        (c for c in caps_configured if c.get("limit_id") == "max_symbol_exposure"),
        None,
    )
    if _obs is not None and _cap_total is not None:
        try:
            cap_val = float(_cap_total.get("cap_value", 0))
            if cap_val > 0:
                util = float(_obs) / cap_val
                if util >= 1.0:
                    exposure_state["risk_status"] = "critical"
                elif util >= 0.8:
                    exposure_state["risk_status"] = "warn"
                else:
                    exposure_state["risk_status"] = "ok"
        except (TypeError, ValueError):
            pass
    _exp_by_sym = exposure_state.get("exposure_by_symbol") or {}
    if _exp_by_sym and _cap_symbol is not None:
        try:
            sym_cap = float(_cap_symbol.get("cap_value", 0))
            if sym_cap > 0:
                for _sym, _sym_exp in _exp_by_sym.items():
                    _sym_util = float(_sym_exp) / sym_cap
                    if _sym_util >= 1.0:
                        exposure_state["risk_status"] = "critical"
                        break
                    if _sym_util >= 0.8 and exposure_state.get("risk_status") != "critical":
                        exposure_state["risk_status"] = "warn"
        except (TypeError, ValueError):
            pass
    # Stale state surface (reconciliation hardening)
    _exp_stale = exposure_state.get("stale", False)
    _has_exposure = exposure_state.get("data_source") == "live_runs"
    _position_stale = "stale" if _exp_stale else ("ok" if _has_exposure else "unknown")
    _exposure_stale = "stale" if _exp_stale else ("ok" if _has_exposure else "unknown")
    _order_stale = "unknown"
    if _live_runs.exists():
        try:
            from src.live.order_staleness_reader import get_live_runs_order_staleness

            _ord_sig = get_live_runs_order_staleness(_live_runs)
            _os_val = str(_ord_sig.get("order_staleness", "unknown"))
            if _os_val in ("ok", "stale"):
                _order_stale = _os_val
        except Exception:
            pass
    _stale_signals = [_position_stale, _exposure_stale, _order_stale]
    _stale_summary = (
        "stale" if "stale" in _stale_signals else ("ok" if "ok" in _stale_signals else "unknown")
    )
    # Balance semantics visibility (operator-facing; from LivePortfolioSnapshot when available)
    _balance_semantic_state: Optional[str] = None
    _balance_reason_code: Optional[str] = None
    _balance_operator_visible_state: Optional[str] = None
    if _config_path and _config_path.exists():
        try:
            from src.core.peak_config import load_config
            from src.live.broker_base import PaperBroker
            from src.live.portfolio_monitor import LivePortfolioMonitor

            peak_config = load_config(_config_path)
            starting_cash = float(peak_config.get("general.starting_capital", 10000.0))
            base_currency = str(peak_config.get("general.base_currency", "EUR"))
            broker = PaperBroker(
                starting_cash=starting_cash,
                base_currency=base_currency,
                log_to_console=False,
            )
            monitor = LivePortfolioMonitor(broker)
            snapshot = monitor.snapshot()
            if snapshot is not None:
                _balance_semantic_state = getattr(snapshot, "balance_semantic_state", None)
                _balance_reason_code = getattr(snapshot, "balance_reason_code", None)
                _balance_operator_visible_state = getattr(
                    snapshot, "balance_operator_visible_state", None
                )
        except Exception:
            pass
    balance_semantics_state = {
        "balance_semantic_state": _balance_semantic_state,
        "balance_reason_code": _balance_reason_code,
        "balance_operator_visible_state": _balance_operator_visible_state,
    }
    _balance_stale = "unknown"
    if _balance_semantic_state == "balance_semantics_blocked":
        _balance_stale = "blocked"
    elif _balance_semantic_state == "balance_semantics_warning":
        _balance_stale = "warn"
    elif _balance_semantic_state == "balance_semantics_clear":
        _balance_stale = "ok"
    stale_state = {
        "balance": _balance_stale,
        "position": _position_stale,
        "order": _order_stale,
        "exposure": _exposure_stale,
        "summary": _stale_summary,
    }
    try:
        from src.live.session_end_mismatch_reader import build_session_end_mismatch_state

        session_end_mismatch_state = build_session_end_mismatch_state(
            sessions_root=_sessions_root,
            live_runs_root=_live_runs,
            stale_state=stale_state,
            balance_semantics_state=balance_semantics_state,
        )
    except Exception:
        session_end_mismatch_state = {
            "status": "unknown",
            "summary": "no_signal",
            "blocked_next_session": False,
            "runbook": "RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH",
            "data_source": "none",
            "observation_reason": "reader_unavailable",
            "provenance": {},
            "reader_schema_version": "session_end_mismatch_reader/error",
        }
    try:
        from src.live.transfer_ambiguity_reader import build_transfer_ambiguity_state

        transfer_ambiguity_state = build_transfer_ambiguity_state(
            guard_state=guard_state,
            stale_state=stale_state,
            balance_semantics_state=balance_semantics_state,
            exposure_state=exposure_state,
        )
    except Exception:
        transfer_ambiguity_state = {
            "status": "unknown",
            "summary": "no_signal",
            "data_source": "none",
            "observation_reason": "reader_unavailable",
            "runbook_ref": "RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY",
            "provenance": {},
            "reader_schema_version": "transfer_ambiguity_reader/error",
            "operator_attention_hint": False,
        }
    # Human supervision surface (read-only; design intent per PILOT_GO_NO_GO_CHECKLIST row 55)
    human_supervision_state = {
        "status": "operator_supervised",
        "mode": "intended",
        "summary": "bounded pilot requires operator supervision",
    }
    _fs_level = str(v3_summary.get("freshness_status", "unknown"))
    _ev_summary = {"ok": "ok", "warn": "partial", "critical": "stale"}.get(_fs_level, "unknown")
    _fresh = _stale = _older = 0
    for s in group_summaries.values():
        if isinstance(s, dict):
            _fresh += int(s.get("fresh", 0))
            _stale += int(s.get("stale", 0))
            _older += int(s.get("older", 0))
    _audit_trail = (
        "intact"
        if _tel_status == "ok"
        else "degraded"
        if _tel_status == "warn"
        else "broken"
        if _tel_status == "critical"
        else "unknown"
    )
    _blended_summary = _ev_summary
    if _tel_status != "unknown":
        _tel_ev = {"ok": "ok", "warn": "partial", "critical": "stale"}.get(_tel_status, "unknown")
        _rank = {"ok": 0, "partial": 1, "stale": 2, "unknown": 3}
        _blended_summary = max(
            [_ev_summary, _tel_ev],
            key=lambda x: _rank.get(x, 3),
        )
    evidence_state = {
        "summary": _blended_summary,
        "last_verified_utc": truth_state["last_verified_utc"],
        "freshness_status": _fs_level,
        "source_freshness": {"fresh": _fresh, "stale": _stale, "older": _older},
        "audit_trail": _audit_trail,
    }
    if _tel_status != "unknown":
        evidence_state["telemetry_evidence"] = _tel_status
    try:
        from src.ops.p85_result_reader import read_p85_exchange_observation

        _p85_obs = read_p85_exchange_observation(repo_root)
    except Exception:
        _p85_obs = {
            "reader_schema_version": "p85_exchange_reader/error",
            "exchange": "unknown",
            "data_source": "none",
            "artifact_path": None,
            "last_updated_utc": None,
            "stale": False,
            "observation_reason": "reader_unavailable",
            "provenance": {},
        }
    _exchange_status = str(_p85_obs.get("exchange") or "unknown")
    try:
        from src.ops.market_data_cache_observation_reader import read_market_data_cache_observation

        _mdc_obs = read_market_data_cache_observation(repo_root, _config_path)
    except Exception:
        _mdc_obs = {
            "reader_schema_version": "market_data_cache_observation_reader/error",
            "market_data_cache": "unknown",
            "data_source": "none",
            "observation_reason": "reader_unavailable",
            "provenance": {},
            "details": None,
            "last_updated_utc": None,
        }
    _mdc_roll = str(_mdc_obs.get("market_data_cache") or "unknown")
    _market_data_cache_status: Optional[str] = None if _mdc_roll == "unknown" else _mdc_roll
    _dep_rank = {"ok": 0, "partial": 1, "warn": 1, "degraded": 2, "stale": 2, "unknown": 3}
    _tel_dep = (
        "ok"
        if _tel_status == "ok" and not _degraded
        else "partial"
        if _tel_status == "warn"
        else "degraded"
        if _tel_status == "critical"
        else "unknown"
    )
    _ex_dep = (
        "ok"
        if _exchange_status == "ok"
        else "degraded"
        if _exchange_status == "degraded"
        else "unknown"
    )
    _cache_dep = _market_data_cache_status if _market_data_cache_status is not None else "unknown"
    _dep_signals = [s for s in [_tel_dep, _ex_dep, _cache_dep] if s != "unknown"]
    _dep_summary = (
        max(_dep_signals, key=lambda x: _dep_rank.get(x, 3)) if _dep_signals else "unknown"
    )
    dependencies_state = {
        "summary": _dep_summary,
        "exchange": _exchange_status,
        "telemetry": _tel_status,
        "degraded": _degraded,
        "p85_exchange_observation": _p85_obs,
        "market_data_cache_observation": _mdc_obs,
    }
    if _market_data_cache_status is not None:
        dependencies_state["market_data_cache"] = _market_data_cache_status
    if update_officer_source_conflict:
        update_officer_ui = build_update_officer_ui_route_conflict()
    else:
        update_officer_ui = build_update_officer_ui_model(
            payload_path=update_officer_notifier_path,
            run_dir=update_officer_run_dir,
        )
    phase83_eligibility_snapshot = _build_phase83_eligibility_snapshot(repo_root)
    workflow_officer_state: Dict[str, object] = build_workflow_officer_panel_context(repo_root)
    system_state: Dict[str, object] = {
        "mode": "truth_first_ops_cockpit_v3",
        "execution_model": "guarded_execution",
        "config_load_status": _config_load_status,
        "environment": _trading_environment if _trading_environment is not None else "unknown",
        "bounded_pilot_mode": _bounded_pilot_mode,
        "gating_posture_observation": policy_state["summary"],
    }
    guard_state_payload = {
        "no_trade_baseline": guard_state["no_trade_baseline"],
        "deny_by_default": guard_state["deny_by_default"],
        "treasury_separation": guard_state["treasury_separation"],
    }
    from src.ops.evidence_audit_observation import build_evidence_audit_observation
    from src.ops.exposure_risk_observation import build_exposure_risk_observation
    from src.ops.governance_boundary_observation import build_governance_boundary_observation
    from src.ops.health_drift_observation import build_health_drift_observation
    from src.ops.policy_go_no_go_observation import build_policy_go_no_go_observation
    from src.ops.incident_safety_observation import build_incident_safety_observation
    from src.ops.run_session_observation import build_run_session_observation
    from src.ops.safety_posture_observation import build_safety_posture_observation
    from src.ops.safety_state import build_safety_state
    from src.ops.system_state_observation import build_system_state_observation

    safety_posture_observation = build_safety_posture_observation(
        policy_state=policy_state,
        guard_state=guard_state_payload,
        incident_state=incident_state,
        operator_state=operator_state,
        system_state=system_state,
        stale_state=stale_state,
        dependencies_state=dependencies_state,
    )
    run_session_observation = build_run_session_observation(
        run_state=run_state,
        session_end_mismatch_state=session_end_mismatch_state,
        stale_state=stale_state,
        operator_state=operator_state,
    )
    health_drift_observation = build_health_drift_observation(
        truth_status=str(v3_summary["truth_status"]),
        freshness_status=str(v3_summary["freshness_status"]),
        source_coverage_status=str(v3_summary["source_coverage_status"]),
        critical_flags=v3_summary["critical_flags"],
        unknown_flags=v3_summary["unknown_flags"],
        evidence_state=evidence_state,
        dependencies_state=dependencies_state,
        stale_state=stale_state,
        executive_summary=v3_summary["executive_summary"],
    )
    exposure_risk_observation = build_exposure_risk_observation(
        exposure_state=exposure_state,
        transfer_ambiguity_state=transfer_ambiguity_state,
        stale_state=stale_state,
        guard_state=guard_state_payload,
    )
    incident_safety_observation = build_incident_safety_observation(
        incident_state=incident_state,
        dependencies_state=dependencies_state,
        policy_state=policy_state,
        operator_state=operator_state,
    )
    safety_state = build_safety_state(
        safety_posture_observation=safety_posture_observation,
        incident_state=incident_state,
        incident_safety_observation=incident_safety_observation,
    )
    evidence_audit_observation = build_evidence_audit_observation(
        evidence_state=evidence_state,
        truth_status=str(v3_summary["truth_status"]),
        freshness_status=str(v3_summary["freshness_status"]),
        executive_summary=v3_summary["executive_summary"],
    )
    ai_boundary_state_payload = build_ai_boundary_state()
    governance_boundary_observation = build_governance_boundary_observation(
        ai_boundary_state=ai_boundary_state_payload,
        human_supervision_state=human_supervision_state,
        guard_state=guard_state_payload,
        evidence_state=evidence_state,
    )
    policy_go_no_go_observation = build_policy_go_no_go_observation(
        policy_state=policy_state,
        incident_state=incident_state,
        operator_state=operator_state,
    )
    system_state_observation = build_system_state_observation(
        system_state=system_state,
        policy_state=policy_state,
    )
    return {
        "system_state": system_state,
        "guard_state": guard_state_payload,
        "policy_state": policy_state,
        "operator_state": operator_state,
        "run_state": run_state,
        "incident_state": incident_state,
        "exposure_state": exposure_state,
        "stale_state": stale_state,
        "balance_semantics_state": balance_semantics_state,
        "session_end_mismatch_state": session_end_mismatch_state,
        "transfer_ambiguity_state": transfer_ambiguity_state,
        "human_supervision_state": human_supervision_state,
        "evidence_state": evidence_state,
        "dependencies_state": dependencies_state,
        "truth_state": truth_state,
        "ai_boundary_state": ai_boundary_state_payload,
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
        "phase83_eligibility_snapshot": phase83_eligibility_snapshot,
        "workflow_officer_state": workflow_officer_state,
        "update_officer_ui": update_officer_ui,
        "safety_posture_observation": safety_posture_observation,
        "safety_state": safety_state,
        "run_session_observation": run_session_observation,
        "health_drift_observation": health_drift_observation,
        "exposure_risk_observation": exposure_risk_observation,
        "incident_safety_observation": incident_safety_observation,
        "evidence_audit_observation": evidence_audit_observation,
        "governance_boundary_observation": governance_boundary_observation,
        "policy_go_no_go_observation": policy_go_no_go_observation,
        "system_state_observation": system_state_observation,
    }


def _render_update_officer_source_ergonomics_block(
    *,
    form_notifier_path: str,
    form_run_dir: str,
    conflict: bool,
    effective_notifier_path: Path | str | None,
    effective_run_dir: Path | str | None,
    source_preset: str,
) -> str:
    """v8/v9/v10: visible GET-only source selection; same resolution rules as v7."""
    esc_np = escape(form_notifier_path)
    esc_rd = escape(form_run_dir)
    esc_preset = escape(source_preset)
    v10_aids = build_update_officer_validation_aids(
        conflict=conflict,
        effective_notifier_path=effective_notifier_path,
        effective_run_dir=effective_run_dir,
        source_preset=source_preset,
    )
    v10_html = _render_update_officer_validation_aids_html(v10_aids)
    v11_trace = build_update_officer_source_trace(
        conflict=conflict,
        effective_notifier_path=effective_notifier_path,
        effective_run_dir=effective_run_dir,
        source_preset=source_preset,
    )
    v11_html = _render_update_officer_operator_trace_html(v11_trace)
    if conflict:
        summary = (
            "Active source: <strong>conflict</strong> — both notifier path and run directory "
            "were supplied; use only one."
        )
    elif effective_notifier_path:
        summary = (
            "Active source: <strong>explicit notifier path</strong> — "
            f"<code>{escape(str(effective_notifier_path))}</code>"
        )
    elif effective_run_dir:
        summary = (
            "Active source: <strong>run directory</strong> — "
            f"<code>{escape(str(effective_run_dir))}</code> (expects notifier_payload.json)"
        )
    else:
        summary = (
            "Active source: <strong>none</strong> — standard empty-state; use the form below "
            "or query parameters."
        )
    pl = _uo_preset_display_label(source_preset)
    preset_note = ""
    if conflict:
        preset_note = (
            ' <span class="uo-preset-context">(preset is informational while source inputs '
            "conflict)</span>"
        )
    preset_summary = (
        f'<p><strong>Active preset:</strong> <span class="uo-active-preset">{escape(pl)}</span>'
        f"{preset_note}</p>"
    )
    href_clear = _uo_ops_preset_href(
        link_kind="clear", form_np=form_notifier_path, form_rd=form_run_dir
    )
    href_manual = _uo_ops_preset_href(
        link_kind="manual_keep", form_np=form_notifier_path, form_rd=form_run_dir
    )
    href_np = _uo_ops_preset_href(
        link_kind="notifier_path", form_np=form_notifier_path, form_rd=form_run_dir
    )
    href_rd = _uo_ops_preset_href(
        link_kind="run_dir", form_np=form_notifier_path, form_rd=form_run_dir
    )
    preset_toolbar = (
        "<h3>Operator presets (GET-only)</h3>"
        "<p>Quick navigation only — presets do not discover paths or change v7 resolution rules. "
        "Focus links omit the other source parameter from the URL.</p>"
        '<ul class="uo-preset-toolbar">'
        f'<li><a href="{escape(href_clear)}">Default — clear query</a></li>'
        f'<li><a href="{escape(href_manual)}">Manual — keep current inputs</a></li>'
        f'<li><a href="{escape(href_np)}">Notifier path focus</a> (omits run directory param)</li>'
        f'<li><a href="{escape(href_rd)}">Run directory focus</a> (omits notifier path param)</li>'
        "</ul>"
    )
    return (
        '<div class="card truth-card">'
        "<h2>Update Officer source selection</h2>"
        "<p><strong>Read-only.</strong> GET-only navigation; no POST, no write actions.</p>"
        f"{v10_html}"
        f"{v11_html}"
        f"<p>{summary}</p>"
        f"{preset_summary}"
        f"{preset_toolbar}"
        '<form class="uo-source-form" method="get" action="/ops">'
        f'<input type="hidden" name="update_officer_source_preset" value="{esc_preset}">'
        '<p><label for="uo-np">Notifier payload path</label><br>'
        f'<input id="uo-np" type="text" name="update_officer_notifier_path" '
        f'value="{esc_np}" size="72" autocomplete="off"></p>'
        '<p><label for="uo-rd">Run directory</label><br>'
        f'<input id="uo-rd" type="text" name="update_officer_run_dir" '
        f'value="{esc_rd}" size="72" autocomplete="off"></p>'
        '<p><button type="submit">Apply source (GET)</button></p>'
        "</form>"
        '<p><a href="/ops">Clear source inputs</a> — returns to default empty-state.</p>'
        "</div>"
    )


def _render_update_officer_card(uo: Dict[str, object]) -> str:
    """Read-only Update Officer summary card (v6). No actions."""
    avail = bool(uo.get("available"))
    if not avail:
        msg = escape(str(uo.get("empty_state_message") or "Unavailable."))
        return (
            '<div class="card truth-card" id="update-officer-visibility-card">'
            "<h2>Update Officer</h2>"
            "<p><strong>Read-only.</strong> Payload key <code>update_officer_ui</code>. "
            "Notifier summary from local payload (if provided). "
            "Does not start Workflow Officer; not execution authority.</p>"
            f'<p><strong>Available:</strong> <span class="chip"><code>false</code></span></p>'
            f"<p>{msg}</p>"
            "</div>"
        )
    qp = uo.get("queue_preview") or []
    qp_items = ""
    if isinstance(qp, list):
        for item in qp:
            if not isinstance(item, dict):
                continue
            qp_items += (
                f"<li>#{escape(str(item.get('rank', '')))} "
                f"{escape(str(item.get('topic_id', '')))} "
                f"[worst_priority={escape(str(item.get('worst_priority', '')))}, "
                f"findings={escape(str(item.get('finding_count', '')))}]</li>"
            )
    qp_html = f"<ul>{qp_items}</ul>" if qp_items else "<p>No queue entries.</p>"
    rp = uo.get("review_paths") or []
    rp_str = ", ".join(escape(str(p)) for p in rp) if isinstance(rp, list) else ""
    return (
        '<div class="card truth-card" id="update-officer-visibility-card">'
        "<h2>Update Officer</h2>"
        "<p><strong>Read-only.</strong> Payload key <code>update_officer_ui</code>. "
        "Deterministic notifier view (v4 consumer layer). "
        "Does not start Workflow Officer; GET-only source ergonomics appear above this card when present; "
        "not execution authority.</p>"
        f'<p><strong>Available:</strong> <span class="chip"><code>true</code></span></p>'
        f"<p><strong>Headline:</strong> {escape(str(uo.get('headline', '')))}</p>"
        f"<p><strong>Status:</strong> <code>{escape(str(uo.get('status', '')))}</code></p>"
        f"<p><strong>Next topic:</strong> <code>{escape(str(uo.get('next_topic', '')))}</code></p>"
        f"<p><strong>Why now:</strong> {escape(str(uo.get('why_now', '')))}</p>"
        f"<p><strong>Next action:</strong> {escape(str(uo.get('next_action', '')))}</p>"
        f"<p><strong>Review paths:</strong> {rp_str or 'none'}</p>"
        f"<p><strong>Requires manual review:</strong> {escape(str(uo.get('requires_manual_review', False)))}</p>"
        f"<p><strong>Severity:</strong> <code>{escape(str(uo.get('severity', '')))}</code></p>"
        f"<p><strong>Reminder class:</strong> <code>{escape(str(uo.get('reminder_class', '')))}</code></p>"
        "<p><strong>Queue preview:</strong></p>"
        f"{qp_html}"
        "</div>"
    )


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


def _render_status_at_a_glance_inner(payload: Dict[str, object]) -> str:
    """Status grid + attribution + flags — reuses badge helpers; read-only."""
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
        '<div class="status-grid">'
        f"{''.join(cards)}"
        "</div>"
        '<p class="status-attribution"><strong>Sources:</strong> operator snapshot, system state, truth sections</p>'
        f"{flags_html}"
    )


def _render_operator_summary_preamble() -> str:
    """Read-only operator summary heading and disclaimer. Stable id for tests and deep links."""
    return (
        '<section class="operator-summary-preamble" id="operator-summary-preamble">'
        "<h2>Operator summary (read-only)</h2>"
        '<p class="operator-summary-disclaimer"><strong>Observation only.</strong> '
        "Read-only snapshot from local artifacts and the <code>GET /api/ops-cockpit</code> "
        "payload shape. <strong>Not an approval, not an unlock,</strong> not a substitute for "
        "your governance process.</p>"
        '<p class="operator-summary-master-v2-non-authority">'
        "This OPS Cockpit view is read-only and non-authorizing. "
        "It does not grant live, testnet, paper, shadow, execution, promotion, or evidence authority. "
        "Canonical authority remains in the Master V2 decision-authority chain and related runbooks. "
        "Double Play semantics are displayed only as read-only observations and are not controlled by the cockpit."
        "</p>"
        "</section>"
    )


def _render_operator_summary_surface(payload: Dict[str, object]) -> str:
    """vNext-aligned operator summary: system status, go/no-go observation, status at a glance. Read-only."""
    sys_state = payload.get("system_state") or {}
    ps = payload.get("policy_state") if isinstance(payload.get("policy_state"), dict) else {}
    inc = payload.get("incident_state") if isinstance(payload.get("incident_state"), dict) else {}
    deps = (
        payload.get("dependencies_state")
        if isinstance(payload.get("dependencies_state"), dict)
        else {}
    )
    ev = payload.get("evidence_state") if isinstance(payload.get("evidence_state"), dict) else {}

    mode_s = escape(str(sys_state.get("mode", "unknown")))
    exec_m = escape(str(sys_state.get("execution_model", "unknown")))
    cfg_ld = escape(str(sys_state.get("config_load_status", "unknown")))
    env_obs = escape(str(sys_state.get("environment", "unknown")))
    gating_mirror = escape(str(sys_state.get("gating_posture_observation", "unknown")))
    bp_raw = sys_state.get("bounded_pilot_mode")
    bp_s = escape(str(bp_raw)) if bp_raw is not None else "n/a"

    sso_block = _render_operator_summary_system_state_observation(
        payload.get("system_state_observation")
    )

    p83_raw = payload.get("phase83_eligibility_snapshot")
    p83_block = ""
    if isinstance(p83_raw, dict):
        p83_status = escape(str(p83_raw.get("status", "unknown")))
        p83_chk = int(p83_raw.get("strategies_checked") or 0)
        p83_eli = int(p83_raw.get("eligible_count") or 0)
        p83_nel = int(p83_raw.get("not_eligible_count") or 0)
        tp_raw = p83_raw.get("truth_posture")
        tp_s = escape(str(tp_raw)) if tp_raw is not None else "n/a"
        ro_raw = p83_raw.get("read_only")
        ro_s = escape(str(ro_raw)) if ro_raw is not None else "n/a"
        rflag = p83_raw.get("require_allow_live_flag")
        rflag_s = escape(str(rflag)) if rflag is not None else "n/a"
        p83_block = (
            '<section class="operator-summary-phase83-eligibility" '
            'id="operator-summary-phase83-eligibility">'
            "<h3>Phase 83 — Strategy eligibility (observation)</h3>"
            "<p><strong>Observation only.</strong> Compact snapshot from "
            "<code>phase83_eligibility_snapshot</code> in this payload — same eligibility check as the "
            "<strong>Phase 83 — Strategy eligibility</strong> card below. "
            "<strong>Does not grant live access,</strong> <strong>not approval,</strong> "
            "not a substitute for external governance or <code>policy_go_no_go_observation</code>.</p>"
            f"<p><strong>status</strong>: <code>{p83_status}</code> · "
            f"<strong>strategies_checked</strong>: <code>{p83_chk}</code> · "
            f"<strong>eligible_count</strong> / <strong>not_eligible_count</strong>: "
            f"<code>{p83_eli}</code> / <code>{p83_nel}</code></p>"
            f"<p><strong>read_only</strong>: <code>{ro_s}</code> · "
            f"<strong>truth_posture</strong>: <code>{tp_s}</code> · "
            f"<strong>require_allow_live_flag</strong> (policy observation): <code>{rflag_s}</code></p>"
            "</section>"
        )

    action = escape(str(ps.get("action", "unknown")))
    blocked = ps.get("blocked")
    blocked_s = escape(str(blocked))
    ks_ps = bool(ps.get("kill_switch_active"))
    ks_inc = bool(inc.get("kill_switch_active"))
    ks_active = ks_ps or ks_inc
    req_att = inc.get("requires_operator_attention")
    inc_summary = escape(str(inc.get("summary", "unknown")))

    go_no_go_intro = (
        "<p><strong>Observation only.</strong> The labels below quote "
        "<code>policy_state</code> and <code>incident_state</code> from this page&apos;s JSON "
        "payload. They describe configured gates and rollups — "
        "<strong>not an approval, not an unlock,</strong> not live permission.</p>"
    )
    go_lines = (
        f"<p><strong>policy_state.action</strong> (observation): <code>{action}</code></p>"
        f"<p><strong>policy_state.blocked</strong> (observation): <code>{blocked_s}</code></p>"
        f"<p><strong>incident_state.summary</strong> (observation): <code>{inc_summary}</code></p>"
        f"<p><strong>incident_state.requires_operator_attention</strong> (observation): "
        f"<code>{escape(str(req_att))}</code></p>"
    )
    if ks_active:
        go_lines += (
            "<p><strong>Kill switch signal</strong> (observation): active in payload — "
            "downstream enforcement remains authoritative; this page does not clear it.</p>"
        )

    pgngo_block = _render_operator_summary_policy_go_no_go_observation(
        payload.get("policy_go_no_go_observation")
    )

    operator_state_summary_block = _render_operator_summary_operator_state(payload)

    spo_block = _render_operator_summary_safety_posture_observation(
        payload.get("safety_posture_observation")
    )

    sstate_raw = payload.get("safety_state")
    sstate_block = ""
    if isinstance(sstate_raw, dict):
        ss_summary = escape(str(sstate_raw.get("summary", "")))
        ss_ds = escape(str(sstate_raw.get("data_source", "")))
        ss_ver = escape(str(sstate_raw.get("reader_schema_version", "")))
        prov = sstate_raw.get("provenance")
        prov_reason = ""
        if isinstance(prov, dict) and prov.get("observation_reason"):
            prov_reason = escape(str(prov.get("observation_reason", "")))
        subs_parts: List[str] = []
        po_ref = sstate_raw.get("posture_observation")
        if isinstance(po_ref, dict):
            subs_parts.append(
                "<p><strong>posture_observation</strong> (projection ref): "
                f"<code>status={escape(str(po_ref.get('status', '')))}</code> · "
                "<strong>reader_schema_version:</strong> "
                f"<code>{escape(str(po_ref.get('reader_schema_version', '')))}</code></p>"
            )
        iso_ref = sstate_raw.get("incident_safety_observation")
        if isinstance(iso_ref, dict):
            subs_parts.append(
                "<p><strong>incident_safety_observation</strong> (projection ref): "
                f"<code>status={escape(str(iso_ref.get('status', '')))}</code> · "
                "<strong>reader_schema_version:</strong> "
                f"<code>{escape(str(iso_ref.get('reader_schema_version', '')))}</code></p>"
            )
        iss = sstate_raw.get("incident_signal_subset")
        if isinstance(iss, dict):
            subs_parts.append(
                "<p><strong>incident_signal_subset</strong> (projection; scalars from "
                "<code>incident_state</code>): "
                f"<code>status={escape(str(iss.get('status', '')))}</code>, "
                f"<code>kill_switch_active={escape(str(iss.get('kill_switch_active')))}</code>, "
                f"<code>blocked={escape(str(iss.get('blocked')))}</code>, "
                f"<code>requires_operator_attention="
                f"{escape(str(iss.get('requires_operator_attention')))}</code></p>"
            )
        subs_html = "".join(subs_parts)
        reason_line = ""
        if prov_reason:
            reason_line = (
                f"<p><strong>provenance.observation_reason:</strong> <code>{prov_reason}</code></p>"
            )
        sstate_block = (
            '<section class="operator-summary-safety-state" '
            'id="operator-summary-safety-state-projection">'
            "<h3>Safety state (vNext projection)</h3>"
            "<p><strong>Observation only.</strong> Top-level <code>safety_state</code> bundles "
            "references to <code>safety_posture_observation</code>, "
            "<code>incident_safety_observation</code>, and scalar <code>incident_state</code> "
            "rollups already in this payload — <strong>not a new safety verdict,</strong> "
            "<strong>not approval or unlock,</strong> not broker truth. Holistic gating posture: "
            "<strong>Safety / gating posture (observation)</strong> above.</p>"
            f"<p><strong>safety_state.summary</strong>: {ss_summary}</p>"
            f"<p><strong>data_source:</strong> <code>{ss_ds}</code> · "
            f"<strong>reader_schema_version:</strong> <code>{ss_ver}</code></p>"
            f"{reason_line}"
            f"{subs_html}"
            "</section>"
        )

    gbo_block = _render_operator_summary_governance_boundary_observation(
        payload.get("governance_boundary_observation")
    )

    wo_sum_raw = payload.get("workflow_officer_state")
    wo_sum_block = ""
    if isinstance(wo_sum_raw, dict):
        wo_intro = (
            "<p><strong>Observation only.</strong> Compact view of <code>workflow_officer_state</code> in "
            "this payload — same artifact as <strong>Operator workflow observation (vNext Phase 4)</strong> "
            "below. <strong>Visibility only</strong> — <strong>not approval,</strong> "
            "<strong>not unlock,</strong> <strong>not a release go-signal;</strong> "
            "does not start Workflow Officer from this page. "
            "<code>policy_go_no_go_observation</code> remains the compact policy aggregate (separate object).</p>"
        )
        if wo_sum_raw.get("present") is not True:
            er = wo_sum_raw.get("empty_reason")
            er_s = escape(str(er)) if er is not None else "unknown"
            wo_sum_block = (
                '<section class="operator-summary-workflow-officer" '
                'id="operator-summary-workflow-officer">'
                "<h3>Operator workflow (observation)</h3>"
                f"{wo_intro}"
                "<p><strong>workflow_officer_state.present</strong>: <code>false</code></p>"
                f"<p><strong>workflow_officer_state.empty_reason</strong>: <code>{er_s}</code></p>"
                "</section>"
            )
        else:
            rollup = wo_sum_raw.get("rollup") if isinstance(wo_sum_raw.get("rollup"), dict) else {}
            ex = (
                wo_sum_raw.get("executive") if isinstance(wo_sum_raw.get("executive"), dict) else {}
            )
            pf_raw = wo_sum_raw.get("primary_followup")
            pf = pf_raw if isinstance(pf_raw, dict) else {}
            tc = rollup.get("total_checks")
            hf = rollup.get("hard_failures")
            wrn = rollup.get("warnings")
            rollup_bits: List[str] = []
            if tc is not None:
                rollup_bits.append(f"total_checks={escape(_fmt_observation_cell(tc))}")
            if hf is not None:
                rollup_bits.append(f"hard_failures={escape(_fmt_observation_cell(hf))}")
            if wrn is not None:
                rollup_bits.append(f"warnings={escape(_fmt_observation_cell(wrn))}")
            rollup_line = ""
            if rollup_bits:
                rollup_line = (
                    f"<p><strong>rollup</strong> (observation): {', '.join(rollup_bits)}</p>"
                )
            ul = ex.get("urgency_label")
            urg_line = ""
            if ul is not None:
                urg_line = (
                    "<p><strong>executive.urgency_label</strong> (observation): "
                    f"<code>{escape(_fmt_observation_cell(ul))}</code></p>"
                )
            cid = pf.get("check_id")
            pf_line = ""
            if cid is not None:
                pf_line = (
                    "<p><strong>primary_followup.check_id</strong> (observation): "
                    f"<code>{escape(_fmt_observation_cell(cid))}</code></p>"
                )
            wo_sum_block = (
                '<section class="operator-summary-workflow-officer" '
                'id="operator-summary-workflow-officer">'
                "<h3>Operator workflow (observation)</h3>"
                f"{wo_intro}"
                "<p><strong>workflow_officer_state.present</strong>: <code>true</code></p>"
                f"{rollup_line}"
                f"{urg_line}"
                f"{pf_line}"
                "</section>"
            )

    uo_sum_block = _render_operator_summary_update_officer_observation(
        payload.get("update_officer_ui")
    )

    phase57_operator_summary_block = _render_operator_summary_phase57_snapshot_discoverability()

    rso_block = _render_operator_summary_run_session_observation(
        payload.get("run_session_observation")
    )

    run_state_summary_block = _render_operator_summary_run_state(payload.get("run_state"))

    sem_block = _render_operator_summary_session_end_mismatch(
        payload.get("session_end_mismatch_state")
    )
    ta_block = _render_operator_summary_transfer_ambiguity(payload.get("transfer_ambiguity_state"))

    stale_signals_block = _render_operator_summary_stale_signals_observation(
        payload.get("stale_state")
    )

    hdo_block = _render_operator_summary_health_drift_observation(
        payload.get("health_drift_observation")
    )

    dep_artifact_block = _render_operator_summary_dependencies_artifact_observations(deps)

    ero_block = _render_operator_summary_exposure_risk_observation(
        payload.get("exposure_risk_observation")
    )

    exposure_state_summary_block = _render_operator_summary_exposure_state(
        payload.get("exposure_state")
    )

    bal_sem_raw = payload.get("balance_semantics_state")
    bs_block = ""
    if isinstance(bal_sem_raw, dict):
        b_sem = bal_sem_raw.get("balance_semantic_state")
        b_reason = bal_sem_raw.get("balance_reason_code")
        b_vis = bal_sem_raw.get("balance_operator_visible_state")
        bs_block = (
            '<section class="operator-summary-balance-semantics" '
            'id="operator-summary-balance-semantics">'
            "<h3>Balance semantics (observation)</h3>"
            "<p><strong>Observation only.</strong> Local monitor / portfolio snapshot labels from "
            "<code>balance_semantics_state</code> in this payload — <strong>not exchange balance truth,</strong> "
            "<strong>not reconciliation approval,</strong> not treasury clearance. "
            "Cross-surface context: <code>stale_state.balance</code>, "
            "<code>transfer_ambiguity_state</code>, <code>session_end_mismatch_state</code> "
            "(detail cards below).</p>"
            "<p><strong>balance_semantic_state</strong> (observation): "
            f"<code>{escape(str(b_sem if b_sem is not None else 'n/a'))}</code></p>"
            "<p><strong>balance_reason_code</strong> (observation): "
            f"<code>{escape(str(b_reason if b_reason is not None else 'n/a'))}</code></p>"
            "<p><strong>balance_operator_visible_state</strong> (observation): "
            f"<code>{escape(str(b_vis if b_vis is not None else 'n/a'))}</code></p>"
            "</section>"
        )

    iso_block = _render_operator_summary_incident_safety_observation(
        payload.get("incident_safety_observation")
    )

    eao_block = _render_operator_summary_evidence_audit_observation(
        payload.get("evidence_audit_observation")
    )

    incident_status = escape(str(inc.get("status", "unknown")))
    incident_degraded = escape(str(inc.get("degraded", "unknown")))
    incident_stop_invoked = escape(str(inc.get("incident_stop_invoked", "unknown")))
    incident_entry_permitted = escape(str(inc.get("entry_permitted", "unknown")))
    incident_authoritative = escape(str(inc.get("operator_authoritative_state", "unknown")))
    dep_summary = escape(str(deps.get("summary", "unknown")))
    dep_telemetry = escape(str(deps.get("telemetry", "unknown")))
    dep_exchange = escape(str(deps.get("exchange", "unknown")))
    dep_degraded = deps.get("degraded")
    dep_degraded_count = 0
    dep_degraded_preview = ""
    if isinstance(dep_degraded, list):
        dep_degraded_count = len(dep_degraded)
        if dep_degraded:
            dep_degraded_preview = ", ".join(str(item) for item in dep_degraded[:3])
    incident_observation_lines = (
        "<p><strong>incident_state.status</strong> (observation): "
        f"<code>{incident_status}</code></p>"
        "<p><strong>incident_state.degraded</strong> (observation): "
        f"<code>{incident_degraded}</code></p>"
        "<p><strong>incident_state.incident_stop_invoked</strong> (observation): "
        f"<code>{incident_stop_invoked}</code></p>"
        "<p><strong>incident_state.entry_permitted</strong> (observation): "
        f"<code>{incident_entry_permitted}</code></p>"
        "<p><strong>incident_state.operator_authoritative_state</strong> (observation): "
        f"<code>{incident_authoritative}</code></p>"
        "<p><strong>dependencies_state.summary</strong> (observation): "
        f"<code>{dep_summary}</code></p>"
        "<p><strong>dependencies_state.telemetry</strong> (observation): "
        f"<code>{dep_telemetry}</code></p>"
        "<p><strong>dependencies_state.exchange</strong> (observation): "
        f"<code>{dep_exchange}</code></p>"
        "<p><strong>dependencies_state.degraded_count</strong> (observation): "
        f"<code>{dep_degraded_count}</code></p>"
    )
    if dep_degraded_preview:
        incident_observation_lines += (
            "<p><strong>dependencies_state.degraded_preview</strong> (observation): "
            f"<code>{escape(dep_degraded_preview)}</code></p>"
        )

    evidence_summary = escape(str(ev.get("summary", "unknown")))
    evidence_freshness = escape(str(ev.get("freshness_status", "unknown")))
    evidence_audit = escape(str(ev.get("audit_trail", "unknown")))
    evidence_last_verified = escape(str(ev.get("last_verified_utc", "unknown")))
    source_freshness = ev.get("source_freshness")
    sf_fresh = sf_stale = sf_older = "unknown"
    if isinstance(source_freshness, dict):
        sf_fresh = escape(str(source_freshness.get("fresh", "unknown")))
        sf_stale = escape(str(source_freshness.get("stale", "unknown")))
        sf_older = escape(str(source_freshness.get("older", "unknown")))
    evidence_observation_lines = (
        "<p><strong>evidence_state.summary</strong> (observation): "
        f"<code>{evidence_summary}</code></p>"
        "<p><strong>evidence_state.freshness_status</strong> (observation): "
        f"<code>{evidence_freshness}</code></p>"
        "<p><strong>evidence_state.audit_trail</strong> (observation): "
        f"<code>{evidence_audit}</code></p>"
        "<p><strong>evidence_state.last_verified_utc</strong> (observation): "
        f"<code>{evidence_last_verified}</code></p>"
        "<p><strong>evidence_state.source_freshness</strong> (observation): "
        f"<code>fresh={sf_fresh}, stale={sf_stale}, older={sf_older}</code></p>"
    )
    if "telemetry_evidence" in ev:
        evidence_observation_lines += (
            "<p><strong>evidence_state.telemetry_evidence</strong> (observation): "
            f"<code>{escape(str(ev.get('telemetry_evidence')))}</code></p>"
        )

    glance_intro = (
        "<p><strong>Read-only.</strong> Same rollup fields as before (v3 executive summary cards); "
        "no write actions.</p>"
    )

    inner = _render_status_at_a_glance_inner(payload)
    truth_state_summary_block = _render_operator_summary_truth_state(payload)
    truth_sources_runtime_block = _render_operator_summary_truth_sources_runtime(payload)

    system_status_lines = (
        "<h3>System status (observation)</h3>"
        "<p><em>Trading <code>environment</code> is config observation when loaded — "
        "not a broker or exchange guarantee.</em></p>"
        "<p><strong>system_state.mode</strong> (observation): "
        f"<code>{mode_s}</code></p>"
        "<p><strong>system_state.execution_model</strong> (observation): "
        f"<code>{exec_m}</code></p>"
        "<p><strong>system_state.config_load_status</strong> (observation): "
        f"<code>{cfg_ld}</code></p>"
        "<p><strong>system_state.environment</strong> (observation): "
        f"<code>{env_obs}</code></p>"
        "<p><strong>system_state.bounded_pilot_mode</strong> (observation): "
        f"<code>{bp_s}</code></p>"
        "<p><strong>system_state.gating_posture_observation</strong> (observation): "
        f"<code>{gating_mirror}</code> "
        "(mirror of <code>policy_state.summary</code> at payload build; not a second gate engine)</p>"
    )

    go_no_go_inline = f"<h3>Go / No-Go observation (not approval)</h3>{go_no_go_intro}{go_lines}"

    return (
        '<div class="operator-summary-surface exec-summary">'
        f"{_render_operator_summary_preamble()}"
        f"{_render_operator_summary_system_status(system_status_lines)}"
        f"{sso_block}"
        f"{p83_block}"
        f"{_render_operator_summary_go_no_go_not_approval(go_no_go_inline)}"
        f"{pgngo_block}"
        f"{operator_state_summary_block}"
        f"{spo_block}"
        f"{sstate_block}"
        f"{gbo_block}"
        f"{_render_operator_summary_policy_governance_rv6(payload)}"
        f"{wo_sum_block}"
        f"{uo_sum_block}"
        f"{phase57_operator_summary_block}"
        f"{rso_block}"
        f"{run_state_summary_block}"
        f"{sem_block}"
        f"{ta_block}"
        f"{stale_signals_block}"
        f"{hdo_block}"
        f"{dep_artifact_block}"
        f"{ero_block}"
        f"{exposure_state_summary_block}"
        f"{bs_block}"
        f"{iso_block}"
        f"{_render_operator_summary_incident_observation_read_only(incident_observation_lines)}"
        f"{eao_block}"
        f"{_render_operator_summary_evidence_freshness_observation_read_only(evidence_observation_lines)}"
        f"{truth_state_summary_block}"
        f"{truth_sources_runtime_block}"
        f"{_render_operator_summary_status_at_a_glance(glance_intro, inner)}"
        "</div>"
    )


def render_ops_cockpit_html(
    repo_root: Path | None = None,
    *,
    update_officer_notifier_path: Path | str | None = None,
    update_officer_run_dir: Path | str | None = None,
    update_officer_source_conflict: bool = False,
    update_officer_form_notifier_path: str = "",
    update_officer_form_run_dir: str = "",
    update_officer_source_preset: str = "manual",
) -> str:
    payload = build_ops_cockpit_payload(
        repo_root=repo_root,
        update_officer_notifier_path=update_officer_notifier_path,
        update_officer_run_dir=update_officer_run_dir,
        update_officer_source_conflict=update_officer_source_conflict,
    )
    truth_state = payload["truth_state"]
    runtime = payload["runtime_unknown_state"]
    exposure = payload.get("exposure_state") or {}
    stale = payload.get("stale_state") or {}
    balance_sem = payload.get("balance_semantics_state") or {}
    session_end_mismatch = payload.get("session_end_mismatch_state") or {}
    transfer_ambiguity = payload.get("transfer_ambiguity_state") or {}
    evidence = payload.get("evidence_state") or {}
    dependencies = payload.get("dependencies_state") or {}
    update_officer_ui = payload.get("update_officer_ui") or {}
    incident = payload.get("incident_state") or {}
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
    operator_summary_surface_html = _render_operator_summary_surface(payload)
    policy_governance_observation_surface_html = _render_policy_governance_observation_surface(
        payload
    )
    phase57_snapshot_discoverability_html = _render_phase57_snapshot_discoverability_card()
    incident_observation_html = _render_incident_observation_card(payload)
    run_state_observation_html = _render_run_state_observation_card(payload)
    workflow_officer_observation_html = _render_workflow_officer_observation_surface(payload)
    phase83_eligibility_html = _render_phase83_eligibility_card(
        payload.get("phase83_eligibility_snapshot") or {}
    )
    update_officer_ergonomics_html = _render_update_officer_source_ergonomics_block(
        form_notifier_path=update_officer_form_notifier_path,
        form_run_dir=update_officer_form_run_dir,
        conflict=update_officer_source_conflict,
        effective_notifier_path=update_officer_notifier_path,
        effective_run_dir=update_officer_run_dir,
        source_preset=update_officer_source_preset,
    )
    update_officer_card_html = _render_update_officer_card(update_officer_ui)

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
    .operator-summary-preamble h2 {{ margin-top: 0; }}
    .operator-summary-disclaimer {{ border-left: 4px solid #607d8b; padding-left: 12px; margin: 12px 0; }}
    .operator-summary-surface h3 {{ font-size: 1.05em; margin-top: 18px; margin-bottom: 8px; }}
    .policy-governance-observation-surface h3 {{ font-size: 1.05em; margin-top: 18px; margin-bottom: 8px; }}
    .operator-workflow-observation-surface h3 {{ font-size: 1.05em; margin-top: 18px; margin-bottom: 8px; }}
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
    .uo-source-form input[type="text"] {{ width: 100%; max-width: 52rem; box-sizing: border-box; }}
    .uo-preset-toolbar {{ margin: 0 0 12px 1.2rem; line-height: 1.5; }}
    .uo-preset-context {{ color: #555; font-size: 0.95em; }}
    .uo-validation-aids {{ border-left: 3px solid #999; padding-left: 12px; margin: 12px 0; }}
    .uo-validation-aids dt {{ font-weight: 600; margin-top: 6px; }}
    .uo-validation-aids dd {{ margin-left: 0; margin-bottom: 4px; }}
    .uo-operator-trace {{ border-left: 3px solid #607d8b; padding-left: 12px; margin: 12px 0; }}
    .uo-operator-trace dt {{ font-weight: 600; margin-top: 6px; }}
    .uo-operator-trace dd {{ margin-left: 0; margin-bottom: 4px; }}
  </style>
</head>
<body>
  {operator_summary_surface_html}
  {policy_governance_observation_surface_html}
  {phase57_snapshot_discoverability_html}
  {incident_observation_html}
  {run_state_observation_html}
  {workflow_officer_observation_html}
  {phase83_eligibility_html}
  <div class="hero">
    <h1>Ops Cockpit v3 — Truth-First</h1>
    <p>Read-only. No write actions.</p>
    <p>Read-only operations cockpit aligned to the current canonical truth model.</p>
    <p><strong>Last verified:</strong> {escape(str(truth_state["last_verified_utc"]))}</p>
    <p><strong>Truth coverage:</strong> {escape(str(truth_state["truth_coverage"]))}</p>
    <p><strong>Available / unavailable:</strong> {escape(str(truth_state["available_count"]))} / {
        escape(str(truth_state["unavailable_count"]))
    }</p>
    <p>
      <span class="priority-inline"><strong>canonical</strong>={
        escape(str(counts["canonical_boundary"]))
    }</span>
      <span class="priority-inline"><strong>runtime</strong>={
        escape(str(counts["runtime_resolution"]))
    }</span>
      <span class="priority-inline"><strong>supporting</strong>={
        escape(str(counts["supporting_truth"]))
    }</span>
    </p>
    <p><strong>Execution model:</strong> {
        escape(str(payload["system_state"]["execution_model"]))
    }</p>
    <p><strong>Config environment (observation):</strong> {
        escape(str(payload["system_state"].get("environment", "unknown")))
    }</p>
    <p><strong>Final trade authority:</strong> {
        escape(str(truth_state["final_trade_authority"]))
    }</p>
  </div>

  <div class="legend">
    <h2>Read-only legends</h2>
    <p><strong>Visual emphasis only.</strong> No semantic or execution changes.</p>
    <p><strong>Availability:</strong> <code>available</code> = source found, <code>unavailable</code> = source missing.</p>
    <p><strong>Freshness:</strong> <code>fresh</code> ≤ 24h, <code>stale</code> ≤ 30d, <code>older</code> > 30d.</p>
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
    <div class="card" id="truth-state-observation-card">
      <h2>Truth State</h2>
      <p><strong>Read-only canonical truth</strong></p>
      <p><strong>Truth-first positioning:</strong> {
        escape(str(truth_state["truth_first_positioning"]))
    }</p>
      <p><strong>Truth coverage:</strong> {escape(str(truth_state["truth_coverage"]))}</p>
      <p><strong>Live autonomy:</strong> {escape(str(truth_state["live_autonomy"]))}</p>
    </div>

    <div class="card" id="runtime-unknown-state-observation-card">
      <h2>Runtime Unknown State</h2>
      <p><strong>Unknown / partial slots (read-only)</strong></p>
      <p><strong>Critic runtime path:</strong> {escape(str(runtime["critic_runtime_path"]))}</p>
      <p><strong>Proposer runtime path:</strong> {escape(str(runtime["proposer_runtime_path"]))}</p>
      <p><strong>Provider/model runtime slots:</strong> {
        escape(str(runtime["provider_model_runtime_slots"]))
    }</p>
      <p><strong>Execution-adjacent contracts:</strong> {
        escape(str(runtime["execution_adjacent_contracts"]))
    }</p>
    </div>

    <div class="card" id="exposure-state-observation-card">
      <h2>Exposure State</h2>
      <p><strong>Read-only exposure / risk observation.</strong> Existing payload fields only; not approval, not unlock.</p>
      <p><strong>Summary:</strong> <span class="chip"><code>{
        escape(str(exposure.get("summary", "unknown")))
    }</code></span></p>
      <p><strong>Treasury separation:</strong> {
        escape(str(exposure.get("treasury_separation", "unknown")))
    }</p>
      <p><strong>Risk status:</strong> {escape(str(exposure.get("risk_status", "unknown")))}</p>
      <p><strong>Observed exposure:</strong> {
        escape(str(exposure.get("observed_exposure", "n/a")))
    }</p>
      <p><strong>Observed currency:</strong> {escape(str(exposure.get("observed_ccy", "n/a")))}</p>
      <p><strong>Data source:</strong> <code>{
        escape(str(exposure.get("data_source", "n/a")))
    }</code></p>
      <p><strong>Last updated (UTC):</strong> {
        escape(str(exposure.get("last_updated_utc", "n/a")))
    }</p>
      <p><strong>Exposure stale flag:</strong> {escape(str(exposure.get("stale", "n/a")))}</p>
      <p><strong>stale_state.exposure:</strong> <code>{
        escape(str(stale.get("exposure", "unknown")))
    }</code></p>
      <p><strong>dependencies_state.summary:</strong> <code>{
        escape(str(dependencies.get("summary", "unknown")))
    }</code></p>
      <p><strong>Configured caps:</strong></p>
      <ul>
        {
        "".join(
            f"<li><code>{escape(str(cap.get('limit_id', 'unknown')))}</code>: "
            f"{escape(str(cap.get('cap_value', 'n/a')))} "
            f"{escape(str(cap.get('ccy', '')))}</li>"
            for cap in list(exposure.get("caps_configured", []))[:6]
            if isinstance(cap, dict)
        )
        or "<li>none</li>"
    }
      </ul>
      <p><strong>Symbol exposures (preview):</strong></p>
      <ul>
        {
        "".join(
            f"<li><code>{escape(str(sym))}</code>: {escape(str(val))}</li>"
            for sym, val in list((exposure.get("exposure_by_symbol") or {}).items())[:5]
        )
        or "<li>none</li>"
    }
      </ul>
    </div>

    <div class="card" id="transfer-ambiguity-observation-surface">
      <h2>Transfer / Treasury ambiguity</h2>
      <p><em>Observation (read-only). Local cockpit signals only; not broker or exchange truth; not approval; not unlock.</em></p>
      <p><strong>Human runbook:</strong> <code>{
        escape(
            str(transfer_ambiguity.get("runbook_ref", "RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY"))
        )
    }</code></p>
      <p><strong>Status:</strong> <span class="chip"><code>{
        escape(str(transfer_ambiguity.get("status", "unknown")))
    }</code></span></p>
      <p><strong>Summary:</strong> {escape(str(transfer_ambiguity.get("summary", "no_signal")))}</p>
      <p><strong>Observation reason:</strong> {
        escape(str(transfer_ambiguity.get("observation_reason", "n/a")))
    }</p>
      <p><strong>Data source:</strong> <code>{
        escape(str(transfer_ambiguity.get("data_source", "unknown")))
    }</code></p>
      <p><strong>Operator attention hint:</strong> {
        escape(str(transfer_ambiguity.get("operator_attention_hint", False)))
    }</p>
      <p><strong>Reader schema:</strong> <code>{
        escape(str(transfer_ambiguity.get("reader_schema_version", "n/a")))
    }</code></p>
    </div>

    <div class="card" id="stale-state-observation-card">
      <h2>Stale State</h2>
      <p><strong>Reconciliation hardening: balance / position / order staleness</strong></p>
      <p><em>Order row: recency of <code>live_runs</code> event logs (read-only); not exchange order-book state.</em></p>
      <p><strong>Summary:</strong> <span class="chip"><code>{
        escape(str(stale.get("summary", "unknown")))
    }</code></span></p>
      <p><strong>Balance:</strong> {escape(str(stale.get("balance", "unknown")))}</p>
      <p><strong>Position:</strong> {escape(str(stale.get("position", "unknown")))}</p>
      <p><strong>Order:</strong> {escape(str(stale.get("order", "unknown")))}</p>
      <p><strong>Exposure:</strong> {escape(str(stale.get("exposure", "unknown")))}</p>
    </div>

    <div class="card" id="balance-semantics-observation-card">
      <h2>Balance Semantics</h2>
      <p><strong>Operator visibility: clear / warning / blocked</strong></p>
      <p><strong>Semantic state:</strong> <span class="chip"><code>{
        escape(str(balance_sem.get("balance_semantic_state") or "n/a"))
    }</code></span></p>
      <p><strong>Reason code:</strong> {
        escape(str(balance_sem.get("balance_reason_code") or "n/a"))
    }</p>
      <p><strong>Operator-visible state:</strong> {
        escape(str(balance_sem.get("balance_operator_visible_state") or "n/a"))
    }</p>
    </div>

    <div class="card" id="session-end-mismatch-observation-surface">
      <h2>Session End Mismatch</h2>
      <p><em>Observation (read-only). Local registry / run metadata / event-table hints only; not broker or exchange truth; not approval; not unlock.</em></p>
      <p><strong>Human runbook (operative steps):</strong> see <code>{
        escape(str(session_end_mismatch.get("runbook", "")))
    }</code> — Cockpit does not replace that process.</p>
      <p><strong>Status:</strong> <span class="chip"><code>{
        escape(str(session_end_mismatch.get("status", "unknown")))
    }</code></span></p>
      <p><strong>Summary:</strong> {escape(str(session_end_mismatch.get("summary", "unknown")))}</p>
      <p><strong>Observation reason:</strong> {
        escape(str(session_end_mismatch.get("observation_reason", "n/a")))
    }</p>
      <p><strong>Data source:</strong> <code>{
        escape(str(session_end_mismatch.get("data_source", "unknown")))
    }</code></p>
      <p><strong>Blocked next session (observation hint only, not enforcement):</strong> {
        escape(str(session_end_mismatch.get("blocked_next_session", False)))
    }</p>
      <p><strong>Reader schema:</strong> <code>{
        escape(str(session_end_mismatch.get("reader_schema_version", "n/a")))
    }</code></p>
    </div>

    <div class="card" id="evidence-state-card">
      <h2>Evidence State</h2>
      {_render_evidence_state_card_body(evidence)}
    </div>

    <div class="card" id="dependencies-state-observation-card">
      <h2>Dependencies State</h2>
      {_render_dependencies_state_card_body(dependencies)}
    </div>

    {update_officer_ergonomics_html}

    {update_officer_card_html}

    <div class="card truth-card" id="incident-state-read-model-observation-card">
      <h2>Incident-state read model</h2>
      <p><strong>Question-specific authority (read-model contract)</strong></p>
      <p><strong>Incident stop invoked:</strong> {
        escape(str(incident.get("incident_stop_invoked", False)))
    }</p>
      <p><strong>Incident stop source:</strong> <code>{
        escape(str(incident.get("incident_stop_source", "n/a")))
    }</code></p>
      <p><strong>PT_FORCE_NO_TRADE:</strong> {
        escape(
            str(
                incident.get("pt_force_no_trade")
                if incident.get("pt_force_no_trade") is not None
                else "n/a"
            )
        )
    }</p>
      <p><strong>PT_ENABLED:</strong> {
        escape(str(incident.get("pt_enabled") if incident.get("pt_enabled") is not None else "n/a"))
    }</p>
      <p><strong>PT_ARMED:</strong> {
        escape(str(incident.get("pt_armed") if incident.get("pt_armed") is not None else "n/a"))
    }</p>
      <p><strong>Kill-switch active:</strong> {
        escape(str(incident.get("kill_switch_active", False)))
    }</p>
      <p><strong>Kill-switch source:</strong> <code>{
        escape(str(incident.get("kill_switch_source", "n/a")))
    }</code></p>
      <p><strong>Entry permitted:</strong> {
        escape(
            str(
                incident.get("entry_permitted")
                if incident.get("entry_permitted") is not None
                else "n/a"
            )
        )
    }</p>
      <p><strong>Risk-gate kill-switch active:</strong> {
        escape(str(incident.get("risk_gate_kill_switch_active", False)))
    }</p>
      <p><strong>Operator authoritative state:</strong> <code>{
        escape(str(incident.get("operator_authoritative_state", "n/a")))
    }</code></p>
      <p><strong>Operator state reason:</strong> {
        escape(str(incident.get("operator_state_reason", "n/a")))
    }</p>
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
    "build_workflow_officer_panel_context",
    "build_ops_cockpit_payload",
    "render_ops_cockpit_html",
    "resolve_update_officer_route_inputs",
    "normalize_update_officer_source_preset",
    "build_update_officer_validation_aids",
]
