"""Contract tests for OKX Historical Funding Archive ingest for materialized panel v0."""

from __future__ import annotations

import io
import json
import tempfile
import zipfile
from pathlib import Path

from src.research.okx_historical_funding_archive_ingest_for_materialized_panel_v0 import (
    CONFIRM_GO,
    REASON_FETCH_GUARD_BLOCKED,
    REASON_FULL_UNIVERSE_SCOPE,
    ArchiveIngestFailClosedReason,
    HistoricalArchiveIngestVerdict,
    _verify_panel_binding_scope_v0,
    build_archive_source_binding_v0,
    fetch_and_parse_panel_archives_v0,
    ingest_archive_bytes_for_instrument_v0,
    load_historical_archive_ingest_config_v0,
    resolve_native_instrument_mapping_v0,
    run_historical_archive_ingest_scope_v0,
)
from src.research.bounded_offline_funding_fetch_for_materialized_panel_v0 import (
    PanelMemberBindingV0,
)
from tests.research.fixtures.cross_sectional_funding_rate_delta_momentum_v0.fixture_builder import (
    build_synthetic_ohlcv_panel_v0,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]

ETH_CSV = """\
instrument_name,funding_rate,funding_time
ETH-USDT-SWAP,0.000004880388991,1714492800000
ETH-USDT-SWAP,0.0000017236956739,1714521600000
ETH-USDT-SWAP,0.0000563153976033,1714550400000
"""


def _csv_zip(csv_text: str, inner: str = "ETH-USDT-SWAP-fundingrates-2024-05.csv") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(inner, csv_text)
    return buf.getvalue()


def test_confirm_go_constant() -> None:
    assert CONFIRM_GO == "GO_BOUNDED_OKX_HISTORICAL_FUNDING_ARCHIVE_INGEST_V0"


def test_config_loads_panel_bounds() -> None:
    config = load_historical_archive_ingest_config_v0(_REPO_ROOT)
    assert config["panel_member_count_bound"] == 118
    assert "2024-05" in config["bound_archive_months"]


def test_resolve_native_instrument_mapping_rejects_bitcoin() -> None:
    symbol, reason = resolve_native_instrument_mapping_v0("BTC-USDT-SWAP")
    assert symbol is None
    assert reason == ArchiveIngestFailClosedReason.INSTRUMENT_MAPPING_UNRESOLVED.value


def test_resolve_native_instrument_mapping_accepts_swap() -> None:
    symbol, reason = resolve_native_instrument_mapping_v0("ETH-USDT-SWAP")
    assert symbol == "ETH-USDT-SWAP"
    assert reason is None


def test_ingest_archive_bytes_parses_minimal_csv() -> None:
    events, report, fail = ingest_archive_bytes_for_instrument_v0(
        _csv_zip(ETH_CSV),
        venue_symbol="ETH-USDT-SWAP",
        period_start_utc="2024-05-01T00:00:00Z",
        period_end_exclusive_utc="2024-09-01T00:00:00Z",
    )
    assert fail is None
    assert len(events) == 3
    assert report["events_in_period"] == 3


def test_ingest_archive_bytes_fail_closed_bad_zip() -> None:
    events, _report, fail = ingest_archive_bytes_for_instrument_v0(
        b"not-a-zip",
        venue_symbol="ETH-USDT-SWAP",
        period_start_utc="2024-05-01T00:00:00Z",
        period_end_exclusive_utc="2024-09-01T00:00:00Z",
    )
    assert not events
    assert fail == ArchiveIngestFailClosedReason.ARCHIVE_FORMAT_UNKNOWN.value


def test_run_scope_blocks_invalid_go_token() -> None:
    durable = Path(tempfile.mkdtemp(prefix="hist_archive_go_"))
    result = run_historical_archive_ingest_scope_v0(
        repo_root=_REPO_ROOT,
        durable_evidence_root=durable,
        staging_root=durable / "missing",
        confirm_go="INVALID",
        execute_fetch=False,
    )
    assert result.verdict is HistoricalArchiveIngestVerdict.FAIL_CLOSED_FETCH
    assert REASON_FETCH_GUARD_BLOCKED in result.reason_codes


def test_full_universe_guard_blocks_more_than_bound_panel_members() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="hist_archive_scope_"))
    staging = tmp / "staging"
    panel = build_synthetic_ohlcv_panel_v0()
    panel_dir = staging / "panel"
    panel_dir.mkdir(parents=True)
    (panel_dir / "panel_dataset_manifest.json").write_text(
        json.dumps(
            {
                "instrument_ids": [series.instrument_id for series in panel],
                "native_instrument_ids": [series.native_instrument_id for series in panel],
                "panel_calendar_start_utc": "2024-05-01T00:00:00Z",
                "panel_calendar_end_utc": "2024-09-01T00:00:00Z",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    binding = PanelMemberBindingV0(
        staging_root=str(staging),
        panel_member_count=200,
        instrument_ids=tuple(series.instrument_id for series in panel),
        native_instrument_ids=tuple(series.native_instrument_id for series in panel),
        panel_calendar_start_utc="2024-05-01T00:00:00Z",
        panel_calendar_end_utc="2024-09-01T00:00:00Z",
        panel_dataset_manifest_path=str(panel_dir / "panel_dataset_manifest.json"),
    )
    ok, reasons = _verify_panel_binding_scope_v0(binding, staging, max_panel_members=118)
    assert ok is False
    assert REASON_FULL_UNIVERSE_SCOPE in reasons


def test_archive_source_binding_declares_no_live_api() -> None:
    config = load_historical_archive_ingest_config_v0(_REPO_ROOT)
    binding = build_archive_source_binding_v0(config)
    assert binding["okx_public_live_api_used"] is False
    assert binding["full_universe_fetch_run"] is False
