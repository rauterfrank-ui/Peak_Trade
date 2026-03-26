from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.ops.workflow_officer import (
    PROFILE_POLICY,
    _recommend_priority_action,
    classify_workflow_officer_sequencing,
    _resolve_effective_level,
    _resolve_outcome,
    _resolve_severity,
    _resolve_status,
    build_executive_summary_view,
    build_followup_topic_ranking,
    build_workflow_officer_dashboard_view,
    build_handoff_context,
    build_next_chat_preview,
    build_operator_report_view,
    build_workflow_officer_provenance,
    load_ops_merge_log_inputs,
    load_ops_registry_inputs,
    parse_merge_log_signals,
    parse_ops_pointer_text,
    render_executive_summary_markdown,
    render_next_chat_preview_markdown,
    render_operator_report_markdown,
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
    assert handoff["handoff_schema_version"] == "workflow_officer.handoff_context/v1"
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
        assert handoff["primary_sequencing"] == ranking[0]["sequencing"]
        assert report["summary"]["primary_sequencing"] == handoff["primary_sequencing"]
        assert ranking[0]["sequencing"]["sequencing_bucket"] in {
            "build_now",
            "stabilize_only",
            "defer_until_prerequisites",
        }
    else:
        assert handoff["primary_followup_check_id"] is None
        assert handoff["top_followups"] == []

    reg_in = report["summary"]["registry_inputs"]
    assert reg_in["registry_dir_present"] is True
    assert reg_in["pointer_count"] >= 3
    assert len(reg_in["pointers"]) == reg_in["pointer_count"]
    names = [p["name"] for p in reg_in["pointers"]]
    assert names == sorted(names)
    rr = handoff["registry_inputs_rollup"]
    assert rr["registry_dir_present"] is True
    assert rr["pointer_count"] == reg_in["pointer_count"]
    if rr["primary_run_id"] is not None:
        assert isinstance(rr["primary_run_id"], str) and rr["primary_run_id"].strip()

    ml_in = report["summary"]["merge_log_inputs"]
    assert ml_in["merge_logs_dir_present"] is True
    assert ml_in["canonical_merge_log_count"] >= 30
    assert len(ml_in["recent_merge_logs"]) == 5
    pr_seq = [row["pr_number"] for row in ml_in["recent_merge_logs"]]
    assert pr_seq == sorted(pr_seq, reverse=True)
    mlr = handoff["merge_log_inputs_rollup"]
    assert mlr["merge_logs_dir_present"] is True
    assert mlr["canonical_merge_log_count"] == ml_in["canonical_merge_log_count"]
    assert mlr["latest_pr_number"] == pr_seq[0]
    if mlr["latest_merge_commit_sha"] is not None:
        assert len(mlr["latest_merge_commit_sha"]) >= 7

    prov = report["summary"]["workflow_officer_provenance"]
    assert prov["provenance_schema_version"] == "workflow_officer.provenance/v0"
    assert prov["followup_topic_ranking"]["ordering_inputs"] == sorted(
        ["check_id", "effective_level", "outcome", "recommended_priority", "severity"]
    )
    assert (
        prov["followup_topic_ranking"]["rank_heuristic_schema_version"]
        == "workflow_officer.followup_rank_heuristic/v0"
    )
    for row in ranking:
        assert "followup_rank_heuristic" in row
        assert row["followup_rank_heuristic"]["tie_break"] == "check_id_ascii"
    assert prov["handoff_context"]["summary_inputs"] == sorted(
        ["followup_topic_ranking", "merge_log_inputs", "registry_inputs", "strict"]
    )
    preview = report["summary"]["next_chat_preview"]
    assert preview["preview_schema_version"] == "workflow_officer.next_chat_preview/v1"
    assert preview["provenance_schema_version"] == prov["provenance_schema_version"]
    assert preview["primary_followup_check_id"] == handoff["primary_followup_check_id"]
    assert preview["queued_followup_check_ids"] == [
        r["check_id"] for r in handoff["top_followups"][:3]
    ]
    assert preview["total_checks"] == handoff["rollup"]["total_checks"]
    assert preview["hard_failures"] == handoff["rollup"]["hard_failures"]
    assert preview["warnings"] == handoff["rollup"]["warnings"]
    assert preview["registry_pointer_count"] == handoff["registry_inputs_rollup"]["pointer_count"]
    assert preview["latest_pr_number"] == handoff["merge_log_inputs_rollup"]["latest_pr_number"]

    op = report["summary"]["operator_report"]
    assert op["operator_report_schema_version"] == "workflow_officer.operator_report/v0"
    assert op["strict"] is report["summary"]["strict"]
    assert op["rollup"] == {
        "total_checks": report["summary"]["total_checks"],
        "hard_failures": report["summary"]["hard_failures"],
        "warnings": report["summary"]["warnings"],
        "infos": report["summary"]["infos"],
    }
    if ranking:
        assert op["primary_followup"] is not None
        assert op["primary_followup"]["check_id"] == ranking[0]["check_id"]
        assert [r["check_id"] for r in op["top_followups"]] == [
            r["check_id"] for r in ranking[: min(5, len(ranking))]
        ]
    assert (
        op["next_chat_essentials"]["primary_followup_check_id"]
        == preview["primary_followup_check_id"]
    )
    assert op["registry_signals"]["pointer_count"] == rr["pointer_count"]
    assert op["merge_log_signals"]["canonical_merge_log_count"] == mlr["canonical_merge_log_count"]
    ex = report["summary"]["executive_summary"]
    assert ex["executive_summary_schema_version"] == "workflow_officer.executive_summary/v0"
    assert ex["urgency_label"] in {"critical", "elevated", "moderate", "clear", "none"}
    assert ex["rollup_snapshot"]["total_checks"] == report["summary"]["total_checks"]
    assert prov["operator_report"]["summary_inputs"] == sorted(
        [
            "followup_topic_ranking",
            "handoff_context",
            "hard_failures",
            "infos",
            "next_chat_preview",
            "strict",
            "total_checks",
            "warnings",
            "workflow_officer_provenance",
        ]
    )
    assert prov["executive_summary"]["summary_inputs"] == sorted(
        [
            "hard_failures",
            "infos",
            "operator_report",
            "strict",
            "total_checks",
            "warnings",
        ]
    )

    summary_md = summary_path.read_text(encoding="utf-8")
    assert "## Executive decision package" in summary_md
    assert "workflow_officer.executive_summary/v0" in summary_md
    assert "## Operator consolidated view" in summary_md
    assert "workflow_officer.operator_report/v0" in summary_md
    assert "## Next chat preview" in summary_md
    assert "workflow_officer.next_chat_preview/v1" in summary_md

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
            "outcome": "pass",
            "severity": "info",
            "surface": "s",
            "category": "c",
        },
        {
            "check_id": "a_check",
            "recommended_priority": "p0",
            "effective_level": "warning",
            "outcome": "fail",
            "severity": "warn",
            "surface": "s",
            "category": "c",
        },
        {
            "check_id": "m_check",
            "recommended_priority": "p0",
            "effective_level": "error",
            "outcome": "fail",
            "severity": "hard_fail",
            "surface": "s",
            "category": "c",
        },
        {
            "check_id": "b_check",
            "recommended_priority": "p0",
            "effective_level": "error",
            "outcome": "fail",
            "severity": "hard_fail",
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
            "recommended_action",
            "recommended_priority",
            "effective_level",
            "surface",
            "category",
            "followup_rank_heuristic",
            "sequencing",
        }
        for r in ranked
    )


