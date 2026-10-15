"""S01 — read-only evidence ingest."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.ghosv_bounded_context_v1.types_v1 import (
    GhosvCompleteness,
    GhosvEvidenceKind,
    GhosvEvidenceRecordV1,
)

INGEST_CONTRACT = "ghosv_s01_evidence_ingest_v1"


class GhosvEvidenceIngestError(ValueError):
    pass


@dataclass(frozen=True)
class GhosvIngestResultV1:
    records: tuple[GhosvEvidenceRecordV1, ...]
    rejected: tuple[str, ...]


def _text(value: object) -> str:
    return str(value or "").strip()


def _event_id(kind: str, source: str, stable: str) -> str:
    raw = f"{kind}|{source}|{stable}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def normalize_evidence_record_v1(raw: Mapping[str, Any]) -> GhosvEvidenceRecordV1:
    kind = _text(raw.get("kind")).upper()
    if kind not in {k.value for k in GhosvEvidenceKind}:
        raise GhosvEvidenceIngestError(f"UNKNOWN_EVIDENCE_KIND:{kind}")
    source_module = _text(raw.get("source_module"))
    source_contract = _text(raw.get("source_contract"))
    if not source_module or not source_contract:
        raise GhosvEvidenceIngestError("MISSING_SOURCE_PROVENANCE")
    trade_id = _text(raw.get("trade_id"))
    instrument_id = _text(raw.get("instrument_id"))
    client_order_id = _text(raw.get("client_order_id"))
    exchange_order_id = _text(raw.get("exchange_order_id"))
    fill_id = _text(raw.get("fill_id"))
    observation_timestamp = _text(raw.get("observation_timestamp"))
    source_timestamp = _text(raw.get("source_timestamp"))
    correlation_context = _text(raw.get("correlation_context"))
    completeness = _text(raw.get("completeness") or GhosvCompleteness.UNKNOWN.value)
    if completeness not in {c.value for c in GhosvCompleteness}:
        completeness = GhosvCompleteness.UNKNOWN.value
    payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
    payload_ref = _text(raw.get("payload_ref"))
    stable = payload_ref or json.dumps(
        {
            "trade_id": trade_id,
            "client_order_id": client_order_id,
            "exchange_order_id": exchange_order_id,
            "fill_id": fill_id,
            "source_timestamp": source_timestamp,
            "kind": kind,
        },
        sort_keys=True,
    )
    event_id = _text(raw.get("event_id")) or _event_id(kind, source_module, stable)
    return GhosvEvidenceRecordV1(
        event_id=event_id,
        kind=kind,
        source_module=source_module,
        source_contract=source_contract,
        trade_id=trade_id,
        instrument_id=instrument_id,
        client_order_id=client_order_id,
        exchange_order_id=exchange_order_id,
        fill_id=fill_id,
        observation_timestamp=observation_timestamp,
        source_timestamp=source_timestamp,
        correlation_context=correlation_context,
        completeness=completeness,
        payload_ref=payload_ref,
        payload=dict(payload),
        source_provenance=f"{source_module}::{source_contract}",
    )


def ingest_evidence_records_v1(raw_records: Sequence[Mapping[str, Any]]) -> GhosvIngestResultV1:
    accepted: list[GhosvEvidenceRecordV1] = []
    rejected: list[str] = []
    for idx, raw in enumerate(raw_records):
        try:
            accepted.append(normalize_evidence_record_v1(raw))
        except GhosvEvidenceIngestError as exc:
            rejected.append(f"idx={idx}:{exc}")
    return GhosvIngestResultV1(records=tuple(accepted), rejected=tuple(rejected))


def load_final_order_envelope_evidence_v1(
    envelope_payload: Mapping[str, Any],
    *,
    trade_id: str,
    source_module: str = "full_core_live_path_composition_root_v1.final_order_envelope_v1",
    source_contract: str = "full_core_final_order_envelope.v1",
) -> GhosvEvidenceRecordV1:
    """Map CURRENT FinalOrderEnvelope fields to GHOSV evidence (read-only)."""
    return normalize_evidence_record_v1(
        {
            "kind": GhosvEvidenceKind.ORDER_ENVELOPE.value,
            "source_module": source_module,
            "source_contract": source_contract,
            "trade_id": trade_id,
            "instrument_id": envelope_payload.get("instrument_id"),
            "client_order_id": envelope_payload.get("client_order_id"),
            "exchange_order_id": "",
            "fill_id": "",
            "observation_timestamp": envelope_payload.get("creation_epoch", ""),
            "source_timestamp": envelope_payload.get("creation_epoch", ""),
            "correlation_context": envelope_payload.get("envelope_id", ""),
            "completeness": GhosvCompleteness.COMPLETE.value,
            "payload_ref": str(envelope_payload.get("envelope_digest", "")),
            "payload": dict(envelope_payload),
        }
    )


def load_productive_reconciliation_evidence_file_v1(
    path: Path,
    *,
    binding_trade_id: str | None = None,
) -> GhosvEvidenceRecordV1:
    """Read persisted productive reconciliation evidence JSON (no mutation)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise GhosvEvidenceIngestError("RECON_EVIDENCE_NOT_OBJECT")
    classification = _text(data.get("classification") or data.get("reconciliation_classification"))
    instrument_id = ""
    mutation_plan = data.get("mutation_plan")
    if isinstance(mutation_plan, dict):
        steps = mutation_plan.get("steps")
        if isinstance(steps, list) and steps:
            first = steps[0]
            if isinstance(first, dict):
                instrument_id = _text(first.get("instrument_id"))
    file_writer_identity = _text(data.get("single_writer_identity"))
    file_fallback_id = file_writer_identity or _text(data.get("config_digest"))
    bound = _text(binding_trade_id)
    trade_id = bound if bound else file_fallback_id
    correlation_context = (
        _text(data.get("observed_state_digest"))
        or _text(data.get("pre_state_digest"))
        or _text(data.get("config_digest"))
    )
    return normalize_evidence_record_v1(
        {
            "kind": GhosvEvidenceKind.RECONCILIATION_GATE.value,
            "source_module": "ops.productive_reconciliation_runtime_binding_v1",
            "source_contract": "productive_reconciliation_runtime_binding.v1",
            "trade_id": trade_id,
            "instrument_id": instrument_id,
            "client_order_id": "",
            "exchange_order_id": "",
            "fill_id": "",
            "observation_timestamp": _text(data.get("wall_time_unix")),
            "source_timestamp": _text(data.get("event_time_unix")),
            "correlation_context": correlation_context,
            "completeness": GhosvCompleteness.COMPLETE.value
            if classification
            else GhosvCompleteness.UNKNOWN.value,
            "payload_ref": str(path),
            "payload": {
                **data,
                "ghosv_binding_trade_id": bound or None,
                "ghosv_file_writer_identity": file_writer_identity or None,
            },
        }
    )
