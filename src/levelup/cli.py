"""
Minimal CLI for Level-Up v0 manifests (validate / round-trip checks).

Does not connect to exchanges or change execution posture.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.levelup.v0_io import read_manifest
from src.levelup.v0_models import LevelUpManifestV0


def _cmd_validate(path: Path) -> int:
    m = read_manifest(path)
    print(json.dumps({"ok": True, "schema": m.schema_version, "slices": len(m.slices)}))
    return 0


def _cmd_dump_empty(path: Path) -> int:
    m = LevelUpManifestV0()
    from src.levelup.v0_io import write_manifest

    write_manifest(path, m)
    print(json.dumps({"ok": True, "wrote": str(path)}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.levelup.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="Validate a levelup manifest JSON file.")
    p_val.add_argument("manifest", type=Path, help="Path to manifest.json")

    p_dump = sub.add_parser(
        "dump-empty",
        help="Write an empty v0 manifest (template) to the given path.",
    )
    p_dump.add_argument("manifest", type=Path, help="Output path")

    args = parser.parse_args(argv)
    if args.cmd == "validate":
        return _cmd_validate(args.manifest)
    if args.cmd == "dump-empty":
        return _cmd_dump_empty(args.manifest)
    return 2


if __name__ == "__main__":
    sys.exit(main())
