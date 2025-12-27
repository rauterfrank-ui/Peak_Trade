"""
Tests für Covariance Estimation
================================
"""

import numpy as np
import pandas as pd
import pytest

from src.risk.covariance import (
    CovarianceEstimator,
    CovarianceEstimatorConfig,
    CovarianceMethod,
)


@pytest.fixture
def sample_returns():
    """Simple 3-asset returns für deterministische Tests."""
    np.random.seed(42)
    returns = np.random.randn(100, 3) * 0.02
    return pd.DataFrame(returns, columns=["A", "B", "C"])


def test_covariance_estimator_config_validation():
    """Test Config validation."""
    # Valid config
    cfg = CovarianceEstimatorConfig(method="sample", min_history=60)
    assert cfg.method == "sample"
    assert cfg.min_history == 60

    # Invalid min_history
    with pytest.raises(ValueError, match="min_history"):
        CovarianceEstimatorConfig(min_history=1)

    # Invalid shrinkage_alpha
    with pytest.raises(ValueError, match="shrinkage_alpha"):
        CovarianceEstimatorConfig(shrinkage_alpha=1.5)

    # Invalid method
    with pytest.raises(ValueError, match="Unknown method"):
        CovarianceEstimatorConfig(method="invalid")


def test_sample_covariance_shape_and_symmetry(sample_returns):
    """Test sample covariance shape und Symmetrie."""
    config = CovarianceEstimatorConfig(method="sample", min_history=50)
    estimator = CovarianceEstimator(config)

    cov = estimator.estimate(sample_returns)

    assert cov.shape == (3, 3)
    assert np.allclose(cov, cov.T)  # Symmetric
    assert np.all(np.diag(cov) > 0)  # Positive diagonal


def test_sample_covariance_insufficient_data():
    """Test ValueError bei zu wenig Daten."""
    config = CovarianceEstimatorConfig(method="sample", min_history=100)
    estimator = CovarianceEstimator(config)

    # Only 50 rows
    returns = pd.DataFrame(np.random.randn(50, 3), columns=["A", "B", "C"])

    with pytest.raises(ValueError, match="Insufficient data"):
        estimator.estimate(returns)


def test_diagonal_shrinkage_without_sklearn(sample_returns):
    """Test diagonal shrinkage (kein sklearn required)."""
    config = CovarianceEstimatorConfig(
        method="diagonal_shrink",
        min_history=50,
        shrinkage_alpha=0.2,
    )
    estimator = CovarianceEstimator(config)

    cov_shrunk = estimator.estimate(sample_returns)

    # Should be symmetric and PSD
    assert np.allclose(cov_shrunk, cov_shrunk.T)
    assert np.all(np.diag(cov_shrunk) > 0)

    # Compare to sample cov
    config_sample = CovarianceEstimatorConfig(method="sample", min_history=50)
    estimator_sample = CovarianceEstimator(config_sample)
    cov_sample = estimator_sample.estimate(sample_returns)

    # Off-diagonal elements should be shrunk towards zero
    off_diag_sample = np.abs(cov_sample - np.diag(np.diag(cov_sample))).sum()
    off_diag_shrunk = np.abs(cov_shrunk - np.diag(np.diag(cov_shrunk))).sum()
    assert off_diag_shrunk < off_diag_sample


def test_ledoit_wolf_requires_sklearn():
    """Test dass Ledoit-Wolf sklearn benötigt."""
    config = CovarianceEstimatorConfig(method="ledoit_wolf", min_history=50)
    estimator = CovarianceEstimator(config)

    returns = pd.DataFrame(np.random.randn(100, 3), columns=["A", "B", "C"])

    try:
        import sklearn.covariance  # noqa: F401

        # sklearn available -> should work
        cov = estimator.estimate(returns)
        assert cov.shape == (3, 3)
    except ImportError:
        # sklearn not available -> should raise ImportError with helpful message
        with pytest.raises(ImportError, match="scikit-learn"):
            estimator.estimate(returns)


def test_correlation_matrix_properties(sample_returns):
    """Test Korrelationsmatrix properties."""
    config = CovarianceEstimatorConfig(method="sample", min_history=50)
    estimator = CovarianceEstimator(config)

    corr = estimator.estimate_correlation(sample_returns)

    # Diagonal should be 1
    assert np.allclose(np.diag(corr), 1.0)

    # Off-diagonal should be in [-1, 1]
    mask = ~np.eye(corr.shape[0], dtype=bool)
    assert np.all(corr[mask] >= -1.0)
    assert np.all(corr[mask] <= 1.0)

    # Symmetric
    assert np.allclose(corr, corr.T)


def test_positive_definite_validation():
    """Test PD validation via Cholesky."""
    config = CovarianceEstimatorConfig(method="sample", min_history=50)
    estimator = CovarianceEstimator(config)

    # Valid PSD matrix
    returns = pd.DataFrame(np.random.randn(100, 3), columns=["A", "B", "C"])
    cov = estimator.estimate(returns, validate=True)  # Should not raise

    # Invalid matrix (manually construct non-PD)
    bad_cov = np.array([[1, 0.9, 0.9], [0.9, 1, 0.9], [0.9, 0.9, 1]])
    # This matrix is actually PD, so let's make it non-PD
    bad_cov = np.array([[1, 2], [2, 1]])  # Not PD (eigenvalues: 3, -1)

    with pytest.raises(ValueError, match="not positive definite"):
        estimator._validate_positive_definite(bad_cov)


def test_non_finite_values_raise_error():
    """Test dass inf/nan Values einen Error werfen."""
    config = CovarianceEstimatorConfig(method="sample", min_history=10)
    estimator = CovarianceEstimator(config)

    # Returns with NaN
    returns = pd.DataFrame(np.random.randn(50, 3), columns=["A", "B", "C"])
    returns.iloc[10, 1] = np.nan

    # After dropna, should still have enough data
    # But if all rows have NaN in at least one column, it will fail min_history check
    # Let's create a case where we have inf
    returns_clean = pd.DataFrame(np.random.randn(50, 3), columns=["A", "B", "C"])
    returns_clean.iloc[10, 1] = np.inf

    with pytest.raises(ValueError, match="non-finite"):
        estimator.estimate(returns_clean)


def test_covariance_method_enum():
    """Test CovarianceMethod Enum."""
    assert CovarianceMethod.SAMPLE == "sample"
    assert CovarianceMethod.LEDOIT_WOLF == "ledoit_wolf"
    assert CovarianceMethod.DIAGONAL_SHRINK == "diagonal_shrink"
