"""WP-A3 static productive import guard for src.portfolio (boundary only).

Scans CURRENT proven productive consumer surfaces. Does not encode a permanent
ban on future explicitly adjudicated learning/research/autonomy contracts.
Does not modify portfolio or trading-core runtime behavior.

Reuse: repository AST forbidden-import walk (ast.Import / ast.ImportFrom).
Relative imports are resolved against the file's src.* module path so that
equivalent imports of src.portfolio are detected without substring matching
comments, docstrings, or doctest text.
"""

from __future__ import annotations

import ast
from pathlib import Path

from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.constants_v1 import (
    NON_AUTHORITY_HELPERS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

# Owner-adjudicated proven productive consumer surfaces only.
# src/ops/** is UNPROVEN as a full forbidden tree and is not scanned here.
PRODUCTIVE_CONSUMER_ROOTS: tuple[str, ...] = (
    "src/trading",
    "src/live",
    "src/execution",
    "src/execution_simple",
)

_R6_PORTFOLIO_NON_AUTHORITY_HELPERS: frozenset[str] = frozenset(
    {
        "src.portfolio.PortfolioManager",
        "src.portfolio.equal_weight",
        "src.portfolio.vol_target",
    }
)


def _iter_python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts))


def _src_module_parts(path: Path) -> tuple[str, ...]:
    resolved = path.resolve()
    try:
        parts = resolved.relative_to(REPO_ROOT).parts
    except ValueError:
        raw = resolved.parts
        if "src" not in raw:
            raise ValueError(f"path is not under repo root or a src/ tree: {resolved}")
        parts = raw[raw.index("src") :]
    name_parts = list(parts)
    if name_parts[-1].endswith(".py"):
        name_parts[-1] = name_parts[-1][:-3]
    if name_parts[-1] == "__init__":
        name_parts = name_parts[:-1]
    return tuple(name_parts)


def _module_name_for_path(path: Path) -> str:
    return ".".join(_src_module_parts(path))


def _current_package(path: Path, current_module: str) -> str:
    if path.name == "__init__.py":
        return current_module
    if "." not in current_module:
        return ""
    return current_module.rsplit(".", 1)[0]


def _resolve_import_from(path: Path, node: ast.ImportFrom) -> str | None:
    if node.level == 0:
        return node.module
    current_module = _module_name_for_path(path)
    package = _current_package(path, current_module)
    base = package
    for _ in range(node.level - 1):
        if not base:
            return None
        base = base.rsplit(".", 1)[0] if "." in base else ""
    if node.module:
        return f"{base}.{node.module}" if base else node.module
    return base or None


def _is_src_portfolio_module(name: str | None) -> bool:
    if not name:
        return False
    return name == "src.portfolio" or name.startswith("src.portfolio.")


def scan_src_portfolio_imports(path: Path) -> list[str]:
    """Return resolved src.portfolio import module names in ``path`` (AST only)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_src_portfolio_module(alias.name):
                    hits.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            resolved = _resolve_import_from(path, node)
            if _is_src_portfolio_module(resolved):
                hits.append(resolved or "")
                continue
            if resolved == "src":
                for alias in node.names:
                    if alias.name == "portfolio":
                        hits.append("src.portfolio")
    return hits


def collect_productive_src_portfolio_imports() -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for rel_root in PRODUCTIVE_CONSUMER_ROOTS:
        root = REPO_ROOT / rel_root
        if not root.is_dir():
            continue
        for path in _iter_python_files(root):
            for hit in scan_src_portfolio_imports(path):
                findings.append((str(path.relative_to(REPO_ROOT)), hit))
    return findings


def test_current_productive_surfaces_have_zero_src_portfolio_imports() -> None:
    findings = collect_productive_src_portfolio_imports()
    assert findings == []


def test_scanned_roots_exclude_src_ops_full_tree() -> None:
    assert all(not root.startswith("src/ops") for root in PRODUCTIVE_CONSUMER_ROOTS)
    scanned = {root.split("/")[1] for root in PRODUCTIVE_CONSUMER_ROOTS}
    assert "ops" not in scanned


def test_src_portfolio_internal_imports_remain_allowed() -> None:
    init_path = REPO_ROOT / "src" / "portfolio" / "__init__.py"
    hits = scan_src_portfolio_imports(init_path)
    assert "src.portfolio.manager" in hits
    assert "src.portfolio.base" in hits
    # Module docstring doctest examples must not be counted as imports.
    assert "src.portfolio" not in hits
    assert collect_productive_src_portfolio_imports() == []


def test_scanner_ignores_comments_docstrings_and_doctest_text(tmp_path: Path) -> None:
    fake = tmp_path / "src" / "trading" / "comment_only.py"
    fake.parent.mkdir(parents=True)
    fake.write_text(
        '''"""Example: from src.portfolio import PortfolioManager."""
# from src.portfolio import PortfolioManager
def _example() -> None:
    """
    >>> from src.portfolio import PortfolioManager
    """
    return None
''',
        encoding="utf-8",
    )
    assert scan_src_portfolio_imports(fake) == []


def test_scanner_detects_absolute_src_portfolio_import(tmp_path: Path) -> None:
    fake = tmp_path / "src" / "trading" / "forbidden_abs.py"
    fake.parent.mkdir(parents=True)
    fake.write_text("from src.portfolio import PortfolioManager\n", encoding="utf-8")
    assert scan_src_portfolio_imports(fake) == ["src.portfolio"]


def test_scanner_detects_import_src_portfolio_statement(tmp_path: Path) -> None:
    fake = tmp_path / "src" / "execution_simple" / "forbidden_import.py"
    fake.parent.mkdir(parents=True)
    fake.write_text("import src.portfolio\n", encoding="utf-8")
    assert scan_src_portfolio_imports(fake) == ["src.portfolio"]


def test_scanner_detects_src_portfolio_submodule_import(tmp_path: Path) -> None:
    fake = tmp_path / "src" / "live" / "forbidden_sub.py"
    fake.parent.mkdir(parents=True)
    fake.write_text("from src.portfolio.manager import PortfolioManager\n", encoding="utf-8")
    assert scan_src_portfolio_imports(fake) == ["src.portfolio.manager"]


def test_scanner_detects_from_src_import_portfolio(tmp_path: Path) -> None:
    fake = tmp_path / "src" / "execution" / "forbidden_pkg.py"
    fake.parent.mkdir(parents=True)
    fake.write_text("from src import portfolio\n", encoding="utf-8")
    assert scan_src_portfolio_imports(fake) == ["src.portfolio"]


def test_scanner_detects_relative_import_resolving_to_src_portfolio(tmp_path: Path) -> None:
    fake = tmp_path / "src" / "trading" / "master_v2" / "forbidden_rel.py"
    fake.parent.mkdir(parents=True)
    fake.write_text("from ...portfolio import PortfolioManager\n", encoding="utf-8")
    assert scan_src_portfolio_imports(fake) == ["src.portfolio"]


def test_scanner_does_not_match_src_risk_portfolio(tmp_path: Path) -> None:
    fake = tmp_path / "src" / "trading" / "risk_portfolio.py"
    fake.parent.mkdir(parents=True)
    fake.write_text("from src.risk.portfolio import something\n", encoding="utf-8")
    assert scan_src_portfolio_imports(fake) == []


def test_r6_non_authority_helper_status_unchanged() -> None:
    helpers = frozenset(NON_AUTHORITY_HELPERS)
    assert _R6_PORTFOLIO_NON_AUTHORITY_HELPERS <= helpers
    assert "src.portfolio.PortfolioManager" in helpers
