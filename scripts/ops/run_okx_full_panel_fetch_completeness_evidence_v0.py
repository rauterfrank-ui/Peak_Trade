#!/usr/bin/env python3
"""Run bounded OKX full-panel archive fetch and completeness evidence v0.

Public archive CDN fetch only. No dataset promotion, no economic evaluation.
Operator GO: GO_BOUNDED_OKX_FULL_PANEL_FETCH_AND_COMPLETENESS_EVIDENCE_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.okx_full_panel_fetch_completeness_evidence_v0 import (  # noqa: E402
    GO_TOKEN,
    run_okx_full_panel_fetch_completeness_evidence_v0,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm", required=True, help=f"Required GO token: {GO_TOKEN}")
    parser.add_argument(
        "--durable-archive-root",
        type=Path,
        default=Path(
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
        ),
    )
    parser.add_argument("--lifecycle-registry-path", type=Path)
    parser.add_argument("--ohlcv-raw-dir", type=Path)
    parser.add_argument("--probe-archive-dir", type=Path)
    parser.add_argument("--execution-root", type=Path)
    parser.add_argument("--max-instruments", type=int)
    parser.add_argument("--max-http-requests", type=int, default=2500)
    parser.add_argument("--max-total-bytes", type=int, default=500_000_000)
    parser.add_argument("--max-runtime-seconds", type=int, default=900)
    parser.add_argument(
        "--network-enabled",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    args = parser.parse_args()

    if args.confirm != GO_TOKEN:
        _die(f"ERR: confirm_go_token_required:{GO_TOKEN}")

    result = run_okx_full_panel_fetch_completeness_evidence_v0(
        confirm=args.confirm,
        durable_archive_root=args.durable_archive_root,
        lifecycle_registry_path=args.lifecycle_registry_path,
        ohlcv_raw_dir=args.ohlcv_raw_dir,
        probe_archive_dir=args.probe_archive_dir,
        execution_root=args.execution_root,
        max_instruments=args.max_instruments,
        max_http_requests=args.max_http_requests,
        max_total_bytes=args.max_total_bytes,
        max_runtime_seconds=args.max_runtime_seconds,
        network_enabled=args.network_enabled,
    )

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_root = (
        args.durable_archive_root
        / "implementation"
        / f"bounded_okx_full_panel_fetch_and_completeness_evidence_v0_{ts_slug}"
    )
    evidence_root.mkdir(parents=True, exist_ok=True)
    summary = {
        "go_token": GO_TOKEN,
        "status": result.status.value,
        "panel_outcome": result.panel_outcome.value,
        "aggregates": result.aggregates.__dict__,
        "dataset_candidate_root": result.dataset_candidate_root,
        "dataset_promoted": result.dataset_promoted,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "manifest_verify_rc": result.manifest_verify_rc,
        "quarantine_before": result.quarantine_before.__dict__,
        "quarantine_after": result.quarantine_after.__dict__,
        "guard_fail_reason": result.guard_fail_reason,
    }
    (evidence_root / "EXECUTION_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "VERDICT.md").write_text(
        "\n".join(
            [
                "# VERDICT",
                "",
                f"FULL_PANEL_FETCH_EXECUTED={result.full_panel_fetch_executed}",
                f"PANEL_COMPLETENESS_RESULT={result.panel_outcome.value}",
                f"DATASET_CANDIDATE_STAGED={result.dataset_candidate_staged}",
                f"DATASET_PROMOTED={result.dataset_promoted}",
                f"ECONOMIC_EVALUATION_EXECUTED={result.economic_evaluation_executed}",
                f"MANIFEST_VERIFY_RC={result.manifest_verify_rc}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
        verify_manifest_sha256,
        write_manifest_sha256,
    )

    write_manifest_sha256(evidence_root)
    manifest_ok, manifest_msg = verify_manifest_sha256(evidence_root)
    if not manifest_ok:
        _die(f"ERR: evidence_manifest_verify_failed:{manifest_msg}", 1)

    print(json.dumps({"execution_result": summary}, indent=2, sort_keys=True))
    if result.guard_fail_reason:
        _die(f"ERR: guard_fail_closed:{result.guard_fail_reason}", 1)


if __name__ == "__main__":
    main()
