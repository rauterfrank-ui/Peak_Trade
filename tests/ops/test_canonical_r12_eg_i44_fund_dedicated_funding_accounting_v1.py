"""R12 EG-I44 dedicated funding accounting tests (read-only, no-order)."""

from __future__ import annotations

import json

import pytest

from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.constants_v1 import (
    CONTRACT_CONFIG_REL_PATH,
    FUNDING_ACCOUNTING_ACTIVATED,
    FUNDING_IMPLEMENTATION_AUTHORIZED,
    G16_CLOSED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
    R6_S3_RUNTIME_IMPLEMENTATION_AUTHORIZED,
)
from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.contract_v1 import (
    REQUIRED_CONTRACT_ITEM_IDS,
    STRUCTURAL_CONTRACT,
    require_contract_item,
)
from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.dimensions_v1 import (
    require_dimension,
)
from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.evidence_pack_v1 import (
    require_evidence_step,
)
from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.models_v1 import (
    ContractItemStatus,
    R12EgI44FundError,
    STRUCTURAL_CLOSABLE_STATUSES,
)
from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.verifier_v1 import (
    evaluate_r12_eg_i44_fund_dedicated_funding_accounting_v1,
    validate_layer_config_v1,
)


def test_layer_config_exists_and_matches_constants() -> None:
    payload = load_layer_config_v1()
    validate_layer_config_v1(payload)
    path = repo_root() / CONTRACT_CONFIG_REL_PATH
    disk = json.loads(path.read_text(encoding="utf-8"))
    assert digest_mapping(payload) == digest_mapping(disk)


def test_structural_contract_is_closable_without_g16_pass() -> None:
    assert tuple(row.item_id for row in STRUCTURAL_CONTRACT) == REQUIRED_CONTRACT_ITEM_IDS
    for row in STRUCTURAL_CONTRACT:
        assert row.status in STRUCTURAL_CLOSABLE_STATUSES
    assert require_contract_item("fail_closed_behavior").status is ContractItemStatus.CLOSED_PROVEN
    assert require_evidence_step("verifier_pass").status is (
        ContractItemStatus.NOT_REQUIRED_UNTIL_ACTIVATION
    )
    assert require_dimension("ACTUAL_FUNDING_PAYMENT").status is ContractItemStatus.MISSING
    assert require_dimension("FUNDING_PNL").status is ContractItemStatus.CLOSED_BOUNDARY
    assert require_dimension("RESEARCH_FUNDING_FEATURE").claim_allowed_today is False


def test_this_pass_does_not_activate_funding_or_close_g16() -> None:
    assert G16_CLOSED is False
    assert FUNDING_ACCOUNTING_ACTIVATED is False
    assert FUNDING_IMPLEMENTATION_AUTHORIZED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MULTI_FUTURE_RUNTIME_IMPLEMENTED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert R6_S3_RUNTIME_IMPLEMENTATION_AUTHORIZED is False


def test_evaluate_pass_keeps_g16_open_and_single_future() -> None:
    claims = evaluate_r12_eg_i44_fund_dedicated_funding_accounting_v1()
    assert claims["verdict"] == "PASS_R12_EG_I44_FUND_STRUCTURAL_CONTRACT_V1"
    assert claims["funding_structural_contract_status"] == "CLOSED_PROVEN_FORENSIC_READ_ONLY"
    assert claims["g16_closed"] is False
    assert claims["target_dag_done_criterion_met"] is False
    assert claims["comparison_g16_semantically_distinct"] is True
    assert claims["master_g16_status"] == "INSUFFICIENT_EVIDENCE"
    assert claims["i44_status"] == "TRANSITIONAL_GATE_GATED_FUTURE_CAPABILITY_KEEP_GAP"
    assert claims["canonical_accounting_owner"] == (
        "ops.productive_futures_accounting_runtime_binding_v1"
    )
    assert claims["funding_application_owner"] == "NONE_PRODUCTIVE"
    assert claims["funding_recon_owner"] == "NONE_PRODUCTIVE"
    assert claims["field_present_does_not_prove_accounting"] is True
    assert claims["research_funding_is_productive_proof"] is False
    assert claims["duplicate_accounting_writer_found"] is False
    assert claims["research_to_accounting_bypass_found"] is False
    assert claims["funding_claim_fail_closed"] is True
    assert claims["r6_s3_runtime_implementation_authorized"] is False
    assert claims["multi_future_runtime_authorized"] is False
    assert claims["max_positions_effective"] == 1
    assert claims["canary_execute"] is False
    assert claims["order_effect"] == "NONE"
    assert claims["actual_funding_payment_status"] == "MISSING"
    assert claims["funding_paid_or_received_status"] == "NOT_REQUIRED_UNTIL_ACTIVATION"


def test_config_g16_close_and_activation_fail_closed() -> None:
    payload = dict(load_layer_config_v1())
    payload["g16_closed"] = True
    with pytest.raises(R12EgI44FundError, match="g16_closed"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["funding_accounting_activated"] = True
    with pytest.raises(R12EgI44FundError, match="funding_accounting_activated"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["funding_implementation_authorized"] = True
    with pytest.raises(R12EgI44FundError, match="funding_implementation_authorized"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["i44_out_of_scope_forever"] = True
    with pytest.raises(R12EgI44FundError, match="i44_out_of_scope_forever"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["research_funding_is_productive_proof"] = True
    with pytest.raises(R12EgI44FundError, match="research_funding_is_productive_proof"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["r6_s3_runtime_implementation_authorized"] = True
    with pytest.raises(R12EgI44FundError, match="r6_s3_runtime_implementation_authorized"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["canary_execute"] = True
    with pytest.raises(R12EgI44FundError, match="canary_execute"):
        validate_layer_config_v1(payload)
