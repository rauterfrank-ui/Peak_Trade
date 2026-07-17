"""Phase 2 Operator Overview display adapter (presentation-only).

Composes a deterministic decision sentence and hero view-model from existing
canonical display contexts. No trading/decision/risk/economic/authority semantics
are derived here — only formatting and honest unavailable markers.
"""

from __future__ import annotations

from typing import Any

from .contracts import ActivityState

_UNAVAILABLE = "unavailable"
_DIRECTION_NEUTRAL = "Neutral"
_DECISION_BLOCKED = "Blocked"
_DECISION_OBSERVE = "Observe"


def _text(value: Any, *, default: str = _UNAVAILABLE) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _display_activity_state(raw: str) -> str:
    """Map legacy ACTIVE (processing evidence) to PROCESSED for operator overview."""
    state = _text(raw, default=ActivityState.NOT_AVAILABLE)
    if state == ActivityState.ACTIVE:
        return ActivityState.PROCESSED
    return state


def _primary_blocker(
    *,
    decision_funnel: dict[str, Any],
    safety_matrix: dict[str, Any],
) -> tuple[str, str]:
    """Return (blocker_label, blocker_scope). Never invent instrument-scoped blockers."""
    reasons = decision_funnel.get("most_frequent_block_reasons")
    if isinstance(reasons, list) and reasons:
        first = reasons[0] if isinstance(reasons[0], dict) else {}
        label = _text(first.get("label"), default="")
        if label and label != _UNAVAILABLE:
            return label, "fleet_or_funnel_scoped"
    if bool(safety_matrix.get("preflight_blocked") is True):
        return "Preflight blocked", "surface_safety_gate"
    return _UNAVAILABLE, "none"


def _regime_from_workspace_or_row(
    *,
    workspace: dict[str, Any],
    governed_row: dict[str, Any] | None,
) -> tuple[str, str]:
    regime = _text(workspace.get("ranking_regime"), default="")
    if regime and regime != _UNAVAILABLE:
        return regime, "selected_instrument_ranking_row"
    if isinstance(governed_row, dict):
        row_regime = _text(governed_row.get("regime"), default="")
        if row_regime and row_regime != _UNAVAILABLE:
            return row_regime, "selected_instrument_ranking_row"
    return _UNAVAILABLE, "none"


def _pipeline_group(funnel: dict[str, Any]) -> str:
    stages = funnel.get("stages")
    if not isinstance(stages, list):
        return _UNAVAILABLE
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        if stage.get("status") == ActivityState.PROCESSED and stage.get("label"):
            return _text(stage.get("label"))
    return _UNAVAILABLE


def _decision_state_label(*, activity_state: str, primary_blocker: str) -> str:
    if primary_blocker != _UNAVAILABLE:
        return _DECISION_BLOCKED
    if activity_state in (
        ActivityState.PROCESSED,
        ActivityState.AVAILABLE_NOT_RUN,
        ActivityState.NOT_AVAILABLE,
        ActivityState.STALE,
        ActivityState.FAILED,
        ActivityState.BLOCKED,
    ):
        if activity_state == ActivityState.FAILED:
            return _DECISION_BLOCKED
        if activity_state == ActivityState.BLOCKED:
            return _DECISION_BLOCKED
        return _DECISION_OBSERVE
    return _DECISION_OBSERVE


