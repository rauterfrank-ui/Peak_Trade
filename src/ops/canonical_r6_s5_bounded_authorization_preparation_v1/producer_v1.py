"""Deterministic R6 S5 bounded-authorization preparation producer.

Builds a fail-closed preparation envelope over persisted S1-S4 contracts.
Does not grant authorization, unlock G13, ratify N>1, or submit orders.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.lineage_v1 import (
    load_layer_config_v1 as load_s1_config_v1,
)
from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.verifier_v1 import (
    evaluate_r6_phase_8_1_policy_precondition_v1,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.lineage_v1 import (
    load_layer_config_v1 as load_s2_config_v1,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.verifier_v1 import (
    evaluate_r6_s2_portfolio_risk_contracts_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    CANONICAL_ACCOUNTING_WRITER_IDENTITY,
    CANONICAL_EXECUTION_WRITER_IDENTITY,
    SINGLE_GLOBAL_ACCOUNTING_WRITER,
    SINGLE_GLOBAL_EXECUTION_WRITER,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.lineage_v1 import (
    load_layer_config_v1 as load_s3_config_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.orchestrator_v1 import (
    default_single_future_request_v1,
    evaluate_phase_82_graph_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.verifier_v1 import (
    evaluate_r6_s3_multi_future_runtime_architecture_v1,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.lineage_v1 import (
    load_layer_config_v1 as load_s4_config_v1,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.verifier_v1 import (
    evaluate_r6_s4_multi_future_shadow_sim_evidence_v1,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.constants_v1 import (
    ACCOUNT_MUTATION_EFFECT,
    ACTIVATED,
    AUTHORITY_EFFECT,
    BOUNDED_AUTO_PROMOTION,
    CANARY_AUTHORIZED,
    COMPONENT_VAR_LIMIT_RATIFIED,
    CONCENTRATION_PERCENTAGE_RATIFIED,
    CORRELATION_THRESHOLD_RATIFIED,
    CURRENT_EFFECTIVE_RUNTIME_MODE,
    EVIDENCE_IS_NOT_AUTHORIZATION,
    FUNDING_RUNTIME_ACTIVATED,
    G13_STATUS,
    G13_UNCHANGED,
    GET_ONLY_LIVE_IS_NOT_LIVE_ORDER_PROOF,
    GROSS_NET_EXPOSURE_LIMIT_RATIFIED,
    I17_IS_NOT_LIVE_PROOF,
    LIVE_AUTHORIZED,
    LIVE_CANARY_PROOF_REQUIRED,
    LIVE_ORDER_ECONOMIC_PROOF_REQUIRED,
    MAX_POSITIONS_EFFECTIVE,
    MF_COOLDOWN_POLICY_RATIFIED,
    MF_OPEN_POSITION_TREATMENT_RATIFIED,
    MF_ROTATION_HYSTERESIS_POLICY_RATIFIED,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
    N_GREATER_THAN_ONE_RATIFIED,
    NETWORK_EFFECT,
    NO_AUTOMATIC_S5_TO_S6_PROGRESSION,
    NUMERIC_POLICY_STATUS,
    ORDER_EFFECT,
    PER_INSTRUMENT_CAPITAL_BUDGET_RATIFIED,
    PORTFOLIO_VAR_LIMIT_RATIFIED,
    PREPARATION_IS_NOT_AUTHORIZATION,
    PRODUCTIVE_MF_CALLER_AUTHORIZED,
    S4_SIM_EVIDENCE_IS_NOT_LIVE_PROOF,
    S5_AUTHORIZATION_GRANTED,
    S5_PREPARED,
    S6_AUTONOMOUS_GRANTED,
    SECOND_ACCOUNTING_AUTHORITY_CREATED,
    SECOND_DECISION_AUTHORITY_CREATED,
    SECOND_EXECUTION_AUTHORITY_CREATED,
    SHADOW_IS_NOT_LIVE_PROOF,
    SINGLE_FUTURE_DEFAULTS_ARE_NOT_MF_NUMERICS,
    SINGLE_FUTURE_LIVE_PROOF,
    SINGLE_FUTURE_LIVE_PROOF_MEANING,
    SINGLE_FUTURE_LIVE_PROOF_REQUIRED_BEFORE_S5_AUTHORIZATION_GRANT,
    SINGLE_FUTURE_LIVE_PROOF_STATUS,
    SOURCE_EVIDENCE_EXTERNAL,
    SOURCE_EVIDENCE_S1,
    SOURCE_EVIDENCE_S2,
    SOURCE_EVIDENCE_S3,
    SOURCE_EVIDENCE_S4,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
    TESTNET_IS_NOT_LIVE_PROOF,
    TOP_N_ACTIVE_SET_AUTHORITY,
    ZERO_CORRELATION_OPTIMISTIC_FALLBACK_FORBIDDEN,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.gates_v1 import (
    future_owner_gates_v1,
    reject_if_any_gate_granted_v1,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.identity_v1 import (
    build_preparation_identity_v1,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.lineage_v1 import (
    digest_mapping,
    envelope_digest,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.models_v1 import (
    R6S5BoundedAuthorizationPreparationError,
)


def _reject(message: str) -> None:
    raise R6S5BoundedAuthorizationPreparationError(message)


def produce_bounded_authorization_preparation_v1() -> Mapping[str, Any]:
    if PREPARATION_IS_NOT_AUTHORIZATION is not True:
        _reject("preparation_is_not_authorization_doctrine_missing")
    if EVIDENCE_IS_NOT_AUTHORIZATION is not True:
        _reject("evidence_is_not_authorization_doctrine_missing")
    if S5_AUTHORIZATION_GRANTED is not False:
        _reject("s5_authorization_granted_must_remain_false")
    if MULTI_FUTURE_RUNTIME_AUTHORIZED is not False:
        _reject("multi_future_runtime_authorized_must_remain_false")
    if S5_PREPARED is not True:
        _reject("s5_prepared_not_true")
    gates = future_owner_gates_v1()
    reject_if_any_gate_granted_v1(gates)
    s1 = evaluate_r6_phase_8_1_policy_precondition_v1()
    s2 = evaluate_r6_s2_portfolio_risk_contracts_v1()
    s3 = evaluate_r6_s3_multi_future_runtime_architecture_v1()
    s4 = evaluate_r6_s4_multi_future_shadow_sim_evidence_v1()
    if s1["verdict"] != "PASS_R6_PHASE_8_1_POLICY_PRECONDITION_V1":
        _reject("s1_contract_not_pass")
    if s2["verdict"] != "PASS_R6_S2_PORTFOLIO_RISK_CONTRACTS_V1":
        _reject("s2_contract_not_pass")
    if s3["verdict"] != "PASS_R6_S3_MULTI_FUTURE_RUNTIME_ARCHITECTURE_V1":
        _reject("s3_contract_not_pass")
    if s4["verdict"] != "PASS_R6_S4_MULTI_FUTURE_SHADOW_SIM_EVIDENCE_V1":
        _reject("s4_contract_not_pass")
    if s4["s5_authorization_granted"] is not False:
        _reject("s4_claimed_s5_authorization")
    if s4["evidence_is_not_authorization"] is not True:
        _reject("s4_evidence_read_as_authorization")
    single = evaluate_phase_82_graph_v1(default_single_future_request_v1("BTC-USDT-SWAP"))
    if single.authorized is not False:
        _reject("s3_graph_authorized_true")
    if single.max_positions_effective != 1:
        _reject("max_positions_effective_drift")
    if single.effective_runtime_mode != CURRENT_EFFECTIVE_RUNTIME_MODE:
        _reject("effective_runtime_mode_drift")
    if SINGLE_GLOBAL_EXECUTION_WRITER is not True:
        _reject("single_global_execution_writer_missing")
    if SINGLE_GLOBAL_ACCOUNTING_WRITER is not True:
        _reject("single_global_accounting_writer_missing")
    writers = {
        "accounting_writer_count": 1,
        "accounting_writer_identity": CANONICAL_ACCOUNTING_WRITER_IDENTITY,
        "execution_writer_count": 1,
        "execution_writer_identity": CANONICAL_EXECUTION_WRITER_IDENTITY,
        "second_accounting_authority_created": SECOND_ACCOUNTING_AUTHORITY_CREATED,
        "second_decision_authority_created": SECOND_DECISION_AUTHORITY_CREATED,
        "second_execution_authority_created": SECOND_EXECUTION_AUTHORITY_CREATED,
        "single_global_accounting_writer_proven": True,
        "single_global_execution_writer_proven": True,
    }
    if writers["execution_writer_identity"] == writers["accounting_writer_identity"]:
        _reject("writer_identities_collapsed")
    source_evidence = {
        "s1_config": {
            "digest": digest_mapping(load_s1_config_v1()),
            "status": SOURCE_EVIDENCE_S1,
        },
        "s2_config": {
            "digest": digest_mapping(load_s2_config_v1()),
            "status": SOURCE_EVIDENCE_S2,
        },
        "s3_config": {
            "digest": digest_mapping(load_s3_config_v1()),
            "status": SOURCE_EVIDENCE_S3,
        },
        "s4_config": {
            "digest": digest_mapping(load_s4_config_v1()),
            "status": SOURCE_EVIDENCE_S4,
        },
        "external": {"digest": None, "status": SOURCE_EVIDENCE_EXTERNAL},
    }
    body = {
        "authority_separation": {
            "activated": ACTIVATED,
            "authority_effect": AUTHORITY_EFFECT,
            "bounded_auto_promotion": BOUNDED_AUTO_PROMOTION,
            "evidence_is_not_authorization": True,
            "g13_status": G13_STATUS,
            "g13_unchanged": G13_UNCHANGED,
            "multi_future_runtime_authorized": MULTI_FUTURE_RUNTIME_AUTHORIZED,
            "n_greater_than_one_ratified": N_GREATER_THAN_ONE_RATIFIED,
            "preparation_is_not_authorization": True,
            "productive_mf_caller_authorized": PRODUCTIVE_MF_CALLER_AUTHORIZED,
            "s5_authorization_granted": False,
            "s5_prepared": True,
            "s6_autonomous_granted": S6_AUTONOMOUS_GRANTED,
            "submit_unlocked": SUBMIT_UNLOCKED,
            "top_n_active_set_authority": TOP_N_ACTIVE_SET_AUTHORITY,
        },
        "current_effective_safety_state": {
            "account_mutation_effect": ACCOUNT_MUTATION_EFFECT,
            "canary_authorized": CANARY_AUTHORIZED,
            "current_effective_runtime_mode": CURRENT_EFFECTIVE_RUNTIME_MODE,
            "funding_runtime_activated": FUNDING_RUNTIME_ACTIVATED,
            "live_authorized": LIVE_AUTHORIZED,
            "max_positions_effective": MAX_POSITIONS_EFFECTIVE,
            "multi_future_runtime_implemented": MULTI_FUTURE_RUNTIME_IMPLEMENTED,
            "network_effect": NETWORK_EFFECT,
            "order_effect": ORDER_EFFECT,
            "testnet_authorized": TESTNET_AUTHORIZED,
            **writers,
        },
        "future_owner_gates": dict(gates),
        "pre_grant_blockers": {
            "component_var_limit_ratified": COMPONENT_VAR_LIMIT_RATIFIED,
            "concentration_percentage_ratified": CONCENTRATION_PERCENTAGE_RATIFIED,
            "correlation_threshold_ratified": CORRELATION_THRESHOLD_RATIFIED,
            "get_only_live_is_not_live_order_proof": GET_ONLY_LIVE_IS_NOT_LIVE_ORDER_PROOF,
            "gross_net_exposure_limit_ratified": GROSS_NET_EXPOSURE_LIMIT_RATIFIED,
            "i17_is_not_live_proof": I17_IS_NOT_LIVE_PROOF,
            "live_canary_proof_required": LIVE_CANARY_PROOF_REQUIRED,
            "live_order_economic_proof_required": LIVE_ORDER_ECONOMIC_PROOF_REQUIRED,
            "live_proof_derivation": {
                "get_only_live": False,
                "i17": False,
                "s4_sim_evidence": False,
                "shadow": False,
                "testnet": False,
            },
            "mf_cooldown_policy_ratified": MF_COOLDOWN_POLICY_RATIFIED,
            "mf_open_position_treatment_ratified": MF_OPEN_POSITION_TREATMENT_RATIFIED,
            "mf_rotation_hysteresis_policy_ratified": MF_ROTATION_HYSTERESIS_POLICY_RATIFIED,
            "no_automatic_s5_to_s6_progression": NO_AUTOMATIC_S5_TO_S6_PROGRESSION,
            "numeric_policy_status": NUMERIC_POLICY_STATUS,
            "per_instrument_capital_budget_ratified": PER_INSTRUMENT_CAPITAL_BUDGET_RATIFIED,
            "portfolio_var_limit_ratified": PORTFOLIO_VAR_LIMIT_RATIFIED,
            "s4_sim_evidence_is_not_live_proof": S4_SIM_EVIDENCE_IS_NOT_LIVE_PROOF,
            "shadow_is_not_live_proof": SHADOW_IS_NOT_LIVE_PROOF,
            "single_future_defaults_are_not_mf_numerics": (
                SINGLE_FUTURE_DEFAULTS_ARE_NOT_MF_NUMERICS
            ),
            "single_future_live_proof": SINGLE_FUTURE_LIVE_PROOF,
            "single_future_live_proof_meaning": SINGLE_FUTURE_LIVE_PROOF_MEANING,
            "single_future_live_proof_required_before_s5_authorization_grant": (
                SINGLE_FUTURE_LIVE_PROOF_REQUIRED_BEFORE_S5_AUTHORIZATION_GRANT
            ),
            "single_future_live_proof_status": SINGLE_FUTURE_LIVE_PROOF_STATUS,
            "testnet_is_not_live_proof": TESTNET_IS_NOT_LIVE_PROOF,
            "zero_correlation_optimistic_fallback_forbidden": (
                ZERO_CORRELATION_OPTIMISTIC_FALLBACK_FORBIDDEN
            ),
        },
        "single_future_authorized_behavior": {
            "authorized": False,
            "effective_active_ids": list(single.effective_active_ids),
            "max_positions_effective": single.max_positions_effective,
            "submit_unlocked": False,
        },
        "source_evidence": source_evidence,
    }
    if any(body["pre_grant_blockers"]["live_proof_derivation"].values()):
        _reject("live_proof_falsely_derived")
    if body["pre_grant_blockers"]["numeric_policy_status"] != "DEFERRED_UNRATIFIED":
        _reject("numeric_policy_not_deferred_unratified")
    preparation_digest = envelope_digest(
        kind="r6_s5_bounded_authorization_preparation_body",
        payload=body,
    )
    identity = build_preparation_identity_v1(preparation_digest=preparation_digest)
    bundle = {
        "body": body,
        "identity": dict(identity),
        "manifest": {
            "content_hash": preparation_digest,
            "experiment_identity_id": identity["experiment_identity_id"],
            "identity_digest": identity["identity_digest"],
            "kind": "r6_s5_bounded_authorization_preparation_manifest_v1",
        },
        "preparation_digest": preparation_digest,
    }
    return MappingProxyType(bundle)
