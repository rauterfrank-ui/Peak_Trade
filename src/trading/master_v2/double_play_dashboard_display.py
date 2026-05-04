# src/trading/master_v2/double_play_dashboard_display.py
"""
Pure read-only dashboard display DTO for Master V2 Double Play.

Aggregates already-computed pure decisions into a display-safe snapshot only.
No WebUI, ASGI web framework imports, I/O, scanner, exchange, sessions, or Live authority.
See docs/ops/specs/MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple

from trading.master_v2.double_play_capital_slot import (
    CapitalSlotRatchetDecision,
    CapitalSlotReleaseDecision,
)
from trading.master_v2.double_play_composition import (
    DoublePlayCompositionDecision,
    DoublePlayCompositionStatus,
)
from trading.master_v2.double_play_futures_input import (
    FuturesInputReadinessDecision,
    FuturesReadinessStatus,
)
from trading.master_v2.double_play_state import TransitionDecision
from trading.master_v2.double_play_suitability import (
    SuitabilityClass,
    SuitabilityProjectionDecision,
)
from trading.master_v2.double_play_survival import (
    SurvivalEnvelopeDecision,
    SurvivalEnvelopeStatus,
)

DOUBLE_PLAY_DASHBOARD_DISPLAY_LAYER_VERSION = "v0"


class DashboardDisplayStatus(str, Enum):
    """Overall display health; non-authority."""

    DISPLAY_READY = "display_ready"
    DISPLAY_WARNING = "display_warning"
    DISPLAY_BLOCKED = "display_blocked"
    DISPLAY_MISSING = "display_missing"
    DISPLAY_ERROR = "display_error"


# Per-panel status uses the same vocabulary (display map / brief).
DashboardPanelStatus = DashboardDisplayStatus


@dataclass(frozen=True)
class DoublePlayDashboardPanel:
    name: str
    status: DashboardPanelStatus
    summary: str
    blockers: Tuple[str, ...]
    missing_inputs: Tuple[str, ...]
    live_authorization: bool = False
    is_authority: bool = False
    is_signal: bool = False


@dataclass(frozen=True)
class DoublePlayDashboardDisplaySnapshot:
    panels: Tuple[DoublePlayDashboardPanel, ...]
    overall_status: DashboardDisplayStatus
    no_live_banner_visible: bool = True
    display_only: bool = True
    trading_ready: bool = False
    testnet_ready: bool = False
    live_ready: bool = False
    live_authorization: bool = False
    warnings: Tuple[str, ...] = ()


# HTTP / JSON payload schema for read-only dashboard display (structured metadata v2).
DISPLAY_JSON_LAYER_VERSION = "v2"

_DISPLAY_JSON_PANEL_GROUP: Mapping[str, str] = {
    "futures_input": "input",
    "state_transition": "state",
    "survival_envelope": "scope",
    "strategy_suitability": "strategy",
    "capital_slot_ratchet": "capital",
    "capital_slot_release": "capital",
    "composition": "composition",
}

_DISPLAY_JSON_PAYLOAD_SEVERITY: Mapping[DashboardDisplayStatus, int] = {
    DashboardDisplayStatus.DISPLAY_READY: 0,
    DashboardDisplayStatus.DISPLAY_WARNING: 10,
    DashboardDisplayStatus.DISPLAY_MISSING: 20,
    DashboardDisplayStatus.DISPLAY_BLOCKED: 30,
    DashboardDisplayStatus.DISPLAY_ERROR: 40,
}


def _panel(
    name: str,
    status: DashboardPanelStatus,
    summary: str,
    *,
    blockers: Tuple[str, ...] = (),
    missing: Tuple[str, ...] = (),
) -> DoublePlayDashboardPanel:
    return DoublePlayDashboardPanel(
        name=name,
        status=status,
        summary=summary,
        blockers=blockers,
        missing_inputs=missing,
        live_authorization=False,
        is_authority=False,
        is_signal=False,
    )


def _severity_rank(s: DashboardDisplayStatus) -> int:
    return {
        DashboardDisplayStatus.DISPLAY_ERROR: 4,
        DashboardDisplayStatus.DISPLAY_BLOCKED: 3,
        DashboardDisplayStatus.DISPLAY_WARNING: 2,
        DashboardDisplayStatus.DISPLAY_MISSING: 1,
        DashboardDisplayStatus.DISPLAY_READY: 0,
    }[s]


def _max_severity(a: DashboardDisplayStatus, b: DashboardDisplayStatus) -> DashboardDisplayStatus:
    return a if _severity_rank(a) >= _severity_rank(b) else b


def _collect_input_live_warnings(
    *,
    futures_input: Optional[FuturesInputReadinessDecision],
    transition: Optional[TransitionDecision],
    survival: Optional[SurvivalEnvelopeDecision],
    suitability: Optional[SuitabilityProjectionDecision],
    capital_slot_ratchet: Optional[CapitalSlotRatchetDecision],
    capital_slot_release: Optional[CapitalSlotReleaseDecision],
    composition: Optional[DoublePlayCompositionDecision],
) -> Tuple[str, ...]:
    w: list[str] = []
    if futures_input is not None and futures_input.live_authorization:
        w.append("futures_input reported live_authorization; ignored for display")
    if transition is not None and transition.live_authorization_granted:
        w.append("transition reported live_authorization_granted; ignored for display")
    if survival is not None and survival.live_authorization:
        w.append("survival reported live_authorization; ignored for display")
    if suitability is not None:
        if suitability.live_authorization:
            w.append("suitability reported live_authorization; ignored for display")
        if suitability.projection.live_authorization:
            w.append("suitability.projection reported live_authorization; ignored for display")
    if capital_slot_ratchet is not None and capital_slot_ratchet.live_authorization:
        w.append("capital_slot_ratchet reported live_authorization; ignored for display")
    if capital_slot_release is not None and capital_slot_release.live_authorization:
        w.append("capital_slot_release reported live_authorization; ignored for display")
    if composition is not None and composition.live_authorization:
        w.append("composition reported live_authorization; ignored for display")
    return tuple(w)


def _panel_futures_input(d: Optional[FuturesInputReadinessDecision]) -> DoublePlayDashboardPanel:
    if d is None:
        return _panel(
            "futures_input",
            DashboardPanelStatus.DISPLAY_MISSING,
            "No futures input readiness decision supplied (display-only gap).",
        )
    if d.status is FuturesReadinessStatus.BLOCKED:
        return _panel(
            "futures_input",
            DashboardPanelStatus.DISPLAY_BLOCKED,
            "Futures input readiness is blocked (data-only).",
            blockers=tuple(str(x) for x in d.block_reasons),
            missing=d.missing_inputs,
        )
    return _panel(
        "futures_input",
        DashboardPanelStatus.DISPLAY_READY,
        "Futures input readiness is data-ready (not trading permission).",
    )


def _panel_transition(d: Optional[TransitionDecision]) -> DoublePlayDashboardPanel:
    if d is None:
        return _panel(
            "state_transition",
            DashboardPanelStatus.DISPLAY_MISSING,
            "No transition decision supplied (display-only gap).",
        )
    if d.live_authorization_granted:
        return _panel(
            "state_transition",
            DashboardPanelStatus.DISPLAY_ERROR,
            "Transition carried live_authorization_granted; display treats as error state.",
            blockers=("live_authorization_granted_true",),
        )
    if not d.allowed:
        return _panel(
            "state_transition",
            DashboardPanelStatus.DISPLAY_WARNING,
            f"Transition not allowed: {d.reason_code}",
            blockers=(d.reason_code,),
        )
    return _panel(
        "state_transition",
        DashboardPanelStatus.DISPLAY_READY,
        f"Transition allowed (model label): {d.reason_code}",
    )


def _panel_survival(d: Optional[SurvivalEnvelopeDecision]) -> DoublePlayDashboardPanel:
    if d is None:
        return _panel(
            "survival_envelope",
            DashboardPanelStatus.DISPLAY_MISSING,
            "No survival envelope decision supplied (display-only gap).",
        )
    if d.status is SurvivalEnvelopeStatus.BLOCKED or not d.pre_authorization_eligible:
        return _panel(
            "survival_envelope",
            DashboardPanelStatus.DISPLAY_BLOCKED,
            "Survival envelope blocked or not pre-authorization eligible (data-only).",
            blockers=tuple(str(x) for x in d.block_reasons),
        )
    return _panel(
        "survival_envelope",
        DashboardPanelStatus.DISPLAY_READY,
        "Survival envelope OK (model label only).",
    )


def _panel_suitability(d: Optional[SuitabilityProjectionDecision]) -> DoublePlayDashboardPanel:
    if d is None:
        return _panel(
            "strategy_suitability",
            DashboardPanelStatus.DISPLAY_MISSING,
            "No suitability projection supplied (display-only gap).",
        )
    if d.live_authorization or d.projection.live_authorization:
        return _panel(
            "strategy_suitability",
            DashboardPanelStatus.DISPLAY_ERROR,
            "Suitability carried live_authorization; display treats as error state.",
            blockers=("live_authorization_true",),
        )
    proj = d.projection
    if proj.suitability_class is SuitabilityClass.UNKNOWN_SUITABILITY:
        return _panel(
            "strategy_suitability",
            DashboardPanelStatus.DISPLAY_BLOCKED,
            "Suitability unknown (fail-closed display).",
            blockers=tuple(str(x) for x in proj.block_reasons),
            missing=proj.missing_inputs,
        )
    if proj.block_reasons:
        return _panel(
            "strategy_suitability",
            DashboardPanelStatus.DISPLAY_WARNING,
            "Suitability has block reasons (metadata only).",
            blockers=tuple(str(x) for x in proj.block_reasons),
            missing=proj.missing_inputs,
        )
    return _panel(
        "strategy_suitability",
        DashboardPanelStatus.DISPLAY_READY,
        "Suitability projection present (not strategy activation).",
    )


def _panel_ratchet(d: Optional[CapitalSlotRatchetDecision]) -> DoublePlayDashboardPanel:
    if d is None:
        return _panel(
            "capital_slot_ratchet",
            DashboardPanelStatus.DISPLAY_MISSING,
            "No capital slot ratchet decision supplied (display-only gap).",
        )
    if d.live_authorization:
        return _panel(
            "capital_slot_ratchet",
            DashboardPanelStatus.DISPLAY_ERROR,
            "Ratchet decision reported live_authorization; display error.",
            blockers=("live_authorization_true",),
        )
    if d.block_reasons:
        return _panel(
            "capital_slot_ratchet",
            DashboardPanelStatus.DISPLAY_BLOCKED,
            "Capital slot ratchet blocked (data-only).",
            blockers=tuple(str(x) for x in d.block_reasons),
        )
    return _panel(
        "capital_slot_ratchet",
        DashboardPanelStatus.DISPLAY_READY,
        "Capital slot ratchet decision present (no allocation).",
    )


def _panel_release(d: Optional[CapitalSlotReleaseDecision]) -> DoublePlayDashboardPanel:
    if d is None:
        return _panel(
            "capital_slot_release",
            DashboardPanelStatus.DISPLAY_MISSING,
            "No capital slot release decision supplied (display-only gap).",
        )
    if d.live_authorization:
        return _panel(
            "capital_slot_release",
            DashboardPanelStatus.DISPLAY_ERROR,
            "Release decision reported live_authorization; display error.",
            blockers=("live_authorization_true",),
        )
    if d.block_reasons:
        return _panel(
            "capital_slot_release",
            DashboardPanelStatus.DISPLAY_BLOCKED,
            "Capital slot release path blocked (data-only).",
            blockers=tuple(str(x) for x in d.block_reasons),
        )
    if d.released:
        return _panel(
            "capital_slot_release",
            DashboardPanelStatus.DISPLAY_WARNING,
            "Capital slot released (data-only label; does not perform release here).",
        )
    return _panel(
        "capital_slot_release",
        DashboardPanelStatus.DISPLAY_READY,
        "Capital slot active (release decision present; data-only).",
    )


def _panel_composition(d: Optional[DoublePlayCompositionDecision]) -> DoublePlayDashboardPanel:
    if d is None:
        return _panel(
            "composition",
            DashboardPanelStatus.DISPLAY_MISSING,
            "No composition decision supplied (display-only gap).",
        )
    if d.live_authorization:
        return _panel(
            "composition",
            DashboardPanelStatus.DISPLAY_ERROR,
            "Composition reported live_authorization; display error.",
            blockers=("live_authorization_true",),
        )
    st = d.status
    if st is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY:
        return _panel(
            "composition",
            DashboardPanelStatus.DISPLAY_READY,
            "Composition: ELIGIBLE_MODEL_ONLY — data-only; not trading-ready.",
            blockers=tuple(str(x) for x in d.block_reasons),
        )
    if st in (DoublePlayCompositionStatus.KILL_ALL, DoublePlayCompositionStatus.CHOP_GUARD):
        return _panel(
            "composition",
            DashboardPanelStatus.DISPLAY_BLOCKED,
            f"Composition status {st.value} (display-only).",
            blockers=tuple(str(x) for x in d.block_reasons),
        )
    if st is DoublePlayCompositionStatus.BLOCKED:
        return _panel(
            "composition",
            DashboardPanelStatus.DISPLAY_BLOCKED,
            "Composition blocked (data-only).",
            blockers=tuple(str(x) for x in d.block_reasons),
        )
    if st is DoublePlayCompositionStatus.OBSERVE_ONLY:
        return _panel(
            "composition",
            DashboardPanelStatus.DISPLAY_WARNING,
            "Composition observe-only (data-only).",
            blockers=tuple(str(x) for x in d.block_reasons),
        )
    return _panel(
        "composition",
        DashboardPanelStatus.DISPLAY_WARNING,
        d.reason,
        blockers=tuple(str(x) for x in d.block_reasons),
    )


def build_dashboard_display_snapshot(
    *,
    futures_input: Optional[FuturesInputReadinessDecision] = None,
    transition: Optional[TransitionDecision] = None,
    survival: Optional[SurvivalEnvelopeDecision] = None,
    suitability: Optional[SuitabilityProjectionDecision] = None,
    capital_slot_ratchet: Optional[CapitalSlotRatchetDecision] = None,
    capital_slot_release: Optional[CapitalSlotReleaseDecision] = None,
    composition: Optional[DoublePlayCompositionDecision] = None,
) -> DoublePlayDashboardDisplaySnapshot:
    """
    Build a display-only snapshot from pure decisions. Never authorizes Live or trading.

    Missing optional inputs produce DISPLAY_MISSING panels. Contradictory live flags on
    inputs yield DISPLAY_ERROR on the affected panel and warning strings on the snapshot.
    """
    input_live = _collect_input_live_warnings(
        futures_input=futures_input,
        transition=transition,
        survival=survival,
        suitability=suitability,
        capital_slot_ratchet=capital_slot_ratchet,
        capital_slot_release=capital_slot_release,
        composition=composition,
    )

    panels = (
        _panel_futures_input(futures_input),
        _panel_transition(transition),
        _panel_survival(survival),
        _panel_suitability(suitability),
        _panel_ratchet(capital_slot_ratchet),
        _panel_release(capital_slot_release),
        _panel_composition(composition),
    )

    overall = DashboardDisplayStatus.DISPLAY_READY
    for p in panels:
        if p.status is DashboardPanelStatus.DISPLAY_MISSING:
            overall = _max_severity(overall, DashboardDisplayStatus.DISPLAY_WARNING)
        else:
            overall = _max_severity(overall, p.status)

    extra: list[str] = list(input_live)
    if any(p.status is DashboardPanelStatus.DISPLAY_MISSING for p in panels):
        extra.append("one_or_more_panels_missing_optional_pure_inputs")

    warnings = tuple(dict.fromkeys(extra))

    return DoublePlayDashboardDisplaySnapshot(
        panels=panels,
        overall_status=overall,
        no_live_banner_visible=True,
        display_only=True,
        trading_ready=False,
        testnet_ready=False,
        live_ready=False,
        live_authorization=False,
        warnings=warnings,
    )


def _assembled_at_iso_utc() -> str:
    dt = datetime.now(timezone.utc).replace(microsecond=0)
    return dt.isoformat().replace("+00:00", "Z")


def _jsonable_dashboard_panel(panel: DoublePlayDashboardPanel, ordinal: int) -> Dict[str, Any]:
    st = panel.status
    status_val = st.value if isinstance(st, Enum) else str(st)
    panel_group = _DISPLAY_JSON_PANEL_GROUP.get(panel.name, "unknown")
    return {
        "name": panel.name,
        "status": status_val,
        "summary": panel.summary,
        "blockers": list(panel.blockers),
        "missing_inputs": list(panel.missing_inputs),
        "live_authorization": panel.live_authorization,
        "is_authority": panel.is_authority,
        "is_signal": panel.is_signal,
        "ordinal": ordinal,
        "panel_group": panel_group,
        "severity_rank": _DISPLAY_JSON_PAYLOAD_SEVERITY[st],
    }


def snapshot_to_jsonable(snap: DoublePlayDashboardDisplaySnapshot) -> Dict[str, Any]:
    """Convert display snapshot to JSON-serializable dict (enum values as strings)."""
    overall = snap.overall_status
    overall_val = overall.value if isinstance(overall, Enum) else str(overall)
    return {
        "display_layer_version": DISPLAY_JSON_LAYER_VERSION,
        "display_snapshot_meta": {
            "source_kind": "static_display_v0",
            "source_id": "webui_dashboard_display_static_v0",
            "assembled_at_iso": _assembled_at_iso_utc(),
        },
        "panels": [_jsonable_dashboard_panel(p, i) for i, p in enumerate(snap.panels)],
        "overall_status": overall_val,
        "no_live_banner_visible": snap.no_live_banner_visible,
        "display_only": snap.display_only,
        "trading_ready": snap.trading_ready,
        "testnet_ready": snap.testnet_ready,
        "live_ready": snap.live_ready,
        "live_authorization": snap.live_authorization,
        "warnings": list(snap.warnings),
    }
