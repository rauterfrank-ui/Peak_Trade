"""Static contract: Companion intent freeze + EFS quarantine v1.

Docs/config/tests-only. Freezes Companion declared intent to FRACTION_DECIMAL_0_1
and quarantines execute_from_signals without runtime math, authority assignment,
or productive src/ mutation.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_companion_intent_freeze_and_efs_quarantine_v1.json"
)
CONTRACT_DOC = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "RISK_SIZING_COMPANION_INTENT_FREEZE_AND_EFS_QUARANTINE_V1.md"
)
RESOLUTION_AUDIT_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_final_quantity_provenance_resolution_audit_v1.json"
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

EFS_DEFINITION_FILE = "src/execution/pipeline.py"

EXPECTED_EFS_ALLOWLIST = (
    "scripts/run_offline_realtime_ma_crossover.py",
    "scripts/run_shadow_execution.py",
)

REQUIRED_DOC_MARKERS = (
    "RISK_SIZING_COMPANION_INTENT_FREEZE_AND_EFS_QUARANTINE_V1=true",
    "INVENTORY_ONLY=true",
    "COMPANION_INTENT_FROZEN=true",
    "COMPANION_SHARED_CONTRACT=true",
    "COMPANION_DECLARED_INTENT=FRACTION_DECIMAL_0_1",
    "COMPANION_RUNTIME_CONVERSION_PRESENT=false",
    "COMPANION_RUNTIME_PASS_THROUGH_TO_QUANTITY_CONSUMER=true",
    "COMPANION_MUST_NOT_REINTERPRET_AS_ABSOLUTE_UNITS=true",
    "EFS_QUARANTINED=true",
    "EFS_DEPRECATED=true",
    "EFS_REMAINS_SEPARATE=true",
    "EFS_NEW_PRODUCTIVE_SRC_CALLER_GUARD=true",
    "FINAL_QUANTITY_PROVENANCE_RESOLVED=false",
    "NO_SIZING_MATH_CHANGE=true",
    "NO_FRACTION_TO_UNITS_CONVERSION=true",
    "NO_QUANTITY_MATH_CHANGE=true",
    "NO_AUTHORITY_ASSIGNMENT=true",
    "NO_REWIRE=true",
    "NO_EFS_REMOVAL=true",
    "NO_SIGNAL_TO_ORDERS_MUTATION=true",
    "NO_CRS_MATH_CHANGE=true",
    "NO_NEW_PRIMARY_AUTHORITY=true",
    "AUTHORITY_EFFECT=NONE",
    "RUNTIME_EFFECT=NONE",
    "RUNTIME_SEMANTICS_CHANGED=false",
    "QUANTITY_MATH_CHANGED=false",
    "TRADING_CORE_CHANGED=false",
    "LIVE_AUTHORIZED=false",
    "ORDERS_ENABLED=false",
    "RUNTIME_BRIDGE_ACTIVATED=false",
    "CANONICAL_RISK_SIZING_OWNER=UNRESOLVED",
    "CANONICAL_RISK_SIZING_AUTHORITY_OWNER=UNRESOLVED",
    "CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED",
    "CANONICAL_EQUITY_OWNER=UNRESOLVED",
    "CANONICAL_PRICE_OWNER=UNRESOLVED",
    "CANONICAL_INSTRUMENT_METADATA_OWNER=UNRESOLVED",
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
    "EXPECTED_COMPANION_CONFLICT_PATH_COUNT=2",
    "EXPECTED_EFS_CONFLICT_PATH_COUNT=1",
    "EXPECTED_EFS_PRODUCTIVE_SRC_CALLER_COUNT=0",
    "EXPECTED_EFS_SCRIPT_OR_OFFLINE_CALLER_COUNT=2",
    "EXPECTED_EFS_QUARANTINE_CONTRACT_COUNT=1",
    "COMMON_UNIFIED_SEMANTICS_DECISION=NOT_TAKEN",
    "NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=false",
)

GLOBAL_NON_CLAIMS = (
    "NO_CANONICAL_RISK_SIZING_OWNER_ASSIGNED",
    "NO_CANONICAL_EXECUTION_AUTHORITY_OWNER_ASSIGNED",
    "NO_CANONICAL_EQUITY_OWNER_ASSIGNED",
    "NO_CANONICAL_PRICE_OWNER_ASSIGNED",
    "NO_CANONICAL_INSTRUMENT_METADATA_OWNER_ASSIGNED",
    "FINAL_QUANTITY_PROVENANCE_NOT_FULLY_RESOLVED",
    "COMPANION_IS_NOT_SIXTH_PRIMARY_OWNER",
    "FRACTION_NOT_CLAIMED_ALREADY_CONVERTED_TO_UNITS",
    "EFS_IS_NOT_COMPANION_SEMANTICS_AUTHORITY",
    "NO_FRACTION_TO_UNITS_CONVERSION_IN_THIS_SLICE",
    "NO_QUANTITY_MATH_CHANGE_IN_THIS_SLICE",
    "NO_REWIRE",
    "NO_SIGNAL_TO_ORDERS_MUTATION",
    "NO_SHADOW_LIVE_ORDER_GENERATION_MUTATION",
    "NO_CRS_MATH_CHANGE",
    "NO_UNIFIED_SEMANTICS_DECISION_ACROSS_COMPANION_AND_EFS",
    "RUNTIME_REACHABILITY_IS_NOT_ACTIVATION",
    "SHADOW_OR_LIVE_NAMING_IS_NOT_LIVE_AUTHORIZED",
    "PERCENT_MUST_NOT_EQUATE_FRACTION",
    "SMOKE_QUANTITY_EQUALS_POSITION_SIZE_IS_RUNTIME_EVIDENCE_NOT_SEMANTIC_PROOF",
)

CRITICAL_SNIPPETS = {
    "PATH_SHADOW_COMPANION": (
        "src/live/shadow_session.py",
        [
            "position_size = self._shadow_cfg.position_fraction",
            "orders = self._pipeline.signal_to_orders(",
        ],
    ),
    "PATH_LIVE_COMPANION": (
        "src/execution/live_session.py",
        [
            "position_size=self._config.position_fraction",
            "orders = self._pipeline.signal_to_orders(",
        ],
    ),
    "PATH_EXECUTE_FROM_SIGNALS": (
        "src/execution/pipeline.py",
        [
            "def execute_from_signals(",
            "base_position_size = self._config.max_position_notional_pct",
            "target_position = signal * base_position_size",
        ],
    ),
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_contract() -> dict:
    return json.loads(_read(CONTRACT_JSON))


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _find_execute_from_signals_calls(root: Path) -> list[tuple[str, int]]:
    hits: list[tuple[str, int]] = []
    for path in root.rglob("*.py"):
        tree = ast.parse(_read(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if _call_name(node.func) == "execute_from_signals":
                rel = str(path.relative_to(REPO_ROOT))
                hits.append((rel, node.lineno))
    return hits


def test_contract_doc_markers_present() -> None:
    text = _read(CONTRACT_DOC)
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, f"missing doc marker: {marker}"
    assert "FINAL_QUANTITY_PROVENANCE_RESOLVED=true" not in text
    assert "COMPANION_RUNTIME_CONVERSION_PRESENT=true" not in text
    assert "CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED" in text
    assert "CANONICAL_EQUITY_OWNER=UNRESOLVED" in text
    assert "CANONICAL_PRICE_OWNER=UNRESOLVED" in text
    assert "CANONICAL_INSTRUMENT_METADATA_OWNER=UNRESOLVED" in text
    assert "NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=true" not in text


def test_companion_shared_intent_freeze_pins() -> None:
    payload = _load_contract()
    companion = payload["companion_shared_subcontract"]
    markers = payload["markers"]

    assert markers["COMPANION_INTENT_FROZEN"] is True
    assert markers["COMPANION_SHARED_CONTRACT"] is True
    assert markers["COMPANION_DECLARED_INTENT"] == "FRACTION_DECIMAL_0_1"
    assert markers["COMPANION_RUNTIME_CONVERSION_PRESENT"] is False
    assert markers["COMPANION_RUNTIME_PASS_THROUGH_TO_QUANTITY_CONSUMER"] is True
    assert markers["COMPANION_MUST_NOT_REINTERPRET_AS_ABSOLUTE_UNITS"] is True

    assert companion["subcontract_id"] == "COMPANION_INTENT_FRACTION_DECIMAL_0_1"
    assert companion["path_ids"] == ["PATH_SHADOW_COMPANION", "PATH_LIVE_COMPANION"]
    assert companion["path_count"] == 2
    assert companion["declared_intent"] == "FRACTION_DECIMAL_0_1"
    assert companion["declared_intent_status"] == "FROZEN"
    assert companion["sizing_role"] == "COMPANION_PASS_THROUGH_NOT_PRIMARY_OWNER"
    assert companion["topology_edge_ids"] == [
        "COMPANION_SHADOW_POSITION_FRACTION",
        "COMPANION_LIVE_SESSION_POSITION_FRACTION",
    ]

    runtime = companion["runtime_contradiction"]
    assert runtime["conversion_present"] is False
    assert runtime["pass_through_observed"] is True
    assert runtime["runtime_consumer"] == "ExecutionPipeline.signal_to_orders"
    assert runtime["runtime_consumer_documented_dimension"] == "QUANTITY_BASE_UNITS"
    assert runtime["missing_conversion"] == "FRACTION_DECIMAL_0_1_TO_QUANTITY_BASE_UNITS"

    assert companion["must_not_silently_reinterpret_as_absolute_units"] == [
        "docs",
        "cli",
        "profiles",
        "config",
    ]
    assert "FRACTION_NOT_CLAIMED_ALREADY_CONVERTED_TO_UNITS" in companion["non_claims"]
    assert "COMPANION_IS_NOT_SIXTH_PRIMARY_OWNER" in companion["non_claims"]


def test_efs_quarantine_pins_and_allowlist() -> None:
    payload = _load_contract()
    efs = payload["efs_quarantine"]
    markers = payload["markers"]

    assert markers["EFS_QUARANTINED"] is True
    assert markers["EFS_DEPRECATED"] is True
    assert markers["EFS_REMAINS_SEPARATE"] is True
    assert markers["EFS_NEW_PRODUCTIVE_SRC_CALLER_GUARD"] is True
    assert markers["NO_EFS_REMOVAL"] is True

    assert efs["subcontract_id"] == "EFS_DEPRECATED_QUARANTINED_PATH"
    assert efs["path_id"] == "PATH_EXECUTE_FROM_SIGNALS"
    assert efs["status"] == "DEPRECATED_QUARANTINED"
    assert efs["remains_separate_from_companion"] is True
    assert efs["no_shared_semantics_authority_with_companion"] is True
    assert efs["productive_src_caller_count"] == 0
    assert efs["script_or_offline_caller_count"] == 2
    assert efs["new_productive_src_caller_policy"] == "FAIL"
    assert efs["removal_in_this_slice"] is False
    assert efs["numeric_runtime_change_in_this_slice"] is False
    assert efs["definition_file"] == EFS_DEFINITION_FILE

    allowlist = [row["path"] for row in efs["script_or_offline_allowlist"]]
    assert tuple(allowlist) == EXPECTED_EFS_ALLOWLIST
    for path in allowlist:
        assert (REPO_ROOT / path).is_file(), path


def test_authority_pins_remain_unresolved() -> None:
    payload = _load_contract()
    auth = payload["authority_status"]
    pins = payload["global_authority_pins"]
    markers = payload["markers"]

    for key in (
        "canonical_execution_authority_owner",
        "canonical_risk_sizing_authority_owner",
        "canonical_risk_sizing_owner",
        "canonical_equity_owner",
        "canonical_price_owner",
        "canonical_instrument_metadata_owner",
    ):
        assert auth[key] == "UNRESOLVED", key

    assert auth["final_quantity_provenance_resolved"] is False
    assert auth["no_candidate_implicitly_elevated_to_owner"] is True
    assert auth["authority_effect"] == "NONE"
    assert auth["runtime_effect"] == "NONE"

    assert pins["CANONICAL_EXECUTION_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert pins["CANONICAL_RISK_SIZING_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert pins["CANONICAL_EQUITY_OWNER"] == "UNRESOLVED"
    assert pins["CANONICAL_PRICE_OWNER"] == "UNRESOLVED"
    assert pins["CANONICAL_INSTRUMENT_METADATA_OWNER"] == "UNRESOLVED"
    assert pins["FINAL_QUANTITY_PROVENANCE_RESOLVED"] is False
    assert pins["LIVE_AUTHORIZED"] is False
    assert pins["ORDERS_ENABLED"] is False
    assert pins["RUNTIME_BRIDGE_ACTIVATED"] is False
    assert pins["NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED"] is False

    assert markers["FINAL_QUANTITY_PROVENANCE_RESOLVED"] is False
    assert markers["RUNTIME_SEMANTICS_CHANGED"] is False
    assert markers["QUANTITY_MATH_CHANGED"] is False
    assert markers["TRADING_CORE_CHANGED"] is False


def test_global_non_claims_and_drift_policy() -> None:
    payload = _load_contract()
    assert tuple(payload["global_non_claims"]) == GLOBAL_NON_CLAIMS
    drift = payload["drift_policy"]
    assert drift["companion_intent_not_fraction_decimal_0_1"] == "FAIL"
    assert drift["companion_reinterpreted_as_absolute_units_in_docs_cli_profile_config"] == "FAIL"
    assert drift["companion_conversion_claimed_present"] == "FAIL"
    assert drift["efs_new_productive_src_caller"] == "FAIL"
    assert drift["efs_script_allowlist_drift"] == "FAIL"
    assert drift["equity_price_instrument_or_final_quantity_owner_assigned"] == "FAIL"
    assert drift["fraction_to_units_conversion_claimed"] == "FAIL"
    assert drift["mutation_of_frozen_counts_5_8_2_5_2_3"] == "FAIL"


def test_baseline_counts_unchanged_quarantine_counts_separately() -> None:
    payload = _load_contract()
    counts = payload["expected_counts"]
    markers = payload["markers"]

    assert counts["primary_owners"] == 5
    assert counts["productive_direct_edges"] == 8
    assert counts["companion_edges"] == 2
    assert counts["direct_sizing_bypass_edges"] == 5
    assert counts["pass_through_edges_topology"] == 2
    assert counts["ambiguous_edges_topology"] == 3
    assert counts["consumption_edges"] == 27
    assert counts["overwrite_edges"] == 13
    assert counts["wrap_delegate_edges"] == 1
    assert counts["final_quantity_provenance_resolved_paths"] == 5
    assert counts["final_quantity_provenance_unresolved_paths"] == 3
    assert counts["semantic_conflict_paths"] == 3
    assert counts["companion_conflict_paths"] == 2
    assert counts["efs_conflict_paths"] == 1
    assert counts["efs_productive_src_callers"] == 0
    assert counts["efs_script_or_offline_callers"] == 2
    assert counts["efs_quarantine_contract_count"] == 1
    assert counts["companion_shared_subcontract_count"] == 1

    assert markers["EXPECTED_EFS_QUARANTINE_CONTRACT_COUNT"] == 1
    assert markers["EXPECTED_EFS_PRODUCTIVE_SRC_CALLER_COUNT"] == 0
    assert markers["EXPECTED_EFS_SCRIPT_OR_OFFLINE_CALLER_COUNT"] == 2

    unresolved = json.loads(_read(UNRESOLVED_V0_JSON))
    consumption = json.loads(_read(CONSUMPTION_JSON))
    topology = json.loads(_read(TOPOLOGY_JSON))
    inventory = json.loads(_read(OWNER_INVENTORY_JSON))
    audit = json.loads(_read(RESOLUTION_AUDIT_JSON))

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
    assert audit["expected_counts"]["semantic_conflict_path_count"] == 3
    assert audit["expected_counts"]["companion_conflict_path_count"] == 2
    assert audit["expected_counts"]["efs_conflict_path_count"] == 1
    assert audit["markers"]["FINAL_QUANTITY_PROVENANCE_RESOLVED"] is False
    assert audit["markers"]["CANONICAL_EXECUTION_AUTHORITY_OWNER"] == "UNRESOLVED"


def test_no_new_execute_from_signals_productive_src_callers() -> None:
    hits = [
        (rel, line)
        for rel, line in _find_execute_from_signals_calls(REPO_ROOT / "src")
        if rel != EFS_DEFINITION_FILE
    ]
    assert hits == [], f"EFS new productive src caller FAIL: {hits}"


def test_efs_script_or_offline_allowlist_matches_repo() -> None:
    payload = _load_contract()
    allowlist = {row["path"] for row in payload["efs_quarantine"]["script_or_offline_allowlist"]}
    assert allowlist == set(EXPECTED_EFS_ALLOWLIST)

    script_hits = {rel for rel, _line in _find_execute_from_signals_calls(REPO_ROOT / "scripts")}
    assert script_hits == set(EXPECTED_EFS_ALLOWLIST), (
        f"EFS script allowlist drift FAIL: observed={sorted(script_hits)} "
        f"expected={list(EXPECTED_EFS_ALLOWLIST)}"
    )


def test_critical_runtime_snippets_unchanged() -> None:
    for path_id, (rel_path, snippets) in CRITICAL_SNIPPETS.items():
        text = _read(REPO_ROOT / rel_path)
        for snippet in snippets:
            assert snippet in text, f"{path_id}: missing snippet {snippet!r} in {rel_path}"


def test_signal_to_orders_still_documents_absolute_units() -> None:
    text = _read(REPO_ROOT / "src/execution/pipeline.py")
    assert "position_size: Gewuenschte Positionsgroesse (in Stueck)" in text
    assert "quantity=position_size" in text


def test_companion_fraction_validators_still_present() -> None:
    live = _read(REPO_ROOT / "src/execution/live_session.py")
    assert "0.0 < self.position_fraction <= 1.0" in live
    assert "Anteil des Kapitals" in live

    profiles = _read(REPO_ROOT / "src/live/testnet_profiles.py")
    assert "0 < profile.position_fraction <= 1.0" in profiles


def test_readme_and_related_docs_point_to_new_contract() -> None:
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "RISK_SIZING_COMPANION_INTENT_FREEZE_AND_EFS_QUARANTINE_V1.md" in readme

    audit_doc = _read(
        REPO_ROOT
        / "docs"
        / "governance"
        / "RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1.md"
    )
    assert "RISK_SIZING_COMPANION_INTENT_FREEZE_AND_EFS_QUARANTINE_V1" in audit_doc


def test_referenced_contracts_exist() -> None:
    payload = _load_contract()
    for rel in payload["referenced_contracts"].values():
        assert (REPO_ROOT / rel).is_file(), rel
    assert CONTRACT_JSON.is_file()
    assert CONTRACT_DOC.is_file()
    units = json.loads(_read(UNITS_JSON))
    assert units["markers"]["NO_SIZING_MATH_CHANGE"] is True


def test_no_authority_escalation_language_in_doc() -> None:
    text = _read(CONTRACT_DOC)
    assert re.search(r"CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED", text)
    assert re.search(r"CANONICAL_RISK_SIZING_AUTHORITY_OWNER=UNRESOLVED", text)
    assert re.search(r"CANONICAL_EQUITY_OWNER=UNRESOLVED", text)
    assert re.search(r"CANONICAL_PRICE_OWNER=UNRESOLVED", text)
    assert re.search(r"CANONICAL_INSTRUMENT_METADATA_OWNER=UNRESOLVED", text)
    assert "FINAL_QUANTITY_PROVENANCE_RESOLVED=true" not in text
    assert "COMPANION_RUNTIME_CONVERSION_PRESENT=true" not in text


def test_companion_and_efs_remain_separate_authorities() -> None:
    payload = _load_contract()
    assert payload["markers"]["EFS_REMAINS_SEPARATE"] is True
    assert payload["markers"]["COMMON_UNIFIED_SEMANTICS_DECISION"] == "NOT_TAKEN"
    assert payload["efs_quarantine"]["no_shared_semantics_authority_with_companion"] is True
    assert "NO_UNIFIED_SEMANTICS_DECISION_ACROSS_COMPANION_AND_EFS" in payload["global_non_claims"]
