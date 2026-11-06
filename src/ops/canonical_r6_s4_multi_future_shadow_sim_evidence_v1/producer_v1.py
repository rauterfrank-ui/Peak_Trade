"""Deterministic R6 S4 shadow/sim evidence producer.

Reuses the unauthorized S3 Phase-8.2 graph. Observes the single writer
boundary without submit, account mutation, or network/order effects.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.lineage_v1 import (
    load_layer_config_v1 as load_s1_config_v1,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.constants_v1 import (
    CONCENTRATION_PERCENTAGE_RATIFIED,
    CORRELATION_THRESHOLD_RATIFIED,
    NAN_CORRELATION_SKIP_AS_AUTHORITY_FORBIDDEN,
    NUMERIC_POLICY_STATUS,
    ZERO_CORRELATION_OPTIMISTIC_FALLBACK_FORBIDDEN,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.lineage_v1 import (
    load_layer_config_v1 as load_s2_config_v1,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.verifier_v1 import (
    evaluate_r6_s2_portfolio_risk_contracts_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.arbitration_v1 import (
    arbitrate_intents_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.instrument_context_v1 import (
    isolate_instrument_contexts_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.lineage_v1 import (
    load_layer_config_v1 as load_s3_config_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    InstrumentContextV1,
    Phase82GraphRequestV1,
    RankingCandidateV1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.orchestrator_v1 import (
    evaluate_phase_82_graph_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.restart_v1 import (
    reconstruct_contexts_v1,
    snapshot_contexts_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.verifier_v1 import (
    evaluate_r6_s3_multi_future_runtime_architecture_v1,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.constants_v1 import (
    ACCOUNT_MUTATION_EFFECT,
    CANARY_AUTHORIZED,
    CURRENT_EFFECTIVE_RUNTIME_MODE,
    EVIDENCE_CANNOT_CREATE_RUNTIME_AUTHORITY,
    EVIDENCE_IS_NOT_AUTHORIZATION,
    EXCHANGE_SUBMIT_ATTEMPTED,
    FILLS_COMMITTED,
    FIXTURE_INSTRUMENT_A,
    FIXTURE_INSTRUMENT_B,
    FIXTURE_SEED,
    FUNDING_RUNTIME_ACTIVATED,
    G13_UNCHANGED,
    LIVE_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MINIMUM_SIM_INSTRUMENT_CONTEXTS,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    NETWORK_EFFECT,
    ORDER_EFFECT,
    SIMULATED_EXECUTION_MODE,
    SOURCE_EVIDENCE_EXTERNAL,
    SOURCE_EVIDENCE_S1,
    SOURCE_EVIDENCE_S2,
    SOURCE_EVIDENCE_S3,
    TESTNET_AUTHORIZED,
    TESTNET_SUBMIT_ATTEMPTED,
    TOP_N_ACTIVE_SET_AUTHORITY,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.identity_v1 import (
    build_evidence_identity_v1,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.lineage_v1 import (
    digest_mapping,
    envelope_digest,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.models_v1 import (
    R6S4ShadowSimEvidenceError,
)


def _reject(message: str) -> None:
    raise R6S4ShadowSimEvidenceError(message)


def fixture_contexts_v1() -> tuple[InstrumentContextV1, InstrumentContextV1]:
    return (
        InstrumentContextV1(
            instrument_id=FIXTURE_INSTRUMENT_A,
            directional_side="FLAT",
            intended_action="ENTRY",
            intended_side="LONG",
            intended_qty="4",
            reconciliation_status="RECONCILED",
            single_use_permission=True,
            isolated_state={"marker": FIXTURE_INSTRUMENT_A, "seed": str(FIXTURE_SEED)},
        ),
        InstrumentContextV1(
            instrument_id=FIXTURE_INSTRUMENT_B,
            directional_side="FLAT",
            intended_action="ENTRY",
            intended_side="LONG",
            intended_qty="4",
            reconciliation_status="RECONCILED",
            single_use_permission=True,
            isolated_state={"marker": FIXTURE_INSTRUMENT_B, "seed": str(FIXTURE_SEED)},
        ),
    )


def fixture_request_v1(
    contexts: tuple[InstrumentContextV1, ...] | None = None,
) -> Phase82GraphRequestV1:
    rows = contexts or fixture_contexts_v1()
    return Phase82GraphRequestV1(
        selected_future_id=FIXTURE_INSTRUMENT_A,
        ranking_candidates=(
            RankingCandidateV1(FIXTURE_INSTRUMENT_A, 1),
            RankingCandidateV1(FIXTURE_INSTRUMENT_B, 2),
        ),
        instrument_contexts=rows,
        economic_evidence_pass=True,
        research_signal_pass=True,
    )


def observe_simulated_execution_v1(result: Any) -> Mapping[str, Any]:
    bundle = result.writer_bundle
    if bundle.submit_unlocked is True or result.submit_unlocked is True:
        _reject("submit_unlocked_in_shadow_sim_evidence")
    if EXCHANGE_SUBMIT_ATTEMPTED is True or TESTNET_SUBMIT_ATTEMPTED is True:
        _reject("exchange_or_testnet_submit_flag_raised")
    if FILLS_COMMITTED is True:
        _reject("fills_committed_must_remain_false")
    return MappingProxyType(
        {
            "account_mutation_effect": ACCOUNT_MUTATION_EFFECT,
            "exchange_submit_attempted": False,
            "execution_mode": SIMULATED_EXECUTION_MODE,
            "execution_writer_identity": bundle.execution_writer_identity,
            "accounting_writer_identity": bundle.accounting_writer_identity,
            "execution_writer_count": 1,
            "accounting_writer_count": 1,
            "fills_committed": False,
            "intents_observed": [intent.to_mapping() for intent in bundle.intents],
            "network_effect": NETWORK_EFFECT,
            "order_effect": ORDER_EFFECT,
            "submit_unlocked": False,
            "testnet_submit_attempted": False,
        }
    )


def produce_shadow_sim_evidence_v1() -> Mapping[str, Any]:
    if EVIDENCE_IS_NOT_AUTHORIZATION is not True:
        _reject("evidence_is_not_authorization_doctrine_missing")
    if EVIDENCE_CANNOT_CREATE_RUNTIME_AUTHORITY is not True:
        _reject("evidence_cannot_create_runtime_authority_doctrine_missing")
    if ZERO_CORRELATION_OPTIMISTIC_FALLBACK_FORBIDDEN is not True:
        _reject("zero_corr_fallback_must_remain_forbidden")
    if NAN_CORRELATION_SKIP_AS_AUTHORITY_FORBIDDEN is not True:
        _reject("nan_corr_skip_must_remain_forbidden")
    contexts = fixture_contexts_v1()
    if len(contexts) < MINIMUM_SIM_INSTRUMENT_CONTEXTS:
        _reject("minimum_sim_instrument_contexts_not_met")
    isolated = isolate_instrument_contexts_v1(contexts)
    if (
        isolated[FIXTURE_INSTRUMENT_A].isolated_state["marker"]
        == isolated[FIXTURE_INSTRUMENT_B].isolated_state["marker"]
    ):
        _reject("instrument_context_identity_not_distinct")
    request = fixture_request_v1(contexts)
    result = evaluate_phase_82_graph_v1(request, portfolio_reduce_entry_qty_to="1")
    if result.authorized is not False:
        _reject("s3_graph_authorized_true")
    if result.effective_runtime_mode != CURRENT_EFFECTIVE_RUNTIME_MODE:
        _reject("effective_runtime_mode_drift")
    if result.max_positions_effective != MAX_POSITIONS_EFFECTIVE:
        _reject("max_positions_effective_drift")
    if result.effective_active_ids != (FIXTURE_INSTRUMENT_A,):
        _reject("top_n_or_active_set_authority_leaked")
    if TOP_N_ACTIVE_SET_AUTHORITY is True:
        _reject("top_n_active_set_authority_must_remain_false")
    first_arbitration = [row.to_mapping() for row in arbitrate_intents_v1(result.safety_intents)]
    second_arbitration = [
        row.to_mapping() for row in arbitrate_intents_v1(tuple(reversed(result.safety_intents)))
    ]
    if first_arbitration != second_arbitration:
        _reject("arbitration_not_deterministic")
    snapshot = dict(snapshot_contexts_v1(contexts))
    reconstructed = reconstruct_contexts_v1(snapshot, authorized_after_restart=False)
    restart_ids = tuple(row.instrument_id for row in reconstructed)
    live_ids = tuple(sorted(context.instrument_id for context in contexts))
    if restart_ids != live_ids:
        _reject("restart_instrument_set_mismatch")
    restarted = evaluate_phase_82_graph_v1(
        Phase82GraphRequestV1(
            selected_future_id=FIXTURE_INSTRUMENT_A,
            ranking_candidates=request.ranking_candidates,
            instrument_contexts=contexts,
            restart_snapshot=snapshot,
            economic_evidence_pass=True,
            research_signal_pass=True,
        ),
        portfolio_reduce_entry_qty_to="1",
    )
    if tuple(sorted(restarted.isolated_contexts)) != live_ids:
        _reject("restart_recovery_identity_mismatch")
    if restarted.authorized is not False:
        _reject("restart_created_authorization")
    s2 = evaluate_r6_s2_portfolio_risk_contracts_v1()
    s3 = evaluate_r6_s3_multi_future_runtime_architecture_v1()
    if s2["verdict"] != "PASS_R6_S2_PORTFOLIO_RISK_CONTRACTS_V1":
        _reject("s2_contract_not_pass")
    if s3["verdict"] != "PASS_R6_S3_MULTI_FUTURE_RUNTIME_ARCHITECTURE_V1":
        _reject("s3_contract_not_pass")
    if s3["s4_authorized"] is not False:
        _reject("s3_s4_authorized_true")
    if s3["multi_future_runtime_authorized"] is not False:
        _reject("s3_authorized_true")
    simulated = observe_simulated_execution_v1(result)
    portfolio_intents = [intent.to_mapping() for intent in result.portfolio_intents]
    if not any("PORTFOLIO_RISK_REDUCED" in row["block_reasons"] for row in portfolio_intents):
        _reject("portfolio_risk_restriction_not_observed")
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
        "external": {"digest": None, "status": SOURCE_EVIDENCE_EXTERNAL},
    }
    body = {
        "active_set": {
            "candidate_ids": list(result.candidate_ids),
            "effective_active_ids": list(result.effective_active_ids),
            "max_positions_effective": result.max_positions_effective,
            "top_n_active_set_authority": False,
        },
        "arbitration": {
            "identical_input_identical_order": True,
            "ordered_instrument_ids": [row["instrument_id"] for row in first_arbitration],
        },
        "authority": {
            "canary_authorized": CANARY_AUTHORIZED,
            "current_effective_runtime_mode": CURRENT_EFFECTIVE_RUNTIME_MODE,
            "evidence_is_not_authorization": True,
            "funding_runtime_activated": FUNDING_RUNTIME_ACTIVATED,
            "g13_unchanged": G13_UNCHANGED,
            "live_authorized": LIVE_AUTHORIZED,
            "max_positions_effective": MAX_POSITIONS_EFFECTIVE,
            "multi_future_runtime_authorized": MULTI_FUTURE_RUNTIME_AUTHORIZED,
            "s4_authorized": False,
            "second_accounting_authority_created": False,
            "second_execution_authority_created": False,
            "testnet_authorized": TESTNET_AUTHORIZED,
        },
        "fixture_seed": FIXTURE_SEED,
        "instrument_contexts": {key: dict(value.to_mapping()) for key, value in isolated.items()},
        "portfolio_risk": {
            "concentration_percentage_ratified": CONCENTRATION_PERCENTAGE_RATIFIED,
            "correlation_threshold_ratified": CORRELATION_THRESHOLD_RATIFIED,
            "effective_active_count": len(result.effective_active_ids),
            "nan_correlation_skip_as_authority_forbidden": (
                NAN_CORRELATION_SKIP_AS_AUTHORITY_FORBIDDEN
            ),
            "numeric_policy_status": NUMERIC_POLICY_STATUS,
            "s2_consumed": True,
            "s2_verdict": s2["verdict"],
            "second_risk_engine_created": False,
            "sim_instrument_context_count": len(isolated),
            "zero_correlation_optimistic_fallback_forbidden": (
                ZERO_CORRELATION_OPTIMISTIC_FALLBACK_FORBIDDEN
            ),
        },
        "reconciliation": {
            "global_instrument_ids": live_ids,
            "per_instrument": {
                key: value["reconciliation_status"]
                for key, value in result.isolated_contexts.items()
            },
        },
        "restart": {
            "authorized_after_restart": False,
            "reconstructed_ids": list(restart_ids),
            "snapshot_ids": list(live_ids),
        },
        "simulated_execution": dict(simulated),
        "source_evidence": source_evidence,
        "state_isolation": {
            FIXTURE_INSTRUMENT_A: isolated[FIXTURE_INSTRUMENT_A].isolated_state["marker"],
            FIXTURE_INSTRUMENT_B: isolated[FIXTURE_INSTRUMENT_B].isolated_state["marker"],
        },
    }
    evidence_digest = envelope_digest(kind="r6_s4_shadow_sim_body", payload=body)
    identity = build_evidence_identity_v1(evidence_digest=evidence_digest)
    bundle = {
        "body": body,
        "evidence_digest": evidence_digest,
        "identity": dict(identity),
        "manifest": {
            "content_hash": evidence_digest,
            "experiment_identity_id": identity["experiment_identity_id"],
            "identity_digest": identity["identity_digest"],
            "kind": "r6_s4_shadow_sim_evidence_manifest_v1",
        },
    }
    return MappingProxyType(bundle)
