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
                if parsed[0] < self._active_sum_locked():
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

    def admitted_budget_v1(self) -> Decimal:
        with self._lock:
            return self._budget if self._admitted else Decimal("0")

    def invariant_holds_v1(self) -> bool:
        with self._lock:
            if not self._admitted:
                return (
                    self._active_sum_locked() <= self._budget
                    if self._store
                    else self._active_sum_locked() == 0
                )
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
            elif value < self._active_sum_locked():
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
    ) -> ReserveResultV1:
        """Consume the feedback join's flat proof and fresh canonical capital.

        No monetary value is inferred from position quantity, fills or PnL.
        This N=1 refresh cannot retire another lane's or unlisted reservation.
        The caller must have reconciled the exact closing order and flat snapshot.
        """
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
        handoff_journal: object | None = None,
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
        with self._lock:
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
                    detached_sizing = ReservationSizingBindingV1.from_dict_v1(
                        sizing_binding.to_dict_v1()
                    )
                except ValueError as exc:
                    return self._result_locked(
                        disposition=ReserveDispositionV1.FAIL_CLOSED,
                        reservation=None,
                        reason_codes=(str(exc),),
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

    def bind_execution_plan_v1(self, reservation_id, envelope):
        from .execution_v1 import bind_plan_locked_v1

        with self._lock:
            return bind_plan_locked_v1(self, str(reservation_id), envelope)

    def mark_execution_submit_boundary_v1(self, reservation_id, identity):
        from .execution_v1 import mark_submit_locked_v1

        with self._lock:
            return mark_submit_locked_v1(self, str(reservation_id), identity)

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

    def _active_sum_locked(self) -> Decimal:
        total = Decimal("0")
        for reservation in self._by_key.values():
            if reservation.counts_against_budget:
                total += reservation.amount
        return total

    def _durable_payload_locked(self) -> dict:
        return {
            "schema": SCHEMA,
            "account_identity": self._account_identity,
            "capital_scope": self._capital_scope,
            "budget": str(self._budget),
            "observation_id": self._observation_id,
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
            binding["schema"] = "reservation_sizing_binding.v1"
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
            if set(payload) - {"sizing_bindings", "execution_links"} != {
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
            from .execution_v1 import detached, validate_link_v1

            links = payload.get("execution_links", {})
            if not isinstance(links, dict) or set(links) - set(records):
                raise ValueError("execution reservation identity")
            for reservation_id, link in links.items():
                validate_link_v1(self, reservation_id, link)
            self._execution_links = detached(links)
            self._admitted = False
        except (ValueError, TypeError, KeyError, AttributeError, InvalidOperation) as exc:
            raise PortfolioCapitalBudgetError("DURABLE_BUDGET_SEMANTIC_RESTORE_UNPROVEN") from exc

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
            recovery_required=self._recovery_required,
            durable_state_enabled=self._store is not None,
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
    restrictive_risk: object | None = None,
    handoff_journal: object | None = None,
) -> SizedReservationResultV1:
    """Producer, 29P admissibility, existing sizing, then atomic reserve.

    Sizing runs against a budget snapshot. Admission is only the later atomic
    reserve of ``resulting_notional``. A lost race denies with no partial hold.
    """
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
            str(existing.reservation_id), request=sizing_input, risk_request=restrictive_risk
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
    facts = capital_context_facts_v1(owner)
    patched = replace(
        sizing_input,
        account_equity=facts["account_equity"],
        already_committed_capital=facts["already_committed_capital"],
        current_reconciled_exposure=facts["current_reconciled_exposure"],
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
    reserved = owner.try_reserve_v1(
        slot_id=slot_id,
        decision_id=decision_id,
        cycle_id=cycle_id,
        observation_id=observation_id,
        amount=amount,
        sizing_binding=ReservationSizingBindingV1(
            request_digest=request_digest_v1(sizing_input),
            applied_input=patched,
            decision=decision,
            risk_binding=risk_binding,
        ),
        max_active_sum=patched.total_capital_limit,
        expected_risk_snapshot_digest=risk_snapshot["digest"]
        if risk_snapshot is not None
        else None,
        handoff_journal=handoff_journal,
    )
    if (
        reserved.disposition is ReserveDispositionV1.IDEMPOTENT_REPLAY
        and reserved.reservation is not None
    ):
        return owner.replay_sized_reservation_v1(
            str(reserved.reservation.reservation_id),
            request=sizing_input,
            risk_request=restrictive_risk,
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
