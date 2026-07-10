"""Bounded cross-sectional panel OHLCV and funding fetch v0.

Anchors pagination at END_EXCLUSIVE, retains only window-overlapping raw pages,
enforces budget guards, and performs PIT backward-asof funding join.
Research-only; no runtime, orders, or authority effect.
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

from src.research.cross_sectional_funding_rate_delta_momentum_scoring_v0 import (
    FUNDING_DELTA_LOOKBACK_K,
    FUNDING_SIGNAL_LAG,
    funding_cashflow_provenance_marker_v0,
    score_input_provenance_marker_v0,
)
from src.research.okx_production_instrument_lifecycle_source_v1 import (
    evaluate_okx_instrument_eligibility_v1,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_BOUNDED_PANEL_FETCH_V0=true"
MODULE_VERSION = "cross_sectional_bounded_panel_fetch.v0"

START_INCLUSIVE_UTC = "2024-05-01T00:00:00Z"
END_EXCLUSIVE_UTC = "2024-09-01T00:00:00Z"
BAR_INTERVAL = "PT1H"
PAGE_LIMIT = 300

PHASE_A_BOUND_OHLCV_PANEL = "BOUND_OHLCV_PANEL"
PHASE_B_BOUND_FUNDING_HISTORY = "BOUND_FUNDING_HISTORY"
PHASE_C_BOUND_OPEN_INTEREST_HISTORY = "BOUND_OPEN_INTEREST_HISTORY"

GO_TOKEN = (
    "GO_BOUNDED_CROSS_SECTIONAL_FUNDING_PANEL_FETCH_PAGINATION_RETENTION_AND_BUDGET_RECOVERY_V0"
)

PublicGetFetcher = Callable[..., tuple[int, bytes, dict[str, str]]]


class FetchTerminalStatus(str, Enum):
    PREFLIGHT_COMPLETE = "PREFLIGHT_COMPLETE"
    BUDGET_EXCEEDED_FAIL_CLOSED = "BUDGET_EXCEEDED_FAIL_CLOSED"
    INCOMPLETE_NOT_PROMOTED = "INCOMPLETE_NOT_PROMOTED"
    VALIDATION_FAILED = "VALIDATION_FAILED"


class BudgetGuardReason(str, Enum):
    MAX_INSTRUMENTS = "MAX_INSTRUMENTS"
    MAX_PAGES_PER_INSTRUMENT = "MAX_PAGES_PER_INSTRUMENT"
    MAX_TOTAL_REQUESTS = "MAX_TOTAL_REQUESTS"
    MAX_TOTAL_RAW_BYTES = "MAX_TOTAL_RAW_BYTES"
    MAX_RUNTIME_SECONDS = "MAX_RUNTIME_SECONDS"
    MAX_CONSECUTIVE_EMPTY_PAGES = "MAX_CONSECUTIVE_EMPTY_PAGES"


@dataclass(frozen=True)
class BoundedWindowV0:
    start_inclusive_utc: str
    end_exclusive_utc: str
    start_ms: int
    end_exclusive_ms: int
    window_hours: int
    required_pre_window_hours: int
    funding_fetch_start_utc: str
    funding_fetch_start_ms: int

    @property
    def fetch_end_exclusive_utc(self) -> str:
        return self.end_exclusive_utc

    @property
    def fetch_end_exclusive_ms(self) -> int:
        return self.end_exclusive_ms


def _parse_utc_ms(value: str) -> int:
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _format_utc_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_bounded_window_v0(
    *,
    start_inclusive_utc: str = START_INCLUSIVE_UTC,
    end_exclusive_utc: str = END_EXCLUSIVE_UTC,
    funding_delta_lookback_k: int = FUNDING_DELTA_LOOKBACK_K,
    funding_signal_lag: int = FUNDING_SIGNAL_LAG,
) -> BoundedWindowV0:
    start_ms = _parse_utc_ms(start_inclusive_utc)
    end_ms = _parse_utc_ms(end_exclusive_utc)
    window_hours = (end_ms - start_ms) // 3_600_000
    pre_hours = funding_delta_lookback_k + funding_signal_lag
    funding_start_ms = start_ms - pre_hours * 3_600_000
    return BoundedWindowV0(
        start_inclusive_utc=start_inclusive_utc,
        end_exclusive_utc=end_exclusive_utc,
        start_ms=start_ms,
        end_exclusive_ms=end_ms,
        window_hours=window_hours,
        required_pre_window_hours=pre_hours,
        funding_fetch_start_utc=_format_utc_ms(funding_start_ms),
        funding_fetch_start_ms=funding_start_ms,
    )


def derive_production_budget_v0(window: BoundedWindowV0) -> dict[str, int]:
    ohlcv_pages = (window.window_hours + PAGE_LIMIT - 1) // PAGE_LIMIT + 2
    funding_span_hours = window.window_hours + window.required_pre_window_hours
    funding_pages = (funding_span_hours + PAGE_LIMIT - 1) // PAGE_LIMIT + 2
    max_pages_per_instrument = ohlcv_pages + funding_pages
    return {
        "max_pages_per_instrument_ohlcv": ohlcv_pages,
        "max_pages_per_instrument_funding": funding_pages,
        "max_pages_per_instrument": max_pages_per_instrument,
        "max_total_requests_per_instrument": max_pages_per_instrument,
    }


@dataclass
class FetchBudgetGuardV0:
    max_instruments: int
    max_pages_per_instrument: int
    max_total_requests: int
    max_total_raw_bytes: int
    max_runtime_seconds: int
    max_consecutive_empty_pages: int = 3
    max_retries: int = 5
    instruments_completed: int = 0
    current_instrument_pages: int = 0
    total_requests: int = 0
    total_raw_bytes: int = 0
    retained_pages: int = 0
    discarded_pages: int = 0
    start_monotonic: float = field(default_factory=time.monotonic)

    def check_runtime(self) -> str | None:
        if time.monotonic() - self.start_monotonic > self.max_runtime_seconds:
            return BudgetGuardReason.MAX_RUNTIME_SECONDS.value
        return None

    def check_request(self) -> str | None:
        if self.total_requests >= self.max_total_requests:
            return BudgetGuardReason.MAX_TOTAL_REQUESTS.value
        return None

    def check_raw_bytes(self, additional: int) -> str | None:
        if self.total_raw_bytes + additional > self.max_total_raw_bytes:
            return BudgetGuardReason.MAX_TOTAL_RAW_BYTES.value
        return None

    def check_instrument_pages(self, pages: int | None = None) -> str | None:
        count = self.current_instrument_pages if pages is None else pages
        if count > self.max_pages_per_instrument:
            return BudgetGuardReason.MAX_PAGES_PER_INSTRUMENT.value
        return None

    def begin_instrument(self) -> None:
        self.current_instrument_pages = 0

    def complete_instrument(self) -> None:
        self.instruments_completed += 1
        self.current_instrument_pages = 0

    def check_instruments(self) -> str | None:
        if self.instruments_completed >= self.max_instruments:
            return BudgetGuardReason.MAX_INSTRUMENTS.value
        return None


@dataclass(frozen=True)
class PaginationPageRecordV0:
    phase: str
    instrument_id: str
    page_sequence: int
    query_params: dict[str, str]
    min_timestamp_ms: int | None
    max_timestamp_ms: int | None
    overlap_with_window: bool
    retained: bool
    raw_path: str
    content_digest: str
    row_count_in_window: int
    http_status: int
    discarded_reason: str = ""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _candle_is_final(row: Sequence[Any]) -> bool:
    if len(row) >= 9:
        return str(row[8]) == "1"
    if len(row) >= 6:
        return str(row[5]) == "1"
    return False


def _row_in_window(ts_ms: int, window: BoundedWindowV0) -> bool:
    return window.start_ms <= ts_ms < window.end_exclusive_ms


def _page_overlaps_window(
    timestamps_ms: Sequence[int],
    window: BoundedWindowV0,
) -> bool:
    if not timestamps_ms:
        return False
    page_min = min(timestamps_ms)
    page_max = max(timestamps_ms)
    return page_max >= window.start_ms and page_min < window.end_exclusive_ms


def _safe_instrument_token(instrument_id: str) -> str:
    return instrument_id.replace(":", "_").replace("/", "_")


def _raw_filename_v0(
    *,
    instrument_id: str,
    data_type: str,
    page_sequence: int,
    min_ts_ms: int | None,
    max_ts_ms: int | None,
    digest: str,
) -> str:
    min_part = str(min_ts_ms) if min_ts_ms is not None else "none"
    max_part = str(max_ts_ms) if max_ts_ms is not None else "none"
    return (
        f"{_safe_instrument_token(instrument_id)}_{data_type}_p{page_sequence:04d}_"
        f"{min_part}_{max_part}_{digest[:16]}.json"
    )


def paginate_bounded_ohlcv_v0(
    *,
    instrument_id: str,
    native_instrument_id: str,
    window: BoundedWindowV0,
    fetcher: PublicGetFetcher,
    rate_limiter: Any,
    fetch_with_retry: Callable[..., tuple[int, bytes, dict[str, str]]],
    build_url: Callable[[str, Mapping[str, str]], str],
    parse_json: Callable[[bytes], dict[str, Any]],
    raw_dir: Path,
    request_log: list[PaginationPageRecordV0],
    budget: FetchBudgetGuardV0,
    okx_bar_param: str = "1H",
) -> tuple[list[list[Any]], str | None]:
    path = "/api/v5/market/history-candles"
    params_base = {"instId": native_instrument_id, "bar": okx_bar_param}
    all_rows: list[list[Any]] = []
    after_cursor: str | None = str(window.end_exclusive_ms)
    page = 0
    consecutive_empty = 0
    fail_reason: str | None = None

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
        params["after"] = after_cursor
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
        finalized = [r for r in rows if isinstance(r, list) and _candle_is_final(r)]
        ts_values = [int(str(r[0])) for r in finalized] if finalized else []
        overlap = _page_overlaps_window(ts_values, window)
        in_window_count = sum(1 for ts in ts_values if _row_in_window(ts, window))
        min_ts = min(ts_values) if ts_values else None
        max_ts = max(ts_values) if ts_values else None

        raw_path = ""
        retained = False
        discarded_reason = ""
        if overlap:
            raw_name = _raw_filename_v0(
                instrument_id=instrument_id,
                data_type="ohlcv",
                page_sequence=page,
                min_ts_ms=min_ts,
                max_ts_ms=max_ts,
                digest=digest,
            )
            raw_path = str(raw_dir / raw_name)
            raw_dir.mkdir(parents=True, exist_ok=True)
            Path(raw_path).write_bytes(body)
            budget.total_raw_bytes += len(body)
            budget.retained_pages += 1
            retained = True
        else:
            budget.discarded_pages += 1
            discarded_reason = "PAGE_FULLY_OUTSIDE_BOUND_WINDOW"

        request_log.append(
            PaginationPageRecordV0(
                phase=PHASE_A_BOUND_OHLCV_PANEL,
                instrument_id=instrument_id,
                page_sequence=page,
                query_params=dict(params),
                min_timestamp_ms=min_ts,
                max_timestamp_ms=max_ts,
                overlap_with_window=overlap,
                retained=retained,
                raw_path=raw_path,
                content_digest=digest,
                row_count_in_window=in_window_count,
                http_status=status,
                discarded_reason=discarded_reason,
            )
        )

        if status < 200 or status >= 300 or str(payload.get("code", "")) != "0":
            fail_reason = f"OHLCV_HTTP_OR_OKX_ERROR:{status}"
            break
        if not rows:
            consecutive_empty += 1
            if consecutive_empty >= budget.max_consecutive_empty_pages:
                fail_reason = BudgetGuardReason.MAX_CONSECUTIVE_EMPTY_PAGES.value
                break
            break

        consecutive_empty = 0
        for row in finalized:
            ts = int(str(row[0]))
            if _row_in_window(ts, window):
                all_rows.append(row)

        if not ts_values:
            break
        oldest = min(ts_values)
        if oldest <= window.start_ms:
            break
        if len(rows) < PAGE_LIMIT:
            break
        before_cursor = str(oldest)
        after_cursor = before_cursor
        page += 1

    dedup: dict[int, list[Any]] = {}
    for row in all_rows:
        dedup[int(str(row[0]))] = row
    return [dedup[k] for k in sorted(dedup)], fail_reason


def paginate_bounded_funding_v0(
    *,
    instrument_id: str,
    native_instrument_id: str,
    window: BoundedWindowV0,
    fetcher: PublicGetFetcher,
    rate_limiter: Any,
    fetch_with_retry: Callable[..., tuple[int, bytes, dict[str, str]]],
    build_url: Callable[[str, Mapping[str, str]], str],
    parse_json: Callable[[bytes], dict[str, Any]],
    raw_dir: Path,
    request_log: list[PaginationPageRecordV0],
    budget: FetchBudgetGuardV0,
) -> tuple[list[dict[str, Any]], str | None]:
    path = "/api/v5/public/funding-rate-history"
    params_base = {"instId": native_instrument_id}
    all_rows: list[dict[str, Any]] = []
    after_cursor: str | None = str(window.end_exclusive_ms)
    use_head_fallback = False
    page = 0
    consecutive_empty = 0
    fail_reason: str | None = None
    fetch_start = window.funding_fetch_start_ms
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
        if after_cursor is not None:
            params["after"] = after_cursor
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
        dict_rows = [dict(r) for r in rows if isinstance(r, Mapping)]
        ts_values = [int(str(r.get("fundingTime", "0"))) for r in dict_rows] if dict_rows else []
        overlap = _page_overlaps_window(ts_values, window) if ts_values else False
        if ts_values:
            overlap = max(ts_values) >= fetch_start and min(ts_values) < fetch_end
        in_window_count = sum(1 for ts in ts_values if fetch_start <= ts < fetch_end)
        min_ts = min(ts_values) if ts_values else None
        max_ts = max(ts_values) if ts_values else None

        raw_path = ""
        retained = False
        discarded_reason = ""
        if overlap:
            raw_name = _raw_filename_v0(
                instrument_id=instrument_id,
                data_type="funding",
                page_sequence=page,
                min_ts_ms=min_ts,
                max_ts_ms=max_ts,
                digest=digest,
            )
            raw_path = str(raw_dir / raw_name)
            raw_dir.mkdir(parents=True, exist_ok=True)
            Path(raw_path).write_bytes(body)
            budget.total_raw_bytes += len(body)
            budget.retained_pages += 1
            retained = True
        else:
            budget.discarded_pages += 1
            discarded_reason = "PAGE_FULLY_OUTSIDE_FETCH_BOUNDS"

        request_log.append(
            PaginationPageRecordV0(
                phase=PHASE_B_BOUND_FUNDING_HISTORY,
                instrument_id=instrument_id,
                page_sequence=page,
                query_params=dict(params),
                min_timestamp_ms=min_ts,
                max_timestamp_ms=max_ts,
                overlap_with_window=overlap,
                retained=retained,
                raw_path=raw_path,
                content_digest=digest,
                row_count_in_window=in_window_count,
                http_status=status,
                discarded_reason=discarded_reason,
            )
        )

        if status < 200 or status >= 300 or str(payload.get("code", "")) != "0":
            fail_reason = f"FUNDING_HTTP_OR_OKX_ERROR:{status}"
            break
        if not rows:
            if after_cursor is not None and not use_head_fallback:
                use_head_fallback = True
                after_cursor = None
                continue
            consecutive_empty += 1
            if consecutive_empty >= budget.max_consecutive_empty_pages:
                fail_reason = BudgetGuardReason.MAX_CONSECUTIVE_EMPTY_PAGES.value
                break
            break

        consecutive_empty = 0
        for row in dict_rows:
            ts = int(str(row.get("fundingTime", "0")))
            if fetch_start <= ts < fetch_end:
                all_rows.append(row)

        if not ts_values:
            break
        oldest = min(ts_values)
        if oldest <= fetch_start:
            break
        if len(rows) < PAGE_LIMIT:
            break
        after_cursor = str(oldest)
        page += 1

    dedup: dict[int, dict[str, Any]] = {}
    for row in all_rows:
        dedup[int(str(row["fundingTime"]))] = row
    return [dedup[k] for k in sorted(dedup)], fail_reason


def backward_asof_funding_lookup_v0(
    funding_rows: Sequence[Mapping[str, Any]],
    bar_timestamp_ms: int,
) -> str | None:
    """Return latest funding rate with fundingTime <= bar_timestamp_ms, else None."""
    chosen: Mapping[str, Any] | None = None
    chosen_ts = -1
    for row in funding_rows:
        ts = int(str(row.get("fundingTime", "0")))
        if ts <= bar_timestamp_ms and ts >= chosen_ts:
            chosen = row
            chosen_ts = ts
    if chosen is None:
        return None
    return str(chosen.get("fundingRate", ""))


def attach_funding_to_ohlcv_bars_v0(
    *,
    instrument_id: str,
    ohlcv_rows: Sequence[Sequence[Any]],
    funding_rows: Sequence[Mapping[str, Any]],
    window: BoundedWindowV0,
) -> tuple[list[dict[str, Any]], list[str]]:
    """PIT backward-asof join; missing funding stays explicit None."""
    missing_reasons: list[str] = []
    output: list[dict[str, Any]] = []
    for row in ohlcv_rows:
        ts = int(str(row[0]))
        if not _row_in_window(ts, window):
            continue
        funding_rate = backward_asof_funding_lookup_v0(funding_rows, ts)
        if funding_rate is None:
            missing_reasons.append(f"missing_funding_at:{_format_utc_ms(ts)}")
        output.append(
            {
                "instrument_id": instrument_id,
                "timestamp_utc": _format_utc_ms(ts),
                "open": str(row[1]),
                "high": str(row[2]),
                "low": str(row[3]),
                "close": str(row[4]),
                "volume": str(row[5]),
                "funding_rate": funding_rate,
                "score_input_provenance": score_input_provenance_marker_v0(),
                "funding_cashflow_provenance": funding_cashflow_provenance_marker_v0(),
                "is_final": _candle_is_final(row),
            }
        )
    return output, missing_reasons


def select_eligible_instruments_v0(
    instruments: Sequence[Mapping[str, Any]],
    *,
    max_instruments: int | None = None,
    listed_before_ms: int | None = None,
) -> list[tuple[str, str]]:
    eligible: list[tuple[str, str]] = []
    for inst in instruments:
        result = evaluate_okx_instrument_eligibility_v1(inst)
        if not result.eligible or result.instrument_id is None or result.metadata is None:
            continue
        if listed_before_ms is not None:
            list_ms = _parse_utc_ms(result.metadata.list_time_utc)
            if list_ms > listed_before_ms:
                continue
        eligible.append((result.instrument_id, result.metadata.inst_id))
    eligible.sort(key=lambda item: item[0])
    if max_instruments is not None:
        eligible = eligible[:max_instruments]
    return eligible


def first_ohlcv_request_anchored_at_end_exclusive(
    request_log: Sequence[PaginationPageRecordV0],
    window: BoundedWindowV0,
) -> bool:
    ohlcv_pages = [r for r in request_log if r.phase == PHASE_A_BOUND_OHLCV_PANEL]
    if not ohlcv_pages:
        return False
    first = min(ohlcv_pages, key=lambda r: (r.instrument_id, r.page_sequence))
    before_val = first.query_params.get("after")
    return before_val == str(window.end_exclusive_ms)


def out_of_window_retained_raw_count(raw_dir: Path) -> int:
    count = 0
    if not raw_dir.is_dir():
        return 0
    for path in raw_dir.glob("*.json"):
        parts = path.stem.split("_")
        if len(parts) < 6:
            continue
        try:
            min_ts = int(parts[-3])
            max_ts = int(parts[-2])
        except ValueError:
            continue
        window = compute_bounded_window_v0()
        if max_ts < window.start_ms or min_ts >= window.end_exclusive_ms:
            count += 1
    return count


def _load_okx_ingest_helpers() -> tuple[Any, Any, Any, Any, Any]:
    import importlib.util
    import sys
    from pathlib import Path as _Path

    repo_root = _Path(__file__).resolve().parents[2]
    mat_script = repo_root / "scripts/ops/materialize_okx_production_lifecycle_and_pt1h_panel_v1.py"
    mat_spec = importlib.util.spec_from_file_location("mat_okx_bounded_fetch", mat_script)
    assert mat_spec is not None and mat_spec.loader is not None
    mat_mod = importlib.util.module_from_spec(mat_spec)
    sys.modules[mat_spec.name] = mat_mod
    mat_spec.loader.exec_module(mat_mod)
    ingest_mod = mat_mod._load_okx_ingest_module()
    return (
        ingest_mod,
        mat_mod,
        ingest_mod.okx_public_fetch_v1,
        ingest_mod.RateLimiter,
        ingest_mod.fetch_with_retry,
    )


def _progress_log(payload: Mapping[str, Any]) -> None:
    print(json.dumps({"progress": dict(payload)}, sort_keys=True), flush=True)


@dataclass(frozen=True)
class BoundedPreflightResultV0:
    status: FetchTerminalStatus
    staging_root: str
    instrument_count: int
    ohlcv_raw_files: int
    funding_raw_files: int
    out_of_window_raw_files: int
    total_requests: int
    total_raw_bytes: int
    runtime_seconds: float
    fail_reason: str
    request_log_count: int
    manifest_verify_rc: int
    promoted: bool


def run_bounded_panel_preflight_v0(
    *,
    confirm: str,
    staging_root: Path,
    max_instruments: int = 2,
    preflight_only: bool = True,
) -> BoundedPreflightResultV0:
    if confirm != GO_TOKEN:
        raise ValueError(f"GO_TOKEN_REQUIRED:{GO_TOKEN}")

    if staging_root.exists():
        raise ValueError(f"STAGING_ROOT_EXISTS:{staging_root}")

    window = compute_bounded_window_v0()
    derived = derive_production_budget_v0(window)
    budget = FetchBudgetGuardV0(
        max_instruments=max_instruments,
        max_pages_per_instrument=derived["max_pages_per_instrument"],
        max_total_requests=max(
            derived["max_total_requests_per_instrument"] * max_instruments + 10, 20
        ),
        max_total_raw_bytes=50_000_000,
        max_runtime_seconds=300,
    )

    ingest_mod, mat_mod, fetcher, rate_limiter_cls, fetch_with_retry = _load_okx_ingest_helpers()
    rate_limiter = rate_limiter_cls()

    staging_root.mkdir(parents=True, exist_ok=False)
    raw_ohlcv_dir = staging_root / "raw" / "ohlcv"
    raw_funding_dir = staging_root / "raw" / "funding"
    panel_dir = staging_root / "panel"
    reports_dir = staging_root / "reports"
    for path in (raw_ohlcv_dir, raw_funding_dir, panel_dir, reports_dir):
        path.mkdir(parents=True, exist_ok=True)

    request_log: list[PaginationPageRecordV0] = []
    all_panel_bars: list[dict[str, Any]] = []
    missing_report: dict[str, list[str]] = {}
    fail_reason = ""
    status = FetchTerminalStatus.PREFLIGHT_COMPLETE

    raw_dir_tmp = staging_root / "raw"
    instruments_payload = mat_mod.fetch_all_swap_instruments(
        ingest_mod,
        fetcher=fetcher,
        rate_limiter=rate_limiter,
        timeout_seconds=30.0,
        max_response_bytes=50_000_000,
        raw_dir=raw_dir_tmp,
    )
    eligible = select_eligible_instruments_v0(
        instruments_payload,
        max_instruments=max_instruments,
        listed_before_ms=window.start_ms,
    )
    if len(eligible) < max_instruments:
        fail_reason = "INSUFFICIENT_ELIGIBLE_INSTRUMENTS"
        status = FetchTerminalStatus.VALIDATION_FAILED

    for instrument_id, native_id in eligible:
        inst_reason = budget.check_instruments()
        if inst_reason:
            fail_reason = inst_reason
            status = FetchTerminalStatus.BUDGET_EXCEEDED_FAIL_CLOSED
            break
        budget.begin_instrument()
        _progress_log(
            {
                "elapsed_seconds": round(time.monotonic() - budget.start_monotonic, 2),
                "instruments_completed": budget.instruments_completed,
                "instruments_total": max_instruments,
                "current_instrument": instrument_id,
                "phase": PHASE_A_BOUND_OHLCV_PANEL,
            }
        )
        ohlcv_rows, ohlcv_fail = paginate_bounded_ohlcv_v0(
            instrument_id=instrument_id,
            native_instrument_id=native_id,
            window=window,
            fetcher=fetcher,
            rate_limiter=rate_limiter,
            fetch_with_retry=fetch_with_retry,
            build_url=ingest_mod._build_url,
            parse_json=ingest_mod._parse_okx_json,
            raw_dir=raw_ohlcv_dir,
            request_log=request_log,
            budget=budget,
        )
        if ohlcv_fail:
            fail_reason = ohlcv_fail
            status = FetchTerminalStatus.BUDGET_EXCEEDED_FAIL_CLOSED
            break

        _progress_log(
            {
                "elapsed_seconds": round(time.monotonic() - budget.start_monotonic, 2),
                "instruments_completed": budget.instruments_completed,
                "instruments_total": max_instruments,
                "current_instrument": instrument_id,
                "phase": PHASE_B_BOUND_FUNDING_HISTORY,
                "ohlcv_rows": len(ohlcv_rows),
            }
        )
        funding_rows, funding_fail = paginate_bounded_funding_v0(
            instrument_id=instrument_id,
            native_instrument_id=native_id,
            window=window,
            fetcher=fetcher,
            rate_limiter=rate_limiter,
            fetch_with_retry=fetch_with_retry,
            build_url=ingest_mod._build_url,
            parse_json=ingest_mod._parse_okx_json,
            raw_dir=raw_funding_dir,
            request_log=request_log,
            budget=budget,
        )
        if funding_fail:
            fail_reason = funding_fail
            status = FetchTerminalStatus.BUDGET_EXCEEDED_FAIL_CLOSED
            break

        joined, missing = attach_funding_to_ohlcv_bars_v0(
            instrument_id=instrument_id,
            ohlcv_rows=ohlcv_rows,
            funding_rows=funding_rows,
            window=window,
        )
        all_panel_bars.extend(joined)
        if missing:
            missing_report[instrument_id] = missing
        budget.complete_instrument()
        _progress_log(
            {
                "elapsed_seconds": round(time.monotonic() - budget.start_monotonic, 2),
                "instruments_completed": budget.instruments_completed,
                "instruments_total": max_instruments,
                "current_instrument": instrument_id,
                "ohlcv_pages": sum(
                    1
                    for r in request_log
                    if r.instrument_id == instrument_id and r.phase == PHASE_A_BOUND_OHLCV_PANEL
                ),
                "funding_pages": sum(
                    1
                    for r in request_log
                    if r.instrument_id == instrument_id and r.phase == PHASE_B_BOUND_FUNDING_HISTORY
                ),
                "retained_pages": budget.retained_pages,
                "discarded_pages": budget.discarded_pages,
                "total_requests": budget.total_requests,
                "raw_bytes": budget.total_raw_bytes,
            }
        )

    if status is FetchTerminalStatus.PREFLIGHT_COMPLETE:
        if not first_ohlcv_request_anchored_at_end_exclusive(request_log, window):
            fail_reason = "FIRST_REQUEST_NOT_ANCHORED_AT_END_EXCLUSIVE"
            status = FetchTerminalStatus.VALIDATION_FAILED
        if not all_panel_bars:
            fail_reason = fail_reason or "PANEL_EMPTY_AFTER_PREFLIGHT"
            status = FetchTerminalStatus.VALIDATION_FAILED
        for bar in all_panel_bars:
            ts = _parse_utc_ms(str(bar["timestamp_utc"]))
            if ts >= window.end_exclusive_ms or ts < window.start_ms:
                fail_reason = "PANEL_BAR_OUTSIDE_WINDOW"
                status = FetchTerminalStatus.VALIDATION_FAILED
                break

    all_panel_bars.sort(key=lambda row: (row["instrument_id"], row["timestamp_utc"]))
    (panel_dir / "normalized_panel_bars_with_funding.json").write_text(
        json.dumps({"bars": all_panel_bars}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": "pit_okx_pt1h_panel_funding_dataset_manifest_v1",
        "panel_id": "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1",
        "dataset_extension": "extended_chronological_with_funding_v1",
        "preflight_only": preflight_only,
        "window": {
            "start_inclusive_utc": window.start_inclusive_utc,
            "end_exclusive_utc": window.end_exclusive_utc,
            "funding_fetch_start_utc": window.funding_fetch_start_utc,
            "required_pre_window_hours": window.required_pre_window_hours,
        },
        "row_count_total": len(all_panel_bars),
        "instrument_ids": sorted({bar["instrument_id"] for bar in all_panel_bars}),
        "score_cashflow_separation": {
            "score_input": score_input_provenance_marker_v0(),
            "funding_cashflow": funding_cashflow_provenance_marker_v0(),
        },
    }
    (panel_dir / "panel_funding_dataset_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (reports_dir / "PAGINATION_REQUEST_LOG.jsonl").write_text(
        "\n".join(json.dumps(record.__dict__, sort_keys=True) for record in request_log) + "\n",
        encoding="utf-8",
    )
    (reports_dir / "MISSING_DATA_REPORT.json").write_text(
        json.dumps(missing_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    from scripts.ops.primary_evidence_retention_v0 import (
        verify_manifest_sha256,
        write_manifest_sha256,
    )

    write_manifest_sha256(staging_root)
    manifest_ok, manifest_msg = verify_manifest_sha256(staging_root)
    manifest_verify_rc = 0 if manifest_ok else 1

    ohlcv_raw_count = len(list(raw_ohlcv_dir.glob("*.json")))
    funding_raw_count = len(list(raw_funding_dir.glob("*.json")))
    oow_count = out_of_window_retained_raw_count(raw_ohlcv_dir) + out_of_window_retained_raw_count(
        raw_funding_dir
    )

    promoted = False
    if status is not FetchTerminalStatus.PREFLIGHT_COMPLETE or fail_reason:
        status = status if fail_reason else FetchTerminalStatus.INCOMPLETE_NOT_PROMOTED

    return BoundedPreflightResultV0(
        status=status,
        staging_root=str(staging_root),
        instrument_count=len(eligible),
        ohlcv_raw_files=ohlcv_raw_count,
        funding_raw_files=funding_raw_count,
        out_of_window_raw_files=oow_count,
        total_requests=budget.total_requests,
        total_raw_bytes=budget.total_raw_bytes,
        runtime_seconds=round(time.monotonic() - budget.start_monotonic, 2),
        fail_reason=fail_reason,
        request_log_count=len(request_log),
        manifest_verify_rc=manifest_verify_rc,
        promoted=promoted,
    )
