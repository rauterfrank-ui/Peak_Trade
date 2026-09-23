"""BOUNDED_WP_C2_INPUT_AUTHORITY_CLOSURE_V1 — census + closure verdict (governance only)."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

C2_JSON = REPO_ROOT / "config" / "governance" / "risk_sizing_c2_input_authority_closure_v1.json"
C2_DOC = REPO_ROOT / "docs" / "governance" / "RISK_SIZING_C2_INPUT_AUTHORITY_CLOSURE_V1.md"
PROVENANCE_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_productive_input_provenance_binding_v1.json"
)
AUTHORITY_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_authority_decision_contract_freeze_v1.json"
)
BYPASS_IMPL_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_bypass_fate_implementation_contract_v1.json"
)
INVENTORY_JSON = REPO_ROOT / "config" / "governance" / "risk_sizing_owner_inventory_ssot_v1.json"

EXPECTED_INPUT_IDS = (
    "ACCOUNT_EQUITY_AVAILABLE_CAPITAL",
    "REFERENCE_PRICE",
    "INSTRUMENT_QUANTITY_METADATA",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_c2_closure_verdict_unresolved_and_gate_not_satisfied() -> None:
    c2 = _load(C2_JSON)
    markers = c2["markers"]
    assert c2["workpackage_id"] == "BOUNDED_WP_C2_INPUT_AUTHORITY_CLOSURE_V1"
    assert markers["C2_STATUS"] == "UNRESOLVED"
    assert markers["C2_INPUT_AUTHORITIES"] == "UNRESOLVED"
    assert markers["C2_CLOSURE_RULE_SATISFIED"] is False
    assert markers["C2_INPUT_SET_COMPLETE_PROVEN"] is True
    assert markers["C2_REQUIRED_INPUT_COUNT"] == 3
    assert markers["CONVERSION_READY"] is False
    assert markers["RUNTIME_MUTATION_EXECUTED"] is False
    assert markers["B05_FATE_PHASE_STATUS"] == "CLOSED"
    assert markers["FATE_IMPLEMENTATION_EXECUTED"] is True
    assert markers["FATE_IMPLEMENTATION_COMPLETE_COUNT"] == 5
    gate = c2["c2_closure_gate"]
    assert gate["c2_closure_rule_satisfied"] is False
    assert c2["implemented_authority_bindings"] == []


def test_c2_input_set_matches_provenance_binding_exhaustive() -> None:
    c2 = _load(C2_JSON)
    prov = _load(PROVENANCE_JSON)
    records = prov["input_provenance_records"]
    required = [r for r in records if r["required_for_companion_conversion"]]
    assert len(required) == 3
    assert {r["input_id"] for r in required} == set(EXPECTED_INPUT_IDS)
    assert c2["c2_required_inputs_sorted"] == list(EXPECTED_INPUT_IDS)
    for iid in EXPECTED_INPUT_IDS:
        census = c2["c2_input_census"][iid]
        assert census["c2_authority_binding_implemented"] is False
        assert census["status"] != "PROVEN_CURRENT"
        assert census["domain_authority_resolution_final_status"] == census["status"]
        assert (
            "risk_sizing_c2_domain_authority_resolution_v1.json"
            in census["domain_authority_resolution_ref"]
        )


def test_c2_census_aligns_with_authority_decision_unresolved_owners() -> None:
    c2 = _load(C2_JSON)
    auth = _load(AUTHORITY_JSON)
    status = auth["authority_status"]
    assert status["account_equity_authority_owner"] == "UNRESOLVED"
    assert status["reference_price_authority_owner"] == "UNRESOLVED"
    assert status["instrument_metadata_authority_owner"] == "UNRESOLVED"
    assert status["account_equity_authority_chain_closed"] is False
    assert status["reference_price_authority_chain_closed"] is False
    assert status["instrument_metadata_authority_chain_closed"] is False
    assert c2["c2_input_census"]["ACCOUNT_EQUITY_AVAILABLE_CAPITAL"]["status"] == "CONFLICTING"
    assert c2["c2_input_census"]["REFERENCE_PRICE"]["status"] == "UNKNOWN"
    assert c2["c2_input_census"]["INSTRUMENT_QUANTITY_METADATA"]["status"] == "UNRESOLVED"


def test_b05_and_inventory_c2_markers_unchanged_unresolved() -> None:
    bypass = _load(BYPASS_IMPL_JSON)
    assert bypass["markers"]["C2_INPUT_AUTHORITIES"] == "UNRESOLVED"
    assert bypass["markers"]["CONVERSION_READY"] is False
    assert bypass["markers"]["FATE_IMPLEMENTATION_EXECUTED"] is True
    assert bypass["markers"]["B05_FATE_PHASE_STATUS"] == "CLOSED"
    inventory = _load(INVENTORY_JSON)
    assert inventory["markers"]["CONVERSION_READY"] is False
    assert inventory["markers"]["FATE_IMPLEMENTATION_EXECUTED"] is True


def test_c2_doc_markers_present() -> None:
    text = C2_DOC.read_text(encoding="utf-8")
    for marker in (
        "RISK_SIZING_C2_INPUT_AUTHORITY_CLOSURE_V1=true",
        "C2_STATUS=UNRESOLVED",
        "C2_INPUT_AUTHORITIES=UNRESOLVED",
        "CONVERSION_READY=false",
    ):
        assert marker in text


def test_productive_src_unmodified_by_c2_wp() -> None:
    needle = "risk_sizing_c2_input_authority_closure_v1"
    hits: list[str] = []
    for path in (REPO_ROOT / "src").rglob("*.py"):
        if needle in path.read_text(encoding="utf-8"):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []
