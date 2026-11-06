"""Fail-closed verifier for R6 S4 multi-future shadow/sim evidence v1."""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.verifier_v1 import (
    evaluate_r6_phase_8_1_policy_precondition_v1,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.verifier_v1 import (
    evaluate_r6_s2_portfolio_risk_contracts_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    S4_AUTHORIZED as S3_S4_AUTHORIZED,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.orchestrator_v1 import (
    default_single_future_request_v1,
    evaluate_phase_82_graph_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.verifier_v1 import (
    evaluate_r6_s3_multi_future_runtime_architecture_v1,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.constants_v1 import (
    ACCOUNT_MUTATION_EFFECT,
    ACTIVATED,
    AUTHORITY_EFFECT,
    CANARY_AUTHORIZED,
    CANARY_EXECUTE,
    CAPABILITY_ID,
    CONTRACT_ID,
    CONTRACT_OWNER,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    CURRENT_EFFECTIVE_RUNTIME_MODE,
    DONE_CRITERION,
    EVIDENCE_IS_NOT_AUTHORIZATION,
    FIXTURE_INSTRUMENT_A,
    FORBIDDEN_IMPORT_ROOTS,
    FUNDING_RUNTIME_ACTIVATED,
    G13_STATUS,
    G13_UNCHANGED,
    LIVE_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MINIMUM_SIM_INSTRUMENT_CONTEXTS,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
    NEGATIVE_CASE_IDS,
    NETWORK_EFFECT,
    NEXT_STAGE_AUTOMATICALLY_AUTHORIZED,
    NO_AUTOMATIC_STAGE_PROGRESSION,
    NO_SILENT_G13_BYPASS,
    ORDER_EFFECT,
    PACKAGE_MARKER,
    PRODUCTIVE_CALLER_EXISTS,
    REMEDIATION_ID,
    REQUIRED_OWNER_RELPATHS,
    S4_AUTHORIZED,
    S4_EVIDENCE_PREPARED,
    S5_AUTHORIZATION_GRANTED,
    SECOND_ACCOUNTING_AUTHORITY_CREATED,
    SECOND_EXECUTION_AUTHORITY_CREATED,
    SELECTED_FUTURE_COUNT,
    SINGLE_SELECTED_FUTURE,
    SOURCE_EVIDENCE_EXTERNAL,
    SOURCE_GAP_IDS,
    STRATEGY_LOGIC_MUTATED,
    SUBMIT_UNLOCKED,
    TARGET_BINDING,
    TESTNET_AUTHORIZED,
    TOP_N_ACTIVE_SET_AUTHORITY,
    TRADING_AUTHORITY_EXPANDED,
    TRADING_GRANT,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.models_v1 import (
    R6S4ShadowSimEvidenceError,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.negative_v1 import (
    run_negative_matrix_v1,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.producer_v1 import (
    produce_shadow_sim_evidence_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1 import (
    constants_v1 as cap72,
)
from src.ops.single_selected_future_policy_v1 import constants_v1 as cap23

_PACKAGE_REL = Path("src") / "ops" / "canonical_r6_s4_multi_future_shadow_sim_evidence_v1"


def _reject(message: str) -> None:
    raise R6S4ShadowSimEvidenceError(message)


def _require(payload: Mapping[str, Any], key: str, expected: Any) -> None:
    actual = payload.get(key)
    if actual != expected:
        _reject(f"config_field_mismatch:{key}:expected={expected!r}:actual={actual!r}")


def _iter_import_names(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return tuple(names)


def validate_layer_config_v1(payload: Mapping[str, Any]) -> None:
    _require(payload, "activated", False)
    _require(payload, "authority_effect", AUTHORITY_EFFECT)
    _require(payload, "canary_authorized", False)
    _require(payload, "capability_id", CAPABILITY_ID)
    _require(payload, "contract_id", CONTRACT_ID)
    _require(payload, "contract_owner", CONTRACT_OWNER)
    _require(payload, "contract_version", CONTRACT_VERSION)
    _require(payload, "core_logic_change", CORE_LOGIC_CHANGE)
    _require(payload, "current_effective_runtime_mode", CURRENT_EFFECTIVE_RUNTIME_MODE)
    _require(payload, "done_criterion", DONE_CRITERION)
    _require(payload, "evidence_is_not_authorization", True)
    _require(payload, "funding_runtime_activated", False)
    _require(payload, "g13_status", G13_STATUS)
    _require(payload, "g13_unchanged", True)
    _require(payload, "live_authorized", False)
    _require(payload, "max_positions_effective", 1)
    _require(payload, "multi_future_runtime_authorized", False)
    _require(payload, "multi_future_runtime_implemented", True)
    _require(payload, "network_effect", NETWORK_EFFECT)
    _require(payload, "next_stage_automatically_authorized", False)
    _require(payload, "no_automatic_stage_progression", True)
    _require(payload, "no_silent_g13_bypass", True)
    _require(payload, "order_effect", ORDER_EFFECT)
    _require(payload, "account_mutation_effect", ACCOUNT_MUTATION_EFFECT)
    _require(payload, "package_marker", PACKAGE_MARKER)
    _require(payload, "productive_caller_exists", False)
    _require(payload, "remediation_id", REMEDIATION_ID)
    _require(payload, "s4_authorized", False)
    _require(payload, "s4_evidence_prepared", True)
    _require(payload, "s5_authorization_granted", False)
    _require(payload, "second_accounting_authority_created", False)
    _require(payload, "second_execution_authority_created", False)
    _require(payload, "selected_future_count", 1)
    _require(payload, "single_selected_future", True)
    _require(payload, "source_gap_ids", list(SOURCE_GAP_IDS))
    _require(payload, "strategy_logic_mutated", False)
    _require(payload, "submit_unlocked", False)
    _require(payload, "target_binding", TARGET_BINDING)
    _require(payload, "testnet_authorized", False)
    _require(payload, "top_n_active_set_authority", False)
    _require(payload, "trading_authority_expanded", False)
    _require(payload, "trading_grant", False)


def assert_package_import_boundary_v1(root: Path | None = None) -> None:
    package = (root or repo_root()) / _PACKAGE_REL
    for path in sorted(package.glob("*.py")):
        for name in _iter_import_names(path):
            for forbidden in FORBIDDEN_IMPORT_ROOTS:
                if name == forbidden or name.startswith(f"{forbidden}."):
                    _reject(f"forbidden_import:{path.name}:{name}")


def assert_required_owners_present_v1(root: Path | None = None) -> None:
    base = root or repo_root()
    for rel in REQUIRED_OWNER_RELPATHS:
        if not (base / rel).is_file():
            _reject(f"owner_file_missing:{rel}")


def evaluate_r6_s4_multi_future_shadow_sim_evidence_v1(
    *,
    root: Path | None = None,
) -> Mapping[str, Any]:
    payload = load_layer_config_v1(root)
    validate_layer_config_v1(payload)
    assert_package_import_boundary_v1(root)
    assert_required_owners_present_v1(root)
    if any(
        (
            ACTIVATED,
            PRODUCTIVE_CALLER_EXISTS,
            TRADING_GRANT,
            LIVE_AUTHORIZED,
            TESTNET_AUTHORIZED,
            CANARY_AUTHORIZED,
            CANARY_EXECUTE,
            SUBMIT_UNLOCKED,
            S4_AUTHORIZED,
            S5_AUTHORIZATION_GRANTED,
            NEXT_STAGE_AUTOMATICALLY_AUTHORIZED,
            MULTI_FUTURE_RUNTIME_AUTHORIZED,
            TOP_N_ACTIVE_SET_AUTHORITY,
            CORE_LOGIC_CHANGE,
            STRATEGY_LOGIC_MUTATED,
            SECOND_EXECUTION_AUTHORITY_CREATED,
            SECOND_ACCOUNTING_AUTHORITY_CREATED,
            TRADING_AUTHORITY_EXPANDED,
            FUNDING_RUNTIME_ACTIVATED,
        )
    ):
        _reject("authority_or_runtime_flag_raised")
    if S3_S4_AUTHORIZED is not False:
        _reject("s3_s4_authorized_true")
    if EVIDENCE_IS_NOT_AUTHORIZATION is not True:
        _reject("evidence_interpreted_as_authorization")
    if S4_EVIDENCE_PREPARED is not True:
        _reject("s4_evidence_prepared_not_true")
    if MULTI_FUTURE_RUNTIME_IMPLEMENTED is not True:
        _reject("implemented_flag_not_true")
    if MAX_POSITIONS_EFFECTIVE != 1 or SELECTED_FUTURE_COUNT != 1:
        _reject("single_future_binding_lost")
    if not (NO_SILENT_G13_BYPASS and NO_AUTOMATIC_STAGE_PROGRESSION and G13_UNCHANGED):
        _reject("g13_doctrine_missing")
    if SINGLE_SELECTED_FUTURE is not True:
        _reject("single_selected_future_lost")
    s1 = evaluate_r6_phase_8_1_policy_precondition_v1()
    s2 = evaluate_r6_s2_portfolio_risk_contracts_v1()
    s3 = evaluate_r6_s3_multi_future_runtime_architecture_v1()
    if s1["verdict"] != "PASS_R6_PHASE_8_1_POLICY_PRECONDITION_V1":
        _reject("s1_not_pass")
    if s2["verdict"] != "PASS_R6_S2_PORTFOLIO_RISK_CONTRACTS_V1":
        _reject("s2_not_pass")
    if s3["verdict"] != "PASS_R6_S3_MULTI_FUTURE_RUNTIME_ARCHITECTURE_V1":
        _reject("s3_not_pass")
    if s3["multi_future_runtime_authorized"] is not False:
        _reject("s3_authorized_true")
    single = evaluate_phase_82_graph_v1(default_single_future_request_v1("BTC-USDT-SWAP"))
    if single.effective_active_ids != ("BTC-USDT-SWAP",):
        _reject("single_future_active_set_drift")
    if single.max_positions_effective != 1:
        _reject("single_future_max_positions_drift")
    if cap23.MAX_POSITIONS_EFFECTIVE != 1:
        _reject("cap23_max_positions_drift")
    if cap23.MULTI_FUTURE_RUNTIME_AUTHORIZED is True:
        _reject("cap23_authorized_true")
    if getattr(cap72, "MULTI_FUTURE_RUNTIME_IMPLEMENTED", False) is True:
        _reject("cap72_multi_future_runtime_implemented_true")
    evidence = produce_shadow_sim_evidence_v1()
    body = evidence["body"]
    if len(body["instrument_contexts"]) < MINIMUM_SIM_INSTRUMENT_CONTEXTS:
        _reject("sim_instrument_context_count")
    if body["active_set"]["effective_active_ids"] != [FIXTURE_INSTRUMENT_A]:
        _reject("effective_active_not_singleton")
    if len(body["active_set"]["effective_active_ids"]) != 1:
        _reject("authorized_runtime_active_count_not_1")
    if body["authority"]["s4_authorized"] is not False:
        _reject("evidence_claimed_s4_authorization")
    if body["simulated_execution"]["order_effect"] != "NONE":
        _reject("order_effect_not_none")
    if body["simulated_execution"]["account_mutation_effect"] != "NONE":
        _reject("account_mutation_effect_not_none")
    if body["source_evidence"]["external"]["status"] != SOURCE_EVIDENCE_EXTERNAL:
        _reject("external_source_evidence_not_explicit")
    negatives = run_negative_matrix_v1()
    if tuple(negatives) != NEGATIVE_CASE_IDS:
        _reject("negative_matrix_incomplete")
    claims = {
        "account_mutation_effect": ACCOUNT_MUTATION_EFFECT,
        "activated": ACTIVATED,
        "authority_effect": AUTHORITY_EFFECT,
        "canary_authorized": CANARY_AUTHORIZED,
        "capability_id": CAPABILITY_ID,
        "config_digest": digest_mapping(payload),
        "core_logic_change": CORE_LOGIC_CHANGE,
        "current_effective_runtime_mode": CURRENT_EFFECTIVE_RUNTIME_MODE,
        "deterministic_arbitration_evidence": True,
        "done_criterion": DONE_CRITERION,
        "duplicate_accounting_writer_found": False,
        "duplicate_execution_writer_found": False,
        "evidence_digest": evidence["evidence_digest"],
        "evidence_is_not_authorization": True,
        "experiment_identity_id": evidence["identity"]["experiment_identity_id"],
        "fail_closed_negative_evidence": True,
        "fail_closed_negative_case_ids": list(NEGATIVE_CASE_IDS),
        "funding_runtime_activated": FUNDING_RUNTIME_ACTIVATED,
        "g13_status": G13_STATUS,
        "g13_unchanged": G13_UNCHANGED,
        "live_authorized": LIVE_AUTHORIZED,
        "manifest_digest": evidence["manifest"]["content_hash"],
        "max_positions_effective": MAX_POSITIONS_EFFECTIVE,
        "multi_future_runtime_authorized": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "multi_future_runtime_implemented": MULTI_FUTURE_RUNTIME_IMPLEMENTED,
        "multi_instrument_sim_evidence": True,
        "network_effect": NETWORK_EFFECT,
        "next_stage_automatically_authorized": NEXT_STAGE_AUTOMATICALLY_AUTHORIZED,
        "order_effect": ORDER_EFFECT,
        "package_marker": PACKAGE_MARKER,
        "per_instrument_recon_evidence": True,
        "portfolio_risk_evidence": True,
        "r6_s1_status": "CLOSED_PROVEN_FORENSIC_READ_ONLY",
        "r6_s2_status": "CLOSED_PROVEN_FORENSIC_READ_ONLY",
        "r6_s3_status": "PERSISTED_ON_MAIN_IMPLEMENTED_UNAUTHORIZED",
        "r6_s4_status": "PREPARED",
        "remediation_id": REMEDIATION_ID,
        "restart_recovery_evidence": True,
        "s4_authorized": S4_AUTHORIZED,
        "s4_evidence_prepared": S4_EVIDENCE_PREPARED,
        "s5_authorization_granted": S5_AUTHORIZATION_GRANTED,
        "second_accounting_authority_created": SECOND_ACCOUNTING_AUTHORITY_CREATED,
        "second_execution_authority_created": SECOND_EXECUTION_AUTHORITY_CREATED,
        "selected_future_count": SELECTED_FUTURE_COUNT,
        "single_future_authorized_behavior_unchanged": True,
        "single_global_accounting_writer_proven": True,
        "single_global_execution_writer_proven": True,
        "single_selected_future": SINGLE_SELECTED_FUTURE,
        "source_evidence_external": SOURCE_EVIDENCE_EXTERNAL,
        "state_isolation_evidence": True,
        "submit_unlocked": SUBMIT_UNLOCKED,
        "target_binding": TARGET_BINDING,
        "testnet_authorized": TESTNET_AUTHORIZED,
        "top_n_active_set_authority": TOP_N_ACTIVE_SET_AUTHORITY,
        "trading_authority_expanded": TRADING_AUTHORITY_EXPANDED,
        "trading_grant": TRADING_GRANT,
        "verdict": "PASS_R6_S4_MULTI_FUTURE_SHADOW_SIM_EVIDENCE_V1",
    }
    return MappingProxyType(claims)
