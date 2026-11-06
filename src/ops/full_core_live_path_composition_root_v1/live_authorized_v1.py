"""LIVE_AUTHORIZED standing authority contract. Offline. No POST.

LIVE_AUTHORIZED is a fail-closed live-execution authority predicate. True is
not automatic send, STEP-29Q eligibility, POST, or external effect.
SUBMISSION_AUTHORIZED, WIRE_SEND_PERMITTED, and LIVE_ARMED remain
independently insufficient.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_AUTHORIZED_DOES_NOT_IMPLY_EXTERNAL_EFFECT,
    LIVE_AUTHORIZED_DOES_NOT_IMPLY_POST,
    LIVE_AUTHORIZED_DOES_NOT_IMPLY_PRODUCTIVE_WIRE_SEND_REACHABLE,
    LIVE_AUTHORIZED_DOES_NOT_IMPLY_STEP_29Q,
    LIVE_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
    LIVE_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_SEND,
    LIVE_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_WIRE,
    LIVE_ENABLED,
    SUBMISSION_AUTHORIZED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)


@dataclass(frozen=True)
class LiveAuthorizedDecisionV1:
    live_authorized: bool
    fail_closed: bool
    reason_codes: Tuple[str, ...]
    standing_live_authorized: bool
    external_effect_authorized: bool
    step_29q_status: str
    post_count: int
    contract_implemented: bool


def evaluate_live_authorized_v1(
    *,
    standing_live_authorized: Optional[bool] = None,
    live_enabled: Optional[bool] = None,
    live_armed: Optional[bool] = None,
    wire_send_permitted: Optional[bool] = None,
    submission_authorized: Optional[bool] = None,
    attempt_external_effect: bool = False,
    attempt_post: bool = False,
    step_29q_status: str = STEP_29Q_PLAN_ONLY,
) -> LiveAuthorizedDecisionV1:
    standing = (
        LIVE_AUTHORIZED is True if standing_live_authorized is None else standing_live_authorized
    )
    enabled = LIVE_ENABLED is True if live_enabled is None else live_enabled is True
    armed = LIVE_ARMED is True if live_armed is None else live_armed is True
    send = (
        WIRE_SEND_PERMITTED is True if wire_send_permitted is None else wire_send_permitted is True
    )
    submitted = (
        SUBMISSION_AUTHORIZED is True
        if submission_authorized is None
        else submission_authorized is True
    )
    reasons: list[str] = []
    if standing is not True and standing is not False:
        reasons.append("LIVE_AUTHORIZED_STANDING_MALFORMED")
    elif standing is not True:
        reasons.append("LIVE_AUTHORIZED_STANDING_FALSE")
    if enabled is not True:
        reasons.append("LIVE_ENABLED_FALSE")
    if armed is not True:
        reasons.append("LIVE_ARMED_FALSE")
    if send is not True:
        reasons.append("WIRE_SEND_NOT_PERMITTED")
    if submitted is not True:
        reasons.append("SUBMISSION_AUTHORIZED_FALSE")
    if attempt_external_effect is True:
        reasons.append("EXTERNAL_EFFECT_FROM_LIVE_AUTHORIZED_FORBIDDEN")
    if attempt_post is True:
        reasons.append("POST_FROM_LIVE_AUTHORIZED_FORBIDDEN")
    unique = tuple(dict.fromkeys(reasons))
    authorized = not unique
    return LiveAuthorizedDecisionV1(
        live_authorized=authorized,
        fail_closed=not authorized,
        reason_codes=unique,
        standing_live_authorized=standing is True,
        external_effect_authorized=False,
        step_29q_status=STEP_29Q_PLAN_ONLY if not step_29q_status else str(step_29q_status),
        post_count=0,
        contract_implemented=LIVE_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED is True,
    )


def prove_live_authorized_not_external_effect_v1(
    decision: LiveAuthorizedDecisionV1,
) -> dict[str, bool]:
    return {
        "live_authorized": decision.live_authorized,
        "EXTERNAL_EFFECT_AUTHORIZED": EXTERNAL_EFFECT_AUTHORIZED,
        "LIVE_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_SEND": LIVE_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_SEND,
        "LIVE_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_WIRE": LIVE_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_WIRE,
        "LIVE_AUTHORIZED_DOES_NOT_IMPLY_EXTERNAL_EFFECT": (
            LIVE_AUTHORIZED_DOES_NOT_IMPLY_EXTERNAL_EFFECT
        ),
        "LIVE_AUTHORIZED_DOES_NOT_IMPLY_POST": LIVE_AUTHORIZED_DOES_NOT_IMPLY_POST,
        "LIVE_AUTHORIZED_DOES_NOT_IMPLY_STEP_29Q": LIVE_AUTHORIZED_DOES_NOT_IMPLY_STEP_29Q,
        "LIVE_AUTHORIZED_DOES_NOT_IMPLY_PRODUCTIVE_WIRE_SEND_REACHABLE": (
            LIVE_AUTHORIZED_DOES_NOT_IMPLY_PRODUCTIVE_WIRE_SEND_REACHABLE
        ),
        "ok": (
            decision.external_effect_authorized is False
            and decision.post_count == 0
            and EXTERNAL_EFFECT_AUTHORIZED is False
        ),
    }
