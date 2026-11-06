"""Static transitive import closure (AST) from runner entrypoints to POST-path modules."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
ENTRIES = sys.argv[2].split(",")
TARGETS = sys.argv[3].split(",")


def mod_to_path(mod: str) -> Path | None:
    parts = mod.split(".")
    for base in (REPO, REPO / "src"):
        p = base.joinpath(*parts)
        if p.with_suffix(".py").is_file():
            return p.with_suffix(".py")
        if (p / "__init__.py").is_file():
            return p / "__init__.py"
    return None


def imports_of(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    out: set[str] = set()
    pkg = None
    rel = path.relative_to(REPO).with_suffix("")
    pkg_parts = list(rel.parts[:-1])
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = pkg_parts[: len(pkg_parts) - (node.level - 1)]
                mod = ".".join(base + ([node.module] if node.module else []))
            else:
                mod = node.module or ""
            out.add(mod)
            for a in node.names:
                out.add(f"{mod}.{a.name}")
    del pkg
    return out


def closure(entry: Path) -> dict[str, str | None]:
    seen: dict[str, str | None] = {str(entry): None}
    stack = [entry]
    while stack:
        cur = stack.pop()
        for mod in imports_of(cur):
            p = mod_to_path(mod)
            if p is None:
                continue
            key = str(p)
            if key not in seen:
                seen[key] = str(cur)
                stack.append(p)
    return seen


def chain(seen: dict[str, str | None], key: str) -> list[str]:
    out = []
    while key is not None:
        out.append(str(Path(key).relative_to(REPO)))
        key = seen[key]
    return list(reversed(out))


report = {}
for e in ENTRIES:
    ep = (REPO / e).resolve()
    seen = closure(ep)
    hits = {}
    for t in TARGETS:
        for k in seen:
            if k.endswith(f"/{t}.py"):
                hits[t] = chain(seen, k)
    report[e] = {"closure_size": len(seen), "post_module_hits": hits}
print(json.dumps(report, indent=2))
