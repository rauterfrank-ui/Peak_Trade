"""
Cache Manifest System (Wave B - Stability Plan)
================================================
Tracks cache files with checksums, schema versions, and metadata per run_id.

Design:
- Each cache operation generates/updates a manifest.json
- Manifest includes: run_id, files, checksums, schema_version, timestamps
- Enables cache validation, staleness detection, and reproducibility tracking

Schema:
    {
        "manifest_version": "1.0",
        "run_id": "unique_run_identifier",
        "created_at": "ISO8601 timestamp",
        "updated_at": "ISO8601 timestamp",
        "git_sha": "commit hash (optional)",
        "config_hash": "SHA256 of config (optional)",
        "python_version": "3.9.6",
        "platform": "darwin",
        "files": [
            {
                "path": "relative/path/to/file.parquet",
                "checksum": "sha256:abc123...",
                "size_bytes": 12345,
                "schema_version": "v1",
                "created_at": "ISO8601 timestamp"
            }
        ]
    }

Usage:
    from src.data.cache_manifest import CacheManifest, add_file_to_manifest

    # Create or load manifest
    manifest = CacheManifest.load_or_create("cache/run_123")

    # Add file after writing cache
    manifest.add_file(
        filepath="cache/run_123/data.parquet",
        schema_version="v1"
    )

    # Save manifest
    manifest.save()

    # Validate all files
    manifest.validate()
"""

import hashlib
import json
import os
import platform
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from src.core.errors import CacheCorruptionError


