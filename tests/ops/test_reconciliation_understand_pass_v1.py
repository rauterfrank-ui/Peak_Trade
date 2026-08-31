"""UNDERSTAND pass v1 contracts. Historical evidence binding only."""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.ops.system_atlas_v1.reconciliation_v1 import (
    load_reconciliation_v1,
    validate_reconciliation_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
UNDERSTAND_ROOT = REPO_ROOT / "docs" / "system_atlas" / "reconciliation" / "understand"
POST_COMPARE_LIFECYCLE = frozenset(
    {
        "ADJUDICATED",
        "DISPOSITION_DECIDED",
        "REINTEGRATED",
        "COVERED",
        "INCOMPATIBLE",
        "REJECTED",
    }
)
FACT_CLASSES = frozenset(
    {"FORENSIC_RAW_FACT", "HISTORICAL_FACT", "CANONICAL_CURRENT_FACT", "ADJUDICATED_CONCLUSION"}
)


def _payload() -> dict:
    return load_reconciliation_v1(repo_root=REPO_ROOT)


def test_understand_pass_v1_status_invariants() -> None:
    status = yaml.safe_load((UNDERSTAND_ROOT / "pass_v1_status.yaml").read_text(encoding="utf-8"))
    assert status["census_closed"] is True
    assert status["census_status"] == "CENSUS_CLOSED"
    assert int(status["surfaces_exhaustion_proven"]) == 17
    assert int(status["ledger_record_count"]) == 53
    assert int(status["current_system_compared_record_count"]) == 0
    assert int(status["adjudicated_record_count"]) == 0
    assert int(status["disposition_decided_record_count"]) == 0
    assert int(status["identity_merges_performed"]) == 0
    assert status["no_current_system_comparison_performed"] is True
    assert status["no_disposition_decided"] is True
    assert status["no_reintegration_performed"] is True
    purpose = int(status["purpose_understood_record_count"])
    partial = int(status["understand_partial_record_count"])
    opened = int(status["understand_open_record_count"])
    assert purpose + partial + opened == 53
    assert purpose > 0


def test_understand_purpose_requires_evidence_and_no_evaluate() -> None:
    payload = _payload()
    assert validate_reconciliation_v1(payload) == []
    ledger = payload["records"]["ledger.yaml"]
    purpose = 0
    for rec in ledger["records"]:
        rid = rec["identity"]["reconciliation_id"]
        understanding = rec["understanding"]
        adjudication = rec["adjudication"]
        comparison = rec["current_comparison"]
        integration = rec["integration"]
        lifecycle = str(adjudication.get("lifecycle_state") or "")
        assert lifecycle not in POST_COMPARE_LIFECYCLE, rid
        assert str(adjudication.get("disposition") or "") == ""
        assert integration.get("reintegration_required") is False
        _ = comparison
        understand_path = UNDERSTAND_ROOT / "records" / f"{rid}.yaml"
        assert understand_path.is_file(), rid
        row = yaml.safe_load(understand_path.read_text(encoding="utf-8"))
        assert row["record_id"] == rid
        assert row["current_system_compared"] is False
        assert row["evaluate_performed"] is False
        assert row["disposition_decided"] is False
        assert row["identity_merge_performed"] is False
        if understanding.get("purpose_understood") is True:
            purpose += 1
            assert str(understanding.get("purpose_statement") or "").strip()
            claims = list(understanding.get("claims") or [])
            fact_hits = [
                claim
                for claim in claims
                if str(claim.get("claim_class") or "") in FACT_CLASSES
                and list(claim.get("evidence") or [])
            ]
            assert fact_hits, rid
            assert row["purpose_understood"] is True
            assert str(row.get("historical_purpose") or "").strip()
            assert lifecycle in {"PURPOSE_UNDERSTOOD", "CURRENT_SYSTEM_COMPARED"}
        else:
            assert lifecycle in {"DISCOVERED", "EVIDENCE_BOUND"}
    latest = UNDERSTAND_ROOT / "pass_v2_status.yaml"
    if not latest.is_file():
        latest = UNDERSTAND_ROOT / "pass_v1_status.yaml"
    assert purpose == int(
        yaml.safe_load(latest.read_text(encoding="utf-8"))["purpose_understood_record_count"]
    )


def test_understand_clusters_are_navigation_not_identity() -> None:
    clusters = yaml.safe_load((UNDERSTAND_ROOT / "clusters.yaml").read_text(encoding="utf-8"))
    assert clusters["clusters_are_not_identity_groups"] is True
    landscape = None
    for row in clusters["clusters"]:
        assert row["cluster_kind"] == "NAVIGATION_ONLY"
        assert row["identity_group"] is False
        if row["cluster_id"] == "landscape_dashboard":
            landscape = row
    assert landscape is not None
    ids = list(landscape["record_ids"])
    assert "RCN-000001" in ids
    assert "RCN-000002" in ids
    assert "RCN-000009" in ids
    assert len(ids) > 1
    index = yaml.safe_load((UNDERSTAND_ROOT / "index.yaml").read_text(encoding="utf-8"))
    assert int(index["row_count"]) == 53
    index_ids = {row["record_id"] for row in index["rows"]}
    assert index_ids == {f"RCN-{n:06d}" for n in range(1, 54)}


def test_understand_raw_quotes_are_not_interpretation() -> None:
    quotes = yaml.safe_load(
        (
            REPO_ROOT / "docs/system_atlas/reconciliation/evidence/understand_v1/raw_quotes.yaml"
        ).read_text(encoding="utf-8")
    )
    assert quotes["kind"] == "FORENSIC_RAW_QUOTES"
    assert quotes["interpretation_forbidden_in_this_file"] is True
    assert quotes["items"]


def test_understand_no_identity_fusion_relations() -> None:
    payload = _payload()
    fusion = {"MERGED_INTO", "RENAMED_TO", "SPLIT_INTO", "SAME_AS"}
    for rec in payload["records"]["ledger.yaml"]["records"]:
        for rel in (rec.get("relations") or {}).get("items") or []:
            assert str(rel.get("relation_type") or "") not in fusion
            if rel.get("relation_type") == "POSSIBLE_SAME_AS":
                assert rel.get("epistemic_status") == "HYPOTHESIS"
    relations = payload["records"]["relations.yaml"]
    assert int(relations.get("identity_merges_performed") or 0) == 0
