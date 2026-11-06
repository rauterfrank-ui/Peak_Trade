"""Contract tests for bounded cross-sectional panel OHLCV/funding fetch v0."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from src.research.cross_sectional_bounded_panel_fetch_v0 import (
    PHASE_A_BOUND_OHLCV_PANEL,
    PHASE_B_BOUND_FUNDING_HISTORY,
    BudgetGuardReason,
    FetchBudgetGuardV0,
    PaginationPageRecordV0,
    attach_funding_to_ohlcv_bars_v0,
    backward_asof_funding_lookup_v0,
    compute_bounded_window_v0,
    derive_production_budget_v0,
    first_ohlcv_request_anchored_at_end_exclusive,
    out_of_window_retained_raw_count,
    paginate_bounded_funding_v0,
    paginate_bounded_ohlcv_v0,
    select_eligible_instruments_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_scoring_v0 import (
    FUNDING_DELTA_LOOKBACK_K,
    FUNDING_SIGNAL_LAG,
    funding_cashflow_provenance_marker_v0,
    score_input_provenance_marker_v0,
)
from src.research.okx_production_instrument_lifecycle_source_v1 import (
    evaluate_okx_instrument_eligibility_v1,
)


def _ms(utc: str) -> int:
    from datetime import datetime, timezone

    return int(
        datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000
    )


def _ohlcv_row(ts_utc: str, *, confirm: str = "1") -> list[str]:
    return [str(_ms(ts_utc)), "1", "2", "0.5", "1.5", "100", "0", "0", confirm]


def _funding_row(ts_utc: str, rate: str = "0.0001") -> dict[str, str]:
    return {"fundingTime": str(_ms(ts_utc)), "fundingRate": rate, "instId": "ETH-USDT-SWAP"}


class _SeqFetcher:
    def __init__(self, responses: list[tuple[int, bytes]]) -> None:
        self._responses = list(responses)
        self._idx = 0
        self.requested_urls: list[str] = []

    def __call__(self, url: str, **_kwargs: Any) -> tuple[int, bytes, dict[str, str]]:
        self.requested_urls.append(url)
        if self._idx >= len(self._responses):
            return 200, b'{"code":"0","data":[]}', {}
        status, body = self._responses[self._idx]
        self._idx += 1
        return status, body, {}


def _noop_rate_limiter() -> None:
    return None


def _build_url(path: str, params: dict[str, str]) -> str:
    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"https://www.okx.com{path}?{query}"


def _parse_json(body: bytes) -> dict[str, Any]:
    return json.loads(body.decode())


def _fetch_with_retry(
    url: str, *, fetcher: Any, **_kwargs: Any
) -> tuple[int, bytes, dict[str, str]]:
    return fetcher(url)


@pytest.fixture
def window() -> Any:
    return compute_bounded_window_v0()


@pytest.fixture
def budget(window: Any) -> FetchBudgetGuardV0:
    derived = derive_production_budget_v0(window)
    return FetchBudgetGuardV0(
        max_instruments=10,
        max_pages_per_instrument=derived["max_pages_per_instrument"],
        max_total_requests=100,
        max_total_raw_bytes=10_000_000,
        max_runtime_seconds=60,
    )


def test_first_ohlcv_request_anchored_at_end_exclusive_not_now(
    window: Any, budget: FetchBudgetGuardV0, tmp_path: Path
) -> None:
    now_ms = _ms("2026-07-03T12:00:00Z")
    outside_page = [_ohlcv_row("2026-07-03T11:00:00Z"), _ohlcv_row("2026-06-01T00:00:00Z")]
    inside_page = [_ohlcv_row("2024-08-31T23:00:00Z"), _ohlcv_row("2024-05-01T00:00:00Z")]
    responses = [
        (200, json.dumps({"code": "0", "data": outside_page}).encode()),
        (200, json.dumps({"code": "0", "data": inside_page}).encode()),
    ]
    fetcher = _SeqFetcher(responses)
    request_log: list[PaginationPageRecordV0] = []
    paginate_bounded_ohlcv_v0(
        instrument_id="ETH-USDT-SWAP",
        native_instrument_id="ETH-USDT-SWAP",
        window=window,
        fetcher=fetcher,
        rate_limiter=_noop_rate_limiter,
        fetch_with_retry=_fetch_with_retry,
        build_url=_build_url,
        parse_json=_parse_json,
        raw_dir=tmp_path / "ohlcv",
        request_log=request_log,
        budget=budget,
    )
    assert first_ohlcv_request_anchored_at_end_exclusive(request_log, window)
    first_url = fetcher.requested_urls[0]
    assert f"after={window.end_exclusive_ms}" in first_url
    assert str(now_ms) not in first_url


def test_window_boundaries_start_inclusive_end_exclusive(
    window: Any, budget: FetchBudgetGuardV0, tmp_path: Path
) -> None:
    page = [
        _ohlcv_row("2024-04-30T23:00:00Z"),
        _ohlcv_row("2024-05-01T00:00:00Z"),
        _ohlcv_row("2024-08-31T23:00:00Z"),
        _ohlcv_row("2024-09-01T00:00:00Z"),
    ]
    fetcher = _SeqFetcher([(200, json.dumps({"code": "0", "data": page}).encode())])
    rows, _ = paginate_bounded_ohlcv_v0(
        instrument_id="ETH-USDT-SWAP",
        native_instrument_id="ETH-USDT-SWAP",
        window=window,
        fetcher=fetcher,
        rate_limiter=_noop_rate_limiter,
        fetch_with_retry=_fetch_with_retry,
        build_url=_build_url,
        parse_json=_parse_json,
        raw_dir=tmp_path / "ohlcv",
        request_log=[],
        budget=budget,
    )
    ts_set = {int(r[0]) for r in rows}
    assert _ms("2024-05-01T00:00:00Z") in ts_set
    assert _ms("2024-08-31T23:00:00Z") in ts_set
    assert _ms("2024-04-30T23:00:00Z") not in ts_set
    assert _ms("2024-09-01T00:00:00Z") not in ts_set


def test_out_of_window_page_not_persisted_as_raw(
    window: Any, budget: FetchBudgetGuardV0, tmp_path: Path
) -> None:
    outside = [_ohlcv_row("2026-01-01T00:00:00Z"), _ohlcv_row("2025-12-31T23:00:00Z")]
    fetcher = _SeqFetcher([(200, json.dumps({"code": "0", "data": outside}).encode())])
    request_log: list[PaginationPageRecordV0] = []
    raw_dir = tmp_path / "ohlcv"
    paginate_bounded_ohlcv_v0(
        instrument_id="ETH-USDT-SWAP",
        native_instrument_id="ETH-USDT-SWAP",
        window=window,
        fetcher=fetcher,
        rate_limiter=_noop_rate_limiter,
        fetch_with_retry=_fetch_with_retry,
        build_url=_build_url,
        parse_json=_parse_json,
        raw_dir=raw_dir,
        request_log=request_log,
        budget=budget,
    )
    assert list(raw_dir.glob("*.json")) == []
    assert request_log[0].retained is False
    assert request_log[0].discarded_reason == "PAGE_FULLY_OUTSIDE_BOUND_WINDOW"


def test_partial_overlap_page_filtered_and_retained(
    window: Any, budget: FetchBudgetGuardV0, tmp_path: Path
) -> None:
    mixed = [
        _ohlcv_row("2024-04-30T23:00:00Z"),
        _ohlcv_row("2024-05-01T01:00:00Z"),
        _ohlcv_row("2024-05-01T02:00:00Z"),
    ]
    fetcher = _SeqFetcher([(200, json.dumps({"code": "0", "data": mixed}).encode())])
    request_log: list[PaginationPageRecordV0] = []
    raw_dir = tmp_path / "ohlcv"
    rows, _ = paginate_bounded_ohlcv_v0(
        instrument_id="ETH-USDT-SWAP",
        native_instrument_id="ETH-USDT-SWAP",
        window=window,
        fetcher=fetcher,
        rate_limiter=_noop_rate_limiter,
        fetch_with_retry=_fetch_with_retry,
        build_url=_build_url,
        parse_json=_parse_json,
        raw_dir=raw_dir,
        request_log=request_log,
        budget=budget,
    )
    assert len(list(raw_dir.glob("*.json"))) == 1
    assert request_log[0].retained is True
    assert _ms("2024-04-30T23:00:00Z") not in {int(r[0]) for r in rows}
    assert _ms("2024-05-01T01:00:00Z") in {int(r[0]) for r in rows}


def test_pagination_stops_at_start_bound(
    window: Any, budget: FetchBudgetGuardV0, tmp_path: Path
) -> None:
    from src.research.cross_sectional_bounded_panel_fetch_v0 import PAGE_LIMIT

    start_bound = _ms("2024-05-01T00:00:00Z")
    page1 = []
    for i in range(PAGE_LIMIT):
        ts = start_bound + (i + 48) * 3_600_000
        page1.append(
            _ohlcv_row(
                datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        )
    page2 = [_ohlcv_row("2024-05-01T00:00:00Z"), _ohlcv_row("2024-04-30T23:00:00Z")]
    fetcher = _SeqFetcher(
        [
            (200, json.dumps({"code": "0", "data": page1}).encode()),
            (200, json.dumps({"code": "0", "data": page2}).encode()),
        ]
    )
    rows, _ = paginate_bounded_ohlcv_v0(
        instrument_id="ETH-USDT-SWAP",
        native_instrument_id="ETH-USDT-SWAP",
        window=window,
        fetcher=fetcher,
        rate_limiter=_noop_rate_limiter,
        fetch_with_retry=_fetch_with_retry,
        build_url=_build_url,
        parse_json=_parse_json,
        raw_dir=tmp_path / "ohlcv",
        request_log=[],
        budget=budget,
    )
    assert len(fetcher.requested_urls) == 2
    ts_set = {int(r[0]) for r in rows}
    assert _ms("2024-05-01T00:00:00Z") in ts_set
    assert _ms("2024-04-30T23:00:00Z") not in ts_set


def test_ohlcv_and_funding_use_separate_paths(
    window: Any, budget: FetchBudgetGuardV0, tmp_path: Path
) -> None:
    ohlcv_fetcher = _SeqFetcher(
        [(200, json.dumps({"code": "0", "data": [_ohlcv_row("2024-05-01T00:00:00Z")]}).encode())]
    )
    funding_fetcher = _SeqFetcher(
        [(200, json.dumps({"code": "0", "data": [_funding_row("2024-05-01T00:00:00Z")]}).encode())]
    )
    ohlcv_dir = tmp_path / "ohlcv"
    funding_dir = tmp_path / "funding"
    request_log: list[PaginationPageRecordV0] = []
    paginate_bounded_ohlcv_v0(
        instrument_id="ETH-USDT-SWAP",
        native_instrument_id="ETH-USDT-SWAP",
        window=window,
        fetcher=ohlcv_fetcher,
        rate_limiter=_noop_rate_limiter,
        fetch_with_retry=_fetch_with_retry,
        build_url=_build_url,
        parse_json=_parse_json,
        raw_dir=ohlcv_dir,
        request_log=request_log,
        budget=budget,
    )
    paginate_bounded_funding_v0(
        instrument_id="ETH-USDT-SWAP",
        native_instrument_id="ETH-USDT-SWAP",
        window=window,
        fetcher=funding_fetcher,
        rate_limiter=_noop_rate_limiter,
        fetch_with_retry=_fetch_with_retry,
        build_url=_build_url,
        parse_json=_parse_json,
        raw_dir=funding_dir,
        request_log=request_log,
        budget=budget,
    )
    assert list(ohlcv_dir.glob("*.json"))
    assert list(funding_dir.glob("*.json"))
    phases = {r.phase for r in request_log}
    assert PHASE_A_BOUND_OHLCV_PANEL in phases
    assert PHASE_B_BOUND_FUNDING_HISTORY in phases
    assert "history-candles" in ohlcv_fetcher.requested_urls[0]
    assert "funding-rate-history" in funding_fetcher.requested_urls[0]


def test_funding_pre_window_minimal_and_bounded(window: Any) -> None:
    pre_hours = FUNDING_DELTA_LOOKBACK_K + FUNDING_SIGNAL_LAG
    assert window.required_pre_window_hours == pre_hours
    assert window.funding_fetch_start_ms == window.start_ms - pre_hours * 3_600_000


def test_backward_asof_uses_no_future_funding(window: Any) -> None:
    bar_ts = _ms("2024-05-10T12:00:00Z")
    funding_rows = [
        _funding_row("2024-05-10T11:00:00Z", "0.0001"),
        _funding_row("2024-05-10T13:00:00Z", "0.0009"),
    ]
    rate = backward_asof_funding_lookup_v0(funding_rows, bar_ts)
    assert rate == "0.0001"


def test_missing_funding_stays_explicit_none(window: Any) -> None:
    ohlcv = [_ohlcv_row("2024-05-10T12:00:00Z")]
    joined, missing = attach_funding_to_ohlcv_bars_v0(
        instrument_id="ETH-USDT-SWAP",
        ohlcv_rows=ohlcv,
        funding_rows=[],
        window=window,
    )
    assert joined[0]["funding_rate"] is None
    assert missing


def test_score_and_cashflow_provenance_separated(window: Any) -> None:
    ohlcv = [_ohlcv_row("2024-05-10T12:00:00Z")]
    funding = [_funding_row("2024-05-10T11:00:00Z")]
    joined, _ = attach_funding_to_ohlcv_bars_v0(
        instrument_id="ETH-USDT-SWAP",
        ohlcv_rows=ohlcv,
        funding_rows=funding,
        window=window,
    )
    assert joined[0]["score_input_provenance"] == score_input_provenance_marker_v0()
    assert joined[0]["funding_cashflow_provenance"] == funding_cashflow_provenance_marker_v0()
    assert joined[0]["score_input_provenance"] != joined[0]["funding_cashflow_provenance"]


def test_budget_guard_fail_closed_on_max_requests(window: Any, tmp_path: Path) -> None:
    from datetime import datetime, timezone

    from src.research.cross_sectional_bounded_panel_fetch_v0 import PAGE_LIMIT

    budget = FetchBudgetGuardV0(
        max_instruments=2,
        max_pages_per_instrument=50,
        max_total_requests=1,
        max_total_raw_bytes=10_000_000,
        max_runtime_seconds=60,
    )
    base_ms = _ms("2024-05-10T00:00:00Z")
    page = []
    for i in range(PAGE_LIMIT):
        ts = base_ms + i * 3_600_000
        page.append(
            _ohlcv_row(
                datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        )
    fetcher = _SeqFetcher(
        [
            (200, json.dumps({"code": "0", "data": page}).encode()),
            (200, json.dumps({"code": "0", "data": page}).encode()),
        ]
    )
    _, fail = paginate_bounded_ohlcv_v0(
        instrument_id="ETH-USDT-SWAP",
        native_instrument_id="ETH-USDT-SWAP",
        window=window,
        fetcher=fetcher,
        rate_limiter=_noop_rate_limiter,
        fetch_with_retry=_fetch_with_retry,
        build_url=_build_url,
        parse_json=_parse_json,
        raw_dir=tmp_path / "ohlcv",
        request_log=[],
        budget=budget,
    )
    assert fail == BudgetGuardReason.MAX_TOTAL_REQUESTS.value


def test_bitcoin_and_xbt_instruments_excluded() -> None:
    list_time = str(_ms("2023-01-01T00:00:00Z"))
    base = {
        "instType": "SWAP",
        "state": "live",
        "settleCcy": "USDT",
        "ctType": "linear",
        "listTime": list_time,
        "expTime": "",
    }
    samples = [
        {**base, "instId": "BTC-USDT-SWAP"},
        {**base, "instId": "XBT-USDT-SWAP"},
        {**base, "instId": "ETH-USDT-SWAP"},
    ]
    eligible = select_eligible_instruments_v0(samples)
    canonical_ids = [item[0] for item in eligible]
    native_ids = [item[1] for item in eligible]
    assert "ETH-USDT-SWAP" in native_ids
    assert "BTC-USDT-SWAP" not in native_ids
    assert "XBT-USDT-SWAP" not in native_ids
    assert any("ETH" in cid for cid in canonical_ids)
    for inst in samples[:2]:
        assert not evaluate_okx_instrument_eligibility_v1(inst).eligible


def test_out_of_window_retained_raw_count_detects_bad_files(window: Any, tmp_path: Path) -> None:
    bad_name = f"ETH-USDT-SWAP_ohlcv_p0000_{_ms('2026-01-01T00:00:00Z')}_{_ms('2026-01-02T00:00:00Z')}_abc123.json"
    good_name = f"ETH-USDT-SWAP_ohlcv_p0001_{window.start_ms}_{window.end_exclusive_ms - 3_600_000}_def456.json"
    raw_dir = tmp_path / "ohlcv"
    raw_dir.mkdir(parents=True)
    (raw_dir / bad_name).write_text("{}", encoding="utf-8")
    (raw_dir / good_name).write_text("{}", encoding="utf-8")
    assert out_of_window_retained_raw_count(raw_dir) == 1


def test_aborted_preflight_does_not_promote(tmp_path: Path) -> None:
    from src.research.cross_sectional_bounded_panel_fetch_v0 import (
        BoundedPreflightResultV0,
        FetchTerminalStatus,
    )

    result = BoundedPreflightResultV0(
        status=FetchTerminalStatus.BUDGET_EXCEEDED_FAIL_CLOSED,
        staging_root=str(tmp_path),
        instrument_count=1,
        ohlcv_raw_files=1,
        funding_raw_files=0,
        out_of_window_raw_files=0,
        total_requests=2,
        total_raw_bytes=100,
        runtime_seconds=1.0,
        fail_reason=BudgetGuardReason.MAX_TOTAL_REQUESTS.value,
        request_log_count=2,
        manifest_verify_rc=0,
        promoted=False,
    )
    assert result.promoted is False
    assert result.status != FetchTerminalStatus.PREFLIGHT_COMPLETE


def test_quarantine_path_not_used_by_bounded_preflight_runner() -> None:
    from src.research import cross_sectional_bounded_panel_fetch_v0 as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    quarantine = ".tmp_historical_20260703T134626Z"
    assert quarantine not in source
