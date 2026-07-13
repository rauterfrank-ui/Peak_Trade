"""Contract tests for canonical volatility_estimate feature contract v1 ratification."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.trading.master_v2 import canonical_volatility_estimate_feature_contract_v1 as contract

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / contract.CONTRACT_CONFIG_REL_PATH


def test_contract_config_exists_and_ratified() -> None:
    payload = contract.load_contract_config_v1()
    parsed = contract.parse_contract_v1(payload)
    assert parsed.contract_version == contract.CONTRACT_VERSION
    assert parsed.verdict == contract.RATIFIED_VERDICT
    assert parsed.owner_ratification_complete is True
    assert parsed.implementation_admissible is False


def test_contract_forbids_implicit_defaults_and_mv2_fallback() -> None:
    parsed = contract.load_ratified_contract_v1()
    assert parsed.implicit_default_allowed is False
    assert parsed.mv2_fallback_0_2_admissible is False
    assert parsed.annualization_mode == "NONE"
    assert parsed.annualization_factor == 1
    assert parsed.ddof == 0
    assert parsed.min_periods == contract.LOOKBACK_BARS == 60


def test_contract_binds_mark_price_log_return_semantics() -> None:
    parsed = contract.load_ratified_contract_v1()
    assert parsed.primary_price_source == "VENUE_MARK_PRICE"
    assert parsed.price_field == "mark_price"
    assert parsed.return_definition == "LOG_RETURN"
    assert parsed.return_formula == "ln(mark_price_t/mark_price_t_minus_1)"
    assert parsed.bar_interval == "PT1M"
    assert parsed.output_unit == "PER_BAR_DECIMAL_RETURN_VOLATILITY"
    assert parsed.output_annualized is False


def test_contract_reuse_basis_is_narrow_adapter_only() -> None:
    parsed = contract.load_ratified_contract_v1()
    assert parsed.implementation_reuse_decision == "REUSE_WITH_NARROW_ADAPTER"
    assert parsed.reuse_basis == contract.REUSE_BASIS
    assert parsed.reuse_limitation == "ROLLING_WINDOW_MECHANICS_ONLY"


def test_assert_ratification_complete_v1() -> None:
    ratified = contract.assert_ratification_complete_v1()
    assert ratified.feature_name == "volatility_estimate"


def test_materialized_owner_ratification_is_implementation_inadmissible() -> None:
    payload = contract.materialize_owner_ratification_v1(owner_operator="Frank Rauter")
    assert payload["ratification_complete"] is True
    assert payload["implementation_admissible"] is False
    assert payload["next_step_requires_separate_operator_go"] is True
    assert payload["verdict"] == contract.RATIFIED_VERDICT


def test_contract_config_digest_is_stable() -> None:
    payload = contract.load_contract_config_v1()
    first = contract.compute_contract_digest_v1(payload)
    second = contract.compute_contract_digest_v1(
        json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    )
    assert first == second


def test_validate_contract_config_v1_rejects_drift() -> None:
    payload = dict(contract.load_contract_config_v1())
    payload["lookback_bars"] = 20
    with pytest.raises(contract.CanonicalVolatilityFeatureContractError, match="lookback_bars"):
        contract.validate_contract_config_v1(payload)


def test_implementation_boundary_defers_productive_work() -> None:
    boundary = contract.materialize_implementation_boundary_v1()
    assert boundary["ratification_scope_complete"] is True
    assert "NO_MATERIALIZER_CHANGE" in boundary["forbidden_in_ratification_scope"]
