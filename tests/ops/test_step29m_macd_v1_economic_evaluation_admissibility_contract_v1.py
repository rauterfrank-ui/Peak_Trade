"""Contract tests for STEP 29M macd v1 economic evaluation admissibility v1."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd
import pytest

from src.backtest import step29m_macd_v1_economic_evaluation_admissibility_contract_v1 as contract
from src.backtest.strategy_signal_binding_v1 import (
    StrategySignalBindingError,
    collect_configured_strategy_params_v1,
    compute_required_warmup_rows_v1,
    resolve_effective_strategy_params_v1,
)
from src.strategies.registry import get_strategy_registry_entry, resolve_strategy_id

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v1.json"
V2_CONFIG_PATH = (
    ROOT / "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v2.json"
)
V3_CONFIG_PATH = (
    ROOT / "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v3.json"
)
PROGRESS_REGISTRY = ROOT / "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
ARCHIVE_ROOT = contract.ARCHIVE_ROOT
DATASET_ROOT = contract.DATASET_ROOT


def _load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _step_29m_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29M — Economic Viability Evidence v1")
    end = text.index("#### RUNBOOK_STEP_29N — Promotion Economic Gate Binding v1", start)
    return text[start:end]


@pytest.fixture
def cfg() -> dict:
    return _load_config()


def test_macd_registry_identity() -> None:
    resolution = resolve_strategy_id("macd")
    assert resolution.canonical_strategy_id == "macd"
    entry = get_strategy_registry_entry("macd")
    assert entry.strategy_version == "v1"
    assert entry.implementation_ref == contract.MACD_V1_STRATEGY_OWNER
    assert entry.futures_compatible is True
    assert entry.spot_compatible is False


def test_macd_version_binding(cfg: dict) -> None:
    assert cfg["economic_evaluation_v1"]["strategy_id"] == "macd"
    assert cfg["economic_evaluation_v1"]["strategy_version"] == "v1"


def test_macd_parameter_contract_defaults() -> None:
    effective, digest = resolve_effective_strategy_params_v1("macd", {})
    assert effective == contract.MACD_V1_CANONICAL_PARAMS
    assert len(digest) == 64


def test_macd_parameter_contract_from_config(cfg: dict) -> None:
    configured = collect_configured_strategy_params_v1(cfg, "macd")
    effective, _ = resolve_effective_strategy_params_v1("macd", configured)
    assert effective == contract.MACD_V1_CANONICAL_PARAMS


def test_unknown_macd_param_fail_closed() -> None:
    with pytest.raises(StrategySignalBindingError, match="unknown_strategy_param"):
        resolve_effective_strategy_params_v1("macd", {"fast_window": 12})


def test_macd_warmup_contract() -> None:
    effective, _ = resolve_effective_strategy_params_v1("macd", {})
    warmup = compute_required_warmup_rows_v1("macd", effective)
    assert warmup == 34


def test_config_schema_and_engine_signal_source(cfg: dict) -> None:
    assert cfg["config_schema_version"] == "step29m_macd_v1_economic_evaluation_admissibility_v1"
    assert cfg["economic_evaluation_v1"]["engine_signal_source"] == "configured_strategy_signal"


def test_config_digest_stable(cfg: dict) -> None:
    digest = contract.compute_evaluation_config_digest_v1(cfg)
    assert digest == contract.compute_evaluation_config_digest_v1(_load_config())
    assert len(digest) == 64


def test_cost_binding(cfg: dict) -> None:
    status, reasons = contract.verify_cost_binding_v1(cfg)
    assert status == "PASS"
    assert not reasons


@pytest.mark.skipif(not DATASET_ROOT.is_dir(), reason="staged OKX dataset not present locally")
def test_dataset_digests_and_profile() -> None:
    manifest = json.loads((DATASET_ROOT / "dataset_manifest.json").read_text(encoding="utf-8"))
    assert manifest["normalized_dataset_digest"] == contract.EXPECTED_DATASET_DIGEST
    assert manifest["manifest_digest"] == contract.EXPECTED_MANIFEST_DIGEST
    assert manifest["dataset_profile"] == "economic_research_v1"
    assert manifest["instrument_id"] == "inst-eth-usdt-perp"
    assert manifest["instrument_metadata"]["canonical_instrument_id"] == "inst-eth-usdt-perp"
    assert manifest["native_instrument_id"] == "ETH-USDT-SWAP"
    assert manifest["provenance"]["source_venue"] == "OKX"


@pytest.mark.skipif(not DATASET_ROOT.is_dir(), reason="staged OKX dataset not present locally")
def test_dataset_columns_and_close_positive() -> None:
    bars = contract.load_admissible_okx_eth_bars_v1()
    assert "close" in bars.columns
    assert bars["close"].isna().sum() == 0
    assert (bars["close"] > 0).all()
    assert bars.index.is_monotonic_increasing
    assert not bars.index.has_duplicates


@pytest.mark.skipif(not DATASET_ROOT.is_dir(), reason="staged OKX dataset not present locally")
def test_macd_signal_admissibility_diagnostic(cfg: dict) -> None:
    bars = contract.load_admissible_okx_eth_bars_v1()
    diagnostic = contract.run_macd_v1_signal_admissibility_diagnostic_v1(bars, cfg)
    assert diagnostic.dataset_rows == 19808
    assert (
        diagnostic.valid_rows_after_warmup
        == diagnostic.dataset_rows - diagnostic.required_warmup_rows
    )
    assert diagnostic.signal_min_value >= -1
    assert diagnostic.signal_max_value <= 1
    assert diagnostic.long_signal_count > 0
    assert diagnostic.short_signal_count > 0
    assert diagnostic.signal_transition_count > 1000
    assert diagnostic.index_alignment_status == "ALIGNED"
    assert diagnostic.signal_contract_status == "PASS"
    assert diagnostic.determinism_status == "PASS"
    assert len(diagnostic.signal_digest) == 64


@pytest.mark.skipif(not DATASET_ROOT.is_dir(), reason="staged OKX dataset not present locally")
def test_signal_transition_count_order_of_magnitude(cfg: dict) -> None:
    bars = contract.load_admissible_okx_eth_bars_v1()
    diagnostic = contract.run_macd_v1_signal_admissibility_diagnostic_v1(bars, cfg)
    # Read-only ranking reference ~3109; not hard-coded, only sanity bounds.
    assert 500 <= diagnostic.signal_transition_count <= 10000


@pytest.mark.skipif(not DATASET_ROOT.is_dir(), reason="staged OKX dataset not present locally")
def test_strategy_engine_provenance_contract(cfg: dict) -> None:
    bars = contract.load_admissible_okx_eth_bars_v1()
    provenance, reasons = contract.verify_macd_v1_provenance_contract_v1(bars, cfg)
    assert not reasons
    assert provenance.configured_strategy_execution_contract == "PASS"
    assert provenance.signal_provenance_contract == "PASS"
    assert provenance.engine_signal_binding_contract == "PASS"
    assert provenance.mv2_diagnostic_separation_contract == "PASS"


@pytest.mark.skipif(not DATASET_ROOT.is_dir(), reason="staged OKX dataset not present locally")
def test_split_warmup_semantics_policy_a(cfg: dict) -> None:
    bars = contract.load_admissible_okx_eth_bars_v1()
    semantics, leakage, reasons = contract.verify_split_warmup_semantics_macd_v1(bars, cfg)
    assert semantics == contract.SPLIT_WARMUP_SEMANTICS
    assert leakage == "PASS"
    assert not reasons


@pytest.mark.skipif(not DATASET_ROOT.is_dir(), reason="staged OKX dataset not present locally")
def test_full_admissibility_contract_passes(cfg: dict) -> None:
    result = contract.evaluate_macd_v1_admissibility_contract_v1(repo_root=ROOT)
    assert result.admissibility_result.value == "PASS", result.blocking_reasons
    assert result.cost_binding_status == "PASS"
    assert result.signal_diagnostic is not None
    assert result.provenance_contract is not None
    assert result.leakage_status == "PASS"


def test_negative_btc_strategy_rejected() -> None:
    with pytest.raises(Exception):
        resolve_strategy_id("btc_momentum")


def test_wrong_expected_dataset_digest_blocks_admissibility(cfg: dict) -> None:
    bad_cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    bad_cfg["real_admissible_futures_evaluation_binding_v1"] = dict(
        bad_cfg["real_admissible_futures_evaluation_binding_v1"]
    )
    bad_cfg["real_admissible_futures_evaluation_binding_v1"]["expected_dataset_digest"] = "0" * 64
    if not DATASET_ROOT.is_dir():
        status, reasons = contract.verify_cost_binding_v1(bad_cfg)
        assert status == "PASS"
        return
    result = contract.evaluate_macd_v1_admissibility_contract_v1(repo_root=ROOT)
    assert result.admissibility_result.value == "PASS"
    bad_path = ROOT / "config/ops/_tmp_bad_macd_config.json"
    bad_path.write_text(json.dumps(bad_cfg), encoding="utf-8")
    try:
        blocked = contract.evaluate_macd_v1_admissibility_contract_v1(
            repo_root=ROOT,
            config_path="config/ops/_tmp_bad_macd_config.json",
        )
        assert blocked.admissibility_result.value == "BLOCKED"
        assert "config_expected_dataset_digest_mismatch" in blocked.blocking_reasons
    finally:
        bad_path.unlink(missing_ok=True)


def test_v2_config_schema_valid_but_entry_infeasible_blocks_admissibility() -> None:
    result = contract.evaluate_macd_v1_admissibility_contract_v1(
        repo_root=ROOT,
        config_path=str(V2_CONFIG_PATH.relative_to(ROOT)),
    )
    assert result.admissibility_result.value == "BLOCKED"
    assert "TOTAL_ENTRY_REJECTION_CONFIG_INVARIANT" in result.blocking_reasons


@pytest.mark.skipif(not DATASET_ROOT.is_dir(), reason="staged OKX dataset not present locally")
def test_v3_config_admissibility_contract_passes() -> None:
    result = contract.evaluate_macd_v1_admissibility_contract_v1(
        repo_root=ROOT,
        config_path=str(V3_CONFIG_PATH.relative_to(ROOT)),
    )
    assert result.admissibility_result.value == "PASS", result.blocking_reasons
    assert result.cost_binding_status == "PASS"
    assert result.leakage_status == "PASS"


def test_v3_config_schema_version() -> None:
    cfg = json.loads(V3_CONFIG_PATH.read_text(encoding="utf-8"))
    assert cfg["config_schema_version"] == "step29m_macd_v1_economic_evaluation_admissibility_v3"


@pytest.mark.skipif(not DATASET_ROOT.is_dir(), reason="staged OKX dataset not present locally")
def test_v3_runner_validate_only_accepts_config_without_evaluation() -> None:
    import importlib.util
    import sys
    from unittest.mock import patch

    runner_path = ROOT / "scripts/ops/run_economic_viability_evidence_evaluation_v1.py"
    spec = importlib.util.spec_from_file_location("runner_v3_feasibility", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    policy_path = Path("/tmp/step29m_macd_v3_policy.json")
    policy_path.write_text(
        json.dumps({"use_canonical": True, "policy_version": "economic_validity_policy_v1"}),
        encoding="utf-8",
    )
    with patch.object(mod, "execute_evaluation") as execute_mock:
        rc = mod.main(
            [
                "--dataset-path",
                str(DATASET_ROOT / "bars.parquet"),
                "--dataset-manifest-path",
                str(DATASET_ROOT / "dataset_manifest.json"),
                "--config-path",
                str(V3_CONFIG_PATH),
                "--policy-path",
                str(policy_path),
                "--output-dir",
                str(Path("/tmp/step29m_macd_v3_validate_only_out")),
                "--validate-only",
            ]
        )
    assert rc == 0
    execute_mock.assert_not_called()


def test_v2_runner_validate_only_blocks_before_evaluation() -> None:
    if not DATASET_ROOT.is_dir():
        pytest.skip("staged OKX dataset not present locally")
    import importlib.util
    import sys

    runner_path = ROOT / "scripts/ops/run_economic_viability_evidence_evaluation_v1.py"
    spec = importlib.util.spec_from_file_location("runner_v2_feasibility", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    policy_path = Path("/tmp/step29m_macd_v2_policy.json")
    policy_path.write_text(
        json.dumps({"use_canonical": True, "policy_version": "economic_validity_policy_v1"}),
        encoding="utf-8",
    )
    rc = mod.main(
        [
            "--dataset-path",
            str(DATASET_ROOT / "bars.parquet"),
            "--dataset-manifest-path",
            str(DATASET_ROOT / "dataset_manifest.json"),
            "--config-path",
            str(V2_CONFIG_PATH),
            "--policy-path",
            str(policy_path),
            "--output-dir",
            str(Path("/tmp/step29m_macd_v2_validate_only_out")),
            "--validate-only",
        ]
    )
    assert rc != 0


def test_registry_truth_after_macd_v1_real_evaluation() -> None:
    section = _step_29m_section(PROGRESS_REGISTRY.read_text(encoding="utf-8"))
    assert _field_value(section, "REAL_EVALUATION_PERFORMED") == "true"
    assert _field_value(section, "REAL_ADMISSIBLE_FUTURES_EVIDENCE_BOUND") == "true"
    assert _field_value(section, "ECONOMIC_VALIDITY_RESULT") == "FAILED"
    assert _field_value(section, "PROFITABILITY_CLAIM_ALLOWED") == "false"
    assert _field_value(section, "LAST_EVALUATED_STRATEGY_ID") == "breakout_donchian"
    assert _field_value(section, "LAST_EVALUATED_STRATEGY_VERSION") == "v1"
    assert _field_value(section, "LAST_EVALUATED_CONFIG_VERSION") == "v1"
    assert _field_value(section, "REAL_EVALUATION_INPUT_STATUS") == (
        "REGISTERED_POLICY_RATIFIED_STRATEGY_FLEET_EVALUATION_COMPLETE"
    )
    assert (
        "step29m_macd_v1_real_admissible_futures_economic_reevaluation_v3_after_risk_limits_rewire_single_rerun_v0_20260701T225645Z"
        in (_field_value(section, "MACD_V1_CONFIG_V3_REAL_EVALUATION_EVIDENCE_REF"))
    )


def test_config_validate_only_runner_accepts_macd_config(cfg: dict) -> None:
    if not DATASET_ROOT.is_dir():
        pytest.skip("staged OKX dataset not present locally")
    import importlib.util
    import sys

    runner_path = ROOT / "scripts/ops/run_economic_viability_evidence_evaluation_v1.py"
    spec = importlib.util.spec_from_file_location("runner", runner_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    policy_path = Path("/tmp/step29m_macd_policy.json")
    policy_path.write_text(
        json.dumps({"use_canonical": True, "policy_version": "economic_validity_policy_v1"}),
        encoding="utf-8",
    )
    rc = mod.main(
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
            str(Path("/tmp/step29m_macd_validate_only_out")),
            "--validate-only",
        ]
    )
    assert rc == 0


def test_config_digest_record_matches(cfg: dict) -> None:
    digest = hashlib.sha256(
        json.dumps(cfg, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
    assert digest == contract.compute_evaluation_config_digest_v1(cfg)
