from __future__ import annotations

from src.research.new_listings.collectors.base import CollectorContext
from src.research.new_listings.collectors.manual_seed import ManualSeedCollector


def test_manual_seed_collector_contract():
    c = ManualSeedCollector()
    out = c.collect(CollectorContext(run_id="nl_test", config_hash="0" * 64))
    assert len(out) == 1
    e = out[0]
    assert e.source == "manual_seed"
    assert e.venue_type == "seed"
    assert isinstance(e.observed_at, str) and "T" in e.observed_at
    assert "run_id" in e.payload
