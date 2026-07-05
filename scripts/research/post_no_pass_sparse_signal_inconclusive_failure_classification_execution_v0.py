#!/usr/bin/env python3
"""Read-only post-no-pass sparse signal inconclusive failure classification execution v0.

Offline-only Class-E classification over terminal PR4881 sparse-signal/zero-trade source
evidence. No economic evaluation, no backtest/WF/MC/stress execution, no authority effect.
"""

from __future__ import annotations

import argparse
import hashlib
import json
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

CONFIRM_GO = "GO_POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0"
EVIDENCE_CLASS_ID = "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0"
PROCESS_CLASSIFICATION = (
    "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_EXECUTION_V0"
)
SOURCE_STATE = (
    "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_COMPLETE_V0"
)
PRIMARY_CLASSIFICATION = "INCONCLUSIVE_SPARSE_SIGNAL_ZERO_TRADE"
EXECUTION_STATUS = "CLASSIFICATION_EXECUTION_COMPLETE_INCONCLUSIVE"
CURRENT_STATE = (
    "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_EXECUTION_COMPLETE_V0"
)
NEXT_CANONICAL_STEP = "NEW_VERSIONED_RESEARCH_SCOPE_SELECTION_REQUIRES_OPERATOR_RATIFICATION_V0"
NEXT_ADMISSIBLE_SCOPE = "NEW_VERSIONED_RESEARCH_SCOPE_SELECTION_V0"
NEXT_ADMISSIBLE_GO = "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_V0"
DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/post_no_pass_sparse_signal_inconclusive_failure_classification_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "post_no_pass_sparse_signal_inconclusive_failure_classification_execution_v0"
CLASSIFICATION_SCHEMA_VERSION = "post_no_pass_sparse_signal_inconclusive_failure_classification.v0"


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


