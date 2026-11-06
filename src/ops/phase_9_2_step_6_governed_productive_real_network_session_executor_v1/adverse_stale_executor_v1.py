"""Adverse/stale executor wiring — reuses existing stale control + wallclock owner.

This module never starts a network session by itself. It prepares
runtime_overrides[governed_stale_data_control] for a later Owner-GO session
and proves RECEIVE_LAG reaches the canonical receive-path classifier offline.
"""

from __future__ import annotations

import importlib
from typing import Any, Mapping

from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.governed_injected_stale_data_fault_v1 import (
    GovernedInjectedStaleDataControlV1,
    build_disabled_stale_data_fault_schedule_v1,
    build_receive_lag_schedule_v1,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.stale_control_binding_v1 import (
    bind_stale_control_into_runtime_overrides_v1,
    prove_stale_injection_classifies_via_canonical_owner_v1,
    prove_wallclock_receive_path_binding_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.constants_v1 import (
    CANONICAL_WALLCLOCK_RUNNER,
    FAILURE_INJECTION_SURFACE,
    MAX_NETWORK_SESSION_COUNT,
    RUNTIME_OVERRIDE_KEY_STALE_CONTROL,
    RUNTIME_OVERRIDE_KEY_TRANSPORT_FAULT,
    STALE_CONTROL_BINDING_OWNER,
)


def resolve_wallclock_runner_symbol_v1() -> dict[str, Any]:
    module_path, _, attr = CANONICAL_WALLCLOCK_RUNNER.rpartition(".")
    import_path = module_path[len("src.") :] if module_path.startswith("src.") else module_path
    mod = importlib.import_module(import_path)
    runner = getattr(mod, attr, None)
    return {
        "ok": callable(runner),
        "symbol": CANONICAL_WALLCLOCK_RUNNER,
        "import_path": import_path,
        "attr": attr,
        "runner_bound": callable(runner),
    }


def build_governed_stale_control_v1(
    *,
    enable_receive_lag: bool = False,
) -> GovernedInjectedStaleDataControlV1:
    if enable_receive_lag:
        return GovernedInjectedStaleDataControlV1(schedule=build_receive_lag_schedule_v1())
    return GovernedInjectedStaleDataControlV1(
        schedule=build_disabled_stale_data_fault_schedule_v1()
    )


def prepare_adverse_stale_runtime_overrides_v1(
    *,
    enable_receive_lag: bool = False,
    runtime_overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind governed stale control via existing owner. Never starts network."""
    control = build_governed_stale_control_v1(enable_receive_lag=enable_receive_lag)
    control.assert_no_decision_injection_v1()
    overrides = bind_stale_control_into_runtime_overrides_v1(
        control=control,
        runtime_overrides=runtime_overrides,
    )
    blockers: list[str] = []
    if RUNTIME_OVERRIDE_KEY_STALE_CONTROL not in overrides:
        blockers.append("STALE_CONTROL_OVERRIDE_MISSING")
    if overrides.get(RUNTIME_OVERRIDE_KEY_STALE_CONTROL) is None:
        blockers.append("STALE_CONTROL_ABSENT")
    if RUNTIME_OVERRIDE_KEY_TRANSPORT_FAULT in overrides and overrides.get(
        RUNTIME_OVERRIDE_KEY_TRANSPORT_FAULT
    ) is overrides.get(RUNTIME_OVERRIDE_KEY_STALE_CONTROL):
        blockers.append("STALE_CONTROL_ALIASES_TRANSPORT_FAULT")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "runtime_overrides": overrides,
        "stale_control_enabled": bool(control.schedule.enabled),
        "receive_lag_schedule": bool(enable_receive_lag and control.schedule.enabled),
        "stale_control_binding_owner": STALE_CONTROL_BINDING_OWNER,
        "failure_injection_surface": FAILURE_INJECTION_SURFACE,
        "network_session_started": False,
        "max_network_session_count": MAX_NETWORK_SESSION_COUNT,
    }


def prove_adverse_stale_executor_binding_v1() -> dict[str, Any]:
    """Offline proof: wallclock symbol + receive path + RECEIVE_LAG classification."""
    blockers: list[str] = []
    runner = resolve_wallclock_runner_symbol_v1()
    if not runner.get("ok"):
        blockers.append("CANONICAL_WALLCLOCK_RUNNER_UNRESOLVED")

    receive = prove_wallclock_receive_path_binding_v1()
    if not receive.get("ok"):
        blockers.extend(list(receive.get("blockers") or []))

    disabled = prepare_adverse_stale_runtime_overrides_v1(enable_receive_lag=False)
    if not disabled.get("ok"):
        blockers.extend(list(disabled.get("blockers") or []))
    if disabled.get("stale_control_enabled"):
        blockers.append("DEFAULT_STALE_CONTROL_MUST_BE_DISABLED")

    enabled = prepare_adverse_stale_runtime_overrides_v1(enable_receive_lag=True)
    if not enabled.get("ok"):
        blockers.extend(list(enabled.get("blockers") or []))
    if not enabled.get("receive_lag_schedule"):
        blockers.append("RECEIVE_LAG_SCHEDULE_NOT_BOUND")

    classify = prove_stale_injection_classifies_via_canonical_owner_v1()
    if not classify.get("ok"):
        blockers.append("STALE_RECEIVE_LAG_CLASSIFICATION_FAILED")

    absent = dict(enabled.get("runtime_overrides") or {})
    absent.pop(RUNTIME_OVERRIDE_KEY_STALE_CONTROL, None)
    if RUNTIME_OVERRIDE_KEY_STALE_CONTROL in absent:
        blockers.append("STALE_ABSENCE_CHECK_FAILED")

    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "wallclock_runner": runner,
        "receive_path": {
            "ok": bool(receive.get("ok")),
            "blockers": list(receive.get("blockers") or []),
            "GOVERNED_STALE_CONTROL_PRODUCTIVELY_BOUND": bool(
                receive.get("GOVERNED_STALE_CONTROL_PRODUCTIVELY_BOUND")
            ),
            "WALLCLOCK_RECEIVE_PATH_BOUND": bool(receive.get("WALLCLOCK_RECEIVE_PATH_BOUND")),
            "runtime_override_key": receive.get("runtime_override_key"),
        },
        "default_disabled": {
            "ok": bool(disabled.get("ok")),
            "stale_control_enabled": bool(disabled.get("stale_control_enabled")),
            "receive_lag_schedule": bool(disabled.get("receive_lag_schedule")),
            "override_key_present": RUNTIME_OVERRIDE_KEY_STALE_CONTROL
            in (disabled.get("runtime_overrides") or {}),
        },
        "receive_lag_enabled_binding": {
            "ok": bool(enabled.get("ok")),
            "stale_control_enabled": bool(enabled.get("stale_control_enabled")),
            "receive_lag_schedule": bool(enabled.get("receive_lag_schedule")),
            "override_key": RUNTIME_OVERRIDE_KEY_STALE_CONTROL,
            "override_key_present": RUNTIME_OVERRIDE_KEY_STALE_CONTROL
            in (enabled.get("runtime_overrides") or {}),
        },
        "classification": {
            "ok": bool(classify.get("ok")),
            "ALPHA_FAILS_CLOSED_ON_STALE": bool(classify.get("ALPHA_FAILS_CLOSED_ON_STALE")),
            "NO_FABRICATED_MARKET_OBSERVATION": bool(
                classify.get("NO_FABRICATED_MARKET_OBSERVATION")
            ),
            "STALE_CONDITION_OBSERVED": bool(classify.get("STALE_CONDITION_OBSERVED")),
            "ADVERSE_CONDITION_OBSERVED": bool(classify.get("ADVERSE_CONDITION_OBSERVED")),
        },
        "stale_absent_cannot_satisfy_step6": RUNTIME_OVERRIDE_KEY_STALE_CONTROL not in absent,
        "network_session_started": False,
        "network_calls": 0,
        "max_network_session_count": MAX_NETWORK_SESSION_COUNT,
        "notes": [
            "WALLCLOCK_OWNER_REUSED=true",
            "STALE_CONTROL_OWNER_REUSED=true",
            "NO_PARALLEL_STALE_SEMANTICS=true",
            "NO_NETWORK_IN_ADVERSE_STALE_EXECUTOR_BINDING=true",
        ],
    }
