"""Load and validate the adverse/stale-data session contract (no network)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import (
    SMOKE_BACKOFF_INITIAL_SECONDS,
    SMOKE_BACKOFF_MAX_SECONDS,
    SMOKE_BACKOFF_MULTIPLIER,
    SMOKE_CONSECUTIVE_STALE_BUDGET,
    SMOKE_HEARTBEAT_LOSS_SECONDS,
    SMOKE_HEARTBEAT_SECONDS,
    SMOKE_MAX_GAP_SECONDS,
    SMOKE_MINIMUM_INTERVAL_SECONDS,
    SMOKE_PER_REQUEST_MAX_RETRIES,
    SMOKE_POLL_INTERVAL_SECONDS,
    SMOKE_RECONNECT_ATTEMPT_LIMIT,
    SMOKE_RECONNECT_TIME_LIMIT_SECONDS,
    SMOKE_RETRY_AFTER_MAX_SECONDS,
    SMOKE_SESSION_HTTP_429_BUDGET,
    SMOKE_STALENESS_BUDGET_SECONDS,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    DEFAULT_WALLCLOCK_DURATION_SECONDS,
    MAX_WALLCLOCK_DURATION_SECONDS,
    MIN_WALLCLOCK_DURATION_SECONDS,
    SESSION_CONTRACT_RELATIVE_PATH,
    SESSION_LADDER_STEP,
    TARGET_SESSION_ID,
    repo_root_v1,
)


class SessionContractError(ValueError):
    """Fail-closed session contract error."""


def load_session_contract_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    path = root / SESSION_CONTRACT_RELATIVE_PATH
    if not path.is_file():
        raise SessionContractError("SESSION_CONTRACT_MISSING")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SessionContractError("SESSION_CONTRACT_NOT_OBJECT")
    return raw


def validate_session_contract_v1(contract: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    if str(contract.get("capability_id") or "") != CAPABILITY_ID:
        gaps.append("CAPABILITY_ID_MISMATCH")
    if str(contract.get("session_id") or "") != TARGET_SESSION_ID:
        gaps.append("SESSION_ID_MISMATCH")
    if str(contract.get("session_ladder_step") or "") != SESSION_LADDER_STEP:
        gaps.append("SESSION_LADDER_STEP_MISMATCH")
    if str(contract.get("canonical_instrument_id") or "") != CANONICAL_INSTRUMENT_ID:
        gaps.append("INSTRUMENT_MISMATCH")
    if bool(contract.get("network_session_authorized")):
        gaps.append("NETWORK_SESSION_PREAUTHORIZED")
    if bool(contract.get("authorization_issuance_authorized")):
        gaps.append("AUTH_ISSUANCE_PREAUTHORIZED")
    if bool(contract.get("authorization_consumption_authorized")):
        gaps.append("AUTH_CONSUMPTION_PREAUTHORIZED")
    if bool(contract.get("runtime_start_authorized")):
        gaps.append("RUNTIME_START_PREAUTHORIZED")
    if bool(contract.get("fault_session_execution_authorized")):
        gaps.append("FAULT_SESSION_PREAUTHORIZED")

    min_d = int(contract.get("min_session_duration_seconds") or 0)
    default_d = int(contract.get("default_session_duration_seconds") or 0)
    max_d = int(contract.get("max_session_duration_seconds") or 0)
    if min_d != MIN_WALLCLOCK_DURATION_SECONDS:
        gaps.append("MIN_DURATION_MISMATCH")
    if default_d != DEFAULT_WALLCLOCK_DURATION_SECONDS:
        gaps.append("DEFAULT_DURATION_MISMATCH")
    if max_d != MAX_WALLCLOCK_DURATION_SECONDS:
        gaps.append("MAX_DURATION_MISMATCH")
    if not (min_d <= default_d <= max_d):
        gaps.append("DURATION_BOUNDS_INCONSISTENT")
    if str(contract.get("clock_authority_duration") or "") != "MONOTONIC":
        gaps.append("DURATION_CLOCK_AUTHORITY_MUST_BE_MONOTONIC")

    if float(contract.get("minimum_interval_seconds") or 0) <= 0:
        gaps.append("ZERO_INTERVAL_BURST")
    if float(contract.get("poll_interval_seconds") or 0) <= 0:
        gaps.append("ZERO_POLL_INTERVAL")
    if float(contract.get("backoff_initial_seconds") or 0) <= 0:
        gaps.append("ZERO_BACKOFF_FORBIDDEN")

    expected = {
        "poll_interval_seconds": SMOKE_POLL_INTERVAL_SECONDS,
        "minimum_interval_seconds": SMOKE_MINIMUM_INTERVAL_SECONDS,
        "reconnect_attempt_limit": SMOKE_RECONNECT_ATTEMPT_LIMIT,
        "reconnect_time_limit_seconds": SMOKE_RECONNECT_TIME_LIMIT_SECONDS,
        "per_request_max_retries": SMOKE_PER_REQUEST_MAX_RETRIES,
        "session_http_429_budget": SMOKE_SESSION_HTTP_429_BUDGET,
        "backoff_initial_seconds": SMOKE_BACKOFF_INITIAL_SECONDS,
        "backoff_multiplier": SMOKE_BACKOFF_MULTIPLIER,
        "backoff_max_seconds": SMOKE_BACKOFF_MAX_SECONDS,
        "retry_after_max_seconds": SMOKE_RETRY_AFTER_MAX_SECONDS,
        "staleness_budget_seconds": SMOKE_STALENESS_BUDGET_SECONDS,
        "consecutive_stale_budget": SMOKE_CONSECUTIVE_STALE_BUDGET,
        "heartbeat_seconds": SMOKE_HEARTBEAT_SECONDS,
        "heartbeat_loss_seconds": SMOKE_HEARTBEAT_LOSS_SECONDS,
        "max_gap_seconds": SMOKE_MAX_GAP_SECONDS,
    }
    for key, want in expected.items():
        got = contract.get(key)
        if isinstance(want, float):
            if float(got) != float(want):
                gaps.append(f"BUDGET_DRIFT:{key}")
        else:
            if int(got) != int(want):
                gaps.append(f"BUDGET_DRIFT:{key}")

    reuses = contract.get("reuses") if isinstance(contract.get("reuses"), dict) else {}
    for required in (
        "staleness",
        "killstate",
        "session_runtime",
        "pacing_policy",
        "eea_transport",
        "wallclock_runner",
    ):
        if not reuses.get(required):
            gaps.append(f"REUSE_MISSING:{required}")

    fault = (
        contract.get("fault_injection") if isinstance(contract.get("fault_injection"), dict) else {}
    )
    if str(fault.get("allowed_kinds") or "") and "RECEIVE_LAG" not in str(
        fault.get("allowed_kinds")
    ):
        gaps.append("FAULT_KINDS_MUST_INCLUDE_RECEIVE_LAG")
    if bool(fault.get("forced_intent_allowed")):
        gaps.append("FORCED_INTENT_MUST_REMAIN_FALSE")
    if bool(fault.get("direct_fill_injection_allowed")):
        gaps.append("DIRECT_FILL_INJECTION_MUST_REMAIN_FALSE")
    if bool(fault.get("fabricated_observation_allowed")):
        gaps.append("FABRICATED_OBSERVATION_MUST_REMAIN_FALSE")

    return gaps


def load_and_validate_session_contract_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    contract = load_session_contract_v1(repo_root=repo_root)
    gaps = validate_session_contract_v1(contract)
    if gaps:
        raise SessionContractError("SESSION_CONTRACT_INVALID:" + ",".join(gaps))
    return contract


def validate_planned_duration_v1(planned_duration_seconds: int) -> list[str]:
    gaps: list[str] = []
    if int(planned_duration_seconds) < MIN_WALLCLOCK_DURATION_SECONDS:
        gaps.append("DURATION_BELOW_MIN")
    if int(planned_duration_seconds) > MAX_WALLCLOCK_DURATION_SECONDS:
        gaps.append("DURATION_BOUND_VIOLATION")
    return gaps
