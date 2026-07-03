#!/usr/bin/env python3
"""Run CSF/RDM v0 extended_chronological_v1 staging and bound funding panel materialization.

Bounded dataset/funding readiness scope only. Assesses canonical staging readiness,
runs PR #4812 preflight gate, and persists durable evidence. Does not execute
economic evaluation and does not auto-start Full-Universe OKX fetch.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import primary_evidence_retention_v0 as retention  # noqa: E402
from src.research.csf_rdm_v0_extended_chronological_v1_staging_funding_panel_materialization_v0 import (  # noqa: E402
    CANONICAL_DATASET_OWNER,
    CANONICAL_FUNDING_OWNER,
    CANONICAL_PREFLIGHT_OWNER,
    DEFAULT_STAGING_ROOT,
    CONFIRM_GO,
    MATERIALIZATION_VERSION,
    MaterializationScopeVerdict,
    load_materialization_binding_config_v0,
    materialization_scope_result_to_dict,
    run_materialization_scope_v0,
    staging_assessment_to_dict,
)

DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
SCOPE_CLASSIFICATION = (
    "BOUNDED_CSF_RDM_V0_EXTENDED_CHRONOLOGICAL_V1_STAGING_FUNDING_PANEL_MATERIALIZATION_V0"
)
PROCESS_CLASSIFICATION = "OFFLINE_DATASET_FUNDING_MATERIALIZATION_READINESS_NO_EVALUATION"


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _git_head(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def run_materialization_scope_cli_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
    binding_origin_main_sha: str | None = None,
    attempt_fetch: bool = False,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR:confirm_go_token_required:{CONFIRM_GO}")

    binding_config = load_materialization_binding_config_v0(_REPO_ROOT)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "research"
        / f"csf_rdm_v0_extended_chronological_v1_staging_funding_panel_materialization_v0_{ts_slug}"
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    scope_result = run_materialization_scope_v0(
        repo_root=_REPO_ROOT,
        staging_root=staging_root,
        durable_evidence_root=durable_evidence_root,
        binding_origin_main_sha=binding_origin_main_sha,
        attempt_fetch=attempt_fetch,
    )
    scope_payload = materialization_scope_result_to_dict(scope_result)
    initial_head = _git_head(_REPO_ROOT)
    ready = scope_result.ready_for_next_pre_evaluation_gate
    verdict = scope_result.verdict.value
    preflight_verdict = scope_result.preflight_status

    payload: dict[str, Any] = {
        "verdict": verdict,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "materialization_version": MATERIALIZATION_VERSION,
        "confirm_go_consumed": CONFIRM_GO,
        "initial_head": initial_head,
        "origin_main_binding": scope_result.origin_main_binding,
        "binding_origin_main_sha": scope_result.binding_origin_main_sha,
        "canonical_dataset_owner": CANONICAL_DATASET_OWNER,
        "canonical_funding_owner": CANONICAL_FUNDING_OWNER,
        "canonical_preflight_owner": CANONICAL_PREFLIGHT_OWNER,
        "reuse_decisions": scope_payload["reuse_decisions"],
        "binding_config": binding_config,
        "primary_worktree": str(primary_worktree),
        "staging_root": str(staging_root),
        "dataset_binding_status": (
            "BOUND" if scope_result.staging_assessment.materialization_ready else "NOT_MATERIALIZED"
        ),
        "funding_binding_status": (
            "BOUND" if scope_result.staging_assessment.materialization_ready else "NOT_MATERIALIZED"
        ),
        "preflight_verdict": preflight_verdict,
        "ready_for_next_pre_evaluation_gate": ready,
        "economic_evaluation_executed": False,
        "economic_evaluation_blocked": True,
        "no_evaluation_retry": True,
        "no_runtime": True,
        "no_testnet": True,
        "no_shadow": True,
        "no_paper": True,
        "no_orders": True,
        "fetch_auto_start_disabled": True,
        "full_universe_fetch_requires_explicit_go": True,
        "attempt_fetch_requested": attempt_fetch,
        "materialization_scope": scope_payload,
        "staging_assessment": staging_assessment_to_dict(scope_result.staging_assessment),
        "durable_evidence_path": str(bundle_dir),
        "safe_next_action": (
            "SEPARATE_OFFLINE_ECONOMIC_EVALUATION_RETRY_SCOPE_FOR_CSF_RDM_V0"
            if ready
            else "RESOLVE_EXPLICIT_MISSING_DATASET_OR_FUNDING_BINDING_PRECONDITION_BEFORE_EVALUATION_RETRY"
        ),
    }

    (bundle_dir / "MATERIALIZATION_SCOPE_RESULT.json").write_text(
        json.dumps(scope_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "PREFLIGHT_RESULT.json").write_text(
        json.dumps(scope_result.preflight_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "STAGING_ASSESSMENT.json").write_text(
        json.dumps(
            staging_assessment_to_dict(scope_result.staging_assessment), indent=2, sort_keys=True
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "REUSE_DECISIONS.json").write_text(
        json.dumps(scope_payload["reuse_decisions"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "SCOPE_AND_GO.txt").write_text(
        "\n".join(
            [
                f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
                f"PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}",
                f"CONFIRM_GO={CONFIRM_GO}",
                "CONFIRM_GO_CONSUMPTION=CONSUMED_ONCE",
                "NO_EVALUATION_RETRY=true",
                "NO_RUNTIME=true",
                "NO_TESTNET=true",
                "NO_SHADOW=true",
                "NO_PAPER=true",
                "NO_ORDERS=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "FINAL_REPORT.md").write_text(
        "\n".join(
            [
                "# CSF/RDM v0 Extended Chronological v1 Staging/Funding Materialization",
                "",
                f"- Verdict: {verdict}",
                f"- Preflight verdict: {preflight_verdict}",
                f"- Ready for next pre-evaluation gate: {ready}",
                f"- Origin/main binding: {scope_result.origin_main_binding}",
                f"- Staging root: {staging_root}",
                "",
                "## Missing preconditions" if not ready else "## Bindings complete",
                *(f"- {code}" for code in scope_result.reason_codes),
                "",
                "## Safety invariants",
                "- NO_EVALUATION_RETRY",
                "- NO_RUNTIME",
                "- NO_TESTNET",
                "- NO_SHADOW",
                "- NO_PAPER",
                "- NO_ORDERS",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    payload["manifest_verify_rc"] = manifest_rc
    payload["manifest_verify_msg"] = manifest_msg
    (bundle_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "MACHINE_SUMMARY.env").write_text(
        "\n".join(
            [
                f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
                f"VERDICT={verdict}",
                f"PREFLIGHT_VERDICT={preflight_verdict}",
                f"READY_FOR_NEXT_PRE_EVALUATION_GATE={'true' if ready else 'false'}",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                f"MANIFEST_VERIFY_RC={manifest_rc}",
                f"ORIGIN_MAIN_BINDING={scope_result.origin_main_binding}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    retention.finalize_durable_bundle_manifest(bundle_dir)

    if scope_result.verdict is not (
        MaterializationScopeVerdict.PREFLIGHT_GATE_PASS_READY_FOR_NEXT_PRE_EVALUATION_GATE
    ):
        _die(f"ERR:materialization_scope_not_ready:{verdict}:{scope_result.reason_codes}", 1)

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--primary-worktree", type=Path, required=True)
    parser.add_argument("--staging-root", type=Path, default=DEFAULT_STAGING_ROOT)
    parser.add_argument("--binding-origin-main-sha", default=None)
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Readiness-only assessment (default when --authorize-full-universe-fetch is omitted).",
    )
    parser.add_argument(
        "--authorize-full-universe-fetch",
        action="store_true",
        help=(
            "Explicitly request Full-Universe fetch authorization check. "
            "Not authorized in this scope; fails closed with "
            "FULL_UNIVERSE_FETCH_REQUIRES_EXPLICIT_OPERATOR_GO."
        ),
    )
    args = parser.parse_args()
    if args.no_fetch and args.authorize_full_universe_fetch:
        _die("ERR:conflicting_fetch_flags:--no-fetch and --authorize-full-universe-fetch")
    attempt_fetch = args.authorize_full_universe_fetch
    result = run_materialization_scope_cli_v0(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        staging_root=args.staging_root,
        binding_origin_main_sha=args.binding_origin_main_sha,
        attempt_fetch=attempt_fetch,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
