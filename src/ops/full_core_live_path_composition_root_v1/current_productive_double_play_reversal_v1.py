"""Assess a single net order for the occupied slot's sealed L10 switch."""

from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime
from decimal import Decimal
import json
import math
from pathlib import Path

from src.execution.position_delta import signed_position_delta
from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingOutcome,
    evaluate_capital_risk_sizing_v1,
)
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
    canonical_digest_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.normalize_v1 import (
    build_capital_risk_sizing_monetary_context_v1,
    crs_operands_from_monetary_context_v1,
)
from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
    read_occupied_scope_mark_snapshot_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    apply_capital_context_facts_v1,
    capital_context_facts_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import HostBudgetRecoveryContextV1
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    BoundedSlotEntryBudgetV1,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    derive_protective_stop_price_from_adverse_exit_v0,
)

from .current_productive_enter_live_29p_join_v1 import (
    CurrentProductiveEnterLive29PInjectedGetV1,
    _DoublePlaySizingDecisionV1,
    bind_double_play_sizing_input_v1,
    read_29p_free_margin_evidence_v1,
)
from .constants_v1 import NUMERIC_EQUITY_TTL_SECONDS
from .current_productive_treasury_single_source_capital_handoff_v1 import (
    build_full_core_margin_inputs_from_budget_owner_v1,
    execute_current_productive_treasury_single_source_capital_handoff_v1,
)
from .current_productive_mv2_capital_context_rebind_v1 import (
    build_current_productive_live_account_capital_context_v1,
)


@dataclass(frozen=True)
class DirectDoublePlayReversalV1:
    episode: PositionEpisodeIdentityV1
    selection_id: str
    selection_digest: str
    scope_digest: str
    position_snapshot_digest: str
    funding_digest: str
    budget_policy_digest: str
    old_reservation_id: str
    decision_epoch: str
    reference_mark: Decimal
    scope_distance: Decimal
    protective_stop: Decimal
    slot_capital_basis_usdc: Decimal
    portfolio_slot_capital_usdc: Decimal
    quote_to_usdc: Decimal
    current_contracts: Decimal
    target_contracts: Decimal
    target_notional_usdc: Decimal

    @property
    def signed_order_contracts(self) -> Decimal:
        return signed_position_delta(self.current_contracts, self.target_contracts)

    def to_dict_v1(self) -> dict:
        return {
            **{
                key: str(value) if isinstance(value, Decimal) else value
                for key, value in asdict(self).items()
            },
            "side": "buy" if self.target_contracts > 0 else "sell",
            "quantity_contracts": str(abs(self.signed_order_contracts)),
            "reduce_only": False,
            "submission_authorized": False,
        }

    def digest_v1(self) -> str:
        return canonical_digest_v1(self.to_dict_v1())

    @classmethod
    def from_dict_v1(cls, record):
        raw = {field.name: record[field.name] for field in fields(cls)}
        identity = dict(raw["episode"])
        identity["account_scope"] = PositionEpisodeScopeV1(**identity["account_scope"])
        raw["episode"] = PositionEpisodeIdentityV1(**identity)
        raw["episode"].validate_v1()
        for field in fields(cls):
            if field.type is Decimal:
                raw[field.name] = Decimal(raw[field.name])
                if not raw[field.name].is_finite():
                    raise ValueError("DIRECT_REVERSAL_NONFINITE_PLAN")
        result = cls(**raw)
        if result.to_dict_v1() != record or result.quote_to_usdc <= 0:
            raise ValueError("DIRECT_REVERSAL_PLAN_READBACK_MISMATCH")
        return result

    def apply_simulated_fill_v1(self, *, ledger, accounting, fill, budget_owner=None):
        """Apply one full offline fill of the retained net order."""
        from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
            ProductiveFuturesAccountingSessionV1,
        )
        from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import (
            SimulatedFillInputV1,
        )

        if (
            self.episode.account_scope.execution_environment != "INTERNAL_SIMULATED_EXECUTION"
            or type(accounting) is not ProductiveFuturesAccountingSessionV1
            or type(fill) is not SimulatedFillInputV1
            or ledger.get("state") != "COMPLETED"
            or ledger.get("direct_reversal_digest") != self.digest_v1()
            or ledger.get("direct_reversal") != self.to_dict_v1()
            or fill.fill_id != "direct-reversal:" + self.digest_v1()
            or fill.instrument_id != self.episode.venue_native_id
            or fill.mark_price != self.reference_mark
            or type(fill.event_time_unix) not in (int, float)
            or not math.isfinite(fill.event_time_unix)
            or not 0
            <= fill.event_time_unix - datetime.fromisoformat(self.decision_epoch).timestamp()
            <= NUMERIC_EQUITY_TTL_SECONDS
        ):
            raise ValueError("DIRECT_REVERSAL_SIMULATED_FILL_SOURCE_MISMATCH")
        if budget_owner is not None:
            return budget_owner.book_simulated_direct_reversal_v1(self, ledger, accounting, fill)
        return accounting.apply_simulated_net_reversal_v1(
            fill, current_contracts=self.current_contracts, target_contracts=self.target_contracts
        )


