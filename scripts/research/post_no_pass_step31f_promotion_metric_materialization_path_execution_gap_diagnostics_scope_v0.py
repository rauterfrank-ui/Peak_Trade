#!/usr/bin/env python3
"""Materialize post-no-pass STEP31F promotion metric materialization path execution gap diagnostics scope v0.

Offline-only scope-definition evidence bundle. No economic evaluation, no diagnostics execution,
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

CONFIRM_GO = "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_V0"
SCOPE_ID = (
    "POST_NO_PASS_STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_GAP_DIAGNOSTICS_SCOPE_V0"
)
PROCESS_CLASSIFICATION = "NEW_RATIFIED_RESEARCH_SCOPE_OR_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_V0"
PRIMARY_CAUSE = "PATH_PRESENT_BUT_NOT_EXECUTED"
NEXT_EXECUTION_GO = "GO_POST_NO_PASS_STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_GAP_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
NEXT_CANONICAL_STEP = "REQUEST_OPERATOR_GO_FOR_POST_NO_PASS_STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_GAP_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/post_no_pass_step31f_promotion_metric_materialization_path_execution_gap_diagnostics_scope_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = (
    "post_no_pass_step31f_promotion_metric_materialization_path_execution_gap_diagnostics_scope_v0"
)
PARENT_EXECUTION_BUNDLE_SUFFIX = "post_no_pass_metric_materialization_path_offline_economic_evaluation_execution_v0_20260705T235133Z"
REQUIRED_DIAGNOSTICS_FIELDS = (
    "source_evidence_refs",
    "candidate_binding_refs",
    "diagnostic_axes",
    "diagnostics_schema_version",
    "failure_axis_results",
    "admissibility_summary",
    "no_promotion_claim",
    "diagnostics_manifest",
    "step31f_path_inventory",
    "materialization_owner_chain_trace",
    "execution_gap_classification",
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
    parent_ref = archive_root / "implementation" / PARENT_EXECUTION_BUNDLE_SUFFIX
    if not parent_ref.is_dir():
        _die(f"ERR:missing parent execution evidence ref: {parent_ref}")

    output_dir = archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    parent_manifest_rc = _verify_source_manifest(
        parent_ref,
        output_dir / "source_parent_execution_evidence_manifest_verify.log",
    )
    if parent_manifest_rc != 0:
        _die("ERR:source parent execution manifest verify failed")

    git_snapshot = _git_snapshot()
    report: dict[str, Any] = {
        "scope_id": SCOPE_ID,
        "process_classification": PROCESS_CLASSIFICATION,
        "selected_class": "E",
        "primary_cause": PRIMARY_CAUSE,
        "panel_zero_trade_refuted": config["panel_zero_trade_refuted"],
        "step31f_promotion_metrics_not_materialized": config[
            "step31f_promotion_metrics_not_materialized"
        ],
        "fleet_status": config["fleet_status"],
        "fleet_verdict": config["fleet_verdict"],
        "go_token": CONFIRM_GO,
        "go_token_consumed": True,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "required_next_go_for_execution": NEXT_EXECUTION_GO,
        "required_versioned_diagnostics_fields": list(REQUIRED_DIAGNOSTICS_FIELDS),
        "required_future_evidence_questions": config["required_future_evidence_questions"],
        "source_parent_execution_evidence_ref": str(parent_ref),
        "source_parent_execution_manifest_verify_rc": parent_manifest_rc,
        "git_snapshot": git_snapshot,
        "execution_id": output_dir.name,
        "new_evidence_dir": str(output_dir),
    }

    (output_dir / "scope_definition_manifest.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    (output_dir / "SCOPE_DEFINITION_REPORT.md").write_text(
        "\n".join(
            [
                "# Scope Definition Report",
                "",
                f"- scope_id: `{SCOPE_ID}`",
                f"- process_classification: `{PROCESS_CLASSIFICATION}`",
                f"- selected_class: `E`",
                f"- primary_cause: `{PRIMARY_CAUSE}`",
                f"- panel_zero_trade_refuted: `{config['panel_zero_trade_refuted']}`",
                f"- step31f_promotion_metrics_not_materialized: `{config['step31f_promotion_metrics_not_materialized']}`",
                f"- fleet_status: `{config['fleet_status']}`",
                f"- fleet_verdict: `{config['fleet_verdict']}`",
                f"- research_hypothesis: `{config['research_hypothesis']}`",
                f"- go_token_consumed: `{CONFIRM_GO}`",
                "",
                "## PR4888 inconclusive binding",
                "",
                "- v3 path-activation bindings executed fail-closed.",
                "- Sparse signal density refutes zero-trade.",
                "- STEP31F promotion metrics not materialized.",
                "- No economic evaluation authorized in this scope.",
                "",
                "## Required future evidence questions",
                "",
                *[f"- {question}" for question in config["required_future_evidence_questions"]],
                "",
                "## Required diagnostics fields before separate execution",
                "",
                *[f"- `{field}`" for field in REQUIRED_DIAGNOSTICS_FIELDS],
                "",
                "## Next canonical step",
                "",
                f"- `{NEXT_CANONICAL_STEP}`",
                f"- execution_go (later, separate): `{NEXT_EXECUTION_GO}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (output_dir / "REGISTRY_UPDATE.md").write_text(
        "\n".join(
            [
                "# Registry Update",
                "",
                "- CURRENT_STATE: `POST_NO_PASS_STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_GAP_DIAGNOSTICS_SCOPE_DEFINED_V0`",
                f"- NEXT_CANONICAL_STEP: `{NEXT_CANONICAL_STEP}`",
                f"- CURRENT_ADMISSIBLE_NEXT_SCOPE: `{SCOPE_ID}`",
                f"- CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN: `{NEXT_EXECUTION_GO}`",
                f"- GO_TOKEN_CONSUMED: `{CONFIRM_GO}`",
                "",
                "Scope-definition GO consumed; separate operator GO required before diagnostics execution.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (output_dir / "SAFETY_BOUNDARY_CONFIRMATION.md").write_text(
        "\n".join(
            [
                "# Safety Boundary Confirmation",
                "",
                "- ECONOMIC_EVALUATION_AUTHORIZED=false",
                "- DIAGNOSTICS_EXECUTION_AUTHORIZED=false",
                "- RUNTIME_REWIRE_ADMISSIBLE=false",
                "- LIVE_AUTHORIZED=false",
                "- CORE_SYSTEM_MUTATION_ALLOWED=false",
                "- CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED=false",
                "- MASTER_V2_MUTATION_ALLOWED=false",
                "- DOUBLE_PLAY_MUTATION_ALLOWED=false",
                "- RISK_SIZING_MUTATION_ALLOWED=false",
                "- SAFETY_RUNTIME_MUTATION_ALLOWED=false",
                "- NO_ECONOMIC_EVALUATION=true",
                "- NO_DIAGNOSTICS_EXECUTION_IN_THIS_SCOPE=true",
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
            "Materialize post-no-pass STEP31F promotion metric materialization path "
            "execution gap diagnostics scope evidence v0."
        )
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()

    report = run_scope_definition_materialization_v0(
        confirm_go_token=args.confirm_go_token,
        config_path=args.config,
        archive_root=args.archive_root,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
