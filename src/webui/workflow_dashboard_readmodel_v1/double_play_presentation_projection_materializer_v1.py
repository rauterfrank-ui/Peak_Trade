"""Non-authoritative materializer for Double Play presentation projection.

CAPABILITY_ID=CAPABILITY_PRESENTATION_DOUBLE_PLAY_PROJECTION_MATERIALIZER_V1

Consumes already-produced DoublePlayDashboardDisplaySnapshot-compatible field
payloads (or the durable sibling producer dump under the Workflow Dashboard
archive root) and writes the existing non-authoritative presentation projection
schema to the loader-owned path. This module:

- AUTHORITY_EFFECT=NONE
- DOUBLE_PLAY_AUTHORITY_EFFECT=NONE
- never creates, mutates, or evaluates Double Play decisions
- never imports trading.master_v2 Double Play composers or display builders
- never calls compose_double_play_decision / build_dashboard_display_snapshot /
  transition_state / KillSwitch / risk / sizing
- never invents display facts, timestamps, or default field values beyond the
  already-ratified projection mapping
- never treats double_play_dashboard_display_json_route_v0 as a source
  (explicitly NON_SOURCE / not landscape truth)
- fail-closed: missing source → MISSING_SOURCE and no artifact write;
  invalid source → FAIL_CLOSED and no artifact write
- projection remains non-authoritative and must never flow back into runtime
  or authority chains

Deterministic serialization and atomic replace only. This projection path does
not own a separate MANIFEST contract; integrity follows the existing loader
schema/authority/display checks.
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

from .double_play_presentation_projection_v1 import (
    AUTHORITY_EFFECT,
    DOUBLE_PLAY_AUTHORITY_EFFECT,
    LOAD_ERROR_DISPLAY_INVALID,
    LOAD_ERROR_SCHEMA_MISMATCH,
    LOAD_ERROR_TIMESTAMP_MISSING,
    PROJECTION_ROLE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STORAGE_RELATIVE_PATH,
    map_double_play_display_to_binder_fields_v1,
)

CAPABILITY_ID = "CAPABILITY_PRESENTATION_DOUBLE_PLAY_PROJECTION_MATERIALIZER_V1"
OWNER_MODULE = (
    "webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_materializer_v1"
)
SOURCE_DISPLAY_RELATIVE_PATH = "readmodels/double_play_dashboard_display.v1.json"
LEGACY_ROUTE_NON_SOURCE = "double_play_dashboard_display_json_route_v0"

STATUS_WRITTEN = "WRITTEN"
STATUS_MISSING_SOURCE = "MISSING_SOURCE"
STATUS_FAIL_CLOSED = "FAIL_CLOSED"

MATERIALIZE_ERROR_MISSING_SOURCE = "MISSING_SOURCE"
MATERIALIZE_ERROR_INVALID_JSON = "DOUBLE_PLAY_PRESENTATION_MATERIALIZER_INVALID_JSON"
MATERIALIZE_ERROR_INVALID_SOURCE = "DOUBLE_PLAY_PRESENTATION_MATERIALIZER_INVALID_SOURCE"
MATERIALIZE_ERROR_WRITE_FAILED = "DOUBLE_PLAY_PRESENTATION_MATERIALIZER_WRITE_FAILED"

_REQUIRED_DISPLAY_ATTRS = (
    "overall_status",
    "panel_summaries",
)
_PANEL_SUMMARY_KEYS = (
    "name",
    "status",
    "summary",
    "blockers",
)


@dataclass(frozen=True)
class DoublePlayPresentationMaterializeResultV1:
    """Result of a fail-closed presentation projection materialize attempt."""

    written: bool
    status: str
    errors: tuple[str, ...]
    projection_path: str | None = None
    source_path: str | None = None
    overall_status: str | None = None
    payload_digest: str | None = None


def _empty_result(
    *,
    status: str,
    errors: tuple[str, ...],
    source_path: str | None = None,
) -> DoublePlayPresentationMaterializeResultV1:
    return DoublePlayPresentationMaterializeResultV1(
        written=False,
        status=status,
        errors=errors,
        source_path=source_path,
    )


def _require_nonempty_str(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _panel_row_from_source(panel: object) -> dict[str, Any] | None:
    """Copy only already-present panel summary fields; no invented keys."""
    raw: Mapping[str, Any]
    if isinstance(panel, Mapping):
        raw = panel
    else:
        extracted: dict[str, Any] = {}
        for key in _PANEL_SUMMARY_KEYS:
            if hasattr(panel, key):
                extracted[key] = getattr(panel, key)
        raw = extracted

    name = raw.get("name")
    status = raw.get("status")
    if isinstance(name, Enum):
        name = name.value
    if isinstance(status, Enum):
        status = status.value
    if _require_nonempty_str(name) is None or _require_nonempty_str(status) is None:
        return None

    row: dict[str, Any] = {
        "name": str(name).strip(),
        "status": str(status).strip(),
    }
    if "summary" in raw:
        summary = raw.get("summary")
        if isinstance(summary, Enum):
            summary = summary.value
        if not isinstance(summary, str):
            return None
        row["summary"] = summary
    if "blockers" in raw:
        blockers = raw.get("blockers")
        if blockers is None:
            row["blockers"] = ()
        elif isinstance(blockers, (list, tuple)):
            row["blockers"] = tuple(str(code) for code in blockers)
        else:
            return None
    return row


def _panel_summaries_from_panels(
    panels: object,
) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    if isinstance(panels, Mapping):
        return (), (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_DISPLAY_INVALID)
    try:
        rows = []
        for panel in panels or ():
            row = _panel_row_from_source(panel)
            if row is None:
                return (), (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_DISPLAY_INVALID)
            rows.append(row)
        return tuple(rows), ()
    except TypeError:
        return (), (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_DISPLAY_INVALID)


def coerce_double_play_display_mapping_v1(
    source: object,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Copy display fields without mutating the caller-owned source."""
    if source is None:
        return None, (MATERIALIZE_ERROR_MISSING_SOURCE,)

    raw: Mapping[str, Any]
    if isinstance(source, Mapping):
        raw = source
    else:
        extracted: dict[str, Any] = {}
        for key in (
            "overall_status",
            "panel_summaries",
            "panels",
            "blockers",
            "display_only",
            "live_authorization",
            "evidence_digest",
        ):
            if hasattr(source, key):
                extracted[key] = getattr(source, key)
        raw = extracted

    # Nested projection/display envelope: {"display": {...}} without conflicting
    # top-level overall_status.
    if "display" in raw and isinstance(raw.get("display"), Mapping):
        nested = raw["display"]
        top_status = raw.get("overall_status")
        nested_status = nested.get("overall_status")
        if (
            isinstance(top_status, str)
            and top_status.strip()
            and isinstance(nested_status, str)
            and nested_status.strip()
            and top_status.strip() != nested_status.strip()
        ):
            return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_DISPLAY_INVALID)
        if not all(key in raw for key in _REQUIRED_DISPLAY_ATTRS):
            raw = nested

    display = deepcopy(dict(raw))

    # Snapshot-shaped sources expose panels; landscape/projection schema uses
    # panel_summaries. Field-copy only — never invent panel content.
    if "panel_summaries" not in display and "panels" in display:
        summaries, panel_errors = _panel_summaries_from_panels(display.get("panels"))
        if panel_errors:
            return None, panel_errors
        display["panel_summaries"] = summaries
        display.pop("panels", None)
    elif "panel_summaries" in display and "panels" in display:
        # Ambiguous dual panel carriers — fail closed.
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_DISPLAY_INVALID)

    missing = [key for key in _REQUIRED_DISPLAY_ATTRS if key not in display]
    if missing:
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_DISPLAY_INVALID)

    overall_status = display.get("overall_status")
    if isinstance(overall_status, Enum):
        overall_status = overall_status.value
    if _require_nonempty_str(overall_status) is None:
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_DISPLAY_INVALID)
    display["overall_status"] = str(overall_status).strip()

    raw_panels = display.get("panel_summaries")
    if isinstance(raw_panels, Mapping):
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_DISPLAY_INVALID)
    try:
        panel_summaries = []
        for panel in raw_panels or ():
            row = _panel_row_from_source(panel)
            if row is None:
                return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_DISPLAY_INVALID)
            panel_summaries.append(row)
        display["panel_summaries"] = tuple(panel_summaries)
    except TypeError:
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_DISPLAY_INVALID)

    return display, ()


