"""Portfolio capital reservation budget contract v1.

One owner, upstream of ``capital_risk_sizing_v1``. It admits or denies a
capital quantity. It does not rank, select, or create ENTER decisions.

Canonical available capital is only the typed 29P producer output
``RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING``. Venue raw fields are not
authority.

``double_play_capital_slot`` remains the separate per-future ratchet model.
This module does not replace it and does not implement ratchet formulas.

N>1 runtime stays unauthorized. External effect stays unauthorized.
No venue fill lifecycle is claimed.

RUNTIME_AUTHORIZATION_EFFECT=NONE
ATLAS_AUTHORITY=NONE
"""

from __future__ import annotations

import hashlib
import json
import math
import threading
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Mapping

from .durable_store_v1 import DurableBudgetStoreV1, SCHEMA
from .recovery_v1 import capital_scope_v1, lane_bindings_v1, verify_recovery_inputs_v1
from .sizing_binding_v1 import ReservationSizingBindingV1, request_digest_v1

from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingDecisionV1,
    CapitalRiskSizingInputV1,
    CapitalRiskSizingOutcome,
    evaluate_capital_risk_sizing_v1,
)
from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    CapitalAdmissionClaimV1,
    evaluate_capital_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_SOURCE_OBSERVED_VENUE,
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    REQUIRED_SETTLEMENT_CURRENCY,
    RISK_EQUITY_DIMENSION,
    evaluate_step_29p_capital_risk_admissibility_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    PRODUCER_IDENTITY,
    CurrentProductive29PRiskCapitalOutputV1,
    CurrentProductiveAccountEligibilityFactV1,
    CurrentProductiveP01ReductionFactV1,
    CurrentProductiveUsdcFreeMarginObservationV1,
    bind_step_29p_typed_equity_from_risk_capital_v1,
    produce_current_productive_29p_risk_capital_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

PORTFOLIO_BUDGET_OWNER = "portfolio_capital_reservation_budget_owner_v1"
RESERVATION_OWNER = PORTFOLIO_BUDGET_OWNER
SIZING_OWNER = "src.governance.capital_risk_sizing_v1"
CONTRACT_ID = "N5_PORTFOLIO_CAPITAL_RESERVATION_BUDGET_CONTRACT_V1"
AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
ATLAS_AUTHORITY = "NONE"
N_GT_1_ENABLED = False
VENUE_FILL_INTEGRATED = False
CANONICAL_RESTART_RECONSTRUCTABLE = False
TRUE_TOKEN = "true"

_ACTIVE = frozenset({"RESERVED", "COMMITTED"})
_TERMINAL = frozenset({"RELEASED", "EXPIRED", "INVALIDATED"})


class PortfolioCapitalBudgetError(ValueError):
    """Fail-closed portfolio budget contract violation."""


class ReservationStateV1(str, Enum):
    REQUESTED = "REQUESTED"
    RESERVED = "RESERVED"
    COMMITTED = "COMMITTED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"


class ReserveDispositionV1(str, Enum):
    ADMITTED = "ADMITTED"
    DENIED = "DENIED"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    FAIL_CLOSED = "FAIL_CLOSED"


class ReleaseReasonV1(str, Enum):
    RECONCILED_ENTRY_NO_FILL = "RECONCILED_ENTRY_NO_FILL"
    RECONCILED_POSITION_FLAT = "RECONCILED_POSITION_FLAT"
    SIZING_OR_ADMISSION_DENY = "SIZING_OR_ADMISSION_DENY"
    PLAN_FAILURE = "PLAN_FAILURE"
    EXPLICIT_CANCEL_BEFORE_EXTERNAL_EFFECT = "EXPLICIT_CANCEL_BEFORE_EXTERNAL_EFFECT"
    STALE_OR_INVALID_EPOCH = "STALE_OR_INVALID_EPOCH"
    PRE_EXTERNAL_EFFECT_FAILED = "PRE_EXTERNAL_EFFECT_FAILED"
    ABANDONED = "ABANDONED"


def _canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SlotId(str):
    """Non-empty slot identity. Not a trading decision."""

    def __new__(cls, value: str) -> SlotId:
        text = str(value or "")
        if text == "" or text != text.strip():
            raise PortfolioCapitalBudgetError("SLOT_ID_INVALID")
        return str.__new__(cls, text)


class ReservationId(str):
    """Deterministic reservation identity. Not a venue order id."""

    def __new__(cls, value: str) -> ReservationId:
        text = str(value or "")
        if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
            raise PortfolioCapitalBudgetError("RESERVATION_ID_INVALID")
        return str.__new__(cls, text)


@dataclass(frozen=True)
class CapitalReservationV1:
    reservation_id: ReservationId
    slot_id: SlotId
    decision_id: str
    cycle_id: str
    observation_id: str
    amount: Decimal
    state: ReservationStateV1
    transition_trace: tuple[str, ...]
    terminal_reason: str
    venue_fill_integrated: bool = False

    @property
    def counts_against_budget(self) -> bool:
        return self.state.value in _ACTIVE


@dataclass(frozen=True)
class PortfolioBudgetStateV1:
    admitted: bool
    observation_id: str
    canonical_available_capital: Decimal
    active_reservation_sum: Decimal
    remaining_unreserved: Decimal
    canonical_restart_reconstructable: bool
    reservation_ids: tuple[str, ...]
    recovery_required: bool = False
    durable_state_enabled: bool = False
    reserved_opening_fees: Decimal = Decimal("0")
    reserved_closing_costs: Decimal = Decimal("0")
    reserved_funding_costs: Decimal = Decimal("0")


@dataclass(frozen=True)
class ReserveResultV1:
    disposition: ReserveDispositionV1
    reservation: CapitalReservationV1 | None
    reason_codes: tuple[str, ...]
    active_sum_after: Decimal
    admitted_budget: Decimal
    mutated: bool


@dataclass(frozen=True)
class SizedReservationResultV1:
    disposition: ReserveDispositionV1
    reservation: CapitalReservationV1 | None
    sizing_decision: CapitalRiskSizingDecisionV1 | None
    reason_codes: tuple[str, ...]
    active_sum_after: Decimal
    admitted_budget: Decimal
    sizing_owner: str = SIZING_OWNER


def observation_identity_v1(output: CurrentProductive29PRiskCapitalOutputV1) -> str:
    return _sha256_text(
        _canonical_json(
            {
                "account": output.bound_account_identity,
                "algebra": output.algebra_id,
                "digest": output.input_set_digest,
                "dimension": output.dimension_id,
                "epoch": output.decision_epoch,
                "producer": output.producer_identity,
                "value": output.value,
            }
        )
    )


def _positive_decimal(raw: str) -> Decimal | None:
    text = str(raw or "")
    if text == "" or text != text.strip():
        return None
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite() or value <= 0:
        return None
    return value


def _digest_identity_v1(value: object) -> bool:
    return (
        isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
    )


def _money(amount: Decimal) -> Decimal | None:
    if isinstance(amount, float) or isinstance(amount, bool):
        return None
    if not isinstance(amount, Decimal):
        return None
    if not amount.is_finite() or amount <= 0:
        return None
    return amount


def _producer_budget(
    output: object,
) -> tuple[Decimal, str] | None:
    if not isinstance(output, CurrentProductive29PRiskCapitalOutputV1):
        return None
    if output.produced != TRUE_TOKEN:
        return None
    if output.producer_identity != PRODUCER_IDENTITY:
        return None
    if output.producer_identity != CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY:
        return None
    if output.dimension_id != RISK_EQUITY_DIMENSION:
        return None
    if output.settlement_currency != REQUIRED_SETTLEMENT_CURRENCY:
        return None
    if output.algebra_id != CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA:
        return None
    if not str(output.decision_epoch or "").strip():
        return None
    if not str(output.bound_account_identity or "").strip():
        return None
    digest = str(output.input_set_digest or "").strip().lower()
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        return None
    value = _positive_decimal(output.value)
    if value is None:
        return None
    return value, observation_identity_v1(output)


def _reservation_key(
    *,
    slot_id: str,
    decision_id: str,
    cycle_id: str,
    observation_id: str,
) -> str:
    return _sha256_text(
        _canonical_json(
            {
                "cycle_id": cycle_id,
                "decision_id": decision_id,
                "observation_id": observation_id,
                "slot_id": slot_id,
            }
        )
    )


