"""Synthetic Pre-Live package status read-model tests.

These tests model a future read-only Pre-Live Package Status / Gap Report
surface. They do not import production report code, read real registries, read
generated artifacts, close sessions, or authorize live trading.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Literal


CONTRACT = "pre_live_package_status_v0"

AUTHORITY_FLAGS = {
    "live_authorization": False,
    "bounded_pilot_approval": False,
    "closeout_approval": False,
    "gate_passage": False,
    "strategy_readiness": False,
    "autonomy_readiness": False,
    "external_authority_completion": False,
}

Status = Literal["NOT_READY", "BLOCKED", "REVIEW_ONLY", "READY_FOR_EXTERNAL_REVIEW"]


@dataclass(frozen=True)
class SyntheticPreLiveInputs:
    docs_present: dict[str, bool]
    read_models_available: dict[str, bool]
    session_registry_summary: dict[str, int]
    open_bounded_pilot_sessions: int
    closeout_lifecycle_status: str
    blocker_states: dict[str, str]
    evidence_package_complete: bool
    external_decision_present: bool = False


def build_pre_live_package_status_v0(inputs: SyntheticPreLiveInputs) -> dict[str, object]:
    missing_or_open_items: list[str] = []
    blockers: list[str] = []

    missing_docs = sorted(key for key, present in inputs.docs_present.items() if not present)
    for doc in missing_docs:
        missing_or_open_items.append(f"docs.{doc}.missing")

    missing_read_models = sorted(
        key for key, present in inputs.read_models_available.items() if not present
    )
    for read_model in missing_read_models:
        missing_or_open_items.append(f"read_models.{read_model}.missing")

    if not inputs.evidence_package_complete:
        missing_or_open_items.append("evidence_package.incomplete")
        blockers.append("GLB-003")

    if inputs.open_bounded_pilot_sessions > 0:
        missing_or_open_items.append("bounded_pilot.open_sessions_present")
        blockers.append("GLB-018")

    if inputs.closeout_lifecycle_status != "TERMINAL_CLEAN":
        missing_or_open_items.append("closeout_lifecycle.non_terminal_or_partial")
        blockers.append("GLB-018")

    for blocker_id, state in sorted(inputs.blocker_states.items()):
        if state in {"OPEN", "BLOCKED"}:
            blockers.append(blocker_id)
            missing_or_open_items.append(f"blockers.{blocker_id}.{state.lower()}")

    unique_blockers = sorted(set(blockers))
    unique_missing = sorted(set(missing_or_open_items))

    if unique_blockers or missing_docs or missing_read_models:
        status: Status = "BLOCKED"
    elif not inputs.evidence_package_complete:
        status = "NOT_READY"
    elif not inputs.external_decision_present:
        status = "READY_FOR_EXTERNAL_REVIEW"
    else:
        status = "REVIEW_ONLY"

    return {
        "contract": CONTRACT,
        "non_authorizing": True,
        "status": status,
        "docs_present": dict(sorted(inputs.docs_present.items())),
        "read_models_available": dict(sorted(inputs.read_models_available.items())),
        "session_registry_summary": dict(sorted(inputs.session_registry_summary.items())),
        "open_bounded_pilot_sessions": inputs.open_bounded_pilot_sessions,
        "closeout_lifecycle_status": inputs.closeout_lifecycle_status,
        "blocker_states": dict(sorted(inputs.blocker_states.items())),
        "blockers": unique_blockers,
        "missing_or_open_items": unique_missing,
        "authority_boundary": dict(AUTHORITY_FLAGS),
    }


def baseline_inputs(**overrides: object) -> SyntheticPreLiveInputs:
    data = {
        "docs_present": {
            "go_live_roadmap": True,
            "first_live_execution_sequence": True,
            "pilot_runbook": True,
            "blocker_register": True,
        },
        "read_models_available": {
            "readiness_ladder": True,
            "gate_status_index": True,
            "session_review_pack": True,
        },
        "session_registry_summary": {"total": 42, "completed": 27, "failed": 7, "started": 5},
        "open_bounded_pilot_sessions": 0,
        "closeout_lifecycle_status": "TERMINAL_CLEAN",
        "blocker_states": {},
        "evidence_package_complete": True,
        "external_decision_present": False,
    }
    data.update(overrides)
    return SyntheticPreLiveInputs(**data)  # type: ignore[arg-type]


def assert_authority_false(payload: dict[str, object]) -> None:
    assert payload["authority_boundary"] == AUTHORITY_FLAGS


def test_all_docs_present_but_open_bounded_pilot_sessions_blocks_readiness() -> None:
    payload = build_pre_live_package_status_v0(
        baseline_inputs(
            open_bounded_pilot_sessions=5, closeout_lifecycle_status="PARTIAL_NON_TERMINAL"
        )
    )

    assert payload["status"] == "BLOCKED"
    assert "bounded_pilot.open_sessions_present" in payload["missing_or_open_items"]
    assert "GLB-018" in payload["blockers"]
    assert_authority_false(payload)


def test_partial_closeout_lifecycle_remains_blocker() -> None:
    payload = build_pre_live_package_status_v0(
        baseline_inputs(closeout_lifecycle_status="PARTIAL_NON_TERMINAL")
    )

    assert payload["status"] == "BLOCKED"
    assert "closeout_lifecycle.non_terminal_or_partial" in payload["missing_or_open_items"]
    assert "GLB-018" in payload["blockers"]
    assert_authority_false(payload)


def test_missing_pre_live_package_evidence_is_not_ready() -> None:
    payload = build_pre_live_package_status_v0(baseline_inputs(evidence_package_complete=False))

    assert payload["status"] == "BLOCKED"
    assert "evidence_package.incomplete" in payload["missing_or_open_items"]
    assert "GLB-003" in payload["blockers"]
    assert_authority_false(payload)


def test_all_blockers_closed_without_external_decision_is_ready_for_external_review_only() -> None:
    payload = build_pre_live_package_status_v0(
        baseline_inputs(
            blocker_states={"GLB-001": "CLOSED", "GLB-003": "CLOSED"},
            external_decision_present=False,
        )
    )

    assert payload["status"] == "READY_FOR_EXTERNAL_REVIEW"
    assert payload["blockers"] == []
    assert payload["missing_or_open_items"] == []
    assert_authority_false(payload)


def test_external_decision_present_still_remains_review_only_not_live_ready() -> None:
    payload = build_pre_live_package_status_v0(
        baseline_inputs(
            blocker_states={"GLB-001": "CLOSED"},
            external_decision_present=True,
        )
    )

    assert payload["status"] == "REVIEW_ONLY"
    assert payload["non_authorizing"] is True
    assert_authority_false(payload)


def test_status_report_does_not_close_open_blockers_automatically() -> None:
    payload = build_pre_live_package_status_v0(
        baseline_inputs(blocker_states={"GLB-008": "BLOCKED", "GLB-014": "OPEN"})
    )

    assert payload["status"] == "BLOCKED"
    assert payload["blocker_states"] == {"GLB-008": "BLOCKED", "GLB-014": "OPEN"}
    assert payload["blockers"] == ["GLB-008", "GLB-014"]
    assert "blockers.GLB-008.blocked" in payload["missing_or_open_items"]
    assert "blockers.GLB-014.open" in payload["missing_or_open_items"]


def test_serialized_output_contains_no_unqualified_authority_claims() -> None:
    payloads = [
        build_pre_live_package_status_v0(baseline_inputs()),
        build_pre_live_package_status_v0(baseline_inputs(open_bounded_pilot_sessions=5)),
        build_pre_live_package_status_v0(baseline_inputs(external_decision_present=True)),
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
    ]

    for payload in payloads:
        serialized = json.dumps(payload, sort_keys=True).lower()
        for claim in forbidden_claims:
            assert claim not in serialized


def test_this_read_model_test_does_not_read_real_artifact_locations() -> None:
    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_fragments = [
        "/".join(["reports", "experiments", "live_sessions"]),
        "/".join(["out", "ops"]),
        "/".join(["execution_events", "sessions"]),
        "_".join(["live", "session", "registry"]),
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source_text
