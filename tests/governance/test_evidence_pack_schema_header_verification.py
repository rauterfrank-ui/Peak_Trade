"""
Governance: Evidence Pack Schema Header Verification

Deterministic tests for:
- Schema header required fields (schema_id, schema_version, pack_id)
- Schema versioning (SemVer format, supported versions)
- validate_schema_header contract and error codes
"""

import pytest

from src.ai_orchestration.evidence_pack_schema import (
    CANONICAL_SCHEMA_ID,
    CURRENT_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    SchemaErrorCode,
    SchemaHeader,
    SchemaValidationError,
    validate_schema_header,
)


class TestEvidencePackSchemaHeaderRequiredFields:
    """Required header fields: schema_id, schema_version, pack_id."""

    def test_valid_header_passes(self):
        pack = {
            "schema_id": "evidence_pack",
            "schema_version": "1.0.0",
            "pack_id": "EVP-L0-20260108-001",
        }
        header = validate_schema_header(pack)
        assert header.schema_id == CANONICAL_SCHEMA_ID
        assert header.schema_version == "1.0.0"
        assert header.pack_id == "EVP-L0-20260108-001"

    def test_schema_id_required(self):
        pack = {"schema_id": "", "schema_version": "1.0.0", "pack_id": "EVP-001"}
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema_header(pack)
        assert exc_info.value.code == SchemaErrorCode.EPACK_SCHEMA_MISSING
        assert "schema_id" in str(exc_info.value).lower()

    def test_schema_id_must_be_evidence_pack(self):
        pack = {"schema_id": "other", "schema_version": "1.0.0", "pack_id": "EVP-001"}
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema_header(pack)
        assert exc_info.value.code == SchemaErrorCode.EPACK_SCHEMA_INVALID_ID
        assert "evidence_pack" in str(exc_info.value)

    def test_schema_version_required(self):
        pack = {"schema_id": "evidence_pack", "schema_version": "", "pack_id": "EVP-001"}
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema_header(pack)
        assert exc_info.value.code == SchemaErrorCode.EPACK_SCHEMA_MISSING
        assert "schema_version" in str(exc_info.value).lower()

    def test_pack_id_required(self):
        pack = {"schema_id": "evidence_pack", "schema_version": "1.0.0", "pack_id": ""}
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema_header(pack)
        assert exc_info.value.code == SchemaErrorCode.EPACK_PACK_ID_MISSING
        assert "pack_id" in str(exc_info.value).lower()

    def test_pack_id_whitespace_only_rejected(self):
        header = SchemaHeader(
            schema_id="evidence_pack",
            schema_version="1.0.0",
            pack_id="   ",
        )
        with pytest.raises(SchemaValidationError) as exc_info:
            header.validate()
        assert exc_info.value.code == SchemaErrorCode.EPACK_PACK_ID_MISSING


class TestEvidencePackSchemaVersioning:
    """Schema version format (SemVer) and supported versions."""

    def test_semver_format_required(self):
        pack = {
            "schema_id": "evidence_pack",
            "schema_version": "v1.0",
            "pack_id": "EVP-001",
        }
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema_header(pack)
        assert exc_info.value.code == SchemaErrorCode.EPACK_SCHEMA_INVALID_VERSION
        assert "SemVer" in str(exc_info.value) or "1.0" in str(exc_info.value)

    def test_semver_three_segments_accepted(self):
        pack = {
            "schema_id": "evidence_pack",
            "schema_version": "1.0.0",
            "pack_id": "EVP-001",
        }
        header = validate_schema_header(pack)
        assert header.schema_version == "1.0.0"

    def test_unsupported_version_rejected(self):
        pack = {
            "schema_id": "evidence_pack",
            "schema_version": "2.0.0",
            "pack_id": "EVP-001",
        }
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema_header(pack)
        assert exc_info.value.code == SchemaErrorCode.EPACK_SCHEMA_UNSUPPORTED
        assert "2.0.0" in str(exc_info.value)

    def test_supported_versions_constant(self):
        assert CURRENT_SCHEMA_VERSION in SUPPORTED_SCHEMA_VERSIONS
        assert "1.0.0" in SUPPORTED_SCHEMA_VERSIONS

    def test_all_supported_versions_accept(self):
        for ver in SUPPORTED_SCHEMA_VERSIONS:
            pack = {"schema_id": "evidence_pack", "schema_version": ver, "pack_id": "EVP-001"}
            header = validate_schema_header(pack)
            assert header.schema_version == ver
