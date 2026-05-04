"""Contract tests for ``create_dummy_returns`` — local RNG, no global mutation (v0).

Offline dummy helper only. No network, subprocess, or live trading paths.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.experiments.dummy_returns_timeline import (
    DUMMY_RETURNS_TIMELINE_START,
    create_dummy_returns,
)


def test_create_dummy_returns_same_seed_is_deterministic_contract_v0() -> None:
    a = create_dummy_returns(120, seed=7)
    b = create_dummy_returns(120, seed=7)
    pd.testing.assert_series_equal(a, b)


@pytest.mark.parametrize(("seed_a", "seed_b"), [(1, 99), (0, 100)])
def test_create_dummy_returns_different_seeds_same_index_different_values_contract_v0(
    seed_a: int,
    seed_b: int,
) -> None:
    a = create_dummy_returns(48, seed=seed_a)
    b = create_dummy_returns(48, seed=seed_b)
    pd.testing.assert_index_equal(a.index, b.index)
    assert a.index[0] == DUMMY_RETURNS_TIMELINE_START
    assert not np.allclose(a.to_numpy(), b.to_numpy())


def test_create_dummy_returns_does_not_mutate_global_numpy_rng_contract_v0() -> None:
    np.random.seed(100)
    expected_first = float(np.random.random())
    expected_second = float(np.random.random())
    np.random.seed(100)
    assert float(np.random.random()) == expected_first
    create_dummy_returns(30, seed=999_001)
    assert float(np.random.random()) == expected_second
