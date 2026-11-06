from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Mapping


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
        # Persist Decimals as strings for stable, non-float JSON.
        return str(x)
    if isinstance(x, Mapping):
        # Force keys to strings deterministically.
        return {str(k): _to_jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_to_jsonable(v) for v in x]
    return x


def dumps_canonical(obj: Any) -> bytes:
    """
    Canonical JSON bytes for deterministic hashing/artifacts.

    Rules:
    - sort keys
    - no whitespace (separators "," ":")
    - ensure_ascii=False
    - forbid float anywhere (caller must pass ints/str/Decimal)
    - Decimal -> string
    """
    validate_no_floats(obj)
    s = json.dumps(_to_jsonable(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")
