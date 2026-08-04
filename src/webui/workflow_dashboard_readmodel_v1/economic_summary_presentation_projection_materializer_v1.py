"""Non-authoritative materializer for Economic Summary presentation projection.

CAPABILITY_ID=CAPABILITY_PRESENTATION_ECONOMIC_SUMMARY_PROJECTION_MATERIALIZER_AUTOBIND_V1

Consumes already-produced EconomicViabilityEvidenceV1-compatible binder field
payloads (or the durable sibling dump under the Workflow Dashboard archive root)
and writes the non-authoritative presentation projection schema to the
loader-owned path. This module:

- AUTHORITY_EFFECT=NONE
- ECONOMIC_AUTHORITY_EFFECT=NONE
- never recomputes metrics, thresholds, or viability status
- never imports src.backtest.economic_viability_evidence_v1 evaluators
- never binds promotion_economic_gate_v1
- never invents status, metrics, digests, or timestamps
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

from .economic_summary_presentation_projection_v1 import (
    AUTHORITY_EFFECT,
    ECONOMIC_AUTHORITY_EFFECT,
    LOAD_ERROR_FIELDS_INVALID,
    LOAD_ERROR_SCHEMA_MISMATCH,
    LOAD_ERROR_TIMESTAMP_MISSING,
    PROJECTION_ROLE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOURCE_FIELDS_RELATIVE_PATH,
    STORAGE_RELATIVE_PATH,
    map_economic_summary_fields_to_binder_fields_v1,
)

CAPABILITY_ID = "CAPABILITY_PRESENTATION_ECONOMIC_SUMMARY_PROJECTION_MATERIALIZER_AUTOBIND_V1"
OWNER_MODULE = (
    "webui.workflow_dashboard_readmodel_v1.economic_summary_presentation_projection_materializer_v1"
)

STATUS_WRITTEN = "WRITTEN"
STATUS_MISSING_SOURCE = "MISSING_SOURCE"
STATUS_FAIL_CLOSED = "FAIL_CLOSED"

MATERIALIZE_ERROR_MISSING_SOURCE = "MISSING_SOURCE"
MATERIALIZE_ERROR_INVALID_JSON = "ECONOMIC_SUMMARY_PRESENTATION_MATERIALIZER_INVALID_JSON"
MATERIALIZE_ERROR_INVALID_SOURCE = "ECONOMIC_SUMMARY_PRESENTATION_MATERIALIZER_INVALID_SOURCE"
MATERIALIZE_ERROR_WRITE_FAILED = "ECONOMIC_SUMMARY_PRESENTATION_MATERIALIZER_WRITE_FAILED"

_REQUIRED_FIELD_ATTRS = (
    "status",
    "economic_validity_proven",
    "profitability_claim_allowed",
    "policy_threshold_status",
    "policy_version",
    "authority_effect",
    "runtime_effect",
    "order_effect",
    "profit_factor",
    "net_return",
    "max_drawdown",
    "sharpe",
    "trade_count",
    "funding_drag",
    "contract_version",
    "owner",
    "strategy_id",
    "strategy_version",
    "config_digest",
    "implementation_digest",
    "data_digest",
    "manifest_digest",
    "wiring_chain_digest",
    "policy_digest",
)


@dataclass(frozen=True)
class EconomicSummaryPresentationMaterializeResultV1:
    """Result of a fail-closed presentation projection materialize attempt."""

    written: bool
    status: str
    errors: tuple[str, ...]
    projection_path: str | None = None
    source_path: str | None = None
    economic_status: str | None = None
    payload_digest: str | None = None


def _empty_result(
    *,
    status: str,
    errors: tuple[str, ...],
    source_path: str | None = None,
) -> EconomicSummaryPresentationMaterializeResultV1:
    return EconomicSummaryPresentationMaterializeResultV1(
        written=False,
        status=status,
        errors=errors,
        source_path=source_path,
    )


def _require_nonempty_str(value: object) -> str | None:
    if isinstance(value, Enum):
        value = value.value
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _enum_or_str(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    return value


def coerce_economic_summary_fields_mapping_v1(
    source: object | None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Copy already-selected Economic binder fields without mutation.

    Accepts:
    - binder-compatible fields (status/metrics/digests/...)
    - nested projection envelope {"economic_summary": {...}}
    - objects exposing the binder field attributes

    Never invents metrics, statuses, timestamps, or productive defaults.
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
            "evidence_ref",
            "schema_version",
            "generated_at",
            "effective_at",
            "source_reference",
            "producer_module",
            "source_kind",
            "economic_summary",
        ):
            if hasattr(source, key):
                extracted[key] = getattr(source, key)
        raw = extracted

    if "economic_summary" in raw and isinstance(raw.get("economic_summary"), Mapping):
        nested = raw["economic_summary"]
        top_status = raw.get("status")
        nested_status = nested.get("status")
        if (
            isinstance(top_status, str)
            and top_status.strip()
            and isinstance(nested_status, str)
            and nested_status.strip()
            and top_status.strip() != nested_status.strip()
        ):
            return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_FIELDS_INVALID)
        if not all(key in raw for key in ("status", "manifest_digest", "profit_factor")):
            raw = nested

    fields = deepcopy(dict(raw))

    if "status" in fields:
        fields["status"] = _enum_or_str(fields["status"])

    missing = [key for key in _REQUIRED_FIELD_ATTRS if key not in fields]
    if missing:
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_FIELDS_INVALID)

    if _require_nonempty_str(fields.get("status")) is None:
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_FIELDS_INVALID)
    fields["status"] = str(_enum_or_str(fields["status"])).strip()

    return fields, ()


def build_economic_summary_presentation_projection_payload_v1(
    *,
    economic_summary: object,
    generated_at: str,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Build the loader-compatible projection envelope from Economic fields."""
    fields_mapping, coerce_errors = coerce_economic_summary_fields_mapping_v1(economic_summary)
    if fields_mapping is None:
        return None, coerce_errors

    if _require_nonempty_str(generated_at) is None:
        return None, (LOAD_ERROR_TIMESTAMP_MISSING,)

    binder_fields, map_errors = map_economic_summary_fields_to_binder_fields_v1(
        economic_summary=fields_mapping,
        generated_at=generated_at,
        effective_at=effective_at,
        source_reference=source_reference,
    )
    if binder_fields is None:
        return None, map_errors

    economic_out: dict[str, Any] = {
        "authority_effect": binder_fields["authority_effect"],
        "config_digest": binder_fields["config_digest"],
        "contract_version": binder_fields["contract_version"],
        "data_digest": binder_fields["data_digest"],
        "economic_validity_proven": binder_fields["economic_validity_proven"],
        "funding_drag": dict(binder_fields["funding_drag"]),
        "implementation_digest": binder_fields["implementation_digest"],
        "manifest_digest": binder_fields["manifest_digest"],
        "max_drawdown": dict(binder_fields["max_drawdown"]),
        "net_return": dict(binder_fields["net_return"]),
        "order_effect": binder_fields["order_effect"],
        "owner": binder_fields["owner"],
        "policy_digest": binder_fields["policy_digest"],
        "policy_threshold_status": binder_fields["policy_threshold_status"],
        "policy_version": binder_fields["policy_version"],
        "profit_factor": dict(binder_fields["profit_factor"]),
        "profitability_claim_allowed": binder_fields["profitability_claim_allowed"],
        "reason_codes": list(binder_fields.get("reason_codes", ())),
        "runtime_effect": binder_fields["runtime_effect"],
        "sharpe": dict(binder_fields["sharpe"]),
        "status": binder_fields["status"],
        "strategy_id": binder_fields["strategy_id"],
        "strategy_version": binder_fields["strategy_version"],
        "trade_count": dict(binder_fields["trade_count"]),
        "wiring_chain_digest": binder_fields["wiring_chain_digest"],
    }
    if "evidence_digest" in binder_fields:
        economic_out["evidence_digest"] = binder_fields["evidence_digest"]
    if "evidence_ref" in binder_fields:
        economic_out["evidence_ref"] = binder_fields["evidence_ref"]
    if "schema_version" in binder_fields:
        economic_out["schema_version"] = binder_fields["schema_version"]
    if "producer_module" in binder_fields:
        economic_out["producer_module"] = binder_fields["producer_module"]
    if "source_kind" in binder_fields:
        economic_out["source_kind"] = binder_fields["source_kind"]

    payload: dict[str, Any] = {
        "authority_effect": AUTHORITY_EFFECT,
        "economic_authority_effect": ECONOMIC_AUTHORITY_EFFECT,
        "economic_summary": economic_out,
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


def serialize_economic_summary_presentation_projection_v1(
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


def write_economic_summary_presentation_projection_v1(
    archive_root: str | Path,
    payload: Mapping[str, Any],
) -> EconomicSummaryPresentationMaterializeResultV1:
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
        or payload.get("economic_authority_effect") != ECONOMIC_AUTHORITY_EFFECT
    ):
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(MATERIALIZE_ERROR_INVALID_SOURCE,),
        )

    root = Path(archive_root).expanduser().resolve()
    path = root / STORAGE_RELATIVE_PATH
    body = serialize_economic_summary_presentation_projection_v1(payload)
    try:
        _atomic_write_text(destination=path, body=body)
    except OSError:
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(MATERIALIZE_ERROR_WRITE_FAILED,),
        )

    economic = payload.get("economic_summary")
    economic_status = None
    if isinstance(economic, Mapping):
        raw_status = economic.get("status")
        if isinstance(raw_status, str) and raw_status.strip():
            economic_status = raw_status.strip()

    return EconomicSummaryPresentationMaterializeResultV1(
        written=True,
        status=STATUS_WRITTEN,
        errors=(),
        projection_path=str(path),
        economic_status=economic_status,
        payload_digest=hashlib.sha256(body.encode("utf-8")).hexdigest(),
    )


