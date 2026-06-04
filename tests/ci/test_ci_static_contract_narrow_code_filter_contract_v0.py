"""Contract tests for CI static-contract narrow code path filter (ci.yml v0).

YAML structure assertions plus path semantics aligned with dorny/paths-filter
(picomatch extglob). Semantics helper mirrors the three `tests/` code globs.
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
SRC_OPS_NON_CONTRACT_GLOB = "src/ops/!(*_contract_v0.py)"
SRC_NON_OPS_GLOB = "src/!(ops)/**"


def _ci_text() -> str:
    return CI_YML.read_text(encoding="utf-8")


def _code_block() -> str:
    text = _ci_text()
    start = text.index("            code:")
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


def _matches_code_filter(path: str) -> bool:
    if path.startswith("templates/"):
        return True
    if _matches_static_contract_ops_src(path):
        return False
    if path.startswith("src/ops/"):
        return True
    if path.startswith("src/"):
        return True
    return _matches_code_tests_bucket(path)


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


def test_matrix_jobs_keep_no_job_level_if_and_short_circuit_skip() -> None:
    text = _ci_text()
    assert "name: tests (${{ matrix.python-version }})" in text
    assert "Docs/static-contract PR — skip full matrix tests" in text
    assert "IMPORTANT: No job-level if condition - matrix jobs must always be created" in text
    assert "Docs/static-contract PR — skip strategy smoke tests" in text


def test_fast_lane_runs_static_contract_tests_when_applicable() -> None:
    text = _ci_text()
    assert "Static contract tests (tests/ci, tests/ops, WebUI structure-contract" in text
    assert "needs.changes.outputs.static_contract_changed == 'true'" in text
    assert "pytest tests/ci tests/ops" in text
    assert "webui_structure_contract=(tests/webui/test_*structure_contract*.py)" in text
    assert '"${webui_structure_contract[@]}"' in text


def test_code_changed_output_uses_narrowed_code_bucket_not_raw_filter_alias() -> None:
    text = _ci_text()
    assert "code_changed: ${{ steps.set_outputs.outputs.code_changed }}" in text
    assert "code_changed: ${{ steps.filter.outputs.code }}" not in text
