# src/trading/master_v2/double_play_composition_matrix_v1.py
"""
Pure Double Play Composition Matrix v1: offline Bull/Bear coordination contract.

Consumes immutable DirectionalAssessmentV1, SurvivalResultV1, and SuitabilityResultV1
evidence for both sides. Produces a single canonical composition result for the
trading decision path — no runtime, authority, order, risk, sizing, or capital effects.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from enum import Enum
from typing import Mapping, Optional, Tuple

from trading.master_v2.directional_assessment_v1 import (
    DirectionalAssessmentSide,
    DirectionalAssessmentStatus,
    DirectionalAssessmentV1,
    serialize_directional_assessment_canonical,
)
from trading.master_v2.suitability_binding_v1 import (
    DirectionalAssessmentRefV1,
    SuitabilityBindingStatus,
    SuitabilityResultV1,
    SurvivalResultRefV1,
    directional_assessment_ref_from_assessment_v1,
    survival_result_ref_from_result,
)
from trading.master_v2.survival_assessment_v1 import (
    SurvivalAssessmentStatus,
    SurvivalResultV1,
)

DOUBLE_PLAY_COMPOSITION_MATRIX_LAYER_VERSION = "v1"
DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION = "double_play_composition_matrix_policy_v1"

_AUTHORITY_EFFECT_NONE = "NONE"
_RUNTIME_EFFECT_NONE = "NONE"
_ORDER_EFFECT_NONE = "NONE"
_RISK_EFFECT_NONE = "NONE"
_SIZING_EFFECT_NONE = "NONE"

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})


class CompositionDirectionState(str, Enum):
    NEUTRAL = "neutral"
    LONG = "long"
    SHORT = "short"


class PositionManagementContext(str, Enum):
    FLAT = "flat"
    LONG_POSITION = "long_position"
    SHORT_POSITION = "short_position"


class CompositionStatus(str, Enum):
    NO_ACTION = "no_action"
    OBSERVE = "observe"
    LONG_SELECTED = "long_selected"
    SHORT_SELECTED = "short_selected"
    CHOP_GUARD_BLOCK = "chop_guard_block"
    REVERSAL_PREPARATION = "reversal_preparation"
    BLOCKED = "blocked"


class CompositionSelectedSide(str, Enum):
    NONE = "none"
    LONG = "long"
    SHORT = "short"


class CompositionConflictStatus(str, Enum):
    NONE = "none"
    BOTH_SIDES_CONFIRMED = "both_sides_confirmed"
    BOTH_SIDES_CANDIDATE = "both_sides_candidate"
    INPUT_CONFLICT = "input_conflict"


class CompositionChopGuardStatus(str, Enum):
    NONE = "none"
    CHOP_GUARD_BLOCK = "chop_guard_block"
    CHOP_GUARD_CANDIDATE = "chop_guard_candidate"


class CompositionBlockedReason(str, Enum):
    INPUT_INCOMPLETE = "input_incomplete"
    INSTRUMENT_KIND_FORBIDDEN = "instrument_kind_forbidden"
    INSTRUMENT_MISMATCH = "instrument_mismatch"
    TRADING_EPOCH_MISMATCH = "trading_epoch_mismatch"
    TRADING_EPOCH_OUT_OF_ORDER = "trading_epoch_out_of_order"
    TRADING_EPOCH_STALE = "trading_epoch_stale"
    INPUT_DIGEST_MISMATCH = "input_digest_mismatch"
    CONTEXT_REFERENCE_MISMATCH = "context_reference_mismatch"
    BULL_SIDE_MISMATCH = "bull_side_mismatch"
    BEAR_SIDE_MISMATCH = "bear_side_mismatch"
    BULL_ASSESSMENT_REF_MISMATCH = "bull_assessment_ref_mismatch"
    BEAR_ASSESSMENT_REF_MISMATCH = "bear_assessment_ref_mismatch"
    BULL_SURVIVAL_REF_MISMATCH = "bull_survival_ref_mismatch"
    BEAR_SURVIVAL_REF_MISMATCH = "bear_survival_ref_mismatch"
    BULL_SUITABILITY_REF_MISMATCH = "bull_suitability_ref_mismatch"
    BEAR_SUITABILITY_REF_MISMATCH = "bear_suitability_ref_mismatch"
    POLICY_VERSION_INVALID = "policy_version_invalid"
    POLICY_VALIDITY_EPOCHS_INVALID = "policy_validity_epochs_invalid"
    SURVIVAL_NOT_PASS = "survival_not_pass"
    SUITABILITY_NOT_PASS = "suitability_not_pass"
    BOTH_SIDES_INVALID = "both_sides_invalid"
    BOTH_SIDES_BLOCKED = "both_sides_blocked"
    AMBIGUOUS_COMPOSITION = "ambiguous_composition"
    EXPLICIT_BLOCKED = "explicit_blocked"


class BothCandidateOutcome(str, Enum):
    OBSERVE = "observe"
    CHOP_GUARD_CANDIDATE = "chop_guard_candidate"


class BothInvalidOutcome(str, Enum):
    BLOCKED = "blocked"
    NO_ACTION = "no_action"


@dataclass(frozen=True)
class SuitabilityResultRefV1:
    suitability_id: str
    semantic_digest: str
    trading_epoch: int
    side: DirectionalAssessmentSide
    status: SuitabilityBindingStatus

    def __post_init__(self) -> None:
        if self.semantic_digest and not _valid_sha256_hex(self.semantic_digest):
            msg = "semantic_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)


@dataclass(frozen=True)
class DoublePlayCompositionPolicyV1:
    validity_epochs: int
    both_candidate_outcome: BothCandidateOutcome = BothCandidateOutcome.OBSERVE
    both_invalid_outcome: BothInvalidOutcome = BothInvalidOutcome.BLOCKED
    policy_version: str = DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION


@dataclass(frozen=True)
class DoublePlayCompositionInputV1:
    instrument_id: str
    trading_epoch: int
    context_reference: str
    bull_directional_assessment: DirectionalAssessmentV1
    bear_directional_assessment: DirectionalAssessmentV1
    bull_survival_result: SurvivalResultV1
    bear_survival_result: SurvivalResultV1
    bull_suitability_result: SuitabilityResultV1
    bear_suitability_result: SuitabilityResultV1
    previous_direction_state: CompositionDirectionState
    position_management_context: PositionManagementContext
    last_evaluated_trading_epoch: int
    input_complete: bool
    input_digest: str
    explicit_blocked_reasons: Tuple[CompositionBlockedReason, ...] = ()
    policy_version: str = DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION


@dataclass(frozen=True)
class DoublePlayCompositionResultV1:
    composition_id: str
    instrument_id: str
    trading_epoch: int
    context_reference: str
    bull_assessment_ref: DirectionalAssessmentRefV1
    bear_assessment_ref: DirectionalAssessmentRefV1
    bull_survival_ref: SurvivalResultRefV1
    bear_survival_ref: SurvivalResultRefV1
    bull_suitability_ref: SuitabilityResultRefV1
    bear_suitability_ref: SuitabilityResultRefV1
    previous_direction_state: CompositionDirectionState
    position_management_context: PositionManagementContext
    composition_status: CompositionStatus
    selected_side: CompositionSelectedSide
    conflict_status: CompositionConflictStatus
    chop_guard_status: CompositionChopGuardStatus
    reason_codes: Tuple[str, ...]
    policy_version: str
    input_digest: str
    semantic_digest: str
    authority_effect: str = _AUTHORITY_EFFECT_NONE
    runtime_effect: str = _RUNTIME_EFFECT_NONE
    order_effect: str = _ORDER_EFFECT_NONE
    risk_effect: str = _RISK_EFFECT_NONE
    sizing_effect: str = _SIZING_EFFECT_NONE

    def __post_init__(self) -> None:
        if self.semantic_digest and not _valid_sha256_hex(self.semantic_digest):
            msg = "semantic_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)
        if self.input_digest and not _valid_sha256_hex(self.input_digest):
            msg = "input_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)


def _valid_sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and value > 0


def _instrument_id_allowed(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return not any(token in lowered for token in _FORBIDDEN_INSTRUMENT_SUBSTRINGS)


def validate_double_play_composition_policy(
    policy: DoublePlayCompositionPolicyV1,
    *,
    policy_version: str,
) -> Tuple[CompositionBlockedReason, ...]:
    blocks: list[CompositionBlockedReason] = []
    if policy.policy_version != policy_version:
        blocks.append(CompositionBlockedReason.POLICY_VERSION_INVALID)
    if not _positive_int(policy.validity_epochs):
        blocks.append(CompositionBlockedReason.POLICY_VALIDITY_EPOCHS_INVALID)
    return tuple(blocks)


def suitability_result_ref_from_result(result: SuitabilityResultV1) -> SuitabilityResultRefV1:
    return SuitabilityResultRefV1(
        suitability_id=result.suitability_id,
        semantic_digest=result.semantic_digest,
        trading_epoch=result.trading_epoch,
        side=result.side,
        status=result.status,
    )


def serialize_composition_input_canonical(inp: DoublePlayCompositionInputV1) -> str:
    payload: dict[str, object] = {
        "instrument_id": inp.instrument_id,
        "trading_epoch": inp.trading_epoch,
        "context_reference": inp.context_reference,
        "bull_directional_assessment": json.loads(
            serialize_directional_assessment_canonical(inp.bull_directional_assessment)
        ),
        "bear_directional_assessment": json.loads(
            serialize_directional_assessment_canonical(inp.bear_directional_assessment)
        ),
        "bull_survival_result": _serialize_survival_canonical(inp.bull_survival_result),
        "bear_survival_result": _serialize_survival_canonical(inp.bear_survival_result),
        "bull_suitability_result": _serialize_suitability_canonical(inp.bull_suitability_result),
        "bear_suitability_result": _serialize_suitability_canonical(inp.bear_suitability_result),
        "previous_direction_state": inp.previous_direction_state.value,
        "position_management_context": inp.position_management_context.value,
        "last_evaluated_trading_epoch": inp.last_evaluated_trading_epoch,
        "input_complete": inp.input_complete,
        "explicit_blocked_reasons": sorted(r.value for r in inp.explicit_blocked_reasons),
        "policy_version": inp.policy_version,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _serialize_survival_canonical(result: SurvivalResultV1) -> dict[str, object]:
    return {
        "survival_id": result.survival_id,
        "instrument_id": result.instrument_id,
        "side": result.side.value,
        "trading_epoch": result.trading_epoch,
        "status": result.status.value,
        "semantic_digest": result.semantic_digest,
        "policy_version": result.policy_version,
    }


def _serialize_suitability_canonical(result: SuitabilityResultV1) -> dict[str, object]:
    return {
        "suitability_id": result.suitability_id,
        "instrument_id": result.instrument_id,
        "side": result.side.value,
        "trading_epoch": result.trading_epoch,
        "status": result.status.value,
        "semantic_digest": result.semantic_digest,
        "ranking_policy_version": result.ranking_policy_version,
    }


def compute_composition_input_digest(inp: DoublePlayCompositionInputV1) -> str:
    canonical = serialize_composition_input_canonical(inp)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def serialize_composition_result_canonical(result: DoublePlayCompositionResultV1) -> str:
    payload: dict[str, object] = {
        "composition_id": result.composition_id,
        "instrument_id": result.instrument_id,
        "trading_epoch": result.trading_epoch,
        "context_reference": result.context_reference,
        "bull_assessment_ref": _serialize_directional_ref(result.bull_assessment_ref),
        "bear_assessment_ref": _serialize_directional_ref(result.bear_assessment_ref),
        "bull_survival_ref": _serialize_survival_ref(result.bull_survival_ref),
        "bear_survival_ref": _serialize_survival_ref(result.bear_survival_ref),
        "bull_suitability_ref": _serialize_suitability_ref(result.bull_suitability_ref),
        "bear_suitability_ref": _serialize_suitability_ref(result.bear_suitability_ref),
        "previous_direction_state": result.previous_direction_state.value,
        "position_management_context": result.position_management_context.value,
        "composition_status": result.composition_status.value,
        "selected_side": result.selected_side.value,
        "conflict_status": result.conflict_status.value,
        "chop_guard_status": result.chop_guard_status.value,
        "reason_codes": list(result.reason_codes),
        "policy_version": result.policy_version,
        "input_digest": result.input_digest,
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "order_effect": result.order_effect,
        "risk_effect": result.risk_effect,
        "sizing_effect": result.sizing_effect,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _serialize_directional_ref(ref: DirectionalAssessmentRefV1) -> dict[str, object]:
    return {
        "assessment_id": ref.assessment_id,
        "semantic_digest": ref.semantic_digest,
        "trading_epoch": ref.trading_epoch,
        "side": ref.side.value,
        "status": ref.status,
    }


def _serialize_survival_ref(ref: SurvivalResultRefV1) -> dict[str, object]:
    return {
        "survival_id": ref.survival_id,
        "semantic_digest": ref.semantic_digest,
        "trading_epoch": ref.trading_epoch,
        "side": ref.side.value,
        "status": ref.status.value,
    }


def _serialize_suitability_ref(ref: SuitabilityResultRefV1) -> dict[str, object]:
    return {
        "suitability_id": ref.suitability_id,
        "semantic_digest": ref.semantic_digest,
        "trading_epoch": ref.trading_epoch,
        "side": ref.side.value,
        "status": ref.status.value,
    }


def compute_composition_result_semantic_digest(result: DoublePlayCompositionResultV1) -> str:
    canonical = serialize_composition_result_canonical(result)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def with_computed_composition_result_digest(
    result: DoublePlayCompositionResultV1,
) -> DoublePlayCompositionResultV1:
    digest = compute_composition_result_semantic_digest(replace(result, semantic_digest=""))
    return replace(result, semantic_digest=digest)


def _derive_composition_id(
    instrument_id: str,
    trading_epoch: int,
    status: CompositionStatus,
) -> str:
    seed = f"{instrument_id}|{trading_epoch}|{status.value}|composition_matrix_v1"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]


def _assessment_status(assessment: DirectionalAssessmentV1) -> DirectionalAssessmentStatus:
    return assessment.status


def _side_fully_admissible(
    assessment: DirectionalAssessmentV1,
    survival: SurvivalResultV1,
    suitability: SuitabilityResultV1,
) -> bool:
    return (
        assessment.status is DirectionalAssessmentStatus.CONFIRMED
        and survival.status is SurvivalAssessmentStatus.PASS
        and suitability.status is SuitabilityBindingStatus.PASS
    )


def _both_assessments_confirmed(
    bull: DirectionalAssessmentV1,
    bear: DirectionalAssessmentV1,
) -> bool:
    return (
        bull.status is DirectionalAssessmentStatus.CONFIRMED
        and bear.status is DirectionalAssessmentStatus.CONFIRMED
    )


def _resolve_epoch_semantics(
    *,
    trading_epoch: int,
    last_evaluated_trading_epoch: int,
    bull_epoch: int,
    bear_epoch: int,
) -> Tuple[str, Optional[CompositionBlockedReason]]:
    max_upstream = max(bull_epoch, bear_epoch)
    if max_upstream > trading_epoch:
        return "stale_upstream_ref", CompositionBlockedReason.TRADING_EPOCH_STALE
    if last_evaluated_trading_epoch < 0:
        return "first", None
    if trading_epoch < last_evaluated_trading_epoch:
        return "out_of_order", CompositionBlockedReason.TRADING_EPOCH_OUT_OF_ORDER
    return "ok", None


def _collect_reference_blocks(
    inp: DoublePlayCompositionInputV1,
) -> Tuple[CompositionBlockedReason, ...]:
    blocks: list[CompositionBlockedReason] = []
    bull_a = inp.bull_directional_assessment
    bear_a = inp.bear_directional_assessment
    bull_s = inp.bull_survival_result
    bear_s = inp.bear_survival_result
    bull_u = inp.bull_suitability_result
    bear_u = inp.bear_suitability_result

    for assessment, survival, suitability, side_reason in (
        (bull_a, bull_s, bull_u, CompositionBlockedReason.BULL_ASSESSMENT_REF_MISMATCH),
        (bear_a, bear_s, bear_u, CompositionBlockedReason.BEAR_ASSESSMENT_REF_MISMATCH),
    ):
        if assessment.instrument_id != inp.instrument_id:
            blocks.append(side_reason)
        if survival.instrument_id != inp.instrument_id:
            blocks.append(
                CompositionBlockedReason.BULL_SURVIVAL_REF_MISMATCH
                if assessment.side is DirectionalAssessmentSide.LONG
                else CompositionBlockedReason.BEAR_SURVIVAL_REF_MISMATCH
            )
        if suitability.instrument_id != inp.instrument_id:
            blocks.append(
                CompositionBlockedReason.BULL_SUITABILITY_REF_MISMATCH
                if assessment.side is DirectionalAssessmentSide.LONG
                else CompositionBlockedReason.BEAR_SUITABILITY_REF_MISMATCH
            )
        if assessment.trading_epoch != inp.trading_epoch:
            blocks.append(side_reason)
        if survival.trading_epoch != inp.trading_epoch:
            blocks.append(
                CompositionBlockedReason.BULL_SURVIVAL_REF_MISMATCH
                if assessment.side is DirectionalAssessmentSide.LONG
                else CompositionBlockedReason.BEAR_SURVIVAL_REF_MISMATCH
            )
        if suitability.trading_epoch != inp.trading_epoch:
            blocks.append(
                CompositionBlockedReason.BULL_SUITABILITY_REF_MISMATCH
                if assessment.side is DirectionalAssessmentSide.LONG
                else CompositionBlockedReason.BEAR_SUITABILITY_REF_MISMATCH
            )
        surv_dref = survival.directional_assessment_ref
        if surv_dref.assessment_id != assessment.assessment_id:
            blocks.append(
                CompositionBlockedReason.BULL_SURVIVAL_REF_MISMATCH
                if assessment.side is DirectionalAssessmentSide.LONG
                else CompositionBlockedReason.BEAR_SURVIVAL_REF_MISMATCH
            )
        if surv_dref.semantic_digest != assessment.semantic_digest:
            blocks.append(
                CompositionBlockedReason.BULL_SURVIVAL_REF_MISMATCH
                if assessment.side is DirectionalAssessmentSide.LONG
                else CompositionBlockedReason.BEAR_SURVIVAL_REF_MISMATCH
            )

    if bull_a.side is not DirectionalAssessmentSide.LONG:
        blocks.append(CompositionBlockedReason.BULL_SIDE_MISMATCH)
    if bear_a.side is not DirectionalAssessmentSide.SHORT:
        blocks.append(CompositionBlockedReason.BEAR_SIDE_MISMATCH)

    if bull_a.instrument_id != bear_a.instrument_id:
        blocks.append(CompositionBlockedReason.INSTRUMENT_MISMATCH)
    if bull_a.trading_epoch != bear_a.trading_epoch:
        blocks.append(CompositionBlockedReason.TRADING_EPOCH_MISMATCH)

    return tuple(dict.fromkeys(blocks))


def _finalize_result(
    inp: DoublePlayCompositionInputV1,
    policy: DoublePlayCompositionPolicyV1,
    *,
    composition_status: CompositionStatus,
    selected_side: CompositionSelectedSide,
    conflict_status: CompositionConflictStatus,
    chop_guard_status: CompositionChopGuardStatus,
    reason_codes: Tuple[str, ...],
    computed_input_digest: str,
) -> DoublePlayCompositionResultV1:
    result = DoublePlayCompositionResultV1(
        composition_id=_derive_composition_id(
            inp.instrument_id, inp.trading_epoch, composition_status
        ),
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        context_reference=inp.context_reference,
        bull_assessment_ref=directional_assessment_ref_from_assessment_v1(
            inp.bull_directional_assessment
        ),
        bear_assessment_ref=directional_assessment_ref_from_assessment_v1(
            inp.bear_directional_assessment
        ),
        bull_survival_ref=survival_result_ref_from_result(inp.bull_survival_result),
        bear_survival_ref=survival_result_ref_from_result(inp.bear_survival_result),
        bull_suitability_ref=suitability_result_ref_from_result(inp.bull_suitability_result),
        bear_suitability_ref=suitability_result_ref_from_result(inp.bear_suitability_result),
        previous_direction_state=inp.previous_direction_state,
        position_management_context=inp.position_management_context,
        composition_status=composition_status,
        selected_side=selected_side,
        conflict_status=conflict_status,
        chop_guard_status=chop_guard_status,
        reason_codes=reason_codes,
        policy_version=policy.policy_version,
        input_digest=computed_input_digest,
        semantic_digest="",
    )
    return with_computed_composition_result_digest(result)


def evaluate_double_play_composition_matrix_v1(
    inp: DoublePlayCompositionInputV1,
    policy: DoublePlayCompositionPolicyV1,
) -> DoublePlayCompositionResultV1:
    """
    Deterministic Double Play composition matrix evaluator.

    Fail-closed on incomplete, mismatched, or epoch-invalid inputs. Never mutates
    upstream assessment, survival, or suitability evidence.
    """

    computed_digest = compute_composition_input_digest(inp)

    def blocked(
        reason: CompositionBlockedReason,
        *,
        reason_code: str,
        extra: Tuple[str, ...] = (),
    ) -> DoublePlayCompositionResultV1:
        codes = (reason_code, reason.value) + extra
        return _finalize_result(
            inp,
            policy,
            composition_status=CompositionStatus.BLOCKED,
            selected_side=CompositionSelectedSide.NONE,
            conflict_status=CompositionConflictStatus.INPUT_CONFLICT,
            chop_guard_status=CompositionChopGuardStatus.NONE,
            reason_codes=codes,
            computed_input_digest=computed_digest,
        )

    policy_blocks = validate_double_play_composition_policy(
        policy, policy_version=inp.policy_version
    )
    if policy_blocks:
        return blocked(
            CompositionBlockedReason.POLICY_VERSION_INVALID,
            reason_code="policy_validation_failed",
        )

    if not _instrument_id_allowed(inp.instrument_id):
        return blocked(
            CompositionBlockedReason.INSTRUMENT_KIND_FORBIDDEN,
            reason_code="instrument_gate_failed",
        )

    if not inp.input_complete:
        return blocked(
            CompositionBlockedReason.INPUT_INCOMPLETE,
            reason_code="input_gate_failed",
        )

    if inp.explicit_blocked_reasons:
        return _finalize_result(
            inp,
            policy,
            composition_status=CompositionStatus.BLOCKED,
            selected_side=CompositionSelectedSide.NONE,
            conflict_status=CompositionConflictStatus.INPUT_CONFLICT,
            chop_guard_status=CompositionChopGuardStatus.NONE,
            reason_codes=("explicit_blocked",)
            + tuple(sorted(r.value for r in inp.explicit_blocked_reasons)),
            computed_input_digest=computed_digest,
        )

    if inp.input_digest and inp.input_digest != computed_digest:
        return blocked(
            CompositionBlockedReason.INPUT_DIGEST_MISMATCH,
            reason_code="input_digest_mismatch",
        )

    ref_blocks = _collect_reference_blocks(inp)
    if ref_blocks:
        return blocked(ref_blocks[0], reason_code="reference_consistency_failed")

    epoch_mode, epoch_block = _resolve_epoch_semantics(
        trading_epoch=inp.trading_epoch,
        last_evaluated_trading_epoch=inp.last_evaluated_trading_epoch,
        bull_epoch=inp.bull_directional_assessment.trading_epoch,
        bear_epoch=inp.bear_directional_assessment.trading_epoch,
    )
    if epoch_block is not None:
        return blocked(epoch_block, reason_code=f"epoch_semantics_failed:{epoch_mode}")

    bull_a = inp.bull_directional_assessment
    bear_a = inp.bear_directional_assessment
    bull_s = inp.bull_survival_result
    bear_s = inp.bear_survival_result
    bull_u = inp.bull_suitability_result
    bear_u = inp.bear_suitability_result

    if _both_assessments_confirmed(bull_a, bear_a):
        reason_codes: Tuple[str, ...] = (
            "both_sides_confirmed",
            "chop_guard_block",
            "no_new_entry",
            "existing_position_management_continues",
        )
        return _finalize_result(
            inp,
            policy,
            composition_status=CompositionStatus.CHOP_GUARD_BLOCK,
            selected_side=CompositionSelectedSide.NONE,
            conflict_status=CompositionConflictStatus.BOTH_SIDES_CONFIRMED,
            chop_guard_status=CompositionChopGuardStatus.CHOP_GUARD_BLOCK,
            reason_codes=reason_codes,
            computed_input_digest=computed_digest,
        )

    bull_status = _assessment_status(bull_a)
    bear_status = _assessment_status(bear_a)

    if (
        bull_status is DirectionalAssessmentStatus.INVALID
        and bear_status is DirectionalAssessmentStatus.INVALID
    ):
        outcome = policy.both_invalid_outcome
        if outcome is BothInvalidOutcome.NO_ACTION:
            return _finalize_result(
                inp,
                policy,
                composition_status=CompositionStatus.NO_ACTION,
                selected_side=CompositionSelectedSide.NONE,
                conflict_status=CompositionConflictStatus.NONE,
                chop_guard_status=CompositionChopGuardStatus.NONE,
                reason_codes=("both_sides_invalid", "no_action"),
                computed_input_digest=computed_digest,
            )
        return blocked(
            CompositionBlockedReason.BOTH_SIDES_INVALID,
            reason_code="both_sides_invalid",
        )

    if (
        bull_status is DirectionalAssessmentStatus.BLOCKED
        and bear_status is DirectionalAssessmentStatus.BLOCKED
    ):
        return blocked(
            CompositionBlockedReason.BOTH_SIDES_BLOCKED,
            reason_code="both_sides_blocked",
        )

    if (
        bull_status is DirectionalAssessmentStatus.CANDIDATE
        and bear_status is DirectionalAssessmentStatus.CANDIDATE
    ):
        if policy.both_candidate_outcome is BothCandidateOutcome.CHOP_GUARD_CANDIDATE:
            return _finalize_result(
                inp,
                policy,
                composition_status=CompositionStatus.OBSERVE,
                selected_side=CompositionSelectedSide.NONE,
                conflict_status=CompositionConflictStatus.BOTH_SIDES_CANDIDATE,
                chop_guard_status=CompositionChopGuardStatus.CHOP_GUARD_CANDIDATE,
                reason_codes=("both_sides_candidate", "chop_guard_candidate", "no_entry"),
                computed_input_digest=computed_digest,
            )
        return _finalize_result(
            inp,
            policy,
            composition_status=CompositionStatus.OBSERVE,
            selected_side=CompositionSelectedSide.NONE,
            conflict_status=CompositionConflictStatus.BOTH_SIDES_CANDIDATE,
            chop_guard_status=CompositionChopGuardStatus.NONE,
            reason_codes=("both_sides_candidate", "observe_only", "no_entry"),
            computed_input_digest=computed_digest,
        )

    bull_admissible = _side_fully_admissible(bull_a, bull_s, bull_u)
    bear_admissible = _side_fully_admissible(bear_a, bear_s, bear_u)

    if (
        inp.position_management_context is PositionManagementContext.LONG_POSITION
        and bear_admissible
    ):
        return _finalize_result(
            inp,
            policy,
            composition_status=CompositionStatus.REVERSAL_PREPARATION,
            selected_side=CompositionSelectedSide.NONE,
            conflict_status=CompositionConflictStatus.NONE,
            chop_guard_status=CompositionChopGuardStatus.NONE,
            reason_codes=("existing_long_position", "bear_confirmed", "reversal_preparation"),
            computed_input_digest=computed_digest,
        )

    if (
        inp.position_management_context is PositionManagementContext.SHORT_POSITION
        and bull_admissible
    ):
        return _finalize_result(
            inp,
            policy,
            composition_status=CompositionStatus.REVERSAL_PREPARATION,
            selected_side=CompositionSelectedSide.NONE,
            conflict_status=CompositionConflictStatus.NONE,
            chop_guard_status=CompositionChopGuardStatus.NONE,
            reason_codes=("existing_short_position", "bull_confirmed", "reversal_preparation"),
            computed_input_digest=computed_digest,
        )

    if bull_admissible and not bear_admissible:
        return _finalize_result(
            inp,
            policy,
            composition_status=CompositionStatus.LONG_SELECTED,
            selected_side=CompositionSelectedSide.LONG,
            conflict_status=CompositionConflictStatus.NONE,
            chop_guard_status=CompositionChopGuardStatus.NONE,
            reason_codes=("long_only_admissible",),
            computed_input_digest=computed_digest,
        )

    if bear_admissible and not bull_admissible:
        return _finalize_result(
            inp,
            policy,
            composition_status=CompositionStatus.SHORT_SELECTED,
            selected_side=CompositionSelectedSide.SHORT,
            conflict_status=CompositionConflictStatus.NONE,
            chop_guard_status=CompositionChopGuardStatus.NONE,
            reason_codes=("short_only_admissible",),
            computed_input_digest=computed_digest,
        )

    for assessment, survival, suitability, side_label in (
        (bull_a, bull_s, bull_u, "bull"),
        (bear_a, bear_s, bear_u, "bear"),
    ):
        if assessment.status is DirectionalAssessmentStatus.CONFIRMED:
            if survival.status is not SurvivalAssessmentStatus.PASS:
                return blocked(
                    CompositionBlockedReason.SURVIVAL_NOT_PASS,
                    reason_code=f"{side_label}_confirmed_survival_not_pass",
                )
            if suitability.status is not SuitabilityBindingStatus.PASS:
                return blocked(
                    CompositionBlockedReason.SUITABILITY_NOT_PASS,
                    reason_code=f"{side_label}_confirmed_suitability_not_pass",
                )

    candidate_present = (
        bull_status is DirectionalAssessmentStatus.CANDIDATE
        or bear_status is DirectionalAssessmentStatus.CANDIDATE
    )
    observe_present = (
        bull_status is DirectionalAssessmentStatus.OBSERVE
        or bear_status is DirectionalAssessmentStatus.OBSERVE
    )
    if candidate_present or observe_present:
        return _finalize_result(
            inp,
            policy,
            composition_status=CompositionStatus.OBSERVE,
            selected_side=CompositionSelectedSide.NONE,
            conflict_status=CompositionConflictStatus.NONE,
            chop_guard_status=CompositionChopGuardStatus.NONE,
            reason_codes=("observe_or_candidate_only", "no_entry"),
            computed_input_digest=computed_digest,
        )

    if (
        bull_status is DirectionalAssessmentStatus.INVALID
        or bear_status is DirectionalAssessmentStatus.INVALID
    ):
        return blocked(
            CompositionBlockedReason.AMBIGUOUS_COMPOSITION,
            reason_code="one_side_invalid",
        )

    return blocked(
        CompositionBlockedReason.AMBIGUOUS_COMPOSITION,
        reason_code="composition_unresolved",
    )


__all__ = [
    "DOUBLE_PLAY_COMPOSITION_MATRIX_LAYER_VERSION",
    "DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION",
    "BothCandidateOutcome",
    "BothInvalidOutcome",
    "CompositionBlockedReason",
    "CompositionChopGuardStatus",
    "CompositionConflictStatus",
    "CompositionDirectionState",
    "CompositionSelectedSide",
    "CompositionStatus",
    "DoublePlayCompositionInputV1",
    "DoublePlayCompositionPolicyV1",
    "DoublePlayCompositionResultV1",
    "PositionManagementContext",
    "SuitabilityResultRefV1",
    "compute_composition_input_digest",
    "compute_composition_result_semantic_digest",
    "evaluate_double_play_composition_matrix_v1",
    "serialize_composition_input_canonical",
    "serialize_composition_result_canonical",
    "suitability_result_ref_from_result",
    "validate_double_play_composition_policy",
    "with_computed_composition_result_digest",
]