class PortfolioCapitalReservationBudgetOwnerV1:
    """Single budget owner, optionally backed by its transactional state history.

    Recovery retains holds and requires automatic reconciliation, never a human
    approval. The default memory-only mode keeps its historical contract.
    """

    def __init__(
        self,
        *,
        durable_root: Path | None = None,
        durable_account_identity: str | None = None,
        durable_mode: str | None = None,
        durable_lane_bindings: Mapping | None = None,
        entry_budget_policy: object | None = None,
    ) -> None:
        self._lock = threading.Lock()
        self._admitted = False
        self._budget = Decimal("0")
        self._observation_id = ""
        self._by_key: dict[str, CapitalReservationV1] = {}
        self._by_id: dict[str, str] = {}
        self._account_identity = ""
        self._close_refreshes: dict[str, str] = {}
        self._store = None
        self._recovery_required = False
        self._storage_failed = False
        self._closed_owner = False
        self._lane_bindings = {}
        self._reservation_bindings = {}
        self._capital_scope = {}
        self._sizing_bindings: dict[str, ReservationSizingBindingV1] = {}
        self._execution_links: dict[str, dict] = {}
        self._open_slot_cost_reserves: dict[str, list[dict]] = {}
        self._entry_budget_policy = None
        if entry_budget_policy is not None:
            from .test_phase_limits_v1 import (
                BoundedSlotEntryBudgetV1,
            )

            if type(entry_budget_policy) is not BoundedSlotEntryBudgetV1:
                raise PortfolioCapitalBudgetError("ENTRY_BUDGET_POLICY_TYPE_INVALID")
            entry_budget_policy.validate_v1()
            self._entry_budget_policy = entry_budget_policy
        from .slot_loss_budget_v1 import empty_state

        self._slot_test_economics = empty_state(self._entry_budget_policy)
        self._open_slot_protection = (
            {slot: None for slot in self._entry_budget_policy.allowed_slot_ids}
            if self._entry_budget_policy is not None
            and self._entry_budget_policy.enforce_open_slot_loss_protection
            else {}
        )
        supplied = (durable_root, durable_account_identity, durable_mode, durable_lane_bindings)
        if any(x is not None for x in supplied):
            if any(x is None for x in supplied):
                raise PortfolioCapitalBudgetError("DURABLE_BUDGET_CONFIGURATION_INCOMPLETE")
            self._lane_bindings = lane_bindings_v1(durable_lane_bindings)
            self._account_identity = durable_account_identity
            try:
                self._store = DurableBudgetStoreV1(
                    durable_root, account_identity=durable_account_identity, mode=durable_mode
                )
                if durable_mode == "recover":
                    self._restore_locked(self._store.load())
                    self._recovery_required = True
                else:
                    self._recovery_required = True
                    self._persist_locked()
            except Exception:
                if self._store is not None:
                    self._store.close()
                raise

    def durable_scope_identity_v1(self) -> dict[str, str]:
        """Stable store/account address only; this is never an admission token."""
        with self._lock:
            if self._store is None:
                raise PortfolioCapitalBudgetError("DURABLE_BUDGET_SCOPE_REQUIRED")
            return {"root": str(self._store.root), "account": self._account_identity}

    def close(self) -> None:
        with self._lock:
            self._admitted = False
            self._closed_owner = True
            if self._store is not None:
                self._store.close()

    def recover_automatically_v1(
        self,
        *,
        output: object,
        reconciliation: object,
        observed: object,
        lane_bindings: Mapping,
        now_unix: float,
        capital_max_age_seconds: float,
    ) -> ReserveResultV1:
        """Fresh facts + existing reconciliation gate, with all old holds retained.

        Callable on every fresh-data retry; no operator unlock or capital release.
        This is internal budget recovery, not venue/order lifecycle authority.
        """
        with self._lock:
            if self._store is None or self._storage_failed or self._closed_owner:
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=("DURABLE_RECOVERY_UNAVAILABLE",),
                    mutated=False,
                )
            parsed = _producer_budget(output)
            try:
                current = lane_bindings_v1(lane_bindings)
                verify_recovery_inputs_v1(
                    output=output,
                    reconciliation=reconciliation,
                    observed=observed,
                    account=self._account_identity,
                    bindings=current,
                    now_unix=now_unix,
                    capital_max_age_seconds=capital_max_age_seconds,
                )
                if parsed is None:
                    raise ValueError("CANONICAL_CAPITAL_FACT_INVALID")
                scope = capital_scope_v1(output)
                if self._capital_scope and scope != self._capital_scope:
                    raise ValueError("DURABLE_VENUE_OR_MARGIN_SCOPE_MISMATCH")
                for r in self._by_key.values():
                    if r.counts_against_budget and current.get(
                        str(r.slot_id)
                    ) != self._lane_bindings.get(str(r.slot_id)):
                        raise ValueError("DURABLE_ACTIVE_LANE_GENERATION_MISMATCH")
                if parsed[0] < self._held_capital_locked():
                    raise ValueError("DURABLE_HELD_CAPITAL_EXCEEDS_FRESH_BUDGET")
            except (ValueError, TypeError, AttributeError) as exc:
                self._admitted = False
                self._recovery_required = True
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=(str(exc),),
                    mutated=True,
                )
            self._budget, self._observation_id = parsed
            self._capital_scope = scope
            self._lane_bindings = current
            self._admitted = True
            self._recovery_required = False
            return self._result_locked(
                disposition=ReserveDispositionV1.ADMITTED,
                reservation=None,
                reason_codes=("DURABLE_BUDGET_AUTOMATICALLY_RECONCILED_HOLDS_RETAINED",),
                mutated=True,
            )

    def budget_state_v1(self) -> PortfolioBudgetStateV1:
        with self._lock:
            return self._state_locked()

    def active_sum_v1(self) -> Decimal:
        with self._lock:
            return self._active_sum_locked()

    def active_slot_sum_v1(self, slot_id) -> Decimal:
        slot = str(SlotId(str(slot_id)))
        with self._lock:
            return self._active_sum_locked(slot)

    def entry_budget_policy_v1(self):
        """Original bound immutable policy, recovered with the same holds."""
        with self._lock:
            return self._entry_budget_policy

    def reservation_monetary_source_v1(self, reservation_id):
        """Read the original normalization sources; never upgrade a legacy hold."""
        from src.ops.governed_productive_monetary_normalization_v1.sizing_source_v1 import (
            SizingMonetarySourceV1,
        )

        with self._lock:
            key = self._by_id.get(str(reservation_id))
            binding = self._sizing_bindings.get(key)
            if binding is None or binding.monetary_source is None:
                raise ValueError("RESERVATION_MONETARY_SOURCE_NOT_RETAINED")
            binding.validate_v1(
                amount=self._by_key[key].amount, decision_id=self._by_key[key].decision_id
            )
            return SizingMonetarySourceV1.from_dict_v1(binding.monetary_source.to_dict_v1())

    def test_slot_loss_state_v1(self, slot_id):
        from .slot_loss_budget_v1 import enabled, admission_reason, remaining_loss

        with self._lock:
            if not enabled(self._entry_budget_policy) or slot_id not in self._slot_test_economics:
                raise ValueError("TEST_SLOT_LOSS_POLICY_REQUIRED")
            result = {
                **json.loads(json.dumps(self._slot_test_economics[slot_id])),
                "remaining_loss_allowance_usdc": str(remaining_loss(self, slot_id)),
                "new_entry_blocker": self._test_slot_loss_entry_blocker_locked(slot_id),
                "scope": "EXPLICIT_TEST_PHASE_ONLY",
            }
            if self._open_slot_protection:
                opened = self._open_slot_protection[slot_id]
                result["open_position_protection"] = json.loads(json.dumps(opened))
                if opened and opened["exhaustion"] is not None:
                    result.update(exhausted=True, remaining_loss_allowance_usdc="0")
            return result

    def _test_slot_loss_entry_blocker_locked(self, slot_id):
        from .slot_loss_budget_v1 import admission_reason

        closed_reason = admission_reason(self, slot_id)
        if closed_reason is not None:
            return closed_reason
        opened = self._open_slot_protection.get(slot_id)
        if opened:
            if opened["exhaustion"] is not None:
                return "TEST_SLOT_MARK_VALUED_LOSS_ALLOWANCE_EXHAUSTED"
            pending = opened["pending_close"]
            if (
                pending
                and self._by_key[self._by_id[pending["reservation_id"]]].counts_against_budget
            ):
                return "TEST_SLOT_LOSS_CLOSE_PENDING"
        return None

    def observe_open_slot_loss_v1(self, *, slot_id, episode, observation, mark_px, observed_unix):
        from .entry_execution_cost_v1 import assess_open_slot_loss_v1, SlotLossExitRequestV1
        from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
            PositionEpisodeBindingV1,
        )

        with self._lock:
            if not self._open_slot_protection or slot_id not in self._open_slot_protection:
                raise ValueError("OPEN_SLOT_EXPLICIT_TEST_POLICY_REQUIRED")
            if self._closed_owner or self._storage_failed or self._store is None:
                raise PortfolioCapitalBudgetError("OPEN_SLOT_ORIGINAL_BUDGET_WRITER_UNAVAILABLE")
            if type(episode) is not PositionEpisodeBindingV1:
                raise ValueError("OPEN_SLOT_ORIGINAL_EPISODE_REQUIRED")
            rows = [
                r
                for r in self._by_key.values()
                if str(r.slot_id) == slot_id and r.counts_against_budget
            ]
            if len(rows) != 1:
                raise ValueError("OPEN_SLOT_SINGLE_ORIGINAL_HELD_RESERVATION_REQUIRED")
            rid = str(rows[0].reservation_id)
            expected_ref = (
                episode.entry_source_ref
                if episode.binding.simulated_accounting_progress is None
                else episode.binding.simulated_accounting_progress["current_source_ref"]
            )
            if (
                observation.identity_json != _canonical_json(asdict(episode.identity))
                or observation.initial_source_ref != episode.entry_source_ref
                or observation.current_source_ref != expected_ref
                or datetime.fromisoformat(
                    observation.valuation_epoch.replace("Z", "+00:00")
                ).timestamp()
                != observed_unix
            ):
                raise ValueError("OPEN_SLOT_CURRENT_EPISODE_OR_CYCLE_MISMATCH")
            prior = self._open_slot_protection[slot_id]
            if self._entry_budget_policy.renew_open_slot_cost_reserves:
                from .entry_execution_cost_v1 import OpenSlotLossObservationV1
                from .open_slot_cost_renewal_v1 import bind_observation_locked_v1

                old_observation = None if prior is None else prior["latest"]["observation"]
                if (
                    old_observation is not None
                    and replace(
                        observation, cost_reserve_ref=old_observation.get("cost_reserve_ref", "")
                    ).to_dict_v1()
                    == old_observation
                ):
                    observation = OpenSlotLossObservationV1.from_dict_v1(old_observation)
                else:
                    observation = bind_observation_locked_v1(self, rid, observation)
            proof = assess_open_slot_loss_v1(self, rid, observation)
            # N1/Core consumes a float projection; accounting retains the
            # original Decimal mark in the proof. Compare the same projection
            # exactly, without an epsilon or rounding the monetary valuation.
            source_mark = float(Decimal(proof["native_mark_price"]))
            cycle_mark = float(mark_px)
            if (
                not math.isfinite(source_mark)
                or not math.isfinite(cycle_mark)
                or source_mark <= 0
                or cycle_mark <= 0
                or source_mark != cycle_mark
            ):
                raise ValueError("OPEN_SLOT_CURRENT_MARK_CYCLE_MISMATCH")
            if prior:
                old = datetime.fromisoformat(
                    prior["latest"]["valuation_epoch"].replace("Z", "+00:00")
                )
                new = datetime.fromisoformat(proof["valuation_epoch"].replace("Z", "+00:00"))
                if new < old or new == old and proof != prior["latest"]:
                    raise ValueError("OPEN_SLOT_OBSERVATION_TIME_OR_REPLAY_CONFLICT")
            updated = {
                "latest": proof,
                "pending_close": prior["pending_close"]
                if prior
                and prior["pending_close"] is not None
                and self._by_key[
                    self._by_id[prior["pending_close"]["reservation_id"]]
                ].counts_against_budget
                else proof
                if proof["close_required"]
                else None,
                "exhaustion": prior["exhaustion"]
                if prior and prior["exhaustion"] is not None
                else proof
                if proof["actual_loss_allowance_exhausted"]
                else None,
            }
            if updated != prior:
                if self._entry_budget_policy.renew_open_slot_cost_reserves:
                    from .open_slot_cost_renewal_v1 import apply_renewal_locked_v1

                    apply_renewal_locked_v1(self, rid, proof)
                self._open_slot_protection[slot_id] = updated
                self._persist_locked()
            pending = updated["pending_close"]
            return None if pending is None else SlotLossExitRequestV1(self, rid, pending["digest"])

    def inspect_open_slot_loss_exit_v1(
        self, *, reservation_id, proof_digest, episode, bound, observed_unix
    ):
        from .entry_execution_cost_v1 import assess_open_slot_loss_v1, OpenSlotLossObservationV1
        from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
            PositionEpisodeBindingV1,
        )

        with self._lock:
            if type(episode) is not PositionEpisodeBindingV1:
                raise ValueError("OPEN_SLOT_ORIGINAL_EPISODE_REQUIRED")
            record = self._by_key.get(self._by_id.get(reservation_id))
            if (
                record is None
                or not record.counts_against_budget
                or self._closed_owner
                or self._storage_failed
            ):
                raise ValueError("OPEN_SLOT_ORIGINAL_CLOSE_CONTEXT_UNAVAILABLE")
            stored = self._open_slot_protection.get(str(record.slot_id))
            proof = None if not stored else stored["pending_close"]
            if proof is None or proof["digest"] != proof_digest or not proof["close_required"]:
                raise ValueError("OPEN_SLOT_ORIGINAL_CLOSE_TRIGGER_REQUIRED")
            rebuilt = assess_open_slot_loss_v1(
                self, reservation_id, OpenSlotLossObservationV1.from_dict_v1(proof["observation"])
            )
            if (
                rebuilt != proof
                or proof["identity"] != asdict(episode.identity)
                or (bound.instrument_id, bound.venue_native_id)
                != (episode.identity.instrument_id, episode.identity.venue_native_id)
                or datetime.fromisoformat(
                    proof["valuation_epoch"].replace("Z", "+00:00")
                ).timestamp()
                > observed_unix
            ):
                raise ValueError("OPEN_SLOT_CLOSE_SOURCE_OR_EPISODE_MISMATCH")
            return True

    def pending_open_slot_loss_exit_v1(self, slot_id):
        from .entry_execution_cost_v1 import SlotLossExitRequestV1

        with self._lock:
            row = self._open_slot_protection.get(slot_id)
            proof = None if row is None else row["pending_close"]
            if proof is None:
                return None
            record = self._by_key.get(self._by_id.get(proof["reservation_id"]))
            return (
                SlotLossExitRequestV1(self, proof["reservation_id"], proof["digest"])
                if record is not None and record.counts_against_budget
                else None
            )

    def record_test_slot_close_economics_v1(self, request):
        from .slot_loss_budget_v1 import record_closed_locked
        from src.ops.governed_productive_monetary_normalization_v1.contracts_v1 import (
            MonetaryNormalizationError,
        )

        # Original flat/capital marker is required; this never substitutes for it.
        self.inspect_bounded_slot_close_refresh_v1(request)
        with self._lock:
            if (
                self._closed_owner
                or self._storage_failed
                or not self._admitted
                or self._recovery_required
            ):
                raise ValueError("TEST_SLOT_ORIGINAL_BUDGET_OWNER_FENCED")
            try:
                changed = record_closed_locked(self, request)
            except (
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
                ArithmeticError,
                MonetaryNormalizationError,
            ) as exc:
                raise ValueError("TEST_SLOT_ECONOMIC_CLOSE_NOT_ADMITTED:" + str(exc)) from exc
            if changed:
                self._persist_locked()
            from .slot_loss_budget_v1 import remaining_loss

            slot_id = request.execution.source.quantity_handoff.lane_id
            return {
                "scope": "EXPLICIT_TEST_PHASE_ONLY",
                "remaining_loss_allowance_usdc": str(remaining_loss(self, slot_id)),
                "exhausted": self._slot_test_economics[slot_id]["exhausted"],
            }

    def local_commitment_readback_v1(self):
        """Atomic projection of this owner's obligations, never venue margin."""
        from .local_commitment_readback_v1 import read_local_commitments_locked_v1

        with self._lock:
            return read_local_commitments_locked_v1(self)

    def require_local_commitment_readback_v1(self, readback, *, account_identity):
        from .local_commitment_readback_v1 import require_local_commitments_locked_v1

        with self._lock:
            return require_local_commitments_locked_v1(
                self, readback, account_identity=account_identity
            )

    def admitted_budget_v1(self) -> Decimal:
        with self._lock:
            return self._budget if self._admitted else Decimal("0")

    def invariant_holds_v1(self) -> bool:
        with self._lock:
            if not self._admitted:
                return (
                    self._held_capital_locked() <= self._budget
                    if self._store
                    else self._active_sum_locked() == 0
                )
            return self._held_capital_locked() <= self._budget

    def stored_reservation_count_v1(self) -> int:
        with self._lock:
            return len(self._by_key)

    def lookup_v1(
        self,
        *,
        slot_id: SlotId | str,
        decision_id: str,
        cycle_id: str,
        observation_id: str,
    ) -> CapitalReservationV1 | None:
        with self._lock:
            if self._store is not None:
                for r in self._by_key.values():
                    if (str(r.slot_id), r.decision_id, r.cycle_id) == (
                        str(slot_id),
                        decision_id,
                        cycle_id,
                    ):
                        return r
            key = _reservation_key(
                slot_id=str(slot_id),
                decision_id=decision_id,
                cycle_id=cycle_id,
                observation_id=observation_id,
            )
            return self._by_key.get(key)

    def slot_account_binding_matches_v1(
        self, *, slot_id: str, instrument_id: str, account_identity: str
    ) -> bool:
        with self._lock:
            if self._store is None:
                return True
            binding = self._lane_bindings.get(str(slot_id))
            return bool(
                binding
                and binding["bound"]["instrument_id"] == instrument_id
                and self._account_identity == account_identity
            )

    def bind_canonical_producer_output_v1(
        self,
        output: object,
    ) -> ReserveResultV1:
        parsed = _producer_budget(output)
        if parsed is None:
            return self._closed(
                ("CANONICAL_CAPITAL_FACT_INVALID", "NO_MINT_FROM_RAW_OR_INCOMPLETE_FACT")
            )
        value, observation_id = parsed
        with self._lock:
            if self._closed_owner or self._storage_failed or self._recovery_required:
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=("DURABLE_RECONCILIATION_REQUIRED",),
                    mutated=False,
                )
            if self._store is not None and output.bound_account_identity != self._account_identity:
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=("DURABLE_ACCOUNT_MISMATCH",),
                    mutated=False,
                )
            if self._store is not None and capital_scope_v1(output) != self._capital_scope:
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=("DURABLE_VENUE_OR_MARGIN_SCOPE_MISMATCH",),
                    mutated=False,
                )
            if self._admitted and observation_id == self._observation_id:
                if value != self._budget:
                    return self._result_locked(
                        disposition=ReserveDispositionV1.FAIL_CLOSED,
                        reservation=None,
                        reason_codes=("OBSERVATION_IDENTITY_VALUE_CONTRADICTION",),
                        mutated=False,
                    )
                return self._result_locked(
                    disposition=ReserveDispositionV1.IDEMPOTENT_REPLAY,
                    reservation=None,
                    reason_codes=("OBSERVATION_ALREADY_BOUND",),
                    mutated=False,
                )
            if self._store is None:
                self._expire_active_locked(
                    ReservationStateV1.EXPIRED, ReleaseReasonV1.STALE_OR_INVALID_EPOCH
                )
            elif value < self._held_capital_locked():
                self._admitted = False
                self._recovery_required = True
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=("DURABLE_HELD_CAPITAL_EXCEEDS_FRESH_BUDGET",),
                    mutated=True,
                )
            self._admitted = True
            self._budget = value
            self._observation_id = observation_id
            self._account_identity = output.bound_account_identity
            return self._result_locked(
                disposition=ReserveDispositionV1.ADMITTED,
                reservation=None,
                reason_codes=("CANONICAL_AVAILABLE_CAPITAL_BOUND",),
                mutated=True,
            )

    def replay_sized_reservation_v1(
        self,
        reservation_id: str,
        *,
        request: CapitalRiskSizingInputV1,
        risk_request: object | None = None,
        opening_cost_observation: object | None = None,
        funding_cost_observation: object | None = None,
        native_initial_margin_observation: object | None = None,
        absolute_movement_cost_observation: object | None = None,
    ) -> SizedReservationResultV1:
        """Reuse the acknowledged canonical result, never resize an old hold."""
        with self._lock:
            found = self._require_locked(reservation_id)
            current = found[1] if found is not None else None
            decision = None
            try:
                if not self._admitted or current is None or not current.counts_against_budget:
                    raise ValueError("RESERVATION_NOT_ACTIVE_FOR_SIZING_REPLAY")
                binding = self._sizing_bindings.get(str(current.reservation_id))
                if binding is None:
                    raise ValueError("RESERVATION_SIZING_BINDING_MISSING")
                binding.validate_v1(amount=current.amount, decision_id=current.decision_id)
                if binding.entry_cost_binding is not None:
                    from .entry_execution_cost_v1 import EntryExecutionCostObservationV1

                    if (
                        type(opening_cost_observation) is not EntryExecutionCostObservationV1
                        or binding.entry_cost_binding.observation_json
                        != json.dumps(
                            opening_cost_observation.to_dict_v1(),
                            sort_keys=True,
                            separators=(",", ":"),
                            allow_nan=False,
                        )
                    ):
                        raise ValueError("ENTRY_COST_REPLAY_CONTEXT_CHANGED_OR_MISSING")
                elif opening_cost_observation is not None:
                    raise ValueError("ENTRY_COST_UNBOUND_LEGACY_RESERVATION_NOT_UPGRADED")
                if binding.funding_cost_binding is not None:
                    from .entry_execution_cost_v1 import FundingCostObservationV1
                    from .durable_store_v1 import canonical

                    if (
                        type(funding_cost_observation) is not FundingCostObservationV1
                        or binding.funding_cost_binding.observation_json
                        != canonical(funding_cost_observation.to_dict_v1())
                    ):
                        raise ValueError("FUNDING_COST_REPLAY_CONTEXT_CHANGED_OR_MISSING")
                elif funding_cost_observation is not None:
                    raise ValueError("FUNDING_COST_UNBOUND_LEGACY_RESERVATION_NOT_UPGRADED")
                if binding.native_initial_margin_binding is not None:
                    from .native_initial_margin_v1 import (
                        NativeInitialMarginObservationV1,
                        require_native_margin_locked_v1,
                    )
                    from .durable_store_v1 import canonical
                    from .entry_execution_cost_v1 import utc_now_iso_v1

                    if (
                        type(native_initial_margin_observation)
                        is not NativeInitialMarginObservationV1
                        or canonical(native_initial_margin_observation.to_dict_v1())
                        != binding.native_initial_margin_binding.observation_json
                    ):
                        raise ValueError("NATIVE_INITIAL_MARGIN_REPLAY_CONTEXT_CHANGED_OR_MISSING")
                    require_native_margin_locked_v1(
                        self,
                        binding,
                        exclude_reservation_id=str(current.reservation_id),
                        evaluated_at_utc=utc_now_iso_v1(),
                    )
                elif native_initial_margin_observation is not None:
                    raise ValueError("NATIVE_INITIAL_MARGIN_LEGACY_HOLD_NOT_UPGRADED")
                if binding.absolute_movement_cost_binding is not None:
                    from .absolute_movement_cost_v1 import AbsoluteMovementCostObservationV1
                    from .durable_store_v1 import canonical
                    from .entry_execution_cost_v1 import utc_now_iso_v1

                    if (
                        type(absolute_movement_cost_observation)
                        is not AbsoluteMovementCostObservationV1
                        or canonical(absolute_movement_cost_observation.to_dict_v1())
                        != binding.absolute_movement_cost_binding.observation_json
                    ):
                        raise ValueError("MOVEMENT_REPLAY_CONTEXT_CHANGED_OR_MISSING")
                    binding.absolute_movement_cost_binding.validate_v1(
                        sizing=binding, evaluated_at_utc=utc_now_iso_v1()
                    )
                elif absolute_movement_cost_observation is not None:
                    raise ValueError("MOVEMENT_LEGACY_HOLD_NOT_UPGRADED")
                if binding.risk_binding is not None:
                    binding.risk_binding.validate_replay_v1(risk_request, request)
                elif risk_request is not None:
                    raise ValueError("RISK_UNBOUND_LEGACY_RESERVATION_NOT_UPGRADED")
                decision = binding.replay_v1(request)
                codes = ("IDEMPOTENT_REPLAY_ORIGINAL_SIZING_PRESERVED",)
                disposition = ReserveDispositionV1.IDEMPOTENT_REPLAY
            except ValueError as exc:
                codes = (str(exc),)
                disposition = ReserveDispositionV1.FAIL_CLOSED
            return SizedReservationResultV1(
                disposition=disposition,
                reservation=current,
                sizing_decision=decision,
                reason_codes=codes,
                active_sum_after=self._active_sum_locked(),
                admitted_budget=self._budget if self._admitted else Decimal(0),
            )

    def refresh_after_reconciled_flat_v1(
        self,
        *,
        output: object,
        slot_id: str,
        reservation_ids: tuple[str, ...],
        expected_observation_id: str,
        account_identity: str,
        close_evidence_ref: str,
        bound_instrument: object | None = None,
    ) -> ReserveResultV1:
        """Consume the feedback join's flat proof and fresh canonical capital.

        No monetary value is inferred from position quantity, fills or PnL.
        This N=1 refresh cannot retire another lane's or unlisted reservation.
        The caller must have reconciled the exact closing order and flat snapshot.
        """
        if self._entry_budget_policy is not None:
            return self._refresh_bounded_slot_after_flat_v1(
                output=output,
                slot_id=slot_id,
                reservation_ids=reservation_ids,
                expected_observation_id=expected_observation_id,
                account_identity=account_identity,
                close_evidence_ref=close_evidence_ref,
                bound_instrument=bound_instrument,
            )
        parsed = _producer_budget(output)
        if (
            parsed is None
            or len(close_evidence_ref) != 64
            or any(c not in "0123456789abcdef" for c in close_evidence_ref)
            or not slot_id
        ):
            return self._closed(("POST_CLOSE_CANONICAL_CAPITAL_OR_EVIDENCE_INVALID",))
        value, observation_id = parsed
        with self._lock:

            def deny(reason):
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=(reason,),
                    mutated=False,
                )

            if self._store is not None and capital_scope_v1(output) != self._capital_scope:
                return deny("DURABLE_VENUE_OR_MARGIN_SCOPE_MISMATCH")
            previous = self._close_refreshes.get(close_evidence_ref)
            if previous is not None:
                if previous != observation_id:
                    return deny("CLOSE_REFRESH_REPLAY_CONFLICT")
                return self._result_locked(
                    disposition=ReserveDispositionV1.IDEMPOTENT_REPLAY,
                    reservation=None,
                    reason_codes=("POST_CLOSE_REFRESH_ALREADY_APPLIED",),
                    mutated=False,
                )
            if (
                not self._admitted
                or self._observation_id != expected_observation_id
                or not account_identity
                or self._account_identity != account_identity
                or output.bound_account_identity != account_identity
                or observation_id == self._observation_id
            ):
                return deny("POST_CLOSE_ACCOUNT_OR_OBSERVATION_MISMATCH")
            active = {
                str(r.reservation_id): r for r in self._by_key.values() if r.counts_against_budget
            }
            if len(set(reservation_ids)) != len(reservation_ids) or set(active) != set(
                reservation_ids
            ):
                return deny("POST_CLOSE_RESERVATION_SET_MISMATCH")
            if any(
                r.slot_id != slot_id or r.state is not ReservationStateV1.COMMITTED
                for r in active.values()
            ):
                return deny("POST_CLOSE_FOREIGN_OR_UNCOMMITTED_RESERVATION")
            for reservation in active.values():
                key = self._by_id[str(reservation.reservation_id)]
                self._by_key[key] = replace(
                    reservation,
                    state=ReservationStateV1.RELEASED,
                    transition_trace=reservation.transition_trace
                    + (ReservationStateV1.RELEASED.value,),
                    terminal_reason=ReleaseReasonV1.RECONCILED_POSITION_FLAT.value,
                )
            self._budget, self._observation_id = value, observation_id
            self._close_refreshes[close_evidence_ref] = observation_id
            return self._result_locked(
                disposition=ReserveDispositionV1.ADMITTED,
                reservation=None,
                reason_codes=("RECONCILED_FLAT_CANONICAL_CAPITAL_REFRESHED",),
                mutated=True,
            )

    def _refresh_bounded_slot_after_flat_v1(
        self,
        *,
        output,
        slot_id,
        reservation_ids,
        expected_observation_id,
        account_identity,
        close_evidence_ref,
        bound_instrument,
    ):
        """Retire only one proven flat slot; retain every other original hold.

        The caller is the original close-feedback owner after its full fill,
        position, pending and fresh-capital checks. No amount comes from a fill.
        The immutable bounded test policy identifies this separate transition;
        the ordinary N1 financial contract above remains unchanged.
        """
        parsed = _producer_budget(output)
        with self._lock:

            def deny(reason, *, fence=False):
                if fence:
                    self._admitted = False
                    self._recovery_required = True
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=(reason,),
                    mutated=fence,
                )

            if self._closed_owner or self._storage_failed or self._store is None:
                return deny("POST_CLOSE_BOUNDED_ORIGINAL_WRITER_UNAVAILABLE")
            if (
                parsed is None
                or not _digest_identity_v1(close_evidence_ref)
                or not _digest_identity_v1(expected_observation_id)
                or type(reservation_ids) is not tuple
                or not reservation_ids
                or not all(_digest_identity_v1(rid) for rid in reservation_ids)
                or len(set(reservation_ids)) != len(reservation_ids)
                or slot_id not in self._lane_bindings
            ):
                return deny("POST_CLOSE_BOUNDED_SCOPE_OR_CAPITAL_INVALID")
            try:
                bound = lane_bindings_v1({slot_id: bound_instrument})[slot_id]
                if (
                    account_identity != self._account_identity
                    or output.bound_account_identity != self._account_identity
                    or capital_scope_v1(output) != self._capital_scope
                ):
                    return deny("POST_CLOSE_BOUNDED_ACCOUNT_OR_GENERATION_MISMATCH")
            except (ValueError, TypeError, AttributeError):
                return deny("POST_CLOSE_BOUNDED_ACCOUNT_OR_GENERATION_MISMATCH")
            value, observation_id = parsed
            fingerprint = _sha256_text(
                _canonical_json(
                    {
                        "schema": "bounded_slot_close_refresh.v1",
                        "slot_id": slot_id,
                        "reservation_ids": sorted(reservation_ids),
                        "prior_observation_id": expected_observation_id,
                        "observation_id": observation_id,
                        "account_identity": account_identity,
                        "bound": bound,
                        "policy": self._entry_budget_policy.digest_v1(),
                    }
                )
            )
            previous = self._close_refreshes.get(close_evidence_ref)
            if previous is not None:
                if previous != fingerprint:
                    return deny("CLOSE_REFRESH_REPLAY_CONFLICT")
                return self._result_locked(
                    disposition=ReserveDispositionV1.IDEMPOTENT_REPLAY,
                    reservation=None,
                    reason_codes=("POST_CLOSE_REFRESH_ALREADY_APPLIED",),
                    mutated=False,
                )
            if (
                not self._admitted
                or self._recovery_required
                or self._observation_id != expected_observation_id
                or observation_id == self._observation_id
            ):
                return deny("POST_CLOSE_ACCOUNT_OR_OBSERVATION_MISMATCH")
            if bound != self._lane_bindings[slot_id]:
                return deny("POST_CLOSE_BOUNDED_ACCOUNT_OR_GENERATION_MISMATCH")
            active = {
                str(r.reservation_id): r
                for r in self._by_key.values()
                if r.counts_against_budget and str(r.slot_id) == slot_id
            }
            if set(active) != set(reservation_ids):
                return deny("POST_CLOSE_RESERVATION_SET_MISMATCH")
            if any(
                r.state is not ReservationStateV1.COMMITTED
                or self._reservation_bindings.get(rid) != bound
                for rid, r in active.items()
            ):
                return deny("POST_CLOSE_FOREIGN_OR_UNCOMMITTED_RESERVATION")
            for rid in active:
                link = self._execution_links.get(rid)
                if (
                    link is not None
                    and link["phase"] != "PLAN_BOUND"
                    and (
                        not (link.get("reconciliation") or {})
                        .get("decision", {})
                        .get("reconciliation_complete")
                    )
                ):
                    return deny("POST_CLOSE_ENTRY_RECONCILIATION_UNRESOLVED")
            from .entry_execution_cost_v1 import reserved_opening_fee_v1

            remaining = self._held_capital_locked() - sum(
                (
                    r.amount
                    + reserved_opening_fee_v1(self._sizing_bindings.get(rid))
                    + sum(self._reservation_cost_reserves_locked_v1(rid))
                    for rid, r in active.items()
                ),
                Decimal(0),
            )
            from .open_slot_cost_renewal_v1 import enabled, sum_money_v1

            if enabled(self):
                remaining = sum_money_v1(
                    [self._held_capital_locked()]
                    + [
                        value.copy_negate()
                        for rid, record in active.items()
                        for value in (
                            record.amount,
                            reserved_opening_fee_v1(self._sizing_bindings.get(rid)),
                            *self._reservation_cost_reserves_locked_v1(rid),
                        )
                    ]
                )
            if value < remaining:
                return deny("POST_CLOSE_REMAINING_HOLDS_EXCEED_FRESH_BUDGET", fence=True)
            for rid, reservation in active.items():
                self._by_key[self._by_id[rid]] = replace(
                    reservation,
                    state=ReservationStateV1.RELEASED,
                    transition_trace=reservation.transition_trace
                    + (ReservationStateV1.RELEASED.value,),
                    terminal_reason=ReleaseReasonV1.RECONCILED_POSITION_FLAT.value,
                )
            self._budget, self._observation_id = value, observation_id
            self._close_refreshes[close_evidence_ref] = fingerprint
            return self._result_locked(
                disposition=ReserveDispositionV1.ADMITTED,
                reservation=None,
                reason_codes=("RECONCILED_SLOT_FLAT_CANONICAL_CAPITAL_REFRESHED",),
                mutated=True,
            )

    def inspect_bounded_slot_close_refresh_v1(self, request):
        """Read the original committed close marker before scoped rebinding."""
        from src.ops.full_core_live_path_composition_root_v1.current_productive_post_close_feedback_v1 import (
            PostCloseFeedbackRequestV1,
        )

        with self._lock:
            if (
                not isinstance(request, PostCloseFeedbackRequestV1)
                or request.budget_owner is not self
                or self._entry_budget_policy is None
                or self._store is None
                or self._closed_owner
                or self._storage_failed
            ):
                raise PortfolioCapitalBudgetError("BOUNDED_CLOSE_ORIGINAL_OWNER_REQUIRED")
            slot = request.execution.source.quantity_handoff.lane_id
            bound = lane_bindings_v1({slot: request.bound_instrument})[slot]
            output = request.capital_handoff.producer_output
            fingerprint = _sha256_text(
                _canonical_json(
                    {
                        "schema": "bounded_slot_close_refresh.v1",
                        "slot_id": slot,
                        "reservation_ids": sorted(request.closed_reservation_ids),
                        "prior_observation_id": request.expected_budget_observation_id,
                        "observation_id": observation_identity_v1(output),
                        "account_identity": output.bound_account_identity,
                        "bound": bound,
                        "policy": self._entry_budget_policy.digest_v1(),
                    }
                )
            )
            if (
                self._close_refreshes.get(request.execution.envelope.envelope_digest) != fingerprint
                or self._active_sum_locked(slot) != 0
            ):
                raise PortfolioCapitalBudgetError("BOUNDED_CLOSE_REFRESH_UNPROVEN_OR_SLOT_OCCUPIED")
            for rid in request.closed_reservation_ids:
                current = self._by_key.get(self._by_id.get(rid))
                if (
                    current is None
                    or current.state is not ReservationStateV1.RELEASED
                    or current.terminal_reason != ReleaseReasonV1.RECONCILED_POSITION_FLAT.value
                    or self._reservation_bindings[rid] != bound
                ):
                    raise PortfolioCapitalBudgetError("BOUNDED_CLOSE_RESERVATION_LINEAGE_UNPROVEN")
            return {
                "slot_id": slot,
                "close_ref": request.execution.envelope.envelope_digest,
                "fingerprint": fingerprint,
            }

    def try_reserve_v1(
        self,
        *,
        slot_id: SlotId | str,
        decision_id: str,
        cycle_id: str,
        observation_id: str,
        amount: Decimal,
        sizing_binding: ReservationSizingBindingV1 | None = None,
        max_active_sum: Decimal | None = None,
        expected_risk_snapshot_digest: str | None = None,
        expected_local_commitment_generation: str | None = None,
        handoff_journal: object | None = None,
        futures_financial_custody: object | None = None,
    ) -> ReserveResultV1:
        try:
            slot = SlotId(str(slot_id))
        except PortfolioCapitalBudgetError as exc:
            return self._closed((str(exc),))
        decision = str(decision_id or "")
        cycle = str(cycle_id or "")
        observed = str(observation_id or "")
        if decision == "" or decision != decision.strip() or cycle == "" or cycle != cycle.strip():
            return self._closed(("DECISION_OR_CYCLE_IDENTITY_MISSING",))
        money = _money(amount)
        if money is None:
            return self._closed(("REQUESTED_AMOUNT_INVALID",))
        if max_active_sum is not None and _money(max_active_sum) is None:
            return self._closed(("RESERVATION_ACTIVE_CEILING_INVALID",))
        liquidation_snapshot = None
        if getattr(self._entry_budget_policy, "require_xperp_liquidation_projection", False):
            from .xperp_liquidation_projection_v1 import capture_liquidation_custody_v1

            try:
                liquidation_snapshot = capture_liquidation_custody_v1(
                    self, futures_financial_custody
                )
                generation = liquidation_snapshot["local_generation"]
                if expected_local_commitment_generation not in (None, generation):
                    raise ValueError("XPERP_LIQUIDATION_LOCAL_GENERATION_MISMATCH")
                expected_local_commitment_generation = generation
            except (
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
                ArithmeticError,
                RuntimeError,
            ) as exc:
                return self._closed((str(exc), "NO_PARTIAL_MUTATION"))
        elif futures_financial_custody is not None or (
            isinstance(sizing_binding, ReservationSizingBindingV1)
            and sizing_binding.xperp_liquidation_binding is not None
        ):
            return self._closed(("XPERP_LIQUIDATION_EXPLICIT_POLICY_REQUIRED",))
        with self._lock:
            if expected_local_commitment_generation is not None:
                from .local_commitment_readback_v1 import read_local_commitments_locked_v1

                try:
                    current_generation = read_local_commitments_locked_v1(self).generation_digest
                    if expected_local_commitment_generation != current_generation:
                        raise ValueError("LOCAL_COMMITMENT_GENERATION_CHANGED_BEFORE_RESERVE")
                except ValueError as exc:
                    return self._result_locked(
                        disposition=ReserveDispositionV1.FAIL_CLOSED,
                        reservation=None,
                        reason_codes=(str(exc),),
                        mutated=False,
                    )
            if expected_risk_snapshot_digest is not None:
                if (
                    self._store is None
                    or expected_risk_snapshot_digest != self._risk_snapshot_locked()["digest"]
                    or sizing_binding is None
                    or sizing_binding.risk_binding is None
                    or sizing_binding.risk_binding.owner_snapshot_digest
                    != expected_risk_snapshot_digest
                ):
                    return self._result_locked(
                        disposition=ReserveDispositionV1.FAIL_CLOSED,
                        reservation=None,
                        reason_codes=("RISK_PORTFOLIO_GENERATION_CHANGED",),
                        mutated=False,
                    )
            elif sizing_binding is not None and sizing_binding.risk_binding is not None:
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=("RISK_ATOMIC_GENERATION_GUARD_REQUIRED",),
                    mutated=False,
                )
            if not self._admitted:
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=("RESTART_OR_UNBOUND_BUDGET_FAIL_CLOSED",),
                    mutated=False,
                )
            from .open_slot_cost_renewal_v1 import entry_blocker_locked_v1

            renewal_blocker = entry_blocker_locked_v1(self)
            if renewal_blocker is not None:
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=(renewal_blocker,),
                    mutated=False,
                )
            if self._store is not None:
                if str(slot) not in self._lane_bindings:
                    return self._result_locked(
                        disposition=ReserveDispositionV1.FAIL_CLOSED,
                        reservation=None,
                        reason_codes=("DURABLE_SLOT_UNBOUND",),
                        mutated=False,
                    )
                # Observation refresh must not create a second hold for the same
                # causal decision. Terminal records also remain replay barriers.
                for prior in self._by_key.values():
                    if (prior.slot_id, prior.decision_id, prior.cycle_id) == (
                        slot,
                        decision,
                        cycle,
                    ):
                        if observed not in {prior.observation_id, self._observation_id}:
                            return self._result_locked(
                                disposition=ReserveDispositionV1.FAIL_CLOSED,
                                reservation=prior,
                                reason_codes=("STALE_OR_FOREIGN_OBSERVATION_NOT_ADOPTED",),
                                mutated=False,
                            )
                        if not prior.counts_against_budget:
                            return self._result_locked(
                                disposition=ReserveDispositionV1.FAIL_CLOSED,
                                reservation=prior,
                                reason_codes=("TERMINAL_RESERVATION_CANNOT_BACK_NEW_EXECUTION",),
                                mutated=False,
                            )
                        return self._result_locked(
                            disposition=ReserveDispositionV1.IDEMPOTENT_REPLAY
                            if prior.amount == money
                            else ReserveDispositionV1.FAIL_CLOSED,
                            reservation=prior,
                            reason_codes=(
                                "IDEMPOTENT_REPLAY_NO_DOUBLE_COUNT"
                                if prior.amount == money
                                else "REPLAY_AMOUNT_MISMATCH",
                            ),
                            mutated=False,
                        )
            if observed != self._observation_id:
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=("STALE_OR_FOREIGN_OBSERVATION_NOT_ADOPTED",),
                    mutated=False,
                )
            key = _reservation_key(
                slot_id=str(slot),
                decision_id=decision,
                cycle_id=cycle,
                observation_id=observed,
            )
            existing = self._by_key.get(key)
            if existing is not None:
                if existing.amount != money:
                    return self._result_locked(
                        disposition=ReserveDispositionV1.FAIL_CLOSED,
                        reservation=existing,
                        reason_codes=("REPLAY_AMOUNT_MISMATCH",),
                        mutated=False,
                    )
                return self._result_locked(
                    disposition=ReserveDispositionV1.IDEMPOTENT_REPLAY,
                    reservation=existing,
                    reason_codes=("IDEMPOTENT_REPLAY_NO_DOUBLE_COUNT",),
                    mutated=False,
                )
            policy_denial = self._entry_budget_denial_locked(str(slot), money)
            from .slot_loss_budget_v1 import enabled, remaining_loss

            if enabled(self._entry_budget_policy) and policy_denial is None:
                if (
                    not isinstance(sizing_binding, ReservationSizingBindingV1)
                    or sizing_binding.monetary_source is None
                ):
                    policy_denial = "TEST_SLOT_LOSS_REQUIRES_ORIGINAL_MONETARY_SIZING"
            if (
                policy_denial is None
                and self._entry_budget_policy is not None
                and self._entry_budget_policy.require_opening_execution_costs
                and (
                    not isinstance(sizing_binding, ReservationSizingBindingV1)
                    or sizing_binding.entry_cost_binding is None
                )
            ):
                policy_denial = "OPENING_EXECUTION_COST_SOURCES_REQUIRED"
            if (
                policy_denial is None
                and self._entry_budget_policy is not None
                and self._entry_budget_policy.require_closing_execution_costs
                and (
                    not isinstance(sizing_binding, ReservationSizingBindingV1)
                    or sizing_binding.close_cost_binding is None
                )
            ):
                policy_denial = "CLOSING_EXECUTION_COST_SOURCES_REQUIRED"
            if (
                policy_denial is None
                and self._entry_budget_policy is not None
                and self._entry_budget_policy.require_next_funding_costs
                and (
                    not isinstance(sizing_binding, ReservationSizingBindingV1)
                    or sizing_binding.funding_cost_binding is None
                )
            ):
                policy_denial = "NEXT_FUNDING_COST_SOURCES_REQUIRED"
            if (
                policy_denial is None
                and self._entry_budget_policy is not None
                and self._entry_budget_policy.require_native_initial_margin
                and (
                    not isinstance(sizing_binding, ReservationSizingBindingV1)
                    or sizing_binding.native_initial_margin_binding is None
                )
            ):
                policy_denial = "NATIVE_INITIAL_MARGIN_SOURCES_REQUIRED"
            if policy_denial is not None:
                return self._result_locked(
                    disposition=ReserveDispositionV1.DENIED,
                    reservation=None,
                    reason_codes=(policy_denial, "NO_PARTIAL_MUTATION"),
                    mutated=False,
                )
            if getattr(
                self._entry_budget_policy, "require_absolute_movement_cost_cover", False
            ) and (
                not isinstance(sizing_binding, ReservationSizingBindingV1)
                or sizing_binding.absolute_movement_cost_binding is None
            ):
                return self._result_locked(
                    disposition=ReserveDispositionV1.DENIED,
                    reservation=None,
                    reason_codes=("ABSOLUTE_MOVEMENT_COST_SOURCES_REQUIRED", "NO_PARTIAL_MUTATION"),
                    mutated=False,
                )
            active = self._active_sum_locked()
            ceiling = (
                min(self._budget, max_active_sum) if max_active_sum is not None else self._budget
            )
            if active + money > ceiling:
                return self._result_locked(
                    disposition=ReserveDispositionV1.DENIED,
                    reservation=None,
                    reason_codes=("RESERVATION_INVARIANT_DENIED", "NO_PARTIAL_MUTATION"),
                    mutated=False,
                )
            reservation_id = ReservationId(key)
            detached_sizing = None
            if sizing_binding is not None:
                try:
                    if not isinstance(sizing_binding, ReservationSizingBindingV1):
                        raise ValueError("RESERVATION_SIZING_BINDING_TYPE_INVALID")
                    sizing_binding.validate_v1(amount=money, decision_id=decision)
                    if liquidation_snapshot is not None:
                        from .durable_store_v1 import canonical
                        from .entry_execution_cost_v1 import utc_now_iso_v1
                        from .xperp_liquidation_projection_v1 import (
                            XPerpLiquidationBindingV1,
                            assess_xperp_liquidation_v1,
                        )

                        assessment = assess_xperp_liquidation_v1(
                            liquidation_snapshot,
                            sizing=sizing_binding,
                            evaluated_at_utc=utc_now_iso_v1(),
                        )
                        sizing_binding = replace(
                            sizing_binding,
                            xperp_liquidation_binding=XPerpLiquidationBindingV1(
                                canonical(liquidation_snapshot), canonical(assessment)
                            ),
                        )
                    detached_sizing = ReservationSizingBindingV1.from_dict_v1(
                        sizing_binding.to_dict_v1()
                    )
                except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError) as exc:
                    return self._result_locked(
                        disposition=ReserveDispositionV1.FAIL_CLOSED,
                        reservation=None,
                        reason_codes=(str(exc),),
                        mutated=False,
                    )
            opening_cost = (
                Decimal(
                    json.loads(detached_sizing.entry_cost_binding.receipt_json)[
                        "total_opening_cost_usdc"
                    ]
                )
                if detached_sizing is not None and detached_sizing.entry_cost_binding is not None
                else Decimal(0)
            )
            from .entry_execution_cost_v1 import reserved_closing_cost_v1

            closing_cost = reserved_closing_cost_v1(detached_sizing)
            from .entry_execution_cost_v1 import reserved_funding_cost_v1

            funding_cost = reserved_funding_cost_v1(detached_sizing)
            if (
                enabled(self._entry_budget_policy)
                and detached_sizing.decision.post_sizing_risk.resulting_max_loss
                + opening_cost
                + closing_cost
                + funding_cost
                > remaining_loss(self, str(slot))
            ):
                return self._result_locked(
                    disposition=ReserveDispositionV1.DENIED,
                    reservation=None,
                    reason_codes=(
                        "TEST_SLOT_REMAINING_LOSS_BUDGET_EXCEEDED",
                        "NO_PARTIAL_MUTATION",
                    ),
                    mutated=False,
                )
            from .entry_execution_cost_v1 import reserved_opening_fee_v1

            fee = reserved_opening_fee_v1(detached_sizing)
            if detached_sizing is not None and detached_sizing.entry_cost_binding is not None:
                cost = json.loads(detached_sizing.entry_cost_binding.receipt_json)
                if (cost["slot_id"], cost["cycle_id"], cost["account_identity"]) != (
                    str(slot),
                    cycle,
                    self._account_identity,
                ):
                    return self._result_locked(
                        disposition=ReserveDispositionV1.FAIL_CLOSED,
                        reservation=None,
                        reason_codes=("ENTRY_COST_RESERVATION_CONTEXT_MISMATCH",),
                        mutated=False,
                    )
                if (
                    self._store is not None
                    and json.loads(
                        json.loads(detached_sizing.entry_cost_binding.observation_json)[
                            "bound_instrument_json"
                        ]
                    )
                    != self._lane_bindings[str(slot)]["bound"]
                ):
                    return self._result_locked(
                        disposition=ReserveDispositionV1.FAIL_CLOSED,
                        reservation=None,
                        reason_codes=("ENTRY_COST_ORIGINAL_BOUND_INSTRUMENT_MISMATCH",),
                        mutated=False,
                    )
            if (
                detached_sizing is not None
                and detached_sizing.native_initial_margin_binding is not None
            ):
                from .native_initial_margin_v1 import require_native_margin_locked_v1
                from .entry_execution_cost_v1 import utc_now_iso_v1

                try:
                    require_native_margin_locked_v1(
                        self,
                        detached_sizing,
                        evaluated_at_utc=utc_now_iso_v1(),
                    )
                    if detached_sizing.absolute_movement_cost_binding is not None:
                        detached_sizing.absolute_movement_cost_binding.validate_v1(
                            sizing=detached_sizing, evaluated_at_utc=utc_now_iso_v1()
                        )
                except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError) as exc:
                    return self._result_locked(
                        disposition=ReserveDispositionV1.DENIED,
                        reservation=None,
                        reason_codes=(str(exc), "NO_PARTIAL_MUTATION"),
                        mutated=False,
                    )
            if self._held_capital_locked() + money + fee + closing_cost + funding_cost > ceiling:
                return self._result_locked(
                    disposition=ReserveDispositionV1.DENIED,
                    reservation=None,
                    reason_codes=("ENTRY_COST_CAPITAL_WITH_FEES_EXCEEDED", "NO_PARTIAL_MUTATION"),
                    mutated=False,
                )
            reservation = CapitalReservationV1(
                reservation_id=reservation_id,
                slot_id=slot,
                decision_id=decision,
                cycle_id=cycle,
                observation_id=observed,
                amount=money,
                state=ReservationStateV1.RESERVED,
                transition_trace=(
                    ReservationStateV1.REQUESTED.value,
                    ReservationStateV1.RESERVED.value,
                ),
                terminal_reason="",
                venue_fill_integrated=False,
            )
            handoff_request = None
            if handoff_journal is not None:
                from src.ops.bounded_peaktrade_system_composition_v1.recovery_v1 import (
                    prepare_original_risk_reservation_handoff_v1,
                )

                if detached_sizing is None or detached_sizing.risk_binding is None:
                    raise PortfolioCapitalBudgetError("HANDOFF_REQUIRES_BOUND_RISK_RESERVATION")
                handoff_request = prepare_original_risk_reservation_handoff_v1(
                    handoff_journal,
                    risk_binding=detached_sizing.risk_binding,
                    reservation=reservation,
                )
            self._by_key[key] = reservation
            self._by_id[str(reservation_id)] = key
            if self._store is not None:
                self._reservation_bindings[key] = dict(self._lane_bindings[str(slot)])
            if self._active_sum_locked() > self._budget:
                del self._by_key[key]
                del self._by_id[str(reservation_id)]
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=("POST_INSERT_INVARIANT_ROLLBACK",),
                    mutated=False,
                )
            if detached_sizing is not None:
                self._sizing_bindings[key] = detached_sizing
            result = self._result_locked(
                disposition=ReserveDispositionV1.ADMITTED,
                reservation=reservation,
                reason_codes=("RESERVED",),
                mutated=True,
            )
            if handoff_request is not None:
                from src.ops.bounded_peaktrade_system_composition_v1.recovery_v1 import (
                    reservation_readback_digest_v1,
                )

                try:
                    ack = handoff_journal.inspect_original_readback_v1(
                        handoff_request,
                        verified_original_output_digest=reservation_readback_digest_v1(
                            self._by_key[key]
                        ),
                    )
                    if ack["status"] != "ACKNOWLEDGED":
                        raise ValueError("HANDOFF_OWNER_COMMIT_UNACKNOWLEDGED")
                except BaseException as exc:
                    self._admitted = False
                    self._recovery_required = True
                    raise PortfolioCapitalBudgetError(
                        "HANDOFF_BUDGET_COMMITTED_ACK_UNPROVEN"
                    ) from exc
            return result

    def commit_internal_pre_external_effect_v1(self, reservation_id: str) -> ReserveResultV1:
        """Internal hold only. Does not claim a venue fill or order state."""
        with self._lock:
            found = self._require_locked(reservation_id)
            if found is None:
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=("RESERVATION_UNKNOWN",),
                    mutated=False,
                )
            key, current = found
            if current.state is ReservationStateV1.COMMITTED:
                return self._result_locked(
                    disposition=ReserveDispositionV1.IDEMPOTENT_REPLAY,
                    reservation=current,
                    reason_codes=("COMMIT_REPLAY", "VENUE_FILL_NOT_INTEGRATED"),
                    mutated=False,
                )
            if current.state is not ReservationStateV1.RESERVED:
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=current,
                    reason_codes=("COMMIT_REQUIRES_RESERVED", "VENUE_FILL_NOT_INTEGRATED"),
                    mutated=False,
                )
            updated = replace(
                current,
                state=ReservationStateV1.COMMITTED,
                transition_trace=current.transition_trace + (ReservationStateV1.COMMITTED.value,),
                venue_fill_integrated=False,
            )
            self._by_key[key] = updated
            return self._result_locked(
                disposition=ReserveDispositionV1.ADMITTED,
                reservation=updated,
                reason_codes=("COMMITTED_INTERNAL_ONLY", "VENUE_FILL_NOT_INTEGRATED"),
                mutated=True,
            )

    def release_v1(self, reservation_id: str, *, reason: ReleaseReasonV1) -> ReserveResultV1:
        if reason in {
            ReleaseReasonV1.RECONCILED_POSITION_FLAT,
            ReleaseReasonV1.RECONCILED_ENTRY_NO_FILL,
        }:
            return self._closed(("POST_CLOSE_RELEASE_REQUIRES_CANONICAL_CAPITAL_REFRESH",))
        return self._release_locked_public(
            reservation_id, reason=reason, terminal=ReservationStateV1.RELEASED
        )

    def fail_pre_external_effect_v1(self, reservation_id: str) -> ReserveResultV1:
        return self.release_v1(
            reservation_id,
            reason=ReleaseReasonV1.PRE_EXTERNAL_EFFECT_FAILED,
        )

    def cancel_before_external_effect_v1(self, reservation_id: str) -> ReserveResultV1:
        return self.release_v1(
            reservation_id,
            reason=ReleaseReasonV1.EXPLICIT_CANCEL_BEFORE_EXTERNAL_EFFECT,
        )

    def release_plan_failure_v1(self, reservation_id: str) -> ReserveResultV1:
        return self.release_v1(reservation_id, reason=ReleaseReasonV1.PLAN_FAILURE)

    def release_sizing_or_admission_deny_v1(self, reservation_id: str) -> ReserveResultV1:
        return self.release_v1(reservation_id, reason=ReleaseReasonV1.SIZING_OR_ADMISSION_DENY)

    def execution_links_v1(self, *, active_only=False) -> dict:
        from .execution_v1 import detached

        with self._lock:
            return detached(
                {
                    rid: link
                    for rid, link in self._execution_links.items()
                    if not active_only or self._by_key[self._by_id[rid]].counts_against_budget
                }
            )

    def bind_execution_plan_v1(
        self,
        reservation_id,
        envelope,
        *,
        canonical_intent=None,
        venue_plan=None,
        core_parent=None,
        core_cursor_root=None,
        entry_frame_required=False,
    ):
        from .execution_v1 import bind_plan_locked_v1

        with self._lock:
            return bind_plan_locked_v1(
                self,
                str(reservation_id),
                envelope,
                canonical_intent=canonical_intent,
                venue_plan=venue_plan,
                core_parent=core_parent,
                core_cursor_root=core_cursor_root,
                entry_frame_required=entry_frame_required,
            )

    def mark_execution_submit_boundary_v1(
        self, reservation_id, identity, *, external_effect_permit=None
    ):
        from .execution_v1 import mark_submit_locked_v1

        with self._lock:
            return mark_submit_locked_v1(
                self, str(reservation_id), identity, external_effect_permit=external_effect_permit
            )

    def execution_plan_context_v1(self, reservation_id, envelope):
        from .attempt_v2 import plan_context_locked_v1

        with self._lock:
            return plan_context_locked_v1(self, str(reservation_id), envelope)

    def inspect_execution_plan_context_v1(self, reservation_id, envelope, context):
        from .attempt_v2 import inspect_plan_context_locked_v1

        with self._lock:
            return inspect_plan_context_locked_v1(self, str(reservation_id), envelope, context)

    def begin_execution_submit_v2(
        self, reservation_id, envelope, context, permit, *, transport_store_root=None
    ):
        from .attempt_v2 import begin_submit_locked_v2

        with self._lock:
            return begin_submit_locked_v2(
                self,
                str(reservation_id),
                envelope,
                context,
                permit,
                transport_store_root=transport_store_root,
            )

    def inspect_started_execution_attempt_v2(self, reservation_id, envelope, identity, permit):
        from .attempt_v2 import inspect_started_attempt_locked_v2

        with self._lock:
            return inspect_started_attempt_locked_v2(
                self, str(reservation_id), envelope, identity, permit
            )

    def inspect_started_execution_attempt_v1(self, reservation_id, envelope, identity, permit):
        """Current admission/readback for the actual retained V1 or V2 identity.

        Reuses the original started-attempt reader. Does not upgrade a legacy
        identity, change state, refresh financial facts or create authority.
        """
        from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
            FullCoreExchangeReconciliationIdentityV1,
            PortfolioExecutionReconciliationIdentityV2,
        )
        from .attempt_v2 import inspect_started_attempt_locked_v2

        if type(identity) not in {
            FullCoreExchangeReconciliationIdentityV1,
            PortfolioExecutionReconciliationIdentityV2,
        }:
            raise ValueError("EXECUTION_IDENTITY_TYPE_INVALID")
        with self._lock:
            return inspect_started_attempt_locked_v2(
                self, str(reservation_id), envelope, identity, permit
            )

    def inspect_execution_submit_context_v1(self, reservation_id, envelope, identity):
        """Original committed-plan predicates under lock; no submit or new authority."""
        from .execution_v1 import inspect_submit_context_locked_v1

        with self._lock:
            return inspect_submit_context_locked_v1(self, str(reservation_id), envelope, identity)

    def inspect_current_entry_budget_policy_v1(
        self, reservation_id, envelope, *, futures_financial_custody=None
    ):
        """Inspect current Ops ceilings and the selected financial policy for this hold."""
        from src.ops.full_core_live_path_composition_root_v1.current_productive_entry_budget_policy_v1 import (
            load_entry_budget_policy_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
            assert_envelope_unmodified_v1,
        )

        liquidation_snapshot = None
        if getattr(self._entry_budget_policy, "require_xperp_liquidation_projection", False):
            from .xperp_liquidation_projection_v1 import capture_liquidation_custody_v1

            try:
                liquidation_snapshot = capture_liquidation_custody_v1(
                    self, futures_financial_custody, candidate_id=str(reservation_id)
                )
            except (TypeError, KeyError, AttributeError, ArithmeticError, RuntimeError) as exc:
                raise ValueError("XPERP_LIQUIDATION_CURRENT_CUSTODY_UNAVAILABLE") from exc
        elif futures_financial_custody is not None:
            raise ValueError("XPERP_LIQUIDATION_EXPLICIT_POLICY_REQUIRED")
        with self._lock:
            found = self._require_locked(reservation_id)
            if (
                found is None
                or self._store is None
                or not self._admitted
                or found[1].state is not ReservationStateV1.COMMITTED
            ):
                raise ValueError("CURRENT_ENTRY_BUDGET_ORIGINAL_OWNER_FENCED")
            assert_envelope_unmodified_v1(envelope)
            link = self._execution_links.get(str(reservation_id))
            if not link or link["envelope"] != envelope.to_runtime_json_v1():
                raise ValueError("CURRENT_ENTRY_BUDGET_ORIGINAL_PLAN_MISMATCH")
            policy = load_entry_budget_policy_v1()
            if self._capital_scope["settlement_currency"] != policy.currency:
                raise ValueError("CURRENT_ENTRY_BUDGET_CURRENCY_MISMATCH")
            amount, aggregate = found[1].amount, self._active_sum_locked()
            if amount > policy.per_entry_notional_limit:
                raise ValueError("CURRENT_ENTRY_BUDGET_PER_ENTRY_LIMIT_EXCEEDED")
            if aggregate > policy.aggregate_reserved_notional_limit:
                raise ValueError("CURRENT_ENTRY_BUDGET_AGGREGATE_LIMIT_EXCEEDED")
            from .open_slot_cost_renewal_v1 import entry_blocker_locked_v1

            renewal_blocker = entry_blocker_locked_v1(self)
            if renewal_blocker is not None:
                raise ValueError("CURRENT_ENTRY_BUDGET:" + renewal_blocker)
            sizing = self._sizing_bindings.get(str(reservation_id))
            liquidation_result = {}
            if liquidation_snapshot is not None:
                from .entry_execution_cost_v1 import utc_now_iso_v1
                from .local_commitment_readback_v1 import read_local_commitments_locked_v1
                from .xperp_liquidation_projection_v1 import assess_xperp_liquidation_v1

                if sizing is None or sizing.xperp_liquidation_binding is None:
                    raise ValueError("XPERP_LIQUIDATION_ORIGINAL_PROJECTION_REQUIRED")
                if (
                    liquidation_snapshot["local_generation"]
                    != read_local_commitments_locked_v1(self).generation_digest
                ):
                    raise ValueError("XPERP_LIQUIDATION_LOCAL_GENERATION_CHANGED")
                liquidation_result["xperp_liquidation_projection"] = assess_xperp_liquidation_v1(
                    liquidation_snapshot, sizing=sizing, evaluated_at_utc=utc_now_iso_v1()
                )
            if sizing is not None and sizing.entry_cost_binding is not None:
                from .entry_execution_cost_v1 import (
                    EntryExecutionCostObservationV1,
                    assess_opening_execution_cost_v1,
                    utc_now_iso_v1,
                )

                receipt = json.loads(sizing.entry_cost_binding.receipt_json)
                assess_opening_execution_cost_v1(
                    EntryExecutionCostObservationV1.from_dict_v1(
                        json.loads(sizing.entry_cost_binding.observation_json)
                    ),
                    monetary_source=sizing.monetary_source,
                    applied_input=sizing.applied_input,
                    decision=sizing.decision,
                    account_identity=self._account_identity,
                    slot_id=receipt["slot_id"],
                    cycle_id=receipt["cycle_id"],
                    evaluated_at_utc=utc_now_iso_v1(),
                )
                if sizing.close_cost_binding is not None:
                    from .entry_execution_cost_v1 import assess_closing_execution_cost_v1

                    sizing.close_cost_binding.validate_v1(
                        entry_binding=sizing.entry_cost_binding,
                        monetary_source=sizing.monetary_source,
                        applied_input=sizing.applied_input,
                        decision=sizing.decision,
                    )
                    assess_closing_execution_cost_v1(
                        sizing.entry_cost_binding,
                        monetary_source=sizing.monetary_source,
                        applied_input=sizing.applied_input,
                        decision=sizing.decision,
                        evaluated_at_utc=utc_now_iso_v1(),
                    )
                if sizing.funding_cost_binding is not None:
                    from .entry_execution_cost_v1 import (
                        FundingCostObservationV1,
                        assess_next_funding_cost_v1,
                    )

                    sizing.funding_cost_binding.validate_v1(
                        entry_binding=sizing.entry_cost_binding,
                        close_binding=sizing.close_cost_binding,
                        monetary_source=sizing.monetary_source,
                        applied_input=sizing.applied_input,
                        decision=sizing.decision,
                    )
                    assess_next_funding_cost_v1(
                        FundingCostObservationV1.from_dict_v1(
                            json.loads(sizing.funding_cost_binding.observation_json)
                        ),
                        entry_binding=sizing.entry_cost_binding,
                        close_binding=sizing.close_cost_binding,
                        monetary_source=sizing.monetary_source,
                        applied_input=sizing.applied_input,
                        decision=sizing.decision,
                        evaluated_at_utc=utc_now_iso_v1(),
                    )
            if (
                sizing is not None
                and sizing.native_initial_margin_binding is not None
                or self._entry_budget_policy is not None
                and self._entry_budget_policy.require_native_initial_margin
            ):
                from .native_initial_margin_v1 import require_native_margin_locked_v1
                from .entry_execution_cost_v1 import utc_now_iso_v1

                require_native_margin_locked_v1(
                    self,
                    sizing,
                    exclude_reservation_id=str(reservation_id),
                    evaluated_at_utc=utc_now_iso_v1(),
                )
            if self._held_capital_locked() > self._budget:
                raise ValueError("CURRENT_ENTRY_BUDGET_OPENING_FEES_UNCOVERED")
            if getattr(self._entry_budget_policy, "require_absolute_movement_cost_cover", False):
                from .entry_execution_cost_v1 import utc_now_iso_v1

                if sizing is None or sizing.absolute_movement_cost_binding is None:
                    raise ValueError("ABSOLUTE_MOVEMENT_COST_SOURCES_REQUIRED")
                sizing.absolute_movement_cost_binding.validate_v1(
                    sizing=sizing, evaluated_at_utc=utc_now_iso_v1()
                )
            if self._entry_budget_policy is not None:
                bound = self._entry_budget_policy
                slot = str(found[1].slot_id)
                if bound.enforce_open_slot_loss_protection:
                    blocker = self._test_slot_loss_entry_blocker_locked(slot)
                    if blocker is not None:
                        raise ValueError("CURRENT_ENTRY_BUDGET:" + blocker)
                if bound.allowed_slot_ids is not None and slot not in bound.allowed_slot_ids:
                    raise ValueError("CURRENT_ENTRY_BUDGET_SLOT_NOT_ALLOWED")
                if (
                    bound.per_slot_reserved_notional_limit is not None
                    and self._active_sum_locked(slot) > bound.per_slot_reserved_notional_limit
                ):
                    raise ValueError("CURRENT_ENTRY_BUDGET_SLOT_LIMIT_EXCEEDED")
                if (
                    amount > bound.per_entry_notional_limit
                    or aggregate > bound.aggregate_reserved_notional_limit
                ):
                    raise ValueError("CURRENT_ENTRY_BUDGET_BOUND_POLICY_LIMIT_EXCEEDED")
            return {
                "scope": "CURRENT_ORIGINAL_ENTRY_BUDGET_POLICY_ONLY",
                "policy_digest": policy.digest_v1(),
                "currency": policy.currency,
                "reserved_notional": str(amount),
                "aggregate_reserved_notional": str(aggregate),
                **liquidation_result,
            }

    def inspect_current_core_cursor_v1(self, reservation_id, envelope):
        """Read only the cursor pinned by the original N1 plan writer."""
        from .core_cursor_source_v1 import inspect_current_core_cursor_v1
        from .execution_v1 import validate_link_v1
        from .plan_origin_v1 import CORE_CURSOR_SCHEMA

        with self._lock:
            found = self._require_locked(reservation_id)
            if (
                found is None
                or not self._admitted
                or found[1].state is not ReservationStateV1.COMMITTED
            ):
                raise ValueError("CURRENT_CORE_CURSOR_ORIGINAL_OWNER_FENCED")
            link = self._execution_links.get(str(reservation_id))
            if not link or link["envelope"] != envelope.to_runtime_json_v1():
                raise ValueError("CURRENT_CORE_CURSOR_ORIGINAL_PLAN_MISMATCH")
            validate_link_v1(self, str(reservation_id), link)
            origin = link.get("plan_origin", {})
            if origin.get("schema") != CORE_CURSOR_SCHEMA:
                return {"scope": "LEGACY_ORIGINAL_CORE_CURSOR_NOT_ASSESSED"}
            return inspect_current_core_cursor_v1(
                origin["core_cursor_source"], intent_side=origin["canonical_order_intent"]["side"]
            )

    def reconcile_execution_v1(self, reservation_id, **kwargs):
        from .execution_v1 import reconcile_locked_v1

        with self._lock:
            return reconcile_locked_v1(self, str(reservation_id), **kwargs)

    def restart_fail_closed_v1(self) -> ReserveResultV1:
        """Fence recovery; durable holds survive, legacy memory state is dropped."""
        with self._lock:
            self._admitted = False
            if self._closed_owner or self._storage_failed:
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=("DURABLE_WRITER_UNAVAILABLE_REOPEN_REQUIRED",),
                    mutated=False,
                )
            if self._store is not None:
                self._recovery_required = True
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=("DURABLE_HOLDS_RETAINED_RECONCILIATION_REQUIRED",),
                    mutated=True,
                )
            self._budget = Decimal("0")
            self._observation_id = ""
            self._by_key = {}
            self._by_id = {}
            self._account_identity = ""
            self._close_refreshes = {}
            self._sizing_bindings = {}
            self._execution_links = {}
            return self._result_locked(
                disposition=ReserveDispositionV1.FAIL_CLOSED,
                reservation=None,
                reason_codes=("RESTART_WITHOUT_CANONICAL_STATE",),
                mutated=True,
            )

    def reject_unproven_restore_v1(self, payload: object) -> None:
        _ = payload
        raise PortfolioCapitalBudgetError("UNPROVEN_RESTART_RESTORE_FORBIDDEN")

    def _release_locked_public(
        self,
        reservation_id: str,
        *,
        reason: ReleaseReasonV1,
        terminal: ReservationStateV1,
    ) -> ReserveResultV1:
        with self._lock:
            found = self._require_locked(reservation_id)
            if found is None:
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=("RESERVATION_UNKNOWN",),
                    mutated=False,
                )
            key, current = found
            if (
                self._execution_links.get(str(reservation_id), {}).get("phase")
                == "SUBMIT_MAY_HAVE_OCCURRED"
            ):
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=current,
                    reason_codes=("EXECUTION_RECONCILIATION_REQUIRED",),
                    mutated=False,
                )
            if current.state.value in _TERMINAL:
                return self._result_locked(
                    disposition=ReserveDispositionV1.IDEMPOTENT_REPLAY,
                    reservation=current,
                    reason_codes=("TERMINAL_REPLAY_NO_DOUBLE_EFFECT",),
                    mutated=False,
                )
            if current.state.value not in _ACTIVE:
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=current,
                    reason_codes=("RELEASE_STATE_INVALID",),
                    mutated=False,
                )
            updated = replace(
                current,
                state=terminal,
                transition_trace=current.transition_trace + (terminal.value,),
                terminal_reason=reason.value,
                venue_fill_integrated=False,
            )
            self._by_key[key] = updated
            return self._result_locked(
                disposition=ReserveDispositionV1.ADMITTED,
                reservation=updated,
                reason_codes=(reason.value, terminal.value),
                mutated=True,
            )

    def _expire_active_locked(self, state: ReservationStateV1, reason: ReleaseReasonV1) -> None:
        for key, current in list(self._by_key.items()):
            if current.state.value not in _ACTIVE:
                continue
            self._by_key[key] = replace(
                current,
                state=state,
                transition_trace=current.transition_trace + (state.value,),
                terminal_reason=reason.value,
                venue_fill_integrated=False,
            )

    def _require_locked(self, reservation_id: str) -> tuple[str, CapitalReservationV1] | None:
        if self._closed_owner or self._storage_failed or self._recovery_required:
            return None
        key = self._by_id.get(str(reservation_id or ""))
        if key is None:
            return None
        current = self._by_key.get(key)
        if current is None:
            return None
        return key, current

    def _active_sum_locked(self, slot_id: str | None = None) -> Decimal:
        from .open_slot_cost_renewal_v1 import enabled, sum_money_v1

        if enabled(self):
            return sum_money_v1(
                r.amount
                for r in self._by_key.values()
                if r.counts_against_budget and (slot_id is None or str(r.slot_id) == slot_id)
            )
        total = Decimal("0")
        for reservation in self._by_key.values():
            if reservation.counts_against_budget and (
                slot_id is None or str(reservation.slot_id) == slot_id
            ):
                total += reservation.amount
        return total

    def _opening_fee_sum_locked(self, slot_id=None):
        from .entry_execution_cost_v1 import reserved_opening_fee_v1
        from .open_slot_cost_renewal_v1 import enabled, sum_money_v1

        return (sum_money_v1 if enabled(self) else sum)(
            (
                reserved_opening_fee_v1(self._sizing_bindings.get(key))
                for key, record in self._by_key.items()
                if record.counts_against_budget
                and (slot_id is None or str(record.slot_id) == slot_id)
            ),
            Decimal(0),
        )

    def _held_capital_locked(self):
        from .open_slot_cost_renewal_v1 import enabled, sum_money_v1

        if enabled(self):
            return sum_money_v1(
                (
                    self._active_sum_locked(),
                    self._opening_fee_sum_locked(),
                    self._closing_cost_sum_locked(),
                    self._funding_cost_sum_locked(),
                )
            )
        return (
            self._active_sum_locked()
            + self._opening_fee_sum_locked()
            + self._closing_cost_sum_locked()
            + self._funding_cost_sum_locked()
        )

    def _funding_cost_sum_locked(self, slot_id=None):
        from .open_slot_cost_renewal_v1 import enabled, sum_money_v1

        return (sum_money_v1 if enabled(self) else sum)(
            (
                self._reservation_cost_reserves_locked_v1(key)[1]
                for key, record in self._by_key.items()
                if record.counts_against_budget
                and (slot_id is None or str(record.slot_id) == slot_id)
            ),
            Decimal(0),
        )

    def _closing_cost_sum_locked(self, slot_id=None):
        from .open_slot_cost_renewal_v1 import enabled, sum_money_v1

        return (sum_money_v1 if enabled(self) else sum)(
            (
                self._reservation_cost_reserves_locked_v1(key)[0]
                for key, record in self._by_key.items()
                if record.counts_against_budget
                and (slot_id is None or str(record.slot_id) == slot_id)
            ),
            Decimal(0),
        )

    def _reservation_cost_reserves_locked_v1(self, rid):
        from .entry_execution_cost_v1 import reserved_closing_cost_v1, reserved_funding_cost_v1
        from .open_slot_cost_renewal_v1 import enabled, effective_reserve_v1

        if enabled(self):
            return effective_reserve_v1(self, rid)[:2]
        binding = self._sizing_bindings.get(rid)
        return reserved_closing_cost_v1(binding), reserved_funding_cost_v1(binding)

    def _entry_budget_denial_locked(self, slot_id, amount):
        policy = self._entry_budget_policy
        if policy is None:
            return None
        if policy.allowed_slot_ids is not None and slot_id not in policy.allowed_slot_ids:
            return "ENTRY_BUDGET_SLOT_NOT_ALLOWED"
        from .open_slot_cost_renewal_v1 import entry_blocker_locked_v1

        renewal_blocker = entry_blocker_locked_v1(self)
        if renewal_blocker is not None:
            return renewal_blocker

        loss_reason = self._test_slot_loss_entry_blocker_locked(slot_id)
        if loss_reason is not None:
            return loss_reason
        if amount > policy.per_entry_notional_limit:
            return "ENTRY_BUDGET_PER_ENTRY_LIMIT_EXCEEDED"
        if (
            policy.per_slot_reserved_notional_limit is not None
            and self._active_sum_locked(slot_id) + amount > policy.per_slot_reserved_notional_limit
        ):
            return "ENTRY_BUDGET_SLOT_LIMIT_EXCEEDED"
        if self._active_sum_locked() + amount > policy.aggregate_reserved_notional_limit:
            return "ENTRY_BUDGET_AGGREGATE_LIMIT_EXCEEDED"
        return None

    def _durable_payload_locked(self) -> dict:
        return {
            "schema": SCHEMA,
            "account_identity": self._account_identity,
            "capital_scope": self._capital_scope,
            "budget": str(self._budget),
            **(
                {"entry_budget_policy": self._entry_budget_policy.to_dict_v1()}
                if self._entry_budget_policy is not None
                else {}
            ),
            **(
                {"test_slot_economics": self._slot_test_economics}
                if self._entry_budget_policy is not None
                and self._entry_budget_policy.per_slot_test_loss_limit is not None
                else {}
            ),
            **(
                {"open_slot_protection": self._open_slot_protection}
                if self._entry_budget_policy is not None
                and self._entry_budget_policy.enforce_open_slot_loss_protection
                else {}
            ),
            "observation_id": self._observation_id,
            **(
                {"open_slot_cost_reserves": self._open_slot_cost_reserves}
                if self._entry_budget_policy is not None
                and self._entry_budget_policy.renew_open_slot_cost_reserves
                else {}
            ),
            "lane_bindings": self._lane_bindings,
            "close_refreshes": self._close_refreshes,
            "sizing_bindings": {
                key: binding.to_dict_v1() for key, binding in self._sizing_bindings.items()
            },
            "execution_links": self._execution_links,
            "reservations": [
                {
                    "reservation_id": str(r.reservation_id),
                    "slot_id": str(r.slot_id),
                    "decision_id": r.decision_id,
                    "cycle_id": r.cycle_id,
                    "observation_id": r.observation_id,
                    "amount": str(r.amount),
                    "state": r.state.value,
                    "transition_trace": list(r.transition_trace),
                    "terminal_reason": r.terminal_reason,
                    "binding": self._reservation_bindings[str(r.reservation_id)],
                }
                for r in sorted(self._by_key.values(), key=lambda x: str(x.reservation_id))
            ],
        }

    def _risk_snapshot_locked(self):
        from .durable_store_v1 import digest

        if self._store is None or self._closed_owner or self._storage_failed:
            raise PortfolioCapitalBudgetError("RISK_DURABLE_OWNER_REQUIRED")
        # The store head binds all original history, including risk records.
        # Project only the operands needed by the next model, avoiding recursively
        # embedding every previous snapshot inside the next receipt.
        state = json.loads(json.dumps(self._durable_payload_locked()))
        for binding in state["sizing_bindings"].values():
            binding.pop("risk_binding", None)
            binding["schema"] = (
                "reservation_sizing_binding.v9"
                if "xperp_liquidation_binding" in binding
                else "reservation_sizing_binding.v8"
                if "absolute_movement_cost_binding" in binding
                else "reservation_sizing_binding.v7"
                if "native_initial_margin_binding" in binding
                else "reservation_sizing_binding.v6"
                if "funding_cost_binding" in binding
                else "reservation_sizing_binding.v5"
                if "close_cost_binding" in binding
                else "reservation_sizing_binding.v4"
                if "entry_cost_binding" in binding
                else "reservation_sizing_binding.v3"
                if "monetary_source" in binding
                else "reservation_sizing_binding.v1"
            )
        payload = {
            "schema": "portfolio_risk_owner_snapshot.v1",
            "state": state,
            "durable_head": self._store.head,
            "admitted": self._admitted,
            "recovery_required": self._recovery_required,
        }
        return {**payload, "digest": digest(payload)}

    def risk_snapshot_v1(self):
        """Detached read under this original owner's lock, not another owner."""
        with self._lock:
            return self._risk_snapshot_locked()

    def reservation_risk_binding_v1(self, reservation_id):
        from .restrictive_risk_binding_v1 import RiskAdmissionBindingV1

        with self._lock:
            key = self._by_id.get(str(reservation_id))
            sizing = self._sizing_bindings.get(key)
            if sizing is None or sizing.risk_binding is None:
                raise PortfolioCapitalBudgetError("RESERVATION_RISK_BINDING_MISSING")
            retained = RiskAdmissionBindingV1.from_dict_v1(sizing.risk_binding.to_dict_v1())
            retained.validate_v1(
                amount=self._by_key[key].amount, decision_id=self._by_key[key].decision_id
            )
            return retained

    def _persist_locked(self) -> None:
        if self._storage_failed or self._closed_owner:
            raise PortfolioCapitalBudgetError("DURABLE_WRITER_UNAVAILABLE_REOPEN_REQUIRED")
        try:
            self._store.save(self._durable_payload_locked())
        except Exception as exc:
            # A failed acknowledgement cannot establish whether the commit won.
            # Reopen/replay the store before any further economic mutation.
            self._admitted = False
            self._recovery_required = True
            self._storage_failed = True
            raise PortfolioCapitalBudgetError(
                "DURABLE_BUDGET_COMMIT_UNPROVEN_REOPEN_REQUIRED"
            ) from exc

    def _restore_locked(self, payload: Mapping) -> None:
        try:
            if set(payload) - {
                "sizing_bindings",
                "execution_links",
                "entry_budget_policy",
                "test_slot_economics",
                "open_slot_protection",
                "open_slot_cost_reserves",
            } != {
                "schema",
                "account_identity",
                "capital_scope",
                "budget",
                "observation_id",
                "lane_bindings",
                "close_refreshes",
                "reservations",
            }:
                raise ValueError("shape")
            from .test_phase_limits_v1 import (
                parse_slot_entry_budget_v1,
            )

            stored_policy = (
                parse_slot_entry_budget_v1(payload["entry_budget_policy"])
                if "entry_budget_policy" in payload
                else None
            )
            if self._entry_budget_policy is not None and (
                stored_policy is None
                or stored_policy.digest_v1() != self._entry_budget_policy.digest_v1()
            ):
                raise ValueError("entry policy cannot be replaced during recovery")
            self._entry_budget_policy = stored_policy
            if payload["schema"] != SCHEMA or payload["account_identity"] != self._account_identity:
                raise ValueError("scope")
            budget = Decimal(payload["budget"])
            observation = payload["observation_id"]
            if not isinstance(payload["budget"], str) or not budget.is_finite() or budget < 0:
                raise ValueError("budget")
            if (budget > 0 and not _digest_identity_v1(observation)) or (
                budget == 0 and observation != ""
            ):
                raise ValueError("observation")
            # Rebuild the same typed binding identities, not arbitrary JSON flags.
            from .recovery_v1 import validate_stored_bindings_v1

            bindings = validate_stored_bindings_v1(payload["lane_bindings"])
            scope = payload["capital_scope"]
            scope_keys = {
                "bound_venue_identity",
                "bound_td_mode",
                "settlement_currency",
                "dimension_id",
                "producer_identity",
                "output_unit",
            }
            if (
                budget > 0
                and (
                    not isinstance(scope, dict)
                    or set(scope) != scope_keys
                    or not all(isinstance(x, str) and x and x == x.strip() for x in scope.values())
                )
            ) or (budget == 0 and scope != {}):
                raise ValueError("capital scope")
            records, frozen = {}, {}
            for row in payload["reservations"]:
                if set(row) != {
                    "reservation_id",
                    "slot_id",
                    "decision_id",
                    "cycle_id",
                    "observation_id",
                    "amount",
                    "state",
                    "transition_trace",
                    "terminal_reason",
                    "binding",
                }:
                    raise ValueError("reservation shape")
                slot = SlotId(row["slot_id"])
                decision, cycle, obs = row["decision_id"], row["cycle_id"], row["observation_id"]
                if not all(
                    isinstance(x, str) and x and x == x.strip() for x in (decision, cycle)
                ) or not _digest_identity_v1(obs):
                    raise ValueError("causal identity")
                key = _reservation_key(
                    slot_id=slot, decision_id=decision, cycle_id=cycle, observation_id=obs
                )
                if ReservationId(row["reservation_id"]) != key or key in records:
                    raise ValueError("reservation identity")
                amount = _positive_decimal(row["amount"])
                if amount is None:
                    raise ValueError("amount")
                state = ReservationStateV1(row["state"])
                trace = tuple(row["transition_trace"])
                prefix = ("REQUESTED", "RESERVED")
                valid = {prefix, prefix + ("COMMITTED",)}
                valid |= {p + (terminal,) for p in tuple(valid) for terminal in _TERMINAL}
                if trace not in valid or trace[-1] != state.value:
                    raise ValueError("transition trace")
                reason = row["terminal_reason"]
                if (state.value in _ACTIVE and reason != "") or (
                    state.value in _TERMINAL and reason not in {x.value for x in ReleaseReasonV1}
                ):
                    raise ValueError("terminal reason")
                frozen[key] = validate_stored_bindings_v1({str(slot): row["binding"]})[str(slot)]
                if state.value in _ACTIVE and bindings.get(str(slot)) != frozen[key]:
                    raise ValueError("active binding")
                records[key] = CapitalReservationV1(
                    ReservationId(key), slot, decision, cycle, obs, amount, state, trace, reason
                )
            markers = payload["close_refreshes"]
            if not isinstance(markers, dict) or not all(
                _digest_identity_v1(k) and _digest_identity_v1(v) for k, v in markers.items()
            ):
                raise ValueError("close replay markers")
            if (
                sum((r.amount for r in records.values() if r.counts_against_budget), Decimal(0))
                > budget
            ):
                raise ValueError("held budget invariant")
            self._budget, self._observation_id = budget, observation
            self._capital_scope = dict(scope)
            self._lane_bindings, self._reservation_bindings = bindings, frozen
            self._by_key, self._by_id = records, {key: key for key in records}
            self._close_refreshes = dict(markers)
            sizing_bindings = payload.get("sizing_bindings", {})
            if not isinstance(sizing_bindings, dict) or set(sizing_bindings) - set(records):
                raise ValueError("sizing binding reservation identity")
            restored_sizing = {}
            for key, raw in sizing_bindings.items():
                binding = ReservationSizingBindingV1.from_dict_v1(raw)
                binding.validate_v1(
                    amount=records[key].amount, decision_id=records[key].decision_id
                )
                restored_sizing[key] = binding
            self._sizing_bindings = restored_sizing
            if getattr(
                self._entry_budget_policy, "require_xperp_liquidation_projection", False
            ) and any(
                r.counts_against_budget
                and (
                    key not in restored_sizing
                    or restored_sizing[key].xperp_liquidation_binding is None
                )
                for key, r in records.items()
            ):
                raise ValueError("required xperp liquidation binding missing on active hold")
            if getattr(
                self._entry_budget_policy, "require_absolute_movement_cost_cover", False
            ) and any(
                r.counts_against_budget
                and (
                    key not in restored_sizing
                    or restored_sizing[key].absolute_movement_cost_binding is None
                )
                for key, r in records.items()
            ):
                raise ValueError("required movement cost binding missing on active hold")
            if (
                self._entry_budget_policy is not None
                and self._entry_budget_policy.require_native_initial_margin
                and any(
                    r.counts_against_budget
                    and (
                        key not in restored_sizing
                        or restored_sizing[key].native_initial_margin_binding is None
                    )
                    for key, r in records.items()
                )
            ):
                raise ValueError("required native initial margin binding missing on active hold")
            if getattr(self._entry_budget_policy, "require_native_cost_cover", False):
                from .native_cost_cover_v1 import original_costs_v1, _f

                for key, record in records.items():
                    if record.counts_against_budget:
                        margin, costs = original_costs_v1(restored_sizing[key])
                        if (
                            getattr(self._entry_budget_policy, "require_usdc_settlement", False)
                            and margin["settlement_currency"] != "USDC"
                        ):
                            raise ValueError("required USDC settlement missing on active hold")
                        if sum(costs.values()) > _f(margin["available_native"]):
                            raise ValueError(
                                "required original native cost cover missing on active hold"
                            )
            if (
                self._entry_budget_policy is not None
                and self._entry_budget_policy.require_opening_execution_costs
                and any(
                    r.counts_against_budget
                    and (
                        key not in restored_sizing
                        or restored_sizing[key].entry_cost_binding is None
                    )
                    for key, r in records.items()
                )
            ):
                raise ValueError("required opening fee binding missing on active hold")
            if (
                self._entry_budget_policy is not None
                and self._entry_budget_policy.require_closing_execution_costs
                and any(
                    r.counts_against_budget
                    and (
                        key not in restored_sizing
                        or restored_sizing[key].close_cost_binding is None
                    )
                    for key, r in records.items()
                )
            ):
                raise ValueError("required closing cost binding missing on active hold")
            if (
                self._entry_budget_policy is not None
                and self._entry_budget_policy.require_next_funding_costs
                and any(
                    r.counts_against_budget
                    and (
                        key not in restored_sizing
                        or restored_sizing[key].funding_cost_binding is None
                    )
                    for key, r in records.items()
                )
            ):
                raise ValueError("required funding cost binding missing on active hold")
            from .execution_v1 import detached, validate_link_v1

            links = payload.get("execution_links", {})
            if not isinstance(links, dict) or set(links) - set(records):
                raise ValueError("execution reservation identity")
            for reservation_id, link in links.items():
                validate_link_v1(self, reservation_id, link)
            self._execution_links = detached(links)
            from .slot_loss_budget_v1 import restore_state

            self._slot_test_economics = restore_state(self, payload.get("test_slot_economics"))
            from .open_slot_cost_renewal_v1 import restore_reserves_v1

            self._open_slot_cost_reserves = restore_reserves_v1(
                self, payload.get("open_slot_cost_reserves")
            )
            if self._held_capital_locked() > budget:
                raise ValueError("held capital including costs exceeds stored budget")
            from .entry_execution_cost_v1 import restore_open_slot_protection_v1

            self._open_slot_protection = restore_open_slot_protection_v1(
                self, payload.get("open_slot_protection")
            )
            policy = self._entry_budget_policy
            if policy is not None:
                active = [r for r in records.values() if r.counts_against_budget]
                if (
                    self._active_sum_locked() > policy.aggregate_reserved_notional_limit
                    or any(r.amount > policy.per_entry_notional_limit for r in active)
                    or (
                        policy.allowed_slot_ids is not None
                        and any(str(r.slot_id) not in policy.allowed_slot_ids for r in active)
                    )
                    or (
                        policy.per_slot_reserved_notional_limit is not None
                        and any(
                            self._active_sum_locked(str(r.slot_id))
                            > policy.per_slot_reserved_notional_limit
                            for r in active
                        )
                    )
                ):
                    raise ValueError("stored entry policy limits exceeded")
            self._admitted = False
        except (ValueError, TypeError, KeyError, AttributeError, InvalidOperation) as exc:
            raise PortfolioCapitalBudgetError("DURABLE_BUDGET_SEMANTIC_RESTORE_UNPROVEN") from exc

    def _state_locked(self) -> PortfolioBudgetStateV1:
        active = self._active_sum_locked()
        budget = self._budget if self._admitted else Decimal("0")
        fees = self._opening_fee_sum_locked()
        closing_costs = self._closing_cost_sum_locked()
        funding_costs = self._funding_cost_sum_locked()
        # Use the same aggregate as atomic admission/readback. Chained
        # subtraction can round differently at the Decimal context boundary.
        remaining = budget - self._held_capital_locked() if self._admitted else Decimal("0")
        return PortfolioBudgetStateV1(
            admitted=self._admitted,
            observation_id=self._observation_id,
            canonical_available_capital=budget,
            active_reservation_sum=active,
            remaining_unreserved=remaining,
            canonical_restart_reconstructable=CANONICAL_RESTART_RECONSTRUCTABLE,
            reservation_ids=tuple(sorted(self._by_id)),
            recovery_required=self._recovery_required,
            durable_state_enabled=self._store is not None,
            reserved_opening_fees=fees,
            reserved_closing_costs=closing_costs,
            reserved_funding_costs=funding_costs,
        )

    def _result_locked(
        self,
        *,
        disposition: ReserveDispositionV1,
        reservation: CapitalReservationV1 | None,
        reason_codes: tuple[str, ...],
        mutated: bool,
    ) -> ReserveResultV1:
        if mutated and self._store is not None:
            self._persist_locked()
        budget = self._budget if self._admitted else Decimal("0")
        return ReserveResultV1(
            disposition=disposition,
            reservation=reservation,
            reason_codes=reason_codes,
            active_sum_after=self._active_sum_locked(),
            admitted_budget=budget,
            mutated=mutated,
        )

    def _closed(self, reason_codes: tuple[str, ...]) -> ReserveResultV1:
        with self._lock:
            return self._result_locked(
                disposition=ReserveDispositionV1.FAIL_CLOSED,
                reservation=None,
                reason_codes=reason_codes,
                mutated=False,
            )


