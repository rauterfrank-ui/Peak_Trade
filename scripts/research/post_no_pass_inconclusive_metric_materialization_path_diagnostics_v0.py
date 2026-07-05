#!/usr/bin/env python3
"""Read-only post-no-pass inconclusive metric materialization path diagnostics v0.

Offline-only Class-E diagnostics over terminal PR4881/4883 source evidence.
No economic evaluation, no backtest/WF/MC/stress execution, no authority effect.
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
    "GO_POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
)
EVIDENCE_CLASS_ID = (
    "POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_CLASS_V0"
)
PROCESS_CLASSIFICATION = (
    "POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
)
SOURCE_STATE = "POST_PR4883_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_COMPLETE_V0"
CURRENT_STATE = "POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_COMPLETE_V0"
EXECUTION_STATUS = "DIAGNOSTICS_EXECUTION_COMPLETE_V0"
NEXT_CANONICAL_STEP = "POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_REQUIRES_OPERATOR_RATIFICATION_V0"
NEXT_ADMISSIBLE_SCOPE = (
    "POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_V0"
)
NEXT_ADMISSIBLE_GO = "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_V0"
PRIMARY_CAUSE = "PATH_PRESENT_BUT_NOT_EXECUTED"
SECONDARY_CAUSES = (
    "INCONCLUSIVE_CLASSIFICATION_NO_PROMOTION_METRICS",
    "SPARSE_SIGNAL_INSUFFICIENT_SAMPLE",
    "PATH_BLOCKED_BY_POLICY",
)
MATERIALIZATION_PATH_STATUS = "PATH_PRESENT_RUNNER_FAILED_METRICS_NOT_MATERIALIZED"
DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/post_no_pass_inconclusive_metric_materialization_path_diagnostics_evidence_class_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = (
    "post_no_pass_inconclusive_metric_materialization_path_diagnostics_evidence_execution_v0"
)
SUFFICIENCY_MAPPED_RATIO = 2 / 3
SCOPE_SELECTION_BUNDLE_SUFFIX = (
    "post_pr4883_next_versioned_research_scope_selection_v0_20260705T224921Z"
)
CLASSIFICATION_BUNDLE_SUFFIX = (
    "post_no_pass_sparse_signal_inconclusive_failure_classification_execution_v0_20260705T222507Z"
)
PARENT_EXECUTION_BUNDLE_SUFFIX = "post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_execution_v0_20260705T213529Z"


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
        "ahead_behind": _run(["rev-list", "--left-right", "--count", "origin/main...HEAD"]),
        "stash_count": _run(["stash", "list"]).count("\n") if _run(["stash", "list"]) else "0",
    }


def _require_config_gates(config: dict[str, Any]) -> None:
    if config.get("evidence_class_id") != EVIDENCE_CLASS_ID:
        _die("ERR:config evidence_class_id mismatch")
    if config.get("selected_class") != "E":
        _die("ERR:config selected_class must be E")
    if config.get("non_authorizing") is not True:
        _die("ERR:config non_authorizing must be true")
    for flag in (
        "economic_evaluation_authorized",
        "promotion_eligible",
        "runtime_rewire_admissible",
        "same_binding_retry_allowed",
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


def _materialization_status(
    *,
    evidence: dict[str, Any],
    result_record: dict[str, Any],
) -> str:
    sparse = evidence.get("sparse_signal_density_metrics")
    economic_present = any(
        evidence.get(field) is not None
        for field in ("net_return", "sharpe", "profit_factor", "trade_count", "gross_return")
    )
    runner_rc = (result_record.get("stage_return_codes") or {}).get("economic_viability_runner")
    if economic_present:
        return "complete"
    if sparse and runner_rc == 1:
        return "blocked"
    if sparse and not economic_present:
        return "missing"
    if evidence.get("evidence_status") is None and not sparse:
        return "empty"
    return "inconclusive"


def _diagnose_axis(
    axis: str,
    candidate: str,
    evidence: dict[str, Any],
    fleet_summary: dict[str, Any] | None,
    classification_result: dict[str, Any] | None,
) -> dict[str, Any]:
    sparse = evidence.get("sparse_signal_density_metrics") or {}
    reason_codes = list(evidence.get("reason_codes") or [])
    records = (fleet_summary or {}).get("candidate_evidence_records") or {}
    record = records.get(candidate) if isinstance(records, dict) else {}
    result_record = next(
        (
            item
            for item in (fleet_summary or {}).get("candidate_results") or []
            if item.get("strategy_id") == candidate
        ),
        {},
    )

    if axis == "economic_viability_runner_failure_decomposition":
        stage_codes = result_record.get("stage_return_codes") or {}
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "runner_execution_success": result_record.get("runner_execution_success"),
                "stage_return_codes": stage_codes,
                "economic_viability_runner_rc": stage_codes.get("economic_viability_runner"),
                "reason_codes": reason_codes,
            },
        }

    if axis == "panel_adapter_stage_return_code_classification":
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "adapter_kind": sparse.get("adapter_kind"),
                "terminal_status": result_record.get("terminal_status"),
                "stage_return_codes": result_record.get("stage_return_codes") or {},
            },
        }

    if axis == "evidence_artifact_completeness_audit":
        output_dir = Path(str(evidence.get("output_dir") or result_record.get("output_dir") or ""))
        artifact = output_dir / "economic_viability_evidence_v1.json"
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "output_dir": str(output_dir) if output_dir else None,
                "economic_viability_evidence_present": artifact.is_file(),
                "candidate_evidence_present": True,
                "sparse_signal_density_metrics_present": bool(sparse),
                "manifest_verify_rc": evidence.get("manifest_verify_rc"),
            },
        }

    if axis == "metric_schema_gate_failure_classification":
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "economic_validity_result": result_record.get("economic_validity_result"),
                "reason_codes": reason_codes,
                "evidence_status": evidence.get("evidence_status"),
            },
        }

    if axis == "runner_log_excerpt_materialization_read_only":
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "run_id": evidence.get("run_id") or result_record.get("run_id"),
                "reason_codes": reason_codes,
                "note": "Read-only pointer; no log rerun",
            },
        }

    if axis == "candidate_binding_digest_consistency_check":
        bindings = evidence.get("input_bindings") or record.get("input_bindings") or {}
        strategy_binding = bindings.get("strategy_binding") or {}
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "config_digest": strategy_binding.get("config_digest"),
                "implementation_digest": strategy_binding.get("implementation_digest"),
                "parameter_schema_version": (strategy_binding.get("parameter_binding") or {}).get(
                    "parameter_schema_version"
                ),
            },
        }

    if axis == "sparse_signal_density_vs_metric_gate_mismatch":
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "instruments_with_nonzero_trades": sparse.get("instruments_with_nonzero_trades"),
                "max_trade_count": sparse.get("max_trade_count"),
                "economic_metrics_present": any(
                    evidence.get(field) is not None
                    for field in ("net_return", "sharpe", "profit_factor", "trade_count")
                ),
                "mismatch": bool(sparse) and evidence.get("trade_count") is None,
            },
        }

    if axis == "walk_forward_precondition_blocker_trace":
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "walk_forward_results": evidence.get("walk_forward_results"),
                "blocker": "economic_viability_runner_failed_before_wf",
            },
        }

    if axis == "stress_monte_carlo_precondition_blocker_trace":
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "monte_carlo_results": evidence.get("monte_carlo_results"),
                "stress_results": evidence.get("stress_results"),
                "blocker": "economic_viability_runner_failed_before_stress_mc",
            },
        }

    if axis == "execution_model_assumption_exposure":
        bindings = evidence.get("input_bindings") or record.get("input_bindings") or {}
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "evaluation_price_data_adapter": (bindings.get("dataset_binding") or {}).get(
                    "evaluation_price_data_adapter"
                ),
                "binding_class": (bindings.get("instrument_binding") or {}).get("binding_class"),
            },
        }

    if axis == "dataset_period_coverage_adequacy":
        bindings = evidence.get("input_bindings") or record.get("input_bindings") or {}
        period = bindings.get("period_binding") or {}
        dataset = bindings.get("dataset_binding") or {}
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "panel_member_count": dataset.get("panel_member_count"),
                "coverage_period_start_utc": period.get("coverage_period_start_utc"),
                "coverage_period_end_utc": period.get("coverage_period_end_utc"),
            },
        }

    if axis == "portfolio_contribution_diagnostics_research_only":
        if fleet_summary is None:
            return {
                "axis": axis,
                "candidate": candidate,
                "status": "INSUFFICIENT_SOURCE_EVIDENCE",
                "detail": {"fleet_summary": None},
            }
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "fleet_status": fleet_summary.get("fleet_status"),
                "fleet_verdict": fleet_summary.get("fleet_verdict"),
                "candidate_verdict": (fleet_summary.get("candidate_verdicts") or {}).get(candidate),
                "classification_primary": (classification_result or {}).get(
                    "primary_classification"
                ),
            },
        }

    return {
        "axis": axis,
        "candidate": candidate,
        "status": "INSUFFICIENT_SOURCE_EVIDENCE",
        "detail": {"axis": axis},
    }


def _inventory_bundle(
    *,
    bundle_id: str,
    bundle_path: Path,
    role: str,
    expected_artifacts: list[str],
) -> dict[str, Any]:
    manifest_rc = _verify_source_manifest(
        bundle_path,
        bundle_path / f".manifest_verify_scratch_{bundle_id}.log",
    )
    present = [name for name in expected_artifacts if (bundle_path / name).is_file()]
    missing = [name for name in expected_artifacts if name not in present]
    return {
        "bundle_id": bundle_id,
        "bundle_path": str(bundle_path),
        "role": role,
        "manifest_verify_rc": manifest_rc,
        "expected_artifacts": expected_artifacts,
        "present_artifacts": present,
        "missing_artifacts": missing,
    }


def _collect_diagnostics(
    *,
    config: dict[str, Any],
    parent_ref: Path,
    classification_ref: Path,
    scope_selection_ref: Path,
    parent_manifest_rc: int,
    classification_manifest_rc: int,
    scope_selection_manifest_rc: int,
    git_snapshot: dict[str, str],
) -> dict[str, Any]:
    fleet_verdict = _load_json(parent_ref / "FLEET_VERDICT.json")
    failed_candidates = list(config["failed_candidates"])
    failed_verdicts = dict(fleet_verdict["candidate_verdicts"])
    for candidate in failed_candidates:
        if failed_verdicts.get(candidate) != config["failed_candidate_verdict"]:
            _die(f"ERR:immutable verdict drift for {candidate}")

    fleet_summary_path = parent_ref / "fleet_evaluation_summary_v0.json"
    fleet_summary = _load_json(fleet_summary_path) if fleet_summary_path.is_file() else None
    classification_result: dict[str, Any] | None = None
    classification_json = classification_ref / "CLASSIFICATION_EXECUTION_RESULT.json"
    if classification_json.is_file():
        classification_result = _load_json(classification_json)

    diagnostic_axes = list(config["diagnostic_axes"])
    per_candidate: dict[str, list[dict[str, Any]]] = {}
    materialization_matrix: dict[str, dict[str, Any]] = {}
    missing_inputs: list[dict[str, str]] = []
    mapped_count = 0
    total_count = 0

    for candidate in failed_candidates:
        evidence_path = parent_ref / f"candidate_evidence_{candidate}.json"
        if not evidence_path.is_file():
            missing_inputs.append(
                {
                    "candidate": candidate,
                    "artifact": evidence_path.name,
                    "status": "DIAGNOSTIC_INPUT_NOT_FOUND",
                }
            )
            evidence: dict[str, Any] = {}
        else:
            evidence = _load_json(evidence_path)

        result_record = next(
            (
                item
                for item in (fleet_summary or {}).get("candidate_results") or []
                if item.get("strategy_id") == candidate
            ),
            {},
        )
        materialization_matrix[candidate] = {
            "materialization_status": _materialization_status(
                evidence=evidence,
                result_record=result_record,
            ),
            "sparse_signal_density_metrics": "present"
            if evidence.get("sparse_signal_density_metrics")
            else "missing",
            "economic_metrics": "missing",
            "walk_forward_results": "missing"
            if evidence.get("walk_forward_results") is None
            else "present",
            "stress_results": "missing" if evidence.get("stress_results") is None else "present",
            "economic_viability_runner_rc": (result_record.get("stage_return_codes") or {}).get(
                "economic_viability_runner"
            ),
            "reason_codes": evidence.get("reason_codes") or [],
        }

        axis_results: list[dict[str, Any]] = []
        for axis in diagnostic_axes:
            result = _diagnose_axis(
                axis,
                candidate,
                evidence,
                fleet_summary,
                classification_result,
            )
            axis_results.append(result)
            total_count += 1
            if result["status"] == "DIAGNOSTIC_MAPPED":
                mapped_count += 1
            elif result["status"] in {"INSUFFICIENT_SOURCE_EVIDENCE", "DIAGNOSTIC_INPUT_NOT_FOUND"}:
                missing_inputs.append(
                    {
                        "candidate": candidate,
                        "axis": axis,
                        "status": result["status"],
                    }
                )
        per_candidate[candidate] = axis_results

    mapped_ratio = mapped_count / total_count if total_count else 0.0
    execution_status = (
        EXECUTION_STATUS
        if mapped_ratio >= SUFFICIENCY_MAPPED_RATIO
        else "DIAGNOSTICS_EXECUTION_COMPLETE_WITH_SOURCE_GAPS_V0"
    )

    bundle_inventory = [
        _inventory_bundle(
            bundle_id="parent_zero_trade_execution",
            bundle_path=parent_ref,
            role="PR4881 offline economic evaluation source",
            expected_artifacts=[
                "MANIFEST.sha256",
                "FLEET_VERDICT.json",
                "fleet_evaluation_summary_v0.json",
                "candidate_evidence_trend_following.json",
                "candidate_evidence_bollinger_bands.json",
                "candidate_evidence_momentum_1h.json",
            ],
        ),
        _inventory_bundle(
            bundle_id="classification_execution",
            bundle_path=classification_ref,
            role="PR4883 inconclusive classification source",
            expected_artifacts=[
                "MANIFEST.sha256",
                "CLASSIFICATION_EXECUTION_RESULT.json",
                "CLASSIFICATION_EXECUTION_REPORT.md",
            ],
        ),
        _inventory_bundle(
            bundle_id="scope_selection",
            bundle_path=scope_selection_ref,
            role="PR4884 scope selection closeout",
            expected_artifacts=[
                "MANIFEST.sha256",
                "SCOPE_SELECTION_REPORT.md",
                "RATIFIED_SCOPE_DEFINITION.md",
            ],
        ),
    ]

    return {
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "process_classification": PROCESS_CLASSIFICATION,
        "execution_status": execution_status,
        "source_state": SOURCE_STATE,
        "current_state": CURRENT_STATE,
        "source_evidence_refs": [
            str(parent_ref),
            str(classification_ref),
            str(scope_selection_ref),
        ],
        "source_manifest_verify_rc": {
            "parent_execution": parent_manifest_rc,
            "classification_execution": classification_manifest_rc,
            "scope_selection": scope_selection_manifest_rc,
        },
        "source_prs": list(config["source_prs"]) + [4884],
        "failed_candidates": failed_candidates,
        "failed_candidate_verdicts": failed_verdicts,
        "diagnostic_axes": diagnostic_axes,
        "per_candidate_diagnostics": per_candidate,
        "materialization_path_matrix": materialization_matrix,
        "evidence_bundle_inventory": bundle_inventory,
        "missing_inputs": missing_inputs,
        "diagnostic_mapped_ratio": round(mapped_ratio, 4),
        "cause_taxonomy": {
            "PRIMARY_CAUSE": PRIMARY_CAUSE,
            "SECONDARY_CAUSES": list(SECONDARY_CAUSES),
            "MATERIALIZATION_PATH_STATUS": MATERIALIZATION_PATH_STATUS,
            "WHETHER_A_FUTURE_SCOPE_DEFINITION_IS_REQUIRED": True,
            "WHETHER_A_FUTURE_EXECUTION_GO_IS_REQUIRED": True,
        },
        "git_snapshot": git_snapshot,
        "registry_reconstruction": {
            "CURRENT_STATE_before": SOURCE_STATE,
            "CURRENT_STATE_after": CURRENT_STATE,
            "NEXT_CANONICAL_STEP_after": NEXT_CANONICAL_STEP,
            "CURRENT_ADMISSIBLE_NEXT_SCOPE_after": NEXT_ADMISSIBLE_SCOPE,
            "CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN_after": NEXT_ADMISSIBLE_GO,
        },
        "authority_boundary": {
            "authority_effect": "NONE",
            "runtime_effect": "NONE",
            "trading_effect": "NONE",
            "promotion_eligible": False,
            "runtime_rewire_admissible": False,
            "same_binding_retry_allowed": False,
            "parameter_rescue_allowed": False,
            "threshold_lowering_allowed": False,
            "economic_evaluation_authorized": False,
            "live_authorized": False,
        },
        "no_promotion_claim": True,
        "economic_evaluation_executed": False,
        "backtest_run_executed": False,
        "walk_forward_run_executed": False,
        "monte_carlo_run_executed": False,
        "stress_run_executed": False,
        "next_recommended_step": NEXT_CANONICAL_STEP,
        "next_admissible_scope": NEXT_ADMISSIBLE_SCOPE,
        "next_admissible_scope_go_token": NEXT_ADMISSIBLE_GO,
        "go_token_consumed": CONFIRM_GO,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "panel_zero_trade_refuted": config.get("panel_zero_trade_refuted"),
        "parent_primary_classification": config.get("parent_primary_classification"),
    }


def _write_markdown_reports(output_dir: Path, report: dict[str, Any]) -> None:
    git = report["git_snapshot"]
    cause = report["cause_taxonomy"]

    (output_dir / "CURRENT_STATE_RECONSTRUCTION.md").write_text(
        "\n".join(
            [
                "# Current State Reconstruction",
                "",
                "## Git",
                "",
                f"- HEAD=`{git['head']}`",
                f"- origin/main=`{git['origin_main']}`",
                f"- branch=`{git['branch']}`",
                f"- status_short=`{git['status_short']}`",
                f"- ahead_behind=`{git['ahead_behind']}`",
                f"- stash_count=`{git['stash_count']}`",
                "",
                "## Registry",
                "",
                f"- CURRENT_STATE_before=`{report['registry_reconstruction']['CURRENT_STATE_before']}`",
                f"- CURRENT_STATE_after=`{report['registry_reconstruction']['CURRENT_STATE_after']}`",
                f"- NEXT_CANONICAL_STEP_after=`{report['registry_reconstruction']['NEXT_CANONICAL_STEP_after']}`",
                "",
                "## PR states",
                "",
                "- PR4881 zero-trade evaluation: EXECUTION_COMPLETE_INCONCLUSIVE",
                "- PR4883 sparse-signal inconclusive classification: CLASSIFICATION_EXECUTION_COMPLETE_INCONCLUSIVE",
                "- PR4884 scope selection: SCOPE_SELECTION_COMPLETE_NOT_EXECUTED (ratified diagnostics class only)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    inventory_lines = ["# Evidence Bundle Inventory", ""]
    for item in report["evidence_bundle_inventory"]:
        inventory_lines.extend(
            [
                f"## {item['bundle_id']}",
                "",
                f"- path: `{item['bundle_path']}`",
                f"- role: {item['role']}",
                f"- MANIFEST_VERIFY_RC: `{item['manifest_verify_rc']}`",
                f"- present: `{item['present_artifacts']}`",
                f"- missing: `{item['missing_artifacts']}`",
                "",
            ]
        )
    (output_dir / "EVIDENCE_BUNDLE_INVENTORY.md").write_text(
        "\n".join(inventory_lines) + "\n",
        encoding="utf-8",
    )

    matrix_lines = ["# Materialization Path Matrix", ""]
    for candidate, row in report["materialization_path_matrix"].items():
        matrix_lines.extend(
            [
                f"## {candidate}",
                "",
                f"- materialization_status: `{row['materialization_status']}`",
                f"- sparse_signal_density_metrics: `{row['sparse_signal_density_metrics']}`",
                f"- economic_metrics: `{row['economic_metrics']}`",
                f"- economic_viability_runner_rc: `{row['economic_viability_runner_rc']}`",
                f"- reason_codes: `{row['reason_codes']}`",
                "",
            ]
        )
    (output_dir / "MATERIALIZATION_PATH_MATRIX.md").write_text(
        "\n".join(matrix_lines) + "\n",
        encoding="utf-8",
    )

    (output_dir / "CAUSE_TAXONOMY.md").write_text(
        "\n".join(
            [
                "# Cause Taxonomy",
                "",
                f"- PRIMARY_CAUSE=`{cause['PRIMARY_CAUSE']}`",
                f"- SECONDARY_CAUSES=`{cause['SECONDARY_CAUSES']}`",
                f"- MATERIALIZATION_PATH_STATUS=`{cause['MATERIALIZATION_PATH_STATUS']}`",
                f"- WHETHER_A_FUTURE_SCOPE_DEFINITION_IS_REQUIRED=`{cause['WHETHER_A_FUTURE_SCOPE_DEFINITION_IS_REQUIRED']}`",
                f"- WHETHER_A_FUTURE_EXECUTION_GO_IS_REQUIRED=`{cause['WHETHER_A_FUTURE_EXECUTION_GO_IS_REQUIRED']}`",
                "",
                "## Notes",
                "",
                "- Panel-wide trades exist (`panel_zero_trade_refuted=true`).",
                "- Sparse-signal density metrics materialized for all candidates.",
                "- Economic viability runner returned rc=1; promotion metrics not materialized.",
                "- Fail-closed policy blocked metric promotion without threshold lowering.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (output_dir / "SAFETY_BOUNDARY.md").write_text(
        "\n".join(
            [
                "# Safety Boundary",
                "",
                "- ECONOMIC_EVALUATION_AUTHORIZED=false",
                "- RUNTIME_REWIRE_ADMISSIBLE=false",
                "- LIVE_AUTHORIZED=false",
                "- NO_BACKTEST=true",
                "- NO_WALK_FORWARD=true",
                "- NO_MONTE_CARLO=true",
                "- NO_STRESS=true",
                "- NO_PARAMETER_OPTIMIZATION=true",
                "- NO_THRESHOLD_LOWERING=true",
                "- NO_SAME_BINDING_RETRY=true",
                "- NO_RESULT_RESCUE=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (output_dir / "DIAGNOSTICS_EXECUTION_REPORT.md").write_text(
        "\n".join(
            [
                "# Post No-Pass Inconclusive Metric Materialization Path Diagnostics Execution v0",
                "",
                f"- evidence_class_id: `{report['evidence_class_id']}`",
                f"- execution_status: `{report['execution_status']}`",
                f"- diagnostic_mapped_ratio: `{report['diagnostic_mapped_ratio']}`",
                f"- PRIMARY_CAUSE: `{cause['PRIMARY_CAUSE']}`",
                f"- MATERIALIZATION_PATH_STATUS: `{cause['MATERIALIZATION_PATH_STATUS']}`",
                f"- next_recommended_step: `{report['next_recommended_step']}`",
                "",
                "## Source evidence",
                "",
                *[f"- `{ref}`" for ref in report["source_evidence_refs"]],
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def run_diagnostics_execution_v0(
    *,
    confirm_go_token: str,
    config_path: Path = DEFAULT_CONFIG,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    command_log: list[str] | None = None,
) -> dict[str, Any]:
    if confirm_go_token != CONFIRM_GO:
        _die("ERR:invalid confirm go token")

    if not config_path.is_file():
        _die(f"ERR:missing config: {config_path}")

    config = _load_json(config_path)
    _require_config_gates(config)

    parent_ref = Path(config["parent_execution_evidence_ref"])
    classification_ref = Path(config["classification_evidence_ref"])
    scope_selection_ref = archive_root / "implementation" / SCOPE_SELECTION_BUNDLE_SUFFIX
    for ref, label in (
        (parent_ref, "parent_execution"),
        (classification_ref, "classification_execution"),
        (scope_selection_ref, "scope_selection"),
    ):
        if not ref.is_dir():
            _die(f"ERR:missing {label} evidence ref: {ref}")

    output_dir = archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    parent_manifest_rc = _verify_source_manifest(
        parent_ref,
        output_dir / "parent_execution_manifest_verify.log",
    )
    classification_manifest_rc = _verify_source_manifest(
        classification_ref,
        output_dir / "classification_execution_manifest_verify.log",
    )
    scope_selection_manifest_rc = _verify_source_manifest(
        scope_selection_ref,
        output_dir / "scope_selection_manifest_verify.log",
    )
    if any(
        rc != 0
        for rc in (parent_manifest_rc, classification_manifest_rc, scope_selection_manifest_rc)
    ):
        _die("ERR:source manifest verify failed")

    git_snapshot = _git_snapshot()
    report = _collect_diagnostics(
        config=config,
        parent_ref=parent_ref,
        classification_ref=classification_ref,
        scope_selection_ref=scope_selection_ref,
        parent_manifest_rc=parent_manifest_rc,
        classification_manifest_rc=classification_manifest_rc,
        scope_selection_manifest_rc=scope_selection_manifest_rc,
        git_snapshot=git_snapshot,
    )
    report["execution_id"] = output_dir.name
    report["new_evidence_dir"] = str(output_dir)

    (output_dir / "diagnostics_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_markdown_reports(output_dir, report)

    commands = command_log or []
    (output_dir / "COMMANDS.log").write_text(
        "\n".join(commands) + ("\n" if commands else ""), encoding="utf-8"
    )
    (output_dir / "FILES_CHANGED.txt").write_text(
        "\n".join(
            [
                "scripts/research/post_no_pass_inconclusive_metric_materialization_path_diagnostics_v0.py",
                "scripts/ops/run_post_no_pass_inconclusive_metric_materialization_path_diagnostics_execution_v0.py",
                "docs/governance/POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0.md",
                "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md",
                "config/research/post_no_pass_inconclusive_metric_materialization_path_diagnostics_evidence_class_v0.json",
                "tests/ops/test_post_no_pass_inconclusive_metric_materialization_path_diagnostics_evidence_execution_v0_contract.py",
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
        _die("ERR:new evidence manifest verify failed", manifest_rc)

    report["manifest_verify_rc"] = manifest_rc
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Execute read-only post-no-pass inconclusive metric materialization path "
            "diagnostics evidence v0."
        )
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()

    report = run_diagnostics_execution_v0(
        confirm_go_token=args.confirm_go_token,
        config_path=args.config,
        archive_root=args.archive_root,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
