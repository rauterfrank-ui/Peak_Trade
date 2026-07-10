"""Contract tests for OKX historical open interest public fetch and panel materialization v0."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from src.research.cross_sectional_open_interest_delta_rank_v0_bound_panel_dataset_materialization_v0 import (
    MaterializationTerminalStatus,
    build_dataset_contract_v0,
    compute_bound_open_interest_data_digest_v0,
    materialize_open_interest_panel_from_observations_v0,
    materializer_roundtrip_contract_v0,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    NO_LOOKAHEAD,
    NO_SILENT_FORWARD_FILL,
    build_pit_open_interest_semantics_contract_v0,
)
from src.research.okx_historical_open_interest_public_fetch_v0 import (
    OpenInterestFetchBudgetGuardV0,
    OpenInterestHorizonReason,
    assess_open_interest_horizon_v0,
    backward_asof_open_interest_lookup_v0,
    classify_open_interest_for_bar_v0,
    compute_availability_time_utc_v0,
    compute_open_interest_bounded_window_v0,
    deduplicate_open_interest_observations_v0,
    paginate_bounded_open_interest_v0,
    parse_okx_open_interest_history_row_v0,
    NormalizedOpenInterestObservationV0,
)
from src.research.missing_open_interest_policy_v0 import (
    MISSING_REASON_LOOKAHEAD_REJECTED,
    MISSING_REASON_NO_PRIOR_OI,
    reject_synthetic_zero_open_interest_fallback_v0,
)
from src.research.okx_production_instrument_lifecycle_source_v1 import (
    evaluate_okx_instrument_eligibility_v1,
)
from src.research.pit_okx_pt1h_panel_open_interest_dataset_v1 import (
    OPEN_INTEREST_UNIT,
    compute_panel_open_interest_digest_v1,
    validate_open_interest_panel_series_v1,
    InstrumentOpenInterestPanelSeriesV1,
    PanelBarWithOpenInterestV1,
)


def _ms(utc: str) -> int:
    return int(
        datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000
    )


def _oi_row(ts_utc: str, oi: str = "1000.0") -> list[str]:
    return [str(_ms(ts_utc)), oi, "100.0", "2000000.0"]


def _obs(
    ts_utc: str,
    *,
    instrument_id: str = "okx:linear_perpetual:ETH:USDT:USDT:perp",
    native: str = "ETH-USDT-SWAP",
    oi: str = "1000.0",
) -> NormalizedOpenInterestObservationV0:
    parsed = parse_okx_open_interest_history_row_v0(
        _oi_row(ts_utc, oi),
        instrument_id=instrument_id,
        native_instrument_id=native,
    )
    assert parsed is not None
    return parsed


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
    return compute_open_interest_bounded_window_v0()


@pytest.fixture
def budget() -> OpenInterestFetchBudgetGuardV0:
    return OpenInterestFetchBudgetGuardV0(
        max_instruments=5,
        max_pages_per_instrument=20,
        max_total_requests=100,
        max_total_raw_bytes=10_000_000,
        max_runtime_seconds=60,
    )


def test_futures_only_btc_spot_exclusion() -> None:
    list_time = str(_ms("2023-01-01T00:00:00Z"))
    base = {
        "instType": "SWAP",
        "state": "live",
        "settleCcy": "USDT",
        "ctType": "linear",
        "listTime": list_time,
        "expTime": "",
    }
    eligible = evaluate_okx_instrument_eligibility_v1({**base, "instId": "ETH-USDT-SWAP"})
    assert eligible.eligible
    btc = evaluate_okx_instrument_eligibility_v1({**base, "instId": "BTC-USDT-SWAP"})
    assert not btc.eligible
    spot = evaluate_okx_instrument_eligibility_v1(
        {
            "instId": "ETH-USDT",
            "instType": "SPOT",
            "settleCcy": "USDT",
            "ctType": "linear",
            "state": "live",
            "listTime": list_time,
            "expTime": "",
        }
    )
    assert not spot.eligible


def test_parse_okx_open_interest_history_row_and_unit() -> None:
    obs = _obs("2024-05-01T01:00:00Z", oi="7134737.07")
    assert obs.open_interest_unit == OPEN_INTEREST_UNIT
    assert obs.open_interest_raw == "7134737.07"


def test_deduplicate_open_interest_observations_stable_sort() -> None:
    rows = [_obs("2024-05-01T00:00:00Z"), _obs("2024-05-01T00:00:00Z", oi="2000")]
    deduped = deduplicate_open_interest_observations_v0(rows)
    assert len(deduped) == 1
    assert deduped[0].open_interest_raw == "2000"


def test_backward_asof_no_lookahead() -> None:
    obs = [_obs("2024-05-01T00:00:00Z"), _obs("2024-05-01T02:00:00Z")]
    chosen = backward_asof_open_interest_lookup_v0(obs, _ms("2024-05-01T01:00:00Z"))
    assert chosen is not None
    assert chosen.observation_time_utc == "2024-05-01T00:00:00Z"
    future_only = backward_asof_open_interest_lookup_v0(obs, _ms("2023-12-31T23:00:00Z"))
    assert future_only is None


def test_classify_lookahead_and_stale_and_missing() -> None:
    obs = _obs("2024-05-01T00:00:00Z")
    ok_val, quality, stale, missing, reason = classify_open_interest_for_bar_v0(
        observation=obs,
        bar_timestamp_ms=_ms("2024-05-01T01:00:00Z"),
        bar_timestamp_utc="2024-05-01T01:00:00Z",
    )
    assert ok_val == "1000.0"
    assert quality == "OK"
    assert not stale
    assert not missing
    assert reason is None

    _, quality2, _, missing2, reason2 = classify_open_interest_for_bar_v0(
        observation=None,
        bar_timestamp_ms=_ms("2024-05-01T01:00:00Z"),
        bar_timestamp_utc="2024-05-01T01:00:00Z",
    )
    assert quality2 == "MISSING"
    assert missing2
    assert reason2 == MISSING_REASON_NO_PRIOR_OI

    future_obs = _obs("2024-05-01T02:00:00Z")
    _, quality3, _, _, reason3 = classify_open_interest_for_bar_v0(
        observation=future_obs,
        bar_timestamp_ms=_ms("2024-05-01T01:00:00Z"),
        bar_timestamp_utc="2024-05-01T01:00:00Z",
    )
    assert quality3 == "LOOKAHEAD_REJECTED"
    assert reason3 == MISSING_REASON_LOOKAHEAD_REJECTED


def test_availability_time_lag_semantics() -> None:
    avail = compute_availability_time_utc_v0("2024-05-01T00:00:00Z", signal_lag_bars=1)
    assert avail == "2024-05-01T01:00:00Z"


def test_pit_semantics_contract_flags() -> None:
    contract = build_pit_open_interest_semantics_contract_v0()
    assert contract.no_lookahead is NO_LOOKAHEAD
    assert contract.no_silent_forward_fill is NO_SILENT_FORWARD_FILL
    assert len(contract.semantic_digest) == 64


def test_paginate_bounded_open_interest_retains_window_rows(
    window: Any, budget: OpenInterestFetchBudgetGuardV0, tmp_path: Path
) -> None:
    inside = [_oi_row("2024-05-01T00:00:00Z"), _oi_row("2024-05-01T01:00:00Z")]
    outside_page = [_oi_row("2026-07-10T18:00:00Z") for _ in range(100)]
    fetcher = _SeqFetcher(
        [
            (200, json.dumps({"code": "0", "data": outside_page}).encode()),
            (200, json.dumps({"code": "0", "data": inside}).encode()),
        ]
    )
    obs, fail = paginate_bounded_open_interest_v0(
        instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
        native_instrument_id="ETH-USDT-SWAP",
        window=window,
        fetcher=fetcher,
        rate_limiter=_noop_rate_limiter,
        fetch_with_retry=_fetch_with_retry,
        build_url=_build_url,
        parse_json=_parse_json,
        raw_dir=tmp_path,
        budget=budget,
    )
    assert fail is None
    assert len(obs) == 2
    assert obs[0].observation_time_utc == "2024-05-01T00:00:00Z"


def test_malformed_response_fail_closed(
    window: Any, budget: OpenInterestFetchBudgetGuardV0, tmp_path: Path
) -> None:
    fetcher = _SeqFetcher([(500, b'{"code":"0","data":[]}')])
    obs, fail = paginate_bounded_open_interest_v0(
        instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
        native_instrument_id="ETH-USDT-SWAP",
        window=window,
        fetcher=fetcher,
        rate_limiter=_noop_rate_limiter,
        fetch_with_retry=_fetch_with_retry,
        build_url=_build_url,
        parse_json=_parse_json,
        raw_dir=tmp_path,
        budget=budget,
    )
    assert fail is not None
    assert obs == []


def test_horizon_assessment_fail_closed_for_insufficient_retention(window: Any) -> None:
    recent = [_obs("2026-05-11T19:00:00Z")]
    assessment = assess_open_interest_horizon_v0(
        recent,
        window=window,
        probe_instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
    )
    assert not assessment.horizon_covers_required_window
    assert assessment.reason == OpenInterestHorizonReason.EARLIEST_AVAILABLE_AFTER_REQUIRED_START


def test_reject_synthetic_zero_open_interest_fallback() -> None:
    with pytest.raises(ValueError):
        reject_synthetic_zero_open_interest_fallback_v0("0")


def test_materialization_fail_closed_on_horizon(tmp_path: Path) -> None:
    window = compute_open_interest_bounded_window_v0()
    assessment = assess_open_interest_horizon_v0([], window=window, probe_instrument_id="probe")
    result = materialize_open_interest_panel_from_observations_v0(
        staging_root=tmp_path,
        observations_by_native={},
        horizon_assessment=assessment,
        source_data_digest="abc",
    )
    assert result.status == MaterializationTerminalStatus.HORIZON_INSUFFICIENT_FAIL_CLOSED


def test_stable_dataset_digest_and_materializer_roundtrip() -> None:
    rows = [
        {
            "instrument_id": "okx:linear_perpetual:ETH:USDT:USDT:perp",
            "native_instrument_id": "ETH-USDT-SWAP",
            "timestamp_utc": "2024-05-01T00:00:00Z",
            "open_interest": "1000.0",
            "open_interest_unit": OPEN_INTEREST_UNIT,
            "is_final": True,
            "data_quality_status": "OK",
            "stale_flag": False,
            "missing_flag": False,
            "universe_membership_status": "ELIGIBLE",
            "source_schema_version": "okx_rubik_open_interest_history.v0",
        }
    ]
    d1 = compute_panel_open_interest_digest_v1(rows)
    d2 = compute_panel_open_interest_digest_v1(rows)
    assert d1 == d2
    rt = materializer_roundtrip_contract_v0()
    assert rt["bound_data_digest"] == compute_bound_open_interest_data_digest_v0()
    contract = build_dataset_contract_v0()
    assert contract["dataset_id"] == "pit_okx_linear_usdt_non_bitcoin_open_interest_panel/v0"


def test_open_interest_panel_series_validation() -> None:
    bar = PanelBarWithOpenInterestV1(
        instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
        native_instrument_id="ETH-USDT-SWAP",
        timestamp_utc="2024-05-01T00:00:00Z",
        open_interest="1000.0",
        open_interest_unit=OPEN_INTEREST_UNIT,
        availability_time_utc="2024-05-01T01:00:00Z",
        is_final=True,
        data_quality_status="OK",
        stale_flag=False,
        missing_flag=False,
        universe_membership_status="ELIGIBLE",
        source_schema_version="okx_rubik_open_interest_history.v0",
    )
    series = InstrumentOpenInterestPanelSeriesV1(
        instrument_id=bar.instrument_id,
        native_instrument_id=bar.native_instrument_id,
        bars=(bar,),
        series_digest="x" * 64,
    )
    result = validate_open_interest_panel_series_v1(series)
    assert result.valid


def test_no_runtime_order_scheduler_imports() -> None:
    forbidden = (
        "src.execution",
        "src.trading",
        "src.scheduler",
        "src.governance.live",
    )
    modules = [
        "src.research.okx_historical_open_interest_public_fetch_v0",
        "src.research.cross_sectional_open_interest_delta_rank_v0_bound_panel_dataset_materialization_v0",
        "src.research.pit_okx_pt1h_panel_open_interest_dataset_v1",
    ]
    for mod_name in modules:
        mod = __import__(mod_name, fromlist=["x"])
        source_path = Path(mod.__file__).read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source_path
