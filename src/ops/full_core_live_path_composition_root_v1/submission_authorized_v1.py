"""SUBMISSION_AUTHORIZED standing admission contract. Offline. No wire.

SUBMISSION_AUTHORIZED is a fail-closed submission-capability predicate.
True admits only that one remainder after Cap-7.2 host-join. It is not
LIVE_AUTHORIZED, STEP-29Q, POST, or productive wire send. Host-join, the
LiveExecutionPort handle, and WIRE_SEND_PERMITTED remain independently
insufficient. STEP-29Q PLAN_ONLY cannot trigger submission.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    LiveExecutionPortV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_EXECUTION_PORT_ROLE,
    EXTERNAL_EFFECT_AUTHORIZED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    SUBMISSION_AUTHORIZED,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_LIVE_AUTHORIZED,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_POST,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_PRODUCTIVE_WIRE_SEND_REACHABLE,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_STEP_29Q,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_WIRE_SEND,
    SUBMISSION_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
    SUBMISSION_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_SEND,
    SUBMISSION_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_WIRE,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    DurableKillSwitchEvidenceStatusV1,
)

STEP_29Q_PLAN_ONLY = "PLAN_ONLY"
_TRUSTED_KS = DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
_UNKNOWN_KS = frozenset(
    {
        DurableKillSwitchEvidenceStatusV1.UNKNOWN_BLOCKED.value,
        DurableKillSwitchEvidenceStatusV1.MISSING.value,
        DurableKillSwitchEvidenceStatusV1.CONTRADICTORY.value,
        "",
        "UNKNOWN",
        "MALFORMED",
    }
)


@dataclass(frozen=True)
class SubmissionAuthorizedDecisionV1:
    submission_authorized: bool
    fail_closed: bool
    reason_codes: Tuple[str, ...]
    host_joined: bool
    live_port_present: bool
    standing_submission_authorized: bool
    live_authorized: bool
    step_29q_status: str
    productive_wire_send_reachable: bool
    post_count: int
    port_role: str
    contract_implemented: bool


def evaluate_submission_authorized_v1(
    *,
    host_joined: bool = False,
    live_port: Optional[LiveExecutionPortV1] = None,
    admitted: bool = False,
    live_enabled: Optional[bool] = None,
    live_armed: Optional[bool] = None,
    wire_send_permitted: Optional[bool] = None,
    standing_submission_authorized: Optional[bool] = None,
    durable_kill_switch_blocked: Optional[bool] = False,
    durable_kill_switch_evidence_status: str = DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value,
    attempt_wire_send: bool = False,
    attempt_submit: bool = False,
    live_authorized: Optional[bool] = None,
    step_29q_status: str = STEP_29Q_PLAN_ONLY,
) -> SubmissionAuthorizedDecisionV1:
    enabled = LIVE_ENABLED is True if live_enabled is None else live_enabled is True
    armed = LIVE_ARMED is True if live_armed is None else live_armed is True
    send = (
        WIRE_SEND_PERMITTED is True if wire_send_permitted is None else wire_send_permitted is True
    )
    standing = (
        SUBMISSION_AUTHORIZED is True
        if standing_submission_authorized is None
        else standing_submission_authorized
    )
    reasons: list[str] = []
    if standing is not True and standing is not False:
        reasons.append("SUBMISSION_AUTHORIZED_STANDING_MALFORMED")
    elif standing is not True:
        reasons.append("SUBMISSION_AUTHORIZED_STANDING_FALSE")
    if host_joined is not True:
        reasons.append("HOST_NOT_JOINED")
    if live_port is None:
        reasons.append("LIVE_PORT_MISSING")
    elif not isinstance(live_port, LiveExecutionPortV1):
        reasons.append("LIVE_PORT_MALFORMED")
    else:
        if getattr(live_port, "WIRE_SEND_OCCURRED", True) is not False:
            reasons.append("LIVE_EXECUTION_PORT_WIRE_SIDE_EFFECT")
        if int(getattr(live_port, "POST_COUNT", 1)) != 0:
            reasons.append("LIVE_EXECUTION_PORT_POST_COUNT_NOT_ZERO")
        if getattr(live_port, "MATERIAL_LOADED", False) is True:
            reasons.append("LIVE_EXECUTION_PORT_CREDENTIAL_MATERIAL_LOADED")
        if getattr(live_port, "EXTERNAL_EFFECT_AUTHORIZED", False) is True:
            reasons.append("LIVE_EXECUTION_PORT_EXTERNAL_EFFECT_AUTHORIZED")
    if admitted is not True:
        reasons.append("EXECUTION_ADMISSION_NOT_ADMITTED")
    if enabled is not True:
        reasons.append("LIVE_ENABLED_FALSE")
    if armed is not True:
        reasons.append("LIVE_ARMED_FALSE")
    if send is not True:
        reasons.append("WIRE_SEND_NOT_PERMITTED")
    ks_status = str(durable_kill_switch_evidence_status or "").strip()
    if ks_status in _UNKNOWN_KS or ks_status != _TRUSTED_KS:
        reasons.append("KILL_SWITCH_EVIDENCE_NOT_TRUSTED")
    if durable_kill_switch_blocked is True:
        reasons.append("KILL_SWITCH_BLOCKED")
    elif durable_kill_switch_blocked is None:
        reasons.append("KILL_SWITCH_UNKNOWN")
    if live_authorized is not None and live_authorized is not True and live_authorized is not False:
        reasons.append("LIVE_AUTHORIZED_MALFORMED")
    if attempt_wire_send is True:
        reasons.append("WIRE_FROM_SUBMISSION_FORBIDDEN")
    if attempt_submit is True:
        reasons.append("SUBMIT_FROM_SUBMISSION_CAPABILITY_FORBIDDEN")
    unique = tuple(dict.fromkeys(reasons))
    authorized = not unique
    return SubmissionAuthorizedDecisionV1(
        submission_authorized=authorized,
        fail_closed=not authorized,
        reason_codes=unique,
        host_joined=host_joined is True,
        live_port_present=isinstance(live_port, LiveExecutionPortV1),
        standing_submission_authorized=standing is True,
        live_authorized=False,
        step_29q_status=STEP_29Q_PLAN_ONLY if not step_29q_status else str(step_29q_status),
        productive_wire_send_reachable=PRODUCTIVE_WIRE_SEND_REACHABLE is True,
        post_count=0,
        port_role=LIVE_EXECUTION_PORT_ROLE,
        contract_implemented=SUBMISSION_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED is True,
    )


def prove_submission_authorized_not_wire_v1(
    decision: SubmissionAuthorizedDecisionV1,
) -> dict[str, bool]:
    return {
        "submission_authorized": decision.submission_authorized,
        "PRODUCTIVE_WIRE_SEND_REACHABLE": PRODUCTIVE_WIRE_SEND_REACHABLE,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "SUBMISSION_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_SEND": (
            SUBMISSION_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_SEND
        ),
        "SUBMISSION_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_WIRE": (
            SUBMISSION_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_WIRE
        ),
        "SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_WIRE_SEND": (
            SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_WIRE_SEND
        ),
        "SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_LIVE_AUTHORIZED": (
            SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_LIVE_AUTHORIZED
        ),
        "SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_STEP_29Q": (
            SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_STEP_29Q
        ),
        "SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_POST": SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_POST,
        "SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_PRODUCTIVE_WIRE_SEND_REACHABLE": (
            SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_PRODUCTIVE_WIRE_SEND_REACHABLE
        ),
        "ok": (
            decision.post_count == 0
            and decision.live_authorized is False
            and EXTERNAL_EFFECT_AUTHORIZED is False
        ),
    }
