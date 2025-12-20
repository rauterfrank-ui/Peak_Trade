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
import socket
import sys
import uuid
from datetime import datetime, timezone
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class ReproContext:
    """
    Reproducibility context capturing environment state.

    Attributes:
        run_id: Unique run identifier (UUID)
        git_sha: Git commit SHA (None = not available)
        config_hash: Stable hash of config dict
        seed: Random seed (None = not set)
        dependencies_hash: Hash of requirements.txt (None = not available)
        timestamp: ISO format timestamp (UTC)
        hostname: Machine identifier
        python_version: Python version string
    """

    run_id: str
    git_sha: Optional[str]
    config_hash: str
    seed: Optional[int]
    dependencies_hash: Optional[str]
    timestamp: str
    hostname: str
    python_version: str

    @classmethod
    def create(
        cls,
        seed: Optional[int] = None,
        git_sha: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
        dependencies_hash: Optional[str] = None,
    ) -> "ReproContext":
        """
        Create a ReproContext from current environment.

        Args:
            seed: Random seed (None = not set)
            git_sha: Git commit SHA (None = auto-detect or not available)
            config_dict: Config dict to hash (None = empty dict)
            dependencies_hash: Hash of dependencies (None = auto-detect)

        Returns:
            ReproContext instance
        """
        # Auto-detect git SHA if not provided
        if git_sha is None:
            git_sha = _get_git_sha()

        # Hash config
        config_dict = config_dict or {}
        config_hash = _stable_hash_dict(config_dict)

        # Hash dependencies if not provided
        if dependencies_hash is None:
            dependencies_hash = hash_dependencies()

        # Capture Python version
        python_version = sys.version.split()[0]  # e.g., "3.9.6"

        # Generate unique run_id
        run_id = generate_run_id()

        # Capture timestamp (UTC)
        timestamp = datetime.now(timezone.utc).isoformat()

        # Capture hostname
        hostname = socket.gethostname()

        return cls(
            run_id=run_id,
            git_sha=git_sha,
            config_hash=config_hash,
            seed=seed,
            dependencies_hash=dependencies_hash,
            timestamp=timestamp,
            hostname=hostname,
            python_version=python_version,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReproContext":
        """
        Deserialize from dict.

        Args:
            data: Dictionary containing ReproContext fields

        Returns:
            ReproContext instance
        """
        return cls(**data)

    def save(self, path: Path) -> None:
        """
        Save to JSON file.

        Args:
            path: Path to JSON file (will be created/overwritten)
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "ReproContext":
        """
        Load from JSON file.

        Args:
            path: Path to JSON file

        Returns:
            ReproContext instance

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        path = Path(path)
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


def get_git_sha(short: bool = True) -> Optional[str]:
    """
    Get current git SHA.

    Args:
        short: If True, return short SHA (7 chars), else full SHA

    Returns:
        Git SHA or None if not in git repo

    Example:
        >>> sha = get_git_sha()  # 'abc1234'
        >>> sha_full = get_git_sha(short=False)  # 'abc1234567890...'
    """
    import subprocess

    try:
        cmd = ["git", "rev-parse", "HEAD"]
        if short:
            cmd.insert(2, "--short=7")

        result = subprocess.run(
            cmd,
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


def _get_git_sha() -> Optional[str]:
    """
    Get current git SHA (short form) - legacy wrapper.

    Returns:
        Git SHA (7 chars) or None if not in git repo
    """
    return get_git_sha(short=True)


def stable_hash_dict(d: Dict[str, Any], short: bool = True) -> str:
    """
    Compute stable SHA256 hash of dict.

    Implementation:
        1. Sort keys recursively
        2. Convert to canonical JSON (sorted keys, no whitespace)
        3. Hash JSON bytes

    Args:
        d: Dict to hash
        short: If True, return first 16 chars, else full hash

    Returns:
        SHA256 hex string (16 chars if short=True, 64 chars if short=False)

    Example:
        >>> config = {"seed": 42, "strategy": "ma_crossover"}
        >>> stable_hash_dict(config)  # '1a2b3c4d5e6f7g8h'
        >>> stable_hash_dict(config, short=False)  # '1a2b3c4d...(64 chars)'
    """
    # Canonical JSON: sorted keys, no whitespace
    canonical_json = json.dumps(d, sort_keys=True, separators=(",", ":"))
    sha256 = hashlib.sha256(canonical_json.encode("utf-8"))
    return sha256.hexdigest()[:16] if short else sha256.hexdigest()


def _stable_hash_dict(d: Dict[str, Any]) -> str:
    """
    Compute stable SHA256 hash of dict (short form) - legacy wrapper.

    Returns:
        SHA256 hex string (first 16 chars)
    """
    return stable_hash_dict(d, short=True)


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


def generate_run_id() -> str:
    """
    Generate unique run ID.

    Returns:
        Short UUID (8 chars) for readability

    Example:
        >>> run_id = generate_run_id()  # 'a1b2c3d4'
    """
    return str(uuid.uuid4())[:8]


def hash_dependencies() -> Optional[str]:
    """
    Hash requirements.txt for environment reproducibility.

    Returns:
        SHA256 hash (first 16 chars) or None if requirements.txt not found

    Example:
        >>> deps_hash = hash_dependencies()  # 'a1b2c3d4e5f6g7h8'
    """
    try:
        with open("requirements.txt", "r") as f:
            content = f.read()
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    except FileNotFoundError:
        return None


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
