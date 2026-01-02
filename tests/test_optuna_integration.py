"""
Tests for Optuna Integration (Phase 3)
=======================================
Tests für run_optuna_study.py und Parameter-Schema → Optuna Mapping.

**Test Coverage**:
- Parameter-Schema → Optuna Search Space Conversion
- Single-Objective Optimization
- Multi-Objective Optimization
- Pruning Callbacks
- Storage Backends
- Error Handling (missing schema, invalid params)
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from src.strategies.parameters import Param

# Conditional imports
try:
    import optuna
    from optuna.trial import Trial

    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    optuna = None
    Trial = None

# Import study runner functions
try:
    from run_optuna_study import (
        check_optuna_available,
        create_pruner,
        create_sampler,
        suggest_params_from_schema,
    )

    STUDY_RUNNER_AVAILABLE = True
except ImportError:
    STUDY_RUNNER_AVAILABLE = False


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_param_schema():
    """Sample parameter schema for testing."""
    return [
        Param(name="fast_window", kind="int", default=20, low=5, high=50),
        Param(name="slow_window", kind="int", default=50, low=20, high=200),
        Param(name="threshold", kind="float", default=0.02, low=0.01, high=0.1),
        Param(name="use_filter", kind="bool", default=True),
        Param(name="mode", kind="choice", default="fast", choices=["fast", "slow", "adaptive"]),
    ]


@pytest.fixture
def mock_strategy(sample_param_schema):
    """Mock strategy with parameter_schema."""
    strategy = MagicMock()
    strategy.parameter_schema = sample_param_schema
    strategy.__class__.__name__ = "MockStrategy"
    return strategy


# ============================================================================
# Test: Optuna Availability Check
# ============================================================================


@pytest.mark.skipif(not STUDY_RUNNER_AVAILABLE, reason="run_optuna_study.py not available")
def test_check_optuna_available_raises_if_not_installed():
    """Test that check_optuna_available() raises SystemExit if Optuna not installed."""
    with patch("run_optuna_study.OPTUNA_AVAILABLE", False):
        with pytest.raises(SystemExit):
            check_optuna_available()


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
@pytest.mark.skipif(not STUDY_RUNNER_AVAILABLE, reason="run_optuna_study.py not available")
def test_check_optuna_available_passes_if_installed():
    """Test that check_optuna_available() passes if Optuna installed."""
    # Should not raise
    check_optuna_available()


# ============================================================================
# Test: Pruner Creation
# ============================================================================


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
@pytest.mark.skipif(not STUDY_RUNNER_AVAILABLE, reason="run_optuna_study.py not available")
def test_create_pruner_noop():
    """Test NopPruner creation."""
    pruner = create_pruner("none")
    assert isinstance(pruner, optuna.pruners.NopPruner)


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
@pytest.mark.skipif(not STUDY_RUNNER_AVAILABLE, reason="run_optuna_study.py not available")
def test_create_pruner_median():
    """Test MedianPruner creation."""
    pruner = create_pruner("median")
    assert isinstance(pruner, optuna.pruners.MedianPruner)


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
@pytest.mark.skipif(not STUDY_RUNNER_AVAILABLE, reason="run_optuna_study.py not available")
def test_create_pruner_hyperband():
    """Test HyperbandPruner creation."""
    pruner = create_pruner("hyperband")
    assert isinstance(pruner, optuna.pruners.HyperbandPruner)


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
@pytest.mark.skipif(not STUDY_RUNNER_AVAILABLE, reason="run_optuna_study.py not available")
def test_create_pruner_invalid_raises():
    """Test that invalid pruner type raises ValueError."""
    with pytest.raises(ValueError, match="Unknown pruner type"):
        create_pruner("invalid")


# ============================================================================
# Test: Sampler Creation
# ============================================================================


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
@pytest.mark.skipif(not STUDY_RUNNER_AVAILABLE, reason="run_optuna_study.py not available")
def test_create_sampler_tpe():
    """Test TPESampler creation."""
    sampler = create_sampler("tpe", seed=42)
    assert isinstance(sampler, optuna.samplers.TPESampler)


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
@pytest.mark.skipif(not STUDY_RUNNER_AVAILABLE, reason="run_optuna_study.py not available")
def test_create_sampler_random():
    """Test RandomSampler creation."""
    sampler = create_sampler("random", seed=42)
    assert isinstance(sampler, optuna.samplers.RandomSampler)


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
@pytest.mark.skipif(not STUDY_RUNNER_AVAILABLE, reason="run_optuna_study.py not available")
def test_create_sampler_grid():
    """Test GridSampler creation."""
    sampler = create_sampler("grid", seed=42)
    # GridSampler requires search_space, so it might fail without it
    # Just check it's created
    assert sampler is not None


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
@pytest.mark.skipif(not STUDY_RUNNER_AVAILABLE, reason="run_optuna_study.py not available")
def test_create_sampler_invalid_raises():
    """Test that invalid sampler type raises ValueError."""
    with pytest.raises(ValueError, match="Unknown sampler type"):
        create_sampler("invalid")


# ============================================================================
# Test: Parameter Schema → Optuna Suggest
# ============================================================================


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
@pytest.mark.skipif(not STUDY_RUNNER_AVAILABLE, reason="run_optuna_study.py not available")
def test_suggest_params_from_schema(mock_strategy):
    """Test parameter suggestion from schema."""
    # Create a study and trial
    study = optuna.create_study(direction="maximize")
    trial = study.ask()

    # Suggest params
    params = suggest_params_from_schema(trial, mock_strategy)

    # Check all params are present
    assert "fast_window" in params
    assert "slow_window" in params
    assert "threshold" in params
    assert "use_filter" in params
    assert "mode" in params

    # Check types
    assert isinstance(params["fast_window"], int)
    assert isinstance(params["slow_window"], int)
    assert isinstance(params["threshold"], float)
    assert isinstance(params["use_filter"], bool)
    assert params["mode"] in ["fast", "slow", "adaptive"]

    # Check ranges
    assert 5 <= params["fast_window"] <= 50
    assert 20 <= params["slow_window"] <= 200
    assert 0.01 <= params["threshold"] <= 0.1


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
@pytest.mark.skipif(not STUDY_RUNNER_AVAILABLE, reason="run_optuna_study.py not available")
def test_suggest_params_from_schema_empty_raises(mock_strategy):
    """Test that empty schema raises ValueError."""
    mock_strategy.parameter_schema = []

    study = optuna.create_study(direction="maximize")
    trial = study.ask()

    with pytest.raises(ValueError, match="has no parameter_schema"):
        suggest_params_from_schema(trial, mock_strategy)


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
@pytest.mark.skipif(not STUDY_RUNNER_AVAILABLE, reason="run_optuna_study.py not available")
def test_suggest_params_from_schema_none_raises(mock_strategy):
    """Test that None schema raises ValueError."""
    mock_strategy.parameter_schema = None

    study = optuna.create_study(direction="maximize")
    trial = study.ask()

    with pytest.raises(ValueError, match="has no parameter_schema"):
        suggest_params_from_schema(trial, mock_strategy)


# ============================================================================
# Test: Param.to_optuna_suggest() for all types
# ============================================================================


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
def test_param_to_optuna_suggest_int():
    """Test Param.to_optuna_suggest() for int type."""
    param = Param(name="window", kind="int", default=20, low=5, high=50)

    study = optuna.create_study()
    trial = study.ask()

    value = param.to_optuna_suggest(trial)
    assert isinstance(value, int)
    assert 5 <= value <= 50


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
def test_param_to_optuna_suggest_float():
    """Test Param.to_optuna_suggest() for float type."""
    param = Param(name="threshold", kind="float", default=0.02, low=0.01, high=0.1)

    study = optuna.create_study()
    trial = study.ask()

    value = param.to_optuna_suggest(trial)
    assert isinstance(value, float)
    assert 0.01 <= value <= 0.1


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
def test_param_to_optuna_suggest_choice():
    """Test Param.to_optuna_suggest() for choice type."""
    param = Param(name="mode", kind="choice", default="fast", choices=["fast", "slow", "adaptive"])

    study = optuna.create_study()
    trial = study.ask()

    value = param.to_optuna_suggest(trial)
    assert value in ["fast", "slow", "adaptive"]


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
def test_param_to_optuna_suggest_bool():
    """Test Param.to_optuna_suggest() for bool type."""
    param = Param(name="use_filter", kind="bool", default=True)

    study = optuna.create_study()
    trial = study.ask()

    value = param.to_optuna_suggest(trial)
    assert isinstance(value, bool)


# ============================================================================
# Test: Single-Objective Study (Integration)
# ============================================================================


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
@pytest.mark.slow
def test_single_objective_study_integration():
    """
    Integration test: Run a small single-objective study.

    Note: This is a slow test, marked with @pytest.mark.slow.
    """

    # Create a simple objective function
    def objective(trial):
        x = trial.suggest_float("x", -10, 10)
        return (x - 2) ** 2  # Minimize (x-2)^2, optimal at x=2

    # Create study
    study = optuna.create_study(direction="minimize")

    # Run optimization
    study.optimize(objective, n_trials=20, show_progress_bar=False)

    # Check results
    assert len(study.trials) == 20
    assert study.best_value < 1.0  # Should find near-optimal solution
    assert 1.0 <= study.best_params["x"] <= 3.0  # Should be near x=2


# ============================================================================
# Test: Multi-Objective Study (Integration)
# ============================================================================


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
@pytest.mark.slow
def test_multi_objective_study_integration():
    """
    Integration test: Run a small multi-objective study.

    Note: This is a slow test, marked with @pytest.mark.slow.
    """

    # Create a multi-objective function
    def objective(trial):
        x = trial.suggest_float("x", -10, 10)
        # Objective 1: Minimize (x-2)^2
        # Objective 2: Minimize (x+3)^2
        # Pareto front: tradeoff between x=2 and x=-3
        return (x - 2) ** 2, (x + 3) ** 2

    # Create study
    study = optuna.create_study(directions=["minimize", "minimize"])

    # Run optimization
    study.optimize(objective, n_trials=30, show_progress_bar=False)

    # Check results
    assert len(study.trials) == 30
    assert len(study.best_trials) > 0  # Should have Pareto front

    # Check that best trials span the Pareto front
    best_x_values = [t.params["x"] for t in study.best_trials]
    assert min(best_x_values) < 0  # Should explore x < 0
    assert max(best_x_values) > 0  # Should explore x > 0


# ============================================================================
# Test: Pruning Integration
# ============================================================================


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
@pytest.mark.slow
def test_pruning_integration():
    """
    Integration test: Verify pruning works.

    Note: This is a slow test, marked with @pytest.mark.slow.
    """

    # Create objective that reports intermediate values
    def objective(trial):
        x = trial.suggest_float("x", -10, 10)

        # Report intermediate values (simulate iterative optimization)
        for step in range(10):
            intermediate_value = (x - 2) ** 2 + step * 0.1
            trial.report(intermediate_value, step)

            # Check if should prune
            if trial.should_prune():
                raise optuna.TrialPruned()

        return (x - 2) ** 2

    # Create study with MedianPruner
    study = optuna.create_study(
        direction="minimize",
        pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=3),
    )

    # Run optimization
    study.optimize(objective, n_trials=20, show_progress_bar=False)

    # Check that some trials were pruned
    pruned_trials = [t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED]
    assert len(pruned_trials) > 0, "Expected some trials to be pruned"


# ============================================================================
# Test: Storage Backend
# ============================================================================


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
def test_storage_backend_in_memory():
    """Test in-memory storage (default)."""
    study = optuna.create_study(direction="maximize")

    def objective(trial):
        return trial.suggest_float("x", 0, 1)

    study.optimize(objective, n_trials=5, show_progress_bar=False)

    assert len(study.trials) == 5


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
def test_storage_backend_sqlite(tmp_path):
    """Test SQLite storage backend."""
    db_path = tmp_path / "optuna_test.db"
    storage = f"sqlite:///{db_path}"

    # Create study
    study = optuna.create_study(
        study_name="test_study",
        storage=storage,
        direction="maximize",
        load_if_exists=False,
    )

    def objective(trial):
        return trial.suggest_float("x", 0, 1)

    study.optimize(objective, n_trials=5, show_progress_bar=False)

    assert len(study.trials) == 5
    assert db_path.exists()

    # Load study from storage
    loaded_study = optuna.load_study(study_name="test_study", storage=storage)
    assert len(loaded_study.trials) == 5


# ============================================================================
# Test: Error Handling
# ============================================================================


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="Optuna not installed")
def test_failed_trial_handling():
    """Test that failed trials are handled gracefully."""

    def objective(trial):
        x = trial.suggest_float("x", 0, 10)
        if x > 5:
            raise ValueError("Simulated failure")
        return x

    study = optuna.create_study(direction="minimize")

    # Run optimization (some trials will fail)
    study.optimize(objective, n_trials=10, show_progress_bar=False, catch=(ValueError,))

    # Check that some trials failed
    failed_trials = [t for t in study.trials if t.state == optuna.trial.TrialState.FAIL]
    complete_trials = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]

    assert len(failed_trials) > 0, "Expected some trials to fail"
    assert len(complete_trials) > 0, "Expected some trials to complete"


# ============================================================================
# Markers for slow tests
# ============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
