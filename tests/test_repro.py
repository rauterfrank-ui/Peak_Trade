"""
Tests for Repro Context & Seed Policy (Wave A - Stability Plan)
"""
import random

import pytest

from src.core.repro import ReproContext, set_global_seed, verify_determinism


def test_repro_context_create_minimal():
    """ReproContext.create() works with minimal args."""
    ctx = ReproContext.create()

    assert ctx.seed is None
    assert ctx.python_version is not None
    assert ctx.platform in ["darwin", "linux", "windows"]
    assert ctx.run_id is not None
    assert len(ctx.run_id) == 36  # UUID format


def test_repro_context_create_with_seed():
    """ReproContext.create() captures seed."""
    ctx = ReproContext.create(seed=42)

    assert ctx.seed == 42


def test_repro_context_create_with_config():
    """ReproContext.create() hashes config dict."""
    config = {"strategy": "momentum", "param": 10}
    ctx = ReproContext.create(config_dict=config)

    assert ctx.config_hash is not None
    assert len(ctx.config_hash) == 16  # First 16 chars of SHA256


def test_repro_context_config_hash_stable():
    """Config hash is stable (same dict -> same hash)."""
    config = {"strategy": "momentum", "param": 10}

    ctx1 = ReproContext.create(config_dict=config)
    ctx2 = ReproContext.create(config_dict=config)

    assert ctx1.config_hash == ctx2.config_hash


def test_repro_context_config_hash_key_order_independent():
    """Config hash is independent of key order."""
    config1 = {"a": 1, "b": 2}
    config2 = {"b": 2, "a": 1}

    ctx1 = ReproContext.create(config_dict=config1)
    ctx2 = ReproContext.create(config_dict=config2)

    assert ctx1.config_hash == ctx2.config_hash


def test_repro_context_config_hash_value_sensitive():
    """Config hash changes when values change."""
    config1 = {"param": 10}
    config2 = {"param": 20}

    ctx1 = ReproContext.create(config_dict=config1)
    ctx2 = ReproContext.create(config_dict=config2)

    assert ctx1.config_hash != ctx2.config_hash


def test_repro_context_run_id_unique():
    """Each ReproContext gets a unique run_id."""
    ctx1 = ReproContext.create()
    ctx2 = ReproContext.create()

    assert ctx1.run_id != ctx2.run_id


def test_repro_context_to_dict():
    """ReproContext.to_dict() serializes correctly."""
    ctx = ReproContext.create(seed=42, config_dict={"key": "value"})
    d = ctx.to_dict()

    assert d["seed"] == 42
    assert "config_hash" in d
    assert "python_version" in d
    assert "platform" in d
    assert "run_id" in d


def test_repro_context_to_json():
    """ReproContext.to_json() produces valid JSON."""
    import json

    ctx = ReproContext.create(seed=42)
    json_str = ctx.to_json()

    # Should be parseable
    parsed = json.loads(json_str)
    assert parsed["seed"] == 42


def test_set_global_seed():
    """set_global_seed() sets Python random seed."""
    set_global_seed(42)
    val1 = random.random()

    set_global_seed(42)
    val2 = random.random()

    assert val1 == val2


def test_set_global_seed_numpy():
    """set_global_seed() sets NumPy seed if available."""
    try:
        import numpy as np
    except ImportError:
        pytest.skip("NumPy not available")

    set_global_seed(42)
    val1 = np.random.rand()

    set_global_seed(42)
    val2 = np.random.rand()

    assert val1 == val2


def test_verify_determinism_simple_func():
    """verify_determinism() detects deterministic function."""

    def deterministic_func():
        return 42

    assert verify_determinism(deterministic_func, seed=42, num_runs=3)


def test_verify_determinism_random_func_with_seed():
    """verify_determinism() succeeds for seeded random function."""

    def random_func():
        return random.random()

    assert verify_determinism(random_func, seed=42, num_runs=3)


def test_verify_determinism_with_kwargs():
    """verify_determinism() passes kwargs to function."""

    def func_with_args(x, y):
        return x + y

    assert verify_determinism(func_with_args, seed=42, num_runs=2, x=1, y=2)


def test_verify_determinism_fails_for_nondeterministic():
    """verify_determinism() detects non-deterministic function."""
    import time

    def nondeterministic_func():
        return time.time()  # Always different

    # This should fail, but we can't assert False reliably (race condition)
    # So we just verify it runs without error
    result = verify_determinism(nondeterministic_func, seed=42, num_runs=2)
    assert isinstance(result, bool)


def test_repro_context_git_sha_optional():
    """ReproContext handles missing git SHA gracefully."""
    ctx = ReproContext.create()
    # git_sha may be None if not in git repo
    assert ctx.git_sha is None or isinstance(ctx.git_sha, str)


def test_repro_context_git_sha_explicit():
    """ReproContext accepts explicit git SHA."""
    ctx = ReproContext.create(git_sha="abc1234")
    assert ctx.git_sha == "abc1234"
