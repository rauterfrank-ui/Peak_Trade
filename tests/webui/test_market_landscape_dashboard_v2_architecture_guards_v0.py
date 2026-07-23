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
    assert "phase4-6b-economic-evidence-explicit-injection-binding" in text
    assert 'data-mdl-field="safety"' in text
    assert 'data-mdl-field="economic"' in text
    assert "<button" not in text.lower()


def test_projection_helpers_are_field_copy_only() -> None:
    proj_path = LANDSCAPE_PKG / "projections.py"
    proj = proj_path.read_text(encoding="utf-8")
    assert "project_canonical_decision_snapshot_v1" in proj
    assert "project_market_instrument_snapshot_v1" in proj
    assert "project_universe_ranking_snapshot_v1" in proj
    assert "project_dynamic_scope_snapshot_v1" in proj
    assert "project_safety_authority_snapshot_v1" in proj
    assert "project_economic_summary_snapshot_v1" in proj
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
        assert "economic_viability_evidence" not in module
        assert "execution" not in module
        assert "order" not in module


def test_producer_binding_is_read_only_and_outside_landscape_package() -> None:
    assert PRODUCER_BINDING.is_file()
    text = PRODUCER_BINDING.read_text(encoding="utf-8")
    assert "bind_market_universe_slots" in text
    assert "4.6B" in text
    assert "project_dynamic_scope_snapshot_v1" in text
    assert "project_canonical_decision_snapshot_v1" in text
    assert "project_double_play_snapshot_v1" in text
    assert "project_safety_authority_snapshot_v1" in text
    assert "project_economic_summary_snapshot_v1" in text
    assert "economic_viability_evidence_fields" in text
    assert "project_economic_viability_evidence_v1" in text
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
    assert "latest_economic" not in text
    assert "discover_economic" not in text
    assert "resolve_latest_economic" not in text
    # Documentation may mention promotion_economic_gate_v1 as a separate owner;
    # forbid executable imports / bindings of that owner.
    assert "from src.governance" not in text
    assert "import promotion_economic_gate" not in text
    assert "promotion_economic_gate_v1(" not in text
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
        assert "promotion_economic_gate" not in module
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


def test_owner_registry_economic_summary_reused_explicit_injection() -> None:
    registry_text = (LANDSCAPE_PKG / "owner_registry.py").read_text(encoding="utf-8")
    assert 'slot="economic_summary"' in registry_text
    assert 'owner_module="backtest.economic_viability_evidence_v1"' in registry_text
    assert "EconomicViabilityEvidenceV1" in registry_text
    assert "Phase 4.6B" in registry_text
    assert "explicit injection only" in registry_text
    assert "MISSING_SOURCE" in registry_text
    assert "promotion_economic_gate_v1 remains a separate owner" in registry_text
    # Ensure economic slot is REUSED (bound), not left NOT_BOUND.
    economic_block = registry_text.split('slot="economic_summary"', 1)[1].split(
        "CanonicalOwnerRefV1(", 1
    )[0]
    assert 'reuse_status="REUSED"' in economic_block


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


def test_economic_summary_forbids_gate_status_alias_and_selector_logic() -> None:
    """Phase 4.6B: economic_viability_status only; injection binding; no discovery."""
    contracts = (LANDSCAPE_PKG / "contracts.py").read_text(encoding="utf-8")
    unavailable = (LANDSCAPE_PKG / "unavailable.py").read_text(encoding="utf-8")
    serialization = (LANDSCAPE_PKG / "serialization.py").read_text(encoding="utf-8")
    projections = (LANDSCAPE_PKG / "projections.py").read_text(encoding="utf-8")
    producer = PRODUCER_BINDING.read_text(encoding="utf-8")
    registry = (LANDSCAPE_PKG / "owner_registry.py").read_text(encoding="utf-8")

    assert "economic_viability_status" in contracts
    assert "class EconomicSummarySnapshotV1" in contracts
    # Forbidden alias must not appear as a live contract field assignment.
    assert re.search(r"\beconomic_gate_status\s*:", contracts) is None
    assert "economic_gate_status" not in unavailable
    assert "economic_gate_status" not in serialization

    assert "project_economic_summary_snapshot_v1" in projections
    assert "project_economic_viability_evidence_v1" in producer
    assert "economic_viability_evidence_fields" in producer
    assert "REASON_ECONOMIC_NOT_PERSISTED" in producer

    # No repository-wide evidence discovery / latest-file selector.
    forbidden_selector_tokens = (
        "latest_economic",
        "discover_economic",
        "select_economic_evidence",
        "resolve_latest_economic",
        "find_economic_viability_evidence",
    )
    landscape_text = "\n".join(
        path.read_text(encoding="utf-8") for path in _iter_py_files(LANDSCAPE_PKG)
    )
    for token in forbidden_selector_tokens:
        assert token not in landscape_text, token
        assert token not in producer, token

    # Lifecycle labels must not be projected fields on the economic contract.
    for label in (
        "DEVELOPMENT_ONLY",
        "HOLDOUT",
        "SEALED_LONG_PANEL",
        "TERMINAL",
        "PREREGISTRATION_ONLY",
        "NOT_EVALUATED",
    ):
        assert re.search(rf"\b{label}\s*:", contracts) is None

    assert 'slot="economic_summary"' in registry
    assert "EconomicViabilityEvidenceV1" in registry
    assert "Phase 4.6B" in registry
    economic_block = registry.split('slot="economic_summary"', 1)[1].split(
        "CanonicalOwnerRefV1(", 1
    )[0]
    assert 'reuse_status="REUSED"' in economic_block


