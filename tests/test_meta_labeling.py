"""Tests for src/research/ml/meta/meta_labeling.py (research-only)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.research.ml.meta.meta_labeling import (
    MetaModelSpec,
    apply_meta_model,
    compute_bet_size,
    compute_meta_labels,
    _create_model,
)


def test_apply_meta_model_passthrough_without_labels():
    signals = pd.Series([1, -1, 1, 0, -1])
    features = pd.DataFrame({"volatility": [0.1, 0.2, 0.15, 0.1, 0.25]})
    spec = MetaModelSpec(model_type="random_forest", min_confidence=0.6)
    result = apply_meta_model(signals, features, spec)
    pd.testing.assert_series_equal(result, signals)


def test_apply_meta_model_filters_with_trained_sklearn():
    from sklearn.ensemble import RandomForestClassifier

    rng = np.random.RandomState(42)
    n = 40
    X = rng.randn(n, 2)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    idx = pd.RangeIndex(n)
    signals = pd.Series(np.random.choice([-1, 0, 1], size=n), index=idx)
    features = pd.DataFrame(
        {"f0": X[:, 0], "f1": X[:, 1], "label": y},
        index=idx,
    )
    clf = RandomForestClassifier(n_estimators=20, random_state=42)
    clf.fit(X, y)
    spec = MetaModelSpec(
        model_type="random_forest",
        feature_cols=["f0", "f1"],
        target_col="label",
        min_confidence=0.99,
    )
    out = apply_meta_model(signals, features, spec, trained_model=clf)
    assert isinstance(out, pd.Series)
    assert len(out) == n
    assert (out != 0).sum() <= (signals != 0).sum()


def test_apply_meta_model_trains_when_label_present():
    rng = np.random.RandomState(0)
    n = 30
    idx = pd.RangeIndex(n)
    X = rng.randn(n, 1)
    y = (X[:, 0] > 0).astype(int)
    signals = pd.Series(np.ones(n), index=idx)
    features = pd.DataFrame({"feat": X[:, 0], "label": y}, index=idx)
    spec = MetaModelSpec(
        model_type="random_forest",
        feature_cols=["feat"],
        min_confidence=0.5,
    )
    out = apply_meta_model(signals, features, spec)
    assert len(out) == n


def test_create_model_random_forest():
    spec = MetaModelSpec(model_type="random_forest", hyperparams={"n_estimators": 5})
    m = _create_model(spec)
    assert m.__class__.__name__ == "RandomForestClassifier"


def test_compute_meta_labels_basic():
    sig = pd.Series([1, 0, -1])
    tb = pd.Series([1, -1, 1])
    ml = compute_meta_labels(sig, tb)
    assert ml.iloc[0] == 1
    assert pd.isna(ml.iloc[1])
    assert ml.iloc[2] == 1


def test_compute_bet_size_sigmoid():
    p = np.array([0.0, 0.5, 1.0])
    b = compute_bet_size(p, method="sigmoid", max_bet=1.0)
    assert b.shape == p.shape
    assert np.all((b >= 0) & (b <= 1.0))


def test_xgboost_missing_raises():
    spec = MetaModelSpec(model_type="xgboost")
    try:
        import xgboost  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError):
            _create_model(spec)
    else:
        m = _create_model(spec)
        assert "XGB" in m.__class__.__name__ or "XGB" in type(m).__name__
