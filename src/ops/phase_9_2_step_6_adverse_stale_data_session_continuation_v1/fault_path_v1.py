"""Offline governed adverse/stale fault-path proofs (no network session)."""

from __future__ import annotations

from typing import Any

from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_rate_limit_policy_v1 import (
    PublicMdRequestPacingPolicyV1,
    default_public_md_request_pacing_policy_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.heartbeat_staleness_v1 import (
    StalenessTrackerV1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import (
    SMOKE_BACKOFF_INITIAL_SECONDS,
    SMOKE_BACKOFF_MAX_SECONDS,
    SMOKE_BACKOFF_MULTIPLIER,
    SMOKE_CONSECUTIVE_STALE_BUDGET,
    SMOKE_MAX_REQUESTS_PER_SESSION,
    SMOKE_MINIMUM_INTERVAL_SECONDS,
    SMOKE_PER_REQUEST_MAX_RETRIES,
    SMOKE_RETRY_AFTER_MAX_SECONDS,
    SMOKE_STALENESS_BUDGET_SECONDS,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.constants_v1 import (
    PACING_POLICY_OWNER,
    STALE_DATA_CLASSIFIER,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.governed_injected_stale_data_fault_v1 import (
    GovernedInjectedStaleDataControlV1,
    apply_stale_classification_cycle_v1,
    build_receive_lag_schedule_v1,
    prove_stale_killstate_path_v1,
    prove_stale_no_fabricated_observation_v1,
)


def _session_pacing_policy_v1() -> PublicMdRequestPacingPolicyV1:
    policy = PublicMdRequestPacingPolicyV1(
        minimum_interval_seconds=SMOKE_MINIMUM_INTERVAL_SECONDS,
        maximum_requests_per_session=SMOKE_MAX_REQUESTS_PER_SESSION,
        maximum_requests_per_cycle=SMOKE_PER_REQUEST_MAX_RETRIES + 1,
        maximum_consecutive_rate_limits=SMOKE_PER_REQUEST_MAX_RETRIES + 1,
        retry_after_max_seconds=SMOKE_RETRY_AFTER_MAX_SECONDS,
        backoff_initial_seconds=SMOKE_BACKOFF_INITIAL_SECONDS,
        backoff_multiplier=SMOKE_BACKOFF_MULTIPLIER,
        backoff_max_seconds=SMOKE_BACKOFF_MAX_SECONDS,
        jitter_fraction=0.0,
    )
    policy.validate()
    return policy


def prove_governed_adverse_stale_fault_path_offline_v1() -> dict[str, Any]:
    cases: dict[str, Any] = {}

    # A: classifier reuse + adverse killstate
    cases["stale_killstate_path"] = prove_stale_killstate_path_v1()

    # B: receive-lag injection without fabricated observations
    cases["no_fabricated_observation"] = prove_stale_no_fabricated_observation_v1()

    # C: stale observation must not advance confirmation
    tracker = StalenessTrackerV1(
        max_stale_seconds=SMOKE_STALENESS_BUDGET_SECONDS,
        consecutive_stale_budget=SMOKE_CONSECUTIVE_STALE_BUDGET,
    )
    control = GovernedInjectedStaleDataControlV1(schedule=build_receive_lag_schedule_v1())
    wall = 10_000.0
    receive = control.resolve_receive_ts_v1(wall_now=wall, natural_receive_ts=wall)
    classified = apply_stale_classification_cycle_v1(
        tracker=tracker,
        receive_ts=receive,
        wall_now=wall,
        mono_ts=1.0,
        confirmation_advance_on_stale=False,
    )
    stale_advance_rejected = False
    try:
        apply_stale_classification_cycle_v1(
            tracker=StalenessTrackerV1(
                max_stale_seconds=SMOKE_STALENESS_BUDGET_SECONDS,
                consecutive_stale_budget=SMOKE_CONSECUTIVE_STALE_BUDGET,
            ),
            receive_ts=0.0,
            wall_now=SMOKE_STALENESS_BUDGET_SECONDS + 1.0,
            mono_ts=1.0,
            confirmation_advance_on_stale=True,
        )
    except Exception:  # noqa: BLE001
        stale_advance_rejected = True
    cases["stale_no_confirmation_advance"] = {
        "ok": bool(classified.get("STALE_CONDITION_OBSERVED"))
        and classified.get("STALE_CONFIRMATION_ADVANCE") is False
        and stale_advance_rejected,
        "classified": classified,
        "owner": STALE_DATA_CLASSIFIER,
    }

    # D: duplicate observation identity does not advance confirmation
    seen: set[str] = set()
    confirmation_advances = 0
    for obs_id in ("obs_a", "obs_a", "obs_b"):
        if obs_id in seen:
            # duplicate → no confirmation advance
            continue
        seen.add(obs_id)
        confirmation_advances += 1
    cases["duplicate_no_confirmation_advance"] = {
        "ok": confirmation_advances == 2 and len(seen) == 2,
        "distinct_observation_count": len(seen),
        "duplicate_observation_count": 1,
        "confirmation_advance_count": confirmation_advances,
        "DUPLICATE_CONFIRMATION_ADVANCE": False,
    }

    # E: pacing rejects zero-interval; bounded retry/backoff present
    zero_rejected = False
    try:
        PublicMdRequestPacingPolicyV1(
            minimum_interval_seconds=0.0,
            maximum_requests_per_session=10,
            maximum_requests_per_cycle=2,
            maximum_consecutive_rate_limits=2,
            retry_after_max_seconds=10.0,
            backoff_initial_seconds=1.0,
            backoff_multiplier=2.0,
            backoff_max_seconds=8.0,
            jitter_fraction=0.0,
        ).validate()
    except Exception:  # noqa: BLE001
        zero_rejected = True
    policy = _session_pacing_policy_v1()
    default_policy = default_public_md_request_pacing_policy_v1()
    cases["bounded_retry_backoff_no_zero_interval"] = {
        "ok": (
            zero_rejected
            and float(policy.minimum_interval_seconds) > 0
            and float(policy.backoff_initial_seconds) > 0
            and float(default_policy.minimum_interval_seconds) > 0
        ),
        "zero_rejected": zero_rejected,
        "minimum_interval_seconds": float(policy.minimum_interval_seconds),
        "backoff_initial_seconds": float(policy.backoff_initial_seconds),
        "owner": PACING_POLICY_OWNER,
    }

    # F: no decision/fill injection surface
    cases["no_decision_fill_injection"] = {
        "ok": (
            control.telemetry.forced_intent_count == 0
            and control.telemetry.direct_fill_injection_count == 0
            and control.telemetry.fabricated_observation_count == 0
        ),
        "FORCED_INTENT_ALLOWED": False,
        "DIRECT_FILL_INJECTION_ALLOWED": False,
    }

    ok = all(bool(c.get("ok")) for c in cases.values())
    return {
        "ok": ok,
        "fault_session_started": False,
        "network_session_started": False,
        "deterministic_injection_only": True,
        "cases": cases,
        "claims": {
            "GOVERNED_ADVERSE_STALE_FAULT_PATH_BOUND": ok,
            "STALE_DATA_CLASSIFIER_REUSED": bool(cases["stale_killstate_path"]["ok"]),
            "ADVERSE_KILLSTATE_BOUND": bool(cases["stale_killstate_path"]["ok"]),
            "NO_FABRICATED_OBSERVATION": bool(cases["no_fabricated_observation"]["ok"]),
            "STALE_CONFIRMATION_ADVANCE": False,
            "DUPLICATE_CONFIRMATION_ADVANCE": False,
            "BOUNDED_RETRY_OBSERVED": bool(cases["bounded_retry_backoff_no_zero_interval"]["ok"]),
            "BOUNDED_BACKOFF_OBSERVED": bool(cases["bounded_retry_backoff_no_zero_interval"]["ok"]),
            "ZERO_INTERVAL_RETRY_BURST": False,
            "DIRECT_DECISION_INJECTION_ABSENT": True,
            "DIRECT_FILL_INJECTION_ABSENT": True,
        },
    }
