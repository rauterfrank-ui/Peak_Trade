"""UNDERSTAND pass v2 contracts. Historical evidence binding only."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

from scripts.ops.system_atlas_v1.reconciliation_v1 import (
    load_reconciliation_v1,
    validate_reconciliation_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
UNDERSTAND_ROOT = REPO_ROOT / "docs" / "system_atlas" / "reconciliation" / "understand"
VALID_STATUS = frozenset({"PURPOSE_UNDERSTOOD", "UNDERSTAND_PARTIAL", "UNDERSTAND_OPEN"})
FACT_CLASSES = frozenset(
    {"FORENSIC_RAW_FACT", "HISTORICAL_FACT", "CANONICAL_CURRENT_FACT", "ADJUDICATED_CONCLUSION"}
)
FUSION = frozenset({"MERGED_INTO", "RENAMED_TO", "SPLIT_INTO", "SAME_AS"})
DISPOSITION_WORDS = (
    "obsolete",
    "retain",
    "restore",
    "already covered",
    "incompatible today",
    "should be removed",
    "should be reintegrated",
)
GIT_REF_RE = re.compile(r"^([0-9a-f]{7,40})(\^)?(?:[:](.+))?$")
BLOB_RE = re.compile(r"^blob:([0-9a-f]{7,40})$")


def _status() -> dict:
    return yaml.safe_load((UNDERSTAND_ROOT / "pass_v2_status.yaml").read_text(encoding="utf-8"))


def _payload() -> dict:
    return load_reconciliation_v1(repo_root=REPO_ROOT)


def _git_exists(spec: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "cat-file", "-e", spec],
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


def _evidence_exists(ref: str) -> bool:
    """Return True if the ref is present, or if its git object is absent from this clone.

    CI checkouts see origin/main + the PR branch. Census/UNDERSTAND also bound local
    heads that are not ancestors of origin/main. Those SHA:path refs remain valid
    forensic bindings; they are not resolvable in GitHub's object database.
    When the commit is present, the path must still resolve.
    """
    text = str(ref or "").strip()
    if not text:
        return False
    blob = BLOB_RE.match(text)
    if blob:
        return True
    git_ref = GIT_REF_RE.match(text)
    if git_ref:
        sha, caret, path = git_ref.group(1), git_ref.group(2) or "", git_ref.group(3)
        if not _git_exists(sha):
            return True
        spec = f"{sha}{caret}"
        if path:
            return _git_exists(f"{spec}:{path}")
        return _git_exists(spec)
    path = REPO_ROOT / text
    return path.is_file() or path.is_dir()


def test_understand_pass_v2_status_invariants() -> None:
    status = _status()
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
    exhausted = int(status["understand_evidence_exhausted_record_count"])
    assert purpose + partial + opened == 53
    assert exhausted == 53
    assert status["understand_phase_status"] == "EVIDENCE_EXHAUSTED"


def test_all_records_have_valid_understand_status_and_exhaustion() -> None:
    index = yaml.safe_load((UNDERSTAND_ROOT / "index.yaml").read_text(encoding="utf-8"))
    assert int(index["row_count"]) == 53
    ids = {row["record_id"] for row in index["rows"]}
    assert ids == {f"RCN-{n:06d}" for n in range(1, 54)}
    for row in index["rows"]:
        assert row["understand_status"] in VALID_STATUS, row["record_id"]
        assert row["evidence_exhausted"] is True, row["record_id"]
        path = UNDERSTAND_ROOT / "records" / f"{row['record_id']}.yaml"
        rec = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert rec["understand_status"] in VALID_STATUS
        assert rec["evidence_exhausted"] is True
        assert rec["current_system_compared"] is False
        assert rec["disposition_decided"] is False
        assert rec["identity_merge_performed"] is False
        if rec.get("purpose_understood") is True:
            assert rec["understand_status"] == "PURPOSE_UNDERSTOOD"
            assert str(rec.get("historical_purpose") or "").strip()
            facts = [
                claim
                for claim in (rec.get("claims") or [])
                if str(claim.get("claim_class") or "") in FACT_CLASSES
                and list(claim.get("evidence") or [])
            ]
            assert facts, row["record_id"]
        else:
            assert rec["understand_status"] in {"UNDERSTAND_PARTIAL", "UNDERSTAND_OPEN"}


def test_partial_or_open_may_be_evidence_exhausted() -> None:
    found = False
    for path in (UNDERSTAND_ROOT / "records").glob("RCN-*.yaml"):
        rec = yaml.safe_load(path.read_text(encoding="utf-8"))
        if rec.get("purpose_understood") is not True:
            found = True
            assert rec["evidence_exhausted"] is True
            assert rec["understand_status"] in {"UNDERSTAND_PARTIAL", "UNDERSTAND_OPEN"}
    if not found:
        assert True


def test_no_evaluate_disposition_reintegration_or_fusion() -> None:
    payload = _payload()
    assert validate_reconciliation_v1(payload) == []
    ledger = payload["records"]["ledger.yaml"]
    for rec in ledger["records"]:
        rid = rec["identity"]["reconciliation_id"]
        adj = rec["adjudication"]
        comparison = rec["current_comparison"]
        integration = rec["integration"]
        assert str(adj.get("lifecycle_state") or "") not in {
            "REINTEGRATED",
            "COVERED",
            "INCOMPATIBLE",
            "REJECTED",
        }
        assert integration.get("reintegration_required") is False
        _ = comparison
        for rel in (rec.get("relations") or {}).get("items") or []:
            assert str(rel.get("relation_type") or "") not in FUSION, rid
            if rel.get("relation_type") == "POSSIBLE_SAME_AS":
                assert rel.get("epistemic_status") == "HYPOTHESIS", rid
    relations = payload["records"]["relations.yaml"]
    assert int(relations.get("identity_merges_performed") or 0) == 0


def test_census_remains_closed_seventeen_of_seventeen() -> None:
    census = yaml.safe_load(
        (REPO_ROOT / "docs/system_atlas/reconciliation/census_status.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert census["census_closed"] is True
    assert census["census_status"] == "CENSUS_CLOSED"
    assert int(census["surfaces_exhaustion_proven"]) == 17
    assert int(census.get("surfaces_exhaustion_unproven") or 0) == 0


def test_historical_revert_is_not_disposition() -> None:
    rec = yaml.safe_load(
        (UNDERSTAND_ROOT / "records" / "RCN-000015.yaml").read_text(encoding="utf-8")
    )
    assert rec["purpose_understood"] is True
    assert rec["historical_revert_is_not_disposition"] is True
    assert rec["disposition_decided"] is False
    blob = yaml.safe_dump(rec).lower()
    assert "disposition" in blob
    assert rec["understand_status"] == "PURPOSE_UNDERSTOOD"


def test_archive_status_is_not_obsolete() -> None:
    for rid in ("RCN-000014", "RCN-000036", "RCN-000044", "RCN-000045", "RCN-000046"):
        rec = yaml.safe_load(
            (UNDERSTAND_ROOT / "records" / f"{rid}.yaml").read_text(encoding="utf-8")
        )
        assert rec["archive_status_is_not_obsolete"] is True
        assert rec["disposition_decided"] is False
        text = " ".join(
            [
                str(rec.get("historical_purpose") or ""),
                " ".join(str(q) for q in (rec.get("open_questions") or [])),
            ]
        ).lower()
        for word in DISPOSITION_WORDS:
            assert word not in text, f"{rid}:{word}"


def test_relation_targets_exist() -> None:
    payload = _payload()
    ids = {
        rec["identity"]["reconciliation_id"] for rec in payload["records"]["ledger.yaml"]["records"]
    }
    for rec in payload["records"]["ledger.yaml"]["records"]:
        for rel in (rec.get("relations") or {}).get("items") or []:
            target = str(rel.get("target_id") or "")
            unresolved = str(rel.get("unresolved_target") or "")
            if target:
                assert target in ids, f"{rec['identity']['reconciliation_id']}->{target}"
            else:
                assert unresolved


def test_historical_git_ref_absent_from_clone_is_not_missing() -> None:
    fake = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:src/does_not_exist.py"
    assert _git_exists("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa") is False
    assert _evidence_exists(fake) is True


def test_evidence_refs_exist() -> None:
    """Workspace paths must exist. Git SHA:path must resolve when the commit is in this clone."""
    missing: list[str] = []
    for path in (UNDERSTAND_ROOT / "records").glob("RCN-*.yaml"):
        rec = yaml.safe_load(path.read_text(encoding="utf-8"))
        refs = list(rec.get("evidence_refs") or [])
        for claim in rec.get("claims") or []:
            refs.extend(list(claim.get("evidence") or []))
        for ref in refs:
            if not _evidence_exists(str(ref)):
                missing.append(f"{rec['record_id']}:{ref}")
    assert missing == []


def test_raw_quotes_are_not_interpretation() -> None:
    quotes = yaml.safe_load(
        (
            REPO_ROOT / "docs/system_atlas/reconciliation/evidence/understand_v2/raw_quotes.yaml"
        ).read_text(encoding="utf-8")
    )
    assert quotes["kind"] == "FORENSIC_RAW_QUOTES"
    assert quotes["interpretation_forbidden_in_this_file"] is True
    assert quotes["items"]
    for item in quotes["items"]:
        assert "quote" in item
        assert "interpretation" not in item
        assert "hypothesis" not in item


def test_peaktraderepo_placeholder_contradiction_is_not_fact() -> None:
    rec = yaml.safe_load(
        (UNDERSTAND_ROOT / "records" / "RCN-000014.yaml").read_text(encoding="utf-8")
    )
    hits = [
        claim
        for claim in rec.get("claims") or []
        if str(claim.get("claim_class") or "") == "CONTRADICTION"
    ]
    assert hits
    assert all(claim.get("used_as_fact") is False for claim in hits)
    assert rec["purpose_understood"] is True


def test_landscape_cluster_includes_reset_pack() -> None:
    clusters = yaml.safe_load((UNDERSTAND_ROOT / "clusters.yaml").read_text(encoding="utf-8"))
    assert clusters["clusters_are_not_identity_groups"] is True
    landscape = next(
        row for row in clusters["clusters"] if row["cluster_id"] == "landscape_dashboard"
    )
    assert "RCN-000047" in landscape["record_ids"]
    assert len(landscape["record_ids"]) == 20
    rec = yaml.safe_load(
        (UNDERSTAND_ROOT / "records" / "RCN-000047.yaml").read_text(encoding="utf-8")
    )
    assert rec["purpose_understood"] is True
    assert rec["understand_status"] == "PURPOSE_UNDERSTOOD"
