#!/usr/bin/env python3
"""Materialize post-PR4940 final research fleet negative evidence terminalization v0.

Offline-only current-state binding and next material research boundary evidence bundle.
No economic evaluation, no binding retry, no runtime authority.
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
from src.research.post_pr4940_final_research_fleet_negative_evidence_terminalization_and_next_material_research_boundary_v0 import (  # noqa: E402
    GO_TOKEN,
    NEXT_ADMISSIBLE_BOUNDARY,
    POST_MERGE_HEAD,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    VERDICT,
    validate_boundary_config_v0,
)

CONFIRM_GO = GO_TOKEN
DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/post_pr4940_final_research_fleet_negative_evidence_terminalization_"
    "and_next_material_research_boundary_v0.json"
)
DEFAULT_DOC = (
    _REPO_ROOT
    / "docs/governance/POST_PR4939_FINAL_RESEARCH_FLEET_NEGATIVE_EVIDENCE_TERMINALIZATION_"
    "AND_NEXT_MATERIAL_RESEARCH_BOUNDARY_V0.md"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "pr4940_final_fleet_terminalization_and_next_material_research_boundary"

REQUIRED_CONFIG_KEYS = (
    "scope_id",
    "scope_version",
    "post_merge_head",
    "parent_evaluation_evidence_dir",
    "parent_pr4938_closeout_dir",
    "final_research_fleet",
    "candidate_results",
    "aggregate_fleet_verdict",
    "fleet_status",
    "fleet_verdict",
    "negative_evidence_terminal_for_unchanged_bindings",
    "next_admissible_boundary",
    "selected_next_scope",
    "terminal_failed_binding_exclusions",
    "unchanged_retry_allowed",
    "evaluation_executed",
    "runtime_authority_touched",
    "promotion_granted",
    "scope_definition_only",
    "blocked_actions",
    "governance_ref",
)

REQUIRED_CONTRACT_FLAGS = (
    ("scope_definition_only", True),
    ("current_state_binding_only", True),
    ("offline_only", True),
    ("economic_evaluation_authorized", False),
    ("economic_evaluation_executed", False),
    ("evaluation_executed", False),
    ("runtime_authority_touched", False),
    ("promotion_granted", False),
    ("unchanged_retry_allowed", False),
    ("negative_evidence_terminal_for_unchanged_bindings", True),
    ("economic_validity_offline_gate_pass", False),
    ("runtime_rewire_admissible", False),
    ("live_authorized", False),
    ("no_runtime_authority", True),
    ("next_admissible_boundary_placeholder_only", True),
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


def _verify_source_manifest(source_dir: Path) -> tuple[int, str]:
    manifest_path = source_dir / "MANIFEST.sha256"
    if not manifest_path.is_file():
        return -1, "manifest_missing"
    ok, msg = verify_manifest_sha256(source_dir)
    return (0 if ok else 1), msg or "ok"


def validate_config(config: dict[str, Any]) -> list[str]:
    validation = validate_boundary_config_v0(config, repo_root=_REPO_ROOT)
    errors = list(validation.reasons)

    for key in REQUIRED_CONFIG_KEYS:
        if key not in config:
            errors.append(f"missing required config key: {key}")

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


def _build_boundary_summary(
    config: dict[str, Any], doc_sha256: str, parent_eval_rc: int, parent_closeout_rc: int
) -> dict[str, Any]:
    return {
        "aggregate_fleet_verdict": config["aggregate_fleet_verdict"],
        "authority_effect": config.get("authority_effect", "NONE"),
        "candidate_results": config["candidate_results"],
        "config_sha256": _sha256_path(DEFAULT_CONFIG),
        "doc_sha256": doc_sha256,
        "economic_validity_offline_gate_pass": config["economic_validity_offline_gate_pass"],
        "evaluation_executed": False,
        "final_research_fleet": config["final_research_fleet"],
        "final_research_fleet_status": config["final_research_fleet_status"],
        "go_token": CONFIRM_GO,
        "go_token_consumption": config["go_token_consumption"],
        "negative_evidence_terminal_for_unchanged_bindings": config[
            "negative_evidence_terminal_for_unchanged_bindings"
        ],
        "next_admissible_boundary": config["next_admissible_boundary"],
        "no_order_authority": True,
        "non_authorizing": True,
        "offline_only": True,
        "parent_evaluation_evidence_dir": config["parent_evaluation_evidence_dir"],
        "parent_evaluation_manifest_verify_rc": parent_eval_rc,
        "parent_pr4938_closeout_dir": config["parent_pr4938_closeout_dir"],
        "parent_pr4938_closeout_manifest_verify_rc": parent_closeout_rc,
        "post_merge_head": config["post_merge_head"],
        "process_classification": PROCESS_CLASSIFICATION,
        "promotion_granted": False,
        "runtime_authority_touched": False,
        "runtime_rewire_admissible": config["runtime_rewire_admissible"],
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_definition_only": True,
        "scope_id": SCOPE_ID,
        "scope_version": config["scope_version"],
        "selected_next_scope": config["selected_next_scope"],
        "status": VERDICT,
        "terminal_failed_binding_count": len(config["terminal_failed_binding_exclusions"]),
        "unchanged_retry_allowed": False,
        "verdict": VERDICT,
    }


def _build_terminal_evidence_drift_matrix(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "aggregate_fleet_verdict": config["aggregate_fleet_verdict"],
        "candidate_results": config["candidate_results"],
        "final_research_fleet_status": config["final_research_fleet_status"],
        "negative_evidence_terminal_for_unchanged_bindings": config[
            "negative_evidence_terminal_for_unchanged_bindings"
        ],
        "next_admissible_boundary": config["next_admissible_boundary"],
        "scope_id": SCOPE_ID,
        "terminal_failed_binding_exclusions": config["terminal_failed_binding_exclusions"],
        "unchanged_retry_allowed": False,
    }


def _build_reuse_first_owner_map() -> dict[str, str]:
    return {
        "boundary_validation_owner": str(
            Path(
                "src/research/post_pr4940_final_research_fleet_negative_evidence_"
                "terminalization_and_next_material_research_boundary_v0.py"
            )
        ),
        "contract_test_pattern": (
            "tests/ops/test_post_pr4936_cross_sectional_funding_rate_research_fleet_"
            "complete_no_pass_scope_definition_v0_contract.py"
        ),
        "manifest_verify_owner": "scripts/ops/primary_evidence_retention_v0.py",
        "parent_evaluation_owner": (
            "src/research/post_pr4938_final_research_fleet_offline_economic_evaluation_"
            "execution_v0.py"
        ),
        "progress_registry": "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md",
        "scope_config": str(DEFAULT_CONFIG.relative_to(_REPO_ROOT)),
        "scope_definition_pattern": (
            "scripts/research/post_pr4936_cross_sectional_funding_rate_research_fleet_"
            "complete_no_pass_scope_definition_v0.py"
        ),
        "scope_governance_doc": str(DEFAULT_DOC.relative_to(_REPO_ROOT)),
    }


def run_post_pr4940_final_research_fleet_negative_evidence_terminalization_and_next_material_research_boundary_v0(
    *,
    confirm_go_token: str,
    config_path: Path = DEFAULT_CONFIG,
    governance_doc_path: Path = DEFAULT_DOC,
    output_dir: Path,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
) -> dict[str, Any]:
    del archive_root
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

    parent_eval_dir = Path(config["parent_evaluation_evidence_dir"])
    parent_closeout_dir = Path(config["parent_pr4938_closeout_dir"])
    parent_eval_rc, _ = _verify_source_manifest(parent_eval_dir)
    parent_closeout_rc, _ = _verify_source_manifest(parent_closeout_dir)
    if parent_eval_rc != int(config.get("parent_evaluation_manifest_verify_rc", 0)):
        _die(f"ERR:parent evaluation manifest verify rc mismatch: {parent_eval_dir}")
    if parent_closeout_rc != int(config.get("parent_pr4938_closeout_manifest_verify_rc", 0)):
        _die(f"ERR:parent closeout manifest verify rc mismatch: {parent_closeout_dir}")

    doc_sha256 = _sha256_path(governance_doc_path)
    boundary_summary = _build_boundary_summary(
        config, doc_sha256, parent_eval_rc, parent_closeout_rc
    )
    drift_matrix = _build_terminal_evidence_drift_matrix(config)
    reuse_map = _build_reuse_first_owner_map()
    git_snapshot = _git_snapshot(fallback_head=config.get("post_merge_head"))

    (output_dir / "BOUNDARY_DEFINITION_SUMMARY.json").write_text(
        json.dumps(boundary_summary, indent=2, sort_keys=True) + "\n",
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
                f"- final_research_fleet_status: `{drift_matrix['final_research_fleet_status']}`",
                f"- aggregate_fleet_verdict: `{drift_matrix['aggregate_fleet_verdict']}`",
                f"- negative_evidence_terminal_for_unchanged_bindings: `true`",
                f"- next_admissible_boundary: `{drift_matrix['next_admissible_boundary']}`",
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
    (output_dir / "CURRENT_STATE_BINDING_RECORD.md").write_text(
        "\n".join(
            [
                "# Current State Binding Record",
                "",
                f"- verdict: `{VERDICT}`",
                f"- post_merge_head: `{config['post_merge_head']}`",
                f"- aggregate_fleet_verdict: `{config['aggregate_fleet_verdict']}`",
                f"- economic_validity_offline_gate_pass: `false`",
                f"- negative_evidence_terminal_for_unchanged_bindings: `true`",
                f"- next_admissible_boundary: `{config['next_admissible_boundary']}`",
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
                "# Final Report — Post-PR4940 Final Fleet Terminalization",
                "",
                f"VERDICT={VERDICT}",
                f"PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}",
                f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
                "GO_TOKEN_CONSUMPTION=CONSUMED_ONCE_FOR_CURRENT_STATE_BINDING_AND_BOUNDARY_DEFINITION_ONLY",
                f"BASE_HEAD={git_snapshot['head']}",
                f"ORIGIN_MAIN={git_snapshot['origin_main']}",
                f"WORKTREE_STATUS={git_snapshot['status_short']}",
                "PR=not_created",
                "PR_URL=none",
                f"POST_MERGE_HEAD={POST_MERGE_HEAD}",
                "FINAL_RESEARCH_FLEET=trend_following,bollinger_bands,momentum_1h",
                'CANDIDATE_RESULTS={"trend_following":"FAIL","bollinger_bands":"FAIL","momentum_1h":"FAIL"}',
                "AGGREGATE_FLEET_VERDICT=FLEET_ECONOMIC_VALIDITY_FAIL",
                "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false",
                "NEGATIVE_EVIDENCE_TERMINAL_FOR_UNCHANGED_BINDINGS=true",
                f"NEXT_ADMISSIBLE_BOUNDARY={NEXT_ADMISSIBLE_BOUNDARY}",
                "RUNTIME_AUTHORITY_TOUCHED=false",
                "PROMOTION_GRANTED=false",
                f"DURABLE_EVIDENCE_DIR={output_dir}",
                "MANIFEST_VERIFY_RC=pending",
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
        "aggregate_fleet_verdict": config["aggregate_fleet_verdict"],
        "candidate_results": config["candidate_results"],
        "durable_evidence_path": str(output_dir),
        "manifest_verify_rc": manifest_rc,
        "negative_evidence_terminal_for_unchanged_bindings": config[
            "negative_evidence_terminal_for_unchanged_bindings"
        ],
        "next_admissible_boundary": config["next_admissible_boundary"],
        "parent_evaluation_manifest_verify_rc": parent_eval_rc,
        "parent_pr4938_closeout_manifest_verify_rc": parent_closeout_rc,
        "post_merge_head": config["post_merge_head"],
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_id": SCOPE_ID,
        "selected_next_scope": config["selected_next_scope"],
        "verdict": VERDICT,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize post-PR4940 final research fleet negative evidence "
            "terminalization and next material research boundary v0"
        )
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--governance-doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()

    result = run_post_pr4940_final_research_fleet_negative_evidence_terminalization_and_next_material_research_boundary_v0(
        confirm_go_token=args.confirm_go_token,
        config_path=args.config,
        governance_doc_path=args.governance_doc,
        output_dir=args.out,
        archive_root=args.durable_evidence_root,
    )
    print(f"VERDICT={VERDICT}")
    print(f"SCOPE_ID={result['scope_id']}")
    print(f"NEXT_ADMISSIBLE_BOUNDARY={result['next_admissible_boundary']}")
    print(f"DURABLE_EVIDENCE_BUNDLE={result['durable_evidence_path']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
