"""Regressions for reality-check defects D1–D5. No full-tree census."""

from __future__ import annotations

from pathlib import Path

from scripts.ops.current_full_stack_semantic_explorer_v1.budget_v1 import BudgetV1
from scripts.ops.current_full_stack_semantic_explorer_v1.git_objects_v1 import list_entries_v1
from scripts.ops.current_full_stack_semantic_explorer_v1.run_v1 import run_explorer_v1
from tests.ops.test_current_full_stack_semantic_explorer_v1 import _budget, _claims, _fixture

COMMIT = "13181496178534ddbeba1d0054bbc6728624a1bd"
REPO = Path(__file__).resolve().parents[2]
NOTIFICATIONS = ("src/notifications",)


def test_d1_prefix_selects_only_the_named_slice() -> None:
    result = run_explorer_v1(
        REPO,
        COMMIT,
        path_prefixes=NOTIFICATIONS,
        budget=BudgetV1(max_files=40),
    )
    files = [
        claim["subject"] for claim in result["slices"][0]["claims"] if claim["predicate"] == "FILE"
    ]
    assert result["selection_mode"] == "BOUNDED_SLICE"
    assert result["run_status"] == "PASS"
    assert result["paths_indexed"] == 3
    assert result["paths_read"] == 3
    assert files == [
        "src/notifications/__init__.py",
        "src/notifications/base.py",
        "src/notifications/slack.py",
    ]


def test_d1_budget_counts_the_slice_not_the_repository(tmp_path: Path) -> None:
    repo, sha = _fixture(tmp_path)
    result = run_explorer_v1(
        repo,
        sha,
        path_prefixes=("sample_pkg",),
        budget=BudgetV1(max_files=1, max_seconds=20),
    )
    assert result["selection_mode"] == "BOUNDED_SLICE"
    assert result["paths_indexed"] > 1
    assert result["paths_read"] == 1
    assert result["run_status"] == "INCOMPLETE"


def test_d2_real_notification_modules_keep_only_resolved_calls() -> None:
    result = run_explorer_v1(
        REPO,
        COMMIT,
        path_prefixes=NOTIFICATIONS,
        budget=BudgetV1(max_files=40),
    )
    claims = _claims(result)
    assert any(
        claim["predicate"] == "DEFINES"
        and claim["subject"] == "src/notifications/slack.py::SlackNotifier.send"
        for claim in claims
    )
    calls = [
        claim
        for claim in claims
        if claim["predicate"] == "CALLS"
        and claim["subject"] == "src/notifications/slack.py::SlackNotifier.send"
        and claim["object"] == "src/notifications/slack.py::_deny_external_effect"
    ]
    assert len(calls) == 1
    assert calls[0]["status"] == "PROVEN"
    assert calls[0]["evidence_class"] == "STATIC"
    assert any("src/notifications/slack.py:" in ref for ref in calls[0]["evidence_refs"])
    assert any(
        claim["predicate"] == "DYNAMIC_TARGET"
        and claim["subject"] == "src/notifications/slack.py::SlackNotifier.send"
        and claim["status"] == "UNPROVEN"
        for claim in claims
    )
    assert not any(
        claim["predicate"] == "CALLS"
        and claim["object"].endswith("::_format_alert_text")
        and claim["status"] == "PROVEN"
        for claim in claims
    )


def test_d3_missing_capture_remains_unproven_after_budget_abort(tmp_path: Path) -> None:
    repo, sha = _fixture(tmp_path)
    result = run_explorer_v1(repo, sha, budget=BudgetV1(max_files=1, max_seconds=20))
    missing = [
        claim
        for claim in result["slices"][3]["claims"]
        if "CAPTURE_NOT_SUPPLIED" in claim["unknowns"]
    ]
    assert result["run_status"] == "INCOMPLETE"
    assert len(missing) == 1
    assert missing[0]["predicate"] == "RUNTIME_CAPTURE"
    assert missing[0]["status"] == "UNPROVEN"
    assert missing[0]["evidence_class"] == "RUNTIME_OBSERVED"


def test_d4_indexes_the_selected_tree_once(tmp_path: Path, monkeypatch) -> None:
    repo, sha = _fixture(tmp_path)
    calls: list[tuple[object, ...]] = []
    original = list_entries_v1

    def _counted(repo_path, commit, prefixes=None):
        calls.append((repo_path, commit, prefixes))
        return original(repo_path, commit, prefixes)

    monkeypatch.setattr(
        "scripts.ops.current_full_stack_semantic_explorer_v1.run_v1.list_entries_v1",
        _counted,
    )
    run_explorer_v1(repo, sha, path_prefixes=("sample_pkg/mod_a.py",), budget=_budget())
    assert len(calls) == 1
    assert calls[0][2] == ("sample_pkg/mod_a.py",)


def test_d4_prefix_listing_stays_inside_the_slice() -> None:
    entries = list_entries_v1(REPO, COMMIT, NOTIFICATIONS)
    assert [entry.path for entry in entries] == [
        "src/notifications/__init__.py",
        "src/notifications/base.py",
        "src/notifications/slack.py",
    ]


def test_d5_call_groups_are_not_promoted_to_functional_layers(tmp_path: Path) -> None:
    repo, sha = _fixture(tmp_path)
    claims = _claims(run_explorer_v1(repo, sha, budget=_budget()))
    members = [claim for claim in claims if claim["predicate"] == "CALL_GROUP_MEMBER"]
    assert members
    assert all(claim["status"] == "PROVEN" for claim in members)
    assert all("TECHNICAL_CALL_GROUP" in claim["unknowns"] for claim in members)
    functional = [claim for claim in claims if claim["predicate"] == "FUNCTIONAL_LAYER"]
    assert functional
    assert all(claim["status"] == "UNPROVEN" for claim in functional)
    assert all("NO_FUNCTIONAL_EVIDENCE" in claim["unknowns"] for claim in functional)
    assert not any(claim["predicate"] in {"LAYER_MEMBER", "LAYER_LINK"} for claim in claims)
    assert not any(
        claim["status"] == "PROVEN"
        and "AUTHORITY" in claim["predicate"]
        and claim["object"] != "NONE"
        for claim in claims
        if claim["subject"].endswith("parent_safety_guardian.py")
    )


def test_real_notification_slice_is_deterministic() -> None:
    budget = BudgetV1(max_files=40)
    first = run_explorer_v1(REPO, COMMIT, path_prefixes=NOTIFICATIONS, budget=budget)
    second = run_explorer_v1(REPO, COMMIT, path_prefixes=NOTIFICATIONS, budget=budget)
    assert first == second
    assert first["external_effects"] == 0
    assert not any(
        claim["predicate"] == "FUNCTIONAL_LAYER" and claim["status"] == "PROVEN"
        for claim in _claims(first)
    )
    assert not any(
        claim["status"] == "PROVEN" and claim["predicate"].endswith("AUTHORITY")
        for claim in _claims(first)
        if claim["predicate"]
        in {"AUTHORITY", "DECISION_AUTHORITY", "EXECUTION_AUTHORITY", "SAFETY_AUTHORITY"}
    )
