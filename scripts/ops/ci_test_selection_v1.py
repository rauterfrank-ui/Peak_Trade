#!/usr/bin/env python3
"""Fail-closed diff-aware CI test selection for required tests job (v1)."""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

FULL_CATEGORIES = frozenset(
    {
        "central_src",
        "global_test_infra",
        "dependencies",
        "packaging",
        "coverage_config",
        "config_paths",
        "unknown",
    }
)
NO_OP_CATEGORIES = frozenset({"docs_only", "workflow_only", "static_contract"})
FOCUSED_CATEGORIES = frozenset(
    {
        "scripts_focused",
        "tests_focused",
        "strategy_regime_owner_focused",
        "market_dashboard_focused",
        "durable_completion_focused",
        "preflight_assembly_focused",
        "risk_killswitch_focused",
        "tiny_order_focused",
    }
)

# Paths that always force FULL when changed (never self-FOCUSED).
CI_SELECTOR_FULL_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
    }
)

# Shared / registry / framework prod paths — never strategy_regime_owner_focused.
STRATEGY_REGIME_OWNER_BLOCKED_PROD = frozenset(
    {
        "src/strategies/__init__.py",
        "src/strategies/composite.py",
        "src/strategies/registry.py",
        "src/strategies/base.py",
        "src/strategies/diagnostics.py",
        "src/strategies/regime_aware_portfolio.py",
        "src/regime/__init__.py",
        "src/regime/base.py",
        "src/regime/switching.py",
        "src/regime/config.py",
    }
)

# Explicit canonical test owners (fail-closed when prod is listed).
CANONICAL_STRATEGY_REGIME_TEST_OWNERS: dict[str, str] = {
    "src/strategies/vol_breakout.py": "tests/test_strategies_phase27.py",
    "src/strategies/vol_regime_filter.py": "tests/test_strategy_vol_regime_filter.py",
    "src/regime/detectors.py": "tests/test_regime_detection.py",
    "src/strategies/el_karoui/vol_model.py": "tests/strategies/el_karoui/test_vol_model.py",
}

MARKET_DASHBOARD_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

DURABLE_COMPLETION_FACADE_PATH = "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"

DURABLE_COMPLETION_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

CANONICAL_DURABLE_COMPLETION_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/ops/test_durable_completion_validation_graph_v1.py",
    "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

REQUIRED_DURABLE_COMPLETION_TEST_OWNERS: tuple[str, ...] = (
    "tests/ops/test_durable_completion_validation_graph_v1.py",
    "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
)

PE26_ASSEMBLY_OWNER = "src/ops/bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0.py"

PREFLIGHT_ASSEMBLY_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

CANONICAL_PREFLIGHT_ASSEMBLY_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/ops/test_bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

REQUIRED_PREFLIGHT_ASSEMBLY_TEST_OWNERS: tuple[str, ...] = (
    "tests/ops/test_bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0.py",
)

PE22_RISK_KILLSWITCH_OWNER = (
    "src/ops/bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py"
)
PE22_RISK_KILLSWITCH_TEST_OWNER = (
    "tests/ops/test_bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py"
)

RISK_KILLSWITCH_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

CANONICAL_RISK_KILLSWITCH_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/ops/test_bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py",
    "tests/ops/test_order_capability_killswitch_abort_binding_contract_v1.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

REQUIRED_RISK_KILLSWITCH_TEST_OWNERS: tuple[str, ...] = (
    "tests/ops/test_bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py",
    "tests/ops/test_order_capability_killswitch_abort_binding_contract_v1.py",
)

PE30_TINY_ORDER_OWNER = (
    "src/ops/bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0.py"
)
PE30_TINY_ORDER_TEST_OWNER = (
    "tests/ops/test_bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0.py"
)

TINY_ORDER_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

CANONICAL_TINY_ORDER_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/ops/test_bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0.py",
    "tests/ops/test_order_capability_killswitch_abort_binding_contract_v1.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

REQUIRED_TINY_ORDER_TEST_OWNERS: tuple[str, ...] = (
    "tests/ops/test_bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0.py",
    "tests/ops/test_order_capability_killswitch_abort_binding_contract_v1.py",
)

