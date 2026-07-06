#!/usr/bin/env python3
"""Execute post-PR4908 offline terminal failure artifact materialization v0.

Read-only decomposition artifact materialization from manifest-verified parent evidence.
No economic evaluation, no backtest/WF/MC/stress execution, no runtime authority.
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

CONFIRM_GO = (
    "GO_OPERATOR_RATIFY_NEXT_OFFLINE_ONLY_ARTIFACT_MATERIALIZATION_OR_EVIDENCE_CLASS_"
    "EXECUTION_SCOPE_AFTER_POST_PR4907_TERMINAL_FAILURE_SCOPE_DEFINITION_V0"
)
SCOPE_ID = "post_pr4908_offline_terminal_failure_artifact_materialization_v0"
EXECUTION_ID = (
    "POST_PR4908_OFFLINE_TERMINAL_FAILURE_ARTIFACT_MATERIALIZATION_OR_EVIDENCE_CLASS_EXECUTION_V0"
)
EVIDENCE_CLASS_ID = EXECUTION_ID
PROCESS_CLASSIFICATION = EXECUTION_ID
SCOPE_CLASSIFICATION = "OFFLINE_ONLY_TERMINAL_FAILURE_DECOMPOSITION_ARTIFACT_MATERIALIZATION_AFTER_PR4908_SCOPE_DEFINITION_V0"
EXECUTION_STATUS = "POST_PR4908_OFFLINE_TERMINAL_FAILURE_ARTIFACT_MATERIALIZATION_COMPLETE_V0"
NEXT_CANONICAL_STEP = (
    "GO_OPERATOR_RATIFY_NEXT_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_"
    "AFTER_OFFLINE_TERMINAL_FAILURE_ARTIFACT_MATERIALIZATION_V0"
)
DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/post_pr4908_offline_terminal_failure_artifact_materialization_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "post_pr4908_offline_terminal_failure_artifact_materialization_v0"
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
PARENT_PR4908_CLOSEOUT_SUFFIX = "pr4908_squash_merge_closeout_20260706T050858Z"
PARENT_EVALUATION_SUFFIX = (
    "post_v4_versioned_fleet_offline_economic_evaluation_execution_v0_20260706T040339Z"
)
PARENT_PR4908_MERGE_COMMIT = "968308ae63c7c3b19b8632fce4fc5d2398dc4a81"
FAILED_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
ARTIFACT_CLASSES = (
    "TRADE_LEDGER_LONG_SHORT_DECOMPOSITION_OFFLINE_ARTIFACT_V0",
    "TURNOVER_COST_DRAG_DECOMPOSITION_OFFLINE_ARTIFACT_V0",
    "INSTRUMENT_CONCENTRATION_DECOMPOSITION_OFFLINE_ARTIFACT_V0",
)
GLOBAL_MISSING_FIELDS = (
    "trade_ledger_per_trade_decomposition",
    "long_short_attribution_ledger",
    "short_contribution_ledger_values",
    "turnover_timeseries_decomposition",
    "fee_drag_decomposition_detail",
    "slippage_impact_decomposition_detail",
    "instrument_concentration_beyond_rotation_metadata",
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
    if config.get("selected_class") != "I":
        _die("ERR:config selected_class must be I")
    if config.get("non_authorizing") is not True:
        _die("ERR:config non_authorizing must be true")
    for flag in (
        "economic_evaluation_authorized",
        "new_economic_evaluation_executed",
        "promotion_eligible",
        "runtime_rewire_admissible",
        "same_binding_retry_allowed",
        "failed_bindings_retry_allowed",
        "parameter_rescue_allowed",
        "threshold_lowering_allowed",
        "policy_threshold_rescue_allowed",
        "failed_evidence_is_terminal",
    ):
        expected = flag == "failed_evidence_is_terminal"
        if config.get(flag) is not expected:
            _die(f"ERR:config {flag} must be {expected}")


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


def _metric_value(payload: dict[str, Any], key: str) -> Any:
    field = payload.get(key)
    if isinstance(field, dict):
        if field.get("semantic") == "COMPUTED":
            return field.get("value")
        return {
            "status": "MISSING_SOURCE_EVIDENCE",
            "reason_code": field.get("reason_code", f"{key}_not_computed"),
            "semantic": field.get("semantic", "NOT_COMPUTED"),
        }
    if field is None:
        return {"status": "MISSING_SOURCE_EVIDENCE", "reason_code": f"{key}_absent"}
    return field


def _load_candidate_sources(parent_evaluation_ref: Path, candidate: str) -> dict[str, Any]:
    candidate_result_path = parent_evaluation_ref / f"CANDIDATE_RESULT_{candidate}.json"
    viability_path = parent_evaluation_ref / f"ECONOMIC_VIABILITY_EVIDENCE_{candidate}.json"
    candidate_result = _load_json(candidate_result_path) if candidate_result_path.is_file() else {}
    viability = _load_json(viability_path) if viability_path.is_file() else {}
    candidate_dir_name = candidate_result.get("output_dir", "")
    metrics: dict[str, Any] = {}
    if candidate_dir_name:
        metrics_path = Path(candidate_dir_name) / "METRICS.json"
        if metrics_path.is_file():
            metrics = _load_json(metrics_path)
    return {
        "candidate_result": candidate_result,
        "viability": viability,
        "metrics": metrics,
    }


def _materialize_trade_ledger_long_short(
    *,
    parent_evaluation_ref: Path,
    parent_pr4907_evidence_ref: Path,
) -> dict[str, Any]:
    pr4907_classification: dict[str, Any] = {}
    classification_path = parent_pr4907_evidence_ref / "terminal_failure_classification.json"
    if classification_path.is_file():
        pr4907_classification = _load_json(classification_path)

    per_candidate: dict[str, Any] = {}
    for candidate in FAILED_CANDIDATES:
        sources = _load_candidate_sources(parent_evaluation_ref, candidate)
        candidate_result = sources["candidate_result"]
        viability = sources["viability"]
        metrics = sources["metrics"]
        pr4907_axis = (
            pr4907_classification.get("per_candidate", {})
            .get(candidate, {})
            .get("long_short_contribution", {})
        )
        per_candidate[candidate] = {
            "canonical_candidate_identifier": candidate_result.get(
                "canonical_candidate_identifier", f"{candidate}/post_v4_hypothesis_v0"
            ),
            "evidence_status": candidate_result.get("evidence_status", "ROBUSTNESS_FAILED"),
            "trade_count": _metric_value(metrics, "trade_count"),
            "net_return": candidate_result.get("net_return"),
            "gross_return": candidate_result.get("gross_return"),
            "long_contribution": _metric_value(viability, "long_contribution"),
            "short_contribution": _metric_value(viability, "short_contribution"),
            "trade_ledger_decomposition": {
                "status": "MISSING_SOURCE_EVIDENCE",
                "detail": pr4907_axis.get(
                    "detail", "trade_ledger_long_short_decomposition_not_materialized"
                ),
                "classification": pr4907_axis.get("classification", "MISSING_SOURCE_ARTIFACT"),
            },
            "retry_allowed": False,
            "economic_evaluation_required": False,
        }

    return {
        "artifact_class": "TRADE_LEDGER_LONG_SHORT_DECOMPOSITION_OFFLINE_ARTIFACT_V0",
        "materialization_status": "PARTIAL_BOUND_FROM_PARENT_EVIDENCE",
        "explanatory_only": True,
        "terminal_failure_persists": True,
        "per_candidate": per_candidate,
        "fleet_summary": {
            "aggregate_result": "FLEET_ECONOMIC_VALIDITY_FAIL",
            "ledger_decomposition_available": False,
            "aggregate_trade_counts": {
                candidate: per_candidate[candidate]["trade_count"]
                for candidate in FAILED_CANDIDATES
            },
        },
    }


def _materialize_turnover_cost_drag(
    *,
    parent_evaluation_ref: Path,
    parent_pr4907_evidence_ref: Path,
) -> dict[str, Any]:
    pr4907_classification: dict[str, Any] = {}
    classification_path = parent_pr4907_evidence_ref / "terminal_failure_classification.json"
    if classification_path.is_file():
        pr4907_classification = _load_json(classification_path)

    per_candidate: dict[str, Any] = {}
    for candidate in FAILED_CANDIDATES:
        sources = _load_candidate_sources(parent_evaluation_ref, candidate)
        candidate_result = sources["candidate_result"]
        viability = sources["viability"]
        gross = float(candidate_result.get("gross_return", 0.0) or 0.0)
        net = float(candidate_result.get("net_return", 0.0) or 0.0)
        pr4907_axis = (
            pr4907_classification.get("per_candidate", {})
            .get(candidate, {})
            .get("turnover_cost_drag_decomposition", {})
        )
        per_candidate[candidate] = {
            "gross_return": gross,
            "net_return": net,
            "aggregate_cost_drag_delta": gross - net,
            "fee_drag": _metric_value(viability, "fee_drag"),
            "funding_drag": _metric_value(viability, "funding_drag"),
            "slippage_impact": _metric_value(viability, "slippage_impact"),
            "turnover": _metric_value(viability, "turnover"),
            "fee_slippage_funding_proxy": (
                pr4907_classification.get("per_candidate", {})
                .get(candidate, {})
                .get("fee_slippage_funding_drag", {})
            ),
            "turnover_decomposition": {
                "status": "MISSING_SOURCE_EVIDENCE",
                "detail": pr4907_axis.get(
                    "detail", "turnover_vs_gross_edge_artifact_not_materialized"
                ),
                "classification": pr4907_axis.get("classification", "MISSING_SOURCE_ARTIFACT"),
            },
            "retry_allowed": False,
            "economic_evaluation_required": False,
        }

    return {
        "artifact_class": "TURNOVER_COST_DRAG_DECOMPOSITION_OFFLINE_ARTIFACT_V0",
        "materialization_status": "PARTIAL_BOUND_FROM_PARENT_EVIDENCE",
        "explanatory_only": True,
        "terminal_failure_persists": True,
        "per_candidate": per_candidate,
        "fleet_summary": {
            "aggregate_result": "FLEET_ECONOMIC_VALIDITY_FAIL",
            "turnover_timeseries_available": False,
            "aggregate_cost_drag_deltas": {
                candidate: per_candidate[candidate]["aggregate_cost_drag_delta"]
                for candidate in FAILED_CANDIDATES
            },
        },
    }


def _materialize_instrument_concentration(
    *,
    parent_evaluation_ref: Path,
    parent_pr4907_evidence_ref: Path,
) -> dict[str, Any]:
    pr4907_classification: dict[str, Any] = {}
    classification_path = parent_pr4907_evidence_ref / "terminal_failure_classification.json"
    if classification_path.is_file():
        pr4907_classification = _load_json(classification_path)

    per_candidate: dict[str, Any] = {}
    instrument_ids: set[str] = set()
    for candidate in FAILED_CANDIDATES:
        sources = _load_candidate_sources(parent_evaluation_ref, candidate)
        viability = sources["viability"]
        instrument_id = viability.get("instrument_id_or_universe")
        if isinstance(instrument_id, str):
            instrument_ids.add(instrument_id)
        pr4907_axis = (
            pr4907_classification.get("per_candidate", {})
            .get(candidate, {})
            .get("instrument_concentration_contribution_beyond_rotation_metadata", {})
        )
        per_candidate[candidate] = {
            "instrument_id_or_universe": instrument_id
            or {"status": "MISSING_SOURCE_EVIDENCE", "reason_code": "instrument_id_absent"},
            "single_instrument_binding": True,
            "rotation_metadata_artifact": {
                "status": "MISSING_SOURCE_EVIDENCE",
                "detail": "instrument_rotation_metadata_not_materialized_in_parent_evidence",
            },
            "concentration_beyond_rotation": {
                "status": "MISSING_SOURCE_EVIDENCE",
                "detail": pr4907_axis.get(
                    "detail",
                    "instrument_concentration_beyond_rotation_metadata_not_materialized",
                ),
                "classification": pr4907_axis.get("classification", "MISSING_SOURCE_ARTIFACT"),
            },
            "retry_allowed": False,
            "economic_evaluation_required": False,
        }

    return {
        "artifact_class": "INSTRUMENT_CONCENTRATION_DECOMPOSITION_OFFLINE_ARTIFACT_V0",
        "materialization_status": "PARTIAL_BOUND_FROM_PARENT_EVIDENCE",
        "explanatory_only": True,
        "terminal_failure_persists": True,
        "per_candidate": per_candidate,
        "fleet_summary": {
            "aggregate_result": "FLEET_ECONOMIC_VALIDITY_FAIL",
            "distinct_instrument_ids": sorted(instrument_ids),
            "multi_instrument_rotation_metadata_available": False,
            "note": (
                "All candidates bound to single-instrument futures dataset; "
                "concentration beyond rotation metadata remains unavailable."
            ),
        },
    }


def _artifact_to_tsv_rows(artifact: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for candidate, payload in artifact.get("per_candidate", {}).items():
        rows.append(
            {
                "artifact_class": artifact["artifact_class"],
                "candidate": candidate,
                "payload_json": json.dumps(payload, sort_keys=True),
            }
        )
    return rows


def _write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(buffer.getvalue(), encoding="utf-8")


def _collect_artifact_materialization(
    *,
    config: dict[str, Any],
    parent_pr4905_output_ref: Path,
    parent_pr4907_evidence_ref: Path,
    parent_evaluation_ref: Path,
    parent_manifest_status: dict[str, int],
    git_snapshot: dict[str, str],
) -> dict[str, Any]:
    trade_ledger = _materialize_trade_ledger_long_short(
        parent_evaluation_ref=parent_evaluation_ref,
        parent_pr4907_evidence_ref=parent_pr4907_evidence_ref,
    )
    turnover_cost_drag = _materialize_turnover_cost_drag(
        parent_evaluation_ref=parent_evaluation_ref,
        parent_pr4907_evidence_ref=parent_pr4907_evidence_ref,
    )
    instrument_concentration = _materialize_instrument_concentration(
        parent_evaluation_ref=parent_evaluation_ref,
        parent_pr4907_evidence_ref=parent_pr4907_evidence_ref,
    )

    authority_boundary = {
        "authority_effect": "NONE",
        "economic_evaluation_authorized": False,
        "economic_evaluation_executed": False,
        "new_economic_evaluation_executed": False,
        "offline_evaluation_executed": False,
        "backtest_executed": False,
        "live_authorized": False,
        "shadow_authorized": False,
        "paper_authorized": False,
        "testnet_authorized": False,
        "orders_allowed": False,
        "promotion_authority": False,
        "runtime_authority_created": False,
        "runtime_rewire_admissible": False,
        "same_binding_retry_allowed": False,
        "unchanged_retry_allowed": False,
        "policy_threshold_rescue_allowed": False,
        "failed_evidence_is_terminal": True,
    }

    return {
        "aggregate_result": "FLEET_ECONOMIC_VALIDITY_FAIL",
        "artifact_classes_materialized": list(ARTIFACT_CLASSES),
        "artifact_materialization_report": {
            "TRADE_LEDGER_LONG_SHORT_DECOMPOSITION_OFFLINE_ARTIFACT_V0": trade_ledger,
            "TURNOVER_COST_DRAG_DECOMPOSITION_OFFLINE_ARTIFACT_V0": turnover_cost_drag,
            "INSTRUMENT_CONCENTRATION_DECOMPOSITION_OFFLINE_ARTIFACT_V0": instrument_concentration,
        },
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
        "missing_source_evidence": list(GLOBAL_MISSING_FIELDS),
        "new_candidates_ratified": False,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "parent_bindings": {
            "parent_pr4905_output_bundle": str(parent_pr4905_output_ref),
            "parent_pr4907_evidence_bundle": str(parent_pr4907_evidence_ref),
            "parent_evaluation_bundle": str(parent_evaluation_ref),
            "parent_pr4908_merge_commit": PARENT_PR4908_MERGE_COMMIT,
            "parent_scope_definition_id": config.get("parent_scope_definition_id"),
        },
        "parent_manifest_status": parent_manifest_status,
        "parent_pr4907_aggregate_result": "FLEET_ECONOMIC_VALIDITY_FAIL",
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_id": SCOPE_ID,
        "selected_class": "I",
        "strategy_version": "post_v4_hypothesis_v0",
        "terminal_negative_evidence_unchanged": True,
        "verdict": EXECUTION_STATUS,
    }


def run_offline_terminal_failure_artifact_materialization_v0(
    *,
    go_token: str,
    parent_pr4905_output_bundle: Path,
    parent_pr4905_closeout_dir: Path,
    parent_pr4906_closeout_dir: Path,
    parent_pr4907_evidence_bundle: Path,
    parent_pr4907_closeout_dir: Path,
    parent_pr4908_closeout_dir: Path,
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
        ("parent_pr4907_evidence_bundle", parent_pr4907_evidence_bundle),
        ("parent_pr4907_closeout_dir", parent_pr4907_closeout_dir),
        ("parent_pr4908_closeout_dir", parent_pr4908_closeout_dir),
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
        ("parent_pr4907_evidence_bundle", parent_pr4907_evidence_bundle),
        ("parent_pr4907_closeout_dir", parent_pr4907_closeout_dir),
        ("parent_pr4908_closeout_dir", parent_pr4908_closeout_dir),
        ("parent_evaluation_bundle", parent_evaluation_bundle),
    ):
        rc = _verify_source_manifest(ref, output_dir / f"{key}_manifest_verify.log")
        manifest_status[key] = rc
        if rc != 0:
            _die(f"ERR:manifest invalid for {key}: {ref}")

    git_snapshot = _git_snapshot()
    report = _collect_artifact_materialization(
        config=config,
        parent_pr4905_output_ref=parent_pr4905_output_bundle,
        parent_pr4907_evidence_ref=parent_pr4907_evidence_bundle,
        parent_evaluation_ref=parent_evaluation_bundle,
        parent_manifest_status=manifest_status,
        git_snapshot=git_snapshot,
    )
    report["durable_evidence_path"] = str(output_dir)

    artifacts = report["artifact_materialization_report"]
    (output_dir / "ARTIFACT_MATERIALIZATION_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "parent_manifest_verification.json").write_text(
        json.dumps(
            {
                "manifest_verify_results": manifest_status,
                "all_parent_manifests_verified": all(rc == 0 for rc in manifest_status.values()),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "TRADE_LEDGER_LONG_SHORT_DECOMPOSITION_OFFLINE_ARTIFACT_V0.json").write_text(
        json.dumps(
            artifacts["TRADE_LEDGER_LONG_SHORT_DECOMPOSITION_OFFLINE_ARTIFACT_V0"],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "TURNOVER_COST_DRAG_DECOMPOSITION_OFFLINE_ARTIFACT_V0.json").write_text(
        json.dumps(
            artifacts["TURNOVER_COST_DRAG_DECOMPOSITION_OFFLINE_ARTIFACT_V0"],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "INSTRUMENT_CONCENTRATION_DECOMPOSITION_OFFLINE_ARTIFACT_V0.json").write_text(
        json.dumps(
            artifacts["INSTRUMENT_CONCENTRATION_DECOMPOSITION_OFFLINE_ARTIFACT_V0"],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    tsv_rows: list[dict[str, str]] = []
    for artifact in artifacts.values():
        tsv_rows.extend(_artifact_to_tsv_rows(artifact))
    _write_tsv(
        output_dir / "ARTIFACT_MATERIALIZATION_SUMMARY.tsv",
        tsv_rows,
        fieldnames=[
            "artifact_class",
            "candidate",
            "payload_json",
        ],
    )

    execution_summary = {
        "verdict": EXECUTION_STATUS,
        "aggregate_result": report["aggregate_result"],
        "economic_validity_offline_gate_pass": False,
        "artifact_classes_materialized": list(ARTIFACT_CLASSES),
        "missing_source_evidence": list(GLOBAL_MISSING_FIELDS),
        "runtime_authority_created": False,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "go_token_consumed": CONFIRM_GO,
    }
    (output_dir / "execution_summary.json").write_text(
        json.dumps(execution_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "EXECUTION_SUMMARY.md").write_text(
        "\n".join(
            [
                "# Offline Terminal Failure Artifact Materialization Summary",
                "",
                f"- execution_status: `{EXECUTION_STATUS}`",
                f"- aggregate_result: `{report['aggregate_result']}`",
                f"- economic_validity_offline_gate_pass: `false`",
                f"- artifact_classes_materialized: `{','.join(ARTIFACT_CLASSES)}`",
                f"- missing_source_evidence_count: `{len(GLOBAL_MISSING_FIELDS)}`",
                f"- runtime_authority_created: `false`",
                f"- next_canonical_step: `{NEXT_CANONICAL_STEP}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output_dir.joinpath("AUTHORITY_BOUNDARY.txt").write_text(
        "\n".join(
            [
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "NEW_ECONOMIC_EVALUATION_EXECUTED=false",
                "OFFLINE_EVALUATION_EXECUTED=false",
                "BACKTEST_EXECUTED=false",
                "FAILED_EVIDENCE_IS_TERMINAL=true",
                "UNCHANGED_RETRY_ALLOWED=false",
                "POLICY_THRESHOLD_RESCUE_ALLOWED=false",
                "RUNTIME_AUTHORITY_CREATED=false",
                "LIVE_AUTHORIZED=false",
                "ORDERS_ALLOWED=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    write_manifest_sha256(output_dir)
    manifest_rc = 0 if verify_manifest_sha256(output_dir)[0] else 1
    if manifest_rc != 0:
        _die(f"ERR:output manifest verify failed: {output_dir}")

    return {
        "verdict": EXECUTION_STATUS,
        "durable_evidence_path": str(output_dir),
        "manifest_verify_rc": manifest_rc,
        "artifact_classes_materialized": list(ARTIFACT_CLASSES),
        "missing_source_evidence": list(GLOBAL_MISSING_FIELDS),
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "parent_manifest_verify_results": manifest_status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute post-PR4908 offline terminal failure artifact materialization v0"
    )
    parser.add_argument("--go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()

    archive = args.durable_evidence_root
    result = run_offline_terminal_failure_artifact_materialization_v0(
        go_token=args.go_token,
        parent_pr4905_output_bundle=archive / "implementation" / PARENT_PR4905_OUTPUT_SUFFIX,
        parent_pr4905_closeout_dir=archive / "implementation" / PARENT_PR4905_CLOSEOUT_SUFFIX,
        parent_pr4906_closeout_dir=archive / "implementation" / PARENT_PR4906_CLOSEOUT_SUFFIX,
        parent_pr4907_evidence_bundle=archive / "implementation" / PARENT_PR4907_EVIDENCE_SUFFIX,
        parent_pr4907_closeout_dir=archive / "implementation" / PARENT_PR4907_CLOSEOUT_SUFFIX,
        parent_pr4908_closeout_dir=archive / "implementation" / PARENT_PR4908_CLOSEOUT_SUFFIX,
        parent_evaluation_bundle=archive / "implementation" / PARENT_EVALUATION_SUFFIX,
        durable_archive_root=archive,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    for key, value in result.items():
        print(f"{key.upper()}={value}")


if __name__ == "__main__":
    main()
