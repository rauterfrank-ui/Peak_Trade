"""Offline characterization for required-checks SSOT vs live reconcile semantics.

These tests pin that previously observed extra live contexts are now part of the
canonical JSON-SSOT effective required set (synced to main branch protection),
without implying trading authority.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_CHECKS_PATH = REPO_ROOT / "config" / "ci" / "required_status_checks.json"
RECONCILER_PATH = REPO_ROOT / "scripts" / "ops" / "reconcile_required_checks_branch_protection.py"

# Contexts that were previously reported as extra_in_live before SSOT sync.
PREVIOUSLY_EXTRA_LIVE_CONTEXTS = {
    "docs-drift-guard",
    "repo-truth-claims",
    "strategy-smoke",
}


def load_ssot_data() -> dict[str, Any]:
    return json.loads(REQUIRED_CHECKS_PATH.read_text(encoding="utf-8"))


def flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        strings: list[str] = []
        for item in value:
            strings.extend(flatten_strings(item))
        return strings
    if isinstance(value, dict):
        strings = []
        for item in value.values():
            strings.extend(flatten_strings(item))
        return strings
    return []


def effective_required_contexts(data: dict[str, Any]) -> set[str]:
    required = set(flatten_strings(data.get("required_contexts", [])))
    ignored = set(flatten_strings(data.get("ignored_contexts", [])))
    return required - ignored


def test_synced_live_contexts_are_plain_non_authority_contexts() -> None:
    forbidden_claims = [
        "live authorization granted",
        "signoff complete",
        "gate passed",
        "autonomy ready",
        "strategy ready",
        "externally authorized",
        "trade approved",
    ]

    for context in PREVIOUSLY_EXTRA_LIVE_CONTEXTS:
        assert context
        assert context.strip() == context
        assert "\n" not in context
        lowered = context.lower()
        for claim in forbidden_claims:
            assert claim not in lowered


def test_previously_extra_live_contexts_are_now_effective_required() -> None:
    data = load_ssot_data()
    effective = effective_required_contexts(data)
    ignored = set(flatten_strings(data.get("ignored_contexts", [])))

    assert PREVIOUSLY_EXTRA_LIVE_CONTEXTS <= effective
    assert PREVIOUSLY_EXTRA_LIVE_CONTEXTS.isdisjoint(ignored)


def test_required_and_ignored_have_no_intersection_in_ssot() -> None:
    data = load_ssot_data()
    required = set(flatten_strings(data.get("required_contexts", [])))
    ignored = set(flatten_strings(data.get("ignored_contexts", [])))
    assert required.isdisjoint(ignored)


def test_ignored_contexts_are_report_concepts_not_trading_authority() -> None:
    data = load_ssot_data()
    ignored_contexts = set(flatten_strings(data.get("ignored_contexts", [])))

    serialized = "\n".join(sorted(ignored_contexts)).lower()
    forbidden_claims = [
        "live authorization granted",
        "signoff complete",
        "gate passed",
        "autonomy ready",
        "strategy ready",
        "trade approved",
    ]
    for claim in forbidden_claims:
        assert claim not in serialized


def test_synthetic_reconcile_match_blob_has_no_conflicting_authority_verbs() -> None:
    diff_blob = (
        "RECONCILE_MATCH: effective required contexts match live protection "
        "(docs-drift-guard, repo-truth-claims, strategy-smoke included)"
    )
    lower = diff_blob.lower()
    assert "reconcile_match" in lower or "reconcile" in lower
    for bad in (
        "live authorization granted",
        "gate passed",
        "signoff complete",
    ):
        assert bad not in lower


def test_reconciler_source_can_be_parsed_offline_without_github_calls() -> None:
    source = RECONCILER_PATH.read_text(encoding="utf-8")

    assert "extra_in_live" in source
    assert "missing_in_live" in source
    assert "required_status_checks" in source
    assert "branch protection" in source.lower() or "branch_protection" in source.lower()


def test_this_characterization_does_not_call_github_or_gh_cli() -> None:
    this_file = Path(__file__).read_text(encoding="utf-8").lower()

    # Build with concat so the forbidden tokens are not self-triggering in this source.
    forbidden_runtime_calls = [
        "".join(("sub", "process", ".", "run")),
        "".join(("g", "h ")),
        "".join(("api", ".", "github", ".", "com")),
        "github" + " " + "api",
        "branch" + " " + "protection" + " " + "api",
    ]

    for call in forbidden_runtime_calls:
        assert call not in this_file
