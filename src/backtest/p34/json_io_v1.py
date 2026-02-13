"""P34 — Report JSON IO v1 (deterministic read/write for P33 schema)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.backtest.p33.report_artifacts_v1 import ArtifactSchemaError, report_from_dict


def write_report_json_v1(path: str | Path, report_dict: dict[str, Any]) -> None:
    """Write schema v1 report dict to JSON file (UTF-8, deterministic, pretty)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(report_dict, ensure_ascii=False, sort_keys=True, indent=2)
    if not txt.endswith("\n"):
        txt += "\n"
    p.write_text(txt, encoding="utf-8")


def read_report_json_v1(path: str | Path) -> dict[str, Any]:
    """Read and validate JSON file as schema v1 report. Returns dict."""
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    try:
        d = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ArtifactSchemaError(f"invalid json: {e}") from e
    report_from_dict(d)  # validate
    return d
