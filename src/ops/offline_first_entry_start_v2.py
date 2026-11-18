"""Bounded offline start from the existing observation port to the original budget."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import re
import time

from src.ops.bounded_peaktrade_system_composition_v1.paper_market_liquidity_v1 import (
    PaperEntryLiquiditySourceV1,
)
from src.ops.first_entry_mark_clock_v2 import (
    ENTRY_MARK_STATE_DIRECTORY,
    LANE_ID,
    FirstEntryBudgetBindingV2,
    FirstEntryMarkCycleV2,
    run_first_entry_mark_cycle_v2,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    STATUS_PASS,
    CurrentProductiveEnterLive29PInjectedGetV1,
    CurrentProductiveEnterLive29PJoinResultV1,
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
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    immutable_json_v1,
)
from src.ops.full_core_live_path_composition_root_v1.pretrade_acquisition_v1 import (
    acquisition_age_seconds_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.instrument_monetary_identity_v1 import (
    instrument_monetary_identity_from_okx_row_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import ReservationStateV1
from src.ops.portfolio_capital_reservation_budget_v1.entry_execution_cost_v1 import (
    FundingCostObservationV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    HostBudgetRecoveryContextV1,
    PortfolioBudgetHostV1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    K1AccountObservationSourceV1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.rest_baseline_v1 import (
    parallel_account_recovery_gets_v1,
)
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


@dataclass(frozen=True)
class OfflineFirstEntryCapitalV2:
    result: CurrentProductiveEnterLive29PJoinResultV1 | None = None
    injected: CurrentProductiveEnterLive29PInjectedGetV1 | None = None
    reason: str = ""
    expired: bool = False


OfflineFirstEntryPretradeV2 = tuple[
    CurrentProductiveEnterLive29PInjectedGetV1, HostBudgetRecoveryContextV1
]


def observe_offline_first_entry_account_v2(
    budget_host: PortfolioBudgetHostV1, bound: BoundInstrumentV1
) -> HostBudgetRecoveryContextV1:
    if budget_host.closed or budget_host.execution_environment != _SIMULATED_ENVIRONMENT:
        raise ValueError("FIRST_ENTRY_START_SIMULATED_BUDGET_HOST_REQUIRED")
    source = budget_host.fetch
    if (
        type(source) is K1AccountObservationSourceV1
        and source.account_inventory_guard
        and source.inventory_inst_type == "FUTURES"
        and source.parallel_pending_reads
    ):
        with parallel_account_recovery_gets_v1():
            return budget_host.observe_v1({LANE_ID: bound})
    return budget_host.observe_v1({LANE_ID: bound})


def bind_offline_first_entry_budget_v2(
    budget_host: PortfolioBudgetHostV1,
) -> FirstEntryBudgetBindingV2:
    owner = budget_host.owner
    if budget_host.closed or budget_host.execution_environment != _SIMULATED_ENVIRONMENT:
        raise ValueError("FIRST_ENTRY_START_SIMULATED_BUDGET_HOST_REQUIRED")
    if owner is None or not owner.budget_state_v1().durable_state_enabled:
        raise ValueError("FIRST_ENTRY_START_DURABLE_BUDGET_REQUIRED")
    scope = owner.durable_scope_identity_v1()
    return FirstEntryBudgetBindingV2(
        scope["root"],
        scope["account"],
        budget_host.session_id,
        owner.stored_reservation_count_v1() > 0 or bool(owner.execution_links_v1()),
    )


def bind_first_entry_funding_clock_v2(
    entry: FirstEntryMarkCycleV2,
    bound: BoundInstrumentV1,
    injected: CurrentProductiveEnterLive29PInjectedGetV1,
) -> CurrentProductiveEnterLive29PInjectedGetV1:
    """Select the X-Perp funding event clock for this flat V2 entry only."""
    funding = injected.funding_cost_observation
    if (
        type(funding) is not FundingCostObservationV1
        or not bound.instrument_id.startswith("okx_eea:")
        or not re.fullmatch(r"[A-Z0-9]+-USD_UM_XPERP-\d{6}", bound.venue_native_id)
    ):
        return injected
    if (
        entry.status != "ENTRY_DECIDED"
        or entry.cycle is None
        or funding.cycle_id != entry.cycle.cycle_id
        or funding.decision_epoch != injected.acquisition_decision_id
    ):
        raise ValueError("FIRST_ENTRY_FUNDING_V2_DECISION_BINDING_REQUIRED")
    return replace(
        injected, funding_cost_observation=replace(funding, okx_xperp_event_clock_v2=True)
    )


def collect_offline_first_entry_pretrade_v2(
    *,
    budget_host: PortfolioBudgetHostV1,
    bound: BoundInstrumentV1,
    pretrade: Callable[[str, str], CurrentProductiveEnterLive29PInjectedGetV1],
    epoch: str,
    cycle_id: str,
) -> OfflineFirstEntryPretradeV2:
    """Run the original independent authenticated GET branches in parallel."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        recovery = pool.submit(observe_offline_first_entry_account_v2, budget_host, bound)
        return pretrade(epoch, cycle_id), recovery.result()


