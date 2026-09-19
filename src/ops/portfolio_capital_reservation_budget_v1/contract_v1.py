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
import threading
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Mapping

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
    """Single in-memory budget. Restart without a fresh producer fact fails closed."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._admitted = False
        self._budget = Decimal("0")
        self._observation_id = ""
        self._by_key: dict[str, CapitalReservationV1] = {}
        self._by_id: dict[str, str] = {}

    def budget_state_v1(self) -> PortfolioBudgetStateV1:
        with self._lock:
            return self._state_locked()

    def active_sum_v1(self) -> Decimal:
        with self._lock:
            return self._active_sum_locked()

    def admitted_budget_v1(self) -> Decimal:
        with self._lock:
            return self._budget if self._admitted else Decimal("0")

    def invariant_holds_v1(self) -> bool:
        with self._lock:
            if not self._admitted:
                return self._active_sum_locked() == 0
            return self._active_sum_locked() <= self._budget

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
            key = _reservation_key(
                slot_id=str(slot_id),
                decision_id=decision_id,
                cycle_id=cycle_id,
                observation_id=observation_id,
            )
            return self._by_key.get(key)

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
            self._expire_active_locked(
                ReservationStateV1.EXPIRED, ReleaseReasonV1.STALE_OR_INVALID_EPOCH
            )
            self._admitted = True
            self._budget = value
            self._observation_id = observation_id
            return self._result_locked(
                disposition=ReserveDispositionV1.ADMITTED,
                reservation=None,
                reason_codes=("CANONICAL_AVAILABLE_CAPITAL_BOUND",),
                mutated=True,
            )

    def try_reserve_v1(
        self,
        *,
        slot_id: SlotId | str,
        decision_id: str,
        cycle_id: str,
        observation_id: str,
        amount: Decimal,
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
        with self._lock:
            if not self._admitted:
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=("RESTART_OR_UNBOUND_BUDGET_FAIL_CLOSED",),
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
            active = self._active_sum_locked()
            if active + money > self._budget:
                return self._result_locked(
                    disposition=ReserveDispositionV1.DENIED,
                    reservation=None,
                    reason_codes=("RESERVATION_INVARIANT_DENIED", "NO_PARTIAL_MUTATION"),
                    mutated=False,
                )
            reservation_id = ReservationId(key)
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
            self._by_key[key] = reservation
            self._by_id[str(reservation_id)] = key
            if self._active_sum_locked() > self._budget:
                del self._by_key[key]
                del self._by_id[str(reservation_id)]
                return self._result_locked(
                    disposition=ReserveDispositionV1.FAIL_CLOSED,
                    reservation=None,
                    reason_codes=("POST_INSERT_INVARIANT_ROLLBACK",),
                    mutated=False,
                )
            return self._result_locked(
                disposition=ReserveDispositionV1.ADMITTED,
                reservation=reservation,
                reason_codes=("RESERVED",),
                mutated=True,
            )

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

    def restart_fail_closed_v1(self) -> ReserveResultV1:
        """Drop in-memory state. Do not rebuild reservations from unproven data."""
        with self._lock:
            self._admitted = False
            self._budget = Decimal("0")
            self._observation_id = ""
            self._by_key = {}
            self._by_id = {}
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
        key = self._by_id.get(str(reservation_id or ""))
        if key is None:
            return None
        current = self._by_key.get(key)
        if current is None:
            return None
        return key, current

    def _active_sum_locked(self) -> Decimal:
        total = Decimal("0")
        for reservation in self._by_key.values():
            if reservation.counts_against_budget:
                total += reservation.amount
        return total

    def _state_locked(self) -> PortfolioBudgetStateV1:
        active = self._active_sum_locked()
        budget = self._budget if self._admitted else Decimal("0")
        remaining = budget - active if self._admitted else Decimal("0")
        return PortfolioBudgetStateV1(
            admitted=self._admitted,
            observation_id=self._observation_id,
            canonical_available_capital=budget,
            active_reservation_sum=active,
            remaining_unreserved=remaining,
            canonical_restart_reconstructable=CANONICAL_RESTART_RECONSTRUCTABLE,
            reservation_ids=tuple(sorted(self._by_id)),
        )

    def _result_locked(
        self,
        *,
        disposition: ReserveDispositionV1,
        reservation: CapitalReservationV1 | None,
        reason_codes: tuple[str, ...],
        mutated: bool,
    ) -> ReserveResultV1:
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
) -> Mapping[str, Decimal]:
    """Facts the existing sizing seam was missing. Not a second quantity owner."""
    state = owner.budget_state_v1()
    if not state.admitted:
        raise PortfolioCapitalBudgetError("CAPITAL_CONTEXT_REQUIRES_BOUND_PRODUCER_OUTPUT")
    return {
        "account_equity": state.canonical_available_capital,
        "already_committed_capital": state.active_reservation_sum,
        "current_reconciled_exposure": state.active_reservation_sum,
    }


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
) -> SizedReservationResultV1:
    """Producer, 29P admissibility, existing sizing, then atomic reserve.

    Sizing runs against a budget snapshot. Admission is only the later atomic
    reserve of ``resulting_notional``. A lost race denies with no partial hold.
    """
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
        return SizedReservationResultV1(
            disposition=ReserveDispositionV1.IDEMPOTENT_REPLAY,
            reservation=existing,
            sizing_decision=None,
            reason_codes=("IDEMPOTENT_REPLAY_NO_DOUBLE_COUNT",),
            active_sum_after=owner.active_sum_v1(),
            admitted_budget=owner.admitted_budget_v1(),
        )
    facts = capital_context_facts_v1(owner)
    patched = replace(
        sizing_input,
        account_equity=facts["account_equity"],
        already_committed_capital=facts["already_committed_capital"],
        current_reconciled_exposure=facts["current_reconciled_exposure"],
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
    reserved = owner.try_reserve_v1(
        slot_id=slot_id,
        decision_id=decision_id,
        cycle_id=cycle_id,
        observation_id=observation_id,
        amount=amount,
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
