#!/usr/bin/env python3
"""Run bounded OKX Historical Funding Archive ingest for materialized panel v0.

Fetches OKX Historical Data Portal monthly funding archives for the 118 already
materialized extended_chronological_v1 panel members only. No live API fallback.
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
    funding_coverage_report_to_dict,
    panel_member_binding_to_dict,
)
from src.research.csf_rdm_v0_extended_chronological_v1_staging_funding_panel_materialization_v0 import (  # noqa: E402
    CANONICAL_FUNDING_OWNER,
    CANONICAL_PREFLIGHT_OWNER,
)
from src.research.okx_historical_funding_archive_ingest_for_materialized_panel_v0 import (  # noqa: E402
    CONFIRM_GO,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    MATERIALIZATION_VERSION,
    HistoricalArchiveIngestVerdict,
    archive_fetch_record_to_dict,
    historical_archive_ingest_scope_result_to_dict,
    load_historical_archive_ingest_config_v0,
    run_historical_archive_ingest_scope_v0,
)

SCOPE_CLASSIFICATION = "OKX_HISTORICAL_FUNDING_ARCHIVE_INGEST_FOR_MATERIALIZED_PANEL_V0"
PROCESS_CLASSIFICATION = (
    "BOUNDED_HISTORICAL_ARCHIVE_INGEST_PANEL_MEMBERS_ONLY_NO_EVALUATION_NO_LIVE_API"
)


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


def run_okx_historical_funding_archive_ingest_cli_v0(
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

    binding_config = load_historical_archive_ingest_config_v0(_REPO_ROOT)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root / "research" / f"okx_historical_funding_archive_ingest_v0_{ts_slug}"
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    scope_result = run_historical_archive_ingest_scope_v0(
        repo_root=_REPO_ROOT,
        durable_evidence_root=durable_evidence_root,
        staging_root=staging_root,
        binding_origin_main_sha=binding_origin_main_sha,
        confirm_go=confirm,
        execute_fetch=execute_fetch,
    )
    scope_payload = historical_archive_ingest_scope_result_to_dict(scope_result)
    initial_head = _git_head(_REPO_ROOT)
    verdict = scope_result.verdict.value

    fetch_cmd = (
        "python scripts/ops/run_okx_historical_funding_archive_ingest_v0.py "
        f"--confirm {CONFIRM_GO} "
        f"--primary-worktree {primary_worktree} "
        f"--durable-evidence-root {durable_evidence_root}"
    )
    if staging_root is not None:
        fetch_cmd += f" --staging-root {staging_root}"

    (bundle_dir / "SCOPE.md").write_text(
        "\n".join(
            [
                "# OKX Historical Funding Archive Ingest v0",
                "",
                f"- Scope classification: {SCOPE_CLASSIFICATION}",
                f"- Process classification: {PROCESS_CLASSIFICATION}",
                f"- GO token: {CONFIRM_GO}",
                "- Panel scope: extended_chronological_v1 materialized panel members only (118)",
                "- Period: 2024-05-01T00:00:00Z .. 2024-09-01T00:00:00Z",
                "- Archive months: 2024-04 (warmup) .. 2024-08",
                "- Full-Universe fetch: forbidden",
                "- OKX Public Live API: forbidden as data source",
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
                f"- Prior panel materialization: {binding_config.get('prior_panel_materialization_evidence_bundle')}",
                f"- Prior funding fetch evidence: {binding_config.get('prior_funding_fetch_evidence_bundle')}",
                f"- Staging root: {scope_result.panel_binding.staging_root if scope_result.panel_binding else 'N/A'}",
                f"- Panel member count: {scope_result.panel_binding.panel_member_count if scope_result.panel_binding else 0}",
                f"- Funding owner: {CANONICAL_FUNDING_OWNER}",
                f"- Preflight owner: {CANONICAL_PREFLIGHT_OWNER}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "PRIOR_EVIDENCE_LINKS.md").write_text(
        "\n".join(
            [
                "# Prior Evidence Links",
                "",
                "- PR #4815 offline panel materialization: offline_panel_materialization_from_partial_tmp_no_fetch_v0_20260703T221342Z",
                "- PR #4816 bounded live funding fetch: bounded_offline_funding_fetch_for_materialized_panel_v0_20260704T165402Z",
                "- Archive probe: probes/okx_historical_funding_archive_probe_v0_20260703T160811Z",
                "- Live API horizon insufficient: OKX_PUBLIC_FUNDING_API_HORIZON_INSUFFICIENT_FOR_PANEL_PERIOD",
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
    (bundle_dir / "ARCHIVE_SOURCE_DISCOVERY.md").write_text(
        "\n".join(
            [
                "# Archive Source Discovery",
                "",
                "- Source: OKX Historical Data Portal CDN",
                "- Base URL: https://static.okx.com/cdn/okex/traderecords/swaprates/monthly",
                "- Object pattern: {yyyymm}/{venue_symbol}-fundingrates-{yyyy}-{mm}.zip",
                "- Prior probe verified ETH-USDT-SWAP and SOL-USDT-SWAP for 2024-05",
                "- Live OKX Public Funding API horizon insufficient for 2024-05..2024-08 panel period",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "ARCHIVE_SOURCE_BINDING.json").write_text(
        json.dumps(scope_result.archive_source_binding or {}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "FETCH_COMMANDS.txt").write_text(fetch_cmd + "\n", encoding="utf-8")
    (bundle_dir / "FETCH_RESULT_SUMMARY.json").write_text(
        json.dumps(
            {
                "verdict": verdict,
                "fetch_record_count": len(scope_result.fetch_records),
                "materialization_result": scope_result.materialization_result,
                "reason_codes": list(scope_result.reason_codes),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "RAW_ARCHIVE_INVENTORY.json").write_text(
        json.dumps(
            [archive_fetch_record_to_dict(record) for record in scope_result.fetch_records],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "NORMALIZATION_REPORT.json").write_text(
        json.dumps(scope_result.normalization_report or {}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "FUNDING_COVERAGE_BEFORE_AFTER.json").write_text(
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
                "HISTORICAL_ARCHIVE_INGEST_RUN=true",
                f"NETWORK_FETCH_RUN={'true' if scope_result.network_fetch_run else 'false'}",
                "OKX_PUBLIC_LIVE_API_USED=false",
                "FULL_UNIVERSE_FETCH_RUN=false",
                "ECONOMIC_EVALUATION_RUN=false",
                "BACKTEST_RUN=false",
                "WALK_FORWARD_RUN=false",
                "MONTE_CARLO_RUN=false",
                "STRESS_RUN=false",
                "RUNTIME_RUN=false",
                "SHADOW/PAPER/TESTNET/LIVE=false",
                "CREDENTIALS_USED=false",
                "ORDERS_ALLOWED=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    if scope_result.reason_codes:
        (bundle_dir / "FAILURE_REASON.md").write_text(
            "\n".join(
                ["# Failure Reason", ""] + [f"- {code}" for code in scope_result.reason_codes]
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
        "historical_archive_ingest_run": scope_result.ingest_run,
        "network_fetch_run": scope_result.network_fetch_run,
        "okx_public_live_api_used": False,
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
                f"HISTORICAL_ARCHIVE_INGEST_RUN={'true' if scope_result.ingest_run else 'false'}",
                f"NETWORK_FETCH_RUN={'true' if scope_result.network_fetch_run else 'false'}",
                "OKX_PUBLIC_LIVE_API_USED=false",
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
        help="Assess scope and preflight only; do not execute archive network fetch.",
    )
    args = parser.parse_args()

    result = run_okx_historical_funding_archive_ingest_cli_v0(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        staging_root=args.staging_root,
        binding_origin_main_sha=args.binding_origin_main_sha,
        execute_fetch=not args.dry_run,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    allowed_verdicts = {
        HistoricalArchiveIngestVerdict.ARCHIVE_INGESTED_PREFLIGHT_COMPLETE.value,
        HistoricalArchiveIngestVerdict.FAIL_CLOSED_PREFLIGHT.value,
        HistoricalArchiveIngestVerdict.FAIL_CLOSED_ARCHIVE.value,
    }
    if result["verdict"] not in allowed_verdicts:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