CANONICAL_MARKET_DASHBOARD_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/webui/test_market_dashboard_no_bitcoin_futures_v1.py",
    "tests/webui/test_market_futures_only_canonical_completion_v1.py",
    "tests/webui/test_market_dashboard_readonly_structure_contract_v0.py",
    "tests/webui/test_market_governed_top20_f5_default_wiring_v1.py",
    "tests/webui/test_market_futures_universe_visual_matrix_v1.py",
    "tests/webui/test_market_dashboard_selected_instrument_workspace_v1.py",
    "tests/webui/test_market_dashboard_topn_navigation_visual_density_v1.py",
    "tests/webui/test_market_futures_first_root_cause_eradication_v1.py",
    "tests/webui/test_futures_read_only_market_dashboard_v0.py",
    "tests/webui/test_market_canonical_short_url_title_real_values_ui_v1.py",
    "tests/webui/test_market_ranking_funnel_readmodel_v0.py",
    "tests/test_market_surface_api.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

_REPO_RELATIVE_PATH = re.compile(r"^[A-Za-z0-9_./-]+$")
_IMPORT_MODULE = re.compile(r"^[a-zA-Z0-9_.]+$")


@dataclass(frozen=True)
class SelectionResult:
    mode: str
    reason: str
    focused_pytest_targets: tuple[str, ...]
    focused_module_imports: tuple[str, ...] = ()

    def github_output_lines(self) -> list[str]:
        lines = [
            f"test_selection_mode={self.mode}",
            f"test_selection_reason={self.reason}",
            f"tests_execute_full={'true' if self.mode == 'FULL' else 'false'}",
            f"tests_execute_focused={'true' if self.mode == 'FOCUSED' else 'false'}",
            f"tests_execute_no_op={'true' if self.mode == 'NO_OP' else 'false'}",
        ]
        if self.focused_pytest_targets:
            lines.append(f"focused_pytest_targets={' '.join(self.focused_pytest_targets)}")
        else:
            lines.append("focused_pytest_targets=")
        if self.focused_module_imports:
            lines.append(f"focused_module_imports={' '.join(self.focused_module_imports)}")
        else:
            lines.append("focused_module_imports=")
        return lines


def _requires_full_ci_selector_change(files: list[str]) -> bool:
    normalized = {PurePosixPath(f).as_posix() for f in files}
    scoped_md = {f for f in normalized if _is_market_dashboard_scoped_path(f)}
    if scoped_md and all(_is_market_dashboard_rebundle_path(f) for f in normalized):
        return False
    scoped_dc = {f for f in normalized if _is_durable_completion_scoped_path(f)}
    if scoped_dc and all(_is_durable_completion_rebundle_path(f) for f in normalized):
        return False
    scoped_pa = {f for f in normalized if _is_preflight_assembly_scoped_path(f)}
    if scoped_pa and all(_is_preflight_assembly_rebundle_path(f) for f in normalized):
        return False
    scoped_rk = {f for f in normalized if _is_risk_killswitch_scoped_path(f)}
    if scoped_rk and all(_is_risk_killswitch_rebundle_path(f) for f in normalized):
        return False
    scoped_to = {f for f in normalized if _is_tiny_order_scoped_path(f)}
    if scoped_to and all(_is_tiny_order_rebundle_path(f) for f in normalized):
        return False
    if normalized & CI_SELECTOR_FULL_PATHS:
        return True
    if any(f.startswith("tests/ci/test_ci_diff_aware_test_selection") for f in normalized):
        return True
    if ".github/workflows/ci.yml" in normalized and (
        "scripts/ops/ci_test_selection_v1.py" in normalized
        or "config/ci/file_category_mapping.yaml" in normalized
        or any(f.startswith("tests/ci/test_ci_diff_aware_test_selection") for f in normalized)
    ):
        return True
    return False


def _is_market_dashboard_scoped_path(path: str) -> bool:
    if path.startswith("src/webui/market_futures_ohlcv_readmodel_v0/"):
        return True
    if path.startswith("src/webui/market_ranking_funnel_readmodel_v0/"):
        return True
    if path.startswith("templates/peak_trade_dashboard/partials/market_"):
        return True
    if path == "templates/peak_trade_dashboard/market_v0.html":
        return True
    if path.startswith("tests/fixtures/market_"):
        return True
    if path.startswith("tests/fixtures/futures_read_only_market_dashboard"):
        return True
    if path.startswith("tests/webui/test_market_"):
        return True
    if path.startswith("tests/webui/test_futures_read_only_market_dashboard"):
        return True
    if path == "tests/test_market_surface_api.py":
        return True
    market_webui_prefixes = (
        "src/webui/market_",
        "src/webui/futures_read_only_market_dashboard_",
        "src/webui/market_futures_ohlcv_",
        "src/webui/market_ranking_funnel_",
    )
    return any(path.startswith(prefix) and path.endswith(".py") for prefix in market_webui_prefixes)


