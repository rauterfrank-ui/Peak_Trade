"""
Tests for Evidence Pack Schema Versioning & Migration (Phase 4B Milestone 1)

Coverage:
- Schema header validation (schema_id, schema_version, pack_id)
- Unsupported version detection
- Migration registry and determinism
- Canonicalization
- Semantic validation (timestamps, git SHA, config fingerprint)
"""

import pytest
from datetime import datetime, timezone

from src.ai_orchestration.evidence_pack_schema import (
    CURRENT_SCHEMA_VERSION,
    SchemaErrorCode,
    SchemaHeader,
    SchemaValidationError,
    canonicalize,
    migrate,
    normalize_path,
    register_migration,
    validate_and_migrate,
    validate_config_fingerprint_format,
    validate_git_sha_format,
    validate_schema_header,
    validate_timestamp_chronology,
)


class TestSchemaHeader:
    """Test schema header validation."""

    def test_schema_header_present(self):
        """Test that valid schema header passes validation."""
        header = SchemaHeader(
            schema_id="evidence_pack",
            schema_version="1.0.0",
            pack_id="EVP-L0-20260108-001",
        )
        # Should not raise
        header.validate()

    def test_schema_id_missing(self):
        """Test that missing schema_id raises error."""
        header = SchemaHeader(
            schema_id="",
            schema_version="1.0.0",
            pack_id="EVP-001",
        )
        with pytest.raises(SchemaValidationError) as exc_info:
            header.validate()
        assert exc_info.value.code == SchemaErrorCode.EPACK_SCHEMA_MISSING
        assert "schema_id is required" in str(exc_info.value)

    def test_schema_id_invalid(self):
        """Test that invalid schema_id raises error."""
        header = SchemaHeader(
            schema_id="wrong_schema",
            schema_version="1.0.0",
            pack_id="EVP-001",
        )
        with pytest.raises(SchemaValidationError) as exc_info:
            header.validate()
        assert exc_info.value.code == SchemaErrorCode.EPACK_SCHEMA_INVALID_ID
        assert "Invalid schema_id" in str(exc_info.value)

    def test_schema_version_missing(self):
        """Test that missing schema_version raises error."""
        header = SchemaHeader(
            schema_id="evidence_pack",
            schema_version="",
            pack_id="EVP-001",
        )
        with pytest.raises(SchemaValidationError) as exc_info:
            header.validate()
        assert exc_info.value.code == SchemaErrorCode.EPACK_SCHEMA_MISSING
        assert "schema_version is required" in str(exc_info.value)

    def test_schema_version_invalid_format(self):
        """Test that invalid SemVer format raises error."""
        header = SchemaHeader(
            schema_id="evidence_pack",
            schema_version="v1.0",  # Missing PATCH
            pack_id="EVP-001",
        )
        with pytest.raises(SchemaValidationError) as exc_info:
            header.validate()
        assert exc_info.value.code == SchemaErrorCode.EPACK_SCHEMA_INVALID_VERSION
        assert "expected SemVer format" in str(exc_info.value)

    def test_pack_id_missing(self):
        """Test that missing pack_id raises error."""
        header = SchemaHeader(
            schema_id="evidence_pack",
            schema_version="1.0.0",
            pack_id="",
        )
        with pytest.raises(SchemaValidationError) as exc_info:
            header.validate()
        assert exc_info.value.code == SchemaErrorCode.EPACK_PACK_ID_MISSING
        assert "pack_id is required" in str(exc_info.value)

    def test_created_at_invalid(self):
        """Test that invalid ISO-8601 timestamp raises error."""
        header = SchemaHeader(
            schema_id="evidence_pack",
            schema_version="1.0.0",
            pack_id="EVP-001",
            created_at="not-a-timestamp",
        )
        with pytest.raises(SchemaValidationError) as exc_info:
            header.validate()
        assert "Invalid created_at" in str(exc_info.value)


