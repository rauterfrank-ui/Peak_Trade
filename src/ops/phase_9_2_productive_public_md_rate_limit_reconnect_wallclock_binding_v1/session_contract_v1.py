"""Load and validate the rate-limit/reconnect session contract (no network)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    SESSION_CONTRACT_RELATIVE_PATH,
    SESSION_LADDER_STEP,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import (
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
    if int(contract.get("reconnect_attempt_limit") or 0) < 1:
        gaps.append("UNBOUNDED_OR_EMPTY_RECONNECT")
    if int(contract.get("reconnect_time_limit_seconds") or 0) < 1:
        gaps.append("UNBOUNDED_OR_EMPTY_RECONNECT_TIME")
    if float(contract.get("minimum_interval_seconds") or 0) <= 0:
        gaps.append("ZERO_INTERVAL_BURST")
    if float(contract.get("poll_interval_seconds") or 0) <= 0:
        gaps.append("ZERO_POLL_INTERVAL")
    if int(contract.get("session_http_429_budget") or 0) < 1:
        gaps.append("HTTP_429_BUDGET_MISSING")
    # Budgets must reuse existing smoke/wallclock safety values (no new thresholds).
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
        "max_requests_per_session": SMOKE_MAX_REQUESTS_PER_SESSION,
        "staleness_budget_seconds": SMOKE_STALENESS_BUDGET_SECONDS,
        "consecutive_stale_budget": SMOKE_CONSECUTIVE_STALE_BUDGET,
    }
    for key, want in expected.items():
        got = contract.get(key)
        if isinstance(want, float):
            if float(got) != float(want):
                gaps.append(f"BUDGET_DRIFT:{key}")
        else:
            if int(got) != int(want):
                gaps.append(f"BUDGET_DRIFT:{key}")
    return gaps


def load_and_validate_session_contract_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    contract = load_session_contract_v1(repo_root=repo_root)
    gaps = validate_session_contract_v1(contract)
    if gaps:
        raise SessionContractError("SESSION_CONTRACT_INVALID:" + ",".join(gaps))
    return contract
