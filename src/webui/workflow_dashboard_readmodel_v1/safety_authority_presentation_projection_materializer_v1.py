"""Non-authoritative materializer for Safety Authority presentation projection.

CAPABILITY_ID=CAPABILITY_PRESENTATION_SAFETY_AUTHORITY_PROJECTION_MATERIALIZER_AUTOBIND_V1

Consumes already-produced Safety binder-compatible field payloads and writes
the non-authoritative presentation projection schema to the loader-owned path
``readmodels/safety_authority.v1.json``. This module:

- AUTHORITY_EFFECT=NONE
- SAFETY_AUTHORITY_EFFECT=NONE
- never creates, mutates, triggers, recovers, or evaluates KillSwitch
- never imports src.risk_layer.kill_switch
- never imports trading.master_v2.killswitch_boundary_* adapters
- never accesses productive/live KillSwitch state files
- never invents kill_switch_state, veto_active, timestamps, or reason_codes
- fail-closed: missing source → MISSING_SOURCE and no artifact write;
  invalid source → FAIL_CLOSED and no artifact write
- projection remains non-authoritative and must never flow back into runtime
  or authority chains

Deterministic serialization and atomic replace only. This projection path does
not own a separate MANIFEST contract; integrity follows the existing loader
schema/authority/fields checks.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .safety_authority_presentation_projection_v1 import (
    AUTHORITY_EFFECT,
    LOAD_ERROR_FIELDS_INVALID,
    LOAD_ERROR_SCHEMA_MISMATCH,
    LOAD_ERROR_TIMESTAMP_MISSING,
    PROJECTION_ROLE,
    SAFETY_AUTHORITY_EFFECT,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STORAGE_RELATIVE_PATH,
    map_safety_authority_fields_to_binder_fields_v1,
    project_safety_authority_presentation_projection_v1,
)

CAPABILITY_ID = "CAPABILITY_PRESENTATION_SAFETY_AUTHORITY_PROJECTION_MATERIALIZER_AUTOBIND_V1"
OWNER_MODULE = (
    "webui.workflow_dashboard_readmodel_v1.safety_authority_presentation_projection_materializer_v1"
)

STATUS_WRITTEN = "WRITTEN"
STATUS_MISSING_SOURCE = "MISSING_SOURCE"
STATUS_FAIL_CLOSED = "FAIL_CLOSED"

MATERIALIZE_ERROR_MISSING_SOURCE = "MISSING_SOURCE"
MATERIALIZE_ERROR_INVALID_JSON = "SAFETY_AUTHORITY_PRESENTATION_MATERIALIZER_INVALID_JSON"
MATERIALIZE_ERROR_INVALID_SOURCE = "SAFETY_AUTHORITY_PRESENTATION_MATERIALIZER_INVALID_SOURCE"
MATERIALIZE_ERROR_WRITE_FAILED = "SAFETY_AUTHORITY_PRESENTATION_MATERIALIZER_WRITE_FAILED"

_REQUIRED_FIELD_ATTRS = (
    "kill_switch_state",
    "veto_active",
)


@dataclass(frozen=True)
class SafetyAuthorityPresentationMaterializeResultV1:
    """Result of a fail-closed presentation projection materialize attempt."""

    written: bool
    status: str
    errors: tuple[str, ...]
    projection_path: str | None = None
    source_path: str | None = None
    kill_switch_state: str | None = None
    veto_active: bool | None = None
    payload_digest: str | None = None


def _empty_result(
    *,
    status: str,
    errors: tuple[str, ...],
    source_path: str | None = None,
) -> SafetyAuthorityPresentationMaterializeResultV1:
    return SafetyAuthorityPresentationMaterializeResultV1(
        written=False,
        status=status,
        errors=errors,
        source_path=source_path,
    )


def _require_nonempty_str(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _enum_or_str(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    return value


def coerce_safety_authority_fields_mapping_v1(
    source: object | None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Copy already-selected Safety Authority fields without mutation.

    Accepts:
    - binder-compatible fields (kill_switch_state/veto_active[/reason_codes])
    - nested projection envelope {"safety_authority": {...}}
    - objects exposing SafetyAuthoritySnapshotV1-compatible attributes

    Never invents KillSwitch state, veto, timestamps, or productive defaults.
    """
    if source is None:
        return None, (MATERIALIZE_ERROR_MISSING_SOURCE,)

    raw: Mapping[str, Any]
    if isinstance(source, Mapping):
        raw = source
    else:
        extracted: dict[str, Any] = {}
        for key in (
            *_REQUIRED_FIELD_ATTRS,
            "reason_codes",
            "evidence_digest",
            "semantic_digest",
            "schema_version",
            "generated_at",
            "effective_at",
            "saved_at",
            "source_reference",
            "killswitch_owner_ref",
            "safety_authority",
        ):
            if hasattr(source, key):
                extracted[key] = getattr(source, key)
        raw = extracted

    # Nested projection envelope: {"safety_authority": {...}}.
    if "safety_authority" in raw and isinstance(raw.get("safety_authority"), Mapping):
        nested = raw["safety_authority"]
        top_state = raw.get("kill_switch_state")
        nested_state = nested.get("kill_switch_state")
        if (
            isinstance(top_state, str)
            and top_state.strip()
            and isinstance(nested_state, str)
            and nested_state.strip()
            and top_state.strip() != nested_state.strip()
        ):
            return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_FIELDS_INVALID)
        top_veto = raw.get("veto_active")
        nested_veto = nested.get("veto_active")
        if (
            isinstance(top_veto, bool)
            and isinstance(nested_veto, bool)
            and top_veto is not nested_veto
        ):
            return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_FIELDS_INVALID)
        if not all(key in raw for key in _REQUIRED_FIELD_ATTRS):
            raw = nested

    fields = deepcopy(dict(raw))

    for key in _REQUIRED_FIELD_ATTRS:
        value = fields.get(key)
        if isinstance(value, Enum):
            fields[key] = value.value

    missing = [key for key in _REQUIRED_FIELD_ATTRS if key not in fields]
    if missing:
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_FIELDS_INVALID)

    if _require_nonempty_str(_enum_or_str(fields.get("kill_switch_state"))) is None:
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_FIELDS_INVALID)
    fields["kill_switch_state"] = str(_enum_or_str(fields["kill_switch_state"])).strip()

    if not isinstance(fields.get("veto_active"), bool):
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_FIELDS_INVALID)

    return fields, ()


