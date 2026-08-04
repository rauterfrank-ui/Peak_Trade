"""Non-authoritative materializer for Dynamic Scope presentation projection.

CAPABILITY_ID=CAPABILITY_PRESENTATION_DYNAMIC_SCOPE_PROJECTION_MATERIALIZER_AUTOBIND_V1

Consumes already-produced durable Dynamic Scope state
(``dynamic_scope_state_v1.json``) or binder-compatible lifecycle identity fields
under the Workflow Dashboard archive root and writes the non-authoritative
presentation projection schema to the loader-owned path. This module:

- AUTHORITY_EFFECT=NONE
- DYNAMIC_SCOPE_AUTHORITY_EFFECT=NONE
- never creates, mutates, or evaluates Dynamic Scope state
- never imports trading.master_v2 scope initializers or transition owners
- never imports ops.dynamic_scope_persistence_binding_v1 writers or mutation APIs
- never invents scope facts, timestamps, or default productive values
- never derives next_scope_ref when absent from source
- fail-closed: missing source → MISSING_SOURCE and no artifact write;
  invalid source → FAIL_CLOSED and no artifact write
- projection remains non-authoritative and must never flow back into runtime
  or authority chains

Deterministic serialization and atomic replace only. This projection path does
not own a separate MANIFEST contract; integrity follows the existing loader
schema/authority/scope checks.
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

from .dynamic_scope_presentation_projection_v1 import (
    AUTHORITY_EFFECT,
    DYNAMIC_SCOPE_AUTHORITY_EFFECT,
    LOAD_ERROR_SCHEMA_MISMATCH,
    LOAD_ERROR_SCOPE_INVALID,
    LOAD_ERROR_TIMESTAMP_MISSING,
    PROJECTION_ROLE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STORAGE_RELATIVE_PATH,
    map_dynamic_scope_fields_to_binder_fields_v1,
)

CAPABILITY_ID = "CAPABILITY_PRESENTATION_DYNAMIC_SCOPE_PROJECTION_MATERIALIZER_AUTOBIND_V1"
OWNER_MODULE = (
    "webui.workflow_dashboard_readmodel_v1.dynamic_scope_presentation_projection_materializer_v1"
)
SOURCE_STATE_RELATIVE_PATH = "readmodels/dynamic_scope_state_v1.json"
PRODUCER_STATE_SCHEMA_VERSION = "dynamic_scope_persistence_binding.v1"
PRODUCER_STATE_VERSION = "v1"

STATUS_WRITTEN = "WRITTEN"
STATUS_MISSING_SOURCE = "MISSING_SOURCE"
STATUS_FAIL_CLOSED = "FAIL_CLOSED"

MATERIALIZE_ERROR_MISSING_SOURCE = "MISSING_SOURCE"
MATERIALIZE_ERROR_INVALID_JSON = "DYNAMIC_SCOPE_PRESENTATION_MATERIALIZER_INVALID_JSON"
MATERIALIZE_ERROR_INVALID_SOURCE = "DYNAMIC_SCOPE_PRESENTATION_MATERIALIZER_INVALID_SOURCE"
MATERIALIZE_ERROR_WRITE_FAILED = "DYNAMIC_SCOPE_PRESENTATION_MATERIALIZER_WRITE_FAILED"

_REQUIRED_SCOPE_ATTRS = (
    "scope_state",
    "current_scope_ref",
)


@dataclass(frozen=True)
class DynamicScopePresentationMaterializeResultV1:
    """Result of a fail-closed presentation projection materialize attempt."""

    written: bool
    status: str
    errors: tuple[str, ...]
    projection_path: str | None = None
    source_path: str | None = None
    current_scope_ref: str | None = None
    payload_digest: str | None = None


def _empty_result(
    *,
    status: str,
    errors: tuple[str, ...],
    source_path: str | None = None,
) -> DynamicScopePresentationMaterializeResultV1:
    return DynamicScopePresentationMaterializeResultV1(
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


def coerce_dynamic_scope_state_mapping_v1(
    source: object | None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Copy persisted Dynamic Scope fields without mutating the caller-owned source.

    Accepts:
    - binder-compatible fields (scope_state/current_scope_ref or aliases)
    - durable CanonicalDynamicScopeStateV1 JSON (existing_scope nested)
    - nested projection envelope {"dynamic_scope": {...}}

    Never invents next_scope_ref, timestamps, or productive defaults.
    """
    if source is None:
        return None, (MATERIALIZE_ERROR_MISSING_SOURCE,)

    raw: Mapping[str, Any]
    if isinstance(source, Mapping):
        raw = source
    else:
        extracted: dict[str, Any] = {}
        for key in (
            *_REQUIRED_SCOPE_ATTRS,
            "lifecycle_state",
            "scope_id",
            "next_scope_ref",
            "reason_codes",
            "semantic_digest",
            "evidence_digest",
            "existing_scope",
            "schema_version",
            "state_version",
            "generated_at",
            "effective_at",
            "source_reference",
        ):
            if hasattr(source, key):
                extracted[key] = getattr(source, key)
        raw = extracted

    # Nested projection envelope: {"dynamic_scope": {...}}.
    if "dynamic_scope" in raw and isinstance(raw.get("dynamic_scope"), Mapping):
        nested = raw["dynamic_scope"]
        top_ref = raw.get("current_scope_ref")
        nested_ref = nested.get("current_scope_ref")
        if (
            isinstance(top_ref, str)
            and top_ref.strip()
            and isinstance(nested_ref, str)
            and nested_ref.strip()
            and top_ref.strip() != nested_ref.strip()
        ):
            return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_SCOPE_INVALID)
        if not all(key in raw for key in _REQUIRED_SCOPE_ATTRS):
            raw = nested

    scope = deepcopy(dict(raw))

    # Durable CanonicalDynamicScopeStateV1 shape → extract existing_scope fields only.
    existing = scope.get("existing_scope")
    looks_like_durable_state = (
        isinstance(existing, Mapping)
        or scope.get("schema_version") == PRODUCER_STATE_SCHEMA_VERSION
        or scope.get("state_version") == PRODUCER_STATE_VERSION
        or "scope_session_id" in scope
    )
    if looks_like_durable_state:
        schema_version = scope.get("schema_version")
        if schema_version is not None and schema_version != PRODUCER_STATE_SCHEMA_VERSION:
            return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_SCHEMA_MISMATCH)
        state_version = scope.get("state_version")
        if state_version is not None and state_version != PRODUCER_STATE_VERSION:
            return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_SCHEMA_MISMATCH)
        if not isinstance(existing, Mapping):
            return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_SCOPE_INVALID)
        mapped: dict[str, Any] = {}
        lifecycle = _enum_or_str(existing.get("lifecycle_state"))
        scope_id = existing.get("scope_id")
        if _require_nonempty_str(lifecycle) is None or _require_nonempty_str(scope_id) is None:
            return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_SCOPE_INVALID)
        mapped["scope_state"] = str(lifecycle).strip()
        mapped["current_scope_ref"] = str(scope_id).strip()
        # next_scope_ref is not part of durable CanonicalDynamicScopeStateV1 —
        # only pass through when explicitly present on the durable payload.
        if "next_scope_ref" in scope:
            mapped["next_scope_ref"] = scope.get("next_scope_ref")
        if "reason_codes" in existing:
            mapped["reason_codes"] = existing.get("reason_codes")
        digest = existing.get("semantic_digest")
        if digest is None:
            digest = existing.get("evidence_digest")
        if digest is not None:
            mapped["semantic_digest"] = digest
            mapped["evidence_digest"] = digest
        scope = mapped

    # Binder alias normalization (exact field copy; no semantic reinterpretation).
    if "scope_state" not in scope and "lifecycle_state" in scope:
        scope["scope_state"] = _enum_or_str(scope.get("lifecycle_state"))
    if "current_scope_ref" not in scope and "scope_id" in scope:
        scope["current_scope_ref"] = scope.get("scope_id")

    for key in ("scope_state", "current_scope_ref"):
        value = scope.get(key)
        if isinstance(value, Enum):
            scope[key] = value.value

    missing = [key for key in _REQUIRED_SCOPE_ATTRS if key not in scope]
    if missing:
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_SCOPE_INVALID)

    if _require_nonempty_str(scope.get("scope_state")) is None:
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_SCOPE_INVALID)
    if _require_nonempty_str(scope.get("current_scope_ref")) is None:
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_SCOPE_INVALID)
    scope["scope_state"] = str(scope["scope_state"]).strip()
    scope["current_scope_ref"] = str(scope["current_scope_ref"]).strip()

    if "next_scope_ref" in scope:
        raw_next = scope.get("next_scope_ref")
        if raw_next is None:
            scope["next_scope_ref"] = None
        elif isinstance(raw_next, Enum):
            scope["next_scope_ref"] = str(raw_next.value).strip() or None
        elif isinstance(raw_next, str):
            stripped = raw_next.strip()
            scope["next_scope_ref"] = stripped if stripped else None
        else:
            return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_SCOPE_INVALID)

    return scope, ()


