"""LiveExecutionPort construction-admission contract. Offline. No credentials.

Evaluates whether construction would be admissible as an explicit conjunction.
Cap 11.1 still forbids construction. This module never constructs a port, never
opens a session, never looks up secrets, and never sends wire.

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
    reasons.append(CAP_11_1_CONSTRUCTION_FORBIDDEN_REASON)
    unique = tuple(dict.fromkeys(reasons))
    return LiveExecutionPortConstructionAdmissionV1(
        constructible=False,
        constructed=False,
        fail_closed=True,
        reason_codes=unique,
        standing_live_enabled=enabled,
        standing_live_armed=armed,
        standing_wire_send_permitted=send,
        execution_admitted=admitted,
        cap_11_1_construction_forbidden=True,
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
            and LIVE_EXECUTION_PORT_CONSTRUCTIBLE is False
            and CAP_11_1_CONSTRUCTION_FORBIDDEN_REASON in decision.reason_codes
        ),
    }
