"""Promotion proposal input reference propagation (Package C, offline, fail-closed)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.meta.learning_loop.config_patch_manifest_v1 import ConfigPatchManifestV1
from src.meta.learning_loop.contract_safety_v1 import (
    SCHEMA_VERSION_V1,
    is_valid_uuid,
    validate_schema_version,
)

from .models import PromotionProposal


class PromotionInputReferencesError(ValueError):
    """Fail-closed error for promotion input reference propagation."""


_FORBIDDEN_META_KEYS = frozenset(
    {
        "patches",
        "refs",
        "integrity",
        "source_scope",
        "trading_logic_immutability_ref",
        "futures_scope_ref",
        "manifest",
        "lineage_manifest",
        "config_patch_manifest",
        "candidate_lineage_manifest",
    }
)

_FORBIDDEN_META_TOKENS = frozenset(
    {
        "master_v2",
        "double_play",
        "strategy",
        "signal",
        "execution",
        "killswitch",
        "leverage",
        "stop_loss",
        "take_profit",
        "order_routing",
        "live_arming",
    }
)

_ALLOWED_REFERENCE_KEYS = frozenset(
    {
        "config_patch_manifest_id",
        "candidate_lineage_manifest_ref",
        "config_patch_manifest_schema_version",
        "candidate_lineage_manifest_schema_version",
    }
)


@dataclass(frozen=True)
class PromotionInputReferencesV1:
    """Reference-only FKs from a validated ConfigPatch-Manifest v1 input."""

    config_patch_manifest_id: str
    candidate_lineage_manifest_ref: str | None
    config_patch_manifest_schema_version: str
    candidate_lineage_manifest_schema_version: str | None = None

    def to_proposal_meta_fields(self) -> dict[str, str]:
        fields: dict[str, str] = {
            "config_patch_manifest_id": self.config_patch_manifest_id,
            "config_patch_manifest_schema_version": self.config_patch_manifest_schema_version,
        }
        if self.candidate_lineage_manifest_ref is not None:
            fields["candidate_lineage_manifest_ref"] = self.candidate_lineage_manifest_ref
        if self.candidate_lineage_manifest_schema_version is not None:
            fields["candidate_lineage_manifest_schema_version"] = (
                self.candidate_lineage_manifest_schema_version
            )
        return fields


def promotion_input_references_from_manifest(
    manifest: ConfigPatchManifestV1,
) -> PromotionInputReferencesV1:
    """Extract fail-closed reference FKs from an already validated manifest."""
    manifest_id = manifest.manifest_id
    if not isinstance(manifest_id, str) or not manifest_id.strip():
        raise PromotionInputReferencesError("config_patch_manifest_id is required")
    if not is_valid_uuid(manifest_id):
        raise PromotionInputReferencesError("config_patch_manifest_id must be a UUID")

    schema_result = validate_schema_version(manifest.schema_version)
    if not schema_result.valid:
        raise PromotionInputReferencesError(
            f"unsupported config_patch_manifest_schema_version: {manifest.schema_version!r}"
        )

    lineage_ref = manifest.lineage_manifest_ref
    lineage_schema_version: str | None = None
    if lineage_ref is not None:
        if not isinstance(lineage_ref, str) or not lineage_ref.strip():
            raise PromotionInputReferencesError("candidate_lineage_manifest_ref must be non-empty")
        if not is_valid_uuid(lineage_ref):
            raise PromotionInputReferencesError("candidate_lineage_manifest_ref must be a UUID")
        lineage_schema_version = SCHEMA_VERSION_V1

    return PromotionInputReferencesV1(
        config_patch_manifest_id=manifest_id,
        candidate_lineage_manifest_ref=lineage_ref,
        config_patch_manifest_schema_version=SCHEMA_VERSION_V1,
        candidate_lineage_manifest_schema_version=lineage_schema_version,
    )


def validate_proposal_reference_meta_fields(meta_fields: Mapping[str, Any]) -> None:
    """Reject embedded payloads, unknown keys, or trading-logic smuggling attempts."""
    for key in meta_fields:
        if key in _FORBIDDEN_META_KEYS:
            raise PromotionInputReferencesError(
                f"embedded manifest payload key not allowed in proposal references: {key!r}"
            )

    unknown = set(meta_fields) - _ALLOWED_REFERENCE_KEYS
    if unknown:
        raise PromotionInputReferencesError(
            f"unsupported promotion input reference keys: {sorted(unknown)!r}"
        )

    for key, value in meta_fields.items():
        if not isinstance(value, str) or not value.strip():
            raise PromotionInputReferencesError(f"{key} must be a non-empty string")
        lowered = value.lower()
        for token in _FORBIDDEN_META_TOKENS:
            if token in lowered:
                raise PromotionInputReferencesError(
                    f"{key} contains forbidden trading-logic token: {token!r}"
                )

    manifest_id = meta_fields.get("config_patch_manifest_id")
    if manifest_id is None:
        raise PromotionInputReferencesError("config_patch_manifest_id is required")
    if not is_valid_uuid(str(manifest_id)):
        raise PromotionInputReferencesError("config_patch_manifest_id must be a UUID")

    manifest_schema = meta_fields.get("config_patch_manifest_schema_version")
    if manifest_schema is None:
        raise PromotionInputReferencesError("config_patch_manifest_schema_version is required")
    schema_result = validate_schema_version(str(manifest_schema))
    if not schema_result.valid:
        raise PromotionInputReferencesError(
            f"unsupported config_patch_manifest_schema_version: {manifest_schema!r}"
        )

    lineage_ref = meta_fields.get("candidate_lineage_manifest_ref")
    lineage_schema = meta_fields.get("candidate_lineage_manifest_schema_version")
    if lineage_ref is not None:
        if not is_valid_uuid(str(lineage_ref)):
            raise PromotionInputReferencesError("candidate_lineage_manifest_ref must be a UUID")
        if lineage_schema is None:
            raise PromotionInputReferencesError(
                "candidate_lineage_manifest_schema_version required when lineage ref present"
            )
        lineage_schema_result = validate_schema_version(str(lineage_schema))
        if not lineage_schema_result.valid:
            raise PromotionInputReferencesError(
                f"unsupported candidate_lineage_manifest_schema_version: {lineage_schema!r}"
            )
    elif lineage_schema is not None:
        raise PromotionInputReferencesError(
            "candidate_lineage_manifest_schema_version without candidate_lineage_manifest_ref"
        )


def apply_promotion_input_references_to_proposal(
    proposal: PromotionProposal,
    references: PromotionInputReferencesV1,
) -> None:
    """Add validated reference-only FK fields to an existing proposal meta dict."""
    meta_fields = references.to_proposal_meta_fields()
    validate_proposal_reference_meta_fields(meta_fields)

    for key, value in meta_fields.items():
        if key in proposal.meta and proposal.meta[key] != value:
            raise PromotionInputReferencesError(
                f"conflicting promotion input reference for {key!r}"
            )
        proposal.meta[key] = value


__all__ = [
    "PromotionInputReferencesError",
    "PromotionInputReferencesV1",
    "apply_promotion_input_references_to_proposal",
    "promotion_input_references_from_manifest",
    "validate_proposal_reference_meta_fields",
]
