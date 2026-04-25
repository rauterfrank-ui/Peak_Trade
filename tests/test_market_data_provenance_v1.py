"""Unit-Tests für ``build_market_data_provenance_v1`` (Forward-Manifest-Metadaten)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from _market_data_provenance import build_market_data_provenance_v1  # noqa: E402


@pytest.mark.parametrize(
    "source,expect_kind,expect_provider,expect_ex,expect_synth,expect_fix",
    [
        ("dummy", "synthetic", "dummy", "none", True, False),
        ("DUMMY", "synthetic", "dummy", "none", True, False),
        ("kraken", "historical_real", "kraken", "kraken", False, False),
        ("csv", "local_file", "csv", "none", False, True),
        ("fixture", "local_file", "csv", "none", False, True),
    ],
)
def test_build_market_data_provenance_v1_mapping(
    source: str,
    expect_kind: str,
    expect_provider: str,
    expect_ex: str,
    expect_synth: bool,
    expect_fix: bool,
) -> None:
    ts = "2026-01-01T00:00:00Z"
    p = build_market_data_provenance_v1(
        ohlcv_source=source,
        symbols=["BTC/EUR"],
        timeframe="1h",
        n_bars=200,
        fetched_at_utc=ts,
        dry_run_execution=True,
    )
    assert p["schema_version"] == "market_data_provenance_v1"
    assert p["source_kind"] == expect_kind
    assert p["provider"] == expect_provider
    assert p["exchange"] == expect_ex
    assert p["is_synthetic"] is expect_synth
    assert p["is_fixture"] is expect_fix
    assert p["is_mock"] is False
    assert p["dry_run_execution"] is True
    assert p["symbols"] == ["BTC/EUR"]
    assert p["timeframe"] == "1h"
    assert p["n_bars"] == 200
    assert p["fetched_at_utc"] == ts
