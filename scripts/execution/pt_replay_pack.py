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
import json
import os
import sys
from pathlib import Path

# Add repo root to path for imports (scripts -> repo root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.execution.replay_pack.builder import build_replay_pack
from src.execution.replay_pack.loader import load_replay_pack
from src.execution.replay_pack.runner import replay_bundle
from src.execution.replay_pack.validator import validate_replay_pack
from src.execution.replay_pack.hashing import parse_sha256sums_text, sha256_file
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


def _short_sha256(s: str | None) -> str | None:
    if s is None:
        return None
    if not isinstance(s, str) or len(s) != 64:
        return None
    return f"{s[:8]}...{s[-8:]}"


def _count_non_empty_lines(p: Path) -> int:
    """
    Deterministic line count for JSONL-like files.
    Counts non-empty lines (after strip()).
    """
    n = 0
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def inspect_bundle(bundle_root: Path) -> dict:
    """
    Pure(ish) deterministic bundle summary (no wall-clock).

    Note: bundle_root is resolved to an absolute path for clarity.
    """
    root = Path(bundle_root).resolve()
    bundle = load_replay_pack(root)
    manifest = bundle.manifest
    contract_version = str(manifest.get("contract_version") or "1")

    # Presence matrix (file existence on disk).
    p_manifest = root / "manifest.json"
    p_events = root / "events" / "execution_events.jsonl"
    p_sums = root / "hashes" / "sha256sums.txt"
    p_fifo_snap = root / "ledger" / "ledger_fifo_snapshot.json"
    p_fifo_entries = root / "ledger" / "ledger_fifo_entries.jsonl"
    presence = {
        "events": p_events.exists(),
        "hashes": p_sums.exists(),
        "manifest": p_manifest.exists(),
        "fifo_snapshot": p_fifo_snap.exists(),
        "fifo_entries": p_fifo_entries.exists(),
    }

    # File inventory (deterministic ordering).
    relpaths = sorted(
        [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()]
    )

    inv = manifest.get("invariants")
    inv_obj = inv if isinstance(inv, dict) else {}
    invariants = {
        "has_execution_events": inv_obj.get("has_execution_events")
        if isinstance(inv_obj.get("has_execution_events"), bool)
        else None,
        "ordering": inv_obj.get("ordering")
        if isinstance(inv_obj.get("ordering"), str)
        else None,
        "has_fifo_ledger": inv_obj.get("has_fifo_ledger")
        if isinstance(inv_obj.get("has_fifo_ledger"), bool)
        else None,
        "fifo_engine": inv_obj.get("fifo_engine")
        if isinstance(inv_obj.get("fifo_engine"), str)
        else None,
    }
    # Derive has_fifo_ledger:
    # - prefer explicit manifest invariants when present
    # - else derive from presence (snapshot/entries on disk)
    derived_has_fifo_ledger = (
        invariants["has_fifo_ledger"]
        if isinstance(invariants["has_fifo_ledger"], bool)
        else bool(presence["fifo_snapshot"] or presence["fifo_entries"])
    )

    # sha256 summary
    manifest_sha = sha256_file(p_manifest) if p_manifest.exists() else None
    sums_sha = sha256_file(p_sums) if p_sums.exists() else None
    sums_count = None
    if p_sums.exists():
        sums_text = p_sums.read_text(encoding="utf-8")
        sums = parse_sha256sums_text(sums_text)
        sums_count = len(sums)

    # Basic counts
    events_lines = _count_non_empty_lines(p_events) if p_events.exists() else None
    fifo_entries_lines = (
        _count_non_empty_lines(p_fifo_entries) if p_fifo_entries.exists() else None
    )

    # FIFO snapshot summary
    fifo_snapshot = {"ts_utc_last": None, "seq_last": None}
    if p_fifo_snap.exists():
        try:
            snap = json.loads(p_fifo_snap.read_text(encoding="utf-8"))
            if isinstance(snap, dict):
                ts_last = snap.get("ts_utc_last")
                seq_last = snap.get("seq_last")
                fifo_snapshot["ts_utc_last"] = ts_last if isinstance(ts_last, str) else None
                fifo_snapshot["seq_last"] = int(seq_last) if isinstance(seq_last, int) else None
        except Exception:
            # Inspect should be best-effort; validate() is the strict gate.
            fifo_snapshot = {"ts_utc_last": None, "seq_last": None}

    out = {
        # Back-compat keys (existing smoke tests rely on these).
        "bundle_root": str(root),
        "contract_version": contract_version,
        "bundle_id": str(manifest.get("bundle_id") or ""),
        "run_id": str(manifest.get("run_id") or ""),
        "created_at_utc": str(manifest.get("created_at_utc") or ""),
        "has_fifo_ledger": bool(derived_has_fifo_ledger),
        "files": relpaths,
        "file_count": len(relpaths),
        "manifest_sha256": manifest_sha,
        "sha256sums_sha256": sums_sha,
        "sha256sums_count": sums_count,
        # New structured fields.
        "presence": {
            "events/execution_events.jsonl": bool(presence["events"]),
            "hashes/sha256sums.txt": bool(presence["hashes"]),
            "manifest.json": bool(presence["manifest"]),
            "ledger/ledger_fifo_snapshot.json": bool(presence["fifo_snapshot"]),
            "ledger/ledger_fifo_entries.jsonl": bool(presence["fifo_entries"]),
        },
        "manifest": {
            "bundle_id": str(manifest.get("bundle_id") or ""),
            "run_id": str(manifest.get("run_id") or ""),
            "created_at_utc": str(manifest.get("created_at_utc") or ""),
            "invariants": invariants,
        },
        "sha256": {
            "manifest": {"full": manifest_sha, "short": _short_sha256(manifest_sha)},
            "sha256sums": {
                "full": sums_sha,
                "short": _short_sha256(sums_sha),
                "count": sums_count,
            },
        },
        "counts": {
            "file_count": len(relpaths),
            "events_lines": events_lines,
            "fifo_entries_lines": fifo_entries_lines,
        },
        "fifo_snapshot": fifo_snapshot,
    }
    return out


