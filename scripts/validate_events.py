from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


def _iter_jsonl(path: Path) -> Iterable[Tuple[int, Dict[str, Any]]]:
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}: line {i}: invalid json: {e}") from e
        if not isinstance(obj, dict):
            raise ValueError(f"{path}: line {i}: expected object, got {type(obj).__name__}")
        yield i, obj


def _load_schema(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _basic_required_check(obj: Dict[str, Any], required: Iterable[str]) -> None:
    missing = [k for k in required if k not in obj]
    if missing:
        raise ValueError(f"missing required fields: {missing}")


def validate_jsonl(jsonl_path: Path, schema_path: Path, *, strict: bool = False) -> None:
    schema = _load_schema(schema_path)

    # Prefer jsonschema if available; otherwise fallback to minimal required-field check.
    validator = None
    try:
        import jsonschema  # type: ignore

        validator = jsonschema.Draft202012Validator(schema)
    except Exception:
        validator = None

    required = schema.get("required", [])

    for line_no, obj in _iter_jsonl(jsonl_path):
        if validator is not None:
            errors = sorted(validator.iter_errors(obj), key=lambda e: e.path)
            if errors:
                msg = errors[0].message
                loc = ".".join([str(x) for x in errors[0].path]) or "<root>"
                raise ValueError(f"{jsonl_path}: line {line_no}: schema error at {loc}: {msg}")
        else:
            _basic_required_check(obj, required)
            if strict:
                # In strict mode (no jsonschema), do a tiny extra sanity check on schema_version const
                sv = obj.get("schema_version")
                const = schema.get("properties", {}).get("schema_version", {}).get("const")
                if const is not None and sv != const:
                    raise ValueError(
                        f"{jsonl_path}: line {line_no}: schema_version {sv!r} != {const!r}"
                    )


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Validate JSONL events against JSON schema.")
    ap.add_argument("--schema", required=True, help="Path to JSON schema file")
    ap.add_argument("--jsonl", required=True, help="Path to JSONL file to validate")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="If jsonschema is unavailable, enable extra checks (schema_version const).",
    )
    args = ap.parse_args(argv)

    jsonl_path = Path(args.jsonl)
    schema_path = Path(args.schema)
    try:
        validate_jsonl(jsonl_path, schema_path, strict=args.strict)
    except Exception as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 2
    print("[OK] events validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
