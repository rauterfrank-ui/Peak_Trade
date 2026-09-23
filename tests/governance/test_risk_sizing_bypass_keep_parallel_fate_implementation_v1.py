"""WP_B05_KEEP_PARALLEL_FATE_IMPLEMENTATION_V1 — S1 governance implementation (no runtime)."""

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
EFS_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_companion_intent_freeze_and_efs_quarantine_v1.json"
)

S1_BYPASS_IDS = (
    "BYPASS_CORE_POSITION_SIZER",
    "BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS",
)
NON_S1_BYPASS_IDS_NOT_STARTED = ("BYPASS_OFFLINE_EVAL_SIZING_CONTRACT",)
KEEP_PARALLEL_FATE = "KEEP_PARALLEL_NON_CANONICAL"
PROVENANCE_EFFECT = (
    "AFFIRM_PARALLEL_NON_CANONICAL_PROVENANCE_LABEL; NO_AUTHORITATIVE_SYSTEM_EVIDENCE_OWNER_CLAIM"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_s1_slice_boundaries_and_global_incomplete() -> None:
    impl = _load(IMPLEMENTATION_JSON)
    markers = impl["markers"]
    assert markers["FATE_IMPLEMENTATION_EXECUTED"] is False
    assert markers["PER_BYPASS_FATE_IMPLEMENTATION_EXECUTED_COUNT"] == 4
    assert markers["S1_KEEP_PARALLEL_FATE_IMPLEMENTATION_EXECUTED"] is True
    assert markers["RUNTIME_MUTATION_EXECUTED"] is False
    assert markers["PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED"] is False
    s1 = impl["s1_keep_parallel_fate_implementation_v1"]
    assert s1["workpackage_id"] == "WP_B05_KEEP_PARALLEL_FATE_IMPLEMENTATION_V1"
    assert s1["global_fate_implementation_executed_remains_false"] is True


def test_s1_targets_complete_per_s0_completion_evidence() -> None:
    impl = _load(IMPLEMENTATION_JSON)
    adjudication = _load(ADJUDICATION_JSON)
    summary = adjudication["operator_fate_summary_sorted"]
    prov = _load(PROVENANCE_JSON)
    for bid in S1_BYPASS_IDS:
        row = impl["bypass_fate_implementations"][bid]
        assert row["operator_fate_adjudication"] == KEEP_PARALLEL_FATE
        assert row["operator_fate_adjudication"] == summary[bid]
        assert row["fate_implementation_status"] == "COMPLETE"
        assert row["fate_implementation_executed"] is True
        assert row["completion_evidence_satisfied"] is True
        assert row["minimum_implementation_requirements_verified"] is True
        assert row["evidence_provenance_effect"] == PROVENANCE_EFFECT
        pin = prov["bypass_provenance_pins"][bid]
        assert pin["parallel_non_canonical_affirmed"] is True
        assert pin["system_economic_evidence_authoritative_size_owner_claim_permitted"] is False
        assert pin["reachability_pin"] == "REACHABLE_PRODUCTIVE"


def test_offline_eval_bypass_remains_not_started() -> None:
    impl = _load(IMPLEMENTATION_JSON)
    for bid in NON_S1_BYPASS_IDS_NOT_STARTED:
        row = impl["bypass_fate_implementations"][bid]
        assert row["fate_implementation_status"] == "NOT_STARTED"
        assert row["fate_implementation_executed"] is False
        assert row["completion_evidence_satisfied"] is False


def test_inventory_and_topology_pins_align() -> None:
    inventory = _load(INVENTORY_JSON)
    bypass = {b["id"]: b for b in inventory["bypass_paths"]}
    for bid in S1_BYPASS_IDS:
        assert bypass[bid]["fate_implementation_executed"] is True
        assert bypass[bid]["fate_implementation_status"] == "COMPLETE"
    topo = _load(TOPOLOGY_JSON)
    by_id = {b["bypass_stable_id"]: b for b in topo["direct_sizing_bypass_edges"]}
    for bid in S1_BYPASS_IDS:
        fate_impl = by_id[bid]["fate_implementation_v1"]
        assert fate_impl["fate_implementation_status"] == "COMPLETE"
        assert fate_impl["canonical_for_mv2_intent_bound_scope"] is False


def test_efs_semantic_conflict_and_quarantine_unchanged() -> None:
    audit = _load(AUDIT_JSON)
    path = next(p for p in audit["audited_paths"] if p["path_id"] == "PATH_EXECUTE_FROM_SIGNALS")
    assert path["classification"] == "SEMANTIC_CONFLICT"
    kp = path["keep_parallel_fate_implementation_v1"]
    assert kp["classification_unchanged"] == "SEMANTIC_CONFLICT"
    assert kp["efs_foreign_status_unchanged"] == "DEPRECATED_QUARANTINED"
    efs = _load(EFS_JSON)
    assert efs["markers"]["EFS_QUARANTINED"] is True
    assert efs["efs_quarantine"]["status"] == "DEPRECATED_QUARANTINED"


def test_productive_src_does_not_import_provenance_binding() -> None:
    needle = "risk_sizing_bypass_fate_provenance_binding_v1"
    hits: list[str] = []
    for path in (REPO_ROOT / "src").rglob("*.py"):
        if needle in path.read_text(encoding="utf-8"):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []
