"""Fail-closed verifier for R6 Phase-8.1 policy precondition v1."""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.checklist_v1 import (
    REQUIRED_ITEM_IDS,
    S1_CHECKLIST,
    require_item,
)
from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.constants_v1 import (
    ACCOUNTING_WRITER,
    ACTIVATED,
    AUTHORITY_EFFECT,
    CANARY_EXECUTE,
    CAPABILITY_ID,
    CONTRACT_ID,
    CONTRACT_OWNER,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    DONE_CRITERION,
    G13_STATUS,
    I17_IS_NOT_LIVE_PROOF,
    LIVE_AUTHORIZED,
    MAX_AGE_ALLOWED_USES,
    MAX_AGE_ENFORCEMENT_ENABLED,
    MAX_AGE_PRODUCTIVE_GATE,
    MAX_AGE_ROLE,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_IMPLEMENTED,
    NETWORK_EFFECT,
    NO_AUTOMATIC_STAGE_PROGRESSION,
    NO_SILENT_G13_BYPASS,
    ORDER_EFFECT,
    PACKAGE_MARKER,
    PRODUCTIVE_CALLER_EXISTS,
    PROMOTION_AUTHORITY,
    R6_RUNTIME_AUTHORIZED,
    REMEDIATION_ID,
    REQUIRED_OWNER_RELPATHS,
    RUNTIME_AUTHORITY_IMPACT,
    RUNTIME_EFFECT,
    S3_IMPLEMENTATION_AUTHORIZED,
    S5_AUTHORIZATION_GRANTED,
    SELECTED_FUTURE_COUNT,
    SHADOW_IS_NOT_LIVE_PROOF,
    SINGLE_FUTURE_LIVE_PROOF,
    SINGLE_FUTURE_LIVE_PROOF_MEANING,
    SINGLE_SELECTED_FUTURE,
    SOURCE_GAP_IDS,
    TARGET_BINDING,
    TESTNET_AUTHORIZED,
    TESTNET_IS_NOT_LIVE_PROOF,
    TOP_N_ACTIVE_SET_AUTHORITY,
    TRADING_GRANT,
    U_MF_S1_RATIFIED,
    UQ5_RATIFIED,
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
from src.ops.productive_futures_accounting_runtime_binding_v1 import constants_v1 as cap31
from src.ops.productive_futures_ranking_producer_v1 import constants_v1 as cap22
from src.ops.productive_reconciliation_runtime_binding_v1 import constants_v1 as cap11
from src.ops.single_future_stateful_no_order_runtime_activation_v1 import (
    constants_v1 as cap72,
)
from src.ops.single_selected_future_policy_v1 import constants_v1 as cap23
from src.ops.single_selected_future_runtime_binding_v1 import constants_v1 as cap24

_PACKAGE_REL = Path("src") / "ops" / "canonical_r6_phase_8_1_policy_precondition_v1"
_FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "src.orders",
        "src.live",
        "src.intents",
        "src.execution_simple",
    }
)


def _reject(message: str) -> None:
    raise R6Phase81PolicyError(message)


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
    _require(payload, "live_authorized", False)
    _require(payload, "max_age_allowed_uses", list(MAX_AGE_ALLOWED_USES))
    _require(payload, "max_age_enforcement_enabled", False)
    _require(payload, "max_age_productive_gate", False)
    _require(payload, "max_age_role", MAX_AGE_ROLE)
    _require(payload, "max_positions_effective", 1)
    _require(payload, "multi_future_runtime_authorized", False)
    _require(payload, "multi_future_runtime_implemented", False)
    _require(payload, "network_effect", False)
    _require(payload, "no_automatic_stage_progression", True)
    _require(payload, "no_silent_g13_bypass", True)
    _require(payload, "order_effect", ORDER_EFFECT)
    _require(payload, "package_marker", PACKAGE_MARKER)
    _require(payload, "productive_caller_exists", False)
    _require(payload, "promotion_authority", False)
    _require(payload, "r6_runtime_authorized", False)
    _require(payload, "remediation_id", REMEDIATION_ID)
    _require(payload, "runtime_authority_impact", RUNTIME_AUTHORITY_IMPACT)
    _require(payload, "runtime_effect", False)
    _require(payload, "s3_implementation_authorized", False)
    _require(payload, "s5_authorization_granted", False)
    _require(payload, "selected_future_count", 1)
    _require(payload, "single_future_live_proof", False)
    _require(payload, "single_selected_future", True)
    _require(payload, "source_gap_ids", list(SOURCE_GAP_IDS))
    _require(payload, "target_binding", TARGET_BINDING)
    _require(payload, "testnet_authorized", False)
    _require(payload, "top_n_active_set_authority", False)
    _require(payload, "trading_grant", False)


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
    if cap23.DEFAULT_HYSTERESIS_RANK_IMPROVEMENT < 1:
        _reject("hysteresis_missing")
    if cap23.DEFAULT_MIN_HOLDING_PERIOD_SECONDS < 1:
        _reject("cooldown_missing")


