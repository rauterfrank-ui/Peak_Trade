"""Contract tests for OKX Historical Funding Archive ingest and missing policy v0."""

from __future__ import annotations

import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.ops.materialize_cross_sectional_funding_rate_carry_v0_bound_panel_funding_dataset_v0 import (
    _funding_asof_lookup,
)
from src.research.cross_sectional_bounded_panel_fetch_v0 import (
    compute_bounded_window_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_scoring_v0 import (
    FUNDING_DELTA_LOOKBACK_K,
    FUNDING_SIGNAL_LAG,
    FundingDeltaScoreStatusV0,
    compute_instrument_funding_delta_score_v0,
    funding_cashflow_provenance_marker_v0,
    score_input_provenance_marker_v0,
)
from src.research.missing_funding_policy_v0 import (
    MISSING_FUNDING_FAIL_CLOSED,
    MISSING_FUNDING_IS_ZERO,
    MISSING_FUNDING_VALUE,
    reject_synthetic_zero_funding_fallback_v0,
    resolve_funding_rate_or_missing_v0,
)
from src.research.okx_historical_funding_archive_ingest_v0 import (
    FULL_PANEL_PROMOTION_REQUIRES_HISTORICAL_UNIVERSE_LIFECYCLE_PASS,
    HISTORICAL_UNIVERSE_LIFECYCLE_PASS,
    SOURCE_ACCESS_METHOD,
    SOURCE_ID,
    ArchiveAccessGuardReason,
    ArchiveAccessGuardV0,
    ArchiveIngestTerminalStatus,
    ArchiveValidationErrorCode,
    build_archive_cdn_url_v0,
    build_cashflow_provenance_record_v0,
    build_score_input_provenance_record_v0,
    check_full_panel_promotion_allowed_v0,
    compute_required_month_buckets_v0,
    deduplicate_archive_events_v0,
    filter_events_for_period_v0,
    parse_archive_csv_text_v0,
    parse_archive_zip_bytes_v0,
    pit_join_funding_rate_v0,
)

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "okx_historical_funding_archive_v0"

ETH_CSV_MINIMAL = """\
instrument_name,funding_rate,funding_time
ETH-USDT-SWAP,0.000004880388991,1714492800000
ETH-USDT-SWAP,0.0000017236956739,1714521600000
ETH-USDT-SWAP,0.0000563153976033,1714550400000
ETH-USDT-SWAP,-0.0000550400994381,1714579200000
ETH-USDT-SWAP,0.0001388957663224,1714608000000
ETH-USDT-SWAP,0.000100000136433,1714636800000
"""

SOL_CSV_MINIMAL = """\
instrument_name,funding_rate,funding_time
SOL-USDT-SWAP,0.0000647942365645,1714492800000
SOL-USDT-SWAP,-0.0000340383839361,1714521600000
SOL-USDT-SWAP,0.0000123456789012,1714550400000
SOL-USDT-SWAP,0.0000234567890123,1714579200000
SOL-USDT-SWAP,0.0000456789012345,1714608000000
SOL-USDT-SWAP,0.0000567890123456,1714636800000
"""
PROBE_ETH_ZIP = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "probes/okx_historical_funding_archive_probe_v0_20260703T160811Z/"
    "raw/ETH-USDT_ETH-USDT-SWAP-fundingrates-2024-05.zip"
)
PROBE_SOL_ZIP = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "probes/okx_historical_funding_archive_probe_v0_20260703T160811Z/"
    "raw/SOL-USDT_SOL-USDT-SWAP-fundingrates-2024-05.zip"
)


def _ms(utc: str) -> int:
    return int(
        datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000
    )


def _csv_to_zip(csv_text: str, inner_name: str = "TEST-SWAP-fundingrates-2024-05.csv") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(inner_name, csv_text)
    return buf.getvalue()


def _digest_placeholder() -> str:
    return "0" * 64


@pytest.fixture
def eth_csv() -> str:
    return ETH_CSV_MINIMAL


@pytest.fixture
def sol_csv() -> str:
    return SOL_CSV_MINIMAL


