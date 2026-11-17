"""Assess a single net order for the occupied slot's sealed L10 switch."""

from dataclasses import asdict, dataclass, field, fields, replace
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
from typing import TYPE_CHECKING

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
    PortfolioCapitalBudgetError,
    apply_capital_context_facts_v1,
    capital_context_facts_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import HostBudgetRecoveryContextV1
from src.ops.portfolio_capital_reservation_budget_v1.slot_loss_budget_v1 import SlotCapitalBasisV1
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


if TYPE_CHECKING:
    from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
        IsolatedLaneSlotV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
        AuthenticatedEntryEpisodeRequestV1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

    from .final_order_envelope_v1 import FinalOrderEnvelopeV1


DIRECT_DOUBLE_PLAY_REVERSAL = "DIRECT_DOUBLE_PLAY_REVERSAL"


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
    authenticated_entry=None,
) -> DirectDoublePlayReversalV1:
    """Size the target exposure of a replacement, with the original hold still retained."""
    identity = episode.identity
    lane = identity.lane_id
    live = identity.account_scope.execution_environment == "LIVE"
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
        or recovery.host.execution_environment not in {"INTERNAL_SIMULATED_EXECUTION", "LIVE"}
        or identity.account_scope.execution_environment != recovery.host.execution_environment
        or identity.account_scope.account_identity != recovery.account
        or recovery.host.bindings.get(lane) != bound
        or recovery.pending_orders
    ):
        raise ValueError("DIRECT_REVERSAL_ORIGINAL_HOST_REQUIRED")
    if live:
        from src.ops.execution_reconciliation_get_provenance_v1 import (
            AuthenticatedReconciliationGetV1,
        )
        from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
            AuthenticatedEntryEpisodeRequestV1,
        )
        from .current_productive_venue_plan_td_mode_and_order_environment_authority_v1 import (
            resolve_current_productive_venue_plan_td_mode_v1,
        )

        if (
            type(authenticated_entry) is not AuthenticatedEntryEpisodeRequestV1
            or authenticated_entry.proof.identity_digest != identity.episode_id
        ):
            raise ValueError("DIRECT_REVERSAL_AUTHENTICATED_ENTRY_REQUIRED")
        proof = authenticated_entry.proof
        link = recovery.inspect_current_authenticated_entry_v1(lane_id=lane, proof=proof)
        source = recovery.authenticated_reconciliation
        if (
            type(source) is not AuthenticatedReconciliationGetV1
            or source.transport is not recovery.host.reconciliation_transport
            or source.evidence.get(proof.reservation_id) != proof
            or source.account_position_mode != "net_mode"
            or link["reconciliation"]["reservation_released"] is not False
        ):
            raise ValueError("DIRECT_REVERSAL_AUTHENTICATED_ENTRY_REQUIRED")
        margin_modes = source.position_margin_modes.get(proof.reservation_id, ())
        resolve_current_productive_venue_plan_td_mode_v1(
            conformance_required=True,
            observed_td_mode=link["envelope"]["td_mode"],
            observed_mgn_mode=margin_modes[0] if len(margin_modes) == 1 else None,
        )
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
    basis = (
        owner.live_reversal_slot_basis_v1(
            slot_id=lane, reservation_id=authenticated_entry.proof.reservation_id, bound=bound
        )
        if live
        else owner.slot_capital_basis_v1(lane)
    )
    if (
        type(basis) is not SlotCapitalBasisV1
        or basis.slot_id != lane
        or basis.account_identity != recovery.account
        or not basis.funding_observation_id
        or not basis.allocation_digest
        or not basis.net_basis_usdc.is_finite()
        or basis.net_basis_usdc <= 0
    ):
        raise ValueError(
            "DIRECT_REVERSAL_FUNDED_LIVE_SLOT_REQUIRED"
            if live
            else "DIRECT_REVERSAL_FUNDED_SIMULATED_SLOT_REQUIRED"
        )
    if not live and not isinstance(policy, BoundedSlotEntryBudgetV1):
        raise ValueError("DIRECT_REVERSAL_FUNDED_SIMULATED_SLOT_REQUIRED")
    commitments = owner.local_commitment_readback_v1()
    holds = [
        row
        for row in commitments.commitments
        if row.slot_id == lane and row.state in {"RESERVED", "COMMITTED"}
    ]
    if len(holds) != 1:
        raise ValueError("DIRECT_REVERSAL_ORIGINAL_HOLD_REQUIRED")
    hold = holds[0]
    if live and (
        hold.state != "COMMITTED" or hold.reservation_id != authenticated_entry.proof.reservation_id
    ):
        raise ValueError("DIRECT_REVERSAL_ORIGINAL_HOLD_REQUIRED")
    previous = (
        None
        if live
        else owner.latest_simulated_direct_reversal_v1(lane, reservation_id=hold.reservation_id)
    )
    live_booking = owner.read_authenticated_net_reversal_v1(hold.reservation_id) if live else None
    previous_plan = DirectDoublePlayReversalV1.from_dict_v1(previous["plan"]) if previous else None
    if (
        hold.instrument_id != bound.instrument_id
        or hold.venue_native_id != bound.venue_native_id
        or (
            previous_plan is None
            and live_booking is None
            and (
                not hold.canonical_quantity or Decimal(hold.canonical_quantity) != quantity.quantity
            )
        )
        or (
            live_booking is not None
            and (
                live_booking["envelope_digest"] != identity.episode_id
                or live_booking["selection_digest"] != bound.selection_integrity_digest
                or Decimal(live_booking["position_contracts"]) != direction * quantity.quantity
            )
        )
        or (
            previous_plan is not None
            and (
                previous_plan.old_reservation_id != hold.reservation_id
                or previous_plan.selection_digest != bound.selection_integrity_digest
                or previous_plan.target_contracts != direction * quantity.quantity
            )
        )
    ):
        raise ValueError("DIRECT_REVERSAL_ORIGINAL_HOLD_REQUIRED")
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
    slot_capital = (
        basis.net_basis_usdc
        if live
        else owner.direct_reversal_basis_v1(lane, hold.reservation_id, epoch)
    )
    portfolio_capital = (
        slot_capital
        if live
        else sum(
            (
                max(Decimal(0), owner.slot_capital_basis_v1(slot).net_basis_usdc)
                for slot in recovery.host.bindings
            ),
            Decimal(0),
        )
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
    budget_digest = policy.digest_v1() if policy is not None else basis.allocation_digest
    funding_digest = canonical_digest_v1(basis.to_dict()) if live else basis.allocation_digest
    decision = _DoublePlaySizingDecisionV1(
        "l10-reversal:" + scope["digest"],
        canonical_digest_v1(
            {
                "scope": scope["digest"],
                "mark": mark_digest,
                "epoch": epoch,
                "budget": budget_digest,
                "funding": basis.to_dict(),
                **({"account_observation": observation.provenance_digest} if live else {}),
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
        funding_digest,
        budget_digest,
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


def prepare_authenticated_net_reversal_order_v1(
    reversal: DirectDoublePlayReversalV1, *, bound, injected, cycle_id: str
) -> dict:
    """Prepare the exact OKX order before any execution admission."""
    from .current_productive_n1_venue_quantity_limit_admission_v1 import (
        assess_n1_final_plan_venue_quantity_v1,
    )
    from .current_productive_venue_plan_td_mode_and_order_environment_authority_v1 import (
        resolve_current_productive_venue_plan_td_mode_v1,
    )
    from .final_order_envelope_v1 import bind_final_order_envelope_from_venue_plan_v1
    from .models_v1 import VenuePlanCandidateV1

    episode = reversal.episode
    if (
        episode.account_scope.execution_environment != "LIVE"
        or not reversal.current_contracts.is_finite()
        or not reversal.target_contracts.is_finite()
        or reversal.current_contracts * reversal.target_contracts >= 0
        or (episode.instrument_id, episode.venue_native_id, reversal.selection_digest)
        != (bound.instrument_id, bound.venue_native_id, bound.selection_integrity_digest)
    ):
        raise ValueError("DIRECT_REVERSAL_ORDER_SOURCE_MISMATCH")
    delta = reversal.signed_order_contracts
    digest = reversal.digest_v1()
    side = "buy" if delta > 0 else "sell"
    quantity = format(abs(delta), "f")
    td_mode = resolve_current_productive_venue_plan_td_mode_v1(conformance_required=False)
    client_order_id = "ptdpr" + digest[:27]
    payload = {
        "instId": episode.venue_native_id,
        "side": side,
        "sz": quantity,
        "ordType": "market",
        "tdMode": td_mode,
        "posSide": "net",
        "clOrdId": client_order_id,
    }
    plan = VenuePlanCandidateV1(
        instrument_id=episode.venue_native_id,
        side=side,
        quantity=quantity,
        order_type="market",
        td_mode=td_mode,
        reduce_only=False,
        clordid=client_order_id,
        venue_native_payload=payload,
        quantity_source="L10_TARGET_MINUS_AUTHENTICATED_POSITION",
        side_source="L10_SIGNED_NET_DELTA",
        instrument_source="ORIGINAL_OCCUPIED_SLOT",
        path_kind=DIRECT_DOUBLE_PLAY_REVERSAL,
        environment="LIVE",
    )
    limits = injected.venue_quantity_limits
    acquisition = json.loads(injected.acquisition_decision_id or "null")
    if not isinstance(acquisition, dict) or acquisition.get("cycle_id") != cycle_id:
        raise ValueError("DIRECT_REVERSAL_ORDER_ACQUISITION_MISMATCH")
    decision_time = datetime.fromisoformat(reversal.decision_epoch)
    acquisition_time = datetime.fromisoformat(acquisition["decision_epoch"].replace("Z", "+00:00"))
    if not 0 <= (decision_time - acquisition_time).total_seconds() <= NUMERIC_EQUITY_TTL_SECONDS:
        raise ValueError("DIRECT_REVERSAL_ORDER_ACQUISITION_STALE")
    admission = assess_n1_final_plan_venue_quantity_v1(
        observation=limits,
        plan=plan,
        bound_instrument=bound,
        account_identity=episode.account_scope.account_identity,
        decision_epoch=acquisition["decision_epoch"],
        cycle_id=cycle_id,
        evaluated_at_utc=reversal.decision_epoch,
    )
    if not admission.allowed:
        raise ValueError(admission.reason_codes[0])
    envelope = bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref=(
            f"direct-reversal:{episode.lane_id}:portfolio-reservation:{reversal.old_reservation_id}"
        ),
        provenance_ref=digest,
        creation_epoch=reversal.decision_epoch,
    )
    return {
        "envelope": envelope.to_runtime_json_v1(),
        "venue_quantity_admission": admission.to_dict(),
    }


def _net_reversal_submit_root_v1(host_root: Path, episode_id: str) -> Path:
    if len(episode_id) != 64 or any(c not in "0123456789abcdef" for c in episode_id):
        raise ValueError("POST_AUTHORITY_ORIGINAL_REVERSAL_EPISODE_REQUIRED")
    root = host_root / "position-episodes" / episode_id / "net-reversal-submit"
    if root.resolve() != root or not root.parent.is_dir():
        raise ValueError("POST_AUTHORITY_ORIGINAL_REVERSAL_STORE_REQUIRED")
    return root


def _read_retained_net_reversal_v1(lane_pair, scope):
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
        _occupied_close_attempt_root_v1,
        bind_occupied_lane_governed_cycle_store_roots_v1,
    )

    from .current_productive_governed_cycle_orchestrator_v1 import _load_ledger
    from .final_order_envelope_v1 import FinalOrderEnvelopeV1, assert_envelope_unmodified_v1

    slot, bound = lane_pair
    lane = slot.lane_id
    _, _, evidence = bind_occupied_lane_governed_cycle_store_roots_v1({lane: lane_pair})[lane]
    ledger_root = _occupied_close_attempt_root_v1(
        evidence, cycle_id=scope["mark"]["cycle_id"], lane_id=lane, authenticated=True
    )
    ledger = _load_ledger(ledger_root)
    if (
        ledger.get("state") != "COMPLETED"
        or ledger.get("terminal_class") != "POSITION_MANAGEMENT_REVERSAL_ASSESSED"
    ):
        raise ValueError("POST_AUTHORITY_ORIGINAL_REVERSAL_ORDER_REQUIRED")
    reversal = DirectDoublePlayReversalV1.from_dict_v1(ledger["direct_reversal"])
    envelope = FinalOrderEnvelopeV1(**ledger["direct_reversal_order"]["envelope"])
    assert_envelope_unmodified_v1(envelope)
    delta = reversal.signed_order_contracts
    target_side = "long" if delta > 0 else "short"
    if (
        envelope.path_kind != DIRECT_DOUBLE_PLAY_REVERSAL
        or envelope.reduce_only
        or envelope.pos_side != "net"
        or envelope.order_type != "market"
        or envelope.price
        or envelope.quantity_unit != "CONTRACTS"
        or envelope.instrument_id != bound.venue_native_id
        or envelope.side != ("buy" if delta > 0 else "sell")
        or reversal.current_contracts * reversal.target_contracts >= 0
        or Decimal(envelope.quantity) != abs(delta)
        or envelope.provenance_ref != reversal.digest_v1()
        or envelope.admission_ref
        != f"direct-reversal:{lane}:portfolio-reservation:{reversal.old_reservation_id}"
        or envelope.creation_epoch != reversal.decision_epoch
        or ledger["direct_reversal_digest"] != reversal.digest_v1()
        or ledger["direct_reversal_order"]["venue_quantity_admission"]["allowed"] is not True
        or reversal.scope_digest != scope["digest"]
        or reversal.scope_distance != Decimal(str(scope["snapshot"]["scope"]["d_t"]))
        or reversal.protective_stop
        != derive_protective_stop_price_from_adverse_exit_v0(
            selected_side=target_side,
            reference_price=reversal.reference_mark,
            adverse_exit_distance=reversal.scope_distance,
        )
        or reversal.episode.episode_id != scope["mark"]["pending_reversal_episode_id"]
        or reversal.episode.lane_id != lane
        or reversal.episode.instrument_id != bound.instrument_id
        or reversal.episode.venue_native_id != bound.venue_native_id
        or reversal.selection_digest != bound.selection_integrity_digest
    ):
        raise ValueError("POST_AUTHORITY_ORIGINAL_REVERSAL_ORDER_MISMATCH")
    return reversal, envelope


def _inspect_original_reversal_hold_v1(owner, bound, reversal):
    basis = owner.live_reversal_slot_basis_v1(
        slot_id=reversal.episode.lane_id, reservation_id=reversal.old_reservation_id, bound=bound
    )
    if (
        basis is None
        or canonical_digest_v1(basis.to_dict()) != reversal.funding_digest
        or basis.net_basis_usdc != reversal.slot_capital_basis_usdc
    ):
        raise ValueError("POST_AUTHORITY_REVERSAL_SLOT_CAPITAL_CHANGED")


@dataclass(frozen=True)
class CurrentPostNetReversalContextV1:
    lane_pair: tuple["IsolatedLaneSlotV1", "BoundInstrumentV1"]
    recovery: HostBudgetRecoveryContextV1 = field(repr=False)
    authenticated_entry: "AuthenticatedEntryEpisodeRequestV1" = field(repr=False)
    reversal: DirectDoublePlayReversalV1
    envelope: "FinalOrderEnvelopeV1"

    def store_root_v1(self) -> Path:
        return _net_reversal_submit_root_v1(
            self.recovery.host.root, self.reversal.episode.episode_id
        )

    def inspect_position_v1(self) -> None:
        from src.ops.execution_reconciliation_get_provenance_v1 import (
            AuthenticatedReconciliationGetV1,
        )
        from src.ops.gates.risk_gate import canonical_kill_switch_state_path
        from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
            AuthenticatedEntryEpisodeRequestV1,
        )

        slot, bound = self.lane_pair
        lane = slot.lane_id
        recovery = self.recovery
        if (
            type(recovery) is not HostBudgetRecoveryContextV1
            or type(self.authenticated_entry) is not AuthenticatedEntryEpisodeRequestV1
        ):
            raise ValueError("POST_AUTHORITY_ORIGINAL_REVERSAL_CONTEXT_REQUIRED")
        host = recovery.host
        proof = self.authenticated_entry.proof
        reversal, envelope = self.reversal, self.envelope
        scope = read_occupied_scope_mark_snapshot_v1(Path(slot.lane_state_root))
        if (
            host.bindings != {lane: bound}
            or scope is None
            or scope["mark"].get("pending_reversal_episode_id") != proof.identity_digest
            or reversal.old_reservation_id != proof.reservation_id
            or host.execution_incident_state_path is None
            or Path(canonical_kill_switch_state_path()).resolve()
            != Path(host.execution_incident_state_path).resolve()
            or _read_retained_net_reversal_v1(self.lane_pair, scope) != (reversal, envelope)
        ):
            raise ValueError("POST_AUTHORITY_ORIGINAL_REVERSAL_SCOPE_REQUIRED")
        entry = recovery.inspect_current_authenticated_entry_v1(lane_id=lane, proof=proof)
        source = recovery.authenticated_reconciliation
        epoch = datetime.fromisoformat(reversal.decision_epoch)
        now = host.clock()
        raw_position = json.dumps(
            recovery.occupancy_payloads.get("POSITIONS"),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        if (
            type(source) is not AuthenticatedReconciliationGetV1
            or source.transport is not host.reconciliation_transport
            or source.evidence.get(proof.reservation_id) != proof
            or source.account_position_mode != "net_mode"
            or source.position_margin_modes.get(proof.reservation_id) != (envelope.td_mode,)
            or entry["envelope"]["td_mode"] != envelope.td_mode
            or entry["reconciliation"]["reservation_released"] is not False
            or reversal.episode.account_scope.execution_environment != "LIVE"
            or reversal.episode.account_scope.account_identity != recovery.account
            or host.expected_account_identity != recovery.account
            or any(
                not 0 <= now - stamp <= recovery.observed.max_age_seconds
                for stamp in (
                    epoch.timestamp(),
                    recovery.observed.event_time_unix,
                    recovery.observed.wall_time_unix,
                )
            )
            or tuple((p.instrument_id, p.signed_quantity) for p in recovery.observed.positions)
            != ((bound.instrument_id, reversal.current_contracts),)
            or sha256(raw_position.encode()).hexdigest() != reversal.position_snapshot_digest
        ):
            raise ValueError("POST_AUTHORITY_REVERSAL_CURRENT_POSITION_UNPROVEN")
        _inspect_original_reversal_hold_v1(host.owner, bound, reversal)


def prepare_authenticated_net_reversal_post_v1(
    *,
    lane_pair,
    recovery,
    authenticated_entry,
    authorization,
    baseline_origin_main_sha,
    execution_integrity_backend=None,
):
    """Consume the scoped grant and reserve a single PRE_SOCKET attempt."""
    _, _, attempt, _ = _prepare_authenticated_net_reversal_post_v1(
        lane_pair=lane_pair,
        recovery=recovery,
        authenticated_entry=authenticated_entry,
        authorization=authorization,
        baseline_origin_main_sha=baseline_origin_main_sha,
        execution_integrity_backend=execution_integrity_backend,
    )
    return attempt


def _prepare_authenticated_net_reversal_post_v1(
    *,
    lane_pair,
    recovery,
    authenticated_entry,
    authorization,
    baseline_origin_main_sha,
    execution_integrity_backend=None,
):
    """Bind the retained order, grant and original attempt for dispatch."""
    from src.governance.current_productive_real_venue_post_admission_v1 import (
        evaluate_real_venue_post_admission_v1,
    )
    from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.lifecycle_lock_v1 import (
        AuthorizationLifecycleLockV1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.pre_live_fresh_runtime_root_isolation_v1 import (
        assert_post_durable_store_root_isolation_v1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
        AuthenticatedEntryEpisodeRequestV1,
    )
    from .current_productive_actual_venue_post_baseline_v1 import (
        resolve_and_assert_live_post_execution_baseline_v1,
    )
    from .current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
        POST_OWNER_GO,
        load_durable_post_owner_go_consume_v1,
        persist_durable_post_owner_go_consume_v1,
    )
    from .current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
        assert_one_shot_join_permit_constraints_v1,
        mint_current_productive_one_shot_post_permit_v1,
        prove_one_shot_join_standing_boundary_v1,
    )
    from .current_productive_post_safety_veto_v1 import resolve_current_post_safety_context_v1
    from .current_productive_shared_post_owner_authority_v1 import SharedPostOwnerAuthorizationV1
    from .external_effect_permit_durable_consume_v1 import (
        DURABLE_STATE_SENT_INITIATED,
        claim_original_permit_transport_attempt_v1,
        load_external_effect_durable_consume_v1,
        persist_external_effect_durable_consume_v1,
    )

    if (
        type(recovery) is not HostBudgetRecoveryContextV1
        or type(authenticated_entry) is not AuthenticatedEntryEpisodeRequestV1
        or type(authorization) is not SharedPostOwnerAuthorizationV1
    ):
        raise ValueError("POST_AUTHORITY_ORIGINAL_REVERSAL_CONTEXT_REQUIRED")
    prove_one_shot_join_standing_boundary_v1()
    slot, bound = lane_pair
    lane = slot.lane_id
    host = recovery.host
    proof = authenticated_entry.proof
    live_sha = resolve_and_assert_live_post_execution_baseline_v1(
        declared_baseline_origin_main_sha=baseline_origin_main_sha,
        integrity_backend=execution_integrity_backend,
    )
    scope = read_occupied_scope_mark_snapshot_v1(Path(slot.lane_state_root))
    if (
        host.repository_sha != live_sha
        or host.bindings != {lane: bound}
        or scope is None
        or scope["mark"].get("pending_reversal_episode_id") != proof.identity_digest
    ):
        raise ValueError("POST_AUTHORITY_ORIGINAL_REVERSAL_SCOPE_REQUIRED")
    reversal, envelope = _read_retained_net_reversal_v1(lane_pair, scope)
    if reversal.old_reservation_id != proof.reservation_id:
        raise ValueError("POST_AUTHORITY_ORIGINAL_REVERSAL_ORDER_MISMATCH")
    root = _net_reversal_submit_root_v1(host.root, proof.identity_digest)
    assert_post_durable_store_root_isolation_v1(store_root=root)
    safety = resolve_current_post_safety_context_v1(envelope, stage="BEFORE_NET_REVERSAL_ADMISSION")
    if (
        host.execution_incident_state_path is None
        or Path(safety.state_path) != Path(host.execution_incident_state_path).resolve()
    ):
        raise ValueError("POST_AUTHORITY_REVERSAL_SAFETY_SOURCE_MISMATCH")

    context = CurrentPostNetReversalContextV1(
        lane_pair, recovery, authenticated_entry, reversal, envelope
    )

    lock = AuthorizationLifecycleLockV1.for_evidence_root(
        evidence_root=root,
        authorization_id=proof.identity_digest,
        owner=DIRECT_DOUBLE_PLAY_REVERSAL,
    )
    lock.acquire()
    try:
        if (
            load_durable_post_owner_go_consume_v1(store_root=root).get("consumed")
            or load_external_effect_durable_consume_v1(store_root=root)["durable_consumed"]
        ):
            raise ValueError("POST_AUTHORITY_REVERSAL_ALREADY_CONSUMED")
        context.inspect_position_v1()
        veto = safety.inspect_v1(stage="BEFORE_NET_REVERSAL_POST_GO")
        permit = mint_current_productive_one_shot_post_permit_v1(envelope, veto=veto)
        assert_one_shot_join_permit_constraints_v1(permit, envelope)
        claim = authorization.consume_v1(
            account=recovery.account,
            action=DIRECT_DOUBLE_PLAY_REVERSAL,
            envelope_digest=envelope.envelope_digest,
            attempt_root=root,
        )
        persist_durable_post_owner_go_consume_v1(
            store_root=root,
            owner_go_token=POST_OWNER_GO,
            baseline_origin_main_sha=live_sha,
            shared_post_owner_claim_digest=claim.receipt_digest_v1(),
        )
        admission = evaluate_real_venue_post_admission_v1(
            post_owner_go=POST_OWNER_GO,
            one_shot_real_post=True,
            permit=permit,
            store_root=root,
            shared_post_owner_claim_digest=claim.receipt_digest_v1(),
        )
        if not admission.post_admission_granted:
            raise ValueError(
                "POST_AUTHORITY_REVERSAL_ADMISSION_DENIED:" + ",".join(admission.reason_codes)
            )
        persist_external_effect_durable_consume_v1(
            store_root=root,
            permit=permit,
            envelope=envelope,
            durable_state=DURABLE_STATE_SENT_INITIATED,
            post_count=0,
            outcome="DIRECT_REVERSAL_PRE_SOCKET",
        )
        attempt = claim_original_permit_transport_attempt_v1(
            store_root=root,
            permit_id=permit.permit_id,
            envelope_id=envelope.envelope_id,
            envelope_digest=envelope.envelope_digest,
        )
        try:
            safety.inspect_v1(stage="NET_REVERSAL_PRE_SOCKET")
            context.inspect_position_v1()
            claim.recheck_v1()
        except (ValueError, RuntimeError, OSError):
            attempt.abort_before_transport_v1(
                reason_code="POST_AUTHORITY_REVERSAL_PRE_SOCKET_CHANGED"
            )
            raise
        return context, safety, attempt, claim
    finally:
        lock.release()


@dataclass(frozen=True)
class AuthenticatedNetReversalReadbackV1:
    episode_id: str
    envelope_digest: str
    client_order_id: str
    reservation_id: str
    transport_phase: str
    outcome: str
    booking_digest: str | None = None
    reconciliation_blocker: str | None = None


def recover_submitted_net_reversal_v1(*, lane_pair, get_budget_host, proof_root=None):
    """Recover the original unresolved attempt before any startup reconciliation."""
    from .current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
        POST_OWNER_GO,
        SHARED_POST_OWNER_CLAIM_FIELD,
        load_durable_post_owner_go_consume_v1,
    )
    from .external_effect_permit_durable_consume_v1 import (
        DURABLE_STATE_COMPLETED,
        load_external_effect_durable_consume_v1,
    )

    slot, bound = lane_pair
    scope = read_occupied_scope_mark_snapshot_v1(Path(slot.lane_state_root))
    episode_id = scope["mark"].get("pending_reversal_episode_id") if scope is not None else None
    if episode_id is None:
        return None
    budget_host = get_budget_host()
    root = _net_reversal_submit_root_v1(budget_host.root, episode_id)
    send = load_external_effect_durable_consume_v1(store_root=root)
    mandate = load_durable_post_owner_go_consume_v1(store_root=root)
    if not send["present"] and not mandate["present"]:
        return None
    reversal, envelope = _read_retained_net_reversal_v1(lane_pair, scope)
    if (
        reversal.episode.account_scope
        != PositionEpisodeScopeV1(budget_host.expected_account_identity, "LIVE")
        or mandate["owner_go_token"] != POST_OWNER_GO
        or not mandate["record"].get(SHARED_POST_OWNER_CLAIM_FIELD)
    ):
        raise ValueError("NET_REVERSAL_ORIGINAL_MANDATE_UNPROVEN")
    original_sha = mandate["record"]["baseline_origin_main_sha"]
    if (
        original_sha != budget_host.repository_sha
        and subprocess.run(
            ["git", "merge-base", "--is-ancestor", original_sha, budget_host.repository_sha],
            cwd=Path(__file__).resolve().parents[3],
            capture_output=True,
            check=False,
        ).returncode
        != 0
    ):
        raise ValueError("NET_REVERSAL_ORIGINAL_MANDATE_REVISION_UNPROVEN")
    record = send["record"]
    phase, outcome = "UNCLAIMED", "SUBMIT_NOT_PROVEN"
    if record is not None:
        if (
            send["durable_consumed"] is not True
            or record["authority_ref"] != POST_OWNER_GO
            or (record["envelope_id"], record["envelope_digest"])
            != (envelope.envelope_id, envelope.envelope_digest)
        ):
            raise ValueError("NET_REVERSAL_ORIGINAL_SUBMIT_IDENTITY_UNPROVEN")
        phase = record.get("transport_attempt", {}).get("phase", "UNCLAIMED")
        if phase == "MAY_HAVE_SENT":
            outcome = (
                record["outcome"]
                if record["durable_state"] == DURABLE_STATE_COMPLETED
                else "UNKNOWN"
            )
    owner = budget_host.recover_owner_for_occupied_execution_v1(
        {slot.lane_id: bound}, operation="NET_REVERSAL_RECOVERY"
    )
    link = owner.execution_links_v1(active_only=True).get(reversal.old_reservation_id)
    if link is None or link["reconciliation"]["reservation_released"] is not False:
        raise ValueError("NET_REVERSAL_ORIGINAL_HOLD_UNPROVEN")
    result = AuthenticatedNetReversalReadbackV1(
        episode_id,
        envelope.envelope_digest,
        envelope.client_order_id,
        reversal.old_reservation_id,
        phase,
        outcome,
    )
    booking = owner.read_authenticated_net_reversal_v1(
        reversal.old_reservation_id, envelope_digest=envelope.envelope_digest
    )
    if booking is not None:
        if phase != "MAY_HAVE_SENT" or booking["previous_episode_id"] != episode_id:
            raise ValueError("NET_REVERSAL_BOOKED_ATTEMPT_MISMATCH")
        if proof_root is not None:
            from src.ops.execution_reconciliation_proof_store_v1 import (
                require_booked_net_reversal_readback_v1,
            )

            require_booked_net_reversal_readback_v1(root=proof_root, booking=booking)
        return replace(result, booking_digest=booking["booking_digest"])
    previous = owner.read_authenticated_net_reversal_v1(reversal.old_reservation_id)
    expected_episode = (
        previous["envelope_digest"]
        if previous is not None
        else link["reconciliation"]["identity_digest"]
    )
    if expected_episode != episode_id:
        raise ValueError("NET_REVERSAL_ORIGINAL_HOLD_UNPROVEN")
    _inspect_original_reversal_hold_v1(owner, bound, reversal)
    if (
        phase != "MAY_HAVE_SENT"
        or proof_root is None
        or budget_host.reconciliation_transport is None
    ):
        return result
    try:
        booking = _reconcile_original_net_reversal_v1(
            host=budget_host,
            proof_root=proof_root,
            lane_pair=lane_pair,
            scope=scope,
            plan=reversal,
            envelope=envelope,
            record=record,
            previous=previous,
            submit_root=root,
        )
    except PortfolioCapitalBudgetError:
        raise
    except (ValueError, OSError, KeyError, TypeError, ArithmeticError) as exc:
        return replace(result, reconciliation_blocker=str(exc))
    return replace(result, booking_digest=booking["booking_digest"])


