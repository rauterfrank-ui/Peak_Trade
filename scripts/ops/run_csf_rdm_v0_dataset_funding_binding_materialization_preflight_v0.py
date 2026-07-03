#!/usr/bin/env python3
"""Run CSF/RDM v0 dataset/funding binding materialization preflight.

Bounded pre-evaluation gate only. Verifies explicit versioned dataset and funding bindings,
runs offline materialization preflight against staging, and persists durable evidence.
Does not execute economic evaluation, runtime, credentials, or order effects.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import primary_evidence_retention_v0 as retention  # noqa: E402
from src.research.csf_rdm_v0_dataset_funding_binding_materialization_preflight_v0 import (  # noqa: E402
    GO_TOKEN,
    PREFLIGHT_VERSION,
    PreflightTerminalStatus,
    preflight_result_to_dict,
    run_dataset_funding_binding_materialization_preflight_v0,
)

CONFIRM_GO = GO_TOKEN
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DEFAULT_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/extended_chronological_v1"
)
SCOPE_CLASSIFICATION = "BOUNDED_CSF_RDM_V0_DATASET_FUNDING_BINDING_MATERIALIZATION_PREFLIGHT_V0"
PROCESS_CLASSIFICATION = "OFFLINE_PRE_EVALUATION_PREFLIGHT_NO_EVALUATION"


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _resolve_origin_main(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def run_preflight_scope_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
    expected_origin_main_sha: str | None = None,
    binding_origin_main_sha: str | None = None,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR:confirm_go_token_required:{CONFIRM_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "research"
        / f"csf_rdm_v0_dataset_funding_binding_materialization_preflight_pr4812_v0_{ts_slug}"
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    preflight = run_dataset_funding_binding_materialization_preflight_v0(
        repo_root=_REPO_ROOT,
        staging_root=staging_root,
        expected_origin_main_sha=expected_origin_main_sha,
        binding_origin_main_sha=binding_origin_main_sha,
        env=os.environ,
    )
    preflight_payload = preflight_result_to_dict(preflight)

    verdict = preflight.status.value
    ready = preflight.ready_for_next_pre_evaluation_gate
    payload: dict[str, Any] = {
        "verdict": verdict,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "preflight_version": PREFLIGHT_VERSION,
        "go_token_consumed": CONFIRM_GO,
        "origin_main_binding": origin_main,
        "initial_head": subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip(),
        "primary_worktree": str(primary_worktree),
        "staging_root": str(staging_root),
        "preflight": preflight_payload,
        "ready_for_next_pre_evaluation_gate": ready,
        "economic_evaluation_executed": False,
        "economic_evaluation_blocked": True,
        "no_evaluation_retry": True,
        "no_runtime": True,
        "no_testnet": True,
        "no_shadow": True,
        "no_paper": True,
        "no_orders": True,
        "authority_effect": preflight.authority_effect,
        "runtime_effect": preflight.runtime_effect,
        "durable_evidence_path": str(bundle_dir),
        "safe_next_action": (
            "SEPARATE_OFFLINE_ECONOMIC_EVALUATION_RETRY_WITH_OPERATOR_GO_AFTER_MATERIALIZATION_COMPLETE"
            if ready
            else "SEPARATE_DATASET_MATERIALIZATION_OR_FUNDING_FETCH_SCOPE_BEFORE_EVALUATION_RETRY"
        ),
    }

    (bundle_dir / "PREFLIGHT_RESULT.json").write_text(
        json.dumps(preflight_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "SCOPE_AND_GO.txt").write_text(
        "\n".join(
            [
                f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
                f"PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}",
                f"GO_TOKEN={CONFIRM_GO}",
                "GO_TOKEN_CONSUMPTION=CONSUMED_ONCE",
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
                "# CSF/RDM v0 Dataset/Funding Binding Materialization Preflight",
                "",
                f"- Verdict: {verdict}",
                f"- Ready for next pre-evaluation gate: {ready}",
                "- Economic evaluation executed: false",
                f"- Origin/main binding: {origin_main}",
                f"- Staging root: {staging_root}",
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
                f"READY_FOR_NEXT_PRE_EVALUATION_GATE={'true' if ready else 'false'}",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                f"MANIFEST_VERIFY_RC={manifest_rc}",
                f"ORIGIN_MAIN_BINDING={origin_main}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    retention.finalize_durable_bundle_manifest(bundle_dir)

    if preflight.status is PreflightTerminalStatus.FAIL_CLOSED_SHA_GUARD:
        _die(f"ERR:sha_guard_failed:{preflight.reason_codes}", 1)
    if not ready:
        _die(f"ERR:preflight_not_ready:{verdict}:{preflight.reason_codes}", 1)

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--primary-worktree", type=Path, required=True)
    parser.add_argument("--staging-root", type=Path, default=DEFAULT_STAGING_ROOT)
    parser.add_argument("--expected-origin-main-sha", default=None)
    parser.add_argument("--binding-origin-main-sha", default=None)
    args = parser.parse_args()
    result = run_preflight_scope_v0(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        staging_root=args.staging_root,
        expected_origin_main_sha=args.expected_origin_main_sha,
        binding_origin_main_sha=args.binding_origin_main_sha,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
