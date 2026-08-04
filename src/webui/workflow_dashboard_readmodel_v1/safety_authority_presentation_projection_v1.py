"""Non-authoritative presentation projection for Safety Authority.

CAPABILITY_ID=CAPABILITY_PRESENTATION_SAFETY_AUTHORITY_PROJECTION_MATERIALIZER_AUTOBIND_V1

Reads already-produced Safety binder-compatible fields from a single durable
archive path and maps them field-for-field into Landscape binder injection
fields. This module:

- AUTHORITY_EFFECT=NONE
- SAFETY_AUTHORITY_EFFECT=NONE
- never creates, mutates, triggers, recovers, or evaluates KillSwitch
- never imports src.risk_layer.kill_switch
- never imports trading.master_v2.killswitch_boundary_* adapters
- never auto-loads productive/live KillSwitch state files
- never invents kill_switch_state, veto_active, reason_codes, or timestamps
- fail-closed: missing, invalid, or ambiguous sources → no fields (MISSING_SOURCE)

Deterministic source selection: exactly one well-known relative path under the
Workflow Dashboard archive root. No silent multi-candidate "latest" picking.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

SCHEMA_NAME = "safety_authority_presentation_projection.v1"
SCHEMA_VERSION = 1
STORAGE_RELATIVE_PATH = "readmodels/safety_authority.v1.json"
AUTHORITY_EFFECT = "NONE"
SAFETY_AUTHORITY_EFFECT = "NONE"
PROJECTION_ROLE = "NON_AUTHORITATIVE_PRESENTATION_PROJECTION"
OWNER_MODULE = "webui.workflow_dashboard_readmodel_v1.safety_authority_presentation_projection_v1"

LOAD_ERROR_ABSENT = "SAFETY_AUTHORITY_PRESENTATION_PROJECTION_ABSENT"
LOAD_ERROR_INVALID_JSON = "SAFETY_AUTHORITY_PRESENTATION_PROJECTION_INVALID_JSON"
LOAD_ERROR_SCHEMA_MISMATCH = "SAFETY_AUTHORITY_PRESENTATION_PROJECTION_SCHEMA_MISMATCH"
LOAD_ERROR_AUTHORITY_CLAIM = "SAFETY_AUTHORITY_PRESENTATION_PROJECTION_AUTHORITY_CLAIM"
LOAD_ERROR_FIELDS_INVALID = "SAFETY_AUTHORITY_PRESENTATION_PROJECTION_FIELDS_INVALID"
LOAD_ERROR_AMBIGUOUS = "SAFETY_AUTHORITY_PRESENTATION_PROJECTION_AMBIGUOUS_SOURCE"
LOAD_ERROR_TIMESTAMP_MISSING = "SAFETY_AUTHORITY_PRESENTATION_PROJECTION_TIMESTAMP_MISSING"

_REQUIRED_FIELD_KEYS = (
    "kill_switch_state",
    "veto_active",
)


@dataclass(frozen=True)
class SafetyAuthorityPresentationLoadV1:
    """Result of a fail-closed presentation projection load attempt."""

    loaded: bool
    load_errors: tuple[str, ...]
    binder_fields: Mapping[str, Any] | None = None
    source_path: str | None = None
    evidence_digest: str | None = None
    kill_switch_state: str | None = None
    veto_active: bool | None = None


def _empty(*, load_errors: tuple[str, ...]) -> SafetyAuthorityPresentationLoadV1:
    return SafetyAuthorityPresentationLoadV1(loaded=False, load_errors=load_errors)


def _require_nonempty_str(payload: Mapping[str, Any], key: str) -> str | None:
    raw = payload.get(key)
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw.strip()


def _normalize_reason_codes(raw_codes: object) -> tuple[str, ...] | None:
    """Deterministic reason-code normalization without changing meaning."""
    if raw_codes is None:
        raw_codes = ()
    if not isinstance(raw_codes, (list, tuple)):
        return None
    return tuple(str(code) for code in raw_codes)


def _fields_payload_from_envelope(
    payload: Mapping[str, Any],
) -> tuple[Mapping[str, Any] | None, tuple[str, ...]]:
    """Extract nested safety_authority fields; fail closed on ambiguity."""
    if "safety_authority" not in payload:
        return None, (LOAD_ERROR_FIELDS_INVALID,)
    fields = payload.get("safety_authority")
    if not isinstance(fields, Mapping):
        return None, (LOAD_ERROR_FIELDS_INVALID,)
    # Reject dual top-level + nested kill_switch_state with conflicting values.
    top_level_state = payload.get("kill_switch_state")
    nested_state = fields.get("kill_switch_state")
    if (
        isinstance(top_level_state, str)
        and top_level_state.strip()
        and isinstance(nested_state, str)
        and nested_state.strip()
        and top_level_state.strip() != nested_state.strip()
    ):
        return None, (LOAD_ERROR_AMBIGUOUS,)
    top_veto = payload.get("veto_active")
    nested_veto = fields.get("veto_active")
    if isinstance(top_veto, bool) and isinstance(nested_veto, bool) and top_veto is not nested_veto:
        return None, (LOAD_ERROR_AMBIGUOUS,)
    return fields, ()


def _validate_safety_fields(
    fields: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    missing = [key for key in _REQUIRED_FIELD_KEYS if key not in fields]
    if missing:
        return None, (LOAD_ERROR_FIELDS_INVALID,)

    kill_switch_state = _require_nonempty_str(fields, "kill_switch_state")
    if kill_switch_state is None:
        return None, (LOAD_ERROR_FIELDS_INVALID,)

    veto_raw = fields.get("veto_active")
    if not isinstance(veto_raw, bool):
        return None, (LOAD_ERROR_FIELDS_INVALID,)

    out: dict[str, Any] = {
        "kill_switch_state": kill_switch_state,
        "veto_active": veto_raw,
    }

    reason_codes = _normalize_reason_codes(fields.get("reason_codes", ()))
    if reason_codes is None:
        return None, (LOAD_ERROR_FIELDS_INVALID,)
    out["reason_codes"] = reason_codes

    digest = fields.get("evidence_digest")
    if digest is None:
        digest = fields.get("semantic_digest")
    if digest is not None:
        if not isinstance(digest, str) or not digest.strip():
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out["evidence_digest"] = digest.strip()
        out["semantic_digest"] = digest.strip()

    source_reference = fields.get("source_reference")
    if source_reference is None:
        source_reference = fields.get("killswitch_owner_ref")
    if source_reference is not None:
        if not isinstance(source_reference, str):
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out["source_reference"] = source_reference
        out["killswitch_owner_ref"] = source_reference

    schema_version = fields.get("schema_version")
    if schema_version is not None:
        if not isinstance(schema_version, str) or not schema_version.strip():
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out["schema_version"] = schema_version.strip()

    return out, ()


def map_safety_authority_fields_to_binder_fields_v1(
    *,
    safety_authority: Mapping[str, Any],
    generated_at: str,
    effective_at: str | None = None,
    saved_at: str | None = None,
    source_reference: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Map Safety Authority fields → Landscape binder fields (projection only)."""
    mapped, errors = _validate_safety_fields(safety_authority)
    if mapped is None:
        return None, errors
    if not isinstance(generated_at, str) or not generated_at.strip():
        return None, (LOAD_ERROR_TIMESTAMP_MISSING,)
    mapped["generated_at"] = generated_at.strip()
    if effective_at is not None:
        if not isinstance(effective_at, str) or not effective_at.strip():
            return None, (LOAD_ERROR_TIMESTAMP_MISSING,)
        mapped["effective_at"] = effective_at.strip()
    if saved_at is not None:
        if not isinstance(saved_at, str) or not saved_at.strip():
            return None, (LOAD_ERROR_TIMESTAMP_MISSING,)
        mapped["saved_at"] = saved_at.strip()
        # Binder treats saved_at as effective_at alias when effective_at absent.
        if "effective_at" not in mapped:
            mapped["effective_at"] = saved_at.strip()
    if source_reference is not None:
        if not isinstance(source_reference, str):
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        mapped["source_reference"] = source_reference
        mapped["killswitch_owner_ref"] = source_reference
    return mapped, ()


