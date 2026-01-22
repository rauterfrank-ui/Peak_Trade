from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Iterable, Mapping, Sequence


def _to_jsonable(obj: Any) -> Any:
    """
    Convert to JSON-safe primitives deterministically.

    Rule: persisted artifacts must not contain binary floats; Decimals are serialized as strings.
    """
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, Mapping):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    return obj


def canonical_json_line(obj: Mapping[str, Any]) -> str:
    """
    Canonical JSON object as a single line (no trailing newline).
    """
    return json.dumps(
        _to_jsonable(dict(obj)), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def canonical_json_bytes(obj: Mapping[str, Any]) -> bytes:
    """
    Canonical JSON bytes (utf-8).
    """
    return (canonical_json_line(obj) + "\n").encode("utf-8")


def canonical_jsonl_bytes(objs: Iterable[Mapping[str, Any]]) -> bytes:
    """
    Canonical JSONL bytes (utf-8) with '\n' line endings.
    """
    parts: list[str] = []
    for o in objs:
        parts.append(canonical_json_line(o))
    # Always end with a newline to make artifacts stable for concatenation.
    return ("\n".join(parts) + "\n").encode("utf-8")
