"""Persist/restore owner for RegimeSideStateProjectionLifecycleStateV1 (B3; no productive bind)."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Tuple

from src.ops.p5_8b_regime_sidestate_projection_phase_authority_v1.contract_v1 import (
    RegimeSideStateProjectionLifecycleStateV1,
    lifecycle_to_dict_v1,
    parse_lifecycle_v1,
)

PERSISTENCE_OWNER = "ops.p5_8b_regime_sidestate_projection_phase_authority_v1.persistence_v1"
ENVELOPE_SCHEMA_NAME = "regime_sidestate_projection_lifecycle_persist_envelope.v1"
ENVELOPE_SCHEMA_VERSION = "v1"
SNAPSHOT_FILENAME = "regime_sidestate_projection_lifecycle.v1.json"
MANIFEST_FILENAME = "regime_sidestate_projection_lifecycle.v1.manifest.sha256"


class RegimeSidestateProjectionLifecyclePersistenceError(ValueError):
    """Fail-closed lifecycle durable store violation."""


@dataclass(frozen=True)
class RegimeSidestateProjectionLifecyclePersistBindingV1:
    """Exact episode/cursor identity binding for lifecycle durable carry-out."""

    instrument_id: str
    layered_episode_snapshot_id: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def envelope_to_dict_v1(
    *,
    lifecycle: RegimeSideStateProjectionLifecycleStateV1,
    binding: RegimeSidestateProjectionLifecyclePersistBindingV1,
) -> dict[str, Any]:
    iid = str(binding.instrument_id or "").strip()
    snap = str(binding.layered_episode_snapshot_id or "").strip()
    if not iid or not snap:
        raise RegimeSidestateProjectionLifecyclePersistenceError("binding_identity_incomplete")
    if lifecycle.instrument_id != iid:
        raise RegimeSidestateProjectionLifecyclePersistenceError("lifecycle_instrument_mismatch")
    return {
        "schema_name": ENVELOPE_SCHEMA_NAME,
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "instrument_id": iid,
        "layered_episode_snapshot_id": snap,
        "lifecycle": lifecycle_to_dict_v1(lifecycle),
    }


def parse_envelope_v1(
    payload: Mapping[str, Any] | None,
    *,
    binding: RegimeSidestateProjectionLifecyclePersistBindingV1,
) -> Tuple[RegimeSideStateProjectionLifecycleStateV1 | None, Tuple[str, ...]]:
    if payload is None or not isinstance(payload, Mapping):
        return None, ("lifecycle_envelope_payload_invalid",)
    schema_name = str(payload.get("schema_name") or "").strip()
    schema_version = str(payload.get("schema_version") or "").strip()
    if schema_name != ENVELOPE_SCHEMA_NAME:
        return None, ("lifecycle_envelope_schema_mismatch",)
    if schema_version != ENVELOPE_SCHEMA_VERSION:
        return None, ("lifecycle_envelope_schema_version_mismatch",)
    envelope_iid = str(payload.get("instrument_id") or "").strip()
    envelope_snap = str(payload.get("layered_episode_snapshot_id") or "").strip()
    expected_iid = str(binding.instrument_id or "").strip()
    expected_snap = str(binding.layered_episode_snapshot_id or "").strip()
    if envelope_iid != expected_iid:
        return None, ("lifecycle_envelope_instrument_mismatch",)
    if envelope_snap != expected_snap:
        return None, ("lifecycle_envelope_snapshot_binding_mismatch",)
    lifecycle_payload = payload.get("lifecycle")
    if not isinstance(lifecycle_payload, Mapping):
        return None, ("lifecycle_envelope_nested_payload_invalid",)
    return parse_lifecycle_v1(lifecycle_payload, expected_instrument_id=expected_iid)


def atomic_persist_regime_sidestate_projection_lifecycle_v1(
    store_root: Path,
    *,
    lifecycle: RegimeSideStateProjectionLifecycleStateV1,
    binding: RegimeSidestateProjectionLifecyclePersistBindingV1,
) -> str:
    """Atomic write lifecycle envelope JSON + manifest digest under store_root."""
    store_root.mkdir(parents=True, exist_ok=True)
    envelope = envelope_to_dict_v1(lifecycle=lifecycle, binding=binding)
    body = _canonical_json(envelope)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    snapshot_path = store_root / SNAPSHOT_FILENAME
    manifest_path = store_root / MANIFEST_FILENAME
    tmp_snapshot = snapshot_path.with_suffix(".json.tmp")
    tmp_manifest = manifest_path.with_suffix(".sha256.tmp")
    tmp_snapshot.write_text(body, encoding="utf-8")
    tmp_manifest.write_text(f"{digest}  {SNAPSHOT_FILENAME}\n", encoding="utf-8")
    os.replace(tmp_snapshot, snapshot_path)
    os.replace(tmp_manifest, manifest_path)
    return digest


def restore_regime_sidestate_projection_lifecycle_v1(
    store_root: Path,
    *,
    binding: RegimeSidestateProjectionLifecyclePersistBindingV1,
) -> RegimeSideStateProjectionLifecycleStateV1:
    """Restore lifecycle from durable store; fail-closed on binding or digest mismatch."""
    snapshot_path = store_root / SNAPSHOT_FILENAME
    manifest_path = store_root / MANIFEST_FILENAME
    if not snapshot_path.is_file() or not manifest_path.is_file():
        raise RegimeSidestateProjectionLifecyclePersistenceError("LIFECYCLE_STORE_INCOMPLETE")
    body = snapshot_path.read_text(encoding="utf-8")
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    manifest_line = manifest_path.read_text(encoding="utf-8").strip().split()
    if not manifest_line or manifest_line[0] != digest:
        raise RegimeSidestateProjectionLifecyclePersistenceError(
            "LIFECYCLE_MANIFEST_DIGEST_MISMATCH"
        )
    payload = json.loads(body)
    if not isinstance(payload, Mapping):
        raise RegimeSidestateProjectionLifecyclePersistenceError("LIFECYCLE_ENVELOPE_NOT_OBJECT")
    lifecycle, codes = parse_envelope_v1(payload, binding=binding)
    if lifecycle is None or codes:
        code = codes[0] if codes else "lifecycle_restore_failed"
        raise RegimeSidestateProjectionLifecyclePersistenceError(code)
    return lifecycle


def roundtrip_regime_sidestate_projection_lifecycle_v1(
    *,
    lifecycle: RegimeSideStateProjectionLifecycleStateV1,
    binding: RegimeSidestateProjectionLifecyclePersistBindingV1,
) -> RegimeSideStateProjectionLifecycleStateV1:
    """Memory codec parity (no filesystem)."""
    envelope = envelope_to_dict_v1(lifecycle=lifecycle, binding=binding)
    restored, codes = parse_envelope_v1(envelope, binding=binding)
    if restored is None or codes:
        code = codes[0] if codes else "lifecycle_roundtrip_failed"
        raise RegimeSidestateProjectionLifecyclePersistenceError(code)
    return restored


__all__ = [
    "ENVELOPE_SCHEMA_NAME",
    "ENVELOPE_SCHEMA_VERSION",
    "MANIFEST_FILENAME",
    "PERSISTENCE_OWNER",
    "RegimeSidestateProjectionLifecyclePersistBindingV1",
    "RegimeSidestateProjectionLifecyclePersistenceError",
    "SNAPSHOT_FILENAME",
    "atomic_persist_regime_sidestate_projection_lifecycle_v1",
    "envelope_to_dict_v1",
    "parse_envelope_v1",
    "restore_regime_sidestate_projection_lifecycle_v1",
    "roundtrip_regime_sidestate_projection_lifecycle_v1",
]
