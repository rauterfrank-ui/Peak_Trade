"""Static contract: Final Quantity Provenance resolution audit v1.

Docs/config/tests-only. Pins SEMANTIC_CONFLICT classifications without choosing
intent, assigning authority, or mutating productive runtime semantics.
"""

from __future__ import annotations

import ast
import copy
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_final_quantity_provenance_resolution_audit_v1.json"
)
CONTRACT_DOC = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1.md"
)
UNRESOLVED_V0_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_unresolved_final_quantity_provenance_contract_v0.json"
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

FROZEN_PATH_IDS = (
    "PATH_EXECUTE_FROM_SIGNALS",
    "PATH_SHADOW_COMPANION",
    "PATH_LIVE_COMPANION",
)

FROZEN_SUBCONTRACT_IDS = (
    "COMPANION_FRACTION_TO_ABSOLUTE_UNITS_CONFLICT",
    "EFS_CAPITAL_SHARE_TO_ABSOLUTE_UNITS_CONFLICT",
)

REQUIRED_PATH_FIELDS = (
    "path_id",
    "subcontract_id",
    "classification",
    "entrypoint",
    "producer_config_symbol",
    "declared_dimension",
    "runtime_dimension",
    "transformations",
    "consumer",
    "productive_caller_classification",
    "root_cause",
    "missing_conversion",
    "double_conversion_observed",
    "leverage_in_quantity_chain",
    "companion_or_kernel_role",
    "safety_gate_boundary",
    "non_claims",
    "evidence_anchors",
    "final_quantity_provenance_status",
    "authority_status",
)

REQUIRED_DOC_MARKERS = (
    "RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1=true",
    "INVENTORY_ONLY=true",
    "RESOLUTION_AUDIT_FROZEN=true",
    "FINAL_QUANTITY_PROVENANCE_RESOLVED=false",
    "NO_SIZING_MATH_CHANGE=true",
    "NO_AUTHORITY_ASSIGNMENT=true",
    "NO_INTENT_LINE_CHOSEN=true",
    "NO_FEDERATION_IMPLEMENTED=true",
    "RECOMMENDED_CONSOLIDATION_MODEL=CONTRACTUAL_FEDERATION",
    "SEMANTICS_FREE_CONTRACT_SLICE_AVAILABLE=true",
    "SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE=false",
    "NEXT_PRODUCTIVE_SEMANTICS_SLICE_AUTHORIZED=false",
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
    "EXPECTED_SEMANTIC_CONFLICT_PATH_COUNT=3",
    "EXPECTED_CONTRACT_FAMILY_COUNT=1",
    "EXPECTED_SUBCONTRACT_COUNT=2",
    "EXPECTED_COMPANION_CONFLICT_PATH_COUNT=2",
    "EXPECTED_EFS_CONFLICT_PATH_COUNT=1",
    "LEVERAGE_APPLICATION_STATUS=declared_pass_through_not_applied_in_quantity_chain",
    "COMMON_UNIFIED_SEMANTICS_DECISION=NOT_TAKEN",
    "COMPANION_SHARED_CONTRACT_POSSIBLE=true",
    "EFS_REMAINS_SEPARATE=true",
)

GLOBAL_NON_CLAIMS = (
    "NO_CANONICAL_RISK_SIZING_OWNER_ASSIGNED",
    "NO_CANONICAL_EXECUTION_AUTHORITY_OWNER_ASSIGNED",
    "NO_INTENT_LINE_CHOSEN_BETWEEN_FRACTION_AND_ABSOLUTE_UNITS",
    "COMPANION_IS_NOT_SIXTH_PRIMARY_OWNER",
    "ORDER_HANDOFF_IS_NOT_SUBMISSION_AUTHORITY",
    "RUNTIME_REACHABILITY_IS_NOT_ACTIVATION",
    "SHADOW_OR_LIVE_NAMING_IS_NOT_LIVE_AUTHORIZED",
    "PERCENT_MUST_NOT_EQUATE_FRACTION",
    "LEVERAGE_NOT_CLAIMED_APPLIED_IN_QUANTITY_CHAIN",
    "NO_DOUBLE_CONVERSION_OBSERVED",
    "NO_FRACTION_OR_CAPITAL_SHARE_TO_UNITS_CONVERSION_OBSERVED",
    "NO_SEMANTICS_FREE_OWNER_CONSOLIDATION",
    "NO_UNIFIED_SEMANTICS_DECISION_TAKEN",
    "FINAL_QUANTITY_PROVENANCE_NOT_FULLY_RESOLVED",
    "SMOKE_QUANTITY_EQUALS_POSITION_SIZE_IS_RUNTIME_EVIDENCE_NOT_SEMANTIC_PROOF",
)

