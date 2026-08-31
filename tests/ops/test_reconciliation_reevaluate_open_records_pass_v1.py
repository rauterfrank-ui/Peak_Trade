"""REEVALUATE_OPEN_RECORDS_PASS_V1 contracts. Re-evaluate OPEN records only."""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.ops.system_atlas_v1.adjudicate_pass_v1_records import (
    ADJUDICATE_BOUND_SHA,
    INSUFFICIENT,
    LANDSCAPE_V1_IDS,
    RETAIN,
    RETAIN_IDS,
)
from scripts.ops.system_atlas_v1.evidence_resolution_pass_v1_records import (
    CONTRADICTION,
    EVIDENCE_RESOLUTION_PASS_ID,
    OPEN_IDS,
)
from scripts.ops.system_atlas_v1.reevaluate_open_records_pass_v1_persist import (
    REEVALUATE_PASS_ID,
)
from scripts.ops.system_atlas_v1.reevaluate_open_records_pass_v1_records import (
    COVERED,
    REEVALUATE_BOUND_SHA,
    REJECT,
    RETAIN as RETAIN_CLASS,
    reevaluate_open_records,
)
from scripts.ops.system_atlas_v1.reconciliation_v1 import (
    load_reconciliation_v1,
    validate_reconciliation_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RECON = REPO_ROOT / "docs" / "system_atlas" / "reconciliation"
PASS_ROOT = RECON / "reevaluate"
EVIDENCE_RESOLUTION_ROOT = RECON / "evidence_resolution"
UNDERSTAND_ROOT = RECON / "understand"
EVALUATE_ROOT = RECON / "evaluate"
ADJUDICATE_ROOT = RECON / "adjudicate"
FUSION = frozenset({"MERGED_INTO", "RENAMED_TO", "SPLIT_INTO", "SAME_AS"})


def _status() -> dict:
    return yaml.safe_load((PASS_ROOT / "pass_v1_status.yaml").read_text(encoding="utf-8"))


def _payload() -> dict:
    return load_reconciliation_v1(repo_root=REPO_ROOT)


def test_reevaluate_pass_v1_status_invariants() -> None:
    status = _status()
    assert status["census_closed"] is True
    assert int(status["ledger_record_count"]) == 53
    assert int(status["input_record_count"]) == 35
    assert int(status["reevaluation_attempted_record_count"]) == 35
    new_final = int(status["new_final_disposition_count"])
    remaining = int(status["remaining_insufficient_evidence_open_count"])
    assert new_final + remaining == 35
    assert new_final == 0
    assert remaining == 35
    assert int(status["new_retain_as_is_count"]) == 0
    assert int(status["new_adapt_and_reintegrate_count"]) == 0
    assert int(status["new_capability_already_covered_count"]) == 0
    assert int(status["new_historically_valid_but_incompatible_count"]) == 0
    assert int(status["new_reject_for_current_system_count"]) == 0
    assert int(status["final_disposition_changes_performed"]) == 0
    assert int(status["identity_merges_performed"]) == 0
    assert status["reintegration_performed"] is False
    assert status["runtime_mutation_performed"] is False
    assert status["bound_against_sha"] == REEVALUATE_BOUND_SHA
    assert status["reevaluate_pass_id"] == REEVALUATE_PASS_ID
    assert status["input_pass_id"] == EVIDENCE_RESOLUTION_PASS_ID
    assert status["adjudicate_bound_against_sha_frozen"] == ADJUDICATE_BOUND_SHA
    assert status["understand_snapshot_frozen"] is True
    assert status["evaluate_snapshot_frozen"] is True
    assert status["adjudication_snapshot_frozen"] is True
    assert status["evidence_resolution_snapshot_frozen"] is True
    assert int(status["total_ledger_record_count"]) == 53
    assert int(status["total_retain_as_is_count"]) == 18
    assert int(status["total_insufficient_evidence_count"]) == 35


def test_open_set_is_exactly_the_35_and_retain_18_untouched() -> None:
    payload = _payload()
    assert validate_reconciliation_v1(payload) == []
    ledger = payload["records"]["ledger.yaml"]
    assert len(ledger["records"]) == 53
    open_ids = []
    retain = 0
    for rec in ledger["records"]:
        adj = rec["adjudication"]
        rid = rec["identity"]["reconciliation_id"]
        if adj["disposition"] == INSUFFICIENT:
            assert adj["lifecycle_state"] == "OPEN"
            open_ids.append(rid)
            block = rec.get("reevaluate") or {}
            assert block.get("disposition_burden_met") is False
            assert block.get("disposition") == INSUFFICIENT
            assert block.get("lifecycle_state") == "OPEN"
            assert block.get("final_disposition_change_performed") is False
            assert block.get("identity_merge_performed") is False
            assert block.get("reintegration_performed") is False
            assert rec.get("evidence_resolution") is not None
            assert rec["evidence_resolution"]["final_disposition_change_performed"] is False
        else:
            retain += 1
            assert adj["disposition"] == RETAIN
            assert rec.get("reevaluate") is None
            assert rec.get("evidence_resolution") is None
            assert rid in RETAIN_IDS
    assert tuple(open_ids) == OPEN_IDS
    assert retain == 18
    assert ledger["reevaluate_pass_id"] == REEVALUATE_PASS_ID
    assert ledger["evidence_resolution_pass_id"] == EVIDENCE_RESOLUTION_PASS_ID
    assert ledger["adjudicate_bound_against_sha"] == ADJUDICATE_BOUND_SHA


def test_persisted_records_match_generated_and_refs_exist() -> None:
    generated = {row["record_id"]: row for row in reevaluate_open_records()}
    index = yaml.safe_load((PASS_ROOT / "index.yaml").read_text(encoding="utf-8"))
    assert int(index["row_count"]) == 35
    index_ids = [row["record_id"] for row in index["rows"]]
    assert tuple(index_ids) == OPEN_IDS
    for rid in OPEN_IDS:
        path = PASS_ROOT / "records" / f"{rid}.yaml"
        persisted = yaml.safe_load(path.read_text(encoding="utf-8"))
        payload = generated[rid]
        assert persisted["record_id"] == rid
        assert persisted["disposition_burden_met"] is False
        assert persisted["disposition"] == INSUFFICIENT
        assert persisted["lifecycle_state"] == "OPEN"
        assert persisted["final_disposition_change_performed"] is False
        assert persisted["identity_merge_performed"] is False
        assert persisted["reintegration_performed"] is False
        assert persisted["evaluation_result"] == payload["evaluation_result"]
        assert persisted["alternatives_rejected"] == payload["alternatives_rejected"]
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


def test_frozen_predecessor_snapshots_remain_phase_frozen() -> None:
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
    er_status = yaml.safe_load((EVIDENCE_RESOLUTION_ROOT / "pass_v1_status.yaml").read_text())
    assert er_status["evidence_resolution_pass_id"] == EVIDENCE_RESOLUTION_PASS_ID
    assert int(er_status["final_disposition_changes_performed"]) == 0
    assert int(er_status["input_open_record_count"]) == 35
    assert int(er_status["evidence_gap_resolved_count"]) == 0
    assert int(er_status["evidence_gap_partially_resolved_count"]) == 34
    assert int(er_status["contradiction_discovered_count"]) == 1


def test_no_identity_fusion() -> None:
    payload = _payload()
    for rec in payload["records"]["ledger.yaml"]["records"]:
        rid = rec["identity"]["reconciliation_id"]
        for rel in (rec.get("relations") or {}).get("items") or []:
            assert str(rel.get("relation_type") or "") not in FUSION, rid
        block = rec.get("reevaluate") or {}
        assert block.get("identity_merge_performed") is not True, rid


def test_landscape_v1_family_not_fused_and_not_family_dispositioned() -> None:
    for rid in LANDSCAPE_V1_IDS:
        rec = yaml.safe_load((PASS_ROOT / "records" / f"{rid}.yaml").read_text())
        assert rec["disposition"] == INSUFFICIENT
        assert rec["disposition_burden_met"] is False
        rejected = " ".join(rec["alternatives_rejected"]).lower()
        assert "get /market" in rejected or "owner_registry" in rejected
        assert "kein rebuild" in rejected or "no-rebuild" in rejected or "rebuild" in rejected
        assert rec["identity_merge_performed"] is False
        assert rec["identity_status"] != "SAME_AS"


def test_rcn_000015_not_covered_by_cap_2_3_and_revert_is_not_reject() -> None:
    rec = yaml.safe_load((PASS_ROOT / "records" / "RCN-000015.yaml").read_text())
    assert rec["disposition"] == INSUFFICIENT
    assert rec["disposition_burden_met"] is False
    blob = " ".join(
        [
            rec["evaluation_result"],
            rec["historical_relations"],
            *rec["alternatives_rejected"],
        ]
    ).lower()
    assert "does not rewrite" in blob or "not rewrite" in blob
    assert "predates" in blob or "refuted" in blob
    assert COVERED in rec["alternatives_rejected"][1] or "cap 2.3" in blob
    assert REJECT in " ".join(rec["alternatives_rejected"])
    assert "revert" in blob
    assert rec["successor_status"] == "REFUTED_AS_SUCCESSOR_OF_SELECTOR"


def test_rcn_000019_kill_switch_package_is_not_gate_family_coverage() -> None:
    rec = yaml.safe_load((PASS_ROOT / "records" / "RCN-000019.yaml").read_text())
    assert rec["disposition"] == INSUFFICIENT
    assert rec["disposition_burden_met"] is False
    blob = " ".join(
        [rec["evaluation_result"], rec["historical_function"], *rec["alternatives_rejected"]]
    )
    assert "KillSwitchLayer" in blob or "kill_switch.py" in blob.lower()
    assert "skeleton" in blob.lower() or "LiquidityGate" in blob
    assert COVERED in " ".join(rec["alternatives_rejected"])


def test_rcn_000052_contradiction_blocks_retain_and_presence_unchanged() -> None:
    rec = yaml.safe_load((PASS_ROOT / "records" / "RCN-000052.yaml").read_text())
    payload = _payload()
    live = next(
        row
        for row in payload["records"]["ledger.yaml"]["records"]
        if row["identity"]["reconciliation_id"] == "RCN-000052"
    )
    assert live["discovery"]["current_presence"] == "CURRENTLY_ABSENT"
    assert rec["disposition"] == INSUFFICIENT
    assert rec["disposition_burden_met"] is False
    assert rec["disposition"] != RETAIN_CLASS
    assert any(c.get("claim_class") == "CONTRADICTION" for c in rec["claims"])
    assert all(
        c.get("used_as_fact") is False for c in rec["claims"] if c["claim_class"] == "CONTRADICTION"
    )
    er = yaml.safe_load((EVIDENCE_RESOLUTION_ROOT / "records" / "RCN-000052.yaml").read_text())
    assert er["evidence_resolution_status"] == CONTRADICTION
    rejected = " ".join(rec["alternatives_rejected"])
    assert RETAIN_CLASS in rejected


def test_taxonomy_aliases_are_not_introduced() -> None:
    status = (PASS_ROOT / "pass_v1_status.yaml").read_text(encoding="utf-8")
    ledger = (RECON / "ledger.yaml").read_text(encoding="utf-8")
    blob = status + ledger
    assert "ALREADY_COVERED" not in blob.replace("CAPABILITY_ALREADY_COVERED", "")
    assert "OPEN_INSUFFICIENT_EVIDENCE" not in blob
