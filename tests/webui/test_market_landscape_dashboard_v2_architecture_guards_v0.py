"""Architecture / import-boundary guards for Market Dashboard Landscape V2.

Prevents:
- Landscape package importing mutable runtime / execution / order APIs
- UI templates importing execution/runtime activation APIs
- Duplicate truth owners inside the Landscape package
- UI-side recomputation of decision / risk / sizing
- Write/action forms on GET /market Landscape shell
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LANDSCAPE_PKG = REPO / "src" / "webui" / "market_dashboard_landscape_v2"
SHELL_ROUTER = REPO / "src" / "webui" / "market_dashboard_landscape_shell_router_v2.py"
PRODUCER_BINDING = REPO / "src" / "webui" / "market_dashboard_landscape_producer_binding_v2.py"
WEBUI_ROOT = REPO / "src" / "webui"
TEMPLATES_ROOT = REPO / "templates" / "peak_trade_dashboard"
LANDSCAPE_TEMPLATE = TEMPLATES_ROOT / "market_landscape_v2.html"

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
    "evaluate_offline_killswitch_boundary_v0",
    "bind_killswitch_boundary_offline_replay_evidence_v0",
    "evaluate_capital_risk_sizing_v1",
)

FORBIDDEN_SECOND_TRUTH_DEFINITIONS = (
    "class CanonicalTradingDecisionEvidence",
    "def evaluate_double_play",
    "def compute_position_size",
    "def compute_risk_budget",
    "class KillSwitch",
    "def evaluate_offline_killswitch_boundary_v0",
)

FORBIDDEN_TEMPLATE_TOKENS = (
    "execution_watch_api",
    "place_order",
    "submit_order",
    "activate_runtime",
    "arm_live",
    'method="post"',
    'method="POST"',
    "Submit Order",
    "Arm Runtime",
    "Activate Runtime",
    "Trigger Kill",
    "Recover Kill",
    "Resume Trading",
)

FORBIDDEN_WEBUI_SAFETY_CALLS = (
    "evaluate_offline_killswitch_boundary_v0",
    "bind_killswitch_boundary_offline_replay_evidence_v0",
    "derive_killswitch_boundary_mode_v0",
)

FORBIDDEN_HEALTHY_SAFETY_DEFAULTS = (
    'kill_switch_state="ACTIVE"',
    "kill_switch_state='ACTIVE'",
    'kill_switch_state="normal"',
    "kill_switch_state='normal'",
    "veto_active=False",
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
                if f'"{token}"' in text or f"'{token}'" in text:
                    continue
                if "Forbidden" in text and token in text:
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


def test_webui_templates_do_not_import_execution_or_runtime_activation() -> None:
    """No Jinja/HTML surface may reference order/execution activation APIs."""
    if not TEMPLATES_ROOT.is_dir():
        return
    hits: list[str] = []
    for path in TEMPLATES_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".html", ".js", ".css", ".jinja", ".j2"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in (
            "execution_watch_api",
            "place_order",
            "submit_order",
            "activate_runtime",
            "arm_live",
        ):
            if token in text:
                hits.append(f"{path.relative_to(REPO)}:{token}")
    assert hits == [], f"template forbidden refs: {hits}"


def test_market_route_wired_read_only_for_landscape_v2() -> None:
    app_text = (WEBUI_ROOT / "app.py").read_text(encoding="utf-8")
    assert "market_dashboard_landscape_shell_router_v2" in app_text
    assert "set_market_landscape_shell_config" in app_text
    assert "create_market_router" not in app_text
    router_text = SHELL_ROUTER.read_text(encoding="utf-8")
    assert '@router.get("/market"' in router_text
    assert "@router.post" not in router_text
    assert "@router.put" not in router_text
    assert "@router.patch" not in router_text
    assert "@router.delete" not in router_text
    for prefix in FORBIDDEN_IMPORT_PREFIXES:
        assert prefix not in router_text, prefix


def test_landscape_shell_template_has_no_write_controls() -> None:
    assert LANDSCAPE_TEMPLATE.is_file()
    text = LANDSCAPE_TEMPLATE.read_text(encoding="utf-8")
    for token in FORBIDDEN_TEMPLATE_TOKENS:
        assert token not in text, token
    assert 'data-market-landscape-v2="true"' in text
    assert 'data-market-dashboard-authority="false"' in text
    assert "method=" not in text.lower()
    assert re.search(r"<form\b", text, flags=re.IGNORECASE) is None
    assert "phase4-4a-canonical-safety-projection-binding" in text
    assert 'data-mdl-field="safety"' in text
    assert "<button" not in text.lower()


def test_projection_helpers_are_field_copy_only() -> None:
    proj_path = LANDSCAPE_PKG / "projections.py"
    proj = proj_path.read_text(encoding="utf-8")
    assert "project_canonical_decision_snapshot_v1" in proj
    assert "project_market_instrument_snapshot_v1" in proj
    assert "project_universe_ranking_snapshot_v1" in proj
    assert "project_dynamic_scope_snapshot_v1" in proj
    assert "project_safety_authority_snapshot_v1" in proj
    assert "Forbidden" in proj
    tree = ast.parse(proj)
    # Guard against executable references, not documentation mentions.
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id not in {"transition_state", "RuntimeScopeState"}
        if isinstance(node, ast.Attribute):
            assert node.attr not in {
                "transition_state",
                "RuntimeScopeState",
                "trigger",
                "request_recovery",
                "complete_recovery",
            }
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "initialize_canonical_scope"
            assert node.func.id not in FORBIDDEN_WEBUI_SAFETY_CALLS
        if isinstance(node, ast.ImportFrom):
            assert node.level > 0 or (node.module or "").split(".", 1)[0] in {
                "__future__",
                "datetime",
                "typing",
            }
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] in {"__future__", "datetime", "typing"}
    assert "from trading.master_v2.double_play_state" not in proj
    for module, level in _import_modules(proj_path):
        if level > 0:
            continue
        assert "canonical_trading_decision_evidence" not in module
        assert "double_play_dashboard_display" not in module
        assert "killswitch_boundary" not in module
        assert "kill_switch" not in module
        assert "execution" not in module
        assert "order" not in module


def test_producer_binding_is_read_only_and_outside_landscape_package() -> None:
    assert PRODUCER_BINDING.is_file()
    text = PRODUCER_BINDING.read_text(encoding="utf-8")
    assert "bind_market_universe_slots" in text
    assert "4.4A" in text
    assert "project_dynamic_scope_snapshot_v1" in text
    assert "project_canonical_decision_snapshot_v1" in text
    assert "project_double_play_snapshot_v1" in text
    assert "project_safety_authority_snapshot_v1" in text
    assert "canonical_decision_fields" in text
    assert "double_play_fields" in text
    assert "safety_authority_fields" in text
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id not in {
                "transition_state",
                "RuntimeScopeState",
                "compose_double_play_decision",
                "build_dashboard_display_snapshot",
                "KillSwitch",
                *FORBIDDEN_WEBUI_SAFETY_CALLS,
            }
        if isinstance(node, ast.Attribute):
            assert node.attr not in {
                "transition_state",
                "RuntimeScopeState",
                "compose_double_play_decision",
                "build_dashboard_display_snapshot",
                "trigger",
                "request_recovery",
                "complete_recovery",
                "save",
            }
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "initialize_canonical_scope",
                "compose_double_play_decision",
                "build_dashboard_display_snapshot",
                *FORBIDDEN_WEBUI_SAFETY_CALLS,
            }
    assert "@router.post" not in text
    assert "place_order" not in text
    assert "activate_runtime" not in text
    assert "workflow_dashboard_runtime_v1" not in text
    assert "execution_watch_api" not in text
    assert "double_play_dashboard_display_json_route" not in text
    assert "StatePersistence" not in text
    assert "RiskGate" not in text
    assert "evaluate_capital_risk_sizing_v1" not in text
    for needle in FORBIDDEN_HEALTHY_SAFETY_DEFAULTS:
        assert needle not in text, needle
    for module, level in _import_modules(PRODUCER_BINDING):
        if level > 0:
            continue
        for prefix in FORBIDDEN_IMPORT_PREFIXES:
            assert not (module == prefix or module.startswith(prefix + ".")), module
        assert "double_play_state" not in module
        assert "double_play_composition" not in module
        assert "double_play_dashboard_display" not in module
        assert "canonical_scope_initialization" not in module
        assert "canonical_trading_decision_evidence" not in module
        assert "killswitch_boundary" not in module
        assert "kill_switch" not in module
        assert "risk_gate" not in module
        assert "capital_risk_sizing" not in module
    # Landscape package must not import the binding module (keeps contracts pure).
    for path in _iter_py_files(LANDSCAPE_PKG):
        for module, level in _import_modules(path):
            assert "market_dashboard_landscape_producer_binding_v2" not in module


def test_owner_registry_distinguishes_safety_authority_from_projection_source() -> None:
    registry_text = (LANDSCAPE_PKG / "owner_registry.py").read_text(encoding="utf-8")
    assert 'slot="safety_authority"' in registry_text
    assert 'owner_module="src.risk_layer.kill_switch"' in registry_text
    assert "AUTHORITY_EFFECT=NONE" in registry_text
    assert "killswitch_boundary_offline_replay_binding_adapter_v0" in registry_text
    assert 'reuse_status="REUSED"' in registry_text
    assert 'slot="risk_sizing_capital"' in registry_text
    assert 'reuse_status="NOT_BOUND"' in registry_text


def test_shell_router_wires_phase41_through_phase43b_binding() -> None:
    text = SHELL_ROUTER.read_text(encoding="utf-8")
    assert "bind_market_universe_slots" in text
    assert "bind_market_universe_scope_slots" not in text
    assert "slot_overrides" in text
    assert "Phase 4.3B" in text or "4.3B" in text
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id not in {
                "transition_state",
                "RuntimeScopeState",
                "compose_double_play_decision",
                "build_dashboard_display_snapshot",
                "KillSwitch",
                *FORBIDDEN_WEBUI_SAFETY_CALLS,
            }
        if isinstance(node, ast.Attribute):
            assert node.attr not in {
                "transition_state",
                "RuntimeScopeState",
                "compose_double_play_decision",
                "build_dashboard_display_snapshot",
                "trigger",
                "request_recovery",
            }
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "initialize_canonical_scope",
                "compose_double_play_decision",
                "build_dashboard_display_snapshot",
                *FORBIDDEN_WEBUI_SAFETY_CALLS,
            }
    assert "@router.post" not in text
    assert "workflow_dashboard_runtime_v1" not in text
    assert "execution_watch_api" not in text
    for module, level in _import_modules(SHELL_ROUTER):
        if level > 0:
            continue
        assert "canonical_scope_initialization" not in module
        assert "canonical_trading_decision_evidence" not in module
        assert "double_play_state" not in module
        assert "double_play_composition" not in module
        assert "double_play_dashboard_display" not in module
        assert "kill_switch" not in module
        assert "killswitch_boundary" not in module


def test_webui_has_no_killswitch_mutation_or_offline_evaluator_calls() -> None:
    """Scoped to Landscape shell surfaces — not the entire webui tree."""
    surfaces = (
        LANDSCAPE_PKG,
        PRODUCER_BINDING,
        SHELL_ROUTER,
    )
    paths: list[Path] = []
    for surface in surfaces:
        if surface.is_dir():
            paths.extend(_iter_py_files(surface))
        elif surface.is_file():
            paths.append(surface)
    hits: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_WEBUI_SAFETY_CALLS:
                    hits.append(f"{path.relative_to(REPO)}:{node.func.id}")
                if isinstance(node.func, ast.Attribute) and node.func.attr in {
                    "trigger",
                    "request_recovery",
                    "complete_recovery",
                }:
                    hits.append(f"{path.relative_to(REPO)}:.{node.func.attr}")
    assert hits == [], hits


def test_shell_router_forbidden_import_count_zero() -> None:
    hits: list[str] = []
    for module, level in _import_modules(SHELL_ROUTER):
        if level > 0:
            continue
        for prefix in FORBIDDEN_IMPORT_PREFIXES:
            if module == prefix or module.startswith(prefix + "."):
                hits.append(module)
    assert hits == []


def test_landscape_v2_css_has_no_visible_structural_divider_lines() -> None:
    """Phase-3 product composition: zero visible structural lines on /market.

    Scoped only to Market Landscape V2 CSS selectors — not global WebUI CSS.
    """
    css_path = REPO / "static" / "css" / "market_dashboard_landscape_v2.css"
    assert css_path.is_file()
    text = css_path.read_text(encoding="utf-8")
    # Strip comments so documentation mentions of "border" do not trip the guard.
    code = re.sub(r"/\*.*?\*/", "", text, flags=re.S)

    forbidden_patterns = (
        r"border-top\s*:\s*[^;]*solid",
        r"border-bottom\s*:\s*[^;]*solid",
        r"border-left\s*:\s*[^;]*solid",
        r"border-right\s*:\s*[^;]*solid",
        r"border\s*:\s*\d+px\s+solid",
        r"border\s*:\s*1px",
        r"repeating-linear-gradient\s*\(",
        r"<hr\b",
    )
    hits: list[str] = []
    for pattern in forbidden_patterns:
        for match in re.finditer(pattern, code, flags=re.I):
            hits.append(f"{pattern} @ {match.group(0)!r}")
    assert hits == [], f"VISIBLE_STRUCTURAL_LINE_SOURCES={hits}"

    # Non-none box-shadow with length is a structural line substitute.
    shadow_hits: list[str] = []
    for match in re.finditer(r"box-shadow\s*:\s*([^;]+);", code, flags=re.I):
        value = match.group(1).strip().lower()
        if value != "none" and "none !" not in value and re.search(r"\d+px", value):
            shadow_hits.append(f"box-shadow @ {match.group(0)!r}")
    assert shadow_hits == [], f"VISIBLE_SHADOW_LINE_SOURCES={shadow_hits}"

    for selector in (
        ".mdl-v2-strip",
        ".mdl-v2-workspace",
        ".mdl-v2-rail",
        ".mdl-v2-primary",
        ".mdl-v2-chart__stage",
        ".mdl-v2-decision",
        ".mdl-v2-ops",
        ".mdl-v2-timeline",
        ".mdl-v2-engineering",
        ".mdl-v2-shell",
        ".mdl-v2-app-chrome",
    ):
        assert selector in code, selector
    assert "border-top: 1px solid" not in code
    assert "border-bottom: 1px solid" not in code
    assert "border-left: 1px solid" not in code
    assert "border-right: 1px solid" not in code
    assert "--mdl-rule" not in code
