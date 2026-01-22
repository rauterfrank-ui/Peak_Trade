from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Mapping


class CanonicalJsonError(ValueError):
    pass


def validate_no_floats(x: Any, *, path: str = "$") -> None:
    if isinstance(x, float):
        raise CanonicalJsonError(f"float forbidden in deterministic artifacts at {path}")
    if isinstance(x, Mapping):
        for k, v in x.items():
            validate_no_floats(v, path=f"{path}.{k}")
        return
    if isinstance(x, (list, tuple)):
        for i, v in enumerate(x):
            validate_no_floats(v, path=f"{path}[{i}]")


def _to_jsonable(x: Any) -> Any:
    if isinstance(x, Decimal):
        return str(x)
    if isinstance(x, Mapping):
        # Force keys to strings deterministically.
        return {str(k): _to_jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_to_jsonable(v) for v in x]
    return x


def dumps_canonical(obj: Any) -> str:
    """
    Canonical JSON string.

    Rules:
    - sort keys
    - separators (",", ":") (no whitespace)
    - ensure_ascii=False
    - forbid floats anywhere
    - Decimal persisted as string
    """
    validate_no_floats(obj)
    s = json.dumps(_to_jsonable(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s


def write_json_canonical(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    s = dumps_canonical(obj)
    # JSON files end with a single LF for deterministic diffs.
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
        f.write("\n")


def write_jsonl_canonical(path: Path, items: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for item in items:
            f.write(dumps_canonical(item))
            f.write("\n")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    """
    Read JSONL file as dicts (no sorting, no normalization).
    """
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)
