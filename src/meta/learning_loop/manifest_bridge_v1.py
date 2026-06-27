"""Offline Learning Bridge v1 — explicit input to ConfigPatch-Manifest v1 (Package D)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.meta.learning_loop.bridge import RawInput, normalize_patches
from src.meta.learning_loop.config_patch_manifest_v1 import (
    ConfigPatchManifestError,
    ConfigPatchManifestV1,
    ConfigPatchManifestValidationError,
    build_empty_config_patch_manifest_v1,
    compute_manifest_integrity,
    deserialize_config_patch_manifest_v1,
    patch_from_mapping,
    serialize_config_patch_manifest_v1,
    validate_config_patch_manifest_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    SCHEMA_VERSION_V1,
    canonical_futures_scope_ref,
    canonical_trading_logic_immutability_ref,
    is_valid_uuid,
)
from src.meta.learning_loop.models import ConfigPatch


class LearningManifestBridgeError(ValueError):
    """Fail-closed Package-D learning manifest bridge error."""


def load_learning_input_from_path(path: Path | str) -> RawInput:
    """Load explicit offline learning input from a JSON or JSONL snippet file."""
    input_path = Path(path)
    if not input_path.is_file():
        raise LearningManifestBridgeError(f"input file not found: {input_path}")

    try:
        text = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LearningManifestBridgeError(f"failed to read input file: {input_path}") from exc

    suffix = input_path.suffix.lower()
    if suffix == ".jsonl":
        rows: list[dict[str, Any]] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise LearningManifestBridgeError(
                    f"invalid JSONL at {input_path}:{line_number}: {exc.msg}"
                ) from exc
            if not isinstance(obj, dict):
                raise LearningManifestBridgeError(
                    f"JSONL row must be an object at {input_path}:{line_number}"
                )
            rows.append(obj)
        return rows

    if suffix == ".json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LearningManifestBridgeError(f"invalid JSON in {input_path}: {exc.msg}") from exc
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, list):
            if not all(isinstance(item, dict) for item in payload):
                raise LearningManifestBridgeError("JSON array input must contain only objects")
            return payload
        raise LearningManifestBridgeError("JSON root must be an object or array of patch objects")

    raise LearningManifestBridgeError(
        f"unsupported input format {suffix!r}; expected .json or .jsonl"
    )


def _raw_patch_dicts_by_target(
    raw: RawInput,
    *,
    normalized_targets: set[str],
) -> dict[str, dict[str, Any]]:
    if not normalized_targets:
        return {}

    if isinstance(raw, Mapping):
        if "patches" in raw and isinstance(raw["patches"], list):
            candidates = [item for item in raw["patches"] if isinstance(item, dict)]
            if raw["patches"] and not candidates:
                raise LearningManifestBridgeError("patch entries must be JSON objects")
        elif "target" in raw:
            candidates = [dict(raw)]
        else:
            candidates = []
    elif isinstance(raw, list):
        candidates = [item for item in raw if isinstance(item, dict)]
        if raw and not candidates:
            raise LearningManifestBridgeError("patch entries must be JSON objects")
    else:
        raise LearningManifestBridgeError("raw input must be a mapping or list of mappings")

    by_target: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        target = candidate.get("target")
        if not isinstance(target, str):
            continue
        key = target.strip()
        if key not in normalized_targets:
            continue
        if key in by_target:
            raise LearningManifestBridgeError(f"duplicate patch targets in explicit input: [{key}]")
        by_target[key] = candidate

    missing = sorted(normalized_targets - set(by_target))
    if missing:
        raise LearningManifestBridgeError(
            "explicit input missing required patch envelope fields for normalized targets: "
            f"{missing}"
        )

    return by_target


def build_config_patches_from_learning_input(raw: RawInput) -> list[ConfigPatch]:
    """Convert explicit offline input to ConfigPatch objects via normalize_patches."""
    try:
        normalized = normalize_patches(raw)
    except TypeError as exc:
        raise LearningManifestBridgeError(str(exc)) from exc

    if not normalized:
        return []

    raw_by_target = _raw_patch_dicts_by_target(
        raw,
        normalized_targets={item["target"] for item in normalized},
    )
    patches: list[ConfigPatch] = []
    for norm in sorted(normalized, key=lambda item: item["target"]):
        raw_patch = raw_by_target[norm["target"]]
        patch_id = raw_patch.get("id")
        status = raw_patch.get("status")
        if not isinstance(patch_id, str) or not patch_id.strip():
            raise LearningManifestBridgeError(f"patch id is required for target {norm['target']!r}")
        if status is None:
            raise LearningManifestBridgeError(
                f"patch status is required for target {norm['target']!r}"
            )

        mapping: dict[str, Any] = {
            "id": patch_id.strip(),
            "target": norm["target"],
            "new_value": norm["new_value"],
            "status": status,
        }
        if "old_value" in norm:
            mapping["old_value"] = norm["old_value"]
        if "reason" in norm:
            mapping["reason"] = norm["reason"]
        if "source_experiment_id" in norm:
            mapping["source_experiment_id"] = norm["source_experiment_id"]
        for optional_field in (
            "generated_at",
            "applied_at",
            "promoted_at",
            "confidence_score",
            "meta",
        ):
            if optional_field in raw_patch:
                mapping[optional_field] = raw_patch[optional_field]

        try:
            patches.append(patch_from_mapping(mapping))
        except ConfigPatchManifestError as exc:
            raise LearningManifestBridgeError(str(exc)) from exc

    patch_ids = [patch.id for patch in patches]
    if len(set(patch_ids)) != len(patch_ids):
        raise LearningManifestBridgeError("duplicate patch id in explicit input")

    return patches


def build_config_patch_manifest_v1_from_learning_input(
    raw: RawInput,
    *,
    manifest_id: str,
    lineage_manifest_ref: str,
    generated_at: datetime,
    generated_by: str | None = "package_d_learning_manifest_bridge_v1",
    metadata: Mapping[str, Any] | None = None,
) -> ConfigPatchManifestV1:
    """Build a validated ConfigPatch-Manifest v1 envelope from explicit offline input."""
    if not isinstance(manifest_id, str) or not is_valid_uuid(manifest_id):
        raise LearningManifestBridgeError("manifest_id must be a UUID")
    if not isinstance(lineage_manifest_ref, str) or not is_valid_uuid(lineage_manifest_ref):
        raise LearningManifestBridgeError("lineage_manifest_ref must be a UUID")

    patches = build_config_patches_from_learning_input(raw)
    if not patches:
        manifest = build_empty_config_patch_manifest_v1(
            manifest_id=manifest_id,
            generated_at=generated_at,
            lineage_manifest_ref=lineage_manifest_ref,
            generated_by=generated_by,
        )
    else:
        manifest = ConfigPatchManifestV1(
            schema_version=SCHEMA_VERSION_V1,
            manifest_id=manifest_id,
            generated_at=generated_at,
            generated_by=generated_by,
            lineage_manifest_ref=lineage_manifest_ref,
            source_scope=canonical_futures_scope_ref(),
            trading_logic_immutability_ref=canonical_trading_logic_immutability_ref(),
            patches=patches,
            metadata=dict(metadata) if metadata is not None else {},
        )
        manifest.integrity = compute_manifest_integrity(manifest)

    serialized = serialize_config_patch_manifest_v1(manifest)
    payload = json.loads(serialized)
    valid, phase, errors, verdict = validate_config_patch_manifest_v1(payload)
    if not valid:
        raise ConfigPatchManifestValidationError(
            "ConfigPatch-Manifest v1 validation failed during bridge production",
            phase=phase,
            errors=errors,
            verdict=verdict,
        )

    return deserialize_config_patch_manifest_v1(payload)


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def write_config_patch_manifest_v1_atomic(
    manifest: ConfigPatchManifestV1,
    output_path: Path | str,
) -> Path:
    """Validate, serialize, and atomically write a ConfigPatch-Manifest v1 JSON file."""
    out = Path(output_path)
    serialized = serialize_config_patch_manifest_v1(manifest)
    payload = json.loads(serialized)
    valid, phase, errors, verdict = validate_config_patch_manifest_v1(payload)
    if not valid:
        raise ConfigPatchManifestValidationError(
            f"refusing to write invalid manifest to {out}",
            phase=phase,
            errors=errors,
            verdict=verdict,
        )

    _atomic_write_text(out, serialized)
    return out


def produce_config_patch_manifest_v1_from_paths(
    *,
    input_path: Path | str,
    output_path: Path | str,
    manifest_id: str,
    lineage_manifest_ref: str,
    generated_at: datetime | None = None,
    generated_by: str | None = "package_d_learning_manifest_bridge_v1",
) -> ConfigPatchManifestV1:
    """End-to-end offline bridge: explicit snippet file -> validated manifest file."""
    raw = load_learning_input_from_path(input_path)
    when = generated_at if generated_at is not None else datetime.now(timezone.utc)
    manifest = build_config_patch_manifest_v1_from_learning_input(
        raw,
        manifest_id=manifest_id,
        lineage_manifest_ref=lineage_manifest_ref,
        generated_at=when,
        generated_by=generated_by,
    )
    write_config_patch_manifest_v1_atomic(manifest, output_path)
    return manifest


__all__ = [
    "LearningManifestBridgeError",
    "build_config_patch_manifest_v1_from_learning_input",
    "build_config_patches_from_learning_input",
    "load_learning_input_from_path",
    "produce_config_patch_manifest_v1_from_paths",
    "write_config_patch_manifest_v1_atomic",
]
