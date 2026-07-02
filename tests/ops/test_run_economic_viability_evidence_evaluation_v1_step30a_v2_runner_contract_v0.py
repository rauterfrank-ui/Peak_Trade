"""Runner contract tests for STEP30A flat economic_research_v1 dataset v2 acceptance."""

from __future__ import annotations

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.backtest import admissible_versioned_futures_dataset_v1 as ds

ROOT = Path(__file__).resolve().parents[2]
RUNNER_SCRIPT = ROOT / "scripts" / "ops" / "run_economic_viability_evidence_evaluation_v1.py"
STEP30A_CONFIG = (
    ROOT / "config/ops/step30a_okx_inst_eth_usdt_perp_rsi_reversion_v1_economic_evaluation_v1.json"
)
ARCHIVE_MANIFEST = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/inst-eth-usdt-perp/v2/dataset_manifest.json"
)

TRAINING_PERIOD = "2026-04-02 10:07:00+00:00..2026-05-18 23:59:00+00:00"
VALIDATION_PERIOD = "2026-05-19 00:00:00+00:00..2026-06-16 23:59:00+00:00"
OUT_OF_SAMPLE_PERIOD = "2026-06-17 10:07:00+00:00..2026-07-01 10:07:00+00:00"
DEVELOPMENT_PERIOD = "2026-04-02 10:07:00+00:00..2026-06-16 23:59:00+00:00"
DEV_DIGEST = "544d1e10987d42a82c834c5580f6424aaf01b4d7762fb08be10dbb3094e38d22"
HOLDOUT_DIGEST = "8612a4cccf5cf321eeb577ed1b6df14417277738f43423cbf152c98d330aa3e4"


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_economic_viability_evidence_evaluation_v1", RUNNER_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _research_bars() -> pd.DataFrame:
    train_idx = pd.date_range("2026-04-02 11:00:00", periods=8, freq="1h", tz="UTC")
    val_idx = pd.date_range("2026-05-19 01:00:00", periods=8, freq="1h", tz="UTC")
    oos_idx = pd.date_range("2026-06-17 11:00:00", periods=8, freq="1h", tz="UTC")
    idx = train_idx.append(val_idx).append(oos_idx)
    close = [100.0 + float(i) for i in range(len(idx))]
    return pd.DataFrame(
        {
            "open": close,
            "high": [v + 0.5 for v in close],
            "low": [v - 0.5 for v in close],
            "close": close,
            "volume": [1000.0 for _ in close],
            "mark_price": close,
            "index_price": [v - 0.1 for v in close],
            "funding_rate": [0.0001 for _ in close],
            "is_final": [True for _ in close],
        },
        index=idx,
    )