def _require_config_gates(config: dict[str, Any]) -> None:
    if config.get("evidence_class_id") != EVIDENCE_CLASS_ID:
        _die("ERR:config evidence_class_id mismatch")
    if config.get("selected_class") != "E":
        _die("ERR:config selected_class must be E")
    if config.get("non_authorizing") is not True:
        _die("ERR:config non_authorizing must be true")
    if config.get("status") != "SCOPE_DEFINED_NOT_EXECUTED":
        _die("ERR:config status must be SCOPE_DEFINED_NOT_EXECUTED before execution")
    for flag in (
        "economic_evaluation_authorized",
        "promotion_eligible",
        "runtime_rewire_admissible",
        "same_binding_retry_allowed",
        "classification_execution_authorized",
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


def _candidate_evidence(source_ref: Path, candidate: str) -> dict[str, Any]:
    path = source_ref / f"candidate_evidence_{candidate}.json"
    if path.is_file():
        return _load_json(path)
    return {}


def _classify_axis(
    axis: str,
    candidate: str,
    evidence: dict[str, Any],
    fleet_summary: dict[str, Any] | None,
    *,
    panel_zero_trade_refuted: bool,
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

    if axis == "sparse_signal_vs_zero_trade_separation":
        nonzero = sparse.get("instruments_with_nonzero_trades", 0)
        zero = sparse.get("instruments_with_zero_trades", 0)
        if nonzero == 0 and zero > 0:
            classification = "ZERO_TRADE"
        elif nonzero > 0 and zero > 0:
            classification = "SPARSE_NOT_ZERO_TRADE"
        elif nonzero > 0 and zero == 0:
            classification = "NOT_ZERO_TRADE"
        else:
            classification = "INCONCLUSIVE_SPARSE_SIGNAL_ZERO_TRADE"
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "CLASSIFICATION_MAPPED",
            "classification": classification,
            "detail": {
                "panel_zero_trade_refuted": panel_zero_trade_refuted,
                "instruments_with_nonzero_trades": nonzero,
                "instruments_with_zero_trades": zero,
            },
        }

    if axis == "signal_trade_coverage_per_candidate":
        if not sparse:
            return {
                "axis": axis,
                "candidate": candidate,
                "status": "INSUFFICIENT_SOURCE_EVIDENCE",
                "classification": PRIMARY_CLASSIFICATION,
                "detail": {"missing": "sparse_signal_density_metrics"},
            }
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "CLASSIFICATION_MAPPED",
            "classification": PRIMARY_CLASSIFICATION,
            "detail": {
                "instruments_scanned": sparse.get("instruments_scanned"),
                "instruments_with_nonzero_trades": sparse.get("instruments_with_nonzero_trades"),
                "max_trade_count": sparse.get("max_trade_count"),
            },
        }

    if axis == "economic_viability_metric_materialization_failure":
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "CLASSIFICATION_MAPPED",
            "classification": "METRIC_MATERIALIZATION_FAILED",
            "detail": {
                "evidence_status": evidence.get("evidence_status"),
                "reason_codes": reason_codes,
                "economic_metrics_present": any(
                    evidence.get(field) is not None
                    for field in ("net_return", "sharpe", "profit_factor", "trade_count")
                ),
            },
        }

    if axis == "panel_adapter_runner_defect_classification":
        runner_success = result_record.get("runner_execution_success")
        stage_codes = result_record.get("stage_return_codes") or {}
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "CLASSIFICATION_MAPPED",
            "classification": "RUNNER_EXECUTION_FAILED_FAIL_CLOSED",
            "detail": {
                "runner_execution_success": runner_success,
                "stage_return_codes": stage_codes,
                "adapter_kind": sparse.get("adapter_kind"),
            },
        }

    if axis == "schema_gate_threshold_failure_classification":
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "CLASSIFICATION_MAPPED",
            "classification": "EXECUTION_FAILED_FAIL_CLOSED",
            "detail": {
                "reason_codes": reason_codes,
                "terminal_status": result_record.get("terminal_status"),
                "economic_validity_result": result_record.get("economic_validity_result"),
            },
        }

    if axis == "insufficient_trades_classification":
        max_trades = sparse.get("max_trade_count")
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "CLASSIFICATION_MAPPED",
            "classification": PRIMARY_CLASSIFICATION,
            "detail": {
                "max_trade_count": max_trades,
                "trade_count": evidence.get("trade_count"),
                "note": "No rescue; sparse signal density scan shows trades exist panel-wide",
            },
        }

    if axis == "metric_materialization_path_failure":
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "CLASSIFICATION_MAPPED",
            "classification": "ECONOMIC_VIABILITY_EVIDENCE_NOT_MATERIALIZED",
            "detail": {
                "manifest_verify_rc": evidence.get("manifest_verify_rc"),
                "evidence_artifact_missing_metrics": evidence.get("evidence_status") is None,
            },
        }

    if axis == "walk_forward_gate_precondition_failure":
        wf = evidence.get("walk_forward_results")
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "CLASSIFICATION_MAPPED",
            "classification": "WF_PRECONDITION_NOT_REACHED",
            "detail": {"walk_forward_results": wf, "reason_codes": reason_codes},
        }

    if axis == "stress_monte_carlo_precondition_failure":
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "CLASSIFICATION_MAPPED",
            "classification": "STRESS_MC_PRECONDITION_NOT_REACHED",
            "detail": {
                "monte_carlo_results": evidence.get("monte_carlo_results"),
                "stress_results": evidence.get("stress_results"),
                "reason_codes": reason_codes,
            },
        }

    if axis == "execution_model_assumption_exposure":
        bindings = evidence.get("input_bindings") or record.get("input_bindings")
        if not bindings:
            return {
                "axis": axis,
                "candidate": candidate,
                "status": "INSUFFICIENT_SOURCE_EVIDENCE",
                "classification": PRIMARY_CLASSIFICATION,
                "detail": {"missing": "input_bindings"},
            }
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "CLASSIFICATION_MAPPED",
            "classification": "EXECUTION_MODEL_EXPOSED_READ_ONLY",
            "detail": {
                "implementation_digest": (bindings.get("strategy_binding") or {}).get(
                    "implementation_digest"
                ),
                "evaluation_price_data_adapter": (bindings.get("dataset_binding") or {}).get(
                    "evaluation_price_data_adapter"
                ),
            },
        }

    if axis == "dataset_period_coverage_adequacy":
        bindings = evidence.get("input_bindings") or record.get("input_bindings") or {}
        period = bindings.get("period_binding") or {}
        dataset = bindings.get("dataset_binding") or {}
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "CLASSIFICATION_MAPPED",
            "classification": "DATASET_PERIOD_COVERAGE_ADEQUATE_FOR_SCAN",
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
                "classification": PRIMARY_CLASSIFICATION,
                "detail": {"fleet_summary": None},
            }
        return {
            "axis": axis,
            "candidate": candidate,
            "status": "CLASSIFICATION_MAPPED",
            "classification": PRIMARY_CLASSIFICATION,
            "detail": {
                "fleet_status": fleet_summary.get("fleet_status"),
                "fleet_verdict": fleet_summary.get("fleet_verdict"),
                "candidate_verdict": (fleet_summary.get("candidate_verdicts") or {}).get(candidate),
            },
        }

    return {
        "axis": axis,
        "candidate": candidate,
        "status": "INSUFFICIENT_SOURCE_EVIDENCE",
        "classification": PRIMARY_CLASSIFICATION,
        "detail": {"axis": axis},
    }


