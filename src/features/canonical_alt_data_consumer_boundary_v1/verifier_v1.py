"""Fail-closed read-only verifier for EG-ALT-CONSUMER consumer matrix v1."""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from src.features.canonical_alt_data_consumer_boundary_v1.constants_v1 import (
    ACTIVATED,
    ALT_DATA_PRESENCE_IS_PROMOTION_ELIGIBILITY,
    ALT_DATA_PRESENCE_IS_REGIME_AUTHORITY,
    ALT_DATA_PRESENCE_IS_STRATEGY_ELIGIBILITY,
    ALT_DATA_PRESENCE_IS_TRADING_AUTHORITY,
    AUTHORITY_EFFECT,
    CANARY_EXECUTE,
    CAPABILITY_ID,
    CONSUMER_WIRING_PRESENT,
    CONTRACT_ID,
    CONTRACT_OWNER,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    CURRENT_BOUND_ROLE,
    DASHBOARD_AUTHORITY,
    DIRECT_RESEARCH_TO_INTENT_PATH,
    DIRECT_RESEARCH_TO_ORDER_PATH,
    DONE_CRITERION,
    G14_NON_AUTHORITATIVE_UNTIL_PROMOTION,
    I04_FEATURE_ID,
    I05_EXECUTION_AUTHORITY,
    I05_FEATURE_ID,
    I55_ALLOWED_IMPORT_RELPATHS,
    I55_CURRENT_TOML_PATH,
    I55_FEATURE_ID,
    I55_PRODUCER_PATH,
    I55_REPLACES_DOUBLE_PLAY,
    I55_REPLACES_MASTER_V2,
    I55_REPLACES_R3,
    I55_SCHEMA_PATH,
    LLM_TRADING_AUTHORITY,
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
    NETWORK_EFFECT,
    ORDER_EFFECT,
    PACKAGE_MARKER,
    PRODUCTIVE_CALLER_EXISTS,
    R1_FEATURE_OWNER,
    R2_REGISTRY_OWNER,
    R2_SUITABILITY_OWNER,
    R3_REGIME_LABEL_OWNER,
    R3_REGIME_META_OWNER,
    REMEDIATION_ID,
    RUNTIME_AUTHORITY_IMPACT,
    RUNTIME_AUTHORIZATION_EFFECT,
    RUNTIME_EFFECT,
    SOURCE_GAP_IDS,
    SOURCE_INTENTS,
    TARGET_BINDING,
    TESTNET_AUTHORIZED,
    UNKNOWN_PRODUCER_DIRS,
    UNKNOWN_PRODUCER_PACKAGES,
)
from src.features.canonical_alt_data_consumer_boundary_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.features.canonical_alt_data_consumer_boundary_v1.matrix_v1 import (
    CONSUMER_MATRIX,
    PRIMARY_ROW_IDS,
    primary_rows,
    require_consumer,
    require_producer,
    require_row,
    require_schema,
)
from src.features.canonical_alt_data_consumer_boundary_v1.models_v1 import (
    AltDataConsumerBoundaryError,
    PathClass,
)
from src.features.canonical_feature_data_contract_layer_v1.catalog_v1 import catalog_entry
from src.features.canonical_feature_data_contract_layer_v1.constants_v1 import (
    ALT_DATA_CORE_CONSUMER_ALLOWED,
    RESEARCH_FEEDER_IDS,
)
from src.features.canonical_feature_data_contract_layer_v1.models_v1 import (
    AuthorityClass,
    ConsumerIntent,
    FeatureDataContractLayerError,
)
from src.features.canonical_feature_data_contract_layer_v1.selective_engine_v1 import (
    run_selective_engine_v1,
)
from src.features.canonical_feature_data_contract_layer_v1.verifier_v1 import (
    evaluate_r1_uq6_v1,
)
from src.regime.canonical_regime_meta_gated_selection_v1.verifier_v1 import (
    evaluate_r3_regime_meta_gated_selection_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.verifier_v1 import (
    evaluate_r2_registry_suitability_selection_v1,
)

_FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "src.execution",
        "src.execution_simple",
        "src.orders",
        "src.live",
        "src.intents",
    }
)
_PACKAGE_REL = Path("src") / "features" / "canonical_alt_data_consumer_boundary_v1"
_I55_IMPORT_ROOTS = ("src.macro_regimes",)
_FEATURE_IDS = (I04_FEATURE_ID, I05_FEATURE_ID, I55_FEATURE_ID)


def _reject(message: str) -> None:
    raise AltDataConsumerBoundaryError(message)


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


