#!/usr/bin/env python3
"""Read-only post-no-pass robustness failure diagnostics evidence execution v0.

Offline-only Class-E diagnostics over terminal PR4875/4876 source evidence.
No economic evaluation, no backtest/WF/MC/stress execution, no authority effect.
"""

from __future__ import annotations

import argparse
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

CONFIRM_GO = "GO_POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
EVIDENCE_CLASS_ID = "POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_CLASS_V0"
DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/post_no_pass_robustness_failure_diagnostics_evidence_class_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "post_no_pass_robustness_failure_diagnostics_evidence_execution_v0"
NEXT_STEP_RATIFICATION = "NEW_VERSIONED_RESEARCH_SCOPE_SELECTION_REQUIRES_OPERATOR_RATIFICATION_V0"
NEXT_STEP_GAP = "POST_NO_PASS_DIAGNOSTICS_SOURCE_EVIDENCE_GAP_REQUIRES_OPERATOR_DECISION_V0"
SUFFICIENCY_MAPPED_RATIO = 2 / 3


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _die(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _axis_status(
    payload: dict[str, Any] | None, required_keys: tuple[str, ...]
) -> tuple[str, dict[str, Any]]:
    if payload is None:
        return "DIAGNOSTIC_INPUT_NOT_FOUND", {}
    missing = [key for key in required_keys if payload.get(key) in (None, "", [], {})]
    if missing:
        return "INSUFFICIENT_SOURCE_EVIDENCE", {"missing_fields": missing, "available": payload}
    return "DIAGNOSTIC_MAPPED", payload


def _diagnose_axis(
    axis: str,
    candidate: str,
    evidence: dict[str, Any],
    fleet_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    if axis == "trade_count_sufficiency_sparse_signal_failure":
        status, detail = _axis_status(
            {
                "trade_count": evidence.get("trade_count"),
                "reason_codes": evidence.get("reason_codes"),
                "evidence_status": evidence.get("evidence_status"),
            },
            ("trade_count", "reason_codes"),
        )
    elif axis == "fee_slippage_funding_drag_decomposition":
        status, detail = _axis_status(
            {
                "fee_drag": evidence.get("fee_drag"),
                "funding_drag": evidence.get("funding_drag"),
                "slippage_impact": evidence.get("slippage_impact"),
                "gross_return": evidence.get("gross_return"),
                "net_return": evidence.get("net_return"),
            },
            ("gross_return", "net_return"),
        )
        if status == "DIAGNOSTIC_MAPPED" and evidence.get("fee_drag") is None:
            status = "INSUFFICIENT_SOURCE_EVIDENCE"
            detail = {**detail, "missing_fields": ["fee_drag"]}
    elif axis == "walk_forward_window_instability":
        wf = evidence.get("walk_forward_results")
        status, detail = _axis_status(wf if isinstance(wf, dict) else None, ("windows",))
    elif axis == "monte_carlo_sequence_fragility":
        mc = evidence.get("monte_carlo_results")
        status, detail = _axis_status(mc if isinstance(mc, dict) else None, ("num_runs",))
    elif axis == "stress_cost_sensitivity":
        stress = evidence.get("stress_results")
        status, detail = _axis_status(stress if isinstance(stress, dict) else None, ("suite",))
    elif axis == "regime_concentration_single_regime_dependence":
        regime = evidence.get("regime_breakdown")
        reason_codes = evidence.get("reason_codes") or []
        if isinstance(regime, dict) and regime:
            status, detail = "DIAGNOSTIC_MAPPED", {"regime_breakdown": regime}
        elif "METRIC_MISSING:single_regime_profit_contribution" in reason_codes:
            status, detail = (
                "INSUFFICIENT_SOURCE_EVIDENCE",
                {"reason_code": "METRIC_MISSING:single_regime_profit_contribution"},
            )
        else:
            status, detail = "INSUFFICIENT_SOURCE_EVIDENCE", {"regime_breakdown": regime}
    elif axis == "long_short_contribution_imbalance":
        status, detail = _axis_status(
            {
                "long_contribution": evidence.get("long_contribution"),
                "short_contribution": evidence.get("short_contribution"),
            },
            ("long_contribution", "short_contribution"),
        )
    elif axis == "turnover_versus_gross_edge":
        status, detail = _axis_status(
            {
                "turnover": evidence.get("turnover"),
                "gross_return": evidence.get("gross_return"),
            },
            ("turnover", "gross_return"),
        )
    elif axis == "parameter_sensitivity_without_optimization":
        params = evidence.get("parameter_sensitivity_results")
        status, detail = _axis_status(
            params if isinstance(params, dict) else None,
            ("parameter_neighbor_degradation",),
        )
        if status != "DIAGNOSTIC_MAPPED" and isinstance(params, dict) and params:
            status = "DIAGNOSTIC_MAPPED"
            detail = {"parameter_sensitivity_results": params}
    elif axis == "dataset_period_coverage_adequacy":
        wf = (
            evidence.get("walk_forward_results")
            if isinstance(evidence.get("walk_forward_results"), dict)
            else {}
        )
        status, detail = _axis_status(
            {
                "window_count": wf.get("window_count"),
                "data_digest": evidence.get("data_digest"),
            },
            ("window_count", "data_digest"),
        )
    elif axis == "execution_model_assumption_exposure":
        status, detail = _axis_status(
            {
                "input_bindings": evidence.get("input_bindings"),
                "implementation_digest": evidence.get("implementation_digest"),
            },
            ("input_bindings", "implementation_digest"),
        )
    elif axis == "portfolio_contribution_diagnostics_research_only":
        if fleet_summary is None:
            status, detail = "INSUFFICIENT_SOURCE_EVIDENCE", {"fleet_summary": None}
        else:
            status, detail = (
                "DIAGNOSTIC_MAPPED",
                {
                    "fleet_status": fleet_summary.get("fleet_status"),
                    "candidate_verdicts": fleet_summary.get("candidate_verdicts"),
                },
            )
    else:
        status, detail = "INSUFFICIENT_SOURCE_EVIDENCE", {"axis": axis}

    return {
        "axis": axis,
        "candidate": candidate,
        "status": status,
        "detail": detail,
    }


def _collect_diagnostics(
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

    diagnostic_axes = list(config["diagnostic_axes"])
    per_candidate: dict[str, list[dict[str, Any]]] = {}
    missing_inputs: list[dict[str, str]] = []
    mapped_count = 0
    total_count = 0

    for candidate in failed_candidates:
        evidence_path = source_ref / f"candidate_evidence_{candidate}.json"
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

        axis_results: list[dict[str, Any]] = []
        for axis in diagnostic_axes:
            result = _diagnose_axis(axis, candidate, evidence, fleet_summary)
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
    next_recommended_step = (
        NEXT_STEP_RATIFICATION if mapped_ratio >= SUFFICIENCY_MAPPED_RATIO else NEXT_STEP_GAP
    )
    execution_status = (
        "DIAGNOSTICS_EXECUTION_COMPLETE_V0"
        if mapped_ratio >= SUFFICIENCY_MAPPED_RATIO
        else "DIAGNOSTICS_EXECUTION_COMPLETE_WITH_SOURCE_GAPS_V0"
    )

    return {
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "execution_id": f"{OUTPUT_PREFIX}_{_utc_stamp()}",
        "execution_status": execution_status,
        "source_evidence_ref": str(source_ref),
        "source_manifest_verify_rc": source_manifest_rc,
        "source_prs": list(config["source_prs"]),
        "failed_candidates": failed_candidates,
        "failed_candidate_verdicts": failed_verdicts,
        "diagnostic_axes": diagnostic_axes,
        "per_candidate_diagnostics": per_candidate,
        "missing_inputs": missing_inputs,
        "diagnostic_mapped_ratio": round(mapped_ratio, 4),
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
        },
        "no_promotion_claim": True,
        "economic_evaluation_executed": False,
        "backtest_run_executed": False,
        "walk_forward_run_executed": False,
        "monte_carlo_run_executed": False,
        "stress_run_executed": False,
        "runtime_effect": "NONE",
        "trading_effect": "NONE",
        "next_recommended_step": next_recommended_step,
        "go_token_consumed": CONFIRM_GO,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
    }


def _write_summary(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Post No-Pass Robustness Failure Diagnostics Evidence Execution v0",
        "",
        f"- evidence_class_id: `{report['evidence_class_id']}`",
        f"- execution_status: `{report['execution_status']}`",
        f"- source_evidence_ref: `{report['source_evidence_ref']}`",
        f"- source_manifest_verify_rc: `{report['source_manifest_verify_rc']}`",
        f"- diagnostic_mapped_ratio: `{report['diagnostic_mapped_ratio']}`",
        f"- next_recommended_step: `{report['next_recommended_step']}`",
        "",
        "## Failed candidates (unchanged)",
        "",
    ]
    for candidate, verdict in report["failed_candidate_verdicts"].items():
        lines.append(f"- `{candidate}`: `{verdict}`")
    lines.extend(
        [
            "",
            "## Authority boundary",
            "",
            "- economic_evaluation_executed=false",
            "- backtest_run_executed=false",
            "- walk_forward_run_executed=false",
            "- monte_carlo_run_executed=false",
            "- stress_run_executed=false",
            "- runtime_effect=NONE",
            "- trading_effect=NONE",
            "",
            "## Missing inputs",
            "",
        ]
    )
    if report["missing_inputs"]:
        for item in report["missing_inputs"]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_diagnostics_execution_v0(
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

    report = _collect_diagnostics(
        config=config,
        source_ref=source_ref,
        source_manifest_rc=source_manifest_rc,
    )
    report["execution_id"] = output_dir.name
    report["new_evidence_dir"] = str(output_dir)

    (output_dir / "diagnostics_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_summary(report, output_dir / "diagnostics_summary.md")

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
        description="Execute read-only post-no-pass robustness failure diagnostics evidence v0."
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
