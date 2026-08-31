"""INTEGRATE_OR_DISPOSITION pass v1 contracts. Adjudication only."""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.ops.system_atlas_v1.adjudicate_pass_v1_persist import ADJUDICATE_PASS_ID
from scripts.ops.system_atlas_v1.adjudicate_pass_v1_records import (
    ADJUDICATE_BOUND_SHA,
    ALLOWED_DISPOSITIONS,
    INSUFFICIENT,
    LANDSCAPE_V1_IDS,
    RETAIN,
    RETAIN_IDS,
    adjudicate_records,
)
from scripts.ops.system_atlas_v1.reconciliation_v1 import (
    load_reconciliation_v1,
    validate_reconciliation_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ADJUDICATE_ROOT = REPO_ROOT / "docs" / "system_atlas" / "reconciliation" / "adjudicate"
UNDERSTAND_ROOT = REPO_ROOT / "docs" / "system_atlas" / "reconciliation" / "understand"
EVALUATE_ROOT = REPO_ROOT / "docs" / "system_atlas" / "reconciliation" / "evaluate"
FUSION = frozenset({"MERGED_INTO", "RENAMED_TO", "SPLIT_INTO", "SAME_AS"})
POST_IMPLEMENTATION = frozenset({"REINTEGRATED", "COVERED", "INCOMPATIBLE", "REJECTED"})


def _status() -> dict:
    return yaml.safe_load((ADJUDICATE_ROOT / "pass_v1_status.yaml").read_text(encoding="utf-8"))


def _payload() -> dict:
    return load_reconciliation_v1(repo_root=REPO_ROOT)


def test_adjudicate_pass_v1_status_invariants() -> None:
    status = _status()
    assert status["census_closed"] is True
    assert status["census_status"] == "CENSUS_CLOSED"
    assert int(status["surfaces_exhaustion_proven"]) == 17
    assert int(status["ledger_record_count"]) == 53
    assert int(status["current_system_compared_record_count"]) == 53
    assert int(status["adjudication_attempted_record_count"]) == 53
    assert int(status["adjudicated_record_count"]) == 53
    retain = int(status["retain_as_is_count"])
    insufficient = int(status["insufficient_evidence_count"])
    adapt = int(status["adapt_and_reintegrate_count"])
    covered = int(status["capability_already_covered_count"])
    incompatible = int(status["historically_valid_but_incompatible_count"])
    rejected = int(status["reject_for_current_system_count"])
    assert retain + insufficient + adapt + covered + incompatible + rejected == 53
    assert int(status["disposition_decided_record_count"]) == retain
    assert int(status["open_insufficient_evidence_count"]) == insufficient
    assert adapt == 0
    assert covered == 0
    assert incompatible == 0
    assert rejected == 0
    assert int(status["identity_merges_performed"]) == 0
    assert status["no_reintegration_performed"] is True
    assert status["no_identity_fusion_performed"] is True
    assert status["no_runtime_mutation_performed"] is True
    assert status["reintegration_performed"] is False
    assert status["bound_against_sha"] == ADJUDICATE_BOUND_SHA
    assert status["adjudicate_pass_id"] == ADJUDICATE_PASS_ID
    assert status["identity_fusion_forbidden"] is True


def test_all_records_attempted_with_schema_disposition() -> None:
    index = yaml.safe_load((ADJUDICATE_ROOT / "index.yaml").read_text(encoding="utf-8"))
    assert int(index["row_count"]) == 53
    ids = {row["record_id"] for row in index["rows"]}
    assert ids == {f"RCN-{n:06d}" for n in range(1, 54)}
    payload = _payload()
    assert validate_reconciliation_v1(payload) == []
    ledger = payload["records"]["ledger.yaml"]
    assert ledger["adjudicate_bound_against_sha"] == ADJUDICATE_BOUND_SHA
    generated = {row["record_id"]: row for row in adjudicate_records()}
    retain = 0
    insufficient = 0
    for rec in ledger["records"]:
        rid = rec["identity"]["reconciliation_id"]
        adj = rec["adjudication"]
        integration = rec["integration"]
        audit = rec["audit"]
        row = generated[rid]
        assert adj["adjudication_attempted"] is True
        assert str(adj.get("disposition") or "") in ALLOWED_DISPOSITIONS
        assert str(adj.get("positive_reason") or "").strip()
        assert list(adj.get("evidence_refs") or [])
        assert list(adj.get("alternatives_rejected") or [])
        assert list(adj.get("claims") or [])
        assert adj["disposition"] == row["disposition"]
        assert adj["lifecycle_state"] == row["lifecycle_state"]
        assert integration.get("reintegration_required") is False
        assert adj.get("reintegration_candidate") is False
        assert str(adj.get("lifecycle_state") or "") not in POST_IMPLEMENTATION
        assert audit.get("last_adjudicated_against_sha") == ADJUDICATE_BOUND_SHA
        if adj["disposition"] == RETAIN:
            retain += 1
            assert adj["lifecycle_state"] == "DISPOSITION_DECIDED"
            assert adj["further_evidence_required"] is False
        if adj["disposition"] == INSUFFICIENT:
            insufficient += 1
            assert adj["lifecycle_state"] == "OPEN"
            assert adj["further_evidence_required"] is True
        path = ADJUDICATE_ROOT / "records" / f"{rid}.yaml"
        persisted = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert persisted["record_id"] == rid
        assert persisted["adjudication_attempted"] is True
        assert persisted["reintegration_performed"] is False
        assert persisted["identity_fusion_forbidden"] is True
        assert persisted["disposition"] == adj["disposition"]
        for claim in persisted.get("claims") or []:
            if str(claim.get("claim_class") or "") in {"HYPOTHESIS", "CONTRADICTION"}:
                assert claim.get("used_as_fact") is False
            for ref in claim.get("evidence") or []:
                target = REPO_ROOT / str(ref)
                assert target.exists(), f"{rid}:{ref}"
        for ref in persisted.get("evidence_refs") or []:
            target = REPO_ROOT / str(ref)
            assert target.exists(), f"{rid}:{ref}"
    assert retain + insufficient == 53
    assert retain == len(RETAIN_IDS)
    assert insufficient == 53 - len(RETAIN_IDS)


def test_understand_and_evaluate_snapshots_remain_phase_frozen() -> None:
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
    evaluate_status = yaml.safe_load((EVALUATE_ROOT / "pass_v1_status.yaml").read_text())
    assert int(evaluate_status["adjudicated_record_count"]) == 0
    assert evaluate_status["disposition_performed"] is False
    understand_v2 = yaml.safe_load((UNDERSTAND_ROOT / "pass_v2_status.yaml").read_text())
    assert int(understand_v2["adjudicated_record_count"]) == 0
    assert understand_v2["no_disposition_decided"] is True


def test_no_identity_fusion_or_reintegration() -> None:
    payload = _payload()
    for rec in payload["records"]["ledger.yaml"]["records"]:
        rid = rec["identity"]["reconciliation_id"]
        for rel in (rec.get("relations") or {}).get("items") or []:
            assert str(rel.get("relation_type") or "") not in FUSION, rid
            if rel.get("relation_type") == "POSSIBLE_SAME_AS":
                assert rel.get("epistemic_status") == "HYPOTHESIS", rid
    relations = payload["records"]["relations.yaml"]
    assert int(relations.get("identity_merges_performed") or 0) == 0


def test_rcn_000015_not_fused_with_cap_2_3() -> None:
    rec = yaml.safe_load((ADJUDICATE_ROOT / "records" / "RCN-000015.yaml").read_text())
    assert rec["disposition"] == INSUFFICIENT
    assert rec["lifecycle_state"] == "OPEN"
    assert rec["identity_status"] == "IDENTITY_UNPROVEN_VERSUS_CAP_2_3"
    blob = " ".join(
        [rec["positive_reason"], *rec["alternatives_rejected"], *rec["unresolved_questions"]]
    ).lower()
    assert "replacement/identity not proven" in blob
    assert "successor of single_selected_future_policy_v1" in blob
    hypotheses = [c for c in rec["claims"] if c["claim_class"] == "HYPOTHESIS"]
    assert hypotheses
    assert all(c.get("used_as_fact") is False for c in hypotheses)


def test_rcn_000019_kill_switch_package_is_not_family_identity() -> None:
    rec = yaml.safe_load((ADJUDICATE_ROOT / "records" / "RCN-000019.yaml").read_text())
    assert rec["disposition"] == INSUFFICIENT
    assert rec["identity_status"] == "PARTIAL_FAMILY_IDENTITY_UNPROVEN"
    assert rec["census_current_presence"] == "CURRENTLY_PARTIAL"
    assert rec["evaluate_capability_overlap"] == "SAME_PATH_FAMILY_PARTIAL"
    blob = rec["positive_reason"]
    assert "does not prove identity" in blob
    assert "LiquidityGate" in blob or "liquidity_gate" in blob.lower()


def test_rcn_000052_preserves_census_tree_contradiction() -> None:
    rec = yaml.safe_load((ADJUDICATE_ROOT / "records" / "RCN-000052.yaml").read_text())
    payload = _payload()
    live = next(
        row
        for row in payload["records"]["ledger.yaml"]["records"]
        if row["identity"]["reconciliation_id"] == "RCN-000052"
    )
    assert live["discovery"]["current_presence"] == "CURRENTLY_ABSENT"
    assert rec["census_current_presence"] == "CURRENTLY_ABSENT"
    assert rec["disposition"] == INSUFFICIENT
    assert rec["identity_status"] == "CENSUS_TREE_CONTRADICTION"
    assert rec["evaluate_capability_overlap"] == "CENSUS_ABSENT_BUT_CURRENT_TREE_PRESENT"
    hits = [c for c in rec["claims"] if c["claim_class"] == "CONTRADICTION"]
    assert hits
    assert all(c.get("used_as_fact") is False for c in hits)
    assert (REPO_ROOT / "docs/webui/observability/OBSERVABILITY_HUB_V0.md").is_file()
    assert any("CURRENTLY_ABSENT" in text for text in rec["contradictions"])


def test_landscape_v1_family_not_replaced_by_v2() -> None:
    for rid in LANDSCAPE_V1_IDS:
        rec = yaml.safe_load((ADJUDICATE_ROOT / "records" / f"{rid}.yaml").read_text())
        assert rec["disposition"] == INSUFFICIENT, rid
        assert rec["identity_status"] == "IDENTITY_UNPROVEN_VERSUS_LANDSCAPE_V2", rid
        assert rec["evaluate_capability_overlap"] == (
            "LATER_CONSUMER_SURFACE_OVERLAP_IDENTITY_UNPROVEN"
        ), rid
        assert "Shared consumer surface is not identity" in rec["positive_reason"]
        assert any("CAPABILITY_ALREADY_COVERED" in item for item in rec["alternatives_rejected"])


def test_same_artifact_present_is_not_automatic_retain_but_retain_is_proven() -> None:
    for rid in RETAIN_IDS:
        rec = yaml.safe_load((ADJUDICATE_ROOT / "records" / f"{rid}.yaml").read_text())
        assert rec["disposition"] == RETAIN
        assert rec["evaluate_capability_overlap"] == "SAME_ARTIFACT_STILL_PRESENT"
        assert rec["identity_status"] == "CURRENT_IDENTITY_PROVEN_SAME_PATH"
        claim_text = " ".join(str(claim.get("text") or "") for claim in rec.get("claims") or [])
        assert "SAME_ARTIFACT_STILL_PRESENT is comparison" in claim_text


def test_raw_quotes_are_not_interpretation() -> None:
    quotes = yaml.safe_load(
        (
            REPO_ROOT / "docs/system_atlas/reconciliation/evidence/adjudicate_v1/raw_quotes.yaml"
        ).read_text(encoding="utf-8")
    )
    assert quotes["kind"] == "FORENSIC_RAW_QUOTES"
    assert quotes["interpretation_forbidden_in_this_file"] is True
    assert quotes["items"]
    for item in quotes["items"]:
        assert "quote" in item
        assert "interpretation" not in item
        assert "hypothesis" not in item
        source = REPO_ROOT / str(item["source"])
        assert source.is_file(), item["source"]
        text = source.read_text(encoding="utf-8")
        assert str(item["quote"]) in text


def test_census_presence_not_rewritten() -> None:
    payload = _payload()
    evaluate_index = yaml.safe_load((EVALUATE_ROOT / "index.yaml").read_text())
    evaluate_presence = {
        row["record_id"]: row["census_current_presence"] for row in evaluate_index["rows"]
    }
    for rec in payload["records"]["ledger.yaml"]["records"]:
        rid = rec["identity"]["reconciliation_id"]
        assert rec["discovery"]["current_presence"] == evaluate_presence[rid], rid
