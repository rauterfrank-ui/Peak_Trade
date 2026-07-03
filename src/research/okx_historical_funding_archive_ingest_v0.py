"""OKX Historical Funding Archive ingest adapter v0.

Consumes public OKX Historical Data Portal monthly settlement archives,
normalizes schema, enforces fail-closed guards, and emits PIT-safe funding
events for cross-sectional panel owners. Research-only; no network in tests.
"""

from __future__ import annotations

import csv
import hashlib
import io
import time
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_funding_rate_delta_momentum_scoring_v0 import (
    funding_cashflow_provenance_marker_v0,
    score_input_provenance_marker_v0,
)
from src.research.missing_funding_policy_v0 import (
    MISSING_FUNDING_FAIL_CLOSED,
    MISSING_FUNDING_IS_ZERO,
    MISSING_FUNDING_VALUE,
    is_missing_funding_value_v0,
    reject_synthetic_zero_funding_fallback_v0,
)

PACKAGE_MARKER = "OKX_HISTORICAL_FUNDING_ARCHIVE_INGEST_V0=true"
MODULE_VERSION = "okx_historical_funding_archive_ingest.v0"
SOURCE_ID = "OKX_HISTORICAL_FUNDING_ARCHIVE"
SOURCE_VENUE = "OKX"
SOURCE_ACCESS_METHOD = "HISTORICAL_DATA_PORTAL_ARCHIVE"
SCHEMA_VERSION = "okx_historical_funding_archive_normalized_event.v0"

FUNDING_RATE_FIELD = "funding_rate"
FUNDING_TIMESTAMP_FIELD = "funding_time"
INSTRUMENT_FIELD = "instrument_name"
SETTLEMENT_CLASS = "SETTLEMENT"
RATE_UNIT = "decimal_fraction_per_8h_interval"
RATE_SIGN_CONVENTION = "signed_decimal_long_pays_positive"
FUNDING_INTERVAL_MS = 28800000
TIMEZONE = "UTC"

REQUIRED_CSV_COLUMNS = frozenset({FUNDING_RATE_FIELD, FUNDING_TIMESTAMP_FIELD, INSTRUMENT_FIELD})
FORECAST_COLUMN_NAMES = frozenset(
    {
        "nextFundingRate",
        "predictedFundingRate",
        "fundingRateForecast",
        "forecast_funding_rate",
        "realizedRate",
    }
)
FORBIDDEN_INSTRUMENT_TOKENS = frozenset({"btc", "xbt", "bitcoin"})
SPOT_DELIVERY_SUFFIXES = ("-SPOT", "-FUTURES", "-FUTURE", "-DELIVERY")

CDN_BASE = "https://static.okx.com/cdn/okex/traderecords/swaprates/monthly"

HISTORICAL_UNIVERSE_LIFECYCLE_PASS = True
FULL_PANEL_PROMOTION_REQUIRES_HISTORICAL_UNIVERSE_LIFECYCLE_PASS = (
    "FULL_PANEL_PROMOTION_REQUIRES_HISTORICAL_UNIVERSE_LIFECYCLE_PASS"
)


class ArchiveValidationErrorCode(str, Enum):
    MISSING_FUNDING_RATE = "MISSING_FUNDING_RATE"
    MISSING_FUNDING_TIME = "MISSING_FUNDING_TIME"
    MISSING_INSTRUMENT = "MISSING_INSTRUMENT"
    FORECAST_COLUMN_PRESENT = "FORECAST_COLUMN_PRESENT"
    WRONG_INSTRUMENT = "WRONG_INSTRUMENT"
    BITCOIN_INSTRUMENT = "BITCOIN_INSTRUMENT"
    SPOT_OR_DELIVERY_INSTRUMENT = "SPOT_OR_DELIVERY_INSTRUMENT"
    INVALID_RATE_UNIT = "INVALID_RATE_UNIT"
    INVALID_TIMESTAMP_TYPE = "INVALID_TIMESTAMP_TYPE"
    INVALID_INTERVAL = "INVALID_INTERVAL"
    DUPLICATE_KEY = "DUPLICATE_KEY"
    NON_MONOTONIC_TIMESTAMPS = "NON_MONOTONIC_TIMESTAMPS"
    EMPTY_ARCHIVE = "EMPTY_ARCHIVE"
    MULTIPLE_CSV_IN_ZIP = "MULTIPLE_CSV_IN_ZIP"
    NO_CSV_IN_ZIP = "NO_CSV_IN_ZIP"


