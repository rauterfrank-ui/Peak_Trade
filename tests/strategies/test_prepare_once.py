from __future__ import annotations

import pandas as pd

from src.strategies.base import BaseStrategy


class _PrepareOnceProbeStrategy(BaseStrategy):
    """
    Mini-Strategie zum Testen des Lifecycle-Verhaltens.
    - prepare() zählt Aufrufe
    - generate_signals() liefert deterministisch flat (0)
    """

    def __init__(self) -> None:
        super().__init__()
        self.prepare_calls = 0

    @classmethod
    def from_config(cls, cfg, section: str):  # pragma: no cover
        return cls()

    def prepare(self, data: pd.DataFrame) -> None:
        self.prepare_calls += 1

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        return pd.Series(0, index=data.index, dtype=int)


def _make_df() -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=10, freq="1h")
    # Minimaler OHLCV-Slice (close reicht für den Test)
    return pd.DataFrame({"close": range(10)}, index=idx)


def test_prepare_once_idempotent_per_dataframe_object_identity():
    """
    BaseStrategy.prepare_once() ist idempotent pro DataFrame-Objekt.

    Repo-Semantik (Stand jetzt):
    - "gleiches DataFrame" wird über Objekt-Identität (id(data)) erkannt.
    - df.copy() ist ein anderes Objekt -> prepare() muss erneut laufen.
    """
    s = _PrepareOnceProbeStrategy()
    df = _make_df()

    s.prepare_once(df)
    s.prepare_once(df)
    assert s.prepare_calls == 1

    out1 = s.run(df)
    out2 = s.run(df)
    assert s.prepare_calls == 1
    assert len(out1) == len(df)
    assert len(out2) == len(df)

    df2 = df.copy()
    s.prepare_once(df2)
    assert s.prepare_calls == 2
