"""Non-authoritative materializer for Risk/Sizing/Capital presentation projection.

CAPABILITY_ID=CAPABILITY_PRESENTATION_RISK_SIZING_CAPITAL_PROJECTION_MATERIALIZER_AUTOBIND_V1

Consumes already-produced Risk/Sizing/Capital binder-compatible field payloads
(or the durable sibling dump under the Workflow Dashboard archive root) and
writes the non-authoritative presentation projection schema to the loader-owned
path. This module:

- AUTHORITY_EFFECT=NONE
- RISK_SIZING_AUTHORITY_EFFECT=NONE
- never creates, mutates, or evaluates capital/risk/sizing decisions
- never imports src.governance.capital_risk_sizing_v1 evaluators
- never imports trading.master_v2 capital_risk_sizing offline adapters
- never invents quantity, status, timestamps, or reason_codes
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

from .risk_sizing_capital_presentation_projection_v1 import (
    AUTHORITY_EFFECT,
    LOAD_ERROR_FIELDS_INVALID,
    LOAD_ERROR_SCHEMA_MISMATCH,
    LOAD_ERROR_TIMESTAMP_MISSING,
    PROJECTION_ROLE,
    RISK_SIZING_AUTHORITY_EFFECT,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOURCE_FIELDS_RELATIVE_PATH,
    STORAGE_RELATIVE_PATH,
    map_risk_sizing_capital_fields_to_binder_fields_v1,
)

CAPABILITY_ID = "CAPABILITY_PRESENTATION_RISK_SIZING_CAPITAL_PROJECTION_MATERIALIZER_AUTOBIND_V1"
OWNER_MODULE = (
    "webui.workflow_dashboard_readmodel_v1."
    "risk_sizing_capital_presentation_projection_materializer_v1"
)

STATUS_WRITTEN = "WRITTEN"
STATUS_MISSING_SOURCE = "MISSING_SOURCE"
STATUS_FAIL_CLOSED = "FAIL_CLOSED"

MATERIALIZE_ERROR_MISSING_SOURCE = "MISSING_SOURCE"
MATERIALIZE_ERROR_INVALID_JSON = "RISK_SIZING_CAPITAL_PRESENTATION_MATERIALIZER_INVALID_JSON"
MATERIALIZE_ERROR_INVALID_SOURCE = "RISK_SIZING_CAPITAL_PRESENTATION_MATERIALIZER_INVALID_SOURCE"
MATERIALIZE_ERROR_WRITE_FAILED = "RISK_SIZING_CAPITAL_PRESENTATION_MATERIALIZER_WRITE_FAILED"

_REQUIRED_FIELD_ATTRS = (
    "risk_status",
    "sizing_status",
    "capital_status",
)


@dataclass(frozen=True)
class RiskSizingCapitalPresentationMaterializeResultV1:
    """Result of a fail-closed presentation projection materialize attempt."""

    written: bool
    status: str
    errors: tuple[str, ...]
    projection_path: str | None = None
    source_path: str | None = None
    risk_status: str | None = None
    payload_digest: str | None = None


def _empty_result(
    *,
    status: str,
    errors: tuple[str, ...],
    source_path: str | None = None,
) -> RiskSizingCapitalPresentationMaterializeResultV1:
    return RiskSizingCapitalPresentationMaterializeResultV1(
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


def coerce_risk_sizing_capital_fields_mapping_v1(
    source: object | None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Copy already-selected Risk/Sizing/Capital fields without mutation.

    Accepts:
    - binder-compatible fields (risk_status/sizing_status/capital_status)
    - nested projection envelope {"risk_sizing_capital": {...}}

    Never invents quantity, statuses, timestamps, or productive defaults.
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
            "quantity",
            "reason_codes",
            "evidence_digest",
            "risk_sizing_ref",
            "schema_version",
            "generated_at",
            "effective_at",
            "source_reference",
            "risk_sizing_capital",
        ):
            if hasattr(source, key):
                extracted[key] = getattr(source, key)
        raw = extracted

    # Nested projection envelope: {"risk_sizing_capital": {...}}.
    if "risk_sizing_capital" in raw and isinstance(raw.get("risk_sizing_capital"), Mapping):
        nested = raw["risk_sizing_capital"]
        top_status = raw.get("risk_status")
        nested_status = nested.get("risk_status")
        if (
            isinstance(top_status, str)
            and top_status.strip()
            and isinstance(nested_status, str)
            and nested_status.strip()
            and top_status.strip() != nested_status.strip()
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

    for key in _REQUIRED_FIELD_ATTRS:
        if _require_nonempty_str(_enum_or_str(fields.get(key))) is None:
            return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_FIELDS_INVALID)
        fields[key] = str(_enum_or_str(fields[key])).strip()

    return fields, ()


def build_risk_sizing_capital_presentation_projection_payload_v1(
    *,
    risk_sizing_capital: object,
    generated_at: str,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Build the loader-compatible projection envelope from Risk fields."""
    fields_mapping, coerce_errors = coerce_risk_sizing_capital_fields_mapping_v1(
        risk_sizing_capital
    )
    if fields_mapping is None:
        return None, coerce_errors

    if _require_nonempty_str(generated_at) is None:
        return None, (LOAD_ERROR_TIMESTAMP_MISSING,)

    binder_fields, map_errors = map_risk_sizing_capital_fields_to_binder_fields_v1(
        risk_sizing_capital=fields_mapping,
        generated_at=generated_at,
        effective_at=effective_at,
        source_reference=source_reference,
    )
    if binder_fields is None:
        return None, map_errors

    risk_out: dict[str, Any] = {
        "capital_status": binder_fields["capital_status"],
        "reason_codes": list(binder_fields.get("reason_codes", ())),
        "risk_status": binder_fields["risk_status"],
        "sizing_status": binder_fields["sizing_status"],
    }
    if "quantity" in binder_fields:
        risk_out["quantity"] = binder_fields["quantity"]
    if "evidence_digest" in binder_fields:
        risk_out["evidence_digest"] = binder_fields["evidence_digest"]
        risk_out["risk_sizing_ref"] = binder_fields["evidence_digest"]
    if "schema_version" in binder_fields:
        risk_out["schema_version"] = binder_fields["schema_version"]

    payload: dict[str, Any] = {
        "authority_effect": AUTHORITY_EFFECT,
        "generated_at": binder_fields["generated_at"],
        "projection_role": PROJECTION_ROLE,
        "risk_sizing_authority_effect": RISK_SIZING_AUTHORITY_EFFECT,
        "risk_sizing_capital": risk_out,
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
    }
    if "effective_at" in binder_fields:
        payload["effective_at"] = binder_fields["effective_at"]
    if "source_reference" in binder_fields:
        payload["source_reference"] = binder_fields["source_reference"]
    return payload, ()


