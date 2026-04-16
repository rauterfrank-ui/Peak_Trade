"""
Minimal CLI for Level-Up v0 manifests (validate / round-trip checks).

Does not connect to exchanges or change execution posture.

validate exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed and model-validated
- 2 — usage / input problem (unreadable path, invalid JSON, UTF-8 decode)
- 3 — JSON ok but model / schema validation failed
"""

from __future__ import annotations

import argparse
import json
import sys
from json import JSONDecodeError
from pathlib import Path

from pydantic import ValidationError

from src.levelup.v0_io import read_manifest
from src.levelup.v0_models import LevelUpManifestV0

EXIT_VALIDATION_OK = 0
EXIT_INPUT = 2
EXIT_VALIDATION_FAILED = 3


def _emit_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _cmd_validate(path: Path) -> int:
    try:
        m = read_manifest(path)
    except OSError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "manifest_read_failed",
                "message": str(exc),
            }
        )
        return EXIT_INPUT
    except UnicodeDecodeError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "utf8_decode_failed",
                "message": str(exc),
            }
        )
        return EXIT_INPUT
    except JSONDecodeError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "json_parse_failed",
                "message": str(exc),
            }
        )
        return EXIT_INPUT
    except ValidationError as exc:
        issues = exc.errors()
        if issues and issues[0].get("type") == "json_invalid":
            msg = str(issues[0].get("msg") or "invalid JSON")
            _emit_json(
                {
                    "ok": False,
                    "error": "input",
                    "reason": "json_parse_failed",
                    "message": msg,
                }
            )
            return EXIT_INPUT
        issues = issues[:8]
        _emit_json(
            {
                "ok": False,
                "error": "validation",
                "reason": "model_validation_failed",
                "message": "manifest failed LevelUpManifestV0 validation",
                "issues": issues,
            }
        )
        return EXIT_VALIDATION_FAILED

    _emit_json({"ok": True, "schema": m.schema_version, "slices": len(m.slices)})
    return EXIT_VALIDATION_OK


def _cmd_dump_empty(path: Path) -> int:
    m = LevelUpManifestV0()
    from src.levelup.v0_io import write_manifest

    write_manifest(path, m)
    _emit_json({"ok": True, "wrote": str(path)})
    return EXIT_VALIDATION_OK


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
    return EXIT_INPUT


if __name__ == "__main__":
    sys.exit(main())