def test_build_followup_topic_ranking_tie_break_check_id_after_shared_heuristic() -> None:
    rows = [
        {
            "check_id": "z_same",
            "recommended_priority": "p1",
            "effective_level": "warning",
            "outcome": "fail",
            "severity": "warn",
            "surface": "s",
            "category": "c",
        },
        {
            "check_id": "a_same",
            "recommended_priority": "p1",
            "effective_level": "warning",
            "outcome": "fail",
            "severity": "warn",
            "surface": "s",
            "category": "c",
        },
    ]
    ranked = build_followup_topic_ranking(rows)
    assert [r["check_id"] for r in ranked] == ["a_same", "z_same"]
    assert (
        ranked[0]["followup_rank_heuristic"]["components"]
        == ranked[1]["followup_rank_heuristic"]["components"]
    )


def test_build_followup_topic_ranking_orders_fail_before_pass_when_priority_effective_match() -> (
    None
):
    rows = [
        {
            "check_id": "pass_first_id",
            "recommended_priority": "p1",
            "effective_level": "warning",
            "outcome": "pass",
            "severity": "warn",
            "surface": "s",
            "category": "c",
        },
        {
            "check_id": "fail_second_id",
            "recommended_priority": "p1",
            "effective_level": "warning",
            "outcome": "fail",
            "severity": "warn",
            "surface": "s",
            "category": "c",
        },
    ]
    ranked = build_followup_topic_ranking(rows)
    assert [r["check_id"] for r in ranked] == ["fail_second_id", "pass_first_id"]


