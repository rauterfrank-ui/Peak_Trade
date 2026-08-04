"""Non-authoritative presentation projection for Dynamic Scope lifecycle identity.

CAPABILITY_ID=CAPABILITY_PRESENTATION_DYNAMIC_SCOPE_PROJECTION_MATERIALIZER_AUTOBIND_V1

Reads already-produced Dynamic Scope lifecycle identity fields from a single
durable archive path and maps them field-for-field into Landscape binder
injection fields. This module:

- AUTHORITY_EFFECT=NONE
- DYNAMIC_SCOPE_AUTHORITY_EFFECT=NONE
- never creates, mutates, or evaluates Dynamic Scope state
- never imports trading.master_v2 scope initializers or transition owners
- never imports ops.dynamic_scope_persistence_binding_v1 writers
- never calls initialize/transition/persist Dynamic Scope APIs
- fail-closed: missing, invalid, or ambiguous sources → no fields (MISSING_SOURCE)

Deterministic source selection: exactly one well-known relative path under the
Workflow Dashboard archive root. No silent multi-candidate "latest" picking.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

SCHEMA_NAME = "dynamic_scope_presentation_projection.v1"
SCHEMA_VERSION = 1
STORAGE_RELATIVE_PATH = "readmodels/dynamic_scope_presentation_projection.v1.json"
AUTHORITY_EFFECT = "NONE"
DYNAMIC_SCOPE_AUTHORITY_EFFECT = "NONE"
PROJECTION_ROLE = "NON_AUTHORITATIVE_PRESENTATION_PROJECTION"
OWNER_MODULE = "webui.workflow_dashboard_readmodel_v1.dynamic_scope_presentation_projection_v1"

LOAD_ERROR_ABSENT = "DYNAMIC_SCOPE_PRESENTATION_PROJECTION_ABSENT"
LOAD_ERROR_INVALID_JSON = "DYNAMIC_SCOPE_PRESENTATION_PROJECTION_INVALID_JSON"
LOAD_ERROR_SCHEMA_MISMATCH = "DYNAMIC_SCOPE_PRESENTATION_PROJECTION_SCHEMA_MISMATCH"
LOAD_ERROR_AUTHORITY_CLAIM = "DYNAMIC_SCOPE_PRESENTATION_PROJECTION_AUTHORITY_CLAIM"
LOAD_ERROR_SCOPE_INVALID = "DYNAMIC_SCOPE_PRESENTATION_PROJECTION_SCOPE_INVALID"
LOAD_ERROR_AMBIGUOUS = "DYNAMIC_SCOPE_PRESENTATION_PROJECTION_AMBIGUOUS_SOURCE"
LOAD_ERROR_TIMESTAMP_MISSING = "DYNAMIC_SCOPE_PRESENTATION_PROJECTION_TIMESTAMP_MISSING"

# Exact Landscape binder contract — lifecycle identity only; no reinterpretation.
_REQUIRED_SCOPE_KEYS = (
    "scope_state",
    "current_scope_ref",
)

# Pass-through vocabulary from CanonicalScopeLifecycleState (no derivation).
KNOWN_SCOPE_STATES = frozenset(
    {
        "scope_uninitialized",
        "scope_warming_up",
        "scope_valid",
        "scope_stale",
        "scope_invalid",
    }
)


@dataclass(frozen=True)
class DynamicScopePresentationLoadV1:
    """Result of a fail-closed presentation projection load attempt."""

    loaded: bool
    load_errors: tuple[str, ...]
    binder_fields: Mapping[str, Any] | None = None
    source_path: str | None = None
    evidence_digest: str | None = None
    current_scope_ref: str | None = None


def _empty(*, load_errors: tuple[str, ...]) -> DynamicScopePresentationLoadV1:
    return DynamicScopePresentationLoadV1(loaded=False, load_errors=load_errors)


def _require_nonempty_str(payload: Mapping[str, Any], key: str) -> str | None:
    raw = payload.get(key)
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw.strip()


def _scope_payload_from_envelope(
    payload: Mapping[str, Any],
) -> tuple[Mapping[str, Any] | None, tuple[str, ...]]:
    """Extract nested dynamic_scope fields; fail closed on ambiguity."""
    if "dynamic_scope" not in payload:
        return None, (LOAD_ERROR_SCOPE_INVALID,)
    scope = payload.get("dynamic_scope")
    if not isinstance(scope, Mapping):
        return None, (LOAD_ERROR_SCOPE_INVALID,)
    # Reject dual top-level + nested current_scope_ref with conflicting values.
    top_level_ref = payload.get("current_scope_ref")
    nested_ref = scope.get("current_scope_ref")
    if (
        isinstance(top_level_ref, str)
        and top_level_ref.strip()
        and isinstance(nested_ref, str)
        and nested_ref.strip()
        and top_level_ref.strip() != nested_ref.strip()
    ):
        return None, (LOAD_ERROR_AMBIGUOUS,)
    return scope, ()


def _validate_scope_fields(
    scope: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    missing = [key for key in _REQUIRED_SCOPE_KEYS if key not in scope]
    if missing:
        return None, (LOAD_ERROR_SCOPE_INVALID,)

    scope_state = _require_nonempty_str(scope, "scope_state")
    current_scope_ref = _require_nonempty_str(scope, "current_scope_ref")
    if scope_state is None or current_scope_ref is None:
        return None, (LOAD_ERROR_SCOPE_INVALID,)
    if scope_state not in KNOWN_SCOPE_STATES:
        return None, (LOAD_ERROR_SCHEMA_MISMATCH,)

    out: dict[str, Any] = {
        "scope_state": scope_state,
        "current_scope_ref": current_scope_ref,
    }

    if "next_scope_ref" in scope:
        raw_next = scope.get("next_scope_ref")
        if raw_next is None:
            out["next_scope_ref"] = None
        elif isinstance(raw_next, str):
            stripped = raw_next.strip()
            out["next_scope_ref"] = stripped if stripped else None
        else:
            return None, (LOAD_ERROR_SCOPE_INVALID,)

    raw_codes = scope.get("reason_codes", ())
    if raw_codes is None:
        raw_codes = ()
    if not isinstance(raw_codes, (list, tuple)):
        return None, (LOAD_ERROR_SCOPE_INVALID,)
    out["reason_codes"] = tuple(str(code) for code in raw_codes)

    digest = scope.get("semantic_digest")
    if digest is None:
        digest = scope.get("evidence_digest")
    if digest is not None:
        if not isinstance(digest, str) or not digest.strip():
            return None, (LOAD_ERROR_SCOPE_INVALID,)
        out["semantic_digest"] = digest.strip()
        out["evidence_digest"] = digest.strip()

    return out, ()


def map_dynamic_scope_fields_to_binder_fields_v1(
    *,
    dynamic_scope: Mapping[str, Any],
    generated_at: str,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Map Dynamic Scope lifecycle fields → Landscape binder fields (projection only)."""
    mapped, errors = _validate_scope_fields(dynamic_scope)
    if mapped is None:
        return None, errors
    if not isinstance(generated_at, str) or not generated_at.strip():
        return None, (LOAD_ERROR_TIMESTAMP_MISSING,)
    mapped["generated_at"] = generated_at.strip()
    if effective_at is not None:
        if not isinstance(effective_at, str) or not effective_at.strip():
            return None, (LOAD_ERROR_TIMESTAMP_MISSING,)
        mapped["effective_at"] = effective_at.strip()
    if source_reference is not None:
        if not isinstance(source_reference, str):
            return None, (LOAD_ERROR_SCOPE_INVALID,)
        mapped["source_reference"] = source_reference
    return mapped, ()