def _flat_v2_manifest(bars: pd.DataFrame, **overrides: Any) -> dict[str, Any]:
    bindings = ds.field_bindings_for_profile(ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1)
    digest = ds.compute_versioned_dataset_digest(bars, field_bindings=bindings)
    payload: dict[str, Any] = {
        "manifest_version": "admissible_versioned_futures_dataset_manifest_v1",
        "dataset_profile": "economic_research_v1",
        "dataset_version": "v2",
        "dataset_schema_version": "v2",
        "instrument_id": "inst-eth-usdt-perp",
        "contract_type": "perpetual",
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "normalized_dataset_digest": digest,
        "development_partition_digest": DEV_DIGEST,
        "frozen_holdout_digest": HOLDOUT_DIGEST,
        "development_period": DEVELOPMENT_PERIOD,
        "training_period": TRAINING_PERIOD,
        "validation_period": VALIDATION_PERIOD,
        "out_of_sample_period": OUT_OF_SAMPLE_PERIOD,
        "row_count": len(bars),
        "l1_observation_status": "EXECUTION_MODEL_BOUND_NOT_OBSERVED",
        "observed_l1_used": False,
        "missing_historical_l1_reason": "NOT_AVAILABLE_BY_PUBLIC_SOURCE",
        "profile_binding": {
            "dataset_profile": "economic_research_v1",
            "l1_observation_status": "EXECUTION_MODEL_BOUND_NOT_OBSERVED",
            "execution_cost_binding": {
                "conservative_half_spread_bps": 5.0,
                "execution_price_observation_source": "MODELLED_NOT_OBSERVED",
                "spread_model_version": "research_conservative_bps_v1",
            },
        },
        "holdout_binding": {
            "development_partition_digest": DEV_DIGEST,
            "development_period": DEVELOPMENT_PERIOD,
            "frozen_holdout_digest": HOLDOUT_DIGEST,
            "frozen_holdout_period": OUT_OF_SAMPLE_PERIOD,
            "frozen_holdout_start_utc": "2026-06-17 10:07:00+00:00",
            "frozen_holdout_end_utc": "2026-07-01 10:07:00+00:00",
            "holdout_access_before_evaluation": "BLOCKED",
        },
        "integrity_results": {
            "integrity_pass": True,
            "dataset_admissible": True,
        },
        "data_period": {
            "start_utc": str(bars.index.min()),
            "end_utc": str(bars.index.max()),
        },
        "acquisition_timestamps": {
            "ingestion_timestamp_utc": "2026-07-02T05:15:27Z",
        },
        "provenance": {
            "source_type": "operator_staged_futures_v1",
            "venue_id": "OKX",
            "ingestion_timestamp": "2026-07-02T05:15:27Z",
            "generation_method": "step30a_okx_economic_research_dataset_v2_staging_v0",
            "provenance_ref": "datasets/admissible_futures/inst-eth-usdt-perp/v2/dataset_manifest.json",
        },
    }
    payload.update(overrides)
    runner = _load_runner()
    payload["manifest_digest"] = runner._compute_manifest_digest(payload)
    return payload


DatasetProfileV1 = ds.DatasetProfileV1


@pytest.fixture(scope="module")
def runner():
    return _load_runner()


def test_v2_manifest_contract_accepts_valid_fixture() -> None:
    bars = _research_bars()
    manifest = _flat_v2_manifest(bars)
    assert not ds.validate_flat_economic_research_v2_runner_manifest_contract_v1(manifest)


def test_v2_manifest_contract_rejects_v3() -> None:
    bars = _research_bars()
    manifest = _flat_v2_manifest(bars, dataset_version="v3")
    reasons = ds.validate_flat_economic_research_v2_runner_manifest_contract_v1(manifest)
    assert "dataset_version_not_v2" in reasons


def test_v2_manifest_contract_rejects_unknown_schema() -> None:
    bars = _research_bars()
    manifest = _flat_v2_manifest(bars, dataset_schema_version="v999")
    reasons = ds.validate_flat_economic_research_v2_runner_manifest_contract_v1(manifest)
    assert "dataset_schema_version_not_v2" in reasons


def test_v2_manifest_contract_rejects_wrong_profile() -> None:
    bars = _research_bars()
    manifest = _flat_v2_manifest(bars, dataset_profile="runtime_market_context_v1")
    reasons = ds.validate_flat_economic_research_v2_runner_manifest_contract_v1(manifest)
    assert "dataset_profile_not_economic_research_v1" in reasons


def test_v2_manifest_contract_rejects_bad_dataset_digest() -> None:
    bars = _research_bars()
    manifest = _flat_v2_manifest(bars, normalized_dataset_digest="not-a-valid-digest")
    reasons = ds.validate_flat_economic_research_v2_runner_manifest_contract_v1(manifest)
    assert "normalized_dataset_digest_invalid" in reasons


def test_v2_manifest_contract_rejects_missing_holdout_block() -> None:
    bars = _research_bars()
    manifest = _flat_v2_manifest(bars)
    manifest["holdout_binding"] = dict(manifest["holdout_binding"])
    manifest["holdout_binding"]["holdout_access_before_evaluation"] = "ALLOWED"
    reasons = ds.validate_flat_economic_research_v2_runner_manifest_contract_v1(manifest)
    assert "holdout_access_before_evaluation_not_blocked" in reasons