def test_build_followup_topic_ranking_orders_hard_fail_before_warn_when_tied_higher() -> None:
    rows = [
        {
            "check_id": "warn_sev",
            "recommended_priority": "p1",
            "effective_level": "warning",
            "outcome": "fail",
            "severity": "warn",
            "surface": "s",
            "category": "c",
        },
        {
            "check_id": "hard_sev",
            "recommended_priority": "p1",
            "effective_level": "warning",
            "outcome": "fail",
            "severity": "hard_fail",
            "surface": "s",
            "category": "c",
        },
    ]
    ranked = build_followup_topic_ranking(rows)
    assert [r["check_id"] for r in ranked] == ["hard_sev", "warn_sev"]


def test_build_followup_topic_ranking_mixed_signals_stable_order() -> None:
    rows = [
        {
            "check_id": "late",
            "recommended_priority": "p2",
            "effective_level": "ok",
            "outcome": "pass",
            "severity": "info",
            "surface": "s",
            "category": "c",
        },
        {
            "check_id": "mid",
            "recommended_priority": "p1",
            "effective_level": "warning",
            "outcome": "pass",
            "severity": "warn",
            "surface": "s",
            "category": "c",
        },
        {
            "check_id": "top",
            "recommended_priority": "p1",
            "effective_level": "warning",
            "outcome": "fail",
            "severity": "info",
            "surface": "s",
            "category": "c",
        },
    ]
    ranked = build_followup_topic_ranking(rows)
    assert [r["check_id"] for r in ranked] == ["top", "mid", "late"]


def test_build_followup_topic_ranking_partial_row_unknown_axis_sorts_last() -> None:
    rows = [
        {
            "check_id": "known_outcome",
            "recommended_priority": "p1",
            "effective_level": "warning",
            "outcome": "pass",
            "severity": "warn",
            "surface": "s",
            "category": "c",
        },
        {
            "check_id": "unknown_outcome",
            "recommended_priority": "p1",
            "effective_level": "warning",
            "severity": "warn",
            "surface": "s",
            "category": "c",
        },
    ]
    ranked = build_followup_topic_ranking(rows)
    assert [r["check_id"] for r in ranked] == ["known_outcome", "unknown_outcome"]
    assert ranked[1]["followup_rank_heuristic"]["components"]["outcome_rank"] == 99


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
        "handoff_schema_version": "workflow_officer.handoff_context/v1",
        "strict": False,
        "rollup": {
            "total_checks": 0,
            "hard_failures": 0,
            "warnings": 0,
            "infos": 0,
        },
        "primary_followup_check_id": None,
        "primary_sequencing": None,
        "top_followups": [],
        "registry_inputs_rollup": {
            "registry_dir_present": False,
            "pointer_count": 0,
            "primary_run_id": None,
        },
        "merge_log_inputs_rollup": {
            "merge_logs_dir_present": False,
            "canonical_merge_log_count": 0,
            "latest_pr_number": None,
            "latest_merge_commit_sha": None,
        },
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
    assert ctx["registry_inputs_rollup"]["primary_run_id"] is None
    assert ctx["merge_log_inputs_rollup"]["latest_pr_number"] is None


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
        set(r.keys())
        == {"rank", "check_id", "recommended_priority", "effective_level", "sequencing"}
        for r in ctx["top_followups"]
    )


def test_build_next_chat_preview_empty_summary_inputs_is_stable() -> None:
    assert build_next_chat_preview({}) == {
        "hard_failures": 0,
        "latest_pr_number": None,
        "preview_schema_version": "workflow_officer.next_chat_preview/v1",
        "primary_followup_check_id": None,
        "primary_sequencing": None,
        "provenance_schema_version": None,
        "queued_followup_check_ids": [],
        "registry_pointer_count": None,
        "total_checks": 0,
        "warnings": 0,
    }


