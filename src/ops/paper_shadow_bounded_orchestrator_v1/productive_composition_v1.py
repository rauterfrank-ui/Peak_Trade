"""Invoke existing productive PRE_EXTERNAL path (no duplicated decision logic)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_e2e_productive_pre_external_tail_bind_v1 import (
    GhvE2EProductivePreExternalTailContextV1,
    build_ghv_e2e_productive_pre_external_tail_context_v1,
    classify_ghv_e2e_productive_pre_external_tail_metrics_v1,
    invoke_ghv_e2e_productive_pre_external_closure_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.shadow_routing_v1 import (
    PreExternalProductiveEventV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


@dataclass(frozen=True)
class ProductiveCompositionResultV1:
    ok: bool
    pre_external: bool
    event: PreExternalProductiveEventV1 | None
    metrics: dict[str, Any]
    fail_reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "pre_external": self.pre_external,
            "event": None if self.event is None else self.event.to_dict(),
            "metrics": self.metrics,
            "fail_reason": self.fail_reason,
            "PRODUCTIVE_DECISION_LOGIC_DUPLICATION_COUNT": 0,
        }


def build_productive_tail_context_v1(
    *,
    origin_main_sha: str,
    store_root: Path,
) -> GhvE2EProductivePreExternalTailContextV1:
    return build_ghv_e2e_productive_pre_external_tail_context_v1(
        origin_main_sha=origin_main_sha,
        store_root=Path(store_root),
    )


def invoke_productive_pre_external_closure_for_orchestrator_v1(
    *,
    ctx: GhvE2EProductivePreExternalTailContextV1,
    origin_main_sha: str,
    bound_instrument: BoundInstrumentV1,
    g17_typed_vol_producer: object,
    cycle_id: str,
    flight_id: str,
    cycle_index: int,
    side: str,
    mark_px: float,
    index_px: float,
    bid_px: float,
    ask_px: float,
    volume: float,
    open_interest: float,
    funding_rate: float,
    finalized_closes: tuple[float, ...],
    last_finalized_event_ts_unix: float,
    observed_unix: float,
    ghv_pre_decision_incoming_cursor: object | None,
    ghv_post_enter_outgoing_cursor: object | None = None,
    instrument_id: str,
    quantity: str = "1",
) -> ProductiveCompositionResultV1:
    """Composition-only: delegates to canonical productive closure (GHV E2E bind)."""
    closure = invoke_ghv_e2e_productive_pre_external_closure_v1(
        ctx=ctx,
        origin_main_sha=origin_main_sha,
        bound_instrument=bound_instrument,
        g17_typed_vol_producer=g17_typed_vol_producer,
        cycle_id=cycle_id,
        mark_px=mark_px,
        index_px=index_px,
        bid_px=bid_px,
        ask_px=ask_px,
        volume=volume,
        open_interest=open_interest,
        funding_rate=funding_rate,
        finalized_closes=finalized_closes,
        last_finalized_event_ts_unix=last_finalized_event_ts_unix,
        observed_unix=observed_unix,
        ghv_pre_decision_incoming_cursor=ghv_pre_decision_incoming_cursor,
        ghv_post_enter_outgoing_cursor=ghv_post_enter_outgoing_cursor,
    )
    metrics = dict(classify_ghv_e2e_productive_pre_external_tail_metrics_v1(closure))
    pre_ext = metrics.get("pre_external") is True
    event = None
    if pre_ext:
        event = PreExternalProductiveEventV1(
            event_key=f"{flight_id}:{cycle_index}",
            flight_id=flight_id,
            cycle_id=cycle_index,
            instrument_id=instrument_id,
            side=side,
            quantity=quantity,
            mark_price=str(mark_px),
            terminal_disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
            substituted=False,
        )
    return ProductiveCompositionResultV1(
        ok=pre_ext,
        pre_external=pre_ext,
        event=event,
        metrics=metrics,
        fail_reason="" if pre_ext else "PRE_EXTERNAL_NOT_REACHED",
    )
