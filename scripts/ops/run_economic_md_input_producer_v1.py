#!/usr/bin/env python3
"""Standalone entrypoint for CAPABILITY_PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MD_INPUT_V1.

Offline/injected Public-MD only by default. Not productively scheduled.
No ranking, selection, Policy A, execution, live, or host join.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.economic_md_input_producer_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
)
from src.ops.economic_md_input_producer_v1.producer_v1 import (  # noqa: E402
    run_economic_md_input_producer_v1,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (  # noqa: E402
    InjectedEconomicMdPublicSourceV1,
    InstrumentPublicMdBundleV1,
    RawMarkCandleV1,
    RawTickerQuoteV1,
)


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(_REPO_ROOT),
            text=True,
        ).strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def _bundle_from_json(payload: MappingLike, venue_native_id: str) -> InstrumentPublicMdBundleV1:
    marks_raw = payload.get("marks") or []
    marks = tuple(
        RawMarkCandleV1(
            venue_native_id=venue_native_id,
            ts_ms=str(row["ts_ms"]),
            mark_px=str(row["mark_px"]),
            confirm=str(row.get("confirm", "1")),
            receive_or_capture_timestamp=str(row["receive_or_capture_timestamp"]),
        )
        for row in marks_raw
    )
    ticker_raw = payload.get("ticker")
    ticker = None
    if isinstance(ticker_raw, dict):
        ticker = RawTickerQuoteV1(
            venue_native_id=venue_native_id,
            bid_px=None if ticker_raw.get("bid_px") in (None, "") else str(ticker_raw["bid_px"]),
            ask_px=None if ticker_raw.get("ask_px") in (None, "") else str(ticker_raw["ask_px"]),
            ticker_event_timestamp=(
                None
                if ticker_raw.get("ticker_event_timestamp") in (None, "")
                else str(ticker_raw.get("ticker_event_timestamp"))
            ),
            capture_or_receive_timestamp=str(ticker_raw["capture_or_receive_timestamp"]),
        )
    return InstrumentPublicMdBundleV1(
        venue_native_id=venue_native_id,
        marks=marks,
        ticker=ticker,
    )


MappingLike = dict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=CAPABILITY_ID)
    parser.add_argument("--state-root", required=True, type=Path)
    parser.add_argument("--universe-json", type=Path, default=None)
    parser.add_argument("--universe-state-root", type=Path, default=None)
    parser.add_argument("--public-md-json", type=Path, default=None)
    parser.add_argument("--collection-started-at-unix", type=float, required=True)
    parser.add_argument("--collection-completed-at-unix", type=float, required=True)
    parser.add_argument("--session-id", type=str, default="default")
    parser.add_argument("--repository-sha", type=str, default=None)
    args = parser.parse_args(argv)

    universe = None
    if args.universe_json is not None:
        universe = json.loads(args.universe_json.read_text(encoding="utf-8"))
    bundles = {}
    if args.public_md_json is not None:
        raw = json.loads(args.public_md_json.read_text(encoding="utf-8"))
        for venue_id, item in dict(raw).items():
            bundles[str(venue_id)] = _bundle_from_json(dict(item), str(venue_id))

    result = run_economic_md_input_producer_v1(
        state_root=args.state_root,
        universe_snapshot=universe,
        universe_state_root=args.universe_state_root,
        public_md_source=InjectedEconomicMdPublicSourceV1(bundles),
        collection_started_at_unix=float(args.collection_started_at_unix),
        collection_completed_at_unix=float(args.collection_completed_at_unix),
        session_id=args.session_id,
    )
    result["repository_sha"] = args.repository_sha or _git_sha()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
