"""Fail-closed verifier for R2 Strategy Registry / Suitability / Selection v1."""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from src.ops.phase_9_1_strategy_registry_closure_v1.classifications_v1 import (
    all_required_registry_ids,
    productive_callers_for,
    registry_target_classification,
)
from src.ops.phase_9_1_strategy_registry_closure_v1.constants_v1 import HOST_COMPOSITION_STUB_ID
from src.strategies.canonical_strategy_registry_suitability_selection_v1.constants_v1 import (
    ACTIVATED,
    AUTHORITY_EFFECT,
    CANARY_EXECUTE,
    CAPABILITY_ID,
    CATALOG_OWNER,
    CATALOG_SELECTION_OWNER,
    CLASSIFICATION_OWNER,
    CONTRACT_ID,
    CONTRACT_OWNER,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    DONE_CRITERION,
    IDENTITY_OWNER,
    INSTRUMENT_SELECTION_OWNER,
    LIVE_AUTHORIZED,
    MAX_AGE_ALLOWED_USES,
    MAX_AGE_CAN_BLOCK_CANARY,
    MAX_AGE_CAN_BLOCK_TRADING,
    MAX_AGE_CAN_CHANGE_EXECUTION,
    MAX_AGE_CAN_CHANGE_PROMOTION,
    MAX_AGE_CAN_CHANGE_RISK_DECISIONS,
    MAX_AGE_CAN_CHANGE_SELECTION,
    MAX_AGE_ENFORCEMENT_ENABLED,
    MAX_AGE_PRODUCTIVE_GATE,
    MAX_AGE_ROLE,
    METADATA_EQUALS_AUTHORITY,
    NUMERIC_MAX_AGE_EFFECT,
    ORDER_EFFECT,
    PACKAGE_MARKER,
    PRODUCTIVE_CALLER_EXISTS,
    REGISTRY_IS_LIVE_PERMISSION,
    REMEDIATION_ID,
    RUNTIME_EFFECT,
    SILENT_AUTHORITY_PROMOTION,
    SOURCE_GAP_IDS,
    SUITABILITY_ADAPTER_OWNER,
    SUITABILITY_OWNER,
    SUITABILITY_SELECTION_OWNER,
    TESTNET_AUTHORIZED,
    TRADING_GRANT,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.eligibility_v1 import (
    evaluate_eligibility_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.identity_v1 import (
    resolve_canonical_identity_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.models_v1 import (
    SelectionIntent,
    StrategyRegistrySuitabilitySelectionError,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.selection_v1 import (
    select_registered_strategies_v1,
)
from src.strategies.registry import build_registry_snapshot
from src.strategies.suitability_registry_adapter_v1 import (
    build_suitability_registry_from_snapshot,
)

_FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "src.execution",
        "src.execution_simple",
        "src.orders",
        "src.live",
    }
)
_PACKAGE_REL = Path("src") / "strategies" / "canonical_strategy_registry_suitability_selection_v1"
_CANONICAL_REGISTRY_REL = Path("src") / "strategies" / "registry.py"
_AUTHORIZED_STRATEGY_SELECTORS = frozenset(
    {
        "select_strategy_deterministic",
        "select_registered_strategies_v1",
    }
)


def _reject(message: str) -> None:
    raise StrategyRegistrySuitabilitySelectionError(message)


def _require(payload: Mapping[str, Any], key: str, expected: Any) -> None:
    actual = payload.get(key)
    if actual != expected:
        _reject(f"config_field_mismatch:{key}:expected={expected!r}:actual={actual!r}")


def validate_layer_config_v1(payload: Mapping[str, Any]) -> None:
    _require(payload, "activated", False)
    _require(payload, "authority_effect", AUTHORITY_EFFECT)
    _require(payload, "canary_execute", False)
    _require(payload, "capability_id", CAPABILITY_ID)
    _require(payload, "catalog_owner", CATALOG_OWNER)
    _require(payload, "classification_owner", CLASSIFICATION_OWNER)
    _require(payload, "contract_id", CONTRACT_ID)
    _require(payload, "contract_owner", CONTRACT_OWNER)
    _require(payload, "contract_version", CONTRACT_VERSION)
    _require(payload, "core_logic_change", CORE_LOGIC_CHANGE)
    _require(payload, "done_criterion", DONE_CRITERION)
    _require(payload, "identity_owner", IDENTITY_OWNER)
    _require(payload, "instrument_selection_owner", INSTRUMENT_SELECTION_OWNER)
    _require(payload, "live_authorized", False)
    _require(payload, "max_age_allowed_uses", list(MAX_AGE_ALLOWED_USES))
    _require(payload, "max_age_can_block_canary", False)
    _require(payload, "max_age_can_block_trading", False)
    _require(payload, "max_age_can_change_execution", False)
    _require(payload, "max_age_can_change_promotion", False)
    _require(payload, "max_age_can_change_risk_decisions", False)
    _require(payload, "max_age_can_change_selection", False)
    _require(payload, "max_age_enforcement_enabled", False)
    _require(payload, "max_age_productive_gate", False)
    _require(payload, "max_age_role", MAX_AGE_ROLE)
    _require(payload, "metadata_equals_authority", False)
    _require(payload, "network_effect", False)
    _require(payload, "order_effect", False)
    _require(payload, "package_marker", PACKAGE_MARKER)
    _require(payload, "productive_caller_exists", False)
    _require(payload, "registry_is_live_permission", False)
    _require(payload, "remediation_id", REMEDIATION_ID)
    _require(payload, "runtime_effect", False)
    _require(payload, "silent_authority_promotion", False)
    _require(payload, "source_gap_ids", list(SOURCE_GAP_IDS))
    _require(payload, "suitability_adapter_owner", SUITABILITY_ADAPTER_OWNER)
    _require(payload, "suitability_owner", SUITABILITY_OWNER)
    _require(payload, "suitability_selection_owner", SUITABILITY_SELECTION_OWNER)
    _require(payload, "testnet_authorized", False)
    _require(payload, "trading_grant", False)
    _require(payload, "volatility_numeric_max_age_effect", NUMERIC_MAX_AGE_EFFECT)
    _require(payload, "volatility_numeric_max_age_enforcing", False)


def assert_package_has_no_execution_imports_v1(root: Path | None = None) -> None:
    package = (root or repo_root()) / _PACKAGE_REL
    for path in sorted(package.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for name in names:
                for forbidden in _FORBIDDEN_IMPORT_ROOTS:
                    if name == forbidden or name.startswith(f"{forbidden}."):
                        _reject(f"forbidden_import:{path.name}:{name}")
                if "max_age" in name.lower() and "watchdog" not in name.lower():
                    _reject(f"max_age_import_in_selection_package:{path.name}:{name}")


def assert_no_second_strategy_registry_v1(root: Path | None = None) -> None:
    src = (root or repo_root()) / "src"
    offenders: list[str] = []
    for path in sorted(src.rglob("*.py")):
        rel = path.relative_to(root or repo_root())
        if rel == _CANONICAL_REGISTRY_REL:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            target_names: list[str] = []
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        target_names.append(target.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                target_names.append(node.target.id)
            if "_STRATEGY_REGISTRY" in target_names:
                offenders.append(str(rel))
                break
    if offenders:
        _reject(f"second_strategy_registry:{offenders}")


def assert_no_second_authorized_selection_path_v1(root: Path | None = None) -> None:
    src = (root or repo_root()) / "src"
    extras: list[str] = []
    for path in sorted(src.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("select_strategy"):
                if node.name not in _AUTHORIZED_STRATEGY_SELECTORS:
                    rel = path.relative_to(root or repo_root())
                    extras.append(f"{rel}:{node.name}")
    if extras:
        _reject(f"second_authorized_selection_path:{extras}")


def assert_registry_uniqueness_and_classification_v1() -> Mapping[str, Any]:
    snapshot = build_registry_snapshot()
    ids = snapshot.strategy_ids_sorted
    if len(ids) != len(set(ids)):
        _reject("duplicate_canonical_strategy_id")
    required = all_required_registry_ids()
    if frozenset(ids) != frozenset(required):
        _reject(f"registry_classification_drift:{sorted(set(ids) ^ set(required))}")
    callers: dict[str, tuple[str, ...]] = {}
    for strategy_id in ids:
        first = resolve_canonical_identity_v1(strategy_id)
        second = resolve_canonical_identity_v1(strategy_id)
        if first.identity_digest != second.identity_digest:
            _reject(f"identity_digest_unstable:{strategy_id}")
        if first.canonical_strategy_id != strategy_id:
            _reject(f"canonical_id_not_stable:{strategy_id}")
        classification = registry_target_classification(strategy_id)
        callers[strategy_id] = productive_callers_for(strategy_id, classification=classification)
        eligibility = evaluate_eligibility_v1(strategy_id)
        if eligibility.runtime_authority_eligible:
            _reject(f"catalog_strategy_claimed_runtime_authority:{strategy_id}")
        if eligibility.max_age_consulted:
            _reject(f"eligibility_consulted_max_age:{strategy_id}")
    alias = resolve_canonical_identity_v1("el_karoui_vol_v1")
    if alias.canonical_strategy_id != "el_karoui_vol_model":
        _reject("alias_identity_drift")
    return MappingProxyType(
        {
            "caller_count": len(callers),
            "registry_semantic_digest": snapshot.semantic_digest,
            "strategy_count": len(ids),
        }
    )


def assert_suitability_and_selection_deterministic_v1() -> Mapping[str, Any]:
    snapshot = build_registry_snapshot()
    first = build_suitability_registry_from_snapshot(snapshot)
    second = build_suitability_registry_from_snapshot(snapshot)
    first_ids = tuple(entry.strategy_id for entry in first.entries)
    second_ids = tuple(entry.strategy_id for entry in second.entries)
    if first_ids != second_ids:
        _reject("suitability_snapshot_nondeterministic")
    if len(first_ids) != len(set(first_ids)):
        _reject("duplicate_suitability_snapshot_id")
    enumerate_a = select_registered_strategies_v1(intent=SelectionIntent.CATALOG_ENUMERATE)
    enumerate_b = select_registered_strategies_v1(intent=SelectionIntent.CATALOG_ENUMERATE)
    if enumerate_a.selection_digest != enumerate_b.selection_digest:
        _reject("catalog_selection_nondeterministic")
    if enumerate_a.selected_strategy_id is not None:
        _reject("catalog_enumerate_selected_a_strategy")
    if enumerate_a.trading_grant or enumerate_a.runtime_effect:
        _reject("catalog_enumerate_granted_trading")
    if enumerate_a.max_age_consulted:
        _reject("selection_consulted_max_age")
    composition = select_registered_strategies_v1(
        requested_ids=(HOST_COMPOSITION_STUB_ID,),
        intent=SelectionIntent.COMPOSITION_CANDIDATE,
    )
    if composition.selected_strategy_id != HOST_COMPOSITION_STUB_ID:
        _reject("host_composition_stub_not_selected")
    if composition.trading_grant:
        _reject("composition_candidate_trading_grant")
    return MappingProxyType(
        {
            "catalog_selection_digest": enumerate_a.selection_digest,
            "registry_semantic_digest": snapshot.semantic_digest,
            "suitability_entry_count": len(first_ids),
            "suitability_snapshot_digest": enumerate_a.suitability_snapshot_digest,
        }
    )


def evaluate_r2_registry_suitability_selection_v1(*, root: Path | None = None) -> Mapping[str, Any]:
    payload = load_layer_config_v1(root)
    validate_layer_config_v1(payload)
    assert_package_has_no_execution_imports_v1(root)
    assert_no_second_strategy_registry_v1(root)
    assert_no_second_authorized_selection_path_v1(root)
    inventory = assert_registry_uniqueness_and_classification_v1()
    selection = assert_suitability_and_selection_deterministic_v1()
    claims = {
        "activated": ACTIVATED,
        "authority_effect": AUTHORITY_EFFECT,
        "canary_execute": CANARY_EXECUTE,
        "capability_id": CAPABILITY_ID,
        "catalog_owner": CATALOG_OWNER,
        "catalog_selection_digest": selection["catalog_selection_digest"],
        "catalog_selection_owner": CATALOG_SELECTION_OWNER,
        "classification_owner": CLASSIFICATION_OWNER,
        "config_digest": digest_mapping(payload),
        "core_logic_change": CORE_LOGIC_CHANGE,
        "done_criterion": DONE_CRITERION,
        "eg_reg_callers_enumerated": True,
        "g14_non_authoritative_until_promotion": True,
        "identity_owner": IDENTITY_OWNER,
        "instrument_selection_owner": INSTRUMENT_SELECTION_OWNER,
        "live_authorized": LIVE_AUTHORIZED,
        "max_age_can_change_selection": MAX_AGE_CAN_CHANGE_SELECTION,
        "max_age_enforcement_enabled": MAX_AGE_ENFORCEMENT_ENABLED,
        "max_age_productive_gate": MAX_AGE_PRODUCTIVE_GATE,
        "max_age_role": MAX_AGE_ROLE,
        "metadata_equals_authority": METADATA_EQUALS_AUTHORITY,
        "order_effect": ORDER_EFFECT,
        "package_marker": PACKAGE_MARKER,
        "productive_caller_exists": PRODUCTIVE_CALLER_EXISTS,
        "registry_is_live_permission": REGISTRY_IS_LIVE_PERMISSION,
        "registry_semantic_digest": inventory["registry_semantic_digest"],
        "remediation_id": REMEDIATION_ID,
        "runtime_effect": RUNTIME_EFFECT,
        "second_identity_model_risk": "NONE_CANONICAL_RESOLVE_STRATEGY_ID",
        "second_selection_path_risk": "NONE_SUITABILITY_SELECT_PLUS_R2_NON_AUTHORITY",
        "second_strategy_registry_risk": "NONE_SRC_STRATEGIES_REGISTRY_ONLY",
        "silent_authority_promotion": SILENT_AUTHORITY_PROMOTION,
        "strategy_count": inventory["strategy_count"],
        "suitability_adapter_owner": SUITABILITY_ADAPTER_OWNER,
        "suitability_owner": SUITABILITY_OWNER,
        "suitability_selection_owner": SUITABILITY_SELECTION_OWNER,
        "suitability_snapshot_digest": selection["suitability_snapshot_digest"],
        "testnet_authorized": TESTNET_AUTHORIZED,
        "trading_grant": TRADING_GRANT,
        "verdict": "PASS_R2_STRATEGY_REGISTRY_SUITABILITY_SELECTION_V1",
    }
    return MappingProxyType(claims)
