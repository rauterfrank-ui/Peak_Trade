"""Contract tests for CI static-contract narrow code path filter (ci.yml v0/v1).

YAML structure assertions plus path semantics aligned with dorny/paths-filter
(picomatch extglob). Semantics helper mirrors the three `tests/` code globs and
webui_surface / non_webui_code buckets (Market/Observability path gating).
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

import pytest

CI_YML = Path(".github/workflows/ci.yml")

CODE_TEST_GLOBS = (
    "tests/!(ci|ops|webui)/**",
    "tests/webui/!(test_*_structure_contract*)/**",
    "tests/webui/!(test_*_structure_contract*).py",
)
STATIC_CONTRACT_WEBUI_GLOB = "tests/webui/test_*_structure_contract*.py"
STATIC_OPS_CONTRACT_GLOB = "src/ops/*_contract_v0.py"
STATIC_OPS_CONTRACT_V1_GLOB = "src/ops/*_contract_v1.py"
SRC_OPS_NON_CONTRACT_GLOB = "src/ops/!(*_contract_v0.py|*_contract_v1.py)"
SRC_NON_OPS_GLOB = "src/!(ops)/**"
WEBUI_SURFACE_GLOBS = (
    "src/webui/**",
    "templates/peak_trade_dashboard/**",
    "docs/webui/**",
    "tests/webui/**",
    "tests/fixtures/**",
    "tests/ops/test_*_env_schema_boundary*.py",
)
NON_WEBUI_CODE_GLOBS = (
    "src/!(ops|webui)/**",
    "src/ops/!(*_contract_v0.py|*_contract_v1.py)",
    "templates/!(peak_trade_dashboard)/**",
    "tests/!(ci|ops|webui|fixtures)/**",
    "scripts/**",
    "config/**",
    "schemas/levelup/**",
    "requirements.txt",
    "requirements*.txt",
    "pyproject.toml",
    "uv.lock",
    "pytest.ini",
    "Makefile",
)
WEBUI_BOUNDED_PYTEST_MODULES = (
    "tests/webui/test_workflow_dashboard_readmodel_v1.py",
    "tests/webui/test_observability_workflow_dashboard_structure_contract_v1.py",
    "tests/ops/test_workflow_dashboard_env_schema_boundary_v1.py",
    "tests/webui/test_observability_hub.py",
    "tests/webui/test_last_paper_run_panel_readmodel_v0.py",
    "tests/webui/test_observability_last_paper_run_panel_structure_contract_v0.py",
    "tests/ops/test_last_paper_run_panel_env_schema_boundary_v0.py",
    "tests/webui/test_market_dashboard_readonly_structure_contract_v0.py",
)


def _ci_text() -> str:
    return CI_YML.read_text(encoding="utf-8")


def _code_block() -> str:
    text = _ci_text()
    start = text.index("            code:")
    end = text.index("            static_contract:")
    return text[start:end]


def _webui_surface_block() -> str:
    text = _ci_text()
    start = text.index("            webui_surface:")
    end = text.index("            non_webui_code:")
    return text[start:end]


def _non_webui_code_block() -> str:
    text = _ci_text()
    start = text.index("            non_webui_code:")
    end = text.index("            static_contract:")
    return text[start:end]


def _static_block() -> str:
    text = _ci_text()
    start = text.index("            static_contract:")
    end = text.index("            docs:")
    return text[start:end]


def _matches_picomatch_extglob(path: str, pattern: str) -> bool:
    """Subset of picomatch extglob used by ci.yml `tests/` code bucket (PR #3728 fix)."""
    if pattern == "tests/!(ci|ops|webui)/**":
        if not path.startswith("tests/"):
            return False
        rest = path[len("tests/") :]
        if not rest or rest.split("/")[0] in {"ci", "ops", "webui"}:
            return False
        return True
    if pattern == "tests/webui/!(test_*_structure_contract*)/**":
        if not path.startswith("tests/webui/"):
            return False
        rest = path[len("tests/webui/") :]
        if not rest:
            return False
        first = rest.split("/")[0]
        return not fnmatch.fnmatch(first, "test_*_structure_contract*")
    if pattern == "tests/webui/!(test_*_structure_contract*).py":
        if not path.startswith("tests/webui/") or "/" in path[len("tests/webui/") :]:
            return False
        name = path.rsplit("/", 1)[-1]
        return not fnmatch.fnmatch(name, "test_*_structure_contract*.py")
    raise AssertionError(f"unsupported pattern: {pattern!r}")


def _matches_code_tests_bucket(path: str) -> bool:
    return any(_matches_picomatch_extglob(path, g) for g in CODE_TEST_GLOBS)


def _matches_static_contract_webui(path: str) -> bool:
    return fnmatch.fnmatch(path, STATIC_CONTRACT_WEBUI_GLOB)


def _matches_static_contract_ops_src(path: str) -> bool:
    return fnmatch.fnmatch(path, STATIC_OPS_CONTRACT_GLOB)


def _matches_static_contract_ops_v1(path: str) -> bool:
    return fnmatch.fnmatch(path, STATIC_OPS_CONTRACT_V1_GLOB)


def _matches_static_contract_ops_offline(path: str) -> bool:
    return _matches_static_contract_ops_src(path) or _matches_static_contract_ops_v1(path)


def _is_contract_only_fast_lane_candidate(paths: list[str]) -> bool:
    if not paths:
        return False
    for path in paths:
        if fnmatch.fnmatch(path, STATIC_OPS_CONTRACT_V1_GLOB):
            continue
        if fnmatch.fnmatch(path, "tests/ops/test_*_contract_v1.py"):
            continue
        return False
    return True


def _matches_code_filter(path: str) -> bool:
    if path.startswith("templates/"):
        return True
    if _matches_static_contract_ops_offline(path):
        return False
    if path.startswith("src/ops/"):
        return True
    if path.startswith("src/"):
        return True
    return _matches_code_tests_bucket(path)


def _matches_webui_surface(path: str) -> bool:
    if path.startswith("src/webui/"):
        return True
    if path.startswith("templates/peak_trade_dashboard/"):
        return True
    if path.startswith("docs/webui/"):
        return True
    if path.startswith("tests/webui/"):
        return True
    if path.startswith("tests/fixtures/"):
        return True
    return fnmatch.fnmatch(path, "tests/ops/test_*_env_schema_boundary*.py")


def _matches_non_webui_code(path: str) -> bool:
    if path in {"requirements.txt", "pyproject.toml", "uv.lock", "pytest.ini", "Makefile"}:
        return True
    if path.startswith("requirements") and path.endswith(".txt"):
        return True
    if path.startswith(("scripts/", "config/", "schemas/levelup/")):
        return True
    if path.startswith("src/webui/"):
        return False
    if _matches_static_contract_ops_offline(path):
        return False
    if path.startswith("src/ops/"):
        return True
    if path.startswith("src/"):
        return True
    if path.startswith("templates/peak_trade_dashboard/"):
        return False
    if path.startswith("templates/"):
        return True
    if path.startswith("tests/fixtures/") or path.startswith("tests/webui/"):
        return False
    if path.startswith("tests/"):
        top = path.split("/")[1]
        if top in {"ci", "ops", "webui", "fixtures"}:
            return False
        return True
    return False


def _run_matrix_for_paths(paths: list[str], *, force_matrix: bool = False) -> bool:
    if force_matrix:
        return True
    return any(_matches_non_webui_code(p) for p in paths)


def test_changes_job_exports_static_contract_outputs() -> None:
    text = _ci_text()
    assert "static_contract_changed:" in text
    assert "docs_or_static_contract_only:" in text
    assert "static_contract_changed=${STATIC}" in text
    assert "docs_or_static_contract_only=true" in text


def test_code_filter_uses_picomatch_extglob_for_tests_bucket() -> None:
    code_block = _code_block()
    for glob in CODE_TEST_GLOBS:
        assert f"'{glob}'" in code_block
    assert "'tests/**'" not in code_block
    assert "'!tests/ci/**'" not in code_block
    assert "'!tests/ops/**'" not in code_block
    assert "'!tests/webui/test_*_structure_contract*.py'" not in code_block


def test_static_contract_includes_webui_structure_contract_whitelist() -> None:
    static_block = _static_block()
    assert f"'{STATIC_CONTRACT_WEBUI_GLOB}'" in static_block


def test_static_contract_includes_ops_offline_contract_modules() -> None:
    static_block = _static_block()
    assert f"'{STATIC_OPS_CONTRACT_GLOB}'" in static_block


def test_static_contract_includes_ops_contract_v1_modules() -> None:
    static_block = _static_block()
    assert f"'{STATIC_OPS_CONTRACT_V1_GLOB}'" in static_block


def test_code_filter_narrows_src_ops_contract_v0_modules() -> None:
    code_block = _code_block()
    assert f"'{SRC_NON_OPS_GLOB}'" in code_block
    assert f"'{SRC_OPS_NON_CONTRACT_GLOB}'" in code_block
    assert "'src/**'" not in code_block
    assert "'templates/**'" in code_block


@pytest.mark.parametrize(
    ("path", "expect_code", "expect_static"),
    [
        (
            "tests/webui/test_market_dashboard_readonly_structure_contract_v0.py",
            False,
            True,
        ),
        ("tests/webui/test_other_webui_behavior.py", True, False),
        (
            "tests/webui/subdir/test_market_dashboard_readonly_structure_contract_v0.py",
            True,
            False,
        ),
        ("tests/ci/foo.py", False, False),
        ("tests/ops/foo.py", False, False),
        ("tests/fixtures/foo.py", True, False),
        ("src/webui/app.py", True, False),
        ("src/ops/bounded_futures_testnet_contract_v0.py", False, True),
        ("src/ops/bounded_futures_testnet_runtime_module.py", True, False),
        ("templates/peak_trade_dashboard/market_v0.html", True, False),
    ],
)
def test_code_and_static_contract_path_semantics_v0(
    path: str,
    expect_code: bool,
    expect_static: bool,
) -> None:
    assert _matches_code_filter(path) is expect_code
    static_match = _matches_static_contract_webui(path) or _matches_static_contract_ops_src(path)
    assert static_match is expect_static


def test_webui_surface_and_non_webui_code_filters_present() -> None:
    webui_block = _webui_surface_block()
    non_webui_block = _non_webui_code_block()
    for glob in WEBUI_SURFACE_GLOBS:
        assert f"'{glob}'" in webui_block
    for glob in NON_WEBUI_CODE_GLOBS:
        assert f"'{glob}'" in non_webui_block


def test_changes_job_exports_webui_surface_outputs() -> None:
    text = _ci_text()
    assert "webui_surface_changed:" in text
    assert "webui_surface_only:" in text
    assert "webui_surface_changed=${WEBUI}" in text
    assert "webui_surface_only=true" in text


def test_run_matrix_derived_from_non_webui_code_not_raw_code_bucket() -> None:
    text = _ci_text()
    assert 'NON_WEBUI="${{ steps.filter.outputs.non_webui_code }}"' in text
    assert 'echo "run_matrix=${CODE}"' not in text
    assert 'elif [ "$NON_WEBUI" = "true" ]; then' in text
    assert 'echo "run_matrix=false"' in text


def test_matrix_jobs_keep_no_job_level_if_and_short_circuit_skip() -> None:
    text = _ci_text()
    assert "name: tests (${{ matrix.python-version }})" in text
    assert "NO_OP — skip full matrix tests (diff-aware)" in text
    assert "IMPORTANT: No job-level if condition - matrix jobs must always be created" in text
    assert "Skip strategy smoke (NO_OP/FOCUSED diff-aware)" in text
    assert "needs.changes.outputs.tests_execute_no_op == 'true'" in text
    assert "needs.changes.outputs.tests_execute_full == 'true'" in text


def test_strategy_smoke_gated_on_tests_execute_full_not_code_changed() -> None:
    text = _ci_text()
    assert "name: strategy-smoke" in text
    assert "needs.changes.outputs.tests_execute_full == 'true'" in text
    assert "needs.changes.outputs.code_changed == 'true'" not in text


def test_fast_lane_uses_selector_static_contract_dispatch() -> None:
    text = _ci_text()
    fast_lane_block = text.split("  fast-lane:", 1)[1].split("  tests:", 1)[0]
    assert "Static contract tests (selector-targeted, bounded NO_OP)" in fast_lane_block
    assert "needs.changes.outputs.fast_lane_execute_static_contract == 'true'" in fast_lane_block
    assert "fast_lane_pytest_targets" in fast_lane_block
    assert "find tests/ops" not in fast_lane_block
    assert "pytest tests/ci tests/ops" not in fast_lane_block


def test_fast_lane_webui_bounded_pytest_modules() -> None:
    text = _ci_text()
    assert "WebUI bounded pytest (market/observability surface)" in text
    assert "needs.changes.outputs.webui_surface_changed == 'true'" in text
    assert "PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED" in text
    assert "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED" in text
    for module in WEBUI_BOUNDED_PYTEST_MODULES:
        assert module in text


def test_required_check_names_unchanged() -> None:
    text = _ci_text()
    assert "name: tests (${{ matrix.python-version }})" in text
    assert "name: strategy-smoke" in text
    assert "name: Fast-Lane" in text
    assert "python-version: ['3.9', '3.10', '3.11']" in text


def test_code_changed_output_uses_narrowed_code_bucket_not_raw_filter_alias() -> None:
    text = _ci_text()
    assert "code_changed: ${{ steps.set_outputs.outputs.code_changed }}" in text
    assert "code_changed: ${{ steps.filter.outputs.code }}" not in text


@pytest.mark.parametrize(
    ("path", "expect_webui", "expect_non_webui"),
    [
        ("src/webui/app.py", True, False),
        ("templates/peak_trade_dashboard/market_v0.html", True, False),
        ("docs/webui/observability/OBSERVABILITY_HUB_V0.md", True, False),
        ("tests/webui/test_observability_hub.py", True, False),
        ("tests/fixtures/workflow_dashboard_readmodel_v1/foo.json", True, False),
        ("tests/ops/test_workflow_dashboard_env_schema_boundary_v1.py", True, False),
        ("tests/ops/test_other_ops.py", False, False),
        ("src/execution/foo.py", False, True),
        ("pyproject.toml", False, True),
        ("templates/other/template.html", False, True),
    ],
)
def test_webui_surface_and_non_webui_path_semantics_v1(
    path: str,
    expect_webui: bool,
    expect_non_webui: bool,
) -> None:
    assert _matches_webui_surface(path) is expect_webui
    assert _matches_non_webui_code(path) is expect_non_webui


@pytest.mark.parametrize(
    ("paths", "expect_run_matrix"),
    [
        (["src/webui/app.py", "templates/peak_trade_dashboard/market_v0.html"], False),
        (["src/webui/app.py", "pyproject.toml"], True),
        (["docs/foo.md"], False),
        (["src/execution/module.py"], True),
        (
            [
                "src/webui/workflow_dashboard_readmodel_v1/builder.py",
                "tests/webui/test_workflow_dashboard_readmodel_v1.py",
                "tests/ops/test_workflow_dashboard_env_schema_boundary_v1.py",
            ],
            False,
        ),
    ],
)
def test_run_matrix_semantics_for_path_sets_v1(paths: list[str], expect_run_matrix: bool) -> None:
    assert _run_matrix_for_paths(paths) is expect_run_matrix


@pytest.mark.parametrize(
    ("path", "expect_code", "expect_static", "expect_non_webui"),
    [
        ("src/ops/order_capability_payload_builder_contract_v1.py", False, True, False),
        ("src/ops/order_capability_killswitch_abort_binding_contract_v1.py", False, True, False),
        ("src/ops/order_capability_cancel_cleanup_failclosed_contract_v1.py", False, True, False),
        ("tests/ops/test_order_capability_payload_builder_contract_v1.py", False, False, False),
        ("src/execution/contracts.py", True, False, True),
        ("src/risk_layer/kill_switch/foo.py", True, False, True),
        ("scripts/ops/run_order_capability_foo.py", False, False, True),
    ],
)
def test_contract_v1_path_semantics(
    path: str,
    expect_code: bool,
    expect_static: bool,
    expect_non_webui: bool,
) -> None:
    assert _matches_code_filter(path) is expect_code
    assert _matches_static_contract_ops_offline(path) is expect_static
    assert _matches_non_webui_code(path) is expect_non_webui


@pytest.mark.parametrize(
    ("paths", "expect_contract_only", "expect_run_matrix"),
    [
        (["src/ops/order_capability_payload_builder_contract_v1.py"], True, False),
        (
            [
                "src/ops/order_capability_killswitch_abort_binding_contract_v1.py",
                "tests/ops/test_order_capability_killswitch_abort_binding_contract_v1.py",
            ],
            True,
            False,
        ),
        (
            [
                "src/ops/order_capability_cancel_cleanup_failclosed_contract_v1.py",
                "tests/ops/test_order_capability_cancel_cleanup_failclosed_contract_v1.py",
            ],
            True,
            False,
        ),
        (["src/execution/contracts.py"], False, True),
        (["src/risk_layer/kill_switch/foo.py"], False, True),
        (["scripts/ops/run_order_capability_foo.py"], False, True),
        ([".github/workflows/ci.yml"], False, False),
        (
            [
                "src/ops/order_capability_foo_contract_v1.py",
                "src/runtime/bar.py",
            ],
            False,
            True,
        ),
    ],
)
def test_contract_only_v1_run_matrix_semantics(
    paths: list[str],
    expect_contract_only: bool,
    expect_run_matrix: bool,
) -> None:
    assert _is_contract_only_fast_lane_candidate(paths) is expect_contract_only
    assert _run_matrix_for_paths(paths) is expect_run_matrix


def test_force_matrix_overrides_contract_only_v1_paths() -> None:
    paths = [
        "src/ops/order_capability_payload_builder_contract_v1.py",
        "tests/ops/test_order_capability_payload_builder_contract_v1.py",
    ]
    assert _is_contract_only_fast_lane_candidate(paths) is True
    assert _run_matrix_for_paths(paths, force_matrix=False) is False
    assert _run_matrix_for_paths(paths, force_matrix=True) is True