class TestSchemaValidation:
    """Test schema validation entry points."""

    def test_validate_schema_header_valid(self):
        """Test that valid pack header is accepted."""
        pack = {
            "schema_id": "evidence_pack",
            "schema_version": "1.0.0",
            "pack_id": "EVP-001",
        }
        header = validate_schema_header(pack)
        assert header.schema_id == "evidence_pack"
        assert header.schema_version == "1.0.0"
        assert header.pack_id == "EVP-001"

    def test_validate_schema_header_strict(self):
        """Test that validate_schema_header is strict (no defaults)."""
        pack = {
            "pack_id": "EVP-001",
            # schema_id and schema_version missing
        }
        # Should raise error (strict validation, no defaults)
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema_header(pack)
        assert exc_info.value.code in [
            SchemaErrorCode.EPACK_SCHEMA_MISSING,
            SchemaErrorCode.EPACK_SCHEMA_INVALID_ID,
        ]

    def test_validate_schema_header_unsupported_version(self):
        """Test that unsupported version raises error."""
        pack = {
            "schema_id": "evidence_pack",
            "schema_version": "2.0.0",  # Not supported
            "pack_id": "EVP-001",
        }
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema_header(pack)
        assert exc_info.value.code == SchemaErrorCode.EPACK_SCHEMA_UNSUPPORTED
        assert "Unsupported schema_version: 2.0.0" in str(exc_info.value)


class TestMigration:
    """Test migration registry and determinism."""

    def test_migration_registry_lookup(self):
        """Test that registered migration is found."""
        # Noop migration (1.0.0 -> 1.0.0) is registered by default
        pack = {"schema_version": "1.0.0", "data": "test"}
        migrated = migrate(pack, "1.0.0", "1.0.0")
        assert migrated["schema_version"] == "1.0.0"
        assert migrated["data"] == "test"

    def test_migration_chain_determinism(self):
        """Test that migration is deterministic (same input -> same output)."""
        pack1 = {"schema_version": "1.0.0", "data": "test", "extra": 123}
        pack2 = {"schema_version": "1.0.0", "data": "test", "extra": 123}

        migrated1 = migrate(pack1, "1.0.0", "1.0.0")
        migrated2 = migrate(pack2, "1.0.0", "1.0.0")

        # Same input should produce identical output
        assert migrated1 == migrated2

    def test_migration_no_migration_needed(self):
        """Test that same version migration is noop."""
        pack = {"schema_version": "1.0.0", "data": "test"}
        migrated = migrate(pack, "1.0.0", "1.0.0")
        assert migrated["data"] == "test"

    def test_migration_unsupported_path(self):
        """Test that unsupported migration path raises error."""
        pack = {"schema_version": "1.0.0"}
        with pytest.raises(SchemaValidationError) as exc_info:
            migrate(pack, "1.0.0", "9.9.9")  # No such migration
        assert exc_info.value.code == SchemaErrorCode.EPACK_MIGRATION_FAILED
        assert "No migration path" in str(exc_info.value)


class TestCanonicalization:
    """Test canonicalization for deterministic validation."""

    def test_canonicalization_key_order(self):
        """Test that keys are sorted alphabetically."""
        pack = {"z_field": 1, "a_field": 2, "m_field": 3}
        canonical = canonicalize(pack)
        keys = list(canonical.keys())
        assert keys == ["a_field", "m_field", "z_field"]

    def test_canonicalization_nested_dicts(self):
        """Test that nested dicts are also canonicalized."""
        pack = {
            "outer": {"z": 1, "a": 2},
            "list": [{"b": 1, "a": 2}],
        }
        canonical = canonicalize(pack)
        assert list(canonical["outer"].keys()) == ["a", "z"]
        assert list(canonical["list"][0].keys()) == ["a", "b"]

    def test_canonicalization_whitespace_stripping(self):
        """Test that trailing whitespace is stripped."""
        pack = {"field": "value  \n  ", "nested": {"text": "data\t "}}
        canonical = canonicalize(pack)
        assert canonical["field"] == "value"
        assert canonical["nested"]["text"] == "data"

    def test_canonicalization_path_normalization(self):
        """Test path normalization (POSIX-like)."""
        assert normalize_path("path\\to\\file") == "path/to/file"
        assert normalize_path("path/to/file/") == "path/to/file"
        assert normalize_path("/root/") == "/root"


