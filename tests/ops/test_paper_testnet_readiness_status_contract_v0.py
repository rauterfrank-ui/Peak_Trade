"""Synthetic Paper/Testnet readiness status contract tests.

These tests characterize a future non-authorizing readiness status payload.
They do not import production report code, read real artifacts, mutate evidence,
or authorize live trading.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Literal


CONTRACT = "paper_testnet_readiness_status_v0"

Status = Literal["BLOCKED", "NOT_READY", "READY_FOR_REVIEW", "REVIEW_ONLY"]

AUTHORITY_FLAGS = {
    "live_authorization": False,
    "bounded_pilot_approval": False,
    "closeout_approval": False,
    "gate_passage": False,
    "strategy_readiness": False,
    "autonomy_readiness": False,
    "external_authority_completion": False,
}


@dataclass(frozen=True)
class SyntheticEvidenceSection:
    evidence_present: bool
    robustness_present: bool
    stress_present: bool


@dataclass(frozen=True)
class SyntheticPaperTestnetInputs:
    paper: SyntheticEvidenceSection
    testnet: SyntheticEvidenceSection
    external_review_decision_present: bool = False


def build_paper_testnet_readiness_status_v0(
    inputs: SyntheticPaperTestnetInputs,
) -> dict[str, object]:
    blockers: list[str] = []
    missing_or_open_items: list[str] = []

    if not inputs.paper.evidence_present:
        blockers.append("paper.evidence_missing")
        missing_or_open_items.append("paper.evidence_missing")
    if not inputs.paper.robustness_present:
        blockers.append("paper.robustness_missing")
        missing_or_open_items.append("paper.robustness_missing")
    if not inputs.paper.stress_present:
        blockers.append("paper.stress_missing")
        missing_or_open_items.append("paper.stress_missing")

    if not inputs.testnet.evidence_present:
        blockers.append("testnet.evidence_missing")
        missing_or_open_items.append("testnet.evidence_missing")
    if not inputs.testnet.robustness_present:
        blockers.append("testnet.robustness_missing")
        missing_or_open_items.append("testnet.robustness_missing")
    if not inputs.testnet.stress_present:
        blockers.append("testnet.stress_missing")
        missing_or_open_items.append("testnet.stress_missing")

    if blockers:
        status: Status = "BLOCKED"
    elif not inputs.external_review_decision_present:
        status = "READY_FOR_REVIEW"
    else:
        status = "REVIEW_ONLY"

    return {
        "contract": CONTRACT,
        "non_authorizing": True,
        "status": status,
        "paper": {
            "evidence_present": inputs.paper.evidence_present,
            "robustness_present": inputs.paper.robustness_present,
            "stress_present": inputs.paper.stress_present,
        },
        "testnet": {
            "evidence_present": inputs.testnet.evidence_present,
            "robustness_present": inputs.testnet.robustness_present,
            "stress_present": inputs.testnet.stress_present,
        },
        "blockers": sorted(set(blockers)),
        "missing_or_open_items": sorted(set(missing_or_open_items)),
        "external_review_decision_present": inputs.external_review_decision_present,
        "authority_boundary": dict(AUTHORITY_FLAGS),
    }


def complete_section() -> SyntheticEvidenceSection:
    return SyntheticEvidenceSection(
        evidence_present=True, robustness_present=True, stress_present=True
    )


def assert_authority_false(payload: dict[str, object]) -> None:
    assert payload["non_authorizing"] is True
    assert payload["authority_boundary"] == AUTHORITY_FLAGS


def test_complete_paper_but_missing_testnet_is_blocked_not_live_ready() -> None:
    payload = build_paper_testnet_readiness_status_v0(
        SyntheticPaperTestnetInputs(
            paper=complete_section(),
            testnet=SyntheticEvidenceSection(
                evidence_present=False,
                robustness_present=False,
                stress_present=False,
            ),
        )
    )

    assert payload["status"] == "BLOCKED"
    assert "testnet.evidence_missing" in payload["blockers"]
    assert "testnet.robustness_missing" in payload["blockers"]
    assert "testnet.stress_missing" in payload["blockers"]
    assert_authority_false(payload)


def test_complete_paper_and_testnet_without_external_decision_is_review_only_boundary() -> None:
    payload = build_paper_testnet_readiness_status_v0(
        SyntheticPaperTestnetInputs(
            paper=complete_section(),
            testnet=complete_section(),
            external_review_decision_present=False,
        )
    )

    assert payload["status"] == "READY_FOR_REVIEW"
    assert payload["blockers"] == []
    assert payload["missing_or_open_items"] == []
    assert_authority_false(payload)


def test_external_decision_present_still_does_not_grant_live_authority() -> None:
    payload = build_paper_testnet_readiness_status_v0(
        SyntheticPaperTestnetInputs(
            paper=complete_section(),
            testnet=complete_section(),
            external_review_decision_present=True,
        )
    )

    assert payload["status"] == "REVIEW_ONLY"
    assert_authority_false(payload)


def test_missing_paper_evidence_blocks() -> None:
    payload = build_paper_testnet_readiness_status_v0(
        SyntheticPaperTestnetInputs(
            paper=SyntheticEvidenceSection(
                evidence_present=False,
                robustness_present=True,
                stress_present=True,
            ),
            testnet=complete_section(),
        )
    )

    assert payload["status"] == "BLOCKED"
    assert payload["blockers"] == ["paper.evidence_missing"]


def test_missing_testnet_evidence_blocks() -> None:
    payload = build_paper_testnet_readiness_status_v0(
        SyntheticPaperTestnetInputs(
            paper=complete_section(),
            testnet=SyntheticEvidenceSection(
                evidence_present=False,
                robustness_present=True,
                stress_present=True,
            ),
        )
    )

    assert payload["status"] == "BLOCKED"
    assert payload["blockers"] == ["testnet.evidence_missing"]


def test_missing_robustness_and_stress_evidence_blocks() -> None:
    payload = build_paper_testnet_readiness_status_v0(
        SyntheticPaperTestnetInputs(
            paper=SyntheticEvidenceSection(
                evidence_present=True,
                robustness_present=False,
                stress_present=False,
            ),
            testnet=SyntheticEvidenceSection(
                evidence_present=True,
                robustness_present=False,
                stress_present=False,
            ),
        )
    )

    assert payload["status"] == "BLOCKED"
    assert payload["blockers"] == [
        "paper.robustness_missing",
        "paper.stress_missing",
        "testnet.robustness_missing",
        "testnet.stress_missing",
    ]


def test_status_contract_separates_paper_and_testnet_evidence() -> None:
    payload = build_paper_testnet_readiness_status_v0(
        SyntheticPaperTestnetInputs(paper=complete_section(), testnet=complete_section())
    )

    assert payload["paper"] == {
        "evidence_present": True,
        "robustness_present": True,
        "stress_present": True,
    }
    assert payload["testnet"] == {
        "evidence_present": True,
        "robustness_present": True,
        "stress_present": True,
    }


def test_serialized_output_contains_no_unqualified_authority_claims() -> None:
    payloads = [
        build_paper_testnet_readiness_status_v0(
            SyntheticPaperTestnetInputs(paper=complete_section(), testnet=complete_section())
        ),
        build_paper_testnet_readiness_status_v0(
            SyntheticPaperTestnetInputs(
                paper=complete_section(),
                testnet=complete_section(),
                external_review_decision_present=True,
            )
        ),
    ]

    forbidden_claims = [
        "live authorization granted",
        "bounded pilot approved",
        "closeout approved",
        "signoff complete",
        "gate passed",
        "strategy ready",
        "autonomy ready",
        "externally authorized",
        "approved for live",
        "trade approved",
        "live ready",
    ]

    for payload in payloads:
        serialized = json.dumps(payload, sort_keys=True).lower()
        for claim in forbidden_claims:
            assert claim not in serialized


def test_this_status_contract_test_does_not_read_real_artifact_locations() -> None:
    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "/".join(["reports", "experiments", "live_sessions"]),
        "/".join(["out", "ops"]),
        "/".join(["execution_events", "sessions"]),
        "_".join(["paper", "testnet", "artifact"]),
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source_text