def inspect_bundle_json(bundle_root: Path) -> dict:
    """
    Machine output for `pt_replay_pack inspect --json`.

    Contract: stable keys, stable types; no wall-clock.
    """
    out = inspect_bundle(bundle_root)
    p = out["presence"]
    inv = out["manifest"]["invariants"]

    entries_present = bool(p.get("ledger/ledger_fifo_entries.jsonl"))
    json_out = {
        "bundle": str(out["bundle_root"]),
        "contract_version": str(out["contract_version"]),
        "files": {
            "manifest_json": bool(p.get("manifest.json")),
            "sha256sums_txt": bool(p.get("hashes/sha256sums.txt")),
            "execution_events_jsonl": bool(p.get("events/execution_events.jsonl")),
            "ledger_fifo_snapshot_json": bool(p.get("ledger/ledger_fifo_snapshot.json")),
            "ledger_fifo_entries_jsonl": bool(p.get("ledger/ledger_fifo_entries.jsonl")),
        },
        "hashes": {
            "sha256sums_count": out["sha256"]["sha256sums"]["count"],
            "manifest_sha256": out["sha256"]["manifest"]["full"],
        },
        "events": {"lines": out["counts"]["events_lines"]},
        "fifo": {
            "has_fifo_ledger": bool(out["has_fifo_ledger"]),
            "fifo_engine": inv.get("fifo_engine"),
            "last_ts_utc": out["fifo_snapshot"]["ts_utc_last"],
            "last_seq": out["fifo_snapshot"]["seq_last"],
            "entries_lines": out["counts"]["fifo_entries_lines"] if entries_present else None,
        },
    }
    return json_out


