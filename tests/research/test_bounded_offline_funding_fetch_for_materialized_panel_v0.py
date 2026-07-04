"""Contract tests for bounded offline funding fetch for materialized panel v0."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.research.bounded_offline_funding_fetch_for_materialized_panel_v0 import (
    CONFIRM_GO,
    REASON_FETCH_GUARD_BLOCKED,
    REASON_FUNDING_ALREADY_FETCHED,
    REASON_FUNDING_SCOPE_DRIFT,
    BoundedFundingFetchVerdict,
    clear_stale_skip_fetch_funding_artifacts_v0,
    compute_funding_coverage_report_v0,
    load_bounded_funding_fetch_config_v0,
    load_panel_member_binding_v0,
    run_bounded_offline_funding_fetch_scope_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (
    PANEL_CALENDAR_END_UTC,
    PANEL_CALENDAR_START_UTC,
)
from src.research.csf_rdm_v0_extended_chronological_v1_staging_funding_panel_materialization_v0 import (
    CANONICAL_FUNDING_OWNER,
    CANONICAL_PREFLIGHT_OWNER,
)
from tests.research.fixtures.cross_sectional_funding_rate_delta_momentum_v0.fixture_builder import (
    build_synthetic_ohlcv_panel_v0,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    "extended_chronological_v1"
)


def test_confirm_go_constant() -> None:
    assert CONFIRM_GO == "GO_BOUNDED_OFFLINE_FUNDING_FETCH_FOR_MATERIALIZED_PANEL_V0"


def test_binding_config_loads_canonical_owners() -> None:
    config = load_bounded_funding_fetch_config_v0(_REPO_ROOT)
    assert config["funding_owner"] == CANONICAL_FUNDING_OWNER
    assert config["preflight_owner"] == CANONICAL_PREFLIGHT_OWNER


def test_run_scope_blocks_invalid_go_token() -> None:
    durable = Path(tempfile.mkdtemp(prefix="bounded_funding_fetch_go_"))
    result = run_bounded_offline_funding_fetch_scope_v0(
        repo_root=_REPO_ROOT,
        durable_evidence_root=durable,
        staging_root=durable / "missing",
        confirm_go="INVALID",
        execute_fetch=False,
    )
    assert result.verdict is BoundedFundingFetchVerdict.FAIL_CLOSED_FETCH
    assert REASON_FETCH_GUARD_BLOCKED in result.reason_codes


def test_clear_stale_skip_fetch_artifacts() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="clear_stale_funding_"))
    staging = tmp / "staging"
    panel_dir = staging / "panel"
    panel_dir.mkdir(parents=True)
    (panel_dir / "panel_funding_dataset_manifest.json").write_text(
        json.dumps({"fetched_from_okx_public": False}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (panel_dir / "normalized_panel_bars_with_funding.json").write_text("{}\n", encoding="utf-8")
    removed, notes = clear_stale_skip_fetch_funding_artifacts_v0(staging)
    assert removed is True
    assert REASON_FUNDING_ALREADY_FETCHED not in notes
    assert not (panel_dir / "panel_funding_dataset_manifest.json").is_file()


def test_clear_stale_blocks_complete_fetch() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="clear_already_fetched_"))
    staging = tmp / "staging"
    panel_dir = staging / "panel"
    panel_dir.mkdir(parents=True)
    (panel_dir / "panel_funding_dataset_manifest.json").write_text(
        json.dumps(
            {
                "fetched_from_okx_public": True,
                "row_count_total": 10,
                "missing_funding_count": 0,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    removed, notes = clear_stale_skip_fetch_funding_artifacts_v0(staging)
    assert removed is False
    assert REASON_FUNDING_ALREADY_FETCHED in notes


def test_clear_stale_allows_incomplete_fetch_retry() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="clear_incomplete_fetch_"))
    staging = tmp / "staging"
    panel_dir = staging / "panel"
    panel_dir.mkdir(parents=True)
    (panel_dir / "panel_funding_dataset_manifest.json").write_text(
        json.dumps(
            {
                "fetched_from_okx_public": True,
                "row_count_total": 10,
                "missing_funding_count": 10,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    removed, notes = clear_stale_skip_fetch_funding_artifacts_v0(staging)
    assert removed is True
    assert REASON_FUNDING_ALREADY_FETCHED not in notes


def test_compute_funding_coverage_from_synthetic_staging() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="coverage_synthetic_"))
    staging = tmp / "staging"
    panel = build_synthetic_ohlcv_panel_v0()
    panel_dir = staging / "panel"
    panel_dir.mkdir(parents=True)
    funding_rows = []
    for series in panel:
        for bar in series.bars:
            funding_rows.append(
                {
                    "instrument_id": bar.instrument_id,
                    "native_instrument_id": series.native_instrument_id,
                    "timestamp_utc": bar.timestamp_utc,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "funding_rate": "0.0001",
                    "missing_funding_reason": None,
                    "is_final": bar.is_final,
                }
            )
    digest = (
        __import__("hashlib")
        .sha256(json.dumps(funding_rows, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        .hexdigest()
    )
    (panel_dir / "normalized_panel_bars_with_funding.json").write_text(
        json.dumps({"bars": funding_rows}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (panel_dir / "panel_funding_dataset_manifest.json").write_text(
        json.dumps(
            {
                "instrument_ids": [series.instrument_id for series in panel],
                "row_count_total": len(funding_rows),
                "missing_funding_count": 0,
                "funding_panel_digest": digest,
                "fetched_from_okx_public": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    coverage = compute_funding_coverage_report_v0(staging)
    assert coverage.row_count_total == len(funding_rows)
    assert coverage.missing_funding_count == 0
    assert coverage.coverage_ratio == 1.0


@pytest.mark.skipif(
    not _STAGING_ROOT.is_dir(), reason="extended_chronological_v1 staging unavailable"
)
def test_load_panel_member_binding_live_probe() -> None:
    binding = load_panel_member_binding_v0(_STAGING_ROOT)
    assert binding.panel_member_count == 118
    assert binding.panel_calendar_start_utc == PANEL_CALENDAR_START_UTC
    assert binding.panel_calendar_end_utc == PANEL_CALENDAR_END_UTC


@pytest.mark.skipif(
    not _STAGING_ROOT.is_dir(), reason="extended_chronological_v1 staging unavailable"
)
def test_run_scope_dry_run_live_probe() -> None:
    durable = Path(tempfile.mkdtemp(prefix="bounded_funding_fetch_dry_"))
    result = run_bounded_offline_funding_fetch_scope_v0(
        repo_root=_REPO_ROOT,
        durable_evidence_root=durable,
        staging_root=_STAGING_ROOT,
        binding_origin_main_sha="4198febdf4100f718a0cd647b69fabdb2196638a",
        execute_fetch=False,
    )
    assert result.panel_binding is not None
    assert result.panel_binding.panel_member_count == 118
    assert result.fetch_run is False
    assert result.network_fetch_run is False
    assert REASON_FUNDING_SCOPE_DRIFT not in result.reason_codes


def test_run_scope_detects_scope_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.research.bounded_offline_funding_fetch_for_materialized_panel_v0 import (
        PanelMemberBindingV0,
    )

    tmp = Path(tempfile.mkdtemp(prefix="scope_drift_fetch_"))
    staging = tmp / "staging"
    panel_dir = staging / "panel"
    panel_dir.mkdir(parents=True)
    (panel_dir / "panel_dataset_manifest.json").write_text("{}\n", encoding="utf-8")

    binding = PanelMemberBindingV0(
        staging_root=str(staging),
        panel_member_count=2,
        instrument_ids=(
            "okx:linear_perpetual:AAA:USDT:USDT:perp",
            "okx:linear_perpetual:BBB:USDT:USDT:perp",
        ),
        native_instrument_ids=("AAA-USDT-SWAP", "BBB-USDT-SWAP"),
        panel_calendar_start_utc=PANEL_CALENDAR_START_UTC,
        panel_calendar_end_utc=PANEL_CALENDAR_END_UTC,
        panel_dataset_manifest_path=str(panel_dir / "panel_dataset_manifest.json"),
    )

    monkeypatch.setattr(
        "src.research.bounded_offline_funding_fetch_for_materialized_panel_v0.load_panel_member_binding_v0",
        lambda _staging_root: binding,
    )
    monkeypatch.setattr(
        "src.research.bounded_offline_funding_fetch_for_materialized_panel_v0.load_panel_series_from_staging",
        lambda _staging_root: (
            (
                __import__(
                    "src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1",
                    fromlist=["InstrumentPanelSeriesV1"],
                ).InstrumentPanelSeriesV1(
                    instrument_id="okx:linear_perpetual:AAA:USDT:USDT:perp",
                    native_instrument_id="AAA-USDT-SWAP",
                    bars=(),
                    series_digest="0" * 64,
                ),
            ),
            "test:panel_ref",
        ),
    )
    monkeypatch.setattr(
        "src.research.bounded_offline_funding_fetch_for_materialized_panel_v0.run_dataset_funding_binding_materialization_preflight_v0",
        lambda **kwargs: __import__(
            "types",
            fromlist=["SimpleNamespace"],
        ).SimpleNamespace(
            status=__import__(
                "src.research.csf_rdm_v0_dataset_funding_binding_materialization_preflight_v0",
                fromlist=["PreflightTerminalStatus"],
            ).PreflightTerminalStatus.FAIL_CLOSED_BOUND_DATA_UNAVAILABLE,
            ready_for_next_pre_evaluation_gate=False,
            reason_codes=("BOUND_DATA_UNAVAILABLE",),
        ),
    )
    monkeypatch.setattr(
        "src.research.bounded_offline_funding_fetch_for_materialized_panel_v0.preflight_result_to_dict",
        lambda preflight: {
            "status": str(preflight.status.value),
            "ready_for_next_pre_evaluation_gate": preflight.ready_for_next_pre_evaluation_gate,
            "reason_codes": list(preflight.reason_codes),
        },
    )

    result = run_bounded_offline_funding_fetch_scope_v0(
        repo_root=_REPO_ROOT,
        durable_evidence_root=tmp,
        staging_root=staging,
        execute_fetch=False,
    )
    assert result.verdict is BoundedFundingFetchVerdict.FAIL_CLOSED_PANEL_BINDING
    assert REASON_FUNDING_SCOPE_DRIFT in result.reason_codes
