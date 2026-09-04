"""Offline Live execution boundary: always HARD STOP BEFORE WIRE.

Does not construct Cap 11.1 LiveExecutionPort. Does not invoke canary HTTP.
"""

from __future__ import annotations

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_EXECUTION_PORT_ROLE,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import (
    CompositionStatusV1,
    ExecutionBoundaryResultV1,
    PretradeConjunctionResultV1,
    VenuePlanCandidateV1,
)


def refuse_wire_send_v1() -> None:
    raise RuntimeError("WIRE_SEND_FORBIDDEN_IN_OFFLINE_FULL_CORE_PATH")


def halt_at_live_execution_boundary_v1(
    *,
    plan: VenuePlanCandidateV1,
    pretrade: PretradeConjunctionResultV1,
    attempt_wire_send: bool = False,
    attempt_construct_live_port: bool = False,
) -> ExecutionBoundaryResultV1:
    reasons: list[str] = [
        "HARD_STOP_BEFORE_WIRE",
        f"LIVE_EXECUTION_PORT_ROLE={LIVE_EXECUTION_PORT_ROLE}",
    ]
    live_port_constructed = False
    if attempt_construct_live_port:
        try:
            construct_live_execution_port_v1()
        except ExecutionPortConstructionForbiddenError:
            reasons.append("LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN")
        else:
            live_port_constructed = True
            reasons.append("LIVE_EXECUTION_PORT_CONSTRUCTED_UNEXPECTED")
    if attempt_wire_send:
        try:
            refuse_wire_send_v1()
        except RuntimeError as exc:
            reasons.append(str(exc))
    if LIVE_ENABLED is not True:
        reasons.append("EXECUTION_DISABLED")
    if LIVE_ARMED is not True:
        reasons.append("EXECUTION_UNARMED")
    if WIRE_SEND_PERMITTED is not True:
        reasons.append("WIRE_SEND_NOT_PERMITTED")
    if not pretrade.owner_go_valid:
        reasons.append("MISSING_OWNER_GO")
    if not pretrade.pretrade_valid:
        reasons.append("PRETRADE_FAIL")
    _ = plan
    wire_send_occurred = False
    halt = (
        live_port_constructed is False
        and wire_send_occurred is False
        and LIVE_ENABLED is False
        and WIRE_SEND_PERMITTED is False
    )
    status = CompositionStatusV1.HALT if halt else CompositionStatusV1.DENY
    return ExecutionBoundaryResultV1(
        status=status,
        reason_codes=tuple(reasons),
        wire_send_occurred=wire_send_occurred,
        live_execution_port_constructed=live_port_constructed,
        canary_http_invoked=False,
        halt_before_wire=halt,
    )