def assert_s1_checklist_complete_v1() -> None:
    present = tuple(row.item_id for row in S1_CHECKLIST)
    if present != REQUIRED_ITEM_IDS:
        _reject(f"s1_item_mismatch:expected={REQUIRED_ITEM_IDS}:actual={present}")
    allowed_s1 = {
        PolicyItemStatus.CLOSED_PROVEN,
        PolicyItemStatus.NOT_REQUIRED_AT_THIS_STAGE,
    }
    for item_id in REQUIRED_ITEM_IDS:
        row = require_item(item_id)
        if row.status not in allowed_s1:
            _reject(f"s1_item_not_closable:{item_id}:{row.status.value}")
    if require_item("no_silent_g13_bypass").status is not PolicyItemStatus.CLOSED_PROVEN:
        _reject("g13_bypass_item_not_closed")
    if require_item("no_automatic_stage_progression").status is not PolicyItemStatus.CLOSED_PROVEN:
        _reject("auto_stage_item_not_closed")


def evaluate_r6_phase_8_1_policy_precondition_v1(*, root: Path | None = None) -> Mapping[str, Any]:
    payload = load_layer_config_v1(root)
    validate_layer_config_v1(payload)
    assert_package_import_boundary_v1(root)
    assert_required_owners_present_v1(root)
    assert_existing_runtime_bindings_remain_single_future_v1()
    assert_s1_checklist_complete_v1()
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
            S3_IMPLEMENTATION_AUTHORIZED,
            S5_AUTHORIZATION_GRANTED,
            MULTI_FUTURE_RUNTIME_AUTHORIZED,
            MULTI_FUTURE_RUNTIME_IMPLEMENTED,
            SINGLE_FUTURE_LIVE_PROOF,
            TOP_N_ACTIVE_SET_AUTHORITY,
            MAX_AGE_ENFORCEMENT_ENABLED,
            MAX_AGE_PRODUCTIVE_GATE,
        )
    ):
        _reject("authority_or_runtime_flag_raised")
    if MAX_POSITIONS_EFFECTIVE != 1 or SELECTED_FUTURE_COUNT != 1:
        _reject("single_future_binding_lost")
    if not (
        NO_SILENT_G13_BYPASS
        and NO_AUTOMATIC_STAGE_PROGRESSION
        and UQ5_RATIFIED
        and U_MF_S1_RATIFIED
    ):
        _reject("doctrine_flags_missing")
    claims = {
        "activated": ACTIVATED,
        "authority_effect": AUTHORITY_EFFECT,
        "canary_execute": CANARY_EXECUTE,
        "capability_id": CAPABILITY_ID,
        "config_digest": digest_mapping(payload),
        "core_logic_change": CORE_LOGIC_CHANGE,
        "done_criterion": DONE_CRITERION,
        "duplicate_accounting_writer_found": False,
        "duplicate_execution_writer_found": False,
        "g13_status": G13_STATUS,
        "i17_is_not_live_proof": I17_IS_NOT_LIVE_PROOF,
        "live_authorized": LIVE_AUTHORIZED,
        "max_age_role": MAX_AGE_ROLE,
        "max_positions_effective": MAX_POSITIONS_EFFECTIVE,
        "multi_future_runtime_authorized": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "multi_future_runtime_implemented": MULTI_FUTURE_RUNTIME_IMPLEMENTED,
        "network_effect": NETWORK_EFFECT,
        "no_automatic_stage_progression": NO_AUTOMATIC_STAGE_PROGRESSION,
        "no_silent_g13_bypass": NO_SILENT_G13_BYPASS,
        "order_effect": ORDER_EFFECT,
        "package_marker": PACKAGE_MARKER,
        "phase_8_1_policy_checklist_status": "CLOSED_PROVEN_FORENSIC_READ_ONLY",
        "r6_canonical_closeout_status": "CLOSED_PROVEN_FORENSIC_READ_ONLY",
        "r6_runtime_authorized": R6_RUNTIME_AUTHORIZED,
        "remediation_id": REMEDIATION_ID,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "runtime_effect": RUNTIME_EFFECT,
        "s0_status": "CLOSED_PROVEN_CURRENT_SINGLE_FUTURE_BARRIER",
        "s1_item_count": len(S1_CHECKLIST),
        "s1_status": "CLOSED_PROVEN_FORENSIC_READ_ONLY",
        "s2_status": "PLANNED_ONLY",
        "s3_status": "BLOCKED_BY_SEPARATE_OWNER_GO",
        "s4_status": "BLOCKED_BY_SEPARATE_OWNER_GO",
        "s5_status": "BLOCKED_BY_SINGLE_FUTURE_LIVE_PROOF",
        "s6_status": "BLOCKED_BY_SINGLE_FUTURE_LIVE_PROOF",
        "s3_implementation_authorized": S3_IMPLEMENTATION_AUTHORIZED,
        "selected_future_count": SELECTED_FUTURE_COUNT,
        "shadow_is_not_live_proof": SHADOW_IS_NOT_LIVE_PROOF,
        "single_future_live_proof": SINGLE_FUTURE_LIVE_PROOF,
        "single_future_live_proof_meaning": SINGLE_FUTURE_LIVE_PROOF_MEANING,
        "single_selected_future": SINGLE_SELECTED_FUTURE,
        "single_selected_future_binding_preserved": True,
        "target_binding": TARGET_BINDING,
        "testnet_authorized": TESTNET_AUTHORIZED,
        "testnet_is_not_live_proof": TESTNET_IS_NOT_LIVE_PROOF,
        "top_n_active_set_authority": TOP_N_ACTIVE_SET_AUTHORITY,
        "trading_grant": TRADING_GRANT,
        "verdict": "PASS_R6_PHASE_8_1_POLICY_PRECONDITION_V1",
    }
    return MappingProxyType(claims)
