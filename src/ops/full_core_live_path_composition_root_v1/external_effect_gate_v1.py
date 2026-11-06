"""Fail-closed Full-Core external-effect gate. Offline. No POST.

EXTERNAL_EFFECT_AUTHORIZED is independent of LIVE_AUTHORIZED,
SUBMISSION_AUTHORIZED, WIRE_SEND_PERMITTED, and PRODUCTIVE_WIRE_SEND_REACHABLE.
True would be required for an actual venue mutation. This persist keeps it
false. The send-capable adapter may exist up to this seam.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Tuple

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    EXTERNAL_EFFECT_FALSE_REMAINS_FAIL_CLOSED,
    EXTERNAL_EFFECT_GATE_IMPLEMENTED,
    LIVE_AUTHORIZED,
    LIVE_AUTHORIZED_DOES_NOT_IMPLY_EXTERNAL_EFFECT,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    PRODUCTIVE_WIRE_SEND_REACHABLE_DOES_NOT_IMPLY_EXTERNAL_EFFECT,
    SUBMISSION_AUTHORIZED,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_POST,
    WIRE_SEND_PERMITTED,
)

TRADE_ORDER_PATH = "/api/v5/trade/order"


class FullCoreExternalEffectNotAuthorizedError(RuntimeError):
    """Raised when an actual venue mutation would be required."""


@dataclass(frozen=True)
class ExternalEffectDecisionV1:
    external_effect_authorized: bool
    fail_closed: bool
    reason_codes: Tuple[str, ...]
    post_count: int
    wire_send_occurred: bool
    venue_mutation_performed: bool
    actual_order_submit_performed: bool
    contract_implemented: bool


def evaluate_external_effect_v1(
    *,
    attempt_external_effect: bool = False,
    attempt_post: bool = False,
    standing_external_effect_authorized: Optional[bool] = None,
    live_authorized: Optional[bool] = None,
    submission_authorized: Optional[bool] = None,
    wire_send_permitted: Optional[bool] = None,
    productive_wire_send_reachable: Optional[bool] = None,
) -> ExternalEffectDecisionV1:
    standing = (
        EXTERNAL_EFFECT_AUTHORIZED is True
        if standing_external_effect_authorized is None
        else standing_external_effect_authorized
    )
    reasons: list[str] = []
    if standing is not True and standing is not False:
        reasons.append("EXTERNAL_EFFECT_STANDING_MALFORMED")
    elif standing is not True:
        reasons.append("EXTERNAL_EFFECT_NOT_AUTHORIZED")
    if live_authorized is True and LIVE_AUTHORIZED_DOES_NOT_IMPLY_EXTERNAL_EFFECT is not True:
        reasons.append("LIVE_AUTHORIZED_MUST_NOT_IMPLY_EXTERNAL_EFFECT")
    if (
        productive_wire_send_reachable is True
        and PRODUCTIVE_WIRE_SEND_REACHABLE_DOES_NOT_IMPLY_EXTERNAL_EFFECT is not True
    ):
        reasons.append("REACHABLE_MUST_NOT_IMPLY_EXTERNAL_EFFECT")
    if submission_authorized is True and SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_POST is not True:
        reasons.append("SUBMISSION_MUST_NOT_IMPLY_POST")
    if attempt_external_effect is True:
        reasons.append("EXTERNAL_EFFECT_ATTEMPT_FORBIDDEN")
    if attempt_post is True:
        reasons.append("POST_FROM_EXTERNAL_EFFECT_GATE_FORBIDDEN")
    unique = tuple(dict.fromkeys(reasons))
    authorized = not unique and standing is True
    return ExternalEffectDecisionV1(
        external_effect_authorized=authorized,
        fail_closed=not authorized,
        reason_codes=unique,
        post_count=0,
        wire_send_occurred=False,
        venue_mutation_performed=False,
        actual_order_submit_performed=False,
        contract_implemented=EXTERNAL_EFFECT_GATE_IMPLEMENTED is True,
    )


def refuse_external_effect_v1(*, reason: str = "EXTERNAL_EFFECT_NOT_AUTHORIZED") -> None:
    _ = (
        LIVE_AUTHORIZED,
        SUBMISSION_AUTHORIZED,
        WIRE_SEND_PERMITTED,
        PRODUCTIVE_WIRE_SEND_REACHABLE,
        EXTERNAL_EFFECT_FALSE_REMAINS_FAIL_CLOSED,
        TRADE_ORDER_PATH,
    )
    raise FullCoreExternalEffectNotAuthorizedError(reason)


def invoke_external_effect_v1(
    *,
    payload: Any = None,
    attempt_post: bool = True,
) -> ExternalEffectDecisionV1:
    del payload
    decision = evaluate_external_effect_v1(
        attempt_external_effect=True,
        attempt_post=attempt_post is True,
    )
    refuse_external_effect_v1()
    return decision
