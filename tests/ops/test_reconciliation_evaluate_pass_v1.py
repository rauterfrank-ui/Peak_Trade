"""EVALUATE_INDIVIDUALLY pass v1 contracts. Current-system comparison only."""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.ops.system_atlas_v1.evaluate_pass_v1_records import (
    ALLOWED_OVERLAP,
    EVALUATE_BOUND_SHA,
)
from scripts.ops.system_atlas_v1.reconciliation_v1 import (
    load_reconciliation_v1,
    validate_reconciliation_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EVALUATE_ROOT = REPO_ROOT / "docs" / "system_atlas" / "reconciliation" / "evaluate"
UNDERSTAND_ROOT = REPO_ROOT / "docs" / "system_atlas" / "reconciliation" / "understand"
FUSION = frozenset({"MERGED_INTO", "RENAMED_TO", "SPLIT_INTO", "SAME_AS"})
DISPOSITION_WORDS = (
    "should be reintegrated",
    "should be removed",
    "retain as is",
    "already covered",
    "reject for current system",
)


def _status() -> dict:
    return yaml.safe_load((EVALUATE_ROOT / "pass_v1_status.yaml").read_text(encoding="utf-8"))


def _payload() -> dict:
    return load_reconciliation_v1(repo_root=REPO_ROOT)


def test_evaluate_pass_v1_status_invariants() -> None:
    status = _status()
    assert status["census_closed"] is True
    assert status["census_status"] == "CENSUS_CLOSED"
    assert int(status["surfaces_exhaustion_proven"]) == 17
    assert int(status["ledger_record_count"]) == 53
    assert int(status["current_system_compared_record_count"]) == 53
    assert int(status["adjudicated_record_count"]) == 0
    assert int(status["disposition_decided_record_count"]) == 0
    assert int(status["identity_merges_performed"]) == 0
    assert status["no_disposition_decided"] is True
    assert status["no_reintegration_performed"] is True
    assert status["no_identity_fusion_performed"] is True
    assert status["evaluate_phase_status"] == "CURRENT_SYSTEM_COMPARED"
    assert status["bound_against_sha"] == EVALUATE_BOUND_SHA
    assert status["identity_fusion_forbidden"] is True
    assert status["disposition_performed"] is False


def test_all_records_compared_without_disposition() -> None:
    index = yaml.safe_load((EVALUATE_ROOT / "index.yaml").read_text(encoding="utf-8"))
    assert int(index["row_count"]) == 53
    ids = {row["record_id"] for row in index["rows"]}
    assert ids == {f"RCN-{n:06d}" for n in range(1, 54)}
    payload = _payload()
    assert validate_reconciliation_v1(payload) == []
    ledger = payload["records"]["ledger.yaml"]
    for rec in ledger["records"]:
        rid = rec["identity"]["reconciliation_id"]
        comparison = rec["current_comparison"]
        adj = rec["adjudication"]
        integration = rec["integration"]
        assert adj["lifecycle_state"] == "CURRENT_SYSTEM_COMPARED", rid
        assert str(adj.get("disposition") or "") == ""
        assert integration.get("reintegration_required") is False
        assert comparison["compared_against_sha"] == EVALUATE_BOUND_SHA
        assert comparison["comparison_status"] == "CURRENT_SYSTEM_COMPARED"
        overlap = str(comparison.get("capability_overlap") or "")
        assert overlap in ALLOWED_OVERLAP, f"{rid}:{overlap}"
        claims = list(comparison.get("claims") or [])
        fact_hits = [
            claim
            for claim in claims
            if str(claim.get("claim_class") or "")
            in {"FORENSIC_RAW_FACT", "HISTORICAL_FACT", "CANONICAL_CURRENT_FACT"}
            and list(claim.get("evidence") or [])
        ]
        assert fact_hits, rid
        path = EVALUATE_ROOT / "records" / f"{rid}.yaml"
        row = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert row["record_id"] == rid
        assert row["comparison_status"] == "CURRENT_SYSTEM_COMPARED"
        assert row["disposition_performed"] is False
        assert row["identity_fusion_forbidden"] is True
        assert row["reintegration_performed"] is False
        blob = yaml.safe_dump(row).lower()
        for word in DISPOSITION_WORDS:
            assert word not in blob, f"{rid}:{word}"


def test_understand_snapshots_remain_unevaluated() -> None:
    for path in (UNDERSTAND_ROOT / "records").glob("RCN-*.yaml"):
        rec = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert rec["current_system_compared"] is False, rec["record_id"]
        assert rec["evaluate_performed"] is False, rec["record_id"]
        assert rec["disposition_decided"] is False, rec["record_id"]
        assert rec["identity_merge_performed"] is False, rec["record_id"]
    v2 = yaml.safe_load((UNDERSTAND_ROOT / "pass_v2_status.yaml").read_text(encoding="utf-8"))
    assert int(v2["current_system_compared_record_count"]) == 0
    assert v2["no_current_system_comparison_performed"] is True


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


def test_same_artifact_present_has_current_paths() -> None:
    for path in (EVALUATE_ROOT / "records").glob("RCN-*.yaml"):
        rec = yaml.safe_load(path.read_text(encoding="utf-8"))
        if rec["capability_overlap"] != "SAME_ARTIFACT_STILL_PRESENT":
            continue
        assert str(rec.get("current_equivalent") or "").strip(), rec["record_id"]
        assert list(rec.get("current_paths") or []), rec["record_id"]
        for rel in rec["current_paths"]:
            target = REPO_ROOT / rel
            assert target.exists(), f"{rec['record_id']}:{rel}"


def test_unproven_replacement_is_not_equivalent() -> None:
    rec = yaml.safe_load(
        (EVALUATE_ROOT / "records" / "RCN-000015.yaml").read_text(encoding="utf-8")
    )
    assert rec["capability_overlap"] == "CURRENT_FUNCTION_CANDIDATE_UNPROVEN"
    assert rec["current_equivalent"] == ""
    assert rec["disposition_performed"] is False
    assert "src/ops/single_selected_future_policy_v1/" in rec["current_paths"]


def test_partial_risk_layer_family() -> None:
    rec = yaml.safe_load(
        (EVALUATE_ROOT / "records" / "RCN-000019.yaml").read_text(encoding="utf-8")
    )
    assert rec["capability_overlap"] == "SAME_PATH_FAMILY_PARTIAL"
    assert rec["census_current_presence"] == "CURRENTLY_PARTIAL"
    assert "src/risk_layer/kill_switch/" in rec["current_paths"]
    assert rec["disposition_performed"] is False


def test_census_absent_observability_family_now_present() -> None:
    rec = yaml.safe_load(
        (EVALUATE_ROOT / "records" / "RCN-000052.yaml").read_text(encoding="utf-8")
    )
    assert rec["capability_overlap"] == "CENSUS_ABSENT_BUT_CURRENT_TREE_PRESENT"
    assert rec["census_current_presence"] == "CURRENTLY_ABSENT"
    assert (REPO_ROOT / "docs/webui/observability/OBSERVABILITY_HUB_V0.md").is_file()
    hits = [
        claim
        for claim in rec.get("claims") or []
        if str(claim.get("claim_class") or "") == "CONTRADICTION"
    ]
    assert hits
    assert all(claim.get("used_as_fact") is False for claim in hits)


def test_raw_quotes_are_not_interpretation() -> None:
    quotes = yaml.safe_load(
        (
            REPO_ROOT / "docs/system_atlas/reconciliation/evidence/evaluate_v1/raw_quotes.yaml"
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


def test_census_remains_closed() -> None:
    census = yaml.safe_load(
        (REPO_ROOT / "docs/system_atlas/reconciliation/census_status.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert census["census_closed"] is True
    assert int(census["surfaces_exhaustion_proven"]) == 17
