"""Deterministic fake public-MD transport boundary for offline integration tests.

Does not inject decisions, intents, or fills. Only emits allowlisted ticker polls.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.network_boundary_guard_v1 import (
    validate_request_boundary_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
)

VENUE_INSTRUMENT_ID = CANONICAL_INSTRUMENT_ID


def build_fake_ticker_fetcher_v1(
    *,
    calls: list[tuple[str, str]],
    clock: Any,
) -> Callable[[str, str, dict[str, str], float], tuple[int, bytes, dict[str, str]]]:
    def fetcher(
        url: str, method: str, headers: dict[str, str], timeout: float
    ) -> tuple[int, bytes, dict[str, str]]:
        _ = timeout
        att = validate_request_boundary_v1(url=url, method=method, headers=headers, environ={})
        if not att.ok:
            raise RuntimeError("FAKE_MD_BOUNDARY_VIOLATION:" + ",".join(att.blockers))
        calls.append((method, url))
        ts = int(float(clock.time()) * 1000) + len(calls)
        mark = 3000.0 + float(len(calls))
        payload = {
            "code": "0",
            "data": [
                {
                    "instId": VENUE_INSTRUMENT_ID,
                    "last": str(mark),
                    "askPx": str(mark + 0.1),
                    "bidPx": str(mark - 0.1),
                    "ts": str(ts),
                }
            ],
        }
        return 200, json.dumps(payload).encode("utf-8"), {"Content-Type": "application/json"}

    return fetcher


def poll_fake_public_md_observations_v1(
    *,
    transport: EeaPublicMdTransportV1,
    count: int = MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
    instrument_id: str = CANONICAL_INSTRUMENT_ID,
    venue_instrument_id: str = VENUE_INSTRUMENT_ID,
) -> list[str]:
    """Poll allowlisted public MD via transport; return distinct observation identities."""
    identities: list[str] = []
    transport.open()
    try:
        for idx in range(int(count)):
            result = transport.fetch_ticker(venue_instrument_id=venue_instrument_id)
            if int(result.status) != 200:
                raise RuntimeError(f"fake_md_status:{result.status}")
            row = result.payload["data"][0]
            identities.append(f"obs:{instrument_id}:{row['ts']}:{row['last']}:{idx}")
    finally:
        transport.close()
    return identities
