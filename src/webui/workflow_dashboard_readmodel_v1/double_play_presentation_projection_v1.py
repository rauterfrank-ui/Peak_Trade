"""Non-authoritative presentation projection for Double Play display.

CAPABILITY_ID=CAPABILITY_PRESENTATION_DOUBLE_PLAY_AUTOBIND_V1

Reads already-produced DoublePlayDashboardDisplaySnapshot-compatible field
payloads from a single durable archive path and maps them field-for-field into
Landscape binder injection fields. This module:

- AUTHORITY_EFFECT=NONE
- DOUBLE_PLAY_AUTHORITY_EFFECT=NONE
- never creates, mutates, or evaluates Double Play decisions
- never imports trading.master_v2 Double Play composers or display builders
- never calls compose_double_play_decision / build_dashboard_display_snapshot /
  transition_state / KillSwitch / risk / sizing
- fail-closed: missing, invalid, or ambiguous sources → no fields (MISSING_SOURCE)

Deterministic source selection: exactly one well-known relative path under the
Workflow Dashboard archive root. No silent multi-candidate "latest" picking.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

SCHEMA_NAME = "double_play_presentation_projection.v1"
SCHEMA_VERSION = 1
STORAGE_RELATIVE_PATH = "readmodels/double_play_presentation_projection.v1.json"
AUTHORITY_EFFECT = "NONE"
DOUBLE_PLAY_AUTHORITY_EFFECT = "NONE"
PROJECTION_ROLE = "NON_AUTHORITATIVE_PRESENTATION_PROJECTION"
OWNER_MODULE = "webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_v1"

LOAD_ERROR_ABSENT = "DOUBLE_PLAY_PRESENTATION_PROJECTION_ABSENT"
LOAD_ERROR_INVALID_JSON = "DOUBLE_PLAY_PRESENTATION_PROJECTION_INVALID_JSON"
LOAD_ERROR_SCHEMA_MISMATCH = "DOUBLE_PLAY_PRESENTATION_PROJECTION_SCHEMA_MISMATCH"
LOAD_ERROR_AUTHORITY_CLAIM = "DOUBLE_PLAY_PRESENTATION_PROJECTION_AUTHORITY_CLAIM"
LOAD_ERROR_DISPLAY_INVALID = "DOUBLE_PLAY_PRESENTATION_PROJECTION_DISPLAY_INVALID"
LOAD_ERROR_AMBIGUOUS = "DOUBLE_PLAY_PRESENTATION_PROJECTION_AMBIGUOUS_SOURCE"
LOAD_ERROR_TIMESTAMP_MISSING = "DOUBLE_PLAY_PRESENTATION_PROJECTION_TIMESTAMP_MISSING"

_REQUIRED_DISPLAY_KEYS = (
    "overall_status",
    "panel_summaries",
)


@dataclass(frozen=True)
class DoublePlayPresentationLoadV1:
    """Result of a fail-closed presentation projection load attempt."""

    loaded: bool
    load_errors: tuple[str, ...]
    binder_fields: Mapping[str, Any] | None = None
    source_path: str | None = None
    evidence_digest: str | None = None
    overall_status: str | None = None


def _empty(*, load_errors: tuple[str, ...]) -> DoublePlayPresentationLoadV1:
    return DoublePlayPresentationLoadV1(loaded=False, load_errors=load_errors)


def _require_nonempty_str(payload: Mapping[str, Any], key: str) -> str | None:
    raw = payload.get(key)
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw.strip()


def _display_payload_from_envelope(
    payload: Mapping[str, Any],
) -> tuple[Mapping[str, Any] | None, tuple[str, ...]]:
    """Extract nested display snapshot fields; fail closed on ambiguity."""
    if "display" not in payload:
        return None, (LOAD_ERROR_DISPLAY_INVALID,)
    display = payload.get("display")
    if not isinstance(display, Mapping):
        return None, (LOAD_ERROR_DISPLAY_INVALID,)
    # Reject dual top-level + nested overall_status with conflicting values.
    top_level_status = payload.get("overall_status")
    nested_status = display.get("overall_status")
    if (
        isinstance(top_level_status, str)
        and top_level_status.strip()
        and isinstance(nested_status, str)
        and nested_status.strip()
        and top_level_status.strip() != nested_status.strip()
    ):
        return None, (LOAD_ERROR_AMBIGUOUS,)
    return display, ()


def _validate_display_fields(
    display: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    missing = [key for key in _REQUIRED_DISPLAY_KEYS if key not in display]
    if missing:
        return None, (LOAD_ERROR_DISPLAY_INVALID,)

    overall_status = _require_nonempty_str(display, "overall_status")
    if overall_status is None:
        return None, (LOAD_ERROR_DISPLAY_INVALID,)

    raw_panels = display.get("panel_summaries")
    if isinstance(raw_panels, Mapping):
        return None, (LOAD_ERROR_DISPLAY_INVALID,)
    try:
        panel_summaries = tuple(dict(row) for row in (raw_panels or ()))
    except (TypeError, ValueError):
        return None, (LOAD_ERROR_DISPLAY_INVALID,)

    out: dict[str, Any] = {
        "overall_status": overall_status,
        "panel_summaries": panel_summaries,
    }

    display_only = display.get("display_only", True)
    if display_only is not True:
        return None, (LOAD_ERROR_DISPLAY_INVALID,)
    out["display_only"] = True

    live_authorization = display.get("live_authorization", False)
    if live_authorization is not False:
        return None, (LOAD_ERROR_DISPLAY_INVALID,)
    out["live_authorization"] = False

    raw_blockers = display.get("blockers", ()) or ()
    if not isinstance(raw_blockers, (list, tuple)):
        return None, (LOAD_ERROR_DISPLAY_INVALID,)
    out["blockers"] = tuple(str(code) for code in raw_blockers)

    digest = display.get("evidence_digest")
    if digest is not None:
        if not isinstance(digest, str) or not digest.strip():
            return None, (LOAD_ERROR_DISPLAY_INVALID,)
        out["evidence_digest"] = digest.strip()

    return out, ()


def map_double_play_display_to_binder_fields_v1(
    *,
    display: Mapping[str, Any],
    generated_at: str,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Map display snapshot fields → Landscape binder fields (projection only)."""
    mapped, errors = _validate_display_fields(display)
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
            return None, (LOAD_ERROR_DISPLAY_INVALID,)
        mapped["source_reference"] = source_reference
    return mapped, ()


