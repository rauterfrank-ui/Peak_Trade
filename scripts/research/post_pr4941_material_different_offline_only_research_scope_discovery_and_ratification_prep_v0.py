#!/usr/bin/env python3
"""Materialize post-PR4941 material-different offline-only research scope discovery v0.

Offline-only discovery/ratification-prep evidence bundle. No economic evaluation,
no binding ratification, no runtime authority.
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
from src.research.post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep_v0 import (  # noqa: E402
    BASE_HEAD,
    GO_TOKEN,
    PROCESS_CLASSIFICATION,
    REQUIRED_MATERIAL_DIFFERENCE_AXES,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    SELECTED_NEXT_SCOPE_BOUNDARY,
    VERDICT,
    validate_discovery_config_v0,
)

CONFIRM_GO = GO_TOKEN
DEFAULT_CONFIG = (
    _REPO_ROOT / "config/research/post_pr4941_material_different_offline_only_research_scope_"
    "discovery_and_ratification_prep_v0.json"
)
DEFAULT_DOC = (
    _REPO_ROOT / "docs/governance/POST_PR4941_MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_"
    "DISCOVERY_AND_RATIFICATION_PREP_V0.md"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = (
    "pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep"
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
    if not (source_dir / "MANIFEST.sha256").is_file():
        return -1, "manifest_missing"
    ok, msg = verify_manifest_sha256(source_dir)
    return (0 if ok else 1), msg or "ok"


def validate_config(config: dict[str, Any]) -> list[str]:
    validation = validate_discovery_config_v0(config, repo_root=_REPO_ROOT)
    return list(validation.reasons)


def _build_failed_binding_exclusion_matrix(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "aggregate_fleet_verdict": "FLEET_ECONOMIC_VALIDITY_FAIL",
        "economic_validity_offline_gate_pass": False,
        "excluded_failed_bindings": config["excluded_failed_bindings"],
        "final_research_fleet": config["final_research_fleet"],
        "negative_evidence_terminal_for_unchanged_bindings": True,
        "unchanged_retry_allowed": False,
    }


def _build_material_difference_matrix(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "material_difference_axes": config["material_difference_axes"],
        "material_difference_confirmed": True,
        "near_duplicate_archetype_blocked": True,
        "selected_next_scope_boundary": config["selected_next_scope_boundary"],
        "threshold_lowering_blocked": True,
    }


def _build_reuse_first_matrix(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "narrow_adapter_need": "realized_vol_feature_from_panel_ohlcv_only",
        "panel_dataset_owner": "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1",
        "ranking_semantics_pattern_owner": (
            "config/research/cross_sectional_relative_strength_non_bitcoin_perpetuals_v0_"
            "ranking_semantics_binding_v0.json"
        ),
        "reuse_first_decision": config["reuse_first_decision"],
        "scope_ratification_pattern_owner": "cross_sectional_funding_rate_research_scope_ratification_v0_family",
    }


def run_post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep_v0(
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

    pr4939_dir = Path(config["parent_pr4939_closeout_dir"])
    pr4940_dir = Path(config["parent_pr4940_closeout_dir"])
    pr4939_rc, pr4939_msg = _verify_source_manifest(pr4939_dir)
    pr4940_rc, pr4940_msg = _verify_source_manifest(pr4940_dir)
    if pr4939_rc != int(config.get("parent_pr4939_closeout_manifest_verify_rc", 0)):
        _die(f"ERR:pr4939 closeout manifest verify rc mismatch: {pr4939_dir}")
    if pr4940_rc != int(config.get("parent_pr4940_closeout_manifest_verify_rc", 0)):
        _die(f"ERR:pr4940 closeout manifest verify rc mismatch: {pr4940_dir}")

    git_snapshot = _git_snapshot(fallback_head=config.get("baseline_head"))
    exclusion_matrix = _build_failed_binding_exclusion_matrix(config)
    material_matrix = _build_material_difference_matrix(config)
    reuse_matrix = _build_reuse_first_matrix(config)

    (output_dir / "git_context.txt").write_text(
        "\n".join(
            [
                f"HEAD={git_snapshot['head']}",
                f"ORIGIN_MAIN={git_snapshot['origin_main']}",
                f"BRANCH={git_snapshot['branch']}",
                f"STATUS={git_snapshot['status_short']}",
                f"BASE_HEAD={BASE_HEAD}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "pr4939_closeout_manifest_verify.log").write_text(
        f"dir={pr4939_dir}\nrc={pr4939_rc}\nmsg={pr4939_msg}\n",
        encoding="utf-8",
    )
    (output_dir / "pr4940_closeout_manifest_verify.log").write_text(
        f"dir={pr4940_dir}\nrc={pr4940_rc}\nmsg={pr4940_msg}\n",
        encoding="utf-8",
    )
    (output_dir / "FAILED_BINDING_EXCLUSION_MATRIX.json").write_text(
        json.dumps(exclusion_matrix, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "MATERIAL_DIFFERENCE_MATRIX.json").write_text(
        json.dumps(material_matrix, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "REUSE_FIRST_MATRIX.json").write_text(
        json.dumps(reuse_matrix, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "CANDIDATE_FAMILY_INVENTORY.json").write_text(
        json.dumps(config["candidate_family_inventory"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "SELECTED_NEXT_SCOPE_BOUNDARY.md").write_text(
        "\n".join(
            [
                "# Selected Next Scope Boundary",
                "",
                f"- selected_next_scope_boundary: `{config['selected_next_scope_boundary']}`",
                f"- selected_strategy_id: `{config['selected_strategy_id']}`",
                f"- selected_strategy_version: `{config['selected_strategy_version']}`",
                f"- reuse_first_decision: `{config['reuse_first_decision']}`",
                f"- required_next_go_for_scope_ratification: `{config['required_next_go_for_scope_ratification']}`",
                "",
                "## Material Difference Axes",
                "",
            ]
            + [f"- `{axis}`" for axis in REQUIRED_MATERIAL_DIFFERENCE_AXES]
            + [""]
        ),
        encoding="utf-8",
    )
    (output_dir / "NO_EVAL_NO_RUNTIME_AUTHORITY_STATEMENT.md").write_text(
        "\n".join(
            [
                "# No-Eval / No-Runtime Authority Statement",
                "",
                "- evaluation_executed: `false`",
                "- economic_evaluation_authorized: `false`",
                "- runtime_authority_touched: `false`",
                "- promotion_granted: `false`",
                "- unchanged_retry_allowed: `false`",
                "- market_airport_excluded: `true`",
                "- scope_discovery_and_ratification_prep_only: `true`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (output_dir / "SCOPE_DISCOVERY_SUMMARY.json").write_text(
        json.dumps(
            {
                "config_sha256": _sha256_path(config_path),
                "doc_sha256": _sha256_path(governance_doc_path),
                "go_token": CONFIRM_GO,
                "go_token_consumption": config["go_token_consumption"],
                "material_difference_axes": config["material_difference_axes"],
                "process_classification": PROCESS_CLASSIFICATION,
                "scope_classification": SCOPE_CLASSIFICATION,
                "scope_id": SCOPE_ID,
                "selected_next_scope_boundary": config["selected_next_scope_boundary"],
                "status": VERDICT,
                "verdict": VERDICT,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "FINAL_REPORT.md").write_text(
        "\n".join(
            [
                f"VERDICT={VERDICT}",
                f"PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}",
                f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
                "GO_TOKEN_CONSUMPTION=CONSUMED_ONCE_FOR_DISCOVERY_AND_RATIFICATION_PREP_ONLY",
                f"BASE_HEAD={git_snapshot['head']}",
                f"ORIGIN_MAIN={git_snapshot['origin_main']}",
                f"WORKTREE_STATUS={git_snapshot['status_short']}",
                "PR=not_created",
                "PR_URL=none",
                f"SELECTED_NEXT_SCOPE_BOUNDARY={SELECTED_NEXT_SCOPE_BOUNDARY}",
                "EVALUATION_EXECUTED=false",
                "RUNTIME_AUTHORITY_TOUCHED=false",
                "PROMOTION_GRANTED=false",
                f"PR4939_MANIFEST_VERIFY_RC={pr4939_rc}",
                f"PR4940_MANIFEST_VERIFY_RC={pr4940_rc}",
                f"DURABLE_EVIDENCE_DIR={output_dir}",
                "MANIFEST_VERIFY_RC=pending",
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

    final_report = output_dir / "FINAL_REPORT.md"
    final_report.write_text(
        final_report.read_text(encoding="utf-8").replace(
            "MANIFEST_VERIFY_RC=pending", f"MANIFEST_VERIFY_RC={manifest_rc}"
        ),
        encoding="utf-8",
    )
    write_manifest_sha256(output_dir)
    ok, msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if ok else 1
    if manifest_rc != 0:
        _die(f"ERR:manifest verify failed after final report update: {output_dir} ({msg})")

    return {
        "durable_evidence_path": str(output_dir),
        "manifest_verify_rc": manifest_rc,
        "material_difference_axes": config["material_difference_axes"],
        "pr4939_manifest_verify_rc": pr4939_rc,
        "pr4940_manifest_verify_rc": pr4940_rc,
        "process_classification": PROCESS_CLASSIFICATION,
        "reuse_first_decision": config["reuse_first_decision"],
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_id": SCOPE_ID,
        "selected_next_scope_boundary": config["selected_next_scope_boundary"],
        "verdict": VERDICT,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize post-PR4941 material-different offline-only research scope "
            "discovery and ratification prep v0"
        )
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--governance-doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()

    result = run_post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep_v0(
        confirm_go_token=args.confirm_go_token,
        config_path=args.config,
        governance_doc_path=args.governance_doc,
        output_dir=args.out,
        archive_root=args.durable_evidence_root,
    )
    print(f"VERDICT={VERDICT}")
    print(f"SCOPE_ID={result['scope_id']}")
    print(f"SELECTED_NEXT_SCOPE_BOUNDARY={result['selected_next_scope_boundary']}")
    print(f"DURABLE_EVIDENCE_BUNDLE={result['durable_evidence_path']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
