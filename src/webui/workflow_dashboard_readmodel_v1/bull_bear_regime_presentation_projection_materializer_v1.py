"""Non-authoritative materializer for Bull/Bear Regime presentation projection.

CAPABILITY_ID=CAPABILITY_PRESENTATION_BULL_BEAR_REGIME_PROJECTION_MATERIALIZER_V1

Consumes already-produced regime_bull_bear_switch field payloads (PR #5577
Landscape binder contract / durable sibling dump under the Workflow Dashboard
archive root) and writes the non-authoritative presentation projection schema
to the loader-owned path. This module:

- AUTHORITY_EFFECT=NONE
- BULL_BEAR_AUTHORITY_EFFECT=NONE
- never creates, mutates, or evaluates SideState / regime / switch decisions
- never imports trading.master_v2 producers or evaluators
- never calls transition_state / compose_double_play_decision /
  build_dashboard_display_snapshot / KillSwitch / risk / sizing
- never invents regime facts, timestamps, or default field values beyond the
  already-ratified projection mapping
- never treats double_play_dashboard_display_json_route_v0 as a source
  (explicitly NON_SOURCE / not landscape bull-bear truth)
- fail-closed: missing source → MISSING_SOURCE and no artifact write;
  invalid source → FAIL_CLOSED and no artifact write
- projection remains non-authoritative and must never flow back into runtime
  or authority chains

Deterministic serialization and atomic replace only. This projection path does
not own a separate MANIFEST contract; integrity follows the existing loader
schema/authority/regime checks.
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

from .bull_bear_regime_presentation_projection_v1 import (
    AUTHORITY_EFFECT,
    BULL_BEAR_AUTHORITY_EFFECT,
    LOAD_ERROR_REGIME_INVALID,
    LOAD_ERROR_SCHEMA_MISMATCH,
    LOAD_ERROR_TIMESTAMP_MISSING,
    PROJECTION_ROLE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STORAGE_RELATIVE_PATH,
    map_regime_bull_bear_switch_to_binder_fields_v1,
)

CAPABILITY_ID = "CAPABILITY_PRESENTATION_BULL_BEAR_REGIME_PROJECTION_MATERIALIZER_V1"
OWNER_MODULE = (
    "webui.workflow_dashboard_readmodel_v1.bull_bear_regime_presentation_projection_materializer_v1"
)
SOURCE_REGIME_RELATIVE_PATH = "readmodels/regime_bull_bear_switch.v1.json"
LEGACY_ROUTE_NON_SOURCE = "double_play_dashboard_display_json_route_v0"

STATUS_WRITTEN = "WRITTEN"
STATUS_MISSING_SOURCE = "MISSING_SOURCE"
STATUS_FAIL_CLOSED = "FAIL_CLOSED"
STATUS_NOT_BOUND = "NOT_BOUND"

MATERIALIZE_ERROR_MISSING_SOURCE = "MISSING_SOURCE"
MATERIALIZE_ERROR_NOT_BOUND = "NOT_BOUND"
MATERIALIZE_ERROR_INVALID_JSON = "BULL_BEAR_REGIME_PRESENTATION_MATERIALIZER_INVALID_JSON"
MATERIALIZE_ERROR_INVALID_SOURCE = "BULL_BEAR_REGIME_PRESENTATION_MATERIALIZER_INVALID_SOURCE"
MATERIALIZE_ERROR_WRITE_FAILED = "BULL_BEAR_REGIME_PRESENTATION_MATERIALIZER_WRITE_FAILED"

_REQUIRED_REGIME_ATTRS = (
    "regime_id",
    "regime_status",
    "side_state",
    "previous_side_state",
    "next_side_state",
    "scope_event_type",
    "transition_allowed",
    "transition_reason_code",
)


@dataclass(frozen=True)
class BullBearRegimePresentationMaterializeResultV1:
    """Result of a fail-closed presentation projection materialize attempt."""

    written: bool
    status: str
    errors: tuple[str, ...]
    projection_path: str | None = None
    source_path: str | None = None
    side_state: str | None = None
    payload_digest: str | None = None


def _empty_result(
    *,
    status: str,
    errors: tuple[str, ...],
    source_path: str | None = None,
) -> BullBearRegimePresentationMaterializeResultV1:
    return BullBearRegimePresentationMaterializeResultV1(
        written=False,
        status=status,
        errors=errors,
        source_path=source_path,
    )


def _require_nonempty_str(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def coerce_regime_bull_bear_switch_mapping_v1(
    source: object | None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Normalize caller or durable source into binder-compatible regime fields."""
    if source is None:
        return None, (MATERIALIZE_ERROR_MISSING_SOURCE,)

    raw: Mapping[str, Any]
    if isinstance(source, Mapping):
        raw = source
    else:
        extracted: dict[str, Any] = {}
        for key in (
            *_REQUIRED_REGIME_ATTRS,
            "reason_codes",
            "evidence_digest",
            "semantic_digest",
            "generated_at",
            "effective_at",
            "source_reference",
            "schema_version",
            "producer_module",
            "source_kind",
        ):
            if hasattr(source, key):
                extracted[key] = getattr(source, key)
        raw = extracted

    # Nested projection/regime envelope: {"regime_bull_bear_switch": {...}}.
    if "regime_bull_bear_switch" in raw and isinstance(raw.get("regime_bull_bear_switch"), Mapping):
        nested = raw["regime_bull_bear_switch"]
        top_side = raw.get("side_state")
        nested_side = nested.get("side_state")
        if (
            isinstance(top_side, str)
            and top_side.strip()
            and isinstance(nested_side, str)
            and nested_side.strip()
            and top_side.strip() != nested_side.strip()
        ):
            return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_REGIME_INVALID)
        if not all(key in raw for key in _REQUIRED_REGIME_ATTRS):
            raw = nested

    regime = deepcopy(dict(raw))

    # Enum-valued SideState / status carriers → exact string values only.
    for key in (
        "regime_id",
        "regime_status",
        "side_state",
        "previous_side_state",
        "next_side_state",
        "scope_event_type",
        "transition_reason_code",
    ):
        value = regime.get(key)
        if isinstance(value, Enum):
            regime[key] = value.value

    missing = [key for key in _REQUIRED_REGIME_ATTRS if key not in regime]
    if missing:
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_REGIME_INVALID)

    for key in (
        "regime_id",
        "regime_status",
        "side_state",
        "previous_side_state",
        "next_side_state",
        "scope_event_type",
        "transition_reason_code",
    ):
        if _require_nonempty_str(regime.get(key)) is None:
            return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_REGIME_INVALID)
        regime[key] = str(regime[key]).strip()

    if not isinstance(regime.get("transition_allowed"), bool):
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_REGIME_INVALID)

    return regime, ()


