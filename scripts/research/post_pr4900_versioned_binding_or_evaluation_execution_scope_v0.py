#!/usr/bin/env python3
"""Post-PR4900 versioned binding or fail-closed evaluation execution scope v0.

Bounded binding inventory and precondition verification after PR4900 scope definition.
Executes offline economic evaluation only when all versioned binding preconditions are
fully satisfied and admissible. Fail-closed without evaluation when any precondition
is missing or inadmissible (e.g. terminal v4 SPARSE_SIGNAL_ZERO_TRADE_RESEARCH_V0 retry).

No runtime authority. Operator GO: GO_POST_PR4899_VERSIONED_BINDING_OR_EVALUATION_EXECUTION_SCOPE_V0
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

CONFIRM_GO = "GO_POST_PR4899_VERSIONED_BINDING_OR_EVALUATION_EXECUTION_SCOPE_V0"
SCOPE_ID = "POST_PR4900_VERSIONED_BINDING_OR_EVALUATION_EXECUTION_SCOPE_V0"
EVIDENCE_CLASS_ID = SCOPE_ID
PROCESS_CLASSIFICATION = SCOPE_ID
SCOPE_CLASSIFICATION = (
    "BOUNDED_VERSIONED_BINDING_FIRST_AND_FAIL_CLOSED_OFFLINE_ECONOMIC_EVALUATION_SCOPE_"
    "AFTER_TERMINAL_V4_FLEET_FAILURE_V0"
)
EXECUTION_STATUS = "BINDING_PRECONDITION_INCOMPLETE_NOT_EVALUATED_V0"
DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/post_pr4900_versioned_binding_or_evaluation_execution_scope_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "post_pr4900_versioned_binding_or_evaluation_execution_scope_v0"
PARENT_SCOPE_REL = "docs/ops/research/POST_PR4899_TERMINAL_FLEET_FAILURE_NEXT_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0.md"
V4_BINDING_RATIFICATION_REL = (
    "config/research/post_pr4895_versioned_fleet_binding_ratification_v0.json"
)
BLOCKED_BINDING_CLASS = "SPARSE_SIGNAL_ZERO_TRADE_RESEARCH_V0"
BLOCKED_STRATEGY_VERSION = "v4"
RESEARCH_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
REQUIRED_BINDING_FIELDS: tuple[str, ...] = (
    "strategy_id",
    "strategy_version",
    "parameter_binding",
    "dataset_binding",
    "period_binding",
    "instrument_binding",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "implementation_digest",
    "config_digest",
    "data_digest",
    "research_hypothesis_binding",
    "binding_class_binding",
)
NEXT_ADMISSIBLE_GO = (
    "GO_OPERATOR_RATIFY_POST_V4_NEW_HYPOTHESIS_AND_VERSIONED_FLEET_BINDING_RATIFICATION_V0"
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
        "\n".join(
            [
                f"SOURCE_EVIDENCE_REF={source_dir}",
                f"MANIFEST_VERIFY_RC={rc}",
                f"MANIFEST_VERIFY_MSG={msg or 'ok'}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return rc


def _extract_binding_class(candidate: dict[str, Any]) -> str | None:
    dataset = candidate.get("dataset_binding")
    if isinstance(dataset, dict):
        adapter = dataset.get("evaluation_price_data_adapter")
        if isinstance(adapter, dict) and adapter.get("binding_class"):
            return str(adapter["binding_class"])
    provenance = candidate.get("dataset_provenance")
    if isinstance(provenance, dict) and provenance.get("binding_class"):
        return str(provenance["binding_class"])
    if candidate.get("binding_class"):
        return str(candidate["binding_class"])
    return None


def _field_status(candidate: dict[str, Any], field: str) -> dict[str, Any]:
    if field == "research_hypothesis_binding":
        value = candidate.get("research_hypothesis_binding")
        if value is None:
            return {
                "field": field,
                "status": "MISSING",
                "admissible": False,
                "reason": "no_ratified_research_hypothesis_binding_present",
            }
        return {"field": field, "status": "PRESENT", "admissible": True, "value": value}

    if field == "binding_class_binding":
        binding_class = _extract_binding_class(candidate)
        if binding_class is None:
            return {
                "field": field,
                "status": "MISSING",
                "admissible": False,
                "reason": "binding_class_not_materialized",
            }
        if binding_class == BLOCKED_BINDING_CLASS:
            return {
                "field": field,
                "status": "PRESENT_INADMISSIBLE",
                "admissible": False,
                "value": binding_class,
                "reason": "terminal_v4_sparse_signal_zero_trade_binding_class_blocked",
            }
        return {
            "field": field,
            "status": "PRESENT",
            "admissible": True,
            "value": binding_class,
        }

    if field == "strategy_version":
        version = candidate.get("strategy_version")
        if version is None:
            return {
                "field": field,
                "status": "MISSING",
                "admissible": False,
                "reason": "strategy_version_not_bound",
            }
        if str(version) == BLOCKED_STRATEGY_VERSION:
            return {
                "field": field,
                "status": "PRESENT_INADMISSIBLE",
                "admissible": False,
                "value": version,
                "reason": "terminal_v4_strategy_version_requires_material_beyond_v4",
            }
        return {"field": field, "status": "PRESENT", "admissible": True, "value": version}

    value = candidate.get(field)
    if value is None:
        return {
            "field": field,
            "status": "MISSING",
            "admissible": False,
            "reason": f"{field}_not_bound",
        }
    return {"field": field, "status": "PRESENT", "admissible": True}


def _candidate_precondition_check(
    candidate: dict[str, Any],
    *,
    terminal_verdict: str,
) -> dict[str, Any]:
    strategy_id = candidate.get("strategy_id") or candidate.get(
        "canonical_candidate_identifier", ""
    )
    per_field = [_field_status(candidate, field) for field in REQUIRED_BINDING_FIELDS]
    missing = [f["field"] for f in per_field if f["status"] == "MISSING"]
    inadmissible = [f for f in per_field if f["status"] == "PRESENT_INADMISSIBLE"]
    admissible = all(f["admissible"] for f in per_field)
    retry_blocked = (
        terminal_verdict == "ROBUSTNESS_FAILED"
        and str(candidate.get("strategy_version")) == BLOCKED_STRATEGY_VERSION
    )
    return {
        "strategy_id": strategy_id,
        "terminal_verdict": terminal_verdict,
        "retry_blocked": retry_blocked,
        "all_fields_admissible": admissible and not retry_blocked,
        "missing_fields": missing,
        "inadmissible_fields": [
            {"field": f["field"], "reason": f.get("reason"), "value": f.get("value")}
            for f in inadmissible
        ],
        "per_field": per_field,
        "existing_binding_source": V4_BINDING_RATIFICATION_REL,
        "existing_binding_class": _extract_binding_class(candidate),
        "existing_strategy_version": candidate.get("strategy_version"),
    }


def _inventory_existing_bindings(v4_ratification: dict[str, Any]) -> dict[str, Any]:
    candidates_raw = v4_ratification.get("candidates") or []
    by_id: dict[str, dict[str, Any]] = {}
    for candidate in candidates_raw:
        if not isinstance(candidate, dict):
            continue
        sid = str(candidate.get("strategy_id") or "")
        by_id[sid] = candidate

    inventory: list[dict[str, Any]] = []
    for strategy_id in RESEARCH_CANDIDATES:
        candidate = by_id.get(strategy_id)
        if candidate is None:
            inventory.append(
                {
                    "strategy_id": strategy_id,
                    "binding_source_found": False,
                    "terminal_verdict": "ROBUSTNESS_FAILED",
                    "all_fields_admissible": False,
                    "missing_fields": list(REQUIRED_BINDING_FIELDS),
                    "inadmissible_fields": [],
                    "per_field": [],
                }
            )
            continue
        inventory.append(
            _candidate_precondition_check(candidate, terminal_verdict="ROBUSTNESS_FAILED")
        )

    return {
        "inventory_sources": [
            V4_BINDING_RATIFICATION_REL,
            PARENT_SCOPE_REL,
        ],
        "candidates": inventory,
        "fleet_all_admissible": all(c.get("all_fields_admissible") for c in inventory),
    }


def _build_precondition_check(inventory: dict[str, Any]) -> dict[str, Any]:
    fleet_admissible = inventory["fleet_all_admissible"]
    status = "COMPLETE" if fleet_admissible else "BINDING_PRECONDITION_INCOMPLETE"
    blocked_reasons: list[str] = []
    if not fleet_admissible:
        blocked_reasons.extend(
            [
                "terminal_v4_robustness_failed_bindings_not_admissible_for_retry",
                "no_ratified_research_hypothesis_binding_beyond_v4",
                "no_binding_class_beyond_sparse_signal_zero_trade_research_v0",
                "no_strategy_version_materially_beyond_v4",
            ]
        )
    return {
        "binding_precondition_status": status,
        "fleet_all_admissible": fleet_admissible,
        "evaluation_admissible": fleet_admissible,
        "evaluation_executed": False,
        "blocked_reasons": blocked_reasons,
        "required_binding_fields": list(REQUIRED_BINDING_FIELDS),
        "per_candidate": inventory["candidates"],
    }


def _write_binding_inventory_report(
    path: Path, inventory: dict[str, Any], check: dict[str, Any]
) -> None:
    lines = [
        "# Binding Inventory Report",
        "",
        f"Scope: `{SCOPE_ID}`",
        f"Status: `{check['binding_precondition_status']}`",
        "",
        "## Inventory Sources",
        "",
    ]
    for source in inventory["inventory_sources"]:
        lines.append(f"- `{source}`")
    lines.extend(["", "## Per-Candidate Summary", ""])
    for candidate in inventory["candidates"]:
        lines.append(f"### `{candidate['strategy_id']}`")
        lines.append("")
        lines.append(f"- all_fields_admissible: `{candidate.get('all_fields_admissible')}`")
        lines.append(f"- retry_blocked: `{candidate.get('retry_blocked')}`")
        lines.append(f"- missing_fields: `{candidate.get('missing_fields')}`")
        lines.append(f"- inadmissible_fields: `{candidate.get('inadmissible_fields')}`")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_admissibility_matrix(path: Path, check: dict[str, Any]) -> None:
    eval_allowed = check["evaluation_admissible"]
    lines = [
        "# Admissibility Matrix",
        "",
        "## allowed_now",
        "",
        "| Action | Status |",
        "|---|---|",
        "| Binding inventory (read-only) | `ALLOWED` |",
        "| Precondition verification | `ALLOWED` |",
        "| Durable evidence bundle | `ALLOWED` |",
        "",
        "## blocked_now",
        "",
        "| Action | Status |",
        "|---|---|",
        f"| Economic evaluation | `{'ALLOWED' if eval_allowed else 'BLOCKED'}` |",
        f"| Backtest | `{'ALLOWED' if eval_allowed else 'BLOCKED'}` |",
        f"| Walk-forward | `{'ALLOWED' if eval_allowed else 'BLOCKED'}` |",
        f"| Monte Carlo | `{'ALLOWED' if eval_allowed else 'BLOCKED'}` |",
        f"| Stress | `{'ALLOWED' if eval_allowed else 'BLOCKED'}` |",
        "| Unchanged v4 binding retry | `BLOCKED` |",
        "| Runtime / Shadow / Paper / Testnet / Live | `BLOCKED` |",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_parent_evidence_trace(
    path: Path,
    *,
    parent_bundle: Path,
    parent_manifest_rc: int,
    scope_file: Path,
) -> None:
    lines = [
        "# Parent Evidence Trace",
        "",
        f"- Parent PR4899 bundle: `{parent_bundle}`",
        f"- Parent MANIFEST_VERIFY_RC: `{parent_manifest_rc}`",
        f"- Parent scope PR4900 file: `{scope_file.relative_to(_REPO_ROOT)}`",
        "",
        "## Bindende Parent Facts",
        "",
        "| Fact | Value |",
        "|---|---|",
        "| FLEET_SIGNAL_EDGE | TERMINAL_NEGATIVE |",
        "| FLEET_WALK_FORWARD_OOS | TERMINAL_NEGATIVE |",
        "| FLEET_MONTE_CARLO_FRAGILITY | TERMINAL_NEGATIVE |",
        "| PARAMETER_FRAGILITY | REFUTED |",
        "| BINDING_DELTA_RESCUE | REFUTED |",
        "| PORTFOLIO_CONTRIBUTION | TERMINAL_NEGATIVE |",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_authority_boundary(output_dir: Path) -> None:
    output_dir.joinpath("GOVERNANCE_BOUNDARY_ATTESTATION.json").write_text(
        json.dumps(
            {
                "runtime_authority": "NONE",
                "economic_evaluation_executed": False,
                "backtest_executed": False,
                "walk_forward_executed": False,
                "monte_carlo_executed": False,
                "stress_executed": False,
                "promotion_authority": False,
                "shadow_authorized": False,
                "paper_authorized": False,
                "testnet_authorized": False,
                "live_authorized": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def run_versioned_binding_or_evaluation_execution_scope_v0(
    *,
    go_token: str,
    scope_id: str,
    parent_evidence_bundle: Path,
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
    if not parent_evidence_bundle.is_dir():
        _die(f"ERR:missing parent evidence bundle: {parent_evidence_bundle}")

    config = _load_json(config_path)
    v4_ratification_path = _REPO_ROOT / V4_BINDING_RATIFICATION_REL
    if not v4_ratification_path.is_file():
        _die(f"ERR:missing v4 binding ratification inventory: {v4_ratification_path}")

    output_dir = durable_archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    parent_manifest_rc = _verify_source_manifest(
        parent_evidence_bundle,
        output_dir / "parent_evidence_manifest_verify.log",
    )
    if parent_manifest_rc != 0:
        _die(f"ERR:parent evidence manifest invalid: {parent_evidence_bundle}")

    v4_ratification = _load_json(v4_ratification_path)
    inventory = _inventory_existing_bindings(v4_ratification)
    precondition = _build_precondition_check(inventory)

    if precondition["evaluation_admissible"]:
        _die("ERR:evaluation path not implemented in v0 without full admissible bindings")

    _write_binding_inventory_report(
        output_dir / "BINDING_INVENTORY_REPORT.md",
        inventory,
        precondition,
    )
    _write_admissibility_matrix(output_dir / "ADMISSIBILITY_MATRIX.md", precondition)
    _write_parent_evidence_trace(
        output_dir / "PARENT_EVIDENCE_TRACE.md",
        parent_bundle=parent_evidence_bundle,
        parent_manifest_rc=parent_manifest_rc,
        scope_file=_REPO_ROOT / PARENT_SCOPE_REL,
    )
    (output_dir / "VERSIONED_BINDING_PRECONDITION_CHECK.json").write_text(
        json.dumps(precondition, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_authority_boundary(output_dir)

    git_snapshot = _git_snapshot()
    report: dict[str, Any] = {
        "verdict": EXECUTION_STATUS,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "scope_id": SCOPE_ID,
        "execution_status": EXECUTION_STATUS,
        "binding_precondition_status": precondition["binding_precondition_status"],
        "result_classification": precondition["binding_precondition_status"],
        "go_token": CONFIRM_GO,
        "go_token_consumed": True,
        "parent_evidence_bundle": str(parent_evidence_bundle),
        "parent_manifest_verify_rc": parent_manifest_rc,
        "parent_scope_pr": 4900,
        "parent_scope_file": PARENT_SCOPE_REL,
        "economic_evaluation_executed": False,
        "backtest_executed": False,
        "walk_forward_executed": False,
        "monte_carlo_executed": False,
        "stress_executed": False,
        "runtime_authority": "NONE",
        "promotion_authority": False,
        "fleet_verdict": "FLEET_ECONOMIC_VALIDITY_FAIL",
        "failed_candidates": list(RESEARCH_CANDIDATES),
        "next_admissible_step": NEXT_ADMISSIBLE_GO,
        "durable_evidence_path": str(output_dir),
        "git_snapshot": git_snapshot,
        "precondition_check": precondition,
    }

    (output_dir / "SCOPE_EXECUTION_SUMMARY.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "RUN_METADATA.json").write_text(
        json.dumps(
            {
                "executed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "process_classification": PROCESS_CLASSIFICATION,
                "scope_classification": SCOPE_CLASSIFICATION,
                "go_token": CONFIRM_GO,
                "go_token_consumed": True,
                "git_snapshot": git_snapshot,
                "parent_manifest_verify_rc": parent_manifest_rc,
                "collector_script": str(Path(__file__).relative_to(_REPO_ROOT)),
            },
            indent=2,
            sort_keys=True,
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
        description="Execute post-PR4900 versioned binding or fail-closed evaluation scope v0."
    )
    parser.add_argument("--go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--parent-evidence-bundle", type=Path, required=True)
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

    report = run_versioned_binding_or_evaluation_execution_scope_v0(
        go_token=args.go_token,
        scope_id=args.scope_id,
        parent_evidence_bundle=args.parent_evidence_bundle,
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
        "binding_precondition_status",
        "durable_evidence_path",
        "manifest_verify_rc",
    ):
        print(f"{key.upper()}={report[key]}")


if __name__ == "__main__":
    main()