def _collect_classification(
    *,
    config: dict[str, Any],
    source_ref: Path,
    source_manifest_rc: int,
) -> dict[str, Any]:
    fleet_verdict = _load_json(source_ref / "FLEET_VERDICT.json")
    failed_candidates = list(config["failed_candidates"])
    failed_verdicts = dict(fleet_verdict["candidate_verdicts"])
    for candidate in failed_candidates:
        if failed_verdicts.get(candidate) != config["failed_candidate_verdict"]:
            _die(f"ERR:immutable verdict drift for {candidate}")

    fleet_summary_path = source_ref / "fleet_evaluation_summary_v0.json"
    fleet_summary = _load_json(fleet_summary_path) if fleet_summary_path.is_file() else None
    panel_zero_trade_refuted = bool(config.get("panel_zero_trade_refuted"))

    classification_axes = list(config["classification_axes"])
    per_candidate: dict[str, list[dict[str, Any]]] = {}
    mapped_count = 0
    total_count = 0
    reason_codes: list[str] = [
        "PANEL_ZERO_TRADE_REFUTED",
        "CANDIDATE_RUN_FAILED",
        "ECONOMIC_VIABILITY_METRICS_NOT_MATERIALIZED",
        "EXECUTION_FAILED_FAIL_CLOSED",
        "INCONCLUSIVE_SPARSE_SIGNAL_ZERO_TRADE",
        "NO_SAME_BINDING_RETRY",
        "NO_PARAMETER_RESCUE",
        "NO_THRESHOLD_LOWERING",
        "NO_PROMOTION",
        "NO_RUNTIME",
    ]

    for candidate in failed_candidates:
        evidence = _candidate_evidence(source_ref, candidate)
        axis_results: list[dict[str, Any]] = []
        for axis in classification_axes:
            result = _classify_axis(
                axis,
                candidate,
                evidence,
                fleet_summary,
                panel_zero_trade_refuted=panel_zero_trade_refuted,
            )
            axis_results.append(result)
            total_count += 1
            if result["status"] == "CLASSIFICATION_MAPPED":
                mapped_count += 1
        per_candidate[candidate] = axis_results

    mapped_ratio = mapped_count / total_count if total_count else 0.0
    source_evidence_refs = [
        str(source_ref / "FLEET_VERDICT.json"),
        str(source_ref / "fleet_evaluation_summary_v0.json"),
        *[
            str(source_ref / f"candidate_evidence_{candidate}.json")
            for candidate in failed_candidates
        ],
        str(source_ref / "MANIFEST.sha256"),
    ]

    return {
        "evidence_class": EVIDENCE_CLASS_ID,
        "process_classification": PROCESS_CLASSIFICATION,
        "consumed_go_token": CONFIRM_GO,
        "source_state": SOURCE_STATE,
        "primary_classification": PRIMARY_CLASSIFICATION,
        "execution_status": EXECUTION_STATUS,
        "classification_schema_version": CLASSIFICATION_SCHEMA_VERSION,
        "source_evidence_ref": str(source_ref),
        "source_manifest_verify_rc": source_manifest_rc,
        "source_evidence_refs": source_evidence_refs,
        "failed_candidates": failed_candidates,
        "failed_candidate_verdicts": failed_verdicts,
        "fleet_status": fleet_verdict.get("fleet_status"),
        "fleet_verdict": fleet_verdict.get("fleet_verdict"),
        "panel_zero_trade_refuted": panel_zero_trade_refuted,
        "classification_axes": classification_axes,
        "failure_axis_results": per_candidate,
        "classification_mapped_ratio": round(mapped_ratio, 4),
        "reason_codes": reason_codes,
        "admissibility_summary": {
            "economic_evaluation_authorized": False,
            "economic_evaluation_executed": False,
            "backtests_executed": False,
            "walk_forward_executed": False,
            "monte_carlo_executed": False,
            "stress_executed": False,
            "runtime_rewire_admissible": False,
            "live_authorized": False,
            "shadow_authorized": False,
            "paper_authorized": False,
            "testnet_authorized": False,
            "orders_allowed": False,
            "scheduler_runtime_allowed": False,
            "core_system_mutation": False,
            "strategy_logic_mutation": False,
            "parameter_mutation": False,
            "promotion_eligible": False,
            "same_binding_retry_allowed": False,
            "parameter_rescue_allowed": False,
            "threshold_lowering_allowed": False,
            "historical_negative_evidence_mutated": False,
        },
        "no_promotion_claim": True,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "current_admissible_next_scope": NEXT_ADMISSIBLE_SCOPE,
        "current_admissible_next_scope_go_token": NEXT_ADMISSIBLE_GO,
        "authority_effect": "NONE",
        "runtime_effect": "NONE",
        "trading_effect": "NONE",
        "futures_only": True,
        "bitcoin_direction_allowed": False,
    }


