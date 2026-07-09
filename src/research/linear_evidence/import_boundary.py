"""AST-based import boundary scanner for offline linear evidence surfaces."""

from __future__ import annotations

import ast
import tokenize
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

FORBIDDEN_IMPORT_SEGMENTS = frozenset(
    {
        "runtime",
        "scheduler",
        "live",
        "order_adapter",
    }
)

# Grep-style false-positive probe tokens (docstrings/comments only; not import hits).
_DOCSTRING_COMMENT_PROBE_TOKENS = frozenset(
    {
        "runtime",
        "scheduler",
        "live",
        "order adapter",
        "order_adapter",
    }
)


@dataclass(frozen=True)
class ImportBoundaryHit:
    path: str
    line: int
    module: str

    def format_scan_line(self) -> str:
        return f"{self.path}:{self.line}:{self.module}"


def _module_segments(module: str) -> tuple[str, ...]:
    return tuple(part for part in module.split(".") if part)


def module_violates_forbidden_boundary(module: str) -> bool:
    """Return True when an import module path crosses a forbidden offline boundary."""
    normalized = module.replace("-", "_")
    segments = _module_segments(normalized)
    if any(segment in FORBIDDEN_IMPORT_SEGMENTS for segment in segments):
        return True
    if "order" in normalized and "adapter" in normalized:
        return True
    return False


def _collect_import_hits(tree: ast.AST) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if module_violates_forbidden_boundary(alias.name):
                    hits.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom) and node.module:
            if module_violates_forbidden_boundary(node.module):
                hits.append((node.lineno, node.module))
    return hits


def _docstring_chunks(tree: ast.AST) -> list[tuple[int, str]]:
    chunks: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                chunks.append((getattr(node, "lineno", 1), doc))
    return chunks


def _comment_and_docstring_probe_hits(source: str, *, rel_path: str) -> list[str]:
    """Detect forbidden tokens appearing only in comments/docstrings (grep false positives)."""
    probe_hits: list[str] = []
    tree = ast.parse(source)
    searchable_chunks: list[tuple[int, str]] = []

    searchable_chunks.extend(_docstring_chunks(tree))

    reader = BytesIO(source.encode("utf-8"))
    for token in tokenize.tokenize(reader.readline):
        if token.type == tokenize.COMMENT:
            searchable_chunks.append((token.start[0], token.string))

    for line_no, text in searchable_chunks:
        lowered = text.lower()
        for token in _DOCSTRING_COMMENT_PROBE_TOKENS:
            if token in lowered:
                probe_hits.append(f"{rel_path}:{line_no}:{token}")
    return probe_hits


def scan_file_import_boundary(
    path: Path, *, repo_root: Path | None = None
) -> list[ImportBoundaryHit]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    rel = path.relative_to(repo_root).as_posix() if repo_root is not None else path.as_posix()
    return [
        ImportBoundaryHit(path=rel, line=line_no, module=module)
        for line_no, module in _collect_import_hits(tree)
    ]


def scan_paths_import_boundary(
    paths: list[Path],
    *,
    repo_root: Path,
) -> tuple[list[ImportBoundaryHit], list[str]]:
    hits: list[ImportBoundaryHit] = []
    docstring_comment_probes: list[str] = []
    for path in sorted(paths):
        if not path.is_file() or path.suffix != ".py":
            continue
        rel = path.relative_to(repo_root).as_posix()
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        hits.extend(
            ImportBoundaryHit(path=rel, line=line_no, module=module)
            for line_no, module in _collect_import_hits(tree)
        )
        docstring_comment_probes.extend(_comment_and_docstring_probe_hits(source, rel_path=rel))
    return hits, docstring_comment_probes


def classify_import_boundary_scan(
    hits: list[ImportBoundaryHit],
    *,
    docstring_comment_probes: list[str] | None = None,
) -> dict[str, str | int | bool]:
    probes = docstring_comment_probes or []
    bad_hits = len(hits)
    status = "PASS" if bad_hits == 0 else "REVIEW_REQUIRED"
    false_positive_docstring_ignored = bad_hits == 0 and bool(probes)
    if false_positive_docstring_ignored:
        status = "PASS_DOCSTRING_FALSE_POSITIVE_IGNORED"
    return {
        "IMPORT_BOUNDARY_HITS": len(hits),
        "BAD_IMPORT_BOUNDARY_HITS": bad_hits,
        "IMPORT_BOUNDARY_STATUS": status,
        "false_positive_docstring_ignored": false_positive_docstring_ignored,
        "DOCSTRING_COMMENT_PROBE_HITS": len(probes),
    }
