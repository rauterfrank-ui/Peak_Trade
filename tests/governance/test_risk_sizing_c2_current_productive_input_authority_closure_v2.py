"""BOUNDED_WP_C2_CURRENT_PRODUCTIVE_INPUT_AUTHORITY_CLOSURE_V2 — productive lineage + verdict preservation."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

V2_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_c2_current_productive_input_authority_closure_v2.json"
)
V2_DOC = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "RISK_SIZING_C2_CURRENT_PRODUCTIVE_INPUT_AUTHORITY_CLOSURE_V2.md"
)
V1_RESOLUTION_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_c2_domain_authority_resolution_v1.json"
)
C2_JSON = REPO_ROOT / "config" / "governance" / "risk_sizing_c2_input_authority_closure_v1.json"
BYPASS_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_bypass_fate_implementation_contract_v1.json"
)

EXPECTED = (
    "ACCOUNT_EQUITY_AVAILABLE_CAPITAL",
    "REFERENCE_PRICE",
    "INSTRUMENT_QUANTITY_METADATA",
)
EXPECTED_VERDICTS = {
    "ACCOUNT_EQUITY_AVAILABLE_CAPITAL": "PARTIAL",
    "REFERENCE_PRICE": "PARTIAL",
    "INSTRUMENT_QUANTITY_METADATA": "PARTIAL",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v2_markers_and_c2_still_unresolved() -> None:
    v2 = _load(V2_JSON)
    m = v2["markers"]
    assert v2["workpackage_id"] == "BOUNDED_WP_C2_CURRENT_PRODUCTIVE_INPUT_AUTHORITY_CLOSURE_V2"
    assert m["C2_STATUS"] == "UNRESOLVED"
    assert m["C2_CLOSURE_RULE_SATISFIED"] is False
    assert m["C2_DOMAINS_PROVEN_CURRENT_COUNT"] == 0
    assert m["CONVERSION_READY"] is False
    assert m["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert len(v2["implemented_authority_bindings"]) >= 1


def test_domain_verdicts_match_6761_and_census() -> None:
    v2 = _load(V2_JSON)
    v1 = _load(V1_RESOLUTION_JSON)
    c2 = _load(C2_JSON)
    for iid in EXPECTED:
        dom = v2["domain_adjudications"][iid]
        assert dom["c2_domain_verdict"] == EXPECTED_VERDICTS[iid]
        if iid in ("INSTRUMENT_QUANTITY_METADATA", "REFERENCE_PRICE"):
            assert dom["c2_authority_binding_implemented"] is True
        else:
            assert dom["c2_authority_binding_implemented"] is False
        assert v1["domain_resolutions"][iid]["final_status"] == EXPECTED_VERDICTS[iid]
        assert c2["c2_input_census"][iid]["status"] == EXPECTED_VERDICTS[iid]
        assert "productive_lineage_matrix" in dom
        assert dom["productive_lineage_trace_status"] != "PROVEN_CURRENT"


def test_productive_lineage_anchors_exist() -> None:
    v2 = _load(V2_JSON)
    for iid in EXPECTED:
        for ref in v2["domain_adjudications"][iid]["evidence_anchors"]:
            if ref.endswith(".json"):
                assert (REPO_ROOT / ref).is_file(), ref
            elif ref.startswith("src/"):
                assert (REPO_ROOT / ref.split("|")[0]).is_file(), ref


def test_account_equity_productive_chain_without_companion_binding() -> None:
    v2 = _load(V2_JSON)
    eq = v2["domain_adjudications"]["ACCOUNT_EQUITY_AVAILABLE_CAPITAL"]
    assert eq["c2_domain_verdict"] == "PARTIAL"
    companion = eq["productive_lineage_matrix"]["companion_c2_consumer"]
    assert companion["equity_input_present"] is False


def test_reference_price_mark_chain_not_elevated() -> None:
    v2 = _load(V2_JSON)
    price = v2["domain_adjudications"]["REFERENCE_PRICE"]
    assert price["c2_domain_verdict"] == "PARTIAL"
    chain = price["productive_lineage_matrix"]["producer_chain"]
    assert any("mark_price" in str(step) for step in chain)
    assert (
        price["productive_lineage_matrix"]["companion_c2_consumer"]["reference_price_input_present"]
        is False
    )


def test_instrument_cap24_identity_with_full_core_binding_partial() -> None:
    v2 = _load(V2_JSON)
    inst = v2["domain_adjudications"]["INSTRUMENT_QUANTITY_METADATA"]
    assert inst["c2_domain_verdict"] == "PARTIAL"
    assert inst["c2_authority_binding_implemented"] is True
    identity = inst["productive_lineage_matrix"]["identity_chain"][0]
    assert "BoundInstrumentV1" in identity["output"]


def test_b05_invariants_and_closure_gate() -> None:
    bypass = _load(BYPASS_JSON)
    assert bypass["markers"]["B05_FATE_PHASE_STATUS"] == "CLOSED"
    v2 = _load(V2_JSON)
    assert v2["c2_closure_reevaluation"]["c2_closure_rule_satisfied"] is False


def test_v2_doc_markers() -> None:
    text = V2_DOC.read_text(encoding="utf-8")
    assert "RISK_SIZING_C2_CURRENT_PRODUCTIVE_INPUT_AUTHORITY_CLOSURE_V2=true" in text
    assert "C2_STATUS=UNRESOLVED" in text


def test_no_src_mutation_marker_in_productive_src() -> None:
    needle = "risk_sizing_c2_current_productive_input_authority_closure_v2"
    hits: list[str] = []
    for path in (REPO_ROOT / "src").rglob("*.py"):
        if needle in path.read_text(encoding="utf-8"):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []
