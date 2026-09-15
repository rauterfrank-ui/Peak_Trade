"""Cap-7.2 CURRENT_PRODUCTIVE host-join to LiveExecutionPort. Offline. No wire.

HOST_JOINED means the productive Cap-7.2 host possesses the authorized
fail-closed LiveExecutionPort handle. It is not submission, LIVE_AUTHORIZED,
STEP-29Q, POST, execution_eligible, or wire send. SimulatedExecutionPort
remains the sole reachable no-order port.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    LiveExecutionPortV1,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CAP_7_2_HOST_JOINED_IS_NOT_EXECUTION_ELIGIBLE,
    CAP_7_2_HOST_JOINED_IS_NOT_LIVE_AUTHORIZED,
    CAP_7_2_HOST_JOINED_IS_NOT_POST,
    CAP_7_2_HOST_JOINED_IS_NOT_STEP_29Q,
    CAP_7_2_HOST_JOINED_IS_NOT_SUBMISSION_AUTHORIZED,
    CAP_7_2_HOST_JOINED_IS_NOT_WIRE_SEND,
    CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT,
    LIVE_EXECUTION_PORT_ROLE,
)
from src.ops.full_core_live_path_composition_root_v1.live_execution_port_construction_admission_v1 import (
    LiveExecutionPortConstructionAdmissionV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.host_binding_v1 import (
    HostActivationBindingV1,
    host_simulated_execution_port_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    SimulatedExecutionPortV1,
)


@dataclass(frozen=True)
class Cap72HostLiveExecutionPortJoinV1:
    host_joined: bool
    fail_closed: bool
    reason_codes: Tuple[str, ...]
    live_execution_port: Optional[LiveExecutionPortV1]
    simulated_port_retained: bool
    simulated_port_sole_reachable: bool
    submission_authorized: bool
    execution_eligible: bool
    wire_send_occurred: bool
    post_count: int
    side_effect_free: bool
    port_role: str
    host_join_standing: bool


def _port_no_external_effect(port: LiveExecutionPortV1) -> bool:
    return (
        getattr(port, "WIRE_SEND_OCCURRED", True) is False
        and int(getattr(port, "POST_COUNT", 1)) == 0
        and getattr(port, "MATERIAL_LOADED", False) is False
        and getattr(port, "EXTERNAL_EFFECT_AUTHORIZED", True) is False
    )


def join_cap72_host_to_live_execution_port_v1(
    *,
    host: HostActivationBindingV1,
    construction_admission: Optional[LiveExecutionPortConstructionAdmissionV1] = None,
    live_port: Optional[LiveExecutionPortV1] = None,
    attempt_submit: bool = False,
    attempt_wire_send: bool = False,
) -> Cap72HostLiveExecutionPortJoinV1:
    reasons: list[str] = []
    standing = CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT is True
    if standing is not True:
        reasons.append("CAP_7_2_HOST_JOIN_NOT_AUTHORIZED")
    if construction_admission is None or construction_admission.constructible is not True:
        reasons.append("CONSTRUCTION_ADMISSION_NOT_CONSTRUCTIBLE")
    if construction_admission is not None and (
        construction_admission.productive_resources_requested is True
    ):
        reasons.append("PRODUCTIVE_CONSTRUCTION_RESOURCES_FORBIDDEN")
    if attempt_submit is True:
        reasons.append("SUBMIT_FROM_HOST_JOIN_FORBIDDEN")
    if attempt_wire_send is True:
        reasons.append("WIRE_FROM_HOST_JOIN_FORBIDDEN")
    unique = tuple(dict.fromkeys(reasons))
    simulated = host_simulated_execution_port_v1(host)
    simulated_ok = (
        isinstance(simulated, SimulatedExecutionPortV1)
        and simulated.EXCHANGE_ORDER_SUBMIT_REACHABLE is False
        and simulated.EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False
        and host.execution_port is simulated
    )
    if unique or simulated_ok is not True:
        if simulated_ok is not True:
            unique = tuple(dict.fromkeys((*unique, "SIMULATED_PORT_NOT_RETAINED")))
        host.live_execution_port = None
        return Cap72HostLiveExecutionPortJoinV1(
            host_joined=False,
            fail_closed=True,
            reason_codes=unique,
            live_execution_port=None,
            simulated_port_retained=simulated_ok,
            simulated_port_sole_reachable=simulated_ok,
            submission_authorized=False,
            execution_eligible=False,
            wire_send_occurred=False,
            post_count=0,
            side_effect_free=True,
            port_role=LIVE_EXECUTION_PORT_ROLE,
            host_join_standing=standing,
        )
    port = live_port
    if port is None:
        try:
            port = construct_live_execution_port_v1(construction_admission=construction_admission)
        except ExecutionPortConstructionForbiddenError:
            host.live_execution_port = None
            return Cap72HostLiveExecutionPortJoinV1(
                host_joined=False,
                fail_closed=True,
                reason_codes=("LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN",),
                live_execution_port=None,
                simulated_port_retained=True,
                simulated_port_sole_reachable=True,
                submission_authorized=False,
                execution_eligible=False,
                wire_send_occurred=False,
                post_count=0,
                side_effect_free=True,
                port_role=LIVE_EXECUTION_PORT_ROLE,
                host_join_standing=standing,
            )
    if not isinstance(port, LiveExecutionPortV1) or _port_no_external_effect(port) is not True:
        host.live_execution_port = None
        return Cap72HostLiveExecutionPortJoinV1(
            host_joined=False,
            fail_closed=True,
            reason_codes=("LIVE_EXECUTION_PORT_EXTERNAL_EFFECT_PRESENT",),
            live_execution_port=None,
            simulated_port_retained=True,
            simulated_port_sole_reachable=True,
            submission_authorized=False,
            execution_eligible=False,
            wire_send_occurred=False,
            post_count=0,
            side_effect_free=True,
            port_role=LIVE_EXECUTION_PORT_ROLE,
            host_join_standing=standing,
        )
    host.live_execution_port = port
    pins_ok = (
        CAP_7_2_HOST_JOINED_IS_NOT_SUBMISSION_AUTHORIZED is True
        and CAP_7_2_HOST_JOINED_IS_NOT_WIRE_SEND is True
        and CAP_7_2_HOST_JOINED_IS_NOT_LIVE_AUTHORIZED is True
        and CAP_7_2_HOST_JOINED_IS_NOT_STEP_29Q is True
        and CAP_7_2_HOST_JOINED_IS_NOT_POST is True
        and CAP_7_2_HOST_JOINED_IS_NOT_EXECUTION_ELIGIBLE is True
        and host.execution_port is simulated
        and host.live_execution_port is port
        and host.live_execution_port is not host.execution_port
    )
    if pins_ok is not True:
        host.live_execution_port = None
        return Cap72HostLiveExecutionPortJoinV1(
            host_joined=False,
            fail_closed=True,
            reason_codes=("HOST_JOIN_OWNERSHIP_PIN_FAILED",),
            live_execution_port=None,
            simulated_port_retained=True,
            simulated_port_sole_reachable=True,
            submission_authorized=False,
            execution_eligible=False,
            wire_send_occurred=False,
            post_count=0,
            side_effect_free=True,
            port_role=LIVE_EXECUTION_PORT_ROLE,
            host_join_standing=standing,
        )
    return Cap72HostLiveExecutionPortJoinV1(
        host_joined=True,
        fail_closed=False,
        reason_codes=(),
        live_execution_port=port,
        simulated_port_retained=True,
        simulated_port_sole_reachable=True,
        submission_authorized=False,
        execution_eligible=False,
        wire_send_occurred=False,
        post_count=0,
        side_effect_free=True,
        port_role=LIVE_EXECUTION_PORT_ROLE,
        host_join_standing=standing,
    )