def try_load_dynamic_scope_presentation_projection_v1(
    archive_root: str | Path,
) -> DynamicScopePresentationLoadV1:
    """Verify-before-trust read of the sole durable Dynamic Scope presentation projection.

    Returns loaded=False with load_errors on any fail-closed condition. Never
    invents Dynamic Scope lifecycle facts.
    """
    root = Path(archive_root).expanduser().resolve()
    path = root / STORAGE_RELATIVE_PATH
    if not path.is_file():
        return _empty(load_errors=(LOAD_ERROR_ABSENT,))

    # Ambiguity guard: a second durable producer dump beside the projection is
    # allowed only when identical current_scope_ref / scope_id; otherwise fail closed.
    sibling = root / "readmodels" / "dynamic_scope_state_v1.json"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return _empty(load_errors=(LOAD_ERROR_INVALID_JSON,))

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return _empty(load_errors=(LOAD_ERROR_INVALID_JSON,))

    if not isinstance(payload, dict):
        return _empty(load_errors=(LOAD_ERROR_INVALID_JSON,))

    schema_name = payload.get("schema_name")
    if schema_name != SCHEMA_NAME:
        return _empty(load_errors=(LOAD_ERROR_SCHEMA_MISMATCH,))

    schema_version = payload.get("schema_version")
    if schema_version is not None and int(schema_version) != SCHEMA_VERSION:
        return _empty(load_errors=(LOAD_ERROR_SCHEMA_MISMATCH,))

    authority = payload.get("authority_effect")
    scope_authority = payload.get("dynamic_scope_authority_effect")
    if authority != AUTHORITY_EFFECT or scope_authority != DYNAMIC_SCOPE_AUTHORITY_EFFECT:
        return _empty(load_errors=(LOAD_ERROR_AUTHORITY_CLAIM,))

    generated_at = _require_nonempty_str(payload, "generated_at")
    if generated_at is None:
        return _empty(load_errors=(LOAD_ERROR_TIMESTAMP_MISSING,))

    effective_at = payload.get("effective_at")
    if effective_at is not None and (not isinstance(effective_at, str) or not effective_at.strip()):
        return _empty(load_errors=(LOAD_ERROR_TIMESTAMP_MISSING,))
    effective_at_s = None if effective_at is None else str(effective_at).strip()

    scope, scope_errors = _scope_payload_from_envelope(payload)
    if scope is None:
        return _empty(load_errors=scope_errors)

    source_reference = payload.get("source_reference")
    if source_reference is None:
        source_reference = f"presentation://{STORAGE_RELATIVE_PATH}"
    elif not isinstance(source_reference, str):
        return _empty(load_errors=(LOAD_ERROR_SCOPE_INVALID,))

    binder_fields, map_errors = map_dynamic_scope_fields_to_binder_fields_v1(
        dynamic_scope=scope,
        generated_at=generated_at,
        effective_at=effective_at_s,
        source_reference=source_reference,
    )
    if binder_fields is None:
        return _empty(load_errors=map_errors)

    if sibling.is_file():
        try:
            sibling_payload = json.loads(sibling.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return _empty(load_errors=(LOAD_ERROR_AMBIGUOUS,))
        if not isinstance(sibling_payload, dict):
            return _empty(load_errors=(LOAD_ERROR_AMBIGUOUS,))
        sibling_ref = sibling_payload.get("current_scope_ref")
        if sibling_ref is None:
            sibling_ref = sibling_payload.get("scope_id")
        if sibling_ref is None:
            existing = sibling_payload.get("existing_scope")
            if isinstance(existing, Mapping):
                sibling_ref = existing.get("scope_id")
        if (
            not isinstance(sibling_ref, str)
            or not sibling_ref.strip()
            or sibling_ref.strip() != binder_fields["current_scope_ref"]
        ):
            return _empty(load_errors=(LOAD_ERROR_AMBIGUOUS,))

    return DynamicScopePresentationLoadV1(
        loaded=True,
        load_errors=(),
        binder_fields=binder_fields,
        source_path=str(path),
        evidence_digest=(
            None
            if binder_fields.get("semantic_digest") is None
            else str(binder_fields.get("semantic_digest"))
        ),
        current_scope_ref=str(binder_fields["current_scope_ref"]),
    )
