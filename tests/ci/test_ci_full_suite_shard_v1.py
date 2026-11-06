"""Contract tests for deterministic FULL-suite CI sharding (v1)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.ops.ci_full_suite_shard_v1 import (
    DEFAULT_SHARD_COUNT,
    MAX_SHARD_COUNT,
    MIN_SHARD_COUNT,
    enumerate_test_files,
    partition_files,
    verify_completeness,
)

NIGHTLY_YML = Path(".github/workflows/test-health-automation.yml")
SHARD_SCRIPT = Path("scripts/ops/ci_full_suite_shard_v1.py")


def test_shard_script_exists() -> None:
    assert SHARD_SCRIPT.is_file()


def test_default_shard_count_in_allowed_range() -> None:
    assert MIN_SHARD_COUNT <= DEFAULT_SHARD_COUNT <= MAX_SHARD_COUNT


def test_all_test_files_assigned_exactly_once() -> None:
    verify_completeness(DEFAULT_SHARD_COUNT)


def test_nightly_workflow_has_exhaustive_full_job() -> None:
    text = NIGHTLY_YML.read_text(encoding="utf-8")
    assert "exhaustive-full:" in text
    assert "run_exhaustive_full" in text
    assert "schedule:" in text
    assert "pytest tests/" in text.split("exhaustive-full:", 1)[1]


def test_emit_shard_files_cli() -> None:
    out = subprocess.check_output(
        [sys.executable, str(SHARD_SCRIPT), "--emit-shard-files", "0"],
        text=True,
    )
    paths = [line for line in out.splitlines() if line]
    assert paths
    buckets = partition_files(DEFAULT_SHARD_COUNT)
    assert paths == buckets[0]
