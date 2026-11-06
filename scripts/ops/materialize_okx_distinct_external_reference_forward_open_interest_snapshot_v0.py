#!/usr/bin/env python3
"""Materialize distinct external reference OKX forward OI snapshot v0.

Bounded public GET via okx_historical_open_interest_public_fetch_v0, materialized into
physically separate observations.jsonl for overlap validation.
Operator GO: GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_DISTINCT_EXTERNAL_REFERENCE_BOUNDED_ACQUISITION_AND_OFFLINE_MATERIALIZATION_V0
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
)
from src.research.okx_distinct_external_reference_forward_open_interest_snapshot_materialization_v0 import (  # noqa: E402
    CONFIRM_GO,
    exit_code_for_materialization_result_v0,
    materialization_result_to_dict_v0,
    materialize_distinct_external_reference_snapshot_v0,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _load_instrument(path: Path) -> dict:
    if not path.is_file():
        _die(f"ERR: missing_instrument_file:{path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        _die("ERR: instrument_file_must_be_object")
    return data


def _build_url(path: str, params: dict[str, str]) -> str:
    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"https://www.okx.com{path}?{query}"


def _parse_json(body: bytes) -> dict:
    return json.loads(body.decode())


def _fetch_with_retry(
    url: str, *, fetcher, rate_limiter, **_kwargs
) -> tuple[int, bytes, dict[str, str]]:
    rate_limiter()
    return fetcher(url, timeout_seconds=30.0, max_response_bytes=50_000_000)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize distinct external reference OKX forward OI snapshot."
    )
    parser.add_argument(
        "--confirm-go-token",
        required=True,
        help=f"Required operator GO token ({CONFIRM_GO})",
    )
    parser.add_argument(
        "--self-archive-input",
        type=Path,
        required=True,
        help="Canonical self-accumulated archive snapshot directory or observations.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Distinct external reference snapshot output directory",
    )
    parser.add_argument(
        "--instrument-file",
        type=Path,
        required=True,
        help="JSON file with one OKX public instrument record",
    )
    parser.add_argument(
        "--collected-at-utc",
        default=None,
        help="Explicit acquisition timestamp UTC (defaults to now UTC)",
    )
    parser.add_argument(
        "--enable-live-fetch",
        action="store_true",
        default=False,
        help="Execute bounded public OKX GET (single bounded acquisition path)",
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        default=False,
        help="Rematerialize from existing raw_fetch directory only",
    )
    parser.add_argument(
        "--raw-fetch-dir",
        type=Path,
        default=None,
        help="Optional raw fetch directory (defaults to output-dir/raw_fetch)",
    )
    parser.add_argument(
        "--enabled",
        action="store_true",
        help="Explicit enable flag; default-off without this flag",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Optional JSON output path",
    )
    args = parser.parse_args(argv)

    if not args.enabled:
        _die("ERR: DEFAULT_OFF_ENABLED_FLAG_REQUIRED")
    if args.confirm_go_token != CONFIRM_GO:
        _die(f"ERR: OPERATOR_GO_MISMATCH expected={CONFIRM_GO}")
    if args.skip_fetch and args.enable_live_fetch:
        _die("ERR: skip_fetch_and_enable_live_fetch_mutually_exclusive")

    collected_at_utc = args.collected_at_utc or datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    fetcher = None
    rate_limiter = None
    if args.enable_live_fetch and not args.skip_fetch:
        import scripts.ops.ingest_okx_futures_public_market_data_canonical_dataset_staging_v1 as ingest

        fetcher = ingest.okx_public_fetch_v1
        rate_limiter = RateLimiter().wait

    result = materialize_distinct_external_reference_snapshot_v0(
        confirm=args.confirm_go_token,
        instrument=_load_instrument(args.instrument_file),
        self_archive_source=args.self_archive_input,
        output_dir=args.output_dir,
        collected_at_utc=collected_at_utc,
        enabled=True,
        fetcher=fetcher,
        fetch_with_retry=_fetch_with_retry if fetcher is not None else None,
        build_url=_build_url if fetcher is not None else None,
        parse_json=_parse_json if fetcher is not None else None,
        rate_limiter=rate_limiter,
        raw_fetch_dir=args.raw_fetch_dir,
        skip_fetch=args.skip_fetch,
    )
    report = materialization_result_to_dict_v0(result)
    serialized = json.dumps(report, sort_keys=True, indent=2)
    print(serialized)
    if args.output_file is not None:
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        args.output_file.write_text(serialized + "\n", encoding="utf-8")
    return exit_code_for_materialization_result_v0(result)


if __name__ == "__main__":
    raise SystemExit(main())
