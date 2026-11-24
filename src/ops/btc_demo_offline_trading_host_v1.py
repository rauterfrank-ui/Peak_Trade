"""Explicit offline BTC decision/entry/occupied joins; no transport or send port.

The original Core, cursor, G17, budget and Exit owners retain their roles.
Public USD valuation is never a USDC sizing operand or account-settlement proof.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.nonlive_mark_timing_v1 import observe_demo_call_v1
from src.ops.btc_demo_budget_reconciliation_host_v1 import (
    BtcDemoBudgetReconciliationHostV1,
    validate_btc_demo_coverage_v1,
)
from src.ops.first_entry_mark_clock_v2 import run_first_entry_mark_cycle_v2, FirstEntryMarkCycleV2
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    load_current_productive_sidestate_confirmation_cursor_v1,
    parse_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_core_entry_assessment_frame_v1 import (
    read_current_core_entry_assessment_frame_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_reconciliation_admission_v1 import (
    ProductiveMasterV2ReconciliationAdmissionContextV1,
)
from src.ops.governed_productive_monetary_normalization_v1.instrument_monetary_identity_v1 import (
    instrument_monetary_identity_from_okx_payload_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.constants_v1 import (
    CANONICAL_INTERNAL_RISK_NUMERAIRE,
    PHYSICAL_USDC_REQUIRED_FOR_NUMERAIRE,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    CurrentProductiveEnterLive29PInjectedGetV1,
    CurrentProductiveEnterLive29PPortfolioSlotContextV1,
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1 import pretrade_acquisition_v1
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    HostBudgetRecoveryContextV1,
    PortfolioBudgetHostV1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    exclusive_v1,
)

from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
    restore_episode_from_store_v1,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    serialize_canonical_trading_decision_evidence_canonical,
)
from trading.master_v2.canonical_market_context_v1 import (
    serialize_canonical_market_context_canonical,
)


def _need(value, reason):
    if not value:
        raise ValueError(reason)


@dataclass(frozen=True)
class BtcDemoMarketObservationV1:
    native_price_currency: str
    cycle_id: str
    observed_unix: float
    candles_payload: dict
    mark_price_payload: dict
    mark_acquired_at_utc: str
    bid_px: float
    ask_px: float
    volume: float
    open_interest: float
    funding_rate: float
    venue_flat: bool
    index_tickers_payload: dict | None = None


class BtcDemoOfflineTradingHostV1:
    """Single-step offline composition, not operational scheduling/dispatch.

    Every call requires explicit original inputs. There is no default clock,
    market feed, signer, order/cancel port, retry or replacement budget ledger.
    """

    def __init__(
        self, *, budget_host, g17_producer, repository_sha, config_digest, writer_session_id
    ):
        from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
            FROZEN_PROFIT_PROTECTION_DISTANCE,
        )
        from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
            layer_c_derived_exit_policy_adverse_config_digest_v1,
        )

        _need(
            type(budget_host) is BtcDemoBudgetReconciliationHostV1,
            "BTC_OFFLINE_ORIGINAL_BUDGET_HOST_REQUIRED",
        )
        _need(
            config_digest
            == layer_c_derived_exit_policy_adverse_config_digest_v1(
                profit_protection_distance=FROZEN_PROFIT_PROTECTION_DISTANCE
            ),
            "BTC_OFFLINE_ORIGINAL_EXIT_CONFIG_REQUIRED",
        )
        self.budget = budget_host
        self.g17 = g17_producer
        self.repository_sha = repository_sha
        self.config_digest = config_digest
        self.writer_session_id = writer_session_id
        self.cursor_root = demo._demo_lane_root(budget_host.root) / "cursor" / demo._LANE

    def _observation(self, value):
        _need(
            type(value) is BtcDemoMarketObservationV1 and value.native_price_currency == "USD",
            "BTC_OFFLINE_NATIVE_USD_OBSERVATION_REQUIRED",
        )
        return value

    @observe_demo_call_v1
    def prepare_entry_v1(self, *, observation, reconciliation):
        obs = self._observation(observation)
        _need(
            self.budget.owner.active_sum_v1() == 0,
            "BTC_OFFLINE_EXISTING_OBLIGATION_BLOCKS_NEW_ENTRY",
        )
        return run_first_entry_mark_cycle_v2(
            offline_state_root=self.budget.root,
            bound=self.budget.bound,
            cycle_id=obs.cycle_id,
            observed_unix=obs.observed_unix,
            candles_payload=obs.candles_payload,
            mark_price_payload=obs.mark_price_payload,
            index_tickers_payload=obs.index_tickers_payload,
            mark_acquired_at_utc=obs.mark_acquired_at_utc,
            bid_px=obs.bid_px,
            ask_px=obs.ask_px,
            volume=obs.volume,
            open_interest=obs.open_interest,
            funding_rate=obs.funding_rate,
            venue_flat=obs.venue_flat,
            g17_producer=self.g17,
            reconciliation=reconciliation,
            lane_id=demo._LANE,
            cursor_store_root=self.cursor_root,
        )

    def assess_monetary_entry_v1(self, *, entry, coverage, now):
        """Return original monetary blockers, never relabel native USD as USDC."""
        _need(
            type(entry) is FirstEntryMarkCycleV2 and entry.status == "ENTRY_DECIDED",
            "BTC_OFFLINE_ORIGINAL_ENTRY_REQUIRED",
        )
        raw = load_current_productive_sidestate_confirmation_cursor_v1(self.cursor_root)
        _need(entry.cycle.outgoing_cursor.to_dict() == raw, "BTC_OFFLINE_ENTRY_CURSOR_CHANGED")
        cursor = parse_current_productive_sidestate_confirmation_cursor_v1(raw)
        frame = read_current_core_entry_assessment_frame_v1(cursor)
        report = validate_btc_demo_coverage_v1(coverage, account=self.budget.account, now=now)
        instrument = next(
            row["payload"]
            for row in report["source_observations"]
            if row["path"] == demo._INSTRUMENTS
        )
        reasons = []
        identity = None
        try:
            identity = instrument_monetary_identity_from_okx_payload_v1(
                instrument, venue_native_id=demo._NATIVE
            )
            if identity.instrument_money_unit != "USD":
                reasons.append("BTC_NATIVE_USD_PRICE_IS_NOT_PRIVATE_SETTLEMENT_AMOUNT")
            else:
                reasons.append("BTC_ORIGINAL_NATIVE_USD_MONETARY_SOURCE_REQUIRED")
        except (ValueError, ArithmeticError, TypeError, KeyError) as exc:
            reasons.append(str(exc))
        reasons.append("BTC_USD_USDC_ACCOUNT_SETTLEMENT_OPERATOR_UNPROVEN")
        return dict(
            status="BLOCKED",
            authority="NONE",
            decision_id=frame["parent"]["decision_id"],
            native_price_currency="USD",
            capital_currency="USDC",
            canonical_risk_numeraire=CANONICAL_INTERNAL_RISK_NUMERAIRE,
            physical_usdc_required_for_numeraire=PHYSICAL_USDC_REQUIRED_FOR_NUMERAIRE,
            instrument_monetary_identity=None
            if identity is None
            else {
                "quote_currency": identity.quote_currency,
                "settle_currency": identity.settle_currency,
                "instrument_money_unit": identity.instrument_money_unit,
                "metadata_digest": identity.metadata_digest,
            },
            public_index_valuation={
                "role": "PUBLIC_INDEX_VALUATION_ONLY",
                "declared_budget_usdc": report["budget_usdc"],
                "declared_budget_value_usd": report["budget_value_usd"],
            },
            account_settlement_proven=report["usd_usdc_account_settlement_proven"],
            usd_usdc_conversion_operator_proven=False,
            canonical_sizing_operands=None,
            coverage_digest=report["coverage_digest"],
            reason_codes=tuple(reasons),
        )

    def _original_rehearsal_cycle(self, entry):
        _need(
            type(entry) is FirstEntryMarkCycleV2
            and entry.status == "ENTRY_DECIDED"
            and entry.cycle is not None
            and entry.cycle.replay_pass == "true",
            "BTC_OFFLINE_ORIGINAL_ENTRY_REQUIRED",
        )
        cycle = entry.cycle
        cursor = cycle.outgoing_cursor
        _need(
            cursor is not None
            and cursor.to_dict()
            == load_current_productive_sidestate_confirmation_cursor_v1(self.cursor_root),
            "BTC_OFFLINE_ENTRY_CURSOR_CHANGED",
        )
        frame = read_current_core_entry_assessment_frame_v1(cursor)
        replay = cycle.replay
        market = replay.intermediate.market_context
        stored = cursor.entry_assessment_frame
        episode = restore_episode_from_store_v1(
            self.cursor_root, expected_instrument_id=self.budget.bound.instrument_id
        )
        _need(
            episode.scope is not None
            and episode.scope.valid
            and resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1(
                episode.scope.d_t
            ).up_distance
            == replay.intermediate.scope_event.semantic_binding.up_distance,
            "BTC_REHEARSAL_DECISION_SCOPE_MISMATCH",
        )
        _need(
            frame["parent"]["decision_id"] == replay.evidence.decision_id
            and stored["components"]["parent"]["canonical"]
            == serialize_canonical_trading_decision_evidence_canonical(replay.evidence)
            and frame["parent"]["replay_id"] == cycle.replay_id == cycle.cycle_id + "-master-v2"
            and stored["market_context"]["canonical"]
            == serialize_canonical_market_context_canonical(market)
            and cursor.instrument_id
            == replay.evidence.instrument_id
            == self.budget.bound.instrument_id
            and cursor.venue_native_id == demo._NATIVE
            and frame["entry"]["decision_outcome"] == cycle.decision_outcome
            and cycle.decision_outcome in {"enter_long", "enter_short"},
            "BTC_REHEARSAL_DECISION_MISMATCH",
        )
        return cycle

    def rehearse_entry_reservation_v1(self, *, entry, injected, recovery):
        """Apply the private linear settlement contract in a separate simulation journal.

        Inputs are already captured. This seam returns only the original budget
        readback and has no venue plan, execution adapter or Demo ledger writer.
        """
        _need(
            type(injected) is CurrentProductiveEnterLive29PInjectedGetV1
            and type(recovery) is HostBudgetRecoveryContextV1,
            "BTC_REHEARSAL_ORIGINAL_RECOVERY_REQUIRED",
        )
        host = recovery.host
        bound = self.budget.bound
        demo_root = self.budget.root.resolve()
        _need(
            type(host) is PortfolioBudgetHostV1
            and host.execution_environment == "INTERNAL_SIMULATED_EXECUTION"
            and not host.closed
            and host.owner is not None
            and recovery.observed.source_id == "host-private-rest-futures"
            and recovery.account_inventory_source is not None
            and recovery.account_inventory_source is host.fetch
            and host.owner.durable_scope_identity_v1()
            == {"root": str(host.root / "owner"), "account": host.account}
            and (host.root / "owner").resolve() == host.root / "owner"
            and not host.root.is_relative_to(demo_root)
            and not demo_root.is_relative_to(host.root)
            and host.bindings == {demo._LANE: bound}
            and host.account
            == recovery.account
            == injected.expected_account_identity
            == self.budget.account,
            "BTC_REHEARSAL_ISOLATED_SLOT_ACCOUNT_REQUIRED",
        )
        policy = host.owner.entry_budget_policy_v1()
        _need(
            policy is not None
            and policy.require_usdc_settlement
            and policy.aggregate_reserved_notional_limit <= demo._BUDGET_USDC
            and policy.per_entry_notional_limit <= demo._BUDGET_USDC
            and policy.per_slot_reserved_notional_limit <= demo._BUDGET_USDC,
            "BTC_REHEARSAL_USDC_COST_POLICY_REQUIRED",
        )
        with exclusive_v1(self.cursor_root / "first_entry_mark_v2.lock"):
            cycle = self._original_rehearsal_cycle(entry)
            replay = cycle.replay
            epoch = replay.intermediate.market_context.decision_time
            _need(
                injected.acquisition_decision_id == epoch
                and injected.acquisition_cycle_id == cycle.cycle_id
                and injected.pretrade_acquired_at_utc
                and injected.entry_public_mark_source is None
                and injected.futures_financial_custody is None
                and injected.index_tickers_payload is None
                and injected.conversion_pair_instruments_payload is None,
                "BTC_REHEARSAL_PRIVATE_LINEAR_DECISION_INPUTS_REQUIRED",
            )
            now = pretrade_acquisition_v1.utc_now_iso_v1()
            pretrade_acquisition_v1.acquisition_age_seconds_v1(acquired_at_utc=epoch, now_utc=now)
            snapshot = recovery.observed
            _need(
                snapshot.event_time_unix is not None
                and snapshot.wall_time_unix is not None
                and snapshot.event_time_unix <= snapshot.wall_time_unix,
                "BTC_REHEARSAL_INVENTORY_CLOCK_REQUIRED",
            )
            for stamp in (snapshot.event_time_unix, snapshot.wall_time_unix):
                pretrade_acquisition_v1.acquisition_age_seconds_v1(
                    acquired_at_utc=datetime.fromtimestamp(stamp, timezone.utc).isoformat(),
                    now_utc=now,
                )
            _need(
                not recovery.pending_orders
                and not any(p.signed_quantity for p in recovery.observed.positions)
                and not host.owner.stored_reservation_count_v1()
                and self.budget.owner.active_sum_v1() == 0,
                "BTC_REHEARSAL_FRESH_FLAT_ENTRY_REQUIRED",
            )
            result = join_current_productive_enter_live_29p_before_venue_plan_v1(
                replay=replay,
                bound_instrument=bound,
                decision_epoch=epoch,
                injected=injected,
                portfolio_budget_owner=host.owner,
                portfolio_slot=CurrentProductiveEnterLive29PPortfolioSlotContextV1(
                    demo._LANE, replay.evidence.decision_id, cycle.cycle_id
                ),
                host_budget_recovery=recovery,
            )
            _need(
                result.status == "PASS", result.first_blocker or "BTC_REHEARSAL_RESERVATION_DENIED"
            )
            journal = host.owner.local_commitment_readback_v1()
            (hold,) = journal.commitments
            _need(
                hold.reservation_id == result.portfolio_reservation_id
                and (hold.slot_id, hold.decision_id, hold.cycle_id)
                == (demo._LANE, replay.evidence.decision_id, cycle.cycle_id)
                and hold.state == "RESERVED"
                and hold.execution_phase == "NO_EXECUTION_LINK",
                "BTC_REHEARSAL_JOURNAL_IDENTITY_MISMATCH",
            )
            return hold

    def reconcile_confirmed_entry_v1(self, *, reads, reservation_id, clock):
        observed = self.budget.reconcile_attempt_v1(
            reads=reads, reservation_id=reservation_id, clock=clock
        )
        episode, publication = self.budget.bind_confirmed_entry_v1(
            reconciliation=observed,
            repository_sha=self.repository_sha,
            config_digest=self.config_digest,
            writer_session_id=self.writer_session_id,
            g17_producer=self.g17,
            cursor_store_root=self.cursor_root,
        )
        return episode, publication, observed

    @observe_demo_call_v1
    def continue_occupied_v1(
        self, *, episode, observation, reconciliation, execution_reconciliation=None
    ):
        """Consume the confirmed original episode; return Core output without send."""
        from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
            IsolatedLaneSlotV1,
        )
        from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
            compose_occupied_lane_mv2_dp_durable_cycle_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
            build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
            extract_finalized_candle_closes_v1,
        )
        from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
        from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
            PositionEpisodeBindingV1,
        )

        obs = self._observation(observation)
        bound = self.budget.bound
        _need(
            reconciliation.context_class
            is not ProductiveMasterV2ReconciliationAdmissionContextV1.PRODUCTIVE_UPSTREAM_GATE,
            "BTC_OFFLINE_NON_PRODUCTIVE_RECONCILIATION_REQUIRED",
        )
        _need(
            type(episode) is PositionEpisodeBindingV1,
            "BTC_OFFLINE_ORIGINAL_POSITION_EPISODE_REQUIRED",
        )
        identity = episode.identity
        _need(
            (
                identity.lane_id,
                identity.instrument_id,
                identity.venue_native_id,
                identity.account_scope.account_identity,
                identity.account_scope.execution_environment,
            )
            == (demo._LANE, bound.instrument_id, demo._NATIVE, self.budget.account, "TESTNET")
            and obs.venue_flat is False,
            "BTC_OFFLINE_ORIGINAL_OCCUPIED_SCOPE_REQUIRED",
        )
        retained = demo.read_btc_demo_first_fill_for_research_v1(
            self.budget.root, identity.episode_id
        )
        _need(
            retained["episode_id"] == identity.episode_id
            and episode.entry_source_ref
            == "okx_eea_demo_first_fill.v2:" + demo.canonical_digest_v1(retained["opening_fill"])
            and Path(episode.binding.state_root)
            == demo._demo_lane_root(self.budget.root) / "position-episodes" / identity.episode_id,
            "BTC_OFFLINE_ORIGINAL_POSITION_SOURCE_REQUIRED",
        )
        slot = IsolatedLaneSlotV1(
            demo._LANE,
            "OCCUPIED",
            bound.instrument_id,
            str(self.cursor_root),
            bound.universe_snapshot_id,
            bound.ranking_snapshot_id,
            bound.ranking_integrity_digest,
        )
        provenance = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
            mark_price_payload=obs.mark_price_payload,
            venue_native_id=demo._NATIVE,
            index_from_index_tickers=obs.index_tickers_payload,
            mark_acquired_at_utc=obs.mark_acquired_at_utc,
        )
        mark_event = provenance.require_current_mark_clock_v1(observed_unix=obs.observed_unix)
        closes, candle_open = extract_finalized_candle_closes_v1(obs.candles_payload)
        _need(
            candle_open is not None and candle_open + 60 <= mark_event,
            "BTC_OFFLINE_FINALIZED_C1_AFTER_MARK",
        )
        with self.budget.occupied_decision_guard_v1(
            reconciliation=execution_reconciliation,
            episode=episode,
            now=obs.observed_unix,
        ):
            return compose_occupied_lane_mv2_dp_durable_cycle_v1(
                {demo._LANE: (slot, bound)},
                cycle_id_prefix=obs.cycle_id,
                observed_unix=obs.observed_unix,
                mark_px=provenance.mark_px,
                index_px=provenance.index_px,
                bid_px=obs.bid_px,
                ask_px=obs.ask_px,
                volume=obs.volume,
                open_interest=obs.open_interest,
                funding_rate=obs.funding_rate,
                finalized_closes=closes,
                last_finalized_event_ts_unix=candle_open,
                venue_flat=False,
                existing_position_side=ExistingPositionSide(identity.position_side),
                g17_typed_vol_producers={demo._LANE: self.g17},
                canonical_price_provenance=provenance,
                master_v2_reconciliation_admission=reconciliation,
                position_episode_bindings={demo._LANE: episode},
                position_episode_scope=identity.account_scope,
                occupied_scope_mark=True,
                incoming_cursor_override=load_current_productive_sidestate_confirmation_cursor_v1(
                    self.cursor_root
                ),
            )[demo._LANE].cycle_result

    def iter_occupied_marks_v1(
        self, *, episode, observations, reconciliation, execution_reconciliation
    ):
        """Feed admitted market observations to the confirmed Demo episode until its first action.

        The caller supplies original Demo reconciliation receipts. The existing
        financial owner validates custody, freshness and the durable head on
        every decision. No transport or booking is constructed here.
        """
        from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
            InjectedContinuousObservationV1,
            _new_occupied_mark_time_v1,
        )

        for obs in observations:
            self._observation(obs)
            event = _new_occupied_mark_time_v1(
                observation=InjectedContinuousObservationV1(
                    candles_payload=obs.candles_payload,
                    occupancy_payloads={},
                    mark_price_payload=obs.mark_price_payload,
                    index_tickers_payload=obs.index_tickers_payload,
                    mark_acquired_at_utc=obs.mark_acquired_at_utc,
                ),
                native_id=self.budget.bound.venue_native_id,
                cursor_store_root=self.cursor_root,
                observed_unix=obs.observed_unix,
            )
            if event is None:
                continue
            result = self.continue_occupied_v1(
                episode=episode,
                observation=obs,
                reconciliation=reconciliation,
                execution_reconciliation=execution_reconciliation(),
            )
            yield result
            if result.replay_pass != "true" or result.decision_outcome != "hold":
                return