def test_render_next_chat_preview_markdown_non_dict_or_missing_schema_returns_empty() -> None:
    assert render_next_chat_preview_markdown({}) == ""
    assert render_next_chat_preview_markdown({"preview_schema_version": ""}) == ""
    assert render_next_chat_preview_markdown({"preview_schema_version": "   "}) == ""


def test_render_next_chat_preview_markdown_stable_full() -> None:
    md = render_next_chat_preview_markdown(
        {
            "preview_schema_version": "workflow_officer.next_chat_preview/v1",
            "provenance_schema_version": "workflow_officer.provenance/v0",
            "total_checks": 2,
            "hard_failures": 1,
            "warnings": 0,
            "primary_followup_check_id": "b",
            "primary_sequencing": {
                "sequencing_bucket": "build_now",
                "sequencing_rationale": "execution-adjacent bounded-pilot / truth / ops work is a nearer prerequisite than broader AI-layer expansion",
                "prerequisite_signals": ["active_path_hardening"],
                "blocked_by": [],
                "suggested_next_theme_class": "bounded_pilot_truth_ops",
                "sequencing_schema_version": "workflow_officer.sequencing/v0",
            },
            "queued_followup_check_ids": ["b", "a"],
            "registry_pointer_count": 4,
            "latest_pr_number": 99,
        }
    )
    assert md == (
        "## Next chat preview\n"
        "\n"
        "- preview_schema_version: `workflow_officer.next_chat_preview/v1`\n"
        "- provenance_schema_version: `workflow_officer.provenance/v0`\n"
        "- total_checks: `2`\n"
        "- hard_failures: `1`\n"
        "- warnings: `0`\n"
        "- primary_followup_check_id: `b`\n"
        "- queued_followup_check_ids (order preserved): `b`, `a`\n"
        "- registry_pointer_count: `4`\n"
        "- latest_pr_number: `99`\n"
        "- sequencing_bucket: `build_now`\n"
        "- sequencing_rationale: execution-adjacent bounded-pilot / truth / ops work is a nearer prerequisite than broader AI-layer expansion\n"
    )


def test_build_next_chat_preview_follows_handoff_ordering() -> None:
    summary = {
        "workflow_officer_provenance": {
            "provenance_schema_version": "workflow_officer.provenance/v0",
        },
        "handoff_context": {
            "rollup": {
                "total_checks": 2,
                "hard_failures": 1,
                "warnings": 0,
                "infos": 0,
            },
            "primary_followup_check_id": "b",
            "top_followups": [
                {
                    "rank": 1,
                    "check_id": "b",
                    "recommended_priority": "p0",
                    "effective_level": "error",
                },
                {
                    "rank": 2,
                    "check_id": "a",
                    "recommended_priority": "p1",
                    "effective_level": "warning",
                },
            ],
            "registry_inputs_rollup": {"pointer_count": 4},
            "merge_log_inputs_rollup": {"latest_pr_number": 99},
        },
    }
    got = build_next_chat_preview(summary)
    assert got["queued_followup_check_ids"] == ["b", "a"]
    assert got["primary_followup_check_id"] == "b"
    assert got["provenance_schema_version"] == "workflow_officer.provenance/v0"
    assert got["registry_pointer_count"] == 4
    assert got["latest_pr_number"] == 99
    assert got["total_checks"] == 2
    assert got["hard_failures"] == 1
    assert got["warnings"] == 0


