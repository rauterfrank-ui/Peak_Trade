"""Offline V2 opening-fill evidence for the existing simulated budget settlement."""

from dataclasses import asdict, replace
from datetime import datetime
from decimal import Decimal
import json

from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import _verify
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import _source
from src.ops.full_core_live_path_composition_root_v1.current_productive_double_play_reversal_v1 import (
    DirectDoublePlayReversalV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalBudgetError,
    PortfolioCapitalReservationBudgetOwnerV1,
    ReservationStateV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.portfolio_capital_reservation_budget_v1.slot_economic_source_v1 import _fill
from src.ops.portfolio_capital_reservation_budget_v1.slot_loss_budget_v1 import (
    build_direct_reversal_booking_v1,
    direct_reversal_instrument_basis_v1,
    restore_state,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
    build_simulated_fill_v1,
)

SIMULATED_ENVIRONMENT = "INTERNAL_SIMULATED_EXECUTION"
_OPENINGS = "offline_v2_opening_fills"
_BOOKINGS = "simulated_direct_reversal_bookings"


class OfflineFirstEntryBudgetOwnerV2(PortfolioCapitalReservationBudgetOwnerV1):
    """Keep the opening proof and the net booking in the original budget store."""

    def __init__(self, **kwargs):
        self._opening_fills = {}
        super().__init__(**kwargs)
        if self._store is None:
            raise ValueError("FIRST_ENTRY_V2_DURABLE_BUDGET_REQUIRED")

    def _durable_payload_locked(self):
        payload = super()._durable_payload_locked()
        if self._opening_fills:
            payload[_OPENINGS] = self._opening_fills
        return payload

    def _opening_predecessor(self, reservation_id, proof):
        identity_fields = dict(proof["identity"])
        identity_fields["account_scope"] = PositionEpisodeScopeV1(
            **identity_fields["account_scope"]
        )
        identity = PositionEpisodeIdentityV1(**identity_fields)
        identity.validate_v1()
        key = self._by_id[reservation_id]
        hold = self._by_key[key]
        bound = self._reservation_bindings[reservation_id]["bound"]
        sizing = self._sizing_bindings[key]
        if (
            identity.account_scope
            != PositionEpisodeScopeV1(self._account_identity, SIMULATED_ENVIRONMENT)
            or identity.lane_id != str(hold.slot_id)
            or identity.instrument_id != bound["instrument_id"]
            or identity.venue_native_id != bound["venue_native_id"]
            or sizing.entry_cost_binding is None
            or self._slot_capital_allocation is None
            or self._slot_capital_allocation["schema"] != "slot_capital_allocation.v1"
        ):
            raise ValueError("FIRST_ENTRY_V2_FILL_SCOPE_MISMATCH")
        link = self._execution_links.get(reservation_id)
        if link is not None and (
            link["phase"] != "PLAN_BOUND"
            or link.get("plan_origin", {}).get("venue_plan", {}).get("environment")
            != SIMULATED_ENVIRONMENT
        ):
            raise ValueError("FIRST_ENTRY_V2_FILL_REQUIRES_OFFLINE_HOLD")
        cost = sizing.entry_cost_binding.validate_v1(
            monetary_source=sizing.monetary_source,
            applied_input=sizing.applied_input,
            decision=sizing.decision,
        )
        (opening,) = map(_fill, proof["fills"])
        session = ProductiveFuturesAccountingSessionV1.from_durable_dict(
            proof["accounting_checkpoint"]
        )
        vwap = Decimal(cost["book_vwap"])
        mark = Decimal(sizing.monetary_source.native_reference_price)
        direction = 1 if cost["side"] == "LONG" else -1
        expected = build_simulated_fill_v1(
            fill_id=f"v2-simulated-reservation:{reservation_id}:{cost['digest']}",
            instrument_id=bound["venue_native_id"],
            side="BUY" if direction > 0 else "SELL",
            quantity=sizing.decision.final_quantity,
            mark_price=mark,
            contract=session.contract,
            fee_rate_bps=Decimal(cost["charged_rate"]) * 10000,
            slippage_bps=direction * (vwap / mark - 1) * 10000,
            event_time_unix=opening.event_time_unix,
        )
        if (
            opening != expected
            or opening.fill_price != vwap
            or opening.fee != Decimal(cost["fee_quote"])
            or session.contract.quote_currency != cost["quote_currency"]
            or session.contract.contract_size
            != Decimal(str(sizing.applied_input.instrument.contract_multiplier))
            or opening.event_time_unix is None
            or opening.event_time_unix
            < datetime.fromisoformat(sizing.monetary_source.decision_epoch).timestamp()
            or session.funding_events
        ):
            raise ValueError("FIRST_ENTRY_V2_FILL_COST_OR_SIZING_MISMATCH")
        verified, _ = _verify(identity=identity, session=session, fills=(opening,))
        if verified != {**proof, "accounting_checkpoint": session.to_durable_dict()}:
            raise ValueError("FIRST_ENTRY_V2_FILL_SOURCE_MISMATCH")
        # Supply the initial confirmed fill prefix to the original settlement
        # builder. Zero prior settlement charges the opening fee exactly once.
        return {
            "plan": {
                "old_reservation_id": reservation_id,
                "selection_digest": bound["selection_integrity_digest"],
                "episode": asdict(identity),
            },
            "after_fill_ids": [opening.fill_id],
            "after_fill_digests": {opening.fill_id: opening.digest()},
            "settled_native_total": "0",
        }

    def retain_opening_fill_v2(self, *, reservation_id, episode):
        proof, anchors = _source(episode.entry_source_ref, episode.identity)
        with self._lock:
            if self._closed_owner or self._storage_failed:
                raise ValueError("FIRST_ENTRY_V2_WRITER_UNAVAILABLE")
            key = self._by_id.get(reservation_id)
            if (
                key is None
                or self._by_key[key].state is not ReservationStateV1.COMMITTED
                or anchors["entry_event_time"] != episode.binding.entry_event_time
                or anchors["entry_price"] != episode.binding.entry_price
            ):
                raise ValueError("FIRST_ENTRY_V2_COMMITTED_HOLD_REQUIRED")
            self._opening_predecessor(reservation_id, proof)
            prior = self._opening_fills.get(reservation_id)
            if prior is not None:
                if prior != proof:
                    raise ValueError("FIRST_ENTRY_V2_OPENING_FILL_CONFLICT")
            else:
                self._opening_fills[reservation_id] = proof
                self._persist_locked()
            return digest(proof)

    def _booking_predecessor(self, plan, prior, before):
        rid = plan.old_reservation_id
        if prior is not None and prior["plan"]["old_reservation_id"] == rid:
            return prior
        proof = self._opening_fills.get(rid)
        if proof is None:
            return prior
        if proof["identity"] != asdict(plan.episode):
            raise ValueError("FIRST_ENTRY_V2_REVERSAL_EPISODE_MISMATCH")
        opening = self._opening_predecessor(rid, proof)
        checkpoint = proof["accounting_checkpoint"]
        if before["fill_order"] != opening["after_fill_ids"] or any(
            before[field] != checkpoint[field]
            for field in (
                "contract",
                "initial_equity",
                "realized_pnl",
                "cumulative_fees",
                "cumulative_slippage",
            )
        ):
            raise ValueError("FIRST_ENTRY_V2_REVERSAL_OPENING_CHECKPOINT_MISMATCH")
        return opening

    def _restore_locked(self, payload):
        if _OPENINGS not in payload:
            super()._restore_locked(payload)
            self._opening_fills = {}
            return
        opening = payload[_OPENINGS]
        series_by_slot = payload.get(_BOOKINGS, {})
        try:
            base = {
                key: value
                for key, value in payload.items()
                if key not in {_OPENINGS, _BOOKINGS, "test_slot_economics"}
            }
            # The original restore validates the financial base. Settlement
            # rows are read below with the V2 first-fill predecessor available.
            if "test_slot_economics" in payload:
                base["test_slot_economics"] = {
                    slot: {"records": [], "exhausted": False, "net_result_usdc": "0"}
                    for slot in payload["test_slot_economics"]
                }
            super()._restore_locked(base)
            if not isinstance(opening, dict) or not opening or not isinstance(series_by_slot, dict):
                raise ValueError("FIRST_ENTRY_V2_DURABLE_PROOF_SHAPE")
            self._opening_fills = opening
            for rid, proof in opening.items():
                self._opening_predecessor(rid, proof)

            self._simulated_direct_reversal_bookings = series_by_slot
            self._slot_test_economics = restore_state(self, payload.get("test_slot_economics"))
            seen = set()
            for slot, series in series_by_slot.items():
                if not isinstance(series, list) or not series:
                    raise ValueError("FIRST_ENTRY_V2_BOOKING_SERIES_INVALID")
                verified = []
                for row in series:
                    plan = DirectDoublePlayReversalV1.from_dict_v1(row["plan"])
                    plan_digest = plan.digest_v1()
                    if (
                        plan.episode.lane_id != slot
                        or plan_digest in seen
                        or plan.slot_capital_basis_usdc
                        != direct_reversal_instrument_basis_v1(
                            self, slot, plan.old_reservation_id, plan.decision_epoch, verified
                        )
                    ):
                        raise ValueError("FIRST_ENTRY_V2_BOOKING_SEQUENCE_INVALID")
                    ledger = {
                        "state": "COMPLETED",
                        "direct_reversal": row["plan"],
                        "direct_reversal_digest": plan_digest,
                    }
                    rebuilt, _, _ = build_direct_reversal_booking_v1(
                        self,
                        plan,
                        ledger,
                        row["pre_fill_accounting"],
                        _fill(row["fill"]),
                        previous=self._booking_predecessor(
                            plan,
                            verified[-1] if verified else None,
                            row["pre_fill_accounting"],
                        ),
                    )
                    if rebuilt != row:
                        raise ValueError("FIRST_ENTRY_V2_BOOKING_READBACK_MISMATCH")
                    seen.add(plan_digest)
                    verified.append(row)
        except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError) as exc:
            raise PortfolioCapitalBudgetError("DURABLE_BUDGET_SEMANTIC_RESTORE_UNPROVEN") from exc

    def book_simulated_direct_reversal_v1(self, plan, ledger, accounting, fill):
        if type(plan) is not DirectDoublePlayReversalV1:
            raise ValueError("DIRECT_REVERSAL_ORIGINAL_PLAN_REQUIRED")
        if plan.old_reservation_id not in self._opening_fills:
            return super().book_simulated_direct_reversal_v1(plan, ledger, accounting, fill)
        slot = plan.episode.lane_id
        with self._lock:
            if self._closed_owner or self._storage_failed:
                raise ValueError("DIRECT_REVERSAL_ORIGINAL_WRITER_REQUIRED")
            series = self._simulated_direct_reversal_bookings.get(slot, [])
            plan_digest = plan.digest_v1()
            for index, record in enumerate(series):
                if record["plan_digest"] != plan_digest:
                    continue
                if fill.digest() != record["fill_digest"]:
                    raise ValueError("DIRECT_REVERSAL_BOOKING_REPLAY_CONFLICT")
                if fill.fill_id in accounting.applied_fill_results:
                    if (
                        accounting.applied_fill_results[fill.fill_id].accounting_output_digest
                        != record["accounting_output_digest"]
                    ):
                        raise ValueError("DIRECT_REVERSAL_BOOKING_REPLAY_CONFLICT")
                    return plan.apply_simulated_fill_v1(
                        ledger=ledger, accounting=accounting, fill=fill
                    )
                before = (
                    type(accounting)
                    .from_durable_dict(record["pre_fill_accounting"])
                    .to_durable_dict()
                )
                if accounting.to_durable_dict() != before:
                    raise ValueError("DIRECT_REVERSAL_BOOKING_REPLAY_CONFLICT")
                rebuilt, updated, outcome = build_direct_reversal_booking_v1(
                    self,
                    plan,
                    ledger,
                    record["pre_fill_accounting"],
                    fill,
                    previous=self._booking_predecessor(
                        plan,
                        series[index - 1] if index else None,
                        record["pre_fill_accounting"],
                    ),
                )
                if rebuilt != record:
                    raise ValueError("DIRECT_REVERSAL_BOOKING_REPLAY_CONFLICT")
                accounting.__dict__.update(updated.__dict__)
                return replace(outcome, idempotent_replay=True)

            basis = self._slot_capital_basis_locked_v1(slot, close_booking=None)
            if (
                basis is None
                or not self._admitted
                or basis.allocation_digest != plan.funding_digest
                or self._direct_reversal_basis_locked_v1(
                    slot, plan.old_reservation_id, plan.decision_epoch
                )
                != plan.slot_capital_basis_usdc
            ):
                raise ValueError("DIRECT_REVERSAL_SLOT_BASIS_CHANGED")
            hold = self._by_key.get(self._by_id.get(plan.old_reservation_id))
            if hold is None or hold.state is not ReservationStateV1.COMMITTED:
                raise ValueError("DIRECT_REVERSAL_ORIGINAL_HOLD_CHANGED")
            before = accounting.to_durable_dict()
            record, updated, outcome = build_direct_reversal_booking_v1(
                self,
                plan,
                ledger,
                before,
                fill,
                previous=self._booking_predecessor(plan, series[-1] if series else None, before),
            )
            self._simulated_direct_reversal_bookings[slot] = [*series, record]
            self._persist_locked()
            accounting.__dict__.update(updated.__dict__)
            return outcome


