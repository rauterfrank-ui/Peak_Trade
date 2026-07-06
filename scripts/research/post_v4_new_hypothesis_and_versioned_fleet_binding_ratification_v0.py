#!/usr/bin/env python3
"""Post-v4 new hypothesis and versioned fleet binding ratification v0.

Offline-only scope definition and binding-definition ratification after PR4901
fail-closed binding-precondition-incomplete closeout. No binding materialization,
no economic evaluation, no runtime authority.

Operator GO: GO_OPERATOR_RATIFY_POST_V4_NEW_HYPOTHESIS_AND_VERSIONED_FLEET_BINDING_RATIFICATION_V0
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

CONFIRM_GO = "GO_OPERATOR_RATIFY_POST_V4_NEW_HYPOTHESIS_AND_VERSIONED_FLEET_BINDING_RATIFICATION_V0"
SCOPE_ID = "POST_V4_NEW_HYPOTHESIS_AND_VERSIONED_FLEET_BINDING_RATIFICATION_V0"
PROCESS_CLASSIFICATION = SCOPE_ID
SCOPE_CLASSIFICATION = (
    "NEW_HYPOTHESIS_AND_VERSIONED_FLEET_BINDING_RATIFICATION_ONLY_AFTER_"
    "PR4901_FAIL_CLOSED_BINDING_PRECONDITION_INCOMPLETE_V0"
)
VERDICT = "SCOPE_DEFINED_NOT_EVALUATED"
RATIFICATION_STATUS = "RATIFIED_FOR_BINDING_DEFINITION_ONLY"
DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/post_v4_new_hypothesis_and_versioned_fleet_binding_ratification_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "post_v4_new_hypothesis_and_versioned_fleet_binding_ratification_v0"
NEXT_ADMISSIBLE_GO = "GO_OPERATOR_RATIFY_POST_V4_VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_V0"
FLEET_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")


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


def _write_hypothesis_ratification_report(path: Path, config: dict[str, Any]) -> None:
    hypothesis = config.get("research_hypothesis_binding") or {}
    lines = [
        "# Research Hypothesis Ratification Report",
        "",
        f"Scope: `{SCOPE_ID}`",
        f"Verdict: `{VERDICT}`",
        "",
        "## Hypothesis",
        "",
        f"- hypothesis_id: `{hypothesis.get('hypothesis_id')}`",
        f"- hypothesis_version: `{hypothesis.get('hypothesis_version')}`",
        f"- ratification_status: `{hypothesis.get('ratification_status')}`",
        "",
        f"> {hypothesis.get('hypothesis_statement', '')}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_fleet_binding_definition_report(path: Path, config: dict[str, Any]) -> None:
    lines = [
        "# Fleet Binding Definition Report",
        "",
        f"Scope: `{SCOPE_ID}`",
        "",
        "## Per-Candidate Binding Definitions",
        "",
    ]
    for candidate in config.get("final_research_fleet") or []:
        if not isinstance(candidate, dict):
            continue
        lines.extend(
            [
                f"### `{candidate.get('strategy_id')}`",
                "",
                f"- strategy_version: `{candidate.get('strategy_version')}`",
                f"- binding_status: `{candidate.get('binding_status')}`",
                f"- evaluation_authorized: `{candidate.get('evaluation_authorized')}`",
                f"- blocked_versions: `{candidate.get('blocked_versions')}`",
                f"- blocked_binding_classes: `{candidate.get('blocked_binding_classes')}`",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_admissibility_matrix(path: Path) -> None:
    lines = [
        "# Admissibility Matrix",
        "",
        "## allowed_now",
        "",
        "| Action | Status |",
        "|---|---|",
        "| Hypothesis ratification (definition only) | `ALLOWED` |",
        "| Fleet binding definition ratification | `ALLOWED` |",
        "| Durable evidence bundle | `ALLOWED` |",
        "",
        "## blocked_now",
        "",
        "| Action | Status |",
        "|---|---|",
        "| Binding materialization | `BLOCKED` |",
        "| Economic evaluation | `BLOCKED` |",
        "| Backtest | `BLOCKED` |",
        "| Walk-forward | `BLOCKED` |",
        "| Monte Carlo | `BLOCKED` |",
        "| Stress | `BLOCKED` |",
        "| Unchanged v4 binding retry | `BLOCKED` |",
        "| Runtime / Shadow / Paper / Testnet / Live | `BLOCKED` |",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_parent_evidence_trace(
    path: Path,
    *,
    parent_closeout_dir: Path,
    parent_manifest_rc: int,
) -> None:
    lines = [
        "# Parent Evidence Trace",
        "",
        f"- Parent PR4901 closeout: `{parent_closeout_dir}`",
        f"- Parent MANIFEST_VERIFY_RC: `{parent_manifest_rc}`",
        f"- Parent scope PR4900 governance: `docs/governance/POST_PR4900_VERSIONED_BINDING_OR_EVALUATION_EXECUTION_SCOPE_V0.md`",
        "",
        "## Bindende Parent Facts",
        "",
        "| Fact | Value |",
        "|---|---|",
        "| BINDING_PRECONDITION_STATUS | BINDING_PRECONDITION_INCOMPLETE |",
        "| BLOCKED_STRATEGY_VERSION | v4 |",
        "| BLOCKED_BINDING_CLASS | SPARSE_SIGNAL_ZERO_TRADE_RESEARCH_V0 |",
        "| ECONOMIC_EVALUATION_EXECUTED | false |",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_authority_boundary(output_dir: Path, authority: dict[str, Any]) -> None:
    output_dir.joinpath("GOVERNANCE_BOUNDARY_ATTESTATION.json").write_text(
        json.dumps(authority, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_post_v4_hypothesis_and_fleet_binding_ratification_v0(
    *,
    go_token: str,
    scope_id: str,
    parent_closeout_dir: Path,
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
    if not parent_closeout_dir.is_dir():
        _die(f"ERR:missing parent closeout dir: {parent_closeout_dir}")

    config = _load_json(config_path)
    output_dir = durable_archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    parent_manifest_rc = _verify_source_manifest(
        parent_closeout_dir,
        output_dir / "parent_closeout_manifest_verify.log",
    )
    if parent_manifest_rc != 0:
        _die(f"ERR:parent closeout manifest invalid: {parent_closeout_dir}")

    _write_hypothesis_ratification_report(
        output_dir / "RESEARCH_HYPOTHESIS_RATIFICATION_REPORT.md",
        config,
    )
    _write_fleet_binding_definition_report(
        output_dir / "FLEET_BINDING_DEFINITION_REPORT.md",
        config,
    )
    _write_admissibility_matrix(output_dir / "ADMISSIBILITY_MATRIX.md")
    _write_parent_evidence_trace(
        output_dir / "PARENT_EVIDENCE_TRACE.md",
        parent_closeout_dir=parent_closeout_dir,
        parent_manifest_rc=parent_manifest_rc,
    )
    authority = config.get("authority") or {}
    _write_authority_boundary(output_dir, authority)

    git_snapshot = _git_snapshot()
    report: dict[str, Any] = {
        "verdict": VERDICT,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_id": SCOPE_ID,
        "go_token": CONFIRM_GO,
        "go_token_consumed": True,
        "parent_closeout_dir": str(parent_closeout_dir),
        "parent_manifest_verify_rc": parent_manifest_rc,
        "research_hypothesis_binding": config.get("research_hypothesis_binding"),
        "final_research_fleet": config.get("final_research_fleet"),
        "required_binding_fields_before_evaluation": config.get(
            "required_binding_fields_before_evaluation"
        ),
        "economic_evaluation_executed": False,
        "backtest_executed": False,
        "walk_forward_executed": False,
        "monte_carlo_executed": False,
        "stress_executed": False,
        "runtime_authority": authority.get("runtime_authority", "NONE"),
        "promotion_authority": authority.get("promotion_authority", False),
        "next_admissible_step": NEXT_ADMISSIBLE_GO,
        "durable_evidence_path": str(output_dir),
        "git_snapshot": git_snapshot,
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
        description=("Execute post-v4 new hypothesis and versioned fleet binding ratification v0.")
    )
    parser.add_argument("--go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--parent-closeout-dir", type=Path, required=True)
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

    report = run_post_v4_hypothesis_and_fleet_binding_ratification_v0(
        go_token=args.go_token,
        scope_id=args.scope_id,
        parent_closeout_dir=args.parent_closeout_dir,
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
    for key in ("verdict", "durable_evidence_path", "manifest_verify_rc", "next_admissible_step"):
        print(f"{key.upper()}={report[key]}")


if __name__ == "__main__":
    main()
