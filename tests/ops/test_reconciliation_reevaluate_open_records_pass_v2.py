"""REEVALUATE_OPEN_RECORDS_PASS_V2 contracts. Additive. V1 snapshots stay frozen."""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.ops.system_atlas_v1.adjudicate_pass_v1_records import RETAIN, RETAIN_IDS
from scripts.ops.system_atlas_v1.evidence_resolution_pass_v1_records import OPEN_IDS
from scripts.ops.system_atlas_v1.reevaluate_open_records_pass_v1_records import (
    REEVALUATE_BOUND_SHA as REEVALUATE_V1_BOUND_SHA,
    REEVALUATE_PASS_ID as REEVALUATE_V1_PASS_ID,
)
from scripts.ops.system_atlas_v1.reevaluate_open_records_pass_v2_persist import (
    REEVALUATE_V2_PASS_ID,
)
from scripts.ops.system_atlas_v1.reevaluate_open_records_pass_v2_records import (
    CONTRADICTION_ID_052,
    INCOMPATIBLE,
    INSUFFICIENT,
    OUT_OF_SCOPE_OPEN_IDS,
    PREDECESSOR_BOUND_SHA,
    PREDECESSOR_PASS_ID,
    REJECT,
    REEVALUATE_V2_BOUND_SHA,
    REMAINING_OPEN_IDS,
    RESULTING_DISPOSITIONS,
    TARGET_FINAL_IDS,
    V2_WRITTEN_RECORD_IDS,
    reevaluate_open_records_pass_v2,
)
from scripts.ops.system_atlas_v1.reconciliation_v1 import (
    load_reconciliation_v1,
    validate_reconciliation_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RECON = REPO_ROOT / "docs" / "system_atlas" / "reconciliation"
PASS_ROOT = RECON / "reevaluate"
V1_RECORDS = PASS_ROOT / "records"
V2_RECORDS = PASS_ROOT / "records_v2"
FUSION = frozenset({"MERGED_INTO", "RENAMED_TO", "SPLIT_INTO", "SAME_AS"})


def _status() -> dict:
    return yaml.safe_load((PASS_ROOT / "pass_v2_status.yaml").read_text(encoding="utf-8"))


def _payload() -> dict:
    return load_reconciliation_v1(repo_root=REPO_ROOT)


def test_reevaluate_pass_v2_status_invariants() -> None:
    status = _status()
    assert status["census_closed"] is True
    assert int(status["input_open_record_count"]) == 35
    assert int(status["new_final_disposition_count"]) == 5
    assert int(status["remaining_insufficient_evidence_open_count"]) == 30
    assert int(status["new_historically_valid_but_incompatible_count"]) == 1
    assert int(status["new_reject_for_current_system_count"]) == 4
    assert int(status["new_retain_as_is_count"]) == 0
    assert int(status["identity_merges_performed"]) == 0
    assert status["reintegration_performed"] is False
    assert status["runtime_mutation_performed"] is False
    assert status["rcn_000052_remains_open"] is True
    assert status["rcn_000052_contradiction_id"] == CONTRADICTION_ID_052
    assert status["c052_contradiction_resolved"] is False
    assert status["frozen_v1_snapshots_unchanged"] is True
    assert status["bound_against_sha"] == REEVALUATE_V2_BOUND_SHA
    assert status["reevaluate_pass_id"] == REEVALUATE_V2_PASS_ID
    assert status["predecessor_pass_id"] == PREDECESSOR_PASS_ID
    assert status["predecessor_bound_sha"] == PREDECESSOR_BOUND_SHA
    assert int(status["total_ledger_record_count"]) == 53
    assert int(status["total_retain_as_is_count"]) == 18
    assert int(status["total_insufficient_evidence_count"]) == 30
    assert list(status["target_final_record_ids"]) == list(TARGET_FINAL_IDS)
    assert status["resulting_dispositions"]["RCN-000015"] == INCOMPATIBLE
    assert status["resulting_dispositions"]["RCN-000044"] == REJECT
    assert status["resulting_dispositions"]["RCN-000045"] == REJECT
    assert status["resulting_dispositions"]["RCN-000046"] == REJECT
    assert status["resulting_dispositions"]["RCN-000051"] == REJECT
    assert status["resulting_dispositions"]["RCN-000052"] == INSUFFICIENT


def test_live_ledger_transition_35_to_30_open() -> None:
    payload = _payload()
    assert validate_reconciliation_v1(payload) == []
    ledger = payload["records"]["ledger.yaml"]
    assert ledger["reevaluate_pass_id"] == REEVALUATE_V2_PASS_ID
    assert ledger["reevaluate_bound_against_sha"] == REEVALUATE_V2_BOUND_SHA
    assert ledger["reevaluate_v1_pass_id_frozen"] == REEVALUATE_V1_PASS_ID
    assert ledger["reevaluate_v1_bound_against_sha_frozen"] == REEVALUATE_V1_BOUND_SHA
    retain = 0
    insufficient = 0
    incompatible = 0
    rejected = 0
    open_ids = []
    for rec in ledger["records"]:
        rid = rec["identity"]["reconciliation_id"]
        disp = rec["adjudication"]["disposition"]
        if disp == RETAIN:
            retain += 1
            assert rid in RETAIN_IDS
            assert rec.get("reevaluate_v2") is None
        elif disp == INSUFFICIENT:
            insufficient += 1
            open_ids.append(rid)
            assert rec["adjudication"]["lifecycle_state"] == "OPEN"
        elif disp == INCOMPATIBLE:
            incompatible += 1
        elif disp == REJECT:
            rejected += 1
        else:
            raise AssertionError(f"unexpected_disposition:{rid}:{disp}")
    assert retain == 18
    assert insufficient == 30
    assert incompatible == 1
    assert rejected == 4
    assert tuple(open_ids) == REMAINING_OPEN_IDS
    assert len(ledger["records"]) == 53


def test_v2_records_match_generated_and_refs_exist() -> None:
    generated = {row["record_id"]: row for row in reevaluate_open_records_pass_v2()}
    index = yaml.safe_load((PASS_ROOT / "index_v2.yaml").read_text(encoding="utf-8"))
    assert int(index["row_count"]) == 35
    assert tuple(row["record_id"] for row in index["rows"]) == OPEN_IDS
    written = [row for row in index["rows"] if row["v2_record_written"] is True]
    unchanged = [row for row in index["rows"] if row["predecessor_unchanged"] is True]
    assert len(written) == 6
    assert len(unchanged) == 29
    assert tuple(row["record_id"] for row in written) == V2_WRITTEN_RECORD_IDS
    assert tuple(row["record_id"] for row in unchanged) == OUT_OF_SCOPE_OPEN_IDS
    for rid in V2_WRITTEN_RECORD_IDS:
        persisted = yaml.safe_load((V2_RECORDS / f"{rid}.yaml").read_text(encoding="utf-8"))
        payload = generated[rid]
        assert persisted["record_id"] == rid
        assert persisted["disposition"] == RESULTING_DISPOSITIONS[rid]
        assert persisted["disposition"] == payload["disposition"]
        assert persisted["identity_merge_performed"] is False
        assert persisted["reintegration_performed"] is False
        assert persisted["runtime_mutation_performed"] is False
        assert persisted["v1_snapshot_frozen"] is True
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


def test_frozen_v1_reevaluate_snapshots_remain_35_open() -> None:
    status = yaml.safe_load((PASS_ROOT / "pass_v1_status.yaml").read_text(encoding="utf-8"))
    assert status["reevaluate_pass_id"] == REEVALUATE_V1_PASS_ID
    assert int(status["remaining_insufficient_evidence_open_count"]) == 35
    assert int(status["new_final_disposition_count"]) == 0
    index = yaml.safe_load((PASS_ROOT / "index.yaml").read_text(encoding="utf-8"))
    assert int(index["row_count"]) == 35
    for rid in OPEN_IDS:
        rec = yaml.safe_load((V1_RECORDS / f"{rid}.yaml").read_text(encoding="utf-8"))
        assert rec["disposition"] == INSUFFICIENT
        assert rec["disposition_burden_met"] is False
        assert rec["lifecycle_state"] == "OPEN"


def test_target_dispositions_and_052_remain_open() -> None:
    payload = _payload()
    by_id = {
        rec["identity"]["reconciliation_id"]: rec
        for rec in payload["records"]["ledger.yaml"]["records"]
    }
    assert by_id["RCN-000015"]["adjudication"]["disposition"] == INCOMPATIBLE
    assert by_id["RCN-000044"]["adjudication"]["disposition"] == REJECT
    assert by_id["RCN-000045"]["adjudication"]["disposition"] == REJECT
    assert by_id["RCN-000046"]["adjudication"]["disposition"] == REJECT
    assert by_id["RCN-000051"]["adjudication"]["disposition"] == REJECT
    rec052 = by_id["RCN-000052"]
    assert rec052["adjudication"]["disposition"] == INSUFFICIENT
    assert rec052["adjudication"]["lifecycle_state"] == "OPEN"
    assert rec052["discovery"]["current_presence"] == "CURRENTLY_ABSENT"
    assert rec052["reevaluate_v2"]["contradiction_id"] == CONTRADICTION_ID_052
    assert rec052["reevaluate_v2"]["final_disposition_change_performed"] is False
    v2_015 = yaml.safe_load((V2_RECORDS / "RCN-000015.yaml").read_text())
    blob = " ".join([v2_015["positive_reason"], *v2_015["alternatives_rejected"]]).lower()
    assert "exclusive selection authority" in blob
    assert "revert" in blob
    assert REJECT in " ".join(v2_015["alternatives_rejected"])
    v2_044 = yaml.safe_load((V2_RECORDS / "RCN-000044.yaml").read_text())
    assert "# Engine placeholder" in v2_044["positive_reason"]
    assert "readme" in " ".join(v2_044["alternatives_rejected"]).lower()
    v2_051 = yaml.safe_load((V2_RECORDS / "RCN-000051.yaml").read_text())
    assert (
        "SAME_BLOB_AS" in v2_051["historical_relations"]
        or "same_blob" in v2_051["positive_reason"].lower()
    )
    assert any(
        item.get("relation_type") == "SAME_BLOB_AS"
        for item in by_id["RCN-000051"]["relations"]["items"]
    )
    assert not any(
        item.get("relation_type") in FUSION for item in by_id["RCN-000051"]["relations"]["items"]
    )


def test_no_identity_fusion_or_reintegration() -> None:
    payload = _payload()
    for rec in payload["records"]["ledger.yaml"]["records"]:
        rid = rec["identity"]["reconciliation_id"]
        for rel in (rec.get("relations") or {}).get("items") or []:
            assert str(rel.get("relation_type") or "") not in FUSION, rid
        v2 = rec.get("reevaluate_v2") or {}
        assert v2.get("identity_merge_performed") is not True, rid
        assert v2.get("reintegration_performed") is not True, rid
        assert rec["integration"].get("reintegration_required") is False, rid
    relations = payload["records"]["relations.yaml"]
    assert int(relations.get("identity_merges_performed") or 0) == 0


def test_raw_quotes_are_not_interpretation() -> None:
    quotes = yaml.safe_load(
        (RECON / "evidence" / "reevaluate_v2" / "raw_quotes.yaml").read_text(encoding="utf-8")
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


def test_schema_pins_v2_counts_and_v1_freeze() -> None:
    schema = yaml.safe_load((RECON / "schema.yaml").read_text(encoding="utf-8"))
    assert schema["reevaluate_v1_snapshots_are_frozen"] is True
    assert int(schema["reevaluate_v2_input_open_count"]) == 35
    assert int(schema["reevaluate_v2_finalized_count"]) == 5
    assert int(schema["reevaluate_v2_remaining_open_count"]) == 30
    assert schema["reevaluate_v2_rcn_000052_remains_open"] is True
    assert schema["reevaluate_v2_no_identity_merges"] is True
    assert schema["reevaluate_v2_no_runtime_mutation"] is True
    assert schema["reevaluate_v2_no_reintegration"] is True
    files = schema["reevaluate_artifact_files"]
    assert "reevaluate/pass_v1_status.yaml" in files
    assert "reevaluate/pass_v2_status.yaml" in files
    assert "reevaluate/index_v2.yaml" in files