def test_build_workflow_officer_provenance_is_stable() -> None:
    assert build_workflow_officer_provenance() == {
        "provenance_schema_version": "workflow_officer.provenance/v0",
        "recommended_priority_and_action": {
            "builder": "_recommend_priority_action",
            "check_row_inputs": sorted(["effective_level", "outcome", "severity"]),
            "profile_plan_fields_appended": sorted(["category", "description", "surface"]),
        },
        "followup_topic_ranking": {
            "builder": "build_followup_topic_ranking",
            "check_row_inputs": sorted(
                [
                    "category",
                    "check_id",
                    "effective_level",
                    "outcome",
                    "recommended_action",
                    "recommended_priority",
                    "sequencing",
                    "severity",
                    "surface",
                ]
            ),
            "ordering_inputs": sorted(
                ["check_id", "effective_level", "outcome", "recommended_priority", "severity"]
            ),
            "rank_heuristic_schema_version": "workflow_officer.followup_rank_heuristic/v0",
        },
        "registry_inputs": {
            "builder": "load_ops_registry_inputs",
            "repo_relative_glob": "docs/ops/registry/*.pointer",
        },
        "merge_log_inputs": {
            "builder": "load_ops_merge_log_inputs",
            "body_signal_parser": "parse_merge_log_signals",
            "parsed_fields": sorted(["merged_at", "merge_commit_sha"]),
            "repo_relative_glob": "docs/ops/merge_logs/PR_*_MERGE_LOG.md",
        },
        "handoff_context": {
            "builder": "build_handoff_context",
            "handoff_output_keys": sorted(
                [
                    "handoff_schema_version",
                    "merge_log_inputs_rollup",
                    "primary_followup_check_id",
                    "primary_sequencing",
                    "registry_inputs_rollup",
                    "rollup",
                    "strict",
                    "top_followups",
                ]
            ),
            "rollup_keys": sorted(["hard_failures", "infos", "total_checks", "warnings"]),
            "summary_inputs": sorted(
                [
                    "followup_topic_ranking",
                    "merge_log_inputs",
                    "registry_inputs",
                    "strict",
                ]
            ),
        },
        "next_chat_preview": {
            "builder": "build_next_chat_preview",
            "queued_followup_max": 3,
            "summary_inputs": sorted(["handoff_context", "workflow_officer_provenance"]),
        },
        "executive_summary": {
            "builder": "build_executive_summary_view",
            "markdown_builder": "render_executive_summary_markdown",
            "summary_inputs": sorted(
                [
                    "hard_failures",
                    "infos",
                    "operator_report",
                    "strict",
                    "total_checks",
                    "warnings",
                ]
            ),
        },
        "operator_report": {
            "builder": "build_operator_report_view",
            "markdown_builder": "render_operator_report_markdown",
            "summary_inputs": sorted(
                [
                    "followup_topic_ranking",
                    "handoff_context",
                    "hard_failures",
                    "infos",
                    "next_chat_preview",
                    "strict",
                    "total_checks",
                    "warnings",
                    "workflow_officer_provenance",
                ]
            ),
        },
    }


def test_build_workflow_officer_dashboard_view_missing_output_is_stable(tmp_path: Path) -> None:
    got = build_workflow_officer_dashboard_view(tmp_path)
    assert got["present"] is False
    assert got["dashboard_schema_version"] == "workflow_officer.dashboard_view/v0"
    assert got["empty_reason"] == "no_officer_output_dir"
    assert got["executive_panel"]["present"] is False
    assert got["executive_panel"]["empty_reason"] == "no_officer_output_dir"


def test_build_workflow_officer_dashboard_view_reads_latest_report_json(tmp_path: Path) -> None:
    run_a = tmp_path / "out" / "ops" / "workflow_officer" / "20260101T000000Z"
    run_b = tmp_path / "out" / "ops" / "workflow_officer" / "20260201T000000Z"
    run_a.mkdir(parents=True)
    run_b.mkdir(parents=True)
    report_a = {
        "officer_version": "v1-min",
        "profile": "docs_only_pr",
        "mode": "audit",
        "success": True,
        "finished_at": "2026-01-01",
        "summary": {
            "total_checks": 1,
            "hard_failures": 0,
            "warnings": 0,
            "infos": 0,
            "strict": False,
            "executive_summary": {
                "executive_summary_schema_version": "workflow_officer.executive_summary/v0",
                "urgency_label": "clear",
                "attention_rationale": "No blocking errors.",
            },
            "operator_report": {
                "operator_report_schema_version": "workflow_officer.operator_report/v0",
                "primary_followup": {
                    "check_id": "chk_a",
                    "recommended_priority": "p3",
                    "effective_level": "ok",
                    "recommended_action": "No action.",
                },
                "rollup": {
                    "total_checks": 1,
                    "hard_failures": 0,
                    "warnings": 0,
                    "infos": 0,
                },
                "top_followups": [
                    {
                        "rank": 1,
                        "check_id": "chk_a",
                        "recommended_priority": "p3",
                        "effective_level": "ok",
                    }
                ],
            },
        },
    }
    (run_a / "report.json").write_text(json.dumps(report_a), encoding="utf-8")
    (run_b / "report.json").write_text(
        json.dumps({**report_a, "profile": "other", "success": False}),
        encoding="utf-8",
    )
    got = build_workflow_officer_dashboard_view(tmp_path)
    assert got["present"] is True
    assert got["profile"] == "other"
    assert got["success"] is False
    assert got["primary_followup"]["check_id"] == "chk_a"
    assert len(got["top_followups"]) == 1
    assert got["executive"]["urgency_label"] == "clear"
    assert "total=1" in got["operator_snapshot_line"]
    ep = got["executive_panel"]
    assert ep["present"] is True
    assert ep["executive_panel_schema_version"] == "workflow_officer.executive_panel_view/v0"
    assert ep["urgency_label"] == "clear"
    assert ep["decision_package_preview_lines"]
    assert any("Executive decision package" in ln for ln in ep["decision_package_preview_lines"])