def test_v2_manifest_contract_rejects_spot_instrument() -> None:
    bars = _research_bars()
    manifest = _flat_v2_manifest(bars, instrument_id="inst-eth-usdt-spot")
    reasons = ds.validate_flat_economic_research_v2_runner_manifest_contract_v1(manifest)
    assert "instrument_forbidden" in reasons


def test_descriptor_from_manifest_accepts_v2_fixture(runner) -> None:
    bars = _research_bars()
    manifest = _flat_v2_manifest(bars)
    descriptor = runner._descriptor_from_manifest(manifest)
    assert descriptor.dataset_version == "v2"
    assert descriptor.dataset_schema_version == "v2"


def test_descriptor_from_manifest_rejects_v3(runner) -> None:
    bars = _research_bars()
    manifest = _flat_v2_manifest(bars, dataset_version="v3")
    with pytest.raises(runner.RunnerError, match="dataset_version_unknown:v3"):
        runner._descriptor_from_manifest(manifest)


def test_v1_descriptor_behavior_unchanged(runner, tmp_path: Path) -> None:
    from tests.ops.test_run_economic_viability_evidence_evaluation_v1 import (  # noqa: PLC0415
        _bars,
        _manifest_payload,
    )

    bars = _bars()
    manifest = _manifest_payload(bars)
    descriptor = runner._descriptor_from_manifest(manifest)
    assert descriptor.dataset_version == ds.DEFAULT_DATASET_VERSION


def _argv(paths: dict[str, Path]) -> list[str]:
    return [
        "--dataset-path",
        str(paths["dataset_path"]),
        "--dataset-manifest-path",
        str(paths["manifest_path"]),
        "--config-path",
        str(paths["config_path"]),
        "--output-dir",
        str(paths["output_dir"]),
        "--run-id",
        "econ_evidence_eval_v1_4709c0fadd0ddb62",
    ]


def _generic_v2_evaluation_config() -> dict[str, Any]:
    return {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
            "funding": {"bind": True, "model_version": "backtest_funding_perpetual_interval_v1"},
            "parameter_sensitivity": {
                "bind": True,
                "grid_version": "v1",
                "grid": {
                    "grid_id": "runner_v2_contract_grid_v1",
                    "parameter_names": ["fee_bps", "slippage_bps"],
                    "parameter_values": [[8.0, 10.0], [4.0, 6.0]],
                    "search_space_bounds": {
                        "fee_bps": {"min": 8.0, "max": 10.0},
                        "slippage_bps": {"min": 4.0, "max": 6.0},
                    },
                    "seed": 42,
                },
            },
            "dataset_admissibility": {
                "bind": True,
                "dataset_profile": "economic_research_v1",
                "profile_binding": {
                    "dataset_profile": "economic_research_v1",
                    "l1_observation_status": "EXECUTION_MODEL_BOUND_NOT_OBSERVED",
                    "execution_cost_binding": {
                        "conservative_half_spread_bps": 5.0,
                        "execution_price_observation_source": "MODELLED_NOT_OBSERVED",
                        "spread_model_version": "research_conservative_bps_v1",
                    },
                },
            },
        },
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
        "economic_evaluation_v1": {
            "strategy_id": "rsi_reversion",
            "strategy_version": "v1",
            "strategy_params": {
                "rsi_window": 14,
                "lower": 30.0,
                "upper": 70.0,
                "price_col": "close",
            },
            "walk_forward": {"bind": True, "train_bars": 8, "test_bars": 4, "step_bars": 4},
            "monte_carlo": {"bind": True, "runs": 16, "seed": 42},
            "stress": {"bind": True},
        },
    }