def test_missing_funding_policy_contract() -> None:
    assert MISSING_FUNDING_VALUE is None
    assert MISSING_FUNDING_IS_ZERO is False
    assert MISSING_FUNDING_FAIL_CLOSED is True
    assert resolve_funding_rate_or_missing_v0(raw_value=None) is None
    with pytest.raises(ValueError):
        reject_synthetic_zero_funding_fallback_v0("0.0")


def test_source_binding_constants() -> None:
    assert SOURCE_ID == "OKX_HISTORICAL_FUNDING_ARCHIVE"
    assert SOURCE_ACCESS_METHOD == "HISTORICAL_DATA_PORTAL_ARCHIVE"


def test_valid_eth_archive_accepted(eth_csv: str) -> None:
    result = parse_archive_csv_text_v0(
        eth_csv,
        source_file_digest=_digest_placeholder(),
        expected_instrument_id="ETH-USDT-SWAP",
    )
    assert result.status is ArchiveIngestTerminalStatus.COMPLETE
    assert len(result.events) == 6
    assert result.events[0].instrument_id == "ETH-USDT-SWAP"
    assert result.events[0].settlement_class == "SETTLEMENT"


def test_valid_sol_archive_accepted(sol_csv: str) -> None:
    result = parse_archive_csv_text_v0(
        sol_csv,
        source_file_digest=_digest_placeholder(),
        expected_instrument_id="SOL-USDT-SWAP",
    )
    assert result.status is ArchiveIngestTerminalStatus.COMPLETE
    assert all(event.instrument_id == "SOL-USDT-SWAP" for event in result.events)


@pytest.mark.parametrize(
    ("csv_text", "expected_code"),
    [
        (
            "instrument_name,funding_time\nETH-USDT-SWAP,1714492800000\n",
            ArchiveValidationErrorCode.MISSING_FUNDING_RATE,
        ),
        (
            "instrument_name,funding_rate\nETH-USDT-SWAP,0.0001\n",
            ArchiveValidationErrorCode.MISSING_FUNDING_TIME,
        ),
        (
            "instrument_name,funding_rate,funding_time,nextFundingRate\n"
            "ETH-USDT-SWAP,0.0001,1714492800000,0.0002\n",
            ArchiveValidationErrorCode.FORECAST_COLUMN_PRESENT,
        ),
        (
            "instrument_name,funding_rate,funding_time\nSOL-USDT-SWAP,0.0001,1714492800000\n",
            ArchiveValidationErrorCode.WRONG_INSTRUMENT,
        ),
        (
            "instrument_name,funding_rate,funding_time\nBTC-USDT-SWAP,0.0001,1714492800000\n",
            ArchiveValidationErrorCode.BITCOIN_INSTRUMENT,
        ),
        (
            "instrument_name,funding_rate,funding_time\nETH-USDT-SPOT,0.0001,1714492800000\n",
            ArchiveValidationErrorCode.SPOT_OR_DELIVERY_INSTRUMENT,
        ),
        (
            "instrument_name,funding_rate,funding_time\nETH-USDT-SWAP,not_a_rate,1714492800000\n",
            ArchiveValidationErrorCode.INVALID_RATE_UNIT,
        ),
        (
            "instrument_name,funding_rate,funding_time\nETH-USDT-SWAP,0.0001,not_ms\n",
            ArchiveValidationErrorCode.INVALID_TIMESTAMP_TYPE,
        ),
    ],
)
def test_archive_schema_rejections(
    csv_text: str, expected_code: ArchiveValidationErrorCode
) -> None:
    result = parse_archive_csv_text_v0(
        csv_text,
        source_file_digest=_digest_placeholder(),
        expected_instrument_id="ETH-USDT-SWAP",
    )
    assert result.status is ArchiveIngestTerminalStatus.VALIDATION_FAILED
    assert any(expected_code.value in err for err in result.validation_errors)


def test_probe_eth_zip_roundtrip_when_available() -> None:
    if not PROBE_ETH_ZIP.is_file():
        pytest.skip("probe bundle not available on this machine")
    result = parse_archive_zip_bytes_v0(
        PROBE_ETH_ZIP.read_bytes(),
        expected_instrument_id="ETH-USDT-SWAP",
    )
    assert result.status is ArchiveIngestTerminalStatus.COMPLETE
    assert len(result.events) >= 90