def _is_market_dashboard_rebundle_path(path: str) -> bool:
    return _is_market_dashboard_scoped_path(path) or path in MARKET_DASHBOARD_CI_POLICY_PATHS


def _market_dashboard_focused_targets() -> tuple[str, ...]:
    targets: list[str] = []
    for path in CANONICAL_MARKET_DASHBOARD_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    return tuple(sorted(targets))


def _is_durable_completion_scoped_path(path: str) -> bool:
    if path == DURABLE_COMPLETION_FACADE_PATH:
        return True
    if path.startswith("src/ops/durable_completion_validation/") and path.endswith(".py"):
        return True
    if path in {
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    }:
        return True
    return False


def _is_durable_completion_rebundle_path(path: str) -> bool:
    return _is_durable_completion_scoped_path(path) or path in DURABLE_COMPLETION_CI_POLICY_PATHS


def _durable_completion_focused_targets() -> tuple[str, ...]:
    for path in REQUIRED_DURABLE_COMPLETION_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    targets: list[str] = []
    for path in CANONICAL_DURABLE_COMPLETION_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    if len(targets) < len(REQUIRED_DURABLE_COMPLETION_TEST_OWNERS):
        return ()
    return tuple(sorted(targets))


def _is_preflight_assembly_scoped_path(path: str) -> bool:
    if path == PE26_ASSEMBLY_OWNER:
        return True
    if path in {
        "tests/ops/test_bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0.py",
        "tests/ops/test_bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0.py",
    }:
        return True
    return False


def _is_preflight_assembly_rebundle_path(path: str) -> bool:
    return _is_preflight_assembly_scoped_path(path) or path in PREFLIGHT_ASSEMBLY_CI_POLICY_PATHS


def _preflight_assembly_focused_targets() -> tuple[str, ...]:
    for path in REQUIRED_PREFLIGHT_ASSEMBLY_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    targets: list[str] = []
    for path in CANONICAL_PREFLIGHT_ASSEMBLY_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    if len(targets) < len(REQUIRED_PREFLIGHT_ASSEMBLY_TEST_OWNERS):
        return ()
    return tuple(sorted(targets))


def _is_risk_killswitch_scoped_path(path: str) -> bool:
    if path == PE22_RISK_KILLSWITCH_OWNER:
        return True
    if path == PE22_RISK_KILLSWITCH_TEST_OWNER:
        return True
    return False


def _is_risk_killswitch_rebundle_path(path: str) -> bool:
    return _is_risk_killswitch_scoped_path(path) or path in RISK_KILLSWITCH_CI_POLICY_PATHS


def _risk_killswitch_focused_targets() -> tuple[str, ...]:
    for path in REQUIRED_RISK_KILLSWITCH_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    targets: list[str] = []
    for path in CANONICAL_RISK_KILLSWITCH_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    if len(targets) < len(REQUIRED_RISK_KILLSWITCH_TEST_OWNERS):
        return ()
    return tuple(sorted(targets))


def _try_risk_killswitch_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_risk_killswitch_scoped_path(f) for f in files):
        return None
    if not all(_is_risk_killswitch_rebundle_path(f) for f in files):
        return None
    files_set = set(files)
    if PE22_RISK_KILLSWITCH_OWNER in files_set and PE22_RISK_KILLSWITCH_TEST_OWNER not in files_set:
        return None
    targets = _risk_killswitch_focused_targets()
    if not targets:
        return None
    modules: tuple[str, ...] = (
        "src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0",
    )
    return SelectionResult(
        "FOCUSED",
        "risk_killswitch_focused",
        targets,
        modules,
    )


def _is_tiny_order_scoped_path(path: str) -> bool:
    if path == PE30_TINY_ORDER_OWNER:
        return True
    if path == PE30_TINY_ORDER_TEST_OWNER:
        return True
    return False


