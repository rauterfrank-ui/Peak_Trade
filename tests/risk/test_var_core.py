import numpy as np
import pytest

from src.risk.var_core import compute_var


def test_var_historical_basic():
    rng = np.random.default_rng(123)
    r = rng.normal(0.0, 0.01, size=10_000)
    res = compute_var(r, alpha=0.99, method="historical")
    assert res.var > 0
    assert res.sample_size == 10_000


def test_var_requires_min_samples():
    r = np.array([0.0] * 10)
    with pytest.raises(ValueError):
        compute_var(r)


def test_var_parametric_zero_sigma():
    r = np.zeros(1000)
    res = compute_var(r, method="parametric_normal")
    assert res.var == 0.0
