"""Operative Python invocation surface contract (non-authorizing)."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "config" / "runtime" / "pt_python_operative_surfaces_v1.json"

_OPERATIVE = {"OPERATIVE_CANONICAL", "OPERATIVE_WRAPPER"}
_INVOCATION = re.compile(
    r"(?m)^(?P<line>[^#\n]*(?:\bpython3\s+|/usr/bin/env python3\b|PY_CMD=\"python3\"|"
    r"source\s+\.venv/bin/activate|PYTHONPATH=\. python))"
)


def test_operative_surfaces_exist_and_are_classified() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert payload["contract_id"] == "pt_python_operative_surfaces_v1"
    missing = []
    for item in payload["surfaces"]:
        path = REPO_ROOT / item["path"]
        if not path.exists():
            missing.append(item["path"])
    assert missing == []


def test_operative_surfaces_have_no_path_python3_invocations() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for item in payload["surfaces"]:
        if item["class"] not in _OPERATIVE:
            continue
        if item["path"].endswith(".yml"):
            continue
        path = REPO_ROOT / item["path"]
        if path.suffix not in {".sh", ".md", ".py", ""} and path.name not in {
            "Makefile",
            "pt",
        }:
            continue
        text = path.read_text(encoding="utf-8")
        for match in _INVOCATION.finditer(text):
            line = match.group("line").strip()
            lowered = line.lower()
            if "never" in lowered or "do not use" in lowered or "prohibited" in lowered:
                continue
            if "PATH `python3`" in line or "PATH python3" in line or "PATH `python`" in line:
                continue
            if line.lstrip().startswith("-") and "source .venv/bin/activate" in line:
                continue
            offenders.append(f"{item['path']}: {line}")
    assert offenders == []


def test_canonical_launcher_rejects_path_fallback_comment() -> None:
    text = (REPO_ROOT / "scripts" / "pt").read_text(encoding="utf-8")
    assert "Never uses PATH python/python3" in text or "never uses PATH" in text.lower()
    assert "source .venv/bin/activate" not in text
    assert "command -v python" not in text
