"""
Learning snippets: schreibt JSON/JSONL nach ``reports/learning_snippets/``.

Vertrag ist kompatibel mit ``scripts/run_learning_apply_cycle.py`` (gleiche Patch-Dicts).
Keine Orchestrierung — nur atomisches, deterministisches Dateischreiben.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

# Relativ zum Prozess-CWD (wie ``run_learning_apply_cycle.DEFAULT_IN_DIR``).
DEFAULT_LEARNING_SNIPPETS_DIR = Path("reports/learning_snippets")

_JSON_SEPARATORS = (",", ":")


def _dumps_sorted(obj: Any) -> str:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=_JSON_SEPARATORS,
        ensure_ascii=True,
    )


def _patch_rows(payload: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [p for p in payload if isinstance(p, dict)]
    if isinstance(payload, dict):
        inner = payload.get("patches")
        if isinstance(inner, list):
            return [p for p in inner if isinstance(p, dict)]
        return [payload]
    raise TypeError(f"payload must be dict or list of dicts, got {type(payload)!r}")


def _body_for_json(payload: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
    if isinstance(payload, list):
        obj: Any = {"patches": payload}
    else:
        obj = payload
    return _dumps_sorted(obj) + "\n"


def _body_for_jsonl(payload: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
    rows = _patch_rows(payload)
    if not rows:
        return ""
    lines = [_dumps_sorted(r) for r in rows]
    return "\n".join(lines) + "\n"


def _atomic_write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding=encoding)
    tmp.replace(path)


def emit_learning_snippet(
    payload: Union[Dict[str, Any], List[Dict[str, Any]]],
    *,
    out_path: Optional[Path] = None,
    out_dir: Path = DEFAULT_LEARNING_SNIPPETS_DIR,
    stem: str = "learning_snippet",
    fmt: Literal["json", "jsonl"] = "json",
) -> Path:
    """
    Schreibt ein Learning-Snippet atomisch und deterministisch.

    Args:
        payload: Ein Patch-Dict, ``{"patches": [dict, ...]}``, oder Liste von Patch-Dicts
            (kompatibel mit ``run_learning_apply_cycle``).
        out_path: Zieldatei. Wenn gesetzt, werden ``out_dir``/``stem`` ignoriert.
        out_dir: Basisverzeichnis, wenn ``out_path`` fehlt.
        stem: Dateiname ohne Endung, wenn ``out_path`` fehlt.
        fmt: ``json`` (ein Objekt pro Datei) oder ``jsonl`` (eine Zeile pro Patch).

    Returns:
        Pfad zur geschriebenen Datei.

    Raises:
        TypeError: Bei ungültigem ``payload``-Typ.
    """
    if fmt == "jsonl":
        body = _body_for_jsonl(payload)
    else:
        body = _body_for_json(payload)

    target = out_path
    if target is None:
        ext = ".jsonl" if fmt == "jsonl" else ".json"
        target = out_dir / f"{stem}{ext}"

    _atomic_write_text(target, body)
    return target


__all__ = [
    "DEFAULT_LEARNING_SNIPPETS_DIR",
    "emit_learning_snippet",
]
