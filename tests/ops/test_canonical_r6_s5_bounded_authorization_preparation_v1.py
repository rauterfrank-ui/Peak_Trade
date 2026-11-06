"""R6 S5 bounded-authorization preparation tests (offline, unauthorized, no-order)."""

from __future__ import annotations

import json

import pytest

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    R6S3RuntimeArchitectureError,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.orchestrator_v1 import (
    default_single_future_request_v1,
    evaluate_phase_82_graph_v1,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.constants_v1 import (
    CONTRACT_CONFIG_REL_PATH,
    CURRENT_EFFECTIVE_RUNTIME_MODE,
    FUTURE_OWNER_GATE_IDS,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
    N_GREATER_THAN_ONE_RATIFIED,
    NEGATIVE_CASE_IDS,
    NUMERIC_POLICY_STATUS,
    PREPARATION_IS_NOT_AUTHORIZATION,
    S5_AUTHORIZATION_GRANTED,
    S5_PREPARED,
    SINGLE_FUTURE_LIVE_PROOF,
    SINGLE_FUTURE_LIVE_PROOF_REQUIRED_BEFORE_S5_AUTHORIZATION_GRANT,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.gates_v1 import (
    future_owner_gates_v1,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.models_v1 import (
    R6S5BoundedAuthorizationPreparationError,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.negative_v1 import (
    run_negative_matrix_v1,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.producer_v1 import (
    produce_bounded_authorization_preparation_v1,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.verifier_v1 import (
    evaluate_r6_s5_bounded_authorization_preparation_v1,
    validate_layer_config_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1 import (
    constants_v1 as cap72,
)
from src.ops.single_selected_future_policy_v1 import constants_v1 as cap23


def test_layer_config_exists_and_matches_constants() -> None:
    payload = load_layer_config_v1()
    validate_layer_config_v1(payload)
    path = repo_root() / CONTRACT_CONFIG_REL_PATH
    disk = json.loads(path.read_text(encoding="utf-8"))
    assert digest_mapping(payload) == digest_mapping(disk)


def test_authorization_flags_remain_fail_closed() -> None:
    assert MULTI_FUTURE_RUNTIME_IMPLEMENTED is True
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert S5_AUTHORIZATION_GRANTED is False
    assert S5_PREPARED is True
    assert PREPARATION_IS_NOT_AUTHORIZATION is True
    assert N_GREATER_THAN_ONE_RATIFIED is False
    assert CURRENT_EFFECTIVE_RUNTIME_MODE == "SINGLE_SELECTED_FUTURE"
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert NUMERIC_POLICY_STATUS == "DEFERRED_UNRATIFIED"
    assert SINGLE_FUTURE_LIVE_PROOF is False
    assert SINGLE_FUTURE_LIVE_PROOF_REQUIRED_BEFORE_S5_AUTHORIZATION_GRANT is True


def test_future_owner_gates_are_independent_and_ungranted() -> None:
    gates = future_owner_gates_v1()
    assert tuple(FUTURE_OWNER_GATE_IDS) == (
        "OWNER_GO_S5_AUTHORIZATION_GRANT",
        "OWNER_GO_N_GREATER_THAN_ONE_POLICY",
        "OWNER_GO_G13_CONTROLLED_UNLOCK",
        "OWNER_GO_PRODUCTIVE_MF_ACTIVATION",
        "OWNER_GO_SUBMIT_UNLOCK",
    )
    for gate_id in FUTURE_OWNER_GATE_IDS:
        assert gates[gate_id] is False
    assert gates["any_future_owner_gate_granted"] is False
    assert gates["one_bool_cannot_unlock_all"] is True


def test_preparation_envelope_records_blockers_without_grant() -> None:
    bundle = produce_bounded_authorization_preparation_v1()
    body = bundle["body"]
    assert body["authority_separation"]["preparation_is_not_authorization"] is True
    assert body["authority_separation"]["s5_authorization_granted"] is False
    assert body["authority_separation"]["multi_future_runtime_authorized"] is False
    assert body["authority_separation"]["g13_unchanged"] is True
    assert body["authority_separation"]["n_greater_than_one_ratified"] is False
    assert body["current_effective_safety_state"]["max_positions_effective"] == 1
    assert body["current_effective_safety_state"]["current_effective_runtime_mode"] == (
        "SINGLE_SELECTED_FUTURE"
    )
    assert body["current_effective_safety_state"]["execution_writer_count"] == 1
    assert body["current_effective_safety_state"]["accounting_writer_count"] == 1
    assert body["pre_grant_blockers"]["numeric_policy_status"] == "DEFERRED_UNRATIFIED"
    assert body["pre_grant_blockers"]["single_future_live_proof"] is False
    assert body["pre_grant_blockers"][
        "single_future_live_proof_required_before_s5_authorization_grant"
    ]
    assert body["pre_grant_blockers"]["s4_sim_evidence_is_not_live_proof"] is True
    assert body["pre_grant_blockers"]["single_future_defaults_are_not_mf_numerics"] is True
    assert not any(body["pre_grant_blockers"]["live_proof_derivation"].values())
    assert body["source_evidence"]["s4_config"]["status"] == "MANIFEST_VERIFIED"
    assert body["source_evidence"]["external"]["status"] == "NOT_REFERENCED"
    assert len(bundle["identity"]["experiment_identity_id"]) == 64
    assert bundle["manifest"]["content_hash"] == bundle["preparation_digest"]
    second = produce_bounded_authorization_preparation_v1()
    assert second["preparation_digest"] == bundle["preparation_digest"]
    assert (
        second["identity"]["experiment_identity_id"] == bundle["identity"]["experiment_identity_id"]
    )


def test_negative_matrix_is_complete_and_fail_closed() -> None:
    results = run_negative_matrix_v1()
    assert tuple(results) == NEGATIVE_CASE_IDS
    for case_id, row in results.items():
        assert row["fail_closed"] is True, case_id


def test_single_future_authorized_behavior_unchanged() -> None:
    result = evaluate_phase_82_graph_v1(
        default_single_future_request_v1("BTC-USDT-SWAP", extra_candidates=("ETH-USDT-SWAP",))
    )
    assert result.effective_active_ids == ("BTC-USDT-SWAP",)
    assert result.max_positions_effective == 1
    assert result.authorized is False
    assert result.submit_unlocked is False
    assert cap23.MAX_POSITIONS_EFFECTIVE == 1
    assert cap23.MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert getattr(cap72, "MULTI_FUTURE_RUNTIME_IMPLEMENTED", False) is False


def test_preparation_pass_cannot_be_read_as_authorization() -> None:
    claims = evaluate_r6_s5_bounded_authorization_preparation_v1()
    assert claims["verdict"] == "PASS_R6_S5_BOUNDED_AUTHORIZATION_PREPARATION_V1"
    assert claims["r6_s5_status"] == "PREPARED_UNAUTHORIZED"
    assert claims["s5_authorization_granted"] is False
    assert claims["s5_prepared"] is True
    assert claims["preparation_is_not_authorization"] is True
    assert claims["evidence_is_not_authorization"] is True
    assert claims["multi_future_runtime_authorized"] is False
    assert claims["multi_future_runtime_implemented"] is True
    assert claims["g13_unchanged"] is True
    assert claims["current_effective_runtime_mode"] == "SINGLE_SELECTED_FUTURE"
    assert claims["max_positions_effective"] == 1
    assert claims["n_greater_than_one_ratified"] is False
    assert claims["top_n_active_set_authority"] is False
    assert claims["productive_mf_caller_authorized"] is False
    assert claims["activated"] is False
    assert claims["submit_unlocked"] is False
    assert claims["second_execution_authority_created"] is False
    assert claims["second_accounting_authority_created"] is False
    assert claims["second_decision_authority_created"] is False
    assert claims["single_future_live_proof"] is False
    assert claims["single_future_live_proof_required_before_s5_authorization_grant"] is True
    assert claims["numeric_policy_status"] == "DEFERRED_UNRATIFIED"
    assert claims["live_authorized"] is False
    assert claims["testnet_authorized"] is False
    assert claims["canary_authorized"] is False
    assert claims["funding_runtime_activated"] is False
    assert claims["network_effect"] == "NONE"
    assert claims["order_effect"] == "NONE"
    assert claims["account_mutation_effect"] == "NONE"
    assert claims["single_global_execution_writer_proven"] is True
    assert claims["single_global_accounting_writer_proven"] is True
    assert claims["single_future_authorized_behavior_unchanged"] is True
    assert claims["s6_autonomous_granted"] is False
    assert claims["next_stage_automatically_authorized"] is False
    assert claims["future_owner_gates"]["OWNER_GO_S5_AUTHORIZATION_GRANT"] is False
    assert claims["future_owner_gates"]["OWNER_GO_SUBMIT_UNLOCK"] is False


def test_config_cannot_authorize_or_raise_positions() -> None:
    payload = dict(load_layer_config_v1())
    payload["multi_future_runtime_authorized"] = True
    with pytest.raises(
        R6S5BoundedAuthorizationPreparationError, match="multi_future_runtime_authorized"
    ):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["s5_authorization_granted"] = True
    with pytest.raises(R6S5BoundedAuthorizationPreparationError, match="s5_authorization_granted"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["max_positions_effective"] = 2
    with pytest.raises(R6S5BoundedAuthorizationPreparationError, match="max_positions_effective"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["submit_unlocked"] = True
    with pytest.raises(R6S5BoundedAuthorizationPreparationError, match="submit_unlocked"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["preparation_is_not_authorization"] = False
    with pytest.raises(
        R6S5BoundedAuthorizationPreparationError, match="preparation_is_not_authorization"
    ):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["single_future_live_proof"] = True
    with pytest.raises(R6S5BoundedAuthorizationPreparationError, match="single_future_live_proof"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["numeric_policy_status"] = "RESOLVED"
    with pytest.raises(R6S5BoundedAuthorizationPreparationError, match="numeric_policy_status"):
        validate_layer_config_v1(payload)


def test_s3_unauthorized_activation_still_rejected() -> None:
    request = default_single_future_request_v1("AAA-FUT")
    with pytest.raises(R6S3RuntimeArchitectureError, match="authorized_rejected"):
        evaluate_phase_82_graph_v1(
            request.__class__(
                selected_future_id=request.selected_future_id,
                ranking_candidates=request.ranking_candidates,
                instrument_contexts=request.instrument_contexts,
                requested_authorized=True,
            )
        )
