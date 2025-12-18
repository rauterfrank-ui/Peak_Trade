"""
Reproducibility Context & Seed Policy (Wave A - Stability Plan)
================================================================
Ensures deterministic execution for debugging and reproducibility.

Design:
- Central ReproContext captures environment state
- Seed policy sets seeds for random/numpy (torch optional guard)
- Stable config hashing (canonical JSON)
- run_id generation for tracing

Usage:
    from src.core.repro import ReproContext, set_global_seed

    # Create repro context
    ctx = ReproContext.create(seed=42, config_dict=my_config)
    print(ctx.run_id)  # Unique run identifier

    # Set global seeds (call once at start of run)
    set_global_seed(42)
"""
import hashlib
import json
import platform
import random
import sys
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class ReproContext:
    """
    Reproducibility context capturing environment state.

    Attributes:
        seed: Random seed (None = not set)
        git_sha: Git commit SHA (None = not available)
        config_hash: Stable hash of config dict
        python_version: Python version string
        platform: Platform string (e.g., "darwin", "linux")
        run_id: Unique run identifier (UUID)
    """

    seed: Optional[int]
    git_sha: Optional[str]
    config_hash: str
    python_version: str
    platform: str
    run_id: str

    @classmethod
    def create(
        cls,
        seed: Optional[int] = None,
        git_sha: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
    ) -> "ReproContext":
        """
        Create a ReproContext from current environment.

        Args:
            seed: Random seed (None = not set)
            git_sha: Git commit SHA (None = auto-detect or not available)
            config_dict: Config dict to hash (None = empty dict)

        Returns:
            ReproContext instance
        """
        # Auto-detect git SHA if not provided
        if git_sha is None:
            git_sha = _get_git_sha()

        # Hash config
        config_dict = config_dict or {}
        config_hash = _stable_hash_dict(config_dict)

        # Capture Python version and platform
        python_version = sys.version.split()[0]  # e.g., "3.9.6"
        platform_str = platform.system().lower()  # e.g., "darwin", "linux"

        # Generate unique run_id
        run_id = str(uuid.uuid4())

        return cls(
            seed=seed,
            git_sha=git_sha,
            config_hash=config_hash,
            python_version=python_version,
            platform=platform_str,
            run_id=run_id,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


def _get_git_sha() -> Optional[str]:
    """
    Get current git SHA (short form).

    Returns:
        Git SHA (7 chars) or None if not in git repo
    """
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short=7", "HEAD"],
            capture_output=True,
            text=True,
            timeout=1.0,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _stable_hash_dict(d: Dict[str, Any]) -> str:
    """
    Compute stable SHA256 hash of dict.

    Implementation:
        1. Sort keys recursively
        2. Convert to canonical JSON (sorted keys, no whitespace)
        3. Hash JSON bytes

    Args:
        d: Dict to hash

    Returns:
        SHA256 hex string (first 16 chars)
    """
    # Canonical JSON: sorted keys, no whitespace
    canonical_json = json.dumps(d, sort_keys=True, separators=(",", ":"))
    sha256 = hashlib.sha256(canonical_json.encode("utf-8"))
    return sha256.hexdigest()[:16]  # First 16 chars


def set_global_seed(seed: int) -> None:
    """
    Set global random seeds for determinism.

    Sets seeds for:
    - Python random module
    - NumPy (if available)
    - PyTorch (if available, with deterministic ops)

    Args:
        seed: Random seed (integer)

    Note:
        Call this ONCE at the start of your run, before any randomness.
    """
    # Python random
    random.seed(seed)

    # NumPy
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass

    # PyTorch (optional guard)
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        # Enable deterministic ops (may impact performance)
        torch.use_deterministic_algorithms(True, warn_only=True)
    except ImportError:
        pass


def verify_determinism(func, seed: int, num_runs: int = 2, **kwargs) -> bool:
    """
    Verify that a function produces deterministic results.

    Args:
        func: Function to test (must return comparable result)
        seed: Random seed to use
        num_runs: Number of runs to compare (default: 2)
        **kwargs: Arguments to pass to func

    Returns:
        True if all runs produce identical results

    Example:
        def my_random_func():
            return random.random()

        is_deterministic = verify_determinism(my_random_func, seed=42)
    """
    results = []
    for _ in range(num_runs):
        set_global_seed(seed)
        result = func(**kwargs)
        results.append(result)

    # Check if all results are identical
    first = results[0]
    return all(str(r) == str(first) for r in results)
