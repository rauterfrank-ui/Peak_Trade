"""Bounded offline start from the existing observation port to the original budget."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import time

from src.ops.first_entry_mark_clock_v2 import (
    ENTRY_MARK_STATE_DIRECTORY,
    LANE_ID,
    run_first_entry_mark_cycle_v2,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    STATUS_PASS,
    CurrentProductiveEnterLive29PInjectedGetV1,
    CurrentProductiveEnterLive29PPortfolioSlotContextV1,
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    ContinuousObservationSourceV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_reconciliation_admission_v1 import (
    ProductiveMasterV2ReconciliationAdmissionV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_n1_venue_quantity_limit_admission_v1 import (
    assess_n1_final_plan_venue_quantity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    CompositionStatusV1,
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import ReservationStateV1
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
)

_SIMULATED_ENVIRONMENT = "INTERNAL_SIMULATED_EXECUTION"


@dataclass(frozen=True)
class OfflineFirstEntryMarketInputsV2:
    bid_px: float
    ask_px: float
    volume: float
    open_interest: float
    funding_rate: float
    g17_producer: CanonicalVolatilityTypedRuntimeProducerScaffoldV1


@dataclass(frozen=True)
class OfflineFirstEntryStartResultV2:
    disposition: str
    polls: int
    decision_id: str = ""
    reservation_id: str = ""
    envelope: FinalOrderEnvelopeV1 | None = None
    reason: str = ""


def run_offline_first_entry_start_v2(
    *,
    state_root: Path,
    bound: BoundInstrumentV1,
    budget_host: PortfolioBudgetHostV1,
    source: ContinuousObservationSourceV1,
    market_inputs: Callable[[float], OfflineFirstEntryMarketInputsV2],
    pretrade: Callable[[str, str], CurrentProductiveEnterLive29PInjectedGetV1],
    reconciliation: ProductiveMasterV2ReconciliationAdmissionV1,
    max_polls: int,
    clock: Callable[[], float] = time.time,
) -> OfflineFirstEntryStartResultV2:
    """Consume current Mark observations and stop at the original pre-external plan.

    The caller supplies offline observations and a simulated budget host. The
    29P input port is invoked only for a natural ENTER and receives its exact
    decision epoch and cycle id. A durable ENTER is terminal for this start.
    """
    if budget_host.closed or budget_host.execution_environment != _SIMULATED_ENVIRONMENT:
        raise ValueError("FIRST_ENTRY_START_SIMULATED_BUDGET_HOST_REQUIRED")
    if type(max_polls) is not int or max_polls <= 0:
        raise ValueError("FIRST_ENTRY_START_POSITIVE_POLL_LIMIT_REQUIRED")

    bindings = {LANE_ID: bound}
    initial = budget_host.observe_v1(bindings)
    if initial.pending_orders or any(p.signed_quantity for p in initial.observed.positions):
        return OfflineFirstEntryStartResultV2("BLOCKED", 0, reason="START_ACCOUNT_NOT_FLAT")
    owner = budget_host.owner
    if owner is None or not owner.budget_state_v1().durable_state_enabled:
        raise ValueError("FIRST_ENTRY_START_DURABLE_BUDGET_REQUIRED")

    for poll in range(1, max_polls + 1):
        observation = source.poll()
        if observation is None or observation.mark_price_payload is None:
            continue
        observed_unix = clock()
        market = market_inputs(observed_unix)
        entry = run_first_entry_mark_cycle_v2(
            offline_state_root=state_root,
            bound=bound,
            cycle_id=f"{budget_host.session_id}:first-entry:{observed_unix}",
            observed_unix=observed_unix,
            candles_payload=observation.candles_payload,
            mark_price_payload=observation.mark_price_payload,
            index_tickers_payload=observation.index_tickers_payload,
            mark_acquired_at_utc=observation.mark_acquired_at_utc,
            bid_px=market.bid_px,
            ask_px=market.ask_px,
            volume=market.volume,
            open_interest=market.open_interest,
            funding_rate=market.funding_rate,
            venue_flat=True,
            g17_producer=market.g17_producer,
            reconciliation=reconciliation,
        )
        if entry.status in {"EVALUATED", "WAITING_FOR_NEW_MARK"}:
            continue
        if entry.status != "ENTRY_DECIDED":
            return OfflineFirstEntryStartResultV2(
                entry.status, poll, reason=entry.cycle.input_blocker if entry.cycle else ""
            )

        cycle = entry.cycle
        replay = cycle.replay
        decision_id = replay.evidence.decision_id
        epoch = replay.intermediate.market_context.decision_time
        recovery = budget_host.observe_v1(bindings)
        if recovery.pending_orders or any(p.signed_quantity for p in recovery.observed.positions):
            return OfflineFirstEntryStartResultV2(
                "BLOCKED", poll, decision_id, reason="ENTRY_ACCOUNT_NOT_FLAT"
            )
        injected = pretrade(epoch, cycle.cycle_id)
        if (
            injected.acquisition_decision_id != epoch
            or injected.acquisition_cycle_id != cycle.cycle_id
            or injected.expected_account_identity != recovery.account
        ):
            return OfflineFirstEntryStartResultV2(
                "BLOCKED", poll, decision_id, reason="ENTRY_PRETRADE_BINDING_MISMATCH"
            )
        capital = join_current_productive_enter_live_29p_before_venue_plan_v1(
            replay=replay,
            bound_instrument=bound,
            injected=injected,
            decision_epoch=epoch,
            portfolio_budget_owner=owner,
            portfolio_slot=CurrentProductiveEnterLive29PPortfolioSlotContextV1(
                LANE_ID, decision_id, cycle.cycle_id
            ),
            host_budget_recovery=recovery,
        )
        rid = capital.portfolio_reservation_id
        if capital.status != STATUS_PASS or not rid:
            return OfflineFirstEntryStartResultV2(
                "BLOCKED", poll, decision_id, reason=capital.first_blocker
            )

        status, reasons, plan = try_bind_current_productive_venue_plan_v1(
            replay=capital.replay,
            bound_instrument=bound,
            session_id=budget_host.session_id,
            run_id=cycle.cycle_id,
            composed_epoch=epoch,
            execution_mode=_SIMULATED_ENVIRONMENT,
        )
        if status is not CompositionStatusV1.PASS or plan is None:
            owner.release_plan_failure_v1(rid)
            return OfflineFirstEntryStartResultV2(
                "BLOCKED", poll, decision_id, rid, reason=reasons[0]
            )
        quantity = assess_n1_final_plan_venue_quantity_v1(
            observation=injected.venue_quantity_limits,
            plan=plan,
            bound_instrument=bound,
            account_identity=recovery.account,
            decision_epoch=epoch,
            cycle_id=cycle.cycle_id,
            evaluated_at_utc=datetime.fromtimestamp(clock(), timezone.utc).isoformat(),
        )
        if not quantity.allowed:
            owner.release_sizing_or_admission_deny_v1(rid)
            return OfflineFirstEntryStartResultV2(
                "BLOCKED", poll, decision_id, rid, reason=quantity.reason_codes[0]
            )

        envelope = bind_final_order_envelope_from_venue_plan_v1(
            plan,
            admission_ref=f"{cycle.cycle_id}:admission:portfolio-reservation:{rid}",
            provenance_ref=f"{cycle.cycle_id}:provenance",
            creation_epoch=epoch,
        )
        committed = owner.commit_internal_pre_external_effect_v1(rid)
        if (
            committed.reservation is None
            or committed.reservation.state is not ReservationStateV1.COMMITTED
        ):
            raise ValueError("FIRST_ENTRY_START_RESERVATION_COMMIT_UNPROVEN")
        owner.bind_execution_plan_v1(
            rid,
            envelope,
            canonical_intent=capital.replay.intermediate.canonical_order_intent,
            venue_plan=plan,
            core_parent=capital.replay.evidence,
            core_cursor_root=Path(state_root).resolve() / ENTRY_MARK_STATE_DIRECTORY / LANE_ID,
            entry_frame_required=True,
        )
        return OfflineFirstEntryStartResultV2(
            "PRE_EXTERNAL_EFFECT", poll, decision_id, rid, envelope
        )

    return OfflineFirstEntryStartResultV2("WAITING_FOR_ENTRY", max_polls)
