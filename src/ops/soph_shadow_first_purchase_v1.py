"""Hand the original sized SOPH entry to the analytical slot's simulated execution."""

from datetime import datetime, timezone
from decimal import Decimal
from math import isfinite

from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.soph_slot_assignment_v1 import SophSlotSourcesV1
from src.ops.instrument_card_stream_v1 import (
    plain,
    validate_card_market_v1,
    validate_shadow_slot_entry_budget_v1,
)


def _selection_window(root, repository_sha, bound, market, decision_time):
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
        inspect_selection_v1,
    )
    from src.ops.ranking_universe_to_full_core_ssf_handoff_contract_v1 import (
        assert_handoff_invariants_v1,
    )

    if not bound.ranking_snapshot_id or not bound.universe_snapshot_id:
        raise ValueError("SOPH_FIRST_PURCHASE_RANKING_UNIVERSE_BINDING_REQUIRED")
    if root is None or not repository_sha:
        raise ValueError("SOPH_FIRST_PURCHASE_SELECTION_SOURCE_REQUIRED")
    epoch = datetime.fromtimestamp(decision_time, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(root, SophSlotSourcesV1):
        sources = root.inspect(repository_sha)
        if sources.selection.state != "SELECTED_ACTIVE":
            raise ValueError("SOPH_FIRST_PURCHASE_SELECTION_NOT_ACTIVE")
    else:
        sources = inspect_selection_v1(
            productivity_root=root,
            repository_sha=repository_sha,
            binding_epoch=epoch,
            mark_price_by_native_id={bound.venue_native_id: str(market.mark)},
        )
    selection, ranking, universe = sources.selection, sources.ranking, sources.universe
    assert_handoff_invariants_v1(
        selection,
        bound,
        ranking_snapshot_id=ranking.ranking_snapshot_id,
        ranking_universe_snapshot_id=ranking.universe_snapshot_id,
        universe_snapshot_id=universe.snapshot_id,
    )
    if (
        bound.selection_state != selection.state
        or bound.selected_future_count != 1
        or bound.max_positions_effective != 1
        or bound.upstream_rank_order_witness != selection.upstream_rank_order_witness
        or bound.ranking_policy_id != selection.ranking_policy_id
        or bound.ranking_policy_version != selection.ranking_policy_version
        or bound.selection_integrity_digest != selection.integrity_digest
        or bound.ranking_integrity_digest != ranking.integrity_digest
        or ranking.repository_sha != repository_sha
        or ranking.universe_payload_digest != universe.payload_digest
        or ranking.universe_source_digest != universe.source_digest
        or not any(
            row.canonical_instrument_id == bound.instrument_id
            and row.venue_native_id == bound.venue_native_id
            and row.rank == selection.selected_rank
            for row in ranking.ranked_candidates
        )
    ):
        raise ValueError("SOPH_FIRST_PURCHASE_SELECTION_REFERENCE_MISMATCH")
    known_at = max(
        datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        for value in (
            selection.valid_from,
            selection.selected_at_event_time,
            selection.selected_at_wall_time,
            ranking.produced_at_wall_time,
            universe.generated_at_wall_time,
        )
    )
    if decision_time < known_at:
        raise ValueError("SOPH_FIRST_PURCHASE_SELECTION_NOT_YET_AVAILABLE")
    expires = datetime.fromisoformat(selection.valid_until.replace("Z", "+00:00")).timestamp()
    if decision_time > expires:
        raise ValueError("SELECTION_STALE_FOR_BINDING_EPOCH")
    return expires


def prepare_soph_shadow_first_purchase_v1(
    *, state, replay, bound, market, budget, cycle_id, repository_sha, clock
):
    """Consume a new binding in its decision cycle. Old or denied entries are never replayed."""
    from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
        try_bind_current_productive_venue_plan_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        bind_final_order_envelope_from_venue_plan_v1,
    )
    from src.ops.soph_shadow_capital_risk_binding_v1 import soph_shadow_cost_check_v1

    entry = state.soph_confirmed_entry_budget
    receipt = dict(
        status="BLOCKED",
        entry_action="FIRST_PURCHASE",
        decision_id=entry["decision_id"],
        cycle_id=cycle_id,
        lane_id=entry["lane_id"],
        binding=bound.to_dict(),
        budget_source_digest=entry["budget_source_digest"],
        entry_digest=canonical_digest_v1(entry),
    )
    try:
        validate_shadow_slot_entry_budget_v1(state=state, bound=bound, budget=budget, entry=entry)
        expires = _selection_window(
            state.soph_selection_root, repository_sha, bound, market, entry["decision_unix"]
        )
        intent = replay.intermediate.canonical_order_intent
        sizing = replay.intermediate.capital_risk_sizing_decision
        position = state.portfolio.model.state.positions.get(bound.instrument_id)
        if (
            intent is None
            or sizing is None
            or state.killstate_active
            or entry["cycle_id"] != cycle_id
            or entry["decision_id"] != intent.decision_id
            or entry["direction"] != intent.side.lower()
            or entry["sizing_ref"] != sizing.quantity_provenance.sizing_ref
            or Decimal(entry["nominal_usd"]) != sizing.post_sizing_risk.resulting_notional
            or Decimal(entry["nominal_usdc"]) != Decimal(entry["nominal_usd"]) / market.usd_per_usdc
            or entry["market_event_unix"] != market.market_event_unix
            or canonical_digest_v1(budget["original_snapshot"]) != budget["source_digest"]
            or budget["original_snapshot"]["original_portfolio"]
            != plain(state.portfolio.snapshot())
            or budget["original_snapshot"].get("confirmed_entry_budget") is not None
            or (position is not None and position.quantity != 0)
        ):
            raise ValueError("SOPH_FIRST_PURCHASE_ORIGINAL_BINDING_REQUIRED")
        mode = "INTERNAL_SIMULATED_EXECUTION"
        epoch = datetime.fromtimestamp(entry["decision_unix"], timezone.utc).isoformat()
        status, reasons, plan = try_bind_current_productive_venue_plan_v1(
            replay=replay,
            bound_instrument=bound,
            session_id=state.session_id,
            run_id=cycle_id,
            composed_epoch=epoch,
            execution_mode=mode,
        )
        if status.value != "PASS" or plan is None:
            return dict(receipt, reason_codes=list(reasons))
        size = Decimal(plan.quantity)
        side = plan.side.upper()
        if (
            plan.environment != mode
            or plan.reduce_only
            or plan.order_type != "market"
            or plan.instrument_id != entry["venue_native_id"]
            or side != entry["first_purchase_side"]
            or size != Decimal(entry["quantity_contracts"])
        ):
            raise ValueError("SOPH_FIRST_PURCHASE_PLAN_MISMATCH")
        envelope = bind_final_order_envelope_from_venue_plan_v1(
            plan,
            admission_ref=receipt["entry_digest"],
            provenance_ref=intent.semantic_digest,
            creation_epoch=epoch,
        )
        qty = size * market.native_contract.contract_size
        check = soph_shadow_cost_check_v1(
            state=state,
            market=market,
            budget=budget,
            side=side,
            quantity=qty,
            stop_distance=sizing.pre_sizing_risk.stop_or_risk_distance,
            entry_cost_limit_usdc=state.soph_entry_cost_limit_usdc,
        )
        if not check["measurement_admitted"]:
            return dict(receipt, reason_codes=check["reason_codes"], execution_check=check)
        if Decimal(entry["cost_allowance_usd"]) != Decimal(check["model_costs"]["total_reserve"]):
            raise ValueError("SOPH_FIRST_PURCHASE_COST_BINDING_MISMATCH")
        if not callable(clock):
            raise ValueError("SOPH_FIRST_PURCHASE_EXECUTION_CLOCK_REQUIRED")
        if isinstance(state.soph_selection_root, SophSlotSourcesV1):
            state.soph_selection_root.inspect(repository_sha).require_matching_binding(bound)
        now = clock()
        if (
            type(now) not in (int, float)
            or not isfinite(now)
            or not entry["decision_unix"] <= now <= expires
        ):
            raise ValueError("SOPH_FIRST_PURCHASE_EXECUTION_TIME_INVALID")
        validate_card_market_v1(market, bound=bound, lane_id=entry["lane_id"], now=now)
        check.update(
            checked_at_unix=now,
            check_time_source="EXECUTION_CLOCK",
            stop_distance_source="ORIGINAL_CRS_PRE_SIZING_RISK",
        )
        return dict(
            receipt,
            status="PLAN_BOUND",
            reason_codes=[],
            environment=mode,
            envelope=envelope.to_runtime_json_v1(),
            quantity_base=str(qty),
            execution_check=check,
        )
    except (ArithmeticError, OSError, RuntimeError, ValueError) as exc:
        return dict(receipt, reason_codes=[str(exc)])


