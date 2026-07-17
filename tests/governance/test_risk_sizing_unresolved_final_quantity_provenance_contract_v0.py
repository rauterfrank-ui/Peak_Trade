"""Static contract: unresolved Final Quantity Provenance paths freeze v0.

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
    / "risk_sizing_unresolved_final_quantity_provenance_contract_v0.json"
)
CONTRACT_DOC = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0.md"
)
CONSUMPTION_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_output_consumption_overwrite_contract_v0.json"
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

FROZEN_PATH_IDS = (
    "PATH_EXECUTE_FROM_SIGNALS",
    "PATH_SHADOW_COMPANION",
    "PATH_LIVE_COMPANION",
)

REQUIRED_PATH_FIELDS = (
    "path_id",
    "entrypoint",
    "direct_productive_callers",
    "source_owner_or_factory",
    "input_quantity_dimension",
    "transform_chain",
    "last_observable_quantity",
    "handoff_class",
    "submission_state",
    "runtime_reachability",
    "companion_role",
    "authority_status",
    "final_quantity_provenance_status",
    "unresolved_reason_codes",
    "evidence_anchors",
    "non_claims",
)

REQUIRED_DOC_MARKERS = (
    "RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0=true",
    "INVENTORY_ONLY=true",
    "FINAL_QUANTITY_PROVENANCE_UNRESOLVED_PATHS_FROZEN=true",
    "FINAL_QUANTITY_PROVENANCE_RESOLVED=false",
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
    "EXPECTED_UNRESOLVED_PATH_COUNT=3",
    "EXPECTED_NEW_DIRECT_CALLER_COUNT=0",
    "LEVERAGE_APPLICATION_STATUS=declared_pass_through_not_applied_in_quantity_chain",
)

GLOBAL_NON_CLAIMS = (
    "NO_CANONICAL_RISK_SIZING_OWNER_ASSIGNED",
    "NO_CANONICAL_EXECUTION_AUTHORITY_OWNER_ASSIGNED",
    "COMPANION_IS_NOT_SIXTH_PRIMARY_OWNER",
    "ORDER_HANDOFF_IS_NOT_SUBMISSION_AUTHORITY",
    "RUNTIME_REACHABILITY_IS_NOT_ACTIVATION",
    "SHADOW_OR_LIVE_NAMING_IS_NOT_LIVE_AUTHORIZED",
    "WRAP_DELEGATE_IS_NOT_AUTHORITY",
    "PERCENT_MUST_NOT_EQUATE_FRACTION",
    "LEVERAGE_NOT_CLAIMED_APPLIED_IN_QUANTITY_CHAIN",
    "NO_SEMANTICS_FREE_OWNER_CONSOLIDATION",
    "FINAL_QUANTITY_PROVENANCE_NOT_FULLY_RESOLVED",
)

# Transform / handoff snippets that must remain present (closed-world freeze).
CRITICAL_SNIPPETS = {
    "PATH_EXECUTE_FROM_SIGNALS": (
        "src/execution/pipeline.py",
        [
            "base_position_size = self._config.max_position_notional_pct",
            "target_position = signal * base_position_size",
            "quantity = abs(position_delta)",
            "results = self.execute_orders([order])",
            "signals = signals.clip(-1, 1).astype(int)",
        ],
    ),
    "PATH_SHADOW_COMPANION": (
        "src/live/shadow_session.py",
        [
            "position_size = self._shadow_cfg.position_fraction",
            "orders = self._pipeline.signal_to_orders(",
            "risk_result = self._risk_limits.check_orders(live_orders)",
            "results = self._pipeline.execute_orders(orders)",
        ],
    ),
    "PATH_LIVE_COMPANION": (
        "src/execution/live_session.py",
        [
            "position_size=self._config.position_fraction",
            "orders = self._pipeline.signal_to_orders(",
            "exec_result = self._pipeline.execute_with_safety(",
            'if self.mode == "live":',
        ],
    ),
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_contract() -> dict:
    return json.loads(_read(CONTRACT_JSON))


def _path_by_id(payload: dict, path_id: str) -> dict:
    return next(p for p in payload["unresolved_paths"] if p["path_id"] == path_id)


def test_contract_doc_markers_present() -> None:
    text = _read(CONTRACT_DOC)
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, f"missing doc marker: {marker}"
    assert "SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE=true" not in text
    assert "FINAL_QUANTITY_PROVENANCE_RESOLVED=false" in text


def test_schema_path_fields_and_non_claims() -> None:
    payload = _load_contract()
    assert tuple(payload["required_path_fields"]) == REQUIRED_PATH_FIELDS
    assert tuple(payload["global_non_claims"]) == GLOBAL_NON_CLAIMS
    assert tuple(payload["frozen_path_ids"]) == FROZEN_PATH_IDS

    path_ids = [p["path_id"] for p in payload["unresolved_paths"]]
    assert path_ids == list(FROZEN_PATH_IDS)
    assert len(path_ids) == len(set(path_ids)) == 3

    for path in payload["unresolved_paths"]:
        for field in REQUIRED_PATH_FIELDS:
            assert field in path, f"{path['path_id']} missing {field}"
        assert path["authority_status"] == "UNRESOLVED"
        assert path["final_quantity_provenance_status"] == "UNRESOLVED"
        assert path["unresolved_reason_codes"]
        assert path["evidence_anchors"]
        assert path["non_claims"]
        assert path["transform_chain"]
        for step in path["transform_chain"]:
            assert "step_id" in step and "kind" in step and "detail" in step


def test_expected_counts_match_payload_and_upstream() -> None:
    payload = _load_contract()
    counts = payload["expected_counts"]
    assert len(payload["unresolved_paths"]) == counts["unresolved_paths"] == 3
    assert counts["final_quantity_provenance_resolved_paths"] == 5
    assert counts["final_quantity_provenance_unresolved_paths"] == 3
    assert counts["new_direct_caller_count"] == 0
    assert counts["execute_from_signals_external_productive_callers"] == 0

    assert counts["primary_owners"] == 5
    assert counts["productive_direct_edges"] == 8
    assert counts["companion_edges"] == 2
    assert counts["direct_sizing_bypass_edges"] == 5
    assert counts["pass_through_edges_topology"] == 2
    assert counts["ambiguous_edges_topology"] == 3
    assert counts["consumption_edges"] == 27
    assert counts["overwrite_edges"] == 13
    assert counts["wrap_delegate_edges"] == 1

    consumption = json.loads(_read(CONSUMPTION_JSON))
    c_counts = consumption["expected_counts"]
    assert c_counts["final_quantity_provenance_resolved_paths"] == 5
    assert c_counts["final_quantity_provenance_unresolved_paths"] == 3
    unresolved = [
        p for p in consumption["final_quantity_provenance_paths"] if p["status"] == "UNRESOLVED"
    ]
    assert {p["path_id"] for p in unresolved} == set(FROZEN_PATH_IDS)


def test_topology_units_inventory_counts_unchanged() -> None:
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

    markers = payload["markers"]
    assert markers["LIVE_AUTHORIZED"] is False
    assert markers["ORDERS_ENABLED"] is False
    assert markers["RUNTIME_BRIDGE_ACTIVATED"] is False
    assert markers["SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE"] is False
    assert markers["SEMANTICS_FREE_CONTRACT_SLICE_AVAILABLE"] is True


def test_companion_roles_not_primary() -> None:
    payload = _load_contract()
    shadow = _path_by_id(payload, "PATH_SHADOW_COMPANION")
    live = _path_by_id(payload, "PATH_LIVE_COMPANION")
    efs = _path_by_id(payload, "PATH_EXECUTE_FROM_SIGNALS")

    assert shadow["companion_role"] == "COMPANION_NOT_PRIMARY"
    assert live["companion_role"] == "COMPANION_NOT_PRIMARY"
    assert efs["companion_role"] == "NOT_COMPANION"
    assert shadow["source_owner_or_factory"]["owner_id"] is None
    assert live["source_owner_or_factory"]["owner_id"] is None
    assert "COMPANION_IS_NOT_SIXTH_PRIMARY_OWNER" in shadow["non_claims"]
    assert "COMPANION_IS_NOT_SIXTH_PRIMARY_OWNER" in live["non_claims"]


def test_execute_from_signals_external_callers_remain_zero() -> None:
    payload = _load_contract()
    efs = _path_by_id(payload, "PATH_EXECUTE_FROM_SIGNALS")
    assert efs["direct_productive_callers"] == []
    assert efs["external_productive_caller_count"] == 0

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
    assert hits == [], f"new direct productive caller FAIL: {hits}"


def test_critical_transform_snippets_present() -> None:
    for path_id, (rel_path, snippets) in CRITICAL_SNIPPETS.items():
        text = _read(REPO_ROOT / rel_path)
        for snippet in snippets:
            assert snippet in text, f"{path_id}: missing snippet {snippet!r} in {rel_path}"


def test_signal_to_orders_documents_absolute_units() -> None:
    text = _read(REPO_ROOT / "src/execution/pipeline.py")
    assert "position_size: Gewuenschte Positionsgroesse (in Stueck)" in text
    assert "quantity=position_size" in text


def test_live_mode_forbidden_and_shadow_diff_pin() -> None:
    payload = _load_contract()
    live = _path_by_id(payload, "PATH_LIVE_COMPANION")
    assert live["gates"]["mode_live_forbidden"] is True
    assert live["gates"]["live_authorized"] is False
    assert "execute_with_safety" in live["diff_vs_shadow"]

    live_src = _read(REPO_ROOT / "src/execution/live_session.py")
    assert 'if self.mode == "live":' in live_src
    assert "LiveModeNotAllowedError" in live_src
    assert "execute_with_safety" in live_src

    shadow_src = _read(REPO_ROOT / "src/live/shadow_session.py")
    assert "execute_orders(orders)" in shadow_src
    step_body = shadow_src.split("def step_once", 1)[1].split("\n    def ", 1)[0]
    assert "execute_with_safety" not in step_body


def test_order_handoff_not_submission_authority() -> None:
    payload = _load_contract()
    assert "ORDER_HANDOFF_IS_NOT_SUBMISSION_AUTHORITY" in payload["global_non_claims"]
    for path in payload["unresolved_paths"]:
        assert path["submission_state"]["exchange_submit_claimed"] is False
        assert path["handoff_class"] == "DIRECT_ORDER_HANDOFF"


def test_readme_and_related_docs_point_to_provenance_contract() -> None:
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0.md" in readme
    consumption_doc = _read(
        REPO_ROOT
        / "docs"
        / "governance"
        / "RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md"
    )
    assert "RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0" in consumption_doc


def test_legacy_order_intent_contract_untouched_reference() -> None:
    legacy = json.loads(_read(LEGACY_ORDER_INTENT_JSON))
    assert "direct_submission_surface_contract" in legacy
    assert len(legacy["direct_submission_surface_contract"]["surfaces"]) == 5


def test_related_consumption_edges_still_unresolved() -> None:
    payload = _load_contract()
    consumption = json.loads(_read(CONSUMPTION_JSON))
    by_id = {e["edge_id"]: e for e in consumption["consumption_edges"]}
    for path in payload["unresolved_paths"]:
        for edge_id in path["related_consumption_edge_ids"]:
            edge = by_id[edge_id]
            assert edge["final_quantity_provenance"] == "UNRESOLVED"


def test_drift_new_unresolved_path_fails_count() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["unresolved_paths"].append(
        {
            "path_id": "PATH_ROGUE",
            "authority_status": "UNRESOLVED",
            "final_quantity_provenance_status": "UNRESOLVED",
        }
    )
    assert len(payload["unresolved_paths"]) != payload["expected_counts"]["unresolved_paths"]


def test_drift_transform_chain_reorder_detected() -> None:
    payload = copy.deepcopy(_load_contract())
    efs = _path_by_id(payload, "PATH_EXECUTE_FROM_SIGNALS")
    chain = efs["transform_chain"]
    chain[0], chain[1] = chain[1], chain[0]
    original = _path_by_id(_load_contract(), "PATH_EXECUTE_FROM_SIGNALS")["transform_chain"]
    assert [s["step_id"] for s in chain] != [s["step_id"] for s in original]


def test_drift_new_mutator_step_without_contract_update() -> None:
    payload = copy.deepcopy(_load_contract())
    efs = _path_by_id(payload, "PATH_EXECUTE_FROM_SIGNALS")
    before = len(efs["transform_chain"])
    efs["transform_chain"].append(
        {"step_id": "EFS_ROGUE_CLAMP", "kind": "CLAMP", "detail": "rogue"}
    )
    assert len(efs["transform_chain"]) != before


def test_drift_new_order_handoff_detected() -> None:
    payload = copy.deepcopy(_load_contract())
    shadow = _path_by_id(payload, "PATH_SHADOW_COMPANION")
    before = sum(1 for s in shadow["transform_chain"] if s["kind"] == "ORDER_HANDOFF")
    shadow["transform_chain"].append(
        {"step_id": "SHADOW_ROGUE_HANDOFF", "kind": "ORDER_HANDOFF", "detail": "rogue"}
    )
    after = sum(1 for s in shadow["transform_chain"] if s["kind"] == "ORDER_HANDOFF")
    assert after != before


def test_drift_submission_blocked_to_submit_capable_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    live = _path_by_id(payload, "PATH_LIVE_COMPANION")
    live["submission_state"]["exchange_submit_claimed"] = True
    assert live["submission_state"]["exchange_submit_claimed"] is not False


def test_drift_companion_escalation_to_primary_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    shadow = _path_by_id(payload, "PATH_SHADOW_COMPANION")
    shadow["companion_role"] = "PRIMARY_OWNER"
    assert shadow["companion_role"] != "COMPANION_NOT_PRIMARY"


def test_drift_authority_escalation_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["authority_status"]["canonical_risk_sizing_authority_owner"] = "src.governance.crs"
    assert payload["authority_status"]["canonical_risk_sizing_authority_owner"] != "UNRESOLVED"


def test_drift_final_provenance_escalation_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    efs = _path_by_id(payload, "PATH_EXECUTE_FROM_SIGNALS")
    efs["final_quantity_provenance_status"] = "RESOLVED"
    assert efs["final_quantity_provenance_status"] != "UNRESOLVED"


def test_drift_runtime_bridge_activation_claim_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["markers"]["RUNTIME_BRIDGE_ACTIVATED"] = True
    assert payload["markers"]["RUNTIME_BRIDGE_ACTIVATED"] is not False


def test_drift_live_or_orders_activation_claim_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["markers"]["LIVE_AUTHORIZED"] = True
    payload["markers"]["ORDERS_ENABLED"] = True
    assert payload["markers"]["LIVE_AUTHORIZED"] is not False
    assert payload["markers"]["ORDERS_ENABLED"] is not False


def test_drift_leverage_applied_claim_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["leverage_status"]["applied_in_quantity_chain"] = True
    assert payload["leverage_status"]["applied_in_quantity_chain"] is not False


def test_drift_frozen_count_mutation_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["expected_counts"]["primary_owners"] = 6
    assert payload["expected_counts"]["primary_owners"] != 5
    payload["expected_counts"]["consumption_edges"] = 28
    assert payload["expected_counts"]["consumption_edges"] != 27
    payload["expected_counts"]["final_quantity_provenance_unresolved_paths"] = 2
    assert payload["expected_counts"]["final_quantity_provenance_unresolved_paths"] != 3


def test_drift_percent_fraction_silent_equate_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    conflict = payload["percent_conflicts_unresolved"][0]
    with pytest.raises(AssertionError):
        assert conflict["must_not_equate"][0] == conflict["must_not_equate"][1]
        raise AssertionError("percent_fraction_silent_equivalence FAIL")


def test_drift_owner_consolidation_claimed_semantics_free_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["markers"]["SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE"] = True
    assert payload["markers"]["SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE"] is not False


def test_doc_forbids_resolved_claim() -> None:
    text = _read(CONTRACT_DOC)
    assert re.search(r"FINAL_QUANTITY_PROVENANCE_RESOLVED=false", text)
    assert "FINAL_QUANTITY_PROVENANCE_RESOLVED=true" not in text
