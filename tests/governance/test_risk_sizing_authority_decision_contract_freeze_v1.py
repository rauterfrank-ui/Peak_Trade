"""Static contract: Authority Decision Contract Freeze v1.

Docs/config/tests-only. Freezes admissible future dimensions, provenance,
freshness, and producer classes for Equity, Reference Price, and Instrument
Metadata without owner assignment/activation, fetch, rewire, or conversion.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_authority_decision_contract_freeze_v1.json"
)
CONTRACT_DOC = (
    REPO_ROOT / "docs" / "governance" / "RISK_SIZING_AUTHORITY_DECISION_CONTRACT_FREEZE_V1.md"
)
PROVENANCE_BINDING_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_productive_input_provenance_binding_v1.json"
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
    "RISK_SIZING_AUTHORITY_DECISION_CONTRACT_FREEZE_V1=true",
    "INVENTORY_ONLY=true",
    "AUTHORITY_DECISION_CONTRACT_FROZEN=true",
    "CONVERSION_READY=false",
    "PRODUCTIVE_SEMANTICS_CHANGE_AUTHORIZED=false",
    "AUTHORITY_ACTIVATION_AUTHORIZED=false",
    "OWNER_ASSIGNED=false",
    "OWNER_ACTIVATED=false",
    "NO_AUTHORITY_ASSIGNMENT=true",
    "NO_OWNER_ACTIVATION=true",
    "NO_FRACTION_TO_UNITS_CONVERSION=true",
    "NO_QUANTITY_MATH_CHANGE=true",
    "NO_REWIRE=true",
    "NO_COMPANION_BINDING=true",
    "NO_FETCH=true",
    "NO_NETWORK_ACCESS=true",
    "NO_EXCHANGE_ACCESS=true",
    "NO_CMC_AUTHORITY_ACTIVATION=true",
    "NO_DEFAULT_ELEVATION=true",
    "NO_START_BALANCE_AS_RUNNING_EQUITY=true",
    "NO_FILL_PRICE_AS_REFERENCE_PRICE_AUTHORITY=true",
    "NO_CANDLE_CLOSE_AS_PRICE_AUTHORITY=true",
    "NO_UNIVERSAL_MULTIPLIER_ONE_DEFAULT=true",
    "OBSERVATION_IS_NOT_AUTHORITY=true",
    "TRANSPORT_IS_NOT_AUTHORITY=true",
    "OFFLINE_OR_SIMULATION_IS_NOT_AUTHORITY=true",
    "SHADOW_BINDING_REQUIRES_SEPARATE_GO=true",
    "LIVE_BINDING_REQUIRES_SEPARATE_GO=true",
    "NETWORK_ACCESS_REQUIRES_SEPARATE_GO=true",
    "EXCHANGE_ACCESS_REQUIRES_SEPARATE_GO=true",
    "FRACTION_TO_UNITS_REQUIRES_SEPARATE_GO=true",
    "ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED",
    "ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED=false",
    "REFERENCE_PRICE_AUTHORITY_OWNER=UNRESOLVED",
    "REFERENCE_PRICE_AUTHORITY_CHAIN_CLOSED=false",
    "INSTRUMENT_METADATA_AUTHORITY_OWNER=UNRESOLVED",
    "INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED=false",
    "EXPECTED_INPUT_DOMAIN_COUNT=3",
    "EXPECTED_AUTHORITY_OWNER_ASSIGNED_COUNT=0",
    "EXPECTED_AUTHORITY_CHAIN_CLOSED_COUNT=0",
    "EXPECTED_PRODUCTIVE_PRODUCER_COUNT=0",
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
    "PROVENANCE_BINDING_REMAINS_CONVERSION_NOT_READY=true",
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
    "NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=false",
)

GLOBAL_NON_CLAIMS = (
    "NO_ACCOUNT_EQUITY_AUTHORITY_OWNER_ASSIGNED",
    "NO_REFERENCE_PRICE_AUTHORITY_OWNER_ASSIGNED",
    "NO_INSTRUMENT_METADATA_AUTHORITY_OWNER_ASSIGNED",
    "NO_AUTHORITY_CHAIN_CLOSED_FOR_ANY_INPUT_DOMAIN",
    "NO_AUTHORITY_ACTIVATION",
    "NO_PRODUCTIVE_SEMANTICS_CHANGE_AUTHORIZED",
    "NO_FRACTION_TO_UNITS_CONVERSION_IN_THIS_SLICE",
    "NO_QUANTITY_MATH_CHANGE_IN_THIS_SLICE",
    "NO_REWIRE",
    "NO_COMPANION_BINDING",
    "NO_FETCH",
    "NO_NETWORK_ACCESS",
    "NO_EXCHANGE_ACCESS",
    "NO_SIGNAL_TO_ORDERS_MUTATION",
    "NO_SHADOW_LIVE_ORDER_GENERATION_MUTATION",
    "NO_CRS_MATH_CHANGE",
    "NO_CMC_AUTHORITY_ACTIVATION",
    "NO_DEFAULT_ELEVATION",
    "NO_START_BALANCE_AS_RUNNING_EQUITY",
    "NO_FILL_PRICE_AS_REFERENCE_PRICE_AUTHORITY",
    "NO_CANDLE_CLOSE_AS_PRICE_AUTHORITY",
    "NO_UNIVERSAL_MULTIPLIER_ONE_DEFAULT",
    "OBSERVATION_IS_NOT_AUTHORITY",
    "TRANSPORT_IS_NOT_AUTHORITY",
    "OFFLINE_OR_SIMULATION_IS_NOT_AUTHORITY",
    "PROVENANCE_BINDING_REMAINS_CONVERSION_NOT_READY",
    "CONVERSION_NOT_READY",
)

FORBIDDEN_PRODUCTIVE_IMPORT_NEEDLES = (
    "fraction_to_units",
    "FractionToUnits",
    "convert_fraction_to_quantity",
    "authority_decision_contract_freeze",
    "risk_sizing_authority_decision_contract_freeze",
)

REQUIRED_DOMAIN_IDS = (
    "ACCOUNT_EQUITY",
    "REFERENCE_PRICE",
    "INSTRUMENT_METADATA",
)

REQUIRED_INSTRUMENT_METADATA_FIELDS = (
    "instrument_id",
    "venue",
    "market_type",
    "base_asset",
    "quote_asset",
    "contract_type_or_linear_inverse",
    "contract_multiplier_or_ctVal",
    "quantity_step_or_lot_size",
    "min_quantity",
    "min_notional",
    "price_tick_if_required_for_normalization",
    "observed_at_or_as_of",
    "freshness_or_ttl",
    "provenance",
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
    assert "OWNER_ACTIVATED=true" not in text
    assert "AUTHORITY_ACTIVATION_AUTHORIZED=true" not in text
    assert "PRODUCTIVE_SEMANTICS_CHANGE_AUTHORIZED=true" not in text
    assert "ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED=true" not in text
    assert "REFERENCE_PRICE_AUTHORITY_CHAIN_CLOSED=true" not in text
    assert "INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED=true" not in text


def test_exactly_three_input_domains_and_owners_unresolved() -> None:
    payload = _load_contract()
    domains = payload["input_domains"]
    pins = payload["global_pins"]
    auth = payload["authority_status"]
    markers = payload["markers"]

    assert len(domains) == 3
    assert [row["domain_id"] for row in domains] == list(REQUIRED_DOMAIN_IDS)
    assert markers["EXPECTED_INPUT_DOMAIN_COUNT"] == 3
    assert payload["expected_counts"]["input_domains"] == 3
    assert payload["contract_version"] == "v1"
    assert pins["contract_version"] == "v1"

    for row in domains:
        assert row["authority_owner"] == "UNRESOLVED", row["domain_id"]
        assert row["authority_chain_closed"] is False, row["domain_id"]
        assert row["productive_producer_present"] is False, row["domain_id"]
        assert isinstance(row["required_provenance_fields"], list)
        assert len(row["required_provenance_fields"]) >= 3
        assert isinstance(row["required_freshness_fields"], list)
        assert len(row["required_freshness_fields"]) >= 2
        assert isinstance(row["forbidden_defaults_elevations"], list)
        assert len(row["forbidden_defaults_elevations"]) >= 1
        assert isinstance(row["forbidden_source_classes"], list)
        assert "OBSERVATION_NOT_AUTHORITY" in row["forbidden_source_classes"]
        assert "TRANSPORT_ONLY_NO_OWNER" in row["forbidden_source_classes"]
        assert "OFFLINE_OR_SIMULATION_ONLY" in row["forbidden_source_classes"]

    assert pins["account_equity_authority_owner"] == "UNRESOLVED"
    assert pins["reference_price_authority_owner"] == "UNRESOLVED"
    assert pins["instrument_metadata_authority_owner"] == "UNRESOLVED"
    assert auth["account_equity_authority_owner"] == "UNRESOLVED"
    assert auth["reference_price_authority_owner"] == "UNRESOLVED"
    assert auth["instrument_metadata_authority_owner"] == "UNRESOLVED"
    assert auth["account_equity_authority_chain_closed"] is False
    assert auth["reference_price_authority_chain_closed"] is False
    assert auth["instrument_metadata_authority_chain_closed"] is False
    assert markers["ACCOUNT_EQUITY_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert markers["REFERENCE_PRICE_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert markers["INSTRUMENT_METADATA_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert markers["ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED"] is False
    assert markers["REFERENCE_PRICE_AUTHORITY_CHAIN_CLOSED"] is False
    assert markers["INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED"] is False
    assert markers["EXPECTED_AUTHORITY_OWNER_ASSIGNED_COUNT"] == 0
    assert markers["EXPECTED_AUTHORITY_CHAIN_CLOSED_COUNT"] == 0
    assert markers["EXPECTED_PRODUCTIVE_PRODUCER_COUNT"] == 0


def test_conversion_and_activation_remain_false() -> None:
    payload = _load_contract()
    pins = payload["global_pins"]
    markers = payload["markers"]
    auth = payload["authority_status"]

    assert pins["conversion_ready"] is False
    assert pins["productive_semantics_change_authorized"] is False
    assert pins["authority_activation_authorized"] is False
    assert markers["CONVERSION_READY"] is False
    assert markers["PRODUCTIVE_SEMANTICS_CHANGE_AUTHORIZED"] is False
    assert markers["AUTHORITY_ACTIVATION_AUTHORIZED"] is False
    assert markers["OWNER_ASSIGNED"] is False
    assert markers["OWNER_ACTIVATED"] is False
    assert auth["owner_assigned"] is False
    assert auth["owner_activated"] is False
    assert auth["authority_activation_authorized"] is False
    assert markers["LIVE_AUTHORIZED"] is False
    assert markers["ORDERS_ENABLED"] is False
    assert markers["RUNTIME_BRIDGE_ACTIVATED"] is False
    assert pins["live_authorized"] is False
    assert pins["orders_enabled"] is False
    assert pins["runtime_bridge_activated"] is False


def test_observation_transport_offline_not_authority() -> None:
    payload = _load_contract()
    pins = payload["global_pins"]
    rules = payload["cross_cutting_fail_closed_rules"]
    markers = payload["markers"]

    assert pins["observation_is_not_authority"] is True
    assert pins["transport_is_not_authority"] is True
    assert pins["offline_or_simulation_is_not_authority"] is True
    assert rules["observation_is_not_authority"] is True
    assert rules["transport_is_not_authority"] is True
    assert rules["offline_or_simulation_is_not_authority"] is True
    assert markers["OBSERVATION_IS_NOT_AUTHORITY"] is True
    assert markers["TRANSPORT_IS_NOT_AUTHORITY"] is True
    assert markers["OFFLINE_OR_SIMULATION_IS_NOT_AUTHORITY"] is True


def test_start_balance_fill_price_and_multiplier_defaults_forbidden() -> None:
    payload = _load_contract()
    rules = payload["cross_cutting_fail_closed_rules"]
    equity = payload["input_domains"][0]
    price = payload["input_domains"][1]
    meta = payload["input_domains"][2]
    markers = payload["markers"]

    assert equity["domain_id"] == "ACCOUNT_EQUITY"
    assert price["domain_id"] == "REFERENCE_PRICE"
    assert meta["domain_id"] == "INSTRUMENT_METADATA"

    assert rules["start_balance_running_equity_allowed"] is False
    assert rules["fill_price_reference_authority_allowed"] is False
    assert rules["universal_multiplier_one_default_allowed"] is False
    assert markers["NO_START_BALANCE_AS_RUNNING_EQUITY"] is True
    assert markers["NO_FILL_PRICE_AS_REFERENCE_PRICE_AUTHORITY"] is True
    assert markers["NO_UNIVERSAL_MULTIPLIER_ONE_DEFAULT"] is True

    assert "start_balance_as_running_equity" in equity["forbidden_defaults_elevations"]
    assert (
        "start_balance_is_initial_risk_cash_base_only_not_running_equity"
        in equity["explicit_non_authority_pins"]
    )
    assert (
        "fill_price_as_conversion_reference_price_authority"
        in price["forbidden_defaults_elevations"]
    )
    assert (
        "fill_or_execution_price_forbidden_as_upstream_conversion_reference_price"
        in price["explicit_non_authority_pins"]
    )
    assert "universal_silent_multiplier_one_default" in meta["forbidden_defaults_elevations"]
    assert (
        "multiplier_one_must_not_act_as_universal_silent_default"
        in meta["explicit_non_authority_pins"]
    )


def test_account_equity_dimension_not_mixed() -> None:
    payload = _load_contract()
    equity = payload["input_domains"][0]
    dim = equity["allowed_fachliche_dimension"]

    assert dim["dimension_id"] == "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
    for forbidden in (
        "free_balance",
        "cash_balance",
        "balance_total",
        "initial_or_start_balance",
        "simulated_or_offline_equity",
    ):
        assert forbidden in dim["must_not_be_confused_with"]


def test_reference_price_semantics_remain_distinct() -> None:
    payload = _load_contract()
    price = payload["input_domains"][1]
    dim = price["allowed_fachliche_dimension"]
    rules = payload["cross_cutting_fail_closed_rules"]

    assert dim["dimension_id"] == "INSTRUMENT_VENUE_TIME_BOUND_CONVERSION_REFERENCE_PRICE"
    for binding in ("instrument_id", "venue_id", "as_of_or_observed_at", "price_semantics_class"):
        assert binding in dim["required_bindings"]
    for semantic in (
        "candle_close",
        "ticker_last",
        "mark_price",
        "index_price",
        "fill_or_execution_price",
    ):
        assert semantic in dim["price_semantics_classes_must_remain_distinct"]
    assert rules["implicit_price_semantics_synonymization_allowed"] is False
    assert rules["candle_close_quantity_input_silent_activation_allowed"] is False
    assert rules["cmc_is_authority_false_elevation_allowed"] is False
    assert (
        "candle_close_silent_activation_as_quantity_input" in price["forbidden_defaults_elevations"]
    )
    assert "cmc_is_authority_false_elevation" in price["forbidden_defaults_elevations"]


def test_instrument_metadata_required_fields_complete() -> None:
    payload = _load_contract()
    meta = payload["input_domains"][2]
    dim = meta["allowed_fachliche_dimension"]
    rules = payload["cross_cutting_fail_closed_rules"]

    assert set(dim["required_metadata_fields"]) == set(REQUIRED_INSTRUMENT_METADATA_FIELDS)
    assert meta["productive_producer_present"] is False
    assert meta["audit_decision_class"] == "NO_PRODUCTIVE_PRODUCER"
    assert rules["partial_instrument_metadata_elevation_allowed"] is False
    assert "PARTIAL_OFFLINE_CONFIG_SNAPSHOT_OR_RESEARCH_DATA" in meta["forbidden_source_classes"]
    assert "UNIVERSAL_MULTIPLIER_ONE_DEFAULT" in meta["forbidden_source_classes"]


def test_separate_go_gates_pinned() -> None:
    payload = _load_contract()
    pins = payload["global_pins"]
    rules = payload["cross_cutting_fail_closed_rules"]
    markers = payload["markers"]

    for key in (
        "shadow_binding_requires_separate_go",
        "live_binding_requires_separate_go",
        "network_access_requires_separate_go",
        "exchange_access_requires_separate_go",
        "fraction_to_units_requires_separate_go",
    ):
        assert pins[key] is True
        assert rules[key] is True

    assert markers["SHADOW_BINDING_REQUIRES_SEPARATE_GO"] is True
    assert markers["LIVE_BINDING_REQUIRES_SEPARATE_GO"] is True
    assert markers["NETWORK_ACCESS_REQUIRES_SEPARATE_GO"] is True
    assert markers["EXCHANGE_ACCESS_REQUIRES_SEPARATE_GO"] is True
    assert markers["FRACTION_TO_UNITS_REQUIRES_SEPARATE_GO"] is True
    assert rules["fetch_in_this_slice_allowed"] is False
    assert rules["companion_binding_in_this_slice_allowed"] is False
    assert rules["fraction_to_units_in_this_slice_allowed"] is False


def test_provenance_binding_contract_remains_consistent() -> None:
    payload = _load_contract()
    provenance = json.loads(_read(PROVENANCE_BINDING_JSON))
    markers = payload["markers"]

    assert markers["PROVENANCE_BINDING_REMAINS_CONVERSION_NOT_READY"] is True
    assert provenance["markers"]["CONVERSION_READY"] is False
    assert provenance["markers"]["OWNER_ASSIGNED"] is False
    assert provenance["companion_conversion_input_binding"]["conversion_ready"] is False
    assert provenance["authority_status"]["canonical_equity_owner"] == "UNRESOLVED"
    assert provenance["authority_status"]["canonical_price_owner"] == "UNRESOLVED"
    assert provenance["authority_status"]["canonical_instrument_metadata_owner"] == "UNRESOLVED"
    assert len(provenance["input_provenance_records"]) == 3
    assert provenance["expected_counts"]["conversion_input_families"] == 3
    assert provenance["expected_counts"]["authoritative_productive_sources"] == 0


def test_global_non_claims_and_drift_policy() -> None:
    payload = _load_contract()
    assert tuple(payload["global_non_claims"]) == GLOBAL_NON_CLAIMS
    drift = payload["drift_policy"]
    assert drift["conversion_ready_claimed_true"] == "FAIL"
    assert drift["productive_semantics_change_authorized_claimed_true"] == "FAIL"
    assert drift["authority_activation_authorized_claimed_true"] == "FAIL"
    assert drift["owner_assignment_claimed"] == "FAIL"
    assert drift["authority_chain_closed_claimed_true"] == "FAIL"
    assert drift["start_balance_elevated_to_running_equity"] == "FAIL"
    assert drift["fill_price_elevated_to_reference_price_authority"] == "FAIL"
    assert drift["universal_multiplier_one_default_claimed"] == "FAIL"
    assert drift["observation_or_transport_or_offline_elevated_to_authority"] == "FAIL"
    assert drift["provenance_binding_conversion_ready_drift"] == "FAIL"


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
    assert markers["EXPECTED_CONVERSION_INPUT_FAMILY_COUNT"] == 3


def test_no_productive_src_caller_or_companion_import_added() -> None:
    src_root = REPO_ROOT / "src"
    hits: list[str] = []
    for path in src_root.rglob("*.py"):
        text = _read(path)
        for needle in FORBIDDEN_PRODUCTIVE_IMPORT_NEEDLES:
            if needle in text:
                hits.append(f"{path.relative_to(REPO_ROOT)}:{needle}")
    assert hits == [], f"productive conversion/authority wiring FAIL: {hits}"

    for rel in ("src/live/shadow_session.py", "src/execution/live_session.py"):
        text = _read(REPO_ROOT / rel)
        assert "authority_decision_contract_freeze" not in text
        assert "risk_sizing_authority_decision" not in text
        assert "capital_risk_sizing" not in text
        assert "evaluate_capital_risk_sizing_v1" not in text


def test_readme_and_referenced_contracts_exist() -> None:
    payload = _load_contract()
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "RISK_SIZING_AUTHORITY_DECISION_CONTRACT_FREEZE_V1.md" in readme
    assert "RISK_SIZING_PRODUCTIVE_INPUT_PROVENANCE_BINDING_V1.md" in readme
    for rel in payload["referenced_contracts"].values():
        assert (REPO_ROOT / rel).is_file(), rel
    assert CONTRACT_JSON.is_file()
    assert CONTRACT_DOC.is_file()
    units = json.loads(_read(UNITS_JSON))
    assert units["markers"]["NO_SIZING_MATH_CHANGE"] is True


def test_docs_markers_match_json_markers() -> None:
    payload = _load_contract()
    text = _read(CONTRACT_DOC)
    markers = payload["markers"]

    bool_true_keys = (
        "RISK_SIZING_AUTHORITY_DECISION_CONTRACT_FREEZE_V1",
        "AUTHORITY_DECISION_CONTRACT_FROZEN",
        "OBSERVATION_IS_NOT_AUTHORITY",
        "TRANSPORT_IS_NOT_AUTHORITY",
        "OFFLINE_OR_SIMULATION_IS_NOT_AUTHORITY",
        "NO_START_BALANCE_AS_RUNNING_EQUITY",
        "NO_FILL_PRICE_AS_REFERENCE_PRICE_AUTHORITY",
        "NO_UNIVERSAL_MULTIPLIER_ONE_DEFAULT",
        "SHADOW_BINDING_REQUIRES_SEPARATE_GO",
        "LIVE_BINDING_REQUIRES_SEPARATE_GO",
        "NETWORK_ACCESS_REQUIRES_SEPARATE_GO",
        "EXCHANGE_ACCESS_REQUIRES_SEPARATE_GO",
        "FRACTION_TO_UNITS_REQUIRES_SEPARATE_GO",
        "PROVENANCE_BINDING_REMAINS_CONVERSION_NOT_READY",
    )
    bool_false_keys = (
        "CONVERSION_READY",
        "PRODUCTIVE_SEMANTICS_CHANGE_AUTHORIZED",
        "AUTHORITY_ACTIVATION_AUTHORIZED",
        "OWNER_ASSIGNED",
        "OWNER_ACTIVATED",
        "ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED",
        "REFERENCE_PRICE_AUTHORITY_CHAIN_CLOSED",
        "INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED",
        "LIVE_AUTHORIZED",
        "ORDERS_ENABLED",
        "RUNTIME_BRIDGE_ACTIVATED",
        "NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED",
    )
    unresolved_keys = (
        "ACCOUNT_EQUITY_AUTHORITY_OWNER",
        "REFERENCE_PRICE_AUTHORITY_OWNER",
        "INSTRUMENT_METADATA_AUTHORITY_OWNER",
        "CANONICAL_EQUITY_OWNER",
        "CANONICAL_PRICE_OWNER",
        "CANONICAL_INSTRUMENT_METADATA_OWNER",
    )

    for key in bool_true_keys:
        assert markers[key] is True
        assert f"{key}=true" in text, key
    for key in bool_false_keys:
        assert markers[key] is False
        assert f"{key}=false" in text, key
    for key in unresolved_keys:
        assert markers[key] == "UNRESOLVED"
        assert f"{key}=UNRESOLVED" in text, key
    assert markers["EXPECTED_INPUT_DOMAIN_COUNT"] == 3
    assert "EXPECTED_INPUT_DOMAIN_COUNT=3" in text


def test_no_authority_escalation_language_in_doc() -> None:
    text = _read(CONTRACT_DOC)
    assert re.search(r"ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED", text)
    assert re.search(r"REFERENCE_PRICE_AUTHORITY_OWNER=UNRESOLVED", text)
    assert re.search(r"INSTRUMENT_METADATA_AUTHORITY_OWNER=UNRESOLVED", text)
    assert re.search(r"CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED", text)
    assert re.search(r"CANONICAL_RISK_SIZING_AUTHORITY_OWNER=UNRESOLVED", text)
    assert "CONVERSION_READY=true" not in text
    assert "OWNER_ASSIGNED=true" not in text
    assert "AUTHORITY_ACTIVATION_AUTHORIZED=true" not in text