def test_owner_registry_diagnostics_summary_option_a_keep_not_bound() -> None:
    """Phase 4.6C: diagnostics_summary stays NOT_BOUND; ReadModel is not its source."""
    registry_text = (LANDSCAPE_PKG / "owner_registry.py").read_text(encoding="utf-8")
    assert 'slot="diagnostics_summary"' in registry_text
    diagnostics_block = registry_text.split('slot="diagnostics_summary"', 1)[1].split(
        "CanonicalOwnerRefV1(", 1
    )[0]
    assert 'owner_module="UNRESOLVED"' in diagnostics_block
    assert 'owner_symbol="UNRESOLVED"' in diagnostics_block
    assert 'reuse_status="NOT_BOUND"' in diagnostics_block
    assert "Phase 4.6C" in diagnostics_block
    assert "OPTION_A_KEEP_NOT_BOUND" in diagnostics_block
    assert "consumer-contract redesign" in diagnostics_block
    assert "WorkflowDashboardReadModelV1" in diagnostics_block
    assert "MUST NOT" in diagnostics_block
    # Must not silently reclaim WorkflowDashboardReadModelV1 as bound owner/source.
    assert 'owner_module="webui.workflow_dashboard_readmodel_v1.types"' not in diagnostics_block
    assert 'owner_symbol="WorkflowDashboardReadModelV1"' not in diagnostics_block
    assert 'reuse_status="PROJECTION_ONLY"' not in diagnostics_block
    assert 'reuse_status="REUSED"' not in diagnostics_block

    # No diagnostics producer / typed injection / project_* adapter authorized.
    landscape_text = "\n".join(
        path.read_text(encoding="utf-8") for path in _iter_py_files(LANDSCAPE_PKG)
    )
    producer = PRODUCER_BINDING.read_text(encoding="utf-8")
    for token in (
        "project_diagnostics_summary",
        "project_diagnostics_",
        "bind_diagnostics",
    ):
        assert token not in landscape_text, token
        assert token not in producer, token
    assert "WorkflowDashboardReadModelV1" not in producer

    runbook = (
        REPO
        / "docs"
        / "ops"
        / "market_dashboard"
        / "PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md"
    ).read_text(encoding="utf-8")
    assert "##### 4.6C — Diagnostics Summary Contract Architecture Ratification" in runbook
    assert "RATIFY_OPTION_A_KEEP_NOT_BOUND=true" in runbook
    assert "DIAGNOSTICS_SUMMARY_STATUS=NOT_BOUND" in runbook
    assert "SOLE_DIAGNOSTICS_OWNER=UNRESOLVED" in runbook
    assert "OPTION_B_NEW_DOMAIN_NEUTRAL_DIAGNOSTICS_EVIDENCE=REJECTED" in runbook
    assert "OPTION_D_SOURCE_HEALTH_ONLY=REJECTED" in runbook
    assert (
        "OPTION_C_MULTIPLE_DOMAIN_SPECIFIC_DIAGNOSTICS=DEFERRED_SEPARATE_OPERATOR_AUTHORIZED_REDESIGN"
        in runbook
    )
    assert "WORKFLOW_DASHBOARD_READMODEL_V1=NON_SOURCE_PROJECTION_ONLY" in runbook


