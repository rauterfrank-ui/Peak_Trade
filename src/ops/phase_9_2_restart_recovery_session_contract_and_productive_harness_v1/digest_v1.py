"""Canonical digest helpers for Phase 9.2 restart harness."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def sha256_canonical_v1(
    payload: Mapping[str, Any] | list[Any] | str | int | float | bool | None,
) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_text_v1(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json_atomic_v1(path: Any, payload: Mapping[str, Any]) -> None:
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(target)


def read_json_v1(path: Any) -> dict[str, Any]:
    from pathlib import Path

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("json_root_must_be_object")
    return payload
