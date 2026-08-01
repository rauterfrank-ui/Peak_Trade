"""Preregistered OKX-EEA public MD source for productive session runner.

Uses the existing EEA public REST transport. Real networking requires an
explicit injected real fetcher; tests inject fakes. No credentials, orders,
private endpoints, websockets, or offline synthetic mark sequences.
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
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportV1,
    HttpFetcher,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.mark_price_contract_v1 import (
    parse_public_mark_price_response_v1,
)

Clock = Callable[[], float]


@dataclass
class PublicMdSourceTelemetryV1:
    fetch_count: int = 0
    paths: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    private_endpoint_request_occurred: bool = False
    credential_access_occurred: bool = False
    order_request_occurred: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "fetch_count": self.fetch_count,
            "paths": list(self.paths),
            "urls": list(self.urls),
            "private_endpoint_request_occurred": self.private_endpoint_request_occurred,
            "credential_access_occurred": self.credential_access_occurred,
            "order_request_occurred": self.order_request_occurred,
            "public_endpoints_only": not self.private_endpoint_request_occurred,
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
        # Credential / private surface refusals.
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


def build_preregistered_public_md_transport_v1(
    *,
    fetcher: HttpFetcher,
    telemetry: Optional[PublicMdSourceTelemetryV1] = None,
) -> tuple[EeaPublicMdTransportV1, PublicMdSourceTelemetryV1]:
    tel = telemetry or PublicMdSourceTelemetryV1()
    transport = EeaPublicMdTransportV1(fetcher=wrap_allowlisted_fetcher_v1(fetcher, telemetry=tel))
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
) -> list[ProductiveBridgeMarketSampleV1]:
    """Fetch public mark-price samples. Runtime polls do not invent market time."""
    del canonical_instrument_id  # identity uses venue-native id from binding authority
    if cycle_count < 1:
        raise PreregisteredSessionRunnerError("cycle_count_required")
    if not transport.opened:
        raise PreregisteredSessionRunnerError("transport_not_opened_before_fetch")
    now_fn = clock or time.time
    samples: list[ProductiveBridgeMarketSampleV1] = []
    for idx in range(int(cycle_count)):
        receive = float(now_fn())
        result = transport.fetch_mark_price(venue_instrument_id=venue_instrument_id)
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
        if idx + 1 < cycle_count and poll_interval_seconds > 0:
            sleep(float(poll_interval_seconds))
    return samples


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
