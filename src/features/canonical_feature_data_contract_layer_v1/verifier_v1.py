"""Fail-closed verifier for R1/UQ6 Feature/Data Contract Layer v1."""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from src.features.canonical_feature_data_contract_layer_v1.catalog_v1 import (
    FEATURE_CATALOG,
    require_complete_uq6_catalog,
)
from src.features.canonical_feature_data_contract_layer_v1.constants_v1 import (
    ACTIVATED,
    AUTHORITY_EFFECT,
    CANARY_EXECUTE,
    CAPABILITY_ID,
    CONTRACT_ID,
    CONTRACT_OWNER,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    I03_CONTRACT_ROLE,
    I03_ENGINE_ROLE,
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
    NUMERIC_MAX_AGE_EFFECT,
    ORDER_EFFECT,
    PACKAGE_MARKER,
    PLACEHOLDER_SRC_FEATURES_DISPOSABLE,
    PRODUCTIVE_CALLER_EXISTS,
    REMEDIATION_ID,
    RUNTIME_EFFECT,
    SOURCE_GAP_IDS,
    STAGING_ORDER,
    TESTNET_AUTHORIZED,
    VOLATILITY_NUMERIC_MAX_AGE_ENFORCING,
)
from src.features.canonical_feature_data_contract_layer_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.features.canonical_feature_data_contract_layer_v1.models_v1 import (
    ConsumerIntent,
    FeatureDataContractLayerError,
)
from src.features.canonical_feature_data_contract_layer_v1.selective_engine_v1 import (
    engine_status_v1,
    run_selective_engine_v1,
)

_FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "src.execution",
        "src.execution_simple",
        "src.orders",
        "src.live",
    }
)


def _reject(message: str) -> None:
    raise FeatureDataContractLayerError(message)


def _require(payload: Mapping[str, Any], key: str, expected: Any) -> None:
    actual = payload.get(key)
    if actual != expected:
        _reject(f"config_field_mismatch:{key}:expected={expected!r}:actual={actual!r}")


def assert_placeholder_retained_v1(root: Path | None = None) -> None:
    path = (root or repo_root()) / "src" / "features" / "__init__.py"
    text = path.read_text(encoding="utf-8")
    if "Placeholder" not in text and "placeholder" not in text:
        _reject("src_features_placeholder_missing")
    if PLACEHOLDER_SRC_FEATURES_DISPOSABLE is not False:
        _reject("placeholder_marked_disposable")


def assert_engine_modules_have_no_execution_imports_v1(root: Path | None = None) -> None:
    package = (
        (root or repo_root()) / "src" / "features" / "canonical_feature_data_contract_layer_v1"
    )
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


def validate_layer_config_v1(payload: Mapping[str, Any]) -> None:
    _require(payload, "activated", False)
    _require(payload, "authority_effect", AUTHORITY_EFFECT)
    _require(payload, "canary_execute", False)
    _require(payload, "capability_id", CAPABILITY_ID)
    _require(payload, "contract_id", CONTRACT_ID)
    _require(payload, "contract_owner", CONTRACT_OWNER)
    _require(payload, "contract_version", CONTRACT_VERSION)
    _require(payload, "core_logic_change", CORE_LOGIC_CHANGE)
    _require(payload, "i03_contract_role", I03_CONTRACT_ROLE)
    _require(payload, "i03_engine_role", I03_ENGINE_ROLE)
    _require(payload, "live_authorized", False)
    _require(payload, "order_effect", False)
    _require(payload, "package_marker", PACKAGE_MARKER)
    _require(payload, "placeholder_src_features_disposable", False)
    _require(payload, "productive_caller_exists", PRODUCTIVE_CALLER_EXISTS)
    _require(payload, "remediation_id", REMEDIATION_ID)
    _require(payload, "runtime_effect", RUNTIME_EFFECT)
    _require(payload, "source_gap_ids", list(SOURCE_GAP_IDS))
    _require(payload, "staging_order", list(STAGING_ORDER))
    _require(payload, "testnet_authorized", False)
    _require(payload, "max_age_role", MAX_AGE_ROLE)
    _require(payload, "max_age_enforcement_enabled", MAX_AGE_ENFORCEMENT_ENABLED)
    _require(payload, "max_age_can_block_trading", MAX_AGE_CAN_BLOCK_TRADING)
    _require(payload, "max_age_can_block_canary", MAX_AGE_CAN_BLOCK_CANARY)
    _require(payload, "max_age_can_change_selection", MAX_AGE_CAN_CHANGE_SELECTION)
    _require(payload, "max_age_can_change_risk_decisions", MAX_AGE_CAN_CHANGE_RISK_DECISIONS)
    _require(payload, "max_age_can_change_execution", MAX_AGE_CAN_CHANGE_EXECUTION)
    _require(payload, "max_age_can_change_promotion", MAX_AGE_CAN_CHANGE_PROMOTION)
    _require(payload, "max_age_productive_gate", MAX_AGE_PRODUCTIVE_GATE)
    _require(payload, "max_age_allowed_uses", list(MAX_AGE_ALLOWED_USES))
    _require(payload, "volatility_numeric_max_age_enforcing", False)
    _require(payload, "volatility_numeric_max_age_effect", NUMERIC_MAX_AGE_EFFECT)


