"""LiveExecutionPort construction-admission contract. Offline. No credentials.

Evaluates whether construction is admissible as an explicit conjunction.
Construction is not LIVE_AUTHORIZED, STEP-29Q, POST, or wire send.
This module never opens a session, never looks up secrets, and never sends wire.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_EXECUTION_PORT_CONSTRUCTIBLE,
    LIVE_EXECUTION_PORT_CONSTRUCTION_ADMISSION_CONTRACT_IMPLEMENTED,
    LIVE_EXECUTION_PORT_ROLE,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ExecutionAdmissionDecisionV1,
)

CAP_11_1_CONSTRUCTION_FORBIDDEN_REASON = (
    "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_1"
)


@dataclass(frozen=True)
class LiveExecutionPortConstructionAdmissionV1:
    constructible: bool
    constructed: bool
    fail_closed: bool
    reason_codes: Tuple[str, ...]
    standing_live_enabled: bool
    standing_live_armed: bool
    standing_wire_send_permitted: bool
    execution_admitted: bool
    cap_11_1_construction_forbidden: bool
    productive_resources_requested: bool
    contract_implemented: bool
    port_role: str


def evaluate_live_execution_port_construction_admission_v1(
    *,
    admission: Optional[ExecutionAdmissionDecisionV1] = None,
    live_enabled: Optional[bool] = None,
    live_armed: Optional[bool] = None,
    wire_send_permitted: Optional[bool] = None,
    attempt_with_credentials: bool = False,
    attempt_network_session: bool = False,
) -> LiveExecutionPortConstructionAdmissionV1:
    enabled = LIVE_ENABLED is True if live_enabled is None else live_enabled is True
    armed = LIVE_ARMED is True if live_armed is None else live_armed is True
    send = (
        WIRE_SEND_PERMITTED is True if wire_send_permitted is None else wire_send_permitted is True
    )
    admitted = admission is not None and admission.admitted is True
    reasons: list[str] = []
    productive_requested = attempt_with_credentials is True or attempt_network_session is True
    if productive_requested:
        reasons.append("PRODUCTIVE_CONSTRUCTION_RESOURCES_FORBIDDEN")
    if enabled is not True:
        reasons.append("LIVE_ENABLED_FALSE")
    if armed is not True:
        reasons.append("LIVE_ARMED_FALSE")
    if send is not True:
        reasons.append("WIRE_SEND_NOT_PERMITTED")
    if admitted is not True:
        reasons.append("EXECUTION_ADMISSION_NOT_ADMITTED")
    unique = tuple(dict.fromkeys(reasons))
    constructible = not unique
    return LiveExecutionPortConstructionAdmissionV1(
        constructible=constructible,
        constructed=False,
        fail_closed=not constructible,
        reason_codes=unique,
        standing_live_enabled=enabled,
        standing_live_armed=armed,
        standing_wire_send_permitted=send,
        execution_admitted=admitted,
        cap_11_1_construction_forbidden=False,
        productive_resources_requested=productive_requested,
        contract_implemented=LIVE_EXECUTION_PORT_CONSTRUCTION_ADMISSION_CONTRACT_IMPLEMENTED,
        port_role=LIVE_EXECUTION_PORT_ROLE,
    )


def prove_live_execution_port_not_constructible_v1() -> dict[str, bool]:
    decision = evaluate_live_execution_port_construction_admission_v1()
    return {
        "constructible": decision.constructible,
        "constructed": decision.constructed,
        "LIVE_EXECUTION_PORT_CONSTRUCTIBLE": LIVE_EXECUTION_PORT_CONSTRUCTIBLE,
        "cap_11_1_construction_forbidden": decision.cap_11_1_construction_forbidden,
        "ok": (
            decision.constructible is False
            and decision.constructed is False
            and "EXECUTION_ADMISSION_NOT_ADMITTED" in decision.reason_codes
        ),
    }


def prove_live_execution_port_constructible_when_admitted_v1(
    *,
    admission: ExecutionAdmissionDecisionV1,
) -> dict[str, bool]:
    decision = evaluate_live_execution_port_construction_admission_v1(
        admission=admission,
        live_enabled=True,
        live_armed=True,
        wire_send_permitted=True,
        attempt_with_credentials=False,
        attempt_network_session=False,
    )
    return {
        "constructible": decision.constructible,
        "constructed": decision.constructed,
        "LIVE_EXECUTION_PORT_CONSTRUCTIBLE": LIVE_EXECUTION_PORT_CONSTRUCTIBLE,
        "cap_11_1_construction_forbidden": decision.cap_11_1_construction_forbidden,
        "ok": (
            admission.admitted is True
            and decision.constructible is True
            and decision.constructed is False
            and decision.cap_11_1_construction_forbidden is False
            and not decision.reason_codes
            and LIVE_EXECUTION_PORT_CONSTRUCTIBLE is True
        ),
    }
