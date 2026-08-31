"""Reconciliation governance/ledger contracts. Not runtime authority."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from scripts.ops.system_atlas_v1.constants_v1 import (
    ATLAS_AUTHORITY,
    RECONCILIATION_AUTHORITY,
    RECONCILIATION_ROLE,
)
from scripts.ops.system_atlas_v1.load_v1 import load_atlas_v1
from scripts.ops.system_atlas_v1.reconciliation_v1 import (
    ReconciliationValidationError,
    load_reconciliation_v1,
    validate_reconciliation_v1,
)
from scripts.ops.system_atlas_v1.validate_v1 import validate_atlas_v1

REPO_ROOT = Path(__file__).resolve().parents[2]
RECON_ROOT = REPO_ROOT / "docs" / "system_atlas" / "reconciliation"


def _payload() -> dict:
    return load_reconciliation_v1(repo_root=REPO_ROOT)


def _minimal_record(*, rid: str = "RCN-000001", **adjudication: object) -> dict:
    adj = {
        "lifecycle_state": "DISCOVERED",
        "disposition": "",
        "positive_reason": "",
        "evidence_refs": [],
        "contradictions": [],
        "unresolved_questions": [],
    }
    adj.update(adjudication)
    purpose = bool(adjudication.get("purpose_understood", False))
    understanding = {
        "purpose_understood": purpose,
        "purpose_statement": "bound-example" if purpose else "",
        "historical_problem_statement": "",
        "inputs": [],
        "outputs": [],
        "dependencies": [],
        "consumers": [],
        "authority_role": "",
        "safety_role": "",
        "runtime_role": "",
        "invariants": [],
    }
    if "purpose_understood" in adjudication:
        understanding["purpose_understood"] = bool(adjudication["purpose_understood"])
        adj.pop("purpose_understood", None)
    if understanding["purpose_understood"] is True:
        understanding["claims"] = [
            {
                "claim_class": "FORENSIC_RAW_FACT",
                "text": "test-bound purpose evidence",
                "evidence": ["tests/ops/test_reconciliation_ledger_v1.py"],
                "used_as_fact": True,
            }
        ]
    return {
        "identity": {
            "reconciliation_id": rid,
            "canonical_record_name": rid,
            "historical_names": [],
            "aliases": [],
        },
        "discovery": {
            "discovery_status": "DISCOVERED",
            "discovered_from": [],
            "discovery_evidence": [],
            "first_bound_ref": "",
            "historical_paths": [],
            "historical_refs": [],
            "historical_commits": [],
        },
        "understanding": understanding,
        "relations": {"items": []},
        "current_comparison": {
            "current_equivalent": "",
            "current_paths": [],
            "capability_overlap": "",
            "semantic_compatibility": "",
            "authority_compatibility": "",
            "safety_compatibility": "",
            "runtime_compatibility": "",
            "conflicts": [],
            "gaps": [],
        },
        "adjudication": adj,
        "integration": {
            "reintegration_required": False,
            "adaptation_required": False,
            "implementation_status": "",
            "implementation_refs": [],
        },
        "audit": {
            "created_from_evidence": True,
            "last_adjudicated_against_sha": "",
            "notes": "test-only",
        },
    }


def _with_records(payload: dict, records: list[dict]) -> dict:
    mutated = copy.deepcopy(payload)
    mutated["records"]["ledger.yaml"]["records"] = records
    mutated["records"]["ledger.yaml"]["ledger_record_count"] = len(records)
    return mutated


def test_authority_markers_remain_none() -> None:
    assert ATLAS_AUTHORITY == "NONE"
    assert RECONCILIATION_AUTHORITY == "NONE"
    assert RECONCILIATION_ROLE == "GOVERNANCE_AND_EVIDENCE_NOT_RUNTIME"
    readme = (RECON_ROOT / "README.md").read_text(encoding="utf-8")
    assert "ATLAS_AUTHORITY=NONE" in readme
    assert "RECONCILIATION_AUTHORITY=NONE" in readme
    atlas_readme = (REPO_ROOT / "docs" / "system_atlas" / "README.md").read_text(encoding="utf-8")
    assert "ATLAS_AUTHORITY=NONE" in atlas_readme
    assert "does not raise Atlas authority" in atlas_readme


def test_constructed_empty_ledger_and_not_started_still_valid() -> None:
    payload = copy.deepcopy(_payload())
    payload["records"]["ledger.yaml"]["records"] = []
    payload["records"]["ledger.yaml"]["ledger_record_count"] = 0
    census = payload["records"]["census_status.yaml"]
    census["census_status"] = "CENSUS_NOT_STARTED"
    census["census_exhaustion_proven"] = False
    census["census_closed"] = False
    census["search_universe_bound"] = False
    census["historical_census_performed"] = False
    census["search_universe_evidence"] = []
    assert validate_reconciliation_v1(payload) == []


def test_live_census_closed_after_pass_v3() -> None:
    census = _payload()["records"]["census_status.yaml"]
    assert census["census_status"] == "CENSUS_CLOSED"
    assert census["census_exhaustion_proven"] is True
    assert census["census_closed"] is True
    assert census["search_universe_bound"] is True
    assert census["historical_census_performed"] is True


def test_known_search_anchors_are_not_records() -> None:
    payload = _payload()
    anchors = payload["records"]["search_anchors.yaml"]
    names = [row["name"] for row in anchors["anchors"]]
    assert names == ["Landscape", "Master V2", "Double Play"]
    assert anchors["counted_as_ledger_records"] is False
    record_ids = {
        str((rec.get("identity") or {}).get("reconciliation_id") or "")
        for rec in payload["records"]["ledger.yaml"]["records"]
    }
    assert not any(str(row.get("id") or "") in record_ids for row in anchors["anchors"])


def test_valid_lifecycle_and_open_insufficient_evidence() -> None:
    payload = _with_records(
        _payload(),
        [
            _minimal_record(lifecycle_state="DISCOVERED"),
            _minimal_record(
                rid="RCN-000002",
                lifecycle_state="OPEN",
                disposition="INSUFFICIENT_EVIDENCE",
                purpose_understood=False,
            ),
        ],
    )
    assert validate_reconciliation_v1(payload) == []


def test_valid_reject_with_positive_reason() -> None:
    payload = _with_records(
        _payload(),
        [
            _minimal_record(
                lifecycle_state="REJECTED",
                disposition="REJECT_FOR_CURRENT_SYSTEM",
                purpose_understood=True,
                positive_reason="proven harmful duplicate of current SSOT child X",
            )
        ],
    )
    assert validate_reconciliation_v1(payload) == []


def test_purpose_understood_without_evidence_rejected() -> None:
    payload = _with_records(
        _payload(),
        [
            _minimal_record(
                lifecycle_state="PURPOSE_UNDERSTOOD",
                purpose_understood=True,
            )
        ],
    )
    payload["records"]["ledger.yaml"]["records"][0]["understanding"]["claims"] = []
    with pytest.raises(ReconciliationValidationError, match="PURPOSE_UNDERSTOOD_WITHOUT_EVIDENCE"):
        validate_reconciliation_v1(payload)


def test_duplicate_id_rejected() -> None:
    payload = _with_records(
        _payload(),
        [
            _minimal_record(rid="RCN-000001"),
            _minimal_record(rid="RCN-000001"),
        ],
    )
    with pytest.raises(ReconciliationValidationError, match="RECORD_ID_DUPLICATE"):
        validate_reconciliation_v1(payload)


def test_malformed_id_rejected() -> None:
    payload = _with_records(_payload(), [_minimal_record(rid="RCN-1")])
    with pytest.raises(ReconciliationValidationError, match="RECORD_ID_MALFORMED"):
        validate_reconciliation_v1(payload)


def test_unknown_disposition_rejected() -> None:
    payload = _with_records(
        _payload(),
        [_minimal_record(disposition="DROP_BECAUSE_OLD", purpose_understood=True)],
    )
    with pytest.raises(ReconciliationValidationError, match="DISPOSITION_UNKNOWN"):
        validate_reconciliation_v1(payload)


def test_reject_without_positive_reason_rejected() -> None:
    payload = _with_records(
        _payload(),
        [
            _minimal_record(
                lifecycle_state="REJECTED",
                disposition="REJECT_FOR_CURRENT_SYSTEM",
                purpose_understood=True,
                positive_reason="",
            )
        ],
    )
    with pytest.raises(ReconciliationValidationError, match="REJECT_WITHOUT_POSITIVE_REASON"):
        validate_reconciliation_v1(payload)


def test_insufficient_evidence_rejected_state_rejected() -> None:
    payload = _with_records(
        _payload(),
        [
            _minimal_record(
                lifecycle_state="REJECTED",
                disposition="INSUFFICIENT_EVIDENCE",
                purpose_understood=False,
            )
        ],
    )
    with pytest.raises(
        ReconciliationValidationError, match="INSUFFICIENT_EVIDENCE_MARKED_REJECTED"
    ):
        validate_reconciliation_v1(payload)


def test_census_closed_without_exhaustion_rejected() -> None:
    payload = copy.deepcopy(_payload())
    census = payload["records"]["census_status.yaml"]
    census["census_status"] = "CENSUS_CLOSED"
    census["census_closed"] = True
    census["census_exhaustion_proven"] = False
    census["search_universe_bound"] = True
    with pytest.raises(ReconciliationValidationError, match="CENSUS_CLOSED_WITHOUT_EXHAUSTION"):
        validate_reconciliation_v1(payload)


def test_census_closed_with_unproven_coverage_surfaces_rejected() -> None:
    payload = copy.deepcopy(_payload())
    census = payload["records"]["census_status.yaml"]
    census["census_status"] = "CENSUS_CLOSED"
    census["census_closed"] = True
    census["census_exhaustion_proven"] = True
    census["search_universe_bound"] = True
    coverage = payload["records"]["coverage.yaml"]
    coverage["exhaustion_proven"] = True
    coverage["census_closed"] = True
    rows = list(coverage.get("rows") or [])
    assert rows
    rows[0]["exhaustion_proven"] = False
    rows[0]["remaining_gap"] = "forced unproven surface for contract test"
    rows[0]["exhaustion_unproven_reason"] = "forced"
    coverage["rows"] = rows
    coverage["surfaces_exhaustion_proven"] = len(rows) - 1
    coverage["surfaces_exhaustion_unproven"] = 1
    with pytest.raises(ReconciliationValidationError, match="CENSUS_CLOSED_WITH_UNPROVEN_SURFACES"):
        validate_reconciliation_v1(payload)


def test_search_anchor_counted_as_record_rejected() -> None:
    payload = copy.deepcopy(_payload())
    payload["records"]["search_anchors.yaml"]["counted_as_ledger_records"] = True
    with pytest.raises(ReconciliationValidationError, match="SEARCH_ANCHORS_COUNTED_AS_RECORDS"):
        validate_reconciliation_v1(payload)


def test_search_anchor_inside_ledger_rejected() -> None:
    record = _minimal_record()
    record["kind"] = "KNOWN_SEARCH_ANCHOR"
    payload = _with_records(_payload(), [record])
    with pytest.raises(ReconciliationValidationError, match="SEARCH_ANCHOR_IN_LEDGER"):
        validate_reconciliation_v1(payload)


def test_disposition_before_purpose_understood_rejected() -> None:
    payload = _with_records(
        _payload(),
        [
            _minimal_record(
                lifecycle_state="DISPOSITION_DECIDED",
                disposition="RETAIN_AS_IS",
                purpose_understood=False,
            )
        ],
    )
    with pytest.raises(
        ReconciliationValidationError, match="DISPOSITION_BEFORE_PURPOSE_UNDERSTOOD"
    ):
        validate_reconciliation_v1(payload)


def test_atlas_validate_includes_empty_reconciliation_tree() -> None:
    atlas = load_atlas_v1(repo_root=REPO_ROOT)
    assert validate_atlas_v1(atlas) == []


def test_atlas_validate_surfaces_reconciliation_failure() -> None:
    atlas = load_atlas_v1(repo_root=REPO_ROOT)
    broken = copy.deepcopy(_payload())
    broken["records"]["ledger.yaml"]["ledger_record_count"] = 7
    with pytest.raises(ReconciliationValidationError, match="LEDGER_RECORD_COUNT_MISMATCH"):
        validate_reconciliation_v1(broken)
    # Atlas hook uses on-disk tree; live census ledger remains valid when consistent.
    assert validate_atlas_v1(atlas) == []


def test_current_system_compared_without_overlap_rejected() -> None:
    payload = _with_records(
        _payload(),
        [
            _minimal_record(
                lifecycle_state="CURRENT_SYSTEM_COMPARED",
                purpose_understood=True,
            )
        ],
    )
    with pytest.raises(
        ReconciliationValidationError, match="CURRENT_SYSTEM_COMPARED_WITHOUT_OVERLAP"
    ):
        validate_reconciliation_v1(payload)


def test_disposition_during_current_system_compare_rejected() -> None:
    payload = _with_records(
        _payload(),
        [
            _minimal_record(
                lifecycle_state="CURRENT_SYSTEM_COMPARED",
                purpose_understood=True,
                disposition="RETAIN_AS_IS",
                positive_reason="not allowed during compare",
            )
        ],
    )
    payload["records"]["ledger.yaml"]["records"][0]["current_comparison"]["capability_overlap"] = (
        "SAME_ARTIFACT_STILL_PRESENT"
    )
    with pytest.raises(
        ReconciliationValidationError, match="DISPOSITION_DURING_CURRENT_SYSTEM_COMPARE"
    ):
        validate_reconciliation_v1(payload)


def test_hypothesis_serialized_as_fact_rejected() -> None:
    record = _minimal_record()
    record["claims"] = [
        {"claim_class": "HYPOTHESIS", "text": "maybe same as X", "used_as_fact": True}
    ]
    payload = _with_records(_payload(), [record])
    with pytest.raises(ReconciliationValidationError, match="HYPOTHESIS_SERIALIZED_AS_FACT"):
        validate_reconciliation_v1(payload)
