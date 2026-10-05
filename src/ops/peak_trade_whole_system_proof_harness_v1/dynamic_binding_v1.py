"""Dynamic binding candidate scan (observational static heuristics)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("importlib", re.compile(r"importlib\.(?:import_module|util\.spec_from_file_location)")),
    ("getattr_dispatch", re.compile(r"getattr\s*\(\s*[^,]+,\s*['\"]")),
    ("os_environ", re.compile(r"os\.environ\.(?:get|\[)")),
    ("registry_lookup", re.compile(r"REGISTRY|register_\w+|_REGISTRY")),
    ("config_selected", re.compile(r"if\s+\w+\s*==\s*['\"][^'\"]+['\"]\s*:")),
]


def scan_dynamic_bindings_v1(repo: Path, module_paths: list[str]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for rel in module_paths:
        path = repo / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for kind, pat in _PATTERNS:
            if pat.search(text):
                candidates.append(
                    {
                        "MODULE": rel,
                        "BINDING_KIND": kind,
                        "CURRENT_SELECTED_BINDING": "UNKNOWN",
                        "SELECTION_PROOF": "NONE",
                        "STATUS": "DYNAMIC_BINDING_CANDIDATE",
                    }
                )
    for c in candidates:
        if c["SELECTION_PROOF"] == "NONE":
            unresolved.append(c)
    return {
        "DYNAMIC_BINDING_CANDIDATES": candidates,
        "UNRESOLVED_DYNAMIC_BINDINGS": unresolved,
        "UNRESOLVED_COUNT": len(unresolved),
    }