def evaluate_r1_uq6_v1(*, root: Path | None = None) -> Mapping[str, Any]:
    require_complete_uq6_catalog()
    payload = load_layer_config_v1(root)
    validate_layer_config_v1(payload)
    assert_placeholder_retained_v1(root)
    assert_engine_modules_have_no_execution_imports_v1(root)
    status = engine_status_v1()
    i25 = run_selective_engine_v1(
        feature_id="I25_VOLATILITY_ESTIMATE",
        intent=ConsumerIntent.NORMALIZE,
    )
    cmc = run_selective_engine_v1(
        feature_id="CMC_MARKET_CONTEXT_FEATURE_CONTRACT",
        intent=ConsumerIntent.NORMALIZE,
    )
    if i25.trading_authority or cmc.trading_authority:
        _reject("normalized_record_claimed_trading_authority")
    if i25.runtime_effect or cmc.runtime_effect:
        _reject("normalized_record_runtime_effect")
    claims = {
        "activated": ACTIVATED,
        "authority_effect": AUTHORITY_EFFECT,
        "canary_execute": CANARY_EXECUTE,
        "capability_id": CAPABILITY_ID,
        "catalog_size": len(FEATURE_CATALOG),
        "cmc_lineage_sha256": cmc.lineage_sha256,
        "config_digest": digest_mapping(payload),
        "core_logic_change": CORE_LOGIC_CHANGE,
        "eg_i03_classc_contracts_specified": True,
        "embedded_ta_equivalent_to_contract_layer": False,
        "i25_lineage_sha256": i25.lineage_sha256,
        "ig_i03_engine_selective_inactive": True,
        "live_authorized": LIVE_AUTHORIZED,
        "order_effect": ORDER_EFFECT,
        "package_marker": PACKAGE_MARKER,
        "productive_caller_exists": PRODUCTIVE_CALLER_EXISTS,
        "remediation_id": REMEDIATION_ID,
        "runtime_effect": RUNTIME_EFFECT,
        "selective_engine_status": dict(status),
        "ssot_bypass": False,
        "testnet_authorized": TESTNET_AUTHORIZED,
        "verdict": "PASS_R1_UQ6_FEATURE_DATA_CONTRACT_LAYER_V1",
        "volatility_numeric_max_age_effect": NUMERIC_MAX_AGE_EFFECT,
        "volatility_numeric_max_age_enforcing": VOLATILITY_NUMERIC_MAX_AGE_ENFORCING,
        "max_age_role": MAX_AGE_ROLE,
        "max_age_enforcement_enabled": MAX_AGE_ENFORCEMENT_ENABLED,
        "max_age_can_block_trading": MAX_AGE_CAN_BLOCK_TRADING,
        "max_age_can_block_canary": MAX_AGE_CAN_BLOCK_CANARY,
        "max_age_can_change_selection": MAX_AGE_CAN_CHANGE_SELECTION,
        "max_age_can_change_risk_decisions": MAX_AGE_CAN_CHANGE_RISK_DECISIONS,
        "max_age_can_change_execution": MAX_AGE_CAN_CHANGE_EXECUTION,
        "max_age_can_change_promotion": MAX_AGE_CAN_CHANGE_PROMOTION,
        "max_age_productive_gate": MAX_AGE_PRODUCTIVE_GATE,
    }
    return MappingProxyType(claims)
