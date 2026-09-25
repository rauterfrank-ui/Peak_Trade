"""BOUNDED_WP_C2_DOMAIN_AUTHORITY_RESOLUTION_V1 — forensic resolution + closure reevaluation."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

RESOLUTION_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_c2_domain_authority_resolution_v1.json"
)
RESOLUTION_DOC = (
    REPO_ROOT / "docs" / "governance" / "RISK_SIZING_C2_DOMAIN_AUTHORITY_RESOLUTION_V1.md"
)
C2_JSON = REPO_ROOT / "config" / "governance" / "risk_sizing_c2_input_authority_closure_v1.json"
PROVENANCE_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_productive_input_provenance_binding_v1.json"
)
AUTHORITY_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_authority_decision_contract_freeze_v1.json"
)
BYPASS_IMPL_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_bypass_fate_implementation_contract_v1.json"
)

EXPECTED_INPUT_IDS = (
    "ACCOUNT_EQUITY_AVAILABLE_CAPITAL",
    "REFERENCE_PRICE",
    "INSTRUMENT_QUANTITY_METADATA",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_resolution_wp_markers_and_no_bindings_implemented() -> None:
    res = _load(RESOLUTION_JSON)
    markers = res["markers"]
    assert res["workpackage_id"] == "BOUNDED_WP_C2_DOMAIN_AUTHORITY_RESOLUTION_V1"
    assert res["prior_census_binding"]["c2_required_input_count"] == 3
    assert res["prior_census_binding"]["c2_input_set_complete_proven"] is True
    assert markers["C2_STATUS"] == "UNRESOLVED"
    assert markers["C2_CLOSURE_RULE_SATISFIED"] is False
    assert markers["C2_DOMAINS_PROVEN_CURRENT_COUNT"] == 0
    assert markers["CONVERSION_READY"] is False
    assert markers["RUNTIME_MUTATION_EXECUTED"] is False
    assert markers["SRC_CHANGED"] is False
    assert markers["B05_FATE_PHASE_STATUS"] == "CLOSED"
    assert markers["FATE_IMPLEMENTATION_EXECUTED"] is True
    assert markers["FATE_IMPLEMENTATION_COMPLETE_COUNT"] == 5
    assert res["implemented_authority_bindings"] == []


def test_domain_final_statuses_match_c2_census_and_no_proven_current() -> None:
    res = _load(RESOLUTION_JSON)
    c2 = _load(C2_JSON)
    for iid in EXPECTED_INPUT_IDS:
        domain = res["domain_resolutions"][iid]
        census = c2["c2_input_census"][iid]
        assert domain["final_status"] == census["status"]
        if iid == "ACCOUNT_EQUITY_AVAILABLE_CAPITAL":
            assert domain["initial_status"] == "CONFLICTING"
            assert domain["final_status"] == "PARTIAL"
        else:
            assert domain["initial_status"] == census["status"]
        assert domain["final_status"] != "PROVEN_CURRENT"
        assert domain["c2_authority_binding_implemented"] is False


def test_account_equity_partial_owner_ratified_companion_unbound() -> None:
    res = _load(RESOLUTION_JSON)
    eq = res["domain_resolutions"]["ACCOUNT_EQUITY_AVAILABLE_CAPITAL"]
    assert eq["final_status"] == "PARTIAL"
    assert eq["owner"] == "ops.governed_productive_account_equity_authority_producer_v1"
    assert eq["owner_scope"] == "FULL_CORE_TRACK_ONLY"
    assert eq["handoff"] == "NO_CONVERSION_HANDOFF_ON_COMPANION_PATH"
    assert eq["provenance_status_companion"] == "REQUIRED_INPUT_MISSING"
    assert len(eq["conflicts_remaining"]) >= 2
    assert eq["full_core_parallel_source"]["observation_is_not_authority"] is True
    shadow = REPO_ROOT / "src/live/shadow_session.py"
    assert "position_fraction" in shadow.read_text(encoding="utf-8")


def test_reference_price_unknown_no_candle_close_authority() -> None:
    res = _load(RESOLUTION_JSON)
    price = res["domain_resolutions"]["REFERENCE_PRICE"]
    assert price["final_status"] == "UNKNOWN"
    assert price["owner"] == "UNRESOLVED"
    prov = _load(PROVENANCE_JSON)
    rec = next(r for r in prov["input_provenance_records"] if r["input_id"] == "REFERENCE_PRICE")
    assert "candle_close" in " ".join(rec["explicit_non_sources"]).lower()


def test_instrument_metadata_unresolved_no_offline_default_authority() -> None:
    res = _load(RESOLUTION_JSON)
    inst = res["domain_resolutions"]["INSTRUMENT_QUANTITY_METADATA"]
    assert inst["final_status"] == "UNRESOLVED"
    assert inst["owner"] == "UNRESOLVED"
    auth = _load(AUTHORITY_JSON)
    dom = next(d for d in auth["input_domains"] if d["domain_id"] == "INSTRUMENT_METADATA")
    assert dom["authority_owner"] == "UNRESOLVED"
    assert dom["audit_decision_class"] == "NO_PRODUCTIVE_PRODUCER"


def test_c2_closure_reevaluation_gate_not_satisfied() -> None:
    res = _load(RESOLUTION_JSON)
    reeval = res["c2_closure_reevaluation"]
    assert reeval["c2_closure_rule_satisfied"] is False
    assert reeval["c2_status"] == "UNRESOLVED"
    assert reeval["domains_proven_current_count"] == 0
    c2 = _load(C2_JSON)
    assert c2["c2_closure_gate"]["c2_closure_rule_satisfied"] is False


def test_b05_invariants_unchanged() -> None:
    bypass = _load(BYPASS_IMPL_JSON)
    assert bypass["markers"]["B05_FATE_PHASE_STATUS"] == "CLOSED"
    assert bypass["markers"]["FATE_IMPLEMENTATION_EXECUTED"] is True
    assert bypass["markers"]["C2_INPUT_AUTHORITIES"] == "UNRESOLVED"
    assert bypass["markers"]["CONVERSION_READY"] is False


def test_resolution_doc_markers_present() -> None:
    text = RESOLUTION_DOC.read_text(encoding="utf-8")
    for marker in (
        "RISK_SIZING_C2_DOMAIN_AUTHORITY_RESOLUTION_V1=true",
        "C2_STATUS=UNRESOLVED",
        "CONVERSION_READY=false",
    ):
        assert marker in text


def test_productive_src_unmodified_by_resolution_wp() -> None:
    needle = "risk_sizing_c2_domain_authority_resolution_v1"
    hits: list[str] = []
    for path in (REPO_ROOT / "src").rglob("*.py"):
        if needle in path.read_text(encoding="utf-8"):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []


def test_forensic_evidence_anchor_files_exist() -> None:
    res = _load(RESOLUTION_JSON)
    for iid in EXPECTED_INPUT_IDS:
        for anchor in res["domain_resolutions"][iid]["forensic_evidence_anchors"]:
            rel = anchor["file"].split("|")[0]
            path = REPO_ROOT / rel
            assert path.is_file(), f"missing anchor {rel} for {iid}"