def assert_package_has_no_intent_or_order_imports_v1(root: Path | None = None) -> None:
    package = (root or repo_root()) / _PACKAGE_REL
    for path in sorted(package.glob("*.py")):
        for name in _iter_import_names(path):
            for forbidden in _FORBIDDEN_IMPORT_ROOTS:
                if name == forbidden or name.startswith(f"{forbidden}."):
                    _reject(f"forbidden_import:{path.name}:{name}")


def assert_unknown_producer_packages_absent_v1(root: Path | None = None) -> None:
    base = root or repo_root()
    for rel in UNKNOWN_PRODUCER_DIRS:
        if (base / rel).exists():
            _reject(f"unknown_producer_dir:{rel}")
    src_root = base / "src"
    for path in sorted(src_root.rglob("*.py")):
        rel = path.relative_to(base).as_posix()
        if rel.startswith(_PACKAGE_REL.as_posix() + "/"):
            continue
        for name in _iter_import_names(path):
            for forbidden in UNKNOWN_PRODUCER_PACKAGES:
                if name == forbidden or name.startswith(f"{forbidden}."):
                    _reject(f"unknown_producer_import:{rel}:{name}")


def assert_i55_loader_not_imported_by_authority_trees_v1(root: Path | None = None) -> None:
    base = root or repo_root()
    allowed = frozenset(I55_ALLOWED_IMPORT_RELPATHS)
    src_root = base / "src"
    hits: list[str] = []
    for path in sorted(src_root.rglob("*.py")):
        rel = path.relative_to(base).as_posix()
        if rel in allowed:
            continue
        if rel.startswith(_PACKAGE_REL.as_posix() + "/"):
            continue
        for name in _iter_import_names(path):
            for root_name in _I55_IMPORT_ROOTS:
                if name == root_name or name.startswith(f"{root_name}."):
                    hits.append(f"{rel}:{name}")
    if hits:
        _reject(f"i55_authority_or_runtime_consumer:{hits}")


def assert_i55_briefing_files_exist_v1(root: Path | None = None) -> None:
    base = root or repo_root()
    for rel in (I55_PRODUCER_PATH, I55_SCHEMA_PATH, I55_CURRENT_TOML_PATH):
        if not (base / rel).is_file():
            _reject(f"i55_producer_artifact_missing:{rel}")


def assert_r1_research_feeder_rights_v1() -> None:
    if ALT_DATA_CORE_CONSUMER_ALLOWED is not False:
        _reject("alt_data_core_consumer_allowed")
    for feature_id in _FEATURE_IDS:
        if feature_id not in RESEARCH_FEEDER_IDS:
            _reject(f"r1_research_feeder_missing:{feature_id}")
        entry = catalog_entry(feature_id)
        if entry.authority_class is not AuthorityClass.RESEARCH_FEEDER:
            _reject(f"r1_authority_class_drift:{feature_id}")
        rights = entry.consumer_rights
        if any(
            (
                rights.core_decision,
                rights.suitability,
                rights.promotion,
                rights.regime_classifier,
                rights.dashboard_authority,
                rights.execution_authority,
            )
        ):
            _reject(f"r1_feeder_claimed_consumer_rights:{feature_id}")
        try:
            run_selective_engine_v1(feature_id=feature_id, intent=ConsumerIntent.SUITABILITY)
        except FeatureDataContractLayerError:
            continue
        _reject(f"r1_suitability_intent_not_fail_closed:{feature_id}")


def assert_primary_rows_keep_research_feeder_v1() -> None:
    for row in primary_rows():
        if row.path_class is not PathClass.RESEARCH_FEEDER_VALID_NO_CANONICAL_CONSUMER_REQUIRED_YET:
            _reject(f"primary_path_class_not_b:{row.row_id}:{row.path_class.value}")
        if row.recommended_target_binding != TARGET_BINDING:
            _reject(f"primary_target_binding_drift:{row.row_id}")
        if row.missing_contract:
            _reject(f"missing_contract_false_gap:{row.row_id}")
        if row.r2_suitability_consumer_present or row.r3_meta_consumer_present:
            _reject(f"canonical_consumer_claimed:{row.row_id}")
        if row.promotion_consumer_present:
            _reject(f"promotion_consumer_claimed:{row.row_id}")
        if row.current_runtime_reachable:
            _reject(f"runtime_reachable:{row.row_id}")
        if row.current_authority_effect != "NONE":
            _reject(f"authority_effect_claimed:{row.row_id}")
        if row.source_intent not in SOURCE_INTENTS:
            _reject(f"unknown_source_intent:{row.source_intent}")


