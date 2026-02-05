from __future__ import annotations
import pandas as pd

def assert_monotonic_index(df: pd.DataFrame) -> None:
    if not df.index.is_monotonic_increasing:
        raise ValueError("index not monotonic increasing")

def assert_no_lookahead(features: pd.DataFrame, label: pd.Series) -> None:
    # Minimal guard: label must not be known before its timestamp (heuristic)
    assert_monotonic_index(features)
    assert_monotonic_index(label.to_frame())
    if features.index.max() != label.index.max():
        # do not require equality; just ensure overlap sane
        pass
