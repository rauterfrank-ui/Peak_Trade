#!/usr/bin/env python3
"""Read-only post-PR4904 v4 fleet robustness failure decomposition v0.

Offline-only Class-E decomposition over PR4904 parent evaluation evidence and closeout.
No economic evaluation, no backtest/WF/MC/stress execution, no authority effect.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
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

CONFIRM_GO = "GO_POST_PR4904_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_V0"
SCOPE_ID = "post_pr4904_v4_fleet_robustness_failure_decomposition_v0"
EXECUTION_ID = "POST_PR4904_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_V0"
EVIDENCE_CLASS_ID = EXECUTION_ID
PROCESS_CLASSIFICATION = EXECUTION_ID
SCOPE_CLASSIFICATION = "READ_ONLY_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_AFTER_POST_V4_FLEET_ECONOMIC_VALIDITY_FAIL_V0"
EXECUTION_STATUS = "FAILURE_DECOMPOSITION_EXECUTION_COMPLETE_V0"
NEXT_CANONICAL_STEP = (
    "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_V0"
)
DEFAULT_CONFIG = (
    _REPO_ROOT / "config/research/post_pr4904_v4_fleet_robustness_failure_decomposition_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "post_pr4904_v4_fleet_robustness_failure_decomposition_v0"
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
    if config.get("scope_id") != SCOPE_ID:
        _die("ERR:config scope_id mismatch")
    if config.get("execution_id") != EXECUTION_ID:
        _die("ERR:config execution_id mismatch")
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


def _axis_result(
    *,
    axis: str,
    candidate: str,
    classification: str,
    failure_class: str | None = None,
    robustness_failure_mode: str | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "axis": axis,
        "candidate": candidate,
        "classification": classification,
        "failure_class": failure_class,
        "robustness_failure_mode": robustness_failure_mode,
        "retry_allowed": False,
        "detail": detail or {},
    }


def _wf_negative_oos_ratio(wf: dict[str, Any] | None) -> tuple[float, float] | None:
    if not isinstance(wf, dict):
        return None
    windows = wf.get("windows") or []
    if not windows:
        return None
    negative = sum(1 for w in windows if (w.get("oos_total_return") or 0) < 0)
    zero_trade = sum(1 for w in windows if (w.get("oos_trade_count") or 0) == 0)
    return negative / len(windows), zero_trade / len(windows)


def _decompose_axis(
    axis: str,
    candidate: str,
    evidence: dict[str, Any],
    fleet_summary: dict[str, Any] | None,
    *,
    parent_manifest_rc: int,
    closeout_manifest_rc: int,
) -> dict[str, Any]:
    sparse = evidence.get("sparse_signal_density_metrics") or {}
    wf = (
        evidence.get("walk_forward_results")
        if isinstance(evidence.get("walk_forward_results"), dict)
        else None
    )
    mc = (
        evidence.get("monte_carlo_results")
        if isinstance(evidence.get("monte_carlo_results"), dict)
        else None
    )
    params = evidence.get("parameter_sensitivity_results")
    stress = (
        evidence.get("stress_results") if isinstance(evidence.get("stress_results"), dict) else None
    )

    if axis == "net_edge_after_costs":
        net_return = evidence.get("net_return")
        gross_return = evidence.get("gross_return")
        if net_return is None:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={"net_return": net_return, "gross_return": gross_return},
            )
        confirmed = net_return < 0
        return _axis_result(
            axis=axis,
            candidate=candidate,
            classification="TERMINAL_NEGATIVE" if confirmed else "INCONCLUSIVE_EVIDENCE",
            failure_class="NEGATIVE_NET_EDGE" if confirmed else None,
            robustness_failure_mode="NET_EDGE_AFTER_COSTS_INSUFFICIENT" if confirmed else None,
            detail={"net_return": net_return, "gross_return": gross_return},
        )

    if axis == "profit_factor":
        profit_factor = evidence.get("profit_factor")
        if profit_factor is None:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={"profit_factor": profit_factor},
            )
        confirmed = profit_factor < 1.0
        return _axis_result(
            axis=axis,
            candidate=candidate,
            classification="TERMINAL_NEGATIVE" if confirmed else "INCONCLUSIVE_EVIDENCE",
            failure_class="PROFIT_FACTOR_BELOW_THRESHOLD" if confirmed else None,
            robustness_failure_mode="PROFIT_FACTOR_INSUFFICIENCY" if confirmed else None,
            detail={"profit_factor": profit_factor},
        )

    if axis == "max_drawdown_tail_loss":
        max_drawdown = evidence.get("max_drawdown")
        mc_total = ((mc or {}).get("metric_quantiles") or {}).get("total_return") or {}
        p5 = mc_total.get("p5")
        if max_drawdown is None and p5 is None:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={"max_drawdown": max_drawdown, "mc_total_return_p5": p5},
            )
        tail_risk = (max_drawdown is not None and max_drawdown < -0.01) or (
            p5 is not None and p5 < -0.01
        )
        return _axis_result(
            axis=axis,
            candidate=candidate,
            classification="TERMINAL_NEGATIVE" if tail_risk else "INCONCLUSIVE_EVIDENCE",
            failure_class="TAIL_LOSS_OR_DRAWDOWN_EXCESS" if tail_risk else None,
            robustness_failure_mode="MAX_DRAWDOWN_OR_MC_P5_TAIL" if tail_risk else None,
            detail={"max_drawdown": max_drawdown, "mc_total_return_p5": p5},
        )

    if axis == "walk_forward_stability":
        if wf is None:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={"walk_forward_results": None},
            )
        ratios = _wf_negative_oos_ratio(wf)
        if ratios is None:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={"walk_forward_results": wf},
            )
        negative_ratio, zero_trade_ratio = ratios
        confirmed = negative_ratio >= 0.5 or zero_trade_ratio >= 0.5
        return _axis_result(
            axis=axis,
            candidate=candidate,
            classification="TERMINAL_NEGATIVE" if confirmed else "INCONCLUSIVE_EVIDENCE",
            failure_class="WALK_FORWARD_OOS_INSTABILITY" if confirmed else None,
            robustness_failure_mode="WALK_FORWARD_OOS_INSTABILITY" if confirmed else None,
            detail={
                "window_count": wf.get("window_count"),
                "negative_oos_window_ratio": round(negative_ratio, 4),
                "zero_oos_trade_window_ratio": round(zero_trade_ratio, 4),
            },
        )

    if axis == "monte_carlo_robustness":
        if mc is None:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={"monte_carlo_results": None},
            )
        mc_total = (mc.get("metric_quantiles") or {}).get("total_return") or {}
        p50 = mc_total.get("p50")
        p5 = mc_total.get("p5")
        if p50 is None:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={"monte_carlo_total_return_quantiles": mc_total},
            )
        confirmed = p50 < 0 or (p5 is not None and p5 < 0)
        return _axis_result(
            axis=axis,
            candidate=candidate,
            classification="TERMINAL_NEGATIVE" if confirmed else "INCONCLUSIVE_EVIDENCE",
            failure_class="MONTE_CARLO_NEGATIVE_MEDIAN_RETURN" if confirmed else None,
            robustness_failure_mode="MONTE_CARLO_RETURN_FRAGILITY" if confirmed else None,
            detail={"num_runs": mc.get("num_runs"), "total_return_p50": p50, "total_return_p5": p5},
        )

    if axis == "stress_robustness":
        if stress is None:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={"stress_results": None},
            )
        scenarios = ((stress.get("suite") or {}).get("scenarios")) or []
        if not scenarios:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={"stress_results": stress},
            )
        worst_return = min((s.get("stressed_total_return") or 0) for s in scenarios)
        confirmed = worst_return < -0.05
        return _axis_result(
            axis=axis,
            candidate=candidate,
            classification="TERMINAL_NEGATIVE" if confirmed else "INCONCLUSIVE_EVIDENCE",
            failure_class="STRESS_SCENARIO_TAIL_FAILURE" if confirmed else None,
            robustness_failure_mode="STRESS_TAIL_LOSS" if confirmed else None,
            detail={"scenario_count": len(scenarios), "worst_stressed_total_return": worst_return},
        )

    if axis == "parameter_sensitivity":
        if not isinstance(params, dict) or not params:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={"parameter_sensitivity_results": None},
            )
        if params.get("parameter_robustness_policy_pass") is True:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="REFUTED",
                robustness_failure_mode="PARAMETER_FRAGILITY_REFUTED_BY_POLICY_PASS",
                detail={
                    "parameter_robustness_policy_pass": True,
                    "parameter_robustness_policy_status": params.get(
                        "parameter_robustness_policy_status"
                    ),
                },
            )
        return _axis_result(
            axis=axis,
            candidate=candidate,
            classification="INCONCLUSIVE_EVIDENCE",
            robustness_failure_mode="PARAMETER_FRAGILITY_PRESENT_NOT_OPTIMIZED",
            detail={"parameter_sensitivity_results": params},
        )

    if axis == "trade_count_sample_adequacy":
        trade_count = evidence.get("trade_count")
        if trade_count is None:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={},
            )
        underpowered = trade_count <= 10
        classification = "TERMINAL_NEGATIVE" if underpowered else "INCONCLUSIVE_EVIDENCE"
        return _axis_result(
            axis=axis,
            candidate=candidate,
            classification=classification,
            failure_class="SPARSE_SIGNAL_UNDERPOWERING" if underpowered else None,
            robustness_failure_mode="LOW_TRADE_COUNT" if underpowered else None,
            detail={
                "trade_count": trade_count,
                "instruments_with_nonzero_trades": sparse.get("instruments_with_nonzero_trades"),
                "panel_member_count": sparse.get("panel_member_count"),
            },
        )

    if axis == "long_short_contribution":
        if evidence.get("long_contribution") is None or evidence.get("short_contribution") is None:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={
                    "long_contribution": evidence.get("long_contribution"),
                    "short_contribution": evidence.get("short_contribution"),
                },
            )
        return _axis_result(
            axis=axis,
            candidate=candidate,
            classification="INCONCLUSIVE_EVIDENCE",
            detail={
                "long_contribution": evidence.get("long_contribution"),
                "short_contribution": evidence.get("short_contribution"),
            },
        )

    if axis == "regime_breakdown":
        if wf is None:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={"walk_forward_results": None},
            )
        windows = wf.get("windows") or []
        if not windows:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={"walk_forward_results": wf},
            )
        returns = [w.get("oos_total_return") or 0 for w in windows]
        positive = sum(1 for r in returns if r > 0)
        negative = sum(1 for r in returns if r < 0)
        mixed = positive > 0 and negative > 0
        return _axis_result(
            axis=axis,
            candidate=candidate,
            classification="INCONCLUSIVE_EVIDENCE" if mixed else "TERMINAL_NEGATIVE",
            failure_class="REGIME_MIXED_OOS" if mixed else "REGIME_CONSISTENTLY_NEGATIVE",
            robustness_failure_mode="REGIME_BREAKDOWN_AVAILABLE",
            detail={
                "positive_oos_windows": positive,
                "negative_oos_windows": negative,
                "window_count": len(windows),
            },
        )

    if axis == "fee_slippage_funding_drag":
        fee_drag = evidence.get("fee_drag")
        slippage = evidence.get("slippage_impact")
        funding = evidence.get("funding_drag")
        partial = any(v is not None for v in (fee_drag, slippage, funding))
        if not partial:
            gross = evidence.get("gross_return")
            net = evidence.get("net_return")
            if gross is not None and net is not None and gross > net:
                return _axis_result(
                    axis=axis,
                    candidate=candidate,
                    classification="INCONCLUSIVE_EVIDENCE",
                    detail={"gross_return": gross, "net_return": net, "implicit_cost_drag": True},
                )
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={"fee_drag": fee_drag, "slippage_impact": slippage, "funding_drag": funding},
            )
        return _axis_result(
            axis=axis,
            candidate=candidate,
            classification="INCONCLUSIVE_EVIDENCE",
            detail={
                "fee_drag": fee_drag,
                "slippage_impact": slippage,
                "funding_drag": funding,
                "gross_return": evidence.get("gross_return"),
                "net_return": evidence.get("net_return"),
            },
        )

    if axis == "dominance_concentration":
        member_counts = (
            sparse.get("member_trade_counts")
            if isinstance(sparse.get("member_trade_counts"), dict)
            else {}
        )
        stress_scenarios = (((stress or {}).get("suite") or {}).get("scenarios")) or []
        stress_returns = [s.get("stressed_total_return") or 0 for s in stress_scenarios]
        if stress_returns:
            worst = min(stress_returns)
            best = max(stress_returns)
            dominance = abs(worst) > 0 and abs(worst) > 5 * max(abs(best), 1e-9)
            if dominance:
                return _axis_result(
                    axis=axis,
                    candidate=candidate,
                    classification="TERMINAL_NEGATIVE",
                    failure_class="SINGLE_STRESS_SCENARIO_DOMINANCE",
                    robustness_failure_mode="STRESS_SCENARIO_DOMINANCE",
                    detail={
                        "worst_stressed_total_return": worst,
                        "best_stressed_total_return": best,
                    },
                )
        if member_counts:
            total = sum(member_counts.values())
            max_member = max(member_counts.values()) if member_counts else 0
            concentration_ratio = max_member / total if total else None
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="INCONCLUSIVE_EVIDENCE",
                robustness_failure_mode="INSTRUMENT_ROTATION_METADATA_ONLY",
                detail={
                    "max_member_trade_share": round(concentration_ratio, 4)
                    if concentration_ratio is not None
                    else None,
                },
            )
        return _axis_result(
            axis=axis,
            candidate=candidate,
            classification="MISSING_EVIDENCE",
            detail={"member_trade_counts": None},
        )

    if axis == "evidence_admissibility":
        candidate_manifest_rc = evidence.get("manifest_verify_rc")
        admissible = (
            parent_manifest_rc == 0
            and closeout_manifest_rc == 0
            and candidate_manifest_rc in (0, None)
        )
        return _axis_result(
            axis=axis,
            candidate=candidate,
            classification="INCONCLUSIVE_EVIDENCE" if admissible else "MISSING_EVIDENCE",
            failure_class=None if admissible else "EVIDENCE_ADMISSIBILITY_GAP",
            robustness_failure_mode="PARENT_MANIFEST_VERIFIED" if admissible else None,
            detail={
                "parent_manifest_verify_rc": parent_manifest_rc,
                "closeout_manifest_verify_rc": closeout_manifest_rc,
                "candidate_manifest_verify_rc": candidate_manifest_rc,
            },
        )

    if axis == "fleet_contribution_failure":
        if fleet_summary is None:
            return _axis_result(
                axis=axis,
                candidate=candidate,
                classification="MISSING_EVIDENCE",
                detail={"fleet_summary": None},
            )
        verdict = (fleet_summary.get("candidate_verdicts") or {}).get(candidate)
        confirmed = verdict == "ROBUSTNESS_FAILED"
        return _axis_result(
            axis=axis,
            candidate=candidate,
            classification="TERMINAL_NEGATIVE" if confirmed else "INCONCLUSIVE_EVIDENCE",
            failure_class="ROBUSTNESS_FAILED" if confirmed else None,
            robustness_failure_mode="FLEET_CONTRIBUTION_FAILURE" if confirmed else None,
            detail={
                "fleet_status": fleet_summary.get("fleet_status"),
                "fleet_verdict": fleet_summary.get("fleet_verdict"),
                "candidate_verdict": verdict,
                "economic_validity_offline_gate_pass": fleet_summary.get(
                    "economic_validity_offline_gate_pass"
                ),
            },
        )

    return _axis_result(
        axis=axis,
        candidate=candidate,
        classification="MISSING_EVIDENCE",
        detail={"axis": axis},
    )


def _candidate_summary(
    candidate: str,
    evidence: dict[str, Any],
    axis_results: list[dict[str, Any]],
    *,
    parent_evaluation_ref: str,
) -> dict[str, Any]:
    sparse = evidence.get("sparse_signal_density_metrics") or {}
    mc = (
        evidence.get("monte_carlo_results")
        if isinstance(evidence.get("monte_carlo_results"), dict)
        else {}
    )
    mc_total = (mc.get("metric_quantiles") or {}).get("total_return") or {}
    failure_classes = sorted({r["failure_class"] for r in axis_results if r.get("failure_class")})
    modes = sorted(
        {r["robustness_failure_mode"] for r in axis_results if r.get("robustness_failure_mode")}
    )
    return {
        "strategy_id": candidate,
        "candidate_id": evidence.get("canonical_candidate_identifier")
        or f"{candidate}/post_v4_hypothesis_v0",
        "strategy_version": evidence.get("input_bindings", {}).get("strategy_version")
        or evidence.get("strategy_version")
        or "post_v4_hypothesis_v0",
        "evidence_source_bundle": parent_evaluation_ref,
        "evidence_artifact": f"CANDIDATE_RESULT_{candidate}.json",
        "verdict": evidence.get("verdict") or evidence.get("evidence_status"),
        "candidate_status": evidence.get("verdict") or evidence.get("evidence_status"),
        "failure_classes": failure_classes,
        "robustness_failure_modes": modes,
        "metrics": {
            "trade_count": evidence.get("trade_count"),
            "net_return": evidence.get("net_return"),
            "profit_factor": evidence.get("profit_factor"),
            "max_drawdown": evidence.get("max_drawdown"),
            "sharpe": evidence.get("sharpe"),
        },
        "data_sufficiency": {
            "trade_count": evidence.get("trade_count"),
            "instruments_with_nonzero_trades": sparse.get("instruments_with_nonzero_trades"),
            "panel_member_count": sparse.get("panel_member_count"),
        },
        "robustness_availability": {
            "walk_forward_available": evidence.get("walk_forward_results") is not None,
            "monte_carlo_available": evidence.get("monte_carlo_results") is not None,
            "stress_available": evidence.get("stress_results") is not None,
            "monte_carlo_total_return_p50": mc_total.get("p50"),
            "monte_carlo_total_return_p5": mc_total.get("p5"),
        },
        "retry_allowed": False,
        "terminal_negative": (evidence.get("verdict") or evidence.get("evidence_status"))
        == "ROBUSTNESS_FAILED",
        "per_axis": axis_results,
    }


def _collect_decomposition(
    *,
    config: dict[str, Any],
    parent_evaluation_ref: Path,
    parent_closeout_ref: Path,
    parent_manifest_rc: int,
    closeout_manifest_rc: int,
    git_snapshot: dict[str, str],
) -> dict[str, Any]:
    fleet_summary = _load_json(parent_evaluation_ref / "FLEET_ECONOMIC_SUMMARY.json")
    failed_candidates = list(config["failed_candidates"])
    failed_verdicts = dict(fleet_summary["candidate_verdicts"])
    for candidate in failed_candidates:
        if failed_verdicts.get(candidate) != config["failed_candidate_verdict"]:
            _die(f"ERR:immutable verdict drift for {candidate}")
    if fleet_summary.get("fleet_verdict") != config["fleet_verdict"]:
        _die("ERR:fleet_verdict drift")
    if fleet_summary.get("economic_validity_offline_gate_pass") is not False:
        _die("ERR:economic_validity_offline_gate_pass must remain false")

    decomposition_axes = list(config["decomposition_axes"])
    per_candidate: dict[str, dict[str, Any]] = {}
    per_candidate_axes: dict[str, list[dict[str, Any]]] = {}
    missing_inputs: list[dict[str, str]] = []
    mapped_count = 0
    total_count = 0

    for candidate in failed_candidates:
        evidence_path = parent_evaluation_ref / f"CANDIDATE_RESULT_{candidate}.json"
        if not evidence_path.is_file():
            missing_inputs.append(
                {
                    "candidate": candidate,
                    "artifact": evidence_path.name,
                    "status": "DECOMPOSITION_INPUT_NOT_FOUND",
                }
            )
            evidence: dict[str, Any] = {}
        else:
            evidence = _load_json(evidence_path)

        axis_results: list[dict[str, Any]] = []
        for axis in decomposition_axes:
            result = _decompose_axis(
                axis,
                candidate,
                evidence,
                fleet_summary,
                parent_manifest_rc=parent_manifest_rc,
                closeout_manifest_rc=closeout_manifest_rc,
            )
            axis_results.append(result)
            total_count += 1
            if result["classification"] in {
                "TERMINAL_NEGATIVE",
                "INCONCLUSIVE_EVIDENCE",
                "REFUTED",
            }:
                mapped_count += 1
            elif result["classification"] == "MISSING_EVIDENCE":
                missing_inputs.append(
                    {
                        "candidate": candidate,
                        "axis": axis,
                        "status": result["classification"],
                    }
                )
        per_candidate_axes[candidate] = axis_results
        per_candidate[candidate] = _candidate_summary(
            candidate,
            evidence,
            axis_results,
            parent_evaluation_ref=str(parent_evaluation_ref),
        )

    mapped_ratio = mapped_count / total_count if total_count else 0.0
    execution_status = (
        EXECUTION_STATUS
        if mapped_ratio >= SUFFICIENCY_MAPPED_RATIO
        else "FAILURE_DECOMPOSITION_EXECUTION_COMPLETE_WITH_SOURCE_GAPS_V0"
    )

    aggregate_status = "FLEET_ECONOMIC_VALIDITY_FAIL"
    aggregate_axis_summary: dict[str, str] = {}
    for axis in decomposition_axes:
        classifications = [
            next(r["classification"] for r in per_candidate_axes[c] if r["axis"] == axis)
            for c in failed_candidates
        ]
        counter = Counter(classifications)
        if counter.get("TERMINAL_NEGATIVE", 0) == len(failed_candidates):
            aggregate_axis_summary[axis] = "TERMINAL_NEGATIVE"
        elif counter.get("TERMINAL_NEGATIVE", 0) > 0:
            aggregate_axis_summary[axis] = "MIXED_TERMINAL_NEGATIVE"
        elif counter.get("MISSING_EVIDENCE", 0) == len(failed_candidates):
            aggregate_axis_summary[axis] = "MISSING_EVIDENCE"
        else:
            aggregate_axis_summary[axis] = "INCONCLUSIVE_OR_REFUTED"

    return {
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "execution_id": EXECUTION_ID,
        "scope_id": SCOPE_ID,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "execution_status": execution_status,
        "aggregate_status": aggregate_status,
        "aggregate_result": aggregate_status,
        "source_evidence_refs": [str(parent_evaluation_ref), str(parent_closeout_ref)],
        "source_manifest_verify_rc": {
            "parent_evaluation": parent_manifest_rc,
            "parent_closeout": closeout_manifest_rc,
        },
        "source_prs": list(config["source_prs"]),
        "failed_candidates": failed_candidates,
        "failed_candidate_verdicts": failed_verdicts,
        "decomposition_axes": decomposition_axes,
        "aggregate_axis_summary": aggregate_axis_summary,
        "per_candidate_decomposition": per_candidate,
        "per_candidate_axis_results": per_candidate_axes,
        "missing_inputs": missing_inputs,
        "decomposition_mapped_ratio": round(mapped_ratio, 4),
        "fleet_verdict": fleet_summary.get("fleet_verdict"),
        "fleet_status": fleet_summary.get("fleet_status"),
        "economic_validity_offline_gate_pass": fleet_summary.get(
            "economic_validity_offline_gate_pass"
        ),
        "strategy_version": config.get("strategy_version"),
        "immutable_binding_retry_allowed": False,
        "same_binding_retry_allowed": False,
        "new_candidates_ratified": False,
        "git_snapshot": git_snapshot,
        "authority_boundary": {
            "authority_effect": "NONE",
            "runtime_effect": "NONE",
            "trading_effect": "NONE",
            "runtime_authority": "NONE",
            "promotion_authority": False,
            "promotion_eligible": False,
            "runtime_rewire_admissible": False,
            "same_binding_retry_allowed": False,
            "parameter_rescue_allowed": False,
            "threshold_lowering_allowed": False,
            "economic_evaluation_authorized": False,
            "live_authorized": False,
            "shadow_authorized": False,
            "paper_authorized": False,
            "testnet_authorized": False,
            "orders_allowed": False,
            "scheduler_runtime_allowed": False,
            "runtime_authority_created": False,
        },
        "no_promotion_claim": True,
        "economic_evaluation_executed": False,
        "backtest_executed": False,
        "walk_forward_run_executed": False,
        "monte_carlo_run_executed": False,
        "stress_run_executed": False,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "go_token_consumed": CONFIRM_GO,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "terminal_negative_evidence_unchanged": True,
        "historical_negative_evidence_mutated": False,
    }


def _write_candidate_matrix(path: Path, report: dict[str, Any]) -> None:
    rows: list[dict[str, str]] = []
    for candidate, summary in report["per_candidate_decomposition"].items():
        for axis_result in summary["per_axis"]:
            detail = axis_result.get("detail") or {}
            value_summary = json.dumps(detail, sort_keys=True)
            rows.append(
                {
                    "candidate": candidate,
                    "dimension": axis_result["axis"],
                    "classification": axis_result["classification"],
                    "failure_class": axis_result.get("failure_class") or "",
                    "robustness_failure_mode": axis_result.get("robustness_failure_mode") or "",
                    "value_summary": value_summary,
                }
            )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "candidate",
                "dimension",
                "classification",
                "failure_class",
                "robustness_failure_mode",
                "value_summary",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_aggregate_matrix(path: Path, report: dict[str, Any]) -> None:
    rows: list[dict[str, str]] = []
    for axis, fleet_classification in report["aggregate_axis_summary"].items():
        terminal_count = sum(
            1
            for candidate in report["failed_candidates"]
            for result in report["per_candidate_axis_results"][candidate]
            if result["axis"] == axis and result["classification"] == "TERMINAL_NEGATIVE"
        )
        rows.append(
            {
                "dimension": axis,
                "fleet_classification": fleet_classification,
                "candidate_count_terminal_negative": str(terminal_count),
                "notes": f"{terminal_count}/{len(report['failed_candidates'])} candidates terminal negative",
            }
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dimension",
                "fleet_classification",
                "candidate_count_terminal_negative",
                "notes",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_summary_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Failure Decomposition Summary",
        "",
        f"VERDICT={report['execution_status']}",
        f"PROCESS_CLASSIFICATION={report['process_classification']}",
        f"SCOPE_CLASSIFICATION={report['scope_classification']}",
        f"AGGREGATE_STATUS={report['aggregate_status']}",
        f"FLEET_VERDICT={report['fleet_verdict']}",
        f"ECONOMIC_VALIDITY_OFFLINE_GATE_PASS={report['economic_validity_offline_gate_pass']}",
        f"STRATEGY_VERSION={report['strategy_version']}",
        f"DECOMPOSITION_MAPPED_RATIO={report['decomposition_mapped_ratio']}",
        "",
        "## Candidate verdicts (immutable)",
        "",
    ]
    for candidate, summary in report["per_candidate_decomposition"].items():
        lines.append(
            f"- `{candidate}`: `{summary['candidate_status']}` "
            f"(failure_classes={summary['failure_classes']})"
        )
    lines.extend(["", "## Aggregate axis summary", ""])
    for axis, classification in report["aggregate_axis_summary"].items():
        lines.append(f"- `{axis}`: `{classification}`")
    lines.extend(
        [
            "",
            "## Authority boundary",
            "",
            "- RUNTIME_AUTHORITY_CREATED=false",
            "- LIVE_AUTHORIZED=false",
            "- SHADOW_AUTHORIZED=false",
            "- PAPER_AUTHORIZED=false",
            "- TESTNET_AUTHORIZED=false",
            "- ORDERS_ALLOWED=false",
            "",
            f"NEXT_STEP={report['next_canonical_step']}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_input_pointers(
    path: Path,
    *,
    parent_evaluation_ref: Path,
    parent_closeout_ref: Path,
    parent_manifest_rc: int,
    closeout_manifest_rc: int,
) -> None:
    payload = {
        "parent_evaluation_bundle": str(parent_evaluation_ref),
        "parent_closeout_bundle": str(parent_closeout_ref),
        "parent_evaluation_manifest_verify_rc": parent_manifest_rc,
        "parent_closeout_manifest_verify_rc": closeout_manifest_rc,
        "artifacts": [
            "FLEET_ECONOMIC_SUMMARY.json",
            "CANDIDATE_RESULT_trend_following.json",
            "CANDIDATE_RESULT_bollinger_bands.json",
            "CANDIDATE_RESULT_momentum_1h.json",
            "FAILURE_CLASSIFICATION.md",
            "EXECUTION_REPORT.md",
        ],
        "closeout_artifacts": [
            "CLOSEOUT_SUMMARY.md",
            "closeout_capture.txt",
            "MANIFEST.sha256",
        ],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_reports(
    output_dir: Path,
    report: dict[str, Any],
    *,
    parent_evaluation_ref: Path,
    parent_closeout_ref: Path,
    parent_manifest_rc: int,
    closeout_manifest_rc: int,
) -> None:
    _write_summary_md(output_dir / "FAILURE_DECOMPOSITION_SUMMARY.md", report)
    (output_dir / "FAILURE_DECOMPOSITION.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_candidate_matrix(output_dir / "CANDIDATE_FAILURE_MATRIX.tsv", report)
    _write_aggregate_matrix(output_dir / "AGGREGATE_FAILURE_MATRIX.tsv", report)
    _write_input_pointers(
        output_dir / "INPUT_POINTERS.json",
        parent_evaluation_ref=parent_evaluation_ref,
        parent_closeout_ref=parent_closeout_ref,
        parent_manifest_rc=parent_manifest_rc,
        closeout_manifest_rc=closeout_manifest_rc,
    )


def run_failure_decomposition_v0(
    *,
    go_token: str,
    parent_evaluation_bundle: Path,
    parent_closeout_bundle: Path,
    durable_archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    config_path: Path = DEFAULT_CONFIG,
    runtime_authority: str = "none",
    no_economic_evaluation: bool = True,
    no_backtest: bool = True,
    no_runtime: bool = True,
    no_promotion: bool = True,
    no_shadow: bool = True,
    no_paper: bool = True,
    no_testnet: bool = True,
    no_live: bool = True,
) -> dict[str, Any]:
    if go_token != CONFIRM_GO:
        _die("ERR:invalid go token")
    if runtime_authority.lower() != "none":
        _die("ERR:runtime_authority must be none")
    if not all(
        (
            no_economic_evaluation,
            no_backtest,
            no_runtime,
            no_promotion,
            no_shadow,
            no_paper,
            no_testnet,
            no_live,
        )
    ):
        _die("ERR:all safety boundary flags must be true")

    if not config_path.is_file():
        _die(f"ERR:missing config: {config_path}")

    config = _load_json(config_path)
    _require_config_gates(config)

    if not parent_evaluation_bundle.is_dir():
        _die(f"ERR:missing parent evaluation bundle: {parent_evaluation_bundle}")
    if not parent_closeout_bundle.is_dir():
        _die(f"ERR:missing parent closeout bundle: {parent_closeout_bundle}")

    output_dir = durable_archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    parent_manifest_rc = _verify_source_manifest(
        parent_evaluation_bundle,
        output_dir / "parent_evaluation_manifest_verify.log",
    )
    closeout_manifest_rc = _verify_source_manifest(
        parent_closeout_bundle,
        output_dir / "parent_closeout_manifest_verify.log",
    )
    if parent_manifest_rc != 0:
        _die(f"ERR:parent evaluation manifest invalid: {parent_evaluation_bundle}")
    if closeout_manifest_rc != 0:
        _die(f"ERR:parent closeout manifest invalid: {parent_closeout_bundle}")

    git_snapshot = _git_snapshot()
    report = _collect_decomposition(
        config=config,
        parent_evaluation_ref=parent_evaluation_bundle,
        parent_closeout_ref=parent_closeout_bundle,
        parent_manifest_rc=parent_manifest_rc,
        closeout_manifest_rc=closeout_manifest_rc,
        git_snapshot=git_snapshot,
    )
    report["durable_evidence_path"] = str(output_dir)
    report["manifest_verify_rc"] = 0

    _write_reports(
        output_dir,
        report,
        parent_evaluation_ref=parent_evaluation_bundle,
        parent_closeout_ref=parent_closeout_bundle,
        parent_manifest_rc=parent_manifest_rc,
        closeout_manifest_rc=closeout_manifest_rc,
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
        description="Execute read-only post-PR4904 v4 fleet robustness failure decomposition v0."
    )
    parser.add_argument("--go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--parent-evaluation-bundle", type=Path, required=True)
    parser.add_argument("--parent-closeout-bundle", type=Path, required=True)
    parser.add_argument("--durable-archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--runtime-authority", default="none")
    parser.add_argument("--no-economic-evaluation", action="store_true", default=True)
    parser.add_argument("--no-backtest", action="store_true", default=True)
    parser.add_argument("--no-runtime", action="store_true", default=True)
    parser.add_argument("--no-promotion", action="store_true", default=True)
    parser.add_argument("--no-shadow", action="store_true", default=True)
    parser.add_argument("--no-paper", action="store_true", default=True)
    parser.add_argument("--no-testnet", action="store_true", default=True)
    parser.add_argument("--no-live", action="store_true", default=True)
    args = parser.parse_args()

    report = run_failure_decomposition_v0(
        go_token=args.go_token,
        parent_evaluation_bundle=args.parent_evaluation_bundle,
        parent_closeout_bundle=args.parent_closeout_bundle,
        durable_archive_root=args.durable_archive_root,
        config_path=args.config,
        runtime_authority=args.runtime_authority,
        no_economic_evaluation=args.no_economic_evaluation,
        no_backtest=args.no_backtest,
        no_runtime=args.no_runtime,
        no_promotion=args.no_promotion,
        no_shadow=args.no_shadow,
        no_paper=args.no_paper,
        no_testnet=args.no_testnet,
        no_live=args.no_live,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    for key in (
        "execution_status",
        "durable_evidence_path",
        "manifest_verify_rc",
        "aggregate_status",
    ):
        print(f"{key.upper()}={report[key]}")


if __name__ == "__main__":
    main()
