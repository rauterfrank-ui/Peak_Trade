from __future__ import annotations

import pandas as pd

import pytest

from src.data.continuous.continuous_contract import (
    AdjustmentMethod,
    ContinuousSegment,
    build_continuous_contract,
    sha256_of_ohlcv_frame,
)


def _mk_df(start: str, rows: int, close0: float) -> pd.DataFrame:
    # pandas 3.x prefers lower-case frequency aliases ("h" vs "H")
    idx = pd.date_range(start=start, periods=rows, freq="1h", tz="UTC")
    close = [close0 + i for i in range(rows)]
    df = pd.DataFrame(
        {
            "open": [c - 0.1 for c in close],
            "high": [c + 0.2 for c in close],
            "low": [c - 0.3 for c in close],
            "close": close,
            "volume": [100.0 for _ in close],
        },
        index=idx,
    )
    return df


def test_build_continuous_none_stitch() -> None:
    a = _mk_df("2026-01-01T00:00:00Z", 3, close0=100.0)  # close: 100,101,102
    b = _mk_df("2026-01-01T03:00:00Z", 3, close0=200.0)  # close: 200,201,202

    segments = [
        ContinuousSegment(contract_symbol="NQH2026", start_ts=a.index[0], end_ts=a.index[-1]),
        ContinuousSegment(contract_symbol="NQM2026", start_ts=b.index[0], end_ts=b.index[-1]),
    ]

    out = build_continuous_contract({"NQH2026": a, "NQM2026": b}, segments, adjustment=AdjustmentMethod.NONE)
    assert out.index.is_monotonic_increasing
    assert float(out.loc[a.index[-1], "close"]) == 102.0
    assert float(out.loc[b.index[0], "close"]) == 200.0


def test_build_continuous_back_adjust() -> None:
    # At the boundary, a last close=102, b first close=200 => offset for a should be +98
    a = _mk_df("2026-01-01T00:00:00Z", 3, close0=100.0)  # last close 102
    b = _mk_df("2026-01-01T03:00:00Z", 3, close0=200.0)  # first close 200

    segments = [
        ContinuousSegment(contract_symbol="NQH2026", start_ts=a.index[0], end_ts=a.index[-1]),
        ContinuousSegment(contract_symbol="NQM2026", start_ts=b.index[0], end_ts=b.index[-1]),
    ]

    out = build_continuous_contract(
        {"NQH2026": a, "NQM2026": b},
        segments,
        adjustment=AdjustmentMethod.BACK_ADJUST,
    )
    assert float(out.loc[a.index[-1], "close"]) == 200.0
    assert float(out.loc[a.index[0], "close"]) == 198.0  # 100 + 98
    assert float(out.loc[b.index[0], "close"]) == 200.0  # last segment unchanged


def test_sha256_of_ohlcv_frame_deterministic() -> None:
    df = _mk_df("2026-01-01T00:00:00Z", 3, close0=123.0)
    h1 = sha256_of_ohlcv_frame(df)
    h2 = sha256_of_ohlcv_frame(df.copy())
    assert h1 == h2


# --- roll policy smoke for -k roll ---
@pytest.mark.roll
def test_roll_policy_import_and_vectors__smoke() -> None:
    """Ensures `-k roll` selects at least one test in this file."""
    from datetime import date

    from src.markets.cme.calendar import cme_equity_index_roll_date

    # (year, month) -> expected roll date (YYYY-MM-DD) per CME roll rule
    vectors = {
        (2024, 3): date(2024, 3, 11),
        # June 2025 third Friday is 2025-06-20 -> roll Monday prior is 2025-06-16
        (2025, 6): date(2025, 6, 16),
        (2026, 9): date(2026, 9, 14),
        (2027, 12): date(2027, 12, 13),
    }

    for (y, m), exp in vectors.items():
        got = cme_equity_index_roll_date(y, m)
        assert got == exp, f"roll_date({y},{m})={got}, expected={exp}"
