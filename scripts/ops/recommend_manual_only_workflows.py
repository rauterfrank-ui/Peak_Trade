#!/usr/bin/env python3
"""
Read-only recommender for GitHub Actions workflows (post PR #3896 + SLICE-OE-2).

Covers (1) manual-only workflows that lost cron in PR #3896 and (2) residual workflows
that still have active `schedule:` triggers (GH residual schedule cost review v0).

Lists workflows that match an operator intent and prints suggested `gh workflow run`
commands as text only. Does not invoke gh, mutate files, or re-enable cron schedules.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

GUARD_BANNER = (
    "READ-ONLY RECOMMENDER — does not run workflows. "
    "Operator-GO required before any manual `gh workflow run`. "
    "Cron/schedule is not reactivated by this tool."
)

# Workflows that lost schedule in PR #3896 (manual dispatch retained).
MANUAL_ONLY_WORKFLOW_FILES: frozenset[str] = frozenset(
    {
        "ci-scheduled-paper-and-export-smoke.yml",
        "class-a-shadow-paper-scheduled-probe-v1.yml",
        "docs_reference_targets_fullscan_schedule.yml",
        "full_audit_weekly.yml",
        "infostream-automation.yml",
        "knowledge_extras_chromadb.yml",
        "market_outlook_automation.yml",
        "offline_suites.yml",
        "ops_doctor_dashboard.yml",
        "ops_doctor_pages.yml",
        "prj-scheduled-shadow-paper-features-smoke.yml",
        "test-health-automation.yml",
        "test_health.yml",
        "weekly_core_audit.yml",
    }
)

# Related downstream workflow (dispatch-only; schedule commented in YAML).
PAPER_TEST_EVIDENCE_FILE = "paper_tests_audit_evidence.yml"

# Residual schedule inventory (13 files): 6 active schedule + 7 manual-only (GH-001..004 + GH-CI + PRCC + PRK).
RESIDUAL_SCHEDULE_WORKFLOW_FILES: frozenset[str] = frozenset(
    {
        "audit.yml",
        "ci.yml",
        "prbc-stability-gate.yml",
        "prbd-live-readiness-scorecard.yml",
        "prbe-shadow-testnet-scorecard.yml",
        "prbg-execution-evidence.yml",
        "prbi-live-pilot-scorecard.yml",
        "prbj-testnet-exec-events.yml",
        "prcc-aws-export-smoke.yml",
        "prk-prj-status-report.yml",
        "pro-prk-nightly-selfcheck.yml",
        "pru-required-checks-drift-detector.yml",
        "real-market-forward-evidence-smoke.yml",
    }
)

RESIDUAL_INTENT_LABELS: dict[str, str] = {
    "residual_ci_ops": "Residual scheduled CI core / audit / PR-U drift (do not batch-remove)",
    "residual_scorecard_chain": "Residual PR-B / PR-K nightly scorecard and evidence chain",
    "residual_data_smoke": "Residual high-frequency market forward evidence smoke",
    "residual_all": "13 inventory workflows (6 active schedule + 7 manual-only; read-only)",
}

RESIDUAL_INTENT_TO_FILES: dict[str, tuple[str, ...]] = {
    "residual_ci_ops": (
        "ci.yml",
        "audit.yml",
        "pru-required-checks-drift-detector.yml",
    ),
    "residual_scorecard_chain": (
        "pro-prk-nightly-selfcheck.yml",
        "prk-prj-status-report.yml",
        "prbc-stability-gate.yml",
        "prbj-testnet-exec-events.yml",
        "prbg-execution-evidence.yml",
        "prbe-shadow-testnet-scorecard.yml",
        "prbi-live-pilot-scorecard.yml",
        "prbd-live-readiness-scorecard.yml",
        "prcc-aws-export-smoke.yml",
    ),
    "residual_data_smoke": ("real-market-forward-evidence-smoke.yml",),
}

INTENT_LABELS: dict[str, str] = {
    "paper_shadow_evidence": "Paper / shadow / scheduled-smoke orchestration",
    "paper_test_evidence": "Direct paper-tests-audit-evidence run",
    "health_suite": "Test health profiles and weekly core audit",
    "market_info_daily": "Market outlook and InfoStream (AI-capable)",
    "ops_hygiene": "Ops doctor, offline suites, knowledge extras",
    "docs_hygiene": "Docs reference full scan",
    "security_audit": "Weekly security and quality audit",
    "all": "All manual-only workflows in the PR #3896 set",
    **RESIDUAL_INTENT_LABELS,
}

INTENT_TO_FILES: dict[str, tuple[str, ...]] = {
    "paper_shadow_evidence": (
        "ci-scheduled-paper-and-export-smoke.yml",
        "class-a-shadow-paper-scheduled-probe-v1.yml",
        "prj-scheduled-shadow-paper-features-smoke.yml",
    ),
    "paper_test_evidence": (PAPER_TEST_EVIDENCE_FILE,),
    "health_suite": (
        "test-health-automation.yml",
        "test_health.yml",
        "weekly_core_audit.yml",
    ),
    "market_info_daily": (
        "infostream-automation.yml",
        "market_outlook_automation.yml",
    ),
    "ops_hygiene": (
        "offline_suites.yml",
        "ops_doctor_dashboard.yml",
        "ops_doctor_pages.yml",
        "knowledge_extras_chromadb.yml",
    ),
    "docs_hygiene": ("docs_reference_targets_fullscan_schedule.yml",),
    "security_audit": ("full_audit_weekly.yml",),
}

STATIC_META: dict[str, dict[str, Any]] = {
    "ci-scheduled-paper-and-export-smoke.yml": {
        "why": "Orchestrates paper-tests-audit-evidence and export-pack verify (former hourly schedule).",
        "risk": "medium — may dispatch child workflows; check PT_SCHEDULED_* vars and export secrets.",
        "variable_gates": "PT_SCHEDULED_PAPER_TESTS_ENABLED, PT_SCHEDULED_EXPORT_VERIFY_ENABLED",
        "ai": False,
    },
    "class-a-shadow-paper-scheduled-probe-v1.yml": {
        "why": "Class-A shadow/paper probe (former ~4x/day schedule).",
        "risk": "medium — shadow probe job; CLASS_A_SHADOW_PAPER_SCHEDULE_ENABLED var for gated jobs.",
        "variable_gates": "CLASS_A_SHADOW_PAPER_SCHEDULE_ENABLED (job if:)",
        "ai": False,
    },
    "prj-scheduled-shadow-paper-features-smoke.yml": {
        "why": "PR-J shadow/paper features smoke (former hourly schedule).",
        "risk": "medium — uses dispatch inputs for PT_ENABLED/ARMED; keep defaults safe.",
        "variable_gates": "PT_PRJ_FEATURES_SMOKE_ENABLED",
        "ai": False,
        "default_flags": {
            "enabled": "false",
            "armed": "false",
            "confirm_present": "false",
            "allow_double_play": "false",
            "allow_dynamic_leverage": "false",
            "strength": "1.0",
            "switch_score": "0.0",
        },
    },
    "test-health-automation.yml": {
        "why": "Full test-health automation suite (former nightly schedule).",
        "risk": "high — long-running matrix; use profile wisely.",
        "variable_gates": "",
        "ai": False,
        "default_flags": {
            "profile": "weekly_core",
            "skip_coverage_checks": "true",
            "fail_on_violations": "false",
        },
    },
    "test_health.yml": {
        "why": "Test health profiles; also runs on PR/push — manual dispatch for ad-hoc profile.",
        "risk": "medium-high depending on profile.",
        "variable_gates": "",
        "ai": False,
        "default_flags": {"profile": "daily_quick"},
    },
    "weekly_core_audit.yml": {
        "why": "Weekly core audit orchestration (former Monday schedule).",
        "risk": "low — dispatches other workflows.",
        "variable_gates": "",
        "ai": False,
        "default_flags": {"note": "weekly core audit"},
    },
    "infostream-automation.yml": {
        "why": "InfoStream cycle after TestHealth (former 03:15 UTC schedule).",
        "risk": "AI cost if skip_ai=false; requires PT_AI_MODELS_ENABLED / PT_PAPERTRAIL_READY for cycle.",
        "variable_gates": "PT_AI_MODELS_ENABLED, PT_PAPERTRAIL_READY",
        "ai": True,
        "default_flags": {"skip_ai": "true", "dry_run": "true"},
        "ai_note": "Prefer -f skip_ai=true unless explicit AI cost approval.",
    },
    "market_outlook_automation.yml": {
        "why": "MarketSentinel daily outlook (former 05:00 UTC schedule).",
        "risk": "AI cost — uses OPENAI_API_KEY; scheduled runs used --skip-llm in CI cron.",
        "variable_gates": "",
        "ai": True,
        "ai_note": "Confirm OPENAI usage / use repo skip-llm patterns before paid run.",
    },
    "offline_suites.yml": {
        "why": "Offline daily/weekly test suites (former schedule).",
        "risk": "medium-long runner time.",
        "variable_gates": "",
        "ai": False,
        "default_flags": {"suite_type": "daily"},
    },
    "ops_doctor_dashboard.yml": {
        "why": "Ops Doctor dashboard artifact (former Monday schedule).",
        "risk": "low",
        "variable_gates": "",
        "ai": False,
    },
    "ops_doctor_pages.yml": {
        "why": "Ops Doctor Pages publish (former Monday schedule).",
        "risk": "low — Pages deploy permissions.",
        "variable_gates": "",
        "ai": False,
    },
    "full_audit_weekly.yml": {
        "why": "Full security and quality audit (former weekly schedule).",
        "risk": "medium",
        "variable_gates": "",
        "ai": False,
    },
    "docs_reference_targets_fullscan_schedule.yml": {
        "why": "Repo-wide docs reference target scan (former Monday schedule).",
        "risk": "low-medium",
        "variable_gates": "",
        "ai": False,
    },
    "knowledge_extras_chromadb.yml": {
        "why": "Optional ChromaDB knowledge tests (former Monday schedule).",
        "risk": "medium — optional deps.",
        "variable_gates": "",
        "ai": False,
        "default_flags": {"reason": "manual trigger"},
    },
    PAPER_TEST_EVIDENCE_FILE: {
        "why": "Direct paper test audit evidence (downstream of scheduled orchestrator).",
        "risk": "medium — execution scope tests.",
        "variable_gates": "",
        "ai": False,
        "default_flags": {"scope": "execution", "note": "manual via recommender"},
    },
}

RESIDUAL_STATIC_META: dict[str, dict[str, Any]] = {
    "ci.yml": {
        "why": "Full Python matrix on PR/push/merge_group/workflow_dispatch (schedule removed GH-CI).",
        "risk": "HIGH — required-gate hybrid; schedule manual-only; dispatch/PR paths unchanged.",
        "variable_gates": "",
        "ai": False,
        "residual_schedule": False,
    },
    "audit.yml": {
        "why": "Weekly pip-audit + PR report validation (supplements PR runs).",
        "risk": "MEDIUM — CI_CORE hybrid; do not batch-remove.",
        "variable_gates": "",
        "ai": False,
        "residual_schedule": True,
    },
    "pru-required-checks-drift-detector.yml": {
        "why": "Weekly branch-protection vs required_status_checks reconciliation.",
        "risk": "ELEVATED — CI_OPS authority surface.",
        "variable_gates": "",
        "ai": False,
        "residual_schedule": True,
    },
    "pro-prk-nightly-selfcheck.yml": {
        "why": "Daily PR-K nightly self-check (mock JSON; safest future manual-only YAML candidate).",
        "risk": "LOW — mock-only; no secrets.",
        "variable_gates": "",
        "ai": False,
        "residual_schedule": True,
    },
    "prk-prj-status-report.yml": {
        "why": "PR-J status report (dispatch-only; schedule removed per signed PRK/PRBD Option B).",
        "risk": "MEDIUM — GitHub API read.",
        "variable_gates": "",
        "ai": False,
        "residual_schedule": True,
    },
    "prbc-stability-gate.yml": {
        "why": "Daily stability gate; upstream artifact for PR-B scorecards.",
        "risk": "ELEVATED — scorecard chain dependency.",
        "variable_gates": "",
        "ai": False,
        "residual_schedule": True,
    },
    "prbj-testnet-exec-events.yml": {
        "why": "Daily testnet exec events producer (orchestrator).",
        "risk": "BLOCKED when KRAKEN_TESTNET_CRON_ENABLED — testnet/runtime boundary.",
        "variable_gates": "vars.KRAKEN_TESTNET_CRON_ENABLED",
        "ai": False,
        "residual_schedule": True,
    },
    "prbg-execution-evidence.yml": {
        "why": "Daily execution evidence bundle (testnet-adjacent).",
        "risk": "BLOCKED — scorecard chain; testnet evidence surface.",
        "variable_gates": "",
        "ai": False,
        "residual_schedule": True,
    },
    "prbe-shadow-testnet-scorecard.yml": {
        "why": "Daily shadow/testnet readiness scorecard.",
        "risk": "BLOCKED — LIVE_SCORECARD semantics; not trading approval.",
        "variable_gates": "",
        "ai": False,
        "residual_schedule": True,
    },
    "prbi-live-pilot-scorecard.yml": {
        "why": "Daily live pilot scorecard (display/evidence only).",
        "risk": "BLOCKED — live-path naming; operator GO required.",
        "variable_gates": "",
        "ai": False,
        "residual_schedule": True,
    },
    "prbd-live-readiness-scorecard.yml": {
        "why": "Daily live readiness scorecard; downloads upstream artifacts.",
        "risk": "BLOCKED — chain dependency with prbc/prk/prbe.",
        "variable_gates": "",
        "ai": False,
        "residual_schedule": True,
    },
    "prcc-aws-export-smoke.yml": {
        "why": "AWS export smoke (dispatch-only; schedule removed per signed AWS policy).",
        "risk": "BLOCKED — AWS_READ secrets surface.",
        "variable_gates": "PT_* export secrets",
        "ai": False,
        "residual_schedule": True,
    },
    "real-market-forward-evidence-smoke.yml": {
        "why": "Kraken OHLCV forward evidence (4×/day schedule).",
        "risk": "HIGH — DATA_INGEST frequency; dry_run_execution in checks only.",
        "variable_gates": "",
        "ai": False,
        "residual_schedule": True,
    },
}


def _meta_for_file(filename: str) -> dict[str, Any]:
    return RESIDUAL_STATIC_META.get(filename) or STATIC_META.get(filename, {})


@dataclass
class WorkflowRecord:
    file: str
    name: str
    has_workflow_dispatch: bool
    has_active_schedule: bool
    input_keys: list[str]
    input_defaults: dict[str, str] = field(default_factory=dict)


def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required; install requirements.txt dependencies.")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _trigger_section(data: dict[str, Any]) -> dict[str, Any]:
    triggers = data.get("on")
    if triggers is None:
        triggers = data.get(True)
    if not isinstance(triggers, dict):
        return {}
    return triggers


def _parse_workflow_file(filename: str) -> WorkflowRecord:
    path = WORKFLOWS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing workflow file: {path}")

    data = _load_yaml(path)
    triggers = _trigger_section(data)
    has_dispatch = "workflow_dispatch" in triggers
    has_schedule = "schedule" in triggers

    input_keys: list[str] = []
    input_defaults: dict[str, str] = {}
    wd = triggers.get("workflow_dispatch")
    if isinstance(wd, dict):
        inputs = wd.get("inputs")
        if isinstance(inputs, dict):
            for key, spec in inputs.items():
                input_keys.append(str(key))
                if isinstance(spec, dict) and "default" in spec:
                    input_defaults[str(key)] = str(spec["default"])

    meta = _meta_for_file(filename)
    for key, val in (meta.get("default_flags") or {}).items():
        input_defaults[str(key)] = str(val)

    for key, val in list(input_defaults.items()):
        if val in ("True", "False"):
            input_defaults[key] = val.lower()

    wf_name = data.get("name")
    if not isinstance(wf_name, str) or not wf_name.strip():
        wf_name = filename

    return WorkflowRecord(
        file=filename,
        name=wf_name.strip(),
        has_workflow_dispatch=has_dispatch,
        has_active_schedule=has_schedule,
        input_keys=input_keys,
        input_defaults=input_defaults,
    )


def _files_for_intent(intent: str) -> list[str]:
    if intent == "all":
        files = sorted(MANUAL_ONLY_WORKFLOW_FILES)
        if (WORKFLOWS_DIR / PAPER_TEST_EVIDENCE_FILE).exists():
            files.append(PAPER_TEST_EVIDENCE_FILE)
        return files
    if intent == "residual_all":
        return sorted(RESIDUAL_SCHEDULE_WORKFLOW_FILES)
    if intent in RESIDUAL_INTENT_TO_FILES:
        return list(RESIDUAL_INTENT_TO_FILES[intent])
    return list(INTENT_TO_FILES[intent])


def _all_intent_ids() -> list[str]:
    return (
        sorted(INTENT_TO_FILES.keys())
        + sorted(RESIDUAL_INTENT_TO_FILES.keys())
        + [
            "all",
            "residual_all",
        ]
    )


def _build_gh_command(rec: WorkflowRecord, ref: str = "main") -> str:
    parts = [f'gh workflow run "{rec.name}"', f"--ref {ref}"]
    for key in rec.input_keys:
        if key in rec.input_defaults:
            parts.append(f"-f {key}={rec.input_defaults[key]}")
    return " ".join(parts)


def _recommendation_dict(rec: WorkflowRecord, include_commands: bool, ref: str) -> dict[str, Any]:
    meta = _meta_for_file(rec.file)
    item: dict[str, Any] = {
        "workflow_file": f".github/workflows/{rec.file}",
        "workflow_name": rec.name,
        "why_recommended": meta.get("why", "Listed for selected intent."),
        "cost_risk_note": meta.get("risk", "review runner time before dispatch."),
        "variable_gates": meta.get("variable_gates") or None,
        "ai_or_paid": bool(meta.get("ai")),
        "ai_note": meta.get("ai_note"),
        "has_active_schedule": rec.has_active_schedule,
        "residual_scheduled_workflow": rec.file in RESIDUAL_SCHEDULE_WORKFLOW_FILES,
        "operator_go_required": True,
    }
    if include_commands:
        item["suggested_command"] = _build_gh_command(rec, ref=ref)
    if rec.has_active_schedule:
        item["warning"] = (
            "Active cron schedule still enabled in YAML — recommender does not disable "
            "schedules; review cost/risk before any manual dispatch."
        )
    return item


def recommend(
    intent: str,
    *,
    include_commands: bool = False,
    ref: str = "main",
) -> dict[str, Any]:
    files = _files_for_intent(intent)
    recommendations: list[dict[str, Any]] = []
    errors: list[str] = []

    for filename in files:
        try:
            rec = _parse_workflow_file(filename)
        except (OSError, ValueError, yaml.YAMLError) as exc:  # type: ignore[union-attr]
            errors.append(f"{filename}: {exc}")
            continue

        if not rec.has_workflow_dispatch:
            errors.append(f"{filename}: missing workflow_dispatch")
            continue

        recommendations.append(_recommendation_dict(rec, include_commands, ref))

    return {
        "intent": intent,
        "intent_label": INTENT_LABELS.get(intent, intent),
        "guard": GUARD_BANNER,
        "schedule_reactivation": False,
        "executes_workflows": False,
        "workflow_dispatch_executed": False,
        "recommendations": recommendations,
        "errors": errors,
    }


def format_text(payload: dict[str, Any]) -> str:
    lines = [
        payload["guard"],
        "",
        f"Intent: {payload['intent']} — {payload['intent_label']}",
        "Cron/schedule is NOT reactivated by this CLI. Manual runs may incur Actions runner and provider costs.",
        "",
    ]
    if payload["errors"]:
        lines.append("Errors:")
        for err in payload["errors"]:
            lines.append(f"  - {err}")
        lines.append("")

    if not payload["recommendations"]:
        lines.append("No workflows matched.")
        return "\n".join(lines)

    for idx, rec in enumerate(payload["recommendations"], start=1):
        lines.append(f"{idx}. {rec['workflow_name']}")
        lines.append(f"   file: {rec['workflow_file']}")
        lines.append(f"   why: {rec['why_recommended']}")
        lines.append(f"   cost/risk: {rec['cost_risk_note']}")
        if rec.get("variable_gates"):
            lines.append(f"   variable gates: {rec['variable_gates']}")
        if rec.get("ai_or_paid"):
            lines.append(
                f"   AI/paid: yes — {rec.get('ai_note') or 'confirm cost before dispatch'}"
            )
        if rec.get("warning"):
            lines.append(f"   WARNING: {rec['warning']}")
        lines.append("   operator-GO: required before running any gh command")
        if "suggested_command" in rec:
            lines.append(f"   command (text only): {rec['suggested_command']}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recommend manual-only GitHub Actions workflows for an operator intent (read-only)."
    )
    parser.add_argument(
        "--intent",
        choices=_all_intent_ids(),
        help="Operator planning intent",
    )
    parser.add_argument(
        "--list-intents",
        action="store_true",
        help="Print supported intents and exit",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument(
        "--include-commands",
        action="store_true",
        help="Include suggested gh workflow run command lines (text only)",
    )
    parser.add_argument(
        "--ref",
        default="main",
        help="Git ref for suggested gh workflow run commands (default: main)",
    )
    args = parser.parse_args(argv)

    if args.list_intents:
        if args.json:
            intent_rows = [
                {"id": k, "label": INTENT_LABELS[k], "files": list(v)}
                for k, v in INTENT_TO_FILES.items()
            ]
            intent_rows.extend(
                {"id": k, "label": INTENT_LABELS[k], "files": list(v)}
                for k, v in RESIDUAL_INTENT_TO_FILES.items()
            )
            intent_rows.append(
                {
                    "id": "all",
                    "label": INTENT_LABELS["all"],
                    "files": _files_for_intent("all"),
                }
            )
            intent_rows.append(
                {
                    "id": "residual_all",
                    "label": INTENT_LABELS["residual_all"],
                    "files": _files_for_intent("residual_all"),
                }
            )
            print(
                json.dumps(
                    {
                        "intents": intent_rows,
                        "guard": GUARD_BANNER,
                        "residual_schedule_count": len(RESIDUAL_SCHEDULE_WORKFLOW_FILES),
                    },
                    indent=2,
                )
            )
        else:
            print(GUARD_BANNER)
            print()
            print("Supported intents:")
            for intent_id in sorted(INTENT_TO_FILES.keys()):
                print(f"  - {intent_id}: {INTENT_LABELS[intent_id]}")
            for intent_id in sorted(RESIDUAL_INTENT_TO_FILES.keys()):
                print(f"  - {intent_id}: {INTENT_LABELS[intent_id]}")
            print(f"  - all: {INTENT_LABELS['all']}")
            print(f"  - residual_all: {INTENT_LABELS['residual_all']}")
        return 0

    if not args.intent:
        parser.error("--intent is required unless --list-intents is set")

    payload = recommend(
        args.intent,
        include_commands=args.include_commands,
        ref=args.ref,
    )

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_text(payload))

    return 1 if payload["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