def validate_layer_config_v1(payload: Mapping[str, Any]) -> None:
    _require(payload, "activated", False)
    _require(payload, "authority_effect", AUTHORITY_EFFECT)
    _require(payload, "canary_execute", False)
    _require(payload, "capability_id", CAPABILITY_ID)
    _require(payload, "consumer_wiring_present", False)
    _require(payload, "contract_id", CONTRACT_ID)
    _require(payload, "contract_owner", CONTRACT_OWNER)
    _require(payload, "contract_version", CONTRACT_VERSION)
    _require(payload, "core_logic_change", CORE_LOGIC_CHANGE)
    _require(payload, "current_bound_role", CURRENT_BOUND_ROLE)
    _require(payload, "dashboard_authority", False)
    _require(payload, "direct_research_to_intent_path", False)
    _require(payload, "direct_research_to_order_path", False)
    _require(payload, "done_criterion", DONE_CRITERION)
    _require(payload, "g14_non_authoritative_until_promotion", True)
    _require(payload, "i05_execution_authority", False)
    _require(payload, "i55_replaces_double_play", False)
    _require(payload, "i55_replaces_master_v2", False)
    _require(payload, "i55_replaces_r3", False)
    _require(payload, "live_authorized", False)
    _require(payload, "llm_trading_authority", LLM_TRADING_AUTHORITY)
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
    _require(payload, "network_effect", False)
    _require(payload, "order_effect", False)
    _require(payload, "package_marker", PACKAGE_MARKER)
    _require(payload, "productive_caller_exists", False)
    _require(payload, "r1_feature_owner", R1_FEATURE_OWNER)
    _require(payload, "r2_registry_owner", R2_REGISTRY_OWNER)
    _require(payload, "r2_suitability_owner", R2_SUITABILITY_OWNER)
    _require(payload, "r3_regime_label_owner", R3_REGIME_LABEL_OWNER)
    _require(payload, "r3_regime_meta_owner", R3_REGIME_META_OWNER)
    _require(payload, "remediation_id", REMEDIATION_ID)
    _require(payload, "runtime_authority_impact", RUNTIME_AUTHORITY_IMPACT)
    _require(payload, "runtime_authorization_effect", RUNTIME_AUTHORIZATION_EFFECT)
    _require(payload, "runtime_effect", False)
    _require(payload, "source_gap_ids", list(SOURCE_GAP_IDS))
    _require(payload, "source_intents", list(SOURCE_INTENTS))
    _require(payload, "target_binding", TARGET_BINDING)
    _require(payload, "testnet_authorized", False)
    _require(payload, "alt_data_presence_is_promotion_eligibility", False)
    _require(payload, "alt_data_presence_is_regime_authority", False)
    _require(payload, "alt_data_presence_is_strategy_eligibility", False)
    _require(payload, "alt_data_presence_is_trading_authority", False)


