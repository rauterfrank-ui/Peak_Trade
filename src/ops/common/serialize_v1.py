from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any


def _jsonable_sort_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, ensure_ascii=True)


def to_jsonable_v1(obj: Any) -> Any:
    """Convert dataclasses / Pathlike / Enum / set / frozenset into JSON-able structures.

    Boundary contract: ops entrypoints should return only JSON-able data.
    """
    if obj is None:
        return None
    # Enum (before dataclass - Enum can be mistaken)
    if hasattr(obj, "value") and not isinstance(obj, type):
        return obj.value
    if is_dataclass(obj) and not isinstance(obj, type):
        d = asdict(obj)
        return {k: to_jsonable_v1(v) for k, v in d.items()}
    if isinstance(obj, dict):
        return {str(k): to_jsonable_v1(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable_v1(x) for x in obj]
    if isinstance(obj, (set, frozenset)):
        converted = [to_jsonable_v1(x) for x in obj]
        return sorted(converted, key=_jsonable_sort_key)
    try:
        import os

        if isinstance(obj, os.PathLike):
            return str(obj)
    except Exception:
        pass
    return obj
