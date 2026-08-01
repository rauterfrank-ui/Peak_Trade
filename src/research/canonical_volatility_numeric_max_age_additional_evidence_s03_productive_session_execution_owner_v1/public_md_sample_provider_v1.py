"""Production public-MD sample provider for S03 real path (reuses preregistered transport)."""

from __future__ import annotations

import time
from typing import Callable, Optional

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    AdditionalEvidenceS03SessionExecutionOwnerError,
    MarketSampleV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.network_boundary_v1 import (
    assert_public_md_request_allowed_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.constants_v1 import (
    BOUND_VENUE_INSTRUMENT_ID,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_source_v1 import (
    build_preregistered_public_md_transport_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportError,
    HttpFetcher,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.mark_price_contract_v1 import (
    parse_public_mark_price_response_v1,
)


def build_s03_public_md_sample_provider_v1(
    *,
    session_id: str,
    http_fetcher: HttpFetcher,
    venue_instrument_id: str = BOUND_VENUE_INSTRUMENT_ID,
    wall_clock: Optional[Callable[[], float]] = None,
    sleep: Callable[[float], None] = time.sleep,
    monotonic_clock: Callable[[], float] = time.monotonic,
) -> Callable[[], Optional[MarketSampleV1]]:
    """Return a provider that performs one allowlisted public mark-price GET per call."""
    if http_fetcher is None:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("http_fetcher_required")
    now = wall_clock or time.time
    transport, _tel = build_preregistered_public_md_transport_v1(
        fetcher=http_fetcher,
        sleep=sleep,
        monotonic_clock=monotonic_clock,
        wall_clock=now,
        session_id=session_id,
    )
    if not transport.opened:
        transport.open()

    def _provider() -> Optional[MarketSampleV1]:
        receive = float(now())
        try:
            result = transport.fetch_mark_price(venue_instrument_id=venue_instrument_id)
        except EeaPublicMdTransportError as exc:
            raise AdditionalEvidenceS03SessionExecutionOwnerError(
                f"public_md_fetch_failed:{exc}"
            ) from exc
        assert_public_md_request_allowed_v1(url=result.url, method="GET")
        mark = parse_public_mark_price_response_v1(
            result.payload,
            expected_venue_instrument_id=venue_instrument_id,
            receive_ts_unix=receive,
        )
        return MarketSampleV1(
            sample_identity=f"mark:{venue_instrument_id}:{int(mark.event_ts_unix)}",
            mark_price=float(mark.mark_px),
            event_time_unix_seconds=float(mark.event_ts_unix),
            receive_time_unix_seconds=float(mark.receive_ts_unix),
            monotonic_elapsed_seconds=0.0,
        )

    return _provider
