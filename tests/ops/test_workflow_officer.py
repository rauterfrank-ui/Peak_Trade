from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.ops.workflow_officer import (
    PROFILE_POLICY,
    _recommend_priority_action,
    _resolve_effective_level,
    _resolve_outcome,
    _resolve_severity,
    _resolve_status,
    build_followup_topic_ranking,
    build_handoff_context,
)


def _run(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "src/ops/workflow_officer.py", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )


def test_workflow_officer_docs_only_pr_emits_report() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    proc = _run(repo_root, "--mode", "audit", "--profile", "docs_only_pr")
    assert proc.returncode in (0, 1)

    out_root = repo_root / "out" / "ops" / "workflow_officer"
    assert out_root.exists()

    latest = sorted([p for p in out_root.iterdir() if p.is_dir()])[-1]
    report_path = latest / "report.json"
    manifest_path = latest / "manifest.json"
    events_path = latest / "events.jsonl"
    summary_path = latest / "summary.md"

    assert report_path.exists()
    assert manifest_path.exists()
    assert events_path.exists()
    assert summary_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["officer_version"] == "v1-min"
    assert report["profile"] == "docs_only_pr"
    assert "checks" in report
    assert "summary" in report
    assert "severity_counts" in report["summary"]
    assert "outcome_counts" in report["summary"]
    assert "effective_level_counts" in report["summary"]
    ranking = report["summary"]["followup_topic_ranking"]
    assert isinstance(ranking, list)
    assert len(ranking) == len(report["checks"])
    assert [row["rank"] for row in ranking] == list(range(1, len(ranking) + 1))

    handoff = report["summary"]["handoff_context"]
    assert handoff["handoff_schema_version"] == "workflow_officer.handoff_context/v0"
    assert handoff["strict"] is report["summary"]["strict"]
    assert handoff["rollup"] == {
        "total_checks": report["summary"]["total_checks"],
        "hard_failures": report["summary"]["hard_failures"],
        "warnings": report["summary"]["warnings"],
        "infos": report["summary"]["infos"],
    }
    if ranking:
        assert handoff["primary_followup_check_id"] == ranking[0]["check_id"]
        assert len(handoff["top_followups"]) == min(5, len(ranking))
        assert handoff["top_followups"][0]["check_id"] == ranking[0]["check_id"]
    else:
        assert handoff["primary_followup_check_id"] is None
        assert handoff["top_followups"] == []

    for check in report["checks"]:
        assert "severity" in check
        assert "outcome" in check
        assert "effective_level" in check
        assert check["recommended_priority"] in {"p0", "p1", "p2", "p3"}
        assert "recommended_action" in check
        assert "surface" in check
        assert "category" in check


def test_workflow_officer_profiles_alias_exports_profiles() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    from src.ops.workflow_officer_profiles import PROFILES

    assert "docs_only_pr" in PROFILES
    assert "ops_local_env" in PROFILES
    assert "live_pilot_preflight" in PROFILES


def test_profile_policy_contains_expected_severities() -> None:
    assert PROFILE_POLICY["docs_only_pr"]["docs_token_policy"] == "hard_fail"
    assert PROFILE_POLICY["ops_local_env"]["ops_doctor_shell"] == "warn"
    assert (
        PROFILE_POLICY["live_pilot_preflight"]["docker_desktop_preflight_readonly"] == "hard_fail"
    )


def test_resolve_severity_and_status() -> None:
    assert _resolve_severity("docs_only_pr", "docs_token_policy") == "hard_fail"
    assert _resolve_severity("ops_local_env", "failure_analysis") == "info"

    assert _resolve_status(0, "hard_fail") == "OK"
    assert _resolve_status(1, "hard_fail") == "FAILED"
    assert _resolve_status(1, "warn") == "WARN"
    assert _resolve_status(1, "info") == "INFO"
    assert _resolve_status(2, "hard_fail", missing=True) == "FAILED_MISSING"
    assert _resolve_status(2, "warn", missing=True) == "WARN_MISSING"
    assert _resolve_status(2, "info", missing=True) == "INFO_MISSING"


def test_resolve_outcome_and_effective_level() -> None:
    assert _resolve_outcome(0) == "pass"
    assert _resolve_outcome(1) == "fail"
    assert _resolve_outcome(2, missing=True) == "missing"

    assert _resolve_effective_level("pass", "hard_fail") == "ok"
    assert _resolve_effective_level("fail", "hard_fail") == "error"
    assert _resolve_effective_level("fail", "warn") == "warning"
    assert _resolve_effective_level("fail", "info") == "info"
    assert _resolve_effective_level("missing", "hard_fail") == "error"
    assert _resolve_effective_level("missing", "warn") == "warning"
    assert _resolve_effective_level("missing", "info") == "info"


