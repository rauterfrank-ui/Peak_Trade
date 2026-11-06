"""R6 Phase-8.1 policy precondition tests (read-only, no-order)."""

from __future__ import annotations

import json

import pytest

from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.checklist_v1 import (
    REQUIRED_ITEM_IDS,
    S1_CHECKLIST,
    require_item,
)
from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.constants_v1 import (
    CONTRACT_CONFIG_REL_PATH,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
)
from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.models_v1 import (
    PolicyItemStatus,
    R6Phase81PolicyError,
)
from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.verifier_v1 import (
    evaluate_r6_phase_8_1_policy_precondition_v1,
    validate_layer_config_v1,
)


def test_layer_config_exists_and_matches_constants() -> None:
    payload = load_layer_config_v1()
    validate_layer_config_v1(payload)
    path = repo_root() / CONTRACT_CONFIG_REL_PATH
    disk = json.loads(path.read_text(encoding="utf-8"))
    assert digest_mapping(payload) == digest_mapping(disk)


def test_s1_checklist_covers_required_items() -> None:
    assert tuple(row.item_id for row in S1_CHECKLIST) == REQUIRED_ITEM_IDS
    allowed = {
        PolicyItemStatus.CLOSED_PROVEN,
        PolicyItemStatus.NOT_REQUIRED_AT_THIS_STAGE,
    }
    for row in S1_CHECKLIST:
        assert row.status in allowed
    assert require_item("no_silent_g13_bypass").status is PolicyItemStatus.CLOSED_PROVEN
    assert (
        require_item("correlation_handling").status is PolicyItemStatus.NOT_REQUIRED_AT_THIS_STAGE
    )
    assert (
        require_item("component_portfolio_var_ownership").status
        is PolicyItemStatus.NOT_REQUIRED_AT_THIS_STAGE
    )


def test_this_pass_does_not_flip_implemented_or_authorized() -> None:
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MULTI_FUTURE_RUNTIME_IMPLEMENTED is False
    assert MAX_POSITIONS_EFFECTIVE == 1


def test_evaluate_pass_preserves_single_future_and_g13() -> None:
    claims = evaluate_r6_phase_8_1_policy_precondition_v1()
    assert claims["verdict"] == "PASS_R6_PHASE_8_1_POLICY_PRECONDITION_V1"
    assert claims["phase_8_1_policy_checklist_status"] == "CLOSED_PROVEN_FORENSIC_READ_ONLY"
    assert claims["s0_status"] == "CLOSED_PROVEN_CURRENT_SINGLE_FUTURE_BARRIER"
    assert claims["s1_status"] == "CLOSED_PROVEN_FORENSIC_READ_ONLY"
    assert claims["s2_status"] == "PLANNED_ONLY"
    assert claims["s3_status"] == "BLOCKED_BY_SEPARATE_OWNER_GO"
    assert claims["s5_status"] == "BLOCKED_BY_SINGLE_FUTURE_LIVE_PROOF"
    assert claims["s6_status"] == "BLOCKED_BY_SINGLE_FUTURE_LIVE_PROOF"
    assert claims["multi_future_runtime_authorized"] is False
    assert claims["multi_future_runtime_implemented"] is False
    assert claims["max_positions_effective"] == 1
    assert claims["single_selected_future_binding_preserved"] is True
    assert claims["duplicate_execution_writer_found"] is False
    assert claims["duplicate_accounting_writer_found"] is False
    assert claims["single_future_live_proof"] is False
    assert claims["i17_is_not_live_proof"] is True
    assert claims["testnet_is_not_live_proof"] is True
    assert claims["shadow_is_not_live_proof"] is True
    assert claims["canary_execute"] is False
    assert claims["r6_runtime_authorized"] is False
    assert claims["g13_status"] == "INTENTIONAL_SAFETY_BARRIER"
    assert claims["top_n_active_set_authority"] is False
    assert claims["order_effect"] == "NONE"


def test_config_activation_and_g13_bypass_fail_closed() -> None:
    payload = dict(load_layer_config_v1())
    payload["multi_future_runtime_authorized"] = True
    with pytest.raises(R6Phase81PolicyError, match="multi_future_runtime_authorized"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["multi_future_runtime_implemented"] = True
    with pytest.raises(R6Phase81PolicyError, match="multi_future_runtime_implemented"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["max_positions_effective"] = 2
    with pytest.raises(R6Phase81PolicyError, match="max_positions_effective"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["single_future_live_proof"] = True
    with pytest.raises(R6Phase81PolicyError, match="single_future_live_proof"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["canary_execute"] = True
    with pytest.raises(R6Phase81PolicyError, match="canary_execute"):
        validate_layer_config_v1(payload)