def build_operator_overview_display_v1(
    *,
    primary_values: dict[str, Any] | None = None,
    selected_instrument_workspace: dict[str, Any] | None = None,
    visual_operator_header: dict[str, Any] | None = None,
    decision_funnel_visual: dict[str, Any] | None = None,
    safety_matrix: dict[str, Any] | None = None,
    ai_activity_state: str | None = None,
    governed_top20: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build Phase-2 Operator Overview VM from existing display contexts only."""
    primary = primary_values if isinstance(primary_values, dict) else {}
    workspace = (
        selected_instrument_workspace if isinstance(selected_instrument_workspace, dict) else {}
    )
    header = visual_operator_header if isinstance(visual_operator_header, dict) else {}
    funnel = decision_funnel_visual if isinstance(decision_funnel_visual, dict) else {}
    safety = safety_matrix if isinstance(safety_matrix, dict) else {}
    governed = governed_top20 if isinstance(governed_top20, dict) else {}

    symbol = _text(workspace.get("symbol") or primary.get("symbol"))
    rank = workspace.get("ranking_rank")
    rank_display = str(rank) if rank is not None else _UNAVAILABLE

    governed_row = None
    rows = governed.get("rows") if isinstance(governed.get("rows"), list) else []
    for row in rows:
        if isinstance(row, dict) and _text(row.get("symbol")) == symbol:
            governed_row = row
            break

    regime, regime_scope = _regime_from_workspace_or_row(
        workspace=workspace, governed_row=governed_row
    )
    activity_raw = _text(ai_activity_state or header.get("ai_activity_state"))
    activity_display = _display_activity_state(activity_raw)
    blocker, blocker_scope = _primary_blocker(decision_funnel=funnel, safety_matrix=safety)
    decision_state = _decision_state_label(activity_state=activity_display, primary_blocker=blocker)

    # Direction is not invented — Neutral unless a canonical field already exists.
    direction = _DIRECTION_NEUTRAL
    if isinstance(governed_row, dict):
        for key in ("direction", "side", "bias"):
            candidate = _text(governed_row.get(key), default="")
            if candidate and candidate != _UNAVAILABLE:
                direction = candidate
                break

    contract = workspace.get("contract_metadata")
    contract_meta = contract if isinstance(contract, dict) else {}

    if symbol == _UNAVAILABLE:
        sentence = (
            f"Kein Instrument geladen (Rang {rank_display}). "
            f"Regime {regime}. "
            f"Entscheidung {decision_state}. "
            f"Primärer Blocker: {blocker}."
        )
    else:
        sentence = (
            f"{symbol} steht auf Rang {rank_display}. "
            f"Regime {regime}. "
            f"Entscheidung {decision_state}. "
            f"Primärer Blocker: {blocker}."
        )

    economic_status = _text(header.get("economic_gate_status"))
    risk_row = next(
        (
            r
            for r in (safety.get("rows") if isinstance(safety.get("rows"), list) else [])
            if isinstance(r, dict) and r.get("dimension_slug") == "risk"
        ),
        {},
    )
    risk_status = _text(risk_row.get("status_label") or risk_row.get("raw_status"))

    return {
        "section_visible": True,
        "read_only": True,
        "view_only": True,
        "non_authorizing": True,
        "phase": "PHASE_2",
        "hero_layout": "8_COLUMNS_PRIMARY,4_COLUMNS_SYSTEM_STATE",
        "decision_sentence": sentence,
        "decision_sentence_tokens": {
            "instrument": symbol,
            "rank": rank_display,
            "regime": regime,
            "decision_state": decision_state,
            "primary_blocker": blocker,
        },
        "selected_instrument": {
            "symbol": symbol,
            "exchange": _text(contract_meta.get("exchange")),
            "contract_type": _text(contract_meta.get("contract_type")),
            "timeframe": _text(primary.get("timeframe")),
            "last_price": _text(primary.get("last_close_display"), default="—"),
            "change": (
                f"{_text(primary.get('change_abs_display'))} ({_text(primary.get('change_pct_display'))})"
                if _text(primary.get("change_status")) == "available"
                else _UNAVAILABLE
            ),
            "high": _text(primary.get("last_high_display"), default="—"),
            "low": _text(primary.get("last_low_display"), default="—"),
            "volume": _text(primary.get("last_volume_display"), default="—"),
            "rank": rank_display,
            "score": _text(workspace.get("ranking_score_display")),
            "data_quality": _text(workspace.get("data_quality_status")),
            "freshness": _text(primary.get("last_bar_ts") or primary.get("generated_at_utc")),
        },
        "market_regime": {
            "trend": regime,
            "momentum": _UNAVAILABLE,
            "volatility": _UNAVAILABLE,
            "liquidity": _UNAVAILABLE,
            "bull_bear_balance": _UNAVAILABLE,
            "confidence_or_evidence_state": activity_display,
            "freshness": _text(header.get("data_freshness")),
            "scope": regime_scope,
            "scope_note": (
                "selected-instrument ranking row"
                if regime_scope == "selected_instrument_ranking_row"
                else "not instrument-scoped / unavailable"
            ),
        },
        "current_decision": {
            "state": decision_state,
            "direction": direction,
            "primary_blocker": blocker,
            "blocker_scope": blocker_scope,
            "pipeline_group": _pipeline_group(funnel),
            "ai_activity_state": activity_display,
            "ai_activity_state_raw": activity_raw,
            "data_quality_state": _text(workspace.get("data_quality_status")),
        },
        "critical_system_state": {
            "economic_validity": economic_status,
            "runtime_authority": _text(header.get("runtime_authority"), default="NONE"),
            "orders": "ORDERS_DISABLED",
            "live": "LIVE_DISABLED",
            "risk_status": risk_status,
            "safety_status": (
                "PREFLIGHT_BLOCKED" if bool(safety.get("preflight_blocked")) else _UNAVAILABLE
            ),
            "orders_allowed": False,
            "live_allowed": False,
            "runtime_authority_none": True,
        },
    }


__all__ = ["build_operator_overview_display_v1"]
