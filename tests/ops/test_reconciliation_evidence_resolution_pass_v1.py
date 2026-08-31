"""OPEN_EVIDENCE_RESOLUTION_PASS_V1 contracts. Evidence resolution only."""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.ops.system_atlas_v1.adjudicate_pass_v1_records import (
    ADJUDICATE_BOUND_SHA,
    INSUFFICIENT,
    LANDSCAPE_V1_IDS,
    RETAIN_IDS,
)
from scripts.ops.system_atlas_v1.evidence_resolution_pass_v1_persist import (
    EVIDENCE_RESOLUTION_PASS_ID,
)
from scripts.ops.system_atlas_v1.evidence_resolution_pass_v1_records import (
    CENSUS_BOUND_SHA,
    CONTRADICTION,
    EVIDENCE_RESOLUTION_BOUND_SHA,
    OPEN_IDS,
    PARTIAL,
    evidence_resolution_records,
)
from scripts.ops.system_atlas_v1.reconciliation_v1 import (
    load_reconciliation_v1,
    validate_reconciliation_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RECON = REPO_ROOT / "docs" / "system_atlas" / "reconciliation"
PASS_ROOT = RECON / "evidence_resolution"
UNDERSTAND_ROOT = RECON / "understand"
EVALUATE_ROOT = RECON / "evaluate"
ADJUDICATE_ROOT = RECON / "adjudicate"
FUSION = frozenset({"MERGED_INTO", "RENAMED_TO", "SPLIT_INTO", "SAME_AS"})


def _status() -> dict:
    return yaml.safe_load((PASS_ROOT / "pass_v1_status.yaml").read_text(encoding="utf-8"))


def _payload() -> dict:
    return load_reconciliation_v1(repo_root=REPO_ROOT)


def test_evidence_resolution_pass_v1_status_invariants() -> None:
    status = _status()
    assert status["census_closed"] is True
    assert int(status["ledger_record_count"]) == 53
    assert int(status["input_open_record_count"]) == 35
    assert int(status["evidence_resolution_attempted_count"]) == 35
    resolved = int(status["evidence_gap_resolved_count"])
    partial = int(status["evidence_gap_partially_resolved_count"])
    unresolved = int(status["evidence_gap_unresolved_count"])
    contradiction = int(status["contradiction_discovered_count"])
    assert resolved + partial + unresolved + contradiction == 35
    assert int(status["final_disposition_changes_performed"]) == 0
    assert int(status["identity_merges_performed"]) == 0
    assert status["reintegration_performed"] is False
    assert status["runtime_mutation_performed"] is False
    assert status["final_disposition_change_performed"] is False
    assert status["bound_against_sha"] == EVIDENCE_RESOLUTION_BOUND_SHA
    assert status["evidence_resolution_pass_id"] == EVIDENCE_RESOLUTION_PASS_ID
    assert status["adjudicate_bound_against_sha_frozen"] == ADJUDICATE_BOUND_SHA
    assert status["understand_snapshot_frozen"] is True
    assert status["evaluate_snapshot_frozen"] is True
    assert status["adjudication_snapshot_frozen"] is True


def test_open_set_is_exactly_the_35_insufficient_open_records() -> None:
    index = yaml.safe_load((PASS_ROOT / "index.yaml").read_text(encoding="utf-8"))
    assert int(index["row_count"]) == 35
    assert tuple(row["record_id"] for row in index["rows"]) == OPEN_IDS
    payload = _payload()
    assert validate_reconciliation_v1(payload) == []
    ledger = payload["records"]["ledger.yaml"]
    retain = 0
    er_ids = []
    for rec in ledger["records"]:
        rid = rec["identity"]["reconciliation_id"]
        if rid in OPEN_IDS:
            er_ids.append(rid)
            block = rec.get("evidence_resolution") or {}
            assert block.get("evidence_resolution_status")
            assert block.get("final_disposition_change_performed") is False
            assert block.get("identity_merge_performed") is False
            for gap_key in (
                "identity_gap",
                "function_gap",
                "relation_gap",
                "successor_or_replacement_gap",
                "current_system_fit_gap",
            ):
                gap = block[gap_key]
                assert str(gap.get("status") or "").strip()
                assert str(gap.get("statement") or "").strip()
            if rec["adjudication"]["disposition"] == INSUFFICIENT:
                assert rec["adjudication"]["lifecycle_state"] == "OPEN"
        else:
            retain += 1
            assert rec.get("evidence_resolution") is None
            assert rid in RETAIN_IDS
            assert rec["adjudication"]["disposition"] != INSUFFICIENT
    assert tuple(er_ids) == OPEN_IDS
    assert retain == 18
    assert ledger["evidence_resolution_pass_id"] == EVIDENCE_RESOLUTION_PASS_ID
    assert ledger["adjudicate_bound_against_sha"] == ADJUDICATE_BOUND_SHA


def test_persisted_records_match_generated_and_refs_exist() -> None:
    generated = {row["record_id"]: row for row in evidence_resolution_records()}
    index = yaml.safe_load((PASS_ROOT / "index.yaml").read_text(encoding="utf-8"))
    assert int(index["row_count"]) == 35
    index_ids = [row["record_id"] for row in index["rows"]]
    assert tuple(index_ids) == OPEN_IDS
    for rid in OPEN_IDS:
        path = PASS_ROOT / "records" / f"{rid}.yaml"
        persisted = yaml.safe_load(path.read_text(encoding="utf-8"))
        payload = generated[rid]
        assert persisted["record_id"] == rid
        assert persisted["evidence_resolution_status"] == payload["evidence_resolution_status"]
        assert persisted["final_disposition_change_performed"] is False
        assert persisted["disposition_unchanged"] is True
        assert persisted["identity_merge_performed"] is False
        assert persisted["reintegration_performed"] is False
        for claim in persisted.get("claims") or []:
            if str(claim.get("claim_class") or "") in {
                "HYPOTHESIS",
                "CONTRADICTION",
                "OPEN_QUESTION",
                "INTERPRETATION",
            }:
                assert claim.get("used_as_fact") is False
        for ref in persisted.get("evidence_refs") or []:
            target = REPO_ROOT / str(ref)
            assert target.exists(), f"{rid}:{ref}"


def test_understand_evaluate_adjudicate_snapshots_remain_phase_frozen() -> None:
    for path in (UNDERSTAND_ROOT / "records").glob("RCN-*.yaml"):
        rec = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert rec["current_system_compared"] is False, rec["record_id"]
        assert rec["evaluate_performed"] is False, rec["record_id"]
        assert rec["disposition_decided"] is False, rec["record_id"]
        assert rec["identity_merge_performed"] is False, rec["record_id"]
    for path in (EVALUATE_ROOT / "records").glob("RCN-*.yaml"):
        rec = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert rec["disposition_performed"] is False, rec["record_id"]
        assert rec["reintegration_performed"] is False, rec["record_id"]
        assert rec["identity_fusion_forbidden"] is True, rec["record_id"]
    adj_status = yaml.safe_load((ADJUDICATE_ROOT / "pass_v1_status.yaml").read_text())
    assert adj_status["adjudicate_pass_id"] == "INTEGRATE_OR_DISPOSITION_PASS_V1"
    assert int(adj_status["open_insufficient_evidence_count"]) == 35
    assert int(adj_status["retain_as_is_count"]) == 18
    assert adj_status["reintegration_performed"] is False


def test_no_identity_fusion() -> None:
    payload = _payload()
    for rec in payload["records"]["ledger.yaml"]["records"]:
        rid = rec["identity"]["reconciliation_id"]
        for rel in (rec.get("relations") or {}).get("items") or []:
            assert str(rel.get("relation_type") or "") not in FUSION, rid
        block = rec.get("evidence_resolution") or {}
        for rel in block.get("relations_proven") or []:
            assert str(rel.get("relation_type") or "") not in FUSION, rid


def test_landscape_v1_family_not_fused_and_not_replaced_by_get_market() -> None:
    for rid in LANDSCAPE_V1_IDS:
        rec = yaml.safe_load((PASS_ROOT / "records" / f"{rid}.yaml").read_text())
        assert rec["evidence_resolution_status"] == PARTIAL
        ident = rec["identity_gap"]["statement"].lower()
        succ = rec["successor_or_replacement_gap"]["statement"].lower()
        assert "same_as" in ident or "distinct" in ident
        assert "get /market" in succ or "later existence is not succession" in succ
        assert rec["identity_merge_performed"] is False


def test_rcn_000015_not_successor_of_cap_2_3() -> None:
    rec = yaml.safe_load((PASS_ROOT / "records" / "RCN-000015.yaml").read_text())
    assert rec["evidence_resolution_status"] == PARTIAL
    blob = " ".join(
        [
            rec["identity_gap"]["statement"],
            rec["successor_or_replacement_gap"]["statement"],
            rec["relation_gap"]["statement"],
        ]
    ).lower()
    assert "does not rewrite cap 2.3" in blob or "not rewrite" in blob
    assert "predates" in blob or "cannot be a successor" in blob
    assert rec["final_disposition_change_performed"] is False
    revert_open = any(
        "6166" in q or "reverted" in q.lower() for q in rec["remaining_open_questions"]
    )
    assert revert_open


def test_rcn_000019_kill_switch_py_is_not_package_identity() -> None:
    rec = yaml.safe_load((PASS_ROOT / "records" / "RCN-000019.yaml").read_text())
    assert rec["evidence_resolution_status"] == PARTIAL
    ident = rec["identity_gap"]["statement"]
    assert "coexisted" in ident.lower() or "KillSwitchLayer" in ident
    assert "KillSwitchLayer" in ident or "different" in ident.lower()
    succ = rec["successor_or_replacement_gap"]["statement"]
    assert "skeleton" in succ.lower() or "LiquidityGate" in succ


def test_rcn_000052_preserves_census_absence_and_refutes_post_census_restore() -> None:
    rec = yaml.safe_load((PASS_ROOT / "records" / "RCN-000052.yaml").read_text())
    payload = _payload()
    live = next(
        row
        for row in payload["records"]["ledger.yaml"]["records"]
        if row["identity"]["reconciliation_id"] == "RCN-000052"
    )
    assert live["discovery"]["current_presence"] == "CURRENTLY_ABSENT"
    assert rec["evidence_resolution_status"] == CONTRADICTION
    assert rec["census_bound_sha"] == CENSUS_BOUND_SHA
    blob = rec["identity_gap"]["statement"].lower()
    assert "not restored after the census" in blob or "already present" in blob
    assert any(c.get("claim_class") == "CONTRADICTION" for c in rec["claims"])
    assert all(
        c.get("used_as_fact") is False for c in rec["claims"] if c["claim_class"] == "CONTRADICTION"
    )
    tree = (
        RECON / "evidence" / "evidence_resolution_v1" / "commands" / "rcn_000052_census_tree.txt"
    ).read_text(encoding="utf-8")
    assert "OBSERVABILITY_HUB_V0.md" in tree
    assert tree.count("docs/webui/observability/") == 11


def test_command_artifacts_and_quotes_exist() -> None:
    quotes = yaml.safe_load(
        (RECON / "evidence" / "evidence_resolution_v1" / "raw_quotes.yaml").read_text()
    )
    assert quotes["kind"] == "FORENSIC_RAW_QUOTES"
    assert quotes["interpretation_forbidden_in_this_file"] is True
    matrix = (
        RECON / "evidence" / "evidence_resolution_v1" / "commands" / "presence_matrix.txt"
    ).read_text(encoding="utf-8")
    assert "RCN-000052" in matrix
    assert "RCN-000015" in matrix
    schema = yaml.safe_load((RECON / "schema.yaml").read_text(encoding="utf-8"))
    assert schema["evidence_resolution_is_not_disposition"] is True
    assert "identity_gap" in schema["evidence_resolution"]
    assert "CONTRADICTION_DISCOVERED" in schema["allowed_evidence_resolution_statuses"]