def _stage_v2_inputs(tmp_path: Path, **manifest_overrides: Any) -> dict[str, Path]:
    bars = _research_bars()
    staging = tmp_path / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    dataset_path = staging / "bars.parquet"
    bars.to_parquet(dataset_path)
    manifest = _flat_v2_manifest(bars, **manifest_overrides)
    manifest_path = staging / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    config_path = staging / "evaluation_config.json"
    config_path.write_text(
        json.dumps(_generic_v2_evaluation_config(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"
    return {
        "dataset_path": dataset_path,
        "manifest_path": manifest_path,
        "config_path": config_path,
        "output_dir": output_dir,
    }


def test_v2_validate_only_passes_with_generic_config(runner, tmp_path: Path) -> None:
    paths = _stage_v2_inputs(tmp_path)
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc == 0
    assert not paths["output_dir"].exists()


def test_v2_validate_only_rejects_partition_digest_mismatch(runner, tmp_path: Path) -> None:
    paths = _stage_v2_inputs(tmp_path)
    config = json.loads(paths["config_path"].read_text(encoding="utf-8"))
    config["real_admissible_futures_evaluation_binding_v1"] = {
        "dataset_version": "v2",
        "canonical_instrument_id": "inst-eth-usdt-perp",
        "development_partition_digest": "f" * 64,
    }
    paths["config_path"].write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc != 0


ARCHIVE_BARS = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/inst-eth-usdt-perp/v2/bars.parquet"
)


@pytest.mark.skipif(
    not ARCHIVE_MANIFEST.is_file() or not ARCHIVE_BARS.is_file() or not STEP30A_CONFIG.is_file(),
    reason="STEP30A archive dataset/config unavailable",
)
def test_step30a_ratified_validate_only_preflight_probe(runner, tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    rc = runner.main(
        [
            "--dataset-path",
            str(ARCHIVE_BARS),
            "--dataset-manifest-path",
            str(ARCHIVE_MANIFEST),
            "--config-path",
            str(STEP30A_CONFIG),
            "--output-dir",
            str(output_dir),
            "--run-id",
            "econ_evidence_eval_v1_4709c0fadd0ddb62",
            "--validate-only",
        ]
    )
    assert rc == 0
    assert not output_dir.exists()


def test_v2_validate_only_rejects_config_count_not_one(runner, tmp_path: Path, monkeypatch) -> None:
    if not ARCHIVE_MANIFEST.is_file() or not ARCHIVE_BARS.is_file():
        pytest.skip("archive unavailable")
    monkeypatch.setattr(
        "src.backtest.step30a_rsi_reversion_v1_economic_evaluation_admissibility_contract_v1.STEP30A_REGISTERED_ECONOMIC_EVALUATION_CONFIGS_V1",
        (
            "config/ops/step30a_okx_inst_eth_usdt_perp_rsi_reversion_v1_economic_evaluation_v1.json",
            "config/ops/other.json",
        ),
    )
    output_dir = tmp_path / "output"
    rc = runner.main(
        [
            "--dataset-path",
            str(ARCHIVE_BARS),
            "--dataset-manifest-path",
            str(ARCHIVE_MANIFEST),
            "--config-path",
            str(STEP30A_CONFIG),
            "--output-dir",
            str(output_dir),
            "--run-id",
            "econ_evidence_eval_v1_4709c0fadd0ddb62",
            "--validate-only",
        ]
    )
    assert rc != 0


@pytest.mark.skipif(not ARCHIVE_MANIFEST.is_file(), reason="STEP30A archive manifest unavailable")
def test_step30a_archive_manifest_passes_descriptor(runner) -> None:
    manifest = json.loads(ARCHIVE_MANIFEST.read_text(encoding="utf-8"))
    descriptor = runner._descriptor_from_manifest(manifest, manifest_path=str(ARCHIVE_MANIFEST))
    assert descriptor.dataset_version == "v2"
    assert descriptor.instrument_id == "inst-eth-usdt-perp"


def test_v2_does_not_downgrade_to_v1(runner) -> None:
    bars = _research_bars()
    manifest = _flat_v2_manifest(bars)
    descriptor = runner._descriptor_from_manifest(manifest)
    assert descriptor.dataset_version != ds.DEFAULT_DATASET_VERSION
