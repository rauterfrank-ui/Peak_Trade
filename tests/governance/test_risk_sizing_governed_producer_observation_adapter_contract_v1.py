"""Static contract: Governed Producer Observation Adapter Contract v1.

Docs/config/tests-only. Freezes admissible future producer/observation adapter
roles, fields, provenance, freshness, and failure states for Equity, Reference
Price, and Instrument Metadata without productive adapters, producer selection,
authority binding, fetch, rewire, or conversion.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_governed_producer_observation_adapter_contract_v1.json"
)
CONTRACT_DOC = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "RISK_SIZING_GOVERNED_PRODUCER_OBSERVATION_ADAPTER_CONTRACT_V1.md"
)
PROVENANCE_BINDING_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_productive_input_provenance_binding_v1.json"
)
AUTHORITY_DECISION_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_authority_decision_contract_freeze_v1.json"
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
    "RISK_SIZING_GOVERNED_PRODUCER_OBSERVATION_ADAPTER_CONTRACT_V1=true",
    "INVENTORY_ONLY=true",
    "PRODUCER_OBSERVATION_ADAPTER_CONTRACT_FROZEN=true",
    "ACCOUNT_EQUITY_ADAPTER_CONTRACT_FROZEN=true",
    "REFERENCE_PRICE_ADAPTER_CONTRACT_FROZEN=true",
    "INSTRUMENT_METADATA_ADAPTER_CONTRACT_FROZEN=true",
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
    "NO_FILL_PRICE_AS_REFERENCE_PRICE_OBSERVATION=true",
    "NO_FILL_PRICE_AS_REFERENCE_PRICE_AUTHORITY=true",
    "NO_CANDLE_CLOSE_AS_PRICE_AUTHORITY=true",
    "NO_UNIVERSAL_MULTIPLIER_ONE_DEFAULT=true",
    "NO_OFFLINE_OR_SIMULATION_AS_PRODUCTIVE_OBSERVATION=true",
    "OBSERVATION_IS_NOT_AUTHORITY=true",
    "TRANSPORT_IS_NOT_AUTHORITY=true",
    "NORMALIZATION_IS_NOT_AUTHORITY=true",
    "OFFLINE_OR_SIMULATION_IS_NOT_AUTHORITY=true",
    "OBSERVATION_IS_AUTHORITY=false",
    "TRANSPORT_IS_AUTHORITY=false",
    "NORMALIZATION_IS_AUTHORITY=false",
    "AUTHORITY_BINDING_IMPLEMENTED=false",
    "PRODUCTIVE_ADAPTER_IMPLEMENTED=false",
    "PRODUCTIVE_PRODUCER_SELECTED=false",
    "COMPANION_REACHABLE=false",
    "CONVERSION_CONSUMER_BOUND=false",
    "PARTIAL_DATA_POLICY=FAIL_CLOSED",
    "AMBIGUOUS_DIMENSION_POLICY=FAIL_CLOSED",
    "STALE_DATA_POLICY=FAIL_CLOSED",
    "SHADOW_BINDING_REQUIRES_SEPARATE_GO=true",
    "LIVE_BINDING_REQUIRES_SEPARATE_GO=true",
    "NETWORK_ACCESS_REQUIRES_SEPARATE_GO=true",
    "EXCHANGE_ACCESS_REQUIRES_SEPARATE_GO=true",
    "PRODUCER_IMPLEMENTATION_REQUIRES_SEPARATE_GO=true",
    "FRACTION_TO_UNITS_REQUIRES_SEPARATE_GO=true",
    "ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED",
    "ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED=false",
    "REFERENCE_PRICE_AUTHORITY_OWNER=UNRESOLVED",
    "REFERENCE_PRICE_AUTHORITY_CHAIN_CLOSED=false",
    "INSTRUMENT_METADATA_AUTHORITY_OWNER=UNRESOLVED",
    "INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED=false",
    "EXPECTED_INPUT_DOMAIN_COUNT=3",
    "EXPECTED_ADAPTER_LAYER_COUNT=5",
    "EXPECTED_ALLOWED_ADAPTER_ROLE_COUNT=3",
    "EXPECTED_FORBIDDEN_ADAPTER_ROLE_COUNT=2",
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
    "AUTHORITY_DECISION_CONTRACT_REMAINS_FROZEN=true",
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
    "NO_PRODUCTIVE_ADAPTER_IMPLEMENTED",
    "NO_PRODUCTIVE_PRODUCER_SELECTED",
    "NO_AUTHORITY_BINDING_IMPLEMENTED",
    "NO_COMPANION_REACHABLE",
    "NO_CONVERSION_CONSUMER_BOUND",
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
    "NO_FILL_PRICE_AS_REFERENCE_PRICE_OBSERVATION",
    "NO_FILL_PRICE_AS_REFERENCE_PRICE_AUTHORITY",
    "NO_CANDLE_CLOSE_AS_PRICE_AUTHORITY",
    "NO_UNIVERSAL_MULTIPLIER_ONE_DEFAULT",
    "OBSERVATION_IS_NOT_AUTHORITY",
    "TRANSPORT_IS_NOT_AUTHORITY",
    "NORMALIZATION_IS_NOT_AUTHORITY",
    "OFFLINE_OR_SIMULATION_IS_NOT_AUTHORITY",
    "PROVENANCE_BINDING_REMAINS_CONVERSION_NOT_READY",
    "AUTHORITY_DECISION_CONTRACT_REMAINS_FROZEN",
    "CONVERSION_NOT_READY",
)

FORBIDDEN_PRODUCTIVE_IMPORT_NEEDLES = (
    "fraction_to_units",
    "FractionToUnits",
    "convert_fraction_to_quantity",
    "governed_producer_observation_adapter_contract",
    "risk_sizing_governed_producer_observation_adapter",
)

REQUIRED_DOMAIN_IDS = (
    "ACCOUNT_EQUITY",
    "REFERENCE_PRICE",
    "INSTRUMENT_METADATA",
)

ALLOWED_ADAPTER_ROLES = (
    "RAW_TRANSPORT",
    "OBSERVATION_ADAPTER",
    "NORMALIZATION_ADAPTER",
)

FORBIDDEN_ADAPTER_ROLES = (
    "AUTHORITY_BINDING",
    "CONVERSION_CONSUMER",
)

REQUIRED_INSTRUMENT_NORMALIZED_FIELDS = (
    "instrument_id",
    "venue",
    "market_type",
    "base_asset",
    "quote_asset",
    "contract_type",
    "contract_multiplier_or_ctVal",
    "quantity_step_or_lot_size",
    "min_quantity",
    "min_notional",
    "price_tick",
    "observed_at_or_as_of",
    "provenance",
    "completeness_or_failure_status",
)

REQUIRED_REFERENCE_PRICE_TYPES = (
    "mark",
    "index",
    "last",
    "candle_close",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_contract() -> dict:
    return json.loads(_read(CONTRACT_JSON))


def _domains_by_id(payload: dict) -> dict[str, dict]:
    return {d["domain_id"]: d for d in payload["input_domains"]}


def test_contract_doc_markers_present() -> None:
    text = _read(CONTRACT_DOC)
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, f"missing doc marker: {marker}"


def test_contract_version_and_exactly_three_domains() -> None:
    payload = _load_contract()
    markers = payload["markers"]
    assert payload["contract_version"] == "v1"
    assert payload["global_pins"]["contract_version"] == "v1"
    assert len(payload["input_domains"]) == 3
    assert markers["EXPECTED_INPUT_DOMAIN_COUNT"] == 3
    assert payload["expected_counts"]["input_domains"] == 3
    assert [d["domain_id"] for d in payload["input_domains"]] == list(REQUIRED_DOMAIN_IDS)
    assert [d["semantic_name"] for d in payload["input_domains"]] == [
        "account_equity",
        "reference_price",
        "instrument_metadata",
    ]


def test_adapter_layer_separation_complete() -> None:
    payload = _load_contract()
    markers = payload["markers"]
    layers = payload["adapter_layers"]
    assert len(layers) == 5
    assert markers["EXPECTED_ADAPTER_LAYER_COUNT"] == 5
    assert [layer["layer_id"] for layer in layers] == [
        "RAW_TRANSPORT",
        "OBSERVATION_ADAPTER",
        "NORMALIZATION_ADAPTER",
        "AUTHORITY_BINDING",
        "CONVERSION_CONSUMER",
    ]
    assert payload["allowed_adapter_roles"] == list(ALLOWED_ADAPTER_ROLES)
    assert payload["forbidden_adapter_roles"] == list(FORBIDDEN_ADAPTER_ROLES)
    assert markers["EXPECTED_ALLOWED_ADAPTER_ROLE_COUNT"] == 3
    assert markers["EXPECTED_FORBIDDEN_ADAPTER_ROLE_COUNT"] == 2

    by_id = {layer["layer_id"]: layer for layer in layers}
    for role in ALLOWED_ADAPTER_ROLES:
        assert by_id[role]["is_authority"] is False
        assert by_id[role]["allowed_in_this_slice_as_contract_role"] is True
        assert by_id[role]["implemented_in_this_slice"] is False
    assert by_id["AUTHORITY_BINDING"]["allowed_in_this_slice_as_contract_role"] is False
    assert by_id["AUTHORITY_BINDING"]["implemented_in_this_slice"] is False
    assert by_id["AUTHORITY_BINDING"]["status"] == "NOT_IMPLEMENTED"
    assert by_id["AUTHORITY_BINDING"]["authority_owner"] == "UNRESOLVED"
    assert by_id["CONVERSION_CONSUMER"]["allowed_in_this_slice_as_contract_role"] is False
    assert by_id["CONVERSION_CONSUMER"]["status"] == "UNBOUND"


def test_observation_transport_normalization_never_authority() -> None:
    payload = _load_contract()
    markers = payload["markers"]
    pins = payload["global_pins"]
    rules = payload["cross_cutting_fail_closed_rules"]

    assert markers["OBSERVATION_IS_AUTHORITY"] is False
    assert markers["TRANSPORT_IS_AUTHORITY"] is False
    assert markers["NORMALIZATION_IS_AUTHORITY"] is False
    assert markers["OBSERVATION_IS_NOT_AUTHORITY"] is True
    assert markers["TRANSPORT_IS_NOT_AUTHORITY"] is True
    assert markers["NORMALIZATION_IS_NOT_AUTHORITY"] is True
    assert pins["observation_is_authority"] is False
    assert pins["transport_is_authority"] is False
    assert pins["normalization_is_authority"] is False
    assert rules["observation_is_authority"] is False
    assert rules["transport_is_authority"] is False
    assert rules["normalization_is_authority"] is False

    for domain in payload["input_domains"]:
        assert domain["observation_is_authority"] is False


def test_no_productive_adapter_or_producer_or_companion_bound() -> None:
    payload = _load_contract()
    markers = payload["markers"]
    pins = payload["global_pins"]
    rules = payload["cross_cutting_fail_closed_rules"]

    assert markers["PRODUCTIVE_ADAPTER_IMPLEMENTED"] is False
    assert markers["PRODUCTIVE_PRODUCER_SELECTED"] is False
    assert markers["AUTHORITY_BINDING_IMPLEMENTED"] is False
    assert markers["COMPANION_REACHABLE"] is False
    assert markers["CONVERSION_CONSUMER_BOUND"] is False
    assert markers["CONVERSION_READY"] is False
    assert pins["productive_adapter_implemented"] is False
    assert pins["productive_producer_selected"] is False
    assert pins["authority_binding_implemented"] is False
    assert pins["companion_reachable"] is False
    assert pins["conversion_consumer_bound"] is False
    assert pins["conversion_ready"] is False
    assert rules["productive_adapter_implemented"] is False
    assert rules["productive_producer_selected"] is False
    assert rules["authority_binding_implemented"] is False
    assert rules["companion_reachable"] is False
    assert rules["conversion_consumer_bound"] is False
    assert rules["conversion_ready"] is False

    for domain in payload["input_domains"]:
        assert domain["productive_adapter_implemented"] is False
        assert domain["productive_producer_selected"] is False


def test_all_authority_owners_remain_unresolved_and_chains_open() -> None:
    payload = _load_contract()
    markers = payload["markers"]
    status = payload["authority_status"]

    assert markers["ACCOUNT_EQUITY_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert markers["REFERENCE_PRICE_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert markers["INSTRUMENT_METADATA_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert markers["ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED"] is False
    assert markers["REFERENCE_PRICE_AUTHORITY_CHAIN_CLOSED"] is False
    assert markers["INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED"] is False
    assert markers["EXPECTED_AUTHORITY_OWNER_ASSIGNED_COUNT"] == 0
    assert markers["EXPECTED_AUTHORITY_CHAIN_CLOSED_COUNT"] == 0
    assert markers["EXPECTED_PRODUCTIVE_PRODUCER_COUNT"] == 0
    assert markers["OWNER_ASSIGNED"] is False
    assert markers["OWNER_ACTIVATED"] is False
    assert markers["AUTHORITY_ACTIVATION_AUTHORIZED"] is False

    assert status["account_equity_authority_owner"] == "UNRESOLVED"
    assert status["reference_price_authority_owner"] == "UNRESOLVED"
    assert status["instrument_metadata_authority_owner"] == "UNRESOLVED"
    assert status["account_equity_authority_chain_closed"] is False
    assert status["reference_price_authority_chain_closed"] is False
    assert status["instrument_metadata_authority_chain_closed"] is False
    assert status["authority_binding_implemented"] is False

    for domain in payload["input_domains"]:
        assert domain["authority_owner"] == "UNRESOLVED"
        assert domain["authority_chain_closed"] is False


def test_fail_closed_partial_ambiguous_stale_policies() -> None:
    payload = _load_contract()
    markers = payload["markers"]
    pins = payload["global_pins"]
    rules = payload["cross_cutting_fail_closed_rules"]

    assert markers["PARTIAL_DATA_POLICY"] == "FAIL_CLOSED"
    assert markers["AMBIGUOUS_DIMENSION_POLICY"] == "FAIL_CLOSED"
    assert markers["STALE_DATA_POLICY"] == "FAIL_CLOSED"
    assert pins["partial_data_policy"] == "FAIL_CLOSED"
    assert pins["ambiguous_dimension_policy"] == "FAIL_CLOSED"
    assert pins["stale_data_policy"] == "FAIL_CLOSED"
    assert rules["partial_data_policy"] == "FAIL_CLOSED"
    assert rules["ambiguous_dimension_policy"] == "FAIL_CLOSED"
    assert rules["stale_data_policy"] == "FAIL_CLOSED"

    for domain in payload["input_domains"]:
        assert domain["partial_data_policy"] == "FAIL_CLOSED"
        assert domain["ambiguous_dimension_policy"] == "FAIL_CLOSED"
        assert domain["stale_data_policy"] == "FAIL_CLOSED"
        assert "required_raw_fields" in domain and domain["required_raw_fields"]
        assert "required_normalized_fields" in domain and domain["required_normalized_fields"]
        assert "required_provenance_fields" in domain and domain["required_provenance_fields"]
        assert "required_freshness_fields" in domain and domain["required_freshness_fields"]
        assert "failure_states" in domain and domain["failure_states"]


def test_start_balance_offline_simulation_forbidden() -> None:
    payload = _load_contract()
    markers = payload["markers"]
    rules = payload["cross_cutting_fail_closed_rules"]
    equity = _domains_by_id(payload)["ACCOUNT_EQUITY"]

    assert markers["NO_START_BALANCE_AS_RUNNING_EQUITY"] is True
    assert markers["NO_OFFLINE_OR_SIMULATION_AS_PRODUCTIVE_OBSERVATION"] is True
    assert markers["OFFLINE_OR_SIMULATION_IS_NOT_AUTHORITY"] is True
    assert rules["start_balance_running_equity_allowed"] is False
    assert rules["offline_or_simulation_as_productive_observation_allowed"] is False
    assert "START_BALANCE_FORBIDDEN" in equity["failure_states"]
    assert "SIMULATED_OR_OFFLINE_VALUE_FORBIDDEN" in equity["failure_states"]
    assert "start_balance_as_observation_or_authority" in equity["forbidden_behaviors"]
    assert "simulated_or_offline_values" in equity["forbidden_behaviors"]
    assert "observation_as_running_equity_authority" in equity["forbidden_behaviors"]
    assert (
        "silent_selection_among_free_total_cash_balance_margin_equity"
        in equity["forbidden_behaviors"]
    )


def test_fill_price_as_reference_observation_forbidden() -> None:
    payload = _load_contract()
    markers = payload["markers"]
    rules = payload["cross_cutting_fail_closed_rules"]
    price = _domains_by_id(payload)["REFERENCE_PRICE"]

    assert markers["NO_FILL_PRICE_AS_REFERENCE_PRICE_OBSERVATION"] is True
    assert markers["NO_FILL_PRICE_AS_REFERENCE_PRICE_AUTHORITY"] is True
    assert rules["fill_price_as_reference_observation_allowed"] is False
    assert price["allowed_price_types"] == list(REQUIRED_REFERENCE_PRICE_TYPES)
    assert price["forbidden_price_types_as_reference_observation"] == ["fill", "execution"]
    assert "FILL_OR_EXECUTION_PRICE_AS_REFERENCE_OBSERVATION_FORBIDDEN" in price["failure_states"]
    assert (
        "fill_or_execution_price_as_upstream_reference_price_observation"
        in price["forbidden_behaviors"]
    )
    assert (
        "implicit_substitution_among_mark_index_last_candle_close" in price["forbidden_behaviors"]
    )
    assert "STALE_REFERENCE_PRICE" in price["failure_states"]
    assert "TIME_AXIS_MISMATCH" in price["failure_states"]
    assert "staleness_classification" in price["required_freshness_fields"]
    assert "time_axis_mismatch_classification" in price["required_freshness_fields"]


def test_universal_multiplier_one_default_forbidden() -> None:
    payload = _load_contract()
    markers = payload["markers"]
    rules = payload["cross_cutting_fail_closed_rules"]
    meta = _domains_by_id(payload)["INSTRUMENT_METADATA"]

    assert markers["NO_UNIVERSAL_MULTIPLIER_ONE_DEFAULT"] is True
    assert rules["universal_multiplier_one_default_allowed"] is False
    assert "UNIVERSAL_MULTIPLIER_ONE_DEFAULT_FORBIDDEN" in meta["failure_states"]
    assert "universal_multiplier_one_default" in meta["forbidden_behaviors"]
    assert "UNKNOWN_FIELD_REPLACED_WITH_NEUTRAL_DEFAULT_FORBIDDEN" in meta["failure_states"]
    assert "replace_unknown_fields_with_neutral_defaults" in meta["forbidden_behaviors"]
    assert meta["snapshot_research_config_authority_class"] == "NON_AUTHORITATIVE"
    for field in REQUIRED_INSTRUMENT_NORMALIZED_FIELDS:
        assert field in meta["required_normalized_fields"], field


def test_account_equity_raw_and_normalized_contracts() -> None:
    equity = _domains_by_id(_load_contract())["ACCOUNT_EQUITY"]
    for field in (
        "raw_balance_fields_preserved",
        "account_id_or_account_scope",
        "venue",
        "currency",
        "observed_at_or_as_of",
        "provenance",
    ):
        assert field in equity["required_raw_fields"], field
    for field in (
        "explicit_normalized_equity_dimension_name",
        "account_id_or_account_scope",
        "venue",
        "currency",
        "observed_at_or_as_of",
        "provenance",
    ):
        assert field in equity["required_normalized_fields"], field
    assert "MISSING_BALANCE_DATA" in equity["failure_states"]
    assert "PARTIAL_BALANCE_DATA" in equity["failure_states"]
    assert "CONTRADICTORY_BALANCE_DATA" in equity["failure_states"]
    assert "AMBIGUOUS_EQUITY_DIMENSION" in equity["failure_states"]


def test_separate_go_gates_pinned() -> None:
    payload = _load_contract()
    markers = payload["markers"]
    pins = payload["global_pins"]
    rules = payload["cross_cutting_fail_closed_rules"]

    for key in (
        "SHADOW_BINDING_REQUIRES_SEPARATE_GO",
        "LIVE_BINDING_REQUIRES_SEPARATE_GO",
        "NETWORK_ACCESS_REQUIRES_SEPARATE_GO",
        "EXCHANGE_ACCESS_REQUIRES_SEPARATE_GO",
        "PRODUCER_IMPLEMENTATION_REQUIRES_SEPARATE_GO",
        "FRACTION_TO_UNITS_REQUIRES_SEPARATE_GO",
    ):
        assert markers[key] is True, key
    assert pins["shadow_binding_requires_separate_go"] is True
    assert pins["live_binding_requires_separate_go"] is True
    assert pins["network_access_requires_separate_go"] is True
    assert pins["exchange_access_requires_separate_go"] is True
    assert pins["producer_implementation_requires_separate_go"] is True
    assert pins["fraction_to_units_requires_separate_go"] is True
    assert rules["producer_implementation_requires_separate_go"] is True


def test_consistency_with_provenance_binding_and_authority_decision() -> None:
    payload = _load_contract()
    markers = payload["markers"]
    provenance = json.loads(_read(PROVENANCE_BINDING_JSON))
    authority = json.loads(_read(AUTHORITY_DECISION_JSON))

    assert markers["PROVENANCE_BINDING_REMAINS_CONVERSION_NOT_READY"] is True
    assert markers["AUTHORITY_DECISION_CONTRACT_REMAINS_FROZEN"] is True
    assert provenance["markers"]["CONVERSION_READY"] is False
    assert provenance["markers"]["OWNER_ASSIGNED"] is False
    assert provenance["companion_conversion_input_binding"]["conversion_ready"] is False
    assert authority["markers"]["CONVERSION_READY"] is False
    assert authority["markers"]["ACCOUNT_EQUITY_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert authority["markers"]["REFERENCE_PRICE_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert authority["markers"]["INSTRUMENT_METADATA_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert authority["markers"]["ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED"] is False
    assert authority["markers"]["REFERENCE_PRICE_AUTHORITY_CHAIN_CLOSED"] is False
    assert authority["markers"]["INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED"] is False
    assert authority["markers"]["AUTHORITY_DECISION_CONTRACT_FROZEN"] is True
    assert (
        payload["referenced_contracts"]["risk_sizing_productive_input_provenance_binding_v1"]
        == "config/governance/risk_sizing_productive_input_provenance_binding_v1.json"
    )
    assert (
        payload["referenced_contracts"]["risk_sizing_authority_decision_contract_freeze_v1"]
        == "config/governance/risk_sizing_authority_decision_contract_freeze_v1.json"
    )


def test_global_non_claims_and_drift_policy() -> None:
    payload = _load_contract()
    for claim in GLOBAL_NON_CLAIMS:
        assert claim in payload["global_non_claims"], claim
    drift = payload["drift_policy"]
    assert drift["productive_adapter_implemented_claimed_true"] == "FAIL"
    assert drift["productive_producer_selected_claimed_true"] == "FAIL"
    assert drift["authority_binding_implemented_claimed_true"] == "FAIL"
    assert drift["companion_reachable_claimed_true"] == "FAIL"
    assert drift["conversion_consumer_bound_claimed_true"] == "FAIL"
    assert drift["observation_or_transport_or_normalization_claimed_authority"] == "FAIL"
    assert drift["partial_or_ambiguous_or_stale_data_not_fail_closed"] == "FAIL"
    assert drift["fill_price_as_reference_observation_allowed"] == "FAIL"
    assert drift["universal_multiplier_one_default_allowed"] == "FAIL"
    assert drift["src_import_or_runtime_wiring_claimed"] == "FAIL"


def test_baseline_obl_b05_counts_unchanged() -> None:
    payload = _load_contract()
    markers = payload["markers"]
    inventory = json.loads(_read(OWNER_INVENTORY_JSON))
    companion_freeze = json.loads(_read(COMPANION_FREEZE_JSON))
    resolution = json.loads(_read(RESOLUTION_AUDIT_JSON))
    unresolved = json.loads(_read(UNRESOLVED_V0_JSON))
    consumption = json.loads(_read(CONSUMPTION_JSON))
    topology = json.loads(_read(TOPOLOGY_JSON))

    assert markers["EXPECTED_PRIMARY_OWNER_COUNT"] == 5
    assert markers["EXPECTED_PRODUCTIVE_DIRECT_EDGE_COUNT"] == 8
    assert markers["EXPECTED_COMPANION_EDGE_COUNT"] == 2
    assert markers["EXPECTED_DIRECT_SIZING_BYPASS_COUNT"] == 5
    assert markers["EXPECTED_PASS_THROUGH_EDGE_COUNT"] == 2
    assert markers["EXPECTED_AMBIGUOUS_EDGE_COUNT"] == 3
    assert markers["EXPECTED_CONSUMPTION_EDGE_COUNT"] == 27
    assert markers["EXPECTED_OVERWRITE_EDGE_COUNT"] == 13
    assert markers["EXPECTED_WRAP_DELEGATE_EDGE_COUNT"] == 1
    assert markers["EXPECTED_FINAL_QUANTITY_PROVENANCE_RESOLVED_PATH_COUNT"] == 5
    assert markers["EXPECTED_FINAL_QUANTITY_PROVENANCE_UNRESOLVED_PATH_COUNT"] == 3
    assert markers["EXPECTED_SEMANTIC_CONFLICT_PATH_COUNT"] == 3
    assert markers["EXPECTED_CONVERSION_INPUT_FAMILY_COUNT"] == 3
    assert inventory["markers"]["PRODUCTIVE_RISK_SIZING_DECISION_OWNER_COUNT"] == 5
    assert companion_freeze["markers"]["COMPANION_DECLARED_INTENT"] == "FRACTION_DECIMAL_0_1"
    assert companion_freeze["markers"]["EFS_QUARANTINED"] is True
    assert companion_freeze["markers"]["FINAL_QUANTITY_PROVENANCE_RESOLVED"] is False
    assert resolution["markers"]["EXPECTED_SEMANTIC_CONFLICT_PATH_COUNT"] == 3
    assert unresolved["markers"]["EXPECTED_UNRESOLVED_PATH_COUNT"] == 3
    assert consumption["markers"]["EXPECTED_CONSUMPTION_EDGE_COUNT"] == 27
    assert topology["markers"]["EXPECTED_PRODUCTIVE_DIRECT_EDGE_COUNT"] == 8


def test_no_productive_src_caller_or_companion_import_added() -> None:
    src_root = REPO_ROOT / "src"
    hits: list[str] = []
    for path in src_root.rglob("*.py"):
        text = _read(path)
        for needle in FORBIDDEN_PRODUCTIVE_IMPORT_NEEDLES:
            if needle in text:
                hits.append(f"{path.relative_to(REPO_ROOT)}:{needle}")
    assert hits == [], f"productive conversion/adapter wiring FAIL: {hits}"

    for rel in ("src/live/shadow_session.py", "src/execution/live_session.py"):
        text = _read(REPO_ROOT / rel)
        assert "governed_producer_observation_adapter" not in text
        assert "risk_sizing_governed_producer_observation" not in text
        assert "capital_risk_sizing" not in text
        assert "evaluate_capital_risk_sizing_v1" not in text


def test_readme_and_referenced_contracts_exist() -> None:
    payload = _load_contract()
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "RISK_SIZING_GOVERNED_PRODUCER_OBSERVATION_ADAPTER_CONTRACT_V1.md" in readme
    assert "RISK_SIZING_PRODUCTIVE_INPUT_PROVENANCE_BINDING_V1.md" in readme
    assert "RISK_SIZING_AUTHORITY_DECISION_CONTRACT_FREEZE_V1.md" in readme
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
        "RISK_SIZING_GOVERNED_PRODUCER_OBSERVATION_ADAPTER_CONTRACT_V1",
        "PRODUCER_OBSERVATION_ADAPTER_CONTRACT_FROZEN",
        "ACCOUNT_EQUITY_ADAPTER_CONTRACT_FROZEN",
        "REFERENCE_PRICE_ADAPTER_CONTRACT_FROZEN",
        "INSTRUMENT_METADATA_ADAPTER_CONTRACT_FROZEN",
        "OBSERVATION_IS_NOT_AUTHORITY",
        "TRANSPORT_IS_NOT_AUTHORITY",
        "NORMALIZATION_IS_NOT_AUTHORITY",
        "NO_START_BALANCE_AS_RUNNING_EQUITY",
        "NO_FILL_PRICE_AS_REFERENCE_PRICE_OBSERVATION",
        "NO_UNIVERSAL_MULTIPLIER_ONE_DEFAULT",
        "SHADOW_BINDING_REQUIRES_SEPARATE_GO",
        "LIVE_BINDING_REQUIRES_SEPARATE_GO",
        "NETWORK_ACCESS_REQUIRES_SEPARATE_GO",
        "EXCHANGE_ACCESS_REQUIRES_SEPARATE_GO",
        "PRODUCER_IMPLEMENTATION_REQUIRES_SEPARATE_GO",
        "FRACTION_TO_UNITS_REQUIRES_SEPARATE_GO",
        "PROVENANCE_BINDING_REMAINS_CONVERSION_NOT_READY",
        "AUTHORITY_DECISION_CONTRACT_REMAINS_FROZEN",
    )
    bool_false_keys = (
        "CONVERSION_READY",
        "PRODUCTIVE_SEMANTICS_CHANGE_AUTHORIZED",
        "AUTHORITY_ACTIVATION_AUTHORIZED",
        "OWNER_ASSIGNED",
        "OWNER_ACTIVATED",
        "OBSERVATION_IS_AUTHORITY",
        "TRANSPORT_IS_AUTHORITY",
        "NORMALIZATION_IS_AUTHORITY",
        "AUTHORITY_BINDING_IMPLEMENTED",
        "PRODUCTIVE_ADAPTER_IMPLEMENTED",
        "PRODUCTIVE_PRODUCER_SELECTED",
        "COMPANION_REACHABLE",
        "CONVERSION_CONSUMER_BOUND",
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
    fail_closed_keys = (
        "PARTIAL_DATA_POLICY",
        "AMBIGUOUS_DIMENSION_POLICY",
        "STALE_DATA_POLICY",
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
    for key in fail_closed_keys:
        assert markers[key] == "FAIL_CLOSED"
        assert f"{key}=FAIL_CLOSED" in text, key
    assert markers["EXPECTED_INPUT_DOMAIN_COUNT"] == 3
    assert "EXPECTED_INPUT_DOMAIN_COUNT=3" in text
    assert markers["EXPECTED_ADAPTER_LAYER_COUNT"] == 5
    assert "EXPECTED_ADAPTER_LAYER_COUNT=5" in text


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
    assert "PRODUCTIVE_ADAPTER_IMPLEMENTED=true" not in text
    assert "PRODUCTIVE_PRODUCER_SELECTED=true" not in text
    assert "AUTHORITY_BINDING_IMPLEMENTED=true" not in text
    assert "COMPANION_REACHABLE=true" not in text
    assert "CONVERSION_CONSUMER_BOUND=true" not in text
