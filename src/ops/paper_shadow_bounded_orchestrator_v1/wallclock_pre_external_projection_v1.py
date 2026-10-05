"""Project existing wallclock bridge_cycle truth into Paper Shadow PRE_EXTERNAL events.

Composition-only: does not re-run Master V2 decision logic or GHV full-core closure.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.shadow_routing_v1 import (
    PreExternalProductiveEventV1,
)


def project_wallclock_pre_external_from_bridge_cycle_v1(
    bridge_cycle: dict[str, Any] | None,
    *,
    session_id: str,
    instrument_id: str,
) -> PreExternalProductiveEventV1 | None:
    """Map bridge intended_action + decision_outcome to PRE_EXTERNAL carrier when already enter-eligible."""
    if not bridge_cycle:
        return None
    outcome = str(bridge_cycle.get("decision_outcome") or "").strip().lower()
    if outcome not in {"enter_long", "enter_short"}:
        return None
    intended = bridge_cycle.get("intended_action")
    if not isinstance(intended, dict):
        return None
    if bool(intended.get("safety_blocked")):
        return None
    side = str(intended.get("intended_side") or "").strip().upper()
    if side not in {"BUY", "SELL"}:
        return None
    qty = Decimal(str(intended.get("intended_quantity") or "0"))
    if qty <= 0:
        return None
    mark = bridge_cycle.get("market_data_reference") or {}
    mark_px = mark.get("mid_price") if isinstance(mark, dict) else None
    if mark_px is None:
        basis = bridge_cycle.get("price_basis") or {}
        mark_px = basis.get("mid_price") if isinstance(basis, dict) else None
    if mark_px is None:
        return None
    cycle_id_str = str(bridge_cycle.get("cycle_id") or "cycle_unknown")
    flight_id = str(session_id or "paper-shadow")
    shadow_side = "long" if side == "BUY" else "short"
    return PreExternalProductiveEventV1(
        event_key=f"{flight_id}:{cycle_id_str}",
        flight_id=flight_id,
        cycle_id=int(bridge_cycle.get("cycle_index") or 0),
        instrument_id=str(instrument_id),
        side=shadow_side,
        quantity=str(qty),
        mark_price=str(mark_px),
        terminal_disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
        substituted=False,
    )
