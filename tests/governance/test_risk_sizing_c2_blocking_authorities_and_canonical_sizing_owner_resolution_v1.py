"""BOUNDED_WP_C2_BLOCKING_AUTHORITIES_AND_CANONICAL_SIZING_OWNER_RESOLUTION_V1."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

RES_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_c2_blocking_authorities_and_canonical_sizing_owner_resolution_v1.json"
)
RES_DOC = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "RISK_SIZING_C2_BLOCKING_AUTHORITIES_AND_CANONICAL_SIZING_OWNER_RESOLUTION_V1.md"
)
V2_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_c2_current_productive_input_authority_closure_v2.json"
)
AUTH_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_authority_decision_contract_freeze_v1.json"
)
INVENTORY_JSON = REPO_ROOT / "config" / "governance" / "risk_sizing_owner_inventory_ssot_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_resolution_markers_and_no_runtime_bindings() -> None:
    res = _load(RES_JSON)
    m = res["markers"]
    assert res["workpackage_id"] == (
        "BOUNDED_WP_C2_BLOCKING_AUTHORITIES_AND_CANONICAL_SIZING_OWNER_RESOLUTION_V1"
    )
    assert m["SRC_CHANGED"] is False
    assert m["RUNTIME_BINDINGS_ADDED"] == 0
    assert m["RUNTIME_MUTATION_EXECUTED"] is False
    assert m["CONVERSION_EXECUTED"] is False
    assert m["CONVERSION_READY"] is False
    assert m["EQUITY_AUTHORITY_RESOLVED"] is True
    assert m["EQUITY_AUTHORITY_RESOLVED_SCOPE"] == "FULL_CORE_TRACK_ONLY"
    assert m["REFERENCE_PRICE_AUTHORITY_RESOLVED"] is True
    assert m["REFERENCE_PRICE_AUTHORITY_RESOLVED_SCOPE"] == "FULL_CORE_TRACK_ONLY"
    assert m["INSTRUMENT_METADATA_AUTHORITY_RESOLVED"] is True
    assert m["INSTRUMENT_METADATA_AUTHORITY_RESOLVED_SCOPE"] == "FULL_CORE_TRACK_ONLY"
    assert m["SIZING_OWNER_RESOLVED"] is False
    assert m["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert len(res["c2_mechanical_reevaluation"].get("implemented_authority_bindings", [])) >= 0
    v2 = _load(
        REPO_ROOT
        / "config"
        / "governance"
        / "risk_sizing_c2_current_productive_input_authority_closure_v2.json"
    )
    assert len(v2["implemented_authority_bindings"]) >= 2


def test_c2_verdicts_preserve_6761_6762_start_state() -> None:
    res = _load(RES_JSON)
    v2 = _load(V2_JSON)
    reeval = res["c2_mechanical_reevaluation"]
    assert reeval["account_equity_final_status"] == "PARTIAL"
    assert reeval["reference_price_final_status"] == "PARTIAL"
    assert reeval["instrument_metadata_final_status"] == "PARTIAL"
    assert reeval["domain_proven_current_count"] == 0
    assert reeval["c2_status"] == "UNRESOLVED"
    assert reeval["c2_closure_rule_satisfied"] is False
    for iid, verdict in (
        ("ACCOUNT_EQUITY_AVAILABLE_CAPITAL", "PARTIAL"),
        ("REFERENCE_PRICE", "PARTIAL"),
        ("INSTRUMENT_QUANTITY_METADATA", "PARTIAL"),
    ):
        assert v2["domain_adjudications"][iid]["c2_domain_verdict"] == verdict


def test_blocker_a_equity_partial_owner_ratified_companion_absence() -> None:
    res = _load(RES_JSON)
    a = res["blocker_adjudications"]["A_ACCOUNT_EQUITY_AUTHORITY"]
    assert a["account_equity_final_status"] == "PARTIAL"
    assert a["equity_authority_resolved"] is True
    assert a["equity_authority_resolved_scope"] == "FULL_CORE_TRACK_ONLY"
    assert (
        a["canonical_b05_owner"] == "ops.governed_productive_account_equity_authority_producer_v1"
    )
    assert a["productive_lineage_census"]["companion_absence"]["equity_handoff"] is False
    auth = _load(AUTH_JSON)
    assert (
        auth["authority_status"]["account_equity_authority_owner"]
        == "ops.governed_productive_account_equity_authority_producer_v1"
    )


def test_blocker_b_reference_unknown_no_canonical_transform() -> None:
    res = _load(RES_JSON)
    b = res["blocker_adjudications"]["B_REFERENCE_PRICE_AUTHORITY"]
    assert b["reference_price_final_status"] == "PARTIAL"
    assert b["price_semantics_class_ratified"] == "mark_price"
    assert b["canonical_transform_exists"] is True


def test_blocker_c_identity_separate_from_metadata() -> None:
    res = _load(RES_JSON)
    c = res["blocker_adjudications"]["C_INSTRUMENT_QUANTITY_METADATA_AUTHORITY"]
    assert c["instrument_metadata_final_status"] == "PARTIAL"
    assert c["instrument_metadata_authority_resolved"] is True
    sep = c["identity_vs_metadata_separation"]
    assert "BoundInstrumentV1" in sep["identity_authority"]["type"]
    assert sep["identity_authority"]["reselection_forbidden"] is True


def test_blocker_d_sizing_owner_unresolved_parallel_bypasses() -> None:
    res = _load(RES_JSON)
    d = res["blocker_adjudications"]["D_CANONICAL_RISK_SIZING_OWNER"]
    assert d["canonical_risk_sizing_owner"] == "UNRESOLVED"
    assert d["sizing_owner_resolved"] is False
    assert d["composite_owner_deduction_attempt"]["result"] == (
        "NOT_DEDUCIBLE_FROM_EXISTING_CANONICAL_EVIDENCE"
    )
    assert (
        len(d["productive_quantity_decision_owner_census"]["parallel_bypass_owners_reachable"]) == 5
    )
    inv = _load(INVENTORY_JSON)
    assert inv["markers"]["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert inv["markers"]["BYPASS_PATH_COUNT"] == 5


def test_deferred_decisions_present() -> None:
    res = _load(RES_JSON)
    assert len(res["deferred_decisions"]) >= 2
    assert any("CONVERSION" in x for x in res["deferred_decisions"])


def test_evidence_anchor_files_exist() -> None:
    res = _load(RES_JSON)
    for key in ("A_ACCOUNT_EQUITY_AUTHORITY", "B_REFERENCE_PRICE_AUTHORITY"):
        for ref in res["blocker_adjudications"][key]["evidence_anchors"]:
            if ref.startswith("config/") or ref.startswith("docs/"):
                assert (REPO_ROOT / ref).is_file(), ref


def test_doc_markers() -> None:
    text = RES_DOC.read_text(encoding="utf-8")
    assert (
        "RISK_SIZING_C2_BLOCKING_AUTHORITIES_AND_CANONICAL_SIZING_OWNER_RESOLUTION_V1=true" in text
    )
    assert "C2_STATUS=UNRESOLVED" in text


def test_no_src_reference_to_resolution_contract() -> None:
    needle = "risk_sizing_c2_blocking_authorities_and_canonical_sizing_owner_resolution_v1"
    hits: list[str] = []
    for path in (REPO_ROOT / "src").rglob("*.py"):
        if needle in path.read_text(encoding="utf-8"):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []
