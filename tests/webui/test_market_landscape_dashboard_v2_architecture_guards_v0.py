"""Architecture / import-boundary guards for Market Dashboard Landscape V2.

Prevents:
- Landscape package importing mutable runtime / execution / order APIs
- UI templates importing Landscape via forbidden execution paths
- Duplicate truth owners inside the Landscape package
- UI-side recomputation of decision / risk / sizing
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LANDSCAPE_PKG = REPO / "src" / "webui" / "market_dashboard_landscape_v2"
WEBUI_ROOT = REPO / "src" / "webui"
TEMPLATES_ROOT = REPO / "templates" / "peak_trade_dashboard"

FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "execution.",
    "src.trading.orders",
    "trading.orders",
    "src.broker",
    "broker.",
    "src.webui.execution_watch_api",
    "webui.execution_watch_api",
    "src.webui.live_track",
    "webui.live_track",
    "src.webui.workflow_dashboard_runtime_v1",
    "webui.workflow_dashboard_runtime_v1",
    "src.webui.last_paper_run_panel_runtime_v0",
    "webui.last_paper_run_panel_runtime_v0",
    "src.meta.learning_loop.deploy_inactive",
    "meta.learning_loop.deploy_inactive",
)

FORBIDDEN_NAME_TOKENS_IN_LANDSCAPE = (
    "place_order",
    "submit_order",
    "create_order",
    "activate_runtime",
    "arm_live",
    "compute_decision",
    "recompute_decision",
    "compute_risk",
    "recompute_risk",
    "compute_sizing",
    "recompute_sizing",
    "select_direction",
    "switch_scope",
)

# Decision/risk/sizing truth must remain outside this consumer package.
FORBIDDEN_SECOND_TRUTH_DEFINITIONS = (
    "class CanonicalTradingDecisionEvidence",
    "def evaluate_double_play",
    "def compute_position_size",
    "def compute_risk_budget",
)


def _iter_py_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def _import_modules(path: Path) -> list[tuple[str, int]]:
    """Return (module, level) pairs. level>0 means relative import."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append((alias.name, 0))
        elif isinstance(node, ast.ImportFrom):
            modules.append((node.module or "", node.level))
    return modules


def test_landscape_package_has_no_forbidden_imports() -> None:
    hits: list[str] = []
    for path in _iter_py_files(LANDSCAPE_PKG):
        for module, level in _import_modules(path):
            if level > 0:
                continue
            for prefix in FORBIDDEN_IMPORT_PREFIXES:
                if module == prefix or module.startswith(prefix + "."):
                    hits.append(f"{path.relative_to(REPO)}:{module}")
    assert hits == [], f"FORBIDDEN_IMPORTS={hits}"


def test_landscape_package_stdlib_and_relative_only() -> None:
    """Contracts stay free of trading/runtime imports (projection uses field args)."""
    allowed_external = {
        "dataclasses",
        "datetime",
        "enum",
        "json",
        "typing",
        "__future__",
    }
    hits: list[str] = []
    for path in _iter_py_files(LANDSCAPE_PKG):
        for module, level in _import_modules(path):
            if level > 0:
                continue
            if not module:
                continue
            root = module.split(".", 1)[0]
            if root in allowed_external:
                continue
            hits.append(f"{path.relative_to(REPO)}:{module}")
    assert hits == [], f"non-stdlib imports in Landscape package: {hits}"


def test_no_ui_side_recomputation_markers() -> None:
    hits: list[str] = []
    for path in _iter_py_files(LANDSCAPE_PKG):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_NAME_TOKENS_IN_LANDSCAPE:
            if token in text:
                # Allow mentions inside forbid-lists / docstrings that say "Forbidden:"
                if f'"{token}"' in text or f"'{token}'" in text:
                    continue
                if "Forbidden" in text and token in text:
                    # still fail if defined as function
                    tree = ast.parse(text)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if node.name == token:
                                hits.append(f"{path.relative_to(REPO)}:def {token}")
                    continue
                tree = ast.parse(text)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if node.name == token:
                            hits.append(f"{path.relative_to(REPO)}:{node.name}")
    assert hits == [], f"UI recomputation markers present: {hits}"


def test_no_second_truth_owner_definitions() -> None:
    hits: list[str] = []
    for path in _iter_py_files(LANDSCAPE_PKG):
        text = path.read_text(encoding="utf-8")
        for needle in FORBIDDEN_SECOND_TRUTH_DEFINITIONS:
            if needle in text:
                hits.append(f"{path.relative_to(REPO)}:{needle}")
    assert hits == [], f"SECOND_TRUTH_OWNERS={hits}"


def test_webui_templates_do_not_import_execution_or_landscape_runtime() -> None:
    """No Jinja/HTML surface may reference order/execution activation APIs."""
    if not TEMPLATES_ROOT.is_dir():
        return
    forbidden_substrings = (
        "execution_watch_api",
        "place_order",
        "submit_order",
        "activate_runtime",
        "arm_live",
        "market_dashboard_landscape_v2",  # no UI wiring in PR1
    )
    hits: list[str] = []
    for path in TEMPLATES_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".html", ".js", ".css", ".jinja", ".j2"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in forbidden_substrings:
            if token in text:
                hits.append(f"{path.relative_to(REPO)}:{token}")
    assert hits == [], f"template forbidden refs: {hits}"


def test_no_market_route_wired_in_app_for_landscape_v2() -> None:
    app_text = (WEBUI_ROOT / "app.py").read_text(encoding="utf-8")
    assert "market_dashboard_landscape_v2" not in app_text
    assert '@app.get("/market"' not in app_text
    assert "create_market_router" not in app_text


def test_projection_helpers_are_field_copy_only() -> None:
    proj_path = LANDSCAPE_PKG / "projections.py"
    proj = proj_path.read_text(encoding="utf-8")
    assert "project_canonical_decision_snapshot_v1" in proj
    assert "Forbidden" in proj
    tree = ast.parse(proj)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.level > 0 or (node.module or "").split(".", 1)[0] in {
                "__future__",
                "datetime",
                "typing",
            }
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] in {"__future__", "datetime", "typing"}
    # Must not import producer evidence modules as runtime dependencies.
    for module, level in _import_modules(proj_path):
        if level > 0:
            continue
        assert "canonical_trading_decision_evidence" not in module
        assert "double_play_dashboard_display" not in module
        assert "execution" not in module
        assert "order" not in module
