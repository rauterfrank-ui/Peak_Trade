"""Regression: GHV forensic control binding fail-closed semantics."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.ghv_forensic_control_binding_v1 import (
    FORENSIC_CONTROL_EXPECTED_SHA,
    FORENSIC_CONTROL_SETTINGS_DIGEST,
    ForensicControlBindingError,
    resolve_forensic_control_binding_v1,
)

REPO = Path(__file__).resolve().parents[2]
WT = REPO / ".ghv_worktrees/b36ccbaa"


def test_correct_historical_control_accepted() -> None:
    if not WT.is_dir():
        pytest.skip("fixpoint worktree missing")
    b = resolve_forensic_control_binding_v1(REPO, fail_closed=True)
    assert b.sha_match is True
    assert b.actual_sha == FORENSIC_CONTROL_EXPECTED_SHA
    assert b.settings_match is True
    assert b.settings_digest == FORENSIC_CONTROL_SETTINGS_DIGEST
    banner = b.emit_banner()
    assert banner["FORENSIC_HEAD_SHA"] == FORENSIC_CONTROL_EXPECTED_SHA


def test_wrong_expected_sha_fail_closed() -> None:
    if not WT.is_dir():
        pytest.skip("fixpoint worktree missing")
    with pytest.raises(ForensicControlBindingError, match="sha_mismatch"):
        resolve_forensic_control_binding_v1(REPO, expected_sha="0" * 40, fail_closed=True)


def test_missing_worktree_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ForensicControlBindingError, match="missing_forensic_control_worktree"):
        resolve_forensic_control_binding_v1(tmp_path, fail_closed=True)
