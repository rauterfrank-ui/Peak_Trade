#!/usr/bin/env python3
"""Probe public inputs or explicitly run the isolated ZKP LANE_1 Paper opening."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from decimal import Decimal, DecimalException
import json
from pathlib import Path
import subprocess
import sys
from time import monotonic, sleep, time

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_entry_v1 import ZkpPaperEntryV1  # noqa: E402
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (  # noqa: E402
    INSTRUMENT_ID,
    NATIVE_ID,
    PAPER_ALLOCATION_USDC,
    PAPER_FEE_RATE,
    collect_zkp_paper_market_v1,
    load_paper_liquidity_policy_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (  # noqa: E402
    durable_bytes_v1,
    immutable_json_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (  # noqa: E402
    FullCoreProductiveReadOnlyGetTransportV1,
)

_POLL_SECONDS = 5


def _new_root(path):
    if (
        not path.is_absolute()
        or path != path.resolve()
        or path.exists()
        or not path.parent.is_dir()
        or path.is_relative_to(REPO)
        or path.is_relative_to(Path.home() / ".local/state/peak_trade/deployments")
    ):
        raise ValueError("ZKP_PAPER_NEW_ISOLATED_PATH_REQUIRED")
    return path


def _capture(policy, *, label, output=None):
    transport = FullCoreProductiveReadOnlyGetTransportV1(timeout_seconds=6, max_request_count=12)
    records = {}

    def retain(name, result, body):
        if output is None:
            return
        path = output / f"{name}.json"
        durable_bytes_v1(path, body)
        record = asdict(result)
        del record["payload"]
        records[name] = {"file": str(path), **record}

    market = collect_zkp_paper_market_v1(
        transport,
        policy=policy,
        capture_id=label,
        retain=retain,
    )
    if output is not None:
        immutable_json_v1(output / "receipts.json", records)
    return market


def preflight_zkp_paper_v1(*, market):
    minimum = market.native_contract.min_qty
    # The real quantity is derived by the canonical sizer after a fresh ENTER.
    checks = {
        side: market.assess_quantity_v1(side=side, quantity=minimum) for side in ("BUY", "SELL")
    }
    return {
        "status": "PREPARED",
        "session_started": False,
        "authority": "NONE",
        "lane_id": "LANE_1",
        "native_instrument_id": NATIVE_ID,
        "instrument_id": INSTRUMENT_ID,
        "observed_unix": market.observed_unix,
        "source_hashes": market.source_hashes,
        "allocation_usdc": str(PAPER_ALLOCATION_USDC),
        "valuation_usd": str(PAPER_ALLOCATION_USDC * market.usd_per_usdc),
        "fee_rate": str(PAPER_FEE_RATE),
        "liquidity_at_minimum_quantity": checks,
        "current_book_admitted_on_both_sides": all(row["risk_admitted"] for row in checks.values()),
        "pending": "FRESH_MASTER_V2_DECISION_AND_EXACT_QUANTITY_CHECK",
    }


def _run(root, market, *, policy, duration, deadline, revision, capture):
    session = ZkpPaperEntryV1(
        root=root,
        repo=REPO,
        revision=revision,
        initial_market=market,
        duration=duration,
    )
    poll = 0

    def fill_clock():
        if monotonic() >= deadline or (root / "STOP").exists():
            raise ValueError("ZKP_PAPER_WINDOW_ENDED_DURING_DECISION")
        return time()

    while monotonic() < deadline and not (root / "STOP").exists():
        if market is not None:
            result = session.step_v1(market, clock=fill_clock)
            if result["status"] == "FIRST_FILL_BOOKED":
                return result
        sleep(min(_POLL_SECONDS, max(0, deadline - monotonic())))
        if monotonic() >= deadline or (root / "STOP").exists():
            break
        poll += 1
        folder = root / "public" / f"{poll:05d}"
        try:
            market = capture(policy, label=f"{root.name}:{poll}", output=folder)
        except (OSError, ValueError, TypeError, KeyError, DecimalException) as exc:
            immutable_json_v1(
                folder / "blocked.json", {"reason": str(exc), "observed_unix": time()}
            )
            market = None
    result = {
        "status": "WINDOW_ENDED_BEFORE_FIRST_FILL",
        "orders_sent": 0,
        "permits_created": 0,
        "authority": "NONE",
    }
    immutable_json_v1(root / "opening-closeout.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    preflight = modes.add_parser(
        "preflight", help="Read public inputs and check executable liquidity"
    )
    preflight.add_argument("--evidence-root", type=Path)
    run = modes.add_parser("run", help="Explicitly start the Paper opening")
    run.add_argument("--run-root", required=True, type=Path)
    run.add_argument("--duration-seconds", type=int, default=7200)
    args = parser.parse_args(argv)
    try:
        policy = load_paper_liquidity_policy_v1(REPO)
        if args.mode == "preflight":
            output = None if args.evidence_root is None else _new_root(args.evidence_root)
            if output is not None:
                output.mkdir(mode=0o700)
            market = _capture(policy, label="zkp-paper-input-preflight", output=output)
            result = preflight_zkp_paper_v1(market=market)
            if output is not None:
                immutable_json_v1(output / "preflight.json", result)
        else:
            root = _new_root(args.run_root)
            if not 1 <= args.duration_seconds <= 7200:
                raise ValueError("ZKP_PAPER_WINDOW_INVALID")
            revision = subprocess.check_output(
                ["git", f"--work-tree={REPO}", "rev-parse", "HEAD"],
                cwd=REPO,
                text=True,
            ).strip()
            deadline = monotonic() + args.duration_seconds
            # Capture the initial FX and market as original public evidence before starting.
            initial_root = root.with_name(root.name + "-inputs")
            _new_root(initial_root).mkdir(mode=0o700)
            market = _capture(policy, label=f"{root.name}:0", output=initial_root)
            if monotonic() >= deadline:
                raise ValueError("ZKP_PAPER_WINDOW_ENDED_DURING_PREFLIGHT")
            result = _run(
                root,
                market,
                policy=policy,
                duration=args.duration_seconds,
                deadline=deadline,
                revision=revision,
                capture=_capture,
            )
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, DecimalException) as exc:
        parser.exit(2, f"ZKP Paper opening stopped: {exc}\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
