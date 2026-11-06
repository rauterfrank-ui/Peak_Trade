"""R6 S2 portfolio-risk contracts tests (read-only, no-order)."""

from __future__ import annotations

import json

import pytest

from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.constants_v1 import (
    CONTRACT_CONFIG_REL_PATH,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
    NUMERIC_POLICY_STATUS,
    S3_RUNTIME_IMPLEMENTATION_AUTHORIZED,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.dimensions_v1 import (
    REQUIRED_ITEM_IDS,
    S2_DIMENSIONS,
    require_item,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.intents_v1 import require_intent
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.models_v1 import (
    ContractItemStatus,
    R6S2PortfolioRiskError,
    S2_CLOSABLE_STATUSES,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.verifier_v1 import (
    evaluate_r6_s2_portfolio_risk_contracts_v1,
    validate_layer_config_v1,
)


def test_layer_config_exists_and_matches_constants() -> None:
    payload = load_layer_config_v1()
    validate_layer_config_v1(payload)
    path = repo_root() / CONTRACT_CONFIG_REL_PATH
    disk = json.loads(path.read_text(encoding="utf-8"))
    assert digest_mapping(payload) == digest_mapping(disk)


def test_s2_dimensions_are_structurally_closable() -> None:
    assert tuple(row.item_id for row in S2_DIMENSIONS) == REQUIRED_ITEM_IDS
    for row in S2_DIMENSIONS:
        assert row.status in S2_CLOSABLE_STATUSES
    assert require_item("correlation_zero_corr_prohibition").status is (
        ContractItemStatus.CLOSED_PROVEN
    )
    assert require_item("safety_per_instrument_kill_interaction").status is (
        ContractItemStatus.NOT_REQUIRED_AT_S2
    )
    assert require_item("portfolio_var").status is ContractItemStatus.CLOSED_BOUNDARY
    assert require_item("safety_auto_liquidation_i12").status is (
        ContractItemStatus.CLOSED_BOUNDARY
    )


def test_intents_are_non_authority_and_not_dual_owners() -> None:
    i37 = require_intent("I37")
    i74 = require_intent("I74")
    i85 = require_intent("I85")
    assert i37.current_authority_effect == "NONE"
    assert i74.current_authority_effect == "NONE"
    assert i85.current_authority_effect == "NONE"
    assert i37.safe_to_bind_read_only is True
    assert i74.safe_to_bind_read_only is True
    assert i85.safe_to_bind_read_only is True
    assert "SECOND_VAR_AUTHORITY" in i37.duplicate_authority_risk
    assert "SECOND_VAR_ENGINE" in i74.duplicate_authority_risk
    assert "PARALLEL_PORTFOLIO_RISK_OWNER" in i85.duplicate_authority_risk


def test_this_pass_does_not_flip_implemented_authorized_or_numerics() -> None:
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MULTI_FUTURE_RUNTIME_IMPLEMENTED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert S3_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
    assert NUMERIC_POLICY_STATUS == "DEFERRED_UNRATIFIED"


def test_evaluate_pass_preserves_single_future_and_g13() -> None:
    claims = evaluate_r6_s2_portfolio_risk_contracts_v1()
    assert claims["verdict"] == "PASS_R6_S2_PORTFOLIO_RISK_CONTRACTS_V1"
    assert claims["s2_structural_contract_status"] == "CLOSED_PROVEN_FORENSIC_READ_ONLY"
    assert claims["r6_s2_closeout_status"] == "CLOSED_PROVEN_FORENSIC_READ_ONLY"
    assert claims["s2_status"] == "CLOSED_PROVEN_FORENSIC_READ_ONLY"
    assert claims["s3_runtime_implementation_authorized"] is False
    assert claims["s3_status"] == "BLOCKED_BY_SEPARATE_OWNER_GO"
    assert claims["s5_status"] == "BLOCKED_BY_SINGLE_FUTURE_LIVE_PROOF"
    assert claims["multi_future_runtime_authorized"] is False
    assert claims["multi_future_runtime_implemented"] is False
    assert claims["max_positions_effective"] == 1
    assert claims["single_selected_future_binding_preserved"] is True
    assert claims["duplicate_execution_writer_found"] is False
    assert claims["duplicate_accounting_writer_found"] is False
    assert claims["duplicate_risk_authority_found"] is False
    assert claims["single_future_live_proof"] is False
    assert claims["numeric_policy_status"] == "DEFERRED_UNRATIFIED"
    assert claims["g13_unchanged"] is True
    assert claims["g13_status"] == "INTENTIONAL_SAFETY_BARRIER"
    assert claims["canary_execute"] is False
    assert claims["order_effect"] == "NONE"
    assert claims["risk_logic_change"] is False
    assert claims["canonical_single_instrument_risk_owner"] == (
        "src.governance.capital_risk_sizing_v1"
    )
    assert claims["i37_status"] == "IMPLEMENTED_NOT_PROVEN_SUPPORTING_LIBRARY"
    assert claims["i74_status"] == "PLANNED_ONLY_ROADMAP_NON_RUNTIME"
    assert claims["i85_status"] == "CLOSED_BOUNDARY_CONTRACT_IDENTITY_G13_GATED"
    assert claims["smallest_missing_contract_gap"] == "NONE_FOR_S2_STRUCTURAL_FRAME"


def test_config_activation_g13_and_numeric_invention_fail_closed() -> None:
    payload = dict(load_layer_config_v1())
    payload["multi_future_runtime_authorized"] = True
    with pytest.raises(R6S2PortfolioRiskError, match="multi_future_runtime_authorized"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["multi_future_runtime_implemented"] = True
    with pytest.raises(R6S2PortfolioRiskError, match="multi_future_runtime_implemented"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["max_positions_effective"] = 2
    with pytest.raises(R6S2PortfolioRiskError, match="max_positions_effective"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["n_greater_than_one_ratified"] = True
    with pytest.raises(R6S2PortfolioRiskError, match="n_greater_than_one_ratified"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["portfolio_var_limit_ratified"] = True
    with pytest.raises(R6S2PortfolioRiskError, match="portfolio_var_limit_ratified"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["s3_runtime_implementation_authorized"] = True
    with pytest.raises(R6S2PortfolioRiskError, match="s3_runtime_implementation_authorized"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["risk_layer_manager_is_authority"] = True
    with pytest.raises(R6S2PortfolioRiskError, match="risk_layer_manager_is_authority"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["canary_execute"] = True
    with pytest.raises(R6S2PortfolioRiskError, match="canary_execute"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["single_future_live_proof"] = True
    with pytest.raises(R6S2PortfolioRiskError, match="single_future_live_proof"):
        validate_layer_config_v1(payload)