class OfflineFirstEntryBudgetHostV2(PortfolioBudgetHostV1):
    """Opt in to V2 simulated evidence without changing the V1 host."""

    def __init__(self, **kwargs):
        if kwargs.get("execution_environment", SIMULATED_ENVIRONMENT) != SIMULATED_ENVIRONMENT:
            raise ValueError("FIRST_ENTRY_V2_SIMULATED_HOST_REQUIRED")
        super().__init__(**{**kwargs, "execution_environment": SIMULATED_ENVIRONMENT})

    def _open_budget_owner_v1(self, *, account, bindings):
        if set(bindings) != {"LANE_1"}:
            raise ValueError("FIRST_ENTRY_V2_LANE_1_REQUIRED")
        owner = OfflineFirstEntryBudgetOwnerV2(
            durable_root=self.root / "owner",
            durable_account_identity=account,
            durable_mode=self.durable_mode,
            durable_lane_bindings=bindings,
            entry_budget_policy=self.entry_budget_policy,
            slot_capital_allocation=self._slot_capital_allocation
            if self.durable_mode == "create"
            else None,
        )
        if owner.has_live_slot_capital_allocation_v1():
            owner.close()
            raise ValueError("FIRST_ENTRY_V2_SIMULATED_HOST_REQUIRED")
        return owner