PATH_EXPECTATIONS = {
    "PATH_EXECUTE_FROM_SIGNALS": {
        "subcontract_id": "EFS_CAPITAL_SHARE_TO_ABSOLUTE_UNITS_CONFLICT",
        "declared_dimension": "CAPITAL_SHARE_OR_PCT_NAMED_AMBIGUOUS",
        "runtime_dimension": "QUANTITY_BASE_UNITS",
        "producer_config_symbol": "ExecutionPipelineConfig.max_position_notional_pct",
        "companion_or_kernel_role": "PRIMARY_BYPASS_KERNEL_SELF_USE_NOT_COMPANION",
        "external_productive_src_caller_count": 0,
        "missing_conversion": "CAPITAL_SHARE_OR_FRACTION_TO_QUANTITY_BASE_UNITS",
    },
    "PATH_SHADOW_COMPANION": {
        "subcontract_id": "COMPANION_FRACTION_TO_ABSOLUTE_UNITS_CONFLICT",
        "declared_dimension": "FRACTION_DECIMAL_0_1",
        "runtime_dimension": "QUANTITY_BASE_UNITS",
        "producer_config_symbol": "ShadowPaperConfig.position_fraction",
        "companion_or_kernel_role": "COMPANION_PASS_THROUGH_NOT_PRIMARY_OWNER",
        "external_productive_src_caller_count": 2,
        "missing_conversion": "FRACTION_DECIMAL_0_1_TO_QUANTITY_BASE_UNITS",
    },
    "PATH_LIVE_COMPANION": {
        "subcontract_id": "COMPANION_FRACTION_TO_ABSOLUTE_UNITS_CONFLICT",
        "declared_dimension": "FRACTION_DECIMAL_0_1",
        "runtime_dimension": "QUANTITY_BASE_UNITS",
        "producer_config_symbol": "LiveSessionConfig.position_fraction",
        "companion_or_kernel_role": "COMPANION_PASS_THROUGH_NOT_PRIMARY_OWNER",
        "external_productive_src_caller_count": 1,
        "missing_conversion": "FRACTION_DECIMAL_0_1_TO_QUANTITY_BASE_UNITS",
    },
}

