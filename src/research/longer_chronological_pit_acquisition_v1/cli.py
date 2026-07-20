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
from src.research.longer_chronological_pit_acquisition_v1.history_depth_probe import (
    DEFAULT_MAX_INSTRUMENTS,
    DEFAULT_REQUEST_BUDGET,
    HistoryDepthProbeError,
    default_probe_universe_sample,
    run_history_depth_probe,
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


def _load_instruments(
    path: Path | None, *, for_history_depth: bool = False
) -> list[dict[str, Any]]:
    if path is None:
        if for_history_depth:
            return [
                {
                    "instrument_id": i.instrument_id,
                    "native_instrument_id": i.native_instrument_id,
                    "base_asset": i.base_asset,
                    "quote_asset": i.quote_asset,
                    "market_type": i.market_type,
                    "listing_time": i.listing_time,
                    "delisting_time": i.delisting_time,
                    "state": i.state,
                }
                for i in default_probe_universe_sample()
            ]
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
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "instruments" in payload:
        return list(payload["instruments"])
    if isinstance(payload, list):
        return payload
    raise ValueError("INSTRUMENTS_JSON_MUST_BE_LIST_OR_OBJECT_WITH_instruments")


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
        choices=(
            "plan",
            "discover",
            "manifest",
            "probe",
            "qualify-dry-run",
            "history-depth-probe",
            "seal-lifecycle",
            "acquire-long-panel",
        ),
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
    p.add_argument(
        "--allow-network-probe",
        action="store_true",
        help="Explicit freigabe for history-depth-probe network calls (default off)",
    )
    p.add_argument(
        "--allow-write-probe",
        action="store_true",
        help="Explicit freigabe to write small probe artifacts under archive root",
    )
    p.add_argument(
        "--request-budget",
        type=int,
        default=None,
        help=f"Hard request budget for history-depth-probe (max {DEFAULT_REQUEST_BUDGET})",
    )
    p.add_argument(
        "--max-instruments",
        type=int,
        default=DEFAULT_MAX_INSTRUMENTS,
        help=f"Max instruments in history-depth sample (1..{DEFAULT_MAX_INSTRUMENTS})",
    )
    p.add_argument(
        "--selection-seed",
        type=int,
        default=0,
        help="Deterministic seed recorded for probe sample edge-case ties",
    )
    p.add_argument(
        "--production-registry-json",
        type=Path,
        default=None,
        help="Absolute path to validated production lifecycle registry_snapshot_v1.json",
    )
    p.add_argument(
        "--sealed-manifest-json",
        type=Path,
        default=None,
        help="Path to sealed lifecycle manifest (acquire-long-panel)",
    )
    p.add_argument(
        "--allow-write-seal",
        action="store_true",
        help="Write sealed lifecycle artifacts under external archive root",
    )
    p.add_argument(
        "--allow-write-acquisition",
        action="store_true",
        help="Write bounded long-panel acquisition artifacts under archive root",
    )
    p.add_argument(
        "--seal-request-budget",
        type=int,
        default=None,
        help="Hard request budget for seal-lifecycle public enrichment",
    )
    p.add_argument(
        "--acquisition-request-budget",
        type=int,
        default=None,
        help="Hard request budget for acquire-long-panel",
    )
    p.add_argument(
        "--seal-max-instruments",
        type=int,
        default=None,
        help="Optional cap on registry intervals enriched during seal (fail-closed tests)",
    )
    p.add_argument(
        "--acquire-max-instruments",
        type=int,
        default=None,
        help="Optional cap on long-panel instruments acquired (bounded runs)",
    )
    p.add_argument("--json", action="store_true", help="Emit JSON")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.command in {"seal-lifecycle", "acquire-long-panel"}:
        instruments = []
    else:
        instruments = _load_instruments(
            args.instruments_json,
            for_history_depth=(args.command == "history-depth-probe"),
        )
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

    if args.command == "history-depth-probe":
        try:
            summary = run_history_depth_probe(
                instruments,
                allow_network_probe=bool(args.allow_network_probe),
                allow_write_probe=bool(args.allow_write_probe),
                request_budget=args.request_budget,
                archive_root=args.archive_root,
                max_instruments=int(args.max_instruments),
                selection_seed=int(args.selection_seed),
                period_start=args.period_start,
                period_end=args.period_end,
            )
        except HistoryDepthProbeError as exc:
            sys.stderr.write(f"{exc}\n")
            return 4
        sys.stdout.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        if summary.get("blockers"):
            return 5
        return 0

    if args.command == "seal-lifecycle":
        from src.research.longer_chronological_pit_acquisition_v1.public_lifecycle_acquisition_v1 import (  # noqa: PLC0415
            run_seal_lifecycle,
        )
        from src.research.longer_chronological_pit_acquisition_v1.sealed_lifecycle_v1 import (  # noqa: PLC0415
            SealedLifecycleError,
        )

        if args.production_registry_json is None:
            sys.stderr.write("PRODUCTION_REGISTRY_JSON_REQUIRED\n")
            return 4
        if args.seal_request_budget is None:
            sys.stderr.write("SEAL_REQUEST_BUDGET_REQUIRED\n")
            return 4
        try:
            summary = run_seal_lifecycle(
                production_registry_path=args.production_registry_json,
                archive_root=args.archive_root,
                allow_network=bool(args.allow_network_probe or args.allow_network),
                allow_write=bool(args.allow_write_seal or args.allow_write_probe),
                request_budget=int(args.seal_request_budget),
                max_instruments=args.seal_max_instruments,
                panel_start=args.period_start,
                panel_end=args.period_end,
            )
        except SealedLifecycleError as exc:
            sys.stderr.write(f"{exc}\n")
            return 4
        sys.stdout.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        return 0 if not summary.get("blockers") else 5

    if args.command == "acquire-long-panel":
        from src.research.longer_chronological_pit_acquisition_v1.public_lifecycle_acquisition_v1 import (  # noqa: PLC0415
            acquire_long_panel_ohlcv,
        )
        from src.research.longer_chronological_pit_acquisition_v1.sealed_lifecycle_v1 import (  # noqa: PLC0415
            SealedLifecycleError,
        )

        if args.sealed_manifest_json is None:
            sys.stderr.write("SEALED_MANIFEST_JSON_REQUIRED\n")
            return 4
        if args.acquisition_request_budget is None:
            sys.stderr.write("ACQUISITION_REQUEST_BUDGET_REQUIRED\n")
            return 4
        sealed = json.loads(args.sealed_manifest_json.read_text(encoding="utf-8"))
        try:
            summary = acquire_long_panel_ohlcv(
                sealed_manifest=sealed,
                archive_root=args.archive_root,
                allow_network=bool(args.allow_network_probe or args.allow_network),
                allow_write=bool(args.allow_write_acquisition or args.allow_write_probe),
                request_budget=int(args.acquisition_request_budget),
                max_instruments=args.acquire_max_instruments,
            )
        except SealedLifecycleError as exc:
            sys.stderr.write(f"{exc}\n")
            return 4
        sys.stdout.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        return 0 if summary.get("acquisition_executed") else 5

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
