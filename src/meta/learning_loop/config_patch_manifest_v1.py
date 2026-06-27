"""ConfigPatch-Manifest v1 — offline canonical promotion-input contract."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.meta.learning_loop.contract_safety_v1 import (
    SCHEMA_VERSION_V1,
    ValidationPhase,
    canonical_futures_scope_ref,
    canonical_trading_logic_immutability_ref,
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
    is_valid_uuid,
    validate_futures_scope_ref,
    validate_integrity_block,
    validate_patch_target,
    validate_schema_version,
    validate_trading_logic_immutability_ref,
)
from src.meta.learning_loop.models import ConfigPatch, PatchStatus


class ConfigPatchManifestError(ValueError):
    """Fail-closed ConfigPatch-Manifest v1 error."""


class ConfigPatchManifestValidationError(ConfigPatchManifestError):
    """Raised when Package-A manifest validation fails fail-closed."""

    def __init__(
        self,
        message: str,
        *,
        phase: ValidationPhase,
        errors: tuple[str, ...],
        verdict: str | None = None,
    ) -> None:
        super().__init__(message)
        self.phase = phase
        self.errors = errors
        self.verdict = verdict


@dataclass(frozen=True)
class ManifestIntegrity:
    content_sha256: str


@dataclass
class ConfigPatchManifestV1:
    schema_version: str
    manifest_id: str
    generated_at: datetime
    source_scope: dict[str, Any]
    trading_logic_immutability_ref: dict[str, Any]
    patches: list[ConfigPatch] = field(default_factory=list)
    generated_by: str | None = None
    lineage_manifest_ref: str | None = None
    integrity: ManifestIntegrity | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def _parse_datetime(value: Any, *, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        raise ConfigPatchManifestError(f"{field_name} must be an ISO8601 string")
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ConfigPatchManifestError(f"{field_name} must be an ISO8601 string") from exc


def _parse_patch_status(value: Any) -> PatchStatus:
    if isinstance(value, PatchStatus):
        return value
    if not isinstance(value, str):
        raise ConfigPatchManifestError("patch status must be a string enum value")
    try:
        return PatchStatus(value)
    except ValueError as exc:
        raise ConfigPatchManifestError(f"unknown PatchStatus: {value!r}") from exc


def patch_from_mapping(raw: Mapping[str, Any]) -> ConfigPatch:
    required = ("id", "target", "new_value", "status")
    for key in required:
        if key not in raw:
            raise ConfigPatchManifestError(f"patch missing required field: {key}")

    generated_at = raw.get("generated_at")
    applied_at = raw.get("applied_at")
    promoted_at = raw.get("promoted_at")
    meta = raw.get("meta")

    return ConfigPatch(
        id=str(raw["id"]),
        target=str(raw["target"]),
        old_value=raw.get("old_value"),
        new_value=raw["new_value"],
        status=_parse_patch_status(raw["status"]),
        generated_at=_parse_datetime(generated_at, field_name="generated_at")
        if generated_at is not None
        else None,
        applied_at=_parse_datetime(applied_at, field_name="applied_at")
        if applied_at is not None
        else None,
        promoted_at=_parse_datetime(promoted_at, field_name="promoted_at")
        if promoted_at is not None
        else None,
        reason=str(raw["reason"]) if raw.get("reason") is not None else None,
        source_experiment_id=str(raw["source_experiment_id"])
        if raw.get("source_experiment_id") is not None
        else None,
        confidence_score=float(raw["confidence_score"])
        if raw.get("confidence_score") is not None
        else None,
        meta=dict(meta) if isinstance(meta, dict) else {},
    )


def patch_to_mapping(patch: ConfigPatch) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": patch.id,
        "target": patch.target,
        "new_value": patch.new_value,
        "status": patch.status.value,
    }
    if patch.old_value is not None:
        payload["old_value"] = patch.old_value
    if patch.generated_at is not None:
        payload["generated_at"] = patch.generated_at.isoformat()
    if patch.applied_at is not None:
        payload["applied_at"] = patch.applied_at.isoformat()
    if patch.promoted_at is not None:
        payload["promoted_at"] = patch.promoted_at.isoformat()
    if patch.reason is not None:
        payload["reason"] = patch.reason
    if patch.source_experiment_id is not None:
        payload["source_experiment_id"] = patch.source_experiment_id
    if patch.confidence_score is not None:
        payload["confidence_score"] = patch.confidence_score
    if patch.meta:
        payload["meta"] = dict(patch.meta)
    return payload


def manifest_to_canonical_dict(
    manifest: ConfigPatchManifestV1,
    *,
    include_integrity: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": manifest.schema_version,
        "manifest_id": manifest.manifest_id,
        "generated_at": manifest.generated_at.isoformat(),
        "source_scope": dict(manifest.source_scope),
        "trading_logic_immutability_ref": dict(manifest.trading_logic_immutability_ref),
        "patches": [patch_to_mapping(patch) for patch in manifest.patches],
    }
    if manifest.generated_by is not None:
        payload["generated_by"] = manifest.generated_by
    if manifest.lineage_manifest_ref is not None:
        payload["lineage_manifest_ref"] = manifest.lineage_manifest_ref
    if manifest.metadata:
        payload["metadata"] = dict(manifest.metadata)
    if include_integrity and manifest.integrity is not None:
        payload["integrity"] = {"content_sha256": manifest.integrity.content_sha256}
    return payload


def compute_manifest_integrity(manifest: ConfigPatchManifestV1) -> ManifestIntegrity:
    payload = manifest_to_canonical_dict(manifest, include_integrity=False)
    return ManifestIntegrity(content_sha256=compute_content_sha256(payload))


def serialize_config_patch_manifest_v1(manifest: ConfigPatchManifestV1) -> str:
    if manifest.integrity is None:
        manifest.integrity = compute_manifest_integrity(manifest)
    return deterministic_json_dumps(manifest_to_canonical_dict(manifest, include_integrity=True))


def deserialize_config_patch_manifest_v1(data: Mapping[str, Any]) -> ConfigPatchManifestV1:
    if not isinstance(data, Mapping):
        raise ConfigPatchManifestError("manifest payload must be a mapping")

    required_fields = (
        "schema_version",
        "manifest_id",
        "generated_at",
        "source_scope",
        "trading_logic_immutability_ref",
        "patches",
        "integrity",
    )
    for key in required_fields:
        if key not in data:
            raise ConfigPatchManifestError(f"missing required field: {key}")

    patches_raw = data["patches"]
    if not isinstance(patches_raw, list):
        raise ConfigPatchManifestError("patches must be an array")

    integrity_raw = data["integrity"]
    if not isinstance(integrity_raw, Mapping):
        raise ConfigPatchManifestError("integrity must be an object")
    digest = integrity_raw.get("content_sha256")
    if not isinstance(digest, str):
        raise ConfigPatchManifestError("integrity.content_sha256 must be a string")

    manifest = ConfigPatchManifestV1(
        schema_version=str(data["schema_version"]),
        manifest_id=str(data["manifest_id"]),
        generated_at=_parse_datetime(data["generated_at"], field_name="generated_at"),
        generated_by=str(data["generated_by"]) if data.get("generated_by") is not None else None,
        lineage_manifest_ref=str(data["lineage_manifest_ref"])
        if data.get("lineage_manifest_ref") is not None
        else None,
        source_scope=dict(data["source_scope"]),
        trading_logic_immutability_ref=dict(data["trading_logic_immutability_ref"]),
        patches=[patch_from_mapping(item) for item in patches_raw if isinstance(item, Mapping)],
        integrity=ManifestIntegrity(content_sha256=digest),
        metadata=dict(data["metadata"]) if isinstance(data.get("metadata"), dict) else {},
    )
    if len(manifest.patches) != len(patches_raw):
        raise ConfigPatchManifestError("each patch must be an object")
    return manifest


def _is_fixture_mode(metadata: Mapping[str, Any]) -> bool:
    return metadata.get("fixture_kind") == "demo_patches_for_promotion"


def validate_config_patch_manifest_v1(
    data: Mapping[str, Any],
) -> tuple[bool, ValidationPhase, tuple[str, ...], str | None]:
    if not isinstance(data, Mapping):
        return False, ValidationPhase.SCHEMA, ("manifest payload must be a mapping",), None

    required_top_level = (
        "schema_version",
        "manifest_id",
        "generated_at",
        "source_scope",
        "trading_logic_immutability_ref",
        "patches",
        "integrity",
    )
    for key in required_top_level:
        if key not in data:
            return False, ValidationPhase.SCHEMA, (f"missing required field: {key}",), None

    if not isinstance(data["patches"], list):
        return False, ValidationPhase.SCHEMA, ("patches must be an array",), None
    if not isinstance(data["integrity"], Mapping):
        return False, ValidationPhase.SCHEMA, ("integrity must be an object",), None
    metadata = data.get("metadata") if isinstance(data.get("metadata"), Mapping) else {}

    schema_version_result = validate_schema_version(data["schema_version"])
    if not schema_version_result.valid:
        return (
            False,
            schema_version_result.phase,
            schema_version_result.errors,
            schema_version_result.verdict,
        )

    futures_result = validate_futures_scope_ref(data["source_scope"])
    if not futures_result.valid:
        return False, futures_result.phase, futures_result.errors, futures_result.verdict

    immutability_result = validate_trading_logic_immutability_ref(
        data["trading_logic_immutability_ref"]
    )
    if not immutability_result.valid:
        return (
            False,
            immutability_result.phase,
            immutability_result.errors,
            immutability_result.verdict,
        )

    for patch in data["patches"]:
        if not isinstance(patch, Mapping):
            return False, ValidationPhase.SCHEMA, ("each patch must be an object",), None
        target = patch.get("target")
        if not isinstance(target, str):
            return False, ValidationPhase.TARGET_POLICY, ("patch target must be a string",), None
        target_result = validate_patch_target(target)
        if not target_result.valid:
            return False, target_result.phase, target_result.errors, target_result.verdict
        status = patch.get("status")
        if status is not None:
            try:
                PatchStatus(str(status))
            except ValueError:
                return False, ValidationPhase.SCHEMA, (f"unknown PatchStatus: {status!r}",), None

    manifest_id = data["manifest_id"]
    if not isinstance(manifest_id, str) or not is_valid_uuid(manifest_id):
        return False, ValidationPhase.SCHEMA, ("manifest_id must be a UUID",), None

    lineage_ref = data.get("lineage_manifest_ref")
    if lineage_ref is None and not _is_fixture_mode(metadata):
        return (
            False,
            ValidationPhase.LINEAGE_REFERENCES,
            ("lineage_manifest_ref is required unless metadata.fixture_kind is set",),
            None,
        )
    if lineage_ref is not None and not is_valid_uuid(str(lineage_ref)):
        return (
            False,
            ValidationPhase.LINEAGE_REFERENCES,
            ("lineage_manifest_ref must be a UUID",),
            None,
        )

    patch_ids: list[str] = []
    for patch in data["patches"]:
        patch_id = patch.get("id")
        if not isinstance(patch_id, str) or not patch_id.strip():
            return (
                False,
                ValidationPhase.CARDINALITY,
                ("patch id must be a non-empty string",),
                None,
            )
        patch_ids.append(patch_id)
    if len(set(patch_ids)) != len(patch_ids):
        return False, ValidationPhase.CARDINALITY, ("duplicate patch id",), None

    try:
        manifest = deserialize_config_patch_manifest_v1(data)
    except ConfigPatchManifestError as exc:
        return False, ValidationPhase.SCHEMA, (str(exc),), None

    expected_digest = compute_manifest_integrity(manifest).content_sha256
    integrity_result = validate_integrity_block(data["integrity"], expected_digest=expected_digest)
    if not integrity_result.valid:
        return False, integrity_result.phase, integrity_result.errors, integrity_result.verdict

    return True, ValidationPhase.RESULT, (), None


def build_empty_config_patch_manifest_v1(
    *,
    manifest_id: str,
    generated_at: datetime,
    lineage_manifest_ref: str,
    generated_by: str | None = "package_a_contract_tests",
) -> ConfigPatchManifestV1:
    manifest = ConfigPatchManifestV1(
        schema_version=SCHEMA_VERSION_V1,
        manifest_id=manifest_id,
        generated_at=generated_at,
        generated_by=generated_by,
        lineage_manifest_ref=lineage_manifest_ref,
        source_scope=canonical_futures_scope_ref(),
        trading_logic_immutability_ref=canonical_trading_logic_immutability_ref(),
        patches=[],
    )
    manifest.integrity = compute_manifest_integrity(manifest)
    return manifest


def load_config_patch_manifest_v1_from_json_path(path: Path | str) -> ConfigPatchManifestV1:
    """Load, validate, and deserialize a ConfigPatch-Manifest v1 JSON file."""
    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise ConfigPatchManifestError(f"manifest file not found: {manifest_path}")

    try:
        raw_text = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigPatchManifestError(f"failed to read manifest file: {manifest_path}") from exc

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ConfigPatchManifestError(f"invalid JSON in manifest file: {manifest_path}") from exc

    if not isinstance(data, Mapping):
        raise ConfigPatchManifestError("manifest root must be a JSON object")

    valid, phase, errors, verdict = validate_config_patch_manifest_v1(data)
    if not valid:
        raise ConfigPatchManifestValidationError(
            f"ConfigPatch-Manifest v1 validation failed for {manifest_path}",
            phase=phase,
            errors=errors,
            verdict=verdict,
        )

    return deserialize_config_patch_manifest_v1(data)


def load_config_patches_for_promotion_from_manifest_path(
    path: Path | str,
) -> list[ConfigPatch]:
    """Return validated ConfigPatch entries from a canonical manifest file."""
    return load_promotion_input_from_manifest_path(path).patches


@dataclass(frozen=True)
class PromotionManifestInputV1:
    """Validated ConfigPatch-Manifest v1 promotion input (patches + reference FKs)."""

    patches: tuple[ConfigPatch, ...]
    manifest: ConfigPatchManifestV1


def load_promotion_input_from_manifest_path(path: Path | str) -> PromotionManifestInputV1:
    """Load manifest envelope and patches without discarding reference FKs."""
    manifest = load_config_patch_manifest_v1_from_json_path(path)
    return PromotionManifestInputV1(patches=tuple(manifest.patches), manifest=manifest)
