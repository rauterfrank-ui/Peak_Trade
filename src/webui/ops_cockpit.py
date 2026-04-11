from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Dict, List, Optional
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
        f'<div class="card truth-card" style="margin-bottom:20px;">'
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


def _render_policy_guard_observation_card(payload: Dict[str, object]) -> str:
    """HTML block: policy/guard observation from existing payload keys only (read-only wording)."""
    ps_raw = payload.get("policy_state")
    gs_raw = payload.get("guard_state")
    ps = ps_raw if isinstance(ps_raw, dict) else {}
    gs = gs_raw if isinstance(gs_raw, dict) else {}

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
        v = escape(_fmt_val(ps.get(key)))
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
        v = escape(_fmt_val(gs.get(key)))
        rows_html.append(
            f"<tr><td style='padding:4px 8px 4px 0;vertical-align:top;'><code>{escape(label)}</code></td>"
            f"<td style='padding:4px 0;'><code>{v}</code></td></tr>"
        )

    table_html = (
        "<table style='width:100%;border-collapse:collapse;font-size:0.9em;'>"
        "<tbody>"
        f"{''.join(rows_html)}"
        "</tbody></table>"
    )
    intro = (
        "Same fields as <code>policy_state</code> / <code>guard_state</code> in the JSON payload for "
        "this page. Observation only — not a control surface; does not grant live access or change "
        "enforcement."
    )
    return (
        f'<div class="card truth-card" style="margin-bottom:20px;">'
        f"<h2>Policy / guard rails — observed state</h2>"
        f"<p><strong>Read-only.</strong> {intro}</p>"
        f"{table_html}"
        f"</div>"
    )


def _render_phase57_snapshot_discoverability_card() -> str:
    """HTML block: discoverability links to existing Phase 57 snapshot API (read-only, no new semantics)."""
    return (
        f'<div class="card truth-card" style="margin-bottom:20px;">'
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
        f'<div class="card truth-card" style="margin-bottom:20px;">'
        f"<h2>Incident — observed rollup</h2>"
        f"<p><strong>Read-only.</strong> {intro}</p>"
        f"{table_html}"
        f"</div>"
    )


