#!/usr/bin/env python3
"""Re-run full offline economic evaluation for cross-sectional funding-rate carry v0.

Bounded pipeline: funding-panel materialization, manifest verification, bound dataset
materialization, full six-stage economic evaluation, durable evidence persistence.
Operator GO: GO_BOUNDED_CROSS_SECTIONAL_FUNDING_RATE_CARRY_V0_OFFLINE_ECONOMIC_EVALUATION_RE_RUN_V0
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
from scripts.ops.materialize_cross_sectional_funding_rate_carry_v0_bound_panel_funding_dataset_v0 import (  # noqa: E402
    materialize_bound_panel_funding_dataset_v0,
)
from src.research.cross_sectional_funding_rate_carry_v0_bound_panel_dataset_materialization_v0 import (  # noqa: E402
    MaterializationTerminalStatus,
    materialization_result_to_dict,
    materialize_bound_funding_panel_dataset_v0,
)
from src.research.cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    EXECUTION_VERSION,
    EXPECTED_ORIGIN_MAIN_SHA,
    FIXTURE_DATA_DIGEST,
    INFRASTRUCTURE_GO_TOKEN,
    RE_RUN_GO_TOKEN,
    RUNTIME_EFFECT,
    execution_result_to_dict,
    load_ohlcv_panel_series_for_backtest,
    load_versioned_research_binding_v0,
    run_full_offline_economic_evaluation_v0,
    verify_execution_start_state_v0,
)
from src.research.cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    materialize_funding_carry_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_panel_staging_source_manifest_v1 import (  # noqa: E402
    materialize_panel_staging_source_manifests_v1,
    source_manifest_result_to_dict,
    verify_panel_staging_source_manifests_v1,
)

CONFIRM_GO = RE_RUN_GO_TOKEN
_INFRA_GO = INFRASTRUCTURE_GO_TOKEN
MAX_RUNTIME_SECONDS = 1500
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DEFAULT_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/v1"
)
SCOPE_CLASSIFICATION = (
    "BOUNDED_CROSS_SECTIONAL_FUNDING_RATE_CARRY_V0_OFFLINE_ECONOMIC_EVALUATION_RE_RUN_V0"
)


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
    dirty_lines = [line for line in dirty.stdout.splitlines() if line.strip()]
    return {
        "head": head.stdout.strip() if head.returncode == 0 else "",
        "dirty_count": len(dirty_lines),
        "dirty_files": dirty_lines,
    }


def _guard_timeout(start_monotonic: float) -> None:
    if time.monotonic() - start_monotonic > MAX_RUNTIME_SECONDS:
        _die(f"ERR: timeout_guard_exceeded:{MAX_RUNTIME_SECONDS}s")


def run_offline_economic_evaluation_re_run_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
    skip_fetch: bool = False,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "implementation"
        / f"bounded_cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_re_run_v0_{ts_slug}"
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    prechecks = {
        "origin_main": origin_main,
        "expected_origin_main": EXPECTED_ORIGIN_MAIN_SHA,
        "origin_main_match": origin_main == EXPECTED_ORIGIN_MAIN_SHA,
        "primary_worktree_head": primary_before["head"],
        "primary_worktree_dirty_count": primary_before["dirty_count"],
        "primary_worktree_dirty_files": primary_before["dirty_files"],
        "confirm_go_alias": "CONFIRM_GO",
        "fixture_data_digest": FIXTURE_DATA_DIGEST,
        "staging_root": str(staging_root),
        "skip_fetch": skip_fetch,
    }
    (bundle_dir / "PRECHECKS.json").write_text(
        json.dumps(prechecks, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not prechecks["origin_main_match"]:
        _die("ERR: origin_main_mismatch_fail_closed")

    versioned_binding = load_versioned_research_binding_v0(_REPO_ROOT)
    ratification = materialize_funding_carry_offline_economic_evaluation_scope_ratification_v0(
        repo_root=_REPO_ROOT,
        versioned_binding=versioned_binding,
    )
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )
    _guard_timeout(start_monotonic)

    funding_materialize_result = materialize_bound_panel_funding_dataset_v0(
        confirm=_INFRA_GO,
        staging_root=staging_root,
        skip_fetch=skip_fetch,
    )
    (bundle_dir / "FUNDING_PANEL_MATERIALIZATION.json").write_text(
        json.dumps(funding_materialize_result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _guard_timeout(start_monotonic)

    manifest_result = materialize_panel_staging_source_manifests_v1(staging_root)
    manifest_ok, manifest_rc, manifest_reasons = verify_panel_staging_source_manifests_v1(
        staging_root
    )
    _guard_timeout(start_monotonic)

    materialization_a = materialize_bound_funding_panel_dataset_v0(
        staging_root,
        period_binding=versioned_binding["period_binding"],
        expected_data_digest=versioned_binding["data_digest"],
    )
    materialization_b = materialize_bound_funding_panel_dataset_v0(
        staging_root,
        period_binding=versioned_binding["period_binding"],
        expected_data_digest=versioned_binding["data_digest"],
    )
    rematerialization_match = (
        materialization_a.panel_data_digest == materialization_b.panel_data_digest
        and materialization_a.status == materialization_b.status
    )
    _guard_timeout(start_monotonic)

    evaluation_payload: dict[str, Any] | None = None
    evaluation = None
    if materialization_a.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE:
        panel_series = load_ohlcv_panel_series_for_backtest(staging_root)
        evaluation = run_full_offline_economic_evaluation_v0(
            repo_root=_REPO_ROOT,
            ratification=ratification,
            staging_root=staging_root,
            panel_series=panel_series,
            versioned_binding=versioned_binding,
            go_token=confirm,
        )
        evaluation_payload = execution_result_to_dict(evaluation)
        (bundle_dir / "ECONOMIC_VIABILITY_EVIDENCE_V1.json").write_text(
            json.dumps(evaluation.economic_viability_evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    _guard_timeout(start_monotonic)

    economic_executed = evaluation.economic_evaluation_executed if evaluation is not None else False
    economic_classification = (
        evaluation.economic_classification.value if evaluation is not None else "FAIL_CLOSED"
    )
    (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").write_text(
        f"ECONOMIC_EVALUATION_EXECUTED={'true' if economic_executed else 'false'}\n",
        encoding="utf-8",
    )

    primary_after = _primary_worktree_snapshot(primary_worktree)
    worktree_protected = (
        primary_before["head"] == primary_after["head"]
        and primary_before["dirty_count"] == primary_after["dirty_count"]
    )

    payload: dict[str, Any] = {
        "verdict": (
            evaluation_payload["status"] if evaluation_payload else "FAIL_CLOSED_DATASET_GATE"
        ),
        "process_classification": SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "staging_root": str(staging_root),
        "start_state_valid": start_state.valid,
        "source_manifests": source_manifest_result_to_dict(manifest_result),
        "manifest_verify_rc": manifest_rc,
        "manifest_verify_ok": manifest_ok,
        "manifest_verify_reasons": list(manifest_reasons),
        "dataset_materialization": materialization_result_to_dict(materialization_a),
        "deterministic_rematerialization_status": "PASS" if rematerialization_match else "FAIL",
        "rematerialization_digest_a": materialization_a.panel_data_digest,
        "rematerialization_digest_b": materialization_b.panel_data_digest,
        "evaluation": evaluation_payload,
        "economic_classification": economic_classification,
        "economic_evaluation_executed": economic_executed,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree_protected": worktree_protected,
        "primary_worktree_head_after": primary_after["head"],
        "primary_worktree_dirty_count_after": primary_after["dirty_count"],
        "durable_evidence_path": str(bundle_dir),
        "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
        "timeout_guard_seconds": MAX_RUNTIME_SECONDS,
    }
    (bundle_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    (bundle_dir / "GIT_PROVENANCE.txt").write_text(
        "\n".join(
            [
                f"WORKTREE_HEAD={subprocess.run(['git', '-C', str(_REPO_ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()}",
                f"ORIGIN_MAIN={origin_main}",
                f"PRIMARY_WORKTREE={primary_worktree}",
                f"PRIMARY_WORKTREE_HEAD_BEFORE={primary_before['head']}",
                f"PRIMARY_WORKTREE_DIRTY_COUNT_BEFORE={primary_before['dirty_count']}",
                f"PRIMARY_WORKTREE_HEAD_AFTER={primary_after['head']}",
                f"PRIMARY_WORKTREE_DIRTY_COUNT_AFTER={primary_after['dirty_count']}",
                f"PRIMARY_WORKTREE_PROTECTED={worktree_protected}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "SCOPE_AND_GO.txt").write_text(
        "\n".join(
            [
                "EXECUTION_SCOPE=FULL_OFFLINE_ECONOMIC_EVALUATION_RE_RUN_V0",
                "GO_TOKEN_ALIAS=CONFIRM_GO",
                "GO_TOKEN_CONSUMPTION=CONSUMED_ONCE",
                f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    stages_executed = (
        evaluation_payload is not None
        and evaluation_payload.get("economic_evaluation_executed") is True
        and len(evaluation_payload.get("stage_wiring", [])) == 6
    )
    final_report_lines = [
        "# Cross-Sectional Funding Rate Carry v0 Offline Economic Evaluation Re-Run",
        "",
        f"- Verdict: {payload['verdict']}",
        f"- Economic classification: {economic_classification}",
        f"- Economic evaluation executed: {economic_executed}",
        f"- Six stages wired: {stages_executed}",
        f"- Panel data digest: {materialization_a.panel_data_digest}",
        f"- Primary worktree protected: {worktree_protected}",
        "",
    ]
    if evaluation_payload:
        final_report_lines.extend(
            [
                "## Key metrics",
                f"- net_return: {evaluation_payload.get('net_return')}",
                f"- trade_count: {evaluation_payload.get('trade_count')}",
                f"- walk_forward_gate: {evaluation_payload.get('walk_forward_gate')}",
                f"- monte_carlo_gate: {evaluation_payload.get('monte_carlo_gate')}",
                f"- stress_gate: {evaluation_payload.get('stress_gate')}",
                f"- economic_validity_offline_gate_pass: {evaluation_payload.get('economic_validity_offline_gate_pass')}",
            ]
        )
    (bundle_dir / "FINAL_REPORT.md").write_text(
        "\n".join(final_report_lines) + "\n", encoding="utf-8"
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
                f"VERDICT={payload['verdict']}",
                f"ECONOMIC_CLASSIFICATION={economic_classification}",
                f"ECONOMIC_EVALUATION_EXECUTED={'true' if economic_executed else 'false'}",
                f"SIX_STAGES_EXECUTED={'true' if stages_executed else 'false'}",
                f"MANIFEST_VERIFY_RC={manifest_rc}",
                "DURABLE_SAVE_CONFIRMED=true",
                f"PRIMARY_WORKTREE_PROTECTED={'true' if worktree_protected else 'false'}",
                f"AUTHORITY_EFFECT={AUTHORITY_EFFECT}",
                f"RUNTIME_EFFECT={RUNTIME_EFFECT}",
                f"ELAPSED_SECONDS={payload['elapsed_seconds']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "SAFETY_INVARIANTS.env").write_text(
        "\n".join(
            [
                "RUNTIME_EFFECT=NONE",
                "ORDER_EFFECT=NONE",
                "AUTHORITY_EFFECT=NONE",
                "NO_LIVE_ACTIONS=true",
                "NO_CREDENTIALS=true",
                f"PRIMARY_WORKTREE_PROTECTED={'true' if worktree_protected else 'false'}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    retention.finalize_durable_bundle_manifest(bundle_dir)
    _guard_timeout(start_monotonic)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--primary-worktree", type=Path, required=True)
    parser.add_argument("--staging-root", type=Path, default=DEFAULT_STAGING_ROOT)
    parser.add_argument("--skip-fetch", action="store_true")
    args = parser.parse_args()
    result = run_offline_economic_evaluation_re_run_v0(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        staging_root=args.staging_root,
        skip_fetch=args.skip_fetch,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
