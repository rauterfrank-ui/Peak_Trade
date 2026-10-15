"""Read-only binding from CURRENT persisted execution evidence to GHOSV DTOs.

RUNTIME_AUTHORIZATION_EFFECT=NONE — no producer mutation, no exchange actions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.ghosv_bounded_context_v1.constants_v1 import PACKAGE_ID
from src.ops.ghosv_bounded_context_v1.pipeline_v1 import run_ghosv_bounded_context_v1
from src.ops.ghosv_bounded_context_v1.s01_evidence_ingest_v1 import (
    GhosvEvidenceIngestError,
    load_final_order_envelope_evidence_v1,
    load_productive_reconciliation_evidence_file_v1,
    normalize_evidence_record_v1,
)
from src.ops.ghosv_bounded_context_v1.types_v1 import (
    GhosvBoundedContextResultV1,
    GhosvCompleteness,
    GhosvEvidenceKind,
    GhosvEvidenceRecordV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    EVIDENCE_FILENAME as RECON_EVIDENCE_FILENAME,
    PORTFOLIO_STATE_FILENAME,
)

READER_CONTRACT = "ghosv_current_execution_evidence_reader.v1"
READER_AUTHORITY = "NONE"
SOURCE_MODULE = f"{PACKAGE_ID}.current_execution_evidence_reader_v1"


@dataclass(frozen=True)
class CurrentExecutionEvidenceSourcesV1:
    """Explicit read-only paths; no implicit productive runtime activation."""

    trade_id: str
    recon_dir: Path | None = None
    final_order_envelope_json: Path | None = None
    pre_external_convergence_report_json: Path | None = None


def _parse_post_count_v1(data: Mapping[str, Any]) -> tuple[int | None, bool]:
    """Return (post_count, known). Missing or non-numeric POST_COUNT is unknown (fail-closed)."""
    if "POST_COUNT" not in data:
        return None, False
    raw = data.get("POST_COUNT")
    if raw is None:
        return None, False
    if isinstance(raw, str) and not raw.strip():
        return None, False
    try:
        return int(raw), True
    except (TypeError, ValueError):
        return None, False


def _read_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise GhosvEvidenceIngestError(f"NOT_OBJECT:{path}")
    return data


def load_productive_portfolio_state_position_evidence_v1(
    path: Path,
    *,
    trade_id: str,
) -> tuple[GhosvEvidenceRecordV1, ...]:
    """Map ProductiveReconciliation portfolio snapshot positions (read-only)."""
    data = _read_json_object(path)
    positions = data.get("positions")
    if not isinstance(positions, list):
        return ()
    records: list[GhosvEvidenceRecordV1] = []
    for idx, pos in enumerate(positions):
        if not isinstance(pos, dict):
            continue
        instrument_id = str(pos.get("instrument_id") or "").strip()
        if not instrument_id:
            continue
        completeness = GhosvCompleteness.COMPLETE.value
        if data.get("missing") is True or data.get("stale") is True:
            completeness = GhosvCompleteness.UNKNOWN.value
        records.append(
            normalize_evidence_record_v1(
                {
                    "kind": GhosvEvidenceKind.POSITION_SNAPSHOT.value,
                    "source_module": "ops.productive_reconciliation_runtime_binding_v1",
                    "source_contract": "productive_portfolio_state.v1",
                    "trade_id": trade_id,
                    "instrument_id": instrument_id,
                    "client_order_id": "",
                    "exchange_order_id": "",
                    "fill_id": "",
                    "observation_timestamp": str(data.get("wall_time_unix") or ""),
                    "source_timestamp": str(data.get("event_time_unix") or ""),
                    "correlation_context": str(data.get("source_id") or ""),
                    "completeness": completeness,
                    "payload_ref": str(path),
                    "payload": {
                        **pos,
                        "portfolio_missing": data.get("missing"),
                        "portfolio_stale": data.get("stale"),
                        "writer_conflict": data.get("writer_conflict"),
                    },
                    "event_id": f"pos-{trade_id}-{idx}-{instrument_id}",
                }
            )
        )
    return tuple(records)


def load_pre_external_convergence_report_evidence_v1(
    path: Path,
    *,
    trade_id: str,
) -> tuple[GhosvEvidenceRecordV1, ...]:
    """Map PRE_EXTERNAL_CONVERGENCE_REPORT (execution boundary witness, read-only)."""
    data = _read_json_object(path)
    native_id = str(data.get("NATIVE_ID") or data.get("instrument_id") or "").strip()
    terminal = str(data.get("TERMINAL_DISPOSITION") or data.get("S5_TERMINAL_CLASS") or "")
    post_count, post_count_known = _parse_post_count_v1(data)
    pre_reached = str(data.get("PRE_EXTERNAL_REACHED") or "").lower() == "true"
    from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
        EXTERNAL_EFFECT_AUTHORIZED,
    )

    records: list[GhosvEvidenceRecordV1] = []
    records.append(
        normalize_evidence_record_v1(
            {
                "kind": GhosvEvidenceKind.PRE_EXTERNAL_REPORT.value,
                "source_module": SOURCE_MODULE,
                "source_contract": "pre_external_convergence_report.v1",
                "trade_id": trade_id,
                "instrument_id": native_id,
                "client_order_id": "",
                "exchange_order_id": "",
                "fill_id": "",
                "observation_timestamp": str(data.get("RUN_ID") or ""),
                "source_timestamp": str(data.get("RUN_ID") or ""),
                "correlation_context": str(path.name),
                "completeness": GhosvCompleteness.COMPLETE.value
                if terminal
                else GhosvCompleteness.UNKNOWN.value,
                "payload_ref": str(path),
                "payload": {
                    "disposition": terminal,
                    "pre_external_reached": pre_reached,
                    "post_count": post_count,
                    "post_count_known": post_count_known,
                    "external_effect_count": data.get("EXTERNAL_EFFECT_COUNT"),
                },
            }
        )
    )
    attempt_payload: dict[str, Any] = {
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED is True,
        "post_count_known": post_count_known,
    }
    if post_count_known:
        assert post_count is not None
        attempt_payload["post_count"] = post_count
        attempt_payload["post_occurred"] = post_count > 0
    records.append(
        normalize_evidence_record_v1(
            {
                "kind": GhosvEvidenceKind.EXECUTION_ATTEMPT.value,
                "source_module": SOURCE_MODULE,
                "source_contract": "pre_external_convergence_report.v1",
                "trade_id": trade_id,
                "instrument_id": native_id,
                "client_order_id": "",
                "exchange_order_id": "",
                "fill_id": "",
                "observation_timestamp": str(data.get("RUN_ID") or ""),
                "source_timestamp": str(data.get("RUN_ID") or ""),
                "correlation_context": str(path.name),
                "completeness": GhosvCompleteness.COMPLETE.value
                if post_count_known
                else GhosvCompleteness.UNKNOWN.value,
                "payload_ref": str(path),
                "payload": attempt_payload,
            }
        )
    )
    return tuple(records)


def load_final_order_envelope_file_evidence_v1(
    path: Path,
    *,
    trade_id: str,
) -> GhosvEvidenceRecordV1:
    payload = _read_json_object(path)
    return load_final_order_envelope_evidence_v1(payload, trade_id=trade_id)


def read_current_execution_evidence_v1(
    sources: CurrentExecutionEvidenceSourcesV1,
) -> tuple[GhosvEvidenceRecordV1, ...]:
    """Collect GHOSV records from explicit CURRENT evidence paths (read-only)."""
    out: list[GhosvEvidenceRecordV1] = []
    trade_id = sources.trade_id.strip()
    if not trade_id:
        raise GhosvEvidenceIngestError("MISSING_TRADE_ID")

    if sources.recon_dir is not None:
        recon_dir = Path(sources.recon_dir)
        recon_path = recon_dir / RECON_EVIDENCE_FILENAME
        if recon_path.is_file():
            out.append(
                load_productive_reconciliation_evidence_file_v1(
                    recon_path,
                    binding_trade_id=trade_id,
                )
            )
        portfolio_path = recon_dir / PORTFOLIO_STATE_FILENAME
        if portfolio_path.is_file():
            out.extend(
                load_productive_portfolio_state_position_evidence_v1(
                    portfolio_path, trade_id=trade_id
                )
            )

    if sources.final_order_envelope_json is not None:
        env_path = Path(sources.final_order_envelope_json)
        if env_path.is_file():
            out.append(load_final_order_envelope_file_evidence_v1(env_path, trade_id=trade_id))

    if sources.pre_external_convergence_report_json is not None:
        report_path = Path(sources.pre_external_convergence_report_json)
        if report_path.is_file():
            out.extend(
                load_pre_external_convergence_report_evidence_v1(report_path, trade_id=trade_id)
            )

    return tuple(out)


def observe_current_execution_via_ghosv_v1(
    sources: CurrentExecutionEvidenceSourcesV1,
    *,
    detected_at: str = "1970-01-01T00:00:00+00:00",
) -> GhosvBoundedContextResultV1:
    """Offline observability only: map CURRENT evidence then run GHOSV pipeline."""
    records = read_current_execution_evidence_v1(sources)
    raw: list[Mapping[str, Any]] = []
    for rec in records:
        raw.append(
            {
                "kind": rec.kind,
                "source_module": rec.source_module,
                "source_contract": rec.source_contract,
                "trade_id": rec.trade_id,
                "instrument_id": rec.instrument_id,
                "client_order_id": rec.client_order_id,
                "exchange_order_id": rec.exchange_order_id,
                "fill_id": rec.fill_id,
                "observation_timestamp": rec.observation_timestamp,
                "source_timestamp": rec.source_timestamp,
                "correlation_context": rec.correlation_context,
                "completeness": rec.completeness,
                "payload_ref": rec.payload_ref,
                "payload": dict(rec.payload),
                "event_id": rec.event_id,
            }
        )
    return run_ghosv_bounded_context_v1(raw, detected_at=detected_at)
