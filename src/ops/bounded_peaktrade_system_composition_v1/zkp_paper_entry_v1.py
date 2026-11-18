"""Isolated XPERP Paper opening from original Master V2 to one simulated Paper fill."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from time import time

from src.governance.canonical_order_intent_v1 import (
    CanonicalOrderIntentBuildInputV1,
    build_canonical_order_intent_v1,
    canonical_order_intent_to_semantic_dict,
)
from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingInputV1,
    InstrumentQuantityConstraintsV1,
    evaluate_capital_risk_sizing_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1.manifest_v1 import repository_source_digest_v1
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
    PAPER_ALLOCATION_USDC,
    PAPER_FEE_RATE,
    ZKP_PAPER_SLOT,
)
from src.ops.exit_policy_producer_binding_v1.constants_v1 import FROZEN_PROFIT_PROTECTION_DISTANCE
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    bind_simulated_accounting_episode_identity_v1,
    create_position_episode_from_simulated_accounting_v1,
)
from src.ops.first_entry_mark_clock_v2 import (
    ENTRY_MARK_STATE_DIRECTORY,
    FirstEntryBudgetBindingV2,
    run_first_entry_mark_cycle_v2,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    resolve_current_productive_live_29p_adverse_exit_distance_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
    prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_reconciliation_admission_v1 import (
    build_explicit_non_productive_bounded_harness_master_v2_reconciliation_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    exclusive_v1,
    immutable_json_v1,
)
from src.ops.offline_first_entry_position_v2 import publish_confirmed_first_entry_c1_v2
from src.ops.instrument_card_budget_assessment_v1 import assess_instrument_budget_v1
from src.ops.peak_trade_public_market_data_runtime_v1.freshness_v1 import (
    classify_live_best_bid_ask_freshness_v1,
    classify_live_mark_price_freshness_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import SimulatedFillInputV1
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    derive_protective_stop_price_from_adverse_exit_v0,
)
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    layer_c_derived_exit_policy_adverse_config_digest_v1,
)

_MODE = "INTERNAL_SIMULATED_EXECUTION"
_ZERO = Decimal(0)
_MAX_SECONDS = 7200
_BUDGET_POLICY = "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V5.json"


def paper_constraints_v1(market):
    contract = market.native_contract
    return InstrumentQuantityConstraintsV1(
        instrument_id=market.slot.instrument_id,
        market_type="futures",
        contract_kind="LINEAR",
        contract_multiplier=contract.contract_size,
        lot_size=market.lot_size,
        minimum_quantity=contract.min_qty,
        maximum_quantity=market.maximum_contracts,
        minimum_notional=None,
        tick_size=contract.tick_size,
        instrument_metadata_version=market.source_hashes["instrument"],
    )


def paper_sizing_v1(
    *,
    decision_id,
    input_digest,
    side,
    market,
    stop,
    distance,
    equity,
    cap,
    loss_limit,
    budget,
    config_digest,
    instrument,
    quantity_cap=None,
):
    # The sizer evaluates the resulting exposure. The net fill separately
    # validates and closes the entire old leg in the same accounting operation.
    return CapitalRiskSizingInputV1(
        decision_id=decision_id,
        instrument_id=instrument.instrument_id,
        selected_side=side.upper(),
        reference_price=market.mark,
        protective_stop_price=stop,
        stop_distance=distance,
        account_equity=equity,
        scope_capital_limit=cap,
        per_trade_risk_limit=loss_limit,
        total_capital_limit=cap,
        daily_loss_remaining_budget=loss_limit,
        current_reconciled_exposure=_ZERO,
        maximum_positions=1,
        current_open_positions_count=0,
        current_open_side=None,
        configured_quantity_cap=quantity_cap,
        leverage_ceiling=Decimal(1),
        reconciliation_status="RECONCILED",
        policy_version=budget.policy_id,
        config_digest=config_digest,
        input_digest=input_digest,
        instrument=instrument,
        decision_outcome="enter_" + side.lower(),
    )


def paper_fill_fresh_v1(market, now):
    return (
        market.observed_unix <= now < market.funding_time_unix
        and classify_live_mark_price_freshness_v1(
            age_seconds=now - market.market_event_unix
        ).publishable
        and classify_live_best_bid_ask_freshness_v1(
            age_seconds=now - market.book_event_unix
        ).publishable
    )


class ZkpPaperEntryV1:
    """One writer for the flat slot and its opening evidence."""

    def __init__(
        self,
        *,
        root: Path,
        repo: Path,
        revision: str,
        initial_market,
        duration: int,
        slot=ZKP_PAPER_SLOT,
    ):
        if not root.is_absolute() or root.resolve() != root or root.is_relative_to(repo):
            raise ValueError("ZKP_PAPER_NEW_ISOLATED_ROOT_REQUIRED")
        if type(duration) is not int or not 1 <= duration <= _MAX_SECONDS:
            raise ValueError("ZKP_PAPER_WINDOW_INVALID")
        self.slot = slot
        self.root = root
        self.revision = revision
        self.budget = load_slot_entry_budget_v1(repo / _BUDGET_POLICY)
        self.contract = initial_market.native_contract
        if (
            initial_market.slot != slot
            or self.contract.symbol != self.slot.native_id
            or self.contract.quote_currency != "USD"
            or self.budget.currency != "USDC"
            or self.slot.lane_id not in self.budget.allowed_slot_ids
        ):
            raise ValueError("ZKP_PAPER_CONTRACT_OR_BUDGET_SCOPE_INVALID")
        self.initial_equity = PAPER_ALLOCATION_USDC * initial_market.usd_per_usdc
        self.accounting = ProductiveFuturesAccountingSessionV1(
            contract=self.contract,
            initial_equity=self.initial_equity,
        )
        self.scope = PositionEpisodeScopeV1(root.name, _MODE)
        self.liquidity_policy = initial_market.policy
        self._g17_window = None
        self._g17_producer = None
        identity = {
            "instrument_id": self.slot.instrument_id,
            "venue_native_id": self.slot.native_id,
            "lane_id": self.slot.lane_id,
            "session_id": root.name,
            "environment": _MODE,
            "budget_digest": self.budget.digest_v1(),
            "contract_digest": self.contract.digest(),
            "fee_rate": str(PAPER_FEE_RATE),
            "spread_limit_bps": str(self.liquidity_policy.spread_limit_bps),
            "slippage_limit_bps": str(self.liquidity_policy.slippage_limit_bps),
            "adv_limit_fraction": str(self.liquidity_policy.adv_participation_limit),
            "adv_days": self.liquidity_policy.adv_days,
        }
        self.binding_digest = canonical_digest_v1(identity)
        self.bound = BoundInstrumentV1(
            instrument_id=self.slot.instrument_id,
            venue_native_id=self.slot.native_id,
            ranking_snapshot_id="",
            ranking_integrity_digest="",
            universe_snapshot_id="",
            selection_id=f"paper-fixed:{self.slot.native_id}",
            selection_integrity_digest=self.binding_digest,
            selection_state="EXPLICIT_SINGLE_INSTRUMENT_PAPER",
        )
        self.reconciliation = (
            build_explicit_non_productive_bounded_harness_master_v2_reconciliation_admission_v1(
                bound_instrument_id=self.slot.instrument_id,
                session_id=root.name,
                repository_sha=revision,
            )
        )
        self.cursor_root = root / ENTRY_MARK_STATE_DIRECTORY / self.slot.lane_id
        self.episode_config_digest = layer_c_derived_exit_policy_adverse_config_digest_v1(
            profit_protection_distance=FROZEN_PROFIT_PROTECTION_DISTANCE
        )
        # Exclusive creation keeps a second start from reopening this slot.
        root.mkdir(mode=0o700)
        immutable_json_v1(
            root / "paper-profile.json",
            {
                "schema": "bounded_single_instrument_paper_profile.v1",
                "execution_environment": _MODE,
                "instrument_binding": self.bound.to_dict(),
                "duration_seconds": duration,
                "repository_sha": revision,
                "source_tree_sha256": repository_source_digest_v1(),
                "initial_equity_usd": str(self.initial_equity),
                "opening_allocation_usdc": str(PAPER_ALLOCATION_USDC),
                "allocation_fx": str(initial_market.usd_per_usdc),
                "allocation_fx_source": initial_market.source_hashes["usdc-index"],
                "entry_budget": self.budget.to_dict_v1(),
                "contract": self.contract.to_dict(),
                "fee_rate": str(PAPER_FEE_RATE),
                "fee_model_source": "https://www.okx.com/en-eu/help/okx-x-perps-eea-fees-overview",
                "fee_model": "PUBLIC_EEA_BASE_TAKER",
                "funding_model": "OKX_REALIZED_RATE_PRECEDING_FINAL_MARK_CLOSE",
                "venue_order_transport": False,
                "authority": "NONE",
                "binding": identity,
            },
        )

    def step_v1(self, market, *, clock=time):
        with exclusive_v1(self.root / ".paper-opening.lock"):
            if (self.root / "opening-plan.json").exists():
                raise ValueError("ZKP_PAPER_OPENING_ALREADY_RETAINED")
            if (
                market.slot != self.slot
                or market.native_contract != self.contract
                or market.policy != self.liquidity_policy
            ):
                raise ValueError("ZKP_PAPER_CONTRACT_OR_POLICY_DRIFT")
            market_checks = {
                side: market.assess_opening_liquidity_v1(side=side) for side in ("BUY", "SELL")
            }
            evidence = {
                "market_precheck": market_checks,
                "observed_unix": market.observed_unix,
                "mark_event_unix": market.market_event_unix,
                "source_hashes": market.source_hashes,
            }
            if not paper_fill_fresh_v1(market, clock()):
                return {
                    **evidence,
                    "status": "BLOCKED",
                    "reason": "ZKP_PAPER_MARKET_EXPIRED_AT_CHECK",
                }
            if not any(check["risk_admitted"] for check in market_checks.values()):
                return {**evidence, "status": "WAITING_FOR_LIQUID_MARKET"}
            window = (market.g17_c1_open_unix, market.g17_window_digest)
            if window != self._g17_window:
                if self._g17_window is not None and window[0] <= self._g17_window[0]:
                    return {
                        **evidence,
                        "status": "BLOCKED",
                        "reason": "ZKP_PAPER_FINALIZED_MARK_WINDOW_CHANGED",
                    }
                g17 = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
                    evidence_store_root=self.root,
                    bound_instrument=self.bound,
                    mark_candles_payload=market.g17_payload,
                    receive_or_capture_timestamp=market.g17_acquired_at,
                )
                if g17.fail_closed or not g17.estimate_present or g17.producer is None:
                    return {
                        **evidence,
                        "status": "BLOCKED",
                        "reason": g17.reason_code or "ZKP_PAPER_G17_ABSENT",
                    }
                self._g17_window, self._g17_producer = window, g17.producer
            # Distinct Marks in one minute share the in-process finalized estimate.
            # Restoring a checkpoint alone cannot rematerialize that estimate.
            cycle_id = f"{self.root.name}:paper:{int(market.market_event_unix * 1000)}"
            entry = run_first_entry_mark_cycle_v2(
                offline_state_root=self.root,
                lane_id=self.slot.lane_id,
                bound=self.bound,
                cycle_id=cycle_id,
                observed_unix=market.observed_unix,
                candles_payload=market.candles_payload,
                mark_price_payload=market.mark_payload,
                index_tickers_payload=market.index_payload,
                mark_acquired_at_utc=market.mark_acquired_at,
                bid_px=float(market.book.bids[0][0]),
                ask_px=float(market.book.asks[0][0]),
                volume=float(market.volume_contracts),
                open_interest=float(market.oi_contracts),
                funding_rate=float(market.funding_rate),
                venue_flat=self.accounting.position is None,
                g17_producer=self._g17_producer,
                reconciliation=self.reconciliation,
                budget_binding=FirstEntryBudgetBindingV2(
                    str(self.root), self.scope.account_identity, self.root.name, False
                ),
            )
            if entry.cycle is None:
                return {**evidence, "status": entry.status}
            cycle = entry.cycle
            evidence.update(
                {
                    "status": entry.status,
                    "cycle_id": cycle.cycle_id,
                    "decision_outcome": cycle.decision_outcome,
                    "reason": cycle.input_blocker,
                    "mark_event_unix": entry.mark_event_unix,
                    "c1_open_unix": entry.candle_open_unix,
                }
            )
            decision_path = self.root / "decisions" / f"{int(market.market_event_unix * 1000)}.json"
            if entry.status != "ENTRY_DECIDED":
                immutable_json_v1(decision_path, evidence)
                return evidence
            result = self._prepare_fill(cycle, market, market_checks, clock)
            fill = result.pop("fill", None)
            evidence.update(result)
            if fill is not None:
                evidence["fill"] = fill.to_dict()
            immutable_json_v1(decision_path, evidence)
            if fill is None:
                return evidence
            # Journal the canonical intent and every price/cost binding before accounting.
            opening = {
                **evidence,
                "authority": "NONE",
                "decision_cursor": cycle.outgoing_cursor.to_dict(),
            }
            immutable_json_v1(self.root / "opening-plan.json", opening)
            return self._book_opening(cycle, self._g17_producer, opening, fill)

    def _prepare_fill(self, cycle, market, market_checks, clock):
        replay = cycle.replay
        parent = replay.evidence
        side = {"enter_long": "LONG", "enter_short": "SHORT"}[cycle.decision_outcome]
        fill_side = "BUY" if side == "LONG" else "SELL"
        check = market_checks[fill_side]
        if not check["risk_admitted"]:
            return {"status": "BLOCKED", "reason_codes": check["reason_codes"]}
        distance, reasons = resolve_current_productive_live_29p_adverse_exit_distance_v1(replay)
        if distance is None:
            return {"status": "BLOCKED", "reason_codes": list(reasons)}
        distance = Decimal(str(distance))
        stop = derive_protective_stop_price_from_adverse_exit_v0(
            selected_side=side, reference_price=market.mark, adverse_exit_distance=distance
        )
        if stop is None:
            return {"status": "BLOCKED", "reason_codes": ["ZKP_PAPER_PROTECTIVE_STOP_INVALID"]}
        equity = self.accounting.portfolio_state().equity
        cap = (
            min(
                PAPER_ALLOCATION_USDC,
                self.budget.per_entry_notional_limit,
                self.budget.per_slot_reserved_notional_limit,
            )
            * market.usd_per_usdc
        )
        loss_limit = min(self.budget.per_slot_test_loss_limit * market.usd_per_usdc, equity)
        sizing = paper_sizing_v1(
            decision_id=parent.decision_id,
            input_digest=parent.input_digest,
            side=side,
            market=market,
            stop=stop,
            distance=distance,
            equity=equity,
            cap=cap,
            loss_limit=loss_limit,
            budget=self.budget,
            config_digest=self.binding_digest,
            instrument=paper_constraints_v1(market),
            quantity_cap=Decimal(check["quantity_cap_contracts"]),
        )
        size = evaluate_capital_risk_sizing_v1(sizing)
        plan = build_canonical_order_intent_v1(
            CanonicalOrderIntentBuildInputV1(
                sizing_input=sizing,
                sizing_decision=size,
                intent_id=f"{cycle.cycle_id}:paper",
                trading_epoch=str(parent.trading_epoch),
                canonical_trading_logic_version="first_entry_mark_clock_v2",
                intent_action=cycle.decision_outcome.upper(),
                policy_digest=self.budget.digest_v1(),
                order_type_policy="MARKET_ONLY",
                price_policy="EXPLICIT_NONE",
                time_in_force_policy="GTC",
                max_slippage_policy="NONE",
                expected_position_side=side,
                current_reconciled_exposure=_ZERO,
            )
        )
        intent = plan.intent
        if intent is None:
            return {
                "status": "BLOCKED",
                "reason_codes": list(size.reason_codes) + list(plan.reason_codes),
            }
        if (
            intent.submission_authorized
            or intent.execution_eligible
            or intent.adapter_compatible
            or intent.reduce_only
            or intent.network_effect != "NONE"
            or intent.authority_effect != "NONE"
            or (intent.instrument_id, intent.side, intent.decision_id)
            != (self.slot.instrument_id, side, parent.decision_id)
        ):
            raise ValueError("ZKP_PAPER_INTENT_SCOPE_OR_AUTHORITY_VIOLATION")

        budget_assessment = assess_instrument_budget_v1(
            market=market,
            available_usdc=max(_ZERO, min(cap, equity)) / market.usd_per_usdc,
            side=fill_side,
            quantity_contracts=intent.quantity,
        )
        liquidity = budget_assessment["liquidity"]
        result = {
            "status": "BLOCKED",
            "decision_id": parent.decision_id,
            "intent": canonical_order_intent_to_semantic_dict(intent),
            "liquidity": liquidity,
            "budget_assessment": budget_assessment,
            "reason_codes": liquidity["reason_codes"],
        }
        if not liquidity["risk_admitted"]:
            return result
        now = clock()
        if not paper_fill_fresh_v1(market, now):
            return {**result, "reason_codes": ["ZKP_PAPER_MARKET_EXPIRED_AT_FILL"]}
        price, close_price = (
            Decimal(liquidity["open_price_usd"]),
            Decimal(liquidity["close_price_usd"]),
        )
        base = intent.quantity * self.contract.contract_size
        direction = 1 if side == "LONG" else -1
        notional = base * price
        fee = notional * PAPER_FEE_RATE
        slip = base * max(_ZERO, direction * (price - market.mark))
        closing_slip = base * max(_ZERO, direction * (market.mark - close_price))
        worst_price = max(market.mark, stop, price, close_price)
        closing_fee = base * worst_price * PAPER_FEE_RATE
        funding_reserve = (
            base * worst_price * (market.funding_cap if side == "LONG" else -market.funding_floor)
        )
        reserved_costs = fee + slip + closing_slip + closing_fee + funding_reserve
        result["costs"] = {
            "currency": "USD",
            "entry_notional": str(notional),
            "entry_fee": str(fee),
            "entry_slippage": str(slip),
            "closing_slippage_allowance": str(closing_slip),
            "closing_fee_allowance": str(closing_fee),
            "funding_allowance": str(funding_reserve),
            "next_funding_unix": market.funding_time_unix,
            "loss_with_costs": str(base * distance + reserved_costs),
            "notional_limit": str(cap),
            "loss_limit": str(loss_limit),
        }
        if (
            notional > cap
            or max(notional, base * market.mark) + reserved_costs > min(cap, equity)
            or base * distance + reserved_costs > loss_limit
        ):
            return {**result, "reason_codes": ["ZKP_PAPER_ENTRY_NOTIONAL_OR_COST_LIMIT"]}
        return {
            **result,
            "status": "SIMULATED_FILL_ADMITTED",
            "fill": SimulatedFillInputV1(
                fill_id=f"paper:{intent.semantic_digest}",
                instrument_id=self.slot.native_id,
                side=fill_side,
                quantity=intent.quantity,
                mark_price=market.mark,
                fill_price=price,
                fee=fee,
                slippage_cost=slip,
                notional=notional,
                event_time_unix=now,
            ),
        }

    def _book_opening(self, cycle, producer, opening, fill):
        applied = self.accounting.apply_fill(fill)
        position = self.accounting.position
        side = "long" if fill.side == "BUY" else "short"
        if position is None or position.side.value.lower() != side or position.qty != fill.quantity:
            raise ValueError("ZKP_PAPER_ACCOUNTING_OPEN_POSITION_UNPROVEN")
        identity = bind_simulated_accounting_episode_identity_v1(
            identity=PositionEpisodeIdentityV1(
                self.slot.lane_id,
                self.slot.instrument_id,
                self.slot.native_id,
                "pending",
                side,
                self.scope,
            ),
            opening_fill=fill,
        )
        episode = create_position_episode_from_simulated_accounting_v1(
            identity=identity,
            session=self.accounting,
            fills=(fill,),
            source_archive_root=self.root / "episode-sources",
            state_root=self.root / "episodes" / identity.episode_id,
            repository_sha=self.revision,
            config_digest=self.episode_config_digest,
            writer_session_id=self.root.name,
        )
        publication = publish_confirmed_first_entry_c1_v2(
            episode=episode,
            cursor_root=self.cursor_root,
            g17_producer=producer,
            writer_session_id=self.root.name,
            retain_opening=lambda: canonical_digest_v1(opening),
        )
        receipt = {
            "status": "FIRST_FILL_BOOKED",
            "authority": "NONE",
            "execution_environment": _MODE,
            "lane_id": self.slot.lane_id,
            "cycle_id": cycle.cycle_id,
            "decision_id": opening["decision_id"],
            "episode_id": identity.episode_id,
            "accounting_output_digest": applied.accounting_output_digest,
            "accounting": self.accounting.portfolio_state().to_dict(),
            "fill": fill.to_dict(),
            "c1_publication": publication,
            "opening_plan_digest": canonical_digest_v1(opening),
            "budget_assessment": opening["budget_assessment"],
            "costs": opening["costs"],
            "orders_sent": 0,
            "permits_created": 0,
        }
        immutable_json_v1(self.root / "opening-fill.json", receipt)
        return receipt
