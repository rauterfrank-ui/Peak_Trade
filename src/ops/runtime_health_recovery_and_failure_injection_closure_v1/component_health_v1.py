"""Explicit per-component health reporting for O6.

Health is derived from explicit fields — never from process existence alone.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional

from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.constants_v1 import (
    DEGRADED_MAX_AGE_SECONDS,
    HEALTH_COMPONENTS,
    HEALTH_DEGRADED,
    HEALTH_DISCONNECTED,
    HEALTH_HEALTHY,
    HEALTH_MISSING_SOURCE,
    HEALTH_STATES,
    HEALTH_STALE,
    HEALTHY_MAX_AGE_SECONDS,
    HEARTBEAT_STALE_SECONDS,
    NON_HEALTHY_STATES,
    REQUIRED_HEALTH_FIELDS,
)


class ComponentHealthErrorV1(ValueError):
    """Fail-closed component-health contract violation."""


@dataclass
class ComponentHealthReportV1:
    component: str
    process_alive: bool
    heartbeat_time: Optional[float]
    last_success_time: Optional[float]
    last_error_time: Optional[float]
    error_class: Optional[str]
    restart_count: int
    input_lag: Optional[float]
    output_lag: Optional[float]
    state_commit_position: int
    evidence_cursor: int
    session_id: str
    repository_sha: str
    config_digest: str
    disconnected: bool = False
    source_present: bool = True
    classification: str = HEALTH_MISSING_SOURCE
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


def assert_required_health_fields_v1(payload: Mapping[str, Any]) -> None:
    missing = [name for name in REQUIRED_HEALTH_FIELDS if name not in payload]
    if missing:
        raise ComponentHealthErrorV1(f"MISSING_HEALTH_FIELDS:{','.join(missing)}")


def classify_component_health_v1(
    *,
    process_alive: bool,
    heartbeat_time: Optional[float],
    last_success_time: Optional[float],
    now_unix: float,
    disconnected: bool = False,
    source_present: bool = True,
    error_class: Optional[str] = None,
    heartbeat_stale_seconds: float = HEARTBEAT_STALE_SECONDS,
    healthy_max_age_seconds: float = HEALTHY_MAX_AGE_SECONDS,
    degraded_max_age_seconds: float = DEGRADED_MAX_AGE_SECONDS,
) -> str:
    """Derive component health. Process-alive alone is never sufficient for HEALTHY."""
    if not source_present:
        return HEALTH_MISSING_SOURCE
    if disconnected:
        return HEALTH_DISCONNECTED
    if not process_alive:
        # Dead process with known source → disconnected, never healthy.
        return HEALTH_DISCONNECTED
    if heartbeat_time is None:
        return HEALTH_DEGRADED
    heartbeat_age = float(now_unix) - float(heartbeat_time)
    if heartbeat_age > float(heartbeat_stale_seconds):
        return HEALTH_STALE
    if last_success_time is None:
        return HEALTH_DEGRADED
    success_age = float(now_unix) - float(last_success_time)
    if success_age > float(degraded_max_age_seconds):
        return HEALTH_STALE
    if success_age > float(healthy_max_age_seconds):
        return HEALTH_DEGRADED
    if error_class and str(error_class).strip():
        # Recent soft error with otherwise fresh success → degraded.
        return HEALTH_DEGRADED
    return HEALTH_HEALTHY


def build_component_health_report_v1(
    *,
    component: str,
    process_alive: bool,
    heartbeat_time: Optional[float],
    last_success_time: Optional[float],
    last_error_time: Optional[float],
    error_class: Optional[str],
    restart_count: int,
    input_lag: Optional[float],
    output_lag: Optional[float],
    state_commit_position: int,
    evidence_cursor: int,
    session_id: str,
    repository_sha: str,
    config_digest: str,
    now_unix: float,
    disconnected: bool = False,
    source_present: bool = True,
    extra: Optional[Mapping[str, Any]] = None,
) -> ComponentHealthReportV1:
    if component not in HEALTH_COMPONENTS:
        raise ComponentHealthErrorV1(f"UNKNOWN_HEALTH_COMPONENT:{component}")
    classification = classify_component_health_v1(
        process_alive=process_alive,
        heartbeat_time=heartbeat_time,
        last_success_time=last_success_time,
        now_unix=now_unix,
        disconnected=disconnected,
        source_present=source_present,
        error_class=error_class,
    )
    report = ComponentHealthReportV1(
        component=component,
        process_alive=bool(process_alive),
        heartbeat_time=heartbeat_time,
        last_success_time=last_success_time,
        last_error_time=last_error_time,
        error_class=error_class,
        restart_count=int(restart_count),
        input_lag=input_lag,
        output_lag=output_lag,
        state_commit_position=int(state_commit_position),
        evidence_cursor=int(evidence_cursor),
        session_id=str(session_id),
        repository_sha=str(repository_sha),
        config_digest=str(config_digest),
        disconnected=bool(disconnected),
        source_present=bool(source_present),
        classification=classification,
        extra=dict(extra or {}),
    )
    assert_required_health_fields_v1(report.to_dict())
    if report.classification not in HEALTH_STATES:
        raise ComponentHealthErrorV1(f"INVALID_CLASSIFICATION:{report.classification}")
    return report


def assert_process_alive_alone_insufficient_v1(
    *,
    process_alive: bool,
    heartbeat_time: Optional[float],
    last_success_time: Optional[float],
    now_unix: float,
) -> dict[str, Any]:
    """Prove HEALTHY cannot be claimed from process_alive alone."""
    classification = classify_component_health_v1(
        process_alive=process_alive,
        heartbeat_time=heartbeat_time,
        last_success_time=last_success_time,
        now_unix=now_unix,
        source_present=True,
        disconnected=False,
    )
    if process_alive and heartbeat_time is None and classification == HEALTH_HEALTHY:
        raise ComponentHealthErrorV1("PROCESS_ALIVE_ALONE_MUST_NOT_BE_HEALTHY")
    if process_alive and last_success_time is None and classification == HEALTH_HEALTHY:
        raise ComponentHealthErrorV1("PROCESS_ALIVE_WITHOUT_SUCCESS_MUST_NOT_BE_HEALTHY")
    return {
        "ok": True,
        "process_alive": process_alive,
        "classification": classification,
        "may_be_healthy": classification == HEALTH_HEALTHY,
    }


def assert_non_healthy_cannot_render_green_v1(
    *,
    classification: str,
    render_as_healthy: bool,
) -> dict[str, Any]:
    state = str(classification or "").strip().upper()
    if state not in HEALTH_STATES:
        raise ComponentHealthErrorV1(f"UNKNOWN_HEALTH_STATE:{classification}")
    if state in NON_HEALTHY_STATES and render_as_healthy:
        raise ComponentHealthErrorV1(f"STALE_OR_DISCONNECTED_CANNOT_RENDER_HEALTHY:{state}")
    return {
        "ok": True,
        "classification": state,
        "render_as_healthy": bool(render_as_healthy),
        "allowed": True,
    }
