# Evidence Pack Schema v1.0.0

**Status:** Active  
**Version:** 1.0.0  
**Phase:** 4B Milestone 1  
**Date:** 2026-01-08

---

## Overview

This document specifies the schema for Evidence Packs in Peak_Trade's AI Autonomy Layer.

Evidence Packs are structured records that document:
- Layer Run metadata
- Model selections
- Verification results
- SoD checks
- Audit trail

Every Evidence Pack MUST include a schema header for versioning and backward compatibility.

---

## Schema Header (Required)

### Mandatory Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `schema_id` | string | Must be `"evidence_pack"` | `"evidence_pack"` |
| `schema_version` | string | SemVer format (MAJOR.MINOR.PATCH) | `"1.0.0"` |
| `pack_id` | string | Stable unique identifier | `"EVP-L0-20260108-001"` |

### Optional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `created_at` | string | ISO-8601 timestamp | `"2026-01-08T10:00:00Z"` |
| `producer` | object | Tool info: `{tool, version, git_sha}` | See below |

**Producer Example:**
```json
{
  "tool": "evidence_pack_runtime",
  "version": "1.0.0",
  "git_sha": "a1b2c3d4..."
}
```

---

## Schema Validation Rules

### Header Validation

1. **schema_id** must be `"evidence_pack"` (exact match)
   - Error Code: `EPACK_SCHEMA_INVALID_ID`

2. **schema_version** must be valid SemVer (e.g., `"1.0.0"`)
   - Error Code: `EPACK_SCHEMA_INVALID_VERSION`

3. **pack_id** must be non-empty string
   - Error Code: `EPACK_PACK_ID_MISSING`

4. **created_at** (if present) must be valid ISO-8601
   - Error Code: `EPACK_SCHEMA_INVALID_VERSION`

### Supported Versions

Current version: **1.0.0**

Supported versions:
- `1.0.0` (current)

Unsupported versions will raise:
- Error Code: `EPACK_SCHEMA_UNSUPPORTED`

---

## SemVer Policy

### Version Components

`MAJOR.MINOR.PATCH`

### Compatibility Rules

| Change | Version Bump | Backward Compatible? |
|--------|--------------|----------------------|
| **PATCH** | 1.0.0 → 1.0.1 | ✅ YES (editorial/constraints only) |
| **MINOR** | 1.0.0 → 1.1.0 | ✅ YES (additive, new optional fields) |
| **MAJOR** | 1.0.0 → 2.0.0 | ❌ NO (breaking changes, migration required) |

### Examples

**PATCH (1.0.0 → 1.0.1):**
- Clarify field documentation
- Add validation constraints (no new fields)

**MINOR (1.0.0 → 1.1.0):**
- Add new optional field `performance_metrics`
- Add new optional nested object

**MAJOR (1.0.0 → 2.0.0):**
- Remove required field
- Rename field
- Change field type

---

## Backward Compatibility

### Legacy Packs (Pre-4B)

Evidence Packs created before Phase 4B may not include schema header fields.

**Handling:**
- Missing `schema_id` → defaults to `"evidence_pack"`
- Missing `schema_version` → defaults to `"1.0.0"`
- Validation continues with default values (no error)

**Migration:**
Legacy packs are automatically migrated to current schema version during validation.

### Migration Process

1. **Load pack** (JSON/TOML)
2. **Validate schema header** (with defaults for legacy packs)
3. **Canonicalize** (stable key ordering, whitespace stripping)
4. **Migrate** (if schema_version < current)
5. **Validate content** (mandatory fields, semantic rules)

---

## Canonicalization

Before validation, packs are canonicalized for deterministic processing:

### Rules

1. **Stable key ordering** (alphabetical)
   ```json
   // Before
   {"z": 1, "a": 2}

   // After canonicalization
   {"a": 2, "z": 1}
   ```

2. **Path normalization** (POSIX-like, forward slashes)
   ```
   path\to\file  →  path/to/file
   path/to/file/ →  path/to/file
   ```

3. **Trailing whitespace stripping**
   ```
   "value  \n  "  →  "value"
   ```

---

## Semantic Validation Rules

### Timestamp Chronology

**Rule:** `started_at` < `finished_at` (if both present in `layer_run_metadata`)

**Error Code:** `EPACK_TIMESTAMP_CHRONOLOGY`

**Example:**
```json
{
  "layer_run_metadata": {
    "started_at": "2026-01-08T10:00:00Z",
    "finished_at": "2026-01-08T10:05:00Z"  // OK: after start
  }
}
```

### Git SHA Format

**Rule:** 40-char hex OR special value `"local-dev"`

**Error Code:** `EPACK_GIT_SHA_INVALID`

**Valid Examples:**
```
"a1b2c3d4e5f6789012345678901234567890abcd"  // 40-char hex
"local-dev"  // Special case for local development
```