def _is_tiny_order_rebundle_path(path: str) -> bool:
    return _is_tiny_order_scoped_path(path) or path in TINY_ORDER_CI_POLICY_PATHS


def _tiny_order_focused_targets() -> tuple[str, ...]:
    for path in REQUIRED_TINY_ORDER_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    targets: list[str] = []
    for path in CANONICAL_TINY_ORDER_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    if len(targets) < len(REQUIRED_TINY_ORDER_TEST_OWNERS):
        return ()
    return tuple(sorted(targets))


def _try_tiny_order_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_tiny_order_scoped_path(f) for f in files):
        return None
    if not all(_is_tiny_order_rebundle_path(f) for f in files):
        return None
    files_set = set(files)
    if PE30_TINY_ORDER_OWNER in files_set and PE30_TINY_ORDER_TEST_OWNER not in files_set:
        return None
    targets = _tiny_order_focused_targets()
    if not targets:
        return None
    modules: tuple[str, ...] = (
        "src.ops.bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0",
    )
    return SelectionResult(
        "FOCUSED",
        "tiny_order_focused",
        targets,
        modules,
    )


def _try_preflight_assembly_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_preflight_assembly_scoped_path(f) for f in files):
        return None
    if not all(_is_preflight_assembly_rebundle_path(f) for f in files):
        return None
    targets = _preflight_assembly_focused_targets()
    if not targets:
        return None
    modules: tuple[str, ...] = (
        "src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0",
    )
    return SelectionResult(
        "FOCUSED",
        "preflight_assembly_focused",
        targets,
        modules,
    )


def _has_productive_src_python(files: list[str]) -> bool:
    return any(f.startswith("src/") and f.endswith(".py") for f in files)


def _try_durable_completion_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_durable_completion_scoped_path(f) for f in files):
        return None
    if not all(_is_durable_completion_rebundle_path(f) for f in files):
        return None
    targets = _durable_completion_focused_targets()
    if not targets:
        return None
    modules: tuple[str, ...] = (
        "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0",
        "src.ops.durable_completion_validation",
    )
    return SelectionResult(
        "FOCUSED",
        "durable_completion_focused",
        targets,
        modules,
    )


def _try_market_dashboard_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_market_dashboard_scoped_path(f) for f in files):
        return None
    if not all(_is_market_dashboard_rebundle_path(f) for f in files):
        return None
    targets = _market_dashboard_focused_targets()
    if not targets:
        return None
    modules: set[str] = set()
    for path in files:
        if path.startswith("src/webui/") and path.endswith(".py"):
            module = _prod_path_to_import_module(path)
            if _validate_import_module(module):
                modules.add(module)
    return SelectionResult(
        "FOCUSED",
        "market_dashboard_focused",
        targets,
        tuple(sorted(modules)),
    )


def categorize(path: str) -> str:
    p = PurePosixPath(path).as_posix()
    if p in DURABLE_COMPLETION_CI_POLICY_PATHS:
        return "durable_completion_focused"
    if _is_durable_completion_scoped_path(p):
        return "durable_completion_focused"
    if p in PREFLIGHT_ASSEMBLY_CI_POLICY_PATHS:
        return "preflight_assembly_focused"
    if _is_preflight_assembly_scoped_path(p):
        return "preflight_assembly_focused"
    if p in RISK_KILLSWITCH_CI_POLICY_PATHS:
        return "risk_killswitch_focused"
    if _is_risk_killswitch_scoped_path(p):
        return "risk_killswitch_focused"
    if p in TINY_ORDER_CI_POLICY_PATHS:
        return "tiny_order_focused"
    if _is_tiny_order_scoped_path(p):
        return "tiny_order_focused"
    if p in MARKET_DASHBOARD_CI_POLICY_PATHS:
        return "market_dashboard_focused"
    if _is_market_dashboard_scoped_path(p):
        return "market_dashboard_focused"
    if p in CI_SELECTOR_FULL_PATHS:
        return "ci_selector_change"
    if p.startswith("tests/ci/test_ci_diff_aware_test_selection"):
        return "ci_selector_change"
    if p.startswith("src/ops/") and (
        fnmatch.fnmatch(p, "src/ops/*_contract_v0.py")
        or fnmatch.fnmatch(p, "src/ops/*_contract_v1.py")
    ):
        return "static_contract"
    if p.startswith("tests/webui/") and fnmatch.fnmatch(
        Path(p).name, "test_*_structure_contract*.py"
    ):
        return "static_contract"
    if p.startswith("tests/ci/") or p.startswith("tests/ops/"):
        return "static_contract"
    if p == "pytest.ini" or p.endswith("/conftest.py") or p == "tests/conftest.py":
        return "global_test_infra"
    if _is_strategy_regime_owner_prod(p):
        return "strategy_regime_owner_focused"
    if p.startswith("src/"):
        return "central_src"
    if p.startswith("scripts/"):
        return "scripts_focused"
    if p.startswith("tests/"):
        return "tests_focused"
    if p.startswith("docs/") or p.startswith("out/") or p.endswith(".md"):
        return "docs_only"
    if p.startswith(".github/workflows/"):
        return "workflow_only"
    if fnmatch.fnmatch(p, "requirements*.txt") or p in {
        "requirements.txt",
        "pyproject.toml",
        "uv.lock",
    }:
        return "dependencies"
    if p in {"setup.cfg", "setup.py"}:
        return "packaging"
    if p == ".coveragerc":
        return "coverage_config"
    if p == "Makefile" or p.startswith("config/") or p.startswith("schemas/levelup/"):
        return "config_paths"
    return "unknown"


