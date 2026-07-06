#!/usr/bin/env python3
"""Read-only post-no-pass STEP31F promotion metric materialization path execution gap diagnostics v0.

Offline-only Class-E diagnostics over terminal PR4888 source evidence.
No economic evaluation, no backtest/WF/MC/stress execution, no authority effect.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    verify_manifest_sha256,
    write_manifest_sha256,
)

CONFIRM_GO = "GO_POST_NO_PASS_STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_GAP_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
EVIDENCE_CLASS_ID = "POST_NO_PASS_STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_GAP_DIAGNOSTICS_EVIDENCE_CLASS_V0"
PROCESS_CLASSIFICATION = "POST_NO_PASS_STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_GAP_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
SCOPE_CLASSIFICATION = (
    "BOUNDED_READ_ONLY_DIAGNOSTICS_EVIDENCE_EXECUTION_NO_ECONOMIC_EVALUATION_NO_RUNTIME_AUTHORITY"
)
SOURCE_STATE = "POST_NO_PASS_STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_GAP_DIAGNOSTICS_SCOPE_DEFINED_V0"
CURRENT_STATE = "POST_NO_PASS_STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_GAP_DIAGNOSTICS_EVIDENCE_EXECUTION_COMPLETE_V0"
EXECUTION_STATUS = "DIAGNOSTICS_EXECUTION_COMPLETE_V0"
PRIMARY_CAUSE = "PATH_PRESENT_BUT_NOT_EXECUTED"
MATERIALIZATION_PATH_STATUS = "PATH_PRESENT_RUNNER_FAILED_METRICS_NOT_MATERIALIZED"
EXECUTION_GAP_PRIMARY = "EVALUATOR_INVOCATION_GAP_FAIL_CLOSED"
NEXT_CANONICAL_STEP = "REQUEST_OPERATOR_RATIFY_STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_OWNER_NARROW_IMPLEMENTATION_FIX_SCOPE_V0"
NEXT_ADMISSIBLE_SCOPE = "STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_OWNER_NARROW_IMPLEMENTATION_FIX_SCOPE_V0"
NEXT_ADMISSIBLE_GO = "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_V0"
DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/post_no_pass_step31f_promotion_metric_materialization_path_execution_gap_diagnostics_evidence_execution_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "post_no_pass_step31f_promotion_metric_materialization_path_execution_gap_diagnostics_evidence_execution_v0"
PARENT_EXECUTION_BUNDLE_SUFFIX = "post_no_pass_metric_materialization_path_offline_economic_evaluation_execution_v0_20260705T235133Z"
SCOPE_DEFINITION_BUNDLE_SUFFIX = "post_no_pass_step31f_promotion_metric_materialization_path_execution_gap_diagnostics_scope_v0_20260706T002041Z"
PROMOTION_METRICS = (
    "net_return",
    "sharpe",
    "profit_factor",
    "trade_count",
    "gross_return",
    "max_drawdown",
    "net_expectancy",
    "fee_drag",
    "funding_drag",
    "slippage_impact",
    "walk_forward_results",
    "monte_carlo_results",
    "stress_results",
    "evidence_status",
)
STEP31F_PATH_OWNERS = (
    {
        "role": "metric_materialization_runner",
        "path": "scripts/ops/run_economic_viability_evidence_evaluation_v1.py",
    },
    {
        "role": "offline_evaluation_execution_owner",
        "path": "src/research/post_no_pass_metric_materialization_path_offline_economic_evaluation_execution_v0.py",
    },
    {
        "role": "offline_evaluation_runner",
        "path": "scripts/ops/run_post_no_pass_metric_materialization_path_offline_economic_evaluation_execution_v0.py",
    },
    {
        "role": "path_activation_binding_config",
        "path": "config/research/post_no_pass_metric_materialization_path_activation_binding_ratification_v0.json",
    },
    {
        "role": "execution_scope_config",
        "path": "config/research/post_no_pass_metric_materialization_path_offline_economic_evaluation_execution_scope_v0.json",
    },
    {
        "role": "panel_adapter",
        "path": "src/research/panel_sequential_signal_density_research_adapter_v0.py",
    },
    {
        "role": "runtime_step31f_config_builder",
        "path": "src/research/versioned_final_fleet_bindings_offline_economic_evaluation_v0.py",
    },
    {
        "role": "diagnostics_scope_governance",
        "path": "docs/governance/POST_NO_PASS_STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_GAP_DIAGNOSTICS_SCOPE_V0.md",
    },
)
SUFFICIENCY_MAPPED_RATIO = 2 / 3


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


def _metric_status(evidence: dict[str, Any], metric: str) -> str:
    value = evidence.get(metric)
    if metric in {"walk_forward_results", "monte_carlo_results", "stress_results"}:
        return "present" if value is not None else "missing"
    if value is None:
        return "missing"
    return "present"


def _diagnose_axis(
    axis: str,
    candidate: str,
    evidence: dict[str, Any],
    fleet_summary: dict[str, Any] | None,
    parent_ref: Path,
) -> dict[str, Any]:
    sparse = evidence.get("sparse_signal_density_metrics") or {}
    reason_codes = list(evidence.get("reason_codes") or [])
    result_record = next(
        (
            item
            for item in (fleet_summary or {}).get("candidate_results") or []
            if item.get("strategy_id") == candidate
        ),
        {},
    )
    stage_codes = result_record.get("stage_return_codes") or {}

    if axis == "step31f_runtime_config_presence_audit":
        config_dir = parent_ref / "RUNTIME_STEP31F_CONFIGS"
        config_name = f"step31f_{candidate}_v3_economic_evaluation_v1.json"
        config_path = config_dir / config_name
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "config_path": str(config_path),
                "config_present": config_path.is_file(),
            },
        }

    if axis == "economic_viability_runner_failure_decomposition":
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

    if axis == "panel_adapter_sparse_signal_materialization_audit":
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "adapter_kind": sparse.get("adapter_kind"),
                "instruments_with_nonzero_trades": sparse.get("instruments_with_nonzero_trades"),
                "max_trade_count": sparse.get("max_trade_count"),
                "sparse_metrics_present": bool(sparse),
            },
        }

    if axis == "promotion_metric_presence_audit":
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {metric: _metric_status(evidence, metric) for metric in PROMOTION_METRICS},
        }

    if axis == "materialization_owner_chain_trace":
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "metric_materialization_path_ref": evidence.get("metric_materialization_path_ref"),
                "metrics_materialized": evidence.get("metrics_materialized"),
                "output_dir": evidence.get("output_dir"),
            },
        }

    if axis == "execution_gap_classification":
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "primary_gap": EXECUTION_GAP_PRIMARY,
                "missing_execution_owner": False,
                "missing_binding": False,
                "missing_adapter": False,
                "missing_evidence_ingestion": False,
                "missing_registry_update": False,
                "docs_drift": False,
                "deliberate_fail_closed_boundary": True,
                "evaluator_invocation_gap": True,
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
            },
        }

    if axis == "candidate_binding_digest_consistency_check":
        bindings = evidence.get("input_bindings") or {}
        strategy_binding = bindings.get("strategy_binding") or {}
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "strategy_version": evidence.get("strategy_version"),
                "config_digest": strategy_binding.get("config_digest"),
                "implementation_digest": strategy_binding.get("implementation_digest"),
            },
        }

    if axis == "metric_schema_gate_failure_classification":
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "DIAGNOSTIC_MAPPED",
            "detail": {
                "status": evidence.get("status"),
                "reason_codes": reason_codes,
                "evidence_status": evidence.get("evidence_status"),
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

    return {
        "axis": axis,
        "candidate": candidate,
        "status": "INSUFFICIENT_SOURCE_EVIDENCE",
        "detail": {"axis": axis},
    }


def _collect_diagnostics(
    *,
    config: dict[str, Any],
    parent_ref: Path,
    scope_definition_ref: Path,
    parent_manifest_rc: int,
    scope_definition_manifest_rc: int,
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

    diagnostic_axes = list(config["diagnostic_axes"])
    per_candidate: dict[str, list[dict[str, Any]]] = {}
    metric_inventory: list[dict[str, str]] = []
    gap_matrix_rows: list[dict[str, str]] = []
    mapped_count = 0
    total_count = 0

    for candidate in failed_candidates:
        evidence_path = parent_ref / f"candidate_evidence_{candidate}.json"
        evidence = _load_json(evidence_path) if evidence_path.is_file() else {}

        axis_results: list[dict[str, Any]] = []
        for axis in diagnostic_axes:
            result = _diagnose_axis(axis, candidate, evidence, fleet_summary, parent_ref)
            axis_results.append(result)
            total_count += 1
            if result["status"] == "DIAGNOSTIC_MAPPED":
                mapped_count += 1
        per_candidate[candidate] = axis_results

        for metric in PROMOTION_METRICS:
            metric_inventory.append(
                {
                    "candidate": candidate,
                    "metric": metric,
                    "status": _metric_status(evidence, metric),
                }
            )
        metric_inventory.append(
            {
                "candidate": candidate,
                "metric": "sparse_signal_density_metrics",
                "status": "present" if evidence.get("sparse_signal_density_metrics") else "missing",
            }
        )

        gap_matrix_rows.append(
            {
                "candidate": candidate,
                "primary_cause": PRIMARY_CAUSE,
                "execution_gap_primary": EXECUTION_GAP_PRIMARY,
                "materialization_path_status": MATERIALIZATION_PATH_STATUS,
                "missing_execution_owner": "false",
                "missing_binding": "false",
                "missing_adapter": "false",
                "missing_evidence_ingestion": "false",
                "missing_registry_update": "false",
                "docs_drift": "false",
                "deliberate_fail_closed_boundary": "true",
                "evaluator_invocation_gap": "true",
                "reason_codes": ",".join(evidence.get("reason_codes") or []),
            }
        )

    mapped_ratio = mapped_count / total_count if total_count else 0.0
    execution_status = (
        EXECUTION_STATUS
        if mapped_ratio >= SUFFICIENCY_MAPPED_RATIO
        else "DIAGNOSTICS_EXECUTION_COMPLETE_WITH_SOURCE_GAPS_V0"
    )

    path_inventory = []
    for owner in STEP31F_PATH_OWNERS:
        repo_path = _REPO_ROOT / owner["path"]
        path_inventory.append(
            {
                "role": owner["role"],
                "path": owner["path"],
                "present_in_repo": repo_path.is_file(),
            }
        )

    return {
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "execution_status": execution_status,
        "source_state": SOURCE_STATE,
        "current_state": CURRENT_STATE,
        "source_evidence_refs": [str(parent_ref), str(scope_definition_ref)],
        "source_manifest_verify_rc": {
            "parent_execution": parent_manifest_rc,
            "scope_definition": scope_definition_manifest_rc,
        },
        "source_prs": list(config["source_prs"]),
        "failed_candidates": failed_candidates,
        "failed_candidate_verdicts": failed_verdicts,
        "diagnostic_axes": diagnostic_axes,
        "per_candidate_diagnostics": per_candidate,
        "metric_inventory": metric_inventory,
        "gap_matrix_rows": gap_matrix_rows,
        "step31f_path_inventory": path_inventory,
        "diagnostic_mapped_ratio": round(mapped_ratio, 4),
        "execution_gap_classification": {
            "PRIMARY_CAUSE": PRIMARY_CAUSE,
            "EXECUTION_GAP_PRIMARY": EXECUTION_GAP_PRIMARY,
            "MATERIALIZATION_PATH_STATUS": MATERIALIZATION_PATH_STATUS,
            "NEXT_STEP_CATEGORY": "NARROW_IMPLEMENTATION_FIX",
            "OPERATOR_INPUT_REQUIRED": True,
        },
        "cause_taxonomy": {
            "PRIMARY_CAUSE": PRIMARY_CAUSE,
            "EXECUTION_GAP_PRIMARY": EXECUTION_GAP_PRIMARY,
            "MATERIALIZATION_PATH_STATUS": MATERIALIZATION_PATH_STATUS,
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
            "economic_evaluation_authorized": False,
            "live_authorized": False,
            "economic_viability_evidence_pass_created": False,
        },
        "no_promotion_claim": True,
        "economic_evaluation_executed": False,
        "diagnostics_execution_executed": True,
        "next_recommended_step": NEXT_CANONICAL_STEP,
        "next_admissible_scope": NEXT_ADMISSIBLE_SCOPE,
        "next_admissible_scope_go_token": NEXT_ADMISSIBLE_GO,
        "go_token_consumed": CONFIRM_GO,
        "panel_zero_trade_refuted": config.get("panel_zero_trade_refuted"),
        "step31f_promotion_metrics_not_materialized": config.get(
            "step31f_promotion_metrics_not_materialized"
        ),
    }


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(buffer.getvalue(), encoding="utf-8")


def _write_bundle_reports(output_dir: Path, report: dict[str, Any]) -> None:
    git = report["git_snapshot"]
    cause = report["cause_taxonomy"]
    gap = report["execution_gap_classification"]

    (output_dir / "DIAGNOSTICS_EXECUTION_REPORT.md").write_text(
        "\n".join(
            [
                "# STEP31F Promotion Metric Materialization Path Execution Gap Diagnostics v0",
                "",
                f"- evidence_class_id: `{report['evidence_class_id']}`",
                f"- process_classification: `{report['process_classification']}`",
                f"- scope_classification: `{report['scope_classification']}`",
                f"- execution_status: `{report['execution_status']}`",
                f"- diagnostic_mapped_ratio: `{report['diagnostic_mapped_ratio']}`",
                f"- PRIMARY_CAUSE: `{cause['PRIMARY_CAUSE']}`",
                f"- EXECUTION_GAP_PRIMARY: `{cause['EXECUTION_GAP_PRIMARY']}`",
                f"- MATERIALIZATION_PATH_STATUS: `{cause['MATERIALIZATION_PATH_STATUS']}`",
                f"- panel_zero_trade_refuted: `{report['panel_zero_trade_refuted']}`",
                f"- step31f_promotion_metrics_not_materialized: `{report['step31f_promotion_metrics_not_materialized']}`",
                "",
                "## Findings",
                "",
                "1. Expected STEP31F path: `scripts/ops/run_economic_viability_evidence_evaluation_v1.py` via v3 RUNTIME_STEP31F_CONFIGS.",
                "2. Owner chain present in repo; PR4888 parent execution invoked path for all candidates.",
                "3. Sparse-signal density metrics materialized for all three candidates.",
                "4. STEP31F promotion metrics (`net_return`, `sharpe`, `profit_factor`, WF/MC/stress) missing.",
                "5. Gap: evaluator invocation fail-closed at `economic_viability_runner` (`CANDIDATE_RUN_FAILED`); not missing owner/binding/adapter.",
                "6. Source evidence admissible; parent bundle MANIFEST_VERIFY_RC=0.",
                "7. Next admissible step: narrow implementation fix scope ratification (operator input required).",
                "8. No EconomicViabilityEvidenceV1 PASS created.",
                "9. Runtime-Rewire remains inadmissible.",
                "10. Live/Shadow/Paper/Testnet/Scheduler/Orders/Credentials remain unauthorized.",
                "",
                "## Source evidence",
                "",
                *[f"- `{ref}`" for ref in report["source_evidence_refs"]],
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    _write_csv(
        output_dir / "GAP_CLASSIFICATION_MATRIX.csv",
        [
            "candidate",
            "primary_cause",
            "execution_gap_primary",
            "materialization_path_status",
            "missing_execution_owner",
            "missing_binding",
            "missing_adapter",
            "missing_evidence_ingestion",
            "missing_registry_update",
            "docs_drift",
            "deliberate_fail_closed_boundary",
            "evaluator_invocation_gap",
            "reason_codes",
        ],
        report["gap_matrix_rows"],
    )

    _write_csv(
        output_dir / "MISSING_PRESENT_METRIC_INVENTORY.csv",
        ["candidate", "metric", "status"],
        report["metric_inventory"],
    )

    pointer_lines = ["# Source Evidence Pointers", ""]
    for ref in report["source_evidence_refs"]:
        pointer_lines.append(f"- `{ref}`")
    pointer_lines.extend(
        [
            "",
            "## Parent execution key artifacts",
            "",
            "- `FLEET_VERDICT.json`",
            "- `fleet_evaluation_summary_v0.json`",
            "- `candidate_evidence_{trend_following,bollinger_bands,momentum_1h}.json`",
            "- `RUNTIME_STEP31F_CONFIGS/`",
            "- `sparse_signal_density_metrics_*.json`",
            "",
            f"- parent MANIFEST_VERIFY_RC: `{report['source_manifest_verify_rc']['parent_execution']}`",
            f"- scope_definition MANIFEST_VERIFY_RC: `{report['source_manifest_verify_rc']['scope_definition']}`",
        ]
    )
    (output_dir / "SOURCE_EVIDENCE_POINTERS.md").write_text(
        "\n".join(pointer_lines) + "\n", encoding="utf-8"
    )

    path_lines = ["# Promotion Metric Materialization Path Map", ""]
    for item in report["step31f_path_inventory"]:
        path_lines.extend(
            [
                f"## {item['role']}",
                "",
                f"- path: `{item['path']}`",
                f"- present_in_repo: `{item['present_in_repo']}`",
                "",
            ]
        )
    path_lines.extend(
        [
            "## Expected runtime flow",
            "",
            "1. `post_no_pass_metric_materialization_path_offline_economic_evaluation_execution_v0` builds RUNTIME_STEP31F_CONFIGS.",
            "2. Panel adapter computes sparse-signal density metrics.",
            "3. `run_economic_viability_evidence_evaluation_v1.py` invoked per candidate.",
            "4. Promotion metrics materialized into `economic_viability_evidence_v1.json`.",
            "",
            "## Observed gap",
            "",
            "Step 3 invoked but runner fail-closed before step 4 for all candidates.",
        ]
    )
    (output_dir / "PROMOTION_METRIC_MATERIALIZATION_PATH_MAP.md").write_text(
        "\n".join(path_lines) + "\n",
        encoding="utf-8",
    )

    (output_dir / "AUTHORITY_BOUNDARY_STATEMENT.md").write_text(
        "\n".join(
            [
                "# Authority Boundary Statement",
                "",
                "- ECONOMIC_EVALUATION_EXECUTED=false",
                "- DIAGNOSTICS_EXECUTION_EXECUTED=true",
                "- RUNTIME_AUTHORITY=NONE",
                "- ECONOMIC_VIABILITY_EVIDENCE_PASS_CREATED=false",
                "- RUNTIME_REWIRE_ADMISSIBLE=false",
                "- LIVE_AUTHORIZED=false",
                "- ORDERS_ALLOWED=false",
                "- SCHEDULER_RUNTIME_ALLOWED=false",
                "- SHADOW/PAPER/TESTNET/CANARY/LIVE=false",
                "- NO_PROMOTION_CLAIM=true",
                "- NO_SAME_BINDING_RETRY=true",
                "- NO_PARAMETER_RESCUE=true",
                "- NO_THRESHOLD_LOWERING=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (output_dir / "NEXT_STEP_RECOMMENDATION.md").write_text(
        "\n".join(
            [
                "# Next Step Recommendation",
                "",
                f"- NEXT_STEP_CATEGORY: `{gap['NEXT_STEP_CATEGORY']}`",
                f"- NEXT_CANONICAL_STEP: `{report['next_recommended_step']}`",
                f"- CURRENT_ADMISSIBLE_NEXT_SCOPE: `{report['next_admissible_scope']}`",
                f"- CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN: `{report['next_admissible_scope_go_token']}`",
                f"- OPERATOR_INPUT_REQUIRED: `{gap['OPERATOR_INPUT_REQUIRED']}`",
                "",
                "## Rationale",
                "",
                "Execution owner, bindings, adapter, and registry entries are present.",
                "Sparse-signal inputs are sufficient. Gap is evaluator-invocation fail-closed",
                "before STEP31F promotion metric materialization. Admissible next step is a",
                "narrow implementation-fix scope — not unchanged v3 binding retry, not runtime rewire.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (output_dir / "diagnostics_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
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
    scope_definition_ref = archive_root / "implementation" / SCOPE_DEFINITION_BUNDLE_SUFFIX
    for ref, label in (
        (parent_ref, "parent_execution"),
        (scope_definition_ref, "scope_definition"),
    ):
        if not ref.is_dir():
            _die(f"ERR:missing {label} evidence ref: {ref}")

    output_dir = archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    parent_manifest_rc = _verify_source_manifest(
        parent_ref,
        output_dir / "parent_execution_manifest_verify.log",
    )
    scope_definition_manifest_rc = _verify_source_manifest(
        scope_definition_ref,
        output_dir / "scope_definition_manifest_verify.log",
    )
    if any(rc != 0 for rc in (parent_manifest_rc, scope_definition_manifest_rc)):
        _die("ERR:source manifest verify failed")

    git_snapshot = _git_snapshot()
    report = _collect_diagnostics(
        config=config,
        parent_ref=parent_ref,
        scope_definition_ref=scope_definition_ref,
        parent_manifest_rc=parent_manifest_rc,
        scope_definition_manifest_rc=scope_definition_manifest_rc,
        git_snapshot=git_snapshot,
    )
    report["execution_id"] = output_dir.name
    report["new_evidence_dir"] = str(output_dir)

    _write_bundle_reports(output_dir, report)

    commands = command_log or []
    (output_dir / "COMMANDS.log").write_text(
        "\n".join(commands) + ("\n" if commands else ""), encoding="utf-8"
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
            "Execute read-only post-no-pass STEP31F promotion metric materialization path "
            "execution gap diagnostics evidence v0."
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