def test_build_executive_summary_view_empty_summary_is_deterministic() -> None:
    assert build_executive_summary_view({}) == {
        "attention_rationale": "No checks recorded; nothing to action.",
        "executive_summary_schema_version": "workflow_officer.executive_summary/v0",
        "next_chat_handoff": {
            "latest_pr_number": None,
            "primary_followup_check_id": None,
            "queued_followup_check_ids": [],
            "registry_pointer_count": None,
        },
        "primary_recommendation": {
            "check_id": None,
            "effective_level": None,
            "recommended_action_excerpt": None,
            "recommended_priority": None,
            "sequencing": None,
        },
        "provenance_schema_version": None,
        "rollup_snapshot": {
            "hard_failures": 0,
            "infos": 0,
            "strict": False,
            "total_checks": 0,
            "warnings": 0,
        },
        "supporting_signals": ["strict=no"],
        "top_followups": [],
        "urgency_label": "none",
    }


def test_render_executive_summary_markdown_requires_schema_version() -> None:
    assert render_executive_summary_markdown({}) == ""
    assert render_executive_summary_markdown({"executive_summary_schema_version": ""}) == ""


def test_render_executive_summary_markdown_stable_minimal() -> None:
    md = render_executive_summary_markdown(
        {
            "executive_summary_schema_version": "workflow_officer.executive_summary/v0",
            "provenance_schema_version": "workflow_officer.provenance/v0",
            "urgency_label": "elevated",
            "attention_rationale": "Warning-level findings need review before treating this run as clean.",
            "primary_recommendation": {
                "check_id": "docs_graph_triage",
                "effective_level": "warning",
                "recommended_action_excerpt": "Review logs.",
                "recommended_priority": "p1",
            },
            "top_followups": [
                {
                    "rank": 1,
                    "check_id": "docs_graph_triage",
                    "effective_level": "warning",
                    "recommended_priority": "p1",
                }
            ],
            "supporting_signals": ["rollup_total=2 errors=0 warnings=1 infos=0", "strict=no"],
            "next_chat_handoff": {
                "latest_pr_number": 100,
                "primary_followup_check_id": "docs_graph_triage",
                "queued_followup_check_ids": ["docs_graph_triage"],
                "registry_pointer_count": 3,
            },
            "rollup_snapshot": {
                "total_checks": 2,
                "hard_failures": 0,
                "warnings": 1,
                "infos": 0,
                "strict": False,
            },
        }
    )
    assert md.startswith("## Executive decision package\n")
    assert "- urgency_label: `elevated`" in md
    assert "- why now: Warning-level findings need review before treating this run as clean." in md