def verify_soph_shadow_purchase_receipt_v1(cycle):
    """Check the retained entry, executable plan and analytical fill on economic readback."""
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        FinalOrderEnvelopeV1,
        assert_envelope_unmodified_v1,
    )

    purchase = cycle.get("soph_simulated_first_purchase")
    action = cycle["intended_action"]
    fill = cycle.get("fill")
    if purchase is None:
        return action.get("intent_action") != "FIRST_PURCHASE" and not (fill or {}).get(
            "opening_envelope_digest"
        )
    try:
        entry = cycle["soph_confirmed_entry_budget"]
        if not (
            purchase["entry_digest"] == canonical_digest_v1(entry)
            and purchase["decision_id"] == entry["decision_id"]
            and purchase["cycle_id"] == entry["cycle_id"] == cycle["cycle_id"]
            and purchase["lane_id"] == entry["lane_id"]
            and purchase["budget_source_digest"] == entry["budget_source_digest"]
            and purchase["binding"]["selection_integrity_digest"]
            == entry["selection_integrity_digest"]
        ):
            return False
        if purchase["status"] == "BLOCKED":
            return (
                fill is None
                and action["intended_side"] == "HOLD"
                and bool(purchase["reason_codes"])
            )
        envelope = FinalOrderEnvelopeV1(**purchase["envelope"])
        assert_envelope_unmodified_v1(envelope, expected_digest=fill["opening_envelope_digest"])
        return (
            purchase["status"] == "FILLED"
            and purchase["environment"] == "INTERNAL_SIMULATED_EXECUTION"
            and envelope.admission_ref == purchase["entry_digest"]
            and envelope.instrument_id == entry["venue_native_id"]
            and purchase["fill_id"] == fill["fill_id"] == cycle["fill_id"]
            and action["intent_action"] == "FIRST_PURCHASE"
            and not envelope.reduce_only
            and envelope.side.upper()
            == entry["first_purchase_side"]
            == fill["side"]
            == action["intended_side"]
            and envelope.quantity_unit == "CONTRACTS"
            and Decimal(envelope.quantity)
            == Decimal(entry["quantity_contracts"])
            == Decimal(fill["quantity_contracts"])
            and Decimal(purchase["quantity_base"])
            == Decimal(fill["quantity"])
            == Decimal(action["intended_quantity"])
        )
    except (ArithmeticError, AttributeError, KeyError, TypeError, RuntimeError, ValueError):
        return False