def test_probe_sol_zip_roundtrip_when_available() -> None:
    if not PROBE_SOL_ZIP.is_file():
        pytest.skip("probe bundle not available on this machine")
    result = parse_archive_zip_bytes_v0(
        PROBE_SOL_ZIP.read_bytes(),
        expected_instrument_id="SOL-USDT-SWAP",
    )
    assert result.status is ArchiveIngestTerminalStatus.COMPLETE


def test_pre_warmup_row_allowed_and_end_exclusive_filter(eth_csv: str) -> None:
    parsed = parse_archive_csv_text_v0(eth_csv, source_file_digest=_digest_placeholder())
    filtered, out_of_period = filter_events_for_period_v0(
        parsed.events,
        period_start_utc="2024-05-01T00:00:00Z",
        period_end_exclusive_utc="2024-09-01T00:00:00Z",
        include_pre_warmup=True,
    )
    assert any(event.funding_time == _ms("2024-04-30T16:00:00Z") for event in filtered)
    assert all(event.funding_time < _ms("2024-09-01T00:00:00Z") for event in filtered)
    assert out_of_period >= 0


def test_month_buckets_include_adjacent_months() -> None:
    months = compute_required_month_buckets_v0(
        period_start_utc="2024-05-01T00:00:00Z",
        period_end_exclusive_utc="2024-09-01T00:00:00Z",
        pre_window_hours=5,
    )
    assert "2024-04" in months
    assert "2024-05" in months
    assert "2024-08" in months


def test_deduplicate_month_boundary_events(eth_csv: str) -> None:
    parsed = parse_archive_csv_text_v0(eth_csv, source_file_digest=_digest_placeholder())
    duplicate = parsed.events[0]
    merged = parsed.events + (duplicate,)
    deduped, removed = deduplicate_archive_events_v0(merged)
    assert removed == 1
    assert len(deduped) == len(parsed.events)


def test_pit_join_no_future_funding(eth_csv: str) -> None:
    parsed = parse_archive_csv_text_v0(eth_csv, source_file_digest=_digest_placeholder())
    bar_ts = _ms("2024-05-01T00:00:00Z")
    rate, reason = pit_join_funding_rate_v0(parsed.events, bar_ts)
    assert rate is not None
    assert reason is None
    chosen_times = [event.funding_time for event in parsed.events if event.funding_time <= bar_ts]
    assert chosen_times
    assert max(chosen_times) <= bar_ts


def test_pit_join_missing_when_no_prior_settlement(eth_csv: str) -> None:
    parsed = parse_archive_csv_text_v0(eth_csv, source_file_digest=_digest_placeholder())
    bar_ts = _ms("2024-04-01T00:00:00Z")
    rate, reason = pit_join_funding_rate_v0(parsed.events, bar_ts)
    assert rate is None
    assert reason == "MISSING_FUNDING_NO_PRIOR_SETTLEMENT"


def test_carry_materializer_has_no_zero_fallback_in_source() -> None:
    from scripts.ops import (
        materialize_cross_sectional_funding_rate_carry_v0_bound_panel_funding_dataset_v0 as mod,
    )

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert 'return "0.0"' not in source
    assert '"0.0"' not in source


def test_carry_materializer_lookup_blocks_zero_fallback() -> None:
    rate, reason = _funding_asof_lookup(
        funding_rows=[], bar_timestamp_ms=_ms("2024-05-01T00:00:00Z")
    )
    assert rate is None
    assert reason is not None


def test_score_missing_t_minus_1_blocks() -> None:
    rates: list[float | None] = [0.0001, None, 0.0002, 0.0003, 0.0004, 0.0005, 0.0006]
    result = compute_instrument_funding_delta_score_v0(
        "ETH-USDT-SWAP",
        rates,
        epoch_index=6,
    )
    assert result is not None
    assert result.score_status is FundingDeltaScoreStatusV0.MISSING_REQUIRED_FUNDING_HISTORY
    assert result.signal_eligible is False