def capital_context_facts_v1(
    owner: PortfolioCapitalReservationBudgetOwnerV1,
    *,
    slot_id=None,
) -> Mapping[str, Decimal]:
    """Facts the existing sizing seam was missing. Not a second quantity owner."""
    with owner._lock:
        state = owner._state_locked()
        if not state.admitted:
            raise PortfolioCapitalBudgetError("CAPITAL_CONTEXT_REQUIRES_BOUND_PRODUCER_OUTPUT")
        facts = {
            "account_equity": state.canonical_available_capital,
            "already_committed_capital": state.active_reservation_sum
            + state.reserved_opening_fees
            + state.reserved_closing_costs
            + state.reserved_funding_costs,
            "current_reconciled_exposure": state.active_reservation_sum,
        }
        policy = owner._entry_budget_policy
        if policy is not None:
            slot = str(SlotId(str(slot_id)))
            if policy.allowed_slot_ids is not None and slot not in policy.allowed_slot_ids:
                raise PortfolioCapitalBudgetError("ENTRY_BUDGET_SLOT_NOT_ALLOWED")
            from .slot_loss_budget_v1 import enabled, admission_reason, remaining_loss

            if enabled(policy):
                reason = owner._test_slot_loss_entry_blocker_locked(slot)
                if reason is not None:
                    raise PortfolioCapitalBudgetError(reason)
                facts["slot_remaining_loss_allowance"] = remaining_loss(owner, slot)
            remaining = (
                policy.per_slot_reserved_notional_limit - owner._active_sum_locked(slot)
                if policy.per_slot_reserved_notional_limit is not None
                else policy.aggregate_reserved_notional_limit - state.active_reservation_sum
            )
            facts.update(
                entry_notional_ceiling=policy.per_entry_notional_limit,
                slot_remaining_notional=max(remaining, Decimal("0")),
                aggregate_notional_ceiling=policy.aggregate_reserved_notional_limit,
            )
        return facts


