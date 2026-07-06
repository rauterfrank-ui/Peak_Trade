#!/usr/bin/env python3
"""Read-only post-PR4897 v4 fleet robustness failure decomposition evidence execution v0.

Offline-only Class-E decomposition over PR4895/4897 source evidence and scope definition.
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

CONFIRM_GO = "GO_POST_PR4897_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_V0"
SCOPE_ID = (
    "POST_PR4897_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_CLASS_SCOPE_DEFINITION_V0"
)
EXECUTION_ID = "POST_PR4897_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_V0"
EVIDENCE_CLASS_ID = EXECUTION_ID
PROCESS_CLASSIFICATION = EXECUTION_ID
SCOPE_CLASSIFICATION = (
    "READ_ONLY_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_AFTER_FLEET_ECONOMIC_VALIDITY_FAIL_V0"
)
EXECUTION_STATUS = "FAILURE_DECOMPOSITION_EXECUTION_COMPLETE_V0"
NEXT_CANONICAL_STEP = (
    "NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_REQUIRES_OPERATOR_RATIFICATION_"
    "AFTER_POST_PR4897_V4_FAILURE_DECOMPOSITION_V0"
)
NEXT_ADMISSIBLE_GO = (
    "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_V0"
)
DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/post_pr4897_v4_fleet_robustness_failure_decomposition_evidence_execution_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "post_pr4897_v4_fleet_robustness_failure_decomposition_evidence_execution_v0"
SUFFICIENCY_MAPPED_RATIO = 2 / 3
V3_REFERENCE_METRICS = {
    "trend_following": {"trade_count": 53.0, "net_return": -0.0008990311367879258},
    "bollinger_bands": {"trade_count": 4.0, "net_return": -0.01985049937499989},
    "momentum_1h": {"trade_count": 94.0, "net_return": -0.08517843749568965},
}


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

    if axis == "signal_edge":
        net_return = evidence.get("net_return")
        profit_factor = evidence.get("profit_factor")
        if net_return is None or profit_factor is None:
            return {
                "axis": axis,
                "candidate": candidate,
                "classification": "MISSING_EVIDENCE",
                "failure_class": None,
                "robustness_failure_mode": None,
                "retry_allowed": False,
                "detail": {"net_return": net_return, "profit_factor": profit_factor},
            }
        confirmed = net_return < 0 and profit_factor < 1.0
        return {
            "axis": axis,
            "candidate": candidate,
            "classification": "TERMINAL_NEGATIVE" if confirmed else "INCONCLUSIVE_EVIDENCE",
            "failure_class": "NEGATIVE_NET_EDGE" if confirmed else None,
            "robustness_failure_mode": "SIGNAL_EDGE_INSUFFICIENCY" if confirmed else None,
            "retry_allowed": False,
            "detail": {
                "net_return": net_return,
                "gross_return": evidence.get("gross_return"),
                "profit_factor": profit_factor,
                "sharpe": evidence.get("sharpe"),
            },
        }

    if axis == "turnover_cost_drag":
        if evidence.get("turnover") is None:
            return {
                "axis": axis,
                "candidate": candidate,
                "classification": "MISSING_EVIDENCE",
                "failure_class": None,
                "robustness_failure_mode": None,
                "retry_allowed": False,
                "detail": {"turnover": None, "gross_return": evidence.get("gross_return")},
            }
        return {
            "axis": axis,
            "candidate": candidate,
            "classification": "INCONCLUSIVE_EVIDENCE",
            "failure_class": None,
            "robustness_failure_mode": None,
            "retry_allowed": False,
            "detail": {
                "turnover": evidence.get("turnover"),
                "gross_return": evidence.get("gross_return"),
            },
        }

    if axis == "regime_instability":
        if wf is None:
            return {
                "axis": axis,
                "candidate": candidate,
                "classification": "MISSING_EVIDENCE",
                "failure_class": None,
                "robustness_failure_mode": None,
                "retry_allowed": False,
                "detail": {"walk_forward_results": None},
            }
        ratios = _wf_negative_oos_ratio(wf)
        if ratios is None:
            return {
                "axis": axis,
                "candidate": candidate,
                "classification": "MISSING_EVIDENCE",
                "failure_class": None,
                "robustness_failure_mode": None,
                "retry_allowed": False,
                "detail": {"walk_forward_results": wf},
            }
        negative_ratio, zero_trade_ratio = ratios
        confirmed = negative_ratio >= 0.5 or zero_trade_ratio >= 0.5
        return {
            "axis": axis,
            "candidate": candidate,
            "classification": "TERMINAL_NEGATIVE" if confirmed else "INCONCLUSIVE_EVIDENCE",
            "failure_class": "WALK_FORWARD_OOS_INSTABILITY" if confirmed else None,
            "robustness_failure_mode": "REGIME_OOS_INSTABILITY" if confirmed else None,
            "retry_allowed": False,
            "detail": {
                "window_count": wf.get("window_count"),
                "negative_oos_window_ratio": round(negative_ratio, 4),
                "zero_oos_trade_window_ratio": round(zero_trade_ratio, 4),
                "windows_available": True,
            },
        }

    if axis == "monte_carlo_negative_return_fragility":
        if mc is None:
            return {
                "axis": axis,
                "candidate": candidate,
                "classification": "MISSING_EVIDENCE",
                "failure_class": None,
                "robustness_failure_mode": None,
                "retry_allowed": False,
                "detail": {"monte_carlo_results": None},
            }
        mc_total = (mc.get("metric_quantiles") or {}).get("total_return") or {}
        p50 = mc_total.get("p50")
        p5 = mc_total.get("p5")
        if p50 is None:
            return {
                "axis": axis,
                "candidate": candidate,
                "classification": "MISSING_EVIDENCE",
                "failure_class": None,
                "robustness_failure_mode": None,
                "retry_allowed": False,
                "detail": {"monte_carlo_total_return_quantiles": mc_total},
            }
        confirmed = p50 < 0 or (p5 is not None and p5 < 0)
        return {
            "axis": axis,
            "candidate": candidate,
            "classification": "TERMINAL_NEGATIVE" if confirmed else "INCONCLUSIVE_EVIDENCE",
            "failure_class": "MONTE_CARLO_NEGATIVE_MEDIAN_RETURN" if confirmed else None,
            "robustness_failure_mode": "MONTE_CARLO_RETURN_FRAGILITY" if confirmed else None,
            "retry_allowed": False,
            "detail": {
                "num_runs": mc.get("num_runs"),
                "total_return_p50": p50,
                "total_return_p5": p5,
            },
        }

    if axis == "parameter_fragility":
        if not isinstance(params, dict) or not params:
            return {
                "axis": axis,
                "candidate": candidate,
                "classification": "MISSING_EVIDENCE",
                "failure_class": None,
                "robustness_failure_mode": None,
                "retry_allowed": False,
                "detail": {"parameter_sensitivity_results": None},
            }
        if params.get("parameter_robustness_policy_pass") is True:
            return {
                "axis": axis,
                "candidate": candidate,
                "classification": "REFUTED",
                "failure_class": None,
                "robustness_failure_mode": "PARAMETER_FRAGILITY_REFUTED_BY_POLICY_PASS",
                "retry_allowed": False,
                "detail": {
                    "parameter_robustness_policy_pass": True,
                    "parameter_robustness_policy_status": params.get(
                        "parameter_robustness_policy_status"
                    ),
                },
            }
        return {
            "axis": axis,
            "candidate": candidate,
            "classification": "INCONCLUSIVE_EVIDENCE",
            "failure_class": None,
            "robustness_failure_mode": "PARAMETER_FRAGILITY_PRESENT_NOT_OPTIMIZED",
            "retry_allowed": False,
            "detail": {"parameter_sensitivity_results": params},
        }

    if axis == "sparse_signal_underpowering":
        trade_count = evidence.get("trade_count")
        if trade_count is None:
            return {
                "axis": axis,
                "candidate": candidate,
                "classification": "MISSING_EVIDENCE",
                "failure_class": None,
                "robustness_failure_mode": None,
                "retry_allowed": False,
                "detail": {},
            }
        instruments_nonzero = sparse.get("instruments_with_nonzero_trades")
        panel_count = sparse.get("panel_member_count")
        underpowered = trade_count <= 10 or (
            isinstance(instruments_nonzero, int)
            and isinstance(panel_count, int)
            and instruments_nonzero < panel_count * 0.95
        )
        classification = "TERMINAL_NEGATIVE" if underpowered else "INCONCLUSIVE_EVIDENCE"
        return {
            "axis": axis,
            "candidate": candidate,
            "classification": classification,
            "failure_class": "SPARSE_SIGNAL_UNDERPOWERING" if underpowered else None,
            "robustness_failure_mode": "LOW_TRADE_COUNT_OR_PANEL_SPARSITY"
            if underpowered
            else None,
            "retry_allowed": False,
            "detail": {
                "trade_count": trade_count,
                "instruments_with_nonzero_trades": instruments_nonzero,
                "panel_member_count": panel_count,
                "max_trade_count": sparse.get("max_trade_count"),
                "panel_zero_trade_refuted": instruments_nonzero != 0
                if instruments_nonzero is not None
                else None,
            },
        }

    if axis == "long_short_asymmetry":
        if evidence.get("long_contribution") is None or evidence.get("short_contribution") is None:
            return {
                "axis": axis,
                "candidate": candidate,
                "classification": "MISSING_EVIDENCE",
                "failure_class": None,
                "robustness_failure_mode": None,
                "retry_allowed": False,
                "detail": {
                    "long_contribution": evidence.get("long_contribution"),
                    "short_contribution": evidence.get("short_contribution"),
                },
            }
        return {
            "axis": axis,
            "candidate": candidate,
            "classification": "INCONCLUSIVE_EVIDENCE",
            "failure_class": None,
            "robustness_failure_mode": None,
            "retry_allowed": False,
            "detail": {
                "long_contribution": evidence.get("long_contribution"),
                "short_contribution": evidence.get("short_contribution"),
            },
        }

    if axis == "instrument_concentration":
        member_counts = (
            sparse.get("member_trade_counts")
            if isinstance(sparse.get("member_trade_counts"), dict)
            else {}
        )
        if not member_counts:
            return {
                "axis": axis,
                "candidate": candidate,
                "classification": "MISSING_EVIDENCE",
                "failure_class": None,
                "robustness_failure_mode": None,
                "retry_allowed": False,
                "detail": {"member_trade_counts": None},
            }
        total = sum(member_counts.values())
        max_member = max(member_counts.values()) if member_counts else 0
        concentration_ratio = max_member / total if total else None
        return {
            "axis": axis,
            "candidate": candidate,
            "classification": "INCONCLUSIVE_EVIDENCE",
            "failure_class": None,
            "robustness_failure_mode": "INSTRUMENT_ROTATION_METADATA_ONLY",
            "retry_allowed": False,
            "detail": {
                "max_member_trade_share": round(concentration_ratio, 4)
                if concentration_ratio is not None
                else None,
                "evaluation_instrument_id": sparse.get("evaluation_instrument_id"),
                "rotation_policy": sparse.get("rotation_policy"),
            },
        }

    if axis == "funding_slippage_sensitivity":
        fee_drag = evidence.get("fee_drag")
        slippage = evidence.get("slippage_impact")
        funding = evidence.get("funding_drag")
        partial = any(v is not None for v in (fee_drag, slippage, funding))
        if not partial:
            return {
                "axis": axis,
                "candidate": candidate,
                "classification": "MISSING_EVIDENCE",
                "failure_class": None,
                "robustness_failure_mode": None,
                "retry_allowed": False,
                "detail": {
                    "fee_drag": fee_drag,
                    "slippage_impact": slippage,
                    "funding_drag": funding,
                },
            }
        decomposition_available = fee_drag is not None and slippage is not None
        return {
            "axis": axis,
            "candidate": candidate,
            "classification": "INCONCLUSIVE_EVIDENCE",
            "failure_class": None,
            "robustness_failure_mode": "PARTIAL_COST_FIELDS_ONLY"
            if not decomposition_available
            else None,
            "retry_allowed": False,
            "detail": {
                "fee_drag": fee_drag,
                "slippage_impact": slippage,
                "funding_drag": funding,
                "gross_return": evidence.get("gross_return"),
                "net_return": evidence.get("net_return"),
            },
        }

    if axis == "portfolio_contribution_failure":
        if fleet_summary is None:
            return {
                "axis": axis,
                "candidate": candidate,
                "classification": "MISSING_EVIDENCE",
                "failure_class": None,
                "robustness_failure_mode": None,
                "retry_allowed": False,
                "detail": {"fleet_summary": None},
            }
        verdict = (fleet_summary.get("candidate_verdicts") or {}).get(candidate)
        confirmed = verdict == "ROBUSTNESS_FAILED"
        return {
            "axis": axis,
            "candidate": candidate,
            "classification": "TERMINAL_NEGATIVE" if confirmed else "INCONCLUSIVE_EVIDENCE",
            "failure_class": "ROBUSTNESS_FAILED" if confirmed else None,
            "robustness_failure_mode": "PORTFOLIO_CONTRIBUTION_FAILURE" if confirmed else None,
            "retry_allowed": False,
            "detail": {
                "fleet_status": fleet_summary.get("fleet_status"),
                "fleet_verdict": fleet_summary.get("fleet_verdict"),
                "candidate_verdict": verdict,
                "economic_validity_offline_gate_pass": fleet_summary.get(
                    "economic_validity_offline_gate_pass"
                ),
            },
        }

    if axis == "binding_delta_rescue_hypothesis":
        ref = V3_REFERENCE_METRICS.get(candidate, {})
        trade_count = evidence.get("trade_count")
        net_return = evidence.get("net_return")
        if trade_count is None or net_return is None:
            return {
                "axis": axis,
                "candidate": candidate,
                "classification": "MISSING_EVIDENCE",
                "failure_class": None,
                "robustness_failure_mode": None,
                "retry_allowed": False,
                "detail": {"v3_reference": ref},
            }
        identical = (
            trade_count == ref.get("trade_count")
            and abs(net_return - ref.get("net_return", 0)) < 1e-9
        )
        return {
            "axis": axis,
            "candidate": candidate,
            "classification": "REFUTED" if identical else "INCONCLUSIVE_EVIDENCE",
            "failure_class": None,
            "robustness_failure_mode": "V4_PANEL_BINDING_DELTA_DID_NOT_RESCUE_METRICS"
            if identical
            else None,
            "retry_allowed": False,
            "detail": {
                "v4_trade_count": trade_count,
                "v4_net_return": net_return,
                "v3_reference_trade_count": ref.get("trade_count"),
                "v3_reference_net_return": ref.get("net_return"),
                "metrics_identical_to_v3": identical,
            },
        }

    return {
        "axis": axis,
        "candidate": candidate,
        "classification": "MISSING_EVIDENCE",
        "failure_class": None,
        "robustness_failure_mode": None,
        "retry_allowed": False,
        "detail": {"axis": axis},
    }


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
        "candidate_id": evidence.get("canonical_candidate_identifier") or f"{candidate}/v4",
        "strategy_version": evidence.get("input_bindings", {}).get("strategy_version") or "v4",
        "evidence_source_bundle": parent_evaluation_ref,
        "evidence_artifact": f"CANDIDATE_RESULT_{candidate}.json",
        "verdict": evidence.get("verdict") or evidence.get("evidence_status"),
        "failure_classes": failure_classes,
        "robustness_failure_modes": modes,
        "data_sufficiency": {
            "trade_count": evidence.get("trade_count"),
            "instruments_with_nonzero_trades": sparse.get("instruments_with_nonzero_trades"),
            "panel_member_count": sparse.get("panel_member_count"),
        },
        "cost_drag": {
            "fee_drag": evidence.get("fee_drag"),
            "slippage_impact": evidence.get("slippage_impact"),
            "funding_drag": evidence.get("funding_drag"),
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
    scope_definition_ref: Path,
    parent_manifest_rc: int,
    scope_manifest_rc: int,
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

    fleet_eval_path = parent_evaluation_ref / "fleet_evaluation_summary_v0.json"
    fleet_eval_summary = _load_json(fleet_eval_path) if fleet_eval_path.is_file() else None
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
            result = _decompose_axis(axis, candidate, evidence, fleet_summary)
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

    input_evidence_index = [
        {
            "bundle_id": "parent_evaluation_pr4895",
            "bundle_path": str(parent_evaluation_ref),
            "role": "PR4895 v4 fleet offline economic evaluation execution",
            "manifest_verify_rc": parent_manifest_rc,
            "artifacts": [
                "FLEET_ECONOMIC_SUMMARY.json",
                "fleet_evaluation_summary_v0.json",
                "CANDIDATE_RESULT_trend_following.json",
                "CANDIDATE_RESULT_bollinger_bands.json",
                "CANDIDATE_RESULT_momentum_1h.json",
            ],
        },
        {
            "bundle_id": "scope_definition_pr4898",
            "bundle_path": str(scope_definition_ref),
            "role": "PR4898 v4 failure decomposition scope definition",
            "manifest_verify_rc": scope_manifest_rc,
            "artifacts": [
                "scope_definition_v0.json",
                "SCOPE_DEFINITION.md",
                "FAILURE_DECOMPOSITION_SUMMARY.md",
                "go_token_consumption.json",
            ],
        },
    ]

    return {
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "execution_id": EXECUTION_ID,
        "scope_id": SCOPE_ID,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "execution_status": execution_status,
        "source_evidence_refs": [str(parent_evaluation_ref), str(scope_definition_ref)],
        "source_manifest_verify_rc": {
            "parent_evaluation": parent_manifest_rc,
            "scope_definition": scope_manifest_rc,
        },
        "source_prs": list(config["source_prs"]),
        "failed_candidates": failed_candidates,
        "failed_candidate_verdicts": failed_verdicts,
        "decomposition_axes": decomposition_axes,
        "per_candidate_decomposition": per_candidate,
        "per_candidate_axis_results": per_candidate_axes,
        "input_evidence_index": input_evidence_index,
        "missing_inputs": missing_inputs,
        "decomposition_mapped_ratio": round(mapped_ratio, 4),
        "fleet_verdict": fleet_summary.get("fleet_verdict"),
        "fleet_status": fleet_summary.get("fleet_status"),
        "economic_validity_offline_gate_pass": fleet_summary.get(
            "economic_validity_offline_gate_pass"
        ),
        "panel_zero_trade_refuted": config.get("panel_zero_trade_refuted"),
        "strategy_version": config.get("strategy_version"),
        "v4_binding_class": config.get("v4_binding_class"),
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
        },
        "no_promotion_claim": True,
        "economic_evaluation_executed": False,
        "backtest_executed": False,
        "walk_forward_run_executed": False,
        "monte_carlo_run_executed": False,
        "stress_run_executed": False,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "next_admissible_scope_go_token": NEXT_ADMISSIBLE_GO,
        "go_token_consumed": CONFIRM_GO,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "terminal_negative_evidence_unchanged": True,
        "historical_negative_evidence_mutated": False,
        "fleet_eval_summary_present": fleet_eval_summary is not None,
    }


def _write_reports(output_dir: Path, report: dict[str, Any]) -> None:
    git = report["git_snapshot"]
    boundary = report["authority_boundary"]

    report_lines = [
        "# Failure Decomposition Report",
        "",
        f"- evidence_class_id: `{report['evidence_class_id']}`",
        f"- execution_id: `{report['execution_id']}`",
        f"- execution_status: `{report['execution_status']}`",
        f"- fleet_verdict: `{report['fleet_verdict']}`",
        f"- strategy_version: `{report['strategy_version']}`",
        f"- decomposition_mapped_ratio: `{report['decomposition_mapped_ratio']}`",
        f"- panel_zero_trade_refuted: `{report['panel_zero_trade_refuted']}`",
        "",
        "## Git snapshot",
        "",
        f"- HEAD=`{git['head']}`",
        f"- origin/main=`{git['origin_main']}`",
        f"- branch=`{git['branch']}`",
        "",
        "## Candidate decomposition",
        "",
    ]
    for candidate, summary in report["per_candidate_decomposition"].items():
        report_lines.extend(
            [
                f"### {candidate}",
                "",
                f"- candidate_id: `{summary['candidate_id']}`",
                f"- verdict: `{summary['verdict']}`",
                f"- failure_classes: `{summary['failure_classes']}`",
                f"- robustness_failure_modes: `{summary['robustness_failure_modes']}`",
                f"- trade_count: `{summary['data_sufficiency']['trade_count']}`",
                f"- signal_density: `{summary['data_sufficiency']['instruments_with_nonzero_trades']}`/`{summary['data_sufficiency']['panel_member_count']}`",
                f"- retry_allowed: `{summary['retry_allowed']}`",
                "",
            ]
        )
    report_lines.extend(["## Missing inputs", ""])
    if report["missing_inputs"]:
        for item in report["missing_inputs"]:
            report_lines.append(f"- `{item}`")
    else:
        report_lines.append("- none")
    (output_dir / "FAILURE_DECOMPOSITION_REPORT.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )

    summary_payload = {
        "evidence_class_id": report["evidence_class_id"],
        "execution_status": report["execution_status"],
        "fleet_verdict": report["fleet_verdict"],
        "failed_candidates": report["failed_candidates"],
        "failed_candidate_verdicts": report["failed_candidate_verdicts"],
        "decomposition_mapped_ratio": report["decomposition_mapped_ratio"],
        "per_candidate_decomposition": report["per_candidate_decomposition"],
        "missing_inputs": report["missing_inputs"],
        "next_canonical_step": report["next_canonical_step"],
    }
    (output_dir / "FAILURE_DECOMPOSITION_SUMMARY.json").write_text(
        json.dumps(summary_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    (output_dir / "INPUT_EVIDENCE_INDEX.json").write_text(
        json.dumps(report["input_evidence_index"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    governance_attestation = {
        **boundary,
        "economic_evaluation_executed": report["economic_evaluation_executed"],
        "backtest_executed": report["backtest_executed"],
        "walk_forward_run_executed": report["walk_forward_run_executed"],
        "monte_carlo_run_executed": report["monte_carlo_run_executed"],
        "stress_run_executed": report["stress_run_executed"],
        "immutable_binding_retry_allowed": report["immutable_binding_retry_allowed"],
        "same_binding_retry_allowed": report["same_binding_retry_allowed"],
        "new_candidates_ratified": report["new_candidates_ratified"],
        "no_promotion_claim": report["no_promotion_claim"],
        "terminal_negative_evidence_unchanged": report["terminal_negative_evidence_unchanged"],
        "historical_negative_evidence_mutated": report["historical_negative_evidence_mutated"],
        "go_token_consumed": report["go_token_consumed"],
        "futures_only": report["futures_only"],
        "bitcoin_direction_allowed": report["bitcoin_direction_allowed"],
    }
    (output_dir / "GOVERNANCE_BOUNDARY_ATTESTATION.json").write_text(
        json.dumps(governance_attestation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    run_metadata = {
        "executed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "process_classification": report["process_classification"],
        "scope_classification": report["scope_classification"],
        "go_token": CONFIRM_GO,
        "go_token_consumed": True,
        "git_snapshot": git,
        "source_manifest_verify_rc": report["source_manifest_verify_rc"],
        "source_prs": report["source_prs"],
        "collector_script": str(Path(__file__).relative_to(_REPO_ROOT)),
    }
    (output_dir / "RUN_METADATA.json").write_text(
        json.dumps(run_metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_failure_decomposition_evidence_execution_v0(
    *,
    go_token: str,
    scope_id: str,
    execution_id: str,
    parent_evaluation_bundle: Path,
    durable_archive_root: Path,
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
    if scope_id != SCOPE_ID:
        _die("ERR:scope_id mismatch")
    if execution_id != EXECUTION_ID:
        _die("ERR:execution_id mismatch")
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

    scope_definition_ref = Path(config["parent_scope_definition_evidence_ref"])
    if not scope_definition_ref.is_dir():
        _die(f"ERR:missing scope definition evidence ref: {scope_definition_ref}")

    output_dir = durable_archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    parent_manifest_rc = _verify_source_manifest(
        parent_evaluation_bundle,
        output_dir / "parent_evaluation_manifest_verify.log",
    )
    scope_manifest_rc = _verify_source_manifest(
        scope_definition_ref,
        output_dir / "scope_definition_manifest_verify.log",
    )
    if parent_manifest_rc != 0:
        _die(f"ERR:parent evaluation manifest invalid: {parent_evaluation_bundle}")
    if scope_manifest_rc != 0:
        _die(f"ERR:scope definition manifest invalid: {scope_definition_ref}")

    git_snapshot = _git_snapshot()
    report = _collect_decomposition(
        config=config,
        parent_evaluation_ref=parent_evaluation_bundle,
        scope_definition_ref=scope_definition_ref,
        parent_manifest_rc=parent_manifest_rc,
        scope_manifest_rc=scope_manifest_rc,
        git_snapshot=git_snapshot,
    )
    report["durable_evidence_path"] = str(output_dir)
    report["manifest_verify_rc"] = 0

    _write_reports(output_dir, report)
    (output_dir / "failure_decomposition_full.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
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
        description=(
            "Execute read-only post-PR4897 v4 fleet robustness failure decomposition evidence v0."
        )
    )
    parser.add_argument("--go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--execution-id", required=True)
    parser.add_argument("--parent-evaluation-bundle", type=Path, required=True)
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

    report = run_failure_decomposition_evidence_execution_v0(
        go_token=args.go_token,
        scope_id=args.scope_id,
        execution_id=args.execution_id,
        parent_evaluation_bundle=args.parent_evaluation_bundle,
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
    for key in ("execution_status", "durable_evidence_path", "manifest_verify_rc"):
        print(f"{key.upper()}={report[key]}")


if __name__ == "__main__":
    main()
