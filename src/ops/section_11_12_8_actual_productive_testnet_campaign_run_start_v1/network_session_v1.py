"""Network session entry — ephemeral network_session_go only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.network_session_go_v1 import (
    bind_ephemeral_network_session_go_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    NEXT_OPERATION_AFTER_STUBBED_BOUNDARY,
)


class ActualStartNetworkSessionError(RuntimeError):
    """Fail-closed network session violation."""


@dataclass(frozen=True)
class NetworkSessionEntryV1:
    boundary_reached: bool
    network_session_started: bool
    network_session_go: bool
    stubbed: bool
    next_operation: str
    session_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_reached": self.boundary_reached,
            "network_session_started": self.network_session_started,
            "network_session_go": self.network_session_go,
            "stubbed": self.stubbed,
            "next_operation": self.next_operation,
            "session_id": self.session_id,
        }


def reach_network_session_entry_boundary_v1(
    *,
    preflight_pass: bool,
    testnet_authorized_runtime: bool,
    campaign_enabled: bool,
    campaign_armed: bool,
    network_session_go: bool,
    environ: Mapping[str, str] | None = None,
    config_network_session_go: bool | None = None,
    persisted_network_session_go: bool | None = None,
    stubbed: bool = True,
    session_id: str = "session-actual-start",
) -> NetworkSessionEntryV1:
    """Last side-effect-free point before permitted TESTNET effect.

    When ``network_session_go`` is False, returns boundary_reached with
    network_session_started=False (inspection only).
    When True and preflight complete, starts session (stubbed or real).
    """
    if not preflight_pass:
        raise ActualStartNetworkSessionError("PREFLIGHT_REQUIRED_BEFORE_NETWORK_SESSION")
    if not testnet_authorized_runtime:
        raise ActualStartNetworkSessionError("TESTNET_RUNTIME_AUTH_REQUIRED")
    if not campaign_enabled or not campaign_armed:
        raise ActualStartNetworkSessionError("ENABLED_ARMED_REQUIRED")

    go = bind_ephemeral_network_session_go_v1(
        network_session_go=network_session_go,
        environ=environ,
        config_network_session_go=config_network_session_go,
        persisted_network_session_go=persisted_network_session_go,
    )
    if go.get("ok") is not True:
        raise ActualStartNetworkSessionError(
            "NETWORK_SESSION_GO_BIND_FAILED:" + ",".join(go.get("blockers") or [])
        )
    if bool(go.get("network_session_go")) is not bool(network_session_go):
        raise ActualStartNetworkSessionError("NETWORK_SESSION_GO_MISMATCH")

    if not network_session_go:
        return NetworkSessionEntryV1(
            boundary_reached=True,
            network_session_started=False,
            network_session_go=False,
            stubbed=stubbed,
            next_operation=NEXT_OPERATION_AFTER_STUBBED_BOUNDARY,
            session_id=session_id,
        )

    # Crossing the boundary: session started. External effect remains stubbed
    # unless a later real-network OWNER_GO path is used.
    return NetworkSessionEntryV1(
        boundary_reached=True,
        network_session_started=True,
        network_session_go=True,
        stubbed=stubbed,
        next_operation=NEXT_OPERATION_AFTER_STUBBED_BOUNDARY,
        session_id=session_id,
    )