def try_load_economic_summary_fields_source_v1(
    archive_root: str | Path,
) -> tuple[dict[str, Any] | None, tuple[str, ...], str | None]:
    """Load the sole durable Economic fields sibling without inventing content."""
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
    fields, errors = coerce_economic_summary_fields_mapping_v1(payload)
    if fields is None:
        return None, errors, source_path
    return fields, (), source_path


def materialize_economic_summary_presentation_projection_v1(
    archive_root: str | Path,
    *,
    economic_summary: object | None = None,
    generated_at: str | None = None,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> EconomicSummaryPresentationMaterializeResultV1:
    """Materialize the presentation projection from Economic fields or durable source.

    Missing source yields MISSING_SOURCE and does not write an artifact.
    Invalid source or missing required timestamps fail closed without writing.
    Caller-owned Economic inputs are never mutated.
    """
    source_path: str | None = None
    source_obj: object | None = economic_summary
    if source_obj is None:
        loaded, load_errors, source_path = try_load_economic_summary_fields_source_v1(archive_root)
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

    caller_snapshot = deepcopy(economic_summary) if isinstance(economic_summary, Mapping) else None

    payload, build_errors = build_economic_summary_presentation_projection_payload_v1(
        economic_summary=source_obj,
        generated_at=generated_at,
        effective_at=effective_at,
        source_reference=source_reference,
    )
    if isinstance(economic_summary, Mapping) and caller_snapshot is not None:
        if dict(economic_summary) != dict(caller_snapshot):
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

    result = write_economic_summary_presentation_projection_v1(archive_root, payload)
    if not result.written:
        return result
    return EconomicSummaryPresentationMaterializeResultV1(
        written=True,
        status=STATUS_WRITTEN,
        errors=(),
        projection_path=result.projection_path,
        source_path=source_path,
        economic_status=result.economic_status,
        payload_digest=result.payload_digest,
    )
