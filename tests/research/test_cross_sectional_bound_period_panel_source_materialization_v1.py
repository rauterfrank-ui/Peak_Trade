"""Contract tests for cross_sectional_bound_period_panel_source_materialization_v1."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.research.cross_sectional_bound_period_panel_source_materialization_v1 import (
    REASON_CONFLICTING_DUPLICATE_CANDLES,
    REASON_NO_ELIGIBLE_RAW_SERIES,
    BoundPeriodSourceMaterializationStatus,
    _canonicalize_swap_instrument,
    group_raw_paths_by_native_instrument_v1,
    materialize_bound_period_panel_from_raw_sources_v1,
    merge_okx_candle_rows_with_dedup_v1,
    parse_native_instrument_id_from_raw_filename,
)
from src.research.cross_sectional_panel_staging_source_manifest_v1 import (
    SourceManifestStatus,
    materialize_panel_staging_source_manifests_v1,
    verify_panel_staging_source_manifests_v1,
)
from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (
    MaterializationTerminalStatus,
    materialize_bound_panel_dataset_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    build_period_binding_v0,
)
from src.research.okx_production_instrument_lifecycle_source_v1 import (
    evaluate_okx_instrument_eligibility_v1,
)

BOUND_START = "2024-05-30T20:00:00Z"
BOUND_END = "2024-06-01T01:00:00Z"


def _ts_ms(ts: str) -> str:
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return str(int(dt.timestamp() * 1000))


def _okx_row(ts: str, close: str = "1.0") -> list[str]:
    return [_ts_ms(ts), close, close, close, close, "100", "100", "100", "1"]


def _live_swap(base: str, *, base_ccy: str = "") -> dict[str, str]:
    return {
        "instId": f"{base}-USDT-SWAP",
        "instType": "SWAP",
        "settleCcy": "USDT",
        "ctType": "linear",
        "baseCcy": base_ccy,
        "state": "live",
        "listTime": "1609459200000",
        "expTime": "",
    }


def _write_instruments_snapshot(raw_dir: Path, instruments: list[dict[str, str]]) -> None:
    payload = {"code": "0", "data": instruments}
    (raw_dir / "instruments_all_swap_test0000000000000001.json").write_text(
        json.dumps(payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_raw_page(
    raw_dir: Path,
    *,
    base: str,
    page: int,
    rows: list[list[str]],
) -> Path:
    path = raw_dir / f"ohlcv_{base.lower()}_usdt_swap_p{page:04d}_{'a' * 16}.json"
    path.write_text(
        json.dumps({"code": "0", "data": rows}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _bound_hourly_rows(start: str, end: str) -> list[list[str]]:
    from datetime import timedelta

    start_dt = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    rows: list[list[str]] = []
    cursor = start_dt
    while cursor <= end_dt:
        rows.append(_okx_row(cursor.strftime("%Y-%m-%dT%H:%M:%SZ")))
        cursor += timedelta(hours=1)
    return rows


class TestEmptyBaseCcyRecovery:
    def test_empty_base_ccy_maps_to_expected_canonical_id(self) -> None:
        inst = _live_swap("1INCH", base_ccy="")
        pair = _canonicalize_swap_instrument(inst)
        assert pair is not None
        instrument_id, native_id = pair
        assert native_id == "1INCH-USDT-SWAP"
        assert instrument_id == "okx:linear_perpetual:1INCH:USDT:USDT:perp"

    def test_bitcoin_instrument_still_excluded_with_empty_base_ccy(self) -> None:
        inst = _live_swap("BTC", base_ccy="")
        assert _canonicalize_swap_instrument(inst) is None
        result = evaluate_okx_instrument_eligibility_v1(inst)
        assert not result.eligible


class TestLifecycleMaterializerParity:
    def test_same_native_contract_canonicalized_identically(self) -> None:
        inst = _live_swap("AAVE", base_ccy="")
        lifecycle = evaluate_okx_instrument_eligibility_v1(inst)
        materializer = _canonicalize_swap_instrument(inst)
        assert lifecycle.eligible
        assert materializer is not None
        assert materializer[0] == lifecycle.instrument_id
        assert materializer[1] == lifecycle.metadata.inst_id


class TestPaginationMerge:
    def test_single_pages_partial_merged_series_full_bound_coverage(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="cs_rs_mat_pagination_"))
        source_root = tmp / "source"
        raw_dir = source_root / "raw"
        raw_dir.mkdir(parents=True)
        bases = ("AAA", "BBB", "CCC", "DDD", "EEE")
        instruments = [_live_swap(base, base_ccy="") for base in bases]
        _write_instruments_snapshot(raw_dir, instruments)

        all_rows = _bound_hourly_rows(BOUND_START, BOUND_END)
        split_at = len(all_rows) // 2
        early_rows = all_rows[:split_at]
        late_rows = all_rows[split_at:]
        for base in bases:
            _write_raw_page(raw_dir, base=base, page=0, rows=early_rows)
            _write_raw_page(raw_dir, base=base, page=1, rows=late_rows)

        lifecycle = source_root / "lifecycle"
        lifecycle.mkdir(parents=True)
        (lifecycle / "SOURCE_REGISTRATION.json").write_text(
            json.dumps({"source_snapshot_digest": "d" * 64}, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        output_root = tmp / "output"
        result = materialize_bound_period_panel_from_raw_sources_v1(
            source_root,
            output_root,
            period_binding=build_period_binding_v0(),
        )
        assert result.status is BoundPeriodSourceMaterializationStatus.MATERIALIZED
        assert result.instrument_count == 5
        assert result.period_start_utc == BOUND_START
        assert result.period_end_utc == BOUND_END
        assert result.data_start_time == BOUND_START
        assert result.data_end_time == BOUND_END


class TestDuplicateHandling:
    def test_identical_duplicate_rows_deduped_idempotently(self) -> None:
        row = _okx_row("2024-05-30T20:00:00Z")
        merged, error = merge_okx_candle_rows_with_dedup_v1([row, row])
        assert error is None
        assert len(merged) == 1

    def test_conflicting_duplicate_rows_fail_closed(self) -> None:
        row_a = _okx_row("2024-05-30T20:00:00Z", close="1.0")
        row_b = _okx_row("2024-05-30T20:00:00Z", close="2.0")
        merged, error = merge_okx_candle_rows_with_dedup_v1([row_a, row_b])
        assert not merged
        assert error == REASON_CONFLICTING_DUPLICATE_CANDLES

    def test_conflicting_duplicates_abort_materialization(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="cs_rs_mat_dup_conflict_"))
        source_root = tmp / "source"
        raw_dir = source_root / "raw"
        raw_dir.mkdir(parents=True)
        instruments = [
            _live_swap(base, base_ccy="") for base in ("AAA", "BBB", "CCC", "DDD", "EEE")
        ]
        _write_instruments_snapshot(raw_dir, instruments)
        row = _okx_row("2024-05-30T20:00:00Z")
        _write_raw_page(
            raw_dir, base="AAA", page=0, rows=[row, _okx_row("2024-05-30T20:00:00Z", "9.9")]
        )
        for base in ("BBB", "CCC", "DDD", "EEE"):
            _write_raw_page(
                raw_dir,
                base=base,
                page=0,
                rows=_bound_hourly_rows(BOUND_START, BOUND_END),
            )

        result = materialize_bound_period_panel_from_raw_sources_v1(
            source_root,
            tmp / "output",
            period_binding=build_period_binding_v0(),
        )
        assert (
            result.status
            is BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED
        )
        assert REASON_CONFLICTING_DUPLICATE_CANDLES in result.reason_codes


class TestIsolation:
    def test_grouping_keeps_instruments_separate(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="cs_rs_mat_isolation_"))
        raw_dir = tmp / "raw"
        raw_dir.mkdir(parents=True)
        _write_raw_page(raw_dir, base="AAA", page=0, rows=[_okx_row("2024-05-30T20:00:00Z")])
        _write_raw_page(raw_dir, base="BBB", page=0, rows=[_okx_row("2024-05-31T12:00:00Z")])
        grouped = group_raw_paths_by_native_instrument_v1(raw_dir)
        assert set(grouped) == {"AAA-USDT-SWAP", "BBB-USDT-SWAP"}
        assert (
            parse_native_instrument_id_from_raw_filename(grouped["AAA-USDT-SWAP"][0].name)
            == "AAA-USDT-SWAP"
        )


class TestRegression:
    def test_non_empty_base_ccy_still_canonicalizes(self) -> None:
        inst = _live_swap("ETH", base_ccy="ETH")
        pair = _canonicalize_swap_instrument(inst)
        assert pair is not None
        assert pair[0] == "okx:linear_perpetual:ETH:USDT:USDT:perp"

    def test_missing_inst_id_remains_fail_closed(self) -> None:
        assert _canonicalize_swap_instrument({"instType": "SWAP"}) is None


class TestEndToEndBoundPeriodFixture:
    def test_paginated_empty_base_ccy_fixture_materializes_and_passes_dataset_gate(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="cs_rs_mat_e2e_"))
        source_root = tmp / "source"
        raw_dir = source_root / "raw"
        raw_dir.mkdir(parents=True)
        bases = ("AAA", "BBB", "CCC", "DDD", "EEE")
        instruments = [_live_swap(base, base_ccy="") for base in bases]
        _write_instruments_snapshot(raw_dir, instruments)

        for base in bases:
            all_rows = _bound_hourly_rows(BOUND_START, BOUND_END)
            split_at = len(all_rows) // 2
            _write_raw_page(raw_dir, base=base, page=0, rows=all_rows[:split_at])
            _write_raw_page(raw_dir, base=base, page=1, rows=all_rows[split_at:])

        lifecycle = source_root / "lifecycle"
        lifecycle.mkdir(parents=True)
        (lifecycle / "SOURCE_REGISTRATION.json").write_text(
            json.dumps({"source_snapshot_digest": "e" * 64}, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        output_root = tmp / "output"
        source_result = materialize_bound_period_panel_from_raw_sources_v1(
            source_root,
            output_root,
            period_binding=build_period_binding_v0(),
        )
        assert source_result.status is BoundPeriodSourceMaterializationStatus.MATERIALIZED
        assert source_result.instrument_count >= 5
        assert REASON_NO_ELIGIBLE_RAW_SERIES not in source_result.reason_codes

        manifest_result = materialize_panel_staging_source_manifests_v1(output_root)
        assert manifest_result.status is SourceManifestStatus.VERIFIED
        ok, _, _ = verify_panel_staging_source_manifests_v1(output_root)
        assert ok

        dataset_result = materialize_bound_panel_dataset_v0(
            output_root,
            period_binding=build_period_binding_v0(),
        )
        assert (
            dataset_result.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
        )
        assert dataset_result.instrument_count >= 5