def build_bull_bear_regime_presentation_projection_payload_v1(
    *,
    regime_bull_bear_switch: object,
    generated_at: str,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Build the loader-compatible projection envelope from regime fields."""
    regime_mapping, coerce_errors = coerce_regime_bull_bear_switch_mapping_v1(
        regime_bull_bear_switch
    )
    if regime_mapping is None:
        return None, coerce_errors

    if _require_nonempty_str(generated_at) is None:
        return None, (LOAD_ERROR_TIMESTAMP_MISSING,)

    binder_fields, map_errors = map_regime_bull_bear_switch_to_binder_fields_v1(
        regime_bull_bear_switch=regime_mapping,
        generated_at=generated_at,
        effective_at=effective_at,
        source_reference=source_reference,
    )
    if binder_fields is None:
        return None, map_errors

    regime_out: dict[str, Any] = {
        "next_side_state": binder_fields["next_side_state"],
        "previous_side_state": binder_fields["previous_side_state"],
        "regime_id": binder_fields["regime_id"],
        "regime_status": binder_fields["regime_status"],
        "reason_codes": list(binder_fields.get("reason_codes", ())),
        "scope_event_type": binder_fields["scope_event_type"],
        "side_state": binder_fields["side_state"],
        "transition_allowed": binder_fields["transition_allowed"],
        "transition_reason_code": binder_fields["transition_reason_code"],
    }
    if "evidence_digest" in binder_fields:
        regime_out["evidence_digest"] = binder_fields["evidence_digest"]
        regime_out["semantic_digest"] = binder_fields["evidence_digest"]

    payload: dict[str, Any] = {
        "authority_effect": AUTHORITY_EFFECT,
        "bull_bear_authority_effect": BULL_BEAR_AUTHORITY_EFFECT,
        "generated_at": binder_fields["generated_at"],
        "projection_role": PROJECTION_ROLE,
        "regime_bull_bear_switch": regime_out,
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
    }
    if "effective_at" in binder_fields:
        payload["effective_at"] = binder_fields["effective_at"]
    if "source_reference" in binder_fields:
        payload["source_reference"] = binder_fields["source_reference"]
    return payload, ()


def serialize_bull_bear_regime_presentation_projection_v1(
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


def write_bull_bear_regime_presentation_projection_v1(
    archive_root: str | Path,
    payload: Mapping[str, Any],
) -> BullBearRegimePresentationMaterializeResultV1:
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
        or payload.get("bull_bear_authority_effect") != BULL_BEAR_AUTHORITY_EFFECT
    ):
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(MATERIALIZE_ERROR_INVALID_SOURCE,),
        )

    root = Path(archive_root).expanduser().resolve()
    path = root / STORAGE_RELATIVE_PATH
    body = serialize_bull_bear_regime_presentation_projection_v1(payload)
    try:
        _atomic_write_text(destination=path, body=body)
    except OSError:
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(MATERIALIZE_ERROR_WRITE_FAILED,),
        )

    regime = payload.get("regime_bull_bear_switch")
    side_state = None
    if isinstance(regime, Mapping):
        raw_side = regime.get("side_state")
        if isinstance(raw_side, str) and raw_side.strip():
            side_state = raw_side.strip()

    return BullBearRegimePresentationMaterializeResultV1(
        written=True,
        status=STATUS_WRITTEN,
        errors=(),
        projection_path=str(path),
        side_state=side_state,
        payload_digest=hashlib.sha256(body.encode("utf-8")).hexdigest(),
    )


def try_load_regime_bull_bear_switch_source_v1(
    archive_root: str | Path,
) -> tuple[dict[str, Any] | None, tuple[str, ...], str | None]:
    """Load the sole durable producer regime sibling without inventing content."""
    root = Path(archive_root).expanduser().resolve()
    path = root / SOURCE_REGIME_RELATIVE_PATH
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
    regime, errors = coerce_regime_bull_bear_switch_mapping_v1(payload)
    if regime is None:
        return None, errors, source_path
    return regime, (), source_path


def materialize_bull_bear_regime_presentation_projection_v1(
    archive_root: str | Path,
    *,
    regime_bull_bear_switch: object | None = None,
    generated_at: str | None = None,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> BullBearRegimePresentationMaterializeResultV1:
    """Materialize the presentation projection from regime fields or durable source.

    Missing source yields MISSING_SOURCE and does not write an artifact.
    Invalid source or missing required timestamps fail closed without writing.
    Caller-owned regime inputs are never mutated.
    Legacy route double_play_dashboard_display_json_route_v0 is NON_SOURCE.
    """
    _ = LEGACY_ROUTE_NON_SOURCE  # documented non-source; never used as input path
    _ = STATUS_NOT_BOUND  # binding vocabulary retained for consumer fail-closed states
    _ = MATERIALIZE_ERROR_NOT_BOUND

    source_path: str | None = None
    source_obj: object | None = regime_bull_bear_switch
    if source_obj is None:
        loaded, load_errors, source_path = try_load_regime_bull_bear_switch_source_v1(archive_root)
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
    caller_snapshot = (
        deepcopy(regime_bull_bear_switch) if isinstance(regime_bull_bear_switch, Mapping) else None
    )

    payload, build_errors = build_bull_bear_regime_presentation_projection_payload_v1(
        regime_bull_bear_switch=source_obj,
        generated_at=generated_at,
        effective_at=effective_at,
        source_reference=source_reference,
    )
    if isinstance(regime_bull_bear_switch, Mapping) and caller_snapshot is not None:
        if dict(regime_bull_bear_switch) != dict(caller_snapshot):
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

    result = write_bull_bear_regime_presentation_projection_v1(archive_root, payload)
    if not result.written:
        return result
    return BullBearRegimePresentationMaterializeResultV1(
        written=True,
        status=STATUS_WRITTEN,
        errors=(),
        projection_path=result.projection_path,
        source_path=source_path,
        side_state=result.side_state,
        payload_digest=result.payload_digest,
    )
