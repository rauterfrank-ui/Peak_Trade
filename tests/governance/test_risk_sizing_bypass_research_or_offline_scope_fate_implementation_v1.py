"""WP_B05_RESEARCH_OR_OFFLINE_SCOPE_FATE_IMPLEMENTATION_V1 — S3 governance (no runtime)."""

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
AUTHORITY_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_authority_decision_contract_freeze_v1.json"
)

S3_BYPASS_ID = "BYPASS_OFFLINE_EVAL_SIZING_CONTRACT"
S1_BYPASS_IDS = (
    "BYPASS_CORE_POSITION_SIZER",
    "BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS",
)
S2_BYPASS_IDS = (
    "BYPASS_CLASSIC_BACKTEST_DEFAULT",
    "BYPASS_LIVE_SHADOW_POSITION_FRACTION",
)
OFFLINE_FATE = "RESEARCH_OR_OFFLINE_SCOPE_ONLY"
OFFLINE_PROVENANCE_EFFECT = (
    "RESEARCH_OR_OFFLINE_SCOPE_ONLY_PROVENANCE_LABEL; NOT_PRODUCTIVE_SYSTEM_EVIDENCE_SIZE_AUTHORITY"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_s3_slice_boundaries_preserve_prior_slices() -> None:
    impl = _load(IMPLEMENTATION_JSON)
    s3 = impl["s3_research_or_offline_scope_fate_implementation_v1"]
    assert s3["workpackage_id"] == "WP_B05_RESEARCH_OR_OFFLINE_SCOPE_FATE_IMPLEMENTATION_V1"
    assert s3["global_fate_implementation_executed_remains_false"] is True
    assert s3["s1_keep_parallel_implementations_unchanged"] is True
    assert s3["s2_governance_exclude_implementations_unchanged"] is True
    assert s3["offline_or_simulation_is_not_authority_preserved"] is True
    assert s3["runtime_mutation_executed"] is False
    assert s3["bypass_ids_implemented_sorted"] == [S3_BYPASS_ID]


def test_s3_target_complete_per_s0_completion_evidence() -> None:
    impl = _load(IMPLEMENTATION_JSON)
    adjudication = _load(ADJUDICATION_JSON)
    summary = adjudication["operator_fate_summary_sorted"]
    prov = _load(PROVENANCE_JSON)
    row = impl["bypass_fate_implementations"][S3_BYPASS_ID]
    assert row["operator_fate_adjudication"] == OFFLINE_FATE
    assert row["operator_fate_adjudication"] == summary[S3_BYPASS_ID]
    assert row["fate_implementation_status"] == "COMPLETE"
    assert row["fate_implementation_executed"] is True
    assert row["completion_evidence_satisfied"] is True
    assert row["minimum_implementation_requirements_verified"] is True
    assert row["evidence_provenance_effect"] == OFFLINE_PROVENANCE_EFFECT
    assert row["runtime_mutation_required"] is False
    pin = prov["bypass_provenance_pins"][S3_BYPASS_ID]
    assert pin["research_or_offline_scope_only_affirmed"] is True
    assert pin["not_productive_system_evidence_size_authority"] is True
    assert pin["host_scope_label"] == "offline_economic_evaluation"
    assert pin["offline_or_simulation_is_not_authority_preserved"] is True
    assert pin["system_economic_evidence_authoritative_size_owner_claim_permitted"] is False
    assert pin["reachability_pin"] == "REACHABLE_PRODUCTIVE"
    assert pin["reachability_pin_unchanged_by_this_slice"] is True
    adm = prov["research_or_offline_scope_evidence_admissibility"]
    assert adm["offline_or_simulation_is_not_authority_preserved"] is True
    assert adm["bypass_stable_ids_research_or_offline_scope_only_sorted"] == [S3_BYPASS_ID]


def test_s1_and_s2_implementations_unchanged() -> None:
    impl = _load(IMPLEMENTATION_JSON)
    prov = _load(PROVENANCE_JSON)
    for bid in S1_BYPASS_IDS:
        row = impl["bypass_fate_implementations"][bid]
        assert row["operator_fate_adjudication"] == "KEEP_PARALLEL_NON_CANONICAL"
        assert row["fate_implementation_status"] == "COMPLETE"
        assert prov["bypass_provenance_pins"][bid]["parallel_non_canonical_affirmed"] is True
    for bid in S2_BYPASS_IDS:
        row = impl["bypass_fate_implementations"][bid]
        assert row["operator_fate_adjudication"] == "GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE"
        assert row["fate_implementation_status"] == "COMPLETE"
        pin = prov["bypass_provenance_pins"][bid]
        assert pin["governance_exclude_from_system_evidence_affirmed"] is True


def test_offline_topology_and_inventory_pins() -> None:
    topo = _load(TOPOLOGY_JSON)
    edges = {e["edge_id"]: e for e in topo["productive_direct_edges"]}
    engine = edges["EDGE_ENGINE_OFFLINE_EVAL_SIZING"]
    feedback = edges["EDGE_FEEDBACK_OFFLINE_EVAL_SIZING"]
    assert (
        engine["research_or_offline_scope_fate_implementation_v1"]["bypass_stable_id"]
        == S3_BYPASS_ID
    )
    assert (
        feedback["research_or_offline_scope_fate_implementation_v1"][
            "companion_caller_shares_scope_only_provenance_class"
        ]
        is True
    )
    by_id = {b["bypass_stable_id"]: b for b in topo["direct_sizing_bypass_edges"]}
    offline = by_id[S3_BYPASS_ID]
    assert offline["fate_implementation_v1"]["fate_implementation_status"] == "COMPLETE"
    inventory = _load(INVENTORY_JSON)
    bypass = {b["id"]: b for b in inventory["bypass_paths"]}
    assert bypass[S3_BYPASS_ID]["fate_implementation_executed"] is True
    assert bypass[S3_BYPASS_ID]["evidence_provenance_effect"] == OFFLINE_PROVENANCE_EFFECT


def test_offline_or_simulation_is_not_authority_global_claim_preserved() -> None:
    authority = _load(AUTHORITY_JSON)
    assert authority["markers"]["OFFLINE_OR_SIMULATION_IS_NOT_AUTHORITY"] is True


def test_productive_src_does_not_import_provenance_binding() -> None:
    needle = "risk_sizing_bypass_fate_provenance_binding_v1"
    hits: list[str] = []
    for path in (REPO_ROOT / "src").rglob("*.py"):
        if needle in path.read_text(encoding="utf-8"):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []
