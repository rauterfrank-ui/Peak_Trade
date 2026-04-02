"""Unit tests for scripts/ops/ensure_truth_branch_protection.py (mocked gh, no network)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "scripts" / "ops"))

import ensure_truth_branch_protection as et  # noqa: E402


def test_collect_context_names_merges_contexts_and_checks():
    data = {
        "required_status_checks": {
            "strict": False,
            "contexts": ["Lint Gate", "docs-drift-guard"],
            "checks": [{"context": "audit", "app_id": 1}],
        }
    }
    assert et.collect_context_names(data) == ["Lint Gate", "audit", "docs-drift-guard"]


def test_missing_truth_checks():
    assert et.missing_truth_checks(["docs-drift-guard"]) == ["repo-truth-claims"]
    assert et.missing_truth_checks(["docs-drift-guard", "repo-truth-claims"]) == []


def test_build_put_body_preserves_strict_and_merges_contexts():
    get_data = {
        "required_status_checks": {
            "strict": True,
            "contexts": ["Lint Gate"],
            "checks": [],
        },
        "enforce_admins": {"enabled": True, "url": "x"},
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": False,
            "require_code_owner_reviews": False,
            "required_approving_review_count": 0,
        },
        "required_linear_history": {"enabled": False},
        "allow_force_pushes": {"enabled": False},
        "allow_deletions": {"enabled": False},
        "block_creations": {"enabled": False},
        "required_conversation_resolution": {"enabled": False},
        "lock_branch": {"enabled": False},
        "allow_fork_syncing": {"enabled": False},
        "required_signatures": {"enabled": False},
    }
    merged = ["Lint Gate", "docs-drift-guard", "repo-truth-claims"]
    body = et.build_put_body(get_data, merged)
    assert body["required_status_checks"]["strict"] is True
    assert body["required_status_checks"]["contexts"] == merged
    assert body["enforce_admins"] is True


def test_run_check_exits_0_when_both_present(capsys):
    sample = {
        "required_status_checks": {
            "contexts": ["docs-drift-guard", "repo-truth-claims", "Lint Gate"],
            "checks": [],
        }
    }

    def fake_fetch(*_a, **_k):
        return 0, sample, ""

    with patch.object(et, "fetch_protection", fake_fetch):
        assert et.run_check("o", "r", "main") == 0
    out = capsys.readouterr().out
    assert "Truth-Gates Required Checks vorhanden" in out


def test_run_check_exits_1_when_missing(capsys):
    sample = {
        "required_status_checks": {
            "contexts": ["Lint Gate"],
            "checks": [],
        }
    }

    def fake_fetch(*_a, **_k):
        return 0, sample, ""

    with patch.object(et, "fetch_protection", fake_fetch):
        assert et.run_check("o", "r", "main") == 1
    out = capsys.readouterr().out
    assert "repo-truth-claims" in out


def test_run_apply_noop_when_already_complete(capsys):
    sample = {
        "required_status_checks": {
            "strict": False,
            "contexts": ["docs-drift-guard", "repo-truth-claims"],
            "checks": [],
        },
        "enforce_admins": {"enabled": False},
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": False,
            "require_code_owner_reviews": False,
            "required_approving_review_count": 0,
        },
    }

    def fake_fetch(*_a, **_k):
        return 0, sample, ""

    with patch.object(et, "fetch_protection", fake_fetch):
        assert et.run_apply("o", "r", "main") == 0
    assert "nichts zu tun" in capsys.readouterr().out


def test_run_apply_calls_put_when_missing():
    sample = {
        "required_status_checks": {
            "strict": False,
            "contexts": ["Lint Gate"],
            "checks": [],
        },
        "enforce_admins": {"enabled": True},
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": False,
            "require_code_owner_reviews": False,
            "required_approving_review_count": 0,
        },
        "required_linear_history": {"enabled": False},
        "allow_force_pushes": {"enabled": False},
        "allow_deletions": {"enabled": False},
        "block_creations": {"enabled": False},
        "required_conversation_resolution": {"enabled": False},
        "lock_branch": {"enabled": False},
        "allow_fork_syncing": {"enabled": False},
        "required_signatures": {"enabled": False},
    }
    put_calls: list[dict] = []

    def fake_gh_api(method: str, path: str, *, body=None):
        if method == "PUT":
            put_calls.append(body or {})
            return 0, "{}", ""
        raise AssertionError(method)

    with patch.object(et, "fetch_protection", lambda *a, **k: (0, sample, "")):
        with patch.object(et, "_gh_api", fake_gh_api):
            assert et.run_apply("o", "r", "main") == 0
    assert len(put_calls) == 1
    ctxs = put_calls[0]["required_status_checks"]["contexts"]
    assert "docs-drift-guard" in ctxs and "repo-truth-claims" in ctxs


def test_main_check_integration():
    argv = ["ensure_truth_branch_protection.py", "--check"]
    sample = {
        "required_status_checks": {
            "contexts": list(et.TRUTH_REQUIRED),
            "checks": [],
        }
    }

    def fake_fetch(*_a, **_k):
        return 0, sample, ""

    with patch.object(sys, "argv", argv):
        with patch.object(et, "fetch_protection", fake_fetch):
            assert et.main() == 0
