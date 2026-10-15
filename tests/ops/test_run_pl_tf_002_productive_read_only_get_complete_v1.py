"""Tests for PL-TF-002 productive read-only GET completion ops runner."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

from src.ops.pl_tf_002_productive_read_only_get_complete_v1.constants_v1 import (
    F1_OWNER_SCOPED_CUMULATIVE_GET_BUDGET,
    OWNER_GO,
    SESSION_OWNER_GO,
)
from tests.ops.test_pl_tf_002_runtime_integrity_v1 import _FakeIntegrityBackend

_TEST_ORIGIN_MAIN = "9bd633bb175dab27dc383b91a512e379bd31cefa"
_TEST_INTEGRITY = _FakeIntegrityBackend(
    origin_main=_TEST_ORIGIN_MAIN,
    head=_TEST_ORIGIN_MAIN,
)
_RUNNER = (
    Path(__file__).resolve().parents[2]
    / "scripts/ops/run_pl_tf_002_productive_read_only_get_complete_v1.py"
)


def _run_runner(argv: list[str]) -> int:
    sys.argv = [str(_RUNNER), *argv]
    try:
        runpy.run_path(str(_RUNNER), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code)
    return 0


def test_runner_execute_network_requires_grant_store() -> None:
    rc = _run_runner(
        [
            "--wp-owner-go",
            OWNER_GO,
            "--session-owner-go",
            SESSION_OWNER_GO,
            "--bound-origin-main-sha",
            _TEST_ORIGIN_MAIN,
            "--execute-network",
        ]
    )
    assert rc == 2


def test_runner_rejects_wrong_wp_owner_go() -> None:
    rc = _run_runner(
        [
            "--wp-owner-go",
            "WRONG",
            "--session-owner-go",
            SESSION_OWNER_GO,
        ]
    )
    assert rc == 2


def test_runner_default_budget_is_f1_nine() -> None:
    assert F1_OWNER_SCOPED_CUMULATIVE_GET_BUDGET == 9
