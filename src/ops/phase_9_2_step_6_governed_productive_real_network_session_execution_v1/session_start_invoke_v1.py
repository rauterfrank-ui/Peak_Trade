"""Productive Step-6 Real-Network start-invoke edge (exactly-once wallclock call).

This module owns the missing call-graph edge:

  session_execution_may_start
  + Owner-GO + NETWORK_SESSION_GO + Real-TTY + Hidden-Confirm consume
  → exactly one run_productive_wallclock_session_v1(...)
    with governed_stale_data_control overrides
    and canonical Public-MD fetcher binding

Default permanent constants remain false. Callers must pass ephemeral GO flags.
Tests inject wallclock_runner doubles; this implementation capability never
starts a real Public-MD network session from prove/materialize paths.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, MutableMapping

from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_run_entrypoint_v1 import (
    run_productive_wallclock_session_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.real_http_fetcher_v1 import (
    make_real_eea_public_md_fetcher_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.constants_v1 import (
    CANONICAL_PUBLIC_MD_FETCHER,
    CANONICAL_WALLCLOCK_RUNNER,
    MAX_NETWORK_SESSION_COUNT,
    TARGET_SESSION_CAPABILITY_ID,
)

WallclockRunnerFn = Callable[..., Any]


def prove_public_md_fetcher_symbol_bound_v1() -> dict[str, Any]:
    return {
        "ok": callable(make_real_eea_public_md_fetcher_v1),
        "symbol": CANONICAL_PUBLIC_MD_FETCHER,
        "attr": "make_real_eea_public_md_fetcher_v1",
        "bound": callable(make_real_eea_public_md_fetcher_v1),
        "parallel_fetcher_created": False,
    }


def invoke_step6_productive_wallclock_once_v1(
    *,
    runtime_overrides: Mapping[str, Any],
    wallclock_kwargs: Mapping[str, Any] | None = None,
    wallclock_runner: WallclockRunnerFn | None = None,
    session_start_state: MutableMapping[str, Any] | None = None,
    allow_real_network: bool = False,
    target_session_capability_id: str = TARGET_SESSION_CAPABILITY_ID,
) -> dict[str, Any]:
    """Invoke the canonical wallclock runner exactly once under start-state guard.

    When ``wallclock_runner`` is provided (tests), that callable is used and the
    productive symbol is not executed. When omitted, the productive callsite
    ``run_productive_wallclock_session_v1`` is used exactly once.
    """
    blockers: list[str] = []
    notes = [
        f"TARGET_SESSION_CAPABILITY_ID={TARGET_SESSION_CAPABILITY_ID}",
        f"CANONICAL_WALLCLOCK_RUNNER={CANONICAL_WALLCLOCK_RUNNER}",
        "EXACTLY_ONCE_SESSION_START_GUARD=true",
    ]
    if target_session_capability_id != TARGET_SESSION_CAPABILITY_ID:
        blockers.append("WRONG_CAPABILITY_ID")
        return {
            "ok": False,
            "blockers": blockers,
            "notes": notes,
            "wallclock_invoked_count": 0,
            "network_session_started": False,
            "stale_control_present": False,
            "public_md_fetcher_bound": False,
            "result": None,
        }

    state = session_start_state if session_start_state is not None else {}
    prior = int(state.get("wallclock_invoked_count") or 0)
    if prior >= MAX_NETWORK_SESSION_COUNT:
        blockers.append("DUPLICATE_SESSION_START_FORBIDDEN")
        notes.append("EXACTLY_ONCE_GUARD_BLOCKED_SECOND_INVOKE=true")
        return {
            "ok": False,
            "blockers": blockers,
            "notes": notes,
            "wallclock_invoked_count": prior,
            "network_session_started": bool(state.get("network_session_started")),
            "stale_control_present": "governed_stale_data_control" in dict(runtime_overrides),
            "public_md_fetcher_bound": True,
            "result": None,
        }

    overrides = dict(runtime_overrides or {})
    stale_present = "governed_stale_data_control" in overrides
    if not stale_present:
        blockers.append("STALE_CONTROL_ABSENT")
        return {
            "ok": False,
            "blockers": blockers,
            "notes": notes,
            "wallclock_invoked_count": prior,
            "network_session_started": False,
            "stale_control_present": False,
            "public_md_fetcher_bound": True,
            "result": None,
        }

    fetcher_proof = prove_public_md_fetcher_symbol_bound_v1()
    if not fetcher_proof.get("ok"):
        blockers.append("CANONICAL_PUBLIC_MD_FETCHER_UNRESOLVED")
        return {
            "ok": False,
            "blockers": blockers,
            "notes": notes,
            "wallclock_invoked_count": prior,
            "network_session_started": False,
            "stale_control_present": True,
            "public_md_fetcher_bound": False,
            "result": None,
        }

    call_kwargs = dict(wallclock_kwargs or {})
    existing_overrides = dict(call_kwargs.get("runtime_overrides") or {})
    existing_overrides.update(overrides)
    call_kwargs["runtime_overrides"] = existing_overrides
    if "use_real_network" not in call_kwargs:
        call_kwargs["use_real_network"] = bool(allow_real_network)

    # Mark start reservation before invoke to prevent recursive/duplicate starts.
    state["wallclock_invoked_count"] = prior + 1
    state["start_reserved"] = True

    if wallclock_runner is not None:
        notes.append("INJECTED_WALLCLOCK_RUNNER_USED=true")
        notes.append("PRODUCTIVE_SYMBOL_NOT_EXECUTED_UNDER_TEST_DOUBLE=true")
        result = wallclock_runner(**call_kwargs)
    else:
        notes.append("PRODUCTIVE_WALLCLOCK_CALLSITE_REACHED=true")
        # PRODUCTIVE CALLSITE (AST-visible): exactly one Step-6 productive invoke edge.
        result = run_productive_wallclock_session_v1(**call_kwargs)

    started = False
    if isinstance(result, Mapping):
        started = bool(
            result.get("network_session_started") or result.get("NETWORK_SESSION_STARTED")
        )
    elif hasattr(result, "ok"):
        # ProductiveRunGateResultV1 / similar — network start is caller-claimed separately.
        started = bool(allow_real_network and getattr(result, "ok", False))
    state["network_session_started"] = bool(started) if allow_real_network else False

    return {
        "ok": not blockers,
        "blockers": blockers,
        "notes": notes,
        "wallclock_invoked_count": int(state["wallclock_invoked_count"]),
        "network_session_started": bool(state.get("network_session_started")),
        "stale_control_present": True,
        "public_md_fetcher_bound": True,
        "runtime_overrides_keys": sorted(existing_overrides.keys()),
        "fetcher_proof": fetcher_proof,
        "result": result,
        "target_session_capability_id": TARGET_SESSION_CAPABILITY_ID,
    }