class TestSemanticValidation:
    """Test semantic validation rules."""

    def test_timestamp_chronology_valid(self):
        """Test that valid timestamp chronology passes."""
        pack = {
            "layer_run_metadata": {
                "started_at": "2026-01-08T10:00:00Z",
                "finished_at": "2026-01-08T10:05:00Z",
            }
        }
        # Should not raise
        validate_timestamp_chronology(pack)

    def test_timestamp_chronology_invalid(self):
        """Test that inverted timestamps fail."""
        pack = {
            "layer_run_metadata": {
                "started_at": "2026-01-08T10:05:00Z",
                "finished_at": "2026-01-08T10:00:00Z",  # Before start
            }
        }
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_timestamp_chronology(pack)
        assert "chronology violation" in str(exc_info.value)

    def test_git_sha_format_valid(self):
        """Test that valid git SHA formats pass."""
        # 40-char hex
        validate_git_sha_format("a" * 40)
        validate_git_sha_format("1234567890abcdef1234567890abcdef12345678")
        # Special case: local-dev
        validate_git_sha_format("local-dev")

    def test_git_sha_format_invalid(self):
        """Test that invalid git SHA formats fail."""
        with pytest.raises(SchemaValidationError):
            validate_git_sha_format("too-short")
        with pytest.raises(SchemaValidationError):
            validate_git_sha_format("x" * 40)  # Non-hex
        with pytest.raises(SchemaValidationError):
            validate_git_sha_format("a" * 39)  # Wrong length

    def test_config_fingerprint_format_valid(self):
        """Test that valid SHA256 fingerprint passes."""
        # 64-char hex (SHA256)
        validate_config_fingerprint_format("a" * 64)
        validate_config_fingerprint_format(
            "1234567890abcdef" * 4  # 64 chars
        )

    def test_config_fingerprint_format_invalid(self):
        """Test that invalid fingerprint formats fail."""
        with pytest.raises(SchemaValidationError):
            validate_config_fingerprint_format("too-short")
        with pytest.raises(SchemaValidationError):
            validate_config_fingerprint_format("x" * 64)  # Non-hex
        with pytest.raises(SchemaValidationError):
            validate_config_fingerprint_format("a" * 63)  # Wrong length


class TestValidateAndMigrate:
    """Test end-to-end validation and migration."""

    def test_validate_and_migrate_valid_pack(self):
        """Test that valid pack is validated and migrated."""
        pack = {
            "schema_id": "evidence_pack",
            "schema_version": "1.0.0",
            "pack_id": "EVP-001",
            "data": "test",
        }
        result = validate_and_migrate(pack)
        assert result["schema_id"] == "evidence_pack"
        assert result["schema_version"] == "1.0.0"
        assert result["pack_id"] == "EVP-001"

    def test_validate_and_migrate_canonicalization(self):
        """Test that pack is canonicalized during validation."""
        pack = {
            "z_field": 1,
            "a_field": 2,
            "schema_id": "evidence_pack",
            "schema_version": "1.0.0",
            "pack_id": "EVP-001",
        }
        result = validate_and_migrate(pack)
        keys = list(result.keys())
        # Keys should be sorted
        assert keys[0] == "a_field"
        assert keys[-1] == "z_field"

    def test_validate_and_migrate_backward_compat_with_id(self):
        """Test that legacy pack with 'id' field uses it as pack_id."""
        pack = {
            "id": "EVP-LEGACY-001",
            "data": "test",
            # schema_id, schema_version, pack_id missing (legacy pack)
        }
        result = validate_and_migrate(pack, target_version="1.0.0")
        # Should not raise (backward compat via legacy detection)
        assert result["pack_id"] == "EVP-LEGACY-001"  # From 'id' field
        assert result["schema_id"] == "evidence_pack"
        assert result["schema_version"] == "1.0.0"

    def test_legacy_pack_id_mapping(self):
        """Test that legacy pack with only 'id' field gets proper schema header."""
        # Pack contains "id": "abc", but no schema_id/schema_version/pack_id
        pack = {"id": "abc"}

        result = validate_and_migrate(pack)

        # Verify pack_id is set from 'id' field
        assert result["pack_id"] == "abc"

        # Verify schema defaults are applied
        assert result["schema_id"] == "evidence_pack"
        assert result["schema_version"] == "1.0.0"

    def test_validate_and_migrate_backward_compat_no_id(self):
        """Test that legacy pack without 'id' or 'pack_id' raises error."""
        pack = {
            "data": "test",
            # schema_id, schema_version, pack_id, id all missing
        }
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_and_migrate(pack, target_version="1.0.0")
        assert exc_info.value.code == SchemaErrorCode.EPACK_PACK_ID_MISSING
