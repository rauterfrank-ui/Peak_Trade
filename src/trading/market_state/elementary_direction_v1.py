"""Elementary direction identity from consecutive C1 mark prices.

PURE_DOMAIN_COMPONENT=true
DETERMINISTIC=true
NO_IO=true
NO_GLOBAL_STATE=true
NO_SIDE_EFFECTS=true
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
ORDER_EFFECT=NONE

Identity only: previous DISTINCT accepted C1 mark vs current bound markPx
→ BULL | BEAR | NEUTRAL.

Does not own state. Does not decide entry, quantity, risk, intent, venue, or POST.
Does not consume trailing_anchor, candle closes, volatility history, C3, Survival,
or Suitability. Does not encode numeric +1/-1 units.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
)
from trading.market_state.observation_identity_v1 import (
    InstrumentObservationKeyV1,
    ObservationIdentityV1,
    is_finite_number,
)

ELEMENTARY_DIRECTION_COMPONENT = "ElementaryDirectionV1"
ELEMENTARY_DIRECTION_PURITY = "PURE_DETERMINISTIC_NO_IO"
ELEMENTARY_DIRECTION_VERSION = "v1"
AUTHORITY_EFFECT_NONE = "NONE"
RUNTIME_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"


class ElementaryDirectionV1(str, Enum):
    """Unsigned elementary movement identity. Not LONG/SHORT and not +1/-1."""

    BULL = "bull"
    BEAR = "bear"
    NEUTRAL = "neutral"


class ElementaryDirectionStatusV1(str, Enum):
    EVALUATED = "evaluated"
    REJECTED = "rejected"


class ElementaryDirectionReasonCodeV1(str, Enum):
    FIRST_OBSERVATION = "first_observation"
    MARK_UNCHANGED = "mark_unchanged"
    MARK_INCREASED = "mark_increased"
    MARK_DECREASED = "mark_decreased"
    INVALID_CURRENT_MARK_MISSING = "invalid_current_mark_missing"
    INVALID_CURRENT_MARK_NON_FINITE = "invalid_current_mark_non_finite"
    INVALID_CURRENT_MARK_NON_POSITIVE = "invalid_current_mark_non_positive"
    INVALID_PREVIOUS_MARK_NON_FINITE = "invalid_previous_mark_non_finite"
    INVALID_PREVIOUS_MARK_NON_POSITIVE = "invalid_previous_mark_non_positive"
    INSTRUMENT_MISMATCH = "instrument_mismatch"
    CURRENT_MARK_PROVENANCE_MISMATCH = "current_mark_provenance_mismatch"
    CURRENT_IDENTITY_MISSING = "current_identity_missing"
    C1_NOT_COMPARABLE = "c1_not_comparable"


@dataclass(frozen=True)
class ElementaryDirectionResultV1:
    status: ElementaryDirectionStatusV1
    direction: Optional[ElementaryDirectionV1]
    previous_mark: Optional[float]
    current_mark: Optional[float]
    reason_code: str
    authority_effect: str = AUTHORITY_EFFECT_NONE
    runtime_effect: str = RUNTIME_EFFECT_NONE
    order_effect: str = ORDER_EFFECT_NONE

    def __post_init__(self) -> None:
        if self.status is ElementaryDirectionStatusV1.EVALUATED and self.direction is None:
            raise ValueError("EVALUATED_DIRECTION_MISSING")
        if self.status is ElementaryDirectionStatusV1.REJECTED and self.direction is not None:
            raise ValueError("REJECTED_DIRECTION_MUST_BE_ABSENT")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("AUTHORITY_EFFECT_MUST_BE_NONE")
        if self.runtime_effect != RUNTIME_EFFECT_NONE:
            raise ValueError("RUNTIME_EFFECT_MUST_BE_NONE")
        if self.order_effect != ORDER_EFFECT_NONE:
            raise ValueError("ORDER_EFFECT_MUST_BE_NONE")


def _current_mark_invalid_reason(value: object) -> Optional[ElementaryDirectionReasonCodeV1]:
    # Reuse C1 mark conventions: present, finite, strictly positive; bools rejected.
    if value is None:
        return ElementaryDirectionReasonCodeV1.INVALID_CURRENT_MARK_MISSING
    if not is_finite_number(value):
        return ElementaryDirectionReasonCodeV1.INVALID_CURRENT_MARK_NON_FINITE
    if float(value) <= 0.0:
        return ElementaryDirectionReasonCodeV1.INVALID_CURRENT_MARK_NON_POSITIVE
    return None


def _previous_mark_invalid_reason(value: object) -> Optional[ElementaryDirectionReasonCodeV1]:
    if not is_finite_number(value):
        return ElementaryDirectionReasonCodeV1.INVALID_PREVIOUS_MARK_NON_FINITE
    if float(value) <= 0.0:
        return ElementaryDirectionReasonCodeV1.INVALID_PREVIOUS_MARK_NON_POSITIVE
    return None


def _rejected(
    *,
    reason: ElementaryDirectionReasonCodeV1,
    previous_mark: Optional[float] = None,
    current_mark: Optional[float] = None,
    reason_code: Optional[str] = None,
) -> ElementaryDirectionResultV1:
    return ElementaryDirectionResultV1(
        status=ElementaryDirectionStatusV1.REJECTED,
        direction=None,
        previous_mark=previous_mark,
        current_mark=current_mark,
        reason_code=reason_code if reason_code is not None else reason.value,
    )


def _evaluated(
    *,
    direction: ElementaryDirectionV1,
    reason: ElementaryDirectionReasonCodeV1,
    previous_mark: Optional[float],
    current_mark: float,
) -> ElementaryDirectionResultV1:
    return ElementaryDirectionResultV1(
        status=ElementaryDirectionStatusV1.EVALUATED,
        direction=direction,
        previous_mark=previous_mark,
        current_mark=current_mark,
        reason_code=reason.value,
    )


def evaluate_elementary_direction_v1(
    *,
    previous_mark: Optional[object],
    current_mark: object,
) -> ElementaryDirectionResultV1:
    """Pure signum over previous accepted mark vs current mark.

    None previous → NEUTRAL.
    current > previous → BULL.
    current < previous → BEAR.
    current == previous → NEUTRAL.
    Invalid numerics are rejected; they are not normalized to NEUTRAL.
    """
    current_reason = _current_mark_invalid_reason(current_mark)
    if current_reason is not None:
        return _rejected(reason=current_reason)

    resolved_current = float(current_mark)  # type: ignore[arg-type]

    if previous_mark is None:
        return _evaluated(
            direction=ElementaryDirectionV1.NEUTRAL,
            reason=ElementaryDirectionReasonCodeV1.FIRST_OBSERVATION,
            previous_mark=None,
            current_mark=resolved_current,
        )

    previous_reason = _previous_mark_invalid_reason(previous_mark)
    if previous_reason is not None:
        return _rejected(reason=previous_reason, current_mark=resolved_current)

    resolved_previous = float(previous_mark)  # type: ignore[arg-type]
    if resolved_current > resolved_previous:
        return _evaluated(
            direction=ElementaryDirectionV1.BULL,
            reason=ElementaryDirectionReasonCodeV1.MARK_INCREASED,
            previous_mark=resolved_previous,
            current_mark=resolved_current,
        )
    if resolved_current < resolved_previous:
        return _evaluated(
            direction=ElementaryDirectionV1.BEAR,
            reason=ElementaryDirectionReasonCodeV1.MARK_DECREASED,
            previous_mark=resolved_previous,
            current_mark=resolved_current,
        )
    return _evaluated(
        direction=ElementaryDirectionV1.NEUTRAL,
        reason=ElementaryDirectionReasonCodeV1.MARK_UNCHANGED,
        previous_mark=resolved_previous,
        current_mark=resolved_current,
    )


def _identity_key(identity: ObservationIdentityV1) -> InstrumentObservationKeyV1:
    return identity.instrument_key()


def evaluate_elementary_direction_from_observation_acceptance_v1(
    result: ObservationAcceptanceResultV1,
    *,
    bound_instrument_key: InstrumentObservationKeyV1,
    current_mark: object,
) -> ElementaryDirectionResultV1:
    """Join helper: previous from C1 state_before, current from this cycle/C1 candidate.

    Does not read state_after, trailing anchors, candle closes, or mark history.
    Instrument mismatch and C1 fail-closed classifications reject; they do not
    silently become NEUTRAL.
    """
    previous_identity = result.state_before.last_accepted_observation_identity
    current_identity = result.observation_identity

    if previous_identity is not None and _identity_key(previous_identity) != bound_instrument_key:
        return _rejected(reason=ElementaryDirectionReasonCodeV1.INSTRUMENT_MISMATCH)
    if current_identity is not None and _identity_key(current_identity) != bound_instrument_key:
        return _rejected(reason=ElementaryDirectionReasonCodeV1.INSTRUMENT_MISMATCH)
    if (
        previous_identity is not None
        and current_identity is not None
        and _identity_key(previous_identity) != _identity_key(current_identity)
    ):
        return _rejected(reason=ElementaryDirectionReasonCodeV1.INSTRUMENT_MISMATCH)

    if result.fail_closed:
        return _rejected(
            reason=ElementaryDirectionReasonCodeV1.C1_NOT_COMPARABLE,
            reason_code=(
                f"{ElementaryDirectionReasonCodeV1.C1_NOT_COMPARABLE.value}:"
                f"{result.classification.value}"
            ),
        )

    if current_identity is None:
        return _rejected(reason=ElementaryDirectionReasonCodeV1.CURRENT_IDENTITY_MISSING)

    identity_mark_reason = _current_mark_invalid_reason(current_identity.mark_price)
    if identity_mark_reason is not None:
        return _rejected(reason=identity_mark_reason)

    provided_mark_reason = _current_mark_invalid_reason(current_mark)
    if provided_mark_reason is not None:
        return _rejected(reason=provided_mark_reason)

    if float(current_identity.mark_price) != float(current_mark):  # type: ignore[arg-type]
        return _rejected(
            reason=ElementaryDirectionReasonCodeV1.CURRENT_MARK_PROVENANCE_MISMATCH,
            previous_mark=(
                None if previous_identity is None else float(previous_identity.mark_price)
            ),
            current_mark=float(current_identity.mark_price),
        )

    previous_mark: Optional[float]
    if previous_identity is None:
        previous_mark = None
    else:
        previous_reason = _previous_mark_invalid_reason(previous_identity.mark_price)
        if previous_reason is not None:
            return _rejected(
                reason=previous_reason,
                current_mark=float(current_identity.mark_price),
            )
        previous_mark = float(previous_identity.mark_price)

    return evaluate_elementary_direction_v1(
        previous_mark=previous_mark,
        current_mark=float(current_identity.mark_price),
    )


__all__ = [
    "AUTHORITY_EFFECT_NONE",
    "ELEMENTARY_DIRECTION_COMPONENT",
    "ELEMENTARY_DIRECTION_PURITY",
    "ELEMENTARY_DIRECTION_VERSION",
    "ORDER_EFFECT_NONE",
    "RUNTIME_EFFECT_NONE",
    "ElementaryDirectionReasonCodeV1",
    "ElementaryDirectionResultV1",
    "ElementaryDirectionStatusV1",
    "ElementaryDirectionV1",
    "evaluate_elementary_direction_from_observation_acceptance_v1",
    "evaluate_elementary_direction_v1",
]
