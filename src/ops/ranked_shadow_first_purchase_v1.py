"""Decision-bound first purchase for the two ranked, analytical USDT swap slots."""

from dataclasses import dataclass, replace
from hashlib import sha256
from datetime import datetime, timezone
from decimal import Decimal
from collections.abc import Callable
import json
from pathlib import Path

from src.governance.capital_risk_sizing_v1 import InstrumentQuantityConstraintsV1
from src.ops.bounded_peaktrade_system_composition_v1.paper_market_liquidity_v1 import (
    _decimal,
    _fresh,
    _one,
    _timestamp,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.instrument_card_stream_v1 import (
    bind_shadow_slot_entry_budget_v1,
    plain,
    ranked_shadow_slot_budget_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportError,
)
from src.ops.peak_trade_public_market_data_runtime_v1.freshness_v1 import (
    classify_live_best_bid_ask_freshness_v1,
    classify_live_mark_price_freshness_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import opening_order_side_v1
from src.ops.ranked_shadow_entry_selection_v1 import (
    read_ranked_entry_bound_v1,
    resolve_ranked_shadow_entry_selection_v1,
)
from src.ops.ranked_slot_run_source_v1 import RankedRunSlotV1
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    BoundedSlotEntryBudgetV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import (
    ReservationSizingBindingV1,
    request_digest_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.network_boundary_guard_v1 import (
    NetworkBoundaryError,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.wallclock_evidence_v1 import (
    WallclockEvidenceError,
)
from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
    build_capital_risk_sizing_input_from_decision_v0,
)
from src.ops.ranked_swap_shadow_observation_v1 import observe_ranked_entry_fx_v1
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    bind_capital_risk_sizing_offline_replay_evidence_v0,
    default_offline_replay_capital_context_v0,
)
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    bind_canonical_order_intent_offline_replay_evidence_v0,
)
from trading.master_v2.mv2_offline_boundary_dynamic_price_context_v1 import (
    build_mv2_offline_boundary_dynamic_price_context_v1,
)


def _native_constraints(inventory, instrument):
    native = instrument.venue_native_inst_id
    row = _one(inventory, native)
    if (
        row["instType"],
        row["ctType"],
        row["state"],
        row["settleCcy"],
        row["ctValCcy"],
        row["uly"],
    ) != (
        "SWAP",
        "linear",
        "live",
        "USDT",
        instrument.base_currency,
        f"{instrument.base_currency}-USDT",
    ):
        raise ValueError("SHADOW_FIRST_PURCHASE_NATIVE_METADATA_MISMATCH")
    size, lot, minimum, tick = (
        _decimal(row[k], positive=True) for k in ("ctVal", "lotSz", "minSz", "tickSz")
    )
    if (size, lot, minimum, tick) != tuple(
        map(
            Decimal,
            (
                instrument.contract_value,
                instrument.lot_size,
                instrument.minimum_order_size,
                instrument.tick_size,
            ),
        )
    ):
        raise ValueError("SHADOW_FIRST_PURCHASE_NATIVE_GRID_CHANGED")
    return InstrumentQuantityConstraintsV1(
        instrument_id=instrument.canonical_instrument_id,
        market_type="futures",
        contract_kind="LINEAR",
        contract_multiplier=size,
        lot_size=lot,
        minimum_quantity=minimum,
        maximum_quantity=_decimal(row["maxMktSz"], positive=True),
        minimum_notional=None,
        tick_size=tick,
        instrument_metadata_version=canonical_digest_v1(row),
    )


def _cost_limit(state, market, native, mark, side, stop_distance, available, loss):
    """Find the largest lot affordable on both sides of this book, before original CRS."""
    return ranked_shadow_book_cost_limit_v1(
        state.portfolio.model.params,
        market.book,
        market.source_observations["funding"].payload,
        market.native_id,
        native,
        mark,
        side,
        stop_distance,
        available,
        loss,
    )


def ranked_shadow_book_cost_limit_v1(
    params, book, funding_payload, native_id, native, mark, side, stop_distance, available, loss
):
    fee, slip = (
        v / 10000
        for v in (
            params.fee_rate_bps,
            params.slippage_bps,
        )
    )
    funding = _one(funding_payload, native_id)
    floor, ceiling = map(_decimal, (funding["minFundingRate"], funding["maxFundingRate"]))
    if not floor <= _decimal(funding["fundingRate"]) <= ceiling or not (0 <= fee and 0 <= slip < 1):
        raise ValueError("SHADOW_FIRST_PURCHASE_COST_INPUT_INVALID")
    funding_rate = max(Decimal(0), ceiling if side == "BUY" else -floor)

    def costs(count):
        opening, closing = (
            book.executable_price_v1(s, count, native.tick_size)
            for s in (side, "SELL" if side == "BUY" else "BUY")
        )
        if opening is None or closing is None:
            return None
        base = count * native.contract_multiplier
        worst = max(mark + stop_distance, opening, closing)
        crossing = max(Decimal(0), opening - mark if side == "BUY" else mark - opening)
        closing_cross = max(Decimal(0), mark - closing if side == "BUY" else closing - mark)
        allowance = base * (
            max(mark * slip, crossing)
            + max(worst * slip, closing_cross)
            + (mark + worst) * (1 + slip) * fee
            + worst * funding_rate
        )
        if (
            base * mark + allowance > available
            or base * opening > available
            or base * stop_distance + allowance > loss
        ):
            return None
        return dict(
            cost_allowance_usdt=str(allowance),
            opening_book_usdt_per_base=str(opening),
            closing_book_usdt_per_base=str(closing),
        )

    lot = native.lot_size
    high = int(min(native.maximum_quantity, available / (mark * native.contract_multiplier)) // lot)
    low = 0
    while low < high:
        mid = (low + high + 1) // 2
        if costs(mid * lot) is None:
            high = mid - 1
        else:
            low = mid
    if low * lot < native.minimum_quantity:
        raise ValueError("SHADOW_FIRST_PURCHASE_MINIMUM_LOT_NOT_ADMITTED")
    return low * lot, costs


@dataclass
class RankedShadowFirstPurchaseV1:
    config: Path
    assignment: RankedRunSlotV1
    inventory: dict
    policy: BoundedSlotEntryBudgetV1
    reconciliation_root: Path
    transport: object
    clock: Callable[[], float]
    transport_error: EeaPublicMdTransportError | None = None

    def prepare(self, *, state, market, replay, cycle_id, host_decision_id, adverse_distance):
        self.transport_error = None
        parent = replay.evidence
        receipt = dict(
            status="BLOCKED",
            session_id=state.session_id,
            lane_id=self.assignment.reference()["lane_id"],
            cycle_id=cycle_id,
            decision_id=parent.decision_id,
            host_decision_id=host_decision_id,
            parent_digest=parent.semantic_digest,
            reason_codes=[],
        )
        try:
            self._prepare(receipt, state, market, replay, adverse_distance)
        except NetworkBoundaryError:
            raise
        except OSError as exc:
            raise WallclockEvidenceError("SHADOW_FIRST_PURCHASE_SOURCE_IO_FAILED") from exc
        except EeaPublicMdTransportError as exc:
            self.transport_error = exc
            receipt["reason_codes"] = [str(exc)]
        except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
            receipt["reason_codes"] = [str(exc)]
        return receipt

    def _prepare(self, receipt, state, market, replay, adverse_distance):
        parent, inter = replay.evidence, replay.intermediate
        direction = parent.selected_side.lower()
        assessment = inter.bull_assessment if direction == "long" else inter.bear_assessment
        progress = inter.directional_confirmation_progress_after
        if (
            not replay.replay_pass
            or parent.decision_outcome != f"enter_{direction}"
            or parent.instrument_id != state.instrument_id
            or state.killstate_active
            or not state.venue_flat
            or state.ranked_confirmed_entry_budget is not None
            or assessment is None
            or assessment.status.value != "confirmed"
            or assessment.side.value != direction
            or assessment.instrument_id != parent.instrument_id
            or progress is None
        ):
            raise ValueError("SHADOW_FIRST_PURCHASE_CONFIRMED_FLAT_ENTRY_REQUIRED")
        confirmed = (
            progress.bull_confirmation_state
            if direction == "long"
            else progress.bear_confirmation_state
        )
        if (
            confirmed.session_id,
            confirmed.instrument.canonical_instrument_id,
            confirmed.instrument.venue_instrument_id,
        ) != (state.session_id, market.canonical_id, market.native_id):
            raise ValueError("SHADOW_FIRST_PURCHASE_CONFIRMATION_SCOPE_MISMATCH")
        if (
            confirmed.assessment_state.value != "confirmed"
            or confirmed.distinct_confirmation_observation_count < 2
        ):
            raise ValueError("SHADOW_FIRST_PURCHASE_DISTINCT_CONFIRMATION_REQUIRED")
        receipt["confirmation"] = dict(
            assessment_id=assessment.assessment_id, progress=confirmed.to_dict()
        )
        config = json.loads(self.config.read_bytes())
        selection, admission = resolve_ranked_shadow_entry_selection_v1(
            self.config,
            session_id=state.session_id,
            assignment=self.assignment,
            state=state,
            market=market,
            decision_id=parent.decision_id,
            clock=self.clock,
            reconciliation_root=self.reconciliation_root,
        )
        receipt["selection"] = selection
        if admission is None:
            receipt["reason_codes"] = selection["blockers"]
            return
        valuation = observe_ranked_entry_fx_v1(
            self.assignment,
            market,
            dict(decision_id=parent.decision_id, decision_outcome=parent.decision_outcome),
            admission=admission,
            transport=self.transport,
            clock=self.clock,
        )
        receipt["valuation"] = valuation
        if valuation["status"] != "OBSERVED":
            raise ValueError(valuation["reason"])
        fx, mark = map(Decimal, (valuation["usdc_per_usdt"], valuation["mark_usdt_per_base"]))
        slot = self.assignment.lane_id
        budget = ranked_shadow_slot_budget_v1(state, slot, self.policy, valuation)
        raw_limit = config.get("shadow_entry_cost_limit_usdc")
        if raw_limit is not None and (not isinstance(raw_limit, str) or _decimal(raw_limit) < 0):
            raise ValueError("SHADOW_FIRST_PURCHASE_COST_LIMIT_INVALID")
        available_usdc = Decimal(budget["available_amount"])
        entry_limit = min(available_usdc, self.policy.per_entry_notional_limit)
        if raw_limit is not None:
            entry_limit = min(entry_limit, Decimal(raw_limit))
        receipt["capacity"] = dict(
            slot_available_usdc=str(available_usdc),
            configured_entry_limit_usdc=raw_limit,
            entry_limit_usdc=str(entry_limit),
            minimum_contracts=valuation["minimum_contracts"],
            minimum_mark_notional_usdc=valuation["minimum_mark_notional_usdc"],
        )
        available = available_usdc / fx
        loss = min(available, self.policy.per_slot_test_loss_limit / fx)
        side = opening_order_side_v1(direction)
        native = _native_constraints(self.inventory, admission.instrument)
        prices = build_mv2_offline_boundary_dynamic_price_context_v1(
            mark_price=mark,
            selected_side=direction.upper(),
            adverse_exit_distance=adverse_distance,
        )
        if prices.protective_stop_price is None or mark != Decimal(
            str(inter.market_context.mark_price)
        ):
            raise ValueError("SHADOW_FIRST_PURCHASE_ORIGINAL_PRICE_REQUIRED")
        cap, costs = _cost_limit(
            state,
            market,
            native,
            mark,
            side,
            abs(mark - prices.protective_stop_price),
            entry_limit / fx,
            loss,
        )
        context = default_offline_replay_capital_context_v0(
            instrument_id=state.instrument_id,
            reference_price=mark,
            protective_stop_price=prices.protective_stop_price,
            account_equity=available,
            scope_capital_limit=cap * native.contract_multiplier * mark,
            total_capital_limit=available,
            per_trade_risk_limit=loss,
            daily_loss_remaining_budget=loss,
            instrument=native,
            config_digest=budget["source_digest"],
        )
        sizing = bind_capital_risk_sizing_offline_replay_evidence_v0(
            parent, capital_context=context
        )
        size = sizing.sizing_decision
        if size is None or size.outcome.value != "PASS":
            raise ValueError("SHADOW_FIRST_PURCHASE_SIZING_DENIED")
        request, errors = build_capital_risk_sizing_input_from_decision_v0(
            decision=parent, capital_context=context
        )
        if errors or request is None:
            raise ValueError("SHADOW_FIRST_PURCHASE_SIZING_SOURCE_MISSING")
        sizing_binding = ReservationSizingBindingV1(request_digest_v1(request), request, size)
        intent_result = bind_canonical_order_intent_offline_replay_evidence_v0(
            sizing.evidence,
            sizing_decision=size,
            capital_context=context,
        )
        intent = intent_result.canonical_intent
        if intent is None:
            raise ValueError("SHADOW_FIRST_PURCHASE_INTENT_DENIED")
        funded = replace(
            replay,
            evidence=intent_result.evidence,
            intermediate=replace(
                inter, capital_risk_sizing_decision=size, canonical_order_intent=intent
            ),
        )
        bound = read_ranked_entry_bound_v1(
            self.config, self.assignment, admission, selection, self.clock()
        )
        epoch = valuation["valuation_epoch"]
        mode = "INTERNAL_SIMULATED_EXECUTION"
        status, reasons, plan = try_bind_current_productive_venue_plan_v1(
            replay=funded,
            bound_instrument=bound,
            session_id=state.session_id,
            run_id=receipt["cycle_id"],
            composed_epoch=epoch,
            execution_mode=mode,
        )
        if status.value != "PASS" or plan is None:
            receipt["reason_codes"] = list(reasons)
            return
        qty = size.final_quantity
        nominal = size.post_sizing_risk.resulting_notional
        exact = costs(qty)
        if (
            plan.environment != mode
            or plan.reduce_only
            or plan.order_type != "market"
            or plan.instrument_id != market.native_id
            or plan.side.upper() != side
            or Decimal(plan.quantity) != qty
            or qty != intent.quantity
            or exact is None
            or qty < native.minimum_quantity
            or qty % native.lot_size
            or qty > cap
            or nominal != qty * native.contract_multiplier * mark
        ):
            raise ValueError("SHADOW_FIRST_PURCHASE_SIZED_PLAN_MISMATCH")
        entry = dict(
            status="CONFIRMED",
            session_id=state.session_id,
            cycle_id=receipt["cycle_id"],
            decision_id=parent.decision_id,
            host_decision_id=receipt["host_decision_id"],
            lane_id=slot,
            instrument_id=state.instrument_id,
            venue_native_id=market.native_id,
            direction=direction,
            entry_action="FIRST_PURCHASE",
            first_purchase_side=side,
            selection_id=bound.selection_id,
            selection_integrity_digest=bound.selection_integrity_digest,
            n5_assignment=self.assignment.reference(),
            cap24_evidence_sha256=selection["cap24_evidence_sha256"],
            entry_limit_usdc=str(entry_limit),
            sizing_request_digest=sizing_binding.request_digest,
            sizing_ref=size.quantity_provenance.sizing_ref,
            sizing_decision_ref=sizing.risk_sizing_ref,
            quantity_contracts=str(qty),
            base_per_contract=str(native.contract_multiplier),
            nominal_usdt=str(nominal),
            nominal_usdc=str(nominal * fx),
            budget_owner=budget["owner"],
            budget_source_digest=budget["source_digest"],
            binding_scope="ANALYTICAL_SLOT_ENTRY",
            fx_sha256=valuation["original_fx_sha256"],
            mark_sha256=market.source_hashes["mark"],
            **exact,
        )
        # Re-read selection and sources after sizing. Bind only an executable, current amount.
        bound = read_ranked_entry_bound_v1(
            self.config, self.assignment, admission, selection, self.clock()
        )
        now = self.clock()
        admission.require_current_v1(now)
        _require_fresh_execution(market, valuation, now)
        if json.loads(self.config.read_bytes()) != config:
            raise ValueError("SHADOW_FIRST_PURCHASE_CONFIG_CHANGED")
        if budget != ranked_shadow_slot_budget_v1(state, slot, self.policy, valuation):
            raise ValueError("SHADOW_FIRST_PURCHASE_BUDGET_CHANGED")
        envelope = bind_final_order_envelope_from_venue_plan_v1(
            plan,
            admission_ref=canonical_digest_v1(entry),
            provenance_ref=intent.semantic_digest,
            creation_epoch=epoch,
        )
        bound_entry = bind_shadow_slot_entry_budget_v1(
            state=state, bound=bound, budget=budget, entry=entry, sizing=sizing_binding
        )
        receipt.update(
            status="PLAN_BOUND",
            entry=bound_entry,
            budget=budget,
            environment=mode,
            envelope=envelope.to_runtime_json_v1(),
            sizing_result=size.outcome.value,
            sizing=sizing_binding.to_dict_v1(),
            quantity_base=str(Decimal(envelope.quantity) * native.contract_multiplier),
            base_currency=admission.instrument.base_currency,
            checked_at_unix=now,
        )


def _require_fresh_execution(market, valuation, now):
    base = market.receipt_path.parent
    raw = (base / "entry-fx.json").read_bytes()
    ref = json.loads((base / "entry-fx-receipt.json").read_bytes())
    received = ref["received_at_unix"]
    if (
        ref["body_sha256"] != sha256(raw).hexdigest()
        or ref["body_sha256"] != valuation["original_fx_sha256"]
        or any(
            ref[k] != valuation[k]
            for k in (
                "decision_id",
                "lane_id",
                "instrument_id",
                "venue_native_id",
                "mark_sha256",
                "n5_selection_digest",
                "entry_selection_digest",
            )
        )
    ):
        raise ValueError("SHADOW_FIRST_PURCHASE_FX_CHANGED")
    _fresh(_one(json.loads(raw), "USDC-USDT"), received, now, classify_live_mark_price_freshness_v1)
    for name, acquired, classify in (
        ("mark", market.mark_acquired_unix, classify_live_mark_price_freshness_v1),
        (
            "book",
            datetime.fromisoformat(market.book_acquired_at_utc).timestamp(),
            classify_live_best_bid_ask_freshness_v1,
        ),
    ):
        _fresh(_one(market.source_observations[name].payload), acquired, now, classify)
    funding = _one(market.source_observations["funding"].payload, market.native_id)
    if (
        not 0 <= now - _timestamp(funding) / 1000 <= 180
        or now >= _timestamp(funding, "fundingTime") / 1000
    ):
        raise ValueError("I17_SWAP_FUNDING_OUTSIDE_WINDOW")


def verify_ranked_first_purchase_v1(cycle):
    """Verify the retained native sizing, bound USDC amount, envelope and booked base units."""
    from src.governance.capital_risk_sizing_v1 import evaluate_capital_risk_sizing_v1
    from src.ops.instrument_card_stream_v1 import validate_ranked_sized_amount_v1
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        FinalOrderEnvelopeV1,
        assert_envelope_unmodified_v1,
    )
    from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
        RANKED_SWAP_SCOPES,
    )
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.provenance_v2 import (
        portfolio_state_hash,
    )

    try:
        p = cycle["ranked_shadow_first_purchase"]
        action, fill = cycle["intended_action"], cycle["fill"]
        scope = next(s for s in RANKED_SWAP_SCOPES if s.canonical_id == cycle["instrument_id"])
        if (p["cycle_id"], p["host_decision_id"], p["session_id"], p["lane_id"]) != (
            cycle["cycle_id"],
            cycle["decision_id"],
            cycle["session_id"],
            scope.lane_id,
        ):
            return False
        if p["status"] == "BLOCKED":
            return (
                bool(p["reason_codes"])
                and fill is None
                and cycle["fill_id"] is None
                and action["intended_side"] == "HOLD"
                and Decimal(action["intended_quantity"]) == 0
                and p.get("entry") is None
            )
        entry, budget, value, sel = p["entry"], p["budget"], p["valuation"], p["selection"]
        sizing = ReservationSizingBindingV1.from_dict_v1(p["sizing"])
        validate_ranked_sized_amount_v1(budget, entry, sizing)
        if evaluate_capital_risk_sizing_v1(sizing.applied_input) != sizing.decision:
            return False
        envelope = FinalOrderEnvelopeV1(**p["envelope"])
        assert_envelope_unmodified_v1(envelope, expected_digest=fill["opening_envelope_digest"])
        expected_base = Decimal(entry["quantity_contracts"]) * Decimal(entry["base_per_contract"])
        progress = p["confirmation"]["progress"]
        return (
            p["status"] == "FILLED"
            and not p["reason_codes"]
            and p["sizing_result"] == "PASS"
            and cycle["risk_sizing_result"] == "PASS"
            and p["environment"] == "INTERNAL_SIMULATED_EXECUTION"
            and (
                entry["decision_id"],
                entry["host_decision_id"],
                entry["cycle_id"],
                entry["session_id"],
            )
            == (p["decision_id"], cycle["decision_id"], cycle["cycle_id"], cycle["session_id"])
            and entry["n5_assignment"] == sel["n5_assignment"]
            and entry["selection_integrity_digest"] == sel["entry_admission"]["selection_digest"]
            and entry["cap24_evidence_sha256"] == sel["cap24_evidence_sha256"]
            and not sel["blockers"]
            and (scope.lane_id, scope.canonical_id, scope.native_id)
            == (entry["lane_id"], entry["instrument_id"], entry["venue_native_id"])
            and budget["original_snapshot"]["valuation"] == value == cycle["shadow_entry_valuation"]
            and cycle["shadow_entry_selection"] == sel
            and budget["reserved_amount"] is None
            and portfolio_state_hash(budget["original_snapshot"]["original_portfolio"])
            == cycle["portfolio_state_before_hash"]
            and budget["lane_id"] == entry["lane_id"]
            and entry["budget_source_digest"] == budget["source_digest"]
            and Decimal(0) < Decimal(entry["nominal_usdc"]) <= Decimal(budget["available_amount"])
            and cycle["decision_outcome"] == "enter_" + entry["direction"]
            and progress["distinct_confirmation_observation_count"] >= 2
            and progress["assessment_state"] == "confirmed"
            and p["fill_id"] == fill["fill_id"] == cycle["fill_id"]
            and action["intent_action"] == entry["entry_action"] == "FIRST_PURCHASE"
            and envelope.admission_ref == canonical_digest_v1(entry)
            and not envelope.reduce_only
            and envelope.instrument_id == scope.native_id
            and fill["instrument_id"] == scope.canonical_id
            and envelope.side.upper()
            == opening_order_side_v1(entry["direction"])
            == fill["side"]
            == entry["first_purchase_side"]
            == action["intended_side"]
            and envelope.quantity_unit == "CONTRACTS"
            and fill["quote_currency"] == "USDT"
            and fill["quantity_unit"] == p["base_currency"] == scope.base
            and Decimal(envelope.quantity)
            == Decimal(entry["quantity_contracts"])
            == Decimal(fill["quantity_contracts"])
            and expected_base
            == Decimal(p["quantity_base"])
            == Decimal(fill["quantity"])
            == Decimal(action["intended_quantity"])
            and sizing.applied_input.reference_price == Decimal(fill["mark_price"])
        )
    except (
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        ArithmeticError,
        RuntimeError,
        StopIteration,
    ):
        return False
