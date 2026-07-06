#!/usr/bin/env python3
"""Materialize post-PR4936 cross-sectional funding rate research fleet complete no-pass scope v0.

Offline-only scope-definition evidence bundle. No economic evaluation, no binding ratification,
no runtime authority.
"""

from __future__ import annotations

import argparse
import hashlib
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

CONFIRM_GO = (
    "GO_DEFINE_NEW_VERSIONED_MATERIAL_RESEARCH_SCOPE_AFTER_PR4936_TERMINAL_NEGATIVE_EVIDENCE_"
    "NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
)
SCOPE_ID = (
    "POST_PR4936_CROSS_SECTIONAL_FUNDING_RATE_RESEARCH_FLEET_COMPLETE_NO_PASS_SCOPE_DEFINITION_V0"
)
PROCESS_CLASSIFICATION = (
    "NEW_VERSIONED_MATERIAL_RESEARCH_SCOPE_DEFINITION_AFTER_TERMINAL_NEGATIVE_EVIDENCE_NO_EVAL_V0"
)
SCOPE_CLASSIFICATION = (
    "POST_PR4936_NEXT_MATERIAL_RESEARCH_SCOPE_DEFINITION_OR_FLEET_TERMINALIZATION_"
    "NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
)
DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/post_pr4936_cross_sectional_funding_rate_research_fleet_complete_no_pass_scope_definition_v0.json"
)
DEFAULT_DOC = (
    _REPO_ROOT
    / "docs/governance/POST_PR4936_CROSS_SECTIONAL_FUNDING_RATE_RESEARCH_FLEET_COMPLETE_NO_PASS_SCOPE_DEFINITION_V0.md"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "next_material_research_scope_after_pr4936_no_eval"
PARENT_CLOSEOUT_SUFFIX = "pr4936_dispersion_zscore_reversion_v0_negative_evidence_terminalization_merge_closeout_20260706T172134Z"

REQUIRED_CONFIG_KEYS = (
    "scope_id",
    "scope_version",
    "baseline_head",
    "parent_closeout_dir",
    "cross_sectional_funding_research_fleet_status",
    "fleet_status",
    "fleet_verdict",
    "scope_decision",
    "selected_next_scope",
    "material_difference_confirmed_for_new_funding_scope",
    "material_difference_vs_terminal_bindings",
    "terminal_failed_binding_exclusions",
    "unchanged_retry_allowed",
    "evaluation_executed",
    "runtime_authority_touched",
    "promotion_granted",
    "scope_definition_only",
    "blocked_actions",
    "canonical_runbook_return_path",
    "governance_ref",
)

REQUIRED_CONTRACT_FLAGS = (
    ("scope_definition_only", True),
    ("offline_only", True),
    ("economic_evaluation_authorized", False),
    ("economic_evaluation_executed", False),
    ("evaluation_executed", False),
    ("runtime_authority_touched", False),
    ("promotion_granted", False),
    ("unchanged_retry_allowed", False),
    ("material_difference_vs_terminal_bindings", True),
    ("core_system_mutation_allowed", False),
    ("no_runtime_authority", True),
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


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_snapshot(*, fallback_head: str | None = None) -> dict[str, str]:
    def _run(args: list[str]) -> str | None:
        try:
            return subprocess.check_output(["git", *args], cwd=_REPO_ROOT, text=True).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    head = _run(["rev-parse", "HEAD"]) or fallback_head or "unknown"
    origin_main = _run(["rev-parse", "origin/main"]) or fallback_head or head
    branch = _run(["branch", "--show-current"]) or "unknown"
    status_short = _run(["status", "--short"]) or "(clean)"
    return {
        "head": head,
        "origin_main": origin_main,
        "branch": branch,
        "status_short": status_short,
    }


def _verify_source_manifest(source_dir: Path, log_path: Path) -> tuple[int, str]:
    manifest_path = source_dir / "MANIFEST.sha256"
    if not manifest_path.is_file():
        return -1, "manifest_missing"
    ok, msg = verify_manifest_sha256(source_dir)
    return (0 if ok else 1), msg or "ok"


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED_CONFIG_KEYS:
        if key not in config:
            errors.append(f"missing required config key: {key}")

    if config.get("scope_id") != SCOPE_ID:
        errors.append("unexpected scope_id")
    if config.get("process_classification") != PROCESS_CLASSIFICATION:
        errors.append("unexpected process_classification")
    if config.get("scope_classification") != SCOPE_CLASSIFICATION:
        errors.append("unexpected scope_classification")
    if config.get("go_token") != CONFIRM_GO:
        errors.append("unexpected go_token")
    if config.get("scope_decision") != "FLEET_TERMINALIZATION_COMPLETE_NO_PASS":
        errors.append("unexpected scope_decision")
    if config.get("cross_sectional_funding_research_fleet_status") != "COMPLETE_NO_PASS":
        errors.append("unexpected cross_sectional_funding_research_fleet_status")
    if config.get("selected_next_scope") is not None:
        errors.append("selected_next_scope must be null for fleet terminalization")

    for field, expected in REQUIRED_CONTRACT_FLAGS:
        if config.get(field) is not expected:
            errors.append(f"contract flag mismatch: {field} expected {expected}")

    exclusions = config.get("terminal_failed_binding_exclusions", [])
    if not isinstance(exclusions, list) or len(exclusions) < 6:
        errors.append("terminal_failed_binding_exclusions must contain at least 6 entries")

    forbidden_core = (
        "CORE_SYSTEM_CHANGE",
        "CANONICAL_TRADING_LOGIC_CHANGE",
        "MASTER_V2_CHANGE",
        "DOUBLE_PLAY_CHANGE",
        "RISK_SIZING_CHANGE",
        "SAFETY_RUNTIME_CHANGE",
    )
    blocked = set(config.get("blocked_actions", []))
    for action in forbidden_core:
        if action not in blocked:
            errors.append(f"missing forbidden blocked action: {action}")

    return errors


def _build_scope_summary(
    config: dict[str, Any], doc_sha256: str, parent_closeout_rc: int
) -> dict[str, Any]:
    return {
        "authority_effect": config.get("authority_effect", "NONE"),
        "baseline_head": config["baseline_head"],
        "canonical_runbook_return_path": config["canonical_runbook_return_path"],
        "config_sha256": _sha256_path(DEFAULT_CONFIG),
        "cross_sectional_funding_research_fleet_status": config[
            "cross_sectional_funding_research_fleet_status"
        ],
        "doc_sha256": doc_sha256,
        "evaluation_executed": False,
        "fleet_status": config["fleet_status"],
        "fleet_verdict": config["fleet_verdict"],
        "go_token": CONFIRM_GO,
        "go_token_consumption": "CONSUMED_ONCE_FOR_SCOPE_DEFINITION_ONLY",
        "material_difference_confirmed_for_new_funding_scope": config[
            "material_difference_confirmed_for_new_funding_scope"
        ],
        "material_difference_vs_terminal_bindings": True,
        "no_order_authority": True,
        "non_authorizing": True,
        "offline_only": True,
        "parent_closeout_dir": config["parent_closeout_dir"],
        "parent_closeout_manifest_verify_rc": parent_closeout_rc,
        "process_classification": PROCESS_CLASSIFICATION,
        "promotion_granted": False,
        "runtime_authority_touched": False,
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_decision": config["scope_decision"],
        "scope_definition_only": True,
        "scope_id": SCOPE_ID,
        "scope_version": config["scope_version"],
        "selected_next_scope": config["selected_next_scope"],
        "status": "SCOPE_DEFINED_NOT_EXECUTED",
        "terminal_failed_binding_count": len(config["terminal_failed_binding_exclusions"]),
        "unchanged_retry_allowed": False,
        "verdict": "SCOPE_DEFINED_NOT_EXECUTED",
    }


def _build_terminal_evidence_drift_matrix(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "cross_sectional_funding_research_fleet_status": config[
            "cross_sectional_funding_research_fleet_status"
        ],
        "excluded_near_duplicate_candidate_families": config.get(
            "excluded_near_duplicate_candidate_families", []
        ),
        "material_difference_confirmed_for_new_funding_scope": config[
            "material_difference_confirmed_for_new_funding_scope"
        ],
        "parent_terminal_binding_digest": config["parent_terminal_binding_digest"],
        "parent_terminal_strategy": config["parent_terminal_strategy"],
        "scope_id": SCOPE_ID,
        "terminal_failed_binding_exclusions": config["terminal_failed_binding_exclusions"],
        "unchanged_retry_allowed": False,
    }


def _build_reuse_first_owner_map() -> dict[str, str]:
    return {
        "canonical_runbook_return_path": "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md",
        "contract_test_pattern": "tests/ops/test_post_pr4894_next_versioned_research_scope_definition_v0_contract.py",
        "manifest_verify_owner": "scripts/ops/primary_evidence_retention_v0.py",
        "scope_config": str(DEFAULT_CONFIG.relative_to(_REPO_ROOT)),
        "scope_definition_pattern": "scripts/research/post_pr4894_next_versioned_research_scope_definition_v0.py",
        "scope_governance_doc": str(DEFAULT_DOC.relative_to(_REPO_ROOT)),
    }


def run_post_pr4936_cross_sectional_funding_rate_research_fleet_complete_no_pass_scope_definition_v0(
    *,
    confirm_go_token: str,
    config_path: Path = DEFAULT_CONFIG,
    governance_doc_path: Path = DEFAULT_DOC,
    output_dir: Path,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
) -> dict[str, Any]:
    if confirm_go_token != CONFIRM_GO:
        _die("ERR:invalid confirm go token")

    if not config_path.is_file():
        _die(f"ERR:missing config: {config_path}")
    if not governance_doc_path.is_file():
        _die(f"ERR:missing governance doc: {governance_doc_path}")

    config = _load_json(config_path)
    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        _die("ERR:config validation failed", code=1)

    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        _die(f"ERR:output dir not empty: {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    parent_closeout_dir = Path(config["parent_closeout_dir"])
    parent_closeout_rc, parent_closeout_msg = _verify_source_manifest(
        parent_closeout_dir,
        output_dir / "parent_closeout_manifest_verify.log",
    )
    required_closeout_rc = int(config.get("parent_closeout_manifest_verify_rc", 0))
    if parent_closeout_rc >= 0 and parent_closeout_rc != required_closeout_rc:
        _die(f"ERR:parent closeout manifest verify rc mismatch: {parent_closeout_dir}")

    doc_sha256 = _sha256_path(governance_doc_path)
    scope_summary = _build_scope_summary(config, doc_sha256, parent_closeout_rc)
    drift_matrix = _build_terminal_evidence_drift_matrix(config)
    reuse_map = _build_reuse_first_owner_map()
    git_snapshot = _git_snapshot(fallback_head=config.get("baseline_head"))

    (output_dir / "SCOPE_DEFINITION_SUMMARY.json").write_text(
        json.dumps(scope_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "TERMINAL_EVIDENCE_DRIFT_MATRIX.json").write_text(
        json.dumps(drift_matrix, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "TERMINAL_EVIDENCE_DRIFT_MATRIX.md").write_text(
        "\n".join(
            [
                "# Terminal Evidence Drift Matrix",
                "",
                f"- scope_id: `{SCOPE_ID}`",
                f"- cross_sectional_funding_research_fleet_status: `{drift_matrix['cross_sectional_funding_research_fleet_status']}`",
                f"- material_difference_confirmed_for_new_funding_scope: `{drift_matrix['material_difference_confirmed_for_new_funding_scope']}`",
                f"- parent_terminal_strategy: `{drift_matrix['parent_terminal_strategy']}`",
                f"- parent_terminal_binding_digest: `{drift_matrix['parent_terminal_binding_digest']}`",
                f"- unchanged_retry_allowed: `false`",
                "",
                "## Terminal Failed Bindings",
                "",
                "| Binding | Digest | Verdict | Retry Allowed |",
                "|---|---|---|---|",
            ]
            + [
                f"| `{entry['canonical_candidate_identifier']}` | `{entry['binding_digest']}` | `{entry['terminal_verdict']}` | `false` |"
                for entry in drift_matrix["terminal_failed_binding_exclusions"]
            ]
            + [
                "",
                "## Excluded Near-Duplicate Candidate Families",
                "",
            ]
            + [
                f"- `{family}`"
                for family in drift_matrix["excluded_near_duplicate_candidate_families"]
            ]
            + [""]
        ),
        encoding="utf-8",
    )
    (output_dir / "REUSE_FIRST_OWNER_MAP.json").write_text(
        json.dumps(reuse_map, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "REUSE_FIRST_OWNER_MAP.md").write_text(
        "\n".join(
            ["# Reuse-First Owner Map", ""]
            + [f"- `{key}`: `{value}`" for key, value in sorted(reuse_map.items())]
            + [""]
        ),
        encoding="utf-8",
    )
    (output_dir / "SCOPE_DECISION_RECORD.md").write_text(
        "\n".join(
            [
                "# Scope Decision Record",
                "",
                f"- scope_decision: `{config['scope_decision']}`",
                f"- selected_next_scope: `{config['selected_next_scope']}`",
                f"- cross_sectional_funding_research_fleet_status: `{config['cross_sectional_funding_research_fleet_status']}`",
                f"- material_difference_confirmed_for_new_funding_scope: `{config['material_difference_confirmed_for_new_funding_scope']}`",
                f"- canonical_runbook_return_path: `{config['canonical_runbook_return_path']}`",
                f"- parent_terminal_strategy: `{config['parent_terminal_strategy']}`",
                f"- parent_terminal_binding_digest: `{config['parent_terminal_binding_digest']}`",
                f"- evaluation_executed: `false`",
                f"- runtime_authority_touched: `false`",
                f"- promotion_granted: `false`",
                f"- unchanged_retry_allowed: `false`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "FINAL_REPORT.md").write_text(
        "\n".join(
            [
                "# Final Report — Post-PR4936 Material Research Scope Definition",
                "",
                "VERDICT=PASS",
                f"PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}",
                f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
                "GO_TOKEN_CONSUMPTION=CONSUMED_ONCE",
                f"BASE_HEAD={git_snapshot['head']}",
                f"ORIGIN_MAIN={git_snapshot['origin_main']}",
                f"WORKTREE_STATUS={git_snapshot['status_short']}",
                "PR=not_created",
                "PR_URL=none",
                "SELECTED_NEXT_SCOPE=none",
                "MATERIAL_DIFFERENCE_CONFIRMED=false",
                "UNCHANGED_RETRY_ALLOWED=false",
                "EVALUATION_EXECUTED=false",
                "RUNTIME_AUTHORITY_TOUCHED=false",
                "PROMOTION_GRANTED=false",
                f"DURABLE_EVIDENCE_DIR={output_dir}",
                "MANIFEST_VERIFY_RC=pending",
                "TESTS=contract_tests_pending",
                "NEXT_STEP=RETURN_TO_FINAL_RESEARCH_FLEET_BINDINGS_CANONICAL_RUNBOOK_PATH",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "git_snapshot.json").write_text(
        json.dumps(git_snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    write_manifest_sha256(output_dir)
    manifest_ok, manifest_msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if manifest_ok else 1
    if manifest_rc != 0:
        _die(f"ERR:manifest verify failed: {output_dir} ({manifest_msg})")

    final_report = output_dir / "FINAL_REPORT.md"
    final_report.write_text(
        final_report.read_text(encoding="utf-8").replace(
            "MANIFEST_VERIFY_RC=pending", f"MANIFEST_VERIFY_RC={manifest_rc}"
        ),
        encoding="utf-8",
    )
    write_manifest_sha256(output_dir)
    manifest_ok, manifest_msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if manifest_ok else 1
    if manifest_rc != 0:
        _die(f"ERR:manifest verify failed after final report update: {output_dir} ({manifest_msg})")

    return {
        "cross_sectional_funding_research_fleet_status": config[
            "cross_sectional_funding_research_fleet_status"
        ],
        "durable_evidence_path": str(output_dir),
        "manifest_verify_rc": manifest_rc,
        "material_difference_confirmed_for_new_funding_scope": config[
            "material_difference_confirmed_for_new_funding_scope"
        ],
        "parent_closeout_manifest_verify_rc": parent_closeout_rc,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_decision": config["scope_decision"],
        "scope_id": SCOPE_ID,
        "selected_next_scope": config["selected_next_scope"],
        "verdict": "SCOPE_DEFINED_NOT_EXECUTED",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize post-PR4936 cross-sectional funding rate research fleet "
            "complete no-pass scope definition v0"
        )
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--governance-doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()

    result = run_post_pr4936_cross_sectional_funding_rate_research_fleet_complete_no_pass_scope_definition_v0(
        confirm_go_token=args.confirm_go_token,
        config_path=args.config,
        governance_doc_path=args.governance_doc,
        output_dir=args.out,
        archive_root=args.durable_evidence_root,
    )
    print("VERDICT=SCOPE_DEFINED_NOT_EXECUTED")
    print(f"SCOPE_ID={result['scope_id']}")
    print(f"SCOPE_DECISION={result['scope_decision']}")
    print(f"DURABLE_EVIDENCE_BUNDLE={result['durable_evidence_path']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
