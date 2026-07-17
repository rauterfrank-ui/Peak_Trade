"""Static contract: Productive Input Provenance Binding v1.

Docs/config/tests-only. Models fail-closed Companion Shadow/Live provenance
contracts for Equity, Reference Price, and Instrument Metadata without
conversion math, owner assignment, productive defaults, or caller rewire.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_productive_input_provenance_binding_v1.json"
)
CONTRACT_DOC = (
    REPO_ROOT / "docs" / "governance" / "RISK_SIZING_PRODUCTIVE_INPUT_PROVENANCE_BINDING_V1.md"
)
COMPANION_FREEZE_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_companion_intent_freeze_and_efs_quarantine_v1.json"
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

REQUIRED_DOC_MARKERS = (
    "RISK_SIZING_PRODUCTIVE_INPUT_PROVENANCE_BINDING_V1=true",
    "INVENTORY_ONLY=true",
    "PROVENANCE_BINDING_FROZEN=true",
    "CONVERSION_READY=false",
    "CONVERSION_MATH_ADDED=false",
    "PRODUCTIVE_CALLER_REWIRED=false",
    "OWNER_ASSIGNED=false",
    "PRODUCTIVE_DEFAULT_COUNT=0",
    "NO_PRODUCTIVE_DEFAULTS=true",
    "NO_FRACTION_TO_UNITS_CONVERSION=true",
    "NO_QUANTITY_MATH_CHANGE=true",
    "NO_AUTHORITY_ASSIGNMENT=true",
    "NO_REWIRE=true",
    "NO_SIGNAL_TO_ORDERS_MUTATION=true",
    "NO_CRS_MATH_CHANGE=true",
    "NO_LEVERAGE_MULTIPLICATION=true",
    "NO_START_BALANCE_AS_RUNNING_EQUITY=true",
    "NO_CANDLE_CLOSE_AS_PRICE_AUTHORITY=true",
    "NO_CMC_MARK_AS_PRICE_AUTHORITY=true",
    "NO_MONITOR_BALANCE_AS_EQUITY_AUTHORITY=true",
    "COMPANION_INTENT=FRACTION_DECIMAL_0_1",
    "COMPANION_PASS_THROUGH_UNCHANGED=true",
    "COMPANION_RUNTIME_CONVERSION_PRESENT=false",
    "SHADOW_LIVE_INPUT_PARITY=PARITY_ON_ABSENCE",
    "EQUITY_PROVENANCE_STATUS=REQUIRED_INPUT_MISSING",
    "PRICE_PROVENANCE_STATUS=REQUIRED_INPUT_MISSING",
    "INSTRUMENT_METADATA_PROVENANCE_STATUS=REQUIRED_INPUT_MISSING",
    "ACCOUNT_BINDING_STATUS=UNRESOLVED",
    "VENUE_BINDING_STATUS=UNRESOLVED",
    "INSTRUMENT_BINDING_STATUS=UNRESOLVED",
    "FRESHNESS_CONTRACT_STATUS=FAIL_CLOSED_MISSING",
    "CRS_CONSUMES_INPUTS_DOES_NOT_OWN_VENUE_ACCOUNT_TRUTH=true",
    "EFS_QUARANTINED=true",
    "RUNTIME_BRIDGE_ACTIVATED=false",
    "LIVE_AUTHORIZED=false",
    "ORDERS_ENABLED=false",
    "AUTHORITY_EFFECT=NONE",
    "RUNTIME_EFFECT=NONE",
    "CANONICAL_RISK_SIZING_OWNER=UNRESOLVED",
    "CANONICAL_RISK_SIZING_AUTHORITY_OWNER=UNRESOLVED",
    "CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED",
    "CANONICAL_EQUITY_OWNER=UNRESOLVED",
    "CANONICAL_PRICE_OWNER=UNRESOLVED",
    "CANONICAL_INSTRUMENT_METADATA_OWNER=UNRESOLVED",
    "FINAL_QUANTITY_PROVENANCE_RESOLVED=false",
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
    "EXPECTED_CONVERSION_INPUT_FAMILY_COUNT=3",
    "EXPECTED_EQUITY_CANDIDATE_COUNT=4",
    "EXPECTED_PRICE_CANDIDATE_COUNT=4",
    "EXPECTED_INSTRUMENT_METADATA_CANDIDATE_COUNT=4",
    "EXPECTED_AUTHORITATIVE_PRODUCTIVE_SOURCE_COUNT=0",
    "EXPECTED_PRODUCTIVE_DEFAULT_COUNT=0",
    "NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=false",
)

GLOBAL_NON_CLAIMS = (
    "NO_CANONICAL_RISK_SIZING_OWNER_ASSIGNED",
    "NO_CANONICAL_EXECUTION_AUTHORITY_OWNER_ASSIGNED",
    "NO_CANONICAL_EQUITY_OWNER_ASSIGNED",
    "NO_CANONICAL_PRICE_OWNER_ASSIGNED",
    "NO_CANONICAL_INSTRUMENT_METADATA_OWNER_ASSIGNED",
    "FINAL_QUANTITY_PROVENANCE_NOT_FULLY_RESOLVED",
    "NO_FRACTION_TO_UNITS_CONVERSION_IN_THIS_SLICE",
    "NO_QUANTITY_MATH_CHANGE_IN_THIS_SLICE",
    "NO_REWIRE",
    "NO_SIGNAL_TO_ORDERS_MUTATION",
    "NO_SHADOW_LIVE_ORDER_GENERATION_MUTATION",
    "NO_CRS_MATH_CHANGE",
    "NO_LEVERAGE_OR_MARGIN_MULTIPLICATION",
    "NO_START_BALANCE_AS_RUNNING_EQUITY",
    "NO_CANDLE_CLOSE_AS_PRICE_AUTHORITY",
    "NO_CMC_MARK_AS_PRICE_AUTHORITY",
    "NO_REPLAY_STATE_AS_LIVE_AUTHORITY",
    "NO_VENUE_SNAPSHOT_AS_LIVE_AUTHORITY",
    "NO_MONITOR_BALANCE_AS_EQUITY_AUTHORITY",
    "NO_PRODUCTIVE_DEFAULTS",
    "CRS_CONSUMES_BUT_DOES_NOT_OWN_VENUE_ACCOUNT_TRUTH",
    "COMPANION_PASS_THROUGH_UNCHANGED",
    "EFS_REMAINS_QUARANTINED",
    "RUNTIME_REACHABILITY_IS_NOT_ACTIVATION",
    "SHADOW_OR_LIVE_NAMING_IS_NOT_LIVE_AUTHORIZED",
    "CONVERSION_NOT_READY",
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
}

REQUIRED_PROVENANCE_FIELDS = (
    "semantic_name",
    "dimension_unit",
    "producer_source_identity",
    "observation_vs_authority",
    "environment_scope",
    "as_of_source_timestamp",
    "freshness_policy_status",
    "instrument_account_binding",
    "authority_status",
    "provenance_completeness",
    "fail_closed_reason",
)

FORBIDDEN_PRODUCTIVE_IMPORT_NEEDLES = (
    "fraction_to_units",
    "FractionToUnits",
    "convert_fraction_to_quantity",
    "productive_input_provenance_binding",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_contract() -> dict:
    return json.loads(_read(CONTRACT_JSON))


def test_contract_doc_markers_present() -> None:
    text = _read(CONTRACT_DOC)
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, f"missing doc marker: {marker}"
    assert "CONVERSION_READY=true" not in text
    assert "OWNER_ASSIGNED=true" not in text
    assert "CONVERSION_MATH_ADDED=true" not in text
    assert "PRODUCTIVE_CALLER_REWIRED=true" not in text
    assert "NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=true" not in text


def test_input_provenance_records_schema_and_missing_status() -> None:
    payload = _load_contract()
    records = payload["input_provenance_records"]
    assert len(records) == 3
    assert [row["input_id"] for row in records] == [
        "ACCOUNT_EQUITY_AVAILABLE_CAPITAL",
        "REFERENCE_PRICE",
        "INSTRUMENT_QUANTITY_METADATA",
    ]

    for row in records:
        for field in REQUIRED_PROVENANCE_FIELDS:
            assert field in row, f"{row['input_id']} missing {field}"
        assert row["required_for_companion_conversion"] is True
        assert row["producer_source_identity"] == "NONE_PRODUCTIVE_ON_COMPANION_PATH"
        assert row["authority_status"] == "UNRESOLVED"
        assert row["provenance_completeness"] == "REQUIRED_INPUT_MISSING"
        assert row["freshness_policy_status"] == "FAIL_CLOSED_MISSING"
        assert row["instrument_account_binding"] == "UNBOUND"
        assert row["as_of_source_timestamp"] is None
        assert set(row["environment_scope"]) == {"shadow", "live"}
        assert len(row["candidate_sources"]) == 4
        for candidate in row["candidate_sources"]:
            assert candidate["authority_status"] == "NOT_AUTHORITY"
            assert candidate["allowed_on_companion_shadow_live"] is False
            assert candidate["classification"] in {
                "SIMULATION_ONLY_SOURCE",
                "TRANSPORT_ONLY_NO_OWNER",
                "OBSERVATION_NOT_AUTHORITY",
                "VENUE_SPECIFIC_SOURCE",
                "MULTIPLE_OWNER_CANDIDATES",
                "REQUIRED_INPUT_MISSING",
                "SEMANTIC_OR_DIMENSION_CONFLICT",
            }


def test_fail_closed_missing_equity() -> None:
    payload = _load_contract()
    equity = payload["input_provenance_records"][0]
    rule = payload["fail_closed_evaluation_rules"]["missing_equity"]
    binding = payload["companion_conversion_input_binding"]

    assert equity["input_id"] == "ACCOUNT_EQUITY_AVAILABLE_CAPITAL"
    assert equity["fail_closed_reason"] == "EQUITY_PROVENANCE_MISSING_ON_COMPANION_PATH"
    assert rule["status"] == "REQUIRED_INPUT_MISSING"
    assert rule["conversion_ready"] is False
    assert rule["fallback_allowed"] is False
    assert rule["default_allowed"] is False
    assert binding["conversion_ready"] is False
    assert "EQUITY_PROVENANCE_MISSING_ON_COMPANION_PATH" in binding["fail_closed_reason_codes"]
    assert (
        "start_balance_is_initial_risk_cash_base_only_not_running_equity"
        in equity["explicit_non_sources"]
    )


def test_fail_closed_observation_without_authority() -> None:
    payload = _load_contract()
    rule = payload["fail_closed_evaluation_rules"]["observation_without_authority"]
    price = payload["input_provenance_records"][1]
    equity = payload["input_provenance_records"][0]

    assert rule["reason_code"] == "OBSERVATION_WITHOUT_AUTHORITY"
    assert rule["conversion_ready"] is False
    assert rule["fallback_allowed"] is False
    assert any(
        c["classification"] == "OBSERVATION_NOT_AUTHORITY" for c in price["candidate_sources"]
    )
    assert any(
        c["classification"] == "OBSERVATION_NOT_AUTHORITY" for c in equity["candidate_sources"]
    )
    assert (
        "OBSERVATION_WITHOUT_AUTHORITY"
        in payload["companion_conversion_input_binding"]["mismatch_fail_closed_codes"]
    )


def test_fail_closed_stale_or_missing_instrument_metadata() -> None:
    payload = _load_contract()
    meta = payload["input_provenance_records"][2]
    rule = payload["fail_closed_evaluation_rules"]["stale_or_missing_instrument_metadata"]

    assert meta["input_id"] == "INSTRUMENT_QUANTITY_METADATA"
    assert meta["freshness_policy_status"] == "FAIL_CLOSED_MISSING"
    assert set(meta["required_fields"]) == {
        "lot_size_or_quantity_step",
        "minimum_quantity",
        "minimum_notional",
        "contract_multiplier",
        "base_quote_or_instrument_dimension",
        "source_timestamp_or_freshness",
    }
    assert rule["reason_code"] == "STALE_OR_MISSING_INSTRUMENT_METADATA"
    assert rule["conversion_ready"] is False
    assert rule["default_allowed"] is False


def test_fail_closed_account_venue_instrument_mismatch() -> None:
    payload = _load_contract()
    binding = payload["companion_conversion_input_binding"]
    rule = payload["fail_closed_evaluation_rules"]["account_venue_instrument_mismatch"]

    assert binding["account_binding_status"] == "UNRESOLVED"
    assert binding["venue_binding_status"] == "UNRESOLVED"
    assert binding["instrument_binding_status"] == "UNRESOLVED"
    assert binding["shared_account_venue_instrument_context"] is False
    assert rule["conversion_ready"] is False
    assert "ACCOUNT_BINDING_MISMATCH" in binding["mismatch_fail_closed_codes"]
    assert "VENUE_BINDING_MISMATCH" in binding["mismatch_fail_closed_codes"]
    assert "INSTRUMENT_BINDING_MISMATCH" in binding["mismatch_fail_closed_codes"]


def test_no_productive_defaults() -> None:
    payload = _load_contract()
    markers = payload["markers"]
    binding = payload["companion_conversion_input_binding"]
    rule = payload["fail_closed_evaluation_rules"]["productive_default_attempt"]

    assert markers["PRODUCTIVE_DEFAULT_COUNT"] == 0
    assert markers["NO_PRODUCTIVE_DEFAULTS"] is True
    assert markers["EXPECTED_PRODUCTIVE_DEFAULT_COUNT"] == 0
    assert binding["productive_default_count"] == 0
    assert binding["simulation_or_default_source_on_shadow_live"] is False
    assert rule["reason_code"] == "PRODUCTIVE_DEFAULT_FORBIDDEN"
    assert rule["default_allowed"] is False
    assert "PRODUCTIVE_DEFAULT_FORBIDDEN" in binding["mismatch_fail_closed_codes"]


def test_companion_pass_through_semantics_unchanged() -> None:
    payload = _load_contract()
    reality = payload["companion_pass_through_reality_freeze"]
    markers = payload["markers"]

    assert markers["COMPANION_INTENT"] == "FRACTION_DECIMAL_0_1"
    assert markers["COMPANION_PASS_THROUGH_UNCHANGED"] is True
    assert markers["COMPANION_RUNTIME_CONVERSION_PRESENT"] is False
    assert markers["SHADOW_LIVE_INPUT_PARITY"] == "PARITY_ON_ABSENCE"
    assert reality["declared_intent"] == "FRACTION_DECIMAL_0_1"
    assert reality["runtime_conversion_present"] is False
    assert reality["productive_conversion_handoff_present"] is False
    assert reality["pass_through_consumer"] == "ExecutionPipeline.signal_to_orders"
    assert reality["shadow_live_input_parity"] == "PARITY_ON_ABSENCE"
    assert reality["path_ids"] == ["PATH_SHADOW_COMPANION", "PATH_LIVE_COMPANION"]

    for path_id, (rel_path, snippets) in CRITICAL_SNIPPETS.items():
        text = _read(REPO_ROOT / rel_path)
        for snippet in snippets:
            assert snippet in text, f"{path_id}: missing snippet {snippet!r} in {rel_path}"

    pipeline = _read(REPO_ROOT / "src/execution/pipeline.py")
    assert "position_size: Gewuenschte Positionsgroesse (in Stueck)" in pipeline
    assert "quantity=position_size" in pipeline


def test_crs_consumes_inputs_but_does_not_own_venue_account_truth() -> None:
    payload = _load_contract()
    crs = payload["crs_consumer_role"]
    markers = payload["markers"]

    assert markers["CRS_CONSUMES_INPUTS_DOES_NOT_OWN_VENUE_ACCOUNT_TRUTH"] is True
    assert crs["consumes_account_equity"] is True
    assert crs["consumes_reference_price"] is True
    assert crs["consumes_instrument_quantity_constraints"] is True
    assert crs["owns_venue_account_truth"] is False
    assert crs["owns_live_equity_authority"] is False
    assert crs["owns_live_price_authority"] is False
    assert crs["owns_live_instrument_metadata_authority"] is False
    assert crs["companion_shadow_live_imports_crs"] is False

    for rel in ("src/live/shadow_session.py", "src/execution/live_session.py"):
        text = _read(REPO_ROOT / rel)
        assert "capital_risk_sizing" not in text
        assert "account_equity" not in text
        assert "evaluate_capital_risk_sizing_v1" not in text


def test_efs_remains_quarantined_and_runtime_bridge_off() -> None:
    payload = _load_contract()
    companion_freeze = json.loads(_read(COMPANION_FREEZE_JSON))
    markers = payload["markers"]
    pins = payload["global_authority_pins"]

    assert markers["EFS_QUARANTINED"] is True
    assert companion_freeze["markers"]["EFS_QUARANTINED"] is True
    assert companion_freeze["markers"]["EFS_DEPRECATED"] is True
    assert companion_freeze["efs_quarantine"]["status"] == "DEPRECATED_QUARANTINED"
    assert companion_freeze["efs_quarantine"]["productive_src_caller_count"] == 0
    assert markers["RUNTIME_BRIDGE_ACTIVATED"] is False
    assert pins["RUNTIME_BRIDGE_ACTIVATED"] is False
    assert pins["LIVE_AUTHORIZED"] is False
    assert pins["ORDERS_ENABLED"] is False


def test_aggregated_binding_not_ready() -> None:
    payload = _load_contract()
    binding = payload["companion_conversion_input_binding"]
    markers = payload["markers"]

    assert binding["conversion_ready"] is False
    assert markers["CONVERSION_READY"] is False
    assert binding["equity_provenance_closed"] is False
    assert binding["price_provenance_closed"] is False
    assert binding["instrument_metadata_complete"] is False
    assert binding["authoritative_productive_source_count"] == 0
    assert len(binding["ready_requires_all_of"]) == 5
    assert (
        "MULTIPLE_NON_AUTHORITATIVE_CANDIDATES_FAIL_CLOSED" in binding["fail_closed_reason_codes"]
    )


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

    assert auth["owner_assigned"] is False
    assert auth["no_candidate_implicitly_elevated_to_owner"] is True
    assert markers["OWNER_ASSIGNED"] is False
    assert pins["CANONICAL_EXECUTION_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert pins["CANONICAL_RISK_SIZING_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert pins["CANONICAL_EQUITY_OWNER"] == "UNRESOLVED"
    assert pins["CANONICAL_PRICE_OWNER"] == "UNRESOLVED"
    assert pins["CANONICAL_INSTRUMENT_METADATA_OWNER"] == "UNRESOLVED"
    assert pins["CONVERSION_READY"] is False
    assert pins["NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED"] is False


def test_global_non_claims_and_drift_policy() -> None:
    payload = _load_contract()
    assert tuple(payload["global_non_claims"]) == GLOBAL_NON_CLAIMS
    drift = payload["drift_policy"]
    assert drift["conversion_ready_claimed_true"] == "FAIL"
    assert drift["owner_assignment_claimed"] == "FAIL"
    assert drift["fraction_to_units_conversion_claimed"] == "FAIL"
    assert drift["productive_default_introduced"] == "FAIL"
    assert drift["start_balance_elevated_to_running_equity"] == "FAIL"
    assert drift["candle_close_elevated_to_price_authority"] == "FAIL"
    assert drift["companion_pass_through_mutated"] == "FAIL"
    assert drift["efs_not_quarantined"] == "FAIL"
    assert drift["mutation_of_frozen_counts_5_8_2_5_2_3"] == "FAIL"


def test_baseline_obl_b05_counts_unchanged() -> None:
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
    assert counts["conversion_input_families"] == 3
    assert counts["equity_candidates"] == 4
    assert counts["price_candidates"] == 4
    assert counts["instrument_metadata_candidates"] == 4
    assert counts["authoritative_productive_sources"] == 0
    assert counts["productive_defaults"] == 0

    assert markers["EXPECTED_CONVERSION_INPUT_FAMILY_COUNT"] == 3
    assert markers["EXPECTED_AUTHORITATIVE_PRODUCTIVE_SOURCE_COUNT"] == 0

    unresolved = json.loads(_read(UNRESOLVED_V0_JSON))
    consumption = json.loads(_read(CONSUMPTION_JSON))
    topology = json.loads(_read(TOPOLOGY_JSON))
    inventory = json.loads(_read(OWNER_INVENTORY_JSON))
    audit = json.loads(_read(RESOLUTION_AUDIT_JSON))
    companion_freeze = json.loads(_read(COMPANION_FREEZE_JSON))

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
    assert companion_freeze["markers"]["COMPANION_DECLARED_INTENT"] == "FRACTION_DECIMAL_0_1"
    assert companion_freeze["markers"]["EFS_QUARANTINED"] is True
    assert companion_freeze["markers"]["FINAL_QUANTITY_PROVENANCE_RESOLVED"] is False


def test_no_productive_src_wires_conversion_math_or_binding_defaults() -> None:
    src_root = REPO_ROOT / "src"
    hits: list[str] = []
    for path in src_root.rglob("*.py"):
        text = _read(path)
        for needle in FORBIDDEN_PRODUCTIVE_IMPORT_NEEDLES:
            if needle in text:
                hits.append(f"{path.relative_to(REPO_ROOT)}:{needle}")
    assert hits == [], f"productive conversion/default wiring FAIL: {hits}"


def test_readme_and_referenced_contracts_exist() -> None:
    payload = _load_contract()
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "RISK_SIZING_PRODUCTIVE_INPUT_PROVENANCE_BINDING_V1.md" in readme
    assert "RISK_SIZING_COMPANION_INTENT_FREEZE_AND_EFS_QUARANTINE_V1.md" in readme
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
    assert "CONVERSION_READY=true" not in text
    assert "OWNER_ASSIGNED=true" not in text
