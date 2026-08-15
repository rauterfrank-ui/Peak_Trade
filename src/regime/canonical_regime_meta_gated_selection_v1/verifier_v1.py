"""Fail-closed verifier for R3 Regime/Meta gated selection v1."""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from src.regime.canonical_regime_meta_gated_selection_v1.constants_v1 import (
    ACTIVATED,
    AUTHORITY_EFFECT,
    CANARY_EXECUTE,
    CAPABILITY_ID,
    CONTRACT_ID,
    CONTRACT_OWNER,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    DONE_CRITERION,
    GATE_OWNER,
    LIVE_AUTHORIZED,
    MAX_AGE_ALLOWED_USES,
    MAX_AGE_CAN_CHANGE_SELECTION,
    MAX_AGE_ENFORCEMENT_ENABLED,
    MAX_AGE_PRODUCTIVE_GATE,
    MAX_AGE_ROLE,
    ORDER_EFFECT,
    PACKAGE_MARKER,
    PRODUCTIVE_CALLER_EXISTS,
    PROMOTION_AUTHORITY,
    R2_CATALOG_SELECTION_OWNER,
    R2_IDENTITY_OWNER,
    R2_REGISTRY_OWNER,
    RAW_LLM_TRADING_AUTHORITY,
    REGIME_LABEL_OWNER,
    REGIME_RESEARCH_SWITCH_ROLE,
    REMEDIATION_ID,
    RUNTIME_AUTHORITY_IMPACT,
    RUNTIME_EFFECT,
    SILENT_THRESHOLD_MUTATION,
    SOURCE_GAP_IDS,
    SUITABILITY_SELECTION_OWNER,
    TESTNET_AUTHORIZED,
    TRADING_GRANT,
)
from src.regime.canonical_regime_meta_gated_selection_v1.gate_v1 import (
    apply_regime_meta_gate_v1,
)
from src.regime.canonical_regime_meta_gated_selection_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.regime.canonical_regime_meta_gated_selection_v1.models_v1 import (
    GateIntent,
    RegimeMetaGateInputV1,
    RegimeMetaGatedSelectionError,
    SourceClass,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.constants_v1 import (
    CATALOG_OWNER as R2_CATALOG_OWNER_CONST,
    IDENTITY_OWNER as R2_IDENTITY_OWNER_CONST,
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
    }
)
_PACKAGE_REL = Path("src") / "regime" / "canonical_regime_meta_gated_selection_v1"
_CANONICAL_REGISTRY_REL = Path("src") / "strategies" / "registry.py"
_AUTHORIZED_STRATEGY_SELECTORS = frozenset(
    {
        "select_strategy_deterministic",
        "select_registered_strategies_v1",
    }
)


def _reject(message: str) -> None:
    raise RegimeMetaGatedSelectionError(message)


def _require(payload: Mapping[str, Any], key: str, expected: Any) -> None:
    actual = payload.get(key)
    if actual != expected:
        _reject(f"config_field_mismatch:{key}:expected={expected!r}:actual={actual!r}")


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
    _require(payload, "live_authorized", False)
    _require(payload, "max_age_allowed_uses", list(MAX_AGE_ALLOWED_USES))
    _require(payload, "max_age_can_change_selection", False)
    _require(payload, "max_age_enforcement_enabled", False)
    _require(payload, "max_age_productive_gate", False)
    _require(payload, "max_age_role", MAX_AGE_ROLE)
    _require(payload, "network_effect", False)
    _require(payload, "order_effect", False)
    _require(payload, "package_marker", PACKAGE_MARKER)
    _require(payload, "productive_caller_exists", False)
    _require(payload, "promotion_authority", False)
    _require(payload, "raw_llm_trading_authority", RAW_LLM_TRADING_AUTHORITY)
    _require(payload, "remediation_id", REMEDIATION_ID)
    _require(payload, "runtime_authority_impact", RUNTIME_AUTHORITY_IMPACT)
    _require(payload, "runtime_effect", False)
    _require(payload, "silent_threshold_mutation", False)
    _require(payload, "source_gap_ids", list(SOURCE_GAP_IDS))
    _require(payload, "testnet_authorized", False)
    _require(payload, "trading_grant", False)
    if not isinstance(payload.get("regime_candidate_mapping"), dict):
        _reject("regime_candidate_mapping_missing")
    if not payload.get("mapping_version"):
        _reject("mapping_version_missing")


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
                if name.startswith("src.regime.switching"):
                    _reject(f"research_switch_imported_as_authority:{path.name}:{name}")
                if name.startswith("src.ai.regimes") or name.startswith("src.meta.infostream"):
                    _reject(f"advisory_imported_as_gate:{path.name}:{name}")


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


