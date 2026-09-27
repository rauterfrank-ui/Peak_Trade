"""Cap-21 productivity root fixtures for PRE_EXTERNAL instType binding tests."""

from __future__ import annotations

from pathlib import Path

from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    run_governed_futures_universe_producer_v1,
)
from tests.ops.test_governed_futures_universe_producer_v1 import (
    OBSERVED_UNIX,
    REPO_SHA,
    SOURCE_EVENT,
    _marks,
    _payload,
    _perp,
)


def write_cap21_productivity_root_for_inst_v1(
    tmp_path: Path,
    *,
    venue_native_id: str,
) -> Path:
    """Minimal Cap-2.1 universe under Cap-2.4 productivity layout (tmp only)."""

    base = venue_native_id.split("-")[0]
    prod_root = tmp_path / "cap24_productivity"
    uni_root = prod_root / "runtime_state" / "universe"
    uni_root.mkdir(parents=True, exist_ok=True)
    out = run_governed_futures_universe_producer_v1(
        state_root=uni_root,
        source_payload=_payload([_perp(inst_id=venue_native_id, base=base)]),
        mark_price_payload=_marks(venue_native_id),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
        session_id="pre-ext-inst-type-fixture",
    )
    assert out.get("ok") is True, out
    return prod_root
