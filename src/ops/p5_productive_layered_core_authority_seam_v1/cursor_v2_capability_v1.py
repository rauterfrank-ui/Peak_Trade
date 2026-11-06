"""Cursor v2 capability: layered-core snapshot provenance + non-authoritative scope mirrors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from trading.master_v2.layered_core_authority_seal_v1 import (
    LayeredCoreAuthoritySealV1,
    validate_layered_core_authority_seal_v1,
)

CURSOR_V2_SCHEMA_NAME = "current_productive_sidestate_confirmation_cursor.v2"
CURSOR_V2_SCHEMA_VERSION = "v2"
CURSOR_V2_CAPABILITY_OWNER = (
    "ops.p5_productive_layered_core_authority_seam_v1.cursor_v2_capability_v1"
)


@dataclass(frozen=True)
class P5CursorV2ProvenanceV1:
    layered_core_snapshot_id: str
    layered_core_store_manifest_digest: str
    layered_core_seal_digest: str
    scope_mirror_non_authoritative: bool = True
    runtime_scope_mirror_non_authoritative: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "layered_core_snapshot_id": self.layered_core_snapshot_id,
            "layered_core_store_manifest_digest": self.layered_core_store_manifest_digest,
            "layered_core_seal_digest": self.layered_core_seal_digest,
            "scope_mirror_non_authoritative": self.scope_mirror_non_authoritative,
            "runtime_scope_mirror_non_authoritative": self.runtime_scope_mirror_non_authoritative,
        }


def build_p5_cursor_v2_provenance_from_seal_v1(
    seal: LayeredCoreAuthoritySealV1,
    *,
    instrument_id: str,
) -> tuple[Optional[P5CursorV2ProvenanceV1], tuple[str, ...]]:
    validation = validate_layered_core_authority_seal_v1(seal, instrument_id=instrument_id)
    if not validation.ok:
        return None, validation.failure_codes
    return (
        P5CursorV2ProvenanceV1(
            layered_core_snapshot_id=seal.episode_snapshot_id,
            layered_core_store_manifest_digest=seal.store_manifest_digest,
            layered_core_seal_digest=seal.seal_digest,
        ),
        (),
    )


def merge_cursor_v2_provenance_into_payload_v1(
    payload: Mapping[str, Any],
    provenance: P5CursorV2ProvenanceV1,
) -> dict[str, Any]:
    merged = dict(payload)
    merged["schema_name"] = CURSOR_V2_SCHEMA_NAME
    merged["schema_version"] = CURSOR_V2_SCHEMA_VERSION
    merged["p5_layered_core_provenance"] = provenance.to_dict()
    return merged


__all__ = [
    "CURSOR_V2_CAPABILITY_OWNER",
    "CURSOR_V2_SCHEMA_NAME",
    "CURSOR_V2_SCHEMA_VERSION",
    "P5CursorV2ProvenanceV1",
    "build_p5_cursor_v2_provenance_from_seal_v1",
    "merge_cursor_v2_provenance_into_payload_v1",
]
