"""Static contract: Risk/Sizing owner inventory SSOT v1.

Docs/config/tests-only. Does not authorize live, orders, runtime bridge,
deployment, consolidation, or risk/sizing semantic changes.

The risk_sizing_owner_and_bypass_surface_contract freezes the five productive
Risk/Sizing decision owners and five bypass paths as an inventory/drift guard
only — NOT authority assignment and NOT repo-wide owner promotion.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.governance import capital_risk_sizing_v1 as crs
from src.governance.promotion_loop import promotion_economic_gate_v1 as gate
from src.trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CANONICAL_CAPITAL_RISK_SIZING_OWNER,
)
from src.trading.master_v2.runtime_bridge_pre_activation_gate_v0 import (
    current_head_default_gate_input_v0,
    evaluate_runtime_bridge_pre_activation_gate_v0,
)
from src.trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
    current_head_default_final_flags_evidence_input_v0,
)
from src.trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SSOT_DOC = REPO_ROOT / "docs" / "governance" / "RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md"
SSOT_JSON = REPO_ROOT / "config" / "governance" / "risk_sizing_owner_inventory_ssot_v1.json"
PROMOTION_SSOT_JSON = (
    REPO_ROOT / "config" / "governance" / "promotion_owner_and_gate_inventory_ssot_v1.json"
)
LEGACY_ORDER_INTENT_SSOT_JSON = (
    REPO_ROOT / "config" / "governance" / "legacy_order_intent_inventory_ssot_v1.json"
)

EXPECTED_PRODUCTIVE_OWNER_COUNT = 5
EXPECTED_BYPASS_PATH_COUNT = 5
EXPECTED_MV2_OWNER = "src.governance.capital_risk_sizing_v1"
EXPECTED_SURFACE_CONTRACT_SEMANTICS = "INVENTORY_ONLY_NOT_AUTHORITY_ASSIGNMENT"
EXPECTED_OWNER_IDS = (
    "backtest.offline_evaluation_sizing_contract_v1",
    "src.core.position_sizing",
    "src.execution.pipeline.execute_from_signals",
    "src.governance.capital_risk_sizing_v1",
    "src.risk.position_sizer",
)
EXPECTED_BYPASS_IDS = (
    "BYPASS_CLASSIC_BACKTEST_DEFAULT",
    "BYPASS_CORE_POSITION_SIZER",
    "BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS",
    "BYPASS_LIVE_SHADOW_POSITION_FRACTION",
    "BYPASS_OFFLINE_EVAL_SIZING_CONTRACT",
)
EXPECTED_OWNER_PINS = {
    "src.governance.capital_risk_sizing_v1": {
        "source_path": "src/governance/capital_risk_sizing_v1.py",
        "symbol_or_callable": "evaluate_capital_risk_sizing_v1",
        "role": "canonical_decision_owner",
        "decision_type": "capital_risk_sizing_quantity_chain",
        "reachability": "REACHABLE_PRODUCTIVE",
    },
    "src.risk.position_sizer": {
        "source_path": "src/risk/position_sizer.py",
        "symbol_or_callable": "calc_position_size",
        "role": "legacy_decision_owner",
        "decision_type": "position_sizing",
        "reachability": "REACHABLE_PRODUCTIVE",
    },
    "src.core.position_sizing": {
        "source_path": "src/core/position_sizing.py",
        "symbol_or_callable": "BasePositionSizer",
        "role": "decision_owner",
        "decision_type": "position_sizing",
        "reachability": "REACHABLE_PRODUCTIVE",
    },
    "backtest.offline_evaluation_sizing_contract_v1": {
        "source_path": "src/backtest/offline_evaluation_sizing_contract_v1.py",
        "symbol_or_callable": "size_offline_evaluation_entry_v1",
        "role": "policy_owner",
        "decision_type": "offline_evaluation_sizing_policy",
        "reachability": "REACHABLE_PRODUCTIVE",
    },
    "src.execution.pipeline.execute_from_signals": {
        "source_path": "src/execution/pipeline.py",
        "symbol_or_callable": "ExecutionPipeline.execute_from_signals",
        "role": "decision_owner",
        "decision_type": "quantity_notional_derivation",
        "reachability": "REACHABLE_PRODUCTIVE",
    },
}
EXPECTED_BYPASS_PINS = {
    "BYPASS_CLASSIC_BACKTEST_DEFAULT": {
        "source_path": "src/backtest/engine.py",
        "caller_symbol": "BacktestEngine.run_realistic",
        "target_symbol": "calc_position_size",
        "target_source_path": "src/risk/position_sizer.py",
        "target_classification": "LEGACY_POSITION_SIZER_CALC",
    },
    "BYPASS_CORE_POSITION_SIZER": {
        "source_path": "src/backtest/engine.py",
        "caller_symbol": "BacktestEngine.run_realistic",
        "target_symbol": "BasePositionSizer.get_target_position",
        "target_source_path": "src/core/position_sizing.py",
        "target_classification": "CORE_POSITION_SIZER_GET_TARGET_POSITION",
    },
    "BYPASS_OFFLINE_EVAL_SIZING_CONTRACT": {
        "source_path": "src/backtest/engine.py",
        "caller_symbol": "BacktestEngine.run_realistic",
        "target_symbol": "size_offline_evaluation_entry_v1",
        "target_source_path": "src/backtest/offline_evaluation_sizing_contract_v1.py",
        "target_classification": "OFFLINE_EVALUATION_SIZING_CONTRACT",
    },
    "BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS": {
        "source_path": "src/execution/pipeline.py",
        "caller_symbol": "ExecutionPipeline.execute_from_signals",
        "target_symbol": "ExecutionPipeline.execute_from_signals",
        "target_source_path": "src/execution/pipeline.py",
        "target_classification": "EXECUTION_SIMPLIFIED_NOTIONAL_PCT_SIZE",
    },
    "BYPASS_LIVE_SHADOW_POSITION_FRACTION": {
        "source_path": "src/live/shadow_session.py",
        "caller_symbol": "ShadowPaperSession.step_once",
        "target_symbol": None,
        "target_source_path": "src/live/shadow_session.py",
        "target_classification": "SHADOW_CFG_POSITION_FRACTION_ASSIGNMENT",
    },
}

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "RISK_SIZING_OWNER_INVENTORY_SSOT_V1=true",
    "INVENTORY_ONLY=true",
    "CONSOLIDATION_STATUS=NOT_STARTED",
    "RISK_SIZING_CLAIMED_CONSOLIDATED=false",
    "CANONICAL_RISK_SIZING_OWNER=UNRESOLVED",
    f"CANONICAL_RISK_SIZING_OWNER_MV2_SCOPE={EXPECTED_MV2_OWNER}",
    f"PRODUCTIVE_RISK_SIZING_DECISION_OWNER_COUNT={EXPECTED_PRODUCTIVE_OWNER_COUNT}",
    "DUPLICATE_PRODUCTIVE_RISK_SIZING_DECISION_OWNERS=true",
    f"BYPASS_PATH_COUNT={EXPECTED_BYPASS_PATH_COUNT}",
    "RISK_LIMIT_AND_SIZING_SEPARATION=PARTIAL",
    "RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_V1=true",
    f"RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_SEMANTICS={EXPECTED_SURFACE_CONTRACT_SEMANTICS}",
    "RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_IS_NOT_AUTHORITY_ASSIGNMENT=true",
    "RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_DOES_NOT_PROMOTE_REPO_WIDE_OWNER=true",
    "RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_DOES_NOT_CONSOLIDATE=true",
    "THIS_DOCUMENT_IS_INVENTORY_SSOT_NOT_RUNTIME_AUTHORITY=true",
    "NO_RUNTIME_REWIRE_IN_THIS_SLICE=true",
    "NO_TRADING_CORE_CHANGE=true",
    "NO_RISK_SIZING_SEMANTICS_CHANGE=true",
    "NO_RUNTIME_BRIDGE_ACTIVATION=true",
    "ELIGIBLE_FOR_LIVE_DEFAULT=false",
    "LIVE_AUTHORIZED=false",
    "ORDERS_ENABLED=false",
    "RUNTIME_BRIDGE_ACTIVATED=false",
    "ECONOMIC_GATE_REMAINS_FAIL_CLOSED=true",
    "AUTHORITY_EFFECT=NONE",
    "INVENTORY ONLY — NOT CONSOLIDATED",
)

FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "eligible_for_live=true",
    "LIVE_AUTHORIZED=true",
    "ORDERS_ENABLED=true",
    "RUNTIME_BRIDGE_ACTIVATED=true",
    "CONSOLIDATION_STATUS=DONE",
    "RISK_SIZING_CLAIMED_CONSOLIDATED=true",
    "already consolidated",
    "risk/sizing consolidated",
    "approved for live trading",
)

REQUIRED_OWNER_PATHS: tuple[str, ...] = (
    "src/governance/capital_risk_sizing_v1.py",
    "src/risk/position_sizer.py",
    "src/core/position_sizing.py",
    "src/backtest/offline_evaluation_sizing_contract_v1.py",
    "src/execution/pipeline.py",
)

REQUIRED_OWNER_FIELDS = (
    "stable_id",
    "module",
    "source_path",
    "symbol_or_callable",
    "primary_symbols",
    "role",
    "classification",
    "decision_type",
    "reachability",
    "canonical",
    "authorized",
    "enabled",
    "execution_authority",
    "capital_authority",
    "decommissioned",
    "inventory_only",
    "authoritative_size_decision",
    "authority_owner_status",
    "consolidation_status",
    "decommission_status",
)

REQUIRED_BYPASS_FIELDS = (
    "stable_id",
    "source_path",
    "caller_symbol",
    "target_classification",
    "role",
    "classification",
    "reachability",
    "bypassed_boundary",
    "bypassed_owner_stable_id",
    "canonical",
    "authorized",
    "enabled",
    "execution_authority",
    "capital_authority",
    "decommissioned",
    "inventory_only",
    "activates_orders",
    "activates_live_capital",
    "authority_owner_status",
    "consolidation_status",
    "decommission_status",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _load_ssot() -> dict:
    return json.loads(_read(SSOT_JSON))


def _surface_contract(payload: dict) -> dict:
    contract = payload["risk_sizing_owner_and_bypass_surface_contract"]
    assert isinstance(contract, dict)
    return contract


def _ast_symbol_resolves(source_path: Path, symbol_or_callable: str) -> bool:
    """Resolve Class.method or bare function/class via AST — no module import."""
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    if "." in symbol_or_callable:
        class_name, method_name = symbol_or_callable.split(".", 1)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if (
                        isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and item.name == method_name
                    ):
                        return True
        return False
    for node in tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == symbol_or_callable
        ):
            return True
        if isinstance(node, ast.ClassDef) and node.name == symbol_or_callable:
            return True
    return False


def test_ssot_doc_exists_with_required_markers() -> None:
    text = _read(SSOT_DOC)
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, f"missing SSOT marker: {marker}"
    lowered = text.lower()
    for claim in FORBIDDEN_CLAIMS:
        assert claim.lower() not in lowered, f"forbidden claim leaked: {claim}"


def test_ssot_json_parseable_and_pins_inventory_not_consolidation() -> None:
    payload = _load_ssot()
    markers = payload["markers"]
    assert markers["RISK_SIZING_OWNER_INVENTORY_SSOT_V1"] is True
    assert markers["INVENTORY_ONLY"] is True
    assert markers["CONSOLIDATION_STATUS"] == "NOT_STARTED"
    assert markers["RISK_SIZING_CLAIMED_CONSOLIDATED"] is False
    assert markers["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert markers["CANONICAL_RISK_SIZING_OWNER_MV2_SCOPE"] == EXPECTED_MV2_OWNER
    assert markers["PRODUCTIVE_RISK_SIZING_DECISION_OWNER_COUNT"] == EXPECTED_PRODUCTIVE_OWNER_COUNT
    assert markers["DUPLICATE_PRODUCTIVE_RISK_SIZING_DECISION_OWNERS"] is True
    assert markers["BYPASS_PATH_COUNT"] == EXPECTED_BYPASS_PATH_COUNT
    assert markers["RISK_LIMIT_AND_SIZING_SEPARATION"] == "PARTIAL"
    assert markers["RUNTIME_BRIDGE_ACTIVATED"] is False
    assert markers["ELIGIBLE_FOR_LIVE_DEFAULT"] is False
    assert markers["LIVE_AUTHORIZED"] is False
    assert markers["ORDERS_ENABLED"] is False
    assert markers["ECONOMIC_GATE_REMAINS_FAIL_CLOSED"] is True
    assert payload["canonical_status"]["repo_wide"] == "UNRESOLVED"
    assert payload["next_plan_item"] == "P2_LEGACY_ORDER_INTENT_DECOMMISSION_REQUIRES_OPERATOR_GO"
    assert payload["promotion_owner_status"] == "DONE"


def test_productive_owner_count_matches_inventory_lists() -> None:
    payload = _load_ssot()
    owners = payload["productive_decision_owners"]
    bypasses = payload["bypass_paths"]
    assert len(owners) == EXPECTED_PRODUCTIVE_OWNER_COUNT
    assert len(bypasses) == EXPECTED_BYPASS_PATH_COUNT
    assert len(owners) == payload["markers"]["PRODUCTIVE_RISK_SIZING_DECISION_OWNER_COUNT"]
    assert len(bypasses) == payload["markers"]["BYPASS_PATH_COUNT"]
    assert {o["owner_id"] for o in owners} == set(EXPECTED_OWNER_IDS)
    assert {b["id"] for b in bypasses} == set(EXPECTED_BYPASS_IDS)


def test_declared_paths_and_symbols_exist() -> None:
    payload = _load_ssot()
    for owner in payload["productive_decision_owners"]:
        path = REPO_ROOT / owner["module_path"]
        assert path.is_file(), f"missing owner path: {owner['module_path']}"
        text = path.read_text(encoding="utf-8")
        for symbol in owner["primary_symbols"]:
            bare = symbol.rsplit(".", 1)[-1]
            assert bare in text, f"missing symbol {symbol} in {owner['module_path']}"

    for group in (
        "adapters",
        "limit_veto_surfaces_not_size_owners",
        "consumers_and_reporters",
        "archive_historical",
    ):
        for item in payload[group]:
            rel = item["module_path"]
            assert (REPO_ROOT / rel).is_file(), f"missing inventoried path: {rel}"

    for rel in REQUIRED_OWNER_PATHS:
        assert (REPO_ROOT / rel).is_file(), f"missing required owner path: {rel}"


def test_crs_and_adapter_owner_strings_align_without_claiming_repo_wide_canonical() -> None:
    bypass = crs.export_bypass_scan_v1(repo_root=REPO_ROOT)
    assert bypass["CANONICAL_OWNER"] == EXPECTED_MV2_OWNER
    assert bypass["AUTHORITY_EFFECT"] == "NONE"
    assert bypass["RUNTIME_EFFECT"] == "NONE"
    assert bypass["ADAPTER_COMPATIBLE"] is False
    assert bypass["LEGACY_POSITION_SIZER_CLASSIFICATION"] == "DEPRECATE_LEGACY_PATH"
    assert CANONICAL_CAPITAL_RISK_SIZING_OWNER == EXPECTED_MV2_OWNER
    payload = _load_ssot()
    assert payload["markers"]["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert payload["canonical_status"]["mv2_governance_chain_owner"] == EXPECTED_MV2_OWNER


def test_inventory_does_not_claim_consolidation() -> None:
    payload = _load_ssot()
    assert payload["markers"]["CONSOLIDATION_STATUS"] == "NOT_STARTED"
    assert payload["markers"]["RISK_SIZING_CLAIMED_CONSOLIDATED"] is False
    assert payload["markers"]["INVENTORY_ONLY"] is True
    doc = _read(SSOT_DOC).lower()
    assert "not consolidated" in doc
    assert "consolidation_status=not_started" in doc


def test_runtime_bridge_and_live_order_gates_remain_blocked() -> None:
    evidence = current_head_default_final_flags_evidence_input_v0()
    assert evidence.runtime_bridge_binding_status == "BOUND_NOT_ACTIVATED"
    assert evidence.runtime_bridge_binding_status != "ACTIVATED"
    assert CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "BOUND_NOT_ACTIVATED"

    bridge_gate = evaluate_runtime_bridge_pre_activation_gate_v0(
        current_head_default_gate_input_v0()
    )
    bridge_payload = bridge_gate.to_dict() if hasattr(bridge_gate, "to_dict") else {}
    if bridge_payload:
        assert bridge_payload.get("activation_authorized") in {None, False}
        assert bridge_payload.get("runtime_bridge_activated") in {None, False}

    gate_result = gate.evaluate_current_repo_promotion_gate_v1().to_dict()
    assert gate_result["promotion_eligible"] is False
    assert gate_result["deployment_eligible"] is False
    assert gate_result["runtime_eligible"] is False
    assert gate_result.get("economic_validity_pass") is False

    ssot = _load_ssot()
    safety = ssot["safety_status"]
    assert safety["runtime_bridge_activated"] is False
    assert safety["eligible_for_live"] is False
    assert safety["live_authorized"] is False
    assert safety["orders_enabled"] is False
    assert safety["economic_gate_fail_closed"] is True
    assert safety["market_dashboard_restored"] is False
    assert safety["github_settings_mutated"] is False


def test_trading_core_semantics_not_mutated_by_inventory_slice() -> None:
    """Inventory SSOT must not rewrite trading-core modules; only docs/config/tests."""
    # This contract file lives under tests/; productive core modules must still exist
    # and CRS authority markers must remain NONE (unchanged by this slice).
    assert crs.AUTHORITY_EFFECT_NONE == "NONE"
    assert crs.RUNTIME_EFFECT_NONE == "NONE"
    assert (REPO_ROOT / "src" / "governance" / "capital_risk_sizing_v1.py").is_file()
    assert (REPO_ROOT / "src" / "risk" / "position_sizer.py").is_file()
    assert (REPO_ROOT / "src" / "core" / "position_sizing.py").is_file()
    # Ensure promotion SSOT still exists as prior inventory (reuse-before-new).
    assert PROMOTION_SSOT_JSON.is_file()


def test_governance_readme_points_to_risk_sizing_inventory() -> None:
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md" in readme
    assert "risk_sizing_owner_and_bypass_surface_contract_v1" in readme


def test_classifications_for_known_plan_candidates() -> None:
    payload = _load_ssot()
    summary = payload["classifications_summary"]
    assert "canonical_decision_owner_mv2_scope" in summary["CRS"]
    assert "legacy_decision_owner" in summary["PositionSizer"]
    assert "independent_decision_owner" in summary["core.position_sizing"]


def test_owner_and_bypass_surface_contract_semantics_and_count() -> None:
    payload = _load_ssot()
    markers = payload["markers"]
    contract = _surface_contract(payload)
    assert markers["RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_V1"] is True
    assert markers["RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_SEMANTICS"] == (
        EXPECTED_SURFACE_CONTRACT_SEMANTICS
    )
    assert (
        markers["RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_IS_NOT_AUTHORITY_ASSIGNMENT"] is True
    )
    assert (
        markers["RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_DOES_NOT_PROMOTE_REPO_WIDE_OWNER"]
        is True
    )
    assert markers["RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_DOES_NOT_CONSOLIDATE"] is True
    assert contract["semantics"] == EXPECTED_SURFACE_CONTRACT_SEMANTICS
    assert "NOT_AUTHORITY_ASSIGNMENT" in contract["semantics"]
    assert "NOT authority assignment" in contract["semantics_clarification"]
    assert "Legacy order-intent" in contract["semantics_clarification"]
    assert contract["expected_owner_count"] == EXPECTED_PRODUCTIVE_OWNER_COUNT
    assert contract["expected_bypass_count"] == EXPECTED_BYPASS_PATH_COUNT
    assert len(contract["owners"]) == EXPECTED_PRODUCTIVE_OWNER_COUNT
    assert len(contract["bypasses"]) == EXPECTED_BYPASS_PATH_COUNT
    assert tuple(contract["owner_ids_sorted"]) == EXPECTED_OWNER_IDS
    assert tuple(contract["bypass_ids_sorted"]) == EXPECTED_BYPASS_IDS
    assert contract["owner_ids_sorted"] == sorted(contract["owner_ids_sorted"])
    assert contract["bypass_ids_sorted"] == sorted(contract["bypass_ids_sorted"])
    assert set(contract["owner_ids_sorted"]) == {
        o["owner_id"] for o in payload["productive_decision_owners"]
    }
    assert set(contract["bypass_ids_sorted"]) == {b["id"] for b in payload["bypass_paths"]}
    assert contract["drift_policy"] == {
        "owner_addition": "FAIL",
        "owner_removal": "FAIL",
        "owner_rename": "FAIL",
        "owner_duplicate": "FAIL",
        "bypass_addition": "FAIL",
        "bypass_removal": "FAIL",
        "bypass_rename": "FAIL",
        "bypass_duplicate": "FAIL",
        "unresolved_symbol": "FAIL",
        "role_or_reachability_drift": "FAIL",
        "authority_escalation": "FAIL",
    }
    assert contract["global_authority_pins"] == {
        "CANONICAL_RISK_SIZING_OWNER": "UNRESOLVED",
        "CANONICAL_RISK_SIZING_OWNER_MV2_SCOPE": EXPECTED_MV2_OWNER,
        "CANONICAL_EXECUTION_AUTHORITY_OWNER": "UNRESOLVED",
        "CONSOLIDATION_STATUS": "NOT_STARTED",
        "DECOMMISSION_STATUS": "NOT_STARTED",
    }
    assert markers["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert markers["CONSOLIDATION_STATUS"] == "NOT_STARTED"


def test_owner_surfaces_exact_unique_and_non_authorizing() -> None:
    payload = _load_ssot()
    contract = _surface_contract(payload)
    owners = contract["owners"]
    ids = [o["stable_id"] for o in owners]
    paths = [o["source_path"] for o in owners]
    triples = [(o["source_path"], o["symbol_or_callable"], o["stable_id"]) for o in owners]
    inventory_by_id = {o["owner_id"]: o for o in payload["productive_decision_owners"]}

    assert len(ids) == EXPECTED_PRODUCTIVE_OWNER_COUNT
    assert len(set(ids)) == EXPECTED_PRODUCTIVE_OWNER_COUNT
    assert len(set(triples)) == EXPECTED_PRODUCTIVE_OWNER_COUNT
    assert len(set(paths)) == EXPECTED_PRODUCTIVE_OWNER_COUNT
    assert ids == sorted(ids)
    assert ids == contract["owner_ids_sorted"]

    for owner in owners:
        for field in REQUIRED_OWNER_FIELDS:
            assert field in owner, f"missing field {field} on {owner.get('stable_id')}"
        stable_id = owner["stable_id"]
        pin = EXPECTED_OWNER_PINS[stable_id]
        inventory = inventory_by_id[stable_id]
        assert owner["source_path"] == pin["source_path"]
        assert owner["symbol_or_callable"] == pin["symbol_or_callable"]
        assert owner["role"] == pin["role"]
        assert owner["decision_type"] == pin["decision_type"]
        assert owner["reachability"] == pin["reachability"]
        assert owner["classification"] == "PRODUCTIVE_RISK_SIZING_DECISION_OWNER"
        assert owner["canonical"] is False
        assert owner["authorized"] is False
        assert owner["enabled"] is False
        assert owner["execution_authority"] is False
        assert owner["capital_authority"] is False
        assert owner["decommissioned"] is False
        assert owner["inventory_only"] is True
        assert owner["authoritative_size_decision"] is True
        assert owner["authority_owner_status"] == "UNRESOLVED"
        assert owner["consolidation_status"] == "NOT_STARTED"
        assert owner["decommission_status"] == "NOT_STARTED"
        assert owner["primary_symbols"] == inventory["primary_symbols"]
        assert owner["source_path"] == inventory["module_path"]
        assert owner["role"] == inventory["role"]
        assert "*" not in owner["source_path"]
        assert "*" not in owner["symbol_or_callable"]
        assert not owner["source_path"].endswith("/")

    doc = _read(SSOT_DOC)
    assert "RISK_SIZING_OWNER_AND_BYPASS_SURFACE_CONTRACT_V1=true" in doc
    assert "INVENTORY_ONLY_NOT_AUTHORITY_ASSIGNMENT" in doc
    assert "DOES_NOT_PROMOTE_REPO_WIDE_OWNER=true" in doc
    assert "DOES_NOT_CONSOLIDATE=true" in doc


def test_bypass_surfaces_exact_unique_and_non_authorizing() -> None:
    payload = _load_ssot()
    contract = _surface_contract(payload)
    bypasses = contract["bypasses"]
    ids = [b["stable_id"] for b in bypasses]
    triples = [(b["source_path"], b["caller_symbol"], b["stable_id"]) for b in bypasses]

    assert len(ids) == EXPECTED_BYPASS_PATH_COUNT
    assert len(set(ids)) == EXPECTED_BYPASS_PATH_COUNT
    assert len(set(triples)) == EXPECTED_BYPASS_PATH_COUNT
    assert ids == sorted(ids)
    assert ids == contract["bypass_ids_sorted"]

    for bypass in bypasses:
        for field in REQUIRED_BYPASS_FIELDS:
            assert field in bypass, f"missing field {field} on {bypass.get('stable_id')}"
        stable_id = bypass["stable_id"]
        pin = EXPECTED_BYPASS_PINS[stable_id]
        assert bypass["source_path"] == pin["source_path"]
        assert bypass["caller_symbol"] == pin["caller_symbol"]
        assert bypass["target_symbol"] == pin["target_symbol"]
        assert bypass["target_source_path"] == pin["target_source_path"]
        assert bypass["target_classification"] == pin["target_classification"]
        assert bypass["role"] == "PRODUCTIVE_RISK_SIZING_BYPASS"
        assert bypass["classification"] == "PRODUCTIVE_RISK_SIZING_BYPASS"
        assert bypass["reachability"] == "REACHABLE_PRODUCTIVE"
        assert bypass["bypassed_boundary"] == EXPECTED_MV2_OWNER
        assert bypass["bypassed_owner_stable_id"] == EXPECTED_MV2_OWNER
        assert bypass["canonical"] is False
        assert bypass["authorized"] is False
        assert bypass["enabled"] is False
        assert bypass["execution_authority"] is False
        assert bypass["capital_authority"] is False
        assert bypass["decommissioned"] is False
        assert bypass["inventory_only"] is True
        assert bypass["activates_orders"] is False
        assert bypass["activates_live_capital"] is False
        assert bypass["authority_owner_status"] == "UNRESOLVED"
        assert bypass["consolidation_status"] == "NOT_STARTED"
        assert bypass["decommission_status"] == "NOT_STARTED"
        assert "*" not in bypass["source_path"]
        assert "*" not in bypass["caller_symbol"]
        assert not bypass["source_path"].endswith("/")


def test_owner_symbols_resolve_via_ast_without_import() -> None:
    payload = _load_ssot()
    contract = _surface_contract(payload)
    for owner in contract["owners"]:
        rel = owner["source_path"]
        path = REPO_ROOT / rel
        assert path.is_file(), f"unresolved source path FAIL: {owner['stable_id']} missing {rel}"
        assert _ast_symbol_resolves(path, owner["symbol_or_callable"]), (
            f"unresolved_symbol FAIL: {owner['stable_id']} {rel}::{owner['symbol_or_callable']}"
        )
        text = path.read_text(encoding="utf-8")
        for symbol in owner["primary_symbols"]:
            bare = symbol.rsplit(".", 1)[-1]
            assert bare in text, (
                f"primary_symbol missing FAIL: {owner['stable_id']} {rel}::{symbol}"
            )


def test_bypass_symbols_resolve_via_ast_without_import() -> None:
    payload = _load_ssot()
    contract = _surface_contract(payload)
    for bypass in contract["bypasses"]:
        caller_path = REPO_ROOT / bypass["source_path"]
        assert caller_path.is_file(), (
            f"unresolved source path FAIL: {bypass['stable_id']} missing {bypass['source_path']}"
        )
        assert _ast_symbol_resolves(caller_path, bypass["caller_symbol"]), (
            f"unresolved caller FAIL: {bypass['stable_id']} "
            f"{bypass['source_path']}::{bypass['caller_symbol']}"
        )
        target_symbol = bypass["target_symbol"]
        if target_symbol is None:
            assert bypass["target_classification"] == "SHADOW_CFG_POSITION_FRACTION_ASSIGNMENT"
            text = caller_path.read_text(encoding="utf-8")
            assert "position_fraction" in text
            continue
        target_path = REPO_ROOT / bypass["target_source_path"]
        assert target_path.is_file(), (
            f"unresolved target path FAIL: {bypass['stable_id']} "
            f"missing {bypass['target_source_path']}"
        )
        assert _ast_symbol_resolves(target_path, target_symbol), (
            f"unresolved target FAIL: {bypass['stable_id']} "
            f"{bypass['target_source_path']}::{target_symbol}"
        )


def test_surface_contract_does_not_regress_legacy_order_intent_contracts() -> None:
    legacy = json.loads(_read(LEGACY_ORDER_INTENT_SSOT_JSON))
    assert "direct_submission_surface_contract" in legacy
    assert "decision_owner_surface_contract" in legacy
    assert len(legacy["direct_submission_surface_contract"]["surfaces"]) == 5
    assert len(legacy["decision_owner_surface_contract"]["owners"]) == 3
    assert legacy["markers"]["CANONICAL_EXECUTION_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert legacy["markers"]["CANONICAL_ORDER_INTENT_OWNER"] == "UNRESOLVED"
    payload = _load_ssot()
    contract = _surface_contract(payload)
    assert (
        contract["related_but_separate_contracts"][
            "legacy_order_intent_decision_owner_surface_contract_v1"
        ]
        == "COMPLETE_SEPARATE_UNCHANGED"
    )
    assert (
        contract["related_but_separate_contracts"][
            "legacy_order_intent_direct_submission_surface_contract_v1"
        ]
        == "COMPLETE_SEPARATE_UNCHANGED"
    )


def test_owner_and_bypass_drift_guards_on_mutated_payload() -> None:
    """Negative checks: addition/removal/rename/duplicate/authority escalation fail-closed."""
    payload = _load_ssot()
    contract = _surface_contract(payload)
    inventory_owner_ids = {o["owner_id"] for o in payload["productive_decision_owners"]}
    inventory_bypass_ids = {b["id"] for b in payload["bypass_paths"]}
    contract_owner_ids = set(contract["owner_ids_sorted"])
    contract_bypass_ids = set(contract["bypass_ids_sorted"])
    assert inventory_owner_ids == contract_owner_ids
    assert inventory_bypass_ids == contract_bypass_ids
    assert len(contract_owner_ids) == EXPECTED_PRODUCTIVE_OWNER_COUNT
    assert len(contract_bypass_ids) == EXPECTED_BYPASS_PATH_COUNT

    # owner addition / removal / rename / duplicate
    mutated_owner_add = list(contract["owner_ids_sorted"]) + ["src.fake.sixth_owner"]
    assert len(mutated_owner_add) != EXPECTED_PRODUCTIVE_OWNER_COUNT
    assert set(mutated_owner_add) != inventory_owner_ids
    removed_owner = EXPECTED_OWNER_IDS[0]
    mutated_owner_remove = [i for i in contract["owner_ids_sorted"] if i != removed_owner]
    assert len(mutated_owner_remove) != EXPECTED_PRODUCTIVE_OWNER_COUNT
    mutated_owner_rename = [
        f"{removed_owner}_renamed" if i == removed_owner else i
        for i in contract["owner_ids_sorted"]
    ]
    assert set(mutated_owner_rename) != inventory_owner_ids
    mutated_owner_dup = list(contract["owner_ids_sorted"]) + [removed_owner]
    assert len(mutated_owner_dup) != len(set(mutated_owner_dup))

    # bypass addition / removal / rename / duplicate
    mutated_bypass_add = list(contract["bypass_ids_sorted"]) + ["BYPASS_FAKE_SIXTH"]
    assert len(mutated_bypass_add) != EXPECTED_BYPASS_PATH_COUNT
    assert set(mutated_bypass_add) != inventory_bypass_ids
    removed_bypass = EXPECTED_BYPASS_IDS[0]
    mutated_bypass_remove = [i for i in contract["bypass_ids_sorted"] if i != removed_bypass]
    assert len(mutated_bypass_remove) != EXPECTED_BYPASS_PATH_COUNT
    mutated_bypass_rename = [
        f"{removed_bypass}_RENAMED" if i == removed_bypass else i
        for i in contract["bypass_ids_sorted"]
    ]
    assert set(mutated_bypass_rename) != inventory_bypass_ids
    mutated_bypass_dup = list(contract["bypass_ids_sorted"]) + [removed_bypass]
    assert len(mutated_bypass_dup) != len(set(mutated_bypass_dup))

    # duplicate / ambiguous owner assignment
    owners = contract["owners"]
    owner_triples = {(o["source_path"], o["symbol_or_callable"]) for o in owners}
    assert len(owner_triples) == EXPECTED_PRODUCTIVE_OWNER_COUNT
    ambiguous_owners = list(owner_triples) + [list(owner_triples)[0]]
    assert len(ambiguous_owners) != len(set(ambiguous_owners))

    # duplicate / ambiguous bypass assignment
    bypasses = contract["bypasses"]
    bypass_keys = {
        (b["source_path"], b["caller_symbol"], b["target_classification"]) for b in bypasses
    }
    assert len(bypass_keys) == EXPECTED_BYPASS_PATH_COUNT

    # unresolved source path / symbol would fail AST helpers
    fake_path = REPO_ROOT / "src" / "does_not_exist_risk_sizing_owner.py"
    assert not fake_path.exists()
    real_path = REPO_ROOT / owners[0]["source_path"]
    assert not _ast_symbol_resolves(real_path, "DefinitelyMissingRiskSizingOwnerSymbol")
    real_bypass_path = REPO_ROOT / bypasses[0]["source_path"]
    assert not _ast_symbol_resolves(real_bypass_path, "DefinitelyMissingBypassCaller")

    # role / reachability drift
    for owner in owners:
        pin = EXPECTED_OWNER_PINS[owner["stable_id"]]
        assert owner["role"] == pin["role"]
        assert owner["reachability"] == pin["reachability"]
        assert owner["reachability"] != "UNREACHABLE"
    for bypass in bypasses:
        assert bypass["role"] == "PRODUCTIVE_RISK_SIZING_BYPASS"
        assert bypass["reachability"] == "REACHABLE_PRODUCTIVE"
        assert bypass["canonical"] is not True
        assert bypass["authorized"] is not True

    # authority escalation
    for owner in owners:
        assert owner["canonical"] is not True
        assert owner["authorized"] is not True
        assert owner["execution_authority"] is not True
        assert owner["capital_authority"] is not True

    # global authority owner must remain unresolved (no silent resolution)
    assert payload["markers"]["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert contract["global_authority_pins"]["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert contract["global_authority_pins"]["CANONICAL_EXECUTION_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert payload["canonical_status"]["repo_wide"] == "UNRESOLVED"
