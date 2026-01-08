"""
Evidence Pack Schema Versioning & Migration (Phase 4B Milestone 1)

Provides:
- Schema header validation (schema_id, schema_version, pack_id, producer)
- Migration registry for backward compatibility
- Canonicalization for deterministic validation

Reference:
- docs/ai/EVIDENCE_PACK_SCHEMA_V1.md
- PHASE4B_PLAN.md (Milestone 1)
"""

import hashlib
import json
import re
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple


# Schema versioning
CANONICAL_SCHEMA_ID = "evidence_pack"
CURRENT_SCHEMA_VERSION = "1.0.0"
SUPPORTED_SCHEMA_VERSIONS = ["1.0.0"]


# Error codes (for deterministic error handling)
class SchemaErrorCode:
    """Standard error codes for schema validation."""

    EPACK_SCHEMA_MISSING = "EPACK_SCHEMA_MISSING"
    EPACK_SCHEMA_UNSUPPORTED = "EPACK_SCHEMA_UNSUPPORTED"
    EPACK_SCHEMA_INVALID_ID = "EPACK_SCHEMA_INVALID_ID"
    EPACK_SCHEMA_INVALID_VERSION = "EPACK_SCHEMA_INVALID_VERSION"
    EPACK_PACK_ID_MISSING = "EPACK_PACK_ID_MISSING"
    EPACK_MIGRATION_FAILED = "EPACK_MIGRATION_FAILED"


@dataclass
class SchemaHeader:
    """
    Schema header for Evidence Packs (Phase 4B).

    Every Evidence Pack MUST include this header.
    """

    schema_id: str  # Must be "evidence_pack"
    schema_version: str  # SemVer (e.g., "1.0.0")
    pack_id: str  # Stable identifier (e.g., "EVP-L0-20260108-001")

    # Optional fields
    created_at: Optional[str] = None  # ISO-8601 (not used for determinism)
    producer: Optional[Dict[str, str]] = None  # {tool, version, git_sha}

    def validate(self) -> None:
        """
        Validate schema header.

        Raises:
            SchemaValidationError: If validation fails
        """
        # schema_id must be "evidence_pack"
        if not self.schema_id:
            raise SchemaValidationError(
                code=SchemaErrorCode.EPACK_SCHEMA_MISSING,
                message="schema_id is required",
            )

        if self.schema_id != "evidence_pack":
            raise SchemaValidationError(
                code=SchemaErrorCode.EPACK_SCHEMA_INVALID_ID,
                message=f"Invalid schema_id: {self.schema_id} (expected: 'evidence_pack')",
            )

        # schema_version must be present and valid SemVer
        if not self.schema_version:
            raise SchemaValidationError(
                code=SchemaErrorCode.EPACK_SCHEMA_MISSING,
                message="schema_version is required",
            )

        if not self._is_valid_semver(self.schema_version):
            raise SchemaValidationError(
                code=SchemaErrorCode.EPACK_SCHEMA_INVALID_VERSION,
                message=f"Invalid schema_version: {self.schema_version} (expected SemVer format)",
            )

        # pack_id must be present
        if not self.pack_id or not self.pack_id.strip():
            raise SchemaValidationError(
                code=SchemaErrorCode.EPACK_PACK_ID_MISSING,
                message="pack_id is required and must not be empty",
            )

        # created_at must be valid ISO-8601 if present
        if self.created_at:
            try:
                datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                raise SchemaValidationError(
                    code=SchemaErrorCode.EPACK_SCHEMA_INVALID_VERSION,
                    message=f"Invalid created_at: {self.created_at} (expected ISO-8601)",
                )

    @staticmethod
    def _is_valid_semver(version: str) -> bool:
        """Validate SemVer format (MAJOR.MINOR.PATCH)."""
        pattern = r"^\d+\.\d+\.\d+$"
        return bool(re.match(pattern, version))