def build_double_play_presentation_projection_payload_v1(
    *,
    display: object,
    generated_at: str,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Build the loader-compatible projection envelope from display fields."""
    display_mapping, coerce_errors = coerce_double_play_display_mapping_v1(display)
    if display_mapping is None:
        return None, coerce_errors

    if _require_nonempty_str(generated_at) is None:
        return None, (LOAD_ERROR_TIMESTAMP_MISSING,)

    binder_fields, map_errors = map_double_play_display_to_binder_fields_v1(
        display=display_mapping,
        generated_at=generated_at,
        effective_at=effective_at,
        source_reference=source_reference,
    )
    if binder_fields is None:
        return None, map_errors

    display_out: dict[str, Any] = {
        "blockers": list(binder_fields.get("blockers", ())),
        "display_only": True,
        "live_authorization": False,
        "overall_status": binder_fields["overall_status"],
        "panel_summaries": [dict(row) for row in binder_fields["panel_summaries"]],
    }
    if "evidence_digest" in binder_fields:
        display_out["evidence_digest"] = binder_fields["evidence_digest"]

    payload: dict[str, Any] = {
        "authority_effect": AUTHORITY_EFFECT,
        "display": display_out,
        "double_play_authority_effect": DOUBLE_PLAY_AUTHORITY_EFFECT,
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


def serialize_double_play_presentation_projection_v1(
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


def write_double_play_presentation_projection_v1(
    archive_root: str | Path,
    payload: Mapping[str, Any],
) -> DoublePlayPresentationMaterializeResultV1:
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
        or payload.get("double_play_authority_effect") != DOUBLE_PLAY_AUTHORITY_EFFECT
    ):
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(MATERIALIZE_ERROR_INVALID_SOURCE,),
        )

    root = Path(archive_root).expanduser().resolve()
    path = root / STORAGE_RELATIVE_PATH
    body = serialize_double_play_presentation_projection_v1(payload)
    try:
        _atomic_write_text(destination=path, body=body)
    except OSError:
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(MATERIALIZE_ERROR_WRITE_FAILED,),
        )

    display = payload.get("display")
    overall_status = None
    if isinstance(display, Mapping):
        raw_status = display.get("overall_status")
        if isinstance(raw_status, str) and raw_status.strip():
            overall_status = raw_status.strip()

    return DoublePlayPresentationMaterializeResultV1(
        written=True,
        status=STATUS_WRITTEN,
        errors=(),
        projection_path=str(path),
        overall_status=overall_status,
        payload_digest=hashlib.sha256(body.encode("utf-8")).hexdigest(),
    )


def try_load_double_play_display_source_v1(
    archive_root: str | Path,
) -> tuple[dict[str, Any] | None, tuple[str, ...], str | None]:
    """Load the sole durable producer display sibling without inventing content."""
    root = Path(archive_root).expanduser().resolve()
    path = root / SOURCE_DISPLAY_RELATIVE_PATH
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
    display, errors = coerce_double_play_display_mapping_v1(payload)
    if display is None:
        return None, errors, source_path
    return display, (), source_path


def materialize_double_play_presentation_projection_v1(
    archive_root: str | Path,
    *,
    display: object | None = None,
    generated_at: str | None = None,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> DoublePlayPresentationMaterializeResultV1:
    """Materialize the presentation projection from display fields or durable source.

    Missing source yields MISSING_SOURCE and does not write an artifact.
    Invalid source or missing required timestamps fail closed without writing.
    Caller-owned display inputs are never mutated.
    Legacy route double_play_dashboard_display_json_route_v0 is NON_SOURCE.
    """
    _ = LEGACY_ROUTE_NON_SOURCE  # documented non-source; never used as input path

    source_path: str | None = None
    source_obj: object | None = display
    if source_obj is None:
        loaded, load_errors, source_path = try_load_double_play_display_source_v1(archive_root)
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
    caller_snapshot = deepcopy(display) if isinstance(display, Mapping) else None

    payload, build_errors = build_double_play_presentation_projection_payload_v1(
        display=source_obj,
        generated_at=generated_at,
        effective_at=effective_at,
        source_reference=source_reference,
    )
    if isinstance(display, Mapping) and caller_snapshot is not None:
        if dict(display) != dict(caller_snapshot):
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

    result = write_double_play_presentation_projection_v1(archive_root, payload)
    if not result.written:
        return result
    return DoublePlayPresentationMaterializeResultV1(
        written=True,
        status=STATUS_WRITTEN,
        errors=(),
        projection_path=result.projection_path,
        source_path=source_path,
        overall_status=result.overall_status,
        payload_digest=result.payload_digest,
    )
