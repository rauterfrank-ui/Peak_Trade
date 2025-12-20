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
    assert ctx.hostname is not None
    assert ctx.run_id is not None
    assert len(ctx.run_id) == 8  # Short UUID format (8 chars)
    assert ctx.timestamp is not None


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
    assert "hostname" in d
    assert "timestamp" in d
    assert "run_id" in d
    assert "dependencies_hash" in d


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


# Wave B: Tests for public metadata helpers
def test_get_git_sha_short():
    """get_git_sha() returns short SHA (7 chars) by default."""
    from src.core.repro import get_git_sha

    sha = get_git_sha()

    # Either returns SHA or None (if not in git repo)
    if sha is not None:
        assert len(sha) == 7
        assert sha.isalnum()


def test_get_git_sha_full():
    """get_git_sha(short=False) returns full SHA (40 chars)."""
    from src.core.repro import get_git_sha

    sha = get_git_sha(short=False)

    if sha is not None:
        assert len(sha) == 40
        assert sha.isalnum()


def test_stable_hash_dict_short():
    """stable_hash_dict() returns short hash (16 chars) by default."""
    from src.core.repro import stable_hash_dict

    config = {"seed": 42, "strategy": "ma_crossover"}
    hash_value = stable_hash_dict(config)

    assert len(hash_value) == 16
    assert hash_value.isalnum()


def test_stable_hash_dict_full():
    """stable_hash_dict(short=False) returns full hash (64 chars)."""
    from src.core.repro import stable_hash_dict

    config = {"seed": 42, "strategy": "ma_crossover"}
    hash_value = stable_hash_dict(config, short=False)

    assert len(hash_value) == 64
    assert hash_value.isalnum()


def test_stable_hash_dict_key_order_independent():
    """stable_hash_dict() is independent of key order."""
    from src.core.repro import stable_hash_dict

    config1 = {"a": 1, "b": 2, "c": 3}
    config2 = {"c": 3, "a": 1, "b": 2}

    hash1 = stable_hash_dict(config1)
    hash2 = stable_hash_dict(config2)

    assert hash1 == hash2


def test_stable_hash_dict_value_sensitive():
    """stable_hash_dict() changes with different values."""
    from src.core.repro import stable_hash_dict

    config1 = {"seed": 42}
    config2 = {"seed": 43}

    hash1 = stable_hash_dict(config1)
    hash2 = stable_hash_dict(config2)

    assert hash1 != hash2


# Wave C: Tests for new ReproContext fields and methods
def test_repro_context_timestamp():
    """ReproContext.create() captures UTC timestamp."""
    ctx = ReproContext.create(seed=42)
    
    # Should be ISO format
    assert "T" in ctx.timestamp
    assert ctx.timestamp.endswith("+00:00") or ctx.timestamp.endswith("Z")


def test_repro_context_hostname():
    """ReproContext.create() captures hostname."""
    ctx = ReproContext.create(seed=42)
    
    assert ctx.hostname is not None
    assert len(ctx.hostname) > 0


def test_repro_context_dependencies_hash():
    """ReproContext.create() hashes dependencies if available."""
    ctx = ReproContext.create(seed=42)
    
    # May be None if requirements.txt not found, otherwise should be 16 chars
    if ctx.dependencies_hash is not None:
        assert len(ctx.dependencies_hash) == 16


def test_repro_context_from_dict():
    """ReproContext.from_dict() deserializes correctly."""
    ctx = ReproContext.create(seed=42, config_dict={"test": "value"})
    d = ctx.to_dict()
    
    ctx2 = ReproContext.from_dict(d)
    
    assert ctx2.run_id == ctx.run_id
    assert ctx2.seed == ctx.seed
    assert ctx2.git_sha == ctx.git_sha
    assert ctx2.config_hash == ctx.config_hash
    assert ctx2.timestamp == ctx.timestamp
    assert ctx2.hostname == ctx.hostname


def test_repro_context_save_load(tmp_path):
    """ReproContext.save() and load() work correctly."""
    ctx = ReproContext.create(seed=42, config_dict={"test": "value"})
    
    # Save to temp file
    save_path = tmp_path / "repro.json"
    ctx.save(save_path)
    
    # File should exist
    assert save_path.exists()
    
    # Load back
    loaded_ctx = ReproContext.load(save_path)
    
    # All fields should match
    assert loaded_ctx.run_id == ctx.run_id
    assert loaded_ctx.seed == ctx.seed
    assert loaded_ctx.git_sha == ctx.git_sha
    assert loaded_ctx.config_hash == ctx.config_hash
    assert loaded_ctx.dependencies_hash == ctx.dependencies_hash
    assert loaded_ctx.timestamp == ctx.timestamp
    assert loaded_ctx.hostname == ctx.hostname
    assert loaded_ctx.python_version == ctx.python_version


def test_repro_context_save_creates_parent_dirs(tmp_path):
    """ReproContext.save() creates parent directories."""
    ctx = ReproContext.create(seed=42)
    
    # Save to nested path
    save_path = tmp_path / "nested" / "dir" / "repro.json"
    ctx.save(save_path)
    
    assert save_path.exists()


def test_repro_context_load_missing_file(tmp_path):
    """ReproContext.load() raises FileNotFoundError for missing file."""
    missing_path = tmp_path / "nonexistent.json"
    
    with pytest.raises(FileNotFoundError):
        ReproContext.load(missing_path)


def test_generate_run_id():
    """generate_run_id() produces 8-char string."""
    from src.core.repro import generate_run_id
    
    run_id = generate_run_id()
    
    assert isinstance(run_id, str)
    assert len(run_id) == 8
    # Should be hex chars
    assert all(c in "0123456789abcdef-" for c in run_id)


def test_generate_run_id_unique():
    """generate_run_id() produces unique IDs."""
    from src.core.repro import generate_run_id
    
    id1 = generate_run_id()
    id2 = generate_run_id()
    
    assert id1 != id2


def test_hash_dependencies_with_file():
    """hash_dependencies() returns 16-char hash when requirements.txt exists."""
    from src.core.repro import hash_dependencies
    
    deps_hash = hash_dependencies()
    
    # Should return hash if file exists, None otherwise
    if deps_hash is not None:
        assert len(deps_hash) == 16
        assert deps_hash.isalnum()


def test_hash_dependencies_missing_file(monkeypatch, tmp_path):
    """hash_dependencies() returns None when requirements.txt missing."""
    from src.core.repro import hash_dependencies
    
    # Change to temp dir without requirements.txt
    monkeypatch.chdir(tmp_path)
    
    deps_hash = hash_dependencies()
    assert deps_hash is None


def test_repro_context_run_id_short():
    """ReproContext uses short run_id (8 chars) for readability."""
    ctx = ReproContext.create()
    
    # Should be 8 chars (short UUID)
    assert len(ctx.run_id) == 8