class ArchiveAccessGuardReason(str, Enum):
    MAX_INSTRUMENTS = "MAX_INSTRUMENTS"
    MAX_MONTHS = "MAX_MONTHS"
    MAX_HTTP_REQUESTS = "MAX_HTTP_REQUESTS"
    MAX_TOTAL_BYTES = "MAX_TOTAL_BYTES"
    MAX_RUNTIME_SECONDS = "MAX_RUNTIME_SECONDS"


class ArchiveIngestTerminalStatus(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE_NOT_PROMOTED = "INCOMPLETE_NOT_PROMOTED"
    GUARD_EXCEEDED_FAIL_CLOSED = "GUARD_EXCEEDED_FAIL_CLOSED"
    VALIDATION_FAILED = "VALIDATION_FAILED"


@dataclass(frozen=True)
class NormalizedFundingEventV0:
    instrument_id: str
    funding_rate: str
    funding_time: int
    source_id: str
    source_file_digest: str
    source_row_number: int
    settlement_class: str
    rate_unit: str
    interval_ms: int
    retrieval_time: str
    schema_version: str


@dataclass(frozen=True)
class ArchiveRetrievalRecordV0:
    portal_reference: str
    instrument_id: str
    month: str
    expected_data_type: str
    http_status: int
    content_type: str
    content_length: int
    sha256: str
    retrieval_time: str
    raw_provenance: str


@dataclass
class ArchiveAccessGuardV0:
    max_instruments: int
    max_months: int
    max_http_requests: int
    max_total_bytes: int
    max_runtime_seconds: int
    instruments_used: int = 0
    months_used: int = 0
    http_requests: int = 0
    total_bytes: int = 0
    start_monotonic: float = field(default_factory=time.monotonic)
    fail_reason: str = ""

    def check_runtime(self) -> str | None:
        if time.monotonic() - self.start_monotonic > self.max_runtime_seconds:
            return ArchiveAccessGuardReason.MAX_RUNTIME_SECONDS.value
        return None

    def check_request(self) -> str | None:
        if self.http_requests >= self.max_http_requests:
            return ArchiveAccessGuardReason.MAX_HTTP_REQUESTS.value
        return None

    def check_bytes(self, additional: int) -> str | None:
        if self.total_bytes + additional > self.max_total_bytes:
            return ArchiveAccessGuardReason.MAX_TOTAL_BYTES.value
        return None

    def check_instruments(self) -> str | None:
        if self.instruments_used >= self.max_instruments:
            return ArchiveAccessGuardReason.MAX_INSTRUMENTS.value
        return None

    def check_months(self) -> str | None:
        if self.months_used >= self.max_months:
            return ArchiveAccessGuardReason.MAX_MONTHS.value
        return None

    def record_request(self, byte_count: int) -> str | None:
        self.http_requests += 1
        self.total_bytes += byte_count
        for checker in (self.check_runtime, self.check_request, lambda: self.check_bytes(0)):
            reason = checker()
            if reason:
                self.fail_reason = reason
                return reason
        return None


@dataclass(frozen=True)
class ArchiveParseResultV0:
    events: tuple[NormalizedFundingEventV0, ...]
    instrument_metadata: tuple[dict[str, str], ...]
    validation_errors: tuple[str, ...]
    duplicate_keys_removed: int
    out_of_period_rows: int
    status: ArchiveIngestTerminalStatus


@dataclass(frozen=True)
class ConsumerProvenanceRecordV0:
    consumer_domain: str
    provenance_marker: str
    instrument_id: str
    funding_time: int
    funding_rate: str
    source_file_digest: str
    source_row_number: int
    join_reason: str


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_utc_ms(value: str) -> int:
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _format_utc_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_archive_cdn_url_v0(*, instrument_id: str, year: int, month: int) -> str:
    yyyymm = f"{year}{month:02d}"
    month_label = f"{year}-{month:02d}"
    return f"{CDN_BASE}/{yyyymm}/{instrument_id}-fundingrates-{month_label}.zip"


def _is_bitcoin_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return any(token in lowered for token in FORBIDDEN_INSTRUMENT_TOKENS)


def _is_spot_or_delivery(instrument_id: str) -> bool:
    upper = instrument_id.upper()
    return any(token in upper for token in SPOT_DELIVERY_SUFFIXES)


def validate_archive_csv_headers_v0(headers: Sequence[str]) -> list[str]:
    errors: list[str] = []
    header_set = {h.strip() for h in headers if h}
    missing = REQUIRED_CSV_COLUMNS - header_set
    if FUNDING_RATE_FIELD in missing:
        errors.append(ArchiveValidationErrorCode.MISSING_FUNDING_RATE.value)
    if FUNDING_TIMESTAMP_FIELD in missing:
        errors.append(ArchiveValidationErrorCode.MISSING_FUNDING_TIME.value)
    if INSTRUMENT_FIELD in missing:
        errors.append(ArchiveValidationErrorCode.MISSING_INSTRUMENT.value)
    forecast_present = header_set & FORECAST_COLUMN_NAMES
    if forecast_present:
        errors.append(ArchiveValidationErrorCode.FORECAST_COLUMN_PRESENT.value)
    return errors


def validate_archive_row_v0(
    row: Mapping[str, str],
    *,
    expected_instrument_id: str | None,
    row_number: int,
) -> list[str]:
    errors: list[str] = []
    instrument = str(row.get(INSTRUMENT_FIELD, "")).strip()
    if not instrument:
        errors.append(f"{ArchiveValidationErrorCode.MISSING_INSTRUMENT.value}:row={row_number}")
        return errors
    if expected_instrument_id is not None and instrument != expected_instrument_id:
        errors.append(f"{ArchiveValidationErrorCode.WRONG_INSTRUMENT.value}:row={row_number}")
    if _is_bitcoin_instrument(instrument):
        errors.append(f"{ArchiveValidationErrorCode.BITCOIN_INSTRUMENT.value}:row={row_number}")
    if _is_spot_or_delivery(instrument):
        errors.append(
            f"{ArchiveValidationErrorCode.SPOT_OR_DELIVERY_INSTRUMENT.value}:row={row_number}"
        )
    rate_raw = str(row.get(FUNDING_RATE_FIELD, "")).strip()
    if not rate_raw:
        errors.append(f"{ArchiveValidationErrorCode.MISSING_FUNDING_RATE.value}:row={row_number}")
    else:
        try:
            rate_val = float(rate_raw)
            if not (-1.0 <= rate_val <= 1.0):
                errors.append(
                    f"{ArchiveValidationErrorCode.INVALID_RATE_UNIT.value}:row={row_number}"
                )
        except ValueError:
            errors.append(f"{ArchiveValidationErrorCode.INVALID_RATE_UNIT.value}:row={row_number}")
    ts_raw = str(row.get(FUNDING_TIMESTAMP_FIELD, "")).strip()
    if not ts_raw:
        errors.append(f"{ArchiveValidationErrorCode.MISSING_FUNDING_TIME.value}:row={row_number}")
    else:
        try:
            ts_val = int(ts_raw)
            if ts_val <= 0:
                errors.append(
                    f"{ArchiveValidationErrorCode.INVALID_TIMESTAMP_TYPE.value}:row={row_number}"
                )
        except ValueError:
            errors.append(
                f"{ArchiveValidationErrorCode.INVALID_TIMESTAMP_TYPE.value}:row={row_number}"
            )
    return errors


def _stable_event_key(instrument_id: str, funding_time: int) -> tuple[str, int]:
    return (instrument_id, funding_time)


def deduplicate_archive_events_v0(
    events: Sequence[NormalizedFundingEventV0],
) -> tuple[tuple[NormalizedFundingEventV0, ...], int]:
    seen: dict[tuple[str, int], NormalizedFundingEventV0] = {}
    duplicates = 0
    for event in sorted(events, key=lambda item: (item.instrument_id, item.funding_time)):
        key = _stable_event_key(event.instrument_id, event.funding_time)
        if key in seen:
            duplicates += 1
            continue
        seen[key] = event
    ordered = tuple(seen[k] for k in sorted(seen))
    return ordered, duplicates


def compute_required_month_buckets_v0(
    *,
    period_start_utc: str,
    period_end_exclusive_utc: str,
    pre_window_hours: int = 5,
) -> tuple[str, ...]:
    """Return YYYY-MM month labels including adjacent months for warmup/end coverage."""
    start_ms = _parse_utc_ms(period_start_utc) - pre_window_hours * 3_600_000
    end_ms = _parse_utc_ms(period_end_exclusive_utc) + FUNDING_INTERVAL_MS

    def _month_label(ms: int) -> str:
        dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        return f"{dt.year}-{dt.month:02d}"

    months: set[str] = set()
    cursor = start_ms
    while cursor < end_ms:
        months.add(_month_label(cursor))
        dt = datetime.fromtimestamp(cursor / 1000, tz=timezone.utc)
        if dt.month == 12:
            cursor = int(datetime(dt.year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        else:
            cursor = int(datetime(dt.year, dt.month + 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    return tuple(sorted(months))


def filter_events_for_period_v0(
    events: Sequence[NormalizedFundingEventV0],
    *,
    period_start_utc: str,
    period_end_exclusive_utc: str,
    include_pre_warmup: bool = True,
) -> tuple[tuple[NormalizedFundingEventV0, ...], int]:
    start_ms = _parse_utc_ms(period_start_utc)
    end_ms = _parse_utc_ms(period_end_exclusive_utc)
    if include_pre_warmup:
        start_ms -= FUNDING_INTERVAL_MS
    kept: list[NormalizedFundingEventV0] = []
    out_of_period = 0
    for event in events:
        if event.funding_time < start_ms or event.funding_time >= end_ms:
            out_of_period += 1
            continue
        kept.append(event)
    return tuple(kept), out_of_period


def validate_funding_intervals_v0(events: Sequence[NormalizedFundingEventV0]) -> list[str]:
    errors: list[str] = []
    by_inst: dict[str, list[int]] = {}
    for event in events:
        by_inst.setdefault(event.instrument_id, []).append(event.funding_time)
    for instrument_id, timestamps in by_inst.items():
        ordered = sorted(timestamps)
        for prev, curr in zip(ordered, ordered[1:]):
            delta = curr - prev
            if delta != FUNDING_INTERVAL_MS:
                errors.append(
                    f"{ArchiveValidationErrorCode.INVALID_INTERVAL.value}:"
                    f"{instrument_id}:{_format_utc_ms(prev)}->{_format_utc_ms(curr)}"
                )
                break
    return errors


def parse_archive_csv_text_v0(
    csv_text: str,
    *,
    source_file_digest: str,
    expected_instrument_id: str | None = None,
    retrieval_time: str | None = None,
) -> ArchiveParseResultV0:
    retrieval = retrieval_time or _utc_now_iso()
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        return ArchiveParseResultV0(
            events=(),
            instrument_metadata=(),
            validation_errors=(ArchiveValidationErrorCode.EMPTY_ARCHIVE.value,),
            duplicate_keys_removed=0,
            out_of_period_rows=0,
            status=ArchiveIngestTerminalStatus.VALIDATION_FAILED,
        )
    header_errors = validate_archive_csv_headers_v0(reader.fieldnames)
    if header_errors:
        return ArchiveParseResultV0(
            events=(),
            instrument_metadata=(),
            validation_errors=tuple(header_errors),
            duplicate_keys_removed=0,
            out_of_period_rows=0,
            status=ArchiveIngestTerminalStatus.VALIDATION_FAILED,
        )

    raw_events: list[NormalizedFundingEventV0] = []
    row_errors: list[str] = []
    instruments_seen: set[str] = set()
    for row_number, row in enumerate(reader, start=2):
        row_errors.extend(
            validate_archive_row_v0(
                row, expected_instrument_id=expected_instrument_id, row_number=row_number
            )
        )
        if row_errors:
            continue
        instrument = str(row[INSTRUMENT_FIELD]).strip()
        instruments_seen.add(instrument)
        raw_events.append(
            NormalizedFundingEventV0(
                instrument_id=instrument,
                funding_rate=str(row[FUNDING_RATE_FIELD]).strip(),
                funding_time=int(str(row[FUNDING_TIMESTAMP_FIELD]).strip()),
                source_id=SOURCE_ID,
                source_file_digest=source_file_digest,
                source_row_number=row_number,
                settlement_class=SETTLEMENT_CLASS,
                rate_unit=RATE_UNIT,
                interval_ms=FUNDING_INTERVAL_MS,
                retrieval_time=retrieval,
                schema_version=SCHEMA_VERSION,
            )
        )

    if row_errors:
        return ArchiveParseResultV0(
            events=(),
            instrument_metadata=(),
            validation_errors=tuple(row_errors),
            duplicate_keys_removed=0,
            out_of_period_rows=0,
            status=ArchiveIngestTerminalStatus.VALIDATION_FAILED,
        )
    if not raw_events:
        return ArchiveParseResultV0(
            events=(),
            instrument_metadata=(),
            validation_errors=(ArchiveValidationErrorCode.EMPTY_ARCHIVE.value,),
            duplicate_keys_removed=0,
            out_of_period_rows=0,
            status=ArchiveIngestTerminalStatus.VALIDATION_FAILED,
        )

    deduped, dup_count = deduplicate_archive_events_v0(raw_events)
    interval_errors = validate_funding_intervals_v0(deduped)
    if interval_errors:
        return ArchiveParseResultV0(
            events=(),
            instrument_metadata=(),
            validation_errors=tuple(interval_errors),
            duplicate_keys_removed=dup_count,
            out_of_period_rows=0,
            status=ArchiveIngestTerminalStatus.VALIDATION_FAILED,
        )

    metadata = tuple(
        {"instrument_id": inst, "source_id": SOURCE_ID, "venue": SOURCE_VENUE}
        for inst in sorted(instruments_seen)
    )
    return ArchiveParseResultV0(
        events=deduped,
        instrument_metadata=metadata,
        validation_errors=(),
        duplicate_keys_removed=dup_count,
        out_of_period_rows=0,
        status=ArchiveIngestTerminalStatus.COMPLETE,
    )


def parse_archive_zip_bytes_v0(
    zip_bytes: bytes,
    *,
    expected_instrument_id: str | None = None,
    retrieval_time: str | None = None,
) -> ArchiveParseResultV0:
    digest = _sha256_bytes(zip_bytes)
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                return ArchiveParseResultV0(
                    events=(),
                    instrument_metadata=(),
                    validation_errors=(ArchiveValidationErrorCode.NO_CSV_IN_ZIP.value,),
                    duplicate_keys_removed=0,
                    out_of_period_rows=0,
                    status=ArchiveIngestTerminalStatus.VALIDATION_FAILED,
                )
            if len(csv_names) > 1:
                return ArchiveParseResultV0(
                    events=(),
                    instrument_metadata=(),
                    validation_errors=(ArchiveValidationErrorCode.MULTIPLE_CSV_IN_ZIP.value,),
                    duplicate_keys_removed=0,
                    out_of_period_rows=0,
                    status=ArchiveIngestTerminalStatus.VALIDATION_FAILED,
                )
            csv_text = zf.read(csv_names[0]).decode("utf-8")
    except zipfile.BadZipFile:
        return ArchiveParseResultV0(
            events=(),
            instrument_metadata=(),
            validation_errors=("BAD_ZIP",),
            duplicate_keys_removed=0,
            out_of_period_rows=0,
            status=ArchiveIngestTerminalStatus.VALIDATION_FAILED,
        )
    return parse_archive_csv_text_v0(
        csv_text,
        source_file_digest=digest,
        expected_instrument_id=expected_instrument_id,
        retrieval_time=retrieval_time,
    )


def archive_events_to_rest_compatible_rows_v0(
    events: Sequence[NormalizedFundingEventV0],
) -> list[dict[str, str]]:
    return [
        {
            "instId": event.instrument_id,
            "fundingTime": str(event.funding_time),
            "fundingRate": event.funding_rate,
        }
        for event in events
    ]


def pit_join_funding_rate_v0(
    events: Sequence[NormalizedFundingEventV0],
    decision_bar_time_ms: int,
) -> tuple[str | None, str | None]:
    """Backward-asof join: funding_time <= decision_bar_time; no future values."""
    from src.research.cross_sectional_bounded_panel_fetch_v0 import (
        backward_asof_funding_lookup_v0,
    )

    rows = archive_events_to_rest_compatible_rows_v0(events)
    rate = backward_asof_funding_lookup_v0(rows, decision_bar_time_ms)
    if is_missing_funding_value_v0(rate):
        return MISSING_FUNDING_VALUE, "MISSING_FUNDING_NO_PRIOR_SETTLEMENT"
    return str(rate), None


def build_score_input_provenance_record_v0(
    event: NormalizedFundingEventV0,
    *,
    decision_bar_time_ms: int,
) -> ConsumerProvenanceRecordV0:
    return ConsumerProvenanceRecordV0(
        consumer_domain="FUNDING_SCORE_INPUT",
        provenance_marker=score_input_provenance_marker_v0(),
        instrument_id=event.instrument_id,
        funding_time=event.funding_time,
        funding_rate=event.funding_rate,
        source_file_digest=event.source_file_digest,
        source_row_number=event.source_row_number,
        join_reason=f"score_lag_observation:funding_time_lte_{decision_bar_time_ms}",
    )


def build_cashflow_provenance_record_v0(
    event: NormalizedFundingEventV0,
    *,
    settlement_consumption_time_ms: int,
) -> ConsumerProvenanceRecordV0:
    return ConsumerProvenanceRecordV0(
        consumer_domain="FUNDING_CASHFLOW",
        provenance_marker=funding_cashflow_provenance_marker_v0(),
        instrument_id=event.instrument_id,
        funding_time=event.funding_time,
        funding_rate=event.funding_rate,
        source_file_digest=event.source_file_digest,
        source_row_number=event.source_row_number,
        join_reason=f"cashflow_settlement:{settlement_consumption_time_ms}",
    )


def check_full_panel_promotion_allowed_v0() -> tuple[bool, str]:
    if HISTORICAL_UNIVERSE_LIFECYCLE_PASS:
        return True, ""
    return False, FULL_PANEL_PROMOTION_REQUIRES_HISTORICAL_UNIVERSE_LIFECYCLE_PASS


def missing_funding_policy_contract_v0() -> dict[str, Any]:
    return {
        "missing_funding_value": MISSING_FUNDING_VALUE,
        "missing_funding_is_zero": MISSING_FUNDING_IS_ZERO,
        "missing_funding_fail_closed": MISSING_FUNDING_FAIL_CLOSED,
    }
