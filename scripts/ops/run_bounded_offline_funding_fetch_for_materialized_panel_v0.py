#!/usr/bin/env python3
"""Run bounded offline funding fetch for materialized extended_chronological_v1 panel v0.

Fetches OKX public funding history for already materialized panel members only.
Does not execute economic evaluation, runtime, credentials access, or Full-Universe fetch.
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
from src.research.bounded_offline_funding_fetch_for_materialized_panel_v0 import (  # noqa: E402
    CONFIRM_GO,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    MATERIALIZATION_VERSION,
    BoundedFundingFetchVerdict,
    bounded_offline_funding_fetch_scope_result_to_dict,
    funding_coverage_report_to_dict,
    load_bounded_funding_fetch_config_v0,
    panel_member_binding_to_dict,
    run_bounded_offline_funding_fetch_scope_v0,
)
from src.research.csf_rdm_v0_extended_chronological_v1_staging_funding_panel_materialization_v0 import (  # noqa: E402
    CANONICAL_FUNDING_OWNER,
    CANONICAL_PREFLIGHT_OWNER,
)

SCOPE_CLASSIFICATION = "BOUNDED_OFFLINE_FUNDING_FETCH_FOR_MATERIALIZED_PANEL_V0"
PROCESS_CLASSIFICATION = "BOUNDED_OFFLINE_FUNDING_FETCH_PANEL_MEMBERS_ONLY_NO_EVALUATION"


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


def run_bounded_offline_funding_fetch_cli_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path | None = None,
    binding_origin_main_sha: str | None = None,
    execute_fetch: bool = True,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR:confirm_go_token_required:{CONFIRM_GO}")

    binding_config = load_bounded_funding_fetch_config_v0(_REPO_ROOT)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "research"
        / f"bounded_offline_funding_fetch_for_materialized_panel_v0_{ts_slug}"
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    scope_result = run_bounded_offline_funding_fetch_scope_v0(
        repo_root=_REPO_ROOT,
        durable_evidence_root=durable_evidence_root,
        staging_root=staging_root,
        binding_origin_main_sha=binding_origin_main_sha,
        confirm_go=confirm,
        execute_fetch=execute_fetch,
    )
    scope_payload = bounded_offline_funding_fetch_scope_result_to_dict(scope_result)
    initial_head = _git_head(_REPO_ROOT)
    verdict = scope_result.verdict.value

    fetch_commands = [
        (
            "python scripts/ops/materialize_cross_sectional_funding_rate_delta_momentum_v0_"
            "bound_panel_funding_dataset_v0.py "
            f"--confirm GO_BOUNDED_CROSS_SECTIONAL_FUNDING_RATE_CARRY_V0_ECONOMIC_EVALUATION_"
            f"EXECUTION_INFRASTRUCTURE_AND_BOUND_FUNDING_PANEL_RECOVERY_V0 "
            f"--staging-root {scope_result.panel_binding.staging_root if scope_result.panel_binding else '<staging>'}"
        ),
    ]

    (bundle_dir / "SCOPE.md").write_text(
        "\n".join(
            [
                "# Bounded Offline Funding Fetch For Materialized Panel v0",
                "",
                f"- Scope classification: {SCOPE_CLASSIFICATION}",
                f"- Process classification: {PROCESS_CLASSIFICATION}",
                f"- GO token: {CONFIRM_GO}",
                "- Panel scope: extended_chronological_v1 materialized panel members only",
                "- Period: 2024-05-01T00:00:00Z .. 2024-09-01T00:00:00Z",
                "- Full-Universe fetch: forbidden",
                "- Economic evaluation: forbidden",
                "- Runtime/orders/credentials: forbidden",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "INPUT_BINDINGS.md").write_text(
        "\n".join(
            [
                "# Input Bindings",
                "",
                f"- Prior materialization evidence: {binding_config.get('prior_materialization_evidence_bundle', 'offline_panel_materialization_from_partial_tmp_no_fetch_v0_20260703T221342Z')}",
                f"- Staging root: {scope_result.panel_binding.staging_root if scope_result.panel_binding else 'N/A'}",
                f"- Panel member count: {scope_result.panel_binding.panel_member_count if scope_result.panel_binding else 0}",
                f"- Funding owner: {CANONICAL_FUNDING_OWNER}",
                f"- Preflight owner: {CANONICAL_PREFLIGHT_OWNER}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    if scope_result.panel_binding is not None:
        (bundle_dir / "PANEL_MEMBER_BINDING.json").write_text(
            json.dumps(
                panel_member_binding_to_dict(scope_result.panel_binding), indent=2, sort_keys=True
            )
            + "\n",
            encoding="utf-8",
        )
    (bundle_dir / "FUNDING_FETCH_PLAN.md").write_text(
        "\n".join(
            [
                "# Funding Fetch Plan",
                "",
                "1. Load panel member binding from extended_chronological_v1 staging manifest.",
                "2. Verify scope drift guard (funding instruments == panel members).",
                "3. Clear stale skip-fetch funding artifacts when fetched_from_okx_public=false.",
                "4. Reuse materialize_cross_sectional_funding_rate_carry_v0 bound panel funding owner with skip_fetch=false.",
                "5. Re-run CSF/RDM dataset/funding binding materialization preflight.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "FETCH_COMMANDS.txt").write_text(
        "\n".join(fetch_commands) + "\n", encoding="utf-8"
    )
    (bundle_dir / "FETCH_RESULT_SUMMARY.json").write_text(
        json.dumps(scope_result.fetch_result or {}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "FUNDING_COVERAGE_REPORT.json").write_text(
        json.dumps(
            {
                "before": (
                    funding_coverage_report_to_dict(scope_result.coverage_before)
                    if scope_result.coverage_before
                    else None
                ),
                "after": (
                    funding_coverage_report_to_dict(scope_result.coverage_after)
                    if scope_result.coverage_after
                    else None
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    before_status = (
        scope_result.preflight_before.get("status") if scope_result.preflight_before else "N/A"
    )
    after_status = (
        scope_result.preflight_after.get("status") if scope_result.preflight_after else "N/A"
    )
    (bundle_dir / "PREFLIGHT_BEFORE_AFTER.md").write_text(
        "\n".join(
            [
                "# Preflight Before/After",
                "",
                f"- Before: {before_status}",
                f"- After: {after_status}",
                f"- Ready for next pre-evaluation gate: {scope_payload.get('ready_for_next_pre_evaluation_gate')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "SAFETY_FLAGS.md").write_text(
        "\n".join(
            [
                "# Safety Flags",
                "",
                f"FETCH_RUN={'true' if scope_result.fetch_run else 'false'}",
                f"NETWORK_FETCH_RUN={'true' if scope_result.network_fetch_run else 'false'}",
                "FULL_UNIVERSE_FETCH_RUN=false",
                "ECONOMIC_EVALUATION_RUN=false",
                "RUNTIME_RUN=false",
                "SHADOW/PAPER/TESTNET/LIVE=false",
                "CREDENTIALS_USED=false",
                "ORDERS_ALLOWED=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    payload: dict[str, Any] = {
        "verdict": verdict,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "materialization_version": MATERIALIZATION_VERSION,
        "confirm_go_consumed": CONFIRM_GO,
        "initial_head": initial_head,
        "binding_origin_main_sha": binding_origin_main_sha or initial_head,
        "canonical_funding_owner": CANONICAL_FUNDING_OWNER,
        "canonical_preflight_owner": CANONICAL_PREFLIGHT_OWNER,
        "binding_config": binding_config,
        "primary_worktree": str(primary_worktree),
        "fetch_run": scope_result.fetch_run,
        "network_fetch_run": scope_result.network_fetch_run,
        "full_universe_fetch_run": False,
        "economic_evaluation_run": False,
        "no_runtime": True,
        "no_testnet": True,
        "no_shadow": True,
        "no_paper": True,
        "no_orders": True,
        "materialization_scope": scope_payload,
        "durable_evidence_path": str(bundle_dir),
    }

    (bundle_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "MACHINE_SUMMARY.env").write_text(
        "\n".join(
            [
                f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
                f"VERDICT={verdict}",
                f"FETCH_RUN={'true' if scope_result.fetch_run else 'false'}",
                f"NETWORK_FETCH_RUN={'true' if scope_result.network_fetch_run else 'false'}",
                "FULL_UNIVERSE_FETCH_RUN=false",
                "ECONOMIC_EVALUATION_RUN=false",
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
        (bundle_dir / "MACHINE_SUMMARY.env").read_text(encoding="utf-8").rstrip("\n")
        + f"\nMANIFEST_VERIFY_RC={manifest_rc}\n",
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
    parser.add_argument("--staging-root", type=Path, default=None)
    parser.add_argument("--binding-origin-main-sha", default=None)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Assess scope and preflight only; do not execute network fetch.",
    )
    args = parser.parse_args()

    result = run_bounded_offline_funding_fetch_cli_v0(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        staging_root=args.staging_root,
        binding_origin_main_sha=args.binding_origin_main_sha,
        execute_fetch=not args.dry_run,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    allowed_verdicts = {
        BoundedFundingFetchVerdict.FUNDING_FETCHED_PREFLIGHT_COMPLETE.value,
        BoundedFundingFetchVerdict.FAIL_CLOSED_PREFLIGHT.value,
    }
    if result["verdict"] not in allowed_verdicts:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
