"""Terminal classification for Step-5 prolonged session evidence."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.constants_v1 import (
    MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
    TERMINAL_CLASSES,
)


def classify_terminal_v1(
    *,
    proposed_terminal: str,
    telemetry: Mapping[str, Any],
    evidence_verified: bool,
    claims_match_telemetry: bool,
    blockers: list[str] | None = None,
    minimum_successful_wallclock_seconds: int = MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
) -> dict[str, Any]:
    blockers = list(blockers or [])
    terminal = str(proposed_terminal or "HARD_STOP")
    if terminal not in TERMINAL_CLASSES:
        return {
            "ok": False,
            "terminal_class": "HARD_STOP",
            "blockers": blockers + ["UNKNOWN_TERMINAL_CLASS"],
            "pass_eligible": False,
        }

    network_started = bool(telemetry.get("network_session_started"))
    wallclock = float(telemetry.get("session_monotonic_wallclock_seconds") or 0.0)
    request_count = int(telemetry.get("request_count") or 0)
    distinct = int(telemetry.get("distinct_observation_count") or 0)
    order_side = bool(telemetry.get("order_side_effect_occurred"))
    cred = bool(telemetry.get("credential_access_occurred"))
    private = bool(telemetry.get("private_endpoint_access_occurred"))
    auth_hdr = bool(telemetry.get("auth_header_transmitted"))

    pass_eligible = (
        terminal == "PASS"
        and network_started
        and wallclock >= float(minimum_successful_wallclock_seconds)
        and request_count > 0
        and distinct > 0
        and evidence_verified
        and claims_match_telemetry
        and not order_side
        and not cred
        and not private
        and not auth_hdr
        and not blockers
    )
    if terminal == "PASS" and not pass_eligible:
        terminal = "HARD_STOP"
        blockers.append("PASS_CRITERIA_NOT_MET")

    return {
        "ok": pass_eligible if proposed_terminal == "PASS" else terminal in TERMINAL_CLASSES,
        "terminal_class": terminal,
        "blockers": sorted(set(blockers)),
        "pass_eligible": pass_eligible,
        "pass_requirements": {
            "NETWORK_SESSION_STARTED": network_started,
            "SESSION_MONOTONIC_WALLCLOCK_SECONDS": wallclock,
            "MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS": minimum_successful_wallclock_seconds,
            "REQUEST_COUNT": request_count,
            "DISTINCT_OBSERVATION_COUNT": distinct,
            "EVIDENCE_VERIFIED": evidence_verified,
            "CLAIMS_MATCH_TELEMETRY": claims_match_telemetry,
            "ORDER_SIDE_EFFECT_OCCURRED": order_side,
            "CREDENTIAL_ACCESS_OCCURRED": cred,
            "PRIVATE_ENDPOINT_ACCESS_OCCURRED": private,
            "AUTH_HEADER_TRANSMITTED": auth_hdr,
        },
    }