def test_build_operator_report_view_empty_summary_is_deterministic() -> None:
    assert build_operator_report_view({}) == {
        "merge_log_signals": {
            "canonical_merge_log_count": 0,
            "latest_merge_commit_sha": None,
            "latest_pr_number": None,
            "merge_logs_dir_present": False,
        },
        "next_chat_essentials": {
            "latest_pr_number": None,
            "primary_followup_check_id": None,
            "queued_followup_check_ids": [],
            "registry_pointer_count": None,
        },
        "operator_report_schema_version": "workflow_officer.operator_report/v0",
        "primary_followup": None,
        "provenance_schema_version": None,
        "ranking_basis": {
            "ordering_inputs": [],
            "rank_heuristic_schema_version": None,
        },
        "registry_signals": {
            "pointer_count": 0,
            "primary_run_id": None,
            "registry_dir_present": False,
        },
        "rollup": {
            "hard_failures": 0,
            "infos": 0,
            "total_checks": 0,
            "warnings": 0,
        },
        "strict": False,
        "top_followups": [],
    }


def test_render_operator_report_markdown_requires_schema_version() -> None:
    assert render_operator_report_markdown({}) == ""
    assert render_operator_report_markdown({"rollup": {}}) == ""


def test_render_operator_report_markdown_matches_empty_build() -> None:
    md = render_operator_report_markdown(build_operator_report_view({}))
    assert md.startswith("## Operator consolidated view\n")
    assert "workflow_officer.operator_report/v0" in md


def test_parse_ops_pointer_text_ignores_comments_and_orders_keys_in_payload() -> None:
    text = """
# comment
run_id=123

repo=org/repo
artifact_hint=x=y
"""
    d = parse_ops_pointer_text(text)
    assert d == {"run_id": "123", "repo": "org/repo", "artifact_hint": "x=y"}


def test_load_ops_registry_inputs_missing_dir_is_stable(tmp_path: Path) -> None:
    assert load_ops_registry_inputs(tmp_path) == {
        "registry_dir_present": False,
        "pointer_count": 0,
        "pointers": [],
    }


def test_load_ops_registry_inputs_sorted_names_and_field_keys(tmp_path: Path) -> None:
    reg = tmp_path / "docs" / "ops" / "registry"
    reg.mkdir(parents=True)
    (reg / "z.pointer").write_text("z=last\nrun_id=9\n", encoding="utf-8")
    (reg / "a.pointer").write_text("a=first\nrun_id=1\n", encoding="utf-8")
    got = load_ops_registry_inputs(tmp_path)
    assert got["registry_dir_present"] is True
    assert got["pointer_count"] == 2
    assert [p["name"] for p in got["pointers"]] == ["a.pointer", "z.pointer"]
    assert got["pointers"][0]["fields"] == {"a": "first", "run_id": "1"}
    assert got["pointers"][1]["fields"] == {"run_id": "9", "z": "last"}


def test_build_handoff_context_registry_primary_run_id_first_pointer() -> None:
    summary = {
        "strict": False,
        "total_checks": 1,
        "hard_failures": 0,
        "warnings": 0,
        "infos": 0,
        "followup_topic_ranking": [],
        "registry_inputs": {
            "registry_dir_present": True,
            "pointer_count": 2,
            "pointers": [
                {
                    "name": "first.pointer",
                    "rel_path": "docs/ops/registry/first.pointer",
                    "fields": {},
                },
                {
                    "name": "second.pointer",
                    "rel_path": "docs/ops/registry/second.pointer",
                    "fields": {"run_id": " 42 "},
                },
            ],
        },
    }
    ctx = build_handoff_context(summary)
    assert ctx["registry_inputs_rollup"] == {
        "registry_dir_present": True,
        "pointer_count": 2,
        "primary_run_id": "42",
    }
    summary2 = {
        **summary,
        "registry_inputs": {
            "registry_dir_present": True,
            "pointer_count": 2,
            "pointers": [
                {
                    "name": "first.pointer",
                    "rel_path": "docs/ops/registry/first.pointer",
                    "fields": {"run_id": "99"},
                },
                {
                    "name": "second.pointer",
                    "rel_path": "docs/ops/registry/second.pointer",
                    "fields": {"run_id": "1"},
                },
            ],
        },
    }
    assert build_handoff_context(summary2)["registry_inputs_rollup"]["primary_run_id"] == "99"


