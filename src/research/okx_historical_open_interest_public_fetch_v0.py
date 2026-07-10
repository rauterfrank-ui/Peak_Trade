"""OKX public historical open interest fetch v0 for bounded cross-sectional panels.

Public GET only via /api/v5/rubik/stat/contracts/open-interest-history.
Research-only; no credentials, runtime, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    LOOKBACK_K,
    SIGNAL_LAG_BARS,
    SOURCE_ENDPOINT,
    SOURCE_SCHEMA_VERSION,
)
from src.research.missing_open_interest_policy_v0 import (
    MISSING_REASON_LOOKAHEAD_REJECTED,
    MISSING_REASON_NO_PRIOR_OI,
    MISSING_REASON_STALE_OBSERVATION,
    resolve_open_interest_or_missing_v0,
)

PACKAGE_MARKER = "OKX_HISTORICAL_OPEN_INTEREST_PUBLIC_FETCH_V0=true"
MODULE_VERSION = "okx_historical_open_interest_public_fetch.v0"
GO_TOKEN = "GO_BOUNDED_OKX_HISTORICAL_OPEN_INTEREST_PANEL_FETCH_PIT_SEMANTICS_REGISTRATION_AND_DATASET_MATERIALIZATION_V0"

START_INCLUSIVE_UTC = "2024-05-01T00:00:00Z"
END_EXCLUSIVE_UTC = "2024-09-01T00:00:00Z"
BAR_INTERVAL = "PT1H"
OKX_PERIOD = "1H"
PAGE_LIMIT = 100
PHASE_C_BOUND_OPEN_INTEREST_HISTORY = "BOUND_OPEN_INTEREST_HISTORY"

PublicGetFetcher = Callable[..., tuple[int, bytes, dict[str, str]]]


class OpenInterestFetchTerminalStatus(str, Enum):
    PREFLIGHT_COMPLETE = "PREFLIGHT_COMPLETE"
    HORIZON_INSUFFICIENT_FAIL_CLOSED = "HORIZON_INSUFFICIENT_FAIL_CLOSED"
    BUDGET_EXCEEDED_FAIL_CLOSED = "BUDGET_EXCEEDED_FAIL_CLOSED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    COMPLETE = "COMPLETE"


class OpenInterestHorizonReason(str, Enum):
    REQUIRED_WINDOW_COVERED = "REQUIRED_WINDOW_COVERED"
    EARLIEST_AVAILABLE_AFTER_REQUIRED_START = "EARLIEST_AVAILABLE_AFTER_REQUIRED_START"
    EMPTY_RESPONSE_FOR_REQUIRED_WINDOW = "EMPTY_RESPONSE_FOR_REQUIRED_WINDOW"


@dataclass(frozen=True)
class OpenInterestBoundedWindowV0:
    start_inclusive_utc: str
    end_exclusive_utc: str
    start_ms: int
    end_exclusive_ms: int
    window_hours: int
    required_pre_window_hours: int
    oi_fetch_start_utc: str
    oi_fetch_start_ms: int


@dataclass
class OpenInterestFetchBudgetGuardV0:
    max_instruments: int
    max_pages_per_instrument: int
    max_total_requests: int
    max_total_raw_bytes: int
    max_runtime_seconds: int
    max_consecutive_empty_pages: int = 3
    instruments_completed: int = 0
    current_instrument_pages: int = 0
    total_requests: int = 0
    total_raw_bytes: int = 0
    retained_pages: int = 0
    discarded_pages: int = 0
    start_monotonic: float = field(default_factory=time.monotonic)
    fail_reason: str = ""

    def check_runtime(self) -> str | None:
        if time.monotonic() - self.start_monotonic > self.max_runtime_seconds:
            return "MAX_RUNTIME_SECONDS"
        return None

    def check_request(self) -> str | None:
        if self.total_requests >= self.max_total_requests:
            return "MAX_TOTAL_REQUESTS"
        return None

    def check_instrument_pages(self, next_page_count: int) -> str | None:
        if next_page_count > self.max_pages_per_instrument:
            return "MAX_PAGES_PER_INSTRUMENT"
        return None

    def check_raw_bytes(self, additional: int) -> str | None:
        if self.total_raw_bytes + additional > self.max_total_raw_bytes:
            return "MAX_TOTAL_RAW_BYTES"
        return None


@dataclass(frozen=True)
class NormalizedOpenInterestObservationV0:
    instrument_id: str
    native_instrument_id: str
    observation_time_ms: int
    observation_time_utc: str
    open_interest_raw: str
    open_interest_unit: str
    source_schema_version: str
    source_record_key: str


@dataclass(frozen=True)
class OpenInterestHorizonAssessmentV0:
    required_start_utc: str
    required_end_exclusive_utc: str
    earliest_available_utc: str | None
    latest_available_utc: str | None
    horizon_covers_required_window: bool
    reason: OpenInterestHorizonReason
    probe_instrument_id: str


def _parse_utc_ms(value: str) -> int:
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _format_utc_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_open_interest_bounded_window_v0(
    *,
    start_inclusive_utc: str = START_INCLUSIVE_UTC,
    end_exclusive_utc: str = END_EXCLUSIVE_UTC,
    lookback_k: int = LOOKBACK_K,
    signal_lag_bars: int = SIGNAL_LAG_BARS,
) -> OpenInterestBoundedWindowV0:
    start_ms = _parse_utc_ms(start_inclusive_utc)
    end_ms = _parse_utc_ms(end_exclusive_utc)
    window_hours = (end_ms - start_ms) // 3_600_000
    pre_hours = lookback_k + signal_lag_bars
    fetch_start_ms = start_ms - pre_hours * 3_600_000
    return OpenInterestBoundedWindowV0(
        start_inclusive_utc=start_inclusive_utc,
        end_exclusive_utc=end_exclusive_utc,
        start_ms=start_ms,
        end_exclusive_ms=end_ms,
        window_hours=window_hours,
        required_pre_window_hours=pre_hours,
        oi_fetch_start_utc=_format_utc_ms(fetch_start_ms),
        oi_fetch_start_ms=fetch_start_ms,
    )


def parse_okx_open_interest_history_row_v0(
    row: Sequence[Any],
    *,
    instrument_id: str,
    native_instrument_id: str,
) -> NormalizedOpenInterestObservationV0 | None:
    if not row or len(row) < 2:
        return None
    ts = int(str(row[0]))
    oi_raw = str(row[1])
    if not oi_raw.strip():
        return None
    return NormalizedOpenInterestObservationV0(
        instrument_id=instrument_id,
        native_instrument_id=native_instrument_id,
        observation_time_ms=ts,
        observation_time_utc=_format_utc_ms(ts),
        open_interest_raw=oi_raw,
        open_interest_unit="okx_native_contract_count",
        source_schema_version=SOURCE_SCHEMA_VERSION,
        source_record_key=f"{native_instrument_id}:{ts}",
    )


def deduplicate_open_interest_observations_v0(
    observations: Sequence[NormalizedOpenInterestObservationV0],
) -> tuple[NormalizedOpenInterestObservationV0, ...]:
    dedup: dict[int, NormalizedOpenInterestObservationV0] = {}
    for obs in observations:
        dedup[obs.observation_time_ms] = obs
    return tuple(dedup[k] for k in sorted(dedup))


def backward_asof_open_interest_lookup_v0(
    observations: Sequence[NormalizedOpenInterestObservationV0],
    bar_timestamp_ms: int,
) -> NormalizedOpenInterestObservationV0 | None:
    chosen: NormalizedOpenInterestObservationV0 | None = None
    chosen_ts = -1
    for obs in observations:
        if obs.observation_time_ms <= bar_timestamp_ms and obs.observation_time_ms >= chosen_ts:
            chosen = obs
            chosen_ts = obs.observation_time_ms
    return chosen


def compute_availability_time_utc_v0(
    observation_time_utc: str,
    *,
    signal_lag_bars: int = SIGNAL_LAG_BARS,
) -> str:
    obs_ms = _parse_utc_ms(observation_time_utc)
    avail_ms = obs_ms + signal_lag_bars * 3_600_000
    return _format_utc_ms(avail_ms)


def classify_open_interest_for_bar_v0(
    *,
    observation: NormalizedOpenInterestObservationV0 | None,
    bar_timestamp_ms: int,
    bar_timestamp_utc: str,
    stale_threshold_bars: int = 1,
) -> tuple[str | None, str, bool, bool, str | None]:
    if observation is None:
        return None, "MISSING", True, True, MISSING_REASON_NO_PRIOR_OI
    if observation.observation_time_ms > bar_timestamp_ms:
        return None, "LOOKAHEAD_REJECTED", False, True, MISSING_REASON_LOOKAHEAD_REJECTED
    staleness_ms = bar_timestamp_ms - observation.observation_time_ms
    stale = staleness_ms > stale_threshold_bars * 3_600_000
    if stale:
        return (
            resolve_open_interest_or_missing_v0(raw_value=observation.open_interest_raw),
            "STALE",
            True,
            False,
            MISSING_REASON_STALE_OBSERVATION,
        )
    return (
        resolve_open_interest_or_missing_v0(raw_value=observation.open_interest_raw),
        "OK",
        False,
        False,
        None,
    )


def paginate_bounded_open_interest_v0(
    *,
    instrument_id: str,
    native_instrument_id: str,
    window: OpenInterestBoundedWindowV0,
    fetcher: PublicGetFetcher,
    rate_limiter: Callable[[], None],
    fetch_with_retry: Callable[..., tuple[int, bytes, dict[str, str]]],
    build_url: Callable[[str, dict[str, str]], str],
    parse_json: Callable[[bytes], dict[str, Any]],
    raw_dir: Path,
    budget: OpenInterestFetchBudgetGuardV0,
) -> tuple[list[NormalizedOpenInterestObservationV0], str | None]:
    path = SOURCE_ENDPOINT
    params_base = {"instId": native_instrument_id, "period": OKX_PERIOD}
    all_obs: list[NormalizedOpenInterestObservationV0] = []
    end_cursor: str | None = str(window.end_exclusive_ms)
    page = 0
    consecutive_empty = 0
    fail_reason: str | None = None
    fetch_start = window.oi_fetch_start_ms
    fetch_end = window.end_exclusive_ms

    while True:
        runtime_reason = budget.check_runtime()
        if runtime_reason:
            fail_reason = runtime_reason
            break
        req_reason = budget.check_request()
        if req_reason:
            fail_reason = req_reason
            break
        page_reason = budget.check_instrument_pages(budget.current_instrument_pages + 1)
        if page_reason:
            fail_reason = page_reason
            break

        params = dict(params_base)
        params["limit"] = str(PAGE_LIMIT)
        if end_cursor is not None:
            params["end"] = end_cursor
        url = build_url(path, params)
        budget.total_requests += 1
        budget.current_instrument_pages += 1
        status, body, _ = fetch_with_retry(
            url,
            timeout_seconds=30.0,
            max_response_bytes=50_000_000,
            rate_limiter=rate_limiter,
            fetcher=fetcher,
        )
        digest = _sha256_bytes(body)
        bytes_reason = budget.check_raw_bytes(len(body))
        if bytes_reason:
            fail_reason = bytes_reason
            break

        payload = parse_json(body)
        rows = payload.get("data") or []
        if not isinstance(rows, list):
            rows = []
        ts_values: list[int] = []
        dict_rows: list[list[Any]] = []
        for row in rows:
            if isinstance(row, list) and row:
                dict_rows.append(row)
                ts_values.append(int(str(row[0])))
        overlap = bool(ts_values) and max(ts_values) >= fetch_start and min(ts_values) < fetch_end
        min_ts = min(ts_values) if ts_values else None
        max_ts = max(ts_values) if ts_values else None

        if overlap:
            raw_name = f"{instrument_id}_open_interest_{page}_{min_ts}_{max_ts}_{digest[:16]}.json"
            raw_path = raw_dir / raw_name
            raw_dir.mkdir(parents=True, exist_ok=True)
            raw_path.write_bytes(body)
            budget.total_raw_bytes += len(body)
            budget.retained_pages += 1
        else:
            budget.discarded_pages += 1

        if status < 200 or status >= 300 or str(payload.get("code", "")) != "0":
            fail_reason = f"OPEN_INTEREST_HTTP_OR_OKX_ERROR:{status}"
            break
        if not rows:
            consecutive_empty += 1
            if consecutive_empty >= budget.max_consecutive_empty_pages:
                break
            break

        consecutive_empty = 0
        for row in dict_rows:
            parsed = parse_okx_open_interest_history_row_v0(
                row,
                instrument_id=instrument_id,
                native_instrument_id=native_instrument_id,
            )
            if parsed is None:
                continue
            if fetch_start <= parsed.observation_time_ms < fetch_end:
                all_obs.append(parsed)

        if not ts_values:
            break
        oldest = min(ts_values)
        if oldest <= fetch_start:
            break
        if len(rows) < PAGE_LIMIT:
            break
        end_cursor = str(oldest)
        page += 1

    deduped = deduplicate_open_interest_observations_v0(all_obs)
    return list(deduped), fail_reason


def assess_open_interest_horizon_v0(
    observations: Sequence[NormalizedOpenInterestObservationV0],
    *,
    window: OpenInterestBoundedWindowV0,
    probe_instrument_id: str,
) -> OpenInterestHorizonAssessmentV0:
    if not observations:
        return OpenInterestHorizonAssessmentV0(
            required_start_utc=window.oi_fetch_start_utc,
            required_end_exclusive_utc=window.end_exclusive_utc,
            earliest_available_utc=None,
            latest_available_utc=None,
            horizon_covers_required_window=False,
            reason=OpenInterestHorizonReason.EMPTY_RESPONSE_FOR_REQUIRED_WINDOW,
            probe_instrument_id=probe_instrument_id,
        )
    earliest_ms = min(o.observation_time_ms for o in observations)
    latest_ms = max(o.observation_time_ms for o in observations)
    earliest_utc = _format_utc_ms(earliest_ms)
    latest_utc = _format_utc_ms(latest_ms)
    covers = earliest_ms <= window.oi_fetch_start_ms
    reason = (
        OpenInterestHorizonReason.REQUIRED_WINDOW_COVERED
        if covers
        else OpenInterestHorizonReason.EARLIEST_AVAILABLE_AFTER_REQUIRED_START
    )
    return OpenInterestHorizonAssessmentV0(
        required_start_utc=window.oi_fetch_start_utc,
        required_end_exclusive_utc=window.end_exclusive_utc,
        earliest_available_utc=earliest_utc,
        latest_available_utc=latest_utc,
        horizon_covers_required_window=covers,
        reason=reason,
        probe_instrument_id=probe_instrument_id,
    )


def horizon_assessment_to_dict(assessment: OpenInterestHorizonAssessmentV0) -> dict[str, Any]:
    return {
        "required_start_utc": assessment.required_start_utc,
        "required_end_exclusive_utc": assessment.required_end_exclusive_utc,
        "earliest_available_utc": assessment.earliest_available_utc,
        "latest_available_utc": assessment.latest_available_utc,
        "horizon_covers_required_window": assessment.horizon_covers_required_window,
        "reason": assessment.reason.value,
        "probe_instrument_id": assessment.probe_instrument_id,
    }