def _is_strategy_regime_owner_prod(path: str) -> bool:
    if path.endswith("__init__.py"):
        return False
    if path in STRATEGY_REGIME_OWNER_BLOCKED_PROD:
        return False
    if path.startswith("src/strategies/") and path.endswith(".py"):
        return True
    if path.startswith("src/regime/") and path.endswith(".py"):
        return True
    return False


def _is_canonical_test_owner(path: str) -> bool:
    if not (path.startswith("tests/") and path.endswith(".py")):
        return False
    if path.startswith("tests/ci/") or path.startswith("tests/ops/"):
        return False
    return True


def _repo_path_exists(path: str) -> bool:
    return Path(path).is_file()


def _prod_path_to_import_module(prod_path: str) -> str:
    return prod_path[:-3].replace("/", ".")


def _validate_repo_relative_path(path: str) -> bool:
    if not path or not _REPO_RELATIVE_PATH.match(path):
        return False
    if path.startswith("/") or ".." in path.split("/"):
        return False
    return path.startswith("tests/") and path.endswith(".py")


def _validate_import_module(module: str) -> bool:
    return bool(module and _IMPORT_MODULE.match(module))


def _discover_load_strategy_contract_tests(prod_path: str) -> tuple[str, ...]:
    module = _prod_path_to_import_module(prod_path)
    import_markers = (
        f"from {module} import",
        f"import {module}",
    )
    found: list[str] = []
    scripts_tests = Path("tests/scripts")
    if not scripts_tests.is_dir():
        return ()
    for candidate in sorted(scripts_tests.glob("test_*load_strategy*.py")):
        rel = candidate.as_posix()
        if not _repo_path_exists(rel):
            continue
        text = candidate.read_text(encoding="utf-8", errors="replace")
        if any(marker in text for marker in import_markers):
            found.append(rel)
    return tuple(found)


def _expected_canonical_test_owner(prod_path: str) -> str | None:
    if prod_path in CANONICAL_STRATEGY_REGIME_TEST_OWNERS:
        return CANONICAL_STRATEGY_REGIME_TEST_OWNERS[prod_path]
    if not prod_path.startswith("src/"):
        return None
    rel = PurePosixPath(prod_path[len("src/") :])
    if len(rel.parts) >= 2:
        return f"tests/{rel.parent}/test_{rel.stem}.py"
    return None


