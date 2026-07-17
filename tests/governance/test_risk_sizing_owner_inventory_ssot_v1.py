"""Static contract: Risk/Sizing owner inventory SSOT v1.

Docs/config/tests-only. Does not authorize live, orders, runtime bridge,
deployment, consolidation, or risk/sizing semantic changes.
"""

from __future__ import annotations

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

EXPECTED_PRODUCTIVE_OWNER_COUNT = 5
EXPECTED_BYPASS_PATH_COUNT = 5
EXPECTED_MV2_OWNER = "src.governance.capital_risk_sizing_v1"

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


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _load_ssot() -> dict:
    return json.loads(_read(SSOT_JSON))


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
    assert payload["next_plan_item"] == "P2_LEGACY_ORDER_INTENT"
    assert payload["promotion_owner_status"] == "DONE"


def test_productive_owner_count_matches_inventory_lists() -> None:
    payload = _load_ssot()
    owners = payload["productive_decision_owners"]
    bypasses = payload["bypass_paths"]
    assert len(owners) == EXPECTED_PRODUCTIVE_OWNER_COUNT
    assert len(bypasses) == EXPECTED_BYPASS_PATH_COUNT
    assert len(owners) == payload["markers"]["PRODUCTIVE_RISK_SIZING_DECISION_OWNER_COUNT"]
    assert len(bypasses) == payload["markers"]["BYPASS_PATH_COUNT"]
    assert {o["owner_id"] for o in owners} == {
        "src.governance.capital_risk_sizing_v1",
        "src.risk.position_sizer",
        "src.core.position_sizing",
        "backtest.offline_evaluation_sizing_contract_v1",
        "src.execution.pipeline.execute_from_signals",
    }


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


def test_classifications_for_known_plan_candidates() -> None:
    payload = _load_ssot()
    summary = payload["classifications_summary"]
    assert "canonical_decision_owner_mv2_scope" in summary["CRS"]
    assert "legacy_decision_owner" in summary["PositionSizer"]
    assert "independent_decision_owner" in summary["core.position_sizing"]