def size_offline_first_entry_v2(
    *,
    entry: FirstEntryMarkCycleV2,
    bound: BoundInstrumentV1,
    budget_host: PortfolioBudgetHostV1,
    pretrade: Callable[[str, str], CurrentProductiveEnterLive29PInjectedGetV1],
    prepared: Future[OfflineFirstEntryPretradeV2] | None = None,
    clock: Callable[[], float] = time.time,
) -> OfflineFirstEntryCapitalV2:
    """Collect both original GET branches against the exact Core decision time."""
    bind_offline_first_entry_budget_v2(budget_host)
    if entry.status != "ENTRY_DECIDED" or entry.cycle is None:
        raise ValueError("FIRST_ENTRY_CAPITAL_REQUIRES_NEW_ENTER")
    cycle = entry.cycle
    replay = cycle.replay
    epoch = replay.intermediate.market_context.decision_time
    try:
        acquisition_age_seconds_v1(
            acquired_at_utc=epoch, now_utc=datetime.fromtimestamp(clock(), timezone.utc).isoformat()
        )
        injected, recovery = (
            prepared.result()
            if prepared is not None
            else collect_offline_first_entry_pretrade_v2(
                budget_host=budget_host,
                bound=bound,
                pretrade=pretrade,
                epoch=epoch,
                cycle_id=cycle.cycle_id,
            )
        )
        acquisition_age_seconds_v1(
            acquired_at_utc=epoch, now_utc=datetime.fromtimestamp(clock(), timezone.utc).isoformat()
        )
    except ValueError as exc:
        reason = str(exc)
        if reason not in {"ACQUISITION_STALE", "HOST_BUDGET_PRIVATE_SNAPSHOT_STALE"}:
            raise
        return OfflineFirstEntryCapitalV2(reason=reason, expired=True)
    if recovery.pending_orders or any(p.signed_quantity for p in recovery.observed.positions):
        return OfflineFirstEntryCapitalV2(reason="ENTRY_ACCOUNT_NOT_FLAT")
    if (
        injected.acquisition_decision_id != epoch
        or injected.acquisition_cycle_id != cycle.cycle_id
        or injected.expected_account_identity != recovery.account
    ):
        return OfflineFirstEntryCapitalV2(reason="ENTRY_PRETRADE_BINDING_MISMATCH")
    result = join_current_productive_enter_live_29p_before_venue_plan_v1(
        replay=replay,
        bound_instrument=bound,
        injected=bind_first_entry_funding_clock_v2(entry, bound, injected),
        decision_epoch=epoch,
        portfolio_budget_owner=budget_host.owner,
        portfolio_slot=CurrentProductiveEnterLive29PPortfolioSlotContextV1(
            LANE_ID, replay.evidence.decision_id, cycle.cycle_id
        ),
        host_budget_recovery=recovery,
    )
    expired = (
        result.first_blocker == "HOST_BUDGET_RECOVERY_BLOCKED:DURABLE_FRESH_CAPITAL_REQUIRED"
        or result.first_blocker == "LIVE_29P_ACQUISITION_FAIL_CLOSED"
        and "ACQUISITION_STALE" in result.reason_codes
    )
    return OfflineFirstEntryCapitalV2(result, injected, result.first_blocker, expired)


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
    prepare_read_only_pretrade: bool = False,
    paper_liquidity: PaperEntryLiquiditySourceV1 | None = None,
) -> OfflineFirstEntryStartResultV2:
    """Consume current Mark observations and stop at the original pre-external plan.

    The caller supplies offline observations and a simulated budget host. The
    29P input port receives the exact decision epoch and cycle id. Callers may
    permit read-only preparation on a candidate Mark. Sizing still requires
    a committed ENTER. Expired entries without a reservation require a new Mark.
    A configured Paper source checks the selected instrument on each new ENTER
    and checks the final quantity before committing the pre-external plan.

    For an offline run continuing past a confirmed simulated fill, use
    OfflineFirstEntryBudgetHostV2 and bind_offline_first_entry_position_v2.
    That handoff retains the opening-fill evidence and publishes the occupied
    lane's finalized C1 clock through the original cursor owner.
    """
    if budget_host.closed or budget_host.execution_environment != _SIMULATED_ENVIRONMENT:
        raise ValueError("FIRST_ENTRY_START_SIMULATED_BUDGET_HOST_REQUIRED")
    if type(max_polls) is not int or max_polls <= 0:
        raise ValueError("FIRST_ENTRY_START_POSITIVE_POLL_LIMIT_REQUIRED")

    initial = observe_offline_first_entry_account_v2(budget_host, bound)
    if initial.pending_orders or any(p.signed_quantity for p in initial.observed.positions):
        return OfflineFirstEntryStartResultV2("BLOCKED", 0, reason="START_ACCOUNT_NOT_FLAT")
    owner = budget_host.owner
    budget_binding = bind_offline_first_entry_budget_v2(budget_host)

    liquidity_blocker = ""
    for poll in range(1, max_polls + 1):
        observation = source.poll()
        if observation is None or observation.mark_price_payload is None:
            continue
        observed_unix = clock()
        market = market_inputs(observed_unix)
        with ThreadPoolExecutor(max_workers=1) as staging:
            prepared = None

            def prepare(epoch: str, cycle_id: str) -> None:
                nonlocal prepared
                prepared = staging.submit(
                    collect_offline_first_entry_pretrade_v2,
                    budget_host=budget_host,
                    bound=bound,
                    pretrade=pretrade,
                    epoch=epoch,
                    cycle_id=cycle_id,
                )

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
                budget_binding=budget_binding,
                prepare_pretrade=prepare if prepare_read_only_pretrade else None,
            )
            if entry.status in {"EVALUATED", "WAITING_FOR_NEW_MARK", "WAITING_FOR_ENTRY_EXPIRY"}:
                continue
            if entry.status != "ENTRY_DECIDED":
                return OfflineFirstEntryStartResultV2(
                    entry.status, poll, reason=entry.cycle.input_blocker if entry.cycle else ""
                )

            cycle = entry.cycle
            replay = cycle.replay
            decision_id = replay.evidence.decision_id
            epoch = replay.intermediate.market_context.decision_time
            liquidity = None
            if paper_liquidity is not None:
                fill_side = {"enter_long": "BUY", "enter_short": "SELL"}[cycle.decision_outcome]
                evidence_name = sha256(cycle.cycle_id.encode()).hexdigest()
                evidence_root = Path(state_root) / "paper-entry-liquidity"
                try:
                    liquidity = paper_liquidity.observe_v1(
                        bound=bound, capture_id=cycle.cycle_id, clock=clock
                    )
                    if liquidity.bound != bound or budget_host.bindings.get(LANE_ID) != bound:
                        raise ValueError("PAPER_LIQUIDITY_ENTRY_BINDING_CHANGED")
                    preflight = liquidity.to_preflight_v1()
                    check = preflight["liquidity_at_minimum_quantity"][fill_side]
                    liquidity_blocker = "" if check["risk_admitted"] else check["reason_codes"][0]
                    if not liquidity.is_fresh_v1(clock()):
                        liquidity_blocker = "PAPER_LIQUIDITY_ENTRY_EXPIRED"
                except (
                    OSError,
                    ValueError,
                    TypeError,
                    KeyError,
                    RuntimeError,
                    ArithmeticError,
                ) as exc:
                    preflight = {}
                    liquidity_blocker = f"PAPER_LIQUIDITY_ENTRY_UNAVAILABLE:{exc}"
                immutable_json_v1(
                    evidence_root / f"{evidence_name}.json",
                    {
                        **preflight,
                        "lane_id": LANE_ID,
                        "cycle_id": cycle.cycle_id,
                        "decision_id": decision_id,
                        "bound": bound.to_dict(),
                        "side": fill_side,
                        "blocker": liquidity_blocker,
                    },
                )
                if liquidity_blocker:
                    continue
            sized = size_offline_first_entry_v2(
                entry=entry,
                bound=bound,
                budget_host=budget_host,
                pretrade=pretrade,
                clock=clock,
                prepared=prepared,
            )
        if sized.expired and not bind_offline_first_entry_budget_v2(budget_host).has_reservation:
            continue
        capital = sized.result
        injected = sized.injected
        if capital is None or injected is None:
            return OfflineFirstEntryStartResultV2("BLOCKED", poll, decision_id, reason=sized.reason)
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
            account_identity=budget_binding.account,
            decision_epoch=epoch,
            cycle_id=cycle.cycle_id,
            evaluated_at_utc=datetime.fromtimestamp(clock(), timezone.utc).isoformat(),
        )
        if not quantity.allowed:
            owner.release_sizing_or_admission_deny_v1(rid)
            return OfflineFirstEntryStartResultV2(
                "BLOCKED", poll, decision_id, rid, reason=quantity.reason_codes[0]
            )

        if liquidity is not None:
            try:
                (contract,) = (
                    row
                    for row in injected.instruments_payload["data"]
                    if row["instId"] == bound.venue_native_id
                )
                snapshot = liquidity.snapshot
                monetary = instrument_monetary_identity_from_okx_row_v1(contract)
                if (
                    monetary.ct_val,
                    monetary.quote_currency,
                    Decimal(contract["lotSz"]),
                    Decimal(contract["minSz"]),
                    Decimal(contract["tickSz"]),
                ) != (
                    snapshot.contract_size,
                    liquidity.quote_asset,
                    snapshot.lot_size,
                    snapshot.minimum_contracts,
                    snapshot.tick_size,
                ):
                    raise ValueError("PAPER_LIQUIDITY_CONTRACT_METADATA_CHANGED")
                if plan.instrument_id != bound.venue_native_id or plan.side != fill_side.lower():
                    raise ValueError("PAPER_LIQUIDITY_PLAN_SCOPE_CHANGED")
                exact = snapshot.assess_quantity_v1(side=fill_side, quantity=Decimal(plan.quantity))
                if budget_host.bindings.get(LANE_ID) != bound:
                    reason = "PAPER_LIQUIDITY_ENTRY_BINDING_CHANGED"
                elif not liquidity.is_fresh_v1(clock()):
                    reason = "PAPER_LIQUIDITY_ENTRY_EXPIRED"
                else:
                    reason = "" if exact["risk_admitted"] else exact["reason_codes"][0]
                immutable_json_v1(
                    evidence_root / f"{evidence_name}.exact.json",
                    {**exact, "decision_id": decision_id, "blocker": reason},
                )
            except (OSError, ValueError, TypeError, KeyError, RuntimeError, ArithmeticError) as exc:
                reason = f"PAPER_LIQUIDITY_EXACT_CHECK_UNAVAILABLE:{exc}"
            if reason:
                owner.release_sizing_or_admission_deny_v1(rid)
                return OfflineFirstEntryStartResultV2(
                    "BLOCKED", poll, decision_id, rid, reason=reason
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

    return OfflineFirstEntryStartResultV2("WAITING_FOR_ENTRY", max_polls, reason=liquidity_blocker)
