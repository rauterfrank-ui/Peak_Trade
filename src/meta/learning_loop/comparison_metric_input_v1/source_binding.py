"""Source artifact binding and digest rules for comparison_metric_input.v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from src.meta.learning_loop.comparison_metric_input_v1.constants import (
    METRIC_SEMANTICS_VERSION,
    SOURCE_DIGEST_RULE_VERSION,
)
from src.meta.learning_loop.comparison_metric_input_v1.models import (
    ComparisonMetricInputError,
    SourceBindingRecord,
    SourceRef,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)


def sha256_file(path: Path) -> str:
    if not path.is_file():
        raise ComparisonMetricInputError(f"source file not found: {path}")
    if path.is_symlink():
        raise ComparisonMetricInputError(f"source file must not be a symlink: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_equity_series_digest(equity: pd.Series) -> str:
    payload = {
        "timestamps": [ts.isoformat() for ts in equity.index],
        "values": [float(v) for v in equity.astype(float).to_numpy()],
    }
    return compute_content_sha256(payload)


def compute_trade_ledger_digest(trades: Sequence[Mapping[str, Any]]) -> str:
    payload = {
        "trades": [{"pnl": float(trade["pnl"])} for trade in trades],
    }
    return compute_content_sha256(payload)


def compute_source_digest(*, equity_series_digest: str, trade_ledger_digest: str) -> str:
    payload = {
        "rule_version": SOURCE_DIGEST_RULE_VERSION,
        "equity_series_digest": equity_series_digest,
        "trade_ledger_digest": trade_ledger_digest,
        "metric_semantics_version": METRIC_SEMANTICS_VERSION,
    }
    return compute_content_sha256(payload)


def load_trades_from_parquet(path: Path) -> list[dict[str, float]]:
    if not path.is_file():
        raise ComparisonMetricInputError(f"trades file not found: {path}")
    if path.is_symlink():
        raise ComparisonMetricInputError(f"trades file must not be a symlink: {path}")
    try:
        frame = pd.read_parquet(path)
    except Exception as exc:  # noqa: BLE001 - fail-closed surface
        raise ComparisonMetricInputError(f"failed to read trades parquet: {path}: {exc}") from exc
    if "pnl" not in frame.columns:
        raise ComparisonMetricInputError(f"trades parquet missing pnl column: {path}")
    trades: list[dict[str, float]] = []
    for index, row in frame.iterrows():
        pnl = row["pnl"]
        if pd.isna(pnl):
            raise ComparisonMetricInputError(f"trade row {index} has NaN pnl")
        trades.append({"pnl": float(pnl)})
    if not trades:
        raise ComparisonMetricInputError("trade ledger is empty")
    return trades


def verify_source_ref(ref: Mapping[str, Any], *, expected_domain: str) -> SourceRef:
    required = ("owner_domain", "ref_type", "ref_id", "digest")
    for key in required:
        if key not in ref:
            raise ComparisonMetricInputError(f"source_ref missing {key}")
        if not isinstance(ref[key], str) or not ref[key].strip():
            raise ComparisonMetricInputError(f"source_ref.{key} must be non-empty string")
    digest = ref["digest"]
    if not is_valid_sha256_hex(digest):
        raise ComparisonMetricInputError("source_ref.digest must be lowercase sha256 hex")
    ref_type = ref["ref_type"]
    if ref_type != expected_domain:
        raise ComparisonMetricInputError(
            f"source_ref.ref_type {ref_type!r} must match domain {expected_domain!r}"
        )
    return SourceRef(
        owner_domain=str(ref["owner_domain"]),
        ref_type=str(ref_type),
        ref_id=str(ref["ref_id"]),
        digest=str(digest),
    )


def verify_digest_matches_file(path: Path, expected_digest: str, *, label: str) -> None:
    actual = sha256_file(path)
    if actual != expected_digest:
        raise ComparisonMetricInputError(
            f"{label} digest mismatch: expected {expected_digest}, got {actual}"
        )


def build_binding_records(*records: SourceBindingRecord) -> tuple[SourceBindingRecord, ...]:
    return tuple(records)


def binding_records_to_mapping(records: Sequence[SourceBindingRecord]) -> list[dict[str, str]]:
    return [
        {"relative_path": record.relative_path, "content_sha256": record.content_sha256}
        for record in records
    ]


def load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ComparisonMetricInputError(f"{label} not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ComparisonMetricInputError(f"invalid JSON in {label}: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ComparisonMetricInputError(f"{label} root must be object: {path}")
    return payload


def canonical_lineage_ref_mapping(ref: SourceRef) -> dict[str, str]:
    return ref.to_mapping()


def serialize_binding_snapshot(bindings: Sequence[SourceBindingRecord]) -> str:
    return deterministic_json_dumps(binding_records_to_mapping(bindings))
