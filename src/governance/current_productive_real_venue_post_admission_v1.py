"""Real venue POST admission evaluator — fail-closed without actual-POST Owner-GO.

PRE-POST authority does not imply POST admission. Standing POST pins remain false.

RUNTIME_AUTHORIZATION_EFFECT=POST_ADMISSION_EVALUATION_ONLY
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
    POST_OWNER_GO,
    load_durable_post_owner_go_consume_v1,
)

POST_GO_STATUS: Final[str] = "UNCONSUMED"
POST_GO_CONSUMED: Final[bool] = False
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ExternalEffectPermitV1,
    permit_authorizes_one_shot_real_post_v1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)

ADMISSION_OWNER: Final[str] = "governance.current_productive_real_venue_post_admission_v1"
STATUS_POST_ADMISSION_DENIED: Final[str] = "REAL_VENUE_POST_ADMISSION_DENIED_FAIL_CLOSED"
STATUS_POST_ADMISSION_REQUIRES_OWNER_GO: Final[str] = (
    "REAL_VENUE_POST_ADMISSION_REQUIRES_ACTUAL_POST_OWNER_GO"
)
NEXT_OWNER_GO: Final[str] = POST_OWNER_GO
BLOCKER_CLASS: Final[str] = "NEW_OWNER_AUTHORITY_REQUIRED"


@dataclass(frozen=True, slots=True)
class RealVenuePostAdmissionResultV1:
    admission_status: str
    post_admission_granted: bool
    post_allowed: bool
    real_venue_post_allowed: bool
    real_venue_post_performed: bool
    one_shot_real_post_required: bool
    post_owner_go_required: bool
    post_go_status: str
    post_go_consumed: bool
    first_real_blocker: str
    blocker_class: str
    next_owner_go: str
    reason_codes: tuple[str, ...]


def evaluate_real_venue_post_admission_v1(
    *,
    post_owner_go: str | None,
    one_shot_real_post: bool,
    permit: ExternalEffectPermitV1 | None = None,
    store_root: Path | str | None = None,
) -> RealVenuePostAdmissionResultV1:
    """Evaluate whether a real venue POST may proceed. Always fail-closed here."""

    reasons: list[str] = []
    if POST_ALLOWED is True or REAL_VENUE_POST_ALLOWED is True:
        reasons.append("STANDING_POST_PINS_MUST_REMAIN_FALSE")
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        reasons.append("STANDING_EXTERNAL_EFFECT_MUST_REMAIN_FALSE")
    if str(STEP_29Q_PLAN_ONLY) != "PLAN_ONLY":
        reasons.append("STEP_29Q_MUST_REMAIN_PLAN_ONLY")
    if POST_GO_CONSUMED is True:
        reasons.append("POST_GO_ALREADY_CONSUMED")
    if POST_GO_STATUS != "UNCONSUMED":
        reasons.append("POST_GO_STATUS_NOT_UNCONSUMED")

    go = str(post_owner_go or "").strip()
    if go != POST_OWNER_GO:
        reasons.append("POST_OWNER_GO_REQUIRED")
    if one_shot_real_post is not True:
        reasons.append("ONE_SHOT_REAL_POST_FLAG_REQUIRED")

    if permit is not None and not permit_authorizes_one_shot_real_post_v1(permit):
        reasons.append("PERMIT_DOES_NOT_AUTHORIZE_ONE_SHOT_REAL_POST")

    if go == POST_OWNER_GO:
        if store_root is None:
            reasons.append("DURABLE_POST_OWNER_GO_STORE_REQUIRED")
        else:
            durable_go = load_durable_post_owner_go_consume_v1(store_root=store_root)
            if durable_go.get("consumed") is not True:
                reasons.append("POST_OWNER_GO_NOT_DURABLE_CONSUMED")
            elif str(durable_go.get("owner_go_token") or "") != POST_OWNER_GO:
                reasons.append("POST_OWNER_GO_DURABLE_TOKEN_MISMATCH")

    granted = not reasons
    status = STATUS_POST_ADMISSION_DENIED
    if "POST_OWNER_GO_REQUIRED" in reasons or go != POST_OWNER_GO:
        status = STATUS_POST_ADMISSION_REQUIRES_OWNER_GO

    return RealVenuePostAdmissionResultV1(
        admission_status=status,
        post_admission_granted=granted,
        post_allowed=False,
        real_venue_post_allowed=False,
        real_venue_post_performed=False,
        one_shot_real_post_required=True,
        post_owner_go_required=True,
        post_go_status=POST_GO_STATUS,
        post_go_consumed=POST_GO_CONSUMED is True,
        first_real_blocker=current_productive_first_real_blocker_v1(),
        blocker_class=BLOCKER_CLASS if not granted else "",
        next_owner_go=NEXT_OWNER_GO if not granted else "",
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


__all__ = [
    "ADMISSION_OWNER",
    "BLOCKER_CLASS",
    "NEXT_OWNER_GO",
    "RealVenuePostAdmissionResultV1",
    "evaluate_real_venue_post_admission_v1",
]