def assess_direct_double_play_reversal_v1(
    *,
    episode,
    bound,
    cursor_root,
    scope_binding,
    position,
    metadata,
    mark,
    epoch,
    recovery,
    owner,
    injected,
) -> DirectDoublePlayReversalV1:
    """Size the target exposure of a replacement, with the original hold still retained."""
    identity = episode.identity
    lane = identity.lane_id
    scope = read_occupied_scope_mark_snapshot_v1(Path(cursor_root))
    if (
        scope is None
        or scope["digest"] != scope_binding["scope_digest"]
        or scope["mark"].get("pending_reversal_episode_id") != identity.episode_id
        or scope["mark"]["seal_id"] != scope_binding["scope_seal_id"]
        or scope["snapshot"]["instrument_id"] != identity.instrument_id
    ):
        raise ValueError("DIRECT_REVERSAL_ORIGINAL_SCOPE_REQUIRED")
    if (
        type(recovery) is not HostBudgetRecoveryContextV1
        or owner is None
        or recovery.host.closed
        or recovery.host.owner is not owner
        or recovery.host.execution_environment != "INTERNAL_SIMULATED_EXECUTION"
        or identity.account_scope.execution_environment != recovery.host.execution_environment
        or identity.account_scope.account_identity != recovery.account
        or recovery.host.bindings.get(lane) != bound
        or recovery.pending_orders
    ):
        raise ValueError("DIRECT_REVERSAL_FUNDED_SIMULATED_SLOT_REQUIRED")
    decision_time = datetime.fromisoformat(epoch.replace("Z", "+00:00"))
    if decision_time.utcoffset() is None:
        raise ValueError("DIRECT_REVERSAL_DECISION_CLOCK_INVALID")
    observed = recovery.observed
    decision_unix = decision_time.timestamp()
    if not (
        0 <= decision_unix - observed.wall_time_unix <= observed.max_age_seconds
        and 0 <= decision_unix - observed.event_time_unix <= observed.max_age_seconds
    ):
        raise ValueError("DIRECT_REVERSAL_STALE_POSITION")
    mark.validate_against_cycle_inputs_v1(
        mark_px=mark.mark_px, index_px=mark.index_px, venue_native_id=bound.venue_native_id
    )
    mark_event = mark.require_current_mark_clock_v1(observed_unix=decision_unix)
    mark_digest = json.loads(mark.mark_clock_json)["payload_sha256"]
    if (
        mark_event < scope["mark"]["event_unix"]
        or mark_event == scope["mark"]["event_unix"]
        and mark_digest != scope["mark"]["mark_payload_sha256"]
    ):
        raise ValueError("DIRECT_REVERSAL_CURRENT_MARK_REQUIRED")
    quantity = position.quantity_observation
    direction = Decimal(1 if identity.position_side == "long" else -1)
    if (
        quantity is None
        or not quantity.quantity.is_finite()
        or quantity.quantity <= 0
        or quantity.lane_id != lane
        or quantity.venue_native_id != bound.venue_native_id
        or quantity.canonical_instrument_id != bound.instrument_id
        or quantity.position_side.value != identity.position_side
        or not any(
            p.instrument_id == bound.instrument_id
            and p.signed_quantity == direction * quantity.quantity
            for p in observed.positions
        )
    ):
        raise ValueError("DIRECT_REVERSAL_ORIGINAL_QUANTITY_REQUIRED")
    if metadata is None or not metadata.produced or metadata.constraints is None:
        raise ValueError("DIRECT_REVERSAL_INSTRUMENT_METADATA_REQUIRED")
    if (
        type(injected) is not CurrentProductiveEnterLive29PInjectedGetV1
        or injected.get_performed is not True
        or injected.http_status != 200
        or injected.payload is None
        or injected.error_class
        or injected.expected_account_identity != recovery.account
    ):
        raise ValueError("DIRECT_REVERSAL_FRESH_CAPITAL_REQUIRED")
    acquisition = datetime.fromisoformat(injected.observed_at.replace("Z", "+00:00"))
    if acquisition.utcoffset() is None:
        raise ValueError("DIRECT_REVERSAL_FRESH_CAPITAL_REQUIRED")
    age = (decision_time - acquisition).total_seconds()
    if not 0 <= age <= NUMERIC_EQUITY_TTL_SECONDS:
        raise ValueError("DIRECT_REVERSAL_FRESH_CAPITAL_REQUIRED")
    policy = owner.entry_budget_policy_v1()
    basis = owner.slot_capital_basis_v1(lane)
    if (
        not isinstance(policy, BoundedSlotEntryBudgetV1)
        or basis is None
        or basis.account_identity != recovery.account
        or basis.net_basis_usdc <= 0
    ):
        raise ValueError("DIRECT_REVERSAL_FUNDED_SIMULATED_SLOT_REQUIRED")
    commitments = owner.local_commitment_readback_v1()
    holds = [
        row
        for row in commitments.commitments
        if row.slot_id == lane and row.state in {"RESERVED", "COMMITTED"}
    ]
    previous = owner.latest_simulated_direct_reversal_v1(lane)
    previous_plan = DirectDoublePlayReversalV1.from_dict_v1(previous["plan"]) if previous else None
    if len(holds) != 1 or (
        holds[0].instrument_id != bound.instrument_id
        or holds[0].venue_native_id != bound.venue_native_id
        or (
            previous_plan is None
            and (
                not holds[0].canonical_quantity
                or Decimal(holds[0].canonical_quantity) != quantity.quantity
            )
        )
        or (
            previous_plan is not None
            and (
                previous_plan.old_reservation_id != holds[0].reservation_id
                or previous_plan.selection_digest != bound.selection_integrity_digest
                or previous_plan.target_contracts != direction * quantity.quantity
            )
        )
    ):
        raise ValueError("DIRECT_REVERSAL_ORIGINAL_HOLD_REQUIRED")
    hold = holds[0]
    side = "short" if direction > 0 else "long"
    reference = Decimal(str(mark.mark_px))
    scope_state = scope["snapshot"]["scope"]
    distance = Decimal(str(scope_state["d_t"]))
    stop = derive_protective_stop_price_from_adverse_exit_v0(
        selected_side=side, reference_price=reference, adverse_exit_distance=distance
    )
    if scope_state["valid"] is not True or stop is None:
        raise ValueError("DIRECT_REVERSAL_FULL_SCOPE_REQUIRED")

    observation = read_29p_free_margin_evidence_v1(
        payload=injected.payload,
        decision_epoch=epoch,
        observed_at=injected.observed_at,
        http_status=injected.http_status,
        body_sha256=injected.body_sha256,
        expected_uid=recovery.account,
        age_seconds=str(age),
    )
    handoff = execute_current_productive_treasury_single_source_capital_handoff_v1(
        margin_observation=observation,
        instrument_id=bound.instrument_id,
        body_sha256=observation.provenance_digest,
        fresh_pretrade_get_status=injected.fresh_pretrade_get_status,
        live_account_bound_status=injected.live_account_bound_status,
        u04_p01_host_inputs=build_full_core_margin_inputs_from_budget_owner_v1(
            raw_acct_lv=injected.raw_acct_lv,
            budget_owner=owner,
        ),
        clear_treasury_idempotency=True,
    )
    if handoff.fail_closed or handoff.step_29p_admissibility.risk_admissible is not True:
        raise ValueError("DIRECT_REVERSAL_FRESH_CAPITAL_REQUIRED")
    recovery.recover_v1(owner, handoff.producer_output)
    facts = dict(capital_context_facts_v1(owner, slot_id=lane))
    # This is the resulting exposure of one net order. Keep the current
    # outstanding cash obligations and credit neither a fill nor released funds.
    facts["current_reconciled_exposure"] -= hold.amount
    # Initial allocation limits govern funding. The next exposure uses the
    # settled balances of the funded slots, subject to fresh account capital.
    slot_capital = basis.net_basis_usdc
    portfolio_capital = sum(
        (
            max(Decimal(0), owner.slot_capital_basis_v1(slot).net_basis_usdc)
            for slot in recovery.host.bindings
        ),
        Decimal(0),
    )
    facts.update(
        slot_remaining_notional=slot_capital,
        entry_notional_ceiling=slot_capital,
        aggregate_notional_ceiling=portfolio_capital,
    )
    money = build_capital_risk_sizing_monetary_context_v1(
        decision_epoch=epoch,
        observed_at=injected.observed_at,
        fresh_pretrade_get_status=injected.fresh_pretrade_get_status,
        account_equity_amount=facts["account_equity"],
        account_equity_currency="USDC",
        native_reference_price=reference,
        native_protective_stop_price=stop,
        instruments_payload=injected.instruments_payload,
        venue_native_id=bound.venue_native_id,
        index_tickers_payload=injected.index_tickers_payload,
        conversion_pair_instruments_payload=injected.conversion_pair_instruments_payload,
    )
    equity, canonical_reference, canonical_stop = crs_operands_from_monetary_context_v1(money)
    context = build_current_productive_live_account_capital_context_v1(
        instrument_id=bound.instrument_id,
        typed_account_equity=equity,
        reference_price=canonical_reference,
        protective_stop_price=canonical_stop,
        instrument_constraints=metadata.constraints,
    )
    context = replace(context, scope_capital_limit=min(context.scope_capital_limit, slot_capital))
    decision = _DoublePlaySizingDecisionV1(
        "l10-reversal:" + scope["digest"],
        canonical_digest_v1(
            {
                "scope": scope["digest"],
                "mark": mark_digest,
                "epoch": epoch,
                "budget": policy.digest_v1(),
                "funding": basis.to_dict(),
                "position": quantity.snapshot_digest,
                "hold": commitments.generation_digest,
            }
        ),
        bound.instrument_id,
        side,
        "enter_" + side,
    )
    sizing = evaluate_capital_risk_sizing_v1(
        apply_capital_context_facts_v1(
            bind_double_play_sizing_input_v1(decision=decision, capital_context=context), facts
        )
    )
    if (
        sizing.outcome is not CapitalRiskSizingOutcome.PASS
        or sizing.canonical_position_sizing is None
    ):
        raise ValueError(sizing.reason_codes[-1])
    if metadata.constraints.maximum_quantity is not None and (
        quantity.quantity + sizing.final_quantity > metadata.constraints.maximum_quantity
    ):
        raise ValueError("DIRECT_REVERSAL_DELTA_ABOVE_INSTRUMENT_LIMIT")
    return DirectDoublePlayReversalV1(
        identity,
        bound.selection_id,
        bound.selection_integrity_digest,
        scope["digest"],
        quantity.snapshot_digest,
        basis.allocation_digest,
        policy.digest_v1(),
        hold.reservation_id,
        epoch,
        reference,
        distance,
        stop,
        slot_capital,
        portfolio_capital,
        canonical_reference / reference,
        direction * quantity.quantity,
        -direction * sizing.final_quantity,
        sizing.canonical_position_sizing.resulting_notional,
    )
