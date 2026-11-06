"""Offline governed fault-path proofs for rate-limit/reconnect binding.

Reuses canonical transport, pacing, reconnect classification, and staleness
owners. Deterministic injected fetcher only — no real network, no fault session
execution, no venue-limit probing.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_rate_limit_policy_v1 import (
    PublicMdRequestPacingPolicyV1,
    default_public_md_request_pacing_policy_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportError,
    EeaPublicMdTransportV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.heartbeat_staleness_v1 import (
    StalenessTrackerV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.killstate_runtime_v1 import (
    KILLSTATE_TRIGGERS,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_state_machine_v1 import (
    WallclockSessionState,
    assert_transition_allowed,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.error_classes_v1 import (
    classify_transport_message_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    EEA_TRANSPORT_OWNER,
    PACING_POLICY_OWNER,
    RATE_LIMIT_METRIC_OWNER,
    SESSION_RUNTIME_OWNER,
    STALENESS_OWNER,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import (
    SMOKE_BACKOFF_INITIAL_SECONDS,
    SMOKE_BACKOFF_MAX_SECONDS,
    SMOKE_BACKOFF_MULTIPLIER,
    SMOKE_CONSECUTIVE_STALE_BUDGET,
    SMOKE_MAX_REQUESTS_PER_SESSION,
    SMOKE_MINIMUM_INTERVAL_SECONDS,
    SMOKE_PER_REQUEST_MAX_RETRIES,
    SMOKE_RECONNECT_ATTEMPT_LIMIT,
    SMOKE_RETRY_AFTER_MAX_SECONDS,
    SMOKE_SESSION_HTTP_429_BUDGET,
    SMOKE_STALENESS_BUDGET_SECONDS,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.rate_limit_metric_v1 import (
    compute_rate_limit_event_count_v1,
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


def _ok_body() -> bytes:
    return json.dumps({"code": "0", "data": [{"ts": "1700000000000"}]}).encode("utf-8")


def prove_governed_fault_path_offline_v1() -> dict[str, Any]:
    """Deterministic offline proofs that bind Step-4 fault surfaces without executing a session."""
    cases: dict[str, Any] = {}
    sleeps: list[float] = []

    def sleep_recorder(seconds: float) -> None:
        sleeps.append(float(seconds))

    # --- Case A: 429 + Retry-After → classified, bounded backoff, no zero-interval ---
    call_n = {"n": 0}

    def fetcher_429_then_ok(
        url: str, method: str, headers: Mapping[str, str], timeout: float
    ) -> tuple[int, bytes, Mapping[str, str]]:
        del method, headers, timeout
        call_n["n"] += 1
        if call_n["n"] == 1:
            return 429, b"{}", {"Retry-After": "2"}
        return 200, _ok_body(), {"Content-Type": "application/json"}

    policy = _session_pacing_policy_v1()
    transport = EeaPublicMdTransportV1(
        fetcher=fetcher_429_then_ok,
        max_retries=SMOKE_PER_REQUEST_MAX_RETRIES,
        session_http_429_budget=SMOKE_SESSION_HTTP_429_BUDGET,
        sleep=sleep_recorder,
        environ={"PATH": "/usr/bin", "HOME": "/tmp"},
        rate_limit_policy=policy,
        jitter_unit_fn=lambda _i: 0.0,
    )
    transport.open()
    result = transport.get_json("/api/v5/public/time", {})
    cases["http_429_retry_after_backoff"] = {
        "ok": (
            result.status == 200
            and transport.http_429_count == 1
            and len(sleeps) == 1
            and sleeps[0] == 2.0
            and sleeps[0] > 0.0
        ),
        "http_429_count": transport.http_429_count,
        "scheduled_backoff_seconds": sleeps[0] if sleeps else None,
        "owner": EEA_TRANSPORT_OWNER,
    }

    # --- Case B: session 429 budget exceeded ---
    def fetcher_always_429(
        url: str, method: str, headers: Mapping[str, str], timeout: float
    ) -> tuple[int, bytes, Mapping[str, str]]:
        del url, method, headers, timeout
        return 429, b"{}", {"Retry-After": "1"}

    budget_transport = EeaPublicMdTransportV1(
        fetcher=fetcher_always_429,
        max_retries=0,
        session_http_429_budget=1,
        sleep=lambda _s: None,
        environ={"PATH": "/usr/bin", "HOME": "/tmp"},
        rate_limit_policy=policy,
        jitter_unit_fn=lambda _i: 0.0,
    )
    budget_transport.open()
    # First 429 counts; second exceeds budget=1
    budget_err = ""
    try:
        budget_transport.get_json("/api/v5/public/time", {})
    except EeaPublicMdTransportError as exc:
        budget_err = str(exc)
    try:
        budget_transport.get_json("/api/v5/public/time", {})
    except EeaPublicMdTransportError as exc:
        budget_err = str(exc)
    cases["http_429_session_budget_exceeded"] = {
        "ok": "RATE_LIMIT_SESSION_BUDGET_EXCEEDED" in budget_err,
        "error": budget_err,
        "http_429_count": budget_transport.http_429_count,
        "owner": EEA_TRANSPORT_OWNER,
    }

    # --- Case C: transport classification reconnectable for rate-limit / fetch failures ---
    cls_a, reconnectable_a = classify_transport_message_v1(
        "FETCH_FAILED:RATE_LIMIT_RETRY_EXHAUSTED:RATE_LIMIT_HTTP_429"
    )
    cls_b, reconnectable_b = classify_transport_message_v1("RATE_LIMIT_HTTP_429")
    cases["rate_limit_classified_reconnectable"] = {
        "ok": reconnectable_a and reconnectable_b and cls_a == "TRANSPORT_FAILURE",
        "class_a": cls_a,
        "class_b": cls_b,
        "reconnectable_a": reconnectable_a,
        "reconnectable_b": reconnectable_b,
        "owner": SESSION_RUNTIME_OWNER,
    }

    # --- Case D: state machine RUNNING ↔ RECONNECTING ---
    reconnect_ok = True
    try:
        assert_transition_allowed(
            from_state=WallclockSessionState.RUNNING,
            to_state=WallclockSessionState.RECONNECTING,
        )
        assert_transition_allowed(
            from_state=WallclockSessionState.RECONNECTING,
            to_state=WallclockSessionState.RUNNING,
        )
    except Exception:  # noqa: BLE001
        reconnect_ok = False
    cases["reconnect_state_transitions"] = {
        "ok": reconnect_ok and SMOKE_RECONNECT_ATTEMPT_LIMIT >= 1,
        "reconnect_attempt_limit": SMOKE_RECONNECT_ATTEMPT_LIMIT,
        "owner": SESSION_RUNTIME_OWNER,
    }

    # --- Case E: staleness gate → STALE_DATA ---
    stale = StalenessTrackerV1(
        max_stale_seconds=SMOKE_STALENESS_BUDGET_SECONDS,
        consecutive_stale_budget=SMOKE_CONSECUTIVE_STALE_BUDGET,
    )
    status = "ok"
    kill = None
    for _ in range(SMOKE_CONSECUTIVE_STALE_BUDGET + 1):
        status, kill = stale.observe(
            receive_ts=0.0,
            wall_now=SMOKE_STALENESS_BUDGET_SECONDS + 1.0,
            mono_ts=1.0,
        )
    cases["stale_data_gate"] = {
        "ok": status == "kill" and kill == "STALE_DATA" and "STALE_DATA" in KILLSTATE_TRIGGERS,
        "status": status,
        "kill": kill,
        "owner": STALENESS_OWNER,
    }

    # --- Case F: rate-limit metric counts structured events only ---
    payloads = [
        {"error_code": "RATE_LIMIT_HTTP_429"},
        {"note": "contains 429 substring but not classified"},
        {"http_status": 429},
    ]
    counted = compute_rate_limit_event_count_v1(payloads=payloads)
    cases["rate_limit_metric_hygiene"] = {
        "ok": counted == 2,
        "count": counted,
        "owner": RATE_LIMIT_METRIC_OWNER,
    }

    # --- Case G: pacing policy rejects zero-interval; default policy positive ---
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
    default_policy = default_public_md_request_pacing_policy_v1()
    cases["pacing_no_zero_interval"] = {
        "ok": zero_rejected and float(default_policy.minimum_interval_seconds) > 0,
        "zero_rejected": zero_rejected,
        "owner": PACING_POLICY_OWNER,
    }

    ok = all(bool(c.get("ok")) for c in cases.values())
    return {
        "ok": ok,
        "fault_session_started": False,
        "network_session_started": False,
        "deterministic_injection_only": True,
        "cases": cases,
        "claims": {
            "GOVERNED_FAULT_PATH_BOUND": ok,
            "HTTP_429_CLASSIFIED": bool(cases["http_429_retry_after_backoff"]["ok"]),
            "BOUNDED_BACKOFF_USED": bool(cases["http_429_retry_after_backoff"]["ok"]),
            "ZERO_INTERVAL_RETRY": False,
            "HTTP_429_BUDGET_ENFORCED": bool(cases["http_429_session_budget_exceeded"]["ok"]),
            "RECONNECT_STATE_BOUND": bool(cases["reconnect_state_transitions"]["ok"]),
            "STALE_DATA_GATE_BOUND": bool(cases["stale_data_gate"]["ok"]),
            "RATE_LIMIT_METRIC_BOUND": bool(cases["rate_limit_metric_hygiene"]["ok"]),
            "NO_IMPROVISED_HARNESS": True,
        },
    }
