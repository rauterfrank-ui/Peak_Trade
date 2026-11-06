"""Terminal classification for future Step-6 productive session evidence."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.constants_v1 import (
    DEFAULT_WALLCLOCK_DURATION_SECONDS,
    TERMINAL_CLASSES,
)


def classify_terminal_v1(
    *,
    proposed_terminal: str,
    telemetry: Mapping[str, Any] | None = None,
    evidence_verified: bool = False,
    claims_match_telemetry: bool = False,
    blockers: list[str] | None = None,
    minimum_successful_wallclock_seconds: int = DEFAULT_WALLCLOCK_DURATION_SECONDS,
    binding_only: bool = False,
) -> dict[str, Any]:
    blockers = list(blockers or [])
    telemetry = dict(telemetry or {})
    terminal = str(proposed_terminal or "HARD_STOP")
    if terminal not in TERMINAL_CLASSES:
        return {
            "ok": False,
            "terminal_class": "HARD_STOP",
            "blockers": blockers + ["UNKNOWN_TERMINAL_CLASS"],
            "pass_eligible": False,
        }

    if binding_only:
        # Binding capability never claims productive session PASS.
        if terminal == "PASS":
            terminal = "BINDING_PROOF"
        return {
            "ok": terminal == "BINDING_PROOF" and not blockers,
            "terminal_class": terminal if terminal != "PASS" else "BINDING_PROOF",
            "blockers": sorted(set(blockers)),
            "pass_eligible": False,
            "binding_only": True,
            "notes": ["PRODUCTIVE_SESSION_PASS_NOT_CLAIMED_IN_BINDING=true"],
        }

    network_started = bool(telemetry.get("network_session_started"))
    wallclock = float(telemetry.get("session_monotonic_wallclock_seconds") or 0.0)
    request_count = int(telemetry.get("request_count") or 0)
    order_side = bool(telemetry.get("order_side_effect_occurred"))
    private = bool(telemetry.get("private_endpoint_access_occurred"))
    cred = bool(telemetry.get("credential_access_occurred"))

    pass_eligible = (
        terminal == "PASS"
        and network_started
        and wallclock >= float(minimum_successful_wallclock_seconds)
        and request_count > 0
        and evidence_verified
        and claims_match_telemetry
        and not order_side
        and not private
        and not cred
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
        "binding_only": False,
    }
