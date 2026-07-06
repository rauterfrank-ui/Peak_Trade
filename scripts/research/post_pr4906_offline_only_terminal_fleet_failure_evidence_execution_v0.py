#!/usr/bin/env python3
"""Execute post-PR4906 offline-only terminal fleet failure evidence execution v0.

Read-only classification over bound PR4905/PR4906 parent evidence for missing axes only.
No economic evaluation, no backtest/WF/MC/stress execution, no runtime authority.
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

CONFIRM_GO = "GO_OPERATOR_RATIFY_NEXT_OFFLINE_ONLY_RESEARCH_OR_EVIDENCE_EXECUTION_SCOPE_AFTER_POST_PR4905_TERMINAL_FAILURE_SCOPE_DEFINITION_V0"
SCOPE_ID = "post_pr4906_offline_only_terminal_fleet_failure_evidence_execution_v0"
EXECUTION_ID = "POST_PR4906_OFFLINE_ONLY_TERMINAL_FLEET_FAILURE_EVIDENCE_EXECUTION_V0"
EVIDENCE_CLASS_ID = EXECUTION_ID
PROCESS_CLASSIFICATION = (
    "POST_PR4906_OFFLINE_ONLY_TERMINAL_FLEET_FAILURE_RESEARCH_EVIDENCE_EXECUTION_V0"
)
SCOPE_CLASSIFICATION = "OFFLINE_ONLY_RESEARCH_EVIDENCE_EXECUTION_AFTER_POST_PR4905_TERMINAL_FLEET_FAILURE_SCOPE_DEFINITION_V0"
EXECUTION_STATUS = "OFFLINE_TERMINAL_FAILURE_EVIDENCE_EXECUTION_COMPLETE_V0"
NEXT_CANONICAL_STEP = "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_AFTER_POST_PR4906_OFFLINE_EVIDENCE_EXECUTION_V0"
DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/post_pr4906_offline_only_terminal_fleet_failure_evidence_execution_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "post_pr4906_offline_only_terminal_fleet_failure_evidence_execution_v0"
PARENT_PR4905_OUTPUT_SUFFIX = (
    "post_pr4904_v4_fleet_robustness_failure_decomposition_v0_20260706T042551Z"
)
PARENT_PR4905_CLOSEOUT_SUFFIX = "pr4905_squash_merge_closeout_20260706T043541Z"
PARENT_PR4906_CLOSEOUT_SUFFIX = (
    "post_pr4905_terminal_fleet_failure_next_scope_definition_merge_closeout_20260706T044625Z"
)
PARENT_EVALUATION_SUFFIX = (
    "post_v4_versioned_fleet_offline_economic_evaluation_execution_v0_20260706T040339Z"
)
PARENT_PR4905_MERGE_COMMIT = "87cea0b920a2e2f7ae37b9bbeeefe01d1f7d2c73"
PARENT_PR4906_MERGE_COMMIT = "4505030938f6a70391973f761fffb183443e9336"
FAILED_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
MISSING_AXES = (
    "long_short_contribution",
    "fee_slippage_funding_drag",
    "turnover_cost_drag_decomposition",
    "regime_bucket_stability_beyond_wf_windows",
    "instrument_concentration_contribution_beyond_rotation_metadata",
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


def _require_config_gates(config: dict[str, Any]) -> None:
    if config.get("scope_id") != SCOPE_ID:
        _die("ERR:config scope_id mismatch")
    if config.get("execution_id") != EXECUTION_ID:
        _die("ERR:config execution_id mismatch")
    if config.get("selected_class") != "F":
        _die("ERR:config selected_class must be F")
    if config.get("non_authorizing") is not True:
        _die("ERR:config non_authorizing must be true")
    for flag in (
        "economic_evaluation_authorized",
        "promotion_eligible",
        "runtime_rewire_admissible",
        "same_binding_retry_allowed",
        "failed_bindings_retry_allowed",
        "parameter_rescue_allowed",
        "threshold_lowering_allowed",
    ):
        if config.get(flag) is not False:
            _die(f"ERR:config {flag} must be false")


def _verify_source_manifest(source_ref: Path, log_path: Path) -> int:
    ok, msg = verify_manifest_sha256(source_ref)
    rc = 0 if ok else 1
    log_path.write_text(
        "\n".join(
            [
                f"SOURCE_EVIDENCE_REF={source_ref}",
                f"MANIFEST_VERIFY_RC={rc}",
                f"MANIFEST_VERIFY_MSG={msg or 'ok'}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return rc


def _wf_regime_classification(wf_payload: dict[str, Any]) -> dict[str, Any]:
    windows = wf_payload.get("windows", [])
    if not isinstance(windows, list) or not windows:
        return {
            "classification": "MISSING_EVIDENCE",
            "negative_oos_window_count": 0,
            "positive_oos_window_count": 0,
            "window_count": 0,
        }
    negative = 0
    positive = 0
    zero_trade = 0
    for window in windows:
        if not isinstance(window, dict):
            continue
        oos_return = float(window.get("oos_total_return", 0.0) or 0.0)
        oos_trades = int(window.get("oos_trade_count", 0) or 0)
        if oos_trades == 0:
            zero_trade += 1
        if oos_return < 0:
            negative += 1
        elif oos_return > 0:
            positive += 1
    total = len(windows)
    if negative > positive:
        classification = "TERMINAL_NEGATIVE"
    elif positive > negative:
        classification = "MIXED_INSTABILITY"
    else:
        classification = "INCONCLUSIVE_EVIDENCE"
    return {
        "classification": classification,
        "negative_oos_window_count": negative,
        "positive_oos_window_count": positive,
        "zero_trade_oos_window_count": zero_trade,
        "window_count": total,
    }


def _fee_drag_proxy(candidate_result: dict[str, Any]) -> dict[str, Any]:
    gross = float(candidate_result.get("gross_return", 0.0) or 0.0)
    net = float(candidate_result.get("net_return", 0.0) or 0.0)
    drag = gross - net
    if abs(drag) < 1e-12:
        classification = "COST_DRAG_NEGLIGIBLE_AT_AGGREGATE_LEVEL"
        rescue_path = "BLOCKED_NOT_PRIMARY_FAILURE_DRIVER"
    elif drag > 0 and net < 0 <= gross:
        classification = "COST_DRAG_MATERIAL_BUT_TERMINAL_EDGE_NEGATIVE"
        rescue_path = "BLOCKED_PARAMETER_OR_THRESHOLD_RESCUE"
    else:
        classification = "COST_DRAG_PRESENT_REQUIRES_DEDICATED_ARTIFACT"
        rescue_path = "BLOCKED_REQUIRES_NEW_OFFLINE_ARTIFACT_NOT_EVALUATION_RETRY"
    return {
        "classification": classification,
        "gross_return": gross,
        "net_return": net,
        "cost_drag_delta": drag,
        "rescue_path": rescue_path,
        "retry_allowed": False,
    }


def _classify_missing_axes(
    *,
    parent_decomposition: dict[str, Any],
    parent_evaluation_ref: Path,
) -> dict[str, Any]:
    per_candidate: dict[str, dict[str, Any]] = {}
    fleet_axis_summary: dict[str, str] = {}

    for candidate in FAILED_CANDIDATES:
        candidate_result_path = parent_evaluation_ref / f"CANDIDATE_RESULT_{candidate}.json"
        wf_path = parent_evaluation_ref / f"WALK_FORWARD_RESULTS_{candidate}.json"
        candidate_result = (
            _load_json(candidate_result_path) if candidate_result_path.is_file() else {}
        )
        wf_payload = _load_json(wf_path) if wf_path.is_file() else {}

        per_candidate[candidate] = {
            "long_short_contribution": {
                "classification": "MISSING_SOURCE_ARTIFACT",
                "detail": "trade_ledger_long_short_decomposition_not_materialized",
                "admissible_next_evidence_class": (
                    "TRADE_LEDGER_LONG_SHORT_DECOMPOSITION_OFFLINE_ARTIFACT_V0"
                ),
                "retry_allowed": False,
                "economic_evaluation_required": False,
            },
            "fee_slippage_funding_drag": _fee_drag_proxy(candidate_result),
            "turnover_cost_drag_decomposition": {
                "classification": "MISSING_SOURCE_ARTIFACT",
                "detail": "turnover_vs_gross_edge_artifact_not_materialized",
                "admissible_next_evidence_class": (
                    "TURNOVER_COST_DRAG_DECOMPOSITION_OFFLINE_ARTIFACT_V0"
                ),
                "retry_allowed": False,
                "economic_evaluation_required": False,
            },
            "regime_bucket_stability_beyond_wf_windows": {
                **_wf_regime_classification(wf_payload),
                "detail": "read_only_summary_from_existing_wf_windows_no_reexecution",
                "retry_allowed": False,
                "economic_evaluation_required": False,
            },
            "instrument_concentration_contribution_beyond_rotation_metadata": {
                "classification": "MISSING_SOURCE_ARTIFACT",
                "detail": "instrument_concentration_beyond_rotation_metadata_not_materialized",
                "admissible_next_evidence_class": (
                    "INSTRUMENT_CONCENTRATION_DECOMPOSITION_OFFLINE_ARTIFACT_V0"
                ),
                "retry_allowed": False,
                "economic_evaluation_required": False,
            },
        }

    for axis in MISSING_AXES:
        classes = {
            per_candidate[c][axis]["classification"]
            for c in FAILED_CANDIDATES
            if axis in per_candidate[c]
        }
        if all(value.startswith("MISSING") for value in classes):
            fleet_axis_summary[axis] = "MISSING_EVIDENCE"
        elif "TERMINAL_NEGATIVE" in classes:
            fleet_axis_summary[axis] = "TERMINAL_NEGATIVE"
        elif "COST_DRAG_MATERIAL_BUT_TERMINAL_EDGE_NEGATIVE" in classes:
            fleet_axis_summary[axis] = "TERMINAL_NEGATIVE"
        elif "MIXED_INSTABILITY" in classes:
            fleet_axis_summary[axis] = "MIXED_TERMINAL_NEGATIVE"
        elif "COST_DRAG_NEGLIGIBLE_AT_AGGREGATE_LEVEL" in classes:
            fleet_axis_summary[axis] = "REFUTED_AS_PRIMARY_RESCUE_PATH"
        else:
            fleet_axis_summary[axis] = "INCONCLUSIVE_EVIDENCE"

    return {
        "fleet_axis_summary": fleet_axis_summary,
        "per_candidate": per_candidate,
        "parent_decomposition_missing_inputs": parent_decomposition.get("missing_inputs", []),
        "terminal_failure_persists": True,
        "aggregate_result": parent_decomposition.get(
            "aggregate_result", "FLEET_ECONOMIC_VALIDITY_FAIL"
        ),
    }


def _build_candidate_failure_matrix(parent_decomposition: dict[str, Any]) -> dict[str, Any]:
    return {
        "aggregate_axis_summary": parent_decomposition.get("aggregate_axis_summary", {}),
        "aggregate_result": parent_decomposition.get("aggregate_result"),
        "failed_candidate_verdicts": parent_decomposition.get("failed_candidate_verdicts", {}),
        "failed_candidates": list(FAILED_CANDIDATES),
        "per_candidate_axis_results": parent_decomposition.get("per_candidate_axis_results", {}),
    }


def _build_non_retry_guard_matrix() -> dict[str, Any]:
    guards = {
        "unchanged_post_v4_hypothesis_v0_binding_retry": False,
        "same_binding_retry": False,
        "failed_binding_retry": False,
        "parameter_rescue": False,
        "threshold_lowering": False,
        "policy_change_to_reclassify_negative_evidence": False,
        "near_duplicate_archetype_retry": False,
        "economic_evaluation_retry": False,
        "promotion_candidate_creation": False,
        "runtime_authority_from_evidence": False,
    }
    return {
        "guards": guards,
        "all_guards_active": all(value is False for value in guards.values()),
        "rationale": (
            "Terminal post_v4_hypothesis_v0 fleet failure remains binding; "
            "missing-axis classification does not authorize rescue retries."
        ),
    }


def _build_admissible_next_scope_matrix(
    missing_axis_classification: dict[str, Any],
) -> dict[str, Any]:
    admissible = []
    blocked = [
        "A_UNMODIFIED_POST_V4_BINDING_REEXECUTION",
        "B_SAME_BINDINGS_NEW_SHA_ONLY",
        "D_NEW_VERSIONED_RESEARCH_SCOPE_WITH_FULL_BINDINGS_WITHOUT_NEW_HYPOTHESIS",
        "E_FAILURE_DECOMPOSITION_REEXECUTION",
        "F_ECONOMIC_EVALUATION_RESCUE",
        "G_RUNTIME_REWIRE",
        "H_NEAR_DUPLICATE_ARCHETYPE_RETRY",
    ]
    for axis, summary in missing_axis_classification["fleet_axis_summary"].items():
        if summary == "MISSING_EVIDENCE":
            admissible.append(
                {
                    "axis": axis,
                    "next_scope_class": "OFFLINE_ARTIFACT_MATERIALIZATION_ONLY",
                    "requires_separate_operator_go": True,
                    "economic_evaluation_allowed": False,
                }
            )
        elif summary in {"TERMINAL_NEGATIVE", "MIXED_TERMINAL_NEGATIVE"}:
            admissible.append(
                {
                    "axis": axis,
                    "next_scope_class": "READ_ONLY_ARTIFACT_OR_SCOPE_DEFINITION_ONLY",
                    "requires_separate_operator_go": True,
                    "economic_evaluation_allowed": False,
                }
            )
        else:
            admissible.append(
                {
                    "axis": axis,
                    "next_scope_class": "SCOPE_DEFINITION_ONLY_NO_RETRY",
                    "requires_separate_operator_go": True,
                    "economic_evaluation_allowed": False,
                }
            )
    return {
        "admissible_next_scopes": admissible,
        "blocked_scope_classes": blocked,
        "required_next_go_for_scope_definition": NEXT_CANONICAL_STEP,
        "runtime_promotion_allowed": False,
    }


def _collect_evidence_execution(
    *,
    config: dict[str, Any],
    parent_pr4905_output_ref: Path,
    parent_pr4905_closeout_ref: Path,
    parent_pr4906_closeout_ref: Path,
    parent_evaluation_ref: Path,
    parent_manifest_status: dict[str, int],
    git_snapshot: dict[str, str],
) -> dict[str, Any]:
    parent_decomposition = _load_json(parent_pr4905_output_ref / "FAILURE_DECOMPOSITION.json")
    scope_definition = _load_json(_REPO_ROOT / config["parent_scope_definition_config_ref"])
    missing_axis_classification = _classify_missing_axes(
        parent_decomposition=parent_decomposition,
        parent_evaluation_ref=parent_evaluation_ref,
    )

    authority_boundary = {
        "authority_effect": "NONE",
        "economic_evaluation_authorized": False,
        "economic_evaluation_executed": False,
        "backtest_executed": False,
        "walk_forward_run_executed": False,
        "monte_carlo_run_executed": False,
        "stress_run_executed": False,
        "live_authorized": False,
        "shadow_authorized": False,
        "paper_authorized": False,
        "testnet_authorized": False,
        "orders_allowed": False,
        "promotion_authority": False,
        "promotion_eligible": False,
        "runtime_authority": "NONE",
        "runtime_authority_created": False,
        "runtime_effect": "NONE",
        "runtime_rewire_admissible": False,
        "same_binding_retry_allowed": False,
        "failed_bindings_retry_allowed": False,
        "parameter_rescue_allowed": False,
        "threshold_lowering_allowed": False,
        "trading_effect": "NONE",
    }

    return {
        "aggregate_result": "FLEET_ECONOMIC_VALIDITY_FAIL",
        "aggregate_status": "FLEET_ECONOMIC_VALIDITY_FAIL",
        "authority_boundary": authority_boundary,
        "economic_validity_offline_gate_pass": False,
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "execution_id": EXECUTION_ID,
        "execution_status": EXECUTION_STATUS,
        "failed_candidates": list(FAILED_CANDIDATES),
        "fleet_status": "FAIL",
        "fleet_verdict": "FLEET_ECONOMIC_VALIDITY_FAIL",
        "git_snapshot": git_snapshot,
        "go_token_consumed": CONFIRM_GO,
        "historical_negative_evidence_mutated": False,
        "immutable_binding_retry_allowed": False,
        "missing_axes_targeted": list(MISSING_AXES),
        "new_candidates_ratified": False,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "same_binding_retry_allowed": False,
        "failed_bindings_retry_allowed": False,
        "parameter_rescue_allowed": False,
        "threshold_lowering_allowed": False,
        "parent_bindings": {
            "parent_pr4905_merge_commit": PARENT_PR4905_MERGE_COMMIT,
            "parent_pr4905_output_bundle": str(parent_pr4905_output_ref),
            "parent_pr4905_closeout_dir": str(parent_pr4905_closeout_ref),
            "parent_pr4906_merge_commit": PARENT_PR4906_MERGE_COMMIT,
            "parent_pr4906_closeout_dir": str(parent_pr4906_closeout_ref),
            "parent_evaluation_bundle": str(parent_evaluation_ref),
            "parent_scope_definition_id": scope_definition.get("scope_id"),
        },
        "parent_manifest_status": parent_manifest_status,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_id": SCOPE_ID,
        "selected_class": "F",
        "strategy_version": "post_v4_hypothesis_v0",
        "terminal_negative_evidence_unchanged": True,
        "terminal_failure_classification": missing_axis_classification,
        "candidate_failure_matrix": _build_candidate_failure_matrix(parent_decomposition),
        "non_retry_guard_matrix": _build_non_retry_guard_matrix(),
        "admissible_next_scope_matrix": _build_admissible_next_scope_matrix(
            missing_axis_classification
        ),
    }


def run_offline_terminal_failure_evidence_execution_v0(
    *,
    go_token: str,
    parent_pr4905_output_bundle: Path,
    parent_pr4905_closeout_dir: Path,
    parent_pr4906_closeout_dir: Path,
    parent_evaluation_bundle: Path,
    durable_archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    config_path: Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    if go_token != CONFIRM_GO:
        _die("ERR:invalid go token")

    if not config_path.is_file():
        _die(f"ERR:missing config: {config_path}")

    config = _load_json(config_path)
    _require_config_gates(config)

    for label, ref in (
        ("parent_pr4905_output_bundle", parent_pr4905_output_bundle),
        ("parent_pr4905_closeout_dir", parent_pr4905_closeout_dir),
        ("parent_pr4906_closeout_dir", parent_pr4906_closeout_dir),
        ("parent_evaluation_bundle", parent_evaluation_bundle),
    ):
        if not ref.is_dir():
            _die(f"ERR:missing {label}: {ref}")

    output_dir = durable_archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    manifest_status: dict[str, int] = {}
    for key, ref in (
        ("parent_pr4905_output_bundle", parent_pr4905_output_bundle),
        ("parent_pr4905_closeout_dir", parent_pr4905_closeout_dir),
        ("parent_pr4906_closeout_dir", parent_pr4906_closeout_dir),
        ("parent_evaluation_bundle", parent_evaluation_bundle),
    ):
        rc = _verify_source_manifest(ref, output_dir / f"{key}_manifest_verify.log")
        manifest_status[key] = rc
        if rc != 0:
            _die(f"ERR:manifest invalid for {key}: {ref}")

    git_snapshot = _git_snapshot()
    scope_definition = _load_json(_REPO_ROOT / config["parent_scope_definition_config_ref"])

    report = _collect_evidence_execution(
        config=config,
        parent_pr4905_output_ref=parent_pr4905_output_bundle,
        parent_pr4905_closeout_ref=parent_pr4905_closeout_dir,
        parent_pr4906_closeout_ref=parent_pr4906_closeout_dir,
        parent_evaluation_ref=parent_evaluation_bundle,
        parent_manifest_status=manifest_status,
        git_snapshot=git_snapshot,
    )
    report["durable_evidence_path"] = str(output_dir)

    parent_manifest_verification = {
        "manifest_verify_results": manifest_status,
        "all_parent_manifests_verified": all(rc == 0 for rc in manifest_status.values()),
        "parent_pr4905_merge_commit": PARENT_PR4905_MERGE_COMMIT,
        "parent_pr4906_merge_commit": PARENT_PR4906_MERGE_COMMIT,
    }
    bound_parent_scope_summary = {
        "parent_scope_definition_id": scope_definition.get("scope_id"),
        "parent_scope_definition_status": scope_definition.get("status"),
        "selected_next_scope_class": scope_definition.get("selected_next_scope_class"),
        "insufficient_source_evidence_axes": scope_definition.get(
            "insufficient_source_evidence_axes", []
        ),
        "required_next_go_for_execution": scope_definition.get("required_next_go_for_execution"),
        "fleet_verdict": scope_definition.get("fleet_verdict"),
        "economic_validity_offline_gate_pass": scope_definition.get(
            "economic_validity_offline_gate_pass"
        ),
    }
    execution_summary = {
        "verdict": EXECUTION_STATUS,
        "aggregate_result": report["aggregate_result"],
        "economic_validity_offline_gate_pass": False,
        "missing_axes_mapped": list(MISSING_AXES),
        "runtime_authority_created": False,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "go_token_consumed": CONFIRM_GO,
    }

    (output_dir / "parent_manifest_verification.json").write_text(
        json.dumps(parent_manifest_verification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "bound_parent_scope_summary.json").write_text(
        json.dumps(bound_parent_scope_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "terminal_failure_classification.json").write_text(
        json.dumps(report["terminal_failure_classification"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "candidate_failure_matrix.json").write_text(
        json.dumps(report["candidate_failure_matrix"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "non_retry_guard_matrix.json").write_text(
        json.dumps(report["non_retry_guard_matrix"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "admissible_next_scope_matrix.json").write_text(
        json.dumps(report["admissible_next_scope_matrix"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "execution_summary.json").write_text(
        json.dumps(execution_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "EVIDENCE_EXECUTION_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "EXECUTION_SUMMARY.md").write_text(
        "\n".join(
            [
                "# Offline Terminal Fleet Failure Evidence Execution Summary",
                "",
                f"- execution_status: `{EXECUTION_STATUS}`",
                f"- aggregate_result: `FLEET_ECONOMIC_VALIDITY_FAIL`",
                f"- economic_validity_offline_gate_pass: `false`",
                f"- missing_axes_targeted: `{','.join(MISSING_AXES)}`",
                f"- runtime_authority_created: `false`",
                f"- next_canonical_step: `{NEXT_CANONICAL_STEP}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    write_manifest_sha256(output_dir)
    ok, msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if ok else 1
    (output_dir / "MANIFEST_VERIFY.log").write_text(
        f"MANIFEST_VERIFY_RC={manifest_rc}\nMANIFEST_VERIFY_MSG={msg or 'ok'}\n",
        encoding="utf-8",
    )
    if manifest_rc != 0:
        _die(f"ERR:new evidence manifest verify failed: {output_dir}")

    report["manifest_verify_rc"] = manifest_rc
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute post-PR4906 offline-only terminal fleet failure evidence v0."
    )
    parser.add_argument("--go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--parent-pr4905-output-bundle", type=Path, required=True)
    parser.add_argument("--parent-pr4905-closeout-dir", type=Path, required=True)
    parser.add_argument("--parent-pr4906-closeout-dir", type=Path, required=True)
    parser.add_argument("--parent-evaluation-bundle", type=Path, required=True)
    parser.add_argument("--durable-archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()

    report = run_offline_terminal_failure_evidence_execution_v0(
        go_token=args.go_token,
        parent_pr4905_output_bundle=args.parent_pr4905_output_bundle,
        parent_pr4905_closeout_dir=args.parent_pr4905_closeout_dir,
        parent_pr4906_closeout_dir=args.parent_pr4906_closeout_dir,
        parent_evaluation_bundle=args.parent_evaluation_bundle,
        durable_archive_root=args.durable_archive_root,
        config_path=args.config,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    for key in (
        "execution_status",
        "durable_evidence_path",
        "manifest_verify_rc",
        "aggregate_result",
    ):
        print(f"{key.upper()}={report[key]}")


if __name__ == "__main__":
    main()
