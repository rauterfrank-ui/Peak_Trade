"""Tests for run_economic_viability_evidence_evaluation_v1 (offline STEP 29M runner)."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pandas as pd
import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.backtest import admissible_versioned_futures_dataset_v1 as ds
from src.backtest import economic_viability_evidence_v1 as ev
from src.backtest import mv2_research_wiring_v1 as wiring

ROOT = Path(__file__).resolve().parents[2]
RUNNER_SCRIPT = ROOT / "scripts" / "ops" / "run_economic_viability_evidence_evaluation_v1.py"
TEST_PACKAGE_MARKER = "RUN_ECONOMIC_VIABILITY_EVIDENCE_EVALUATION_V1_TEST=true"


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_economic_viability_evidence_evaluation_v1", RUNNER_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _bars(n: int = 24) -> pd.DataFrame:
    idx = pd.date_range("2026-06-01", periods=n, freq="1h", tz="UTC")
    close = [100.0 + float(i) for i in range(n)]
    return pd.DataFrame(
        {
            "open": close,
            "high": [v + 0.5 for v in close],
            "low": [v - 0.5 for v in close],
            "close": close,
            "mark_price": close,
            "index_price": [v - 0.1 for v in close],
            "best_bid": [v - 0.05 for v in close],
            "best_ask": [v + 0.05 for v in close],
            "spread": [0.1 for _ in close],
            "volume": [1000.0 for _ in close],
            "open_interest": [10000.0 for _ in close],
            "funding_rate": [0.0001 for _ in close],
            "volatility_estimate": [0.2 for _ in close],
            "is_final": [True for _ in close],
            "bar_interval": ["1h" for _ in close],
        },
        index=idx,
    )


def _provenance(**overrides: Any) -> dict[str, str]:
    payload = {
        "source_type": "operator_staged_futures_v1",
        "venue_id": "neutral_offline_venue_v1",
        "ingestion_timestamp": "2026-06-01T00:00:00+00:00",
        "generation_method": "operator_curated_versioned_export",
        "provenance_ref": "operator/staged/eth_perp_neutral_v1",
    }
    payload.update(overrides)
    return payload


def _descriptor_dict(bars: pd.DataFrame, **overrides: Any) -> dict[str, Any]:
    bindings = ds.default_field_bindings_v1()
    digest = ds.compute_versioned_dataset_digest(bars, field_bindings=bindings)
    train, val, oos = ds.compute_split_periods_from_bars(bars)
    idx = bars.sort_index().index
    payload: dict[str, Any] = {
        "dataset_id": "neutral_eth_perp_operator_staged_v1",
        "dataset_version": ds.DEFAULT_DATASET_VERSION,
        "dataset_schema_version": ds.DATASET_SCHEMA_VERSION,
        "dataset_digest": digest,
        "instrument_id": wiring.MV2_REQUIRED_INSTRUMENT_ID,
        "contract_type": "perpetual",
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "venue_id": "neutral_offline_venue_v1",
        "start_time": str(idx[0]),
        "end_time": str(idx[-1]),
        "row_count": len(bars),
        "field_bindings": bindings.to_dict(),
        "training_period": train,
        "validation_period": val,
        "out_of_sample_period": oos,
        "split_policy_version": ds.SPLIT_POLICY_VERSION,
        "timestamp_semantics": ds.TIMESTAMP_SEMANTICS,
        "timezone": ds.TIMEZONE,
        "ordering_status": ds.ORDERING_STATUS_SORTED,
        "duplicate_policy": ds.DUPLICATE_POLICY,
        "missing_data_policy": ds.MISSING_DATA_POLICY,
    }
    payload.update(overrides)
    return payload


def _manifest_payload(bars: pd.DataFrame, **overrides: Any) -> dict[str, Any]:
    manifest = {
        "manifest_version": "admissible_versioned_futures_dataset_manifest_v1",
        "dataset_profile": "runtime_market_context_v1",
        "profile_binding": ds.default_runtime_profile_binding_v1().to_dict(),
        "dataset": _descriptor_dict(bars, **overrides.get("descriptor_overrides", {})),
        "provenance": _provenance(**overrides.get("provenance_overrides", {})),
    }
    manifest["manifest_digest"] = _load_runner()._compute_manifest_digest(manifest)
    return manifest


def _evaluation_config(bars: pd.DataFrame | None = None, **overrides: Any) -> dict[str, Any]:
    frame = _bars() if bars is None else bars
    descriptor = _descriptor_dict(frame)
    cfg: dict[str, Any] = {
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
                    "grid_id": "runner_contract_grid_v1",
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
                "dataset_profile": "runtime_market_context_v1",
                "profile_binding": ds.default_runtime_profile_binding_v1().to_dict(),
                "dataset": descriptor,
                "provenance": _provenance(),
            },
        },
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
        "economic_evaluation_v1": {
            "strategy_id": "ma_crossover",
            "strategy_params": {
                "fast_window": 2,
                "slow_window": 3,
            },
            "walk_forward": {"bind": True, "train_bars": 8, "test_bars": 4, "step_bars": 4},
            "monte_carlo": {"bind": True, "runs": 16, "seed": 42},
            "stress": {"bind": True},
        },
    }
    if "backtest" in overrides:
        cfg["backtest"].update(overrides.pop("backtest"))
    cfg.update(overrides)
    return cfg


def _stage_run_inputs(
    tmp_path: Path,
    *,
    bars: pd.DataFrame | None = None,
    manifest_overrides: dict[str, Any] | None = None,
    config_overrides: dict[str, Any] | None = None,
) -> dict[str, Path]:
    frame = _bars() if bars is None else bars
    staging = tmp_path / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    dataset_path = staging / "bars.parquet"
    frame.to_parquet(dataset_path)
    manifest = _manifest_payload(frame, **(manifest_overrides or {}))
    manifest_path = staging / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    config = _evaluation_config(frame, **(config_overrides or {}))
    config_path = staging / "evaluation_config.json"
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")
    policy_path = staging / "policy_canonical.json"
    policy_path.write_text(
        json.dumps(
            {"use_canonical": True, "policy_version": "economic_validity_policy_v1"},
            indent=2,
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"
    return {
        "dataset_path": dataset_path,
        "manifest_path": manifest_path,
        "config_path": config_path,
        "policy_path": policy_path,
        "output_dir": output_dir,
    }


def _argv(paths: dict[str, Path], **extra: Any) -> list[str]:
    argv = [
        "--dataset-path",
        str(paths["dataset_path"]),
        "--dataset-manifest-path",
        str(paths["manifest_path"]),
        "--config-path",
        str(paths["config_path"]),
        "--policy-path",
        str(paths["policy_path"]),
        "--output-dir",
        str(paths["output_dir"]),
        "--run-id",
        "runner_contract_test_v1",
    ]
    if extra.get("validate_only"):
        argv.append("--validate-only")
    if extra.get("allow_existing_output"):
        argv.append("--allow-existing-output")
    return argv


@pytest.fixture
def runner():
    return _load_runner()


def test_scripts_exist() -> None:
    assert TEST_PACKAGE_MARKER
    assert RUNNER_SCRIPT.is_file()


def test_help_smoke() -> None:
    proc = subprocess.run(
        [sys.executable, str(RUNNER_SCRIPT), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "--dataset-path" in proc.stdout
    assert "--validate-only" in proc.stdout


def test_missing_dataset_path_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    rc = runner.main(
        _argv(paths) + ["--dataset-path", str(tmp_path / "missing.parquet"), "--validate-only"]
    )
    assert rc != 0


def test_url_dataset_path_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    rc = runner.main(
        _argv(paths) + ["--dataset-path", "https://example.com/data.parquet", "--validate-only"]
    )
    assert rc != 0


def test_missing_manifest_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    rc = runner.main(
        _argv(paths)
        + [
            "--dataset-manifest-path",
            str(tmp_path / "missing_manifest.json"),
            "--validate-only",
        ]
    )
    assert rc != 0


def test_manifest_digest_mismatch_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    manifest = json.loads(paths["manifest_path"].read_text(encoding="utf-8"))
    manifest["manifest_digest"] = "0" * 64
    paths["manifest_path"].write_text(json.dumps(manifest), encoding="utf-8")
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc != 0


def test_unknown_dataset_version_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(
        tmp_path,
        manifest_overrides={"descriptor_overrides": {"dataset_version": "v999"}},
    )
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc != 0


def test_real_admissible_validate_only_accepted(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc == 0


def test_test_fixture_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(
        tmp_path,
        manifest_overrides={
            "provenance_overrides": {
                "source_type": "test_fixture",
                "provenance_ref": "tests/backtest/fixture_only",
            }
        },
    )
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc != 0


def test_synthetic_fixture_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(
        tmp_path,
        manifest_overrides={
            "provenance_overrides": {
                "source_type": "synthetic_contract_fixture",
                "generation_method": "deterministic_test_fixture",
            }
        },
    )
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc != 0


def test_preview_probe_data_rejected(runner, tmp_path: Path) -> None:
    for source_type in ("preview_data", "probe_data"):
        case_root = tmp_path / source_type
        paths = _stage_run_inputs(
            case_root,
            manifest_overrides={"provenance_overrides": {"source_type": source_type}},
        )
        rc = runner.main(_argv(paths) + ["--validate-only"])
        assert rc != 0


def test_spot_and_synthetic_spot_rejected(runner, tmp_path: Path) -> None:
    for source_type in ("spot", "synthetic_spot"):
        case_root = tmp_path / source_type
        paths = _stage_run_inputs(
            case_root,
            manifest_overrides={"provenance_overrides": {"source_type": source_type}},
        )
        rc = runner.main(_argv(paths) + ["--validate-only"])
        assert rc != 0


def test_kraken_u5d_fixture_rejected_via_generic_classification(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(
        tmp_path,
        manifest_overrides={
            "provenance_overrides": {
                "source_type": "transport_fixture",
                "generation_method": "offline_transform_probe",
                "provenance_ref": (
                    "tests/fixtures/u5d_offline_transform_v1/minimal/"
                    "kraken_futures_tickers.raw.v1.json"
                ),
            }
        },
    )
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc != 0
    source = RUNNER_SCRIPT.read_text(encoding="utf-8")
    assert "kraken" not in source.lower()


def test_no_kraken_venue_specific_production_logic(runner) -> None:
    source = RUNNER_SCRIPT.read_text(encoding="utf-8").lower()
    assert "kraken" not in source
    assert "xbt" not in source
    assert "btc" not in source


def test_missing_provenance_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(
        tmp_path,
        manifest_overrides={"provenance_overrides": {"provenance_ref": ""}},
    )
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc != 0


def test_missing_versioned_config_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    rc = runner.main(
        _argv(paths) + ["--config-path", str(tmp_path / "missing_config.json"), "--validate-only"]
    )
    assert rc != 0


def test_missing_policy_thresholds_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    bad_policy = paths["policy_path"].parent / "bad_policy.json"
    bad_policy.write_text(
        json.dumps(
            {
                "economic_validity_policy": {
                    "policy_version": "economic_validity_policy_v1",
                    "owner": "backtest.economic_validity_policy_v1",
                    "thresholds": {},
                }
            }
        ),
        encoding="utf-8",
    )
    argv = _argv(paths) + ["--validate-only"]
    argv[argv.index(str(paths["policy_path"]))] = str(bad_policy)
    rc = runner.main(argv)
    assert rc != 0


def test_zero_cost_config_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path, config_overrides={"backtest": {"fee_bps": 0.0}})
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc != 0


def test_missing_funding_binding_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path, config_overrides={"backtest": {"funding": {"bind": False}}})
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc != 0


def test_missing_parameter_sensitivity_binding_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(
        tmp_path, config_overrides={"backtest": {"parameter_sensitivity": {"bind": False}}}
    )
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc != 0


def test_missing_walk_forward_binding_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(
        tmp_path,
        config_overrides={"economic_evaluation_v1": {"walk_forward": {"bind": False}}},
    )
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc != 0


def test_missing_monte_carlo_binding_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(
        tmp_path,
        config_overrides={"economic_evaluation_v1": {"monte_carlo": {"bind": False}}},
    )
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc != 0


def test_missing_stress_binding_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(
        tmp_path,
        config_overrides={"economic_evaluation_v1": {"stress": {"bind": False}}},
    )
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc != 0


def test_existing_output_fail_closed(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    paths["output_dir"].mkdir()
    (paths["output_dir"] / "existing.txt").write_text("x", encoding="utf-8")
    rc = runner.main(_argv(paths))
    assert rc != 0


def test_runner_uses_existing_library_owners(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    parser = runner.build_arg_parser()
    args = parser.parse_args(_argv(paths) + ["--validate-only"])
    plan = runner.build_validation_plan(args)
    assert ev.ECONOMIC_VIABILITY_EVIDENCE_OWNER in plan.owners
    assert ds.ADMISSIBLE_VERSIONED_FUTURES_DATASET_OWNER in plan.owners


def test_technical_success_economic_fail_exit_zero(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    rc = runner.main(_argv(paths))
    assert rc == 0
    summary = (paths["output_dir"] / "run_summary.env").read_text(encoding="utf-8")
    assert "RUNNER_EXECUTION_SUCCESS=true" in summary
    assert "ECONOMIC_EVIDENCE_BUILT=true" in summary
    assert "ECONOMIC_GATE_EVALUATED=true" in summary
    # Economic FAIL is expected for small fixture data
    assert re.search(r"ECONOMIC_VALIDITY_RESULT=(FAIL|BLOCKED)", summary)


def test_technical_error_exit_nonzero(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    rc = runner.main(
        _argv(paths) + ["--dataset-path", "ftp://invalid.example/data.parquet", "--validate-only"]
    )
    assert rc != 0


def test_economic_pass_does_not_imply_promotion_or_runtime(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    runner.main(_argv(paths))
    summary = (paths["output_dir"] / "run_summary.env").read_text(encoding="utf-8")
    assert "PROMOTION_ELIGIBILITY=false" in summary
    assert "RUNTIME_EFFECT=false" in summary
    assert "LIVE_AUTHORIZED=false" in summary


def test_economic_fail_no_runtime_effect(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    runner.main(_argv(paths))
    summary = (paths["output_dir"] / "run_summary.env").read_text(encoding="utf-8")
    assert "RUNTIME_EFFECT=false" in summary
    assert "ORDER_EFFECT=false" in summary


def test_output_manifest_created_and_verified(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    runner.main(_argv(paths))
    ok, _msg = verify_manifest_sha256(paths["output_dir"])
    assert ok is True
    assert (paths["output_dir"] / "MANIFEST.sha256").is_file()


def test_deterministic_repeat_produces_identical_core_artifacts(runner, tmp_path: Path) -> None:
    paths_a = _stage_run_inputs(tmp_path / "a")
    paths_b = _stage_run_inputs(tmp_path / "b")
    runner.main(_argv(paths_a))
    runner.main(_argv(paths_b))
    for name in (
        "economic_viability_evidence_v1.json",
        "dataset_admissibility_result_v1.json",
        "economic_validity_evaluation_v1.json",
    ):
        a = json.loads((paths_a["output_dir"] / name).read_text(encoding="utf-8"))
        b = json.loads((paths_b["output_dir"] / name).read_text(encoding="utf-8"))
        assert a == b


def test_no_network_calls_in_runner_source(runner) -> None:
    source = RUNNER_SCRIPT.read_text(encoding="utf-8")
    for token in ("requests.", "urllib.request", "httpx", "aiohttp", "socket."):
        assert token not in source


def test_no_credential_env_reads(runner) -> None:
    source = RUNNER_SCRIPT.read_text(encoding="utf-8")
    assert "os.environ" not in source
    assert "getenv" not in source


def test_no_runtime_adapter_imports(runner) -> None:
    source = RUNNER_SCRIPT.read_text(encoding="utf-8")
    forbidden = (
        "ccxt",
        "live_runtime",
        "order_submission",
        "adapter_submission",
        "websocket",
    )
    for token in forbidden:
        assert token not in source.lower()


def test_futures_only_and_no_bitcoin_direction(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    runner.main(_argv(paths))
    summary = (paths["output_dir"] / "run_summary.env").read_text(encoding="utf-8")
    assert "FUTURES_ONLY=true" in summary
    assert "BITCOIN_DIRECTION_ALLOWED=false" in summary


def test_digest_bindings_present(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    runner.main(_argv(paths))
    provenance = json.loads(
        (paths["output_dir"] / "INPUT_PROVENANCE.json").read_text(encoding="utf-8")
    )
    for key in (
        "dataset_digest",
        "config_digest",
        "policy_digest",
        "implementation_digest",
        "canonical_trading_logic_version",
        "run_id",
    ):
        assert provenance.get(key)


def test_validate_only_does_not_build_evidence(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc == 0
    assert not paths["output_dir"].exists()


def test_source_dataset_unchanged(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    before = paths["dataset_path"].read_bytes()
    runner.main(_argv(paths))
    after = paths["dataset_path"].read_bytes()
    assert before == after


def test_real_owner_graph_validate_only_integration(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    bars = pd.read_parquet(paths["dataset_path"])
    manifest = json.loads(paths["manifest_path"].read_text(encoding="utf-8"))
    descriptor = runner._descriptor_from_manifest(manifest)
    provenance = runner._provenance_from_manifest(manifest)
    fixture_class = runner.classify_dataset_fixture_class_v1(
        descriptor=descriptor,
        provenance=provenance,
        dataset_path=paths["dataset_path"],
        manifest_path=paths["manifest_path"],
    )
    assert fixture_class.value == "REAL_ADMISSIBLE_VERSIONED_FUTURES_DATASET"
    result = ds.evaluate_admissible_versioned_futures_dataset_v1(
        bars=bars,
        descriptor=descriptor,
        provenance=provenance,
        instrument_id=descriptor.instrument_id,
        profile_binding=ds.load_profile_binding_from_manifest(manifest),
    )
    assert result.is_admissible() is True


def test_missing_manifest_dataset_profile_rejected(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    manifest = json.loads(paths["manifest_path"].read_text(encoding="utf-8"))
    manifest.pop("dataset_profile", None)
    manifest.pop("profile_binding", None)
    manifest["manifest_digest"] = runner._compute_manifest_digest(manifest)
    paths["manifest_path"].write_text(json.dumps(manifest), encoding="utf-8")
    rc = runner.main(_argv(paths) + ["--validate-only"])
    assert rc != 0


def test_fixture_classification_matrix(runner, tmp_path: Path) -> None:
    bars = _bars()
    raw = _descriptor_dict(bars)
    bindings = ds.DatasetFieldBindingsV1(**raw.pop("field_bindings"))
    descriptor = ds.VersionedFuturesDatasetDescriptorV1(field_bindings=bindings, **raw)
    cases = {
        "synthetic_contract_fixture": runner.DatasetFixtureClass.SYNTHETIC_FIXTURE,
        "spot": runner.DatasetFixtureClass.SPOT_DATA,
        "synthetic_spot": runner.DatasetFixtureClass.SYNTHETIC_SPOT_DATA,
        "preview_data": runner.DatasetFixtureClass.PREVIEW_DATA,
        "probe_data": runner.DatasetFixtureClass.PROBE_DATA,
        "transport_fixture": runner.DatasetFixtureClass.TRANSPORT_FIXTURE,
        "webui_fixture": runner.DatasetFixtureClass.WEBUI_FIXTURE,
        "test_fixture": runner.DatasetFixtureClass.TEST_FIXTURE,
    }
    for source_type, expected in cases.items():
        provenance = ds.DatasetProvenanceV1(
            source_type=source_type,
            venue_id="neutral",
            ingestion_timestamp="2026-06-01T00:00:00+00:00",
            generation_method="x",
            provenance_ref="operator/staged/x",
        )
        got = runner.classify_dataset_fixture_class_v1(
            descriptor=descriptor,
            provenance=provenance,
            dataset_path=tmp_path / "data.parquet",
            manifest_path=tmp_path / "manifest.json",
        )
        assert got is expected


def test_runner_does_not_duplicate_build_logic(runner) -> None:
    source = RUNNER_SCRIPT.read_text(encoding="utf-8")
    assert "build_and_persist_economic_viability_evidence_bundle_v1" in source
    assert "evaluate_economic_validity_against_policy_v1" in source
    assert "def compute_funding_drag_v1" not in source
    assert "def run_mv2_research_backtest_wiring_v1" not in source


def test_mocked_owner_orchestration_contract(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    captured: dict[str, Any] = {}

    def _fake_build_and_persist(output_dir, **kwargs):
        captured.update(kwargs)
        build_kwargs = {
            key: value
            for key, value in kwargs.items()
            if key not in {"input_provenance", "verify_reproducibility"}
        }
        evidence = ev.build_economic_viability_evidence_v1(**build_kwargs)
        bundle = ev.persist_economic_viability_evidence_bundle_v1(
            output_dir,
            evidence,
            config_snapshot={"cfg": dict(kwargs["cfg"]), "strategy_id": kwargs["strategy_id"]},
            metrics={"trade_count": evidence.trade_count.to_dict()},
            input_provenance=dict(kwargs["input_provenance"]),
        )
        repro = ev.verify_economic_viability_evidence_reproducibility_v1(
            persisted=evidence,
            rebuilt=ev.build_economic_viability_evidence_v1(**build_kwargs),
        )
        return bundle, repro

    with patch.object(
        ev, "build_and_persist_economic_viability_evidence_bundle_v1", _fake_build_and_persist
    ):
        rc = runner.main(_argv(paths))
    assert rc == 0
    assert captured.get("strategy_id") == "ma_crossover"
    assert captured.get("cfg") is not None