def _strategy_regime_focused_targets(
    prod_path: str, test_path: str, all_files: list[str]
) -> tuple[str, ...] | None:
    if not (_is_strategy_regime_owner_prod(prod_path) and _is_canonical_test_owner(test_path)):
        return None
    expected_owner = _expected_canonical_test_owner(prod_path)
    if (
        expected_owner is None
        or test_path != expected_owner
        or not _repo_path_exists(expected_owner)
    ):
        return None
    if len([f for f in all_files if _is_strategy_regime_owner_prod(f)]) != 1:
        return None
    test_files = [f for f in all_files if _is_canonical_test_owner(f)]
    if len(test_files) != 1 or test_files[0] != test_path:
        return None
    extra = [f for f in all_files if f not in {prod_path, test_path}]
    if extra:
        return None

    targets: list[str] = []
    seen: set[str] = set()

    def add(path: str) -> None:
        if path not in seen and _validate_repo_relative_path(path) and _repo_path_exists(path):
            seen.add(path)
            targets.append(path)

    add(test_path)
    for load_test in _discover_load_strategy_contract_tests(prod_path):
        add(load_test)
    if not targets:
        return None
    return tuple(sorted(targets))


def _try_strategy_regime_owner_focused(files: list[str]) -> SelectionResult | None:
    categories = {categorize(f) for f in files}
    if "ci_selector_change" in categories:
        return None
    if categories & FULL_CATEGORIES:
        return None
    if categories & NO_OP_CATEGORIES:
        return None

    prod_files = sorted(f for f in files if _is_strategy_regime_owner_prod(f))
    test_files = sorted(f for f in files if _is_canonical_test_owner(f))
    if len(prod_files) != 1 or len(test_files) != 1:
        return None

    other = [f for f in files if f not in prod_files and f not in test_files]
    if other:
        return None

    prod_path = prod_files[0]
    test_path = test_files[0]
    targets = _strategy_regime_focused_targets(prod_path, test_path, files)
    if not targets:
        return None

    module = _prod_path_to_import_module(prod_path)
    if not _validate_import_module(module):
        return None

    return SelectionResult(
        "FOCUSED",
        "strategy_regime_owner_focused",
        targets,
        (module,),
    )


def _focused_targets(files: list[str]) -> tuple[str, ...]:
    targets: list[str] = []
    seen: set[str] = set()

    def add(path: str) -> None:
        if path not in seen and _repo_path_exists(path):
            seen.add(path)
            targets.append(path)

    for path in files:
        if path.startswith("tests/") and path.endswith(".py"):
            add(path)
        elif path.startswith("scripts/") and path.endswith(".py"):
            script_stem = PurePosixPath(path).stem
            for candidate in (
                f"tests/scripts/test_{script_stem}_load_strategy_v1.py",
                f"tests/scripts/test_{script_stem}.py",
            ):
                add(candidate)
        elif path == ".github/workflows/ci.yml":
            add("tests/ci/test_ci_diff_aware_test_selection_v1.py")
            add("tests/ci/test_ci_static_contract_narrow_code_filter_contract_v0.py")

    if not targets and any(categorize(f) in FOCUSED_CATEGORIES for f in files):
        add("tests/ci/test_ci_diff_aware_test_selection_v1.py")
    return tuple(sorted(targets))


