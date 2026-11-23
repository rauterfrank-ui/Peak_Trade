"""Explicit offline BTC decision/entry/occupied joins; no transport or send port.

The original Core, cursor, G17, budget and Exit owners retain their roles.
Public USD valuation is never a USDC sizing operand or account-settlement proof.
"""

from dataclasses import dataclass
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
