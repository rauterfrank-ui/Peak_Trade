"""Tests for JSON-SSOT required-checks branch-protection reconciliation."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "scripts" / "ops"))

import reconcile_required_checks_branch_protection as reconcile  # noqa: E402


def _sample_protection(contexts: list[str]) -> dict:
    return {
        "required_status_checks": {
            "strict": False,
            "contexts": contexts,
            "checks": [],
        },
        "enforce_admins": {"enabled": True},
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": False,
            "require_code_owner_reviews": False,
            "required_approving_review_count": 1,
        },
    }


def test_run_check_ok_when_live_matches_effective_required(tmp_path: Path) -> None:
    cfg = tmp_path / "required_status_checks.json"
    cfg.write_text(
        '{"required_contexts":["Lint Gate","IGNORED"],"ignored_contexts":["IGNORED"]}\n',
        encoding="utf-8",
    )

    with patch.object(
        reconcile,
        "fetch_protection",
        lambda *_a, **_k: (0, _sample_protection(["Lint Gate"]), ""),
    ):
        assert reconcile.run_check("o", "r", "main", str(cfg)) == 0


def test_run_check_fail_closed_on_diff(tmp_path: Path, capsys) -> None:
    cfg = tmp_path / "required_status_checks.json"
    cfg.write_text('{"required_contexts":["Lint Gate","audit"]}\n', encoding="utf-8")

    with patch.object(
        reconcile,
        "fetch_protection",
        lambda *_a, **_k: (0, _sample_protection(["Lint Gate"]), ""),
    ):
        assert reconcile.run_check("o", "r", "main", str(cfg)) == 1

    output = capsys.readouterr().out
    assert "missing_in_live:" in output
    assert "- audit" in output


def test_run_check_fail_closed_on_empty_effective_required(tmp_path: Path) -> None:
    cfg = tmp_path / "required_status_checks.json"
    cfg.write_text('{"required_contexts":["IGNORED"],"ignored_contexts":["IGNORED"]}\n', encoding="utf-8")

    with patch.object(reconcile, "fetch_protection", side_effect=AssertionError("must not be called")):
        assert reconcile.run_check("o", "r", "main", str(cfg)) == 1


def test_run_apply_overwrites_live_to_ssot_contexts(tmp_path: Path) -> None:
    cfg = tmp_path / "required_status_checks.json"
    cfg.write_text('{"required_contexts":["Lint Gate","audit"]}\n', encoding="utf-8")

    put_payloads: list[dict] = []

    def fake_gh_api(method: str, path: str, *, body=None):
        if method == "PUT":
            put_payloads.append(body or {})
            return 0, "{}", ""
        raise AssertionError(path)

    with patch.object(
        reconcile,
        "fetch_protection",
        lambda *_a, **_k: (0, _sample_protection(["Lint Gate", "legacy-extra"]), ""),
    ):
        with patch.object(reconcile, "_gh_api", fake_gh_api):
            assert reconcile.run_apply("o", "r", "main", str(cfg)) == 0

    assert len(put_payloads) == 1
    assert put_payloads[0]["required_status_checks"]["contexts"] == ["Lint Gate", "audit"]


def test_run_apply_fail_closed_when_put_fails(tmp_path: Path) -> None:
    cfg = tmp_path / "required_status_checks.json"
    cfg.write_text('{"required_contexts":["Lint Gate","audit"]}\n', encoding="utf-8")

    with patch.object(
        reconcile,
        "fetch_protection",
        lambda *_a, **_k: (0, _sample_protection(["Lint Gate"]), ""),
    ):
        with patch.object(reconcile, "_gh_api", lambda *_a, **_k: (1, "", "permission denied")):
            assert reconcile.run_apply("o", "r", "main", str(cfg)) == 1
