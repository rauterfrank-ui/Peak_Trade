"""P39 — Registry CLI v1: inspect and verify backtest bundle registries."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from src.backtest.p35.bundle_v1 import BundleIntegrityError, verify_report_bundle_v1
from src.backtest.p36.tarball_v1 import TarballBundleError, verify_bundle_tarball_v1
from src.backtest.p37.bundle_index_v1 import (
    IndexIntegrityError,
    read_bundle_index_v1,
    verify_bundle_index_v1,
)
from src.backtest.p38.registry_v1 import RegistryError, read_registry_v1, verify_registry_v1

EXIT_OK = 0
EXIT_VERIFY_FAILED = 2
EXIT_USAGE = 3
EXIT_UNEXPECTED = 4


def _dump_json(payload: Any) -> str:
    def _default(o: Any) -> Any:
        if is_dataclass(o):
            return asdict(o)
        raise TypeError(f"not json serializable: {type(o).__name__}")

    return (
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False, default=_default) + "\n"
    )


def _print(payload: Any, *, as_json: bool) -> None:
    if as_json:
        sys.stdout.write(_dump_json(payload))
    else:
        if isinstance(payload, str):
            sys.stdout.write(payload.rstrip("\n") + "\n")
        else:
            sys.stdout.write(str(payload).rstrip("\n") + "\n")


def _cmd_verify(args: argparse.Namespace) -> int:
    try:
        if args.registry:
            p = Path(args.registry)
            verify_registry_v1(p)
            _print({"ok": True, "type": "registry", "path": str(p)}, as_json=args.json)
            return EXIT_OK

        if args.index:
            p = Path(args.index)
            idx = read_bundle_index_v1(p)
            verify_bundle_index_v1(idx, base_dir=p.parent)
            _print({"ok": True, "type": "index", "path": str(p)}, as_json=args.json)
            return EXIT_OK

        if args.bundle_dir:
            p = Path(args.bundle_dir)
            verify_report_bundle_v1(p)
            _print({"ok": True, "type": "bundle_dir", "path": str(p)}, as_json=args.json)
            return EXIT_OK

        if args.tarball:
            p = Path(args.tarball)
            verify_bundle_tarball_v1(p)
            _print({"ok": True, "type": "tarball", "path": str(p)}, as_json=args.json)
            return EXIT_OK

        return EXIT_USAGE
    except (BundleIntegrityError, TarballBundleError, IndexIntegrityError, RegistryError) as e:
        _print({"ok": False, "error": str(e)}, as_json=args.json)
        return EXIT_VERIFY_FAILED


def _cmd_list(args: argparse.Namespace) -> int:
    if args.registry:
        p = Path(args.registry)
        reg = read_registry_v1(p)
        entries = sorted(reg.entries, key=lambda e: e.ref_path)
        if args.json:
            _print(
                {"type": "registry", "path": str(p), "entries": [e.to_dict() for e in entries]},
                as_json=True,
            )
        else:
            for e in entries:
                sys.stdout.write(f"{e.ref_path}\n")
        return EXIT_OK

    if args.index:
        p = Path(args.index)
        idx = read_bundle_index_v1(p)
        entries = sorted(idx.entries, key=lambda e: e.relpath)
        if args.json:
            _print(
                {"type": "index", "path": str(p), "entries": [e.to_dict() for e in entries]},
                as_json=True,
            )
        else:
            for e in entries:
                sys.stdout.write(f"{e.relpath}\n")
        return EXIT_OK

    return EXIT_USAGE


def _cmd_show(args: argparse.Namespace) -> int:
    if args.registry:
        p = Path(args.registry)
        reg = read_registry_v1(p)
        hit = next(
            (e for e in reg.entries if e.ref_path == args.key or e.bundle_id == args.key),
            None,
        )
        if hit is None:
            _print(f"not found: {args.key}", as_json=False)
            return EXIT_VERIFY_FAILED
        _print(hit.to_dict(), as_json=args.json)
        return EXIT_OK

    if args.index:
        p = Path(args.index)
        idx = read_bundle_index_v1(p)
        hit = next((e for e in idx.entries if e.relpath == args.key), None)
        if hit is None:
            _print(f"not found: {args.key}", as_json=False)
            return EXIT_VERIFY_FAILED
        _print(hit.to_dict(), as_json=args.json)
        return EXIT_OK

    return EXIT_USAGE


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="registry_cli_v1", add_help=True)
    p.add_argument("--json", action="store_true", help="emit deterministic JSON")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("verify", help="verify registry/index/bundle artifacts")
    g = v.add_mutually_exclusive_group(required=True)
    g.add_argument("--registry", type=str, help="path to registry.json (P38)")
    g.add_argument("--index", type=str, help="path to index.json (P37)")
    g.add_argument("--bundle-dir", type=str, help="path to bundle dir (P35)")
    g.add_argument("--tarball", type=str, help="path to bundle tarball (P36)")
    v.set_defaults(_fn=_cmd_verify)

    l = sub.add_parser("list", help="list entries in stable order")
    g2 = l.add_mutually_exclusive_group(required=True)
    g2.add_argument("--registry", type=str, help="path to registry.json (P38)")
    g2.add_argument("--index", type=str, help="path to index.json (P37)")
    l.set_defaults(_fn=_cmd_list)

    s = sub.add_parser("show", help="show one entry by relpath/bundle_id")
    g3 = s.add_mutually_exclusive_group(required=True)
    g3.add_argument("--registry", type=str, help="path to registry.json (P38)")
    g3.add_argument("--index", type=str, help="path to index.json (P37)")
    s.add_argument("--key", type=str, required=True, help="entry relpath or bundle_id")
    s.set_defaults(_fn=_cmd_show)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args._fn(args))
    except SystemExit:
        return EXIT_USAGE
    except Exception as e:  # pragma: no cover
        sys.stderr.write(f"unexpected error: {e}\n")
        return EXIT_UNEXPECTED


if __name__ == "__main__":
    raise SystemExit(main())