### Config Fingerprint Format

**Rule:** 64-char hex (SHA256)

**Error Code:** `EPACK_FINGERPRINT_INVALID`

**Valid Example:**
```
"a1b2c3d4e5f6789012345678901234567890abcd1234567890abcdef123456789"
```

---

## Error Codes Reference

| Code | Description | Severity |
|------|-------------|----------|
| `EPACK_SCHEMA_MISSING` | schema_id or schema_version missing | ERROR |
| `EPACK_SCHEMA_UNSUPPORTED` | schema_version not supported | ERROR |
| `EPACK_SCHEMA_INVALID_ID` | schema_id != "evidence_pack" | ERROR |
| `EPACK_SCHEMA_INVALID_VERSION` | Invalid SemVer format | ERROR |
| `EPACK_PACK_ID_MISSING` | pack_id missing or empty | ERROR |
| `EPACK_MIGRATION_FAILED` | Migration path not found | ERROR |
| `EPACK_TIMESTAMP_CHRONOLOGY` | started_at >= finished_at | ERROR |
| `EPACK_TIMESTAMP_INVALID` | Invalid ISO-8601 format | ERROR |
| `EPACK_GIT_SHA_INVALID` | Invalid git SHA format | ERROR |
| `EPACK_FINGERPRINT_INVALID` | Invalid config fingerprint | ERROR |

---

## Example Evidence Pack (v1.0.0)

```json
{
  "schema_id": "evidence_pack",
  "schema_version": "1.0.0",
  "pack_id": "EVP-L0-20260108-001",
  "created_at": "2026-01-08T10:00:00Z",
  "producer": {
    "tool": "evidence_pack_runtime",
    "version": "1.0.0",
    "git_sha": "a1b2c3d4e5f6789012345678901234567890abcd"
  },

  "evidence_pack_id": "EVP-PHASE4B-20260108",
  "phase_id": "Phase4B-M1",
  "creation_timestamp": "2026-01-08T10:00:00Z",
  "registry_version": "v1.0",
  "layer_id": "L0",
  "autonomy_level": "REC",

  "layer_run_metadata": {
    "layer_id": "L0",
    "layer_name": "Context Analysis",
    "autonomy_level": "REC",
    "primary_model_id": "gpt-4",
    "critic_model_id": "claude-3-opus",
    "capability_scope_id": "read_only",
    "matrix_version": "v1.0",
    "started_at": "2026-01-08T10:00:00Z",
    "finished_at": "2026-01-08T10:05:00Z"
  },

  "sod_checks": [
    {
      "primary_model_id": "gpt-4",
      "critic_model_id": "claude-3-opus",
      "sod_result": "PASS",
      "critic_decision": "APPROVE",
      "timestamp": "2026-01-08T10:05:00Z"
    }
  ],

  "validator_run": true,
  "tests_passed": 12,
  "tests_total": 12,
  "description": "Schema validation test pack",
  "related_prs": [],
  "related_evidence_packs": []
}
```

---

## Migration Notes

### v1.0.0 (Current)

**Initial schema with header support.**

**Changes from Legacy (Pre-4B):**
- Added `schema_id` (required)
- Added `schema_version` (required)
- Added `pack_id` (required)
- Added `created_at` (optional)
- Added `producer` (optional)

**Backward Compatibility:**
- Legacy packs (without header) default to v1.0.0
- No breaking changes for existing validation logic

---

## API Usage

### Python API

```python
from src.ai_orchestration.evidence_pack_schema import (
    validate_and_migrate,
    validate_schema_header,
    SchemaValidationError,
)

# Load pack
pack = {...}  # From JSON/TOML

# Validate and migrate
try:
    validated_pack = validate_and_migrate(pack, target_version="1.0.0")
    print("✅ Pack validated successfully")
except SchemaValidationError as e:
    print(f"❌ Validation failed: [{e.code}] {e.message}")
```

### CLI (Future)

```bash
# Validate pack
python3 scripts/validate_evidence_pack_ci.py --pack pack.json

# Migrate pack
python3 scripts/migrate_evidence_pack_schema.py --pack pack.json --target 1.1.0
```

---

## References

- **Phase 4B Plan:** `PHASE4B_PLAN.md`
- **Mandatory Fields:** `docs/governance/ai_autonomy/SCHEMA_MANDATORY_FIELDS.md`
- **Phase 3B Quickstart:** `docs/ops/PHASE3B_EVIDENCE_PACK_QUICKSTART.md`
- **CI Gate Guide:** `docs/ai/EVIDENCE_PACK_CI_GATE.md`

---

## Changelog

### v1.0.0 (2026-01-08)
- Initial schema with header support
- Backward compatibility with legacy packs
- Migration registry framework
- Canonicalization rules
- Semantic validation rules

---

**Status:** ✅ Active Schema Version
