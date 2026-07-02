"""STEP30A dataset v2 promotion from verified raw staging v0 tests."""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
STAGING_SCRIPT = (
    ROOT / "scripts/ops/stage_step30a_okx_inst_eth_usdt_perp_dataset_v2_from_raw_staging_v0.py"
)
RAW_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/inst-eth-usdt-perp/.tmp_20260702T050638Z"
)
V2_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/inst-eth-usdt-perp/v2"
)


def _load_mod():
    spec = importlib.util.spec_from_file_location("_step30a_stage_v2", STAGING_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _minimal_raw_tree(tmp_path: Path) -> Path:
    if not RAW_ROOT.is_dir():
        pytest.skip("authorized raw staging cache unavailable")
    dst = tmp_path / "raw_staging"
    shutil.copytree(RAW_ROOT, dst)
    return dst


def test_missing_historical_l1_reason_constant() -> None:
    mod = _load_mod()
    from src.backtest import admissible_versioned_futures_dataset_v1 as ds

    assert mod.MISSING_HISTORICAL_L1_REASON == (
        ds.MissingHistoricalL1ReasonV1.NOT_AVAILABLE_BY_PUBLIC_SOURCE.value
    )


def test_holdout_constants_match_step29m_frozen() -> None:
    mod = _load_mod()
    mod.verify_holdout_constants_match_step29m_v1()


def test_resolve_verified_raw_staging_root_v1() -> None:
    if not RAW_ROOT.is_dir():
        pytest.skip("authorized raw staging cache unavailable")
    mod = _load_mod()
    resolved = mod.resolve_verified_raw_staging_root_v1(RAW_ROOT.parent)
    assert resolved.is_dir()
    assert resolved.name.startswith(".tmp_")


def test_holdout_access_guard_blocks_full_dataset_before_evaluation(tmp_path: Path) -> None:
    mod = _load_mod()
    raw_root = _minimal_raw_tree(tmp_path)
    config = json.loads((raw_root / "INGESTION_CONFIG.json").read_text())
    bars, report = __import__(
        "scripts.ops.stage_okx_economic_research_dataset_from_raw_staging_v1",
        fromlist=["normalize_economic_research_bars"],
    ).normalize_economic_research_bars(
        raw_dir=raw_root / "raw",
        start_utc=config["data_period"]["start_utc"],
        end_utc=config["data_period"]["end_utc"],
    )
    assert report.passed
    with pytest.raises(mod.Step30aDatasetPromotionError, match="holdout_access_blocked"):
        mod.assert_holdout_access_blocked_v1(bars, evaluation_authorized=False)
    development = mod.slice_development_partition_v1(bars)
    assert (development.index >= pd.Timestamp(mod.STEP30A_FROZEN_HOLDOUT_START_UTC)).sum() == 0


def test_deterministic_partition_digests(tmp_path: Path) -> None:
    mod = _load_mod()
    raw_root = _minimal_raw_tree(tmp_path)
    config = json.loads((raw_root / "INGESTION_CONFIG.json").read_text())
    staging = __import__(
        "scripts.ops.stage_okx_economic_research_dataset_from_raw_staging_v1",
        fromlist=["normalize_economic_research_bars"],
    )
    bars_a, report_a = staging.normalize_economic_research_bars(
        raw_dir=raw_root / "raw",
        start_utc=config["data_period"]["start_utc"],
        end_utc=config["data_period"]["end_utc"],
    )
    bars_b, report_b = staging.normalize_economic_research_bars(
        raw_dir=raw_root / "raw",
        start_utc=config["data_period"]["start_utc"],
        end_utc=config["data_period"]["end_utc"],
    )
    assert report_a.passed and report_b.passed
    from src.backtest import admissible_versioned_futures_dataset_v1 as ds

    bindings = ds.field_bindings_for_profile(ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1)
    digests_a = mod.compute_partition_digests_v1(bars_a, field_bindings=bindings)
    digests_b = mod.compute_partition_digests_v1(bars_b, field_bindings=bindings)
    assert digests_a == digests_b


def test_promoted_v2_manifest_binds_missing_l1_reason() -> None:
    if not V2_ROOT.is_dir():
        pytest.skip("dataset v2 not promoted")
    manifest = json.loads((V2_ROOT / "dataset_manifest.json").read_text())
    assert manifest["dataset_version"] == "v2"
    assert manifest["dataset_schema_version"] == "v2"
    assert manifest["missing_historical_l1_reason"] == "NOT_AVAILABLE_BY_PUBLIC_SOURCE"
    assert "best_bid" not in manifest["required_columns"]
    assert "best_ask" not in manifest["required_columns"]


def test_runtime_profile_still_requires_l1() -> None:
    from src.backtest import admissible_versioned_futures_dataset_v1 as ds

    idx = pd.date_range("2026-06-01", periods=4, freq="1h", tz="UTC")
    close = [100.0, 101.0, 102.0, 103.0]
    bars = pd.DataFrame(
        {
            "open": close,
            "high": close,
            "low": close,
            "close": close,
            "volume": [1.0] * 4,
            "mark_price": close,
            "index_price": close,
            "funding_rate": [0.0001] * 4,
            "is_final": [True] * 4,
        },
        index=idx,
    )
    bindings = ds.field_bindings_for_profile(ds.DatasetProfileV1.RUNTIME_MARKET_CONTEXT_V1)
    digest = ds.compute_versioned_dataset_digest(bars, field_bindings=bindings)
    train, val, oos = ds.compute_split_periods_from_bars(bars)
    descriptor = ds.VersionedFuturesDatasetDescriptorV1(
        dataset_id="fixture",
        dataset_version="v1",
        dataset_schema_version="v1",
        dataset_digest=digest,
        instrument_id="inst-eth-usdt-perp",
        contract_type="perpetual",
        futures_only=True,
        bitcoin_direction_allowed=False,
        venue_id="OKX",
        start_time=str(idx[0]),
        end_time=str(idx[-1]),
        row_count=len(bars),
        field_bindings=bindings,
        training_period=train,
        validation_period=val,
        out_of_sample_period=oos,
        split_policy_version=ds.SPLIT_POLICY_VERSION,
        timestamp_semantics=ds.TIMESTAMP_SEMANTICS,
        timezone=ds.TIMEZONE,
        ordering_status=ds.ORDERING_STATUS_SORTED,
        duplicate_policy=ds.DUPLICATE_POLICY,
        missing_data_policy=ds.MISSING_DATA_POLICY,
    )
    provenance = ds.DatasetProvenanceV1(
        source_type="fixture",
        venue_id="OKX",
        ingestion_timestamp="1970-01-01T00:00:00+00:00",
        generation_method="fixture",
        provenance_ref="fixture",
    )
    result = ds.evaluate_admissible_versioned_futures_dataset_v1(
        bars=bars,
        descriptor=descriptor,
        provenance=provenance,
        instrument_id="inst-eth-usdt-perp",
        profile_binding=ds.default_runtime_profile_binding_v1(),
    )
    assert result.admissibility_status is ds.AdmissibilityStatus.BLOCKED_L1_REQUIRED_FOR_RUNTIME
