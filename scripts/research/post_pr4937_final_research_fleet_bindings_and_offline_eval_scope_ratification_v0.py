#!/usr/bin/env python3
"""Materialize post-PR4937 final research fleet bindings and offline eval scope ratification v0.

Offline-only binding and scope ratification evidence bundle. No economic evaluation,
no backtest, walk-forward, Monte Carlo, stress, or runtime authority.
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
from src.research.post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    GO_TOKEN,
    NEXT_STEP,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    VERDICT,
    validate_ratification_config_v0,
)

CONFIRM_GO = GO_TOKEN

DEFAULT_CONFIG = _REPO_ROOT / CONFIG_REL_PATH
DEFAULT_DOC = (
    _REPO_ROOT
    / "docs/governance/FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFICATION_POST_PR4937_V0.md"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "final_research_fleet_bindings_and_offline_eval_scope_ratification"
PARENT_CLOSEOUT_SUFFIX = (
    "pr4937_cross_sectional_funding_research_fleet_complete_no_pass_merge_closeout_20260706T175340Z"
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


def _git_snapshot() -> dict[str, str]:
    def _run(args: list[str]) -> str:
        return subprocess.check_output(["git", *args], cwd=_REPO_ROOT, text=True).strip()

    return {
        "head": _run(["rev-parse", "HEAD"]),
        "origin_main": _run(["rev-parse", "origin/main"]),
        "branch": _run(["branch", "--show-current"]),
        "status_short": _run(["status", "--short"]) or "(clean)",
    }


def _verify_source_manifest(source_dir: Path) -> tuple[int, str]:
    if not source_dir.is_dir():
        return -1, "missing"
    ok, msg = verify_manifest_sha256(source_dir)
    return (0 if ok else 1), msg or "ok"


def run_post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0(
    *,
    confirm_go_token: str,
    config_path: Path = DEFAULT_CONFIG,
    governance_doc_path: Path = DEFAULT_DOC,
    output_dir: Path,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
) -> dict[str, Any]:
    if confirm_go_token != GO_TOKEN:
        _die("ERR:invalid confirm go token")

    if not config_path.is_file():
        _die(f"ERR:missing config: {config_path}")
    if not governance_doc_path.is_file():
        _die(f"ERR:missing governance doc: {governance_doc_path}")

    config = _load_json(config_path)
    validation = validate_ratification_config_v0(config, repo_root=_REPO_ROOT)
    if not validation.valid:
        for reason in validation.fail_reasons:
            print(f"ERROR: {reason}", file=sys.stderr)
        _die("ERR:config validation failed", code=1)

    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        _die(f"ERR:output dir not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    parent_closeout_dir = Path(config["parent_closeout_dir"])
    parent_closeout_rc, parent_closeout_msg = _verify_source_manifest(parent_closeout_dir)
    required_rc = int(config.get("parent_closeout_manifest_verify_rc", 0))
    if parent_closeout_rc >= 0 and parent_closeout_rc != required_rc:
        _die(f"ERR:parent closeout manifest verify rc mismatch: {parent_closeout_dir}")

    git_snapshot = _git_snapshot()
    doc_sha256 = _sha256_path(governance_doc_path)
    config_sha256 = _sha256_path(config_path)

    ratification_summary = {
        "authority_effect": config.get("authority_effect", "NONE"),
        "binding_ratification_only": True,
        "config_sha256": config_sha256,
        "doc_sha256": doc_sha256,
        "evaluation_executed": False,
        "evaluation_scope_ratified": True,
        "final_research_fleet": config["final_research_fleet"],
        "go_token": GO_TOKEN,
        "go_token_consumption": config.get("go_token_consumption"),
        "next_step": NEXT_STEP,
        "offline_economic_evaluation_scope_ratified": True,
        "parent_closeout_dir": str(parent_closeout_dir),
        "parent_closeout_manifest_verify_rc": parent_closeout_rc,
        "pr4937_terminalization_prerequisite": config["pr4937_terminalization_prerequisite"],
        "process_classification": PROCESS_CLASSIFICATION,
        "promotion_granted": False,
        "ratified_binding_count": len(config["ratified_bindings"]),
        "runtime_authority_touched": False,
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_id": SCOPE_ID,
        "status": VERDICT,
        "verdict": VERDICT,
    }

    authority_boundary = {
        "backtest_execution_authorized": False,
        "binding_ratification_only": True,
        "economic_evaluation_authorized": False,
        "evaluation_executed": False,
        "live_authorized": False,
        "monte_carlo_execution_authorized": False,
        "next_step": NEXT_STEP,
        "orders_allowed": False,
        "parameter_rescue_authorized": False,
        "promotion_granted": False,
        "result_rescue_authorized": False,
        "runtime_authority": "NONE",
        "runtime_rewire_admissible": False,
        "stress_execution_authorized": False,
        "threshold_lowering_authorized": False,
        "walk_forward_execution_authorized": False,
    }

    reuse_map = {
        "binding_completion_owner": config["binding_completion_owner_ref"],
        "contract_test": "tests/ops/test_post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0_contract.py",
        "manifest_verify_owner": "scripts/ops/primary_evidence_retention_v0.py",
        "offline_evaluation_scope_owner": config["offline_economic_evaluation_scope_owner_ref"],
        "parent_scope_config": config["parent_scope_config"],
        "parent_scope_doc": config["parent_scope_doc"],
        "ratification_config": str(config_path.relative_to(_REPO_ROOT)),
        "ratification_governance_doc": str(governance_doc_path.relative_to(_REPO_ROOT)),
        "ratification_module": "src/research/post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0.py",
    }

    (output_dir / "FINAL_RESEARCH_FLEET_BINDINGS_SCOPE_RATIFICATION.md").write_text(
        "\n".join(
            [
                "# Final Research Fleet Bindings and Offline Evaluation Scope Ratification",
                "",
                f"- scope_id: `{SCOPE_ID}`",
                f"- verdict: `{VERDICT}`",
                f"- final_research_fleet: `{config['final_research_fleet']}`",
                f"- evaluation_executed: `false`",
                f"- evaluation_scope_ratified: `true`",
                f"- runtime_authority_touched: `false`",
                f"- promotion_granted: `false`",
                f"- pr4937_fleet_terminalization: `{config['pr4937_terminalization_prerequisite']['fleet_terminalization']}`",
                "",
                "## Ratified Candidates",
                "",
            ]
            + [
                f"- `{binding['canonical_candidate_identifier']}` digest `{binding['binding_semantic_digest']}`"
                for binding in config["ratified_bindings"]
            ]
            + [
                "",
                "## Shared Offline Evaluation Scope",
                "",
                f"- evaluation_authorized: `false`",
                f"- allowed_future_actions_after_separate_go: `{','.join(config['allowed_future_actions_after_separate_go'])}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (output_dir / "RATIFICATION_SUMMARY.json").write_text(
        json.dumps(ratification_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "RATIFIED_BINDINGS.json").write_text(
        json.dumps(config["ratified_bindings"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "OFFLINE_EVALUATION_SCOPE.json").write_text(
        json.dumps(config["shared_offline_evaluation_scope"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "AUTHORITY_BOUNDARY.json").write_text(
        json.dumps(authority_boundary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "REUSE_FIRST_OWNER_MAP.json").write_text(
        json.dumps(reuse_map, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "git_context.txt").write_text(
        "\n".join(f"{key}={value}" for key, value in git_snapshot.items()) + "\n",
        encoding="utf-8",
    )
    (output_dir / "parent_closeout_manifest_verify.log").write_text(
        "\n".join(
            [
                f"PARENT_CLOSEOUT_DIR={parent_closeout_dir}",
                f"MANIFEST_VERIFY_RC={parent_closeout_rc}",
                f"MANIFEST_VERIFY_MSG={parent_closeout_msg}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    write_manifest_sha256(output_dir)
    ok, msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if ok else 1
    if manifest_rc != 0:
        _die(f"ERR:manifest verify failed: {output_dir} ({msg})")

    return {
        "durable_evidence_path": str(output_dir),
        "manifest_verify_rc": manifest_rc,
        "next_step": NEXT_STEP,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_id": SCOPE_ID,
        "verdict": VERDICT,
        "ratified_binding_count": len(config["ratified_bindings"]),
        "parent_closeout_manifest_verify_rc": parent_closeout_rc,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize post-PR4937 final research fleet bindings and offline "
            "evaluation scope ratification v0"
        )
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[GO_TOKEN])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--governance-doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()

    result = run_post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0(
        confirm_go_token=args.confirm_go_token,
        config_path=args.config,
        governance_doc_path=args.governance_doc,
        output_dir=args.out,
        archive_root=args.durable_evidence_root,
    )
    print(f"VERDICT={result['verdict']}")
    print(f"SCOPE_ID={result['scope_id']}")
    print(f"DURABLE_EVIDENCE_DIR={result['durable_evidence_path']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    print(f"NEXT_STEP={result['next_step']}")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