def _cmd_build(args: argparse.Namespace) -> int:
    try:
        version = str(args.version)
        include_fifo = version == "2"
        build_replay_pack(
            args.run_id_or_dir,
            args.out,
            bundle_version=version,  # type: ignore[arg-type]
            include_fifo=include_fifo,
            include_fifo_entries=bool(args.include_fifo_entries),
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


def _cmd_inspect(args: argparse.Namespace) -> int:
    """
    Print deterministic bundle summary (no wall-clock).
    """
    try:
        out = inspect_bundle(Path(args.bundle))
        if args.json:
            json_out = inspect_bundle_json(Path(args.bundle))
            print(json.dumps(json_out, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        else:
            # Human-friendly, deterministic ordering.
            print("ReplayPack Inspect")
            print(f"bundle: {out['bundle_root']}")
            print(f"contract_version: {out['contract_version']}")

            print("files:")
            def _present(k: str) -> str:
                return "present" if bool(out["presence"].get(k)) else "absent"

            print(f"  manifest.json: {_present('manifest.json')}")
            print(f"  hashes/sha256sums.txt: {_present('hashes/sha256sums.txt')}")
            print(f"  events/execution_events.jsonl: {_present('events/execution_events.jsonl')}")
            print(
                f"  ledger/ledger_fifo_snapshot.json: {_present('ledger/ledger_fifo_snapshot.json')}"
            )
            print(
                f"  ledger/ledger_fifo_entries.jsonl: {_present('ledger/ledger_fifo_entries.jsonl')}"
            )

            print("hashes:")
            print(f"  sha256sums_count: {out['sha256']['sha256sums']['count']}")
            print(f"  manifest_sha256: {out['sha256']['manifest']['full']}")

            print("events:")
            print(f"  lines: {out['counts']['events_lines']}")

            inv = out["manifest"]["invariants"]
            derived_has_fifo = out["has_fifo_ledger"]
            print("fifo:")
            print(f"  has_fifo_ledger: {str(derived_has_fifo).lower()}")
            print(f"  fifo_engine: {inv['fifo_engine']}")
            print(f"  last_ts_utc: {out['fifo_snapshot']['ts_utc_last']}")
            print(f"  last_seq: {out['fifo_snapshot']['seq_last']}")
            if out["presence"].get("ledger/ledger_fifo_entries.jsonl"):
                print(f"  entries_lines: {out['counts']['fifo_entries_lines']}")
        return EXIT_OK
    except (SchemaValidationError, ContractViolationError, FileNotFoundError, ValueError) as e:
        _eprint(f"ContractViolationError: {type(e).__name__}: {e}")
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
    src = p_build.add_mutually_exclusive_group(required=True)
    src.add_argument("--run-id-or-dir", help="run_id or run directory")
    src.add_argument("--events", help="path to execution_events.jsonl (BETA_EXEC_V1)")
    p_build.add_argument(
        "--out", required=True, help="output directory (bundle created under this)"
    )
    p_build.add_argument(
        "--version",
        default="1",
        choices=["1", "2"],
        help="bundle contract version (1=legacy, 2=additive FIFO ledger artifacts)",
    )
    p_build.add_argument(
        "--include-fifo-entries",
        action="store_true",
        help="(v2 only) include ledger/ledger_fifo_entries.jsonl",
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

    p_ins = sub.add_parser("inspect", help="Inspect a replay bundle (metadata + file list)")
    p_ins.add_argument("--bundle", required=True, help="bundle root directory")
    p_ins.add_argument("--json", action="store_true", help="print machine-readable JSON")
    p_ins.set_defaults(func=_cmd_inspect)

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
    # Build uses either --run-id-or-dir or --events.
    if getattr(ns, "cmd", None) == "build":
        if getattr(ns, "events", None):
            ns.run_id_or_dir = ns.events
    return int(ns.func(ns))


if __name__ == "__main__":
    raise SystemExit(main())