def try_load_double_play_presentation_projection_v1(
    archive_root: str | Path,
) -> DoublePlayPresentationLoadV1:
    """Verify-before-trust read of the sole durable Double Play presentation projection.

    Returns loaded=False with load_errors on any fail-closed condition. Never
    invents Double Play display facts.
    """
    root = Path(archive_root).expanduser().resolve()
    path = root / STORAGE_RELATIVE_PATH
    if not path.is_file():
        return _empty(load_errors=(LOAD_ERROR_ABSENT,))

    # Ambiguity guard: a second durable producer dump beside the projection is
    # allowed only when identical evidence_digest (when both present);
    # otherwise fail closed.
    sibling = root / "readmodels" / "double_play_dashboard_display.v1.json"
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
    double_play_authority = payload.get("double_play_authority_effect")
    if authority != AUTHORITY_EFFECT or double_play_authority != DOUBLE_PLAY_AUTHORITY_EFFECT:
        return _empty(load_errors=(LOAD_ERROR_AUTHORITY_CLAIM,))

    generated_at = _require_nonempty_str(payload, "generated_at")
    if generated_at is None:
        return _empty(load_errors=(LOAD_ERROR_TIMESTAMP_MISSING,))

    effective_at = payload.get("effective_at")
    if effective_at is not None and (not isinstance(effective_at, str) or not effective_at.strip()):
        return _empty(load_errors=(LOAD_ERROR_TIMESTAMP_MISSING,))
    effective_at_s = None if effective_at is None else str(effective_at).strip()

    display, display_errors = _display_payload_from_envelope(payload)
    if display is None:
        return _empty(load_errors=display_errors)

    source_reference = payload.get("source_reference")
    if source_reference is None:
        source_reference = f"presentation://{STORAGE_RELATIVE_PATH}"
    elif not isinstance(source_reference, str):
        return _empty(load_errors=(LOAD_ERROR_DISPLAY_INVALID,))

    binder_fields, map_errors = map_double_play_display_to_binder_fields_v1(
        display=display,
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
        sibling_digest = sibling_payload.get("evidence_digest")
        projection_digest = binder_fields.get("evidence_digest")
        if (
            not isinstance(sibling_digest, str)
            or not sibling_digest.strip()
            or not isinstance(projection_digest, str)
            or not projection_digest.strip()
            or sibling_digest.strip() != projection_digest.strip()
        ):
            return _empty(load_errors=(LOAD_ERROR_AMBIGUOUS,))

    return DoublePlayPresentationLoadV1(
        loaded=True,
        load_errors=(),
        binder_fields=binder_fields,
        source_path=str(path),
        evidence_digest=(
            None
            if binder_fields.get("evidence_digest") is None
            else str(binder_fields.get("evidence_digest"))
        ),
        overall_status=str(binder_fields["overall_status"]),
    )