def build_dynamic_scope_presentation_projection_payload_v1(
    *,
    dynamic_scope: object,
    generated_at: str,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Build the loader-compatible projection envelope from Dynamic Scope fields."""
    scope_mapping, coerce_errors = coerce_dynamic_scope_state_mapping_v1(dynamic_scope)
    if scope_mapping is None:
        return None, coerce_errors

    if _require_nonempty_str(generated_at) is None:
        return None, (LOAD_ERROR_TIMESTAMP_MISSING,)

    binder_fields, map_errors = map_dynamic_scope_fields_to_binder_fields_v1(
        dynamic_scope=scope_mapping,
        generated_at=generated_at,
        effective_at=effective_at,
        source_reference=source_reference,
    )
    if binder_fields is None:
        return None, map_errors

    scope_out: dict[str, Any] = {
        "current_scope_ref": binder_fields["current_scope_ref"],
        "reason_codes": list(binder_fields.get("reason_codes", ())),
        "scope_state": binder_fields["scope_state"],
    }
    if "next_scope_ref" in binder_fields:
        scope_out["next_scope_ref"] = binder_fields["next_scope_ref"]
    if "semantic_digest" in binder_fields:
        scope_out["semantic_digest"] = binder_fields["semantic_digest"]
        scope_out["evidence_digest"] = binder_fields["semantic_digest"]

    payload: dict[str, Any] = {
        "authority_effect": AUTHORITY_EFFECT,
        "dynamic_scope": scope_out,
        "dynamic_scope_authority_effect": DYNAMIC_SCOPE_AUTHORITY_EFFECT,
        "generated_at": binder_fields["generated_at"],
        "projection_role": PROJECTION_ROLE,
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
    }
    if "effective_at" in binder_fields:
        payload["effective_at"] = binder_fields["effective_at"]
    if "source_reference" in binder_fields:
        payload["source_reference"] = binder_fields["source_reference"]
    return payload, ()


def serialize_dynamic_scope_presentation_projection_v1(
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


def write_dynamic_scope_presentation_projection_v1(
    archive_root: str | Path,
    payload: Mapping[str, Any],
) -> DynamicScopePresentationMaterializeResultV1:
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
        or payload.get("dynamic_scope_authority_effect") != DYNAMIC_SCOPE_AUTHORITY_EFFECT
    ):
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(MATERIALIZE_ERROR_INVALID_SOURCE,),
        )

    root = Path(archive_root).expanduser().resolve()
    path = root / STORAGE_RELATIVE_PATH
    body = serialize_dynamic_scope_presentation_projection_v1(payload)
    try:
        _atomic_write_text(destination=path, body=body)
    except OSError:
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(MATERIALIZE_ERROR_WRITE_FAILED,),
        )

    scope = payload.get("dynamic_scope")
    current_scope_ref = None
    if isinstance(scope, Mapping):
        raw_ref = scope.get("current_scope_ref")
        if isinstance(raw_ref, str) and raw_ref.strip():
            current_scope_ref = raw_ref.strip()

    return DynamicScopePresentationMaterializeResultV1(
        written=True,
        status=STATUS_WRITTEN,
        errors=(),
        projection_path=str(path),
        current_scope_ref=current_scope_ref,
        payload_digest=hashlib.sha256(body.encode("utf-8")).hexdigest(),
    )


def try_load_dynamic_scope_state_source_v1(
    archive_root: str | Path,
) -> tuple[dict[str, Any] | None, tuple[str, ...], str | None]:
    """Load the sole durable Dynamic Scope state sibling without inventing content."""
    root = Path(archive_root).expanduser().resolve()
    path = root / SOURCE_STATE_RELATIVE_PATH
    source_path = str(path)
    if not path.is_file():
        return None, (MATERIALIZE_ERROR_MISSING_SOURCE,), source_path
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None, (MATERIALIZE_ERROR_INVALID_JSON,), source_path
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None, (MATERIALIZE_ERROR_INVALID_JSON,), source_path
    if not isinstance(payload, dict):
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE,), source_path
    scope, errors = coerce_dynamic_scope_state_mapping_v1(payload)
    if scope is None:
        return None, errors, source_path
    return scope, (), source_path


def materialize_dynamic_scope_presentation_projection_v1(
    archive_root: str | Path,
    *,
    dynamic_scope: object | None = None,
    generated_at: str | None = None,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> DynamicScopePresentationMaterializeResultV1:
    """Materialize the presentation projection from Dynamic Scope fields or durable source.

    Missing source yields MISSING_SOURCE and does not write an artifact.
    Invalid source or missing required timestamps fail closed without writing.
    Caller-owned Dynamic Scope inputs are never mutated.
    """
    source_path: str | None = None
    source_obj: object | None = dynamic_scope
    if source_obj is None:
        loaded, load_errors, source_path = try_load_dynamic_scope_state_source_v1(archive_root)
        if loaded is None:
            status = (
                STATUS_MISSING_SOURCE
                if MATERIALIZE_ERROR_MISSING_SOURCE in load_errors
                else STATUS_FAIL_CLOSED
            )
            return _empty_result(status=status, errors=load_errors, source_path=source_path)
        source_obj = loaded

    if _require_nonempty_str(generated_at) is None:
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(LOAD_ERROR_TIMESTAMP_MISSING,),
            source_path=source_path,
        )

    # Snapshot caller-owned mapping to prove / preserve non-mutation.
    caller_snapshot = deepcopy(dynamic_scope) if isinstance(dynamic_scope, Mapping) else None

    payload, build_errors = build_dynamic_scope_presentation_projection_payload_v1(
        dynamic_scope=source_obj,
        generated_at=generated_at,
        effective_at=effective_at,
        source_reference=source_reference,
    )
    if isinstance(dynamic_scope, Mapping) and caller_snapshot is not None:
        if dict(dynamic_scope) != dict(caller_snapshot):
            return _empty_result(
                status=STATUS_FAIL_CLOSED,
                errors=(MATERIALIZE_ERROR_INVALID_SOURCE,),
                source_path=source_path,
            )
    if payload is None:
        status = (
            STATUS_MISSING_SOURCE
            if MATERIALIZE_ERROR_MISSING_SOURCE in build_errors
            else STATUS_FAIL_CLOSED
        )
        return _empty_result(status=status, errors=build_errors, source_path=source_path)

    result = write_dynamic_scope_presentation_projection_v1(archive_root, payload)
    if not result.written:
        return result
    return DynamicScopePresentationMaterializeResultV1(
        written=True,
        status=STATUS_WRITTEN,
        errors=(),
        projection_path=result.projection_path,
        source_path=source_path,
        current_scope_ref=result.current_scope_ref,
        payload_digest=result.payload_digest,
    )
