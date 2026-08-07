"""Productive Step-7 multi-session campaign start-invoke edge.

This module owns the missing call-graph edge:

  campaign_may_start
  + Owner-GO + NETWORK_SESSION_GO + Real-TTY + Hidden-Confirm consume
  → strictly more than one run_productive_wallclock_session_v1(...)
    under TARGET_CAMPAIGN_CAPABILITY_ID
    with Public-MD fetcher binding and Step-7 harness/verifier handoff

Default permanent constants remain false. Tests inject wallclock_runner doubles.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, MutableMapping

from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_run_entrypoint_v1 import (
    run_productive_wallclock_session_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.real_http_fetcher_v1 import (
    make_real_eea_public_md_fetcher_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.constants_v1 import (
    CANONICAL_PUBLIC_MD_FETCHER,
    CANONICAL_WALLCLOCK_RUNNER,
    MULTI_SESSION_REQUIREMENT_EXPRESSION,
    TARGET_CAMPAIGN_CAPABILITY_ID,
    TARGET_SESSION_ID_PREFIX,
    is_target_campaign_capability_id_v1,
    multi_session_requirement_satisfied_v1,
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


def invoke_step7_productive_campaign_sessions_v1(
    *,
    planned_session_count: int,
    runtime_overrides: Mapping[str, Any] | None = None,
    wallclock_kwargs: Mapping[str, Any] | None = None,
    wallclock_runner: WallclockRunnerFn | None = None,
    campaign_start_state: MutableMapping[str, Any] | None = None,
    allow_real_network: bool = False,
    target_campaign_capability_id: str = TARGET_CAMPAIGN_CAPABILITY_ID,
) -> dict[str, Any]:
    """Invoke canonical wallclock runner once per planned session (count must be >1)."""
    blockers: list[str] = []
    notes = [
        f"TARGET_CAMPAIGN_CAPABILITY_ID={TARGET_CAMPAIGN_CAPABILITY_ID}",
        f"CANONICAL_WALLCLOCK_RUNNER={CANONICAL_WALLCLOCK_RUNNER}",
        f"MULTI_SESSION_REQUIREMENT_EXPRESSION={MULTI_SESSION_REQUIREMENT_EXPRESSION}",
        "PER_SESSION_WALLCLOCK_INVOKE_GUARD=true",
    ]
    if not is_target_campaign_capability_id_v1(target_campaign_capability_id):
        blockers.append("WRONG_CAPABILITY_ID")
        return {
            "ok": False,
            "blockers": blockers,
            "notes": notes,
            "wallclock_invoked_count": 0,
            "planned_session_count": int(planned_session_count),
            "completed_session_count": 0,
            "network_session_started": False,
            "public_md_fetcher_bound": False,
            "session_results": [],
        }

    if not multi_session_requirement_satisfied_v1(planned_session_count):
        blockers.append("MULTI_SESSION_REQUIREMENT_NOT_SATISFIED")
        return {
            "ok": False,
            "blockers": blockers,
            "notes": notes,
            "wallclock_invoked_count": 0,
            "planned_session_count": int(planned_session_count),
            "completed_session_count": 0,
            "network_session_started": False,
            "public_md_fetcher_bound": True,
            "session_results": [],
        }

    fetcher_proof = prove_public_md_fetcher_symbol_bound_v1()
    if not fetcher_proof.get("ok"):
        blockers.append("CANONICAL_PUBLIC_MD_FETCHER_UNRESOLVED")
        return {
            "ok": False,
            "blockers": blockers,
            "notes": notes,
            "wallclock_invoked_count": 0,
            "planned_session_count": int(planned_session_count),
            "completed_session_count": 0,
            "network_session_started": False,
            "public_md_fetcher_bound": False,
            "session_results": [],
        }

    state = campaign_start_state if campaign_start_state is not None else {}
    prior = int(state.get("wallclock_invoked_count") or 0)
    planned = int(planned_session_count)
    if prior > 0:
        blockers.append("CAMPAIGN_ALREADY_STARTED_FORBIDDEN")
        return {
            "ok": False,
            "blockers": blockers,
            "notes": notes + ["DUPLICATE_CAMPAIGN_START_GUARD=true"],
            "wallclock_invoked_count": prior,
            "planned_session_count": planned,
            "completed_session_count": int(state.get("completed_session_count") or 0),
            "network_session_started": bool(state.get("network_session_started")),
            "public_md_fetcher_bound": True,
            "session_results": list(state.get("session_results") or []),
        }

    overrides = dict(runtime_overrides or {})
    session_results: list[dict[str, Any]] = []
    invoked = 0

    for idx in range(1, planned + 1):
        session_id = f"{TARGET_SESSION_ID_PREFIX}_{idx:03d}"
        call_kwargs = dict(wallclock_kwargs or {})
        existing_overrides = dict(call_kwargs.get("runtime_overrides") or {})
        existing_overrides.update(overrides)
        call_kwargs["runtime_overrides"] = existing_overrides
        if "use_real_network" not in call_kwargs:
            call_kwargs["use_real_network"] = bool(allow_real_network)
        call_kwargs.setdefault("session_id", session_id)
        call_kwargs.setdefault("campaign_session_index", idx)
        call_kwargs.setdefault("campaign_planned_session_count", planned)

        state["wallclock_invoked_count"] = prior + idx
        state["start_reserved"] = True
        invoked = prior + idx

        if wallclock_runner is not None:
            notes.append(f"INJECTED_WALLCLOCK_RUNNER_USED_SESSION_{idx:03d}=true")
            result = wallclock_runner(**call_kwargs)
        else:
            notes.append(f"PRODUCTIVE_WALLCLOCK_CALLSITE_REACHED_SESSION_{idx:03d}=true")
            # PRODUCTIVE CALLSITE (AST-visible): Step-7 multi-session invoke edge.
            result = run_productive_wallclock_session_v1(**call_kwargs)

        session_results.append(
            {
                "session_index": idx,
                "session_id": session_id,
                "ok": True if not isinstance(result, Mapping) else bool(result.get("ok", True)),
                "result_type": type(result).__name__,
            }
        )

    state["completed_session_count"] = len(session_results)
    state["session_results"] = list(session_results)
    if wallclock_runner is not None:
        state["network_session_started"] = False
        notes.append("TEST_DOUBLE_INVOKE_DOES_NOT_CLAIM_REAL_NETWORK_SESSION=true")
    else:
        state["network_session_started"] = bool(allow_real_network and invoked > 0)

    ok = (
        not blockers
        and multi_session_requirement_satisfied_v1(len(session_results))
        and invoked == planned
    )
    return {
        "ok": ok,
        "blockers": blockers,
        "notes": notes,
        "wallclock_invoked_count": invoked,
        "planned_session_count": planned,
        "completed_session_count": len(session_results),
        "network_session_started": bool(state.get("network_session_started")),
        "public_md_fetcher_bound": True,
        "fetcher_proof": fetcher_proof,
        "runtime_overrides_keys": sorted(overrides.keys()),
        "session_results": session_results,
        "target_campaign_capability_id": TARGET_CAMPAIGN_CAPABILITY_ID,
        "multi_session_requirement_expression": MULTI_SESSION_REQUIREMENT_EXPRESSION,
    }