class SchemaValidationError(Exception):
    """Schema validation error with error code."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


# ============================================================================
# Migration Registry (pure functions for backward compatibility)
# ============================================================================

# Type alias for migration functions
MigrationFn = Callable[[Dict[str, Any]], Dict[str, Any]]

# Migration registry: (from_version, to_version) -> migration_fn
_MIGRATION_REGISTRY: Dict[Tuple[str, str], MigrationFn] = {}


def register_migration(from_version: str, to_version: str):
    """
    Decorator to register a migration function.

    Usage:
        @register_migration("1.0.0", "1.1.0")
        def migrate_1_0_to_1_1(pack: Dict[str, Any]) -> Dict[str, Any]:
            # Migration logic here
            return pack
    """

    def decorator(fn: MigrationFn) -> MigrationFn:
        _MIGRATION_REGISTRY[(from_version, to_version)] = fn
        return fn

    return decorator


def migrate(
    pack: Dict[str, Any], from_version: str, to_version: str
) -> Dict[str, Any]:
    """
    Migrate pack from one schema version to another.

    Applies migration chain if direct migration not available.

    Args:
        pack: Pack data (dict)
        from_version: Source schema version
        to_version: Target schema version

    Returns:
        Migrated pack data

    Raises:
        SchemaValidationError: If migration not possible
    """
    if from_version == to_version:
        # No migration needed
        return pack

    # Check for direct migration
    migration_key = (from_version, to_version)
    if migration_key in _MIGRATION_REGISTRY:
        migrated = _MIGRATION_REGISTRY[migration_key](pack)
        # Add migration info (for debugging, not used in validation)
        migrated["migration_info"] = {
            "migrated_from": from_version,
            "migrated_to": to_version,
        }
        return migrated

    # TODO: Implement migration chain (multi-hop migrations)
    # For now, only support direct migrations
    raise SchemaValidationError(
        code=SchemaErrorCode.EPACK_MIGRATION_FAILED,
        message=f"No migration path from {from_version} to {to_version}",
    )


# ============================================================================
# Baseline Migration (noop for v1.0.0 -> v1.0.0)
# ============================================================================


@register_migration("1.0.0", "1.0.0")
def migrate_1_0_to_1_0(pack: Dict[str, Any]) -> Dict[str, Any]:
    """Noop migration (baseline for v1.0.0)."""
    return pack


# ============================================================================
# Canonicalization (deterministic normalization)
# ============================================================================


def canonicalize(pack: Dict[str, Any]) -> Dict[str, Any]:
    """
    Canonicalize pack data for deterministic validation.

    Applies:
    - Stable key ordering (alphabetical)
    - Path normalization (POSIX-like)
    - Trailing whitespace stripping

    Args:
        pack: Pack data (dict)

    Returns:
        Canonicalized pack data (new dict)
    """
    return _canonicalize_recursive(pack)


def _canonicalize_recursive(obj: Any) -> Any:
    """Recursively canonicalize data structure."""
    if isinstance(obj, dict):
        # Sort keys alphabetically (stable ordering)
        return {k: _canonicalize_recursive(v) for k, v in sorted(obj.items())}
    elif isinstance(obj, list):
        return [_canonicalize_recursive(item) for item in obj]
    elif isinstance(obj, str):
        # Strip trailing whitespace (preserve leading/internal whitespace)
        return obj.rstrip()
    else:
        # Pass through other types (int, float, bool, None)
        return obj


def normalize_path(path: str) -> str:
    """
    Normalize file path to POSIX-like format.

    Args:
        path: File path (str)

    Returns:
        Normalized path (forward slashes, no trailing slash)
    """
    # Convert backslashes to forward slashes
    normalized = path.replace("\\", "/")
    # Remove trailing slash (except for root "/")
    if len(normalized) > 1 and normalized.endswith("/"):
        normalized = normalized.rstrip("/")
    return normalized


# ============================================================================
# Schema Validation (main entry point)
# ============================================================================


def validate_schema_header(pack: Dict[str, Any]) -> SchemaHeader:
    """
    Validate and extract schema header from pack.

    Args:
        pack: Pack data (dict)

    Returns:
        Validated SchemaHeader

    Raises:
        SchemaValidationError: If validation fails
    """
    # Extract header fields (strict, no defaults)
    schema_id = pack.get("schema_id")
    schema_version = pack.get("schema_version")
    pack_id = pack.get("pack_id")
    created_at = pack.get("created_at")
    producer = pack.get("producer")

    # Create and validate header (strict validation)
    header = SchemaHeader(
        schema_id=schema_id or "",
        schema_version=schema_version or "",
        pack_id=pack_id or "",
        created_at=created_at,
        producer=producer,
    )

    header.validate()

    # Check if version is supported
    if header.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise SchemaValidationError(
            code=SchemaErrorCode.EPACK_SCHEMA_UNSUPPORTED,
            message=f"Unsupported schema_version: {header.schema_version} "
            f"(supported: {', '.join(SUPPORTED_SCHEMA_VERSIONS)})",
        )

    return header


def validate_and_migrate(
    pack: Dict[str, Any], target_version: str = CURRENT_SCHEMA_VERSION
) -> Dict[str, Any]:
    """
    Validate schema header and migrate pack to target version.

    Args:
        pack: Pack data (dict)
        target_version: Target schema version (default: current)

    Returns:
        Validated and migrated pack data

    Raises:
        SchemaValidationError: If validation or migration fails
    """
    # Legacy pack detection (minimal invasive backward compatibility)
    legacy = (
        ("schema_id" not in pack)
        and ("schema_version" not in pack)
        and ("pack_id" not in pack)
    )

    if legacy:
        # Create safe copy to avoid mutating input
        pack = deepcopy(pack)

        # Set defaults for legacy packs
        pack.setdefault("schema_id", CANONICAL_SCHEMA_ID)
        pack.setdefault("schema_version", "1.0.0")

        # Handle pack_id: try to use existing "id" field, else error
        if not pack.get("pack_id"):
            if pack.get("id"):
                pack["pack_id"] = str(pack["id"])
            else:
                raise SchemaValidationError(
                    code=SchemaErrorCode.EPACK_PACK_ID_MISSING,
                    message="pack_id is required (and no 'id' field found for legacy pack)",
                )

    # Validate header (strict validation, no further defaults)
    header = validate_schema_header(pack)

    # Canonicalize before migration
    canonical_pack = canonicalize(pack)

    # Migrate if needed
    if header.schema_version != target_version:
        canonical_pack = migrate(canonical_pack, header.schema_version, target_version)

    return canonical_pack


# ============================================================================
# Semantic Validation Rules (timestamps, formats, etc.)
# ============================================================================


def validate_timestamp_chronology(pack: Dict[str, Any]) -> None:
    """
    Validate timestamp chronology (started_at < finished_at).

    Args:
        pack: Pack data (dict)

    Raises:
        SchemaValidationError: If chronology is violated
    """
    # Extract timestamps from layer_run_metadata (if present)
    layer_run = pack.get("layer_run_metadata")
    if not layer_run:
        return  # No timestamps to validate

    started_at = layer_run.get("started_at")
    finished_at = layer_run.get("finished_at")

    if started_at and finished_at:
        try:
            start_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            finish_dt = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))

            if start_dt >= finish_dt:
                raise SchemaValidationError(
                    code="EPACK_TIMESTAMP_CHRONOLOGY",
                    message=f"Timestamp chronology violation: started_at ({started_at}) >= finished_at ({finished_at})",
                )
        except (ValueError, AttributeError) as e:
            raise SchemaValidationError(
                code="EPACK_TIMESTAMP_INVALID",
                message=f"Invalid timestamp format: {e}",
            )


def validate_git_sha_format(git_sha: str) -> None:
    """
    Validate git SHA format (40-char hex or 'local-dev').

    Args:
        git_sha: Git SHA string

    Raises:
        SchemaValidationError: If format is invalid
    """
    if git_sha == "local-dev":
        return  # Special case for local development

    # Check 40-char hex format
    if not re.match(r"^[0-9a-f]{40}$", git_sha):
        raise SchemaValidationError(
            code="EPACK_GIT_SHA_INVALID",
            message=f"Invalid git_sha format: {git_sha} (expected 40-char hex or 'local-dev')",
        )


def validate_config_fingerprint_format(fingerprint: str) -> None:
    """
    Validate config fingerprint format (64-char SHA256).

    Args:
        fingerprint: Config fingerprint string

    Raises:
        SchemaValidationError: If format is invalid
    """
    if not re.match(r"^[0-9a-f]{64}$", fingerprint):
        raise SchemaValidationError(
            code="EPACK_FINGERPRINT_INVALID",
            message=f"Invalid config_fingerprint format: {fingerprint} (expected 64-char SHA256)",
        )
