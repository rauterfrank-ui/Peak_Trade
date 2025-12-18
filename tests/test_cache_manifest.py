"""
Tests for Cache Manifest System (Wave B)
=========================================
"""
import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.core.errors import CacheCorruptionError
from src.data.cache_manifest import CacheManifest, FileEntry


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_df():
    """Create sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=10, freq="1h", tz="UTC"),
            "value": range(10),
        }
    ).set_index("timestamp")


class TestFileEntry:
    """Tests for FileEntry dataclass."""

    def test_to_dict(self):
        """Test serialization to dict."""
        entry = FileEntry(
            path="test.parquet",
            checksum="sha256:abc123",
            size_bytes=1024,
            schema_version="v1",
            created_at="2024-01-01T00:00:00Z",
        )

        data = entry.to_dict()

        assert data["path"] == "test.parquet"
        assert data["checksum"] == "sha256:abc123"
        assert data["size_bytes"] == 1024
        assert data["schema_version"] == "v1"
        assert data["created_at"] == "2024-01-01T00:00:00Z"

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "path": "test.parquet",
            "checksum": "sha256:abc123",
            "size_bytes": 1024,
            "schema_version": "v1",
            "created_at": "2024-01-01T00:00:00Z",
        }

        entry = FileEntry.from_dict(data)

        assert entry.path == "test.parquet"
        assert entry.checksum == "sha256:abc123"
        assert entry.size_bytes == 1024
        assert entry.schema_version == "v1"
        assert entry.created_at == "2024-01-01T00:00:00Z"

    def test_roundtrip(self):
        """Test to_dict -> from_dict roundtrip."""
        original = FileEntry(
            path="test.parquet",
            checksum="sha256:abc123",
            size_bytes=1024,
            schema_version="v1",
            created_at="2024-01-01T00:00:00Z",
        )

        roundtrip = FileEntry.from_dict(original.to_dict())

        assert roundtrip.path == original.path
        assert roundtrip.checksum == original.checksum
        assert roundtrip.size_bytes == original.size_bytes
        assert roundtrip.schema_version == original.schema_version
        assert roundtrip.created_at == original.created_at


class TestCacheManifest:
    """Tests for CacheManifest class."""

    def test_init_defaults(self):
        """Test manifest initialization with defaults."""
        manifest = CacheManifest(run_id="test_run_123")

        assert manifest.manifest_version == "1.0"
        assert manifest.run_id == "test_run_123"
        assert manifest.created_at  # Should be set
        assert manifest.updated_at  # Should be set
        assert manifest.python_version  # Should be set
        assert manifest.platform  # Should be set
        assert manifest.files == []

    def test_init_with_metadata(self):
        """Test manifest initialization with custom metadata."""
        manifest = CacheManifest(
            run_id="test_run_123",
            git_sha="abc123",
            config_hash="def456",
        )

        assert manifest.run_id == "test_run_123"
        assert manifest.git_sha == "abc123"
        assert manifest.config_hash == "def456"

    def test_add_file(self, temp_dir, sample_df):
        """Test adding file to manifest."""
        # Create test file
        filepath = os.path.join(temp_dir, "test.parquet")
        sample_df.to_parquet(filepath)

        # Create manifest
        manifest = CacheManifest(
            run_id="test_run",
            manifest_path=os.path.join(temp_dir, "manifest.json"),
        )

        # Add file
        manifest.add_file(filepath, schema_version="v1")

        # Verify
        assert len(manifest.files) == 1
        entry = manifest.files[0]
        assert entry.path == "test.parquet"  # Relative path
        assert entry.checksum.startswith("sha256:")
        assert entry.size_bytes > 0
        assert entry.schema_version == "v1"
        assert entry.created_at  # Should be set

    def test_add_file_missing(self, temp_dir):
        """Test adding non-existent file raises FileNotFoundError."""
        manifest = CacheManifest(
            run_id="test_run",
            manifest_path=os.path.join(temp_dir, "manifest.json"),
        )

        with pytest.raises(FileNotFoundError):
            manifest.add_file("/nonexistent/file.parquet")

    def test_add_file_update_existing(self, temp_dir, sample_df):
        """Test adding same file twice updates entry."""
        # Create test file
        filepath = os.path.join(temp_dir, "test.parquet")
        sample_df.to_parquet(filepath)

        manifest = CacheManifest(
            run_id="test_run",
            manifest_path=os.path.join(temp_dir, "manifest.json"),
        )

        # Add file twice
        manifest.add_file(filepath, schema_version="v1")
        first_checksum = manifest.files[0].checksum

        # Modify file and add again
        (sample_df * 2).to_parquet(filepath)
        manifest.add_file(filepath, schema_version="v2")

        # Should have only one entry (updated)
        assert len(manifest.files) == 1
        assert manifest.files[0].schema_version == "v2"
        assert manifest.files[0].checksum != first_checksum

    def test_save_and_load(self, temp_dir, sample_df):
        """Test saving and loading manifest."""
        # Create manifest with file
        filepath = os.path.join(temp_dir, "test.parquet")
        sample_df.to_parquet(filepath)

        manifest_path = os.path.join(temp_dir, "manifest.json")
        manifest = CacheManifest(
            run_id="test_run_123",
            git_sha="abc123",
            manifest_path=manifest_path,
        )
        manifest.add_file(filepath, schema_version="v1")
        manifest.save()

        # Load manifest
        loaded = CacheManifest.load(manifest_path)

        # Verify
        assert loaded.run_id == "test_run_123"
        assert loaded.git_sha == "abc123"
        assert len(loaded.files) == 1
        assert loaded.files[0].path == "test.parquet"
        assert loaded.files[0].schema_version == "v1"

    def test_save_creates_directory(self, temp_dir):
        """Test save creates parent directories if needed."""
        nested_path = os.path.join(temp_dir, "nested", "dir", "manifest.json")

        manifest = CacheManifest(
            run_id="test_run",
            manifest_path=nested_path,
        )
        manifest.save()

        assert os.path.exists(nested_path)

    def test_load_missing_file(self, temp_dir):
        """Test loading non-existent manifest raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            CacheManifest.load(os.path.join(temp_dir, "nonexistent.json"))

    def test_load_corrupted_json(self, temp_dir):
        """Test loading corrupted JSON raises CacheCorruptionError."""
        manifest_path = os.path.join(temp_dir, "manifest.json")

        # Write invalid JSON
        with open(manifest_path, "w") as f:
            f.write("not valid json {{{")

        with pytest.raises(CacheCorruptionError):
            CacheManifest.load(manifest_path)

    def test_validate_success(self, temp_dir, sample_df):
        """Test validation succeeds for valid files."""
        # Create file and manifest
        filepath = os.path.join(temp_dir, "test.parquet")
        sample_df.to_parquet(filepath)

        manifest = CacheManifest(
            run_id="test_run",
            manifest_path=os.path.join(temp_dir, "manifest.json"),
        )
        manifest.add_file(filepath, schema_version="v1")

        # Should not raise
        manifest.validate()

    def test_validate_missing_file(self, temp_dir, sample_df):
        """Test validation fails for missing file."""
        # Create file, add to manifest, then delete
        filepath = os.path.join(temp_dir, "test.parquet")
        sample_df.to_parquet(filepath)

        manifest = CacheManifest(
            run_id="test_run",
            manifest_path=os.path.join(temp_dir, "manifest.json"),
        )
        manifest.add_file(filepath, schema_version="v1")

        # Delete file
        os.remove(filepath)

        # Validation should fail
        with pytest.raises(CacheCorruptionError) as exc_info:
            manifest.validate()

        assert "Missing file" in str(exc_info.value)

    def test_validate_checksum_mismatch(self, temp_dir, sample_df):
        """Test validation fails for checksum mismatch."""
        # Create file and manifest
        filepath = os.path.join(temp_dir, "test.parquet")
        sample_df.to_parquet(filepath)

        manifest = CacheManifest(
            run_id="test_run",
            manifest_path=os.path.join(temp_dir, "manifest.json"),
        )
        manifest.add_file(filepath, schema_version="v1")

        # Modify file (corrupts checksum)
        (sample_df * 2).to_parquet(filepath)

        # Validation should fail
        with pytest.raises(CacheCorruptionError) as exc_info:
            manifest.validate()

        assert "Checksum mismatch" in str(exc_info.value)

    def test_load_or_create_new(self, temp_dir):
        """Test load_or_create creates new manifest if not exists."""
        manifest = CacheManifest.load_or_create(
            cache_dir=temp_dir,
            run_id="test_run_123",
            git_sha="abc123",
        )

        assert manifest.run_id == "test_run_123"
        assert manifest.git_sha == "abc123"
        assert manifest.manifest_path == os.path.join(temp_dir, "manifest.json")
        assert len(manifest.files) == 0

    def test_load_or_create_existing(self, temp_dir, sample_df):
        """Test load_or_create loads existing manifest."""
        # Create and save manifest
        manifest_path = os.path.join(temp_dir, "manifest.json")
        manifest = CacheManifest(
            run_id="test_run_123",
            git_sha="abc123",
            manifest_path=manifest_path,
        )

        filepath = os.path.join(temp_dir, "test.parquet")
        sample_df.to_parquet(filepath)
        manifest.add_file(filepath)
        manifest.save()

        # Load or create (should load existing)
        loaded = CacheManifest.load_or_create(
            cache_dir=temp_dir,
            run_id="different_run",  # Should be ignored
        )

        assert loaded.run_id == "test_run_123"  # Original value
        assert loaded.git_sha == "abc123"
        assert len(loaded.files) == 1

    def test_multiple_files(self, temp_dir, sample_df):
        """Test manifest with multiple files."""
        manifest = CacheManifest(
            run_id="test_run",
            manifest_path=os.path.join(temp_dir, "manifest.json"),
        )

        # Add multiple files
        for i in range(3):
            filepath = os.path.join(temp_dir, f"test_{i}.parquet")
            sample_df.to_parquet(filepath)
            manifest.add_file(filepath, schema_version=f"v{i+1}")

        # Verify
        assert len(manifest.files) == 3

        for i, entry in enumerate(manifest.files):
            assert entry.path == f"test_{i}.parquet"
            assert entry.schema_version == f"v{i+1}"

        # Save and load
        manifest.save()
        loaded = CacheManifest.load(manifest.manifest_path)
        assert len(loaded.files) == 3

        # Validate all files
        loaded.validate()

    def test_json_structure(self, temp_dir, sample_df):
        """Test that saved JSON has expected structure."""
        filepath = os.path.join(temp_dir, "test.parquet")
        sample_df.to_parquet(filepath)

        manifest_path = os.path.join(temp_dir, "manifest.json")
        manifest = CacheManifest(
            run_id="test_run_123",
            git_sha="abc123",
            config_hash="def456",
            manifest_path=manifest_path,
        )
        manifest.add_file(filepath, schema_version="v1")
        manifest.save()

        # Load raw JSON
        with open(manifest_path, "r") as f:
            data = json.load(f)

        # Verify structure
        assert data["manifest_version"] == "1.0"
        assert data["run_id"] == "test_run_123"
        assert data["git_sha"] == "abc123"
        assert data["config_hash"] == "def456"
        assert "created_at" in data
        assert "updated_at" in data
        assert "python_version" in data
        assert "platform" in data
        assert len(data["files"]) == 1

        file_entry = data["files"][0]
        assert file_entry["path"] == "test.parquet"
        assert file_entry["checksum"].startswith("sha256:")
        assert file_entry["size_bytes"] > 0
        assert file_entry["schema_version"] == "v1"
        assert "created_at" in file_entry
