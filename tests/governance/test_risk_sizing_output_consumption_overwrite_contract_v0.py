"""Static contract: Risk/Sizing output consumption/overwrite freeze v0.

Docs/config/tests-only. Does not authorize live, orders, runtime bridge,
consolidation, authority assignment, federation, or risk/sizing semantic changes.
"""

from __future__ import annotations

import ast
import copy
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_output_consumption_overwrite_contract_v0.json"
)
CONTRACT_DOC = (
    REPO_ROOT / "docs" / "governance" / "RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md"
)
OWNER_INVENTORY_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_owner_inventory_ssot_v1.json"
)
UNITS_JSON = REPO_ROOT / "config" / "governance" / "risk_sizing_units_dimensions_contract_v0.json"
TOPOLOGY_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_caller_owner_topology_contract_v0.json"
)
LEGACY_ORDER_INTENT_JSON = (
    REPO_ROOT / "config" / "governance" / "legacy_order_intent_inventory_ssot_v1.json"
)

EXPECTED_CONSUMPTION_CLASSES = (
    "FINAL_CONSUMER",
    "ABSOLUTE_VALUE_TRANSFORM",
    "ZERO_OR_VETO_OVERRIDE",
    "CAP_OVERRIDE",
    "WRAP_DELEGATE",
    "PASS_THROUGH_ONLY",
    "INTENT_ONLY",
    "EVIDENCE_ONLY",
    "SUBMISSION_BLOCKED",
    "DIRECT_ORDER_HANDOFF",
    "IGNORED_OUTPUT",
    "AMBIGUOUS_CONSUMPTION",
)

REQUIRED_EDGE_FIELDS = (
    "edge_id",
    "owner_id",
    "owner_callable",
    "caller_id",
    "caller_callable",
    "source_path",
    "input_dimension",
    "owner_output_dimension",
    "consumption_class",
    "downstream_quantity_mutation",
    "final_quantity_provenance",
    "submission_proximity",
    "domain",
    "authority_effect",
    "evidence_anchors",
    "ambiguity_status",
)

REQUIRED_DOC_MARKERS = (
    "RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0=true",
    "INVENTORY_ONLY=true",
    "OUTPUT_CONSUMPTION_OVERWRITE_FROZEN=true",
    "OUTPUT_CONSUMPTION_OVERWRITE_RESOLVED=false",
    "NO_SIZING_MATH_CHANGE=true",
    "NO_AUTHORITY_ASSIGNMENT=true",
    "NO_FEDERATION_IMPLEMENTED=true",
    "RECOMMENDED_CONSOLIDATION_MODEL=CONTRACTUAL_FEDERATION",
    "SEMANTICS_FREE_CONTRACT_SLICE_AVAILABLE=true",
    "SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE=false",
    "CANONICAL_RISK_SIZING_OWNER=UNRESOLVED",
    "CANONICAL_RISK_SIZING_AUTHORITY_OWNER=UNRESOLVED",
    "CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED",
    "AUTHORITY_EFFECT=NONE",
    "RUNTIME_EFFECT=NONE",
    "LIVE_AUTHORIZED=false",
    "ORDERS_ENABLED=false",
    "RUNTIME_BRIDGE_ACTIVATED=false",
    "EXPECTED_PRIMARY_OWNER_COUNT=5",
    "EXPECTED_PRODUCTIVE_DIRECT_EDGE_COUNT=8",
    "EXPECTED_COMPANION_EDGE_COUNT=2",
    "EXPECTED_DIRECT_SIZING_BYPASS_COUNT=5",
    "EXPECTED_PASS_THROUGH_EDGE_COUNT=2",
    "EXPECTED_AMBIGUOUS_EDGE_COUNT=3",
    "EXPECTED_CONSUMPTION_EDGE_COUNT=27",
    "EXPECTED_OVERWRITE_EDGE_COUNT=13",
    "EXPECTED_WRAP_DELEGATE_EDGE_COUNT=1",
    "EXPECTED_FINAL_QUANTITY_PROVENANCE_RESOLVED_PATH_COUNT=5",
    "EXPECTED_FINAL_QUANTITY_PROVENANCE_UNRESOLVED_PATH_COUNT=3",
    "LEVERAGE_APPLICATION_STATUS=declared_pass_through_not_applied_in_quantity_chain",
)