@dataclass
class FileEntry:
    """Single file entry in cache manifest."""

    path: str
    checksum: str
    size_bytes: int
    schema_version: str
    created_at: str

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return {
            "path": self.path,
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "FileEntry":
        """Create from dict (JSON deserialization)."""
        return cls(
            path=data["path"],
            checksum=data["checksum"],
            size_bytes=data["size_bytes"],
            schema_version=data["schema_version"],
            created_at=data["created_at"],
        )


@dataclass
class CacheManifest:
    """
    Cache manifest tracking files, checksums, and metadata.

    Attributes:
        manifest_version: Schema version of manifest itself
        run_id: Unique identifier for this cache/run
        created_at: ISO8601 timestamp of first creation
        updated_at: ISO8601 timestamp of last update
        git_sha: Git commit hash (optional)
        config_hash: SHA256 of config (optional)
        python_version: Python version string
        platform: Platform identifier (e.g., "darwin", "linux")
        files: List of tracked file entries
        manifest_path: Path to manifest.json file
    """

    manifest_version: str = "1.0"
    run_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    git_sha: Optional[str] = None
    config_hash: Optional[str] = None
    python_version: str = ""
    platform: str = ""
    files: List[FileEntry] = field(default_factory=list)
    manifest_path: Optional[str] = None

    def __post_init__(self):
        """Initialize timestamps and platform info if not set."""
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.python_version:
            self.python_version = sys.version.split()[0]
        if not self.platform:
            self.platform = platform.system().lower()

    def add_file(
        self,
        filepath: str,
        schema_version: str = "v1",
        base_dir: Optional[str] = None,
    ) -> None:
        """
        Add file to manifest with checksum computation.

        Args:
            filepath: Absolute or relative path to file
            schema_version: Schema version of this file (e.g., "v1", "v2")
            base_dir: Base directory for computing relative paths
                     (defaults to manifest directory)

        Raises:
            FileNotFoundError: If file doesn't exist
            CacheCorruptionError: If checksum computation fails
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        # Compute relative path
        if base_dir is None and self.manifest_path:
            base_dir = str(Path(self.manifest_path).parent)

        if base_dir:
            rel_path = os.path.relpath(filepath, base_dir)
        else:
            rel_path = filepath

        # Compute checksum
        try:
            checksum = self._compute_checksum(filepath)
        except Exception as exc:
            raise CacheCorruptionError(
                f"Failed to compute checksum for {filepath}",
                hint="Check file permissions and disk health",
                context={"filepath": filepath, "error": str(exc)},
            ) from exc

        # Get file size
        size_bytes = os.path.getsize(filepath)

        # Create entry
        entry = FileEntry(
            path=rel_path,
            checksum=f"sha256:{checksum}",
            size_bytes=size_bytes,
            schema_version=schema_version,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # Remove existing entry with same path (update case)
        self.files = [f for f in self.files if f.path != rel_path]

        # Add new entry
        self.files.append(entry)

        # Update timestamp
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def validate(self, base_dir: Optional[str] = None) -> None:
        """
        Validate all files in manifest (existence + checksum).

        Args:
            base_dir: Base directory for resolving relative paths
                     (defaults to manifest directory)

        Raises:
            CacheCorruptionError: If any file is missing or has checksum mismatch
        """
        if base_dir is None and self.manifest_path:
            base_dir = str(Path(self.manifest_path).parent)

        errors = []

        for entry in self.files:
            # Resolve path
            if base_dir and not os.path.isabs(entry.path):
                full_path = os.path.join(base_dir, entry.path)
            else:
                full_path = entry.path

            # Check existence
            if not os.path.exists(full_path):
                errors.append(f"Missing file: {entry.path}")
                continue

            # Verify checksum
            try:
                actual_checksum = self._compute_checksum(full_path)
                expected_checksum = entry.checksum.replace("sha256:", "")

                if actual_checksum != expected_checksum:
                    errors.append(
                        f"Checksum mismatch: {entry.path} "
                        f"(expected: {expected_checksum[:8]}..., "
                        f"got: {actual_checksum[:8]}...)"
                    )
            except Exception as exc:
                errors.append(f"Failed to verify {entry.path}: {exc}")

        if errors:
            raise CacheCorruptionError(
                f"Cache validation failed for run_id={self.run_id}",
                hint="Delete corrupted cache and re-run",
                context={"run_id": self.run_id, "errors": errors},
            )

    def save(self, manifest_path: Optional[str] = None) -> None:
        """
        Save manifest to JSON file.

        Args:
            manifest_path: Path to manifest.json (default: use self.manifest_path)

        Raises:
            CacheCorruptionError: If write fails
        """
        if manifest_path:
            self.manifest_path = manifest_path
        elif not self.manifest_path:
            raise ValueError("manifest_path must be provided or set in __init__")

        # Update timestamp
        self.updated_at = datetime.now(timezone.utc).isoformat()

        # Serialize
        data = {
            "manifest_version": self.manifest_version,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "git_sha": self.git_sha,
            "config_hash": self.config_hash,
            "python_version": self.python_version,
            "platform": self.platform,
            "files": [f.to_dict() for f in self.files],
        }

        # Write atomically (temp + rename)
        manifest_file = Path(self.manifest_path)
        manifest_file.parent.mkdir(parents=True, exist_ok=True)

        temp_path = str(manifest_file) + ".tmp"

        try:
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())

            os.replace(temp_path, self.manifest_path)

        except Exception as exc:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise CacheCorruptionError(
                f"Failed to write manifest: {self.manifest_path}",
                hint="Check disk space and permissions",
                context={"manifest_path": self.manifest_path, "error": str(exc)},
            ) from exc

    @classmethod
    def load(cls, manifest_path: str) -> "CacheManifest":
        """
        Load manifest from JSON file.

        Args:
            manifest_path: Path to manifest.json

        Returns:
            CacheManifest instance

        Raises:
            FileNotFoundError: If manifest doesn't exist
            CacheCorruptionError: If manifest is corrupted or invalid
        """
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        try:
            with open(manifest_path, "r") as f:
                data = json.load(f)

            # Parse files
            files = [FileEntry.from_dict(f) for f in data.get("files", [])]

            manifest = cls(
                manifest_version=data.get("manifest_version", "1.0"),
                run_id=data["run_id"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                git_sha=data.get("git_sha"),
                config_hash=data.get("config_hash"),
                python_version=data.get("python_version", "unknown"),
                platform=data.get("platform", "unknown"),
                files=files,
                manifest_path=manifest_path,
            )

            return manifest

        except Exception as exc:
            raise CacheCorruptionError(
                f"Failed to load manifest: {manifest_path}",
                hint="Manifest file may be corrupted. Delete and regenerate.",
                context={"manifest_path": manifest_path, "error": str(exc)},
            ) from exc

    @classmethod
    def load_or_create(
        cls,
        cache_dir: str,
        run_id: str,
        git_sha: Optional[str] = None,
        config_hash: Optional[str] = None,
    ) -> "CacheManifest":
        """
        Load existing manifest or create new one.

        Args:
            cache_dir: Directory containing/to-contain manifest.json
            run_id: Unique run identifier
            git_sha: Git commit hash (optional)
            config_hash: Config hash (optional)

        Returns:
            CacheManifest instance (loaded or new)
        """
        manifest_path = os.path.join(cache_dir, "manifest.json")

        if os.path.exists(manifest_path):
            return cls.load(manifest_path)
        else:
            return cls(
                run_id=run_id,
                git_sha=git_sha,
                config_hash=config_hash,
                manifest_path=manifest_path,
            )

    @staticmethod
    def _compute_checksum(filepath: str) -> str:
        """Compute SHA256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
