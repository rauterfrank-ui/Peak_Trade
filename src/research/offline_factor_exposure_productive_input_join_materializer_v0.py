"""Offline factor exposure productive input join materializer v0.

Deterministic, offline-only join of manifest-verified TRADE_LEDGER_V1 rows to
factor snapshot rows via the operator-ratified productive contract v0. Reuses
``validate_productive_join_batch_v0`` as the sole join owner. No OLS, economic
evaluation, runtime, order, scheduler, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.linear_evidence.factor_exposure import FactorExposureInputV1
from src.research.linear_evidence.factor_exposure_productive_contract_v0 import (
    AUTHORITY_EFFECT,
    EXPECTED_DATASET_DIGEST,
    EXPECTED_PRODUCTIVE_FACTOR_ORDER,
    FactorExposureJoinContractV0,
    FactorExposureProductiveProvenanceV0,
    ProductiveInputRowV0,
    ProductiveJoinValidationResultV0,
    RUNTIME_EFFECT,
    TARGET_NAME,
    stable_digest_v0,
    validate_dataset_digest_v0,
    validate_productive_join_batch_v0,
)

PACKAGE_MARKER = "OFFLINE_FACTOR_EXPOSURE_PRODUCTIVE_INPUT_JOIN_MATERIALIZER_V0=true"
SCHEMA_VERSION = "offline_factor_exposure_productive_input_join_materializer.v0"
CANONICAL_CONTRACT_OWNER = "src/research/linear_evidence/factor_exposure_productive_contract_v0.py"
CANONICAL_JOIN_KEY = FactorExposureJoinContractV0().primary_join_key
SECONDARY_INTEGRITY_KEY = FactorExposureJoinContractV0().secondary_integrity_key
IMPLEMENTATION_DIGEST = stable_digest_v0(
    {
        "contract": SCHEMA_VERSION,
        "join_owner": CANONICAL_CONTRACT_OWNER,
        "join_key": CANONICAL_JOIN_KEY,
        "secondary_integrity_key": SECONDARY_INTEGRITY_KEY,
    }
)


class MaterializationStatus(str, Enum):
    PASS = "PASS"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    TARGET_BINDING_MISSING = "TARGET_BINDING_MISSING"


@dataclass(frozen=True)
class MaterializationResultV0:
    status: MaterializationStatus
    records: tuple[FactorExposureInputV1, ...]
    join_result: ProductiveJoinValidationResultV0
    provenance: FactorExposureProductiveProvenanceV0
    materialization_digest: str
    output_digest: str
    source_trade_ledger_digest: str
    source_factor_snapshot_digest: str
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


def load_jsonl_rows(path: Path) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError("JSONL_ROW_NOT_OBJECT")
        rows.append(payload)
    return tuple(rows)


def compute_source_rows_digest(rows: Sequence[Mapping[str, Any]]) -> str:
    ordered = sorted(
        rows,
        key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":"), default=str),
    )
    return stable_digest_v0({"rows": list(ordered), "schema": "offline_evidence_jsonl_v0"})


def productive_input_row_to_factor_exposure_input_v0(
    row: ProductiveInputRowV0,
    *,
    timestamp: int,
) -> FactorExposureInputV1:
    ordered_factor_values = {
        name: float(row.factor_values[name]) for name in EXPECTED_PRODUCTIVE_FACTOR_ORDER
    }
    return FactorExposureInputV1(
        instrument_id=row.instrument_id,
        timestamp=timestamp,
        target_return=float(row.target_return),
        factor_values=ordered_factor_values,
        factor_time=row.factor_time,
        decision_time=row.decision_time,
    )


def _records_from_join_result(
    join_result: ProductiveJoinValidationResultV0,
) -> tuple[FactorExposureInputV1, ...]:
    ordered_rows = sorted(
        join_result.admissible_rows,
        key=lambda row: (row.decision_time, row.trade_id, row.instrument_id),
    )
    records: list[FactorExposureInputV1] = []
    for index, row in enumerate(ordered_rows, start=1):
        records.append(productive_input_row_to_factor_exposure_input_v0(row, timestamp=index))
    return tuple(records)


def _serialize_records(records: Sequence[FactorExposureInputV1]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for record in records:
        payload.append(
            {
                "instrument_id": record.instrument_id,
                "timestamp": record.timestamp,
                "target_return": record.target_return,
                "factor_values": {
                    name: record.factor_values[name] for name in EXPECTED_PRODUCTIVE_FACTOR_ORDER
                },
                "factor_time": record.factor_time,
                "decision_time": record.decision_time,
            }
        )
    return payload


def build_productive_provenance_v0(
    *,
    join_result: ProductiveJoinValidationResultV0,
    source_trade_ledger_digest: str,
    source_factor_snapshot_digest: str,
) -> FactorExposureProductiveProvenanceV0:
    validate_dataset_digest_v0(EXPECTED_DATASET_DIGEST)
    return FactorExposureProductiveProvenanceV0(
        implementation_digest=IMPLEMENTATION_DIGEST,
        dataset_digest=EXPECTED_DATASET_DIGEST,
        instrument_universe=join_result.instrument_universe,
        instrument_universe_digest=join_result.instrument_universe_digest,
        time_range=dict(join_result.time_range),
        row_count_before_filter=join_result.row_count_before_filter,
        row_count_after_filter=join_result.row_count_after_filter,
        dropped_rows_by_reason=dict(join_result.dropped_rows_by_reason),
        source_trade_ledger_digest=source_trade_ledger_digest,
        source_factor_snapshot_digest=source_factor_snapshot_digest,
    )


def materialize_offline_factor_exposure_productive_inputs_v0(
    *,
    trade_ledger_rows: Sequence[Mapping[str, Any]],
    factor_snapshot_rows: Sequence[Mapping[str, Any]],
    source_trade_ledger_digest: str | None = None,
    source_factor_snapshot_digest: str | None = None,
) -> MaterializationResultV0:
    """Materialize productive FactorExposureInputV1 records from ledger + snapshots."""
    ledger_digest = source_trade_ledger_digest or compute_source_rows_digest(trade_ledger_rows)
    snapshot_digest = source_factor_snapshot_digest or compute_source_rows_digest(
        factor_snapshot_rows
    )

    join_result = validate_productive_join_batch_v0(
        trade_ledger_rows=trade_ledger_rows,
        factor_snapshots=factor_snapshot_rows,
    )
    records = _records_from_join_result(join_result)
    serialized = _serialize_records(records)
    output_digest = stable_digest_v0(
        {
            "schema_version": SCHEMA_VERSION,
            "target_name": TARGET_NAME,
            "records": serialized,
        }
    )
    materialization_digest = stable_digest_v0(
        {
            "schema_version": SCHEMA_VERSION,
            "output_digest": output_digest,
            "source_trade_ledger_digest": ledger_digest,
            "source_factor_snapshot_digest": snapshot_digest,
            "row_count_after_filter": join_result.row_count_after_filter,
            "dropped_rows_by_reason": dict(join_result.dropped_rows_by_reason),
        }
    )
    provenance = build_productive_provenance_v0(
        join_result=join_result,
        source_trade_ledger_digest=ledger_digest,
        source_factor_snapshot_digest=snapshot_digest,
    )

    if not records:
        status = (
            MaterializationStatus.TARGET_BINDING_MISSING
            if trade_ledger_rows
            else MaterializationStatus.INSUFFICIENT_DATA
        )
    else:
        status = MaterializationStatus.PASS

    return MaterializationResultV0(
        status=status,
        records=records,
        join_result=join_result,
        provenance=provenance,
        materialization_digest=materialization_digest,
        output_digest=output_digest,
        source_trade_ledger_digest=ledger_digest,
        source_factor_snapshot_digest=snapshot_digest,
    )


def serialize_materialized_productive_inputs_v0(
    records: Sequence[FactorExposureInputV1],
) -> str:
    """Deterministic JSONL serialization for repeated materialization checks."""
    serialized = _serialize_records(records)
    ordered = sorted(
        serialized,
        key=lambda row: (
            str(row.get("decision_time", "")),
            str(row.get("instrument_id", "")),
            int(row.get("timestamp", 0)),
        ),
    )
    lines = [json.dumps(row, sort_keys=True, separators=(",", ":"), default=str) for row in ordered]
    return "\n".join(lines) + ("\n" if lines else "")


def materialize_from_manifest_paths_v0(
    *,
    trade_ledger_path: Path,
    factor_snapshot_path: Path,
) -> MaterializationResultV0:
    ledger_rows = load_jsonl_rows(trade_ledger_path)
    snapshot_rows = load_jsonl_rows(factor_snapshot_path)
    return materialize_offline_factor_exposure_productive_inputs_v0(
        trade_ledger_rows=ledger_rows,
        factor_snapshot_rows=snapshot_rows,
        source_trade_ledger_digest=compute_source_rows_digest(ledger_rows),
        source_factor_snapshot_digest=compute_source_rows_digest(snapshot_rows),
    )


__all__ = [
    "AUTHORITY_EFFECT",
    "RUNTIME_EFFECT",
    "PACKAGE_MARKER",
    "SCHEMA_VERSION",
    "CANONICAL_CONTRACT_OWNER",
    "CANONICAL_JOIN_KEY",
    "SECONDARY_INTEGRITY_KEY",
    "IMPLEMENTATION_DIGEST",
    "MaterializationResultV0",
    "MaterializationStatus",
    "build_productive_provenance_v0",
    "compute_source_rows_digest",
    "load_jsonl_rows",
    "materialize_from_manifest_paths_v0",
    "materialize_offline_factor_exposure_productive_inputs_v0",
    "productive_input_row_to_factor_exposure_input_v0",
    "serialize_materialized_productive_inputs_v0",
]
