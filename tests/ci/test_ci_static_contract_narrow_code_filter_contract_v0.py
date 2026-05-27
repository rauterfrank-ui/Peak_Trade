"""Contract tests for CI static-contract narrow code path filter (ci.yml v0).

Read-only YAML text assertions; no workflow dispatch, no GitHub API, no runtime.
"""

from __future__ import annotations

from pathlib import Path

CI_YML = Path(".github/workflows/ci.yml")


def _ci_text() -> str:
    return CI_YML.read_text(encoding="utf-8")


def test_changes_job_exports_static_contract_outputs() -> None:
    text = _ci_text()
    assert "static_contract_changed:" in text
    assert "docs_or_static_contract_only:" in text
    assert "static_contract_changed=${STATIC}" in text
    assert "docs_or_static_contract_only=true" in text


def test_code_filter_excludes_tests_ci_and_ops_buckets() -> None:
    text = _ci_text()
    assert "static_contract:" in text
    assert "'tests/ci/**'" in text
    assert "'tests/ops/**'" in text
    assert "'!tests/ci/**'" in text
    assert "'!tests/ops/**'" in text


def test_matrix_jobs_keep_no_job_level_if_and_short_circuit_skip() -> None:
    text = _ci_text()
    assert "name: tests (${{ matrix.python-version }})" in text
    assert "Docs/static-contract PR — skip full matrix tests" in text
    assert "IMPORTANT: No job-level if condition - matrix jobs must always be created" in text
    assert "Docs/static-contract PR — skip strategy smoke tests" in text


def test_fast_lane_runs_static_contract_tests_when_applicable() -> None:
    text = _ci_text()
    assert "Static contract tests (tests/ci, tests/ops)" in text
    assert "needs.changes.outputs.static_contract_changed == 'true'" in text
    assert "pytest tests/ci tests/ops" in text


def test_code_changed_output_uses_narrowed_code_bucket_not_raw_filter_alias() -> None:
    text = _ci_text()
    assert "code_changed: ${{ steps.set_outputs.outputs.code_changed }}" in text
    assert "code_changed: ${{ steps.filter.outputs.code }}" not in text
