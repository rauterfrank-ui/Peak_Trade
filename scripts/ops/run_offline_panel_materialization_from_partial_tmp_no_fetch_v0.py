#!/usr/bin/env python3
"""Run offline panel materialization from durable-archive partial tmp (no fetch) v0.

Bounded scope: materialize extended_chronological_v1 panel from existing partial tmp raw,
prepare funding bindings for panel members only (--skip-fetch), and run CSF/RDM preflight
with attempt_fetch=False. Does not execute economic evaluation, runtime, or network fetch.
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

from scripts.ops import primary_evidence_retention_v0 as retention  # noqa: E402
from src.research.offline_panel_materialization_from_partial_tmp_no_fetch_v0 import (  # noqa: E402
    CONFIRM_GO,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    DEFAULT_OUTPUT_STAGING_REL,
    DEFAULT_PARTIAL_TMP_REL,
    FUNDING_OWNER,
    MATERIALIZATION_VERSION,
    PREFLIGHT_OWNER,
    SOURCE_OWNER,
    OfflinePanelMaterializationVerdict,
    load_offline_panel_materialization_config_v0,
    offline_panel_materialization_scope_result_to_dict,
    run_offline_panel_materialization_scope_v0,
)

SCOPE_CLASSIFICATION = "OFFLINE_PANEL_MATERIALIZATION_FROM_PARTIAL_TMP_NO_FETCH_V0"
PROCESS_CLASSIFICATION = "OFFLINE_PANEL_MATERIALIZATION_FUNDING_PREP_PREFLIGHT_NO_FETCH"


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _git_head(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def run_offline_panel_materialization_cli_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    partial_tmp_root: Path | None = None,
    output_staging_root: Path | None = None,
    binding_origin_main_sha: str | None = None,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR:confirm_go_token_required:{CONFIRM_GO}")

    binding_config = load_offline_panel_materialization_config_v0(_REPO_ROOT)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "research"
        / f"offline_panel_materialization_from_partial_tmp_no_fetch_v0_{ts_slug}"
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    scope_result = run_offline_panel_materialization_scope_v0(
        repo_root=_REPO_ROOT,
        durable_evidence_root=durable_evidence_root,
        partial_tmp_root=partial_tmp_root,
        output_staging_root=output_staging_root,
        binding_origin_main_sha=binding_origin_main_sha,
    )
    scope_payload = offline_panel_materialization_scope_result_to_dict(scope_result)
    initial_head = _git_head(_REPO_ROOT)
    verdict = scope_result.verdict.value
    materialized = scope_result.materialization_run
    preflight_ready = (
        scope_result.preflight_scope is not None
        and scope_result.preflight_scope.ready_for_next_pre_evaluation_gate
    )

    payload: dict[str, Any] = {
        "verdict": verdict,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "materialization_version": MATERIALIZATION_VERSION,
        "confirm_go_consumed": CONFIRM_GO,
        "initial_head": initial_head,
        "binding_origin_main_sha": binding_origin_main_sha or initial_head,
        "canonical_source_owner": SOURCE_OWNER,
        "canonical_funding_owner": FUNDING_OWNER,
        "canonical_preflight_owner": PREFLIGHT_OWNER,
        "reuse_decisions": scope_payload["reuse_decisions"],
        "binding_config": binding_config,
        "primary_worktree": str(primary_worktree),
        "partial_tmp_root": scope_result.partial_tmp_resolution.partial_tmp_root,
        "output_staging_root": str(
            output_staging_root or (durable_evidence_root / DEFAULT_OUTPUT_STAGING_REL)
        ),
        "fetch_run": False,
        "network_fetch_run": False,
        "full_universe_fetch_run": False,
        "materialization_run": materialized,
        "preflight_no_fetch": True,
        "funding_binding_scope": "panel_members_only",
        "economic_evaluation_run": False,
        "no_runtime": True,
        "no_testnet": True,
        "no_shadow": True,
        "no_paper": True,
        "no_orders": True,
        "partial_tmp_cleanup_status": "untouched",
        "materialization_scope": scope_payload,
        "durable_evidence_path": str(bundle_dir),
    }

    (bundle_dir / "MATERIALIZATION_SCOPE_RESULT.json").write_text(
        json.dumps(scope_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if scope_result.preflight_scope is not None:
        (bundle_dir / "PREFLIGHT_RESULT.json").write_text(
            json.dumps(scope_result.preflight_scope.preflight_payload, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
    (bundle_dir / "SCOPE_AND_GO.txt").write_text(
        "\n".join(
            [
                f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
                f"PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}",
                f"CONFIRM_GO={CONFIRM_GO}",
                "FETCH_RUN=false",
                "NETWORK_FETCH_RUN=false",
                "FULL_UNIVERSE_FETCH_RUN=false",
                f"MATERIALIZATION_RUN={'true' if materialized else 'false'}",
                "PREFLIGHT_NO_FETCH=true",
                "FUNDING_BINDING_SCOPE=panel_members_only",
                "ECONOMIC_EVALUATION_RUN=false",
                "PARTIAL_TMP_CLEANUP_STATUS=untouched",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "FINAL_REPORT.md").write_text(
        "\n".join(
            [
                "# Offline Panel Materialization From Partial Tmp (No Fetch) v0",
                "",
                f"- Verdict: {verdict}",
                f"- Partial tmp: {scope_result.partial_tmp_resolution.partial_tmp_root}",
                f"- Materialization run: {materialized}",
                f"- Preflight ready: {preflight_ready}",
                "",
                "## Reason codes",
                *(f"- {code}" for code in scope_result.reason_codes),
                "",
                "## Safety invariants",
                "- FETCH_RUN=false",
                "- NETWORK_FETCH_RUN=false",
                "- FULL_UNIVERSE_FETCH_RUN=false",
                "- PREFLIGHT_NO_FETCH=true",
                "- PARTIAL_TMP_CLEANUP_STATUS=untouched",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    payload["manifest_verify_rc"] = manifest_rc
    payload["manifest_verify_msg"] = manifest_msg
    (bundle_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "MACHINE_SUMMARY.env").write_text(
        "\n".join(
            [
                f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
                f"VERDICT={verdict}",
                f"MATERIALIZATION_RUN={'true' if materialized else 'false'}",
                "FETCH_RUN=false",
                "NETWORK_FETCH_RUN=false",
                "FULL_UNIVERSE_FETCH_RUN=false",
                "PREFLIGHT_NO_FETCH=true",
                "FUNDING_BINDING_SCOPE=panel_members_only",
                "ECONOMIC_EVALUATION_RUN=false",
                "PARTIAL_TMP_CLEANUP_STATUS=untouched",
                f"MANIFEST_VERIFY_RC={manifest_rc}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument(
        "--durable-evidence-root",
        type=Path,
        default=DEFAULT_DURABLE_ARCHIVE_ROOT,
    )
    parser.add_argument("--primary-worktree", type=Path, required=True)
    parser.add_argument(
        "--partial-tmp-root",
        type=Path,
        default=None,
        help=f"Explicit partial tmp root (default: {DEFAULT_PARTIAL_TMP_REL})",
    )
    parser.add_argument(
        "--output-staging-root",
        type=Path,
        default=None,
        help=f"Output staging root (default: durable archive / {DEFAULT_OUTPUT_STAGING_REL})",
    )
    parser.add_argument("--binding-origin-main-sha", default=None)
    args = parser.parse_args()

    result = run_offline_panel_materialization_cli_v0(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        partial_tmp_root=args.partial_tmp_root,
        output_staging_root=args.output_staging_root,
        binding_origin_main_sha=args.binding_origin_main_sha,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["verdict"] not in {
        OfflinePanelMaterializationVerdict.MATERIALIZED_PANEL_FUNDING_PREPARED_PREFLIGHT_COMPLETE.value,
    }:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
