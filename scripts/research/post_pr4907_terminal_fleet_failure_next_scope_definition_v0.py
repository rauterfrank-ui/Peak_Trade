#!/usr/bin/env python3
"""Materialize post-PR4907 terminal fleet failure next scope definition v0.

Offline-only scope-definition evidence bundle. No economic evaluation, no evidence execution,
no runtime authority.
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

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    verify_manifest_sha256,
    write_manifest_sha256,
)

CONFIRM_GO = (
    "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_"
    "AFTER_POST_PR4906_OFFLINE_EVIDENCE_EXECUTION_V0"
)
SCOPE_ID = "POST_PR4907_TERMINAL_FLEET_FAILURE_NEXT_SCOPE_DEFINITION_V0"
PROCESS_CLASSIFICATION = "POST_PR4907_TERMINAL_FLEET_FAILURE_NEXT_SCOPE_DEFINITION_V0"
SCOPE_CLASSIFICATION = (
    "NEW_VERSIONED_RESEARCH_SCOPE_OR_EVIDENCE_CLASS_DEFINITION_ONLY_AFTER_TERMINAL_"
    "PR4907_FLEET_ECONOMIC_VALIDITY_FAIL_V0"
)
SELECTED_NEXT_SCOPE_CLASS = "OFFLINE_ARTIFACT_MATERIALIZATION_OR_EVIDENCE_CLASS_EXECUTION_REQUIRED"
NEXT_EXECUTION_GO = (
    "GO_OPERATOR_RATIFY_NEXT_OFFLINE_ONLY_ARTIFACT_MATERIALIZATION_OR_EVIDENCE_CLASS_"
    "EXECUTION_SCOPE_AFTER_POST_PR4907_TERMINAL_FAILURE_SCOPE_DEFINITION_V0"
)
DEFAULT_CONFIG = (
    _REPO_ROOT / "config/research/post_pr4907_terminal_fleet_failure_next_scope_definition_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "post_pr4907_terminal_fleet_failure_next_scope_definition_v0"
PARENT_PR4905_OUTPUT_SUFFIX = (
    "post_pr4904_v4_fleet_robustness_failure_decomposition_v0_20260706T042551Z"
)
PARENT_PR4905_CLOSEOUT_SUFFIX = "pr4905_squash_merge_closeout_20260706T043541Z"
PARENT_PR4906_CLOSEOUT_SUFFIX = (
    "post_pr4905_terminal_fleet_failure_next_scope_definition_merge_closeout_20260706T044625Z"
)
PARENT_PR4907_EVIDENCE_SUFFIX = (
    "post_pr4906_offline_only_terminal_fleet_failure_evidence_execution_v0_20260706T045000Z"
)
PARENT_PR4907_CLOSEOUT_SUFFIX = (
    "post_pr4906_offline_only_terminal_fleet_failure_evidence_execution_merge_closeout_"
    "20260706T045620Z"
)
PARENT_MANIFEST_SOURCES = (
    ("parent_pr4905_output_bundle", PARENT_PR4905_OUTPUT_SUFFIX),
    ("parent_pr4905_closeout_dir", PARENT_PR4905_CLOSEOUT_SUFFIX),
    ("parent_pr4906_closeout_dir", PARENT_PR4906_CLOSEOUT_SUFFIX),
    ("parent_pr4907_evidence_bundle", PARENT_PR4907_EVIDENCE_SUFFIX),
    ("parent_pr4907_closeout_dir", PARENT_PR4907_CLOSEOUT_SUFFIX),
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _die(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def _git_snapshot() -> dict[str, str]:
    def _run(args: list[str]) -> str:
        return subprocess.check_output(["git", *args], cwd=_REPO_ROOT, text=True).strip()

    return {
        "head": _run(["rev-parse", "HEAD"]),
        "origin_main": _run(["rev-parse", "origin/main"]),
        "branch": _run(["branch", "--show-current"]),
        "status_short": _run(["status", "--short"]) or "(clean)",
    }


def _verify_source_manifest(source_dir: Path, log_path: Path) -> int:
    ok, msg = verify_manifest_sha256(source_dir)
    rc = 0 if ok else 1
    log_path.write_text(
        f"MANIFEST_VERIFY_RC={rc}\nMANIFEST_VERIFY_MSG={msg or 'ok'}\nSOURCE={source_dir}\n",
        encoding="utf-8",
    )
    return rc


def _write_authority_boundary(output_dir: Path) -> None:
    output_dir.joinpath("AUTHORITY_BOUNDARY.txt").write_text(
        "\n".join(
            [
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "OFFLINE_EVALUATION_EXECUTED=false",
                "ECONOMIC_EVALUATION_AUTHORIZED=false",
                "BACKTEST_EXECUTED=false",
                "EVIDENCE_EXECUTION_AUTHORIZED=false",
                "EVIDENCE_EXECUTED=false",
                "EVIDENCE_EXECUTION_IN_THIS_SCOPE=false",
                "RUNTIME_AUTHORITY=NONE",
                "RUNTIME_AUTHORITY_CREATED=false",
                "FAILED_BINDINGS_RETRY_ALLOWED=false",
                "UNCHANGED_RETRY_ALLOWED=false",
                "POLICY_THRESHOLD_RESCUE_ALLOWED=false",
                "FAILED_EVIDENCE_IS_TERMINAL=true",
                "NEW_CANDIDATES_RATIFIED=false",
                "PROMOTION_AUTHORITY=false",
                "SHADOW_AUTHORIZED=false",
                "PAPER_AUTHORIZED=false",
                "TESTNET_AUTHORIZED=false",
                "LIVE_AUTHORIZED=false",
                "ORDERS_ALLOWED=false",
                "BOUNDARIES=NO_RUNTIME_NO_SHADOW_NO_PAPER_NO_TESTNET_NO_ORDERS_NO_LIVE",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_terminal_failure_summary_md(output_dir: Path) -> None:
    output_dir.joinpath("TERMINAL_FAILURE_SUMMARY.md").write_text(
        "\n".join(
            [
                "# Terminal Failure Summary",
                "",
                "## Fleet verdict",
                "",
                "- fleet_verdict: `FLEET_ECONOMIC_VALIDITY_FAIL`",
                "- parent_pr4907_aggregate_result: `FLEET_ECONOMIC_VALIDITY_FAIL`",
                "- economic_validity_offline_gate_pass: `false`",
                "- failed_evidence_is_terminal: `true`",
                "",
                "## Candidate verdicts (immutable)",
                "",
                "- trend_following/post_v4_hypothesis_v0: `ROBUSTNESS_FAILED`",
                "- bollinger_bands/post_v4_hypothesis_v0: `ROBUSTNESS_FAILED`",
                "- momentum_1h/post_v4_hypothesis_v0: `ROBUSTNESS_FAILED`",
                "",
                "## PR4907 evidence execution axis outcomes",
                "",
                "- long_short_contribution: `MISSING_SOURCE_ARTIFACT`",
                "- fee_slippage_funding_drag: `REFUTED_AS_PRIMARY_RESCUE_PATH`",
                "- turnover_cost_drag_decomposition: `MISSING_SOURCE_ARTIFACT`",
                "- regime_bucket_stability_beyond_wf_windows: `INCONCLUSIVE_EVIDENCE`",
                "- instrument_concentration_contribution_beyond_rotation_metadata: `MISSING_SOURCE_ARTIFACT`",
                "",
                "## Blocked paths",
                "",
                "- unchanged post_v4_hypothesis_v0 binding retry: `BLOCKED`",
                "- parameter rescue: `BLOCKED`",
                "- threshold lowering: `BLOCKED`",
                "- policy threshold rescue: `BLOCKED`",
                "- economic evaluation rescue: `BLOCKED`",
                "- policy change to reclassify negative evidence: `BLOCKED`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_admissibility_matrix_md(output_dir: Path) -> None:
    output_dir.joinpath("ADMISSIBILITY_MATRIX.md").write_text(
        "\n".join(
            [
                "# Admissibility Matrix",
                "",
                "| Scope class | Status |",
                "|---|---|",
                "| A_UNMODIFIED_POST_V4_BINDING_REEXECUTION | BLOCKED |",
                "| B_SAME_BINDINGS_NEW_SHA_ONLY | BLOCKED |",
                "| C_GOVERNANCE_REWORDING_ONLY | BLOCKED |",
                "| D_NEW_VERSIONED_RESEARCH_SCOPE_WITH_FULL_BINDINGS_WITHOUT_NEW_HYPOTHESIS | BLOCKED |",
                "| E_FAILURE_DECOMPOSITION_REEXECUTION | BLOCKED |",
                "| F_ECONOMIC_EVALUATION_RESCUE | BLOCKED |",
                "| F_OFFLINE_ONLY_RESEARCH_OR_EVIDENCE_EXECUTION_REEXECUTION | BLOCKED |",
                "| G_RUNTIME_REWIRE | BLOCKED |",
                "| H_NEAR_DUPLICATE_ARCHETYPE_RETRY | BLOCKED |",
                "| I_OFFLINE_ARTIFACT_MATERIALIZATION_OR_EVIDENCE_CLASS_AFTER_TERMINAL_PR4907_FLEET_FAILURE_EVIDENCE_EXECUTION_V0 | ADMISSIBLE_NEXT_SCOPE |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def run_scope_definition_materialization_v0(
    *,
    confirm_go_token: str,
    config_path: Path = DEFAULT_CONFIG,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
) -> dict[str, Any]:
    if confirm_go_token != CONFIRM_GO:
        _die("ERR:invalid confirm go token")

    if not config_path.is_file():
        _die(f"ERR:missing config: {config_path}")

    config = _load_json(config_path)
    output_dir = archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    parent_manifest_results: dict[str, int] = {}
    for label, suffix in PARENT_MANIFEST_SOURCES:
        source_dir = archive_root / "implementation" / suffix
        if not source_dir.is_dir():
            _die(f"ERR:missing parent source dir: {source_dir}")
        rc = _verify_source_manifest(source_dir, output_dir / f"{label}_manifest_verify.log")
        parent_manifest_results[label] = rc
        if rc != 0:
            _die(f"ERR:parent manifest invalid: {source_dir}")

    git_snapshot = _git_snapshot()
    (output_dir / "scope_definition_v0.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "git_snapshot.json").write_text(
        json.dumps(git_snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "parent_manifest_verification.json").write_text(
        json.dumps(parent_manifest_results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "go_token_consumption.json").write_text(
        json.dumps(
            {
                "consumed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "go_token": CONFIRM_GO,
                "go_token_consumed": True,
                "go_token_consumption": "CONSUMED_ONCE_FOR_SCOPE_DEFINITION_ONLY",
                "scope_id": SCOPE_ID,
                "process_classification": PROCESS_CLASSIFICATION,
                "scope_classification": SCOPE_CLASSIFICATION,
                "selected_next_scope_class": SELECTED_NEXT_SCOPE_CLASS,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    output_dir.joinpath("NEXT_EXECUTION_GO_TOKEN.txt").write_text(
        f"{NEXT_EXECUTION_GO}\n",
        encoding="utf-8",
    )

    commands = [
        f"python3 {__file__} --confirm-go-token {CONFIRM_GO}",
        f"OUTPUT_DIR={output_dir}",
    ]
    (output_dir / "COMMAND_LOG.md").write_text(
        "\n".join(["# Command Log", ""] + [f"- `{line}`" for line in commands]) + "\n",
        encoding="utf-8",
    )
    (output_dir / "SCOPE_DEFINITION_REPORT.md").write_text(
        "\n".join(
            [
                "# Scope Definition Report",
                "",
                f"- scope_id: `{SCOPE_ID}`",
                f"- process_classification: `{PROCESS_CLASSIFICATION}`",
                f"- scope_classification: `{SCOPE_CLASSIFICATION}`",
                f"- selected_class: `{config.get('selected_class')}`",
                f"- selected_next_scope_class: `{SELECTED_NEXT_SCOPE_CLASS}`",
                f"- fleet_verdict: `{config.get('fleet_verdict')}`",
                f"- parent_pr4907_aggregate_result: `{config.get('parent_pr4907_aggregate_result')}`",
                f"- failed_evidence_is_terminal: `{config.get('failed_evidence_is_terminal')}`",
                f"- required_next_go_for_execution: `{config.get('required_next_go_for_execution')}`",
                f"- verdict: `SCOPE_DEFINED_NOT_EXECUTED`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_terminal_failure_summary_md(output_dir)
    _write_admissibility_matrix_md(output_dir)
    _write_authority_boundary(output_dir)

    write_manifest_sha256(output_dir)
    manifest_rc = 0 if verify_manifest_sha256(output_dir)[0] else 1
    if manifest_rc != 0:
        _die(f"ERR:manifest verify failed: {output_dir}")

    return {
        "verdict": "SCOPE_DEFINED_NOT_EXECUTED",
        "scope_id": SCOPE_ID,
        "selected_next_scope_class": SELECTED_NEXT_SCOPE_CLASS,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "next_execution_go_token": NEXT_EXECUTION_GO,
        "durable_evidence_path": str(output_dir),
        "manifest_verify_rc": manifest_rc,
        "parent_manifest_verify_results": parent_manifest_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize post-PR4907 terminal fleet failure next scope definition v0"
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()

    result = run_scope_definition_materialization_v0(
        confirm_go_token=args.confirm_go_token,
        archive_root=args.durable_evidence_root,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    for key, value in result.items():
        print(f"{key.upper()}={value}")


if __name__ == "__main__":
    main()
