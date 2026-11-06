"""Fail-closed verifier for R6 S5 bounded-authorization preparation v1."""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    S5_AUTHORIZATION_GRANTED as S3_S5_AUTHORIZATION_GRANTED,
    SINGLE_GLOBAL_ACCOUNTING_WRITER,
    SINGLE_GLOBAL_EXECUTION_WRITER,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.orchestrator_v1 import (
    default_single_future_request_v1,
    evaluate_phase_82_graph_v1,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.constants_v1 import (
    ACCOUNT_MUTATION_EFFECT,
    ACTIVATED,
    AUTHORITY_EFFECT,
    BOUNDED_AUTO_PROMOTION,
    CANARY_AUTHORIZED,
    CANARY_EXECUTE,
    CAPABILITY_ID,
    COMPONENT_VAR_LIMIT_RATIFIED,
    CONCENTRATION_PERCENTAGE_RATIFIED,
    CONTRACT_ID,
    CONTRACT_OWNER,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    CORRELATION_THRESHOLD_RATIFIED,
    CURRENT_EFFECTIVE_RUNTIME_MODE,
    DONE_CRITERION,
    EVIDENCE_IS_NOT_AUTHORIZATION,
    FORBIDDEN_IMPORT_ROOTS,
    FUNDING_RUNTIME_ACTIVATED,
    G13_STATUS,
    G13_UNCHANGED,
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
    NEGATIVE_CASE_IDS,
    NETWORK_EFFECT,
    NEXT_STAGE_AUTOMATICALLY_AUTHORIZED,
    NO_AUTOMATIC_S5_TO_S6_PROGRESSION,
    NO_AUTOMATIC_STAGE_PROGRESSION,
    NO_SILENT_G13_BYPASS,
    NUMERIC_POLICY_STATUS,
    ORDER_EFFECT,
    PACKAGE_MARKER,
    PER_INSTRUMENT_CAPITAL_BUDGET_RATIFIED,
    PORTFOLIO_VAR_LIMIT_RATIFIED,
    PREPARATION_IS_NOT_AUTHORIZATION,
    PRODUCTIVE_CALLER_EXISTS,
    PRODUCTIVE_MF_CALLER_AUTHORIZED,
    REMEDIATION_ID,
    REQUIRED_OWNER_RELPATHS,
    S4_AUTHORIZED,
    S4_SIM_EVIDENCE_IS_NOT_LIVE_PROOF,
    S5_AUTHORIZATION_GRANTED,
    S5_PREPARED,
    S6_AUTONOMOUS_GRANTED,
    SECOND_ACCOUNTING_AUTHORITY_CREATED,
    SECOND_DECISION_AUTHORITY_CREATED,
    SECOND_EXECUTION_AUTHORITY_CREATED,
    SELECTED_FUTURE_COUNT,
    SHADOW_IS_NOT_LIVE_PROOF,
    SINGLE_FUTURE_DEFAULTS_ARE_NOT_MF_NUMERICS,
    SINGLE_FUTURE_LIVE_PROOF,
    SINGLE_FUTURE_LIVE_PROOF_REQUIRED_BEFORE_S5_AUTHORIZATION_GRANT,
    SINGLE_FUTURE_LIVE_PROOF_STATUS,
    SINGLE_SELECTED_FUTURE,
    SOURCE_GAP_IDS,
    STRATEGY_LOGIC_MUTATED,
    SUBMIT_UNLOCKED,
    TARGET_BINDING,
    TESTNET_AUTHORIZED,
    TESTNET_IS_NOT_LIVE_PROOF,
    TOP_N_ACTIVE_SET_AUTHORITY,
    TRADING_AUTHORITY_EXPANDED,
    TRADING_GRANT,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.gates_v1 import (
    future_owner_gates_v1,
    reject_if_any_gate_granted_v1,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.models_v1 import (
    R6S5BoundedAuthorizationPreparationError,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.producer_v1 import (
    produce_bounded_authorization_preparation_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1 import (
    constants_v1 as cap72,
)
from src.ops.single_selected_future_policy_v1 import constants_v1 as cap23

_PACKAGE_REL = Path("src") / "ops" / "canonical_r6_s5_bounded_authorization_preparation_v1"


def _reject(message: str) -> None:
    raise R6S5BoundedAuthorizationPreparationError(message)


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
    _require(payload, "component_var_limit_ratified", False)
    _require(payload, "concentration_percentage_ratified", False)
    _require(payload, "contract_id", CONTRACT_ID)
    _require(payload, "contract_owner", CONTRACT_OWNER)
    _require(payload, "contract_version", CONTRACT_VERSION)
    _require(payload, "core_logic_change", CORE_LOGIC_CHANGE)
    _require(payload, "correlation_threshold_ratified", False)
    _require(payload, "current_effective_runtime_mode", CURRENT_EFFECTIVE_RUNTIME_MODE)
    _require(payload, "done_criterion", DONE_CRITERION)
    _require(payload, "evidence_is_not_authorization", True)
    _require(payload, "funding_runtime_activated", False)
    _require(payload, "g13_status", G13_STATUS)
    _require(payload, "g13_unchanged", True)
    _require(payload, "gross_net_exposure_limit_ratified", False)
    _require(payload, "i17_is_not_live_proof", True)
    _require(payload, "live_authorized", False)
    _require(payload, "live_canary_proof_required", True)
    _require(payload, "live_order_economic_proof_required", True)
    _require(payload, "max_positions_effective", 1)
    _require(payload, "mf_cooldown_policy_ratified", False)
    _require(payload, "mf_open_position_treatment_ratified", False)
    _require(payload, "mf_rotation_hysteresis_policy_ratified", False)
    _require(payload, "multi_future_runtime_authorized", False)
    _require(payload, "multi_future_runtime_implemented", True)
    _require(payload, "n_greater_than_one_ratified", False)
    _require(payload, "network_effect", NETWORK_EFFECT)
    _require(payload, "next_stage_automatically_authorized", False)
    _require(payload, "no_automatic_s5_to_s6_progression", True)
    _require(payload, "no_automatic_stage_progression", True)
    _require(payload, "no_silent_g13_bypass", True)
    _require(payload, "numeric_policy_status", "DEFERRED_UNRATIFIED")
    _require(payload, "order_effect", ORDER_EFFECT)
    _require(payload, "account_mutation_effect", ACCOUNT_MUTATION_EFFECT)
    _require(payload, "package_marker", PACKAGE_MARKER)
    _require(payload, "per_instrument_capital_budget_ratified", False)
    _require(payload, "portfolio_var_limit_ratified", False)
    _require(payload, "preparation_is_not_authorization", True)
    _require(payload, "productive_caller_exists", False)
    _require(payload, "productive_mf_caller_authorized", False)
    _require(payload, "remediation_id", REMEDIATION_ID)
    _require(payload, "s4_authorized", False)
    _require(payload, "s4_sim_evidence_is_not_live_proof", True)
    _require(payload, "s5_authorization_granted", False)
    _require(payload, "s5_prepared", True)
    _require(payload, "s6_autonomous_granted", False)
    _require(payload, "second_accounting_authority_created", False)
    _require(payload, "second_decision_authority_created", False)
    _require(payload, "second_execution_authority_created", False)
    _require(payload, "selected_future_count", 1)
    _require(payload, "shadow_is_not_live_proof", True)
    _require(payload, "single_future_defaults_are_not_mf_numerics", True)
    _require(payload, "single_future_live_proof", False)
    _require(
        payload,
        "single_future_live_proof_required_before_s5_authorization_grant",
        True,
    )
    _require(payload, "single_selected_future", True)
    _require(payload, "source_gap_ids", list(SOURCE_GAP_IDS))
    _require(payload, "strategy_logic_mutated", False)
    _require(payload, "submit_unlocked", False)
    _require(payload, "target_binding", TARGET_BINDING)
    _require(payload, "testnet_authorized", False)
    _require(payload, "testnet_is_not_live_proof", True)
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


def evaluate_r6_s5_bounded_authorization_preparation_v1(
    *,
    root: Path | None = None,
) -> Mapping[str, Any]:
    from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.negative_v1 import (
        run_negative_matrix_v1,
    )

    payload = load_layer_config_v1(root)
    validate_layer_config_v1(payload)
    assert_package_import_boundary_v1(root)
    assert_required_owners_present_v1(root)
    if any(
        (
            ACTIVATED,
            PRODUCTIVE_CALLER_EXISTS,
            PRODUCTIVE_MF_CALLER_AUTHORIZED,
            TRADING_GRANT,
            LIVE_AUTHORIZED,
            TESTNET_AUTHORIZED,
            CANARY_AUTHORIZED,
            CANARY_EXECUTE,
            SUBMIT_UNLOCKED,
            S4_AUTHORIZED,
            S5_AUTHORIZATION_GRANTED,
            S6_AUTONOMOUS_GRANTED,
            NEXT_STAGE_AUTOMATICALLY_AUTHORIZED,
            MULTI_FUTURE_RUNTIME_AUTHORIZED,
            N_GREATER_THAN_ONE_RATIFIED,
            TOP_N_ACTIVE_SET_AUTHORITY,
            CORE_LOGIC_CHANGE,
            STRATEGY_LOGIC_MUTATED,
            SECOND_EXECUTION_AUTHORITY_CREATED,
            SECOND_ACCOUNTING_AUTHORITY_CREATED,
            SECOND_DECISION_AUTHORITY_CREATED,
            TRADING_AUTHORITY_EXPANDED,
            FUNDING_RUNTIME_ACTIVATED,
            BOUNDED_AUTO_PROMOTION,
            SINGLE_FUTURE_LIVE_PROOF,
            CONCENTRATION_PERCENTAGE_RATIFIED,
            CORRELATION_THRESHOLD_RATIFIED,
            PORTFOLIO_VAR_LIMIT_RATIFIED,
            COMPONENT_VAR_LIMIT_RATIFIED,
            PER_INSTRUMENT_CAPITAL_BUDGET_RATIFIED,
            GROSS_NET_EXPOSURE_LIMIT_RATIFIED,
            MF_ROTATION_HYSTERESIS_POLICY_RATIFIED,
            MF_COOLDOWN_POLICY_RATIFIED,
            MF_OPEN_POSITION_TREATMENT_RATIFIED,
        )
    ):
        _reject("authority_or_runtime_flag_raised")
    if S3_S5_AUTHORIZATION_GRANTED is not False:
        _reject("s3_s5_authorization_granted_true")
    if PREPARATION_IS_NOT_AUTHORIZATION is not True:
        _reject("preparation_interpreted_as_authorization")
    if EVIDENCE_IS_NOT_AUTHORIZATION is not True:
        _reject("evidence_interpreted_as_authorization")
    if S5_PREPARED is not True:
        _reject("s5_prepared_not_true")
    if MULTI_FUTURE_RUNTIME_IMPLEMENTED is not True:
        _reject("implemented_flag_not_true")
    if MAX_POSITIONS_EFFECTIVE != 1 or SELECTED_FUTURE_COUNT != 1:
        _reject("single_future_binding_lost")
    if not (
        NO_SILENT_G13_BYPASS
        and NO_AUTOMATIC_STAGE_PROGRESSION
        and NO_AUTOMATIC_S5_TO_S6_PROGRESSION
        and G13_UNCHANGED
    ):
        _reject("g13_doctrine_missing")
    if SINGLE_SELECTED_FUTURE is not True:
        _reject("single_selected_future_lost")
    if NUMERIC_POLICY_STATUS != "DEFERRED_UNRATIFIED":
        _reject("numeric_policy_treated_resolved")
    if SINGLE_FUTURE_DEFAULTS_ARE_NOT_MF_NUMERICS is not True:
        _reject("single_future_defaults_promoted_to_mf_numerics")
    if not (
        SHADOW_IS_NOT_LIVE_PROOF
        and TESTNET_IS_NOT_LIVE_PROOF
        and I17_IS_NOT_LIVE_PROOF
        and S4_SIM_EVIDENCE_IS_NOT_LIVE_PROOF
        and SINGLE_FUTURE_LIVE_PROOF_REQUIRED_BEFORE_S5_AUTHORIZATION_GRANT
        and LIVE_CANARY_PROOF_REQUIRED
        and LIVE_ORDER_ECONOMIC_PROOF_REQUIRED
    ):
        _reject("live_proof_doctrine_missing")
    if SINGLE_GLOBAL_EXECUTION_WRITER is not True:
        _reject("single_global_execution_writer_missing")
    if SINGLE_GLOBAL_ACCOUNTING_WRITER is not True:
        _reject("single_global_accounting_writer_missing")
    gates = future_owner_gates_v1()
    reject_if_any_gate_granted_v1(gates)
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
    envelope = produce_bounded_authorization_preparation_v1()
    body = envelope["body"]
    if body["authority_separation"]["s5_authorization_granted"] is not False:
        _reject("envelope_claimed_s5_authorization")
    if body["authority_separation"]["preparation_is_not_authorization"] is not True:
        _reject("envelope_missing_preparation_doctrine")
    if any(body["pre_grant_blockers"]["live_proof_derivation"].values()):
        _reject("live_proof_falsely_derived")
    if body["pre_grant_blockers"]["numeric_policy_status"] != "DEFERRED_UNRATIFIED":
        _reject("envelope_numeric_policy_resolved")
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
        "done_criterion": DONE_CRITERION,
        "evidence_is_not_authorization": True,
        "fail_closed_negative_case_ids": list(NEGATIVE_CASE_IDS),
        "fail_closed_negative_evidence": True,
        "funding_runtime_activated": FUNDING_RUNTIME_ACTIVATED,
        "future_owner_gates": dict(gates),
        "g13_status": G13_STATUS,
        "g13_unchanged": G13_UNCHANGED,
        "live_authorized": LIVE_AUTHORIZED,
        "live_canary_proof_required": LIVE_CANARY_PROOF_REQUIRED,
        "live_order_economic_proof_required": LIVE_ORDER_ECONOMIC_PROOF_REQUIRED,
        "manifest_digest": envelope["manifest"]["content_hash"],
        "max_positions_effective": MAX_POSITIONS_EFFECTIVE,
        "multi_future_runtime_authorized": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "multi_future_runtime_implemented": MULTI_FUTURE_RUNTIME_IMPLEMENTED,
        "n_greater_than_one_ratified": N_GREATER_THAN_ONE_RATIFIED,
        "network_effect": NETWORK_EFFECT,
        "next_stage_automatically_authorized": NEXT_STAGE_AUTOMATICALLY_AUTHORIZED,
        "numeric_policy_status": NUMERIC_POLICY_STATUS,
        "order_effect": ORDER_EFFECT,
        "package_marker": PACKAGE_MARKER,
        "preparation_digest": envelope["preparation_digest"],
        "preparation_is_not_authorization": True,
        "productive_mf_caller_authorized": PRODUCTIVE_MF_CALLER_AUTHORIZED,
        "r6_s1_status": "CLOSED_PROVEN_FORENSIC_READ_ONLY",
        "r6_s2_status": "CLOSED_PROVEN_FORENSIC_READ_ONLY",
        "r6_s3_status": "PERSISTED_ON_MAIN_IMPLEMENTED_UNAUTHORIZED",
        "r6_s4_status": "CLOSED_PROVEN_PERSISTED_UNAUTHORIZED",
        "r6_s5_status": "PREPARED_UNAUTHORIZED",
        "remediation_id": REMEDIATION_ID,
        "s5_authorization_granted": S5_AUTHORIZATION_GRANTED,
        "s5_prepared": S5_PREPARED,
        "s6_autonomous_granted": S6_AUTONOMOUS_GRANTED,
        "second_accounting_authority_created": SECOND_ACCOUNTING_AUTHORITY_CREATED,
        "second_decision_authority_created": SECOND_DECISION_AUTHORITY_CREATED,
        "second_execution_authority_created": SECOND_EXECUTION_AUTHORITY_CREATED,
        "selected_future_count": SELECTED_FUTURE_COUNT,
        "single_future_authorized_behavior_unchanged": True,
        "single_future_live_proof": SINGLE_FUTURE_LIVE_PROOF,
        "single_future_live_proof_required_before_s5_authorization_grant": True,
        "single_future_live_proof_status": SINGLE_FUTURE_LIVE_PROOF_STATUS,
        "single_global_accounting_writer_proven": True,
        "single_global_execution_writer_proven": True,
        "single_selected_future": SINGLE_SELECTED_FUTURE,
        "submit_unlocked": SUBMIT_UNLOCKED,
        "target_binding": TARGET_BINDING,
        "testnet_authorized": TESTNET_AUTHORIZED,
        "top_n_active_set_authority": TOP_N_ACTIVE_SET_AUTHORITY,
        "trading_authority_expanded": TRADING_AUTHORITY_EXPANDED,
        "trading_grant": TRADING_GRANT,
        "verdict": "PASS_R6_S5_BOUNDED_AUTHORIZATION_PREPARATION_V1",
    }
    return MappingProxyType(claims)