def evaluate_eg_alt_consumer_v1(*, root: Path | None = None) -> Mapping[str, Any]:
    payload = load_layer_config_v1(root)
    validate_layer_config_v1(payload)
    assert_package_has_no_intent_or_order_imports_v1(root)
    assert_unknown_producer_packages_absent_v1(root)
    assert_i55_briefing_files_exist_v1(root)
    assert_i55_loader_not_imported_by_authority_trees_v1(root)
    assert_r1_research_feeder_rights_v1()
    assert_primary_rows_keep_research_feeder_v1()
    for row in CONSUMER_MATRIX:
        require_row(row.row_id)
        require_producer(row.producer)
        require_schema(row.output_schema)
        require_consumer(row.current_consumer)
    r1 = evaluate_r1_uq6_v1(root=root)
    r2 = evaluate_r2_registry_suitability_selection_v1(root=root)
    r3 = evaluate_r3_regime_meta_gated_selection_v1(root=root)
    if r1["verdict"] != "PASS_R1_UQ6_FEATURE_DATA_CONTRACT_LAYER_V1":
        _reject(f"r1_regression:{r1['verdict']}")
    if r2["verdict"] != "PASS_R2_STRATEGY_REGISTRY_SUITABILITY_SELECTION_V1":
        _reject(f"r2_regression:{r2['verdict']}")
    if r3["verdict"] != "PASS_R3_REGIME_META_GATED_SELECTION_V1":
        _reject(f"r3_regression:{r3['verdict']}")
    if any(
        (
            ACTIVATED,
            CONSUMER_WIRING_PRESENT,
            PRODUCTIVE_CALLER_EXISTS,
            DIRECT_RESEARCH_TO_INTENT_PATH,
            DIRECT_RESEARCH_TO_ORDER_PATH,
            ALT_DATA_PRESENCE_IS_STRATEGY_ELIGIBILITY,
            ALT_DATA_PRESENCE_IS_REGIME_AUTHORITY,
            ALT_DATA_PRESENCE_IS_PROMOTION_ELIGIBILITY,
            ALT_DATA_PRESENCE_IS_TRADING_AUTHORITY,
            I05_EXECUTION_AUTHORITY,
            I55_REPLACES_R3,
            I55_REPLACES_MASTER_V2,
            I55_REPLACES_DOUBLE_PLAY,
            DASHBOARD_AUTHORITY,
            LIVE_AUTHORIZED,
            TESTNET_AUTHORIZED,
            CANARY_EXECUTE,
            NETWORK_EFFECT,
            ORDER_EFFECT,
            MAX_AGE_ENFORCEMENT_ENABLED,
            MAX_AGE_PRODUCTIVE_GATE,
        )
    ):
        _reject("authority_or_activation_flag_raised")
    claims = {
        "activated": ACTIVATED,
        "authority_effect": AUTHORITY_EFFECT,
        "canary_execute": CANARY_EXECUTE,
        "capability_id": CAPABILITY_ID,
        "config_digest": digest_mapping(payload),
        "consumer_matrix_complete": True,
        "consumer_wiring_present": CONSUMER_WIRING_PRESENT,
        "core_logic_change": CORE_LOGIC_CHANGE,
        "current_bound_role": CURRENT_BOUND_ROLE,
        "dashboard_authority": DASHBOARD_AUTHORITY,
        "direct_research_to_intent_path": DIRECT_RESEARCH_TO_INTENT_PATH,
        "direct_research_to_order_path": DIRECT_RESEARCH_TO_ORDER_PATH,
        "done_criterion": DONE_CRITERION,
        "eg_alt_consumer_status": "CLOSED_PROVEN_FORENSIC",
        "g14_non_authoritative_until_promotion": G14_NON_AUTHORITATIVE_UNTIL_PROMOTION,
        "i04_path_class": require_row("I04_PRIMARY").path_class.value,
        "i05_execution_authority": I05_EXECUTION_AUTHORITY,
        "i05_path_class": require_row("I05_PRIMARY").path_class.value,
        "i55_path_class": require_row("I55_PRIMARY").path_class.value,
        "i55_replaces_double_play": I55_REPLACES_DOUBLE_PLAY,
        "i55_replaces_master_v2": I55_REPLACES_MASTER_V2,
        "i55_replaces_r3": I55_REPLACES_R3,
        "implementation_required": False,
        "live_authorized": LIVE_AUTHORIZED,
        "llm_trading_authority": LLM_TRADING_AUTHORITY,
        "matrix_row_ids": list(PRIMARY_ROW_IDS)
        + [row.row_id for row in CONSUMER_MATRIX if row.row_id not in PRIMARY_ROW_IDS],
        "max_age_can_block_canary": MAX_AGE_CAN_BLOCK_CANARY,
        "max_age_can_block_trading": MAX_AGE_CAN_BLOCK_TRADING,
        "max_age_can_change_execution": MAX_AGE_CAN_CHANGE_EXECUTION,
        "max_age_can_change_promotion": MAX_AGE_CAN_CHANGE_PROMOTION,
        "max_age_can_change_risk_decisions": MAX_AGE_CAN_CHANGE_RISK_DECISIONS,
        "max_age_can_change_selection": MAX_AGE_CAN_CHANGE_SELECTION,
        "max_age_enforcement_enabled": MAX_AGE_ENFORCEMENT_ENABLED,
        "max_age_productive_gate": MAX_AGE_PRODUCTIVE_GATE,
        "max_age_role": MAX_AGE_ROLE,
        "order_effect": ORDER_EFFECT,
        "package_marker": PACKAGE_MARKER,
        "path_class_all_primary": PathClass.RESEARCH_FEEDER_VALID_NO_CANONICAL_CONSUMER_REQUIRED_YET.value,
        "productive_caller_exists": PRODUCTIVE_CALLER_EXISTS,
        "r1_verdict": r1["verdict"],
        "r2_verdict": r2["verdict"],
        "r3_verdict": r3["verdict"],
        "remediation_id": REMEDIATION_ID,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "runtime_effect": RUNTIME_EFFECT,
        "second_feature_owner_risk": "NONE_R1_CATALOG_ONLY",
        "second_regime_meta_owner_risk": "NONE_R3_GATE_ONLY",
        "second_selection_owner_risk": "NONE_R2_SELECTION_ONLY",
        "second_suitability_owner_risk": "NONE_R2_SUITABILITY_ONLY",
        "source_intents": list(SOURCE_INTENTS),
        "target_binding": TARGET_BINDING,
        "testnet_authorized": TESTNET_AUTHORIZED,
        "verdict": "PASS_EG_ALT_CONSUMER_BOUNDARY_V1",
    }
    return MappingProxyType(claims)
