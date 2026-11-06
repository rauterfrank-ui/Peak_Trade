#!/usr/bin/env python3
"""Bounded default-off one-shot OKX forward open-interest collector.

Public GET only via allowlisted OKX rubik open-interest-history endpoint.
Operator GO: GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_ONE_SHOT_COLLECTOR_HARNESS_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.okx_self_accumulated_forward_open_interest_one_shot_collector_harness_v0 import (  # noqa: E402
    CONFIRM_GO,
    CollectionMode,
    HarnessTerminalVerdict,
    result_to_final_report_dict_v0,
    run_one_shot_collection_cycle_v0,
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


def _load_fixture(path: Path | None) -> dict | None:
    if path is None:
        return None
    if not path.is_file():
        _die(f"ERR: missing_fixture_response:{path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        _die("ERR: fixture_response_must_be_object")
    return data


def _exit_code_for_verdict(verdict: HarnessTerminalVerdict) -> int:
    if verdict in {
        HarnessTerminalVerdict.VALIDATE_ONLY_PASS,
        HarnessTerminalVerdict.COLLECT_ONCE_COMPLETE,
    }:
        return 0
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bounded default-off one-shot OKX forward OI collector."
    )
    parser.add_argument(
        "--confirm-go-token",
        required=True,
        help=f"Required operator GO token ({CONFIRM_GO})",
    )
    parser.add_argument(
        "--mode",
        choices=[m.value for m in CollectionMode],
        default=CollectionMode.VALIDATE_ONLY.value,
        help="validate-only (no persistence) or collect-once (single bounded cycle)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Archive output directory (required for collect-once)",
    )
    parser.add_argument(
        "--instrument-file",
        type=Path,
        required=True,
        help="JSON file with one OKX public instrument record",
    )
    parser.add_argument(
        "--fixture-response",
        type=Path,
        default=None,
        help="Offline fixture OKX response JSON (tests/operator offline use)",
    )
    parser.add_argument(
        "--collected-at-utc",
        default=None,
        help="Explicit collected_at UTC timestamp (deterministic runs)",
    )
    parser.add_argument(
        "--enable-live-fetch",
        action="store_true",
        default=False,
        help="Use live public OKX fetch instead of fixture (still bounded single request)",
    )
    args = parser.parse_args(argv)

    if args.confirm_go_token != CONFIRM_GO:
        _die(f"ERR: invalid_confirm_go_token_required:{CONFIRM_GO}")

    mode = CollectionMode(args.mode)
    fixture = _load_fixture(args.fixture_response)
    fetcher = None
    if args.enable_live_fetch and fixture is None:
        import scripts.ops.ingest_okx_futures_public_market_data_canonical_dataset_staging_v1 as ingest

        fetcher = ingest.okx_public_fetch_v1
    elif fixture is None:
        _die("ERR: fixture_response_or_enable_live_fetch_required")

    result = run_one_shot_collection_cycle_v0(
        confirm=args.confirm_go_token,
        mode=mode,
        instrument=_load_instrument(args.instrument_file),
        output_dir=args.output_dir,
        collected_at_utc=args.collected_at_utc,
        fixture_response=fixture,
        fetcher=fetcher,
        enabled=False,
    )
    report = result_to_final_report_dict_v0(result)
    print(json.dumps(report, sort_keys=True, indent=2))
    return _exit_code_for_verdict(result.verdict)


if __name__ == "__main__":
    raise SystemExit(main())
