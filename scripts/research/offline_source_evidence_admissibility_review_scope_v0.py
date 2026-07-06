#!/usr/bin/env python3
"""Materialize offline source evidence admissibility review scope definition v0.

Offline-only scope-definition evidence bundle. No admissibility review execution,
no economic evaluation, no runtime authority.
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

SCOPE_ID = "OFFLINE_SOURCE_EVIDENCE_ADMISSIBILITY_REVIEW_SCOPE_V0"
PROCESS_CLASSIFICATION = (
    "OFFLINE_SOURCE_EVIDENCE_ADMISSIBILITY_REVIEW_OR_ECONOMIC_EVALUATION_PRECONDITION_"
    "SCOPE_DEFINITION_V0"
)
SCOPE_CLASSIFICATION = "SCOPE_DEFINITION_ONLY_NO_ECONOMIC_EVALUATION_NO_RUNTIME_AUTHORITY_V0"
GO_TOKEN = (
    "GO_OPERATOR_RATIFY_NEXT_OFFLINE_ONLY_SOURCE_EVIDENCE_ADMISSIBILITY_REVIEW_OR_"
    "ECONOMIC_EVALUATION_PRECONDITION_SCOPE_V0"
)
DEFAULT_CONFIG = (
    _REPO_ROOT / "config/research/offline_source_evidence_admissibility_review_scope_v0.json"
)
DEFAULT_DOC = (
    _REPO_ROOT / "docs/governance/OFFLINE_SOURCE_EVIDENCE_ADMISSIBILITY_REVIEW_SCOPE_V0.md"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "offline_source_evidence_admissibility_review_scope_v0"

FORBIDDEN_AUTHORITY_FLAGS = (
    "economic_evaluation_executed",
    "economic_viability_claimed",
    "economic_viability_evidence_emitted",
    "runtime_authority_granted",
    "orders_allowed",
    "scheduler_runtime_allowed",
    "live_authorized",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "adapter_submission_allowed",
    "credentials_required",
    "arming_allowed",
    "core_system_mutation_allowed",
    "canonical_trading_logic_mutation_allowed",
    "master_v2_mutation_allowed",
    "double_play_mutation_allowed",
    "risk_sizing_mutation_allowed",
    "safety_runtime_mutation_allowed",
)

REQUIRED_REVIEW_DIMENSIONS = (
    "source_evidence_manifest_integrity",
    "source_evidence_contract_coverage",
    "candidate_binding_precondition_coverage",
    "dataset_binding_precondition_coverage",
    "period_binding_precondition_coverage",
    "instrument_binding_precondition_coverage",
    "fee_slippage_funding_execution_binding_precondition_coverage",
    "economic_policy_binding_precondition_coverage",
    "implementation_config_data_digest_precondition_coverage",
    "failed_binding_no_retry_guard",
    "no_policy_threshold_backfit_guard",
    "no_runtime_authority_from_evidence_guard",
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


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if config.get("scope_id") != SCOPE_ID:
        errors.append("unexpected scope_id")
    if config.get("go_token") != GO_TOKEN:
        errors.append("unexpected go_token")
    if config.get("process_classification") != PROCESS_CLASSIFICATION:
        errors.append("unexpected process_classification")
    if config.get("scope_classification") != SCOPE_CLASSIFICATION:
        errors.append("unexpected scope_classification")
    if config.get("parent_pr") != 4912:
        errors.append("unexpected parent_pr")
    if config.get("admissibility_review_defined") is not True:
        errors.append("admissibility_review_defined must be true")
    if config.get("admissibility_review_executed") is not False:
        errors.append("admissibility_review_executed must be false")
    if config.get("economic_evaluation_authorized") is not False:
        errors.append("economic_evaluation_authorized must be false")

    for flag in FORBIDDEN_AUTHORITY_FLAGS:
        if config.get(flag) is not False:
            errors.append(f"forbidden authority flag must be false: {flag}")

    dimensions = config.get("required_review_dimensions", [])
    missing_dimensions = sorted(set(REQUIRED_REVIEW_DIMENSIONS) - set(dimensions))
    if missing_dimensions:
        errors.append(f"missing required review dimensions: {missing_dimensions}")

    return errors


def _write_scope_definition_md(output_dir: Path, config: dict[str, Any]) -> None:
    lines = [
        "# Scope Definition",
        "",
        f"- scope_id: `{SCOPE_ID}`",
        f"- verdict: `SCOPE_DEFINED_NOT_EXECUTED`",
        f"- process_classification: `{PROCESS_CLASSIFICATION}`",
        f"- scope_classification: `{SCOPE_CLASSIFICATION}`",
        f"- go_token: `{GO_TOKEN}`",
        f"- parent_pr: `{config.get('parent_pr')}`",
        f"- parent_pre_merge_origin_main: `{config.get('parent_pre_merge_origin_main')}`",
        f"- parent_pr_head: `{config.get('parent_pr_head')}`",
        f"- parent_post_merge_head: `{config.get('parent_post_merge_head')}`",
        f"- parent_closeout_dir: `{config.get('parent_closeout_dir')}`",
        "",
        "## Scope boundary",
        "",
        "This bundle defines the admissibility review scope only.",
        "It does not execute an admissibility review.",
        "It does not execute an economic evaluation.",
        "It does not emit EconomicViabilityEvidenceV1.",
        "No strategy, parameter, dataset, period, fee, slippage, funding, execution, or policy binding is changed.",
        "No runtime, shadow, paper, testnet, scheduler, adapter, credential, arming, canary, or live authority is granted.",
        "",
        "## Required review dimensions",
        "",
    ]
    for dimension in config.get("required_review_dimensions", []):
        lines.append(f"- `{dimension}`")
    lines.extend(
        [
            "",
            "## Review outcome vocabulary (for later execution only)",
            "",
            "The later admissibility review may emit one of: `PASS`, `FAIL`, `INCONCLUSIVE`.",
            "This scope definition emits no such outcome.",
            "",
            "## Next step",
            "",
            f"`{config.get('next_step_after_this_scope')}`",
            "",
        ]
    )
    output_dir.joinpath("SCOPE_DEFINITION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_offline_source_evidence_admissibility_review_scope_v0(
    *,
    config_path: Path = DEFAULT_CONFIG,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
) -> dict[str, Any]:
    if not config_path.is_file():
        _die(f"ERR:missing config: {config_path}")

    config = _load_json(config_path)
    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        _die("ERR:config validation failed", code=1)

    parent_closeout_dir = Path(config["parent_closeout_dir"])
    if not parent_closeout_dir.is_dir():
        _die(f"ERR:missing parent closeout dir: {parent_closeout_dir}")

    parent_manifest_rc = 0
    parent_manifest_msg = "skipped"
    parent_manifest_path = parent_closeout_dir / "MANIFEST.sha256"
    if parent_manifest_path.is_file():
        ok, msg = verify_manifest_sha256(parent_closeout_dir)
        parent_manifest_rc = 0 if ok else 1
        parent_manifest_msg = msg or "ok"
        if parent_manifest_rc != int(config.get("required_parent_manifest_rc", 0)):
            _die(f"ERR:parent manifest verify rc mismatch: {parent_closeout_dir}")
    else:
        _die(f"ERR:parent MANIFEST.sha256 missing: {parent_closeout_dir}")

    output_dir = archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    git_snapshot = _git_snapshot()
    (output_dir / "scope_definition_v0.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "git_snapshot.json").write_text(
        json.dumps(git_snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "parent_manifest_verify.log").write_text(
        "\n".join(
            [
                f"PARENT_CLOSEOUT_DIR={parent_closeout_dir}",
                f"MANIFEST_VERIFY_RC={parent_manifest_rc}",
                f"MANIFEST_VERIFY_MSG={parent_manifest_msg}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_scope_definition_md(output_dir, config)

    summary = {
        "verdict": "SCOPE_DEFINED_NOT_EXECUTED",
        "scope_id": SCOPE_ID,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token": GO_TOKEN,
        "go_token_consumption": "CONSUMED",
        "parent_pr": config["parent_pr"],
        "parent_pre_merge_origin_main": config["parent_pre_merge_origin_main"],
        "parent_pr_head": config["parent_pr_head"],
        "parent_post_merge_head": config["parent_post_merge_head"],
        "parent_closeout_dir": str(parent_closeout_dir),
        "parent_manifest_verify_rc": parent_manifest_rc,
        "admissibility_review_defined": True,
        "admissibility_review_executed": False,
        "economic_evaluation_authorized": False,
        "economic_evaluation_executed": False,
        "economic_viability_evidence_emitted": False,
        "runtime_authority_granted": False,
        "required_review_dimensions": config["required_review_dimensions"],
        "next_step_after_this_scope": config["next_step_after_this_scope"],
        "durable_evidence_path": str(output_dir),
        "git_snapshot": git_snapshot,
    }
    (output_dir / "SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    write_manifest_sha256(output_dir)
    manifest_ok, manifest_msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if manifest_ok else 1
    if manifest_rc != 0:
        _die(f"ERR:manifest verify failed: {output_dir} ({manifest_msg})")

    summary["manifest_verify_rc"] = manifest_rc
    (output_dir / "SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256(output_dir)
    manifest_ok, manifest_msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if manifest_ok else 1
    if manifest_rc != 0:
        _die(f"ERR:manifest verify failed after summary update: {output_dir} ({manifest_msg})")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize offline source evidence admissibility review scope definition v0"
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()

    result = run_offline_source_evidence_admissibility_review_scope_v0(
        config_path=args.config,
        archive_root=args.durable_evidence_root,
    )
    print("VERDICT=SCOPE_DEFINED_NOT_EXECUTED")
    print(f"SCOPE_ID={result['scope_id']}")
    print(f"DURABLE_EVIDENCE_BUNDLE={result['durable_evidence_path']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    print(f"NEXT_STEP={result['next_step_after_this_scope']}")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
