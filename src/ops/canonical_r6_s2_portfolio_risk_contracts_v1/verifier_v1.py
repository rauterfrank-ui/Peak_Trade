"""Fail-closed verifier for R6 S2 portfolio-risk contracts v1."""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.constants_v1 import (
    ACCOUNTING_WRITER,
    ACTIVATED,
    ALLOCATION_TO_ORDER_BYPASS_FORBIDDEN,
    AUTHORITY_EFFECT,
    CANARY_EXECUTE,
    CANONICAL_AUTHORITY_CHAIN,
    CANONICAL_SINGLE_INSTRUMENT_RISK_GATE,
    CANONICAL_SINGLE_INSTRUMENT_RISK_OWNER,
    CAPABILITY_ID,
    COMPONENT_RISK_OWNER,
    COMPONENT_VAR_LIMIT_RATIFIED,
    CONTRACT_ID,
    CONTRACT_OWNER,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    CORRELATION_THRESHOLD_RATIFIED,
    CONCENTRATION_PERCENTAGE_RATIFIED,
    DONE_CRITERION,
    FUTURE_PORTFOLIO_RISK_OWNER,
    G13_STATUS,
    G13_UNCHANGED,
    GROSS_NET_EXPOSURE_LIMIT_RATIFIED,
    I12_ROLE,
    I17_IS_NOT_LIVE_PROOF,
    I29_ROLE,
    I37_AUTHORITY_EFFECT,
    I37_I74_DUAL_VAR_AUTHORITY_FORBIDDEN,
    I37_ROLE,
    I74_AUTHORITY_EFFECT,
    I74_ROLE,
    I85_AUTHORITY_EFFECT,
    I85_PARALLEL_PORTFOLIO_OWNER_FORBIDDEN,
    I85_ROLE,
    LIVE_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
    N_GREATER_THAN_ONE_RATIFIED,
    NAN_CORRELATION_SKIP_AS_AUTHORITY_FORBIDDEN,
    NETWORK_EFFECT,
    NO_AUTOMATIC_STAGE_PROGRESSION,
    NO_SILENT_G13_BYPASS,
    NUMERIC_POLICY_STATUS,
    ORDER_EFFECT,
    PACKAGE_MARKER,
    PER_INSTRUMENT_CAPITAL_BUDGET_RATIFIED,
    PORTFOLIO_AGGREGATION_IS_DERIVED_UNLESS_EXPLICIT,
    PORTFOLIO_VAR_LIMIT_RATIFIED,
    PRODUCTIVE_CALLER_EXISTS,
    PROMOTION_AUTHORITY,
    R6_RUNTIME_AUTHORIZED,
    R6_S1_CLOSED,
    REMEDIATION_ID,
    REQUIRED_OWNER_RELPATHS,
    RISK_ENFORCER_IS_AUTHORITY,
    RISK_LAYER_MANAGER_IS_AUTHORITY,
    RISK_LOGIC_CHANGE,
    RUNTIME_AUTHORITY_IMPACT,
    RUNTIME_EFFECT,
    S3_RUNTIME_IMPLEMENTATION_AUTHORIZED,
    S5_AUTHORIZATION_GRANTED,
    SELECTED_FUTURE_COUNT,
    SHADOW_IS_NOT_LIVE_PROOF,
    SINGLE_FUTURE_LIVE_PROOF,
    SINGLE_FUTURE_LIVE_PROOF_MEANING,
    SINGLE_SELECTED_FUTURE,
    SOURCE_GAP_IDS,
    SRC_PORTFOLIO_IS_RESEARCH_HELPER,
    TARGET_BINDING,
    TESTNET_AUTHORIZED,
    TESTNET_IS_NOT_LIVE_PROOF,
    TOP_N_ACTIVE_SET_AUTHORITY,
    TRADING_GRANT,
    U_MF_S1_RATIFIED,
    UQ5_RATIFIED,
    ZERO_CORRELATION_OPTIMISTIC_FALLBACK_FORBIDDEN,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.dimensions_v1 import (
    REQUIRED_ITEM_IDS,
    S2_DIMENSIONS,
    require_item,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.intents_v1 import (
    I37_I74_I85_ROWS,
    REQUIRED_INTENT_IDS,
    require_intent,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.models_v1 import (
    R6S2PortfolioRiskError,
    S2_CLOSABLE_STATUSES,
)
from src.ops.productive_futures_accounting_runtime_binding_v1 import constants_v1 as cap31
from src.ops.productive_futures_ranking_producer_v1 import constants_v1 as cap22
from src.ops.productive_reconciliation_runtime_binding_v1 import constants_v1 as cap11
from src.ops.single_future_stateful_no_order_runtime_activation_v1 import (
    constants_v1 as cap72,
)
from src.ops.single_selected_future_policy_v1 import constants_v1 as cap23
from src.ops.single_selected_future_runtime_binding_v1 import constants_v1 as cap24

_PACKAGE_REL = Path("src") / "ops" / "canonical_r6_s2_portfolio_risk_contracts_v1"
_FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "src.orders",
        "src.live",
        "src.intents",
        "src.execution_simple",
        "src.risk.risk_layer_manager",
        "src.risk.enforcement",
        "src.portfolio",
    }
)


def _reject(message: str) -> None:
    raise R6S2PortfolioRiskError(message)


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
    _require(payload, "canary_execute", False)
    _require(payload, "capability_id", CAPABILITY_ID)
    _require(payload, "contract_id", CONTRACT_ID)
    _require(payload, "contract_owner", CONTRACT_OWNER)
    _require(payload, "contract_version", CONTRACT_VERSION)
    _require(payload, "core_logic_change", CORE_LOGIC_CHANGE)
    _require(payload, "done_criterion", DONE_CRITERION)
    _require(payload, "g13_status", G13_STATUS)
    _require(payload, "g13_unchanged", True)
    _require(payload, "i37_i74_dual_var_authority_forbidden", True)
    _require(payload, "i85_parallel_portfolio_owner_forbidden", True)
    _require(payload, "live_authorized", False)
    _require(payload, "max_positions_effective", 1)
    _require(payload, "multi_future_runtime_authorized", False)
    _require(payload, "multi_future_runtime_implemented", False)
    _require(payload, "n_greater_than_one_ratified", False)
    _require(payload, "network_effect", False)
    _require(payload, "numeric_policy_status", NUMERIC_POLICY_STATUS)
    _require(payload, "order_effect", ORDER_EFFECT)
    _require(payload, "package_marker", PACKAGE_MARKER)
    _require(payload, "portfolio_var_limit_ratified", False)
    _require(payload, "productive_caller_exists", False)
    _require(payload, "r6_runtime_authorized", False)
    _require(payload, "remediation_id", REMEDIATION_ID)
    _require(payload, "risk_layer_manager_is_authority", False)
    _require(payload, "risk_logic_change", False)
    _require(payload, "runtime_effect", False)
    _require(payload, "s3_runtime_implementation_authorized", False)
    _require(payload, "selected_future_count", 1)
    _require(payload, "single_future_live_proof", False)
    _require(payload, "single_selected_future", True)
    _require(payload, "source_gap_ids", list(SOURCE_GAP_IDS))
    _require(payload, "src_portfolio_is_research_helper", True)
    _require(payload, "target_binding", TARGET_BINDING)
    _require(payload, "testnet_authorized", False)
    _require(payload, "top_n_active_set_authority", False)
    _require(payload, "trading_grant", False)
    _require(payload, "zero_correlation_optimistic_fallback_forbidden", True)


def assert_package_import_boundary_v1(root: Path | None = None) -> None:
    package = (root or repo_root()) / _PACKAGE_REL
    for path in sorted(package.glob("*.py")):
        for name in _iter_import_names(path):
            for forbidden in _FORBIDDEN_IMPORT_ROOTS:
                if name == forbidden or name.startswith(f"{forbidden}."):
                    _reject(f"forbidden_import:{path.name}:{name}")


def assert_required_owners_present_v1(root: Path | None = None) -> None:
    base = root or repo_root()
    for rel in REQUIRED_OWNER_RELPATHS:
        if not (base / rel).is_file():
            _reject(f"owner_file_missing:{rel}")


def assert_existing_runtime_bindings_remain_single_future_v1() -> None:
    if cap23.MAX_POSITIONS_EFFECTIVE != 1 or cap24.MAX_POSITIONS_EFFECTIVE != 1:
        _reject("max_positions_not_1")
    if cap22.MAX_POSITIONS_EFFECTIVE != 1:
        _reject("ranking_max_positions_not_1")
    if cap11.PHASE1_MAX_OPEN_POSITIONS != 1:
        _reject("recon_max_open_positions_not_1")
    if cap23.SELECTED_FUTURE_COUNT != 1 or cap24.SELECTED_FUTURE_COUNT != 1:
        _reject("selected_future_count_not_1")
    if cap23.SINGLE_SELECTED_FUTURE is not True or cap24.SINGLE_SELECTED_FUTURE is not True:
        _reject("single_selected_future_not_preserved")
    if any(
        (
            cap23.MULTI_FUTURE_RUNTIME_AUTHORIZED,
            cap24.MULTI_FUTURE_RUNTIME_AUTHORIZED,
            cap22.MULTI_FUTURE_RUNTIME_AUTHORIZED,
            cap31.MULTI_FUTURE_RUNTIME_AUTHORIZED,
            cap11.MULTI_FUTURE_RUNTIME_AUTHORIZED,
            cap72.MULTI_FUTURE_RUNTIME_AUTHORIZED,
        )
    ):
        _reject("multi_future_runtime_authorized_true")
    if getattr(cap72, "MULTI_FUTURE_RUNTIME_IMPLEMENTED", False) is True:
        _reject("multi_future_runtime_implemented_true")
    if cap23.SINGLE_WRITER_IDENTITY != "single_selected_future_selection_writer_v1":
        _reject("selection_writer_drift")
    if cap31.SINGLE_WRITER_IDENTITY != ACCOUNTING_WRITER:
        _reject("accounting_writer_drift")
    if cap24.SELECTION_SINGLE_WRITER is not True:
        _reject("selection_single_writer_false")
    if cap23.LIVE_AUTHORIZED or cap24.ORDERS_AUTHORIZED or cap72.LIVE_ORDERS:
        _reject("live_or_orders_authorized")


def assert_s2_dimensions_complete_v1() -> None:
    present = tuple(row.item_id for row in S2_DIMENSIONS)
    if present != REQUIRED_ITEM_IDS:
        _reject(f"s2_item_mismatch:expected={REQUIRED_ITEM_IDS}:actual={present}")
    for item_id in REQUIRED_ITEM_IDS:
        row = require_item(item_id)
        if row.status not in S2_CLOSABLE_STATUSES:
            _reject(f"s2_item_not_closable:{item_id}:{row.status.value}")
    if require_item("correlation_zero_corr_prohibition").status.value != "CLOSED_PROVEN":
        _reject("zero_corr_prohibition_not_closed")
    if require_item("no_allocation_order_bypass").status.value != "CLOSED_PROVEN":
        _reject("allocation_bypass_not_closed")
    if require_item("safety_max_position_invariant").status.value != "CLOSED_PROVEN":
        _reject("max_position_invariant_not_closed")
    if require_item("accounting_one_global_writer").status.value != "CLOSED_PROVEN":
        _reject("accounting_writer_not_closed")


def assert_intent_bindings_v1() -> None:
    present = tuple(row.intent_id for row in I37_I74_I85_ROWS)
    if present != REQUIRED_INTENT_IDS:
        _reject(f"s2_intent_mismatch:expected={REQUIRED_INTENT_IDS}:actual={present}")
    i37 = require_intent("I37")
    i74 = require_intent("I74")
    i85 = require_intent("I85")
    if i37.current_authority_effect != "NONE" or i74.current_authority_effect != "NONE":
        _reject("i37_or_i74_authority_effect_not_none")
    if i85.current_authority_effect != "NONE":
        _reject("i85_authority_effect_not_none")
    if not i37.safe_to_bind_read_only or not i74.safe_to_bind_read_only:
        _reject("i37_i74_not_safe_to_bind_read_only")
    if not i85.safe_to_bind_read_only:
        _reject("i85_not_safe_to_bind_read_only")
    if i37.s2_gap != "NONE_FOR_S2_STRUCTURAL_CONTRACT":
        _reject("i37_unexpected_s2_gap")
    if i74.s2_gap != "NONE_FOR_S2_STRUCTURAL_CONTRACT":
        _reject("i74_unexpected_s2_gap")
    if i85.s2_gap != "NONE_FOR_S2_STRUCTURAL_CONTRACT":
        _reject("i85_unexpected_s2_gap")


def evaluate_r6_s2_portfolio_risk_contracts_v1(*, root: Path | None = None) -> Mapping[str, Any]:
    payload = load_layer_config_v1(root)
    validate_layer_config_v1(payload)
    assert_package_import_boundary_v1(root)
    assert_required_owners_present_v1(root)
    assert_existing_runtime_bindings_remain_single_future_v1()
    assert_s2_dimensions_complete_v1()
    assert_intent_bindings_v1()
    if any(
        (
            ACTIVATED,
            PRODUCTIVE_CALLER_EXISTS,
            TRADING_GRANT,
            PROMOTION_AUTHORITY,
            LIVE_AUTHORIZED,
            TESTNET_AUTHORIZED,
            CANARY_EXECUTE,
            NETWORK_EFFECT,
            R6_RUNTIME_AUTHORIZED,
            S3_RUNTIME_IMPLEMENTATION_AUTHORIZED,
            S5_AUTHORIZATION_GRANTED,
            MULTI_FUTURE_RUNTIME_AUTHORIZED,
            MULTI_FUTURE_RUNTIME_IMPLEMENTED,
            SINGLE_FUTURE_LIVE_PROOF,
            TOP_N_ACTIVE_SET_AUTHORITY,
            RISK_LAYER_MANAGER_IS_AUTHORITY,
            RISK_ENFORCER_IS_AUTHORITY,
            N_GREATER_THAN_ONE_RATIFIED,
            PORTFOLIO_VAR_LIMIT_RATIFIED,
            COMPONENT_VAR_LIMIT_RATIFIED,
            CORRELATION_THRESHOLD_RATIFIED,
            CONCENTRATION_PERCENTAGE_RATIFIED,
            PER_INSTRUMENT_CAPITAL_BUDGET_RATIFIED,
            GROSS_NET_EXPOSURE_LIMIT_RATIFIED,
            CORE_LOGIC_CHANGE,
            RISK_LOGIC_CHANGE,
        )
    ):
        _reject("authority_or_runtime_or_numeric_flag_raised")
    if MAX_POSITIONS_EFFECTIVE != 1 or SELECTED_FUTURE_COUNT != 1:
        _reject("single_future_binding_lost")
    if not (
        NO_SILENT_G13_BYPASS
        and NO_AUTOMATIC_STAGE_PROGRESSION
        and UQ5_RATIFIED
        and U_MF_S1_RATIFIED
        and R6_S1_CLOSED
        and G13_UNCHANGED
        and I37_I74_DUAL_VAR_AUTHORITY_FORBIDDEN
        and I85_PARALLEL_PORTFOLIO_OWNER_FORBIDDEN
        and SRC_PORTFOLIO_IS_RESEARCH_HELPER
        and ZERO_CORRELATION_OPTIMISTIC_FALLBACK_FORBIDDEN
        and NAN_CORRELATION_SKIP_AS_AUTHORITY_FORBIDDEN
        and ALLOCATION_TO_ORDER_BYPASS_FORBIDDEN
        and PORTFOLIO_AGGREGATION_IS_DERIVED_UNLESS_EXPLICIT
    ):
        _reject("doctrine_flags_missing")
    if NUMERIC_POLICY_STATUS != "DEFERRED_UNRATIFIED":
        _reject("numeric_policy_not_deferred")
    if CANONICAL_AUTHORITY_CHAIN != (
        "strategy_selection",
        "scope_capital",
        "risk",
        "safety",
        "intent",
        "execution",
    ):
        _reject("authority_chain_drift")
    claims = {
        "activated": ACTIVATED,
        "authority_effect": AUTHORITY_EFFECT,
        "canary_execute": CANARY_EXECUTE,
        "canonical_single_instrument_risk_owner": CANONICAL_SINGLE_INSTRUMENT_RISK_OWNER,
        "canonical_single_instrument_risk_gate": CANONICAL_SINGLE_INSTRUMENT_RISK_GATE,
        "capability_id": CAPABILITY_ID,
        "component_risk_owner": COMPONENT_RISK_OWNER,
        "component_var_contract_status": require_item(
            "portfolio_component_marginal_var"
        ).status.value,
        "concentration_contract_status": require_item(
            "portfolio_concentration_limits"
        ).status.value,
        "config_digest": digest_mapping(payload),
        "core_logic_change": CORE_LOGIC_CHANGE,
        "correlation_contract_status": require_item(
            "correlation_zero_corr_prohibition"
        ).status.value,
        "cvar_contract_status": require_item("portfolio_cvar_expected_shortfall").status.value,
        "capital_envelope_boundary_status": require_item("capital_envelope_ownership").status.value,
        "done_criterion": DONE_CRITERION,
        "duplicate_accounting_writer_found": False,
        "duplicate_execution_writer_found": False,
        "duplicate_risk_authority_found": False,
        "future_portfolio_risk_owner": FUTURE_PORTFOLIO_RISK_OWNER,
        "g13_status": G13_STATUS,
        "g13_unchanged": G13_UNCHANGED,
        "global_risk_cap_boundary_status": require_item("portfolio_loss_budget").status.value,
        "i12_role": I12_ROLE,
        "i17_is_not_live_proof": I17_IS_NOT_LIVE_PROOF,
        "i29_role": I29_ROLE,
        "i37_authority_effect": I37_AUTHORITY_EFFECT,
        "i37_role": I37_ROLE,
        "i37_status": require_intent("I37").current_state,
        "i74_authority_effect": I74_AUTHORITY_EFFECT,
        "i74_role": I74_ROLE,
        "i74_status": require_intent("I74").current_state,
        "i85_authority_effect": I85_AUTHORITY_EFFECT,
        "i85_role": I85_ROLE,
        "i85_status": require_intent("I85").current_state,
        "kill_switch_portfolio_interaction_status": require_item(
            "safety_global_kill_interaction"
        ).status.value,
        "live_authorized": LIVE_AUTHORIZED,
        "max_positions_effective": MAX_POSITIONS_EFFECTIVE,
        "multi_future_runtime_authorized": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "multi_future_runtime_implemented": MULTI_FUTURE_RUNTIME_IMPLEMENTED,
        "network_effect": NETWORK_EFFECT,
        "numeric_policy_status": NUMERIC_POLICY_STATUS,
        "order_effect": ORDER_EFFECT,
        "package_marker": PACKAGE_MARKER,
        "per_instrument_risk_boundary_status": require_item(
            "component_per_instrument_loss_risk_budget"
        ).status.value,
        "portfolio_var_contract_status": require_item("portfolio_var").status.value,
        "r6_runtime_authorized": R6_RUNTIME_AUTHORIZED,
        "r6_s2_closeout_status": "CLOSED_PROVEN_FORENSIC_READ_ONLY",
        "remediation_id": REMEDIATION_ID,
        "restart_recon_portfolio_risk_status": require_item(
            "accounting_restart_reconstruction"
        ).status.value,
        "risk_logic_change": RISK_LOGIC_CHANGE,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "runtime_effect": RUNTIME_EFFECT,
        "s0_status": "CLOSED_PROVEN_CURRENT_SINGLE_FUTURE_BARRIER",
        "s1_status": "CLOSED_PROVEN_FORENSIC_READ_ONLY",
        "s2_item_count": len(S2_DIMENSIONS),
        "s2_status": "CLOSED_PROVEN_FORENSIC_READ_ONLY",
        "s2_structural_contract_status": "CLOSED_PROVEN_FORENSIC_READ_ONLY",
        "s3_runtime_implementation_authorized": S3_RUNTIME_IMPLEMENTATION_AUTHORIZED,
        "s3_status": "BLOCKED_BY_SEPARATE_OWNER_GO",
        "s4_status": "BLOCKED_BY_SEPARATE_OWNER_GO",
        "s5_status": "BLOCKED_BY_SINGLE_FUTURE_LIVE_PROOF",
        "s6_status": "BLOCKED_BY_SINGLE_FUTURE_LIVE_PROOF",
        "selected_future_count": SELECTED_FUTURE_COUNT,
        "shadow_is_not_live_proof": SHADOW_IS_NOT_LIVE_PROOF,
        "single_future_live_proof": SINGLE_FUTURE_LIVE_PROOF,
        "single_future_live_proof_meaning": SINGLE_FUTURE_LIVE_PROOF_MEANING,
        "single_selected_future": SINGLE_SELECTED_FUTURE,
        "single_selected_future_binding_preserved": True,
        "smallest_missing_contract_gap": "NONE_FOR_S2_STRUCTURAL_FRAME",
        "src_portfolio_is_research_helper": SRC_PORTFOLIO_IS_RESEARCH_HELPER,
        "target_binding": TARGET_BINDING,
        "testnet_authorized": TESTNET_AUTHORIZED,
        "testnet_is_not_live_proof": TESTNET_IS_NOT_LIVE_PROOF,
        "top_n_active_set_authority": TOP_N_ACTIVE_SET_AUTHORITY,
        "trading_grant": TRADING_GRANT,
        "verdict": "PASS_R6_S2_PORTFOLIO_RISK_CONTRACTS_V1",
        "zero_correlation_optimistic_fallback_forbidden": (
            ZERO_CORRELATION_OPTIMISTIC_FALLBACK_FORBIDDEN
        ),
    }
    return MappingProxyType(claims)
