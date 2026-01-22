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
import sys
from pathlib import Path

# Add repo root to path for imports (scripts -> repo root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.execution.replay_pack.builder import build_replay_pack
from src.execution.replay_pack.runner import replay_bundle
from src.execution.replay_pack.validator import validate_replay_pack
from src.execution.replay_pack.contract import ContractViolationError


def _cmd_build(args: argparse.Namespace) -> int:
    build_replay_pack(
        args.run_id_or_dir,
        args.out,
        created_at_utc_override=args.created_at_utc,
        include_outputs=args.include_outputs,
    )
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    try:
        validate_replay_pack(args.bundle)
        return 0
    except ContractViolationError:
        return 2
    except Exception:
        return 2


def _cmd_replay(args: argparse.Namespace) -> int:
    return replay_bundle(args.bundle, check_outputs=args.check_outputs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pt_replay_pack", add_help=True)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Build a replay bundle")
    p_build.add_argument("--run-id-or-dir", required=True, help="run_id or run directory")
    p_build.add_argument("--out", required=True, help="output directory (bundle created under this)")
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
    p_rep.set_defaults(func=_cmd_replay)

    ns = parser.parse_args(argv)
    return int(ns.func(ns))


if __name__ == "__main__":
    raise SystemExit(main())
