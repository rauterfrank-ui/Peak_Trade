"""Contract tests for STEP 29M vol_breakout v1 economic evaluation admissibility v1."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

import pytest

from src.backtest import (
    step29m_vol_breakout_v1_economic_evaluation_admissibility_contract_v1 as contract,
)
from src.backtest.strategy_signal_binding_v1 import (
    StrategySignalBindingError,
    collect_configured_strategy_params_v1,
    compute_required_warmup_rows_v1,
    project_strategy_params_for_binding_v1,
    resolve_effective_strategy_params_v1,
)
from src.strategies.registry import get_strategy_registry_entry, resolve_strategy_id

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    ROOT / "config/ops/step29m_okx_inst_eth_usdt_perp_vol_breakout_v1_economic_evaluation_v1.json"
)
PROGRESS_REGISTRY = ROOT / "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
VERSIONED_BINDING_PATH = ROOT / "config/research/vol_breakout_v1_versioned_research_binding_v0.json"
SCOPE_RATIFICATION_PATH = (
    ROOT / "config/research/vol_breakout_v1_offline_economic_evaluation_scope_ratification_v0.json"
)


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


def test_vol_breakout_registry_identity() -> None:
    resolution = resolve_strategy_id("vol_breakout")
    assert resolution.canonical_strategy_id == "vol_breakout"
    entry = get_strategy_registry_entry("vol_breakout")
    assert entry.strategy_version == "v1"
    assert entry.implementation_ref == contract.VOL_BREAKOUT_V1_STRATEGY_OWNER
    assert entry.futures_compatible is True
    assert entry.spot_compatible is False


def test_config_schema_valid(cfg: dict) -> None:
    assert (
        cfg["config_schema_version"]
        == "step29m_vol_breakout_v1_economic_evaluation_admissibility_v1"
    )
    assert cfg["economic_evaluation_v1"]["strategy_id"] == "vol_breakout"
    assert (
        cfg["economic_evaluation_v1"]["strategy_params"]
        == contract.VOL_BREAKOUT_V1_CANONICAL_PARAMS
    )


def test_atr_multiple_excluded_from_config(cfg: dict) -> None:
    assert "atr_multiple" not in cfg["economic_evaluation_v1"]["strategy_params"]


def test_wrong_strategy_id_rejected() -> None:
    bad = _load_config()
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_id"] = "macd"
    reasons = contract.verify_vol_breakout_v1_config_schema_v1(bad)
    assert "config_strategy_id_mismatch" in reasons


def test_excluded_atr_multiple_rejected() -> None:
    bad = _load_config()
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_params"] = dict(
        contract.VOL_BREAKOUT_V1_CANONICAL_PARAMS
    )
    bad["economic_evaluation_v1"]["strategy_params"]["atr_multiple"] = 1.5
    reasons = contract.verify_vol_breakout_v1_config_schema_v1(bad)
    assert "excluded_binding_param_in_config" in reasons


def test_invalid_side_rejected() -> None:
    bad = _load_config()
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_params"] = {
        **contract.VOL_BREAKOUT_V1_CANONICAL_PARAMS,
        "side": "long",
    }
    reasons = contract.verify_vol_breakout_v1_config_schema_v1(bad)
    assert "side_not_allowed" in reasons


def test_risk_per_trade_invariant(cfg: dict) -> None:
    reasons = contract.verify_vol_breakout_v1_sizing_policy_v1(cfg)
    assert not reasons
    bad = deepcopy(cfg)
    bad["offline_evaluation_sizing_contract_v1"] = dict(
        bad["offline_evaluation_sizing_contract_v1"]
    )
    bad["offline_evaluation_sizing_contract_v1"]["risk_per_trade"] = 0.01
    reasons = contract.verify_vol_breakout_v1_sizing_policy_v1(bad)
    assert "policy_invariant_violation" in reasons


def test_roundtrip_cost_40bps(cfg: dict) -> None:
    binding = cfg["real_admissible_futures_evaluation_binding_v1"]
    assert binding["roundtrip_cost_bps"] == 40.0
    assert binding["effective_entry_cost_bps"] == 20.0
    assert binding["effective_exit_cost_bps"] == 20.0


def test_no_btc_or_spot_binding(cfg: dict) -> None:
    reasons = contract.verify_vol_breakout_v1_instrument_binding_v1(cfg)
    assert not reasons
    bad = deepcopy(cfg)
    bad["real_admissible_futures_evaluation_binding_v1"] = dict(
        bad["real_admissible_futures_evaluation_binding_v1"]
    )
    bad["real_admissible_futures_evaluation_binding_v1"]["native_instrument_id"] = "BTC-USDT-SWAP"
    reasons = contract.verify_vol_breakout_v1_instrument_binding_v1(bad)
    assert any("forbidden_instrument_binding" in r for r in reasons)


def test_ratification_authority_blocked_in_slice(cfg: dict) -> None:
    reasons = contract.verify_vol_breakout_v1_ratification_authority_v1(cfg)
    assert not reasons
    bad = deepcopy(cfg)
    bad["step29m_policy_ratification_v1"] = dict(bad["step29m_policy_ratification_v1"])
    bad["step29m_policy_ratification_v1"]["evaluation_authorized"] = True
    reasons = contract.verify_vol_breakout_v1_ratification_authority_v1(bad)
    assert "evaluation_authorized_not_false" in reasons


def test_warmup_for_canonical_params() -> None:
    effective, _ = resolve_effective_strategy_params_v1(
        "vol_breakout",
        project_strategy_params_for_binding_v1(
            "vol_breakout",
            contract.VOL_BREAKOUT_V1_CANONICAL_PARAMS,
        ),
    )
    assert compute_required_warmup_rows_v1("vol_breakout", effective) == 40


def test_unknown_strategy_param_fail_closed() -> None:
    with pytest.raises(StrategySignalBindingError, match="unknown_strategy_param"):
        resolve_effective_strategy_params_v1("vol_breakout", {"atr_multiple": 1.5})


def test_full_admissibility_contract_passes() -> None:
    result = contract.evaluate_vol_breakout_v1_admissibility_contract_v1(repo_root=ROOT)
    assert result.admissibility_result.value == "PASS", result.blocking_reasons
    assert result.cost_binding_status == "PASS"
    assert result.policy_invariant_result == contract.POLICY_INVARIANT_RESULT
    assert result.signal_semantics == "LONG_SHORT_FLAT_NEG1_0_1"
    assert result.required_warmup_rows == 40


def test_versioned_bindings_materialized() -> None:
    binding = json.loads(VERSIONED_BINDING_PATH.read_text(encoding="utf-8"))
    scope = json.loads(SCOPE_RATIFICATION_PATH.read_text(encoding="utf-8"))
    assert binding["candidate_id"] == "vol_breakout/v1"
    assert binding["binding"]["binding_status"]["overall_binding_status"] == "COMPLETE"
    assert binding["binding"]["digest_bindings"]["config_digest"][
        "value"
    ] == contract.compute_evaluation_config_digest_v1(_load_config())
    assert scope["candidate_id"] == "vol_breakout/v1"
    assert scope["config_digest"] == contract.compute_evaluation_config_digest_v1(_load_config())
    assert scope["economic_evaluation_executed"] is False
    assert scope["parameter_search_forbidden"] is True
    assert "atr_multiple" not in scope["parameter_binding"]["parameters"]


def test_progress_registry_ratified_terminal_negative_fields() -> None:
    section = _step_29m_section(PROGRESS_REGISTRY.read_text(encoding="utf-8"))
    assert _field_value(section, "VOL_BREAKOUT_V1_POLICY_RATIFIED") == "true"
    assert _field_value(section, "VOL_BREAKOUT_V1_FIXED_CONFIG_BOUND") == "true"
    assert _field_value(section, "VOL_BREAKOUT_V1_ECONOMIC_EVALUATION_EXECUTED") == "true"
    assert (
        _field_value(section, "VOL_BREAKOUT_V1_STATUS") == "TECHNICALLY_VALID_ECONOMIC_POLICY_FAIL"
    )
    assert _field_value(section, "NEXT_EVALUATION_STRATEGY_ID") == "NONE"
    assert (
        _field_value(section, "NEXT_EVALUATION_CONFIG_STATUS")
        == "TERMINAL_NEGATIVE_EVIDENCE_REGISTERED"
    )
    assert _field_value(section, "AUTHORIZED_PENDING_EVALUATION_COUNT") == "0"
    assert _field_value(section, "ATR_MULTIPLE_BOUND") == "false"
    assert _field_value(section, "PARAMETER_SEARCH_ALLOWED") == "false"
    assert _field_value(section, "ECONOMIC_EVALUATION_ALLOWED") == "false"
