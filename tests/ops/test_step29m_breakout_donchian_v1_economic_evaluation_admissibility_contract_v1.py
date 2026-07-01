"""Contract tests for STEP 29M breakout_donchian v1 economic evaluation admissibility v1."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

import pytest

from src.backtest import (
    step29m_breakout_donchian_v1_economic_evaluation_admissibility_contract_v1 as contract,
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
    ROOT
    / "config/ops/step29m_okx_inst_eth_usdt_perp_breakout_donchian_v1_economic_evaluation_v1.json"
)
PROGRESS_REGISTRY = ROOT / "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"


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


def test_breakout_donchian_registry_identity() -> None:
    resolution = resolve_strategy_id("breakout_donchian")
    assert resolution.canonical_strategy_id == "breakout_donchian"
    entry = get_strategy_registry_entry("breakout_donchian")
    assert entry.strategy_version == "v1"
    assert entry.implementation_ref == contract.BREAKOUT_DONCHIAN_V1_STRATEGY_OWNER
    assert entry.futures_compatible is True
    assert entry.spot_compatible is False


def test_config_schema_valid(cfg: dict) -> None:
    assert (
        cfg["config_schema_version"]
        == "step29m_breakout_donchian_v1_economic_evaluation_admissibility_v1"
    )
    assert cfg["economic_evaluation_v1"]["strategy_id"] == "breakout_donchian"
    assert cfg["economic_evaluation_v1"]["strategy_params"] == {
        "lookback": 20,
        "price_col": "close",
    }


def test_wrong_strategy_id_rejected() -> None:
    bad = _load_config()
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_id"] = "macd"
    reasons = contract.verify_breakout_donchian_v1_config_schema_v1(bad)
    assert "config_strategy_id_mismatch" in reasons


def test_missing_lookback_rejected() -> None:
    bad = _load_config()
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_params"] = {"price_col": "close"}
    reasons = contract.verify_breakout_donchian_v1_config_schema_v1(bad)
    assert "lookback_missing" in reasons


def test_invalid_lookback_rejected() -> None:
    bad = _load_config()
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_params"] = {"lookback": 1, "price_col": "close"}
    reasons = contract.verify_breakout_donchian_v1_config_schema_v1(bad)
    assert "lookback_out_of_range" in reasons


def test_invalid_price_col_rejected() -> None:
    bad = _load_config()
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_params"] = {"lookback": 20, "price_col": "volume"}
    reasons = contract.verify_breakout_donchian_v1_config_schema_v1(bad)
    assert "price_col_not_allowed" in reasons


def test_risk_per_trade_invariant(cfg: dict) -> None:
    reasons = contract.verify_breakout_donchian_v1_sizing_policy_v1(cfg)
    assert not reasons
    bad = deepcopy(cfg)
    bad["offline_evaluation_sizing_contract_v1"] = dict(
        bad["offline_evaluation_sizing_contract_v1"]
    )
    bad["offline_evaluation_sizing_contract_v1"]["risk_per_trade"] = 0.01
    reasons = contract.verify_breakout_donchian_v1_sizing_policy_v1(bad)
    assert "policy_invariant_violation" in reasons


def test_oversize_policy_must_reject_offline_binding(cfg: dict) -> None:
    assert (
        cfg["offline_evaluation_sizing_contract_v1"]["oversize_policy"]
        == contract.OFFLINE_BOUND_OVERSIZE_POLICY
    )
    bad = deepcopy(cfg)
    bad["offline_evaluation_sizing_contract_v1"] = dict(
        bad["offline_evaluation_sizing_contract_v1"]
    )
    bad["offline_evaluation_sizing_contract_v1"]["oversize_policy"] = "CAP_TO_MAX_POSITION_PCT"
    reasons = contract.verify_breakout_donchian_v1_sizing_policy_v1(bad)
    assert "oversize_policy_not_reject" in reasons


def test_no_btc_or_spot_binding(cfg: dict) -> None:
    reasons = contract.verify_breakout_donchian_v1_instrument_binding_v1(cfg)
    assert not reasons
    bad = deepcopy(cfg)
    bad["real_admissible_futures_evaluation_binding_v1"] = dict(
        bad["real_admissible_futures_evaluation_binding_v1"]
    )
    bad["real_admissible_futures_evaluation_binding_v1"]["native_instrument_id"] = "BTC-USDT-SWAP"
    reasons = contract.verify_breakout_donchian_v1_instrument_binding_v1(bad)
    assert any("forbidden_instrument_binding" in r for r in reasons)


def test_realistic_cost_fields_present(cfg: dict) -> None:
    status, reasons = contract.verify_cost_binding_v1(cfg)
    assert status == "PASS"
    assert not reasons


def test_config_registry_resolution() -> None:
    registry = contract.list_step29m_registered_economic_evaluation_configs_v1()
    assert contract.DEFAULT_EVALUATION_CONFIG_PATH in registry
    assert (ROOT / contract.DEFAULT_EVALUATION_CONFIG_PATH).is_file()


def test_warmup_for_lookback_20() -> None:
    effective, _ = resolve_effective_strategy_params_v1("breakout_donchian", {"lookback": 20})
    assert compute_required_warmup_rows_v1("breakout_donchian", effective) == 20


def test_warmup_follows_other_valid_lookback_deterministically() -> None:
    effective, _ = resolve_effective_strategy_params_v1("breakout_donchian", {"lookback": 55})
    assert compute_required_warmup_rows_v1("breakout_donchian", effective) == 55


def test_missing_lookback_warmup_fail_closed() -> None:
    with pytest.raises(StrategySignalBindingError, match="breakout_donchian_lookback_missing"):
        compute_required_warmup_rows_v1("breakout_donchian", {})


def test_unknown_strategy_warmup_fail_closed() -> None:
    with pytest.raises(StrategySignalBindingError, match="required_warmup_rows_unbound"):
        compute_required_warmup_rows_v1("unknown_strategy", {})


def test_unknown_strategy_param_fail_closed() -> None:
    with pytest.raises(StrategySignalBindingError, match="unknown_strategy_param"):
        resolve_effective_strategy_params_v1("breakout_donchian", {"fast_window": 12})


def test_full_admissibility_contract_passes() -> None:
    result = contract.evaluate_breakout_donchian_v1_admissibility_contract_v1(repo_root=ROOT)
    assert result.admissibility_result.value == "PASS", result.blocking_reasons
    assert result.cost_binding_status == "PASS"
    assert result.policy_invariant_result == contract.POLICY_INVARIANT_RESULT


def test_progress_registry_ratified_policy_fields() -> None:
    section = _step_29m_section(PROGRESS_REGISTRY.read_text(encoding="utf-8"))
    assert _field_value(section, "OPERATOR_POLICY_DECISION") == "RATIFIED"
    assert _field_value(section, "OPERATOR_POLICY_DECISION_OWNER") == "Frank Rauter"
    assert _field_value(section, "NEXT_EVALUATION_STRATEGY_ID") == "breakout_donchian"
    assert _field_value(section, "NEXT_EVALUATION_INSTRUMENT_ID") == "inst-eth-usdt-perp"
    assert _field_value(section, "NEXT_EVALUATION_VENUE") == "OKX"
    assert _field_value(section, "BREAKOUT_DONCHIAN_LOOKBACK") == "20"
    assert _field_value(section, "BREAKOUT_DONCHIAN_PRICE_COL") == "close"
    assert _field_value(section, "BREAKOUT_DONCHIAN_RISK_PER_TRADE") == "0.005"
    assert _field_value(section, "BREAKOUT_DONCHIAN_STOP_PCT") == "0.02"
    assert _field_value(section, "BREAKOUT_DONCHIAN_MAX_POSITION_PCT") == "0.25"
    assert _field_value(section, "BREAKOUT_DONCHIAN_OVERSIZE_POLICY") == "REJECT"
    assert _field_value(section, "MACD_POLICY_REUSED") == "false"
    assert _field_value(section, "CONFIG_TOML_AUTO_ADOPTION") == "false"
    assert _field_value(section, "PARAMETER_TUNING_PERFORMED") == "false"
    assert _field_value(section, "ECONOMIC_EVALUATION_ALLOWED") == "false"
    assert _field_value(section, "PROMOTION_ALLOWED") == "false"
    assert "breakout_donchian" in _field_value(section, "NEXT_EVALUATION_CONFIG_PATH")
    assert "macd" not in _field_value(section, "NEXT_EVALUATION_CONFIG_PATH")


def test_macd_contract_unchanged_for_last_evaluated() -> None:
    section = _step_29m_section(PROGRESS_REGISTRY.read_text(encoding="utf-8"))
    assert _field_value(section, "LAST_EVALUATED_STRATEGY_ID") == "macd"
    assert _field_value(section, "MACD_V1_ADMISSIBILITY_CONTRACT_STATUS") == "PASS"


def test_config_params_from_evaluation_section(cfg: dict) -> None:
    configured = collect_configured_strategy_params_v1(cfg, "breakout_donchian")
    effective, _ = resolve_effective_strategy_params_v1("breakout_donchian", configured)
    assert effective == contract.BREAKOUT_DONCHIAN_V1_CANONICAL_PARAMS
