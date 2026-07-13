"""Operator-ratified productive normative contract for offline factor exposure v0.

Offline-only, authority-neutral contract owner. No IO, runtime, trading logic, or solver
duplication. Materializer execution remains a separate scope.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Any, Mapping, Sequence

from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    EXPECTED_DATASET_DIGEST,
)

PACKAGE_MARKER = "OFFLINE_FACTOR_EXPOSURE_PRODUCTIVE_CONTRACT_V0=true"

TARGET_CONTRACT_VERSION = "offline_factor_exposure_target_return_v0"
FACTOR_SCHEMA_VERSION = "offline_factor_exposure_productive_factors_v0"
JOIN_CONTRACT_VERSION = "offline_factor_exposure_trade_join_v0"
PROVENANCE_CONTRACT_VERSION = "offline_factor_exposure_provenance_v0"

TARGET_NAME = "net_trade_return_decimal"
TARGET_RETURN_SOURCE_NUMERATOR = "trade_ledger.net_pnl"
TARGET_RETURN_SOURCE_DENOMINATOR = "trade_ledger.entry_notional"
TARGET_RETURN_FORMULA = "net_pnl / entry_notional"
TARGET_RETURN_UNIT = "DECIMAL_RETURN"
TARGET_RETURN_BPS_FORMULA = "(net_pnl / entry_notional) * 10000"
TARGET_RETURN_PRIMARY_UNIT = "DECIMAL"
TARGET_RETURN_GROSS_NET_SEMANTICS = "NET_AFTER_RECORDED_COST_COMPONENTS"

TARGET_TIME = "exit_time"
DECISION_TIME = "entry_decision_time"
ROW_IDENTITY = "ONE_ROW_PER_COMPLETED_TRADE"

PRODUCTIVE_EVIDENCE_TYPE = "FACTOR_EXPOSURE"
PRODUCTIVE_MODEL_FAMILY = "OLS"

RATIFIED_DATASET_ID = (
    "config/research/final_research_fleet_versioned_binding_completion_v0.json"
    "#trend_following/v1.dataset_binding"
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"

INCONCLUSIVE_SENTINEL = "INCONCLUSIVE"

_ENTRY_NOTIONAL_FIELD_PRIORITY: tuple[str, ...] = (
    "entry_notional",
    "opening_notional",
    "executed_entry_notional",
    "notional",
)


class ProductiveJoinRejectionReason(str, Enum):
    MISSING_TRADE_ID = "MISSING_TRADE_ID"
    DUPLICATE_TRADE_ID = "DUPLICATE_TRADE_ID"
    MISSING_FACTOR_SNAPSHOT = "MISSING_FACTOR_SNAPSHOT"
    DUPLICATE_FACTOR_SNAPSHOT = "DUPLICATE_FACTOR_SNAPSHOT"
    ORPHAN_TARGET = "ORPHAN_TARGET"
    ORPHAN_FACTOR_ROW = "ORPHAN_FACTOR_ROW"
    INSTRUMENT_ID_MISMATCH = "INSTRUMENT_ID_MISMATCH"
    ENTRY_TIME_MISMATCH = "ENTRY_TIME_MISMATCH"
    TARGET_TIME_MISSING = "TARGET_TIME_MISSING"
    DECISION_TIME_MISSING = "DECISION_TIME_MISSING"
    TRADE_NOT_FINALIZED = "TRADE_NOT_FINALIZED"
    FEATURE_LEAKAGE_DETECTED = "FEATURE_LEAKAGE_DETECTED"
    INVALID_TIME_ORDER = "INVALID_TIME_ORDER"
    UNFINALIZED_FACTOR_INPUT = "UNFINALIZED_FACTOR_INPUT"
    TARGET_BINDING_MISSING = "TARGET_BINDING_MISSING"
    TARGET_NUMERATOR_MISSING = "TARGET_NUMERATOR_MISSING"
    TARGET_DENOMINATOR_MISSING = "TARGET_DENOMINATOR_MISSING"
    TARGET_DENOMINATOR_NON_POSITIVE = "TARGET_DENOMINATOR_NON_POSITIVE"
    TARGET_NON_FINITE = "TARGET_NON_FINITE"
    TARGET_ACCOUNTING_SEMANTICS_INCONCLUSIVE = "TARGET_ACCOUNTING_SEMANTICS_INCONCLUSIVE"
    TARGET_NOTIONAL_OWNER_AMBIGUOUS = "TARGET_NOTIONAL_OWNER_AMBIGUOUS"
    MISSING_FACTOR_VALUE = "MISSING_FACTOR_VALUE"
    NON_FINITE_FACTOR_VALUE = "NON_FINITE_FACTOR_VALUE"
    DATASET_DIGEST_CANONICAL_OWNER_MISMATCH = "DATASET_DIGEST_CANONICAL_OWNER_MISMATCH"


@dataclass(frozen=True)
class TargetReturnContractV0:
    contract_version: str = TARGET_CONTRACT_VERSION
    target_name: str = TARGET_NAME
    source_numerator: str = TARGET_RETURN_SOURCE_NUMERATOR
    source_denominator: str = TARGET_RETURN_SOURCE_DENOMINATOR
    formula: str = TARGET_RETURN_FORMULA
    unit: str = TARGET_RETURN_UNIT
    bps_formula: str = TARGET_RETURN_BPS_FORMULA
    primary_unit: str = TARGET_RETURN_PRIMARY_UNIT
    gross_net_semantics: str = TARGET_RETURN_GROSS_NET_SEMANTICS
    target_time: str = TARGET_TIME
    decision_time: str = DECISION_TIME
    use_recorded_net_pnl_as_persisted: bool = True
    do_not_synthesize_missing_cost_components: bool = True
    do_not_reconstruct_net_pnl_from_unproven_components: bool = True


@dataclass(frozen=True)
class ProductiveFactorSpecV0:
    canonical_name: str
    source_field: str
    transformation: str
    unit: str


PRODUCTIVE_FACTOR_SPECS: tuple[ProductiveFactorSpecV0, ...] = (
    ProductiveFactorSpecV0(
        canonical_name="funding_rate_abs",
        source_field="funding_rate",
        transformation="abs(float(funding_rate))",
        unit="ABSOLUTE_FUNDING_RATE_DECIMAL",
    ),
    ProductiveFactorSpecV0(
        canonical_name="spread_bps",
        source_field="spread_bps",
        transformation="float(spread_bps)",
        unit="BASIS_POINTS",
    ),
    ProductiveFactorSpecV0(
        canonical_name="volatility_estimate",
        source_field="volatility_estimate",
        transformation="float(volatility_estimate)",
        unit="EXISTING_CANONICAL_VOLATILITY_ESTIMATE_UNIT",
    ),
)

PRODUCTIVE_FACTOR_NAMES: tuple[str, ...] = tuple(
    spec.canonical_name for spec in PRODUCTIVE_FACTOR_SPECS
)
EXPECTED_PRODUCTIVE_FACTOR_ORDER: tuple[str, ...] = tuple(sorted(PRODUCTIVE_FACTOR_NAMES))
PRODUCTIVE_FACTOR_NORMALIZATION = "NONE"


@dataclass(frozen=True)
class FactorExposureJoinContractV0:
    contract_version: str = JOIN_CONTRACT_VERSION
    row_grain: str = ROW_IDENTITY
    primary_join_key: str = "trade_id"
    secondary_integrity_key: str = "instrument_id + entry_time"
    fallback_join_allowed: bool = False


@dataclass(frozen=True)
class FactorExposureProvenanceContractV0:
    contract_version: str = PROVENANCE_CONTRACT_VERSION
    dataset_id: str = RATIFIED_DATASET_ID
    expected_dataset_digest: str = EXPECTED_DATASET_DIGEST
    instrument_universe_digest_owner: str = (
        "src/research/linear_evidence/factor_exposure_productive_contract_v0.py"
        "::compute_instrument_universe_digest_v0"
    )


@dataclass(frozen=True)
class ProductiveJoinRejectedRowV0:
    trade_id: str
    reason: ProductiveJoinRejectionReason


@dataclass(frozen=True)
class ProductiveInputRowV0:
    trade_id: str
    instrument_id: str
    entry_time: str
    exit_time: str
    decision_time: str
    target_time: str
    factor_time: str
    target_return: float
    factor_values: dict[str, float]
    trade_finalized: bool
    target_finalized: bool
    factor_snapshot_finalized: bool


@dataclass(frozen=True)
class ProductiveJoinValidationResultV0:
    admissible_rows: tuple[ProductiveInputRowV0, ...]
    rejected: tuple[ProductiveJoinRejectedRowV0, ...]
    row_count_before_filter: int
    row_count_after_filter: int
    dropped_rows_by_reason: dict[str, int]
    instrument_universe: tuple[str, ...]
    instrument_universe_digest: str
    time_range: dict[str, str]
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


@dataclass(frozen=True)
class FactorExposureProductiveProvenanceV0:
    target_unit: str = TARGET_RETURN_UNIT
    target_formula: str = TARGET_RETURN_FORMULA
    target_time_semantics: str = TARGET_TIME
    feature_names: tuple[str, ...] = PRODUCTIVE_FACTOR_NAMES
    feature_source_fields: tuple[str, ...] = tuple(
        spec.source_field for spec in PRODUCTIVE_FACTOR_SPECS
    )
    feature_transformations: dict[str, str] = field(
        default_factory=lambda: {
            spec.canonical_name: spec.transformation for spec in PRODUCTIVE_FACTOR_SPECS
        }
    )
    feature_units: dict[str, str] = field(
        default_factory=lambda: {spec.canonical_name: spec.unit for spec in PRODUCTIVE_FACTOR_SPECS}
    )
    implementation_digest: str = ""
    dataset_id: str = RATIFIED_DATASET_ID
    dataset_digest: str = ""
    instrument_universe: tuple[str, ...] = ()
    instrument_universe_digest: str = ""
    time_range: dict[str, str] = field(default_factory=dict)
    row_count_before_filter: int = 0
    row_count_after_filter: int = 0
    dropped_rows_by_reason: dict[str, int] = field(default_factory=dict)
    source_trade_ledger_digest: str = ""
    source_factor_snapshot_digest: str = ""
    join_contract_version: str = JOIN_CONTRACT_VERSION
    target_contract_version: str = TARGET_CONTRACT_VERSION
    factor_schema_version: str = FACTOR_SCHEMA_VERSION
    provenance_contract_version: str = PROVENANCE_CONTRACT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_unit": self.target_unit,
            "target_formula": self.target_formula,
            "target_time_semantics": self.target_time_semantics,
            "feature_names": list(self.feature_names),
            "feature_source_fields": list(self.feature_source_fields),
            "feature_transformations": dict(self.feature_transformations),
            "feature_units": dict(self.feature_units),
            "implementation_digest": self.implementation_digest,
            "dataset_id": self.dataset_id,
            "dataset_digest": self.dataset_digest,
            "instrument_universe": list(self.instrument_universe),
            "instrument_universe_digest": self.instrument_universe_digest,
            "time_range": dict(self.time_range),
            "row_count_before_filter": self.row_count_before_filter,
            "row_count_after_filter": self.row_count_after_filter,
            "dropped_rows_by_reason": dict(self.dropped_rows_by_reason),
            "source_trade_ledger_digest": self.source_trade_ledger_digest,
            "source_factor_snapshot_digest": self.source_factor_snapshot_digest,
            "join_contract_version": self.join_contract_version,
            "target_contract_version": self.target_contract_version,
            "factor_schema_version": self.factor_schema_version,
            "provenance_contract_version": self.provenance_contract_version,
        }


def stable_digest_v0(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def compute_instrument_universe_digest_v0(instrument_ids: Sequence[str]) -> str:
    unique_sorted = sorted({str(value) for value in instrument_ids if str(value)})
    return stable_digest_v0(
        {
            "contract": "offline_factor_exposure_instrument_universe_v0",
            "instrument_ids": unique_sorted,
        }
    )


def validate_dataset_digest_v0(dataset_digest: str) -> None:
    if dataset_digest != EXPECTED_DATASET_DIGEST:
        raise ValueError(
            ProductiveJoinRejectionReason.DATASET_DIGEST_CANONICAL_OWNER_MISMATCH.value
        )


def _is_inconclusive(value: Any) -> bool:
    return value is None or value == INCONCLUSIVE_SENTINEL


def _resolve_entry_notional_v0(trade: Mapping[str, Any]) -> tuple[float | None, str | None]:
    matched_fields: list[tuple[str, float]] = []
    for field_name in _ENTRY_NOTIONAL_FIELD_PRIORITY:
        if field_name not in trade:
            continue
        raw = trade.get(field_name)
        if _is_inconclusive(raw):
            continue
        try:
            parsed = float(raw)
        except (TypeError, ValueError):
            continue
        if math.isfinite(parsed):
            matched_fields.append((field_name, parsed))
    if not matched_fields:
        return None, ProductiveJoinRejectionReason.TARGET_DENOMINATOR_MISSING.value
    if len({value for _, value in matched_fields}) > 1:
        return None, ProductiveJoinRejectionReason.TARGET_NOTIONAL_OWNER_AMBIGUOUS.value
    _, value = matched_fields[0]
    if value <= 0:
        return None, ProductiveJoinRejectionReason.TARGET_DENOMINATOR_NON_POSITIVE.value
    return value, None


def compute_target_return_decimal_v0(trade: Mapping[str, Any]) -> tuple[float | None, str | None]:
    net_raw = trade.get("net_pnl")
    if _is_inconclusive(net_raw):
        return None, ProductiveJoinRejectionReason.TARGET_NUMERATOR_MISSING.value
    try:
        net_pnl = float(net_raw)
    except (TypeError, ValueError):
        return None, ProductiveJoinRejectionReason.TARGET_NUMERATOR_MISSING.value
    if not isfinite(net_pnl):
        return None, ProductiveJoinRejectionReason.TARGET_NON_FINITE.value

    entry_notional, denom_reason = _resolve_entry_notional_v0(trade)
    if denom_reason is not None or entry_notional is None:
        return None, denom_reason or ProductiveJoinRejectionReason.TARGET_DENOMINATOR_MISSING.value

    target_return = net_pnl / entry_notional
    if not isfinite(target_return):
        return None, ProductiveJoinRejectionReason.TARGET_NON_FINITE.value
    return target_return, None


def _derive_trade_finalized_v0(trade: Mapping[str, Any]) -> tuple[bool, str | None]:
    exit_time = trade.get("exit_time")
    if _is_inconclusive(exit_time) or not str(exit_time).strip():
        return False, ProductiveJoinRejectionReason.TARGET_TIME_MISSING.value
    net_raw = trade.get("net_pnl")
    if _is_inconclusive(net_raw):
        return False, ProductiveJoinRejectionReason.TRADE_NOT_FINALIZED.value
    try:
        net_pnl = float(net_raw)
    except (TypeError, ValueError):
        return False, ProductiveJoinRejectionReason.TRADE_NOT_FINALIZED.value
    if not isfinite(net_pnl):
        return False, ProductiveJoinRejectionReason.TRADE_NOT_FINALIZED.value
    return True, None


def _resolve_factor_time_v0(snapshot: Mapping[str, Any]) -> str:
    feature_time = snapshot.get("feature_timestamp")
    if not _is_inconclusive(feature_time) and str(feature_time).strip():
        return str(feature_time)
    bar_timestamp = snapshot.get("bar_timestamp")
    if not _is_inconclusive(bar_timestamp) and str(bar_timestamp).strip():
        return str(bar_timestamp)
    return ""


def validate_time_order_v0(
    *,
    factor_time: str,
    decision_time: str,
    target_time: str,
) -> str | None:
    if not factor_time:
        return ProductiveJoinRejectionReason.FEATURE_LEAKAGE_DETECTED.value
    if not decision_time:
        return ProductiveJoinRejectionReason.DECISION_TIME_MISSING.value
    if not target_time:
        return ProductiveJoinRejectionReason.TARGET_TIME_MISSING.value
    if factor_time >= decision_time:
        return ProductiveJoinRejectionReason.FEATURE_LEAKAGE_DETECTED.value
    if decision_time >= target_time:
        return ProductiveJoinRejectionReason.INVALID_TIME_ORDER.value
    return None


def resolve_productive_factor_values_v0(
    snapshot: Mapping[str, Any],
) -> tuple[dict[str, float] | None, str | None]:
    values: dict[str, float] = {}
    for spec in PRODUCTIVE_FACTOR_SPECS:
        raw = snapshot.get(spec.source_field)
        if _is_inconclusive(raw):
            return None, ProductiveJoinRejectionReason.MISSING_FACTOR_VALUE.value
        try:
            parsed = float(raw)
        except (TypeError, ValueError):
            return None, ProductiveJoinRejectionReason.MISSING_FACTOR_VALUE.value
        if not isfinite(parsed):
            return None, ProductiveJoinRejectionReason.NON_FINITE_FACTOR_VALUE.value
        if spec.canonical_name == "funding_rate_abs":
            parsed = abs(parsed)
        values[spec.canonical_name] = parsed
    return values, None


def _validate_snapshot_finality_v0(snapshot: Mapping[str, Any]) -> str | None:
    if snapshot.get("is_finalized") is not True:
        return ProductiveJoinRejectionReason.UNFINALIZED_FACTOR_INPUT.value
    return None


def _build_snapshot_index_by_trade_id_v0(
    snapshots: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Mapping[str, Any]], dict[str, int]]:
    index: dict[str, Mapping[str, Any]] = {}
    counts: dict[str, int] = {}
    for snapshot in snapshots:
        trade_id = str(snapshot.get("trade_id", ""))
        if not trade_id:
            continue
        counts[trade_id] = counts.get(trade_id, 0) + 1
        if counts[trade_id] == 1:
            index[trade_id] = snapshot
    return index, counts


def materialize_productive_input_row_v0(
    *,
    trade: Mapping[str, Any],
    snapshot: Mapping[str, Any],
) -> tuple[ProductiveInputRowV0 | None, ProductiveJoinRejectionReason | None]:
    trade_id = str(trade.get("trade_id", ""))
    if not trade_id:
        return None, ProductiveJoinRejectionReason.MISSING_TRADE_ID

    snapshot_trade_id = str(snapshot.get("trade_id", ""))
    if not snapshot_trade_id:
        return None, ProductiveJoinRejectionReason.MISSING_FACTOR_SNAPSHOT
    if snapshot_trade_id != trade_id:
        return None, ProductiveJoinRejectionReason.INSTRUMENT_ID_MISMATCH

    instrument_id = str(trade.get("instrument_id", ""))
    snapshot_instrument_id = str(snapshot.get("instrument_id", ""))
    if not instrument_id or instrument_id != snapshot_instrument_id:
        return None, ProductiveJoinRejectionReason.INSTRUMENT_ID_MISMATCH

    entry_time = str(trade.get("entry_time", ""))
    snapshot_entry_time = str(snapshot.get("entry_time") or snapshot.get("bar_timestamp") or "")
    if not entry_time or not snapshot_entry_time or entry_time != snapshot_entry_time:
        return None, ProductiveJoinRejectionReason.ENTRY_TIME_MISMATCH

    exit_time = str(trade.get("exit_time", ""))
    if not exit_time:
        return None, ProductiveJoinRejectionReason.TARGET_TIME_MISSING

    finalized, finalized_reason = _derive_trade_finalized_v0(trade)
    if not finalized:
        reason_name = finalized_reason or ProductiveJoinRejectionReason.TRADE_NOT_FINALIZED.value
        return None, ProductiveJoinRejectionReason(reason_name)

    finality_reason = _validate_snapshot_finality_v0(snapshot)
    if finality_reason is not None:
        return None, ProductiveJoinRejectionReason(finality_reason)

    factor_time = _resolve_factor_time_v0(snapshot)
    decision_time = entry_time
    target_time = exit_time
    time_reason = validate_time_order_v0(
        factor_time=factor_time,
        decision_time=decision_time,
        target_time=target_time,
    )
    if time_reason is not None:
        return None, ProductiveJoinRejectionReason(time_reason)

    target_return, target_reason = compute_target_return_decimal_v0(trade)
    if target_reason is not None or target_return is None:
        return None, ProductiveJoinRejectionReason(
            target_reason or ProductiveJoinRejectionReason.TARGET_BINDING_MISSING.value
        )

    factor_values, factor_reason = resolve_productive_factor_values_v0(snapshot)
    if factor_reason is not None or factor_values is None:
        return None, ProductiveJoinRejectionReason(
            factor_reason or ProductiveJoinRejectionReason.MISSING_FACTOR_VALUE.value
        )

    return (
        ProductiveInputRowV0(
            trade_id=trade_id,
            instrument_id=instrument_id,
            entry_time=entry_time,
            exit_time=exit_time,
            decision_time=decision_time,
            target_time=target_time,
            factor_time=factor_time,
            target_return=target_return,
            factor_values=factor_values,
            trade_finalized=True,
            target_finalized=True,
            factor_snapshot_finalized=True,
        ),
        None,
    )


def validate_productive_join_batch_v0(
    *,
    trade_ledger_rows: Sequence[Mapping[str, Any]],
    factor_snapshots: Sequence[Mapping[str, Any]],
) -> ProductiveJoinValidationResultV0:
    snapshot_index, snapshot_counts = _build_snapshot_index_by_trade_id_v0(factor_snapshots)
    rejected: list[ProductiveJoinRejectedRowV0] = []
    dropped: dict[str, int] = {}
    admissible: list[ProductiveInputRowV0] = []
    seen_trade_ids: set[str] = set()

    ordered_trades = sorted(
        trade_ledger_rows,
        key=lambda row: (
            str(row.get("trade_id", "")),
            str(row.get("entry_time", "")),
            str(row.get("instrument_id", "")),
        ),
    )

    for trade in ordered_trades:
        trade_id = str(trade.get("trade_id", ""))
        if not trade_id:
            reason = ProductiveJoinRejectionReason.MISSING_TRADE_ID
            rejected.append(ProductiveJoinRejectedRowV0(trade_id="", reason=reason))
            dropped[reason.value] = dropped.get(reason.value, 0) + 1
            continue
        if trade_id in seen_trade_ids:
            reason = ProductiveJoinRejectionReason.DUPLICATE_TRADE_ID
            rejected.append(ProductiveJoinRejectedRowV0(trade_id=trade_id, reason=reason))
            dropped[reason.value] = dropped.get(reason.value, 0) + 1
            continue
        seen_trade_ids.add(trade_id)

        if snapshot_counts.get(trade_id, 0) > 1:
            reason = ProductiveJoinRejectionReason.DUPLICATE_FACTOR_SNAPSHOT
            rejected.append(ProductiveJoinRejectedRowV0(trade_id=trade_id, reason=reason))
            dropped[reason.value] = dropped.get(reason.value, 0) + 1
            continue

        snapshot = snapshot_index.get(trade_id)
        if snapshot is None:
            reason = ProductiveJoinRejectionReason.MISSING_FACTOR_SNAPSHOT
            rejected.append(ProductiveJoinRejectedRowV0(trade_id=trade_id, reason=reason))
            dropped[reason.value] = dropped.get(reason.value, 0) + 1
            continue

        row, row_reason = materialize_productive_input_row_v0(trade=trade, snapshot=snapshot)
        if row_reason is not None or row is None:
            reason = row_reason or ProductiveJoinRejectionReason.TARGET_BINDING_MISSING
            rejected.append(ProductiveJoinRejectedRowV0(trade_id=trade_id, reason=reason))
            dropped[reason.value] = dropped.get(reason.value, 0) + 1
            continue
        admissible.append(row)

    snapshot_trade_ids = {
        str(row.get("trade_id", "")) for row in factor_snapshots if row.get("trade_id")
    }
    ledger_trade_ids = {
        str(row.get("trade_id", "")) for row in trade_ledger_rows if row.get("trade_id")
    }
    for orphan_id in sorted(snapshot_trade_ids - ledger_trade_ids):
        reason = ProductiveJoinRejectionReason.ORPHAN_FACTOR_ROW
        rejected.append(ProductiveJoinRejectedRowV0(trade_id=orphan_id, reason=reason))
        dropped[reason.value] = dropped.get(reason.value, 0) + 1

    instrument_universe = tuple(sorted({row.instrument_id for row in admissible}))
    time_range: dict[str, str] = {}
    if admissible:
        ordered = sorted(admissible, key=lambda row: row.decision_time)
        time_range = {"start": ordered[0].decision_time, "end": ordered[-1].target_time}

    return ProductiveJoinValidationResultV0(
        admissible_rows=tuple(admissible),
        rejected=tuple(rejected),
        row_count_before_filter=len(trade_ledger_rows),
        row_count_after_filter=len(admissible),
        dropped_rows_by_reason=dropped,
        instrument_universe=instrument_universe,
        instrument_universe_digest=compute_instrument_universe_digest_v0(instrument_universe),
        time_range=time_range,
    )


def productive_factor_names_v0() -> tuple[str, ...]:
    return EXPECTED_PRODUCTIVE_FACTOR_ORDER
