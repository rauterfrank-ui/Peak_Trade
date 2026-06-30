# src/trading/master_v2/double_play_entry_exit_policy_v0.py
"""
Pure Entry / Existing-Position-Management / Exit Policy v0 for Master V2 Double Play.

Consumes immutable DoublePlayCompositionResultV1 and explicit gate/signal inputs.
Produces fachliche decision outcomes only — no orders, quantity binding, runtime,
adapter, or safety-authority effects.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from enum import Enum
from typing import Mapping, Optional, Tuple

from trading.master_v2.canonical_market_context_v1 import (
    ClockTrustStatus,
    DataIntegrityStatus,
)
from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentStatus
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionChopGuardStatus,
    CompositionConflictStatus,
    CompositionSelectedSide,
    CompositionStatus,
    DoublePlayCompositionResultV1,
    PositionManagementContext,
)
from trading.master_v2.suitability_binding_v1 import SuitabilityBindingStatus
from trading.master_v2.survival_assessment_v1 import SurvivalAssessmentStatus

ENTRY_EXIT_POLICY_LAYER_VERSION = "v0"
ENTRY_EXIT_POLICY_VERSION = "double_play_entry_exit_policy_v0"

_AUTHORITY_EFFECT_NONE = "NONE"
_RUNTIME_EFFECT_NONE = "NONE"
_ORDER_EFFECT_NONE = "NONE"
_RISK_EFFECT_NONE = "NONE"
_SIZING_EFFECT_NONE = "NONE"
_QUANTITY_STATUS_NOT_BOUND = "NOT_BOUND"

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})


class EntryExitDirectionState(str, Enum):
    NEUTRAL = "neutral"
    LONG_ARMED = "long_armed"
    SHORT_ARMED = "short_armed"
    LONG_ACTIVE = "long_active"
    SHORT_ACTIVE = "short_active"


class PositionState(str, Enum):
    FLAT_RECONCILED = "flat_reconciled"
    OPEN_FULL = "open_full"
    OPEN_PARTIAL = "open_partial"
    REDUCING_PARTIAL = "reducing_partial"
    EXIT_PENDING = "exit_pending"
    SUBMISSION_UNKNOWN = "submission_unknown"
    RECONCILIATION_REQUIRED = "reconciliation_required"


class ReconciliationState(str, Enum):
    RECONCILED = "reconciled"
    RECONCILIATION_REQUIRED = "reconciliation_required"
    UNKNOWN = "unknown"


class TradingGate(str, Enum):
    ENTRY_ALLOWED = "entry_allowed"
    INCREASE_ALLOWED = "increase_allowed"
    EXIT_ONLY = "exit_only"
    BLOCKED = "blocked"


class SafetyMode(str, Enum):
    NORMAL = "normal"
    DEGRADED = "degraded"
    EXIT_ONLY = "exit_only"
    BLOCKED = "blocked"


class ExistingPositionSide(str, Enum):
    NONE = "none"
    LONG = "long"
    SHORT = "short"


class ExitClass(str, Enum):
    NONE = "none"
    SAFETY_EXIT = "safety_exit"
    HARD_RISK_EXIT = "hard_risk_exit"
    ADVERSE_SCOPE_EXIT = "adverse_scope_exit"
    PROFIT_PROTECTION_EXIT = "profit_protection_exit"
    TIME_EXIT = "time_exit"
    STRATEGY_INVALIDATION_EXIT = "strategy_invalidation_exit"
    REVERSAL_PREPARATION_EXIT = "reversal_preparation_exit"


# Stable mandatory-exit priority (highest first). Not collection-order dependent.
_MANDATORY_EXIT_PRIORITY: Tuple[ExitClass, ...] = (
    ExitClass.ADVERSE_SCOPE_EXIT,
    ExitClass.PROFIT_PROTECTION_EXIT,
    ExitClass.TIME_EXIT,
    ExitClass.STRATEGY_INVALIDATION_EXIT,
)


class DecisionOutcome(str, Enum):
    NO_ACTION = "no_action"
    OBSERVE = "observe"
    HOLD = "hold"
    REDUCE = "reduce"
    EXIT = "exit"
    ENTER_LONG = "enter_long"
    ENTER_SHORT = "enter_short"
    CANCEL_PENDING = "cancel_pending"
    RECONCILE_ONLY = "reconcile_only"
    BLOCKED = "blocked"


class EntryEligibility(str, Enum):
    ELIGIBLE = "eligible"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"


class PositionManagementAction(str, Enum):
    NONE = "none"
    HOLD = "hold"
    REDUCE = "reduce"
    EXIT = "exit"
    RECONCILE = "reconcile"


class ReversalState(str, Enum):
    NONE = "none"
    PREPARATION = "preparation"
    BLOCKED = "blocked"


class PolicyBlockedReason(str, Enum):
    INPUT_INCOMPLETE = "input_incomplete"
    INSTRUMENT_KIND_FORBIDDEN = "instrument_kind_forbidden"
    INSTRUMENT_MISMATCH = "instrument_mismatch"
    TRADING_EPOCH_MISMATCH = "trading_epoch_mismatch"
    INPUT_DIGEST_MISMATCH = "input_digest_mismatch"
    COMPOSITION_REF_MISMATCH = "composition_ref_mismatch"
    POLICY_VERSION_INVALID = "policy_version_invalid"
    MISSING_MANDATORY_INPUT = "missing_mandatory_input"
    EXPLICIT_BLOCKED = "explicit_blocked"


class DecisionPrecedenceStage(str, Enum):
    SAFETY_AUTHORITY = "safety_authority"
    HARD_RISK = "hard_risk"
    RECONCILIATION = "reconciliation"
    MANDATORY_EXIT = "mandatory_exit"
    EXISTING_POSITION = "existing_position"
    REVERSAL = "reversal"
    NEW_ENTRY = "new_entry"
    OBSERVE = "observe"
    NO_ACTION = "no_action"


@dataclass(frozen=True)
class PolicySignalV0:
    """Explicit fachlicher signal input; never inferred from confidence alone."""

    triggered: bool
    reason_code: str = ""


@dataclass(frozen=True)
class DoublePlayEntryExitPolicyV0:
    policy_version: str = ENTRY_EXIT_POLICY_VERSION


@dataclass(frozen=True)
class DoublePlayEntryExitPolicyInputV0:
    instrument_id: str
    trading_epoch: int
    context_reference: str
    composition_result: DoublePlayCompositionResultV1
    direction_state: EntryExitDirectionState
    position_state: PositionState
    reconciliation_state: ReconciliationState
    trading_gate: TradingGate
    safety_mode: SafetyMode
    data_integrity_state: DataIntegrityStatus
    clock_trust_status: ClockTrustStatus
    clock_trust_valid: bool
    cooldown_pass: bool
    existing_position_side: ExistingPositionSide
    venue_flat: bool
    scope_adverse_exit_signal: PolicySignalV0
    profit_protection_signal: PolicySignalV0
    time_exit_signal: PolicySignalV0
    strategy_invalidation_signal: PolicySignalV0
    hard_risk_reduction_signal: PolicySignalV0
    safety_exit_signal: PolicySignalV0
    input_complete: bool
    input_digest: str
    explicit_blocked_reasons: Tuple[PolicyBlockedReason, ...] = ()
    policy_version: str = ENTRY_EXIT_POLICY_VERSION


@dataclass(frozen=True)
class EntryExitPolicyDecisionV0:
    policy_decision_id: str
    instrument_id: str
    trading_epoch: int
    composition_result_ref: str
    previous_direction_state: EntryExitDirectionState
    position_state: PositionState
    reconciliation_state: ReconciliationState
    decision_outcome: DecisionOutcome
    entry_eligibility: EntryEligibility
    exit_class: ExitClass
    position_management_action: PositionManagementAction
    reversal_state: ReversalState
    reduce_only: bool
    position_flip_allowed: bool
    quantity_status: str
    selected_side: CompositionSelectedSide
    reason_codes: Tuple[str, ...]
    decision_precedence_trace: Tuple[str, ...]
    policy_version: str
    input_digest: str
    semantic_digest: str
    execution_eligible: bool = False
    adapter_compatible: bool = False
    authority_effect: str = _AUTHORITY_EFFECT_NONE
    runtime_effect: str = _RUNTIME_EFFECT_NONE
    order_effect: str = _ORDER_EFFECT_NONE
    risk_sizing_effect: str = _RISK_EFFECT_NONE

    def __post_init__(self) -> None:
        if self.semantic_digest and not _valid_sha256_hex(self.semantic_digest):
            msg = "semantic_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)
        if self.input_digest and not _valid_sha256_hex(self.input_digest):
            msg = "input_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)


def _valid_sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _instrument_id_allowed(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return not any(token in lowered for token in _FORBIDDEN_INSTRUMENT_SUBSTRINGS)


def _position_blocks_opposite_entry(position_state: PositionState) -> bool:
    return position_state in (
        PositionState.REDUCING_PARTIAL,
        PositionState.EXIT_PENDING,
        PositionState.SUBMISSION_UNKNOWN,
    )


def _position_is_flat(position_state: PositionState) -> bool:
    return position_state is PositionState.FLAT_RECONCILED


def _position_has_open(position_state: PositionState) -> bool:
    return position_state in (
        PositionState.OPEN_FULL,
        PositionState.OPEN_PARTIAL,
        PositionState.REDUCING_PARTIAL,
        PositionState.EXIT_PENDING,
    )


def _reconciliation_blocks_entry(
    position_state: PositionState,
    reconciliation_state: ReconciliationState,
) -> bool:
    if position_state is PositionState.SUBMISSION_UNKNOWN:
        return True
    if position_state is PositionState.RECONCILIATION_REQUIRED:
        return True
    if reconciliation_state is not ReconciliationState.RECONCILED:
        return True
    return False


def _effective_flat(position_state: PositionState, venue_flat: bool) -> bool:
    """Venue-flat alone does not imply FLAT_RECONCILED."""
    return position_state is PositionState.FLAT_RECONCILED


def _selected_side_status(
    composition: DoublePlayCompositionResultV1,
) -> Tuple[
    Optional[DirectionalAssessmentStatus],
    Optional[SurvivalAssessmentStatus],
    Optional[SuitabilityBindingStatus],
]:
    if composition.selected_side is CompositionSelectedSide.LONG:
        bull_status = DirectionalAssessmentStatus(composition.bull_assessment_ref.status)
        return (
            bull_status,
            composition.bull_survival_ref.status,
            composition.bull_suitability_ref.status,
        )
    if composition.selected_side is CompositionSelectedSide.SHORT:
        bear_status = DirectionalAssessmentStatus(composition.bear_assessment_ref.status)
        return (
            bear_status,
            composition.bear_survival_ref.status,
            composition.bear_suitability_ref.status,
        )
    return None, None, None


def _direction_armed_for_entry(direction_state: EntryExitDirectionState) -> bool:
    return direction_state in (
        EntryExitDirectionState.LONG_ARMED,
        EntryExitDirectionState.SHORT_ARMED,
    )


def _entry_gate_allows(trading_gate: TradingGate) -> bool:
    return trading_gate in (TradingGate.ENTRY_ALLOWED, TradingGate.INCREASE_ALLOWED)


def _resolve_mandatory_exit(
    inp: DoublePlayEntryExitPolicyInputV0,
) -> Optional[ExitClass]:
    signal_map: Mapping[ExitClass, PolicySignalV0] = {
        ExitClass.ADVERSE_SCOPE_EXIT: inp.scope_adverse_exit_signal,
        ExitClass.PROFIT_PROTECTION_EXIT: inp.profit_protection_signal,
        ExitClass.TIME_EXIT: inp.time_exit_signal,
        ExitClass.STRATEGY_INVALIDATION_EXIT: inp.strategy_invalidation_signal,
    }
    for exit_class in _MANDATORY_EXIT_PRIORITY:
        signal = signal_map[exit_class]
        if signal.triggered:
            return exit_class
    return None


def _mandatory_outcome_for(exit_class: ExitClass) -> DecisionOutcome:
    if exit_class is ExitClass.ADVERSE_SCOPE_EXIT:
        return DecisionOutcome.REDUCE
    return DecisionOutcome.EXIT


def serialize_entry_exit_policy_input_canonical(
    inp: DoublePlayEntryExitPolicyInputV0,
) -> str:
    payload: dict[str, object] = {
        "instrument_id": inp.instrument_id,
        "trading_epoch": inp.trading_epoch,
        "context_reference": inp.context_reference,
        "composition_result_ref": inp.composition_result.composition_id,
        "composition_semantic_digest": inp.composition_result.semantic_digest,
        "direction_state": inp.direction_state.value,
        "position_state": inp.position_state.value,
        "reconciliation_state": inp.reconciliation_state.value,
        "trading_gate": inp.trading_gate.value,
        "safety_mode": inp.safety_mode.value,
        "data_integrity_state": inp.data_integrity_state.value,
        "clock_trust_status": inp.clock_trust_status.value,
        "clock_trust_valid": inp.clock_trust_valid,
        "cooldown_pass": inp.cooldown_pass,
        "existing_position_side": inp.existing_position_side.value,
        "venue_flat": inp.venue_flat,
        "scope_adverse_exit_signal": inp.scope_adverse_exit_signal.triggered,
        "profit_protection_signal": inp.profit_protection_signal.triggered,
        "time_exit_signal": inp.time_exit_signal.triggered,
        "strategy_invalidation_signal": inp.strategy_invalidation_signal.triggered,
        "hard_risk_reduction_signal": inp.hard_risk_reduction_signal.triggered,
        "safety_exit_signal": inp.safety_exit_signal.triggered,
        "input_complete": inp.input_complete,
        "explicit_blocked_reasons": sorted(r.value for r in inp.explicit_blocked_reasons),
        "policy_version": inp.policy_version,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_entry_exit_policy_input_digest(inp: DoublePlayEntryExitPolicyInputV0) -> str:
    canonical = serialize_entry_exit_policy_input_canonical(inp)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def serialize_entry_exit_policy_decision_canonical(decision: EntryExitPolicyDecisionV0) -> str:
    payload: dict[str, object] = {
        "policy_decision_id": decision.policy_decision_id,
        "instrument_id": decision.instrument_id,
        "trading_epoch": decision.trading_epoch,
        "composition_result_ref": decision.composition_result_ref,
        "previous_direction_state": decision.previous_direction_state.value,
        "position_state": decision.position_state.value,
        "reconciliation_state": decision.reconciliation_state.value,
        "decision_outcome": decision.decision_outcome.value,
        "entry_eligibility": decision.entry_eligibility.value,
        "exit_class": decision.exit_class.value,
        "position_management_action": decision.position_management_action.value,
        "reversal_state": decision.reversal_state.value,
        "reduce_only": decision.reduce_only,
        "position_flip_allowed": decision.position_flip_allowed,
        "quantity_status": decision.quantity_status,
        "selected_side": decision.selected_side.value,
        "reason_codes": list(decision.reason_codes),
        "decision_precedence_trace": list(decision.decision_precedence_trace),
        "policy_version": decision.policy_version,
        "input_digest": decision.input_digest,
        "execution_eligible": decision.execution_eligible,
        "adapter_compatible": decision.adapter_compatible,
        "authority_effect": decision.authority_effect,
        "runtime_effect": decision.runtime_effect,
        "order_effect": decision.order_effect,
        "risk_sizing_effect": decision.risk_sizing_effect,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_entry_exit_policy_semantic_digest(decision: EntryExitPolicyDecisionV0) -> str:
    canonical = serialize_entry_exit_policy_decision_canonical(
        replace(decision, semantic_digest="")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def with_computed_entry_exit_policy_digest(
    decision: EntryExitPolicyDecisionV0,
) -> EntryExitPolicyDecisionV0:
    digest = compute_entry_exit_policy_semantic_digest(replace(decision, semantic_digest=""))
    return replace(decision, semantic_digest=digest)


def _derive_policy_decision_id(
    instrument_id: str,
    trading_epoch: int,
    outcome: DecisionOutcome,
) -> str:
    seed = f"{instrument_id}|{trading_epoch}|{outcome.value}|entry_exit_policy_v0"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]


def _finalize_decision(
    inp: DoublePlayEntryExitPolicyInputV0,
    policy: DoublePlayEntryExitPolicyV0,
    *,
    decision_outcome: DecisionOutcome,
    entry_eligibility: EntryEligibility,
    exit_class: ExitClass,
    position_management_action: PositionManagementAction,
    reversal_state: ReversalState,
    reduce_only: bool,
    position_flip_allowed: bool,
    reason_codes: Tuple[str, ...],
    precedence_trace: Tuple[str, ...],
    computed_input_digest: str,
) -> EntryExitPolicyDecisionV0:
    decision = EntryExitPolicyDecisionV0(
        policy_decision_id=_derive_policy_decision_id(
            inp.instrument_id, inp.trading_epoch, decision_outcome
        ),
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        composition_result_ref=inp.composition_result.composition_id,
        previous_direction_state=inp.direction_state,
        position_state=inp.position_state,
        reconciliation_state=inp.reconciliation_state,
        decision_outcome=decision_outcome,
        entry_eligibility=entry_eligibility,
        exit_class=exit_class,
        position_management_action=position_management_action,
        reversal_state=reversal_state,
        reduce_only=reduce_only,
        position_flip_allowed=position_flip_allowed,
        quantity_status=_QUANTITY_STATUS_NOT_BOUND,
        selected_side=inp.composition_result.selected_side,
        reason_codes=reason_codes,
        decision_precedence_trace=precedence_trace,
        policy_version=policy.policy_version,
        input_digest=computed_input_digest,
        semantic_digest="",
    )
    return with_computed_entry_exit_policy_digest(decision)


def _blocked_decision(
    inp: DoublePlayEntryExitPolicyInputV0,
    policy: DoublePlayEntryExitPolicyV0,
    *,
    reason: PolicyBlockedReason,
    reason_code: str,
    computed_input_digest: str,
    extra_codes: Tuple[str, ...] = (),
) -> EntryExitPolicyDecisionV0:
    codes = (reason_code, reason.value) + extra_codes
    return _finalize_decision(
        inp,
        policy,
        decision_outcome=DecisionOutcome.BLOCKED,
        entry_eligibility=EntryEligibility.BLOCKED,
        exit_class=ExitClass.NONE,
        position_management_action=PositionManagementAction.NONE,
        reversal_state=ReversalState.BLOCKED,
        reduce_only=False,
        position_flip_allowed=False,
        reason_codes=codes,
        precedence_trace=(DecisionPrecedenceStage.NO_ACTION.value,),
        computed_input_digest=computed_input_digest,
    )


def _exit_decision(
    inp: DoublePlayEntryExitPolicyInputV0,
    policy: DoublePlayEntryExitPolicyV0,
    *,
    exit_class: ExitClass,
    decision_outcome: DecisionOutcome,
    position_management_action: PositionManagementAction,
    precedence_stage: DecisionPrecedenceStage,
    reason_codes: Tuple[str, ...],
    computed_input_digest: str,
    reversal_state: ReversalState = ReversalState.NONE,
) -> EntryExitPolicyDecisionV0:
    trace = (precedence_stage.value, exit_class.value)
    return _finalize_decision(
        inp,
        policy,
        decision_outcome=decision_outcome,
        entry_eligibility=EntryEligibility.NOT_APPLICABLE,
        exit_class=exit_class,
        position_management_action=position_management_action,
        reversal_state=reversal_state,
        reduce_only=True,
        position_flip_allowed=False,
        reason_codes=reason_codes,
        precedence_trace=trace,
        computed_input_digest=computed_input_digest,
    )


def _entry_preconditions_met(inp: DoublePlayEntryExitPolicyInputV0) -> Tuple[bool, Tuple[str, ...]]:
    reasons: list[str] = []
    comp = inp.composition_result

    if not _direction_armed_for_entry(inp.direction_state):
        reasons.append("direction_not_armed")

    if comp.composition_status not in (
        CompositionStatus.LONG_SELECTED,
        CompositionStatus.SHORT_SELECTED,
    ):
        reasons.append("composition_not_directional_selected")

    if comp.chop_guard_status is CompositionChopGuardStatus.CHOP_GUARD_BLOCK:
        reasons.append("chop_guard_block")

    if comp.conflict_status is CompositionConflictStatus.BOTH_SIDES_CONFIRMED:
        reasons.append("both_sides_confirmed_chop_guard")

    assess_status, surv_status, suit_status = _selected_side_status(comp)
    if assess_status is not DirectionalAssessmentStatus.CONFIRMED:
        reasons.append("selected_assessment_not_confirmed")
    if surv_status is not SurvivalAssessmentStatus.PASS:
        reasons.append("survival_not_pass")
    if suit_status is not SuitabilityBindingStatus.PASS:
        reasons.append("suitability_not_pass")

    if not _effective_flat(inp.position_state, inp.venue_flat):
        reasons.append("position_not_flat_reconciled")

    if inp.reconciliation_state is not ReconciliationState.RECONCILED:
        reasons.append("reconciliation_not_reconciled")

    if not _entry_gate_allows(inp.trading_gate):
        reasons.append("trading_gate_blocks_entry")

    if inp.safety_mode is not SafetyMode.NORMAL:
        reasons.append("safety_mode_not_normal")

    if inp.data_integrity_state is not DataIntegrityStatus.TRUSTED:
        reasons.append("data_integrity_untrusted")

    if not inp.clock_trust_valid or inp.clock_trust_status is not ClockTrustStatus.TRUSTED:
        reasons.append("clock_trust_invalid")

    if not inp.cooldown_pass:
        reasons.append("cooldown_fail")

    if _position_blocks_opposite_entry(inp.position_state):
        reasons.append("partial_fill_or_unknown_blocks_entry")

    return len(reasons) == 0, tuple(sorted(reasons))


def evaluate_double_play_entry_exit_policy_v0(
    inp: DoublePlayEntryExitPolicyInputV0,
    policy: DoublePlayEntryExitPolicyV0,
) -> EntryExitPolicyDecisionV0:
    """
    Deterministic entry / position-management / exit policy evaluator.

    Fail-closed on incomplete or mismatched inputs. Never creates orders,
    quantities, or runtime effects.
    """

    computed_digest = compute_entry_exit_policy_input_digest(inp)
    comp = inp.composition_result

    if policy.policy_version != inp.policy_version:
        return _blocked_decision(
            inp,
            policy,
            reason=PolicyBlockedReason.POLICY_VERSION_INVALID,
            reason_code="policy_validation_failed",
            computed_input_digest=computed_digest,
        )

    if not _instrument_id_allowed(inp.instrument_id):
        return _blocked_decision(
            inp,
            policy,
            reason=PolicyBlockedReason.INSTRUMENT_KIND_FORBIDDEN,
            reason_code="instrument_gate_failed",
            computed_input_digest=computed_digest,
        )

    if not inp.input_complete:
        return _blocked_decision(
            inp,
            policy,
            reason=PolicyBlockedReason.INPUT_INCOMPLETE,
            reason_code="input_gate_failed",
            computed_input_digest=computed_digest,
        )

    if inp.explicit_blocked_reasons:
        return _blocked_decision(
            inp,
            policy,
            reason=PolicyBlockedReason.EXPLICIT_BLOCKED,
            reason_code="explicit_blocked",
            computed_input_digest=computed_digest,
            extra_codes=tuple(sorted(r.value for r in inp.explicit_blocked_reasons)),
        )

    if inp.input_digest and inp.input_digest != computed_digest:
        return _blocked_decision(
            inp,
            policy,
            reason=PolicyBlockedReason.INPUT_DIGEST_MISMATCH,
            reason_code="input_digest_mismatch",
            computed_input_digest=computed_digest,
        )

    if comp.instrument_id != inp.instrument_id:
        return _blocked_decision(
            inp,
            policy,
            reason=PolicyBlockedReason.INSTRUMENT_MISMATCH,
            reason_code="composition_instrument_mismatch",
            computed_input_digest=computed_digest,
        )

    if comp.trading_epoch != inp.trading_epoch:
        return _blocked_decision(
            inp,
            policy,
            reason=PolicyBlockedReason.TRADING_EPOCH_MISMATCH,
            reason_code="composition_epoch_mismatch",
            computed_input_digest=computed_digest,
        )

    # --- Precedence 1: Safety exit ---
    if inp.safety_exit_signal.triggered:
        codes = ("safety_exit", inp.safety_exit_signal.reason_code or "safety_authority")
        return _exit_decision(
            inp,
            policy,
            exit_class=ExitClass.SAFETY_EXIT,
            decision_outcome=DecisionOutcome.EXIT,
            position_management_action=PositionManagementAction.EXIT,
            precedence_stage=DecisionPrecedenceStage.SAFETY_AUTHORITY,
            reason_codes=codes,
            computed_input_digest=computed_digest,
        )

    # --- Precedence 2: Hard risk reduction ---
    if inp.hard_risk_reduction_signal.triggered:
        codes = (
            "hard_risk_reduction",
            inp.hard_risk_reduction_signal.reason_code or "hard_risk",
        )
        return _exit_decision(
            inp,
            policy,
            exit_class=ExitClass.HARD_RISK_EXIT,
            decision_outcome=DecisionOutcome.REDUCE,
            position_management_action=PositionManagementAction.REDUCE,
            precedence_stage=DecisionPrecedenceStage.HARD_RISK,
            reason_codes=codes,
            computed_input_digest=computed_digest,
        )

    # --- Precedence 3: Reconciliation requirement ---
    if (
        inp.position_state is PositionState.SUBMISSION_UNKNOWN
        or inp.position_state is PositionState.RECONCILIATION_REQUIRED
        or inp.reconciliation_state is ReconciliationState.RECONCILIATION_REQUIRED
        or inp.reconciliation_state is ReconciliationState.UNKNOWN
    ):
        codes = ("reconciliation_required", inp.position_state.value)
        return _finalize_decision(
            inp,
            policy,
            decision_outcome=DecisionOutcome.RECONCILE_ONLY,
            entry_eligibility=EntryEligibility.BLOCKED,
            exit_class=ExitClass.NONE,
            position_management_action=PositionManagementAction.RECONCILE,
            reversal_state=ReversalState.BLOCKED,
            reduce_only=False,
            position_flip_allowed=False,
            reason_codes=codes,
            precedence_trace=(DecisionPrecedenceStage.RECONCILIATION.value,),
            computed_input_digest=computed_digest,
        )

    if inp.reconciliation_state is not ReconciliationState.RECONCILED:
        return _finalize_decision(
            inp,
            policy,
            decision_outcome=DecisionOutcome.RECONCILE_ONLY,
            entry_eligibility=EntryEligibility.BLOCKED,
            exit_class=ExitClass.NONE,
            position_management_action=PositionManagementAction.RECONCILE,
            reversal_state=ReversalState.BLOCKED,
            reduce_only=False,
            position_flip_allowed=False,
            reason_codes=("reconciliation_not_reconciled",),
            precedence_trace=(DecisionPrecedenceStage.RECONCILIATION.value,),
            computed_input_digest=computed_digest,
        )

    # --- Precedence 4: Mandatory exit policy ---
    mandatory_exit = _resolve_mandatory_exit(inp)
    if mandatory_exit is not None:
        outcome = _mandatory_outcome_for(mandatory_exit)
        mgmt = (
            PositionManagementAction.REDUCE
            if outcome is DecisionOutcome.REDUCE
            else PositionManagementAction.EXIT
        )
        signal = {
            ExitClass.ADVERSE_SCOPE_EXIT: inp.scope_adverse_exit_signal,
            ExitClass.PROFIT_PROTECTION_EXIT: inp.profit_protection_signal,
            ExitClass.TIME_EXIT: inp.time_exit_signal,
            ExitClass.STRATEGY_INVALIDATION_EXIT: inp.strategy_invalidation_signal,
        }[mandatory_exit]
        codes = (mandatory_exit.value, signal.reason_code or mandatory_exit.value)
        return _exit_decision(
            inp,
            policy,
            exit_class=mandatory_exit,
            decision_outcome=outcome,
            position_management_action=mgmt,
            precedence_stage=DecisionPrecedenceStage.MANDATORY_EXIT,
            reason_codes=codes,
            computed_input_digest=computed_digest,
        )

    # --- Precedence 5: Existing position management ---
    if _position_has_open(inp.position_state):
        if inp.existing_position_side is ExistingPositionSide.LONG:
            if comp.selected_side is CompositionSelectedSide.SHORT:
                # Precedence 6 handled below — reversal preparation
                pass
            elif comp.composition_status in (
                CompositionStatus.LONG_SELECTED,
                CompositionStatus.NO_ACTION,
                CompositionStatus.OBSERVE,
            ):
                return _finalize_decision(
                    inp,
                    policy,
                    decision_outcome=DecisionOutcome.HOLD,
                    entry_eligibility=EntryEligibility.NOT_APPLICABLE,
                    exit_class=ExitClass.NONE,
                    position_management_action=PositionManagementAction.HOLD,
                    reversal_state=ReversalState.NONE,
                    reduce_only=False,
                    position_flip_allowed=False,
                    reason_codes=("existing_long_hold",),
                    precedence_trace=(DecisionPrecedenceStage.EXISTING_POSITION.value,),
                    computed_input_digest=computed_digest,
                )
        elif inp.existing_position_side is ExistingPositionSide.SHORT:
            if comp.selected_side is CompositionSelectedSide.LONG:
                pass
            elif comp.composition_status in (
                CompositionStatus.SHORT_SELECTED,
                CompositionStatus.NO_ACTION,
                CompositionStatus.OBSERVE,
            ):
                return _finalize_decision(
                    inp,
                    policy,
                    decision_outcome=DecisionOutcome.HOLD,
                    entry_eligibility=EntryEligibility.NOT_APPLICABLE,
                    exit_class=ExitClass.NONE,
                    position_management_action=PositionManagementAction.HOLD,
                    reversal_state=ReversalState.NONE,
                    reduce_only=False,
                    position_flip_allowed=False,
                    reason_codes=("existing_short_hold",),
                    precedence_trace=(DecisionPrecedenceStage.EXISTING_POSITION.value,),
                    computed_input_digest=computed_digest,
                )

    # --- Precedence 6: Reversal preparation (no direct position flip) ---
    if (
        inp.existing_position_side is ExistingPositionSide.LONG
        and comp.selected_side is CompositionSelectedSide.SHORT
        and _position_has_open(inp.position_state)
    ):
        if _position_blocks_opposite_entry(inp.position_state):
            return _blocked_decision(
                inp,
                policy,
                reason=PolicyBlockedReason.MISSING_MANDATORY_INPUT,
                reason_code="reversal_blocked_partial_or_unknown",
                computed_input_digest=computed_digest,
            )
        codes = ("reversal_preparation", "selected_opposite_short")
        return _exit_decision(
            inp,
            policy,
            exit_class=ExitClass.REVERSAL_PREPARATION_EXIT,
            decision_outcome=DecisionOutcome.REDUCE,
            position_management_action=PositionManagementAction.REDUCE,
            precedence_stage=DecisionPrecedenceStage.REVERSAL,
            reason_codes=codes,
            computed_input_digest=computed_digest,
            reversal_state=ReversalState.PREPARATION,
        )

    if (
        inp.existing_position_side is ExistingPositionSide.SHORT
        and comp.selected_side is CompositionSelectedSide.LONG
        and _position_has_open(inp.position_state)
    ):
        if _position_blocks_opposite_entry(inp.position_state):
            return _blocked_decision(
                inp,
                policy,
                reason=PolicyBlockedReason.MISSING_MANDATORY_INPUT,
                reason_code="reversal_blocked_partial_or_unknown",
                computed_input_digest=computed_digest,
            )
        codes = ("reversal_preparation", "selected_opposite_long")
        return _exit_decision(
            inp,
            policy,
            exit_class=ExitClass.REVERSAL_PREPARATION_EXIT,
            decision_outcome=DecisionOutcome.REDUCE,
            position_management_action=PositionManagementAction.REDUCE,
            precedence_stage=DecisionPrecedenceStage.REVERSAL,
            reason_codes=codes,
            computed_input_digest=computed_digest,
            reversal_state=ReversalState.PREPARATION,
        )

    # --- Precedence 7: New entry ---
    entry_ok, entry_block_reasons = _entry_preconditions_met(inp)
    if entry_ok:
        if comp.selected_side is CompositionSelectedSide.LONG:
            if inp.direction_state is EntryExitDirectionState.LONG_ARMED:
                return _finalize_decision(
                    inp,
                    policy,
                    decision_outcome=DecisionOutcome.ENTER_LONG,
                    entry_eligibility=EntryEligibility.ELIGIBLE,
                    exit_class=ExitClass.NONE,
                    position_management_action=PositionManagementAction.NONE,
                    reversal_state=ReversalState.NONE,
                    reduce_only=False,
                    position_flip_allowed=False,
                    reason_codes=("entry_long_eligible",),
                    precedence_trace=(DecisionPrecedenceStage.NEW_ENTRY.value,),
                    computed_input_digest=computed_digest,
                )
        if comp.selected_side is CompositionSelectedSide.SHORT:
            if inp.direction_state is EntryExitDirectionState.SHORT_ARMED:
                return _finalize_decision(
                    inp,
                    policy,
                    decision_outcome=DecisionOutcome.ENTER_SHORT,
                    entry_eligibility=EntryEligibility.ELIGIBLE,
                    exit_class=ExitClass.NONE,
                    position_management_action=PositionManagementAction.NONE,
                    reversal_state=ReversalState.NONE,
                    reduce_only=False,
                    position_flip_allowed=False,
                    reason_codes=("entry_short_eligible",),
                    precedence_trace=(DecisionPrecedenceStage.NEW_ENTRY.value,),
                    computed_input_digest=computed_digest,
                )

    if entry_block_reasons and comp.composition_status in (
        CompositionStatus.LONG_SELECTED,
        CompositionStatus.SHORT_SELECTED,
    ):
        return _finalize_decision(
            inp,
            policy,
            decision_outcome=DecisionOutcome.BLOCKED,
            entry_eligibility=EntryEligibility.BLOCKED,
            exit_class=ExitClass.NONE,
            position_management_action=PositionManagementAction.NONE,
            reversal_state=ReversalState.NONE,
            reduce_only=False,
            position_flip_allowed=False,
            reason_codes=("entry_blocked",) + entry_block_reasons,
            precedence_trace=(DecisionPrecedenceStage.NEW_ENTRY.value,),
            computed_input_digest=computed_digest,
        )

    # --- Precedence 8: Observe ---
    if (
        comp.composition_status
        in (
            CompositionStatus.OBSERVE,
            CompositionStatus.CHOP_GUARD_BLOCK,
        )
        or comp.conflict_status is CompositionConflictStatus.BOTH_SIDES_CONFIRMED
    ):
        return _finalize_decision(
            inp,
            policy,
            decision_outcome=DecisionOutcome.OBSERVE,
            entry_eligibility=EntryEligibility.BLOCKED,
            exit_class=ExitClass.NONE,
            position_management_action=PositionManagementAction.NONE,
            reversal_state=ReversalState.NONE,
            reduce_only=False,
            position_flip_allowed=False,
            reason_codes=("observe_only",),
            precedence_trace=(DecisionPrecedenceStage.OBSERVE.value,),
            computed_input_digest=computed_digest,
        )

    # --- Precedence 9: No action ---
    return _finalize_decision(
        inp,
        policy,
        decision_outcome=DecisionOutcome.NO_ACTION,
        entry_eligibility=EntryEligibility.NOT_APPLICABLE,
        exit_class=ExitClass.NONE,
        position_management_action=PositionManagementAction.NONE,
        reversal_state=ReversalState.NONE,
        reduce_only=False,
        position_flip_allowed=False,
        reason_codes=("no_action",),
        precedence_trace=(DecisionPrecedenceStage.NO_ACTION.value,),
        computed_input_digest=computed_digest,
    )