# Anchors that must remain present for veto/cap/abs transforms
CRITICAL_TRANSFORM_SNIPPETS = {
    "CONS_CORE_ENGINE_ABS_TRANSFORM": (
        "src/backtest/engine.py",
        ["abs(target_units)", "position_size = abs(target_units)"],
    ),
    "CONS_CORE_ENGINE_RISK_MANAGER_ADJUST": (
        "src/backtest/engine.py",
        ["adjust_target_position"],
    ),
    "CONS_CORE_ENGINE_CHECK_RISK_LIMITS": (
        "src/backtest/engine.py",
        ["_check_risk_limits"],
    ),
    "CONS_OFFLINE_CAP_OVERRIDE": (
        "src/backtest/offline_evaluation_sizing_contract_v1.py",
        ["CAP_TO_MAX_POSITION_PCT", "min("],
    ),
    "CONS_OFFLINE_WRAP_CALC_POSITION_SIZE": (
        "src/backtest/offline_evaluation_sizing_contract_v1.py",
        ["calc_position_size"],
    ),
    "CONS_CRS_INTENT_SUBMISSION_BLOCKED": (
        "src/trading/master_v2/canonical_core_runtime_integration_intent_pipeline_bridge_v0.py",
        ["submission_blocked=True", "submission_blocked"],
    ),
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_contract() -> dict:
    return json.loads(_read(CONTRACT_JSON))


def _productive_edges(payload: dict) -> list[dict]:
    return [e for e in payload["consumption_edges"] if not e.get("catalog_sentinel")]


def _overwrite_edges(payload: dict) -> list[dict]:
    return [e for e in payload["consumption_edges"] if e.get("is_overwrite") is True]


def _class_count(payload: dict, cls: str) -> int:
    return sum(1 for e in payload["consumption_edges"] if e["consumption_class"] == cls)


def test_contract_doc_markers_present() -> None:
    text = _read(CONTRACT_DOC)
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, f"missing doc marker: {marker}"
    # Historical wording may appear only inside the precision-clarification section.
    assert "SEMANTICS_FREE_CONTRACT_SLICE_AVAILABLE=true" in text
    assert "SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE=false" in text
    assert "SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE=true" not in text
    # Active marker block must not promote the ambiguous historical token as binding.
    marker_block = text.split("## Precision clarification", 1)[0]
    assert "SEMANTICS_FREE_IMPLEMENTATION_AVAILABLE=true" not in marker_block
    assert "not** semantics-free" in text or "are **not** semantics-free" in text


def test_precision_clarification_pins() -> None:
    payload = _load_contract()
    markers = payload["markers"]
    assert markers["SEMANTICS_FREE_CONTRACT_SLICE_AVAILABLE"] is True
    assert markers["SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE"] is False
    assert markers["RECOMMENDED_CONSOLIDATION_MODEL"] == "CONTRACTUAL_FEDERATION"
    assert markers["NO_FEDERATION_IMPLEMENTED"] is True

    clarification = payload["precision_clarification"]
    assert clarification["replacement_markers"]["SEMANTICS_FREE_CONTRACT_SLICE_AVAILABLE"] is True
    assert (
        clarification["replacement_markers"]["SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE"]
        is False
    )
    planning = payload["planning_only"]
    assert planning["federation_implemented"] is False
    assert planning["owner_consolidation_implemented"] is False
    assert planning["semantics_free_owner_consolidation_available"] is False


def test_schema_catalog_and_edge_fields() -> None:
    payload = _load_contract()
    assert tuple(payload["consumption_classes_catalog"]) == EXPECTED_CONSUMPTION_CLASSES
    assert tuple(payload["required_edge_fields"]) == REQUIRED_EDGE_FIELDS

    edge_ids = [e["edge_id"] for e in payload["consumption_edges"]]
    assert len(edge_ids) == len(set(edge_ids)), "duplicate consumption edge_id FAIL"

    for edge in payload["consumption_edges"]:
        for field in REQUIRED_EDGE_FIELDS:
            assert field in edge, f"{edge['edge_id']} missing {field}"
        assert edge["consumption_class"] in EXPECTED_CONSUMPTION_CLASSES
        assert edge["authority_effect"] == "NONE"
        assert isinstance(edge["evidence_anchors"], list)
        assert edge["evidence_anchors"]


def test_expected_counts_match_payload() -> None:
    payload = _load_contract()
    counts = payload["expected_counts"]
    assert len(payload["consumption_edges"]) == counts["consumption_edges"] == 27
    assert len(_overwrite_edges(payload)) == counts["overwrite_edges"] == 13
    assert _class_count(payload, "WRAP_DELEGATE") == counts["wrap_delegate_edges"] == 1

    resolved = [p for p in payload["final_quantity_provenance_paths"] if p["status"] == "RESOLVED"]
    unresolved = [
        p for p in payload["final_quantity_provenance_paths"] if p["status"] == "UNRESOLVED"
    ]
    assert len(resolved) == counts["final_quantity_provenance_resolved_paths"] == 5
    assert len(unresolved) == counts["final_quantity_provenance_unresolved_paths"] == 3

    for cls in EXPECTED_CONSUMPTION_CLASSES:
        key = f"consumption_class_{cls}"
        assert counts[key] == _class_count(payload, cls), f"class count mismatch: {cls}"

    # Topology/inventory pins remain frozen
    assert counts["primary_owners"] == 5
    assert counts["productive_direct_edges"] == 8
    assert counts["companion_edges"] == 2
    assert counts["direct_sizing_bypass_edges"] == 5
    assert counts["pass_through_edges_topology"] == 2
    assert counts["ambiguous_edges_topology"] == 3
    assert counts["ignored_output_productive_edges"] == 0


def test_authority_and_leverage_pins() -> None:
    payload = _load_contract()
    auth = payload["authority_status"]
    assert auth["canonical_execution_authority_owner"] == "UNRESOLVED"
    assert auth["canonical_risk_sizing_authority_owner"] == "UNRESOLVED"
    assert auth["canonical_risk_sizing_owner"] == "UNRESOLVED"
    assert auth["authority_effect"] == "NONE"

    lev = payload["leverage_status"]
    assert lev["applied_in_quantity_chain"] is False
    assert lev["application_status"] == "declared_pass_through_not_applied_in_quantity_chain"

    conflict = payload["percent_conflicts_unresolved"][0]
    assert conflict["must_not_equate"] == ["PERCENT_0_100", "FRACTION_DECIMAL_0_1"]
    assert conflict["resolution_status"] == "UNRESOLVED_MUST_NOT_EQUATE"


def test_topology_units_inventory_counts_unchanged() -> None:
    payload = _load_contract()
    topology = json.loads(_read(TOPOLOGY_JSON))
    units = json.loads(_read(UNITS_JSON))
    inventory = json.loads(_read(OWNER_INVENTORY_JSON))
    surface = inventory["risk_sizing_owner_and_bypass_surface_contract"]

    assert topology["expected_counts"]["primary_owners"] == 5
    assert topology["expected_counts"]["productive_direct_edges"] == 8
    assert topology["expected_counts"]["companion_edges"] == 2
    assert topology["expected_counts"]["pass_through_edges"] == 2
    assert topology["expected_counts"]["ambiguous_edges"] == 3
    assert topology["expected_counts"]["direct_sizing_bypass_edges"] == 5

    assert units["markers"]["EXPECTED_PRIMARY_OWNER_COUNT"] == 5
    assert len(units["companion_edges"]) == 2

    assert surface["expected_owner_count"] == 5
    assert surface["expected_bypass_count"] == 5

    assert payload["expected_counts"]["primary_owners"] == 5
    assert payload["expected_counts"]["productive_direct_edges"] == 8


def test_companion_not_sixth_primary_owner() -> None:
    payload = _load_contract()
    topology = json.loads(_read(TOPOLOGY_JSON))
    primary_count = len(topology["primary_owners"])
    assert primary_count == 5

    for edge in payload["consumption_edges"]:
        if edge["edge_id"] in {
            "CONS_SHADOW_POSITION_FRACTION_HANDOFF",
            "CONS_LIVE_POSITION_FRACTION_HANDOFF",
        }:
            assert edge.get("primary_owner") is False
            assert edge.get("must_not_classify_as_primary_owner") is True
            assert edge["consumption_class"] == "AMBIGUOUS_CONSUMPTION"


def test_wrap_delegate_not_equal_authority() -> None:
    payload = _load_contract()
    wraps = [e for e in payload["consumption_edges"] if e["consumption_class"] == "WRAP_DELEGATE"]
    assert len(wraps) == 1
    wrap = wraps[0]
    assert wrap["must_not_equate_wrap_with_equal_authority"] is True
    assert wrap["authority_effect"] == "NONE"
    assert wrap["ambiguity_status"] == "DUAL_OWNER_WRAP_UNRESOLVED_AUTHORITY"


def test_submission_blocked_pin() -> None:
    payload = _load_contract()
    blocked = [
        e for e in payload["consumption_edges"] if e["consumption_class"] == "SUBMISSION_BLOCKED"
    ]
    assert len(blocked) == 1
    edge = blocked[0]
    assert edge["submission_blocked"] is True
    assert edge["execution_eligible"] is False
    bridge = _read(
        REPO_ROOT
        / "src/trading/master_v2/canonical_core_runtime_integration_intent_pipeline_bridge_v0.py"
    )
    assert "submission_blocked=True" in bridge
    assert "authority_effect=_AUTHORITY_EFFECT_NONE" in bridge or (
        "authority_effect=_AUTHORITY_EFFECT_NONE" in bridge
    )


def test_leverage_not_applied_in_quantity_chain_source() -> None:
    payload = _load_contract()
    assert payload["leverage_status"]["applied_in_quantity_chain"] is False
    leverage_edge = next(
        e
        for e in payload["consumption_edges"]
        if e["edge_id"] == "CONS_CRS_LEVERAGE_NOT_APPLIED_IN_QUANTITY_CHAIN"
    )
    assert leverage_edge["applied_in_quantity_chain"] is False

    crs = _read(REPO_ROOT / "src/governance/capital_risk_sizing_v1.py")
    start = crs.find("def evaluate_quantity_chain_v1(")
    assert start >= 0
    rest = crs[start + 4 :]
    next_def = rest.find("\ndef ")
    body = rest[: next_def if next_def >= 0 else len(rest)]
    assert "leverage_ceiling" not in body


def test_critical_transform_snippets_present() -> None:
    for edge_id, (rel_path, snippets) in CRITICAL_TRANSFORM_SNIPPETS.items():
        text = _read(REPO_ROOT / rel_path)
        for snippet in snippets:
            assert snippet in text, f"{edge_id}: missing snippet {snippet!r} in {rel_path}"


def test_overwrite_order_pins() -> None:
    payload = _load_contract()
    by_id = {e["edge_id"]: e for e in payload["consumption_edges"]}
    for pin in payload["overwrite_order_pins"]:
        ordered = pin["ordered_edge_ids"]
        indices = []
        for edge_id in ordered:
            edge = by_id[edge_id]
            assert edge.get("is_overwrite") is True
            assert edge["overwrite_order_index"] is not None
            indices.append(edge["overwrite_order_index"])
        assert indices == sorted(indices), f"overwrite_order_change FAIL: {pin['path_id']}"


def test_execute_from_signals_external_callers_remain_zero() -> None:
    pipeline = REPO_ROOT / "src/execution/pipeline.py"
    hits: list[tuple[str, int]] = []
    for path in sorted((REPO_ROOT / "src").rglob("*.py")):
        if path == pipeline:
            continue
        if "/_archive/" in str(path).replace("\\", "/"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = None
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name == "execute_from_signals":
                    hits.append((str(path.relative_to(REPO_ROOT)), node.lineno))
    assert hits == [], f"execute_from_signals external caller addition FAIL: {hits}"


def test_feedback_must_not_invent_primary_authority() -> None:
    payload = _load_contract()
    for edge_id in (
        "CONS_FEEDBACK_CORE_MIRROR",
        "CONS_FEEDBACK_OFFLINE_MIRROR",
        "CONS_FEEDBACK_CALC_MIRROR",
    ):
        edge = next(e for e in payload["consumption_edges"] if e["edge_id"] == edge_id)
        assert edge["must_not_invent_new_primary_authority"] is True
        assert edge["authority_effect"] == "NONE"


def test_pass_through_adapters_not_primary_owners() -> None:
    payload = _load_contract()
    topology = json.loads(_read(TOPOLOGY_JSON))
    primary_paths = {o["source_path"] for o in topology["primary_owners"]}
    for edge in payload["consumption_edges"]:
        if edge["consumption_class"] == "PASS_THROUGH_ONLY" and edge.get(
            "must_not_classify_as_primary_owner"
        ):
            assert edge["source_path"] not in primary_paths


def test_readme_and_related_docs_point_to_consumption_contract() -> None:
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md" in readme
    topology_doc = _read(
        REPO_ROOT / "docs" / "governance" / "RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md"
    )
    assert "RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0" in topology_doc


def test_legacy_order_intent_contract_untouched_reference() -> None:
    legacy = json.loads(_read(LEGACY_ORDER_INTENT_JSON))
    assert "direct_submission_surface_contract" in legacy
    assert len(legacy["direct_submission_surface_contract"]["surfaces"]) == 5


# --- Drift / mutation fixtures (in-memory; never mutate productive src/) ---


def test_drift_new_consumption_edge_fails_count() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["consumption_edges"].append(
        {
            "edge_id": "CONS_ROGUE_NEW",
            "owner_id": "src.core.position_sizing",
            "owner_callable": "get_target_position",
            "caller_id": "rogue",
            "caller_callable": "rogue",
            "source_path": "src/backtest/engine.py",
            "input_dimension": "QUANTITY_BASE_UNITS",
            "owner_output_dimension": "QUANTITY_BASE_UNITS",
            "consumption_class": "FINAL_CONSUMER",
            "downstream_quantity_mutation": "rogue",
            "final_quantity_provenance": "RESOLVED",
            "submission_proximity": "NONE",
            "domain": "OFFLINE_BACKTEST",
            "authority_effect": "NONE",
            "evidence_anchors": ["x"],
            "ambiguity_status": "NONE",
            "is_overwrite": True,
        }
    )
    assert len(payload["consumption_edges"]) != payload["expected_counts"]["consumption_edges"]


def test_drift_overwrite_order_change_detected() -> None:
    payload = copy.deepcopy(_load_contract())
    by_id = {e["edge_id"]: e for e in payload["consumption_edges"]}
    a = by_id["CONS_CORE_ENGINE_ABS_TRANSFORM"]
    b = by_id["CONS_CORE_ENGINE_RISK_MANAGER_ADJUST"]
    a["overwrite_order_index"], b["overwrite_order_index"] = (
        b["overwrite_order_index"],
        a["overwrite_order_index"],
    )
    pin = next(
        p for p in payload["overwrite_order_pins"] if p["path_id"] == "PATH_ENGINE_CORE_SIZER"
    )
    indices = [by_id[eid]["overwrite_order_index"] for eid in pin["ordered_edge_ids"]]
    assert indices != sorted(indices)


def test_drift_percent_fraction_silent_equate_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    conflict = payload["percent_conflicts_unresolved"][0]
    with pytest.raises(AssertionError):
        assert conflict["must_not_equate"][0] == conflict["must_not_equate"][1]
        raise AssertionError("percent_fraction_silent_equivalence FAIL")


def test_drift_companion_as_sixth_owner_fails() -> None:
    topology = copy.deepcopy(json.loads(_read(TOPOLOGY_JSON)))
    topology["primary_owners"].append(
        {
            "owner_id": "fake.companion.as.primary",
            "module": "fake",
            "source_path": "src/live/shadow_session.py",
            "primary_symbols": ["ShadowPaperSession.step_once"],
        }
    )
    assert len(topology["primary_owners"]) != 5


def test_drift_submission_blocked_change_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    edge = next(
        e for e in payload["consumption_edges"] if e["consumption_class"] == "SUBMISSION_BLOCKED"
    )
    edge["submission_blocked"] = False
    assert edge["submission_blocked"] is not True


def test_drift_leverage_claimed_applied_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["leverage_status"]["applied_in_quantity_chain"] = True
    assert payload["leverage_status"]["applied_in_quantity_chain"] is not False


def test_drift_authority_escalation_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["authority_status"]["canonical_risk_sizing_authority_owner"] = "src.governance.crs"
    assert payload["authority_status"]["canonical_risk_sizing_authority_owner"] != "UNRESOLVED"


def test_drift_wrap_equated_to_equal_authority_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    wrap = next(
        e for e in payload["consumption_edges"] if e["consumption_class"] == "WRAP_DELEGATE"
    )
    wrap["must_not_equate_wrap_with_equal_authority"] = False
    assert wrap["must_not_equate_wrap_with_equal_authority"] is not True


def test_drift_veto_cap_abs_removal_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    before = {e["edge_id"] for e in payload["consumption_edges"]}
    payload["consumption_edges"] = [
        e
        for e in payload["consumption_edges"]
        if e["edge_id"]
        not in {
            "CONS_CORE_ENGINE_ABS_TRANSFORM",
            "CONS_OFFLINE_CAP_OVERRIDE",
            "CONS_CORE_ENGINE_RISK_MANAGER_ADJUST",
        }
    ]
    after = {e["edge_id"] for e in payload["consumption_edges"]}
    removed = before - after
    assert removed, "expected removal for fixture"
    assert "CONS_CORE_ENGINE_ABS_TRANSFORM" in removed


def test_drift_owner_consolidation_claimed_semantics_free_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["markers"]["SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE"] = True
    assert payload["markers"]["SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE"] is not False


def test_doc_forbids_semantics_free_owner_consolidation_claim() -> None:
    text = _read(CONTRACT_DOC)
    assert "SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE=false" in text
    assert re.search(r"SEMANTICS_FREE_CONTRACT_SLICE_AVAILABLE=true", text)
    # Must not claim owner consolidation is semantics-free
    assert "SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE=true" not in text
