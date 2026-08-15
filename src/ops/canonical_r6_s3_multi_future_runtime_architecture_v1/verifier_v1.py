"""Fail-closed verifier for R6 S3 Phase-8.2 runtime architecture v1."""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    ACCOUNT_MUTATION_EFFECT,
    ACTIVATED,
    AUTHORITY_EFFECT,
    CANARY_AUTHORIZED,
    CANARY_EXECUTE,
    CANONICAL_ACCOUNTING_WRITER_IDENTITY,
    CANONICAL_EXECUTION_WRITER_IDENTITY,
    CAPABILITY_ID,
    CONTRACT_ID,
    CONTRACT_OWNER,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    CURRENT_EFFECTIVE_RUNTIME_MODE,
    DONE_CRITERION,
    FORBIDDEN_IMPORT_ROOTS,
    G13_STATUS,
    G13_UNCHANGED,
    LIVE_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
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
    SECOND_ACCOUNTING_AUTHORITY_CREATED,
    SECOND_EXECUTION_AUTHORITY_CREATED,
    SELECTED_FUTURE_COUNT,
    SINGLE_SELECTED_FUTURE,
    SOURCE_GAP_IDS,
    STRATEGY_LOGIC_MUTATED,
    SUBMIT_UNLOCKED,
    TARGET_BINDING,
    TESTNET_AUTHORIZED,
    TOP_N_ACTIVE_SET_AUTHORITY,
    TRADING_AUTHORITY_EXPANDED,
    TRADING_GRANT,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    R6S3RuntimeArchitectureError,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.orchestrator_v1 import (
    default_single_future_request_v1,
    evaluate_phase_82_graph_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1 import constants_v1 as cap31
from src.ops.productive_futures_ranking_producer_v1 import constants_v1 as cap22
from src.ops.productive_reconciliation_runtime_binding_v1 import constants_v1 as cap11
from src.ops.single_future_stateful_no_order_runtime_activation_v1 import (
    constants_v1 as cap72,
)
from src.ops.single_selected_future_policy_v1 import constants_v1 as cap23
from src.ops.single_selected_future_runtime_binding_v1 import constants_v1 as cap24

_PACKAGE_REL = Path("src") / "ops" / "canonical_r6_s3_multi_future_runtime_architecture_v1"


def _reject(message: str) -> None:
    raise R6S3RuntimeArchitectureError(message)


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
    _require(payload, "package_marker", PACKAGE_MARKER)
    _require(payload, "productive_caller_exists", False)
    _require(payload, "remediation_id", REMEDIATION_ID)
    _require(payload, "s4_authorized", False)
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


def assert_existing_runtime_bindings_remain_single_future_v1() -> None:
    if cap23.MAX_POSITIONS_EFFECTIVE != 1 or cap24.MAX_POSITIONS_EFFECTIVE != 1:
        _reject("max_positions_not_1")
    if cap22.MAX_POSITIONS_EFFECTIVE != 1:
        _reject("ranking_max_positions_not_1")
    if cap11.PHASE1_MAX_OPEN_POSITIONS != 1:
        _reject("recon_max_open_positions_not_1")
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
        _reject("cap72_multi_future_runtime_implemented_true")
    if cap31.SINGLE_WRITER_IDENTITY != CANONICAL_ACCOUNTING_WRITER_IDENTITY:
        _reject("accounting_writer_drift")
    if cap72.SIMULATED_EXECUTION_PORT_OWNER != CANONICAL_EXECUTION_WRITER_IDENTITY:
        _reject("execution_writer_drift")


def evaluate_r6_s3_multi_future_runtime_architecture_v1(
    *,
    root: Path | None = None,
) -> Mapping[str, Any]:
    payload = load_layer_config_v1(root)
    validate_layer_config_v1(payload)
    assert_package_import_boundary_v1(root)
    assert_required_owners_present_v1(root)
    assert_existing_runtime_bindings_remain_single_future_v1()
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
            NEXT_STAGE_AUTOMATICALLY_AUTHORIZED,
            MULTI_FUTURE_RUNTIME_AUTHORIZED,
            TOP_N_ACTIVE_SET_AUTHORITY,
            CORE_LOGIC_CHANGE,
            STRATEGY_LOGIC_MUTATED,
            SECOND_EXECUTION_AUTHORITY_CREATED,
            SECOND_ACCOUNTING_AUTHORITY_CREATED,
            TRADING_AUTHORITY_EXPANDED,
        )
    ):
        _reject("authority_or_runtime_flag_raised")
    if MULTI_FUTURE_RUNTIME_IMPLEMENTED is not True:
        _reject("implemented_flag_not_true")
    if MAX_POSITIONS_EFFECTIVE != 1 or SELECTED_FUTURE_COUNT != 1:
        _reject("single_future_binding_lost")
    if not (NO_SILENT_G13_BYPASS and NO_AUTOMATIC_STAGE_PROGRESSION and G13_UNCHANGED):
        _reject("g13_doctrine_missing")
    if SINGLE_SELECTED_FUTURE is not True:
        _reject("single_selected_future_lost")
    result = evaluate_phase_82_graph_v1(default_single_future_request_v1("BTC-USDT-SWAP"))
    if result.authorized is not False:
        _reject("graph_authorized_true")
    if result.submit_unlocked is not False:
        _reject("graph_submit_unlocked")
    if len(result.effective_active_ids) != 1:
        _reject("graph_effective_active_not_1")
    if result.writer_bundle.execution_writer_identity != CANONICAL_EXECUTION_WRITER_IDENTITY:
        _reject("graph_execution_writer_drift")
    if result.writer_bundle.accounting_writer_identity != CANONICAL_ACCOUNTING_WRITER_IDENTITY:
        _reject("graph_accounting_writer_drift")
    claims = {
        "activated": ACTIVATED,
        "authority_effect": AUTHORITY_EFFECT,
        "canary_authorized": CANARY_AUTHORIZED,
        "capability_id": CAPABILITY_ID,
        "config_digest": digest_mapping(payload),
        "core_logic_change": CORE_LOGIC_CHANGE,
        "current_effective_runtime_mode": CURRENT_EFFECTIVE_RUNTIME_MODE,
        "done_criterion": DONE_CRITERION,
        "duplicate_accounting_writer_found": False,
        "duplicate_execution_writer_found": False,
        "g13_status": G13_STATUS,
        "g13_unchanged": G13_UNCHANGED,
        "live_authorized": LIVE_AUTHORIZED,
        "max_positions_effective": MAX_POSITIONS_EFFECTIVE,
        "multi_future_runtime_authorized": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "multi_future_runtime_implemented": MULTI_FUTURE_RUNTIME_IMPLEMENTED,
        "network_effect": NETWORK_EFFECT,
        "next_stage_automatically_authorized": NEXT_STAGE_AUTOMATICALLY_AUTHORIZED,
        "order_effect": ORDER_EFFECT,
        "account_mutation_effect": ACCOUNT_MUTATION_EFFECT,
        "package_marker": PACKAGE_MARKER,
        "r6_s1_status": "CLOSED_PROVEN_FORENSIC_READ_ONLY",
        "r6_s2_status": "CLOSED_PROVEN_FORENSIC_READ_ONLY",
        "r6_s3_implementation_complete": True,
        "remediation_id": REMEDIATION_ID,
        "s4_authorized": S4_AUTHORIZED,
        "second_accounting_authority_created": SECOND_ACCOUNTING_AUTHORITY_CREATED,
        "second_execution_authority_created": SECOND_EXECUTION_AUTHORITY_CREATED,
        "selected_future_count": SELECTED_FUTURE_COUNT,
        "single_selected_future": SINGLE_SELECTED_FUTURE,
        "submit_unlocked": SUBMIT_UNLOCKED,
        "target_binding": TARGET_BINDING,
        "testnet_authorized": TESTNET_AUTHORIZED,
        "top_n_active_set_authority": TOP_N_ACTIVE_SET_AUTHORITY,
        "trading_authority_expanded": TRADING_AUTHORITY_EXPANDED,
        "trading_grant": TRADING_GRANT,
        "verdict": "PASS_R6_S3_MULTI_FUTURE_RUNTIME_ARCHITECTURE_V1",
    }
    return MappingProxyType(claims)
