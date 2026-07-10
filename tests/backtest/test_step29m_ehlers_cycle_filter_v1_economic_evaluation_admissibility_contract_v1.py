"""Contract tests for STEP 29M ehlers_cycle_filter v1 economic evaluation admissibility v1."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.backtest import (
    step29m_ehlers_cycle_filter_v1_economic_evaluation_admissibility_contract_v1 as contract,
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
    ROOT
    / "config/ops/step29m_okx_inst_eth_usdt_perp_ehlers_cycle_filter_v1_economic_evaluation_v1.json"
)
VERSIONED_BINDING_PATH = (
    ROOT / "config/research/ehlers_cycle_filter_v1_versioned_research_binding_v0.json"
)
SCOPE_RATIFICATION_PATH = (
    ROOT
    / "config/research/ehlers_cycle_filter_v1_offline_economic_evaluation_scope_ratification_v0.json"
)
MATERIAL_DIFFERENCE_PATH = (
    ROOT
    / "config/research/ehlers_cycle_filter_v1_material_difference_and_non_claim_contract_v0.json"
)


def _load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def cfg() -> dict:
    return _load_config()


def test_ehlers_registry_identity() -> None:
    resolution = resolve_strategy_id("ehlers_cycle_filter")
    assert resolution.canonical_strategy_id == "ehlers_cycle_filter"
    entry = get_strategy_registry_entry("ehlers_cycle_filter")
    assert entry.strategy_version == "v1"
    assert entry.implementation_ref == contract.EHLERS_CYCLE_FILTER_V1_STRATEGY_OWNER
    assert entry.futures_compatible is True
    assert entry.spot_compatible is False


def test_config_schema_valid(cfg: dict) -> None:
    assert (
        cfg["config_schema_version"]
        == "step29m_ehlers_cycle_filter_v1_economic_evaluation_admissibility_v1"
    )
    assert cfg["economic_evaluation_v1"]["strategy_id"] == "ehlers_cycle_filter"
    assert (
        cfg["economic_evaluation_v1"]["strategy_params"]
        == contract.EHLERS_CYCLE_FILTER_V1_CANONICAL_PARAMS
    )


def test_excluded_params_not_in_config(cfg: dict) -> None:
    params = cfg["economic_evaluation_v1"]["strategy_params"]
    for excluded in contract.EXCLUDED_BINDING_PARAMS:
        assert excluded not in params


def test_wrong_strategy_id_rejected() -> None:
    bad = _load_config()
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_id"] = "macd"
    reasons = contract.verify_ehlers_cycle_filter_v1_config_schema_v1(bad)
    assert "config_strategy_id_mismatch" in reasons


def test_excluded_param_rejected() -> None:
    bad = _load_config()
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_params"] = dict(
        contract.EHLERS_CYCLE_FILTER_V1_CANONICAL_PARAMS
    )
    bad["economic_evaluation_v1"]["strategy_params"]["cycle_threshold"] = 0.5
    reasons = contract.verify_ehlers_cycle_filter_v1_config_schema_v1(bad)
    assert "excluded_binding_param_in_config" in reasons


def test_risk_per_trade_invariant(cfg: dict) -> None:
    reasons = contract.verify_ehlers_cycle_filter_v1_sizing_policy_v1(cfg)
    assert not reasons
    bad = deepcopy(cfg)
    bad["offline_evaluation_sizing_contract_v1"] = dict(
        bad["offline_evaluation_sizing_contract_v1"]
    )
    bad["offline_evaluation_sizing_contract_v1"]["risk_per_trade"] = 0.01
    reasons = contract.verify_ehlers_cycle_filter_v1_sizing_policy_v1(bad)
    assert "policy_invariant_violation" in reasons


def test_roundtrip_cost_40bps(cfg: dict) -> None:
    binding = cfg["real_admissible_futures_evaluation_binding_v1"]
    assert binding["roundtrip_cost_bps"] == 40.0
    assert binding["effective_entry_cost_bps"] == 20.0
    assert binding["effective_exit_cost_bps"] == 20.0


def test_no_btc_or_spot_binding(cfg: dict) -> None:
    reasons = contract.verify_ehlers_cycle_filter_v1_instrument_binding_v1(cfg)
    assert not reasons
    bad = deepcopy(cfg)
    bad["real_admissible_futures_evaluation_binding_v1"] = dict(
        bad["real_admissible_futures_evaluation_binding_v1"]
    )
    bad["real_admissible_futures_evaluation_binding_v1"]["native_instrument_id"] = "BTC-USDT-SWAP"
    reasons = contract.verify_ehlers_cycle_filter_v1_instrument_binding_v1(bad)
    assert any("forbidden_instrument_binding" in r for r in reasons)


def test_ratification_authority_blocked_in_slice(cfg: dict) -> None:
    reasons = contract.verify_ehlers_cycle_filter_v1_ratification_authority_v1(cfg)
    assert not reasons
    bad = deepcopy(cfg)
    bad["step29m_policy_ratification_v1"] = dict(bad["step29m_policy_ratification_v1"])
    bad["step29m_policy_ratification_v1"]["evaluation_authorized"] = True
    reasons = contract.verify_ehlers_cycle_filter_v1_ratification_authority_v1(bad)
    assert "evaluation_authorized_not_false" in reasons


def test_warmup_for_canonical_params() -> None:
    effective, _ = resolve_effective_strategy_params_v1(
        "ehlers_cycle_filter",
        project_strategy_params_for_binding_v1(
            "ehlers_cycle_filter",
            contract.EHLERS_CYCLE_FILTER_V1_CANONICAL_PARAMS,
        ),
    )
    assert compute_required_warmup_rows_v1("ehlers_cycle_filter", effective) == 100


def test_unknown_strategy_param_fail_closed() -> None:
    with pytest.raises(StrategySignalBindingError, match="unknown_strategy_param"):
        resolve_effective_strategy_params_v1("ehlers_cycle_filter", {"cycle_threshold": 0.5})


def test_full_admissibility_contract_passes() -> None:
    result = contract.evaluate_ehlers_cycle_filter_v1_admissibility_contract_v1(repo_root=ROOT)
    assert result.admissibility_result.value == "PASS", result.blocking_reasons
    assert result.cost_binding_status == "PASS"
    assert result.policy_invariant_result == contract.POLICY_INVARIANT_RESULT
    assert result.signal_semantics == "LONG_FLAT_0_1"
    assert result.required_warmup_rows == 100


def test_versioned_bindings_materialized() -> None:
    binding = json.loads(VERSIONED_BINDING_PATH.read_text(encoding="utf-8"))
    scope = json.loads(SCOPE_RATIFICATION_PATH.read_text(encoding="utf-8"))
    material = json.loads(MATERIAL_DIFFERENCE_PATH.read_text(encoding="utf-8"))
    assert binding["candidate_id"] == "ehlers_cycle_filter/v1"
    assert binding["binding"]["binding_status"]["overall_binding_status"] == "COMPLETE"
    assert binding["binding"]["digest_bindings"]["config_digest"][
        "value"
    ] == contract.compute_evaluation_config_digest_v1(_load_config())
    assert scope["candidate_id"] == "ehlers_cycle_filter/v1"
    assert scope["config_digest"] == contract.compute_evaluation_config_digest_v1(_load_config())
    assert scope["economic_evaluation_executed"] is False
    assert scope["parameter_search_forbidden"] is True
    assert scope["material_difference_confirmed"] is True
    assert scope["prior_evidence_exclusion_pass"] is True
    assert material["material_difference_confirmed"] is True
    assert material["signal_family"] == "DSP_CYCLE_BANDPASS"


def test_configured_params_collected(cfg: dict) -> None:
    configured = collect_configured_strategy_params_v1(cfg, "ehlers_cycle_filter")
    assert configured == contract.EHLERS_CYCLE_FILTER_V1_CANONICAL_PARAMS
