"""Step-5 claim semantics: reachability ≠ natural occurrence ≠ observed outcome."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.constants_v1 import (
    CLAIM_FIELDS,
    RECONNECT_PATH_STATUS_NOT_NATURAL,
)


def classify_reconnect_claims_v1(
    *,
    reconnect_path_reachable: bool,
    reconnect_timeline: list[Any] | tuple[Any, ...] | None,
    reconnect_attempt_count: int = 0,
    reconnect_success_count: int = 0,
    reconnect_path_status: str | None = None,
) -> dict[str, Any]:
    """Never promote NOT_NATURALLY_OCCURRED_CLASSIFIED to RECONNECT_OBSERVED=true."""
    timeline = list(reconnect_timeline or [])
    natural = bool(timeline) or int(reconnect_attempt_count) > 0 or int(reconnect_success_count) > 0
    status = str(reconnect_path_status or "").strip()
    if status == RECONNECT_PATH_STATUS_NOT_NATURAL:
        natural = False
    observed = bool(natural and timeline)
    if status == RECONNECT_PATH_STATUS_NOT_NATURAL:
        observed = False
    return {
        "RECONNECT_PATH_REACHABLE": bool(reconnect_path_reachable),
        "RECONNECT_NATURALLY_OCCURRED": bool(natural),
        "RECONNECT_OBSERVED": bool(observed),
        "RECONNECT_PATH_STATUS": status
        or (RECONNECT_PATH_STATUS_NOT_NATURAL if not natural else "NATURALLY_OCCURRED_CLASSIFIED"),
        "notes": [
            "REACHABLE_NE_NATURALLY_OCCURRED_NE_OBSERVED=true",
            f"RECONNECT_PATH_STATUS_NOT_NATURAL_NEVER_OBSERVED="
            f"{status == RECONNECT_PATH_STATUS_NOT_NATURAL}",
        ],
    }


def classify_trade_outcome_claims_v1(
    *,
    entry_intent_count: int = 0,
    entry_fill_count: int = 0,
    reduce_intent_count: int = 0,
    reduce_fill_count: int = 0,
    exit_intent_count: int = 0,
    exit_fill_count: int = 0,
) -> dict[str, Any]:
    return {
        "ENTRY_OBSERVED": int(entry_intent_count) > 0 or int(entry_fill_count) > 0,
        "REDUCE_OBSERVED": int(reduce_intent_count) > 0 or int(reduce_fill_count) > 0,
        "EXIT_OBSERVED": int(exit_intent_count) > 0 or int(exit_fill_count) > 0,
        "NATURAL_ABSENCE_ALLOWED": True,
        "notes": [
            "ZERO_TRADE_COUNTS_MAY_COEXIST_WITH_PASS=true",
            "NATURAL_ABSENCE_IS_NOT_AUTOMATIC_FAIL=true",
        ],
    }


def classify_stale_claims_v1(
    *,
    stale_observation_count: int = 0,
    stale_events: list[Any] | tuple[Any, ...] | None = None,
) -> dict[str, Any]:
    events = list(stale_events or [])
    natural = int(stale_observation_count) > 0 or bool(events)
    return {
        "STALE_DATA_NATURALLY_OCCURRED": bool(natural),
        "STALE_DATA_OBSERVED": bool(natural and (events or int(stale_observation_count) > 0)),
        "STALE_NATURAL_ABSENCE_IS_NOT_DEFECT": True,
    }


def build_binding_claim_matrix_v1(
    *,
    runtime_reachable: bool = True,
    session_started: bool = False,
    duration_completed: bool = False,
    graceful_stop_observed: bool = False,
    interrupt_recovery_observed: bool = False,
    restart_recovery_observed: bool = False,
    reconnect_claims: Mapping[str, Any] | None = None,
    stale_claims: Mapping[str, Any] | None = None,
    trade_claims: Mapping[str, Any] | None = None,
    no_order_boundary_proven: bool = True,
    evidence_verified: bool = False,
    capability_closed: bool = False,
) -> dict[str, Any]:
    reconnect = dict(
        reconnect_claims
        or classify_reconnect_claims_v1(
            reconnect_path_reachable=True,
            reconnect_timeline=[],
            reconnect_path_status=RECONNECT_PATH_STATUS_NOT_NATURAL,
        )
    )
    stale = dict(stale_claims or classify_stale_claims_v1())
    trade = dict(trade_claims or classify_trade_outcome_claims_v1())
    claims = {
        "STEP5_RUNTIME_REACHABLE": bool(runtime_reachable),
        "STEP5_SESSION_STARTED": bool(session_started),
        "STEP5_DURATION_COMPLETED": bool(duration_completed),
        "STEP5_GRACEFUL_STOP_OBSERVED": bool(graceful_stop_observed),
        "STEP5_INTERRUPT_RECOVERY_OBSERVED": bool(interrupt_recovery_observed),
        "STEP5_RESTART_RECOVERY_OBSERVED": bool(restart_recovery_observed),
        "RECONNECT_PATH_REACHABLE": bool(reconnect.get("RECONNECT_PATH_REACHABLE")),
        "RECONNECT_NATURALLY_OCCURRED": bool(reconnect.get("RECONNECT_NATURALLY_OCCURRED")),
        "RECONNECT_OBSERVED": bool(reconnect.get("RECONNECT_OBSERVED")),
        "STALE_DATA_NATURALLY_OCCURRED": bool(stale.get("STALE_DATA_NATURALLY_OCCURRED")),
        "STALE_DATA_OBSERVED": bool(stale.get("STALE_DATA_OBSERVED")),
        "ENTRY_OBSERVED": bool(trade.get("ENTRY_OBSERVED")),
        "REDUCE_OBSERVED": bool(trade.get("REDUCE_OBSERVED")),
        "EXIT_OBSERVED": bool(trade.get("EXIT_OBSERVED")),
        "NO_ORDER_BOUNDARY_PROVEN": bool(no_order_boundary_proven),
        "EVIDENCE_VERIFIED": bool(evidence_verified),
        "CAPABILITY_CLOSED": bool(capability_closed),
    }
    # Invariant: classified natural absence must never overstate observed reconnect.
    if reconnect.get("RECONNECT_PATH_STATUS") == RECONNECT_PATH_STATUS_NOT_NATURAL:
        claims["RECONNECT_OBSERVED"] = False
        claims["RECONNECT_NATURALLY_OCCURRED"] = False
    missing = [k for k in CLAIM_FIELDS if k not in claims]
    return {
        "ok": not missing
        and not (
            claims["RECONNECT_OBSERVED"]
            and reconnect.get("RECONNECT_PATH_STATUS") == RECONNECT_PATH_STATUS_NOT_NATURAL
        ),
        "claims": claims,
        "claim_fields": list(CLAIM_FIELDS),
        "missing_claim_fields": missing,
        "reconnect_detail": reconnect,
        "stale_detail": stale,
        "trade_detail": trade,
        "notes": [
            "BINDING_PR_LEAVES_CAPABILITY_CLOSED_FALSE=true",
            "REACHABLE_NE_OBSERVED_NE_NATURALLY_OCCURRED_NE_CLOSED=true",
        ],
    }


def prove_claim_semantics_offline_v1() -> dict[str, Any]:
    """Offline proof that natural-absence classification never overstates reconnect."""
    natural_absence = classify_reconnect_claims_v1(
        reconnect_path_reachable=True,
        reconnect_timeline=[],
        reconnect_attempt_count=0,
        reconnect_success_count=0,
        reconnect_path_status=RECONNECT_PATH_STATUS_NOT_NATURAL,
    )
    overclaim_blocked = (
        natural_absence["RECONNECT_OBSERVED"] is False
        and natural_absence["RECONNECT_NATURALLY_OCCURRED"] is False
        and natural_absence["RECONNECT_PATH_REACHABLE"] is True
    )
    with_natural = classify_reconnect_claims_v1(
        reconnect_path_reachable=True,
        reconnect_timeline=[{"event": "reconnect", "at": 1.0}],
        reconnect_attempt_count=1,
        reconnect_success_count=1,
    )
    trade_zero = classify_trade_outcome_claims_v1()
    matrix = build_binding_claim_matrix_v1(
        runtime_reachable=True,
        session_started=False,
        reconnect_claims=natural_absence,
        trade_claims=trade_zero,
        capability_closed=False,
    )
    blockers: list[str] = []
    if not overclaim_blocked:
        blockers.append("NOT_NATURAL_RECONNECT_OVERCLAIMED")
    if with_natural["RECONNECT_OBSERVED"] is not True:
        blockers.append("NATURAL_RECONNECT_SHOULD_OBSERVE")
    if trade_zero["ENTRY_OBSERVED"] or trade_zero["REDUCE_OBSERVED"] or trade_zero["EXIT_OBSERVED"]:
        blockers.append("ZERO_TRADE_COUNTS_MUST_NOT_OBSERVE")
    if matrix["claims"]["CAPABILITY_CLOSED"]:
        blockers.append("BINDING_MUST_LEAVE_CAPABILITY_CLOSED_FALSE")
    if matrix["claims"]["RECONNECT_OBSERVED"]:
        blockers.append("BINDING_MATRIX_RECONNECT_OVERCLAIM")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "natural_absence": natural_absence,
        "natural_reconnect": with_natural,
        "trade_zero": trade_zero,
        "binding_claim_matrix": matrix,
        "network_session_started": False,
        "fault_session_started": False,
        "claims": {
            "CLAIM_SEMANTICS_BOUND": True,
            "RECONNECT_PATH_STATUS_NOT_NATURAL_NEVER_OBSERVED": True,
            "NATURAL_ABSENCE_ALLOWED": True,
        },
    }