def _reconcile_original_net_reversal_v1(
    *, host, proof_root, lane_pair, scope, plan, envelope, record, previous, submit_root
):
    from src.ops.execution_reconciliation_proof_store_v1 import (
        find_authenticated_entry_sources_v1,
        publish_authenticated_net_reversal_readback_v1,
    )

    from .current_productive_net_reversal_reconciliation_v1 import (
        collect_authenticated_net_reversal_fill_v1,
        collect_reversal_settlement_v1,
    )
    from .current_productive_l10_close_reconciliation_v1 import _utc_ms
    from .external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )
    from .productive_read_only_get_transport_v1 import FullCoreProductiveReadOnlyGetError

    if previous is None:
        candidates = {}
        raw_digest = plan.position_snapshot_digest
        for candidate in find_authenticated_entry_sources_v1(
            root=proof_root,
            budget_owner_root=host.root / "owner",
            account=host.account,
            reservation_id=plan.old_reservation_id,
            episode_id=plan.episode.episode_id,
        ):
            payload = candidate.snapshot.positions_observation["response"]
            canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
            if sha256(canonical.encode()).hexdigest() == raw_digest:
                (position,) = payload["data"]
                candidates[canonical] = position
        if len(candidates) != 1:
            raise ValueError("NET_REVERSAL_ORIGINAL_POSITION_EVIDENCE_UNPROVEN")
        old_position = next(iter(candidates.values()))
        previously_booked_fee = Decimal(0)
    else:
        old_position = {
            "posId": previous["position_id"],
            "cTime": previous["position_created_ms"],
            "uTime": previous["position_updated_ms"],
            "fee": previous["position_fee"],
            "ccy": previous["settlement_currency"],
            "instType": "SWAP" if previous["native_id"].endswith("-SWAP") else "FUTURES",
        }
        previously_booked_fee = Decimal(previous["position_fee"])
    try:
        source, fill, reads, bodies = collect_authenticated_net_reversal_fill_v1(
            transport=host.reconciliation_transport,
            clock=host.clock,
            plan=plan,
            envelope=envelope,
            record=record,
        )
        native_net, history_read, history_body = collect_reversal_settlement_v1(
            source=source,
            fill=fill,
            plan=plan,
            envelope=envelope,
            old_position=old_position,
            socket_ms=_utc_ms(record["transport_attempt"]["socket_boundary_at_utc"]),
            previously_booked_fee=previously_booked_fee,
        )
    except FullCoreProductiveReadOnlyGetError as exc:
        raise ValueError(str(exc)) from exc
    if read_occupied_scope_mark_snapshot_v1(Path(lane_pair[0].lane_state_root)) != scope:
        raise ValueError("NET_REVERSAL_ORIGINAL_SCOPE_CHANGED")
    if load_external_effect_durable_consume_v1(store_root=submit_root)["record"] != record:
        raise ValueError("NET_REVERSAL_ORIGINAL_SUBMIT_CHANGED")
    digest = publish_authenticated_net_reversal_readback_v1(
        root=proof_root,
        binding={
            "account": plan.episode.account_scope.account_identity,
            "slot_id": plan.episode.lane_id,
            "instrument_id": plan.episode.instrument_id,
            "reservation_id": plan.old_reservation_id,
            "envelope_digest": envelope.envelope_digest,
            "client_order_id": envelope.client_order_id,
            "claim_id": record["transport_attempt"]["claim_id"],
            "plan_digest": plan.digest_v1(),
            "fill_evidence_digest": fill.evidence_digest,
            "settlement_native": str(native_net),
        },
        reads=(*reads, history_read),
        bodies=(*bodies, history_body),
    )
    return host.owner.record_authenticated_net_reversal_v1(
        plan=plan, envelope=envelope, fill=fill, native_net=native_net, settlement_digest=digest
    )
