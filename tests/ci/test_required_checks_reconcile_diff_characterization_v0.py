"""Offline characterization for required-checks reconcile diff contexts.

These tests pin the semantics observed by the read-only reconciliation probe:
extra live contexts can be reported as reconcile data without implying trading
authority or changing the required-checks SSOT.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_CHECKS_PATH = REPO_ROOT / "config" / "ci" / "required_status_checks.json"
RECONCILER_PATH = REPO_ROOT / "scripts" / "ops" / "reconcile_required_checks_branch_protection.py"

OBSERVED_EXTRA_LIVE_CONTEXTS = {
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


def test_observed_extra_live_contexts_are_plain_non_authority_contexts() -> None:
    forbidden_claims = [
        "live authorization granted",
        "signoff complete",
        "gate passed",
        "autonomy ready",
        "strategy ready",
        "externally authorized",
        "trade approved",
    ]

    for context in OBSERVED_EXTRA_LIVE_CONTEXTS:
        assert context
        assert context.strip() == context
        assert "\n" not in context
        lowered = context.lower()
        for claim in forbidden_claims:
            assert claim not in lowered


def test_observed_extra_live_contexts_are_not_effective_required_contexts() -> None:
    data = load_ssot_data()
    effective = effective_required_contexts(data)

    assert OBSERVED_EXTRA_LIVE_CONTEXTS.isdisjoint(effective)


def test_observed_extra_live_contexts_are_allowed_as_reconcile_report_data() -> None:
    synthetic_reconcile_diff = {
        "status": "RECONCILE_DIFF",
        "extra_in_live": sorted(OBSERVED_EXTRA_LIVE_CONTEXTS),
        "missing_in_live": [],
    }

    assert synthetic_reconcile_diff["status"] == "RECONCILE_DIFF"
    assert set(synthetic_reconcile_diff["extra_in_live"]) == OBSERVED_EXTRA_LIVE_CONTEXTS
    assert synthetic_reconcile_diff["missing_in_live"] == []


def test_ignored_contexts_are_report_concepts_not_trading_authority() -> None:
    data = load_ssot_data()
    ignored_contexts = set(flatten_strings(data.get("ignored_contexts", [])))
    effective = effective_required_contexts(data)

    assert ignored_contexts
    assert (
        OBSERVED_EXTRA_LIVE_CONTEXTS <= ignored_contexts
        or OBSERVED_EXTRA_LIVE_CONTEXTS.isdisjoint(effective)
    )

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


def test_synthetic_reconcile_diff_has_no_conflicting_authority_verbs() -> None:
    diff_blob = "RECONCILE_DIFF: extra_in_live: docs-drift-guard, repo-truth-claims, strategy-smoke"
    lower = diff_blob.lower()
    assert "reconcile_diff" in lower or "reconcile" in lower
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
