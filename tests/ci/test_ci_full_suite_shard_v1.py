"""Contract tests for deterministic FULL-suite CI sharding (v1)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ops.ci_full_suite_shard_v1 import (
    DEFAULT_SHARD_COUNT,
    MAX_SHARD_COUNT,
    MIN_SHARD_COUNT,
    enumerate_test_files,
    partition_files,
    verify_completeness,
)

CI_YML = Path(".github/workflows/ci.yml")
NIGHTLY_YML = Path(".github/workflows/ci-extended-nightly.yml")
SHARD_SCRIPT = Path("scripts/ops/ci_full_suite_shard_v1.py")


def _ci_text() -> str:
    return CI_YML.read_text(encoding="utf-8")


def _nightly_text() -> str:
    return NIGHTLY_YML.read_text(encoding="utf-8")


def test_shard_script_exists() -> None:
    assert SHARD_SCRIPT.is_file()


def test_default_shard_count_in_allowed_range() -> None:
    assert MIN_SHARD_COUNT <= DEFAULT_SHARD_COUNT <= MAX_SHARD_COUNT


def test_all_test_files_assigned_exactly_once() -> None:
    verify_completeness(DEFAULT_SHARD_COUNT)


def test_no_empty_shards() -> None:
    buckets = partition_files(DEFAULT_SHARD_COUNT)
    assert all(buckets[idx] for idx in range(DEFAULT_SHARD_COUNT))


def test_no_duplicate_assignments() -> None:
    buckets = partition_files(DEFAULT_SHARD_COUNT)
    flat = [path for idx in range(DEFAULT_SHARD_COUNT) for path in buckets[idx]]
    assert len(flat) == len(set(flat))


def test_partition_covers_full_inventory() -> None:
    all_files = enumerate_test_files()
    buckets = partition_files(DEFAULT_SHARD_COUNT)
    assigned = {path for idx in range(DEFAULT_SHARD_COUNT) for path in buckets[idx]}
    assert assigned == set(all_files)


def test_emit_shard_files_cli_matches_partition() -> None:
    for shard_id in range(DEFAULT_SHARD_COUNT):
        out = subprocess.check_output(
            [sys.executable, str(SHARD_SCRIPT), "--emit-shard-files", str(shard_id)],
            text=True,
        )
        cli_files = [line for line in out.splitlines() if line]
        assert cli_files == partition_files(DEFAULT_SHARD_COUNT)[shard_id]


def test_verify_completeness_cli_exits_zero() -> None:
    subprocess.run(
        [sys.executable, str(SHARD_SCRIPT), "--verify-completeness"],
        check=True,
    )


def test_ci_tests_job_uses_sharded_full_suite_not_monolith() -> None:
    text = _ci_text()
    assert "Run full test suite (sharded)" in text
    assert "ci_full_suite_shard_v1.py --verify-completeness" in text
    assert "ci_full_suite_shard_v1.py --emit-shard-files" in text
    assert re.search(r"pytest\s+tests/\s", text) is None


def test_ci_tests_job_timeout_is_25_minutes() -> None:
    assert re.search(
        r"^\s*tests:\n(?:.*\n)*?\s*timeout-minutes:\s*25\s*$",
        _ci_text(),
        re.MULTILINE,
    )


def test_ci_pr_gate_timeout_is_10_minutes() -> None:
    pr_gate_block = _ci_text().split("  pr-gate:", 1)[1].split("  #", 1)[0]
    assert re.search(r"timeout-minutes:\s*10", pr_gate_block)


def test_ci_fast_lane_timeout_is_15_minutes() -> None:
    fast_lane_block = _ci_text().split("  fast-lane:", 1)[1].split("  #", 1)[0]
    assert re.search(r"timeout-minutes:\s*15", fast_lane_block)


def test_ci_coverage_uses_sharded_append_not_full_rerun() -> None:
    text = _ci_text()
    assert "Coverage report (FULL 3.11 sharded)" in text
    assert "coverage xml" in text
    assert "pytest tests/ --cov=src" not in text


def test_nightly_workflow_uses_github_hosted_runner() -> None:
    text = _nightly_text()
    assert "runs-on: ubuntu-latest" in text
    assert "self-hosted" not in text


def test_nightly_workflow_has_schedule_and_dispatch() -> None:
    text = _nightly_text()
    assert "schedule:" in text
    assert "30 2 * * *" in text
    assert "workflow_dispatch" in text


def test_nightly_workflow_timeout_is_60_minutes_per_shard() -> None:
    shard_block = (
        _nightly_text()
        .split("  extended-nightly-shard:", 1)[1]
        .split("  extended-nightly-aggregate:", 1)[0]
    )
    assert re.search(r"timeout-minutes:\s*60", shard_block)


def test_nightly_aggregate_fail_closed_on_shard_failure() -> None:
    text = _nightly_text()
    aggregate = text.split("  extended-nightly-aggregate:", 1)[1]
    assert "if: always() && !cancelled()" in aggregate
    assert "needs.extended-nightly-shard.result" in aggregate
    assert "exit 1" in aggregate


def test_nightly_does_not_start_runtime_or_exchange() -> None:
    text = _nightly_text().lower()
    forbidden = (
        "testnet",
        "live_start",
        "paper_start",
        "shadow_start",
        "exchange_api",
        "credentials",
        "scheduler_start",
    )
    for token in forbidden:
        assert token not in text


def test_required_tests_job_naming_preserved() -> None:
    text = _ci_text()
    tests_block = text.split("  tests:", 1)[1].split("  strategy-smoke:", 1)[0]
    assert re.search(
        r"name:\s*tests\s*\(\$\{\{\s*matrix\.python-version\s*\}\}\)",
        tests_block,
    )


def test_required_tests_job_has_no_job_level_if() -> None:
    tests_block = _ci_text().split("  tests:", 1)[1].split("  strategy-smoke:", 1)[0]
    assert "if:" not in tests_block.split("steps:")[0]