def test_recommend_priority_action_mapping() -> None:
    assert _recommend_priority_action("error", "fail", "hard_fail") == (
        "p0",
        "[workflow_officer.recommend.remediate_error] Stop and remediate: hard_fail check failed "
        "or a required target is missing under hard_fail severity.",
    )
    assert _recommend_priority_action("warning", "fail", "warn") == (
        "p1",
        "[workflow_officer.recommend.review_warning] Review stdout/stderr logs; resolve "
        "warnings before relying on this path.",
    )
    assert _recommend_priority_action("info", "fail", "info") == (
        "p2",
        "[workflow_officer.recommend.verify_manual_info] Informational: verify manually if this "
        "check matters for your change.",
    )
    assert _recommend_priority_action("info", "pass", "info") == (
        "p3",
        "[workflow_officer.recommend.no_action_info_pass] No operator action required.",
    )
    assert _recommend_priority_action("ok", "pass", "hard_fail") == (
        "p3",
        "[workflow_officer.recommend.no_action_ok] No operator action required.",
    )


def test_recommend_priority_action_boundary_missing_effective_levels() -> None:
    assert _recommend_priority_action("error", "missing", "hard_fail")[0] == "p0"
    assert _recommend_priority_action("warning", "missing", "warn")[0] == "p1"
    assert _recommend_priority_action("info", "missing", "info")[0] == "p2"


def test_recommend_priority_action_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="effective_level"):
        _recommend_priority_action("bogus", "pass", "info")
    with pytest.raises(ValueError, match="outcome"):
        _recommend_priority_action("ok", "bogus", "info")
    with pytest.raises(ValueError, match="severity"):
        _recommend_priority_action("ok", "pass", "bogus")


def test_build_followup_topic_ranking_empty_is_stable() -> None:
    assert build_followup_topic_ranking([]) == []


def test_build_followup_topic_ranking_orders_by_priority_effective_check_id() -> None:
    rows = [
        {
            "check_id": "z_check",
            "recommended_priority": "p2",
            "effective_level": "ok",
            "surface": "s",
            "category": "c",
        },
        {
            "check_id": "a_check",
            "recommended_priority": "p0",
            "effective_level": "warning",
            "surface": "s",
            "category": "c",
        },
        {
            "check_id": "m_check",
            "recommended_priority": "p0",
            "effective_level": "error",
            "surface": "s",
            "category": "c",
        },
        {
            "check_id": "b_check",
            "recommended_priority": "p0",
            "effective_level": "error",
            "surface": "s",
            "category": "c",
        },
    ]
    ranked = build_followup_topic_ranking(rows)
    assert [r["check_id"] for r in ranked] == ["b_check", "m_check", "a_check", "z_check"]
    assert [r["rank"] for r in ranked] == [1, 2, 3, 4]
    assert all(
        set(r.keys())
        == {
            "rank",
            "check_id",
            "recommended_priority",
            "effective_level",
            "surface",
            "category",
        }
        for r in ranked
    )


def test_build_handoff_context_empty_ranking_is_stable() -> None:
    summary = {
        "strict": False,
        "total_checks": 0,
        "hard_failures": 0,
        "warnings": 0,
        "infos": 0,
        "followup_topic_ranking": [],
    }
    ctx = build_handoff_context(summary)
    assert ctx == {
        "handoff_schema_version": "workflow_officer.handoff_context/v0",
        "strict": False,
        "rollup": {
            "total_checks": 0,
            "hard_failures": 0,
            "warnings": 0,
            "infos": 0,
        },
        "primary_followup_check_id": None,
        "top_followups": [],
    }


def test_build_handoff_context_missing_ranking_treated_as_empty() -> None:
    summary = {
        "strict": True,
        "total_checks": 2,
        "hard_failures": 0,
        "warnings": 0,
        "infos": 1,
    }
    ctx = build_handoff_context(summary)
    assert ctx["primary_followup_check_id"] is None
    assert ctx["top_followups"] == []
    assert ctx["rollup"]["total_checks"] == 2


def test_build_handoff_context_caps_top_followups() -> None:
    ranking = [
        {
            "rank": i,
            "check_id": f"chk_{i}",
            "recommended_priority": "p3",
            "effective_level": "ok",
            "surface": "s",
            "category": "c",
        }
        for i in range(1, 7)
    ]
    summary = {
        "strict": False,
        "total_checks": 6,
        "hard_failures": 0,
        "warnings": 0,
        "infos": 0,
        "followup_topic_ranking": ranking,
    }
    ctx = build_handoff_context(summary)
    assert ctx["primary_followup_check_id"] == "chk_1"
    assert len(ctx["top_followups"]) == 5
    assert [r["check_id"] for r in ctx["top_followups"]] == [
        "chk_1",
        "chk_2",
        "chk_3",
        "chk_4",
        "chk_5",
    ]
    assert all(
        set(r.keys()) == {"rank", "check_id", "recommended_priority", "effective_level"}
        for r in ctx["top_followups"]
    )
