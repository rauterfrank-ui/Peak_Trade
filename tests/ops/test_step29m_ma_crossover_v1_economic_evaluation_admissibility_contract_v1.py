"""Contract tests for STEP 29M ma_crossover v1 economic evaluation admissibility v1."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

import pytest

from src.backtest import (
    step29m_ma_crossover_v1_economic_evaluation_admissibility_contract_v1 as contract,
)
from src.backtest.strategy_signal_binding_v1 import (
    StrategySignalBindingError,
    collect_configured_strategy_params_v1,
    compute_required_warmup_rows_v1,
    resolve_effective_strategy_params_v1,
)
from src.strategies.registry import get_strategy_registry_entry, resolve_strategy_id

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    ROOT / "config/ops/step29m_okx_inst_eth_usdt_perp_ma_crossover_v1_economic_evaluation_v1.json"
)
PROGRESS_REGISTRY = ROOT / "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"


def _load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _field_value(text: str, field: str) -> str:
    match = re.search(
        rf"\| `{re.escape(field)}` \| `([^`]*)`(?: <!--.*?-->)? \|",
        text,
    )
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _step_29m_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29M — Economic Viability Evidence v1")
    end = text.index("#### RUNBOOK_STEP_29N — Promotion Economic Gate Binding v1", start)
    return text[start:end]


@pytest.fixture
def cfg() -> dict:
    return _load_config()


def test_ma_crossover_registry_identity() -> None:
    resolution = resolve_strategy_id("ma_crossover")
    assert resolution.canonical_strategy_id == "ma_crossover"
    entry = get_strategy_registry_entry("ma_crossover")
    assert entry.strategy_version == "v1"
    assert entry.implementation_ref == contract.MA_CROSSOVER_V1_STRATEGY_OWNER
    assert entry.futures_compatible is True
    assert entry.spot_compatible is False


def test_config_schema_valid(cfg: dict) -> None:
    assert (
        cfg["config_schema_version"]
        == "step29m_ma_crossover_v1_economic_evaluation_admissibility_v1"
    )
    assert cfg["economic_evaluation_v1"]["strategy_id"] == "ma_crossover"
    assert cfg["economic_evaluation_v1"]["strategy_params"] == {
        "fast_window": 20,
        "slow_window": 50,
        "price_col": "close",
    }


def test_wrong_strategy_id_rejected() -> None:
    bad = _load_config()
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_id"] = "macd"
    reasons = contract.verify_ma_crossover_v1_config_schema_v1(bad)
    assert "config_strategy_id_mismatch" in reasons


def test_fast_window_gte_slow_window_rejected() -> None:
    bad = _load_config()
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_params"] = {
        "fast_window": 50,
        "slow_window": 20,
        "price_col": "close",
    }
    reasons = contract.verify_ma_crossover_v1_config_schema_v1(bad)
    assert "fast_window_not_lt_slow_window" in reasons


def test_missing_fast_window_rejected() -> None:
    bad = _load_config()
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_params"] = {"slow_window": 50, "price_col": "close"}
    reasons = contract.verify_ma_crossover_v1_config_schema_v1(bad)
    assert "fast_window_missing" in reasons


def test_invalid_price_col_rejected() -> None:
    bad = _load_config()
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_params"] = {
        "fast_window": 20,
        "slow_window": 50,
        "price_col": "volume",
    }
    reasons = contract.verify_ma_crossover_v1_config_schema_v1(bad)
    assert "price_col_not_allowed" in reasons


def test_risk_per_trade_invariant(cfg: dict) -> None:
    reasons = contract.verify_ma_crossover_v1_sizing_policy_v1(cfg)
    assert not reasons
    bad = deepcopy(cfg)
    bad["offline_evaluation_sizing_contract_v1"] = dict(
        bad["offline_evaluation_sizing_contract_v1"]
    )
    bad["offline_evaluation_sizing_contract_v1"]["risk_per_trade"] = 0.01
    reasons = contract.verify_ma_crossover_v1_sizing_policy_v1(bad)
    assert "policy_invariant_violation" in reasons


def test_oversize_policy_must_reject_offline_binding(cfg: dict) -> None:
    assert (
        cfg["offline_evaluation_sizing_contract_v1"]["oversize_policy"]
        == contract.OFFLINE_BOUND_OVERSIZE_POLICY
    )


def test_no_btc_or_spot_binding(cfg: dict) -> None:
    reasons = contract.verify_ma_crossover_v1_instrument_binding_v1(cfg)
    assert not reasons
    bad = deepcopy(cfg)
    bad["real_admissible_futures_evaluation_binding_v1"] = dict(
        bad["real_admissible_futures_evaluation_binding_v1"]
    )
    bad["real_admissible_futures_evaluation_binding_v1"]["native_instrument_id"] = "BTC-USDT-SWAP"
    reasons = contract.verify_ma_crossover_v1_instrument_binding_v1(bad)
    assert any("forbidden_instrument_binding" in r for r in reasons)


def test_ratification_authority_blocked_in_slice(cfg: dict) -> None:
    reasons = contract.verify_ma_crossover_v1_ratification_authority_v1(cfg)
    assert not reasons
    bad = deepcopy(cfg)
    bad["step29m_policy_ratification_v1"] = dict(bad["step29m_policy_ratification_v1"])
    bad["step29m_policy_ratification_v1"]["evaluation_authorized"] = True
    reasons = contract.verify_ma_crossover_v1_ratification_authority_v1(bad)
    assert "evaluation_authorized_not_false" in reasons


def test_realistic_cost_fields_present(cfg: dict) -> None:
    status, reasons = contract.verify_cost_binding_v1(cfg)
    assert status == "PASS"
    assert not reasons


def test_warmup_for_slow_window_50() -> None:
    effective, _ = resolve_effective_strategy_params_v1(
        "ma_crossover",
        {"fast_window": 20, "slow_window": 50},
    )
    assert compute_required_warmup_rows_v1("ma_crossover", effective) == 50


def test_unknown_strategy_param_fail_closed() -> None:
    with pytest.raises(StrategySignalBindingError, match="unknown_strategy_param"):
        resolve_effective_strategy_params_v1("ma_crossover", {"lookback": 12})


def test_full_admissibility_contract_passes() -> None:
    result = contract.evaluate_ma_crossover_v1_admissibility_contract_v1(repo_root=ROOT)
    assert result.admissibility_result.value == "PASS", result.blocking_reasons
    assert result.cost_binding_status == "PASS"
    assert result.policy_invariant_result == contract.POLICY_INVARIANT_RESULT
    assert result.signal_semantics == "LONG_OR_FLAT_ONLY_0_1"


def test_progress_registry_ratified_pending_evaluation_fields() -> None:
    section = _step_29m_section(PROGRESS_REGISTRY.read_text(encoding="utf-8"))
    assert _field_value(section, "MA_CROSSOVER_V1_POLICY_RATIFIED") == "true"
    assert _field_value(section, "MA_CROSSOVER_V1_FIXED_CONFIG_BOUND") == "true"
    assert _field_value(section, "MA_CROSSOVER_V1_ECONOMIC_EVALUATION_EXECUTED") == "false"
    assert _field_value(section, "MA_CROSSOVER_V1_STATUS") == "AUTHORIZED_PENDING_EVALUATION"
    assert _field_value(section, "NEXT_EVALUATION_STRATEGY_ID") == "ma_crossover"
    assert _field_value(section, "NEXT_EVALUATION_CONFIG_STATUS") == "AUTHORIZED_PENDING_EVALUATION"
    assert _field_value(section, "AUTHORIZED_PENDING_EVALUATION_COUNT") == "1"
    assert _field_value(section, "MACD_V1_CONFIG_V3_STATUS") == (
        "TECHNICALLY_VALID_ECONOMIC_POLICY_FAIL"
    )
    assert _field_value(section, "BREAKOUT_DONCHIAN_V1_STATUS") == (
        "TECHNICALLY_VALID_ECONOMIC_POLICY_FAIL"
    )
    assert _field_value(section, "ECONOMIC_EVALUATION_ALLOWED") == "false"
    assert _field_value(section, "PROMOTION_ALLOWED") == "false"


def test_config_params_from_evaluation_section(cfg: dict) -> None:
    configured = collect_configured_strategy_params_v1(cfg, "ma_crossover")
    effective, _ = resolve_effective_strategy_params_v1(
        "ma_crossover",
        contract._window_params_for_binding_v1(configured),
    )
    assert effective == {"fast_window": 20, "slow_window": 50}
    assert configured["price_col"] == "close"
