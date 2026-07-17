"""Static contract: Legacy Order Intent inventory SSOT v1.

Docs/config/tests-only. Does not authorize live, orders, runtime bridge,
decommission, consolidation, rewire, or execution-semantic changes.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.governance import canonical_order_intent_v1 as coi
from src.governance.promotion_loop import promotion_economic_gate_v1 as gate
from src.trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
    INTEGRATION_STATUS_BOUND_NOT_ACTIVATED,
)
from src.trading.master_v2.legacy_runtime_entrypoint_guard_v0 import (
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
)
from src.trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
    current_head_default_final_flags_evidence_input_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SSOT_DOC = REPO_ROOT / "docs" / "governance" / "LEGACY_ORDER_INTENT_INVENTORY_SSOT_V1.md"
SSOT_JSON = REPO_ROOT / "config" / "governance" / "legacy_order_intent_inventory_ssot_v1.json"

EXPECTED_BASE_SHA = "19e4b1f26dcbbfeeef3b7138f15dfa5bc4181319"
EXPECTED_DECISION_OWNER_COUNT = 3
EXPECTED_BYPASS_COUNT = 4
EXPECTED_SUBMISSION_BYPASS_COUNT = 5
EXPECTED_MV2_OWNER = "src.governance.canonical_order_intent_v1"

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "LEGACY_ORDER_INTENT_INVENTORY_SSOT_V1=true",
    "INVENTORY_ONLY=true",
    "CONSOLIDATION_STATUS=NOT_STARTED",
    "DECOMMISSION_STATUS=NOT_STARTED",
    "LEGACY_ORDER_INTENT_CLAIMED_DECOMMISSIONED=false",
    "LEGACY_ORDER_INTENT_CLAIMED_CONSOLIDATED=false",
    "CANONICAL_ORDER_INTENT_OWNER=UNRESOLVED",
    f"CANONICAL_ORDER_INTENT_OWNER_MV2_SCOPE={EXPECTED_MV2_OWNER}",
    "CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED",
    f"PRODUCTIVE_ORDER_INTENT_DECISION_OWNER_COUNT={EXPECTED_DECISION_OWNER_COUNT}",
    f"PRODUCTIVE_BYPASS_PATH_COUNT={EXPECTED_BYPASS_COUNT}",
    f"DIRECT_SUBMISSION_BYPASS_COUNT={EXPECTED_SUBMISSION_BYPASS_COUNT}",
    "AUTHORITY_LEAK_DETECTED=false",
    "THIS_DOCUMENT_IS_INVENTORY_SSOT_NOT_RUNTIME_AUTHORITY=true",
    "NO_RUNTIME_REWIRE_IN_THIS_SLICE=true",
    "NO_TRADING_CORE_CHANGE=true",
    "NO_EXECUTION_SEMANTICS_CHANGE=true",
    "NO_RISK_SIZING_CHANGE=true",
    "NO_RUNTIME_BRIDGE_ACTIVATION=true",
    "ELIGIBLE_FOR_LIVE_DEFAULT=false",
    "LIVE_AUTHORIZED=false",
    "ORDERS_ENABLED=false",
    "RUNTIME_BRIDGE_ACTIVATED=false",
    "RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED",
    "ECONOMIC_GATE_REMAINS_FAIL_CLOSED=true",
    "AUTHORITY_EFFECT=NONE",
    "INVENTORY ONLY — CONSOLIDATION NOT STARTED — DECOMMISSION NOT STARTED",
)

FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "eligible_for_live=true",
    "LIVE_AUTHORIZED=true",
    "ORDERS_ENABLED=true",
    "RUNTIME_BRIDGE_ACTIVATED=true",
    "CONSOLIDATION_STATUS=DONE",
    "DECOMMISSION_STATUS=DONE",
    "LEGACY_ORDER_INTENT_CLAIMED_DECOMMISSIONED=true",
    "LEGACY_ORDER_INTENT_CLAIMED_CONSOLIDATED=true",
    "already decommissioned",
    "legacy order intent retired",
    "approved for live trading",
)

ALLOWED_ROLES = {
    "CANONICAL_DECISION_OWNER",
    "CANONICAL_ADAPTER",
    "PRODUCTIVE_LEGACY_OWNER",
    "PRODUCTIVE_BYPASS",
    "REPORTING_OR_OBSERVABILITY",
    "TEST_OR_FIXTURE",
    "DEAD_OR_ARCHIVED",
    "FALSE_POSITIVE",
}


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


def test_ssot_json_pins_inventory_not_decommission() -> None:
    payload = _load_ssot()
    markers = payload["markers"]
    assert markers["LEGACY_ORDER_INTENT_INVENTORY_SSOT_V1"] is True
    assert markers["INVENTORY_ONLY"] is True
    assert markers["CONSOLIDATION_STATUS"] == "NOT_STARTED"
    assert markers["DECOMMISSION_STATUS"] == "NOT_STARTED"
    assert markers["LEGACY_ORDER_INTENT_CLAIMED_DECOMMISSIONED"] is False
    assert markers["LEGACY_ORDER_INTENT_CLAIMED_CONSOLIDATED"] is False
    assert markers["CANONICAL_ORDER_INTENT_OWNER"] == "UNRESOLVED"
    assert markers["CANONICAL_ORDER_INTENT_OWNER_MV2_SCOPE"] == EXPECTED_MV2_OWNER
    assert markers["CANONICAL_EXECUTION_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert markers["PRODUCTIVE_ORDER_INTENT_DECISION_OWNER_COUNT"] == EXPECTED_DECISION_OWNER_COUNT
    assert markers["PRODUCTIVE_BYPASS_PATH_COUNT"] == EXPECTED_BYPASS_COUNT
    assert markers["DIRECT_SUBMISSION_BYPASS_COUNT"] == EXPECTED_SUBMISSION_BYPASS_COUNT
    assert markers["AUTHORITY_LEAK_DETECTED"] is False
    assert markers["RUNTIME_BRIDGE_ACTIVATED"] is False
    assert markers["LIVE_AUTHORIZED"] is False
    assert markers["ORDERS_ENABLED"] is False
    assert payload["canonical_order_intent_owner"] == "UNRESOLVED"
    assert payload["canonical_execution_authority_owner"] == "UNRESOLVED"
    assert payload["consolidation_status"] == "NOT_STARTED"
    assert payload["decommission_status"] == "NOT_STARTED"
    assert payload["authority_leak_detected"] is False
    assert payload["generated_from_main_sha"] == EXPECTED_BASE_SHA
    assert payload["schema_version"] == "legacy_order_intent_inventory_schema_v1"


def test_doc_and_json_counts_agree() -> None:
    payload = _load_ssot()
    doc = _read(SSOT_DOC)
    assert len(payload["productive_decision_owners"]) == EXPECTED_DECISION_OWNER_COUNT
    assert len(payload["productive_bypass_paths"]) == EXPECTED_BYPASS_COUNT
    assert len(payload["direct_submission_bypasses"]) == EXPECTED_SUBMISSION_BYPASS_COUNT
    assert (
        payload["productive_order_intent_decision_owner_count"]
        == EXPECTED_DECISION_OWNER_COUNT
    )
    assert f"PRODUCTIVE_ORDER_INTENT_DECISION_OWNER_COUNT={EXPECTED_DECISION_OWNER_COUNT}" in doc
    assert f"PRODUCTIVE_BYPASS_PATH_COUNT={EXPECTED_BYPASS_COUNT}" in doc
    assert f"DIRECT_SUBMISSION_BYPASS_COUNT={EXPECTED_SUBMISSION_BYPASS_COUNT}" in doc


def test_classified_paths_exist_and_roles_valid() -> None:
    payload = _load_ssot()
    paths = payload["classified_paths"]
    assert paths, "classified_paths must not be empty"
    for item in paths:
        role = item["role"]
        assert role in ALLOWED_ROLES, f"invalid role: {role}"
        rel = item["module_path"]
        path = REPO_ROOT / rel
        assert path.exists(), f"missing inventoried path: {rel}"
        if path.is_file() and item.get("primary_symbols"):
            text = path.read_text(encoding="utf-8")
            for symbol in item["primary_symbols"]:
                bare = symbol.rsplit(".", 1)[-1]
                assert bare in text, f"missing symbol {symbol} in {rel}"


def test_productive_entries_classified_and_listed() -> None:
    payload = _load_ssot()
    by_id = {item["owner_id"]: item for item in payload["classified_paths"]}
    for owner_id in payload["productive_decision_owners"]:
        assert owner_id in by_id, f"decision owner missing from classified_paths: {owner_id}"
        assert by_id[owner_id]["role"] in {
            "CANONICAL_DECISION_OWNER",
            "PRODUCTIVE_LEGACY_OWNER",
        }
    for bypass_id in payload["productive_bypass_paths"]:
        assert bypass_id in by_id, f"bypass missing from classified_paths: {bypass_id}"
        assert by_id[bypass_id]["role"] == "PRODUCTIVE_BYPASS"
        assert by_id[bypass_id]["reachability"] == "REACHABLE_PRODUCTIVE"
    for sub_id in payload["direct_submission_bypasses"]:
        assert sub_id in by_id, f"submission bypass missing: {sub_id}"
        assert by_id[sub_id]["can_submit_orders"] is True


def test_no_false_decommission_or_rewire_claim() -> None:
    payload = _load_ssot()
    assert payload["consolidation_status"] == "NOT_STARTED"
    assert payload["decommission_status"] == "NOT_STARTED"
    doc = _read(SSOT_DOC).lower()
    assert "not started" in doc
    assert "does **not** retire legacy paths".lower() in doc or "does not retire legacy paths" in doc


def test_coi_and_runtime_remain_non_authorizing() -> None:
    assert coi.AUTHORITY_EFFECT_NONE == "NONE"
    assert INTEGRATION_STATUS_BOUND_NOT_ACTIVATED == "BOUND_NOT_ACTIVATED"
    assert CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "BOUND_NOT_ACTIVATED"
    evidence = current_head_default_final_flags_evidence_input_v0()
    assert evidence.runtime_bridge_binding_status == "BOUND_NOT_ACTIVATED"
    assert evidence.runtime_bridge_binding_status != "ACTIVATED"

    gate_result = gate.evaluate_current_repo_promotion_gate_v1().to_dict()
    assert gate_result["promotion_eligible"] is False
    assert gate_result.get("economic_validity_pass") is False

    safety = _load_ssot()["safety_status"]
    assert safety["runtime_bridge_activated"] is False
    assert safety["live_authorized"] is False
    assert safety["orders_enabled"] is False
    assert safety["authority_leak_detected"] is False
    assert safety["economic_gate_fail_closed"] is True


def test_governance_readme_points_to_legacy_order_intent_inventory() -> None:
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "LEGACY_ORDER_INTENT_INVENTORY_SSOT_V1.md" in readme
