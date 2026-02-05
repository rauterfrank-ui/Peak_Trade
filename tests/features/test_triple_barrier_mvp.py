import pandas as pd

from src.research.ml.labeling import compute_triple_barrier_labels


def test_triple_barrier_basic_contract():
    close = pd.Series([100, 101, 102, 99, 98, 103], index=pd.RangeIndex(6), name="close")
    signals = pd.Series([1, 0, 0, 0, 0, 0], index=close.index, name="signal")  # long entry at 0
    y = compute_triple_barrier_labels(
        prices=close,
        signals=signals,
        take_profit=0.02,
        stop_loss=0.02,
        vertical_barrier_bars=3,
    )
    assert y.dtype.name == "Int64"
    assert int(y.iloc[0]) == 1


def test_triple_barrier_stop_loss_first_long():
    from src.research.ml.labeling import compute_triple_barrier_labels

    close = pd.Series([100, 99, 98, 97, 96, 95], index=pd.RangeIndex(6), name="close")
    signals = pd.Series([1, 0, 0, 0, 0, 0], index=close.index, name="signal")
    y = compute_triple_barrier_labels(
        prices=close,
        signals=signals,
        take_profit=0.02,
        stop_loss=0.02,
        vertical_barrier_bars=3,
    )
    assert int(y.iloc[0]) == -1
