"""Versioned public-MD request pacing, budget, and HTTP-429 contracts.

Ops/transport safety policy only. Not a strategy or alpha parameter surface.
Defaults are derived from existing wallclock observation runbook/config values
(poll_interval_seconds=2.0, per_request_max_retries=2, session_http_429_budget=20).
They are conservative safety defaults and are NOT claimed to be official OKX limits.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Mapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.models_v1 import (
    PreregisteredSessionRunnerError,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    DEFAULT_PER_REQUEST_MAX_RETRIES,
    DEFAULT_POLL_INTERVAL_SECONDS,
    DEFAULT_SESSION_HTTP_429_BUDGET,
)

POLICY_SCHEMA_VERSION = "canonical_volatility_numeric_max_age_public_md_request_pacing_policy/v1"
HTTP_429_CONTRACT_VERSION = "canonical_volatility_numeric_max_age_public_md_http_429_contract/v1"
ATTEMPT_EVIDENCE_SCHEMA = (
    "canonical_volatility_numeric_max_age_public_md_physical_attempt_evidence/v1"
)

# Conservative ops safety defaults (reuse wallclock observation contracts).
DEFAULT_MINIMUM_INTERVAL_SECONDS = float(DEFAULT_POLL_INTERVAL_SECONDS)  # 2.0
DEFAULT_MAXIMUM_REQUESTS_PER_CYCLE = int(DEFAULT_PER_REQUEST_MAX_RETRIES) + 1  # 3
DEFAULT_MAXIMUM_CONSECUTIVE_RATE_LIMITS = DEFAULT_MAXIMUM_REQUESTS_PER_CYCLE
DEFAULT_MAXIMUM_REQUESTS_PER_SESSION = 160  # safety cap; not an OKX-claimed limit
DEFAULT_RETRY_AFTER_MAX_SECONDS = 60.0
DEFAULT_BACKOFF_INITIAL_SECONDS = 1.0
DEFAULT_BACKOFF_MULTIPLIER = 2.0
DEFAULT_BACKOFF_MAX_SECONDS = 30.0
DEFAULT_JITTER_FRACTION = 0.1

ERROR_REQUEST_BUDGET_EXHAUSTED = "REQUEST_BUDGET_EXHAUSTED"
ERROR_RATE_LIMIT_RETRY_SCHEDULED = "RATE_LIMIT_RETRY_SCHEDULED"
ERROR_RATE_LIMIT_RETRY_AFTER_INVALID = "RATE_LIMIT_RETRY_AFTER_INVALID"
ERROR_RATE_LIMIT_RETRY_EXHAUSTED = "RATE_LIMIT_RETRY_EXHAUSTED"
ERROR_RATE_LIMIT_SESSION_BUDGET_EXHAUSTED = "RATE_LIMIT_SESSION_BUDGET_EXHAUSTED"
ERROR_ZERO_INTERVAL_BURST_FORBIDDEN = "ZERO_INTERVAL_BURST_FORBIDDEN"

MonotonicClock = Callable[[], float]
Sleeper = Callable[[float], None]
JitterSource = Callable[[], float]


@dataclass(frozen=True)
class PublicMdRequestPacingPolicyV1:
    """Typed, versioned rate-limit / pacing contract for productive public MD."""

    minimum_interval_seconds: float
    maximum_requests_per_session: int
    maximum_requests_per_cycle: int
    maximum_consecutive_rate_limits: int
    retry_after_max_seconds: float
    backoff_initial_seconds: float
    backoff_multiplier: float
    backoff_max_seconds: float
    jitter_fraction: float
    schema_version: str = POLICY_SCHEMA_VERSION
    http_429_contract_version: str = HTTP_429_CONTRACT_VERSION
    origin: str = (
        "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1"
        "+conservative_safety_defaults_not_official_okx_limits"
    )

    def validate(self) -> None:
        if float(self.minimum_interval_seconds) <= 0:
            raise PreregisteredSessionRunnerError("pacing_minimum_interval_must_be_positive")
        if int(self.maximum_requests_per_session) < 1:
            raise PreregisteredSessionRunnerError("pacing_session_budget_invalid")
        if int(self.maximum_requests_per_cycle) < 1:
            raise PreregisteredSessionRunnerError("pacing_per_cycle_budget_invalid")
        if int(self.maximum_consecutive_rate_limits) < 1:
            raise PreregisteredSessionRunnerError("pacing_consecutive_rate_limit_invalid")
        if float(self.retry_after_max_seconds) <= 0:
            raise PreregisteredSessionRunnerError("retry_after_max_invalid")
        if float(self.backoff_initial_seconds) <= 0:
            raise PreregisteredSessionRunnerError("backoff_initial_invalid")
        if float(self.backoff_multiplier) < 1.0:
            raise PreregisteredSessionRunnerError("backoff_multiplier_invalid")
        if float(self.backoff_max_seconds) < float(self.backoff_initial_seconds):
            raise PreregisteredSessionRunnerError("backoff_max_invalid")
        if not (0.0 <= float(self.jitter_fraction) < 1.0):
            raise PreregisteredSessionRunnerError("jitter_fraction_invalid")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_public_md_request_pacing_policy_v1() -> PublicMdRequestPacingPolicyV1:
    policy = PublicMdRequestPacingPolicyV1(
        minimum_interval_seconds=DEFAULT_MINIMUM_INTERVAL_SECONDS,
        maximum_requests_per_session=DEFAULT_MAXIMUM_REQUESTS_PER_SESSION,
        maximum_requests_per_cycle=DEFAULT_MAXIMUM_REQUESTS_PER_CYCLE,
        maximum_consecutive_rate_limits=DEFAULT_MAXIMUM_CONSECUTIVE_RATE_LIMITS,
        retry_after_max_seconds=DEFAULT_RETRY_AFTER_MAX_SECONDS,
        backoff_initial_seconds=DEFAULT_BACKOFF_INITIAL_SECONDS,
        backoff_multiplier=DEFAULT_BACKOFF_MULTIPLIER,
        backoff_max_seconds=DEFAULT_BACKOFF_MAX_SECONDS,
        jitter_fraction=DEFAULT_JITTER_FRACTION,
    )
    policy.validate()
    return policy


@dataclass(frozen=True)
class EffectiveRequestBudgetV1:
    max_cycles: int
    maximum_requests_per_cycle: int
    maximum_requests_per_session_policy: int
    derived_from_cycles: int
    effective_maximum_requests: int
    clamped: bool
    clamp_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_effective_request_budget_v1(
    *,
    max_cycles: int,
    policy: PublicMdRequestPacingPolicyV1,
) -> EffectiveRequestBudgetV1:
    if int(max_cycles) < 1:
        raise PreregisteredSessionRunnerError("max_cycles_required_for_budget")
    derived = int(max_cycles) * int(policy.maximum_requests_per_cycle)
    policy_max = int(policy.maximum_requests_per_session)
    effective = min(policy_max, derived)
    clamped = effective != derived or effective != policy_max
    if effective == policy_max and policy_max < derived:
        reason = "limited_by_policy_maximum_requests_per_session"
    elif effective == derived and derived < policy_max:
        reason = "limited_by_max_cycles_times_per_cycle"
    else:
        reason = "limits_equal"
    return EffectiveRequestBudgetV1(
        max_cycles=int(max_cycles),
        maximum_requests_per_cycle=int(policy.maximum_requests_per_cycle),
        maximum_requests_per_session_policy=policy_max,
        derived_from_cycles=derived,
        effective_maximum_requests=effective,
        clamped=bool(clamped and reason != "limits_equal"),
        clamp_reason=reason,
    )


@dataclass
class SessionRequestBudgetV1:
    """Physical-attempt budget. Retries count. Check before network side effect."""

    effective: EffectiveRequestBudgetV1
    remaining: int = 0
    consumed: int = 0

    def __post_init__(self) -> None:
        if self.remaining == 0 and self.consumed == 0:
            self.remaining = int(self.effective.effective_maximum_requests)

    def peek_before(self) -> int:
        return int(self.remaining)

    def assert_available(self) -> None:
        if self.remaining < 1:
            raise PreregisteredSessionRunnerError(ERROR_REQUEST_BUDGET_EXHAUSTED)

    def consume_one(self) -> tuple[int, int]:
        """Return (before, after). Fail-closed if exhausted."""
        before = self.peek_before()
        self.assert_available()
        self.remaining -= 1
        self.consumed += 1
        return before, int(self.remaining)

    def to_dict(self) -> dict[str, Any]:
        return {
            "effective": self.effective.to_dict(),
            "remaining": int(self.remaining),
            "consumed": int(self.consumed),
            "SESSION_REQUEST_BUDGET_COUNTS_PHYSICAL_ATTEMPTS": True,
            "RETRY_ATTEMPTS_COUNT_AGAINST_BUDGET": True,
            "BUDGET_CHECK_BEFORE_NETWORK_SIDE_EFFECT": True,
            "BUDGET_CANNOT_BE_EXCEEDED": True,
            "BUDGET_EXHAUSTION_IS_DETERMINISTIC": True,
        }


@dataclass
class MonotonicRequestPacerV1:
    """Monotonic-clock pacing before every physical HTTP attempt."""

    policy: PublicMdRequestPacingPolicyV1
    clock: MonotonicClock
    sleep: Sleeper
    last_attempt_started_monotonic: Optional[float] = None
    waits: list[float] = field(default_factory=list)

    def wait_before_attempt(self) -> float:
        now = float(self.clock())
        waited = 0.0
        if self.last_attempt_started_monotonic is not None:
            elapsed = now - float(self.last_attempt_started_monotonic)
            need = float(self.policy.minimum_interval_seconds) - elapsed
            if need > 0:
                self.sleep(need)
                waited = need
                self.waits.append(need)
                now = float(self.clock())
        self.last_attempt_started_monotonic = now
        return waited

    def effective_interval_for_cycle_count(
        self, *, cycle_count: int, requested_poll: float
    ) -> float:
        if int(cycle_count) > 1 and float(requested_poll) <= 0:
            return float(self.policy.minimum_interval_seconds)
        return max(float(requested_poll), float(self.policy.minimum_interval_seconds))


@dataclass(frozen=True)
class RetryAfterParseResultV1:
    raw: Optional[str]
    parsed_seconds: Optional[float]
    source: str
    valid: bool
    error_code: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _header_get_ci(headers: Mapping[str, str] | None, name: str) -> Optional[str]:
    if not headers:
        return None
    wanted = name.lower()
    for key, value in headers.items():
        if str(key).lower() == wanted:
            text = str(value).strip()
            return text if text else None
    return None


def parse_retry_after_header_v1(
    headers: Mapping[str, str] | None,
    *,
    now_unix: float,
    max_seconds: float,
) -> RetryAfterParseResultV1:
    raw = _header_get_ci(headers, "Retry-After")
    if raw is None:
        return RetryAfterParseResultV1(raw=None, parsed_seconds=None, source="absent", valid=False)
    # Delta-seconds first.
    try:
        seconds = float(raw)
        if seconds < 0:
            return RetryAfterParseResultV1(
                raw=raw,
                parsed_seconds=None,
                source="delta_seconds",
                valid=False,
                error_code=ERROR_RATE_LIMIT_RETRY_AFTER_INVALID,
            )
        capped = min(seconds, float(max_seconds))
        return RetryAfterParseResultV1(
            raw=raw,
            parsed_seconds=float(capped),
            source="delta_seconds_capped" if capped < seconds else "delta_seconds",
            valid=True,
        )
    except ValueError:
        pass
    # Optional HTTP-date.
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            return RetryAfterParseResultV1(
                raw=raw,
                parsed_seconds=None,
                source="http_date",
                valid=False,
                error_code=ERROR_RATE_LIMIT_RETRY_AFTER_INVALID,
            )
        delta = dt.timestamp() - float(now_unix)
        if delta < 0:
            return RetryAfterParseResultV1(
                raw=raw,
                parsed_seconds=None,
                source="http_date",
                valid=False,
                error_code=ERROR_RATE_LIMIT_RETRY_AFTER_INVALID,
            )
        capped = min(delta, float(max_seconds))
        return RetryAfterParseResultV1(
            raw=raw,
            parsed_seconds=float(capped),
            source="http_date_capped" if capped < delta else "http_date",
            valid=True,
        )
    except (TypeError, ValueError, IndexError, OverflowError):
        return RetryAfterParseResultV1(
            raw=raw,
            parsed_seconds=None,
            source="unparseable",
            valid=False,
            error_code=ERROR_RATE_LIMIT_RETRY_AFTER_INVALID,
        )


def compute_exponential_backoff_seconds_v1(
    *,
    policy: PublicMdRequestPacingPolicyV1,
    attempt_index: int,
    jitter_unit: float,
) -> float:
    base = float(policy.backoff_initial_seconds) * (
        float(policy.backoff_multiplier) ** int(attempt_index)
    )
    capped = min(base, float(policy.backoff_max_seconds))
    # Deterministic jitter: jitter_unit in [0,1) from injectable source.
    unit = max(0.0, min(0.999999, float(jitter_unit)))
    span = capped * float(policy.jitter_fraction)
    return max(0.0, capped - span + (span * unit))


def deterministic_jitter_unit_v1(*, session_id: str, global_request_index: int) -> float:
    digest = hashlib.sha256(f"{session_id}:{global_request_index}".encode("utf-8")).hexdigest()
    return (int(digest[:8], 16) % 10_000) / 10_000.0


@dataclass
class PhysicalAttemptEvidenceV1:
    session_id: str
    cycle_index: int
    attempt_index: int
    global_request_index: int
    method: str
    host: str
    path: str
    instrument_id: str
    request_started_monotonic: float
    request_finished_monotonic: float
    latency_seconds: float
    http_status: Optional[int]
    response_class: str
    retry_after_raw: Optional[str]
    retry_after_parsed_seconds: Optional[float]
    backoff_source: str
    scheduled_backoff_seconds: float
    request_budget_before: int
    request_budget_after: int
    rate_limit_count: int
    terminal: bool
    error_code: str

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["schema"] = ATTEMPT_EVIDENCE_SCHEMA
        return out


@dataclass
class PublicMdTelemetryCountersV1:
    physical_request_attempt_count: int = 0
    successful_response_count: int = 0
    rate_limited_response_count: int = 0
    terminal_transport_failure_count: int = 0
    completed_market_sample_count: int = 0
    completed_accumulation_cycle_count: int = 0
    market_data_request_occurred: bool = False
    attempt_evidence: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "physical_request_attempt_count": self.physical_request_attempt_count,
            "successful_response_count": self.successful_response_count,
            "rate_limited_response_count": self.rate_limited_response_count,
            "terminal_transport_failure_count": self.terminal_transport_failure_count,
            "completed_market_sample_count": self.completed_market_sample_count,
            "completed_accumulation_cycle_count": self.completed_accumulation_cycle_count,
            "market_data_request_occurred": self.market_data_request_occurred,
            "attempt_evidence": list(self.attempt_evidence),
            "NETWORK_FAILURES_IS_NOT_PHYSICAL_REQUEST_COUNT": True,
        }


def classify_http_response_v1(status: Optional[int]) -> str:
    if status is None:
        return "TRANSPORT_ERROR"
    if status == 429:
        return "RATE_LIMITED"
    if 200 <= int(status) < 300:
        return "SUCCESS"
    if int(status) in {401, 403}:
        return "AUTH_SURFACE"
    if int(status) >= 400:
        return "HTTP_ERROR"
    return "OTHER"