def build_safety_authority_presentation_projection_payload_v1(
    *,
    safety_authority: object,
    generated_at: str,
    effective_at: str | None = None,
    saved_at: str | None = None,
    source_reference: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Build the loader-compatible projection envelope from Safety fields."""
    fields_mapping, coerce_errors = coerce_safety_authority_fields_mapping_v1(safety_authority)
    if fields_mapping is None:
        return None, coerce_errors

    if _require_nonempty_str(generated_at) is None:
        return None, (LOAD_ERROR_TIMESTAMP_MISSING,)

    return project_safety_authority_presentation_projection_v1(
        safety_authority=fields_mapping,
        generated_at=generated_at,
        effective_at=effective_at,
        saved_at=saved_at,
        source_reference=source_reference,
    )


def serialize_safety_authority_presentation_projection_v1(
    payload: Mapping[str, Any],
) -> str:
    """Deterministic JSON serialization for the presentation projection artifact."""
    return json.dumps(dict(payload), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _atomic_write_text(*, destination: Path, body: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, destination)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def write_safety_authority_presentation_projection_v1(
    archive_root: str | Path,
    payload: Mapping[str, Any],
) -> SafetyAuthorityPresentationMaterializeResultV1:
    """Atomically persist an already-validated projection payload."""
    if payload.get("schema_name") != SCHEMA_NAME:
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(LOAD_ERROR_SCHEMA_MISMATCH,),
        )
    schema_version = payload.get("schema_version")
    if schema_version is not None and int(schema_version) != SCHEMA_VERSION:
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(LOAD_ERROR_SCHEMA_MISMATCH,),
        )
    if (
        payload.get("authority_effect") != AUTHORITY_EFFECT
        or payload.get("safety_authority_effect") != SAFETY_AUTHORITY_EFFECT
    ):
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(MATERIALIZE_ERROR_INVALID_SOURCE,),
        )

    root = Path(archive_root).expanduser().resolve()
    path = root / STORAGE_RELATIVE_PATH
    body = serialize_safety_authority_presentation_projection_v1(payload)
    try:
        _atomic_write_text(destination=path, body=body)
    except OSError:
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(MATERIALIZE_ERROR_WRITE_FAILED,),
        )

    safety = payload.get("safety_authority")
    kill_switch_state = None
    veto_active = None
    if isinstance(safety, Mapping):
        raw_state = safety.get("kill_switch_state")
        if isinstance(raw_state, str) and raw_state.strip():
            kill_switch_state = raw_state.strip()
        raw_veto = safety.get("veto_active")
        if isinstance(raw_veto, bool):
            veto_active = raw_veto

    return SafetyAuthorityPresentationMaterializeResultV1(
        written=True,
        status=STATUS_WRITTEN,
        errors=(),
        projection_path=str(path),
        kill_switch_state=kill_switch_state,
        veto_active=veto_active,
        payload_digest=hashlib.sha256(body.encode("utf-8")).hexdigest(),
    )


def materialize_safety_authority_presentation_projection_v1(
    archive_root: str | Path,
    *,
    safety_authority: object | None = None,
    generated_at: str | None = None,
    effective_at: str | None = None,
    saved_at: str | None = None,
    source_reference: str | None = None,
) -> SafetyAuthorityPresentationMaterializeResultV1:
    """Materialize the presentation projection from Safety binder-compatible fields.

    Missing source yields MISSING_SOURCE and does not write an artifact.
    Invalid source or missing required timestamps fail closed without writing.
    Caller-owned Safety inputs are never mutated.
    Never reads productive/live KillSwitch state files.
    """
    if safety_authority is None:
        return _empty_result(
            status=STATUS_MISSING_SOURCE,
            errors=(MATERIALIZE_ERROR_MISSING_SOURCE,),
        )

    if _require_nonempty_str(generated_at) is None:
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(LOAD_ERROR_TIMESTAMP_MISSING,),
        )

    # Snapshot caller-owned mapping to prove / preserve non-mutation.
    caller_snapshot = deepcopy(safety_authority) if isinstance(safety_authority, Mapping) else None

    payload, build_errors = build_safety_authority_presentation_projection_payload_v1(
        safety_authority=safety_authority,
        generated_at=generated_at,
        effective_at=effective_at,
        saved_at=saved_at,
        source_reference=source_reference,
    )
    if isinstance(safety_authority, Mapping) and caller_snapshot is not None:
        if dict(safety_authority) != dict(caller_snapshot):
            return _empty_result(
                status=STATUS_FAIL_CLOSED,
                errors=(MATERIALIZE_ERROR_INVALID_SOURCE,),
            )
    if payload is None:
        status = (
            STATUS_MISSING_SOURCE
            if MATERIALIZE_ERROR_MISSING_SOURCE in build_errors
            else STATUS_FAIL_CLOSED
        )
        return _empty_result(status=status, errors=build_errors)

    # Re-validate via binder map to ensure invalid payloads are never persisted.
    nested = payload.get("safety_authority")
    if not isinstance(nested, Mapping):
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_FIELDS_INVALID),
        )
    mapped, map_errors = map_safety_authority_fields_to_binder_fields_v1(
        safety_authority=nested,
        generated_at=str(payload.get("generated_at") or ""),
        effective_at=(
            None if payload.get("effective_at") is None else str(payload.get("effective_at"))
        ),
        saved_at=(None if payload.get("saved_at") is None else str(payload.get("saved_at"))),
        source_reference=(
            None
            if payload.get("source_reference") is None
            else str(payload.get("source_reference"))
        ),
    )
    if mapped is None:
        return _empty_result(status=STATUS_FAIL_CLOSED, errors=map_errors)

    result = write_safety_authority_presentation_projection_v1(archive_root, payload)
    if not result.written:
        return result
    return SafetyAuthorityPresentationMaterializeResultV1(
        written=True,
        status=STATUS_WRITTEN,
        errors=(),
        projection_path=result.projection_path,
        kill_switch_state=result.kill_switch_state,
        veto_active=result.veto_active,
        payload_digest=result.payload_digest,
    )
