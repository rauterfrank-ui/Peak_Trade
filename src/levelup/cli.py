"""
Minimal CLI for Level-Up v0 manifests (validate / format / schema export / round-trip checks).

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

canonical-check exit contract (stdout is one JSON object per invocation):
- 0 — manifest validated and already canonical
- 2 — usage / input problem (unreadable path, invalid JSON, UTF-8 decode)
- 3 — model / schema validation failed, or manifest is valid but not canonical

export-json-schema exit contract (stdout is one JSON object per invocation):
- 0 — schema export succeeded

describe-slice exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed, model-validated, slice_id found
- 2 — usage / input problem (same as validate: unreadable path, invalid JSON, UTF-8 decode)
- 3 — JSON ok but model / schema validation failed, or manifest valid but slice_id not found

list-slices exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed, model-validated; stdout lists slice_id values in manifest order
- 2 — usage / input problem (same as validate)
- 3 — JSON ok but model / schema validation failed

check-evidence exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed, model-validated; every slice with evidence has an existing directory at repo-relative path
- 2 — usage / input problem (same as validate), or repository root could not be resolved from the manifest path
- 3 — manifest ok but at least one evidence path is missing or not a directory
"""

from __future__ import annotations

import argparse
import json
import sys
from json import JSONDecodeError
from pathlib import Path

from pydantic import ValidationError

from src.levelup.v0_io import canonical_manifest_json, read_manifest, write_manifest
from src.levelup.v0_models import LevelUpManifestV0, levelup_manifest_v0_json_schema

EXIT_VALIDATION_OK = 0
EXIT_INPUT = 2
EXIT_VALIDATION_FAILED = 3


def _find_peak_trade_repo_root(manifest_path: Path) -> Path | None:
    """Walk parents from *manifest_path* for a checkout marker (pyproject + src/levelup)."""
    resolved = manifest_path.resolve()
    anchor = resolved.parent if resolved.is_file() else resolved
    for p in [anchor, *anchor.parents]:
        if (p / "pyproject.toml").is_file() and (p / "src" / "levelup").is_dir():
            return p
    return None


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


def _cmd_canonical_check(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    try:
        current = path.read_text(encoding="utf-8")
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

    expected = canonical_manifest_json(m)
    if current != expected:
        _emit_json(
            {
                "ok": False,
                "error": "validation",
                "reason": "manifest_not_canonical",
                "message": "manifest is valid but not in canonical serialized form",
                "canonical": False,
                "schema": m.schema_version,
                "slices": len(m.slices),
            }
        )
        return EXIT_VALIDATION_FAILED

    _emit_json({"ok": True, "canonical": True, "schema": m.schema_version, "slices": len(m.slices)})
    return EXIT_VALIDATION_OK


def _cmd_export_json_schema() -> int:
    schema = levelup_manifest_v0_json_schema()
    _emit_json({"ok": True, "schema": LevelUpManifestV0().schema_version, "json_schema": schema})
    return EXIT_VALIDATION_OK


def _cmd_describe_slice(path: Path, slice_id: str) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    for sl in m.slices:
        if sl.slice_id == slice_id:
            _emit_json(
                {
                    "ok": True,
                    "schema": m.schema_version,
                    "command": "describe-slice",
                    "slice_id": sl.slice_id,
                    "title": sl.title,
                    "contract_summary": sl.contract_summary,
                    "evidence": sl.evidence.model_dump(mode="json")
                    if sl.evidence is not None
                    else None,
                }
            )
            return EXIT_VALIDATION_OK

    _emit_json(
        {
            "ok": False,
            "error": "validation",
            "reason": "slice_not_found",
            "message": f"no slice with slice_id {slice_id!r} in manifest",
            "schema": m.schema_version,
            "slice_id": slice_id,
        }
    )
    return EXIT_VALIDATION_FAILED


def _cmd_list_slices(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    ids = [sl.slice_id for sl in m.slices]
    _emit_json(
        {
            "ok": True,
            "schema": m.schema_version,
            "command": "list-slices",
            "count": len(ids),
            "slices": ids,
        }
    )
    return EXIT_VALIDATION_OK


def _cmd_check_evidence(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    repo_root = _find_peak_trade_repo_root(path)
    if repo_root is None:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "repo_root_not_found",
                "message": (
                    "could not locate repository root (expected pyproject.toml and src/levelup/ "
                    "on the parent chain of the manifest path)"
                ),
            }
        )
        return EXIT_INPUT

    entries: list[dict[str, object]] = []
    for sl in m.slices:
        if sl.evidence is None:
            continue
        rel = sl.evidence.relative_dir
        target = repo_root / rel
        exists = target.exists()
        is_dir = target.is_dir()
        entries.append(
            {
                "slice_id": sl.slice_id,
                "evidence": rel,
                "exists": exists,
                "is_dir": is_dir,
            }
        )

    missing_count = sum(1 for e in entries if not e["exists"])
    not_dir_count = sum(1 for e in entries if e["exists"] and not e["is_dir"])
    ok = missing_count == 0 and not_dir_count == 0

    _emit_json(
        {
            "ok": ok,
            "schema": m.schema_version,
            "command": "check-evidence",
            "manifest_path": str(path.resolve()),
            "checked_count": len(entries),
            "missing_count": missing_count,
            "not_dir_count": not_dir_count,
            "entries": entries,
        }
    )
    return EXIT_VALIDATION_OK if ok else EXIT_VALIDATION_FAILED


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

    p_check = sub.add_parser(
        "canonical-check",
        help="Validate a v0 manifest and check if it is already canonical (read-only).",
    )
    p_check.add_argument("manifest", type=Path, help="Path to existing manifest.json")

    sub.add_parser(
        "export-json-schema",
        help="Export the LevelUpManifestV0 JSON schema as one JSON object on stdout.",
    )

    p_desc = sub.add_parser(
        "describe-slice",
        help="Print one slice contract from a v0 manifest as one JSON object on stdout (read-only).",
    )
    p_desc.add_argument("manifest", type=Path, help="Path to manifest.json")
    p_desc.add_argument("slice_id", help="slice_id to resolve inside the manifest")

    p_list = sub.add_parser(
        "list-slices",
        help="List slice_id values from a v0 manifest as one JSON object on stdout (read-only).",
    )
    p_list.add_argument("manifest", type=Path, help="Path to manifest.json")

    p_ev = sub.add_parser(
        "check-evidence",
        help=(
            "Verify repo-relative evidence directories for slices (read-only; one JSON line on stdout)."
        ),
    )
    p_ev.add_argument("manifest", type=Path, help="Path to manifest.json")

    args = parser.parse_args(argv)
    if args.cmd == "validate":
        return _cmd_validate(args.manifest)
    if args.cmd == "dump-empty":
        return _cmd_dump_empty(args.manifest)
    if args.cmd == "format":
        return _cmd_format(args.manifest)
    if args.cmd == "canonical-check":
        return _cmd_canonical_check(args.manifest)
    if args.cmd == "export-json-schema":
        return _cmd_export_json_schema()
    if args.cmd == "describe-slice":
        return _cmd_describe_slice(args.manifest, args.slice_id)
    if args.cmd == "list-slices":
        return _cmd_list_slices(args.manifest)
    if args.cmd == "check-evidence":
        return _cmd_check_evidence(args.manifest)
    return EXIT_INPUT


if __name__ == "__main__":
    sys.exit(main())
