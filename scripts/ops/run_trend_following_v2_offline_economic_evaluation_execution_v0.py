#!/usr/bin/env python3
"""Ops runner for trend_following v2 offline economic evaluation execution infrastructure.

Bounded infrastructure mode only:
- GO_TREND_FOLLOWING_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_V0

No runtime, order, or authority effect. No economic evaluation execution in this scope.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import primary_evidence_retention_v0 as retention  # noqa: E402
from src.research.trend_following_v2_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    EXECUTION_VERSION,
    INFRASTRUCTURE_GO_TOKEN,
    RUNTIME_EFFECT,
    entrypoint_result_to_dict,
    load_authorization_ratification_v0,
    load_versioned_research_binding_v0,
    materialize_infrastructure_summary_v0,
    run_contract_smoke_evaluation_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    verify_execution_start_state_v0,
)

INFRASTRUCTURE_GO = INFRASTRUCTURE_GO_TOKEN
SCOPE_CLASSIFICATION = (
    "BOUNDED_TREND_FOLLOWING_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_V0"
)
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
MAX_RUNTIME_SECONDS = 900


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


def _primary_worktree_snapshot(primary_worktree: Path) -> dict[str, Any]:
    head = subprocess.run(
        ["git", "-C", str(primary_worktree), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    dirty = subprocess.run(
        ["git", "-C", str(primary_worktree), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    dirty_count = len([line for line in dirty.stdout.splitlines() if line.strip()])
    return {
        "head": head.stdout.strip() if head.returncode == 0 else "",
        "dirty_count": dirty_count,
    }


def run_execution_infrastructure_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != INFRASTRUCTURE_GO:
        _die(f"ERR:confirm_go_token_required:{INFRASTRUCTURE_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "implementation"
        / (f"trend_following_v2_offline_economic_evaluation_execution_infrastructure_v0_{ts_slug}")
    )
    bundle_dir.mkdir(parents=True, exist_ok=True)

    versioned_binding = load_versioned_research_binding_v0(_REPO_ROOT)
    authorization_ratification = load_authorization_ratification_v0(_REPO_ROOT)
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )
    entrypoint = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        go_token=INFRASTRUCTURE_GO,
    )
    readiness = run_contract_smoke_evaluation_v0(
        repo_root=_REPO_ROOT,
        versioned_binding=versioned_binding,
        authorization_ratification=authorization_ratification,
    )
    entrypoint_payload = entrypoint_result_to_dict(entrypoint)
    summary = materialize_infrastructure_summary_v0(
        authorization_ratification=authorization_ratification,
        readiness=readiness,
        origin_main_sha=origin_main,
        execution_bundle_dir=str(bundle_dir),
    )

    (bundle_dir / "PREFLIGHT.txt").write_text(
        "\n".join(
            [
                f"ORIGIN_MAIN={origin_main}",
                f"PRIMARY_HEAD_BEFORE={primary_before['head']}",
                f"PRIMARY_DIRTY_COUNT_BEFORE={primary_before['dirty_count']}",
                f"START_STATE_VALID={start_state.valid}",
                f"START_STATE_FAIL_REASONS={list(start_state.fail_reasons)}",
                "ROOT_CAUSE=CANONICAL_ENTRY_POINT_AND_RUNNER_NOT_MATERIALIZED",
                f"REPAIR_SCOPE={SCOPE_CLASSIFICATION}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "EXECUTION_LOG.txt").write_text(
        "\n".join(
            [
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "EXECUTION_SCOPE=INFRASTRUCTURE_ONLY_V0",
                f"GO_TOKEN={confirm}",
                "GO_TOKEN_CONSUMPTION=CONSUMED_ONCE",
                f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "ENTRYPOINT_DRY_RUN_RESULT.json").write_text(
        json.dumps(entrypoint_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "INFRASTRUCTURE_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").write_text(
        "ECONOMIC_EVALUATION_EXECUTED=false\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    payload: dict[str, Any] = {
        "verdict": entrypoint_payload["status"],
        "process_classification": SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "start_state_valid": start_state.valid,
        "entrypoint": entrypoint_payload,
        "infrastructure_summary": summary,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree": str(primary_worktree),
        "durable_evidence_path": str(bundle_dir),
        "manifest_verify_rc": manifest_rc,
        "manifest_verify_msg": manifest_msg,
        "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
    }
    (bundle_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if time.monotonic() - start_monotonic > MAX_RUNTIME_SECONDS:
        _die(f"ERR:timeout_guard_exceeded:{MAX_RUNTIME_SECONDS}s")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--primary-worktree", type=Path, default=_REPO_ROOT)
    args = parser.parse_args()
    result = run_execution_infrastructure_v0(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
