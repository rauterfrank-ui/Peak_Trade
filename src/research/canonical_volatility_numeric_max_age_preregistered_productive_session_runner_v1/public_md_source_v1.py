"""Preregistered OKX-EEA public MD source for productive session runner.

Uses the existing EEA public REST transport. Real networking requires an
explicit injected real fetcher; tests inject fakes. No credentials, orders,
private endpoints, websockets, or offline synthetic mark sequences.

Hardened pacing/budget/429 evidence is applied around every physical GET.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Sequence
from urllib.parse import urlparse

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.productive_bridge_runner_v1 import (
    ProductiveBridgeMarketSampleV1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.constants_v1 import (
    BOUND_INSTRUMENT_ID,
    BOUND_PUBLIC_MD_HOST_V1,
    BOUND_VENUE_INSTRUMENT_ID,
    PUBLIC_MD_ENDPOINT_ALLOWLIST,
    PUBLIC_MD_METHOD_ALLOWLIST,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.models_v1 import (
    PreregisteredSessionRunnerError,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_rate_limit_policy_v1 import (
    MonotonicRequestPacerV1,
    PhysicalAttemptEvidenceV1,
    PublicMdRequestPacingPolicyV1,
    PublicMdTelemetryCountersV1,
    SessionRequestBudgetV1,
    classify_http_response_v1,
    compute_effective_request_budget_v1,
    default_public_md_request_pacing_policy_v1,
    deterministic_jitter_unit_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportError,
    EeaPublicMdTransportV1,
    HttpFetcher,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.mark_price_contract_v1 import (
    parse_public_mark_price_response_v1,
)

Clock = Callable[[], float]


@dataclass
class PublicMdSourceTelemetryV1:
    """Backward-compatible telemetry plus hardened counters/evidence."""

    fetch_count: int = 0
    paths: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    private_endpoint_request_occurred: bool = False
    credential_access_occurred: bool = False
    order_request_occurred: bool = False
    counters: PublicMdTelemetryCountersV1 = field(default_factory=PublicMdTelemetryCountersV1)
    effective_budget: dict[str, Any] = field(default_factory=dict)
    pacing_policy: dict[str, Any] = field(default_factory=dict)
    instrument_binding: dict[str, Any] = field(default_factory=dict)

    @property
    def market_data_request_occurred(self) -> bool:
        return bool(self.counters.market_data_request_occurred)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fetch_count": self.fetch_count,
            "paths": list(self.paths),
            "urls": list(self.urls),
            "private_endpoint_request_occurred": self.private_endpoint_request_occurred,
            "credential_access_occurred": self.credential_access_occurred,
            "order_request_occurred": self.order_request_occurred,
            "public_endpoints_only": not self.private_endpoint_request_occurred,
            "market_data_request_occurred": self.market_data_request_occurred,
            "counters": self.counters.to_dict(),
            "effective_budget": dict(self.effective_budget),
            "pacing_policy": dict(self.pacing_policy),
            "instrument_binding": dict(self.instrument_binding),
        }


def assert_public_get_allowlist_v1(*, url: str, method: str = "GET") -> str:
    if str(method).upper() not in PUBLIC_MD_METHOD_ALLOWLIST:
        raise PreregisteredSessionRunnerError("public_md_method_forbidden")
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    expected_host = urlparse(BOUND_PUBLIC_MD_HOST_V1).hostname or "eea.okx.com"
    if host != expected_host:
        raise PreregisteredSessionRunnerError(f"public_md_host_forbidden:{host}")
    path = parsed.path or ""
    if path not in PUBLIC_MD_ENDPOINT_ALLOWLIST:
        raise PreregisteredSessionRunnerError(f"public_md_path_forbidden:{path}")
    if any(tok in url.lower() for tok in ("apikey", "secret", "passphrase", "authorization=")):
        raise PreregisteredSessionRunnerError("credential_query_forbidden")
    return path


def reject_offline_synthetic_mark_source_v1(source_kind: str | None) -> None:
    kind = str(source_kind or "").strip().lower()
    if kind in {
        "offline",
        "synthetic",
        "deterministic_mark_path",
        "productive-bridge-accumulate",
        "fixture",
        "probe",
    }:
        raise PreregisteredSessionRunnerError("offline_synthetic_mark_source_forbidden")


def wrap_allowlisted_fetcher_v1(
    fetcher: HttpFetcher,
    *,
    telemetry: PublicMdSourceTelemetryV1,
) -> HttpFetcher:
    def _wrapped(
        url: str, method: str, headers: Mapping[str, str], timeout: float
    ) -> tuple[int, bytes, Mapping[str, str]]:
        path = assert_public_get_allowlist_v1(url=url, method=method)
        for key in headers:
            if str(key).lower() in {"authorization", "ok-access-key", "ok-access-sign"}:
                telemetry.credential_access_occurred = True
                raise PreregisteredSessionRunnerError("credential_header_forbidden")
        if path.startswith("/api/v5/trade") or "order" in path:
            telemetry.private_endpoint_request_occurred = True
            telemetry.order_request_occurred = True
            raise PreregisteredSessionRunnerError("private_or_order_endpoint_forbidden")
        telemetry.fetch_count += 1
        telemetry.paths.append(path)
        telemetry.urls.append(url)
        return fetcher(url, method, headers, timeout)

    return _wrapped


@dataclass
class ProductiveMdAttemptGateV1:
    """Budget + pacing + per-attempt evidence around each physical GET."""

    session_id: str
    venue_instrument_id: str
    budget: SessionRequestBudgetV1
    pacer: MonotonicRequestPacerV1
    telemetry: PublicMdSourceTelemetryV1
    monotonic_clock: Clock
    cycle_index: int = 0
    rate_limit_count: int = 0

    def set_cycle_index(self, cycle_index: int) -> None:
        self.cycle_index = int(cycle_index)

    def before_physical_attempt(
        self, *, url: str, path: str, attempt_index: int
    ) -> Mapping[str, Any]:
        del path
        self.budget.assert_available()
        self.pacer.wait_before_attempt()
        # Mark request occurred as soon as the physical attempt is about to start.
        self.telemetry.counters.market_data_request_occurred = True
        before, after = self.budget.consume_one()
        self.telemetry.counters.physical_request_attempt_count += 1
        return {
            "budget_before": before,
            "budget_after": after,
            "url": url,
            "attempt_index": attempt_index,
        }

    def after_physical_attempt(
        self,
        *,
        url: str,
        path: str,
        attempt_index: int,
        status: Optional[int],
        headers: Mapping[str, str],
        error_code: str,
        terminal: bool,
        backoff_source: str,
        scheduled_backoff_seconds: float,
        retry_after_raw: Optional[str],
        retry_after_parsed_seconds: Optional[float],
        started_monotonic: float,
        finished_monotonic: float,
        budget_before: int,
        budget_after: int,
    ) -> None:
        del headers
        parsed = urlparse(url)
        response_class = classify_http_response_v1(status)
        if response_class == "RATE_LIMITED":
            self.rate_limit_count += 1
            self.telemetry.counters.rate_limited_response_count += 1
        elif response_class == "SUCCESS" and not error_code:
            self.telemetry.counters.successful_response_count += 1
        if terminal and error_code:
            self.telemetry.counters.terminal_transport_failure_count += 1
        row = PhysicalAttemptEvidenceV1(
            session_id=self.session_id,
            cycle_index=int(self.cycle_index),
            attempt_index=int(attempt_index),
            global_request_index=int(self.telemetry.counters.physical_request_attempt_count),
            method="GET",
            host=(parsed.hostname or ""),
            path=path,
            instrument_id=self.venue_instrument_id,
            request_started_monotonic=float(started_monotonic),
            request_finished_monotonic=float(finished_monotonic),
            latency_seconds=max(0.0, float(finished_monotonic) - float(started_monotonic)),
            http_status=int(status) if status is not None else None,
            response_class=response_class,
            retry_after_raw=retry_after_raw,
            retry_after_parsed_seconds=retry_after_parsed_seconds,
            backoff_source=str(backoff_source or ""),
            scheduled_backoff_seconds=float(scheduled_backoff_seconds or 0.0),
            request_budget_before=int(budget_before),
            request_budget_after=int(budget_after),
            rate_limit_count=int(self.rate_limit_count),
            terminal=bool(terminal),
            error_code=str(error_code or ""),
        )
        self.telemetry.counters.attempt_evidence.append(row.to_dict())


def build_preregistered_public_md_transport_v1(
    *,
    fetcher: HttpFetcher,
    telemetry: Optional[PublicMdSourceTelemetryV1] = None,
    rate_limit_policy: Optional[PublicMdRequestPacingPolicyV1] = None,
    attempt_gate: Optional[ProductiveMdAttemptGateV1] = None,
    sleep: Callable[[float], None] = time.sleep,
    monotonic_clock: Clock = time.monotonic,
    wall_clock: Clock = time.time,
    session_id: str = "",
) -> tuple[EeaPublicMdTransportV1, PublicMdSourceTelemetryV1]:
    tel = telemetry or PublicMdSourceTelemetryV1()
    policy = rate_limit_policy or default_public_md_request_pacing_policy_v1()
    transport = EeaPublicMdTransportV1(
        fetcher=wrap_allowlisted_fetcher_v1(fetcher, telemetry=tel),
        sleep=sleep,
        rate_limit_policy=policy,
        attempt_gate=attempt_gate,
        monotonic_clock=monotonic_clock,
        wall_clock=wall_clock,
        jitter_unit_fn=(
            (
                lambda idx: deterministic_jitter_unit_v1(
                    session_id=session_id, global_request_index=idx
                )
            )
            if session_id
            else None
        ),
        max_retries=max(0, int(policy.maximum_consecutive_rate_limits) - 1),
        session_http_429_budget=max(
            int(policy.maximum_consecutive_rate_limits),
            int(policy.maximum_requests_per_session),
        ),
    )
    return transport, tel


def collect_public_mark_samples_v1(
    *,
    transport: EeaPublicMdTransportV1,
    cycle_count: int,
    venue_instrument_id: str = BOUND_VENUE_INSTRUMENT_ID,
    canonical_instrument_id: str = BOUND_INSTRUMENT_ID,
    clock: Optional[Clock] = None,
    sleep: Callable[[float], None] = time.sleep,
    poll_interval_seconds: float = 0.0,
    session_id: str = "",
    telemetry: Optional[PublicMdSourceTelemetryV1] = None,
    rate_limit_policy: Optional[PublicMdRequestPacingPolicyV1] = None,
    attempt_gate: Optional[ProductiveMdAttemptGateV1] = None,
    monotonic_clock: Optional[Clock] = None,
) -> list[ProductiveBridgeMarketSampleV1]:
    """Fetch public mark-price samples with hardened pacing/budget/429 contracts."""
    del canonical_instrument_id  # identity uses resolved venue-native id
    if cycle_count < 1:
        raise PreregisteredSessionRunnerError("cycle_count_required")
    if not transport.opened:
        raise PreregisteredSessionRunnerError("transport_not_opened_before_fetch")

    policy = rate_limit_policy or default_public_md_request_pacing_policy_v1()
    policy.validate()
    # Zero-interval bursts are forbidden when more than one cycle is requested.
    # Per-attempt pacing (attempt_gate / transport) is the sole wait authority.
    if int(cycle_count) > 1:
        if float(policy.minimum_interval_seconds) <= 0:
            raise PreregisteredSessionRunnerError("ZERO_INTERVAL_BURST_FORBIDDEN")
        if transport.attempt_gate is None and float(poll_interval_seconds) <= 0:
            raise PreregisteredSessionRunnerError("ZERO_INTERVAL_BURST_FORBIDDEN")

    now_fn = clock or time.time
    del sleep, monotonic_clock  # waits are owned by attempt_gate / transport policy
    tel = telemetry
    gate = attempt_gate
    samples: list[ProductiveBridgeMarketSampleV1] = []

    for idx in range(int(cycle_count)):
        if gate is not None:
            gate.set_cycle_index(idx)
        receive = float(now_fn())
        try:
            result = transport.fetch_mark_price(venue_instrument_id=venue_instrument_id)
        except EeaPublicMdTransportError as exc:
            # Terminal transport/429 failure must not be retried by the outer cycle loop.
            raise PreregisteredSessionRunnerError(str(exc)) from exc
        assert_public_get_allowlist_v1(url=result.url, method="GET")
        mark = parse_public_mark_price_response_v1(
            result.payload,
            expected_venue_instrument_id=venue_instrument_id,
            receive_ts_unix=receive,
        )
        samples.append(
            ProductiveBridgeMarketSampleV1(
                mark_price=float(mark.mark_px),
                event_time_unix_seconds=float(mark.event_ts_unix),
                receive_time_unix_seconds=float(mark.receive_ts_unix),
            )
        )
        if tel is not None:
            tel.counters.completed_market_sample_count += 1
    return samples


def initialize_session_md_controls_v1(
    *,
    session_id: str,
    max_cycles: int,
    venue_instrument_id: str,
    telemetry: PublicMdSourceTelemetryV1,
    policy: Optional[PublicMdRequestPacingPolicyV1] = None,
    sleep: Callable[[float], None] = time.sleep,
    monotonic_clock: Clock = time.monotonic,
) -> tuple[PublicMdRequestPacingPolicyV1, SessionRequestBudgetV1, ProductiveMdAttemptGateV1]:
    pacing = policy or default_public_md_request_pacing_policy_v1()
    pacing.validate()
    effective = compute_effective_request_budget_v1(max_cycles=max_cycles, policy=pacing)
    budget = SessionRequestBudgetV1(effective=effective)
    pacer = MonotonicRequestPacerV1(policy=pacing, clock=monotonic_clock, sleep=sleep)
    gate = ProductiveMdAttemptGateV1(
        session_id=session_id,
        venue_instrument_id=venue_instrument_id,
        budget=budget,
        pacer=pacer,
        telemetry=telemetry,
        monotonic_clock=monotonic_clock,
    )
    telemetry.effective_budget = budget.to_dict()
    telemetry.pacing_policy = pacing.to_dict()
    return pacing, budget, gate


def assert_no_orders_or_credentials_v1(telemetry: PublicMdSourceTelemetryV1) -> None:
    if telemetry.credential_access_occurred:
        raise PreregisteredSessionRunnerError("credential_access_occurred")
    if telemetry.private_endpoint_request_occurred:
        raise PreregisteredSessionRunnerError("private_endpoint_request_occurred")
    if telemetry.order_request_occurred:
        raise PreregisteredSessionRunnerError("order_request_occurred")
    for path in telemetry.paths:
        if path not in PUBLIC_MD_ENDPOINT_ALLOWLIST:
            raise PreregisteredSessionRunnerError(f"path_not_allowlisted:{path}")
