"""Contract tests for STEP29M bouchaud_microstructure_ohlcv_proxy v1 admissibility v1."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.backtest import (
    step29m_bouchaud_microstructure_ohlcv_proxy_v1_economic_evaluation_admissibility_contract_v1 as contract,
)
from src.backtest.strategy_signal_binding_v1 import (
    compute_required_warmup_rows_v1,
    project_strategy_params_for_binding_v1,
    resolve_effective_strategy_params_v1,
)
from src.strategies.bouchaud.bouchaud_microstructure_strategy import BouchaudMicrostructureStrategy
from src.strategies.registry import get_strategy_registry_entry, resolve_strategy_id

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    ROOT
    / "config/ops/step29m_okx_inst_eth_usdt_perp_bouchaud_microstructure_ohlcv_proxy_v1_economic_evaluation_v1.json"
)
BINDING_PATH = (
    ROOT
    / "config/research/bouchaud_microstructure_ohlcv_proxy_v1_versioned_research_binding_v0.json"
)


def _load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def cfg() -> dict:
    return _load_config()


def test_research_scope_is_bouchaud_ohlcv_proxy_v1(cfg: dict) -> None:
    assert (
        cfg["economic_evaluation_v1"]["research_scope"] == "bouchaud_microstructure_ohlcv_proxy/v1"
    )
    assert (
        cfg["research_scope_binding_v1"]["research_scope"]
        == "bouchaud_microstructure_ohlcv_proxy/v1"
    )


def test_hypothesis_id_stable(cfg: dict) -> None:
    assert (
        cfg["research_scope_binding_v1"]["hypothesis_id"]
        == "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1"
    )


def test_proxy_semantics_explicitly_true(cfg: dict) -> None:
    assert cfg["research_scope_binding_v1"]["proxy_semantics"] is True


def test_true_tick_l2_semantics_explicitly_false(cfg: dict) -> None:
    assert cfg["research_scope_binding_v1"]["true_tick_l2_microstructure"] is False
    for flag in (
        "tick_data_required",
        "orderbook_data_required",
        "depth_data_required",
        "l2_data_required",
    ):
        assert cfg["research_scope_binding_v1"][flag] is False


def test_finalized_ohlcv_bars_only(cfg: dict) -> None:
    assert cfg["research_scope_binding_v1"]["data_class"] == "FINALIZED_OHLCV_BARS"


def test_bitcoin_spot_synthetic_spot_blocked(cfg: dict) -> None:
    reasons = contract.verify_bouchaud_microstructure_ohlcv_proxy_v1_instrument_binding_v1(cfg)
    assert not reasons
    bad = deepcopy(cfg)
    bad["real_admissible_futures_evaluation_binding_v1"] = dict(
        bad["real_admissible_futures_evaluation_binding_v1"]
    )
    bad["real_admissible_futures_evaluation_binding_v1"]["canonical_instrument_id"] = (
        "inst-btc-usdt-perp"
    )
    reasons = contract.verify_bouchaud_microstructure_ohlcv_proxy_v1_instrument_binding_v1(bad)
    assert any("forbidden_instrument_binding" in r for r in reasons)


def test_wrong_research_scope_rejected() -> None:
    bad = _load_config()
    bad["research_scope_binding_v1"] = dict(bad["research_scope_binding_v1"])
    bad["research_scope_binding_v1"]["research_scope"] = "bouchaud_microstructure_tick_l2/v1"
    reasons = contract.verify_bouchaud_microstructure_ohlcv_proxy_v1_scope_binding_v1(bad)
    assert "research_scope_mismatch" in reasons


def test_tick_l2_scope_rejected_by_adapter_helper() -> None:
    from src.research.bouchaud_microstructure_ohlcv_proxy_v1_step29m_single_instrument_offline_evaluation_adapter_v0 import (
        verify_tick_l2_scope_rejected_v0,
    )

    assert verify_tick_l2_scope_rejected_v0("bouchaud_microstructure_tick_l2/v1") == (
        "tick_l2_scope_not_implemented",
    )


def test_implementation_go_rejected_for_evaluation_authorization() -> None:
    reasons = contract.verify_bouchaud_microstructure_ohlcv_proxy_v1_go_token_policy_v1(
        contract.IMPLEMENTATION_GO_TOKEN
    )
    assert "implementation_go_cannot_authorize_evaluation" in reasons


def test_future_evaluation_go_accepted_for_validation_only() -> None:
    assert contract.verify_evaluation_go_token_accepted_for_validation_only_v1(
        contract.EVALUATION_GO_TOKEN
    )


def test_missing_future_evaluation_go_rejected() -> None:
    reasons = contract.verify_bouchaud_microstructure_ohlcv_proxy_v1_go_token_policy_v1("GO_WRONG")
    assert any(r.startswith("invalid_go_token:") for r in reasons)


def test_canonical_strategy_owner_invoked() -> None:
    entry = get_strategy_registry_entry("bouchaud_microstructure")
    assert (
        entry.implementation_ref == contract.BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_STRATEGY_OWNER
    )
    strategy = BouchaudMicrostructureStrategy()
    assert strategy.KEY == "bouchaud_microstructure"


def test_admissibility_contract_passes_on_canonical_config() -> None:
    result = contract.evaluate_bouchaud_microstructure_ohlcv_proxy_v1_admissibility_contract_v1(
        repo_root=ROOT,
    )
    assert result.admissibility_result.value == "PASS"
    assert result.research_scope == "bouchaud_microstructure_ohlcv_proxy/v1"
    assert result.proxy_semantics is True
    assert result.true_tick_l2_microstructure is False
    guard = contract.evaluate_bouchaud_microstructure_ohlcv_proxy_v1_sizing_digest_admissibility_guard_v1(
        repo_root=ROOT,
    )
    assert guard.admissible is True
    assert guard.economic_evaluation_executed is False


def test_stale_sizing_digest_blocked_by_admissibility_contract(cfg: dict) -> None:
    bad = deepcopy(cfg)
    bad["offline_evaluation_sizing_contract_v1"] = dict(
        bad["offline_evaluation_sizing_contract_v1"]
    )
    bad["offline_evaluation_sizing_contract_v1"]["config_digest"] = (
        "c0b377c523ccc6ed8c69e0976c36f19ba6d1f5f01080aecd36004f9d87bcddee"
    )
    configured = bad["economic_evaluation_v1"]["strategy_params"]
    effective, params_digest = resolve_effective_strategy_params_v1(
        "bouchaud_microstructure",
        project_strategy_params_for_binding_v1("bouchaud_microstructure", configured),
    )
    reasons = contract.verify_bouchaud_microstructure_ohlcv_proxy_v1_sizing_config_digest_v1(
        bad,
        strategy_params_digest=params_digest,
    )
    assert "sizing_config_digest_mismatch" in reasons


def test_warmup_rows_match_lookback_ticks(cfg: dict) -> None:
    params = cfg["economic_evaluation_v1"]["strategy_params"]
    effective, _ = resolve_effective_strategy_params_v1(
        "bouchaud_microstructure",
        project_strategy_params_for_binding_v1("bouchaud_microstructure", params),
    )
    warmup = compute_required_warmup_rows_v1("bouchaud_microstructure", effective)
    assert warmup == contract.BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_REQUIRED_WARMUP_ROWS


def test_versioned_binding_matches_research_scope() -> None:
    binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
    assert binding["research_scope"] == "bouchaud_microstructure_ohlcv_proxy/v1"
    assert binding["evaluation_authorized"] is False
    assert binding["economic_evaluation_executed"] is False