def project_safety_authority_presentation_projection_v1(
    *,
    safety_authority: Mapping[str, Any],
    generated_at: str,
    effective_at: str | None = None,
    saved_at: str | None = None,
    source_reference: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Build the non-authoritative presentation projection envelope.

    Field-faithful projection of already binder-compatible Safety fields only.
    Never invents KillSwitch state, veto, timestamps, or productive defaults.
    """
    binder_fields, map_errors = map_safety_authority_fields_to_binder_fields_v1(
        safety_authority=safety_authority,
        generated_at=generated_at,
        effective_at=effective_at,
        saved_at=saved_at,
        source_reference=source_reference,
    )
    if binder_fields is None:
        return None, map_errors

    safety_out: dict[str, Any] = {
        "kill_switch_state": binder_fields["kill_switch_state"],
        "reason_codes": list(binder_fields.get("reason_codes", ())),
        "veto_active": binder_fields["veto_active"],
    }
    if "evidence_digest" in binder_fields:
        safety_out["evidence_digest"] = binder_fields["evidence_digest"]
        safety_out["semantic_digest"] = binder_fields["evidence_digest"]
    if "schema_version" in binder_fields:
        safety_out["schema_version"] = binder_fields["schema_version"]
    if "source_reference" in binder_fields and source_reference is None:
        # Preserve nested provenance when carried on fields payload.
        safety_out["source_reference"] = binder_fields["source_reference"]
        safety_out["killswitch_owner_ref"] = binder_fields["source_reference"]

    payload: dict[str, Any] = {
        "authority_effect": AUTHORITY_EFFECT,
        "generated_at": binder_fields["generated_at"],
        "projection_role": PROJECTION_ROLE,
        "safety_authority": safety_out,
        "safety_authority_effect": SAFETY_AUTHORITY_EFFECT,
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
    }
    if "effective_at" in binder_fields:
        payload["effective_at"] = binder_fields["effective_at"]
    if "saved_at" in binder_fields:
        payload["saved_at"] = binder_fields["saved_at"]
    if source_reference is not None:
        payload["source_reference"] = source_reference
    elif "source_reference" in binder_fields:
        payload["source_reference"] = binder_fields["source_reference"]
    return payload, ()


def try_load_safety_authority_presentation_projection_v1(
    archive_root: str | Path,
) -> SafetyAuthorityPresentationLoadV1:
    """Verify-before-trust read of the sole durable Safety presentation projection.

    Returns loaded=False with load_errors on any fail-closed condition. Never
    invents Safety/KillSwitch facts and never reads productive live state paths.
    """
    root = Path(archive_root).expanduser().resolve()
    path = root / STORAGE_RELATIVE_PATH
    if not path.is_file():
        return _empty(load_errors=(LOAD_ERROR_ABSENT,))

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
    safety_authority = payload.get("safety_authority_effect")
    if authority != AUTHORITY_EFFECT or safety_authority != SAFETY_AUTHORITY_EFFECT:
        return _empty(load_errors=(LOAD_ERROR_AUTHORITY_CLAIM,))

    generated_at = _require_nonempty_str(payload, "generated_at")
    if generated_at is None:
        return _empty(load_errors=(LOAD_ERROR_TIMESTAMP_MISSING,))

    effective_at = payload.get("effective_at")
    if effective_at is not None and (not isinstance(effective_at, str) or not effective_at.strip()):
        return _empty(load_errors=(LOAD_ERROR_TIMESTAMP_MISSING,))
    effective_at_s = None if effective_at is None else str(effective_at).strip()

    saved_at = payload.get("saved_at")
    if saved_at is not None and (not isinstance(saved_at, str) or not saved_at.strip()):
        return _empty(load_errors=(LOAD_ERROR_TIMESTAMP_MISSING,))
    saved_at_s = None if saved_at is None else str(saved_at).strip()

    fields, field_errors = _fields_payload_from_envelope(payload)
    if fields is None:
        return _empty(load_errors=field_errors)

    source_reference = payload.get("source_reference")
    if source_reference is None:
        source_reference = f"presentation://{STORAGE_RELATIVE_PATH}"
    elif not isinstance(source_reference, str):
        return _empty(load_errors=(LOAD_ERROR_FIELDS_INVALID,))

    binder_fields, map_errors = map_safety_authority_fields_to_binder_fields_v1(
        safety_authority=fields,
        generated_at=generated_at,
        effective_at=effective_at_s,
        saved_at=saved_at_s,
        source_reference=source_reference,
    )
    if binder_fields is None:
        return _empty(load_errors=map_errors)

    return SafetyAuthorityPresentationLoadV1(
        loaded=True,
        load_errors=(),
        binder_fields=binder_fields,
        source_path=str(path),
        evidence_digest=(
            None
            if binder_fields.get("evidence_digest") is None
            else str(binder_fields.get("evidence_digest"))
        ),
        kill_switch_state=str(binder_fields["kill_switch_state"]),
        veto_active=bool(binder_fields["veto_active"]),
    )