def resolve_selection(
    files: list[str], *, force_full: bool = False, event_name: str = "pull_request"
) -> SelectionResult:
    normalized = sorted({PurePosixPath(f).as_posix() for f in files if f.strip()})
    if force_full or event_name in {"push", "merge_group", "schedule"}:
        return SelectionResult("FULL", "force_full_or_non_pr_event", ())
    if not normalized:
        return SelectionResult("FULL", "empty_diff_fail_closed", ())

    market_dashboard = _try_market_dashboard_focused(normalized)
    if market_dashboard is not None:
        return market_dashboard

    durable_completion = _try_durable_completion_focused(normalized)
    if durable_completion is not None:
        return durable_completion

    preflight_assembly = _try_preflight_assembly_focused(normalized)
    if preflight_assembly is not None:
        return preflight_assembly

    risk_killswitch = _try_risk_killswitch_focused(normalized)
    if risk_killswitch is not None:
        return risk_killswitch

    tiny_order = _try_tiny_order_focused(normalized)
    if tiny_order is not None:
        return tiny_order

    if any(_is_durable_completion_scoped_path(f) for f in normalized):
        if not all(_is_durable_completion_rebundle_path(f) for f in normalized):
            return SelectionResult("FULL", "durable_completion_foreign_path_requires_full", ())
        return SelectionResult("FULL", "durable_completion_incomplete_or_missing_test_owner", ())

    if any(_is_preflight_assembly_scoped_path(f) for f in normalized):
        if not all(_is_preflight_assembly_rebundle_path(f) for f in normalized):
            return SelectionResult("FULL", "preflight_assembly_foreign_path_requires_full", ())
        return SelectionResult("FULL", "preflight_assembly_incomplete_or_missing_test_owner", ())

    if any(_is_risk_killswitch_scoped_path(f) for f in normalized):
        if not all(_is_risk_killswitch_rebundle_path(f) for f in normalized):
            return SelectionResult("FULL", "risk_killswitch_foreign_path_requires_full", ())
        return SelectionResult("FULL", "risk_killswitch_incomplete_or_missing_test_owner", ())

    if any(_is_tiny_order_scoped_path(f) for f in normalized):
        if not all(_is_tiny_order_rebundle_path(f) for f in normalized):
            return SelectionResult("FULL", "tiny_order_foreign_path_requires_full", ())
        return SelectionResult("FULL", "tiny_order_incomplete_or_missing_test_owner", ())

    if _requires_full_ci_selector_change(normalized):
        return SelectionResult("FULL", "ci_selector_or_contract_change_requires_full", ())

    categories = {categorize(f) for f in normalized}

    if categories & FULL_CATEGORIES:
        hit = sorted(categories & FULL_CATEGORIES)[0]
        return SelectionResult("FULL", f"category_{hit}_requires_full", ())

    if categories <= NO_OP_CATEGORIES:
        if _has_productive_src_python(normalized):
            return SelectionResult("FULL", "productive_src_no_op_blocked_fail_closed", ())
        return SelectionResult("NO_OP", "docs_workflow_or_static_contract_only", ())

    strategy_focused = _try_strategy_regime_owner_focused(normalized)
    if strategy_focused is not None:
        return strategy_focused

    if "strategy_regime_owner_focused" in categories:
        return SelectionResult("FULL", "strategy_regime_owner_incomplete_or_ambiguous", ())

    if categories <= (NO_OP_CATEGORIES | FOCUSED_CATEGORIES):
        return SelectionResult(
            "FOCUSED",
            "focused_script_or_test_diff",
            _focused_targets(normalized),
        )

    return SelectionResult("FULL", "mixed_or_unclassified_fail_closed", ())


def emit_validated_pytest_targets(raw: str) -> int:
    for part in raw.split():
        if not _validate_repo_relative_path(part) or not _repo_path_exists(part):
            print(f"invalid pytest target: {part!r}", file=sys.stderr)
            return 1
        print(part)
    return 0


def run_import_smoke(modules: str) -> int:
    import importlib

    repo_root = Path(__file__).resolve().parents[2]
    root_str = str(repo_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    for part in modules.split():
        if not _validate_import_module(part):
            print(f"invalid import module: {part!r}", file=sys.stderr)
            return 1
        importlib.import_module(part)
        print(f"import smoke ok: {part}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CI diff-aware test selection v1")
    parser.add_argument("--files", nargs="*", default=None, help="Changed file paths")
    parser.add_argument("--files-file", type=Path, default=None)
    parser.add_argument("--force-full", action="store_true")
    parser.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME", "pull_request"))
    parser.add_argument("--github-output", action="store_true")
    parser.add_argument(
        "--emit-validated-pytest-targets",
        metavar="TARGETS",
        help="Print validated repo-relative pytest paths (one per line)",
    )
    parser.add_argument(
        "--import-smoke-modules",
        metavar="MODULES",
        help="Import listed Python modules (space-separated)",
    )
    args = parser.parse_args(argv)

    if args.emit_validated_pytest_targets is not None:
        return emit_validated_pytest_targets(args.emit_validated_pytest_targets)

    if args.import_smoke_modules is not None:
        return run_import_smoke(args.import_smoke_modules)

    files: list[str] = []
    if args.files_file and args.files_file.exists():
        files = [
            ln.strip()
            for ln in args.files_file.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
    elif args.files is not None:
        files = list(args.files)
    else:
        raw = os.environ.get("CHANGED_FILES", "")
        files = [ln.strip() for ln in raw.splitlines() if ln.strip()]

    result = resolve_selection(files, force_full=args.force_full, event_name=args.event_name)
    lines = result.github_output_lines()
    if args.github_output:
        out_path = os.environ.get("GITHUB_OUTPUT")
        if out_path:
            with open(out_path, "a", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
        else:
            print("\n".join(lines))
    else:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