def test_owner_registry_autonomy_stage_option_d_keep_not_bound() -> None:
    """Phase 4.7B OPTION_D: autonomy_stage NOT_BOUND; no aggregate; runtime separate."""
    from datetime import datetime, timezone

    from webui.market_dashboard_landscape_v2.availability import Availability
    from webui.market_dashboard_landscape_v2.owner_registry import owner_registry_by_slot
    from webui.market_dashboard_landscape_v2.unavailable import default_not_bound_bundle

    entry = owner_registry_by_slot()["autonomy_stage"]
    assert entry.owner_module == "NONE"
    assert entry.owner_symbol == "NONE"
    assert entry.reuse_status == "NOT_BOUND"
    assert entry.authority_class == "autonomy"
    stamp = datetime(2026, 7, 24, 0, 0, 0, tzinfo=timezone.utc)
    snap = default_not_bound_bundle(generated_at=stamp)["autonomy_stage"]
    assert snap.availability is Availability.NOT_BOUND
    assert snap.autonomy_stage is None
    assert snap.runtime_bridge_status is None

    registry_text = (LANDSCAPE_PKG / "owner_registry.py").read_text(encoding="utf-8")
    assert 'slot="autonomy_stage"' in registry_text
    autonomy_block = registry_text.split('slot="autonomy_stage"', 1)[1].split(
        "CanonicalOwnerRefV1(", 1
    )[0]
    assert 'owner_module="NONE"' in autonomy_block
    assert 'owner_symbol="NONE"' in autonomy_block
    assert 'reuse_status="NOT_BOUND"' in autonomy_block
    assert 'authority_class="autonomy"' in autonomy_block
    assert "Phase 4.7B" in autonomy_block
    assert "OPTION_D" in autonomy_block
    assert "docs-only" in autonomy_block
    assert "AUTHORITY_EFFECT=NONE" in autonomy_block
    assert "NON_SOURCE" in autonomy_block
    assert "WorkflowDashboardReadModelV1" in autonomy_block
    assert "MUST NOT" in autonomy_block
    # Runtime bridge status must not be named as autonomy_stage owner/source.
    assert "runtime_bridge_pre_activation_gate_v0" not in autonomy_block
    assert 'owner_symbol="BOUND_NOT_ACTIVATED"' not in autonomy_block
    assert 'authority_class="runtime_status"' not in autonomy_block
    assert "CANONICAL_RUNTIME_ENTRYPOINT_STATUS" in autonomy_block
    assert "separate fact" in autonomy_block
    # Must not reclaim WorkflowDashboardReadModelV1 or other productive owners.
    assert 'owner_module="webui.workflow_dashboard_readmodel_v1.types"' not in autonomy_block
    assert 'owner_symbol="WorkflowDashboardReadModelV1"' not in autonomy_block
    assert "promotion_economic_gate_v1" in autonomy_block
    assert 'reuse_status="REUSED"' not in autonomy_block
    assert 'reuse_status="PROJECTION_ONLY"' not in autonomy_block

    # Runtime State vs Autonomy Stage remain distinct registry semantics.
    assert 'slot="autonomy_stage"' in registry_text
    assert "BOUND_NOT_ACTIVATED" in registry_text
    assert "separate fact and NON_SOURCE for autonomy_stage" in autonomy_block

    # No Autonomy producer / injection / project_autonomy_* adapter.
    landscape_text = "\n".join(
        path.read_text(encoding="utf-8") for path in _iter_py_files(LANDSCAPE_PKG)
    )
    producer = PRODUCER_BINDING.read_text(encoding="utf-8")
    projections = (LANDSCAPE_PKG / "projections.py").read_text(encoding="utf-8")
    contracts = (LANDSCAPE_PKG / "contracts.py").read_text(encoding="utf-8")
    for token in (
        "project_autonomy_",
        "project_autonomy_stage",
        "bind_autonomy",
        "AutonomyStateAggregate",
        "CanonicalAutonomyState",
    ):
        assert token not in landscape_text, token
        assert token not in producer, token
        assert token not in projections, token
    assert "class AutonomyStageSnapshotV1" in contracts
    assert "class AutonomyStateAggregate" not in contracts
    assert "WorkflowDashboardReadModelV1" not in producer

    runbook = (
        REPO
        / "docs"
        / "ops"
        / "market_dashboard"
        / "PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md"
    ).read_text(encoding="utf-8")
    assert "PHASE_4_7A_RATIFIED_OPTION_D=true" in runbook
    assert "RATIFY_OPTION_D_NO_CANONICAL_AGGREGATE_REQUIRED=true" in runbook
    assert "AUTONOMY_STAGE_BINDING_STATUS=NOT_BOUND" in runbook
    assert "AUTONOMY_AGGREGATE_REQUIRED=false" in runbook
    assert "AUTONOMY_BINDING_COMPLETE_BY_EXPLICIT_NOT_BOUND=true" in runbook
    assert "SOLE_AUTONOMY_OWNER=NONE" in runbook
    assert "SOLE_AUTONOMY_PRODUCER=NONE" in runbook
    assert "SOLE_AUTONOMY_CONTRACT=NONE" in runbook
    assert "CROSS_SOURCE_SYNTHESIS_AUTHORIZED=false" in runbook
    assert "WORKFLOW_DASHBOARD_READMODEL_V1=NON_SOURCE" in runbook
    assert "DASHBOARD_CAN_BE_OWNER=false" in runbook
    # Visible-fact registry keeps Runtime State distinct from Autonomy Stage.
    assert "| Runtime State | Runtime Bridge State |" in runbook
    assert "OPTION_D; docs-only ladder; no productive aggregate" in runbook
