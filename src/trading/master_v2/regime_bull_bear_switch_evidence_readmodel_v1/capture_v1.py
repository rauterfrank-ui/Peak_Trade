"""Capture helpers at the authorized runtime point (evidence only)."""

from __future__ import annotations

from pathlib import Path

from trading.master_v2.double_play_state import ScopeEvent, SideState, TransitionDecision
from trading.master_v2.regime_bull_bear_switch_evidence_readmodel_v1.models_v1 import (
    RegimeBullBearSwitchEvidenceError,
    RegimeBullBearSwitchEvidenceReadmodelV1,
    build_from_authorized_capture_inputs_v1,
)
from trading.master_v2.regime_bull_bear_switch_evidence_readmodel_v1.persistence_v1 import (
    write_regime_bull_bear_switch_evidence_readmodel_v1,
)
from trading.master_v2.suitability_binding_v1 import SuitabilityRegimeStatus


def capture_regime_bull_bear_switch_evidence_readmodel_v1(
    *,
    regime_id: str,
    regime_status: SuitabilityRegimeStatus,
    previous_side_state: SideState,
    next_side_state: SideState,
    scope_event_type: ScopeEvent,
    transition: TransitionDecision,
    instrument_id: str,
    trading_epoch: int,
    evidence_path: str | Path | None = None,
) -> RegimeBullBearSwitchEvidenceReadmodelV1:
    """Capture eight fields; optionally persist to an explicit evidence path."""
    evidence = build_from_authorized_capture_inputs_v1(
        regime_id=regime_id,
        regime_status=regime_status,
        previous_side_state=previous_side_state,
        next_side_state=next_side_state,
        scope_event_type=scope_event_type,
        transition=transition,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
    )
    if evidence_path is not None and str(evidence_path).strip():
        write_regime_bull_bear_switch_evidence_readmodel_v1(evidence_path, evidence)
    return evidence


def try_capture_regime_bull_bear_switch_evidence_readmodel_v1(
    *,
    regime_id: str,
    regime_status: SuitabilityRegimeStatus,
    previous_side_state: SideState,
    next_side_state: SideState,
    scope_event_type: ScopeEvent,
    transition: TransitionDecision,
    instrument_id: str,
    trading_epoch: int,
    evidence_path: str | Path | None = None,
) -> RegimeBullBearSwitchEvidenceReadmodelV1 | None:
    """Trading-safe capture: never raises into the decision path.

    In-memory capture failures yield ``None``. Optional durable write failures are
    swallowed so trading outcomes remain unchanged; the in-memory capture is kept.
    """
    try:
        evidence = build_from_authorized_capture_inputs_v1(
            regime_id=regime_id,
            regime_status=regime_status,
            previous_side_state=previous_side_state,
            next_side_state=next_side_state,
            scope_event_type=scope_event_type,
            transition=transition,
            instrument_id=instrument_id,
            trading_epoch=trading_epoch,
        )
    except (RegimeBullBearSwitchEvidenceError, TypeError, ValueError):
        return None
    if evidence_path is not None and str(evidence_path).strip():
        try:
            write_regime_bull_bear_switch_evidence_readmodel_v1(evidence_path, evidence)
        except (RegimeBullBearSwitchEvidenceError, OSError):
            pass
    return evidence
