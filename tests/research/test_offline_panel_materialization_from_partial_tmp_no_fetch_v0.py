"""Contract tests for offline panel materialization from partial tmp (no fetch) v0."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.research.cross_sectional_bound_period_panel_source_materialization_v1 import (
    BoundPeriodSourceMaterializationStatus,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (
    PANEL_CALENDAR_END_UTC,
    PANEL_CALENDAR_START_UTC,
)
from src.research.offline_panel_materialization_from_partial_tmp_no_fetch_v0 import (
    CONFIRM_GO,
    DEFAULT_PARTIAL_TMP_SLUG,
    FUNDING_OWNER,
    PREFLIGHT_OWNER,
    REASON_EVIDENCE_AMBIGUOUS,
    REASON_FETCH_GUARD_BLOCKED,
    REASON_FUNDING_SCOPE_DRIFT,
    REASON_PARTIAL_TMP_MISSING,
    SOURCE_OWNER,
    OfflinePanelMaterializationVerdict,
    load_offline_panel_materialization_config_v0,
    materialize_offline_panel_from_partial_tmp_v0,
    prepare_funding_binding_for_panel_members_v0,
    resolve_partial_tmp_root_v0,
    run_offline_panel_materialization_scope_v0,
)
from tests.research.fixtures.cross_sectional_funding_rate_delta_momentum_v0.fixture_builder import (
    build_synthetic_ohlcv_panel_v0,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PARTIAL_TMP_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    ".tmp_historical_20260703T181515Z"
)


def test_confirm_go_constant() -> None:
    assert CONFIRM_GO == "GO_OFFLINE_PANEL_MATERIALIZATION_FROM_PARTIAL_TMP_NO_FETCH_V0"


def test_binding_config_loads_canonical_owners() -> None:
    config = load_offline_panel_materialization_config_v0(_REPO_ROOT)
    assert config["source_owner"] == SOURCE_OWNER
    assert config["funding_owner"] == FUNDING_OWNER
    assert config["preflight_owner"] == PREFLIGHT_OWNER
    assert config["partial_tmp_slug"] == DEFAULT_PARTIAL_TMP_SLUG


def test_resolve_partial_tmp_explicit_missing() -> None:
    missing = Path(tempfile.mkdtemp(prefix="missing_partial_")) / "missing"
    resolution = resolve_partial_tmp_root_v0(
        Path(tempfile.mkdtemp(prefix="durable_")),
        explicit_partial_tmp_root=missing,
    )
    assert REASON_PARTIAL_TMP_MISSING in resolution.reason_codes


def test_resolve_partial_tmp_ambiguous_without_slug() -> None:
    durable = Path(tempfile.mkdtemp(prefix="durable_ambiguous_"))
    dataset_parent = (
        durable / "datasets/admissible_futures/"
        "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1"
    )
    dataset_parent.mkdir(parents=True)
    (dataset_parent / ".tmp_historical_a").mkdir()
    (dataset_parent / ".tmp_historical_b").mkdir()
    resolution = resolve_partial_tmp_root_v0(durable)
    assert REASON_EVIDENCE_AMBIGUOUS in resolution.reason_codes


def test_prepare_funding_binding_blocks_fetch() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="funding_fetch_guard_"))
    staging = tmp / "staging"
    panel = build_synthetic_ohlcv_panel_v0()
    panel_dir = staging / "panel"
    panel_dir.mkdir(parents=True)
    rows = []
    for series in panel:
        for bar in series.bars:
            rows.append(
                {
                    "instrument_id": bar.instrument_id,
                    "timestamp_utc": bar.timestamp_utc,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "is_final": bar.is_final,
                }
            )
    (panel_dir / "normalized_panel_bars.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (panel_dir / "panel_dataset_manifest.json").write_text(
        json.dumps(
            {
                "instrument_ids": [series.instrument_id for series in panel],
                "panel_calendar_start_utc": PANEL_CALENDAR_START_UTC,
                "panel_calendar_end_utc": PANEL_CALENDAR_END_UTC,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    result = prepare_funding_binding_for_panel_members_v0(staging, skip_fetch=False)
    assert REASON_FETCH_GUARD_BLOCKED in result.reason_codes


def test_prepare_funding_binding_detects_scope_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1, PanelBarV1

    tmp = Path(tempfile.mkdtemp(prefix="funding_scope_drift_"))
    staging = tmp / "staging"
    panel_dir = staging / "panel"
    panel_dir.mkdir(parents=True)
    bar = PanelBarV1(
        instrument_id="okx:linear_perpetual:AAA:USDT:USDT:perp",
        timestamp_utc=PANEL_CALENDAR_START_UTC,
        open="1",
        high="1",
        low="1",
        close="1",
        volume="1",
        is_final=True,
    )
    series = InstrumentPanelSeriesV1(
        instrument_id=bar.instrument_id,
        native_instrument_id="AAA-USDT-SWAP",
        bars=(bar,),
        series_digest="0" * 64,
    )

    def _fake_load_panel_series(
        _staging_root: Path,
    ) -> tuple[tuple[InstrumentPanelSeriesV1, ...], str]:
        return (series,), "test:panel_ref"

    monkeypatch.setattr(
        "src.research.offline_panel_materialization_from_partial_tmp_no_fetch_v0.load_panel_series_from_staging",
        _fake_load_panel_series,
    )
    monkeypatch.setattr(
        "scripts.ops.materialize_cross_sectional_funding_rate_carry_v0_bound_panel_funding_dataset_v0.materialize_bound_panel_funding_dataset_v0",
        lambda **kwargs: {"verdict": "BOUND_FUNDING_PANEL_READY"},
    )

    (panel_dir / "panel_funding_dataset_manifest.json").write_text(
        json.dumps(
            {
                "instrument_ids": [
                    "okx:linear_perpetual:AAA:USDT:USDT:perp",
                    "okx:linear_perpetual:BBB:USDT:USDT:perp",
                ],
                "funding_panel_digest": "0" * 64,
                "row_count_total": 0,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    result = prepare_funding_binding_for_panel_members_v0(staging, skip_fetch=True)
    assert result.scope_drift is True
    assert REASON_FUNDING_SCOPE_DRIFT in result.reason_codes


@pytest.mark.skipif(not _PARTIAL_TMP_ROOT.is_dir(), reason="partial tmp unavailable")
def test_materialize_offline_panel_from_partial_tmp_live_probe() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="offline_panel_materialization_live_"))
    output = tmp / "extended_chronological_v1"
    result = materialize_offline_panel_from_partial_tmp_v0(_PARTIAL_TMP_ROOT, output)
    assert result.status is BoundPeriodSourceMaterializationStatus.MATERIALIZED
    assert result.instrument_count >= 5
    assert (output / "panel" / "normalized_panel_bars.json").is_file()
    assert (output / "panel" / "panel_dataset_manifest.json").is_file()
    provenance = json.loads((output / "SOURCE_PROVENANCE.json").read_text(encoding="utf-8"))
    assert provenance["membership_filter"]["selected_count"] == result.instrument_count


def test_run_scope_fails_closed_on_missing_partial_tmp() -> None:
    durable = Path(tempfile.mkdtemp(prefix="offline_scope_missing_"))
    result = run_offline_panel_materialization_scope_v0(
        repo_root=_REPO_ROOT,
        durable_evidence_root=durable,
        partial_tmp_root=durable / "missing_partial_tmp",
    )
    assert result.verdict is OfflinePanelMaterializationVerdict.FAIL_CLOSED_PARTIAL_TMP
    assert result.fetch_run is False
    assert result.preflight_no_fetch is True
