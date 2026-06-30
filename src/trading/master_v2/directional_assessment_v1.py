# src/trading/master_v2/directional_assessment_v1.py
"""
Pure Directional Assessment v1: shared Bull/Bear offline assessment contract.

Consumes immutable scope-event references and explicit feature inputs. Produces
fachliche directional assessment evidence only — no runtime, authority, order,
risk, sizing, or survival-formula effects.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional, Tuple

from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    ClockTrustStatus,
    DataIntegrityStatus,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import mirror_price_for_short

DIRECTIONAL_ASSESSMENT_LAYER_VERSION = "v1"
DIRECTIONAL_ASSESSMENT_POLICY_VERSION = "directional_assessment_policy_v1"

_AUTHORITY_EFFECT_NONE = "NONE"
_RUNTIME_EFFECT_NONE = "NONE"
_ORDER_EFFECT_NONE = "NONE"
_RISK_EFFECT_NONE = "NONE"

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})


class DirectionalAssessmentSide(str, Enum):
    """Unified side semantics: LONG/BULL and SHORT/BEAR share one contract."""

    LONG = "long"
    SHORT = "short"


class DirectionalAssessmentStatus(str, Enum):
    INVALID = "invalid"
    BLOCKED = "blocked"
    OBSERVE = "observe"
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"


class DirectionalAssessmentHardBlockReason(str, Enum):
    INSTRUMENT_KIND_FORBIDDEN = "instrument_kind_forbidden"
    INPUT_INCOMPLETE = "input_incomplete"
    PRICE_PATH_TOO_SHORT = "price_path_too_short"
    REFERENCE_PRICE_NON_POSITIVE = "reference_price_non_positive"
    SCOPE_EVENT_REF_INVALID = "scope_event_ref_invalid"
    SCOPE_EVENT_REF_STALE = "scope_event_ref_stale"
    POLICY_VERSION_INVALID = "policy_version_invalid"
    POLICY_CANDIDATE_THRESHOLD_INVALID = "policy_candidate_threshold_invalid"
    POLICY_CONFIRMATION_THRESHOLD_INVALID = "policy_confirmation_threshold_invalid"
    POLICY_OBSERVE_THRESHOLD_INVALID = "policy_observe_threshold_invalid"
    POLICY_CONFIRMATION_EPOCHS_INVALID = "policy_confirmation_epochs_invalid"
    POLICY_VALIDITY_EPOCHS_INVALID = "policy_validity_epochs_invalid"
    POLICY_THRESHOLD_ORDER_INVALID = "policy_threshold_order_invalid"
    BAR_UNFINALIZED = "bar_unfinalized"
    DATA_INTEGRITY_UNTRUSTED = "data_integrity_untrusted"
    DATA_INTEGRITY_UNKNOWN = "data_integrity_unknown"
    CLOCK_TRUST_UNTRUSTED = "clock_trust_untrusted"
    CLOCK_TRUST_UNKNOWN = "clock_trust_unknown"
    TRUSTED_DATA_FALSE = "trusted_data_false"
    TRADING_EPOCH_OUT_OF_ORDER = "trading_epoch_out_of_order"
    TRADING_EPOCH_STALE = "trading_epoch_stale"
    EXPLICIT_HARD_BLOCK = "explicit_hard_block"


_BULL_BEAR_ALIASES: Mapping[str, DirectionalAssessmentSide] = {
    "long": DirectionalAssessmentSide.LONG,
    "bull": DirectionalAssessmentSide.LONG,
    "short": DirectionalAssessmentSide.SHORT,
    "bear": DirectionalAssessmentSide.SHORT,
}


def normalize_bull_bear_side(label: str) -> DirectionalAssessmentSide:
    """Map LONG/BULL and SHORT/BEAR labels to the unified side enum."""
    key = label.strip().lower()
    if key not in _BULL_BEAR_ALIASES:
        msg = f"unsupported bull/bear side label: {label!r}"
        raise ValueError(msg)
    return _BULL_BEAR_ALIASES[key]


@dataclass(frozen=True)
class ScopeEventRefV1:
    """Immutable scope-event reference; never mutates underlying evidence."""

    scope_event_id: str
    semantic_digest: str
    event_type: str
    trading_epoch: int

    def __post_init__(self) -> None:
        if self.semantic_digest and not _valid_sha256_hex(self.semantic_digest):
            msg = "semantic_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)


@dataclass(frozen=True)
class DirectionalConfirmationStateV1:
    candidate_count: int
    last_evaluated_trading_epoch: int
    last_signal_strength: float


@dataclass(frozen=True)
class DirectionalAssessmentPolicyV1:
    observe_signal_threshold: float
    candidate_signal_threshold: float
    confirmation_signal_threshold: float
    confirmation_epochs: int
    validity_epochs: int
    policy_version: str = DIRECTIONAL_ASSESSMENT_POLICY_VERSION


@dataclass(frozen=True)
class DirectionalAssessmentInputV1:
    instrument_id: str
    trading_epoch: int
    side: DirectionalAssessmentSide
    price_path: Tuple[float, ...]
    reference_price: float
    feature_refs: Tuple[str, ...]
    scope_event_ref: ScopeEventRefV1
    survival_preconditions: Tuple[str, ...]
    confirmation_state: DirectionalConfirmationStateV1
    data_integrity_status: DataIntegrityStatus
    clock_trust_status: ClockTrustStatus
    bar_finality_status: BarFinalityStatus
    trusted_data: bool
    input_complete: bool
    explicit_hard_block_reasons: Tuple[DirectionalAssessmentHardBlockReason, ...]
    policy_version: str


@dataclass(frozen=True)
class DirectionalAssessmentV1:
    assessment_id: str
    side: DirectionalAssessmentSide
    instrument_id: str
    trading_epoch: int
    status: DirectionalAssessmentStatus
    signal_strength: float
    confidence: float
    feature_refs: Tuple[str, ...]
    scope_event_ref: ScopeEventRefV1
    survival_preconditions: Tuple[str, ...]
    hard_block_reasons: Tuple[str, ...]
    reason_codes: Tuple[str, ...]
    valid_until_epoch: int
    semantic_digest: str
    authority_effect: str = _AUTHORITY_EFFECT_NONE
    runtime_effect: str = _RUNTIME_EFFECT_NONE
    order_effect: str = _ORDER_EFFECT_NONE
    risk_effect: str = _RISK_EFFECT_NONE

    def __post_init__(self) -> None:
        if self.semantic_digest and not _valid_sha256_hex(self.semantic_digest):
            msg = "semantic_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)
        if self.valid_until_epoch <= self.trading_epoch:
            msg = "valid_until_epoch must be strictly greater than trading_epoch"
            raise ValueError(msg)


def _valid_sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _positive_finite(value: object) -> bool:
    return isinstance(value, (int, float)) and float(value) > 0.0


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and value > 0


def _instrument_id_allowed(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return not any(token in lowered for token in _FORBIDDEN_INSTRUMENT_SUBSTRINGS)


def _sorted_reason_values(
    reasons: Tuple[DirectionalAssessmentHardBlockReason, ...],
) -> Tuple[str, ...]:
    return tuple(sorted(r.value for r in reasons))


def validate_directional_assessment_policy(
    policy: DirectionalAssessmentPolicyV1,
    *,
    policy_version: str,
) -> Tuple[DirectionalAssessmentHardBlockReason, ...]:
    blocks: list[DirectionalAssessmentHardBlockReason] = []
    if not policy.policy_version or policy.policy_version != DIRECTIONAL_ASSESSMENT_POLICY_VERSION:
        blocks.append(DirectionalAssessmentHardBlockReason.POLICY_VERSION_INVALID)
    if policy_version != DIRECTIONAL_ASSESSMENT_POLICY_VERSION:
        blocks.append(DirectionalAssessmentHardBlockReason.POLICY_VERSION_INVALID)
    if not _positive_finite(policy.observe_signal_threshold):
        blocks.append(DirectionalAssessmentHardBlockReason.POLICY_OBSERVE_THRESHOLD_INVALID)
    if not _positive_finite(policy.candidate_signal_threshold):
        blocks.append(DirectionalAssessmentHardBlockReason.POLICY_CANDIDATE_THRESHOLD_INVALID)
    if not _positive_finite(policy.confirmation_signal_threshold):
        blocks.append(DirectionalAssessmentHardBlockReason.POLICY_CONFIRMATION_THRESHOLD_INVALID)
    if not _positive_int(policy.confirmation_epochs):
        blocks.append(DirectionalAssessmentHardBlockReason.POLICY_CONFIRMATION_EPOCHS_INVALID)
    if not _positive_int(policy.validity_epochs):
        blocks.append(DirectionalAssessmentHardBlockReason.POLICY_VALIDITY_EPOCHS_INVALID)
    if (
        DirectionalAssessmentHardBlockReason.POLICY_OBSERVE_THRESHOLD_INVALID not in blocks
        and DirectionalAssessmentHardBlockReason.POLICY_CANDIDATE_THRESHOLD_INVALID not in blocks
        and DirectionalAssessmentHardBlockReason.POLICY_CONFIRMATION_THRESHOLD_INVALID not in blocks
        and not (
            policy.observe_signal_threshold
            < policy.candidate_signal_threshold
            < policy.confirmation_signal_threshold
        )
    ):
        blocks.append(DirectionalAssessmentHardBlockReason.POLICY_THRESHOLD_ORDER_INVALID)
    return tuple(dict.fromkeys(blocks))


def compute_signal_strength(
    *,
    price_path: Tuple[float, ...],
    side: DirectionalAssessmentSide,
    reference_price: float,
) -> float:
    if len(price_path) < 2 or not _positive_finite(reference_price):
        return 0.0
    start = float(price_path[0])
    end = float(price_path[-1])
    raw_return = (end - start) / float(reference_price)
    if side is DirectionalAssessmentSide.SHORT:
        raw_return = -raw_return
    return raw_return


def mirror_price_path_for_short(
    price_path: Tuple[float, ...],
    reference: float,
) -> Tuple[float, ...]:
    """Structural mirror for Bull/Bear symmetry tests."""
    return tuple(mirror_price_for_short(float(p), float(reference)) for p in price_path)


def compute_directional_confidence(
    signal_strength: float,
    confirmation_threshold: float,
) -> float:
    if not _positive_finite(confirmation_threshold) or signal_strength <= 0.0:
        return 0.0
    return min(1.0, float(signal_strength) / float(confirmation_threshold))


def _collect_input_gate_blocks(
    inp: DirectionalAssessmentInputV1,
) -> Tuple[DirectionalAssessmentHardBlockReason, ...]:
    blocks: list[DirectionalAssessmentHardBlockReason] = []
    if not inp.input_complete:
        blocks.append(DirectionalAssessmentHardBlockReason.INPUT_INCOMPLETE)
    if len(inp.price_path) < 2:
        blocks.append(DirectionalAssessmentHardBlockReason.PRICE_PATH_TOO_SHORT)
    if not _positive_finite(inp.reference_price):
        blocks.append(DirectionalAssessmentHardBlockReason.REFERENCE_PRICE_NON_POSITIVE)
    if not inp.scope_event_ref.scope_event_id or not inp.scope_event_ref.semantic_digest:
        blocks.append(DirectionalAssessmentHardBlockReason.SCOPE_EVENT_REF_INVALID)
    if not _instrument_id_allowed(inp.instrument_id):
        blocks.append(DirectionalAssessmentHardBlockReason.INSTRUMENT_KIND_FORBIDDEN)
    if inp.bar_finality_status is not BarFinalityStatus.FINALIZED:
        blocks.append(DirectionalAssessmentHardBlockReason.BAR_UNFINALIZED)
    if inp.data_integrity_status in (DataIntegrityStatus.UNTRUSTED, DataIntegrityStatus.INVALID):
        blocks.append(DirectionalAssessmentHardBlockReason.DATA_INTEGRITY_UNTRUSTED)
    elif inp.data_integrity_status is DataIntegrityStatus.UNKNOWN:
        blocks.append(DirectionalAssessmentHardBlockReason.DATA_INTEGRITY_UNKNOWN)
    if inp.clock_trust_status in (ClockTrustStatus.UNTRUSTED, ClockTrustStatus.INVALID):
        blocks.append(DirectionalAssessmentHardBlockReason.CLOCK_TRUST_UNTRUSTED)
    elif inp.clock_trust_status is ClockTrustStatus.UNKNOWN:
        blocks.append(DirectionalAssessmentHardBlockReason.CLOCK_TRUST_UNKNOWN)
    if not inp.trusted_data:
        blocks.append(DirectionalAssessmentHardBlockReason.TRUSTED_DATA_FALSE)
    if inp.explicit_hard_block_reasons:
        blocks.append(DirectionalAssessmentHardBlockReason.EXPLICIT_HARD_BLOCK)
    return tuple(dict.fromkeys(blocks))


def _resolve_epoch_semantics(
    *,
    trading_epoch: int,
    last_evaluated_trading_epoch: int,
    scope_event_epoch: int,
) -> Tuple[str, Optional[DirectionalAssessmentHardBlockReason]]:
    if scope_event_epoch > trading_epoch:
        return "stale_scope_ref", DirectionalAssessmentHardBlockReason.SCOPE_EVENT_REF_STALE
    if last_evaluated_trading_epoch < 0:
        return "first", None
    if trading_epoch < last_evaluated_trading_epoch:
        return "out_of_order", DirectionalAssessmentHardBlockReason.TRADING_EPOCH_OUT_OF_ORDER
    if trading_epoch > last_evaluated_trading_epoch + 1:
        return "skipped", None
    if trading_epoch == last_evaluated_trading_epoch:
        return "duplicate", None
    return "consecutive", None


def _derive_assessment_id(
    instrument_id: str,
    trading_epoch: int,
    side: DirectionalAssessmentSide,
    status: DirectionalAssessmentStatus,
) -> str:
    return f"dir-assess-{instrument_id}-epoch{trading_epoch}-{side.value}-{status.value}"


def _status_for_signal(
    *,
    signal_strength: float,
    policy: DirectionalAssessmentPolicyV1,
    confirmation_state: DirectionalConfirmationStateV1,
    epoch_mode: str,
) -> Tuple[DirectionalAssessmentStatus, Tuple[str, ...], int]:
    if signal_strength < policy.observe_signal_threshold:
        return DirectionalAssessmentStatus.OBSERVE, ("signal_below_observe_threshold",), 0

    if signal_strength < policy.candidate_signal_threshold:
        return DirectionalAssessmentStatus.OBSERVE, ("signal_between_observe_and_candidate",), 0

    next_count = 1
    if (
        epoch_mode == "consecutive"
        and confirmation_state.last_signal_strength >= policy.candidate_signal_threshold
    ):
        next_count = confirmation_state.candidate_count + 1
    elif epoch_mode == "duplicate":
        next_count = confirmation_state.candidate_count

    if (
        signal_strength >= policy.confirmation_signal_threshold
        and next_count >= policy.confirmation_epochs
    ):
        return (
            DirectionalAssessmentStatus.CONFIRMED,
            ("signal_meets_confirmation_threshold", "confirmation_epochs_satisfied"),
            next_count,
        )

    return (
        DirectionalAssessmentStatus.CANDIDATE,
        ("signal_meets_candidate_threshold", "confirmation_pending"),
        next_count,
    )


def serialize_directional_assessment_canonical(assessment: DirectionalAssessmentV1) -> str:
    scope_ref = assessment.scope_event_ref
    payload = {
        "assessment_id": assessment.assessment_id,
        "authority_effect": assessment.authority_effect,
        "confidence": assessment.confidence,
        "feature_refs": sorted(assessment.feature_refs),
        "hard_block_reasons": sorted(assessment.hard_block_reasons),
        "instrument_id": assessment.instrument_id,
        "layer_version": DIRECTIONAL_ASSESSMENT_LAYER_VERSION,
        "order_effect": assessment.order_effect,
        "policy_version": DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
        "reason_codes": sorted(assessment.reason_codes),
        "risk_effect": assessment.risk_effect,
        "runtime_effect": assessment.runtime_effect,
        "scope_event_id": scope_ref.scope_event_id,
        "scope_event_digest": scope_ref.semantic_digest,
        "scope_event_epoch": scope_ref.trading_epoch,
        "scope_event_type": scope_ref.event_type,
        "side": assessment.side.value,
        "signal_strength": assessment.signal_strength,
        "status": assessment.status.value,
        "survival_preconditions": sorted(assessment.survival_preconditions),
        "trading_epoch": assessment.trading_epoch,
        "valid_until_epoch": assessment.valid_until_epoch,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_directional_assessment_semantic_digest(assessment: DirectionalAssessmentV1) -> str:
    canonical = serialize_directional_assessment_canonical(assessment)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def with_computed_directional_assessment_digest(
    assessment: DirectionalAssessmentV1,
) -> DirectionalAssessmentV1:
    digest = compute_directional_assessment_semantic_digest(assessment)
    return DirectionalAssessmentV1(
        assessment_id=assessment.assessment_id,
        side=assessment.side,
        instrument_id=assessment.instrument_id,
        trading_epoch=assessment.trading_epoch,
        status=assessment.status,
        signal_strength=assessment.signal_strength,
        confidence=assessment.confidence,
        feature_refs=assessment.feature_refs,
        scope_event_ref=assessment.scope_event_ref,
        survival_preconditions=assessment.survival_preconditions,
        hard_block_reasons=assessment.hard_block_reasons,
        reason_codes=assessment.reason_codes,
        valid_until_epoch=assessment.valid_until_epoch,
        semantic_digest=digest,
        authority_effect=assessment.authority_effect,
        runtime_effect=assessment.runtime_effect,
        order_effect=assessment.order_effect,
        risk_effect=assessment.risk_effect,
    )


def _finalize_assessment(
    inp: DirectionalAssessmentInputV1,
    policy: DirectionalAssessmentPolicyV1,
    *,
    status: DirectionalAssessmentStatus,
    signal_strength: float,
    confidence: float,
    hard_block_reasons: Tuple[str, ...],
    reason_codes: Tuple[str, ...],
) -> DirectionalAssessmentV1:
    valid_until = inp.trading_epoch + policy.validity_epochs
    assessment = DirectionalAssessmentV1(
        assessment_id=_derive_assessment_id(inp.instrument_id, inp.trading_epoch, inp.side, status),
        side=inp.side,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        status=status,
        signal_strength=signal_strength,
        confidence=confidence,
        feature_refs=inp.feature_refs,
        scope_event_ref=inp.scope_event_ref,
        survival_preconditions=inp.survival_preconditions,
        hard_block_reasons=hard_block_reasons,
        reason_codes=reason_codes,
        valid_until_epoch=valid_until,
        semantic_digest="",
    )
    return with_computed_directional_assessment_digest(assessment)


def evaluate_directional_assessment_v1(
    inp: DirectionalAssessmentInputV1,
    policy: DirectionalAssessmentPolicyV1,
) -> DirectionalAssessmentV1:
    """
    Deterministic Bull/Bear directional assessment evaluator.

    Fail-closed on untrusted, incomplete, or epoch-invalid inputs. Never mutates
    ``inp.scope_event_ref`` or upstream scope-event evidence.
    """
    policy_blocks = validate_directional_assessment_policy(
        policy, policy_version=inp.policy_version
    )
    if policy_blocks:
        return _finalize_assessment(
            inp,
            policy,
            status=DirectionalAssessmentStatus.BLOCKED,
            signal_strength=0.0,
            confidence=0.0,
            hard_block_reasons=_sorted_reason_values(policy_blocks),
            reason_codes=("policy_validation_failed",),
        )

    gate_blocks = _collect_input_gate_blocks(inp)
    if gate_blocks:
        status = (
            DirectionalAssessmentStatus.INVALID
            if any(
                r
                in {
                    DirectionalAssessmentHardBlockReason.INPUT_INCOMPLETE,
                    DirectionalAssessmentHardBlockReason.PRICE_PATH_TOO_SHORT,
                    DirectionalAssessmentHardBlockReason.REFERENCE_PRICE_NON_POSITIVE,
                    DirectionalAssessmentHardBlockReason.SCOPE_EVENT_REF_INVALID,
                }
                for r in gate_blocks
            )
            else DirectionalAssessmentStatus.BLOCKED
        )
        return _finalize_assessment(
            inp,
            policy,
            status=status,
            signal_strength=0.0,
            confidence=0.0,
            hard_block_reasons=_sorted_reason_values(gate_blocks),
            reason_codes=("input_gate_failed",),
        )

    epoch_mode, epoch_block = _resolve_epoch_semantics(
        trading_epoch=inp.trading_epoch,
        last_evaluated_trading_epoch=inp.confirmation_state.last_evaluated_trading_epoch,
        scope_event_epoch=inp.scope_event_ref.trading_epoch,
    )
    if epoch_block is not None:
        status = (
            DirectionalAssessmentStatus.INVALID
            if epoch_block is DirectionalAssessmentHardBlockReason.TRADING_EPOCH_OUT_OF_ORDER
            else DirectionalAssessmentStatus.BLOCKED
        )
        return _finalize_assessment(
            inp,
            policy,
            status=status,
            signal_strength=0.0,
            confidence=0.0,
            hard_block_reasons=(epoch_block.value,),
            reason_codes=("epoch_semantics_failed",),
        )

    signal_strength = compute_signal_strength(
        price_path=inp.price_path,
        side=inp.side,
        reference_price=inp.reference_price,
    )
    confidence = compute_directional_confidence(
        signal_strength, policy.confirmation_signal_threshold
    )

    status, reason_codes, _next_count = _status_for_signal(
        signal_strength=signal_strength,
        policy=policy,
        confirmation_state=inp.confirmation_state,
        epoch_mode=epoch_mode,
    )

    return _finalize_assessment(
        inp,
        policy,
        status=status,
        signal_strength=signal_strength,
        confidence=confidence,
        hard_block_reasons=(),
        reason_codes=reason_codes,
    )