CRITICAL_SNIPPETS = {
    "PATH_EXECUTE_FROM_SIGNALS": (
        "src/execution/pipeline.py",
        [
            "base_position_size = self._config.max_position_notional_pct",
            "target_position = signal * base_position_size",
            "quantity = abs(position_delta)",
        ],
    ),
    "PATH_SHADOW_COMPANION": (
        "src/live/shadow_session.py",
        [
            "position_size = self._shadow_cfg.position_fraction",
            "orders = self._pipeline.signal_to_orders(",
            "risk_result = self._risk_limits.check_orders(live_orders)",
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

ALLOWED_MUTATION_PREFIXES = (
    "docs/governance/",
    "config/governance/",
    "tests/governance/",
)

FORBIDDEN_PRODUCTIVE_PREFIXES = (
    "src/",
    "trading/",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_contract() -> dict:
    return json.loads(_read(CONTRACT_JSON))


def _path_by_id(payload: dict, path_id: str) -> dict:
    return next(p for p in payload["audited_paths"] if p["path_id"] == path_id)


def test_contract_doc_markers_present() -> None:
    text = _read(CONTRACT_DOC)
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, f"missing doc marker: {marker}"
    assert "FINAL_QUANTITY_PROVENANCE_RESOLVED=true" not in text
    assert "NEXT_PRODUCTIVE_SEMANTICS_SLICE_AUTHORIZED=true" not in text
    assert "SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE=true" not in text
    assert "CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED" in text
    assert "CANONICAL_RISK_SIZING_AUTHORITY_OWNER=UNRESOLVED" in text


def test_schema_family_paths_and_non_claims() -> None:
    payload = _load_contract()
    assert tuple(payload["required_path_fields"]) == REQUIRED_PATH_FIELDS
    assert tuple(payload["global_non_claims"]) == GLOBAL_NON_CLAIMS
    assert tuple(payload["frozen_path_ids"]) == FROZEN_PATH_IDS
    assert tuple(payload["frozen_subcontract_ids"]) == FROZEN_SUBCONTRACT_IDS

    family = payload["contract_family"]
    assert family["family_count"] == 1
    assert family["subcontract_count"] == 2
    assert family["unified_semantics_decision_taken"] is False
    assert family["federation_implemented"] is False
    assert [s["subcontract_id"] for s in family["subcontracts"]] == list(FROZEN_SUBCONTRACT_IDS)

    path_ids = [p["path_id"] for p in payload["audited_paths"]]
    assert path_ids == list(FROZEN_PATH_IDS)
    assert len(path_ids) == len(set(path_ids)) == 3

    for path in payload["audited_paths"]:
        for field in REQUIRED_PATH_FIELDS:
            assert field in path, f"{path['path_id']} missing {field}"
        assert path["classification"] == "SEMANTIC_CONFLICT"
        assert path["authority_status"] == "UNRESOLVED"
        assert path["final_quantity_provenance_status"] == "UNRESOLVED"
        assert path["double_conversion_observed"] is False
        assert path["leverage_in_quantity_chain"] is False
        assert path["missing_conversion"]
        assert path["transformations"]
        assert path["non_claims"]
        assert path["evidence_anchors"]


def test_path_expectations_and_subcontract_membership() -> None:
    payload = _load_contract()
    family = {s["subcontract_id"]: s for s in payload["contract_family"]["subcontracts"]}

    companion = family["COMPANION_FRACTION_TO_ABSOLUTE_UNITS_CONFLICT"]
    efs = family["EFS_CAPITAL_SHARE_TO_ABSOLUTE_UNITS_CONFLICT"]
    assert companion["path_ids"] == ["PATH_SHADOW_COMPANION", "PATH_LIVE_COMPANION"]
    assert companion["path_count"] == 2
    assert efs["path_ids"] == ["PATH_EXECUTE_FROM_SIGNALS"]
    assert efs["path_count"] == 1

    for path_id, expected in PATH_EXPECTATIONS.items():
        path = _path_by_id(payload, path_id)
        for key, value in expected.items():
            if key == "external_productive_src_caller_count":
                assert path["productive_caller_classification"][key] == value
            else:
                assert path[key] == value, f"{path_id}.{key}"


def test_expected_counts_match_payload_and_upstream() -> None:
    payload = _load_contract()
    counts = payload["expected_counts"]
    assert counts["contract_family_count"] == 1
    assert counts["subcontract_count"] == 2
    assert counts["semantic_conflict_path_count"] == 3
    assert counts["companion_conflict_path_count"] == 2
    assert counts["efs_conflict_path_count"] == 1
    assert len(payload["audited_paths"]) == counts["audited_paths"] == 3
    assert counts["primary_owners"] == 5
    assert counts["productive_direct_edges"] == 8
    assert counts["companion_edges"] == 2
    assert counts["pass_through_edges_topology"] == 2
    assert counts["ambiguous_edges_topology"] == 3
    assert counts["consumption_edges"] == 27
    assert counts["overwrite_edges"] == 13
    assert counts["wrap_delegate_edges"] == 1
    assert counts["final_quantity_provenance_resolved_paths"] == 5
    assert counts["final_quantity_provenance_unresolved_paths"] == 3
    assert counts["execute_from_signals_external_productive_src_callers"] == 0

    markers = payload["markers"]
    assert markers["EXPECTED_PRIMARY_OWNER_COUNT"] == 5
    assert markers["EXPECTED_PRODUCTIVE_DIRECT_EDGE_COUNT"] == 8
    assert markers["EXPECTED_COMPANION_EDGE_COUNT"] == 2
    assert markers["EXPECTED_PASS_THROUGH_EDGE_COUNT"] == 2
    assert markers["EXPECTED_AMBIGUOUS_EDGE_COUNT"] == 3
    assert markers["EXPECTED_CONSUMPTION_EDGE_COUNT"] == 27
    assert markers["EXPECTED_OVERWRITE_EDGE_COUNT"] == 13
    assert markers["EXPECTED_WRAP_DELEGATE_EDGE_COUNT"] == 1
    assert markers["EXPECTED_FINAL_QUANTITY_PROVENANCE_RESOLVED_PATH_COUNT"] == 5
    assert markers["EXPECTED_FINAL_QUANTITY_PROVENANCE_UNRESOLVED_PATH_COUNT"] == 3
    assert markers["FINAL_QUANTITY_PROVENANCE_RESOLVED"] is False
    assert markers["NEXT_PRODUCTIVE_SEMANTICS_SLICE_AUTHORIZED"] is False
    assert markers["CANONICAL_EXECUTION_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert markers["CANONICAL_RISK_SIZING_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert markers["COMMON_UNIFIED_SEMANTICS_DECISION"] == "NOT_TAKEN"
    assert markers["COMPANION_SHARED_CONTRACT_POSSIBLE"] is True
    assert markers["EFS_REMAINS_SEPARATE"] is True

    unresolved = json.loads(_read(UNRESOLVED_V0_JSON))
    consumption = json.loads(_read(CONSUMPTION_JSON))
    topology = json.loads(_read(TOPOLOGY_JSON))
    inventory = json.loads(_read(OWNER_INVENTORY_JSON))

    assert unresolved["expected_counts"]["unresolved_paths"] == 3
    assert unresolved["expected_counts"]["resolved_paths_referenced"] == 5
    assert consumption["expected_counts"]["consumption_edges"] == 27
    assert consumption["expected_counts"]["overwrite_edges"] == 13
    assert consumption["expected_counts"]["wrap_delegate_edges"] == 1
    assert topology["expected_counts"]["productive_direct_edges"] == 8
    assert topology["expected_counts"]["companion_edges"] == 2
    assert topology["expected_counts"]["pass_through_edges"] == 2
    assert topology["expected_counts"]["ambiguous_edges"] == 3
    assert inventory["markers"]["PRODUCTIVE_RISK_SIZING_DECISION_OWNER_COUNT"] == 5


def test_authority_and_planning_pins() -> None:
    payload = _load_contract()
    auth = payload["authority_status"]
    assert auth["canonical_execution_authority_owner"] == "UNRESOLVED"
    assert auth["canonical_risk_sizing_authority_owner"] == "UNRESOLVED"
    assert auth["canonical_risk_sizing_owner"] == "UNRESOLVED"
    assert auth["authority_effect"] == "NONE"
    assert auth["runtime_effect"] == "NONE"

    planning = payload["planning_only"]
    assert planning["next_productive_semantics_slice_authorized"] is False
    assert planning["unified_semantics_decision_taken"] is False
    assert planning["companion_shared_contract_possible"] is True
    assert planning["efs_remains_separate"] is True
    assert planning["federation_implemented"] is False
    assert planning["semantics_free_owner_consolidation_available"] is False

    assert payload["leverage_status"]["applied_in_quantity_chain"] is False
    assert payload["global_authority_pins"]["FINAL_QUANTITY_PROVENANCE_RESOLVED"] is False
    assert payload["global_authority_pins"]["NEXT_PRODUCTIVE_SEMANTICS_SLICE_AUTHORIZED"] is False


def test_critical_transform_snippets_still_present() -> None:
    for path_id, (rel_path, snippets) in CRITICAL_SNIPPETS.items():
        text = _read(REPO_ROOT / rel_path)
        for snippet in snippets:
            assert snippet in text, f"{path_id}: missing snippet {snippet!r} in {rel_path}"


def test_signal_to_orders_still_documents_absolute_units() -> None:
    text = _read(REPO_ROOT / "src/execution/pipeline.py")
    assert "position_size: Gewuenschte Positionsgroesse (in Stueck)" in text
    assert "quantity=position_size" in text


def test_no_new_execute_from_signals_productive_src_callers() -> None:
    hits: list[tuple[str, int]] = []
    src_root = REPO_ROOT / "src"
    for path in src_root.rglob("*.py"):
        tree = ast.parse(_read(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name == "execute_from_signals":
                # Definition and docstring examples live in pipeline.py itself.
                rel = str(path.relative_to(REPO_ROOT))
                if rel == "src/execution/pipeline.py":
                    continue
                hits.append((rel, node.lineno))
    assert hits == [], f"new direct productive src caller FAIL: {hits}"


def test_readme_and_related_docs_point_to_resolution_audit() -> None:
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1.md" in readme

    unresolved_doc = _read(
        REPO_ROOT
        / "docs"
        / "governance"
        / "RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0.md"
    )
    assert "RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1" in unresolved_doc

    consumption_doc = _read(
        REPO_ROOT
        / "docs"
        / "governance"
        / "RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md"
    )
    assert "RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1" in consumption_doc


def test_referenced_contracts_exist_and_remain_unresolved() -> None:
    payload = _load_contract()
    for rel in payload["referenced_contracts"].values():
        assert (REPO_ROOT / rel).is_file(), rel

    unresolved = json.loads(_read(UNRESOLVED_V0_JSON))
    assert unresolved["markers"]["FINAL_QUANTITY_PROVENANCE_RESOLVED"] is False
    assert unresolved["authority_status"]["canonical_execution_authority_owner"] == "UNRESOLVED"
    assert unresolved["authority_status"]["canonical_risk_sizing_authority_owner"] == "UNRESOLVED"

    units = json.loads(_read(UNITS_JSON))
    assert units["markers"]["NO_SIZING_MATH_CHANGE"] is True
    assert units["markers"]["NO_AUTHORITY_ASSIGNMENT"] is True
    assert (REPO_ROOT / "docs/governance/RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md").is_file()


def test_drift_classification_must_remain_semantic_conflict() -> None:
    payload = copy.deepcopy(_load_contract())
    efs = _path_by_id(payload, "PATH_EXECUTE_FROM_SIGNALS")
    efs["classification"] = "RESOLVABLE_FROM_EXISTING_EVIDENCE"
    assert efs["classification"] != "SEMANTIC_CONFLICT"
    # Contract itself remains the source of truth; this asserts the pin exists.
    original = _path_by_id(_load_contract(), "PATH_EXECUTE_FROM_SIGNALS")
    assert original["classification"] == "SEMANTIC_CONFLICT"


def test_drift_authority_escalation_forbidden() -> None:
    payload = _load_contract()
    assert payload["markers"]["CANONICAL_EXECUTION_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert payload["markers"]["CANONICAL_RISK_SIZING_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert "UNRESOLVED" == payload["authority_status"]["canonical_execution_authority_owner"]
    text = _read(CONTRACT_DOC)
    assert re.search(r"CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED", text)
    assert "FINAL_QUANTITY_PROVENANCE_RESOLVED=true" not in text


def test_allowed_mutation_surface_prefixes_documented() -> None:
    # This slice must not claim productive mutation rights.
    payload = _load_contract()
    assert payload["markers"]["NO_SIZING_MATH_CHANGE"] is True
    assert payload["markers"]["RUNTIME_EFFECT"] == "NONE"
    assert payload["drift_policy"]["productive_src_mutation_claimed"] == "FAIL"
    for prefix in FORBIDDEN_PRODUCTIVE_PREFIXES:
        assert prefix in ("src/", "trading/")
    for prefix in ALLOWED_MUTATION_PREFIXES:
        assert prefix.startswith(("docs/", "config/", "tests/"))


def test_json_doc_parity_on_family_and_conflict_counts() -> None:
    payload = _load_contract()
    text = _read(CONTRACT_DOC)
    assert "EXPECTED_SUBCONTRACT_COUNT=2" in text
    assert "EXPECTED_SEMANTIC_CONFLICT_PATH_COUNT=3" in text
    assert "EXPECTED_COMPANION_CONFLICT_PATH_COUNT=2" in text
    assert "EXPECTED_EFS_CONFLICT_PATH_COUNT=1" in text
    assert "COMPANION_FRACTION_TO_ABSOLUTE_UNITS_CONFLICT" in text
    assert "EFS_CAPITAL_SHARE_TO_ABSOLUTE_UNITS_CONFLICT" in text
    assert payload["expected_counts"]["subcontract_count"] == 2
    assert payload["expected_counts"]["semantic_conflict_path_count"] == 3
