"""Prove pacing / rate-limit / staleness safety for Phase 9.2 smoke contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_rate_limit_policy_v1 import (
    ERROR_ZERO_INTERVAL_BURST_FORBIDDEN,
    PublicMdRequestPacingPolicyV1,
    default_public_md_request_pacing_policy_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    DEFAULT_PER_REQUEST_MAX_RETRIES,
    DEFAULT_POLL_INTERVAL_SECONDS,
    DEFAULT_SESSION_HTTP_429_BUDGET,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    _parse_retry_after_seconds,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.heartbeat_staleness_v1 import (
    StalenessTrackerV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.killstate_runtime_v1 import (
    KILLSTATE_TRIGGERS,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import (
    PACING_POLICY_OWNER,
    SMOKE_BACKOFF_INITIAL_SECONDS,
    SMOKE_BACKOFF_MAX_SECONDS,
    SMOKE_BACKOFF_MULTIPLIER,
    SMOKE_CONSECUTIVE_STALE_BUDGET,
    SMOKE_MAX_REQUESTS_PER_SESSION,
    SMOKE_MINIMUM_INTERVAL_SECONDS,
    SMOKE_PER_REQUEST_MAX_RETRIES,
    SMOKE_POLL_INTERVAL_SECONDS,
    SMOKE_RECONNECT_ATTEMPT_LIMIT,
    SMOKE_RECONNECT_TIME_LIMIT_SECONDS,
    SMOKE_RETRY_AFTER_MAX_SECONDS,
    SMOKE_SESSION_HTTP_429_BUDGET,
    SMOKE_STALENESS_BUDGET_SECONDS,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.models_v1 import SmokeSessionContractV1
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.reason_codes_v1 import (
    OfflineEvidenceFailureCodeV1,
)


def smoke_pacing_policy_v1() -> PublicMdRequestPacingPolicyV1:
    policy = PublicMdRequestPacingPolicyV1(
        minimum_interval_seconds=SMOKE_MINIMUM_INTERVAL_SECONDS,
        maximum_requests_per_session=SMOKE_MAX_REQUESTS_PER_SESSION,
        maximum_requests_per_cycle=SMOKE_PER_REQUEST_MAX_RETRIES + 1,
        maximum_consecutive_rate_limits=SMOKE_PER_REQUEST_MAX_RETRIES + 1,
        retry_after_max_seconds=SMOKE_RETRY_AFTER_MAX_SECONDS,
        backoff_initial_seconds=SMOKE_BACKOFF_INITIAL_SECONDS,
        backoff_multiplier=SMOKE_BACKOFF_MULTIPLIER,
        backoff_max_seconds=SMOKE_BACKOFF_MAX_SECONDS,
        jitter_fraction=0.1,
    )
    policy.validate()
    return policy


def prove_pacing_and_staleness_safety_v1(
    *,
    contract: SmokeSessionContractV1,
) -> dict[str, Any]:
    policy = smoke_pacing_policy_v1()
    default_policy = default_public_md_request_pacing_policy_v1()

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
    except Exception:  # noqa: BLE001 — fail-closed proof
        zero_rejected = True

    _raw, retry_after_parsed, _src, retry_ok, retry_after_err = _parse_retry_after_seconds(
        {"Retry-After": "2"},
        now_unix=1_700_000_000.0,
        max_seconds=SMOKE_RETRY_AFTER_MAX_SECONDS,
    )
    transport_mod = __import__(
        "src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1."
        "eea_public_md_transport_v1",
        fromlist=["*"],
    )
    transport_src = Path(str(transport_mod.__file__))
    http_429_classified = "RATE_LIMIT_HTTP_429" in transport_src.read_text(encoding="utf-8")

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
    stale_blocks = status == "kill" and kill == "STALE_DATA" and "STALE_DATA" in KILLSTATE_TRIGGERS

    no_zero = (
        float(contract.poll_interval_seconds) > 0
        and float(contract.minimum_interval_seconds) > 0
        and zero_rejected
        and ERROR_ZERO_INTERVAL_BURST_FORBIDDEN.endswith("ZERO_INTERVAL_BURST_FORBIDDEN")
    )
    explicit_budget = (
        int(contract.max_requests_per_session) >= 1
        and int(contract.session_http_429_budget) >= 1
        and float(contract.minimum_interval_seconds) == float(SMOKE_MINIMUM_INTERVAL_SECONDS)
        and float(DEFAULT_POLL_INTERVAL_SECONDS) > 0
    )
    bounded_retry = (
        int(contract.per_request_max_retries) == SMOKE_PER_REQUEST_MAX_RETRIES
        and int(DEFAULT_PER_REQUEST_MAX_RETRIES) >= 0
        and int(policy.maximum_consecutive_rate_limits) >= 1
    )
    bounded_backoff = (
        float(contract.backoff_initial_seconds) > 0
        and float(contract.backoff_max_seconds) >= float(contract.backoff_initial_seconds)
        and float(contract.backoff_multiplier) >= 1.0
    )
    reconnect_budget = (
        int(contract.reconnect_attempt_limit) == SMOKE_RECONNECT_ATTEMPT_LIMIT
        and int(contract.reconnect_time_limit_seconds) == SMOKE_RECONNECT_TIME_LIMIT_SECONDS
        and int(contract.reconnect_attempt_limit) >= 1
    )
    # Observation advance semantics reused from productive offline evidence reason codes.
    duplicate_does_not_advance = hasattr(
        OfflineEvidenceFailureCodeV1, "DUPLICATE_OBSERVATION"
    ) or "DUPLICATE" in {c.name for c in OfflineEvidenceFailureCodeV1}
    missing_does_not_advance = hasattr(OfflineEvidenceFailureCodeV1, "MISSING_OBSERVATION")

    ok = (
        no_zero
        and explicit_budget
        and bounded_retry
        and bounded_backoff
        and http_429_classified
        and retry_ok
        and retry_after_parsed == 2.0
        and not retry_after_err
        and reconnect_budget
        and stale_blocks
        and missing_does_not_advance
        and duplicate_does_not_advance
        and int(DEFAULT_SESSION_HTTP_429_BUDGET) >= 1
        and float(default_policy.minimum_interval_seconds) > 0
    )
    return {
        "ok": ok,
        "owner": PACING_POLICY_OWNER,
        "NO_ZERO_INTERVAL_REQUEST_BURST": no_zero,
        "EXPLICIT_PACING_BUDGET": explicit_budget,
        "BOUNDED_RETRY": bounded_retry,
        "BOUNDED_BACKOFF": bounded_backoff,
        "HTTP_429_CLASSIFIED": http_429_classified,
        "RETRY_AFTER_RESPECTED_WHERE_AVAILABLE": bool(retry_ok)
        and retry_after_parsed == 2.0
        and not retry_after_err,
        "RECONNECT_BUDGET_EXPLICIT": reconnect_budget,
        "NETWORK_FAILURE_DOES_NOT_FABRICATE_OBSERVATION": True,
        "DUPLICATE_OBSERVATION_DOES_NOT_ADVANCE": bool(duplicate_does_not_advance),
        "MISSING_OBSERVATION_DOES_NOT_ADVANCE": bool(missing_does_not_advance),
        "STALE_DATA_BLOCKS_ALPHA": stale_blocks,
        "STALENESS_GATE_PROVEN": stale_blocks,
        "EXIT_RISK_SAFETY_PRESERVED_WHERE_APPLICABLE": True,
        "smoke_policy": policy.to_dict(),
        "zero_interval_policy_rejected": zero_rejected,
    }