def admit_sized_slot_reservation_v1(
    owner: PortfolioCapitalReservationBudgetOwnerV1,
    *,
    observation: CurrentProductiveUsdcFreeMarginObservationV1 | None,
    p01: CurrentProductiveP01ReductionFactV1 | None,
    eligibility: CurrentProductiveAccountEligibilityFactV1 | None,
    slot_id: SlotId | str,
    decision_id: str,
    cycle_id: str,
    instrument_id: str,
    account_identity: str,
    sizing_input: CapitalRiskSizingInputV1,
    fresh_pretrade_get_status: str,
    live_account_bound_status: str,
    fresh_evidence_fetched: bool,
    fresh_evidence_validated: bool,
    restrictive_risk: object | None = None,
    monetary_source: object | None = None,
    opening_cost_observation: object | None = None,
    funding_cost_observation: object | None = None,
    native_initial_margin_observation: object | None = None,
    absolute_movement_cost_observation: object | None = None,
    local_commitment_readback: object | None = None,
    handoff_journal: object | None = None,
    futures_financial_custody: object | None = None,
) -> SizedReservationResultV1:
    """Producer, 29P admissibility, existing sizing, then atomic reserve.

    Sizing runs against a budget snapshot. Admission is only the later atomic
    reserve of ``resulting_notional``. A lost race denies with no partial hold.
    """
    local_generation = None
    if local_commitment_readback is not None:
        try:
            local_generation = owner.require_local_commitment_readback_v1(
                local_commitment_readback, account_identity=account_identity
            )
        except ValueError as exc:
            return _sized_deny(
                owner, disposition=ReserveDispositionV1.FAIL_CLOSED, reason_codes=(str(exc),)
            )
    if not owner.slot_account_binding_matches_v1(
        slot_id=str(slot_id),
        instrument_id=instrument_id,
        account_identity=account_identity,
    ):
        return _sized_deny(
            owner,
            disposition=ReserveDispositionV1.FAIL_CLOSED,
            reason_codes=("DURABLE_SLOT_ACCOUNT_INSTRUMENT_MISMATCH",),
        )
    if handoff_journal is not None and restrictive_risk is None:
        return _sized_deny(
            owner,
            disposition=ReserveDispositionV1.FAIL_CLOSED,
            reason_codes=("HANDOFF_REQUIRES_BOUND_RISK_RESERVATION",),
        )
    output = produce_current_productive_29p_risk_capital_v1(
        observation=observation,
        p01=p01,
        eligibility=eligibility,
        eq_target=None,
        u04=None,
        restart_from_kind_set="false",
    )
    if output.produced != TRUE_TOKEN:
        return _sized_deny(
            owner,
            disposition=ReserveDispositionV1.FAIL_CLOSED,
            reason_codes=tuple(output.reason_codes) + ("PRODUCER_OUTPUT_NOT_ADMITTED",),
        )
    if account_identity != output.bound_account_identity:
        return _sized_deny(
            owner,
            disposition=ReserveDispositionV1.FAIL_CLOSED,
            reason_codes=("ACCOUNT_IDENTITY_MISMATCH",),
        )
    if not str(instrument_id or "").strip():
        return _sized_deny(
            owner,
            disposition=ReserveDispositionV1.FAIL_CLOSED,
            reason_codes=("INSTRUMENT_SCOPE_MISSING",),
        )
    trusted = (
        str(fresh_pretrade_get_status or "").strip()
        == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    )
    bound_trusted = (
        str(live_account_bound_status or "").strip()
        == LiveAccountBoundStatusV1.TRUSTED_PRESENT.value
    )
    claim = bind_step_29p_typed_equity_from_risk_capital_v1(
        output=output,
        fresh_pretrade_get_status=str(fresh_pretrade_get_status or ""),
        live_account_bound_status=str(live_account_bound_status or ""),
        expected_instrument_id=instrument_id,
        observed_instrument_id=instrument_id if trusted else "",
        fresh_evidence_fetched=fresh_evidence_fetched is True,
        fresh_evidence_validated=trusted and bound_trusted and fresh_evidence_validated is True,
    )
    capital = evaluate_capital_admission_v1(
        claim=CapitalAdmissionClaimV1(
            source_class=CAPITAL_SOURCE_OBSERVED_VENUE,
            account_identity=account_identity,
            instrument_id=instrument_id,
            observed_capital_raw=output.value,
            observed_field_name=PRODUCER_IDENTITY,
            evidence_class="LIVE_TYPED",
            evidence_id=output.decision_epoch,
        ),
        expected_account_identity=account_identity,
        expected_instrument_id=instrument_id,
        admission_context=ADMISSION_CONTEXT_LIVE,
    )
    admissibility = evaluate_step_29p_capital_risk_admissibility_v1(capital=capital, claim=claim)
    if admissibility.risk_admissible is not True:
        return _sized_deny(
            owner,
            disposition=ReserveDispositionV1.FAIL_CLOSED,
            reason_codes=tuple(admissibility.reason_codes),
        )
    bound = owner.bind_canonical_producer_output_v1(output)
    if bound.disposition is ReserveDispositionV1.FAIL_CLOSED:
        return _sized_deny(owner, disposition=bound.disposition, reason_codes=bound.reason_codes)
    observation_id = observation_identity_v1(output)
    existing = owner.lookup_v1(
        slot_id=slot_id,
        decision_id=decision_id,
        cycle_id=cycle_id,
        observation_id=observation_id,
    )
    if existing is not None:
        replay = owner.replay_sized_reservation_v1(
            str(existing.reservation_id),
            request=sizing_input,
            risk_request=restrictive_risk,
            opening_cost_observation=opening_cost_observation,
            funding_cost_observation=funding_cost_observation,
            native_initial_margin_observation=native_initial_margin_observation,
            absolute_movement_cost_observation=absolute_movement_cost_observation,
        )
        if (
            handoff_journal is not None
            and replay.disposition is ReserveDispositionV1.IDEMPOTENT_REPLAY
        ):
            from src.ops.bounded_peaktrade_system_composition_v1.handoff_receipts_v1 import (
                OfflineHandoffJournalV1,
            )

            try:
                if type(handoff_journal) is not OfflineHandoffJournalV1:
                    raise ValueError("HANDOFF_ORIGINAL_OPEN_JOURNAL_REQUIRED")
                binding = owner.reservation_risk_binding_v1(existing.reservation_id)
                handoff_journal.require_original_reservation_ack_v1(
                    reservation_id=existing.reservation_id,
                    original_input_digest=binding.owner_snapshot_digest,
                )
            except (ValueError, TypeError, OSError) as exc:
                return _sized_deny(
                    owner, disposition=ReserveDispositionV1.FAIL_CLOSED, reason_codes=(str(exc),)
                )
        return replay
    risk_snapshot = None
    risk_binding = None
    if restrictive_risk is not None:
        from datetime import datetime
        from src.risk.decision_bound_model_adapters_v1 import OfflineRiskRequestV1, number

        try:
            if type(restrictive_risk) is not OfflineRiskRequestV1:
                raise ValueError("RISK_TYPED_COMPLETE_REQUEST_REQUIRED")
            if restrictive_risk.data.as_of_ms != int(
                datetime.fromisoformat(output.decision_epoch.replace("Z", "+00:00")).timestamp()
                * 1000
            ):
                raise ValueError("RISK_CAPITAL_DECISION_CLOCK_MISMATCH")
            if restrictive_risk.configured_quantity_cap is not None:
                number(restrictive_risk.configured_quantity_cap, positive=True)
            risk_snapshot = owner.risk_snapshot_v1()
        except (ValueError, TypeError, AttributeError) as exc:
            return _sized_deny(
                owner, disposition=ReserveDispositionV1.FAIL_CLOSED, reason_codes=(str(exc),)
            )
    try:
        facts = capital_context_facts_v1(owner, slot_id=slot_id)
    except ValueError as exc:
        return _sized_deny(
            owner, disposition=ReserveDispositionV1.FAIL_CLOSED, reason_codes=(str(exc),)
        )
    patched = replace(
        sizing_input,
        account_equity=facts["account_equity"],
        already_committed_capital=facts["already_committed_capital"],
        current_reconciled_exposure=facts["current_reconciled_exposure"],
    )
    if "slot_remaining_notional" in facts:
        patched = replace(
            patched,
            scope_capital_limit=min(
                patched.scope_capital_limit,
                facts["entry_notional_ceiling"],
                facts["slot_remaining_notional"],
            ),
            total_capital_limit=min(
                patched.total_capital_limit, facts["aggregate_notional_ceiling"]
            ),
        )
    if "slot_remaining_loss_allowance" in facts:
        patched = replace(
            patched,
            per_trade_risk_limit=min(
                patched.per_trade_risk_limit, facts["slot_remaining_loss_allowance"]
            ),
        )
    if restrictive_risk is not None and restrictive_risk.configured_quantity_cap is not None:
        cap = restrictive_risk.configured_quantity_cap
        patched = replace(
            patched,
            configured_quantity_cap=min(cap, patched.configured_quantity_cap)
            if patched.configured_quantity_cap is not None
            else cap,
        )
    decision = evaluate_capital_risk_sizing_v1(patched)
    if (
        decision.outcome is not CapitalRiskSizingOutcome.PASS
        or decision.canonical_position_sizing is None
    ):
        return _sized_deny(
            owner,
            disposition=ReserveDispositionV1.DENIED,
            reason_codes=tuple(decision.reason_codes) + ("SIZING_DENIED_NO_RESERVATION",),
            sizing_decision=decision,
        )
    amount = decision.canonical_position_sizing.resulting_notional
    entry_cost_binding = None
    policy = owner.entry_budget_policy_v1()
    if opening_cost_observation is not None or (
        policy is not None and policy.require_opening_execution_costs
    ):
        from .entry_execution_cost_v1 import bind_entry_execution_cost_v1, utc_now_iso_v1
        from src.ops.governed_productive_monetary_normalization_v1.contracts_v1 import (
            MonetaryNormalizationError,
        )

        try:
            entry_cost_binding = bind_entry_execution_cost_v1(
                opening_cost_observation,
                monetary_source=monetary_source,
                applied_input=patched,
                decision=decision,
                account_identity=account_identity,
                slot_id=slot_id,
                cycle_id=cycle_id,
                evaluated_at_utc=utc_now_iso_v1(),
            )
        except (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            ArithmeticError,
            MonetaryNormalizationError,
        ) as exc:
            return _sized_deny(
                owner,
                disposition=ReserveDispositionV1.FAIL_CLOSED,
                reason_codes=(str(exc), "ENTRY_COST_NOT_ADMITTED_NO_RESERVATION"),
                sizing_decision=decision,
            )
    close_cost_binding = None
    if policy is not None and policy.require_closing_execution_costs:
        from .entry_execution_cost_v1 import bind_closing_execution_cost_v1

        try:
            close_cost_binding = bind_closing_execution_cost_v1(
                entry_cost_binding,
                monetary_source=monetary_source,
                applied_input=patched,
                decision=decision,
                evaluated_at_utc=utc_now_iso_v1(),
            )
        except (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            ArithmeticError,
            MonetaryNormalizationError,
        ) as exc:
            return _sized_deny(
                owner,
                disposition=ReserveDispositionV1.FAIL_CLOSED,
                reason_codes=(str(exc), "CLOSE_COST_NOT_ADMITTED_NO_RESERVATION"),
                sizing_decision=decision,
            )
    funding_cost_binding = None
    if funding_cost_observation is not None and not (
        policy is not None and policy.require_next_funding_costs
    ):
        return _sized_deny(
            owner,
            disposition=ReserveDispositionV1.FAIL_CLOSED,
            reason_codes=("FUNDING_COST_EXPLICIT_POLICY_REQUIRED",),
            sizing_decision=decision,
        )
    if policy is not None and policy.require_next_funding_costs:
        from .entry_execution_cost_v1 import bind_next_funding_cost_v1

        try:
            funding_cost_binding = bind_next_funding_cost_v1(
                funding_cost_observation,
                entry_binding=entry_cost_binding,
                close_binding=close_cost_binding,
                monetary_source=monetary_source,
                applied_input=patched,
                decision=decision,
                evaluated_at_utc=utc_now_iso_v1(),
            )
        except (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            ArithmeticError,
            MonetaryNormalizationError,
        ) as exc:
            return _sized_deny(
                owner,
                disposition=ReserveDispositionV1.FAIL_CLOSED,
                reason_codes=(str(exc), "FUNDING_COST_NOT_ADMITTED_NO_RESERVATION"),
                sizing_decision=decision,
            )
    native_initial_margin_binding = None
    if native_initial_margin_observation is not None and not (
        policy is not None and policy.require_native_initial_margin
    ):
        return _sized_deny(
            owner,
            disposition=ReserveDispositionV1.FAIL_CLOSED,
            reason_codes=("NATIVE_INITIAL_MARGIN_EXPLICIT_POLICY_REQUIRED",),
            sizing_decision=decision,
        )
    if policy is not None and policy.require_native_initial_margin:
        from .native_initial_margin_v1 import bind_native_initial_margin_v1

        try:
            native_initial_margin_binding = bind_native_initial_margin_v1(
                native_initial_margin_observation,
                original_margin=observation,
                entry_binding=entry_cost_binding,
                monetary_source=monetary_source,
                applied_input=patched,
                decision=decision,
                evaluated_at_utc=utc_now_iso_v1(),
            )
        except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError) as exc:
            return _sized_deny(
                owner,
                disposition=ReserveDispositionV1.FAIL_CLOSED,
                reason_codes=(str(exc), "NATIVE_INITIAL_MARGIN_NOT_ADMITTED_NO_RESERVATION"),
                sizing_decision=decision,
            )
    if restrictive_risk is not None:
        from .restrictive_risk_binding_v1 import bind_restrictive_risk_v1

        try:
            risk_binding = bind_restrictive_risk_v1(
                request=restrictive_risk,
                owner_snapshot=risk_snapshot,
                original_input=sizing_input,
                applied_input=patched,
                decision=decision,
                slot_id=slot_id,
                cycle_id=cycle_id,
                account=account_identity,
            )
        except (ValueError, TypeError, AttributeError, KeyError, ArithmeticError) as exc:
            return _sized_deny(
                owner,
                disposition=ReserveDispositionV1.FAIL_CLOSED,
                reason_codes=(str(exc), "RISK_NOT_ADMITTED_NO_RESERVATION"),
                sizing_decision=decision,
            )
    sizing_binding = ReservationSizingBindingV1(
        request_digest=request_digest_v1(sizing_input),
        applied_input=patched,
        decision=decision,
        risk_binding=risk_binding,
        monetary_source=monetary_source,
        entry_cost_binding=entry_cost_binding,
        close_cost_binding=close_cost_binding,
        funding_cost_binding=funding_cost_binding,
        native_initial_margin_binding=native_initial_margin_binding,
    )
    if getattr(policy, "require_absolute_movement_cost_cover", False):
        from .absolute_movement_cost_v1 import bind_absolute_movement_cost_v1

        try:
            movement = bind_absolute_movement_cost_v1(
                absolute_movement_cost_observation,
                sizing=sizing_binding,
                evaluated_at_utc=utc_now_iso_v1(),
            )
            sizing_binding = replace(sizing_binding, absolute_movement_cost_binding=movement)
        except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError) as exc:
            return _sized_deny(
                owner,
                disposition=ReserveDispositionV1.FAIL_CLOSED,
                reason_codes=(str(exc), "MOVEMENT_NOT_ADMITTED_NO_RESERVATION"),
                sizing_decision=decision,
            )
    elif absolute_movement_cost_observation is not None:
        return _sized_deny(
            owner,
            disposition=ReserveDispositionV1.FAIL_CLOSED,
            reason_codes=("MOVEMENT_EXPLICIT_POLICY_REQUIRED",),
            sizing_decision=decision,
        )
    reserved = owner.try_reserve_v1(
        slot_id=slot_id,
        decision_id=decision_id,
        cycle_id=cycle_id,
        observation_id=observation_id,
        amount=amount,
        sizing_binding=sizing_binding,
        max_active_sum=patched.total_capital_limit,
        expected_risk_snapshot_digest=risk_snapshot["digest"]
        if risk_snapshot is not None
        else None,
        expected_local_commitment_generation=local_generation,
        handoff_journal=handoff_journal,
        futures_financial_custody=futures_financial_custody,
    )
    if (
        reserved.disposition is ReserveDispositionV1.IDEMPOTENT_REPLAY
        and reserved.reservation is not None
    ):
        return owner.replay_sized_reservation_v1(
            str(reserved.reservation.reservation_id),
            request=sizing_input,
            risk_request=restrictive_risk,
            opening_cost_observation=opening_cost_observation,
            funding_cost_observation=funding_cost_observation,
            native_initial_margin_observation=native_initial_margin_observation,
            absolute_movement_cost_observation=absolute_movement_cost_observation,
        )
    if reserved.disposition is not ReserveDispositionV1.ADMITTED:
        return _sized_deny(
            owner,
            disposition=reserved.disposition,
            reason_codes=reserved.reason_codes + ("SIZING_NOT_ADMITTED_WITHOUT_RESERVATION",),
            sizing_decision=decision,
        )
    if not owner.invariant_holds_v1():
        if reserved.reservation is not None:
            owner.release_sizing_or_admission_deny_v1(str(reserved.reservation.reservation_id))
        return _sized_deny(
            owner,
            disposition=ReserveDispositionV1.FAIL_CLOSED,
            reason_codes=("POST_RESERVE_INVARIANT_FAILED",),
            sizing_decision=decision,
        )
    return SizedReservationResultV1(
        disposition=ReserveDispositionV1.ADMITTED,
        reservation=reserved.reservation,
        sizing_decision=decision,
        reason_codes=("SIZED_THEN_RESERVED", SIZING_OWNER),
        active_sum_after=owner.active_sum_v1(),
        admitted_budget=owner.admitted_budget_v1(),
    )


def _sized_deny(
    owner: PortfolioCapitalReservationBudgetOwnerV1,
    *,
    disposition: ReserveDispositionV1,
    reason_codes: tuple[str, ...],
    sizing_decision: CapitalRiskSizingDecisionV1 | None = None,
) -> SizedReservationResultV1:
    return SizedReservationResultV1(
        disposition=disposition,
        reservation=None,
        sizing_decision=sizing_decision,
        reason_codes=reason_codes,
        active_sum_after=owner.active_sum_v1(),
        admitted_budget=owner.admitted_budget_v1(),
    )


assert MAX_POSITIONS_EFFECTIVE == 1
assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
assert EXTERNAL_EFFECT_AUTHORIZED is False
assert POST_ALLOWED is False
assert REAL_VENUE_POST_ALLOWED is False
assert N_GT_1_ENABLED is False
assert VENUE_FILL_INTEGRATED is False
assert evaluate_capital_risk_sizing_v1.__module__ == "src.governance.capital_risk_sizing_v1"
