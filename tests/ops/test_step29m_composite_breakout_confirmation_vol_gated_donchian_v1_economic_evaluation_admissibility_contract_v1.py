"""Contract tests for composite breakout confirmation vol-gated donchian v1 admissibility."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.backtest import (
    step29m_composite_breakout_confirmation_vol_gated_donchian_v1_economic_evaluation_admissibility_contract_v1 as contract,
)
from src.backtest.strategy_signal_binding_v1 import (
    StrategySignalBindingError,
    compute_composite_required_warmup_rows_v1,
    parse_composite_strategy_binding_v1,
)
from src.strategies.registry import get_strategy_registry_entry, resolve_strategy_id

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / contract.DEFAULT_EVALUATION_CONFIG_PATH


def _load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_composite_registry_identity() -> None:
    resolution = resolve_strategy_id("composite")
    assert resolution.canonical_strategy_id == "composite"
    entry = get_strategy_registry_entry("composite")
    assert entry.strategy_version == "v1"
    assert entry.implementation_ref == contract.COMPOSITE_V1_STRATEGY_OWNER
    assert entry.futures_compatible is True
    assert entry.spot_compatible is False


def test_config_schema_valid() -> None:
    cfg = _load_config()
    assert cfg["candidate_binding_id"] == contract.CANDIDATE_BINDING_ID
    assert cfg["config_schema_version"] == contract.CONFIG_SCHEMA_VERSION
    assert cfg["economic_evaluation_v1"]["strategy_id"] == "composite"
    assert cfg["economic_evaluation_v1"]["walk_forward"]["bind"] is True
    assert cfg["economic_evaluation_v1"]["monte_carlo"]["bind"] is True
    assert cfg["economic_evaluation_v1"]["stress"]["bind"] is True


def test_wrong_candidate_binding_id_rejected() -> None:
    bad = _load_config()
    bad["candidate_binding_id"] = "composite_vol_gated_breakout_donchian_v1"
    reasons = (
        contract.verify_composite_breakout_confirmation_vol_gated_donchian_v1_candidate_binding_v1(
            bad
        )
    )
    assert "candidate_binding_id_mismatch" in reasons


def test_non_canonical_confirmation_epochs_rejected() -> None:
    bad = _load_config()
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_params"] = dict(
        bad["economic_evaluation_v1"]["strategy_params"]
    )
    bad["economic_evaluation_v1"]["strategy_params"]["confirmation_epochs"] = 2
    reasons = (
        contract.verify_composite_breakout_confirmation_vol_gated_donchian_v1_config_schema_v1(bad)
    )
    assert any("composite_confirmation_epochs_not_allowed" in r for r in reasons)


def test_risk_per_trade_invariant() -> None:
    cfg = _load_config()
    reasons = (
        contract.verify_composite_breakout_confirmation_vol_gated_donchian_v1_sizing_policy_v1(cfg)
    )
    assert not reasons
    bad = deepcopy(cfg)
    bad["offline_evaluation_sizing_contract_v1"] = dict(
        bad["offline_evaluation_sizing_contract_v1"]
    )
    bad["offline_evaluation_sizing_contract_v1"]["risk_per_trade"] = 0.01
    reasons = (
        contract.verify_composite_breakout_confirmation_vol_gated_donchian_v1_sizing_policy_v1(bad)
    )
    assert "policy_invariant_violation" in reasons


def test_realistic_cost_fields_present() -> None:
    cfg = _load_config()
    status, reasons = contract.verify_cost_binding_v1(cfg)
    assert status == "PASS"
    assert not reasons


def test_config_registry_resolution() -> None:
    registry = contract.list_step29m_registered_economic_evaluation_configs_v1()
    assert contract.DEFAULT_EVALUATION_CONFIG_PATH in registry
    assert CONFIG_PATH.is_file()


def test_warmup_includes_confirmation_epoch() -> None:
    params = _load_config()["economic_evaluation_v1"]["strategy_params"]
    warmup = compute_composite_required_warmup_rows_v1(params)
    assert warmup >= 20 + 1


def test_binding_semantic_digest_matches_architecture_binding() -> None:
    arch_path = (
        ROOT
        / "config/ops/composite_breakout_confirmation_vol_gated_donchian_v1_architecture_binding_v1.json"
    )
    arch = json.loads(arch_path.read_text(encoding="utf-8"))
    eval_params = _load_config()["economic_evaluation_v1"]["strategy_params"]
    eval_binding = parse_composite_strategy_binding_v1(eval_params)
    arch_binding = parse_composite_strategy_binding_v1(
        arch["economic_evaluation_v1"]["strategy_params"]
    )
    assert eval_binding.binding_semantic_digest == arch_binding.binding_semantic_digest


def test_full_admissibility_contract_passes() -> None:
    result = contract.evaluate_composite_breakout_confirmation_vol_gated_donchian_v1_admissibility_contract_v1(
        repo_root=ROOT
    )
    assert result.admissibility_result.value == "PASS", result.blocking_reasons
    assert result.cost_binding_status == "PASS"
    assert result.policy_invariant_result == contract.POLICY_INVARIANT_RESULT


def test_non_one_confirmation_epochs_fail_closed() -> None:
    bad_params = dict(contract.COMPOSITE_V1_CANONICAL_PARAMS)
    bad_params["confirmation_epochs"] = 2
    with pytest.raises(
        StrategySignalBindingError, match="composite_confirmation_epochs_not_allowed"
    ):
        parse_composite_strategy_binding_v1(bad_params)
