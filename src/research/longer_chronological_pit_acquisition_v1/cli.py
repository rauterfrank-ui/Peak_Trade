"""CLI for longer chronological PIT acquisition scaffold.

Defaults: dry-run, no network, no write, no credentials.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from src.research.longer_chronological_pit_acquisition_v1 import (
    DATASET_ID,
    ENV_ARCHIVE_ROOT,
    TARGET_PERIOD_END,
    TARGET_PERIOD_START,
)
from src.research.longer_chronological_pit_acquisition_v1.adapter import (
    NetworkDisabledError,
    OkxPublicHistoryAdapterV1,
)
from src.research.longer_chronological_pit_acquisition_v1.archive_root import (
    resolve_archive_root,
)
from src.research.longer_chronological_pit_acquisition_v1.manifest import (
    build_partition_manifest_row,
)
from src.research.longer_chronological_pit_acquisition_v1.partition_planner import (
    plan_partitions,
)
from src.research.longer_chronological_pit_acquisition_v1.qualification import (
    render_dry_run_text,
    run_qualification_dry_run,
)
from src.research.longer_chronological_pit_acquisition_v1.source_discovery import (
    list_public_sources,
)


def _load_instruments(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        # Tiny built-in sample for dry-run demos (non-BTC linear perps)
        return [
            {
                "instrument_id": "okx:linear_perpetual:ETH:USDT:USDT:perp",
                "native_instrument_id": "ETH-USDT-SWAP",
                "base_asset": "ETH",
                "quote_asset": "USDT",
                "market_type": "linear_usdt_perpetual",
                "listing_time": "2021-01-01T00:00:00Z",
                "delisting_time": None,
                "state": "KNOWN",
            },
            {
                "instrument_id": "okx:linear_perpetual:SOL:USDT:USDT:perp",
                "native_instrument_id": "SOL-USDT-SWAP",
                "base_asset": "SOL",
                "quote_asset": "USDT",
                "market_type": "linear_usdt_perpetual",
                "listing_time": "2022-06-01T00:00:00Z",
                "delisting_time": None,
                "state": "KNOWN",
            },
        ]
    return json.loads(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m src.research.longer_chronological_pit_acquisition_v1",
        description=(
            "Longer chronological PIT acquisition scaffold. "
            "Defaults: dry-run / no-network / no-write."
        ),
    )
    p.add_argument(
        "command",
        choices=("plan", "discover", "manifest", "probe", "qualify-dry-run"),
        help="Acquisition scaffold command",
    )
    p.add_argument("--instruments-json", type=Path, default=None)
    p.add_argument("--period-start", default=TARGET_PERIOD_START)
    p.add_argument("--period-end", default=TARGET_PERIOD_END)
    p.add_argument("--max-partitions", type=int, default=None)
    p.add_argument(
        "--archive-root",
        default=None,
        help=f"External archive root (or env {ENV_ARCHIVE_ROOT})",
    )
    p.add_argument(
        "--write-manifest",
        action="store_true",
        help="Persist manifest under external archive root (requires root)",
    )
    p.add_argument(
        "--allow-network",
        action="store_true",
        help="Permit network acquire (still requires probe limits; default off)",
    )
    p.add_argument(
        "--probe-one",
        action="store_true",
        help="Probe mode: at most one partition",
    )
    p.add_argument("--json", action="store_true", help="Emit JSON")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    instruments = _load_instruments(args.instruments_json)
    max_parts = args.max_partitions
    if args.probe_one:
        max_parts = 1

    if args.command in {"plan", "discover", "manifest", "qualify-dry-run"}:
        report = run_qualification_dry_run(
            instruments,
            period_start=args.period_start,
            period_end=args.period_end,
            max_partitions=max_parts,
            archive_root=args.archive_root,
            write_manifest=bool(args.write_manifest),
        )
        if args.command == "discover":
            report = {
                **report,
                "sources": list_public_sources(),
            }
        if args.command == "manifest":
            out = report["manifest"]
        elif args.json:
            out = report
        else:
            out = render_dry_run_text(report)
            if args.command == "discover":
                out += "SOURCES=\n" + json.dumps(list_public_sources(), indent=2) + "\n"
        if isinstance(out, str):
            sys.stdout.write(out)
        else:
            sys.stdout.write(json.dumps(out, indent=2, sort_keys=True) + "\n")
        return 0

    if args.command == "probe":
        # Default still no network — demonstrate gate
        plan = plan_partitions(
            instruments,
            period_start=args.period_start,
            period_end=args.period_end,
            max_partitions=1 if args.probe_one or max_parts is None else max_parts,
        )
        if not plan["partitions"]:
            sys.stderr.write("NO_PARTITIONS_TO_PROBE\n")
            return 2
        part = plan["partitions"][0]
        row = build_partition_manifest_row(part)
        adapter = OkxPublicHistoryAdapterV1()
        try:
            root = None
            if args.write_manifest or args.allow_network:
                # write still needs root; probe acquire without write ok
                if args.write_manifest:
                    root = resolve_archive_root(explicit=args.archive_root, require_for_write=True)
            result = adapter.acquire_partition(
                {**part, **row},
                allow_network=bool(args.allow_network),
                archive_root=root,
                write=False,
                source_locator=row["source_locator"],
            )
            sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
            return 0
        except NetworkDisabledError as exc:
            sys.stderr.write(f"{exc}\n")
            sys.stderr.write(
                "Refused: default probe is no-network. "
                "Re-run with --allow-network only for bounded operator probe.\n"
            )
            return 3

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
