#!/usr/bin/env python3
"""Run OKX full-panel cross-sectional ranking strategy archetype offline economic evaluation v0.

Bounded pipeline: binding digest verification, promoted dataset gate, full-panel panel
materialization, six-stage economic evaluation, durable evidence persistence.
Operator GO: GO_OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_BOUNDED_OFFLINE_ECONOMIC_EVALUATION_V0
"""

from __future__ import annotations

import argparse
import json
import os
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
from src.research.cross_sectional_panel_economic_evaluation_wiring_v0 import (  # noqa: E402
    robustness_results_to_dict,
)
from src.research.okx_full_panel_cross_sectional_ranking_strategy_archetype_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    BOUND_DATASET_CONTENT_DIGEST,
    DEFAULT_STAGING_REL,
    EXECUTION_VERSION,
    EXPECTED_ORIGIN_MAIN_SHA,
    GO_TOKEN,
    RUNTIME_EFFECT,
    build_evaluation_envelope_v0,
    execution_result_to_dict,
    load_archetype_bindings_v0,
    load_execution_scope_v0,
    load_ops_evaluation_config_v0,
    origin_main_sha_guard_to_dict,
    run_full_offline_economic_evaluation_v0,
    verify_origin_main_sha_guard_v0,
)

CONFIRM_GO = GO_TOKEN
MAX_RUNTIME_SECONDS = 1500
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
SCOPE_CLASSIFICATION = (
    "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_"
    "BOUNDED_OFFLINE_ECONOMIC_EVALUATION_V0"
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


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


def run_offline_economic_evaluation_execution_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
    expected_origin_main_sha: str | None = None,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    sha_guard = verify_origin_main_sha_guard_v0(
        repo_root=_REPO_ROOT,
        expected_origin_main_sha=expected_origin_main_sha,
        env=os.environ,
    )
    origin_main = sha_guard.actual_origin_main_sha
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "implementation"
        / f"okx_full_panel_cross_sectional_ranking_strategy_archetype_bounded_offline_economic_evaluation_v0_{ts_slug}"
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    bindings = load_archetype_bindings_v0(_REPO_ROOT)
    scope = load_execution_scope_v0(_REPO_ROOT)
    ops_config = load_ops_evaluation_config_v0(_REPO_ROOT)
    envelope = build_evaluation_envelope_v0(bindings, scope)

    prechecks = {
        "origin_main": origin_main,
        "expected_origin_main_sha": sha_guard.expected_origin_main_sha,
        "origin_main_sha_guard": origin_main_sha_guard_to_dict(sha_guard),
        "origin_main_match": sha_guard.passed,
        "primary_worktree_head": primary_before["head"],
        "primary_worktree_dirty_count": primary_before["dirty_count"],
        "primary_worktree_dirty_files": primary_before["dirty_files"],
        "go_token": confirm,
        "bound_dataset_content_digest": BOUND_DATASET_CONTENT_DIGEST,
        "staging_root": str(staging_root),
        "eligible_instrument_count": bindings["instrument_panel_binding"][
            "eligible_instrument_count"
        ],
    }
    (bundle_dir / "PRECHECKS.json").write_text(
        json.dumps(prechecks, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not sha_guard.passed:
        _die(f"ERR:origin_main_sha_guard_failed:{sha_guard.fail_reasons}")

    _guard_timeout(start_monotonic)
    evaluation = run_full_offline_economic_evaluation_v0(
        repo_root=_REPO_ROOT,
        durable_archive_root=durable_evidence_root,
        staging_root=staging_root,
        go_token=confirm,
        expected_origin_main_sha=expected_origin_main_sha,
    )
    evaluation_payload = execution_result_to_dict(evaluation)
    _guard_timeout(start_monotonic)

    binding_digests = {
        "binding_config_digest": scope["binding_config_digest"],
        "scope_ratification_digest": scope["scope_ratification_digest"],
        "dataset_content_digest": BOUND_DATASET_CONTENT_DIGEST,
        "promoted_dataset_content_digest": evaluation.promoted_dataset_content_digest,
        "panel_data_digest": evaluation.panel_data_digest,
        "implementation_digests": scope["implementation_digests"],
        "config_digests": scope["config_digests"],
    }
    (bundle_dir / "BINDING_DIGESTS.json").write_text(
        json.dumps(binding_digests, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "EVALUATION_CONFIG_RESOLVED.json").write_text(
        json.dumps(
            {
                "envelope": envelope,
                "ops_config": ops_config,
                "execution_scope_id": scope["scope_id"],
                "evidence_class_id": scope["evidence_class_id"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    metrics = {
        "net_return": evaluation_payload.get("net_return"),
        "net_expectancy": evaluation_payload.get("net_expectancy"),
        "profit_factor": evaluation_payload.get("profit_factor"),
        "sharpe": evaluation_payload.get("sharpe"),
        "max_drawdown": evaluation_payload.get("max_drawdown"),
        "trade_count": evaluation_payload.get("trade_count"),
        "fee_drag": evaluation_payload.get("fee_drag"),
        "slippage_impact": evaluation_payload.get("slippage_impact"),
        "funding_drag": evaluation_payload.get("funding_drag"),
        "walk_forward_status": evaluation_payload.get("walk_forward_status"),
        "monte_carlo_status": evaluation_payload.get("monte_carlo_status"),
        "stress_status": evaluation_payload.get("stress_status"),
        "parameter_sensitivity_status": evaluation_payload.get("parameter_sensitivity_status"),
        "verdict_classification": evaluation_payload.get("verdict_classification"),
        "economic_validity_offline_gate_pass": evaluation_payload.get(
            "economic_validity_offline_gate_pass"
        ),
    }
    (bundle_dir / "METRICS.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    robustness_dict = (
        robustness_results_to_dict(evaluation.robustness)
        if evaluation.robustness is not None
        else {}
    )
    (bundle_dir / "WALK_FORWARD_RESULTS.json").write_text(
        json.dumps(
            robustness_dict.get(
                "walk_forward_results",
                {"status": "FAIL_CLOSED", "reason_codes": evaluation.reason_codes},
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "MONTE_CARLO_RESULTS.json").write_text(
        json.dumps(
            robustness_dict.get(
                "monte_carlo_results",
                {"status": "FAIL_CLOSED", "reason_codes": evaluation.reason_codes},
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "STRESS_RESULTS.json").write_text(
        json.dumps(
            robustness_dict.get(
                "stress_results", {"status": "FAIL_CLOSED", "reason_codes": evaluation.reason_codes}
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "PARAMETER_SENSITIVITY_RESULTS.json").write_text(
        json.dumps(
            robustness_dict.get(
                "parameter_sensitivity_results",
                {"status": "FAIL_CLOSED", "reason_codes": evaluation.reason_codes},
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "ECONOMIC_VIABILITY_EVIDENCE_V1.json").write_text(
        json.dumps(evaluation.economic_viability_evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    primary_after = _primary_worktree_snapshot(primary_worktree)
    worktree_protected = (
        primary_before["head"] == primary_after["head"]
        and primary_before["dirty_count"] == primary_after["dirty_count"]
    )

    summary_lines = [
        "# OKX Full-Panel Cross-Sectional Ranking Strategy Archetype Bounded Offline Economic Evaluation v0",
        "",
        f"- Verdict: {evaluation_payload.get('verdict_classification')}",
        f"- Status: {evaluation_payload.get('status')}",
        f"- Economic evaluation executed: {evaluation_payload.get('economic_evaluation_executed')}",
        f"- Economic validity offline gate pass: {evaluation_payload.get('economic_validity_offline_gate_pass')}",
        f"- Authority effect: {AUTHORITY_EFFECT}",
        f"- Runtime effect: {RUNTIME_EFFECT}",
        f"- Promotion candidate eligible: false",
        f"- Panel data digest: {evaluation.panel_data_digest}",
        f"- Promoted dataset content digest: {evaluation.promoted_dataset_content_digest}",
        f"- Primary worktree protected: {worktree_protected}",
        "",
        "## Key metrics",
        f"- net_return: {metrics['net_return']}",
        f"- net_expectancy: {metrics['net_expectancy']}",
        f"- profit_factor: {metrics['profit_factor']}",
        f"- sharpe: {metrics['sharpe']}",
        f"- max_drawdown: {metrics['max_drawdown']}",
        f"- trade_count: {metrics['trade_count']}",
        f"- fee_drag: {metrics['fee_drag']}",
        f"- slippage_impact: {metrics['slippage_impact']}",
        f"- funding_drag: {metrics['funding_drag']}",
        f"- walk_forward_status: {metrics['walk_forward_status']}",
        f"- monte_carlo_status: {metrics['monte_carlo_status']}",
        f"- stress_status: {metrics['stress_status']}",
        f"- parameter_sensitivity_status: {metrics['parameter_sensitivity_status']}",
        "",
        "## Authority boundaries",
        "- No runtime / no shadow / no paper / no testnet / no orders / no promotion",
        f"- GO_TOKEN consumed: {CONFIRM_GO}",
        f"- HEAD/origin/main: {origin_main}",
    ]
    (bundle_dir / "EXECUTION_SUMMARY.md").write_text(
        "\n".join(summary_lines) + "\n", encoding="utf-8"
    )

    payload: dict[str, Any] = {
        "verdict": evaluation_payload.get("verdict_classification"),
        "process_classification": SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "go_token_consumed": CONFIRM_GO,
        "origin_main": origin_main,
        "expected_origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
        "staging_root": str(staging_root),
        "evaluation": evaluation_payload,
        "metrics": metrics,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree_protected": worktree_protected,
        "durable_evidence_path": str(bundle_dir),
        "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
        "timeout_guard_seconds": MAX_RUNTIME_SECONDS,
    }
    (bundle_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    payload["manifest_verify_rc"] = manifest_rc
    payload["manifest_verify_msg"] = manifest_msg
    (bundle_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "OKX full-panel cross-sectional ranking strategy archetype "
            "bounded offline economic evaluation v0"
        )
    )
    parser.add_argument("--confirm", required=True, help=f"Operator GO token ({CONFIRM_GO})")
    parser.add_argument(
        "--durable-evidence-root",
        type=Path,
        default=DEFAULT_DURABLE_ROOT,
    )
    parser.add_argument(
        "--primary-worktree",
        type=Path,
        default=_REPO_ROOT,
    )
    parser.add_argument(
        "--staging-root",
        type=Path,
        default=DEFAULT_DURABLE_ROOT / DEFAULT_STAGING_REL,
    )
    parser.add_argument(
        "--expected-origin-main-sha",
        default=EXPECTED_ORIGIN_MAIN_SHA,
    )
    args = parser.parse_args()

    result = run_offline_economic_evaluation_execution_v0(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        staging_root=args.staging_root,
        expected_origin_main_sha=args.expected_origin_main_sha,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
