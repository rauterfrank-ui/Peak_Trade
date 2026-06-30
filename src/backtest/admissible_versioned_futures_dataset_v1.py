"""
Deterministic offline admissible versioned futures dataset binding v1 (RUNBOOK STEP 29M).

Fail-closed contract for versioned futures dataset identity, digest, provenance,
split/leakage integrity, and field semantics. No network, no credentials, no runtime.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

import pandas as pd

ADMISSIBLE_VERSIONED_FUTURES_DATASET_VERSION = "backtest_admissible_versioned_futures_dataset_v1"
ADMISSIBLE_VERSIONED_FUTURES_DATASET_OWNER = "backtest.admissible_versioned_futures_dataset_v1"
DEFAULT_DATASET_VERSION = "v1"
DATASET_SCHEMA_VERSION = "v1"
SPLIT_POLICY_VERSION = "v1"
TIMESTAMP_SEMANTICS = "utc_bar_close_exclusive_end"
TIMEZONE = "UTC"
ORDERING_STATUS_SORTED = "SORTED_ASCENDING_UNIQUE_INDEX"
DUPLICATE_POLICY = "FAIL_CLOSED_ON_DUPLICATE_INDEX"
MISSING_DATA_POLICY = "FAIL_CLOSED_ON_REQUIRED_FIELD_MISSING"
FINALITY_RULE = "ALL_ROWS_IS_FINAL_TRUE"

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})
_ALLOWED_CONTRACT_TYPES = frozenset({"futures", "perpetual", "swap"})
_REQUIRED_BAR_COLUMNS = frozenset(
    {
        "open",
        "high",
        "low",
        "close",
        "volume",
        "mark_price",
        "index_price",
        "best_bid",
        "best_ask",
        "funding_rate",
        "is_final",
    }
)


class AdmissibleVersionedFuturesDatasetError(ValueError):
    """Fail-closed dataset admissibility error."""


class AdmissibilityStatus(str, Enum):
    ADMISSIBLE = "ADMISSIBLE"
    BLOCKED_MISSING_VERSION = "BLOCKED_MISSING_VERSION"
    BLOCKED_MISSING_DIGEST = "BLOCKED_MISSING_DIGEST"
    BLOCKED_NON_FUTURES_DATA = "BLOCKED_NON_FUTURES_DATA"
    BLOCKED_BITCOIN_DIRECTION = "BLOCKED_BITCOIN_DIRECTION"
    BLOCKED_SCHEMA_MISMATCH = "BLOCKED_SCHEMA_MISMATCH"
    BLOCKED_PROVENANCE_MISSING = "BLOCKED_PROVENANCE_MISSING"
    BLOCKED_DATA_MUTATION = "BLOCKED_DATA_MUTATION"
    BLOCKED_TEMPORAL_LEAKAGE = "BLOCKED_TEMPORAL_LEAKAGE"
    BLOCKED_SPLIT_OVERLAP = "BLOCKED_SPLIT_OVERLAP"
    BLOCKED_UNSORTED_OR_DUPLICATE_EVENTS = "BLOCKED_UNSORTED_OR_DUPLICATE_EVENTS"
    BLOCKED_REQUIRED_FIELD_MISSING = "BLOCKED_REQUIRED_FIELD_MISSING"


@dataclass(frozen=True)
class DatasetFieldBindingsV1:
    mark_price_field_binding: str
    index_price_field_binding: str
    bid_ask_field_binding: str
    funding_field_binding: str
    ohlcv_field_binding: str

    def to_dict(self) -> dict[str, str]:
        return {
            "mark_price_field_binding": self.mark_price_field_binding,
            "index_price_field_binding": self.index_price_field_binding,
            "bid_ask_field_binding": self.bid_ask_field_binding,
            "funding_field_binding": self.funding_field_binding,
            "ohlcv_field_binding": self.ohlcv_field_binding,
        }


@dataclass(frozen=True)
class DatasetProvenanceV1:
    source_type: str
    venue_id: str
    ingestion_timestamp: str
    generation_method: str
    provenance_ref: str

    def to_dict(self) -> dict[str, str]:
        return {
            "source_type": self.source_type,
            "venue_id": self.venue_id,
            "ingestion_timestamp": self.ingestion_timestamp,
            "generation_method": self.generation_method,
            "provenance_ref": self.provenance_ref,
        }


@dataclass(frozen=True)
class VersionedFuturesDatasetDescriptorV1:
    dataset_id: str
    dataset_version: str
    dataset_schema_version: str
    dataset_digest: str
    instrument_id: str
    contract_type: str
    futures_only: bool
    bitcoin_direction_allowed: bool
    venue_id: str
    start_time: str
    end_time: str
    row_count: int
    field_bindings: DatasetFieldBindingsV1
    training_period: str
    validation_period: str
    out_of_sample_period: str
    split_policy_version: str
    timestamp_semantics: str
    timezone: str
    ordering_status: str
    duplicate_policy: str
    missing_data_policy: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "dataset_schema_version": self.dataset_schema_version,
            "dataset_digest": self.dataset_digest,
            "instrument_id": self.instrument_id,
            "contract_type": self.contract_type,
            "futures_only": self.futures_only,
            "bitcoin_direction_allowed": self.bitcoin_direction_allowed,
            "venue_id": self.venue_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "row_count": self.row_count,
            "field_bindings": self.field_bindings.to_dict(),
            "training_period": self.training_period,
            "validation_period": self.validation_period,
            "out_of_sample_period": self.out_of_sample_period,
            "split_policy_version": self.split_policy_version,
            "timestamp_semantics": self.timestamp_semantics,
            "timezone": self.timezone,
            "ordering_status": self.ordering_status,
            "duplicate_policy": self.duplicate_policy,
            "missing_data_policy": self.missing_data_policy,
        }


@dataclass(frozen=True)
class AdmissibleVersionedFuturesDatasetResultV1:
    contract_version: str
    owner: str
    admissibility_status: AdmissibilityStatus
    reason_codes: tuple[str, ...]
    descriptor: Optional[VersionedFuturesDatasetDescriptorV1]
    provenance: Optional[DatasetProvenanceV1]
    provenance_digest: str
    dataset_digest: str
    config_digest: str
    implementation_digest: str
    manifest_digest: str
    leakage_check_status: str
    mutation_check_status: str
    futures_only: bool
    bitcoin_direction_allowed: bool
    event_count: int

    def is_admissible(self) -> bool:
        return self.admissibility_status is AdmissibilityStatus.ADMISSIBLE

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "contract_version": self.contract_version,
            "owner": self.owner,
            "admissibility_status": self.admissibility_status.value,
            "reason_codes": list(self.reason_codes),
            "provenance_digest": self.provenance_digest,
            "dataset_digest": self.dataset_digest,
            "config_digest": self.config_digest,
            "implementation_digest": self.implementation_digest,
            "manifest_digest": self.manifest_digest,
            "leakage_check_status": self.leakage_check_status,
            "mutation_check_status": self.mutation_check_status,
            "futures_only": self.futures_only,
            "bitcoin_direction_allowed": self.bitcoin_direction_allowed,
            "event_count": self.event_count,
        }
        if self.descriptor is not None:
            payload.update(self.descriptor.to_dict())
        if self.provenance is not None:
            payload["source_type"] = self.provenance.source_type
            payload["provenance_ref"] = self.provenance.provenance_ref
        return payload

    def evidence_digest(self) -> str:
        payload = self.to_dict()
        payload.pop("manifest_digest", None)
        return _stable_digest(payload)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _valid_sha256(value: str) -> bool:
    return bool(_SHA256_HEX_RE.match(str(value)))


def _reject_forbidden_instrument(instrument_id: str) -> None:
    lowered = instrument_id.lower()
    for token in _FORBIDDEN_INSTRUMENT_SUBSTRINGS:
        if token in lowered:
            raise AdmissibleVersionedFuturesDatasetError(
                f"instrument_kind_forbidden:{instrument_id}"
            )


def compute_versioned_dataset_digest(
    bars: pd.DataFrame,
    *,
    field_bindings: DatasetFieldBindingsV1,
) -> str:
    if bars.empty:
        return _stable_digest({"empty": True, "owner": ADMISSIBLE_VERSIONED_FUTURES_DATASET_OWNER})
    frame = bars.sort_index()
    columns_to_digest: set[str] = set()
    for columns_csv in field_bindings.to_dict().values():
        for column in columns_csv.split(","):
            column = column.strip()
            if column:
                columns_to_digest.add(column)
    columns_payload: dict[str, Any] = {}
    for column in sorted(columns_to_digest):
        if column not in frame.columns:
            continue
        series = frame[column]
        if pd.api.types.is_bool_dtype(series):
            columns_payload[column] = _stable_digest(series.tolist())
        elif pd.api.types.is_numeric_dtype(series):
            columns_payload[column] = _stable_digest(series.astype(float).tolist())
        else:
            columns_payload[column] = _stable_digest([str(value) for value in series.tolist()])
    payload = {
        "owner": ADMISSIBLE_VERSIONED_FUTURES_DATASET_OWNER,
        "field_bindings": field_bindings.to_dict(),
        "columns": columns_payload,
        "index_start": str(frame.index[0]),
        "index_end": str(frame.index[-1]),
        "row_count": len(frame),
    }
    return _stable_digest(payload)


def compute_provenance_digest(provenance: DatasetProvenanceV1) -> str:
    return _stable_digest(provenance.to_dict())


def _period_label(start: pd.Timestamp, end: pd.Timestamp) -> str:
    return f"{start}..{end}"


def compute_split_periods_from_bars(
    bars: pd.DataFrame,
    *,
    train_fraction: float = 0.50,
    validation_fraction: float = 0.25,
) -> tuple[str, str, str]:
    if bars.empty:
        raise AdmissibleVersionedFuturesDatasetError("bars_empty_for_split")
    n = len(bars)
    train_end = max(1, int(n * train_fraction))
    val_end = max(train_end + 1, int(n * (train_fraction + validation_fraction)))
    if val_end >= n:
        val_end = n - 1
    if train_end >= val_end:
        raise AdmissibleVersionedFuturesDatasetError("split_fractions_too_small")
    idx = bars.sort_index().index
    training = _period_label(idx[0], idx[train_end - 1])
    validation = _period_label(idx[train_end], idx[val_end - 1])
    out_of_sample = _period_label(idx[val_end], idx[-1])
    return training, validation, out_of_sample


def _parse_period_bounds(period: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    if ".." not in period:
        raise AdmissibleVersionedFuturesDatasetError(f"invalid_period_format:{period}")
    start_raw, end_raw = period.split("..", 1)
    return pd.Timestamp(start_raw), pd.Timestamp(end_raw)


def _slice_for_period(bars: pd.DataFrame, period: str) -> pd.DataFrame:
    start, end = _parse_period_bounds(period)
    frame = bars.sort_index()
    mask = (frame.index >= start) & (frame.index <= end)
    return frame.loc[mask]


def default_field_bindings_v1() -> DatasetFieldBindingsV1:
    return DatasetFieldBindingsV1(
        mark_price_field_binding="mark_price",
        index_price_field_binding="index_price",
        bid_ask_field_binding="best_bid,best_ask",
        funding_field_binding="funding_rate",
        ohlcv_field_binding="open,high,low,close,volume",
    )


def dataset_admissibility_binding_requested(cfg: Mapping[str, Any]) -> bool:
    backtest = cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        return False
    section = backtest.get("dataset_admissibility")
    if not isinstance(section, Mapping):
        return False
    if section.get("bind") is True:
        return True
    dataset = section.get("dataset")
    if isinstance(dataset, Mapping):
        return str(dataset.get("dataset_version", "")) == DEFAULT_DATASET_VERSION
    return False


def _require_mapping(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AdmissibleVersionedFuturesDatasetError(f"{field_name}_missing_or_invalid")
    return value


def load_dataset_admissibility_from_cfg(
    cfg: Mapping[str, Any],
) -> tuple[VersionedFuturesDatasetDescriptorV1, DatasetProvenanceV1]:
    backtest = cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        raise AdmissibleVersionedFuturesDatasetError("backtest_section_missing")
    section = _require_mapping(
        backtest.get("dataset_admissibility"), field_name="dataset_admissibility"
    )
    dataset_raw = _require_mapping(section.get("dataset"), field_name="dataset")
    provenance_raw = _require_mapping(section.get("provenance"), field_name="provenance")
    bindings_raw = dataset_raw.get("field_bindings")
    if isinstance(bindings_raw, Mapping):
        field_bindings = DatasetFieldBindingsV1(
            mark_price_field_binding=str(bindings_raw["mark_price_field_binding"]),
            index_price_field_binding=str(bindings_raw["index_price_field_binding"]),
            bid_ask_field_binding=str(bindings_raw["bid_ask_field_binding"]),
            funding_field_binding=str(bindings_raw["funding_field_binding"]),
            ohlcv_field_binding=str(bindings_raw["ohlcv_field_binding"]),
        )
    else:
        field_bindings = default_field_bindings_v1()
    descriptor = VersionedFuturesDatasetDescriptorV1(
        dataset_id=str(dataset_raw["dataset_id"]),
        dataset_version=str(dataset_raw["dataset_version"]),
        dataset_schema_version=str(
            dataset_raw.get("dataset_schema_version", DATASET_SCHEMA_VERSION)
        ),
        dataset_digest=str(dataset_raw["dataset_digest"]),
        instrument_id=str(dataset_raw["instrument_id"]),
        contract_type=str(dataset_raw["contract_type"]),
        futures_only=bool(dataset_raw.get("futures_only", True)),
        bitcoin_direction_allowed=bool(dataset_raw.get("bitcoin_direction_allowed", False)),
        venue_id=str(dataset_raw.get("venue_id", provenance_raw.get("venue_id", ""))),
        start_time=str(dataset_raw["start_time"]),
        end_time=str(dataset_raw["end_time"]),
        row_count=int(dataset_raw["row_count"]),
        field_bindings=field_bindings,
        training_period=str(dataset_raw["training_period"]),
        validation_period=str(dataset_raw["validation_period"]),
        out_of_sample_period=str(dataset_raw["out_of_sample_period"]),
        split_policy_version=str(dataset_raw.get("split_policy_version", SPLIT_POLICY_VERSION)),
        timestamp_semantics=str(dataset_raw.get("timestamp_semantics", TIMESTAMP_SEMANTICS)),
        timezone=str(dataset_raw.get("timezone", TIMEZONE)),
        ordering_status=str(dataset_raw.get("ordering_status", ORDERING_STATUS_SORTED)),
        duplicate_policy=str(dataset_raw.get("duplicate_policy", DUPLICATE_POLICY)),
        missing_data_policy=str(dataset_raw.get("missing_data_policy", MISSING_DATA_POLICY)),
    )
    provenance = DatasetProvenanceV1(
        source_type=str(provenance_raw["source_type"]),
        venue_id=str(provenance_raw["venue_id"]),
        ingestion_timestamp=str(provenance_raw["ingestion_timestamp"]),
        generation_method=str(provenance_raw["generation_method"]),
        provenance_ref=str(provenance_raw["provenance_ref"]),
    )
    return descriptor, provenance


def _validate_field_bindings(
    bars: pd.DataFrame,
    bindings: DatasetFieldBindingsV1,
    reason_codes: list[str],
) -> bool:
    ok = True
    for binding_name, columns_csv in bindings.to_dict().items():
        for column in columns_csv.split(","):
            column = column.strip()
            if not column:
                reason_codes.append(f"field_binding_empty:{binding_name}")
                ok = False
                continue
            if column not in bars.columns:
                reason_codes.append(f"field_binding_column_missing:{column}")
                ok = False
    return ok


def _validate_required_values(bars: pd.DataFrame, reason_codes: list[str]) -> bool:
    ok = True
    for column in sorted(_REQUIRED_BAR_COLUMNS):
        if column not in bars.columns:
            reason_codes.append(f"required_column_missing:{column}")
            ok = False
            continue
        series = bars[column]
        if series.isna().any():
            reason_codes.append(f"required_column_has_missing:{column}")
            ok = False
        if column == "is_final" and not bool(series.all()):
            reason_codes.append("required_is_final_not_all_true")
            ok = False
    return ok


def _validate_ordering(bars: pd.DataFrame, reason_codes: list[str]) -> bool:
    if not bars.index.is_monotonic_increasing:
        reason_codes.append("index_not_sorted")
        return False
    if bars.index.has_duplicates:
        reason_codes.append("duplicate_index_timestamps")
        return False
    return True


def _validate_splits(
    bars: pd.DataFrame,
    descriptor: VersionedFuturesDatasetDescriptorV1,
    reason_codes: list[str],
) -> tuple[bool, str, str]:
    leakage_status = "PASS"
    try:
        train = _slice_for_period(bars, descriptor.training_period)
        val = _slice_for_period(bars, descriptor.validation_period)
        oos = _slice_for_period(bars, descriptor.out_of_sample_period)
    except AdmissibleVersionedFuturesDatasetError as exc:
        reason_codes.append(str(exc))
        return False, "BLOCKED", "NOT_RUN"

    if train.empty or val.empty or oos.empty:
        reason_codes.append("split_period_empty")
        return False, "BLOCKED", "NOT_RUN"

    train_idx = set(train.index)
    val_idx = set(val.index)
    oos_idx = set(oos.index)
    if train_idx & val_idx or train_idx & oos_idx or val_idx & oos_idx:
        reason_codes.append("split_index_overlap")
        return False, "BLOCKED", "NOT_RUN"

    train_max = train.index.max()
    val_min = val.index.min()
    val_max = val.index.max()
    oos_min = oos.index.min()
    if not (train_max < val_min):
        reason_codes.append("temporal_leakage_train_validation")
        leakage_status = "BLOCKED"
    if not (val_max < oos_min):
        reason_codes.append("temporal_leakage_validation_oos")
        leakage_status = "BLOCKED"
    if leakage_status == "BLOCKED":
        return False, leakage_status, "PASS"
    return True, leakage_status, "PASS"


def evaluate_admissible_versioned_futures_dataset_v1(
    *,
    bars: pd.DataFrame,
    descriptor: VersionedFuturesDatasetDescriptorV1,
    provenance: DatasetProvenanceV1,
    instrument_id: str,
) -> AdmissibleVersionedFuturesDatasetResultV1:
    reason_codes: list[str] = []
    status = AdmissibilityStatus.ADMISSIBLE
    mutation_status = "NOT_RUN"
    leakage_status = "NOT_RUN"

    if not descriptor.dataset_version or not descriptor.dataset_schema_version:
        status = AdmissibilityStatus.BLOCKED_MISSING_VERSION
        reason_codes.append("dataset_version_or_schema_missing")
    if not _valid_sha256(descriptor.dataset_digest):
        status = AdmissibilityStatus.BLOCKED_MISSING_DIGEST
        reason_codes.append("dataset_digest_missing_or_invalid")

    if not provenance.source_type or not provenance.provenance_ref:
        status = AdmissibilityStatus.BLOCKED_PROVENANCE_MISSING
        reason_codes.append("provenance_missing")

    if descriptor.contract_type.lower() not in _ALLOWED_CONTRACT_TYPES:
        status = AdmissibilityStatus.BLOCKED_NON_FUTURES_DATA
        reason_codes.append(f"contract_type_not_futures:{descriptor.contract_type}")
    if not descriptor.futures_only:
        status = AdmissibilityStatus.BLOCKED_NON_FUTURES_DATA
        reason_codes.append("futures_only_false")
    if provenance.source_type.lower() in {"spot", "synthetic_spot"}:
        status = AdmissibilityStatus.BLOCKED_NON_FUTURES_DATA
        reason_codes.append(f"source_type_spot:{provenance.source_type}")

    if descriptor.bitcoin_direction_allowed:
        status = AdmissibilityStatus.BLOCKED_BITCOIN_DIRECTION
        reason_codes.append("bitcoin_direction_allowed_true")
    try:
        _reject_forbidden_instrument(descriptor.instrument_id)
    except AdmissibleVersionedFuturesDatasetError:
        status = AdmissibilityStatus.BLOCKED_BITCOIN_DIRECTION
        reason_codes.append("instrument_forbidden")
    if descriptor.instrument_id != instrument_id:
        reason_codes.append("instrument_id_mismatch")

    if descriptor.dataset_schema_version != DATASET_SCHEMA_VERSION:
        status = AdmissibilityStatus.BLOCKED_SCHEMA_MISMATCH
        reason_codes.append("dataset_schema_version_mismatch")

    if bars.empty:
        status = AdmissibilityStatus.BLOCKED_REQUIRED_FIELD_MISSING
        reason_codes.append("bars_empty")
    elif descriptor.row_count != len(bars):
        reason_codes.append("row_count_mismatch")

    computed_digest = compute_versioned_dataset_digest(
        bars, field_bindings=descriptor.field_bindings
    )
    provenance_digest = compute_provenance_digest(provenance) if provenance.provenance_ref else ""
    mutation_status = "NOT_RUN"
    if _valid_sha256(descriptor.dataset_digest):
        mutation_status = "PASS"
        if descriptor.dataset_digest != computed_digest:
            status = AdmissibilityStatus.BLOCKED_DATA_MUTATION
            mutation_status = "BLOCKED"
            reason_codes.append("dataset_digest_mismatch")

    if not bars.empty:
        if not _validate_ordering(bars, reason_codes):
            status = AdmissibilityStatus.BLOCKED_UNSORTED_OR_DUPLICATE_EVENTS
        if not _validate_field_bindings(bars, descriptor.field_bindings, reason_codes):
            status = AdmissibilityStatus.BLOCKED_REQUIRED_FIELD_MISSING
        if not _validate_required_values(bars, reason_codes):
            status = AdmissibilityStatus.BLOCKED_REQUIRED_FIELD_MISSING
        split_ok, leakage_status, _ = _validate_splits(bars, descriptor, reason_codes)
        if not split_ok:
            if "split_index_overlap" in reason_codes:
                status = AdmissibilityStatus.BLOCKED_SPLIT_OVERLAP
            elif any(code.startswith("temporal_leakage") for code in reason_codes):
                status = AdmissibilityStatus.BLOCKED_TEMPORAL_LEAKAGE
            else:
                status = AdmissibilityStatus.BLOCKED_SPLIT_OVERLAP

    config_payload = {
        "descriptor": descriptor.to_dict(),
        "provenance": provenance.to_dict(),
        "instrument_id": instrument_id,
    }
    config_digest = _stable_digest(config_payload)
    implementation_digest = _stable_digest(
        {
            "owner": ADMISSIBLE_VERSIONED_FUTURES_DATASET_OWNER,
            "contract_version": ADMISSIBLE_VERSIONED_FUTURES_DATASET_VERSION,
            "dataset_schema_version": DATASET_SCHEMA_VERSION,
            "split_policy_version": SPLIT_POLICY_VERSION,
        }
    )

    result_without_manifest = {
        "admissibility_status": status.value,
        "dataset_digest": computed_digest,
        "provenance_digest": provenance_digest,
        "config_digest": config_digest,
        "implementation_digest": implementation_digest,
        "reason_codes": sorted(set(reason_codes)),
    }
    manifest_digest = _stable_digest(result_without_manifest)

    return AdmissibleVersionedFuturesDatasetResultV1(
        contract_version=ADMISSIBLE_VERSIONED_FUTURES_DATASET_VERSION,
        owner=ADMISSIBLE_VERSIONED_FUTURES_DATASET_OWNER,
        admissibility_status=status,
        reason_codes=tuple(sorted(set(reason_codes))),
        descriptor=descriptor,
        provenance=provenance,
        provenance_digest=provenance_digest,
        dataset_digest=computed_digest,
        config_digest=config_digest,
        implementation_digest=implementation_digest,
        manifest_digest=manifest_digest,
        leakage_check_status=leakage_status,
        mutation_check_status=mutation_status,
        futures_only=descriptor.futures_only,
        bitcoin_direction_allowed=descriptor.bitcoin_direction_allowed,
        event_count=len(bars),
    )


def serialize_dataset_admissibility_binding_v1(
    result: AdmissibleVersionedFuturesDatasetResultV1,
) -> dict[str, Any]:
    payload = result.to_dict()
    payload["binding_status"] = (
        "PASS" if result.is_admissible() else result.admissibility_status.value
    )
    payload["evidence_digest"] = result.evidence_digest()
    return payload
