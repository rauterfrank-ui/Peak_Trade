"""
Minimal CLI for Level-Up v0 manifests (validate / format / round-trip checks).

Does not connect to exchanges or change execution posture.

validate exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed and model-validated
- 2 — usage / input problem (unreadable path, invalid JSON, UTF-8 decode)
- 3 — JSON ok but model / schema validation failed

dump-empty exit contract (stdout is one JSON object per invocation):
- 0 — empty manifest written
- 2 — usage / path / write problem (e.g. target is a directory, mkdir/write permission)

format exit contract (stdout is one JSON object per invocation):
- 0 — manifest validated and canonically rewritten
- 2 — usage / input problem (unreadable path, invalid JSON, UTF-8 decode) or write problem
- 3 — JSON ok but model / schema validation failed
"""

from __future__ import annotations

import argparse
import json
import sys
from json import JSONDecodeError
from pathlib import Path

from pydantic import ValidationError

from src.levelup.v0_io import read_manifest, write_manifest
from src.levelup.v0_models import LevelUpManifestV0

EXIT_VALIDATION_OK = 0
EXIT_INPUT = 2
EXIT_VALIDATION_FAILED = 3


def _emit_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _read_manifest_with_contract(path: Path) -> tuple[LevelUpManifestV0 | None, int | None]:
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
        return None, EXIT_INPUT
    except UnicodeDecodeError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "utf8_decode_failed",
                "message": str(exc),
            }
        )
        return None, EXIT_INPUT
    except JSONDecodeError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "json_parse_failed",
                "message": str(exc),
            }
        )
        return None, EXIT_INPUT
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
            return None, EXIT_INPUT
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
        return None, EXIT_VALIDATION_FAILED

    return m, None


def _cmd_validate(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    _emit_json({"ok": True, "schema": m.schema_version, "slices": len(m.slices)})
    return EXIT_VALIDATION_OK


def _cmd_dump_empty(path: Path) -> int:
    m = LevelUpManifestV0()
    try:
        write_manifest(path, m)
    except IsADirectoryError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "target_path_is_directory",
                "message": str(exc),
            }
        )
        return EXIT_INPUT
    except OSError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "manifest_write_failed",
                "message": str(exc),
            }
        )
        return EXIT_INPUT

    _emit_json({"ok": True, "wrote": str(path)})
    return EXIT_VALIDATION_OK


def _cmd_format(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    try:
        write_manifest(path, m)
    except IsADirectoryError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "target_path_is_directory",
                "message": str(exc),
            }
        )
        return EXIT_INPUT
    except OSError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "manifest_write_failed",
                "message": str(exc),
            }
        )
        return EXIT_INPUT

    _emit_json(
        {"ok": True, "wrote": str(path), "schema": m.schema_version, "slices": len(m.slices)}
    )
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

    p_format = sub.add_parser(
        "format",
        help="Validate and canonically rewrite an existing v0 manifest in place.",
    )
    p_format.add_argument("manifest", type=Path, help="Path to existing manifest.json")

    args = parser.parse_args(argv)
    if args.cmd == "validate":
        return _cmd_validate(args.manifest)
    if args.cmd == "dump-empty":
        return _cmd_dump_empty(args.manifest)
    if args.cmd == "format":
        return _cmd_format(args.manifest)
    return EXIT_INPUT


if __name__ == "__main__":
    sys.exit(main())