def serialize_risk_sizing_capital_presentation_projection_v1(
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


def write_risk_sizing_capital_presentation_projection_v1(
    archive_root: str | Path,
    payload: Mapping[str, Any],
) -> RiskSizingCapitalPresentationMaterializeResultV1:
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
        or payload.get("risk_sizing_authority_effect") != RISK_SIZING_AUTHORITY_EFFECT
    ):
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(MATERIALIZE_ERROR_INVALID_SOURCE,),
        )

    root = Path(archive_root).expanduser().resolve()
    path = root / STORAGE_RELATIVE_PATH
    body = serialize_risk_sizing_capital_presentation_projection_v1(payload)
    try:
        _atomic_write_text(destination=path, body=body)
    except OSError:
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(MATERIALIZE_ERROR_WRITE_FAILED,),
        )

    risk = payload.get("risk_sizing_capital")
    risk_status = None
    if isinstance(risk, Mapping):
        raw_status = risk.get("risk_status")
        if isinstance(raw_status, str) and raw_status.strip():
            risk_status = raw_status.strip()

    return RiskSizingCapitalPresentationMaterializeResultV1(
        written=True,
        status=STATUS_WRITTEN,
        errors=(),
        projection_path=str(path),
        risk_status=risk_status,
        payload_digest=hashlib.sha256(body.encode("utf-8")).hexdigest(),
    )


def try_load_risk_sizing_capital_fields_source_v1(
    archive_root: str | Path,
) -> tuple[dict[str, Any] | None, tuple[str, ...], str | None]:
    """Load the sole durable Risk/Sizing/Capital fields sibling without inventing content."""
    root = Path(archive_root).expanduser().resolve()
    path = root / SOURCE_FIELDS_RELATIVE_PATH
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
    fields, errors = coerce_risk_sizing_capital_fields_mapping_v1(payload)
    if fields is None:
        return None, errors, source_path
    return fields, (), source_path


def materialize_risk_sizing_capital_presentation_projection_v1(
    archive_root: str | Path,
    *,
    risk_sizing_capital: object | None = None,
    generated_at: str | None = None,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> RiskSizingCapitalPresentationMaterializeResultV1:
    """Materialize the presentation projection from Risk fields or durable source.

    Missing source yields MISSING_SOURCE and does not write an artifact.
    Invalid source or missing required timestamps fail closed without writing.
    Caller-owned Risk inputs are never mutated.
    """
    source_path: str | None = None
    source_obj: object | None = risk_sizing_capital
    if source_obj is None:
        loaded, load_errors, source_path = try_load_risk_sizing_capital_fields_source_v1(
            archive_root
        )
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
        deepcopy(risk_sizing_capital) if isinstance(risk_sizing_capital, Mapping) else None
    )

    payload, build_errors = build_risk_sizing_capital_presentation_projection_payload_v1(
        risk_sizing_capital=source_obj,
        generated_at=generated_at,
        effective_at=effective_at,
        source_reference=source_reference,
    )
    if isinstance(risk_sizing_capital, Mapping) and caller_snapshot is not None:
        if dict(risk_sizing_capital) != dict(caller_snapshot):
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

    result = write_risk_sizing_capital_presentation_projection_v1(archive_root, payload)
    if not result.written:
        return result
    return RiskSizingCapitalPresentationMaterializeResultV1(
        written=True,
        status=STATUS_WRITTEN,
        errors=(),
        projection_path=result.projection_path,
        source_path=source_path,
        risk_status=result.risk_status,
        payload_digest=result.payload_digest,
    )
