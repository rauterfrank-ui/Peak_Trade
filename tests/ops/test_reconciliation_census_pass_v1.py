"""Census pass v1 contracts. Discovery/evidence-binding only."""

from __future__ import annotations

from pathlib import Path

from scripts.ops.system_atlas_v1.reconciliation_v1 import (
    load_reconciliation_v1,
    validate_reconciliation_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_LIFECYCLE = frozenset({"DISCOVERED", "EVIDENCE_BOUND"})
FORBIDDEN_LIFECYCLE = frozenset(
    {
        "PURPOSE_UNDERSTOOD",
        "CURRENT_SYSTEM_COMPARED",
        "ADJUDICATED",
        "DISPOSITION_DECIDED",
        "REINTEGRATED",
        "COVERED",
        "INCOMPATIBLE",
        "REJECTED",
    }
)


def _payload() -> dict:
    return load_reconciliation_v1(repo_root=REPO_ROOT)


def test_census_pass_v1_live_tree_valid() -> None:
    payload = _payload()
    assert validate_reconciliation_v1(payload) == []


def test_census_pass_v1_lifecycle_and_epistemic_bounds() -> None:
    payload = _payload()
    ledger = payload["records"]["ledger.yaml"]
    records = list(ledger.get("records") or [])
    assert ledger["ledger_record_count"] == len(records)
    assert len(records) > 0
    purpose_true = 0
    compared = 0
    adjudicated = 0
    dispositioned = 0
    for rec in records:
        understanding = rec.get("understanding") or {}
        adjudication = rec.get("adjudication") or {}
        comparison = rec.get("current_comparison") or {}
        integration = rec.get("integration") or {}
        lifecycle = str(adjudication.get("lifecycle_state") or "")
        assert lifecycle in ALLOWED_LIFECYCLE
        assert lifecycle not in FORBIDDEN_LIFECYCLE
        assert understanding.get("purpose_understood") is False
        assert str(understanding.get("purpose_statement") or "") == ""
        assert str(adjudication.get("disposition") or "") == ""
        assert integration.get("reintegration_required") is False
        assert str(comparison.get("current_equivalent") or "") == ""
        assert list(comparison.get("current_paths") or []) == []
        if understanding.get("purpose_understood") is True:
            purpose_true += 1
        if str(comparison.get("capability_overlap") or ""):
            compared += 1
        if lifecycle in {"ADJUDICATED", "DISPOSITION_DECIDED"}:
            adjudicated += 1
        if str(adjudication.get("disposition") or ""):
            dispositioned += 1
    assert purpose_true == 0
    assert compared == 0
    assert adjudicated == 0
    assert dispositioned == 0


def test_census_pass_v1_artifacts_and_anchors() -> None:
    payload = _payload()
    census = payload["records"]["census_status.yaml"]
    assert census["census_status"] == "CENSUS_IN_PROGRESS"
    assert census["census_exhaustion_proven"] is False
    assert census["census_closed"] is False
    assert census["search_universe_bound"] is True
    for rel in (
        "search_surfaces.yaml",
        "coverage.yaml",
        "discovery_candidates.yaml",
        "relations.yaml",
    ):
        assert rel in payload["records"]
    candidates = payload["records"]["discovery_candidates.yaml"]
    assert candidates.get("counted_as_ledger_records") is False
    assert str(candidates.get("kind") or "") == "CANDIDATE_NOT_LEDGER_BOUND"
    anchors = payload["records"]["search_anchors.yaml"]
    assert anchors["counted_as_ledger_records"] is False
    assert anchors["anchors_are_not_census_boundaries"] is True
    coverage = payload["records"]["coverage.yaml"]
    assert coverage.get("exhaustion_proven") is False
    assert int(coverage.get("surfaces_exhaustion_proven") or 0) == 0