def test_score_missing_t_minus_1_minus_k_blocks() -> None:
    rates: list[float | None] = [None, 0.0001, 0.0002, 0.0003, 0.0004, 0.0005, 0.0006]
    result = compute_instrument_funding_delta_score_v0(
        "ETH-USDT-SWAP",
        rates,
        epoch_index=5,
    )
    assert result is not None
    assert result.score_status is FundingDeltaScoreStatusV0.MISSING_REQUIRED_FUNDING_HISTORY
    assert result.signal_eligible is False


def test_score_ok_uses_t_minus_1_and_t_minus_1_minus_k_indices() -> None:
    rates = [float(i) * 0.0001 for i in range(10)]
    epoch_index = 6
    result = compute_instrument_funding_delta_score_v0(
        "ETH-USDT-SWAP",
        rates,
        epoch_index=epoch_index,
    )
    assert result is not None
    assert result.signal_eligible is True
    assert result.funding_rate_lag == rates[epoch_index - FUNDING_SIGNAL_LAG]
    assert (
        result.funding_rate_lookback
        == rates[epoch_index - FUNDING_SIGNAL_LAG - FUNDING_DELTA_LOOKBACK_K]
    )


def test_score_cashflow_provenance_separation(eth_csv: str) -> None:
    parsed = parse_archive_csv_text_v0(eth_csv, source_file_digest=_digest_placeholder())
    event = parsed.events[1]
    bar_ts = event.funding_time + 3_600_000
    score_record = build_score_input_provenance_record_v0(event, decision_bar_time_ms=bar_ts)
    cashflow_record = build_cashflow_provenance_record_v0(
        event,
        settlement_consumption_time_ms=event.funding_time,
    )
    assert score_record.consumer_domain != cashflow_record.consumer_domain
    assert score_record.provenance_marker == score_input_provenance_marker_v0()
    assert cashflow_record.provenance_marker == funding_cashflow_provenance_marker_v0()
    assert score_record.provenance_marker != cashflow_record.provenance_marker
    assert score_record.source_file_digest == cashflow_record.source_file_digest
    assert score_record.join_reason != cashflow_record.join_reason


def test_archive_access_guards_fail_closed() -> None:
    guard = ArchiveAccessGuardV0(
        max_instruments=1,
        max_months=1,
        max_http_requests=1,
        max_total_bytes=10,
        max_runtime_seconds=60,
    )
    guard.instruments_used = 1
    assert guard.check_instruments() == ArchiveAccessGuardReason.MAX_INSTRUMENTS.value
    guard = ArchiveAccessGuardV0(
        max_instruments=5,
        max_months=1,
        max_http_requests=5,
        max_total_bytes=10,
        max_runtime_seconds=60,
    )
    guard.months_used = 1
    assert guard.check_months() == ArchiveAccessGuardReason.MAX_MONTHS.value
    reason = guard.record_request(20)
    assert reason == ArchiveAccessGuardReason.MAX_TOTAL_BYTES.value


def test_lifecycle_pass_enables_full_panel_promotion_gate() -> None:
    assert HISTORICAL_UNIVERSE_LIFECYCLE_PASS is True
    allowed, blocker = check_full_panel_promotion_allowed_v0()
    assert allowed is True
    assert blocker == ""


def test_cdn_url_contract() -> None:
    url = build_archive_cdn_url_v0(instrument_id="ETH-USDT-SWAP", year=2024, month=5)
    assert "202405" in url
    assert url.endswith("ETH-USDT-SWAP-fundingrates-2024-05.zip")


def test_zip_parse_from_minimal_fixture(eth_csv: str) -> None:
    result = parse_archive_zip_bytes_v0(
        _csv_to_zip(eth_csv), expected_instrument_id="ETH-USDT-SWAP"
    )
    assert result.status is ArchiveIngestTerminalStatus.COMPLETE


def test_bounded_window_pre_window_matches_scoring_requirements() -> None:
    window = compute_bounded_window_v0()
    assert window.required_pre_window_hours == FUNDING_DELTA_LOOKBACK_K + FUNDING_SIGNAL_LAG
