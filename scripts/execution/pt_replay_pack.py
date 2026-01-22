#!/usr/bin/env python3
"""
pt_replay_pack

Deterministic Replay Pack CLI:
- build: export a run into a replay bundle
- validate: verify schema + hashes
- replay: replay deterministically (optional invariant checks)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add repo root to path for imports (scripts -> repo root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.execution.replay_pack.builder import build_replay_pack
from src.execution.replay_pack.loader import load_replay_pack
from src.execution.replay_pack.runner import replay_bundle
from src.execution.replay_pack.validator import validate_replay_pack
from src.execution.replay_pack.contract import (
    ContractViolationError,
    HashMismatchError,
    ReplayMismatchError,
    SchemaValidationError,
)
from src.execution.replay_pack.datarefs import (
    DataRefHashMismatchError,
    MissingRequiredDataRefError,
    ResolutionMode,
    embed_resolution_report_into_bundle,
    enforce_resolution_mode,
    parse_market_data_refs_document,
    resolve_market_data_refs,
    write_resolution_report_json,
)
from src.execution.replay_pack.compare import generate_compare_report


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


EXIT_OK = 0
EXIT_CONTRACT = 2
EXIT_HASH = 3
EXIT_REPLAY_MISMATCH = 4
EXIT_UNEXPECTED = 5
EXIT_MISSING_REQUIRED_DATAREF = 6


def _cmd_build(args: argparse.Namespace) -> int:
    try:
        build_replay_pack(
            args.run_id_or_dir,
            args.out,
            created_at_utc_override=args.created_at_utc,
            include_outputs=args.include_outputs,
        )
        return EXIT_OK
    except ContractViolationError as e:
        _eprint(f"ContractViolationError: {e}")
        return EXIT_CONTRACT
    except (FileNotFoundError, ValueError) as e:
        _eprint(f"ContractViolationError: {type(e).__name__}: {e}")
        return EXIT_CONTRACT
    except Exception as e:
        _eprint(f"UnexpectedError: {type(e).__name__}: {e}")
        return EXIT_UNEXPECTED


def _cmd_validate(args: argparse.Namespace) -> int:
    try:
        validate_replay_pack(args.bundle)
        return EXIT_OK
    except HashMismatchError as e:
        _eprint(f"HashMismatchError: {e}")
        return EXIT_HASH
    except ContractViolationError as e:
        _eprint(f"ContractViolationError: {e}")
        return EXIT_CONTRACT
    except Exception as e:
        _eprint(f"UnexpectedError: {type(e).__name__}: {e}")
        return EXIT_UNEXPECTED


def _cmd_replay(args: argparse.Namespace) -> int:
    try:
        return int(
            replay_bundle(
                args.bundle,
                check_outputs=args.check_outputs,
                resolve_datarefs=args.resolve_datarefs,
                cache_root=args.cache_root,
                datarefs_generated_at_utc=args.generated_at_utc,
            )
        )
    except ReplayMismatchError as e:
        _eprint(f"ReplayMismatchError: {e}")
        return EXIT_REPLAY_MISMATCH
    except HashMismatchError as e:
        _eprint(f"HashMismatchError: {e}")
        return EXIT_HASH
    except ContractViolationError as e:
        _eprint(f"ContractViolationError: {e}")
        return EXIT_CONTRACT
    except Exception as e:
        _eprint(f"UnexpectedError: {type(e).__name__}: {e}")
        return EXIT_UNEXPECTED


def _cmd_resolve_datarefs(args: argparse.Namespace) -> int:
    bundle_root = Path(args.bundle)
    cache_root = args.cache_root or os.environ.get("PEAK_TRADE_DATA_CACHE_ROOT") or ""
    if not cache_root:
        _eprint("ContractViolationError: missing --cache-root (or PEAK_TRADE_DATA_CACHE_ROOT)")
        return EXIT_CONTRACT

    mode: ResolutionMode = args.mode

    try:
        # Ensure bundle is structurally valid (includes strict schema checks for market_data_refs if present).
        validate_replay_pack(bundle_root)
        bundle = load_replay_pack(bundle_root)

        doc = bundle.market_data_refs()
        refs = parse_market_data_refs_document(doc) if doc is not None else []

        generated_at = args.generated_at_utc or str(bundle.manifest.get("created_at_utc") or "")
        report = resolve_market_data_refs(
            bundle_root,
            refs,
            cache_root,
            mode=mode,
            bundle_id=str(bundle.manifest.get("bundle_id") or ""),
            run_id=str(bundle.manifest.get("run_id") or ""),
            generated_at_utc=generated_at,
            run_id_for_report=str(bundle.manifest.get("run_id") or ""),
        )

        # Write report deterministically.
        out_arg = args.out
        if out_arg is None:
            embed_resolution_report_into_bundle(bundle_root=bundle_root, report=report)
        else:
            out_path = Path(out_arg)
            if not out_path.is_absolute():
                out_path = bundle_root / out_path
            if out_path.exists() and out_path.is_dir():
                out_path = out_path / "resolution_report.json"
            # If the output is inside the bundle, keep it hash-protected via sha256sums.
            try:
                rel = out_path.resolve().relative_to(bundle_root.resolve()).as_posix()
                embed_resolution_report_into_bundle(
                    bundle_root=bundle_root,
                    report=report,
                    relpath=rel,
                )
            except Exception:
                write_resolution_report_json(out_path, report)

        # Enforce strict mode *after* writing report.
        try:
            enforce_resolution_mode(mode=mode, refs=refs, report=report)
        except MissingRequiredDataRefError as e:
            _eprint(f"MissingRequiredDataRefError: {e}")
            return EXIT_MISSING_REQUIRED_DATAREF
        except DataRefHashMismatchError as e:
            _eprint(f"DataRefHashMismatchError: {e}")
            return EXIT_HASH

        return EXIT_OK

    except HashMismatchError as e:
        _eprint(f"HashMismatchError: {e}")
        return EXIT_HASH
    except (SchemaValidationError, ContractViolationError, ValueError) as e:
        _eprint(f"ContractViolationError: {type(e).__name__}: {e}")
        return EXIT_CONTRACT
    except Exception as e:
        _eprint(f"UnexpectedError: {type(e).__name__}: {e}")
        return EXIT_UNEXPECTED


def _cmd_compare(args: argparse.Namespace) -> int:
    try:
        code, _report = generate_compare_report(
            args.bundle,
            check_outputs=args.check_outputs,
            resolve_datarefs=args.resolve_datarefs,
            cache_root=args.cache_root,
            generated_at_utc=args.generated_at_utc,
            out_path=args.out,
        )
        return int(code)
    except Exception as e:
        _eprint(f"UnexpectedError: {type(e).__name__}: {e}")
        return EXIT_UNEXPECTED


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pt_replay_pack", add_help=True)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Build a replay bundle")
    p_build.add_argument("--run-id-or-dir", required=True, help="run_id or run directory")
    p_build.add_argument(
        "--out", required=True, help="output directory (bundle created under this)"
    )
    p_build.add_argument(
        "--created-at-utc",
        default=None,
        help="override created_at_utc ISO8601 (for deterministic tests)",
    )
    p_build.add_argument("--include-outputs", action="store_true", help="write expected outputs")
    p_build.set_defaults(func=_cmd_build)

    p_val = sub.add_parser("validate", help="Validate a replay bundle")
    p_val.add_argument("--bundle", required=True, help="bundle root directory")
    p_val.set_defaults(func=_cmd_validate)

    p_rep = sub.add_parser("replay", help="Replay a bundle deterministically")
    p_rep.add_argument("--bundle", required=True, help="bundle root directory")
    p_rep.add_argument("--check-outputs", action="store_true", help="compare to expected outputs")
    p_rep.add_argument(
        "--resolve-datarefs",
        nargs="?",
        const="best_effort",
        default=None,
        choices=["best_effort", "strict"],
        help="optionally resolve market_data_refs offline before replay",
    )
    p_rep.add_argument(
        "--cache-root",
        default=None,
        help="local cache root (defaults to PEAK_TRADE_DATA_CACHE_ROOT if set)",
    )
    p_rep.add_argument(
        "--generated-at-utc",
        default=None,
        help="override generated_at_utc for the datarefs report (for deterministic tests)",
    )
    p_rep.set_defaults(func=_cmd_replay)

    p_res = sub.add_parser("resolve-datarefs", help="Resolve market_data_refs offline")
    p_res.add_argument("--bundle", required=True, help="bundle root directory")
    p_res.add_argument(
        "--cache-root",
        default=None,
        help="local cache root (defaults to PEAK_TRADE_DATA_CACHE_ROOT if set)",
    )
    p_res.add_argument(
        "--mode",
        default="best_effort",
        choices=["best_effort", "strict"],
        help="resolution mode (strict fails on missing required refs or hash mismatch)",
    )
    p_res.add_argument(
        "--out",
        default=None,
        help="write report to this path (default: meta/resolution_report.json inside bundle)",
    )
    p_res.add_argument(
        "--generated-at-utc",
        default=None,
        help="override generated_at_utc for deterministic tests",
    )
    p_res.set_defaults(func=_cmd_resolve_datarefs)

    p_cmp = sub.add_parser(
        "compare", help="Generate deterministic compare report (baseline vs replay)"
    )
    p_cmp.add_argument("--bundle", required=True, help="bundle root directory")
    p_cmp.add_argument(
        "--check-outputs", action="store_true", help="compare to expected outputs if present"
    )
    p_cmp.add_argument(
        "--resolve-datarefs",
        nargs="?",
        const="best_effort",
        default=None,
        choices=["best_effort", "strict"],
        help="optionally resolve market_data_refs offline before compare",
    )
    p_cmp.add_argument(
        "--cache-root",
        default=None,
        help="local cache root (defaults to PEAK_TRADE_DATA_CACHE_ROOT if set)",
    )
    p_cmp.add_argument(
        "--generated-at-utc",
        default=None,
        help="override generated_at_utc for deterministic tests",
    )
    p_cmp.add_argument(
        "--out",
        default=None,
        help="write compare report to this path (default: meta/compare_report.json inside bundle)",
    )
    p_cmp.set_defaults(func=_cmd_compare)

    ns = parser.parse_args(argv)
    return int(ns.func(ns))


if __name__ == "__main__":
    raise SystemExit(main())