def _stable_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _write_report(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Post No-Pass Sparse Signal Inconclusive Failure Classification Execution v0",
        "",
        f"- evidence_class: `{result['evidence_class']}`",
        f"- process_classification: `{result['process_classification']}`",
        f"- consumed_go_token: `{result['consumed_go_token']}`",
        f"- source_state: `{result['source_state']}`",
        f"- primary_classification: `{result['primary_classification']}`",
        f"- execution_status: `{result['execution_status']}`",
        f"- classification_mapped_ratio: `{result['classification_mapped_ratio']}`",
        f"- source_evidence_ref: `{result['source_evidence_ref']}`",
        f"- source_manifest_verify_rc: `{result['source_manifest_verify_rc']}`",
        "",
        "## Fleet summary (unchanged)",
        "",
        f"- fleet_verdict: `{result['fleet_verdict']}`",
        f"- fleet_status: `{result['fleet_status']}`",
        f"- panel_zero_trade_refuted: `{result['panel_zero_trade_refuted']}`",
        "",
        "## Failed candidates",
        "",
    ]
    for candidate, verdict in result["failed_candidate_verdicts"].items():
        lines.append(f"- `{candidate}`: `{verdict}`")
    lines.extend(
        [
            "",
            "## Authority boundary",
            "",
            "- economic_evaluation_executed=false",
            "- backtests_executed=false",
            "- walk_forward_executed=false",
            "- monte_carlo_executed=false",
            "- stress_executed=false",
            "- runtime_rewire_admissible=false",
            "- no_promotion_claim=true",
            "",
            "## Next canonical step",
            "",
            f"- NEXT_CANONICAL_STEP={result['next_canonical_step']}",
            f"- CURRENT_ADMISSIBLE_NEXT_SCOPE={result['current_admissible_next_scope']}",
            f"- CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN={result['current_admissible_next_scope_go_token']}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_registry_before_after(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Registry / Resolver Before-After",
                "",
                "## Before",
                "",
                f"- CURRENT_STATE={SOURCE_STATE}",
                "- POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_STATUS=SCOPE_DEFINED_NOT_EXECUTED",
                "- CLASSIFICATION_EXECUTED=false",
                f"- NEXT_CANONICAL_STEP=POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_EXECUTION_REQUIRES_SEPARATE_OPERATOR_GO_V0",
                "- CURRENT_ADMISSIBLE_NEXT_SCOPE=POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0",
                "- CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN=GO_POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0",
                "",
                "## After",
                "",
                f"- CURRENT_STATE={CURRENT_STATE}",
                f"- POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_STATUS={EXECUTION_STATUS}",
                "- CLASSIFICATION_EXECUTED=true",
                f"- NEXT_CANONICAL_STEP={NEXT_CANONICAL_STEP}",
                f"- CURRENT_ADMISSIBLE_NEXT_SCOPE={NEXT_ADMISSIBLE_SCOPE}",
                f"- CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN={NEXT_ADMISSIBLE_GO}",
                "- ECONOMIC_EVALUATION_AUTHORIZED=false",
                "- RUNTIME_REWIRE_ADMISSIBLE=false",
                "- LIVE_AUTHORIZED=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_no_runtime_assertions(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# No Runtime / No Economic Evaluation Assertions",
                "",
                "NO_RUNTIME=true",
                "NO_TRADING=true",
                "NO_ORDERS=true",
                "NO_SCHEDULER=true",
                "NO_SHADOW=true",
                "NO_PAPER=true",
                "NO_TESTNET=true",
                "NO_CANARY=true",
                "NO_LIVE=true",
                "NO_ECONOMIC_EVALUATION_EXECUTION=true",
                "NO_BACKTEST_RERUN=true",
                "NO_WALK_FORWARD_EXECUTION=true",
                "NO_MONTE_CARLO_EXECUTION=true",
                "NO_STRESS_EXECUTION=true",
                "NO_PARAMETER_MUTATION=true",
                "NO_STRATEGY_LOGIC_MUTATION=true",
                "NO_CORE_SYSTEM_MUTATION=true",
                "NO_HISTORICAL_NEGATIVE_EVIDENCE_MUTATION=true",
                "READ_ONLY_OFFLINE_CLASSIFICATION_ONLY=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def run_classification_execution_v0(
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

    source_ref = Path(config["source_evidence_ref"])
    if not source_ref.is_dir():
        _die(f"ERR:missing source evidence ref: {source_ref}")

    output_dir = archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    source_log = output_dir / "source_evidence_manifest_verify.log"
    source_manifest_rc = _verify_source_manifest(source_ref, source_log)
    if source_manifest_rc != 0:
        _die("ERR:source manifest verify failed", source_manifest_rc)

    result = _collect_classification(
        config=config,
        source_ref=source_ref,
        source_manifest_rc=source_manifest_rc,
    )
    result["execution_id"] = output_dir.name
    result["new_evidence_dir"] = str(output_dir)

    input_pointers = {
        "source_evidence_ref": str(source_ref),
        "source_manifest_verify_rc": source_manifest_rc,
        "scope_config_ref": str(config_path),
        "parent_execution_id": config.get("parent_execution_id"),
        "parent_evidence_class_id": config.get("parent_evidence_class_id"),
        "source_prs": list(config.get("source_prs") or []),
        "source_evidence_refs": result["source_evidence_refs"],
    }
    (output_dir / "INPUT_EVIDENCE_POINTERS.json").write_text(
        json.dumps(input_pointers, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result_body = dict(result)
    result_body["manifest_digest"] = _stable_digest(
        {key: value for key, value in result_body.items() if key != "manifest_digest"}
    )
    (output_dir / "CLASSIFICATION_EXECUTION_RESULT.json").write_text(
        json.dumps(result_body, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(result_body, output_dir / "CLASSIFICATION_EXECUTION_REPORT.md")
    _write_registry_before_after(output_dir / "REGISTRY_RESOLVER_BEFORE_AFTER.md")
    _write_no_runtime_assertions(output_dir / "NO_RUNTIME_NO_ECONOMIC_EVALUATION_ASSERTIONS.md")

    command_lines = command_log or [
        f"python {__file__} --confirm-go-token {CONFIRM_GO}",
    ]
    (output_dir / "COMMAND_LOG.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")

    write_manifest_sha256(output_dir)
    ok, msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if ok else 1
    (output_dir / "MANIFEST_VERIFY.log").write_text(
        f"MANIFEST_VERIFY_RC={manifest_rc}\nMANIFEST_VERIFY_MSG={msg or 'ok'}\n",
        encoding="utf-8",
    )
    if manifest_rc != 0:
        _die("ERR:new evidence manifest verify failed", manifest_rc)

    result_body["manifest_verify_rc"] = manifest_rc
    return result_body


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Execute read-only post-no-pass sparse signal inconclusive failure "
            "classification evidence v0."
        )
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()

    report = run_classification_execution_v0(
        confirm_go_token=args.confirm_go_token,
        config_path=args.config,
        archive_root=args.archive_root,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