def test_parse_merge_log_signals_evidence_block_and_compact_line() -> None:
    sha40 = "0123456789abcdef0123456789abcdef01234567"
    evidence_style = f"""
## Verification
- Post-Merge Evidence (Truth):
  - mergeCommit: `{sha40}`
  - mergedAt: `2026-01-30T23:44:08Z`
"""
    sig = parse_merge_log_signals(evidence_style)
    assert sig["merge_commit_sha"] == sha40
    assert sig["merged_at"] == "2026-01-30T23:44:08Z"

    compact = """
- Merge commit: 0ae34d94394d8ff63cbc356e3ff1b82bddb31bf6
- Merged at (UTC): 2026-01-18T18:28:31Z
"""
    sig2 = parse_merge_log_signals(compact)
    assert sig2["merge_commit_sha"] == "0ae34d94394d8ff63cbc356e3ff1b82bddb31bf6"
    assert sig2["merged_at"] == "2026-01-18T18:28:31Z"


def test_load_ops_merge_log_inputs_missing_dir_is_stable(tmp_path: Path) -> None:
    assert load_ops_merge_log_inputs(tmp_path) == {
        "merge_logs_dir_present": False,
        "canonical_merge_log_count": 0,
        "recent_merge_logs": [],
    }


def test_load_ops_merge_log_inputs_orders_by_pr_desc_and_caps(tmp_path: Path) -> None:
    ml = tmp_path / "docs" / "ops" / "merge_logs"
    ml.mkdir(parents=True)
    (ml / "PR_2_MERGE_LOG.md").write_text(
        "Merge commit: aaa0000000000000000000000000000000000000\n",
        encoding="utf-8",
    )
    (ml / "PR_10_MERGE_LOG.md").write_text(
        "Merge commit: bbb0000000000000000000000000000000000000\n",
        encoding="utf-8",
    )
    (ml / "PR_99_MERGE_LOG.md").write_text("# x\n", encoding="utf-8")
    for i in range(1, 8):
        (ml / f"PR_{100 + i}_MERGE_LOG.md").write_text("# stub\n", encoding="utf-8")
    got = load_ops_merge_log_inputs(tmp_path)
    assert got["merge_logs_dir_present"] is True
    assert got["canonical_merge_log_count"] == 10
    recent = got["recent_merge_logs"]
    assert len(recent) == 5
    assert [r["pr_number"] for r in recent] == [107, 106, 105, 104, 103]
    assert recent[0]["merge_commit_sha"] is None


def test_classify_sequencing_defer_ai_expansion_when_gates_incomplete() -> None:
    row = {
        "check_id": "exp",
        "recommended_action": "Broaden provider model and critic-proposer expansion.",
        "category": "ai",
        "surface": "x",
    }
    got = classify_workflow_officer_sequencing(row, gates_incomplete=True)
    assert got["sequencing_bucket"] == "defer_until_prerequisites"
    assert got["sequencing_schema_version"] == "workflow_officer.sequencing/v0"


def test_classify_sequencing_build_now_execution_path() -> None:
    row = {
        "check_id": "ks",
        "recommended_action": "Verify kill switch and incident operator gating.",
        "category": "ops",
        "surface": "x",
    }
    got = classify_workflow_officer_sequencing(row, gates_incomplete=True)
    assert got["sequencing_bucket"] == "build_now"


def test_classify_sequencing_stabilize_only_polish() -> None:
    row = {
        "check_id": "ui",
        "recommended_action": "Workflow officer dashboard wording polish.",
        "category": "ux",
        "surface": "x",
    }
    got = classify_workflow_officer_sequencing(row, gates_incomplete=True)
    assert got["sequencing_bucket"] == "stabilize_only"


def test_sequencing_handoff_matches_ranking_primary() -> None:
    row = {
        "check_id": "c1",
        "recommended_priority": "p3",
        "effective_level": "ok",
        "outcome": "pass",
        "severity": "info",
        "surface": "docs",
        "category": "documentation",
        "recommended_action": "Workflow officer dashboard polish regression.",
    }
    ranking = build_followup_topic_ranking([row])
    summary = {
        "strict": False,
        "total_checks": 1,
        "hard_failures": 0,
        "warnings": 0,
        "infos": 0,
        "followup_topic_ranking": ranking,
    }
    hc = build_handoff_context(summary)
    assert hc["primary_sequencing"] == ranking[0]["sequencing"]
    assert hc["primary_sequencing"]["sequencing_bucket"] == "stabilize_only"
