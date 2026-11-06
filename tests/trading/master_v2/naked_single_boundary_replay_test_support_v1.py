"""Test support: bind typed canonical volatility for productive replay fixtures."""

from __future__ import annotations

from datetime import datetime, timezone

from trading.master_v2.canonical_market_context_v1 import CanonicalMarketContextV1
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    build_canonical_volatility_estimate_v1,
)

_AS_OF = datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc)


def with_typed_volatility_for_replay_tests_v1(
    context: CanonicalMarketContextV1,
    *,
    sigma_value: float = 0.004321,
) -> CanonicalMarketContextV1:
    if context.canonical_volatility_estimate is not None:
        return context
    estimate = build_canonical_volatility_estimate_v1(
        value=float(sigma_value),
        observation_count=60,
        as_of_event_time=_AS_OF,
        fallback_used=False,
    )
    return bind_typed_canonical_volatility_estimate_into_market_context_v1(context, estimate)
