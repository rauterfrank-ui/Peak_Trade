"""Network-session entry boundary (dry / no-effect) for §11.12.8 activation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.network_session_go_v1 import (
    bind_ephemeral_network_session_go_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.constants_v1 import (
    LIVE_ORDER_EFFECT,
    NETWORK_EFFECT,
    NETWORK_SESSION_STARTED,
    ORDER_EFFECT,
    SECTION_11_13_STARTED,
)
from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.run_consumer_v1 import (
    Section11128RunConsumerError,
    refuse_cap_11_13_v1,
    refuse_live_path_v1,
    refuse_network_session_v1,
    refuse_order_submit_v1,
)


class Section11128NetworkBoundaryError(RuntimeError):
    """Fail-closed network-session boundary violation."""


@dataclass(frozen=True)
class NetworkSessionEntryBoundaryV1:
    boundary_reached: bool
    network_session_started: bool
    network_effect: str
    order_effect: str
    live_order_effect: str
    network_session_go_default_false: bool
    live_path_hard_blocked: bool
    section_11_13_unreachable: bool
    order_submit_refused: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_reached": self.boundary_reached,
            "network_session_started": self.network_session_started,
            "network_effect": self.network_effect,
            "order_effect": self.order_effect,
            "live_order_effect": self.live_order_effect,
            "network_session_go_default_false": self.network_session_go_default_false,
            "live_path_hard_blocked": self.live_path_hard_blocked,
            "section_11_13_unreachable": self.section_11_13_unreachable,
            "order_submit_refused": self.order_submit_refused,
        }


def reach_network_session_entry_boundary_dry_v1(
    *,
    allow_network_start: bool = False,
) -> NetworkSessionEntryBoundaryV1:
    """Reach the canonical network-session entry boundary without side effects."""
    if allow_network_start:
        raise Section11128NetworkBoundaryError("NETWORK_START_FORBIDDEN_IN_DRY_ACTIVATION")

    go = bind_ephemeral_network_session_go_v1(network_session_go=False)
    if go.get("ok") is not True or go.get("network_session_go") is not False:
        raise Section11128NetworkBoundaryError("NETWORK_SESSION_GO_MUST_REMAIN_FALSE")
    if NETWORK_SESSION_STARTED is not False:
        raise Section11128NetworkBoundaryError("NETWORK_SESSION_STARTED_CONSTANT_DRIFT")
    if NETWORK_EFFECT != "NONE" or ORDER_EFFECT != "NONE" or LIVE_ORDER_EFFECT != "NONE":
        raise Section11128NetworkBoundaryError("EFFECT_CONSTANTS_DRIFT")
    if SECTION_11_13_STARTED is not False:
        raise Section11128NetworkBoundaryError("SECTION_11_13_STARTED_DRIFT")

    live_blocked = False
    try:
        refuse_live_path_v1()
    except Section11128RunConsumerError as exc:
        live_blocked = "LIVE_PATH_FORBIDDEN" in str(exc)

    section_unreachable = False
    try:
        refuse_cap_11_13_v1()
    except Section11128RunConsumerError as exc:
        section_unreachable = "CAPABILITY_11_13_FORBIDDEN" in str(exc)

    order_refused = False
    try:
        refuse_order_submit_v1()
    except Section11128RunConsumerError as exc:
        order_refused = "ORDER_SUBMIT_FORBIDDEN" in str(exc)

    # Boundary reach: invoke the refuse surface that guards network session start.
    boundary_guarded = False
    try:
        refuse_network_session_v1(session_id="dry-boundary")
    except Section11128RunConsumerError as exc:
        boundary_guarded = "NETWORK_SESSION_FORBIDDEN" in str(exc)
    if not boundary_guarded:
        raise Section11128NetworkBoundaryError("NETWORK_SESSION_BOUNDARY_GUARD_BROKEN")
    if not live_blocked:
        raise Section11128NetworkBoundaryError("LIVE_PATH_HARD_BLOCK_BROKEN")
    if not section_unreachable:
        raise Section11128NetworkBoundaryError("SECTION_11_13_ISOLATION_BROKEN")
    if not order_refused:
        raise Section11128NetworkBoundaryError("ORDER_SUBMIT_REFUSAL_BROKEN")

    return NetworkSessionEntryBoundaryV1(
        boundary_reached=True,
        network_session_started=False,
        network_effect="NONE",
        order_effect="NONE",
        live_order_effect="NONE",
        network_session_go_default_false=True,
        live_path_hard_blocked=True,
        section_11_13_unreachable=True,
        order_submit_refused=True,
    )