def _render_run_state_observation_card(payload: Dict[str, object]) -> str:
    """HTML block: compact run-state rollup from existing ``run_state`` keys only (read-only wording)."""
    rs_raw = payload.get("run_state")
    rs = rs_raw if isinstance(rs_raw, dict) else {}

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
        ("run_state.status", "status"),
        ("run_state.active", "active"),
        ("run_state.last_run_status", "last_run_status"),
        ("run_state.session_active", "session_active"),
        ("run_state.generated_at", "generated_at"),
        ("run_state.freshness_status", "freshness_status"),
    ):
        if key not in rs:
            continue
        v = escape(_fmt_val(rs.get(key)))
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
        f'<div class="card truth-card" style="margin-bottom:20px;">'
        f"<h2>Run state — observed rollup</h2>"
        f"<p><strong>Read-only.</strong> {intro}</p>"
        f"{table_html}"
        f"</div>"
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
        except Exception:
            pass
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
        except Exception:
            pass
    run_state = {
        "status": "active" if _session_active else "idle",
        "active": _session_active,
        "last_run_status": _last_run_status,
        "session_active": _session_active,
        "generated_at": truth_state["last_verified_utc"],
        "freshness_status": v3_summary["freshness_status"],
    }
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
    _stale_signals = [_position_stale, _exposure_stale]
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
        "order": "unknown",
        "exposure": _exposure_stale,
        "summary": _stale_summary,
    }
    # Session-end mismatch surface (placeholder: no runtime reconciliation yet)
    session_end_mismatch_state = {
        "status": "unknown",
        "summary": "no_session_end_reconciliation",
        "blocked_next_session": False,
        "runbook": "RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH",
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
    _exchange_status = "unknown"
    _p85_base = repo_root / "out" / "ops" if repo_root else Path("out/ops")
    if _p85_base.exists():
        try:
            import json
            import time

            p85_files = sorted(
                _p85_base.glob("**/P85_RESULT.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if p85_files:
                p85_path = p85_files[0]
                age_sec = time.time() - p85_path.stat().st_mtime
                if age_sec <= 3600:
                    with open(p85_path, encoding="utf-8") as f:
                        p85_data = json.load(f)
                    conn = p85_data.get("connectivity", {})
                    if conn.get("ok") is True:
                        _exchange_status = "ok"
                    else:
                        _exchange_status = "degraded"
        except Exception:
            pass
    _market_data_cache_status: Optional[str] = None
    if _config_path and _config_path.exists():
        try:
            from src.data.kraken_cache_loader import (
                check_data_health_only,
                get_real_market_smokes_config,
            )

            rms = get_real_market_smokes_config(str(_config_path))
            base_path = repo_root / rms["base_path"] if repo_root else Path(rms["base_path"])
            if base_path.exists():
                health = check_data_health_only(
                    base_path,
                    market=rms.get("default_market", "BTC/EUR"),
                    timeframe=rms.get("default_timeframe", "1h"),
                    min_bars=rms.get("min_bars", 500),
                )
                if health.status == "ok":
                    _market_data_cache_status = "ok"
                elif health.status in ("missing_file", "too_few_bars", "empty", "invalid_format"):
                    _market_data_cache_status = "degraded"
                else:
                    _market_data_cache_status = "warn"
        except Exception:
            pass
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
        "run_state": run_state,
        "incident_state": incident_state,
        "exposure_state": exposure_state,
        "stale_state": stale_state,
        "balance_semantics_state": balance_semantics_state,
        "session_end_mismatch_state": session_end_mismatch_state,
        "human_supervision_state": human_supervision_state,
        "evidence_state": evidence_state,
        "dependencies_state": dependencies_state,
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
        "phase83_eligibility_snapshot": phase83_eligibility_snapshot,
        "update_officer_ui": update_officer_ui,
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
            '<div class="card truth-card">'
            "<h2>Update Officer</h2>"
            "<p><strong>Read-only.</strong> Notifier summary from local payload (if provided).</p>"
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
        '<div class="card truth-card">'
        "<h2>Update Officer</h2>"
        "<p><strong>Read-only.</strong> Deterministic notifier view (v4 consumer layer).</p>"
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

    dep_extra = ""
    dep_sum = deps.get("summary")
    if dep_sum is not None and str(dep_sum).strip() != "":
        dep_extra = (
            "<p><strong>dependencies_state.summary</strong> (observation): "
            f"<code>{escape(str(dep_sum))}</code></p>"
        )

    ev_extra = ""
    ev_sum = ev.get("summary")
    if ev_sum is not None and str(ev_sum).strip() != "":
        ev_extra = (
            "<p><strong>evidence_state.summary</strong> (observation): "
            f"<code>{escape(str(ev_sum))}</code></p>"
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

    glance_intro = (
        "<p><strong>Read-only.</strong> Same rollup fields as before (v3 executive summary cards); "
        "no write actions.</p>"
    )

    inner = _render_status_at_a_glance_inner(payload)

    return (
        '<div class="operator-summary-surface exec-summary">'
        "<h2>Operator summary (read-only)</h2>"
        '<p class="operator-summary-disclaimer"><strong>Observation only.</strong> '
        "Read-only snapshot from local artifacts and the <code>GET /api/ops-cockpit</code> "
        "payload shape. <strong>Not an approval, not an unlock,</strong> not a substitute for "
        "your governance process.</p>"
        "<h3>System status (observation)</h3>"
        "<p><strong>system_state.mode</strong> (observation): "
        f"<code>{mode_s}</code></p>"
        "<p><strong>system_state.execution_model</strong> (observation): "
        f"<code>{exec_m}</code></p>"
        f"{dep_extra}"
        f"{ev_extra}"
        "<h3>Go / No-Go observation (not approval)</h3>"
        f"{go_no_go_intro}"
        f"{go_lines}"
        "<h3>Status at a glance</h3>"
        f"{glance_intro}"
        f"{inner}"
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
    boundary = payload["ai_boundary_state"]
    runtime = payload["runtime_unknown_state"]
    exposure = payload.get("exposure_state") or {}
    stale = payload.get("stale_state") or {}
    balance_sem = payload.get("balance_semantics_state") or {}
    session_end_mismatch = payload.get("session_end_mismatch_state") or {}
    human_supervision = payload.get("human_supervision_state") or {}
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
    policy_guard_observation_html = _render_policy_guard_observation_card(payload)
    phase57_snapshot_discoverability_html = _render_phase57_snapshot_discoverability_card()
    incident_observation_html = _render_incident_observation_card(payload)
    run_state_observation_html = _render_run_state_observation_card(payload)
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
    .operator-summary-disclaimer {{ border-left: 4px solid #607d8b; padding-left: 12px; margin: 12px 0; }}
    .operator-summary-surface h3 {{ font-size: 1.05em; margin-top: 18px; margin-bottom: 8px; }}
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
  {policy_guard_observation_html}
  {phase57_snapshot_discoverability_html}
  {incident_observation_html}
  {run_state_observation_html}
  {phase83_eligibility_html}
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

    <div class="card">
      <h2>Exposure State</h2>
      <p><strong>Read-only exposure / risk surface (placeholder)</strong></p>
      <p><strong>Summary:</strong> <span class="chip"><code>{escape(str(exposure.get("summary", "unknown")))}</code></span></p>
      <p><strong>Treasury separation:</strong> {escape(str(exposure.get("treasury_separation", "unknown")))}</p>
      <p><strong>Risk status:</strong> {escape(str(exposure.get("risk_status", "unknown")))}</p>
    </div>

    <div class="card">
      <h2>Stale State</h2>
      <p><strong>Reconciliation hardening: balance / position / order staleness</strong></p>
      <p><strong>Summary:</strong> <span class="chip"><code>{escape(str(stale.get("summary", "unknown")))}</code></span></p>
      <p><strong>Balance:</strong> {escape(str(stale.get("balance", "unknown")))}</p>
      <p><strong>Position:</strong> {escape(str(stale.get("position", "unknown")))}</p>
      <p><strong>Order:</strong> {escape(str(stale.get("order", "unknown")))}</p>
      <p><strong>Exposure:</strong> {escape(str(stale.get("exposure", "unknown")))}</p>
    </div>

    <div class="card">
      <h2>Balance Semantics</h2>
      <p><strong>Operator visibility: clear / warning / blocked</strong></p>
      <p><strong>Semantic state:</strong> <span class="chip"><code>{escape(str(balance_sem.get("balance_semantic_state") or "n/a"))}</code></span></p>
      <p><strong>Reason code:</strong> {escape(str(balance_sem.get("balance_reason_code") or "n/a"))}</p>
      <p><strong>Operator-visible state:</strong> {escape(str(balance_sem.get("balance_operator_visible_state") or "n/a"))}</p>
    </div>

    <div class="card">
      <h2>Session End Mismatch</h2>
      <p><strong>Local closeout vs broker at session end; unresolved blocks next session</strong></p>
      <p><strong>Status:</strong> <span class="chip"><code>{escape(str(session_end_mismatch.get("status", "unknown")))}</code></span></p>
      <p><strong>Summary:</strong> {escape(str(session_end_mismatch.get("summary", "unknown")))}</p>
      <p><strong>Blocked next session:</strong> {escape(str(session_end_mismatch.get("blocked_next_session", False)))}</p>
      <p><strong>Runbook:</strong> <code>{escape(str(session_end_mismatch.get("runbook", "")))}</code></p>
    </div>

    <div class="card">
      <h2>Human Supervision</h2>
      <p><strong>Pilot design intent (read-only; per PILOT_GO_NO_GO_CHECKLIST row 55)</strong></p>
      <p><strong>Status:</strong> <span class="chip"><code>{escape(str(human_supervision.get("status", "unknown")))}</code></span></p>
      <p><strong>Mode:</strong> <span class="chip"><code>{escape(str(human_supervision.get("mode", "unknown")))}</code></span></p>
      <p><strong>Summary:</strong> {escape(str(human_supervision.get("summary", "unknown")))}</p>
    </div>

    <div class="card">
      <h2>Evidence State</h2>
      <p><strong>Read-only evidence / audit surface (derived from truth sources)</strong></p>
      <p><strong>Summary:</strong> <span class="chip"><code>{escape(str(evidence.get("summary", "unknown")))}</code></span></p>
      <p><strong>Freshness:</strong> {escape(str(evidence.get("freshness_status", "unknown")))}</p>
      <p><strong>Audit trail:</strong> {escape(str(evidence.get("audit_trail", "unknown")))}</p>
    </div>

    <div class="card">
      <h2>Dependencies State</h2>
      <p><strong>Read-only dependencies surface (placeholder)</strong></p>
      <p><strong>Summary:</strong> <span class="chip"><code>{escape(str(dependencies.get("summary", "unknown")))}</code></span></p>
      <p><strong>Exchange:</strong> {escape(str(dependencies.get("exchange", "unknown")))}</p>
      <p><strong>Telemetry:</strong> {escape(str(dependencies.get("telemetry", "unknown")))}</p>
    </div>

    {update_officer_ergonomics_html}

    {update_officer_card_html}

    <div class="card truth-card">
      <h2>Incident-state read model</h2>
      <p><strong>Question-specific authority (read-model contract)</strong></p>
      <p><strong>Incident stop invoked:</strong> {escape(str(incident.get("incident_stop_invoked", False)))}</p>
      <p><strong>Incident stop source:</strong> <code>{escape(str(incident.get("incident_stop_source", "n/a")))}</code></p>
      <p><strong>PT_FORCE_NO_TRADE:</strong> {escape(str(incident.get("pt_force_no_trade") if incident.get("pt_force_no_trade") is not None else "n/a"))}</p>
      <p><strong>PT_ENABLED:</strong> {escape(str(incident.get("pt_enabled") if incident.get("pt_enabled") is not None else "n/a"))}</p>
      <p><strong>PT_ARMED:</strong> {escape(str(incident.get("pt_armed") if incident.get("pt_armed") is not None else "n/a"))}</p>
      <p><strong>Kill-switch active:</strong> {escape(str(incident.get("kill_switch_active", False)))}</p>
      <p><strong>Kill-switch source:</strong> <code>{escape(str(incident.get("kill_switch_source", "n/a")))}</code></p>
      <p><strong>Entry permitted:</strong> {escape(str(incident.get("entry_permitted") if incident.get("entry_permitted") is not None else "n/a"))}</p>
      <p><strong>Risk-gate kill-switch active:</strong> {escape(str(incident.get("risk_gate_kill_switch_active", False)))}</p>
      <p><strong>Operator authoritative state:</strong> <code>{escape(str(incident.get("operator_authoritative_state", "n/a")))}</code></p>
      <p><strong>Operator state reason:</strong> {escape(str(incident.get("operator_state_reason", "n/a")))}</p>
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
