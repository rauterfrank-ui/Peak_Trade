"""Process observations cannot override original bounded-session owner gates."""

from dataclasses import dataclass
import json
import math
import os

STOP = "offline_session_stop_v1.json"


@dataclass(frozen=True)
class OfflineProcessObservationV1:
    session_id: str
    manifest_digest: str
    pid: int
    heartbeat_unix: float
    healthy: bool


def check_stop_v1(session):
    path = session.root / STOP
    if path.exists():
        value = json.loads(path.read_text())
        if (
            not isinstance(value, dict)
            or set(value) != {"schema", "manifest_digest", "reason", "requested_unix"}
            or value["schema"] != "bounded_offline_session_stop.v1"
            or value["manifest_digest"] != session.manifest.digest()
            or type(value["reason"]) is not str
            or not value["reason"]
            or value["reason"] != value["reason"].strip()
            or type(value["requested_unix"]) not in {int, float}
            or not math.isfinite(value["requested_unix"])
            or value["requested_unix"] <= 0
        ):
            raise ValueError("OFFLINE_SESSION_STOP_RECORD_INVALID")
        raise ValueError("OFFLINE_SESSION_STOP_REQUESTED:" + value["reason"])


def project_offline_session_readiness_v1(
    session,
    *,
    process,
    now_unix,
    maximum_heartbeat_age_seconds,
    portfolio_owner=None,
    action_scope="SESSION",
):
    reasons = []
    if action_scope not in {"SESSION", "POSITION_MANAGEMENT", "NEW_ENTRY"}:
        raise ValueError("OFFLINE_READINESS_ACTION_SCOPE_REQUIRED")
    if (
        type(process) is not OfflineProcessObservationV1
        or type(process.pid) is not int
        or process.pid <= 0
        or type(process.healthy) is not bool
        or type(process.heartbeat_unix) not in {int, float}
        or type(now_unix) not in {int, float}
        or type(maximum_heartbeat_age_seconds) not in {int, float}
        or not all(
            math.isfinite(x)
            for x in (process.heartbeat_unix, now_unix, maximum_heartbeat_age_seconds)
        )
        or maximum_heartbeat_age_seconds <= 0
    ):
        reasons.append("PROCESS_OBSERVATION_INVALID")
    elif (
        process.session_id != session.manifest.session_id
        or process.manifest_digest != session.manifest.digest()
        or process.pid != getattr(session, "_process_pid", None)
        or process.pid != os.getpid()
    ):
        reasons.append("PROCESS_SESSION_IDENTITY_MISMATCH")
    elif (
        not process.healthy
        or not 0 <= now_unix - process.heartbeat_unix <= maximum_heartbeat_age_seconds
    ):
        reasons.append("PROCESS_UNHEALTHY_OR_STALE")
    else:
        try:
            os.kill(process.pid, 0)
        except OSError:
            reasons.append("PROCESS_NOT_ALIVE")
    if not session._active or not session._fds:
        reasons.append("OFFLINE_SESSION_NOT_OPEN")
    try:
        session._validate_state()
        if session.state["status"] != "READY":
            reasons.append("OFFLINE_SESSION_NOT_READY:" + session.state["status"])
        if session.state["attempts_used"] >= session.manifest.max_attempts:
            reasons.append("OFFLINE_SESSION_ATTEMPTS_EXHAUSTED")
        check_stop_v1(session)
        from .session_v1 import MANIFEST, RECEIPT
        from .manifest_v1 import load_offline_episode_session_manifest_v1

        if (
            json.loads((session.root / RECEIPT).read_text()) != session.state
            or load_offline_episode_session_manifest_v1(session.root / MANIFEST).digest()
            != session.manifest.digest()
        ):
            raise ValueError("OFFLINE_SESSION_RECEIPT_OR_MANIFEST_CHANGED")
        session._load_episodes()
        session._resource_bindings()
    except (ValueError, TypeError, OSError, RuntimeError) as exc:
        reasons.append(str(exc))
    capital_reasons = []
    if portfolio_owner is not None:
        state = portfolio_owner.budget_state_v1()
        if not state.durable_state_enabled or not state.admitted or state.recovery_required:
            capital_reasons.append("PORTFOLIO_OWNER_RECOVERY_REQUIRED")
        try:
            snapshot = portfolio_owner.risk_snapshot_v1()
            if (
                snapshot["state"]["account_identity"]
                != session.manifest.account_scope.account_identity
            ):
                reasons.append("PORTFOLIO_OWNER_ACCOUNT_MISMATCH")
            for lane in session.manifest.lanes:
                bound = snapshot["state"]["lane_bindings"].get(lane.identity.lane_id)
                if bound is None or (
                    bound["bound_instrument_identity"],
                    bound["instrument_epoch"],
                ) != (lane.bound_instrument_identity, lane.instrument_epoch):
                    reasons.append("PORTFOLIO_OWNER_LANE_GENERATION_MISMATCH")
        except ValueError as exc:
            reasons.append(str(exc))
    if action_scope == "NEW_ENTRY":
        if portfolio_owner is None:
            capital_reasons.append("PORTFOLIO_OWNER_REQUIRED")
        if session._episodes:
            reasons.append("NEW_ENTRY_FORBIDDEN_IN_OCCUPIED_EPISODE_PROFILE")
    if action_scope != "POSITION_MANAGEMENT":
        reasons.extend(capital_reasons)
    return {
        "schema": "bounded_offline_session_readiness.v1",
        "session_id": session.manifest.session_id,
        "manifest_digest": session.manifest.digest(),
        "ready": not reasons,
        "reason_codes": reasons,
        "capital_reason_codes": capital_reasons,
        "action_scope": action_scope,
        "venue_truth_proven": False,
        "external_effect_authorized": False,
    }


def run_readiness_checked_offline_cycle_v1(
    session,
    composed_pairs,
    *,
    process,
    now_unix,
    maximum_heartbeat_age_seconds,
    portfolio_owner=None,
    **kwargs,
):
    """Explicit E2 management entry; fresh entry capital is not an Exit gate."""
    result = project_offline_session_readiness_v1(
        session,
        process=process,
        now_unix=now_unix,
        maximum_heartbeat_age_seconds=maximum_heartbeat_age_seconds,
        portfolio_owner=portfolio_owner,
        action_scope="POSITION_MANAGEMENT",
    )
    if not result["ready"]:
        raise ValueError("OFFLINE_SESSION_READINESS_BLOCKED:" + "|".join(result["reason_codes"]))
    return session.run_occupied_cycle_v1(composed_pairs, **kwargs)
