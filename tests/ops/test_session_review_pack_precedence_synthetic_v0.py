"""Synthetic tests for Session Review Pack precedence rules.

These tests intentionally do not bind real sessions, registries, manifests, or
paper/live artifacts. They mirror the docs-only precedence model with local
synthetic fixtures so future binding work has a safe fail-closed baseline.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SourceState(str, Enum):
    OK = "ok"
    MISSING = "missing"
    UNRESOLVED = "unresolved"
    NEEDS_REVIEW = "needs_review"
    NOT_APPLICABLE = "not_applicable"


class SourceClass(str, Enum):
    RUNTIME_ARTIFACT = "runtime_artifact"
    PROVENANCE = "provenance"
    EVIDENCE_INDEX = "evidence_index"
    REGISTRY = "registry"
    READINESS_HANDOFF_PACKET = "readiness_handoff_packet"
    OPERATOR_NOTE = "operator_note"
    DASHBOARD_OBSERVER_SUMMARY = "dashboard_observer_summary"
    LEARNING_LOOP_FEEDBACK = "learning_loop_feedback"
    AI_SUMMARY = "ai_summary"


PRECEDENCE_RANK: dict[SourceClass, int] = {
    SourceClass.RUNTIME_ARTIFACT: 1,
    SourceClass.PROVENANCE: 2,
    SourceClass.EVIDENCE_INDEX: 3,
    SourceClass.REGISTRY: 4,
    SourceClass.READINESS_HANDOFF_PACKET: 5,
    SourceClass.OPERATOR_NOTE: 6,
    SourceClass.DASHBOARD_OBSERVER_SUMMARY: 7,
    SourceClass.LEARNING_LOOP_FEEDBACK: 8,
    SourceClass.AI_SUMMARY: 9,
}

NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "live_authorization": False,
    "signoff_complete": False,
    "gate_passed": False,
    "strategy_ready": False,
    "autonomy_ready": False,
}


@dataclass(frozen=True)
class SyntheticSource:
    source_class: SourceClass
    state: SourceState
    value: str | None = None


def classify_missing(source: SyntheticSource) -> SourceState:
    if source.state == SourceState.NOT_APPLICABLE:
        return SourceState.NOT_APPLICABLE
    if source.value is None:
        return SourceState.MISSING
    return source.state


def resolve_sources(sources: list[SyntheticSource]) -> dict[str, object]:
    normalized = [
        SyntheticSource(
            source_class=source.source_class,
            state=classify_missing(source),
            value=source.value,
        )
        for source in sources
    ]

    active = [
        source
        for source in normalized
        if source.state not in {SourceState.MISSING, SourceState.NOT_APPLICABLE}
    ]

    if not active:
        return {
            "state": SourceState.MISSING,
            "selected_source": None,
            "authority_boundary": dict(NON_AUTHORIZING_FLAGS),
        }

    values = {source.value for source in active}
    if len(values) > 1:
        return {
            "state": SourceState.UNRESOLVED,
            "selected_source": None,
            "authority_boundary": dict(NON_AUTHORIZING_FLAGS),
        }

    selected = min(active, key=lambda s: PRECEDENCE_RANK[s.source_class])
    return {
        "state": selected.state,
        "selected_source": selected.source_class,
        "authority_boundary": dict(NON_AUTHORIZING_FLAGS),
    }


def assert_non_authorizing(result: dict[str, object]) -> None:
    ab = result["authority_boundary"]
    assert isinstance(ab, dict)
    assert ab == NON_AUTHORIZING_FLAGS
    assert all(value is False for value in ab.values())


def test_precedence_rank_order_is_stable_and_unique() -> None:
    assert list(PRECEDENCE_RANK) == [
        SourceClass.RUNTIME_ARTIFACT,
        SourceClass.PROVENANCE,
        SourceClass.EVIDENCE_INDEX,
        SourceClass.REGISTRY,
        SourceClass.READINESS_HANDOFF_PACKET,
        SourceClass.OPERATOR_NOTE,
        SourceClass.DASHBOARD_OBSERVER_SUMMARY,
        SourceClass.LEARNING_LOOP_FEEDBACK,
        SourceClass.AI_SUMMARY,
    ]
    assert sorted(PRECEDENCE_RANK.values()) == list(range(1, 10))


def test_runtime_artifact_has_highest_rank_but_no_authority() -> None:
    result = resolve_sources(
        [
            SyntheticSource(SourceClass.RUNTIME_ARTIFACT, SourceState.OK, "same"),
            SyntheticSource(SourceClass.PROVENANCE, SourceState.OK, "same"),
        ]
    )

    assert result["state"] == SourceState.OK
    assert result["selected_source"] == SourceClass.RUNTIME_ARTIFACT
    assert_non_authorizing(result)


def test_ai_summary_has_lowest_rank_and_never_wins_conflicts() -> None:
    same_value_result = resolve_sources(
        [
            SyntheticSource(SourceClass.PROVENANCE, SourceState.OK, "same"),
            SyntheticSource(SourceClass.AI_SUMMARY, SourceState.OK, "same"),
        ]
    )
    conflict_result = resolve_sources(
        [
            SyntheticSource(SourceClass.PROVENANCE, SourceState.OK, "source-truth"),
            SyntheticSource(SourceClass.AI_SUMMARY, SourceState.OK, "ai-claim"),
        ]
    )

    assert same_value_result["selected_source"] == SourceClass.PROVENANCE
    assert conflict_result["state"] == SourceState.UNRESOLVED
    assert conflict_result["selected_source"] is None
    assert_non_authorizing(same_value_result)
    assert_non_authorizing(conflict_result)


def test_missing_source_never_becomes_ok() -> None:
    result = resolve_sources(
        [
            SyntheticSource(SourceClass.RUNTIME_ARTIFACT, SourceState.OK, None),
        ]
    )

    assert result["state"] == SourceState.MISSING
    assert result["state"] != SourceState.OK
    assert_non_authorizing(result)


def test_conflicting_sources_fail_closed_to_unresolved() -> None:
    result = resolve_sources(
        [
            SyntheticSource(SourceClass.RUNTIME_ARTIFACT, SourceState.OK, "artifact"),
            SyntheticSource(SourceClass.PROVENANCE, SourceState.OK, "provenance"),
        ]
    )

    assert result["state"] == SourceState.UNRESOLVED
    assert result["selected_source"] is None
    assert_non_authorizing(result)


def test_operator_note_does_not_override_runtime_artifact() -> None:
    result = resolve_sources(
        [
            SyntheticSource(SourceClass.RUNTIME_ARTIFACT, SourceState.OK, "same"),
            SyntheticSource(SourceClass.OPERATOR_NOTE, SourceState.OK, "same"),
        ]
    )

    assert result["selected_source"] == SourceClass.RUNTIME_ARTIFACT
    assert_non_authorizing(result)


def test_dashboard_observer_summary_does_not_override_runtime_artifact() -> None:
    result = resolve_sources(
        [
            SyntheticSource(SourceClass.RUNTIME_ARTIFACT, SourceState.OK, "same"),
            SyntheticSource(SourceClass.DASHBOARD_OBSERVER_SUMMARY, SourceState.OK, "same"),
        ]
    )

    assert result["selected_source"] == SourceClass.RUNTIME_ARTIFACT
    assert_non_authorizing(result)


def test_evidence_index_is_navigation_not_truth_by_itself() -> None:
    result = resolve_sources(
        [
            SyntheticSource(SourceClass.EVIDENCE_INDEX, SourceState.NEEDS_REVIEW, "ref-only"),
        ]
    )

    assert result["state"] == SourceState.NEEDS_REVIEW
    assert result["selected_source"] == SourceClass.EVIDENCE_INDEX
    assert_non_authorizing(result)


def test_all_states_remain_non_authorizing() -> None:
    for state in SourceState:
        result = resolve_sources(
            [
                SyntheticSource(
                    SourceClass.RUNTIME_ARTIFACT,
                    state,
                    None if state == SourceState.MISSING else "value",
                )
            ]
        )

        assert_non_authorizing(result)


def test_serialized_result_has_no_positive_authority_claims() -> None:
    result = resolve_sources(
        [
            SyntheticSource(SourceClass.RUNTIME_ARTIFACT, SourceState.OK, "same"),
            SyntheticSource(SourceClass.PROVENANCE, SourceState.OK, "same"),
        ]
    )

    serialized = repr(result).lower()
    forbidden_claims = [
        "live authorization granted",
        "signoff complete",
        "gate passed",
        "strategy ready",
        "autonomy ready",
        "externally authorized",
        "trade approved",
    ]

    for claim in forbidden_claims:
        assert claim not in serialized
