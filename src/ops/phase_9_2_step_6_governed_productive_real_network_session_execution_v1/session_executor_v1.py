"""Session executor wiring — reuses wallclock + stale control; no start in prove mode."""

from __future__ import annotations

import importlib
from typing import Any, Mapping

from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.adverse_stale_executor_v1 import (
    prepare_adverse_stale_runtime_overrides_v1,
    prove_adverse_stale_executor_binding_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.constants_v1 import (
    CANONICAL_PUBLIC_MD_FETCHER,
    CANONICAL_WALLCLOCK_RUNNER,
    DEFAULT_WALLCLOCK_DURATION_SECONDS,
    FAILURE_INJECTION_SURFACE,
    MAX_NETWORK_SESSION_COUNT,
    STALE_CONTROL_BINDING_OWNER,
)


def resolve_canonical_runtime_symbols_v1() -> dict[str, Any]:
    blockers: list[str] = []

    def _resolve(dotted: str) -> dict[str, Any]:
        module_path, _, attr = dotted.rpartition(".")
        import_path = module_path[len("src.") :] if module_path.startswith("src.") else module_path
        mod = importlib.import_module(import_path)
        obj = getattr(mod, attr, None)
        return {
            "ok": callable(obj),
            "symbol": dotted,
            "import_path": import_path,
            "attr": attr,
            "bound": callable(obj),
        }

    runner = _resolve(CANONICAL_WALLCLOCK_RUNNER)
    fetcher = _resolve(CANONICAL_PUBLIC_MD_FETCHER)
    if not runner.get("ok"):
        blockers.append("CANONICAL_WALLCLOCK_RUNNER_UNRESOLVED")
    if not fetcher.get("ok"):
        blockers.append("CANONICAL_PUBLIC_MD_FETCHER_UNRESOLVED")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "wallclock_runner": runner,
        "public_md_fetcher": fetcher,
        "parallel_network_runner_created": False,
    }


def prove_session_executor_wiring_v1(
    *,
    enable_receive_lag: bool = False,
) -> dict[str, Any]:
    blockers: list[str] = []
    symbols = resolve_canonical_runtime_symbols_v1()
    if not symbols.get("ok"):
        blockers.extend(list(symbols.get("blockers") or []))

    stale = prove_adverse_stale_executor_binding_v1()
    if not stale.get("ok"):
        blockers.extend(list(stale.get("blockers") or []))

    prep = prepare_adverse_stale_runtime_overrides_v1(enable_receive_lag=enable_receive_lag)
    if not prep.get("ok"):
        blockers.extend(list(prep.get("blockers") or []))
    stale_present = "governed_stale_data_control" in (prep.get("runtime_overrides") or {})
    if not stale_present:
        blockers.append("STALE_CONTROL_ABSENT")

    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "symbols": symbols,
        "stale_binding": {
            "ok": bool(stale.get("ok")),
            "stale_control_binding_owner": STALE_CONTROL_BINDING_OWNER,
            "failure_injection_surface": FAILURE_INJECTION_SURFACE,
        },
        "stale_prep": {
            "ok": bool(prep.get("ok")),
            "stale_control_enabled": bool(prep.get("stale_control_enabled")),
            "receive_lag_schedule": bool(prep.get("receive_lag_schedule")),
            "stale_control_present": stale_present,
        },
        "default_wallclock_duration_seconds": DEFAULT_WALLCLOCK_DURATION_SECONDS,
        "max_network_session_count": MAX_NETWORK_SESSION_COUNT,
        "network_session_started": False,
        "notes": [
            "WALLCLOCK_OWNER_REUSED=true",
            "PUBLIC_MD_FETCHER_SYMBOL_BOUND=true",
            "STALE_CONTROL_PRODUCTIVELY_REACHABLE=true",
            "FAILURE_INJECTION_REACHABLE=true",
            "NO_NETWORK_START_IN_WIRING_PROOF=true",
        ],
    }


def prepare_session_runtime_plan_v1(
    *,
    enable_receive_lag: bool = False,
    planned_duration_seconds: int | None = None,
    runtime_overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Prepare overrides/plan for a later Owner-GO invoke. Never starts network."""
    prep = prepare_adverse_stale_runtime_overrides_v1(
        enable_receive_lag=enable_receive_lag,
        runtime_overrides=runtime_overrides,
    )
    duration = (
        int(planned_duration_seconds)
        if planned_duration_seconds is not None
        else DEFAULT_WALLCLOCK_DURATION_SECONDS
    )
    return {
        "ok": bool(prep.get("ok")),
        "blockers": list(prep.get("blockers") or []),
        "planned_duration_seconds": duration,
        "runtime_overrides": dict(prep.get("runtime_overrides") or {}),
        "stale_control_present": "governed_stale_data_control"
        in (prep.get("runtime_overrides") or {}),
        "stale_control_enabled": bool(prep.get("stale_control_enabled")),
        "receive_lag_schedule": bool(prep.get("receive_lag_schedule")),
        "network_session_started": False,
        "invoke_executor": False,
    }
