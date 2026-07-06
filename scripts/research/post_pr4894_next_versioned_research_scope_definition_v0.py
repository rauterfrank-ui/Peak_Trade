#!/usr/bin/env python3
"""Materialize post-PR4894 next versioned research scope definition v0.

Offline-only scope-definition evidence bundle. No economic evaluation, no binding ratification,
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

CONFIRM_GO = (
    "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_V0"
)
SCOPE_ID = "POST_PR4894_NEXT_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0"
PROCESS_CLASSIFICATION = "NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_V0"
SCOPE_CLASSIFICATION = (
    "POST_PR4894_NEXT_VERSIONED_RESEARCH_SCOPE_OR_EVIDENCE_CLASS_DEFINITION_ONLY_AFTER_"
    "ROOT_CAUSE_DECOMPOSITION_V0"
)
DEFAULT_CONFIG = (
    _REPO_ROOT / "config/research/post_pr4894_next_versioned_research_scope_definition_v0.json"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "post_pr4894_next_scope_definition_v0"
PARENT_DECOMPOSITION_BUNDLE_SUFFIX = (
    "post_pr4892_failed_fleet_robustness_root_cause_decomposition_evidence_v0_20260706T015337Z"
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


def _write_authority_boundary(output_dir: Path) -> None:
    output_dir.joinpath("AUTHORITY_BOUNDARY.txt").write_text(
        "\n".join(
            [
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "ECONOMIC_EVALUATION_AUTHORIZED=false",
                "BACKTEST_EXECUTED=false",
                "RUNTIME_AUTHORITY=NONE",
                "FAILED_BINDINGS_RETRY_ALLOWED=false",
                "NEW_CANDIDATE_RATIFIED=false",
                "PROMOTION_AUTHORITY=false",
                "SHADOW_AUTHORIZED=false",
                "PAPER_AUTHORIZED=false",
                "TESTNET_AUTHORIZED=false",
                "LIVE_AUTHORIZED=false",
                "BOUNDARIES=NO_RUNTIME_NO_SHADOW_NO_PAPER_NO_TESTNET_NO_ORDERS_NO_LIVE",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


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
    parent_ref = archive_root / "implementation" / PARENT_DECOMPOSITION_BUNDLE_SUFFIX
    if not parent_ref.is_dir():
        _die(f"ERR:missing parent decomposition evidence ref: {parent_ref}")

    output_dir = archive_root / "implementation" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    output_dir.mkdir(parents=True, exist_ok=False)

    parent_manifest_rc = _verify_source_manifest(
        parent_ref,
        output_dir / "parent_decomposition_manifest_verify.log",
    )
    if parent_manifest_rc != 0:
        _die(f"ERR:parent decomposition manifest invalid: {parent_ref}")

    git_snapshot = _git_snapshot()
    (output_dir / "scope_definition_v0.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "git_snapshot.json").write_text(
        json.dumps(git_snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "go_token_consumption.json").write_text(
        json.dumps(
            {
                "consumed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "go_token": CONFIRM_GO,
                "go_token_consumed": True,
                "go_token_consumption": "CONSUMED_ONCE_FOR_SCOPE_DEFINITION_ONLY",
                "scope_id": SCOPE_ID,
                "process_classification": PROCESS_CLASSIFICATION,
                "scope_classification": SCOPE_CLASSIFICATION,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    commands = [
        f"python3 {__file__} --confirm-go-token {CONFIRM_GO}",
        f"PARENT_DECOMPOSITION_REF={parent_ref}",
        f"OUTPUT_DIR={output_dir}",
    ]
    (output_dir / "COMMAND_LOG.md").write_text(
        "\n".join(["# Command Log", ""] + [f"- `{line}`" for line in commands]) + "\n",
        encoding="utf-8",
    )
    (output_dir / "SCOPE_DEFINITION_REPORT.md").write_text(
        "\n".join(
            [
                "# Scope Definition Report",
                "",
                f"- scope_id: `{SCOPE_ID}`",
                f"- process_classification: `{PROCESS_CLASSIFICATION}`",
                f"- scope_classification: `{SCOPE_CLASSIFICATION}`",
                f"- selected_class: `{config.get('selected_class')}`",
                f"- fleet_verdict: `{config.get('fleet_verdict')}`",
                f"- final_research_fleet: `{','.join(config.get('final_research_fleet', []))}`",
                f"- economic_validity_offline_gate_pass: `{config.get('economic_validity_offline_gate_pass')}`",
                f"- panel_zero_trade_refuted: `{config.get('panel_zero_trade_refuted')}`",
                f"- required_next_go_for_binding_ratification: `{config.get('required_next_go_for_binding_ratification')}`",
                f"- parent_decomposition_manifest_verify_rc: `{parent_manifest_rc}`",
                f"- verdict: `SCOPE_DEFINED_NOT_EXECUTED`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_authority_boundary(output_dir)

    write_manifest_sha256(output_dir)
    manifest_rc = 0 if verify_manifest_sha256(output_dir)[0] else 1
    if manifest_rc != 0:
        _die(f"ERR:manifest verify failed: {output_dir}")

    return {
        "verdict": "SCOPE_DEFINED_NOT_EXECUTED",
        "scope_id": SCOPE_ID,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "durable_evidence_path": str(output_dir),
        "manifest_verify_rc": manifest_rc,
        "parent_decomposition_manifest_verify_rc": parent_manifest_rc,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize post-PR4894 next versioned research scope definition v0"
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()

    result = run_scope_definition_materialization_v0(
        confirm_go_token=args.confirm_go_token,
        archive_root=args.durable_evidence_root,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    for key, value in result.items():
        print(f"{key.upper()}={value}")


if __name__ == "__main__":
    main()
