#!/usr/bin/env python3
"""Execute bounded ETH PT1H gap remediation for self-accumulated forward OI archive v0.

Public read-only OKX fetch of exactly seven missing venue timestamps, gap-insert
archive correction, and durable evidence emission. No forward collection.
Operator GO: GO_CORE_SYSTEM_DEVELOPMENT_SELF_ACCUMULATED_OI_ETH_GAP_REMEDIATION_IMPLEMENTATION_V0
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

from scripts.ops.ingest_okx_futures_public_market_data_canonical_dataset_staging_v1 import (  # noqa: E402
    RateLimiter,
    fetch_with_retry,
    okx_public_fetch_v1,
)
from src.research.okx_self_accumulated_forward_open_interest_eth_gap_remediation_v0 import (  # noqa: E402
    CONFIRM_GO,
    ETH_NATIVE_INSTRUMENT_ID,
    REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC,
    execute_eth_gap_remediation_v0,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _build_url(path: str, params: dict[str, str]) -> str:
    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"https://www.okx.com{path}?{query}"


def _parse_json(body: bytes) -> dict:
    return json.loads(body.decode())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bounded ETH gap remediation for self-accumulated OI archive v0."
    )
    parser.add_argument("--confirm-go-token", required=True)
    parser.add_argument("--target-archive", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--collection-execution-id", required=True)
    parser.add_argument("--enabled", action="store_true")
    parser.add_argument(
        "--execute-mutation",
        action="store_true",
        help="Authorize archive correction mutation on target archive",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Fetch and validate only; no archive mutation",
    )
    args = parser.parse_args(argv)

    if args.confirm_go_token != CONFIRM_GO:
        _die(f"OPERATOR_GO_MISMATCH expected={CONFIRM_GO}")

    if not args.enabled:
        _die("DEFAULT_OFF_ENABLED_FLAG_REQUIRED")

    if args.execute_mutation and args.validate_only:
        _die("EXECUTE_MUTATION_AND_VALIDATE_ONLY_MUTUALLY_EXCLUSIVE")

    target_archive = args.target_archive.resolve()
    if not target_archive.is_dir():
        _die(f"MISSING_TARGET_ARCHIVE:{target_archive}")

    evidence_dir = args.evidence_dir.resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = evidence_dir / "raw_fetch"
    raw_dir.mkdir(parents=True, exist_ok=True)

    collected_at_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = execute_eth_gap_remediation_v0(
        confirm=args.confirm_go_token,
        enabled=True,
        target_archive_path=target_archive,
        collected_at_utc=collected_at_utc,
        collection_execution_id=args.collection_execution_id,
        evidence_ref=str(evidence_dir),
        fetcher=okx_public_fetch_v1,
        rate_limiter=RateLimiter(),
        fetch_with_retry=fetch_with_retry,
        build_url=_build_url,
        parse_json=_parse_json,
        raw_dir=raw_dir,
        execute_mutation=args.execute_mutation and not args.validate_only,
    )

    report = {
        "status": result.status,
        "fetch_verdict": result.fetch_validation.verdict.value,
        "requested_missing_timestamps": list(REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC),
        "fetched_timestamps": list(result.fetch_validation.fetched_timestamps_utc),
        "correction_status": result.correction_status,
        "gap_insert_count": result.gap_insert_count,
        "observations_jsonl_byte_identical": result.observations_jsonl_byte_identical,
        "correction_idempotent": result.correction_idempotent,
        "fetch_instrument": ETH_NATIVE_INSTRUMENT_ID,
        "reason_codes": list(result.reason_codes),
    }
    (evidence_dir / "gap_remediation_result.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True, indent=2))

    if result.status not in {"REMEDIATION_COMPLETE", "VALIDATE_ONLY_PASS"}:
        if result.correction_status == "VALIDATE_ONLY_PASS":
            return 0
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
