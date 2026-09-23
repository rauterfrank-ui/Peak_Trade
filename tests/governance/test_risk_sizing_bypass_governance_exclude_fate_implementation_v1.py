"""WP_B05_GOVERNANCE_EXCLUDE_FATE_IMPLEMENTATION_V1 — S2 governance implementation (no runtime)."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

IMPLEMENTATION_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_bypass_fate_implementation_contract_v1.json"
)
PROVENANCE_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_bypass_fate_provenance_binding_v1.json"
)
ADJUDICATION_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_bypass_fate_operator_adjudication_v1.json"
)
INVENTORY_JSON = REPO_ROOT / "config" / "governance" / "risk_sizing_owner_inventory_ssot_v1.json"
TOPOLOGY_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_caller_owner_topology_contract_v0.json"
)
AUDIT_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_final_quantity_provenance_resolution_audit_v1.json"
)

S2_BYPASS_IDS = (
    "BYPASS_CLASSIC_BACKTEST_DEFAULT",
    "BYPASS_LIVE_SHADOW_POSITION_FRACTION",
)
S1_BYPASS_IDS = (
    "BYPASS_CORE_POSITION_SIZER",
    "BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS",
)
OFFLINE_BYPASS_ID = "BYPASS_OFFLINE_EVAL_SIZING_CONTRACT"
EXCLUDE_FATE = "GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE"
EXCLUDE_PROVENANCE_EFFECT = (
    "EXCLUDE_FROM_AUTHORITATIVE_PRODUCTIVE_SIZE_PROVENANCE_FOR_SYSTEM_EVIDENCE"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_s2_slice_boundaries_and_global_incomplete() -> None:
    impl = _load(IMPLEMENTATION_JSON)
    markers = impl["markers"]
    assert markers["FATE_IMPLEMENTATION_EXECUTED"] is False
    assert markers["PER_BYPASS_FATE_IMPLEMENTATION_EXECUTED_COUNT"] == 4
    assert markers["S2_GOVERNANCE_EXCLUDE_FATE_IMPLEMENTATION_EXECUTED"] is True
    assert markers["S1_KEEP_PARALLEL_FATE_IMPLEMENTATION_EXECUTED"] is True
    assert markers["RUNTIME_MUTATION_EXECUTED"] is False
    assert markers["PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED"] is False
    s2 = impl["s2_governance_exclude_fate_implementation_v1"]
    assert s2["workpackage_id"] == "WP_B05_GOVERNANCE_EXCLUDE_FATE_IMPLEMENTATION_V1"
    assert s2["global_fate_implementation_executed_remains_false"] is True
    assert s2["offline_eval_fate_implementation_status"] == "NOT_STARTED"
    assert s2["s1_keep_parallel_implementations_unchanged"] is True


def test_s2_targets_complete_per_s0_completion_evidence() -> None:
    impl = _load(IMPLEMENTATION_JSON)
    adjudication = _load(ADJUDICATION_JSON)
    summary = adjudication["operator_fate_summary_sorted"]
    prov = _load(PROVENANCE_JSON)
    adm = prov["system_economic_evidence_admissibility"]
    assert adm[
        "bypass_stable_ids_excluded_from_authoritative_system_economic_size_evidence_sorted"
    ] == list(S2_BYPASS_IDS)
    for bid in S2_BYPASS_IDS:
        row = impl["bypass_fate_implementations"][bid]
        assert row["operator_fate_adjudication"] == EXCLUDE_FATE
        assert row["operator_fate_adjudication"] == summary[bid]
        assert row["fate_implementation_status"] == "COMPLETE"
        assert row["fate_implementation_executed"] is True
        assert row["completion_evidence_satisfied"] is True
        assert row["minimum_implementation_requirements_verified"] is True
        assert row["evidence_provenance_effect"] == EXCLUDE_PROVENANCE_EFFECT
        assert row["runtime_mutation_required"] is False
        pin = prov["bypass_provenance_pins"][bid]
        assert pin["governance_exclude_from_system_evidence_affirmed"] is True
        assert (
            pin["exclude_from_authoritative_productive_size_provenance_for_system_evidence"] is True
        )
        assert pin["system_economic_evidence_authoritative_size_owner_claim_permitted"] is False
        assert pin["reachability_pin"] == "REACHABLE_PRODUCTIVE"
        assert pin["reachability_pin_unchanged_by_this_slice"] is True


def test_offline_eval_remains_not_started() -> None:
    impl = _load(IMPLEMENTATION_JSON)
    row = impl["bypass_fate_implementations"][OFFLINE_BYPASS_ID]
    assert row["fate_implementation_status"] == "NOT_STARTED"
    assert row["fate_implementation_executed"] is False


def test_s1_implementations_unchanged() -> None:
    impl = _load(IMPLEMENTATION_JSON)
    prov = _load(PROVENANCE_JSON)
    for bid in S1_BYPASS_IDS:
        row = impl["bypass_fate_implementations"][bid]
        assert row["fate_implementation_status"] == "COMPLETE"
        assert row["operator_fate_adjudication"] == "KEEP_PARALLEL_NON_CANONICAL"
        pin = prov["bypass_provenance_pins"][bid]
        assert pin["parallel_non_canonical_affirmed"] is True
        assert pin["fate_implementation_executed"] is True


def test_classic_companion_and_topology_exclude_pins() -> None:
    topo = _load(TOPOLOGY_JSON)
    edges = {e["edge_id"]: e for e in topo["productive_direct_edges"]}
    feedback = edges["EDGE_FEEDBACK_CALC_POSITION_SIZE"]
    engine = edges["EDGE_ENGINE_CALC_POSITION_SIZE"]
    assert feedback["governance_exclude_fate_implementation_v1"][
        "companion_caller_shares_exclusion_provenance_class"
    ]
    assert (
        feedback["governance_exclude_fate_implementation_v1"]["bypass_stable_id"]
        == "BYPASS_CLASSIC_BACKTEST_DEFAULT"
    )
    assert (
        engine["governance_exclude_fate_implementation_v1"][
            "system_economic_evidence_authoritative_size_owner_claim_permitted"
        ]
        is False
    )
    by_id = {b["bypass_stable_id"]: b for b in topo["direct_sizing_bypass_edges"]}
    classic = by_id["BYPASS_CLASSIC_BACKTEST_DEFAULT"]
    assert classic["fate_implementation_v1"]["fate_implementation_status"] == "COMPLETE"
    shadow = by_id["BYPASS_LIVE_SHADOW_POSITION_FRACTION"]
    assert shadow["fate_implementation_v1"]["fraction_to_units_conversion_resolved"] is False


def test_shadow_audit_pin_without_live_conflation() -> None:
    audit = _load(AUDIT_JSON)
    path = next(p for p in audit["audited_paths"] if p["path_id"] == "PATH_SHADOW_COMPANION")
    block = path["governance_exclude_fate_implementation_v1"]
    assert block["bypass_stable_id"] == "BYPASS_LIVE_SHADOW_POSITION_FRACTION"
    assert block["classification_unchanged"] == "SEMANTIC_CONFLICT"
    assert (
        block["companion_live_session_edge_not_conflated"]
        == "COMPANION_LIVE_SESSION_POSITION_FRACTION"
    )
    assert block["system_economic_evidence_authoritative_size_owner_claim_permitted"] is False


def test_inventory_pins_align() -> None:
    inventory = _load(INVENTORY_JSON)
    bypass = {b["id"]: b for b in inventory["bypass_paths"]}
    for bid in S2_BYPASS_IDS:
        assert bypass[bid]["fate_implementation_executed"] is True
        assert bypass[bid]["evidence_provenance_effect"] == EXCLUDE_PROVENANCE_EFFECT


def test_productive_src_does_not_import_provenance_binding() -> None:
    needle = "risk_sizing_bypass_fate_provenance_binding_v1"
    hits: list[str] = []
    for path in (REPO_ROOT / "src").rglob("*.py"):
        if needle in path.read_text(encoding="utf-8"):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []
