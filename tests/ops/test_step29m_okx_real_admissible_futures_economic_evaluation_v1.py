"""Contract tests for STEP 29M real OKX inst-eth-usdt-perp economic evaluation v1."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

from src.backtest import admissible_versioned_futures_dataset_v1 as ds

ROOT = Path(__file__).resolve().parents[2]
RUNNER_SCRIPT = ROOT / "scripts" / "ops" / "run_economic_viability_evidence_evaluation_v1.py"
CONFIG_PATH = ROOT / "config" / "ops" / "step29m_okx_inst_eth_usdt_perp_economic_evaluation_v1.json"
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
DATASET_ROOT = ARCHIVE_ROOT / "datasets/admissible_futures/inst-eth-usdt-perp/v1"
EXPECTED_DATASET_DIGEST = "b4cbe7fff81a137da055588231757937406d8cb30d531ee0aab41d95ee9b6c78"
EXPECTED_MANIFEST_DIGEST = "317105798c749943074911b1e9ea91ac9b94fab3b115fb7a64b692339426651a"


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_economic_viability_evidence_evaluation_v1", RUNNER_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def runner():
    return _load_runner()


def test_evaluation_config_exists_and_binds_costs() -> None:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    binding = cfg["real_admissible_futures_evaluation_binding_v1"]
    assert cfg["backtest"]["fee_bps"] == 10.0
    assert cfg["backtest"]["slippage_bps"] == 5.0
    assert binding["effective_entry_cost_bps"] == 20.0
    assert binding["effective_exit_cost_bps"] == 20.0
    assert binding["roundtrip_cost_bps"] == 40.0
    assert (
        cfg["backtest"]["economic_research_execution_cost"]["conservative_half_spread_bps"] == 5.0
    )


def test_evaluation_config_binds_expected_digests() -> None:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    binding = cfg["real_admissible_futures_evaluation_binding_v1"]
    assert binding["expected_dataset_digest"] == EXPECTED_DATASET_DIGEST
    assert binding["expected_manifest_digest"] == EXPECTED_MANIFEST_DIGEST


def test_evaluation_config_binds_splits() -> None:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    binding = cfg["real_admissible_futures_evaluation_binding_v1"]
    assert binding["training_period"] == "2026-06-17 16:00:00+00:00..2026-06-24 13:03:00+00:00"
    assert binding["validation_period"] == "2026-06-24 13:04:00+00:00..2026-06-27 23:35:00+00:00"
    assert binding["out_of_sample_period"] == "2026-06-27 23:36:00+00:00..2026-07-01 10:07:00+00:00"


@pytest.mark.skipif(not DATASET_ROOT.is_dir(), reason="staged OKX dataset not present locally")
def test_staged_dataset_manifest_digests_match() -> None:
    manifest = json.loads((DATASET_ROOT / "dataset_manifest.json").read_text(encoding="utf-8"))
    assert manifest["normalized_dataset_digest"] == EXPECTED_DATASET_DIGEST
    assert manifest["manifest_digest"] == EXPECTED_MANIFEST_DIGEST
    assert manifest["dataset_profile"] == "economic_research_v1"
    assert manifest["integrity_results"]["integrity_pass"] is True
    assert manifest["integrity_results"]["dataset_admissible"] is True
    assert manifest["observed_l1_used"] is False
    assert manifest["l1_observation_status"] == "EXECUTION_MODEL_BOUND_NOT_OBSERVED"


@pytest.mark.skipif(not DATASET_ROOT.is_dir(), reason="staged OKX dataset not present locally")
def test_flat_manifest_adapter_loads_descriptor_and_provenance(runner) -> None:
    manifest_path = DATASET_ROOT / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert ds.is_flat_economic_research_manifest_v1(manifest)
    descriptor, provenance = ds.load_dataset_admissibility_from_flat_economic_research_manifest_v1(
        manifest,
        manifest_path=str(manifest_path),
    )
    assert descriptor.instrument_id == "inst-eth-usdt-perp"
    assert descriptor.dataset_digest == EXPECTED_DATASET_DIGEST
    assert provenance.source_type == "operator_staged_futures_v1"
    assert provenance.venue_id == "OKX"
    assert provenance.provenance_ref


@pytest.mark.skipif(not DATASET_ROOT.is_dir(), reason="staged OKX dataset not present locally")
def test_flat_manifest_validate_only_accepted(runner, tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps({"use_canonical": True, "policy_version": "economic_validity_policy_v1"}),
        encoding="utf-8",
    )
    rc = runner.main(
        [
            "--dataset-path",
            str(DATASET_ROOT / "bars.parquet"),
            "--dataset-manifest-path",
            str(DATASET_ROOT / "dataset_manifest.json"),
            "--config-path",
            str(CONFIG_PATH),
            "--policy-path",
            str(policy_path),
            "--output-dir",
            str(tmp_path / "out"),
            "--validate-only",
        ]
    )
    assert rc == 0


@pytest.mark.skipif(not DATASET_ROOT.is_dir(), reason="staged OKX dataset not present locally")
def test_dataset_digest_recomputed_from_bars_matches_manifest() -> None:
    bars = pd.read_parquet(DATASET_ROOT / "bars.parquet")
    if "timestamp" in bars.columns:
        bars = bars.set_index("timestamp")
        bars.index = pd.to_datetime(bars.index, utc=True)
    bindings = ds.field_bindings_for_profile(ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1)
    digest = ds.compute_versioned_dataset_digest(bars.sort_index(), field_bindings=bindings)
    assert digest == EXPECTED_DATASET_DIGEST


def test_config_digest_stable() -> None:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    digest = hashlib.sha256(
        json.dumps(cfg, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
    assert len(digest) == 64


def test_wrong_expected_dataset_digest_rejected(runner, tmp_path: Path) -> None:
    if not DATASET_ROOT.is_dir():
        pytest.skip("staged OKX dataset not present locally")
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    cfg["real_admissible_futures_evaluation_binding_v1"]["expected_dataset_digest"] = "0" * 64
    cfg_path = tmp_path / "bad_config.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps({"use_canonical": True, "policy_version": "economic_validity_policy_v1"}),
        encoding="utf-8",
    )
    rc = runner.main(
        [
            "--dataset-path",
            str(DATASET_ROOT / "bars.parquet"),
            "--dataset-manifest-path",
            str(DATASET_ROOT / "dataset_manifest.json"),
            "--config-path",
            str(cfg_path),
            "--policy-path",
            str(policy_path),
            "--output-dir",
            str(tmp_path / "out"),
            "--validate-only",
        ]
    )
    assert rc != 0
