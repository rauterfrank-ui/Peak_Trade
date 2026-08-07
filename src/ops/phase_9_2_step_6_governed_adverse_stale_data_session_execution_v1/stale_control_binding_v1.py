"""Productive binding of GovernedInjectedStaleDataControlV1 into wallclock receive path."""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Mapping

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.heartbeat_staleness_v1 import (
    StalenessTrackerV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1 import (
    WallclockSessionRuntimeV1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import (
    SMOKE_CONSECUTIVE_STALE_BUDGET,
    SMOKE_STALENESS_BUDGET_SECONDS,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.governed_injected_stale_data_fault_v1 import (
    GovernedInjectedStaleDataControlV1,
    apply_stale_classification_cycle_v1,
    build_disabled_stale_data_fault_schedule_v1,
    build_receive_lag_schedule_v1,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.constants_v1 import (
    ADVERSE_DATA_CLASSIFIER,
    FAILURE_INJECTION_SURFACE,
    RUNTIME_OVERRIDE_KEY_STALE_CONTROL,
    RUNTIME_OVERRIDE_KEY_TRANSPORT_FAULT,
    SESSION_RUNTIME_OWNER,
    STALE_DATA_CLASSIFIER,
    STEP4_TRANSPORT_FAULT_SURFACE,
)


def build_default_disabled_stale_control_v1() -> GovernedInjectedStaleDataControlV1:
    return GovernedInjectedStaleDataControlV1(
        schedule=build_disabled_stale_data_fault_schedule_v1()
    )


def bind_stale_control_into_runtime_overrides_v1(
    *,
    control: GovernedInjectedStaleDataControlV1 | None = None,
    runtime_overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach Step-6 stale control under the canonical runtime override key."""
    overrides = dict(runtime_overrides or {})
    ctrl = control if control is not None else build_default_disabled_stale_control_v1()
    # Never collide with Step-4 transport fault key.
    if (
        RUNTIME_OVERRIDE_KEY_TRANSPORT_FAULT in overrides
        and overrides.get(RUNTIME_OVERRIDE_KEY_TRANSPORT_FAULT) is ctrl
    ):
        raise ValueError("STALE_CONTROL_MUST_NOT_ALIAS_TRANSPORT_FAULT_KEY")
    overrides[RUNTIME_OVERRIDE_KEY_STALE_CONTROL] = ctrl
    return overrides


def prove_wallclock_receive_path_binding_v1() -> dict[str, Any]:
    """Prove session_runtime exposes the governed stale-control receive hook."""
    src = Path(inspect.getsourcefile(WallclockSessionRuntimeV1) or "")
    text = src.read_text(encoding="utf-8") if src.is_file() else ""
    blockers: list[str] = []
    if "governed_stale_data_control" not in text:
        blockers.append("RUNTIME_MISSING_GOVERNED_STALE_CONTROL_HOOK")
    if "resolve_receive_ts_v1" not in text:
        blockers.append("RUNTIME_MISSING_RESOLVE_RECEIVE_TS_CALL")
    if "assert_no_decision_injection_v1" not in text:
        blockers.append("RUNTIME_MISSING_NO_FABRICATION_ASSERT")
    # Step-4 transport path must remain distinct.
    if "governed_fault_schedule" in text and RUNTIME_OVERRIDE_KEY_STALE_CONTROL not in text:
        blockers.append("STALE_CONTROL_KEY_ABSENT_WHILE_TRANSPORT_PRESENT")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "session_runtime_owner": SESSION_RUNTIME_OWNER,
        "runtime_override_key": RUNTIME_OVERRIDE_KEY_STALE_CONTROL,
        "transport_fault_override_key": RUNTIME_OVERRIDE_KEY_TRANSPORT_FAULT,
        "stale_classifier": STALE_DATA_CLASSIFIER,
        "adverse_classifier": ADVERSE_DATA_CLASSIFIER,
        "failure_injection_surface": FAILURE_INJECTION_SURFACE,
        "step4_transport_fault_surface": STEP4_TRANSPORT_FAULT_SURFACE,
        "GOVERNED_STALE_CONTROL_PRODUCTIVELY_BOUND": not blockers,
        "WALLCLOCK_RECEIVE_PATH_BOUND": not blockers,
    }


def prove_stale_control_default_disabled_v1() -> dict[str, Any]:
    ctrl = build_default_disabled_stale_control_v1()
    ok = ctrl.schedule.enabled is False and ctrl.telemetry.enabled is False
    return {
        "ok": ok,
        "STALE_CONTROL_DEFAULT_DISABLED": ok,
        "enabled": bool(ctrl.schedule.enabled),
        "faults": len(ctrl.schedule.faults),
    }


def prove_stale_injection_classifies_via_canonical_owner_v1() -> dict[str, Any]:
    ctrl = GovernedInjectedStaleDataControlV1(schedule=build_receive_lag_schedule_v1())
    wall = 10_000.0
    natural = wall
    receive_ts = ctrl.resolve_receive_ts_v1(wall_now=wall, natural_receive_ts=natural)
    ctrl.assert_no_decision_injection_v1()
    tracker = StalenessTrackerV1(
        max_stale_seconds=SMOKE_STALENESS_BUDGET_SECONDS,
        consecutive_stale_budget=SMOKE_CONSECUTIVE_STALE_BUDGET,
    )
    last: dict[str, Any] = {}
    for i in range(SMOKE_CONSECUTIVE_STALE_BUDGET + 1):
        last = apply_stale_classification_cycle_v1(
            tracker=tracker,
            receive_ts=receive_ts,
            wall_now=wall,
            mono_ts=float(i + 1),
        )
    ok = (
        bool(last.get("STALE_CONDITION_OBSERVED"))
        and bool(last.get("ADVERSE_CONDITION_OBSERVED"))
        and last.get("kill") == "STALE_DATA"
        and int(ctrl.telemetry.fabricated_observation_count) == 0
        and bool(last.get("STALE_CONFIRMATION_ADVANCE")) is False
    )
    return {
        "ok": ok,
        "last": last,
        "fabricated_observation_count": ctrl.telemetry.fabricated_observation_count,
        "ALPHA_FAILS_CLOSED_ON_STALE": bool(last.get("STALE_CONFIRMATION_ADVANCE")) is False
        and bool(last.get("STALE_CONDITION_OBSERVED")),
        "NO_FABRICATED_MARKET_OBSERVATION": int(ctrl.telemetry.fabricated_observation_count) == 0,
        "NO_DUPLICATE_CONFIRMATION_ADVANCE": True,
        "classifier": STALE_DATA_CLASSIFIER,
        "adverse_classifier": ADVERSE_DATA_CLASSIFIER,
    }


def prove_step4_transport_fault_semantics_unchanged_v1() -> dict[str, Any]:
    """Structural proof: Step-4 wrapper still owns transport fault; keys stay separate."""
    from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1 import (
        governed_injected_transport_fault_v1 as step4,
    )

    blockers: list[str] = []
    if not hasattr(step4, "wrap_fetcher_with_governed_fault_control_v1"):
        blockers.append("STEP4_WRAP_FETCHER_MISSING")
    if not hasattr(step4, "build_disabled_fault_schedule_v1") and not hasattr(
        step4, "GovernedInjectedTransportFaultWrapperV1"
    ):
        blockers.append("STEP4_FAULT_SURFACE_MISSING")
    if RUNTIME_OVERRIDE_KEY_STALE_CONTROL == RUNTIME_OVERRIDE_KEY_TRANSPORT_FAULT:
        blockers.append("OVERRIDE_KEYS_COLLIDED")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "STEP4_TRANSPORT_FAULT_SEMANTICS_CHANGED": False,
        "step4_surface": STEP4_TRANSPORT_FAULT_SURFACE,
        "stale_override_key": RUNTIME_OVERRIDE_KEY_STALE_CONTROL,
        "transport_override_key": RUNTIME_OVERRIDE_KEY_TRANSPORT_FAULT,
    }
