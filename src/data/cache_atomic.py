"""
Atomic Cache Operations (Wave A - Stability Plan)
==================================================
Atomic writes with optional checksums for corruption detection.

Design:
- Write to temp file first
- fsync() to ensure data is on disk
- Atomic rename (POSIX guarantees)
- Optional SHA256 checksum stored as .sha256 sidecar file

Usage:
    from src.data.cache_atomic import atomic_write, atomic_read

    # Write with checksum
    atomic_write(df, "path/to/file.parquet", checksum=True)

    # Read with checksum verification
    df = atomic_read("path/to/file.parquet", verify_checksum=True)
"""
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Optional

import pandas as pd

from src.core.errors import CacheCorruptionError


def _compute_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def _checksum_path(filepath: str) -> str:
    """Get path to checksum sidecar file."""
    return f"{filepath}.sha256"


def atomic_write(
    df: pd.DataFrame,
    filepath: str,
    checksum: bool = False,
    compression: str = "snappy",
) -> None:
    """
    Atomically write DataFrame to Parquet with optional checksum.

    Args:
        df: DataFrame to write
        filepath: Target file path
        checksum: If True, write SHA256 checksum sidecar file
        compression: Parquet compression (default: snappy)

    Raises:
        CacheCorruptionError: If write fails or checksum cannot be written

    Implementation:
        1. Write to temp file in same directory (ensures same filesystem)
        2. fsync() to flush data to disk
        3. Atomic rename (POSIX guarantee)
        4. If checksum=True: compute SHA256 and write .sha256 sidecar
    """
    target_path = Path(filepath)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Use temp file in same directory (required for atomic rename)
    temp_fd, temp_path = tempfile.mkstemp(
        dir=target_path.parent,
        prefix=f".tmp_{target_path.stem}_",
        suffix=".parquet",
    )

    try:
        # Close fd immediately, pandas will reopen
        os.close(temp_fd)

        # Write to temp file
        df.to_parquet(temp_path, compression=compression, index=True)

        # fsync to ensure data is on disk
        with open(temp_path, "rb") as f:
            os.fsync(f.fileno())

        # Atomic rename (overwrites existing file)
        os.replace(temp_path, filepath)

        # Optional: Write checksum sidecar
        if checksum:
            checksum_value = _compute_checksum(filepath)
            checksum_file = _checksum_path(filepath)

            # Write checksum atomically too
            with open(checksum_file + ".tmp", "w") as f:
                f.write(checksum_value)
                f.flush()
                os.fsync(f.fileno())

            os.replace(checksum_file + ".tmp", checksum_file)

    except Exception as exc:
        # Clean up temp file on failure
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise CacheCorruptionError(
            f"Failed to write cache file: {filepath}",
            hint="Check disk space and permissions",
            context={"filepath": filepath, "error": str(exc)},
        ) from exc


def atomic_read(
    filepath: str,
    verify_checksum: bool = False,
) -> pd.DataFrame:
    """
    Read DataFrame from Parquet with optional checksum verification.

    Args:
        filepath: Path to Parquet file
        verify_checksum: If True, verify SHA256 checksum from .sha256 sidecar

    Returns:
        DataFrame loaded from file

    Raises:
        FileNotFoundError: If file doesn't exist
        CacheCorruptionError: If checksum verification fails

    Implementation:
        1. Check if file exists
        2. If verify_checksum: load .sha256 sidecar and compare
        3. Read Parquet file
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cache file not found: {filepath}")

    # Verify checksum before reading (fail fast)
    if verify_checksum:
        checksum_file = _checksum_path(filepath)

        if not os.path.exists(checksum_file):
            raise CacheCorruptionError(
                f"Checksum file missing: {checksum_file}",
                hint="Re-generate cache with checksum=True",
                context={"filepath": filepath, "checksum_file": checksum_file},
            )

        # Load expected checksum
        with open(checksum_file, "r") as f:
            expected_checksum = f.read().strip()

        # Compute actual checksum
        actual_checksum = _compute_checksum(filepath)

        if actual_checksum != expected_checksum:
            raise CacheCorruptionError(
                f"Checksum mismatch for {filepath}",
                hint="Delete corrupted cache file and re-generate",
                context={
                    "filepath": filepath,
                    "expected": expected_checksum,
                    "actual": actual_checksum,
                },
            )

    # Read file
    try:
        return pd.read_parquet(filepath)
    except Exception as exc:
        raise CacheCorruptionError(
            f"Failed to read cache file: {filepath}",
            hint="File may be corrupted. Delete and re-generate cache.",
            context={"filepath": filepath, "error": str(exc)},
        ) from exc
