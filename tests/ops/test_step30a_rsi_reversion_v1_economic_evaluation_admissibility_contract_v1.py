"""Contract tests for STEP30A rsi_reversion admissibility contract v1."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest

from src.backtest import (
    step30a_rsi_reversion_v1_economic_evaluation_admissibility_contract_v1 as contract,
)
from src.backtest.strategy_signal_binding_v1 import (
    collect_configured_strategy_params_v1,
    compute_required_warmup_rows_v1,
    project_strategy_params_for_binding_v1,
    resolve_effective_strategy_params_v1,
)
from src.strategies.registry import get_strategy_registry_entry, resolve_strategy_id

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / contract.DEFAULT_EVALUATION_CONFIG_PATH


def _load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_rsi_reversion_registry_identity() -> None:
    resolution = resolve_strategy_id("rsi_reversion")
    assert resolution.canonical_strategy_id == "rsi_reversion"
    entry = get_strategy_registry_entry("rsi_reversion")
    assert entry.strategy_version == "v1"
    assert entry.implementation_ref == contract.RSI_REVERSION_V1_STRATEGY_OWNER
    assert entry.futures_compatible is True
    assert entry.spot_compatible is False


def test_config_schema_valid() -> None:
    cfg = _load_config()
    assert cfg["config_schema_version"] == contract.CONFIG_SCHEMA_VERSION
    assert cfg["economic_evaluation_v1"]["strategy_id"] == "rsi_reversion"
    assert cfg["economic_evaluation_v1"]["strategy_params"] == {
        "rsi_window": 14,
        "lower": 30.0,
        "upper": 70.0,
        "price_col": "close",
    }


def test_use_trend_filter_forbidden_in_strategy_params() -> None:
    bad = _load_config()
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_params"] = dict(
        bad["economic_evaluation_v1"]["strategy_params"]
    )
    bad["economic_evaluation_v1"]["strategy_params"]["use_trend_filter"] = True
    reasons = contract.verify_rsi_reversion_v1_config_schema_v1(bad)
    assert "forbidden_use_trend_filter_in_strategy_params" in reasons


def test_holdout_separation_contract() -> None:
    reasons = contract.verify_holdout_separation_v1(_load_config())
    assert not reasons
    bad = _load_config()
    bad["real_admissible_futures_evaluation_binding_v1"] = dict(
        bad["real_admissible_futures_evaluation_binding_v1"]
    )
    bad["real_admissible_futures_evaluation_binding_v1"]["validation_period"] = (
        "2026-05-19 00:00:00+00:00..2026-06-17 10:07:00+00:00"
    )
    reasons = contract.verify_holdout_separation_v1(bad)
    assert "validation_not_before_holdout" in reasons


def test_dataset_v2_binding_fields_required() -> None:
    reasons = contract.verify_rsi_reversion_v1_instrument_binding_v1(_load_config())
    assert not reasons
    bad = _load_config()
    bad["real_admissible_futures_evaluation_binding_v1"] = dict(
        bad["real_admissible_futures_evaluation_binding_v1"]
    )
    bad["real_admissible_futures_evaluation_binding_v1"]["dataset_version"] = "v1"
    reasons = contract.verify_rsi_reversion_v1_instrument_binding_v1(bad)
    assert "dataset_version_not_v2" in reasons


def test_evaluation_authorized_false_in_ratification() -> None:
    reasons = contract.verify_step30a_policy_ratification_v1(_load_config())
    assert not reasons
    bad = deepcopy(_load_config())
    bad["step30a_policy_ratification_v1"] = dict(bad["step30a_policy_ratification_v1"])
    bad["step30a_policy_ratification_v1"]["evaluation_authorized"] = True
    reasons = contract.verify_step30a_policy_ratification_v1(bad)
    assert "evaluation_authorized_not_false" in reasons


def test_warmup_equals_rsi_window_from_binding() -> None:
    cfg = _load_config()
    configured = collect_configured_strategy_params_v1(cfg, "rsi_reversion")
    effective, _ = resolve_effective_strategy_params_v1(
        "rsi_reversion",
        project_strategy_params_for_binding_v1("rsi_reversion", configured),
    )
    assert compute_required_warmup_rows_v1("rsi_reversion", effective) == 14


def test_holdout_access_block_contract() -> None:
    from src.backtest import (
        step30a_rsi_reversion_v1_economic_evaluation_admissibility_contract_v1 as contract,
    )

    idx = pd.date_range("2026-06-01", periods=4, freq="1h", tz="UTC")
    holdout_idx = pd.date_range("2026-06-18", periods=2, freq="1h", tz="UTC")
    bars = pd.DataFrame({"close": [1.0, 2.0, 3.0, 4.0]}, index=idx)
    holdout_bars = pd.DataFrame({"close": [5.0, 6.0]}, index=holdout_idx)
    with pytest.raises(ValueError, match="holdout_access_blocked"):
        contract.assert_holdout_access_blocked_before_evaluation_v1(
            holdout_bars,
            evaluation_authorized=False,
        )
    development = contract.slice_development_partition_bars_v1(
        pd.concat([bars, holdout_bars]).sort_index()
    )
    assert len(development) == len(bars)


def test_full_admissibility_contract_passes() -> None:
    result = contract.evaluate_step30a_rsi_reversion_v1_admissibility_contract_v1(repo_root=ROOT)
    assert result.admissibility_result.value == "PASS", result.blocking_reasons
    assert result.cost_binding_status == "PASS"
    assert result.signal_semantics == "LONG_SHORT_REVERSION_-1_0_1"