def assert_gate_deterministic_and_non_authority_v1(
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    inp = RegimeMetaGateInputV1(
        candidate_ids=("ma_crossover", "rsi_reversion", "trend_following"),
        regime_id="trending",
        source_class=SourceClass.REGIME_CONTEXT,
        intent=GateIntent.APPLY_GATED_CONTEXT,
        meta_context=MappingProxyType({"note": "r3_verifier"}),
        mapping_version=str(payload["mapping_version"]),
    )
    first = apply_regime_meta_gate_v1(inp, config=payload)
    second = apply_regime_meta_gate_v1(inp, config=payload)
    if first.result_digest != second.result_digest:
        _reject("gate_nondeterministic")
    if first.trading_grant or first.promotion_authority:
        _reject("gate_granted_trading_or_promotion")
    if first.selected_strategy_id is not None:
        _reject("gate_selected_strategy")
    if first.runtime_authority_impact != "NONE":
        _reject("runtime_authority_impact_not_none")
    if first.max_age_consulted or first.silent_threshold_mutation:
        _reject("max_age_or_threshold_mutation")
    if not first.adjustment_applied:
        _reject("expected_regime_adjustment")
    llm = apply_regime_meta_gate_v1(
        RegimeMetaGateInputV1(
            candidate_ids=("ma_crossover", "rsi_reversion"),
            regime_id="UP",
            source_class=SourceClass.ADVISORY_LLM_CONTEXT,
            intent=GateIntent.ADVISORY_RECORD_ONLY,
            meta_context=MappingProxyType({"advisory_text": "non_authority"}),
            mapping_version=str(payload["mapping_version"]),
        ),
        config=payload,
    )
    if llm.adjustment_applied or llm.trading_grant:
        _reject("llm_context_adjusted_or_granted")
    if llm.raw_llm_trading_authority != RAW_LLM_TRADING_AUTHORITY:
        _reject("llm_trading_authority_not_permanent_non_authority")
    return MappingProxyType(
        {
            "gate_result_digest": first.result_digest,
            "identity_digest": first.identity_digest,
            "mapping_digest": first.mapping_digest,
        }
    )


def evaluate_r3_regime_meta_gated_selection_v1(*, root: Path | None = None) -> Mapping[str, Any]:
    payload = load_layer_config_v1(root)
    validate_layer_config_v1(payload)
    assert_package_has_no_execution_imports_v1(root)
    assert_no_second_strategy_registry_v1(root)
    assert_no_second_authorized_selection_path_v1(root)
    r2 = evaluate_r2_registry_suitability_selection_v1(root=root)
    if r2["verdict"] != "PASS_R2_STRATEGY_REGISTRY_SUITABILITY_SELECTION_V1":
        _reject("r2_regression")
    if R2_IDENTITY_OWNER_CONST != R2_IDENTITY_OWNER:
        _reject("identity_owner_drift")
    if R2_CATALOG_OWNER_CONST != R2_REGISTRY_OWNER:
        _reject("registry_owner_drift")
    gate = assert_gate_deterministic_and_non_authority_v1(payload)
    claims = {
        "activated": ACTIVATED,
        "authority_effect": AUTHORITY_EFFECT,
        "canary_execute": CANARY_EXECUTE,
        "capability_id": CAPABILITY_ID,
        "config_digest": digest_mapping(payload),
        "core_logic_change": CORE_LOGIC_CHANGE,
        "done_criterion": DONE_CRITERION,
        "gate_owner": GATE_OWNER,
        "gate_result_digest": gate["gate_result_digest"],
        "identity_digest": gate["identity_digest"],
        "live_authorized": LIVE_AUTHORIZED,
        "mapping_digest": gate["mapping_digest"],
        "max_age_can_change_selection": MAX_AGE_CAN_CHANGE_SELECTION,
        "max_age_enforcement_enabled": MAX_AGE_ENFORCEMENT_ENABLED,
        "max_age_productive_gate": MAX_AGE_PRODUCTIVE_GATE,
        "max_age_role": MAX_AGE_ROLE,
        "order_effect": ORDER_EFFECT,
        "package_marker": PACKAGE_MARKER,
        "productive_caller_exists": PRODUCTIVE_CALLER_EXISTS,
        "promotion_authority": PROMOTION_AUTHORITY,
        "r2_catalog_selection_owner": R2_CATALOG_SELECTION_OWNER,
        "r2_identity_owner": R2_IDENTITY_OWNER,
        "r2_registry_owner": R2_REGISTRY_OWNER,
        "r2_verdict": r2["verdict"],
        "raw_llm_trading_authority": RAW_LLM_TRADING_AUTHORITY,
        "regime_label_owner": REGIME_LABEL_OWNER,
        "regime_research_switch_role": REGIME_RESEARCH_SWITCH_ROLE,
        "remediation_id": REMEDIATION_ID,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "runtime_effect": RUNTIME_EFFECT,
        "second_regime_meta_authority_risk": "NONE_R3_GATE_ONLY_RESEARCH_SWITCH_NON_AUTHORITY",
        "second_selection_path_risk": "NONE_SUITABILITY_SELECT_PLUS_R2_NON_AUTHORITY",
        "second_strategy_registry_risk": "NONE_SRC_STRATEGIES_REGISTRY_ONLY",
        "silent_threshold_mutation": SILENT_THRESHOLD_MUTATION,
        "suitability_selection_owner": SUITABILITY_SELECTION_OWNER,
        "testnet_authorized": TESTNET_AUTHORIZED,
        "trading_grant": TRADING_GRANT,
        "verdict": "PASS_R3_REGIME_META_GATED_SELECTION_V1",
    }
    return MappingProxyType(claims)
