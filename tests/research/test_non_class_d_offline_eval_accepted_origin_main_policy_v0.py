"""Narrow contract tests for Non-Class-D offline evaluation origin-main allowlist."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    ORIGIN_MAIN_AFTER_FULL_CANONICAL_BACKTEST_PARITY_CLOSEOUT_SHA,
    ORIGIN_MAIN_AFTER_NON_CLASS_D_OFFLINE_EVAL_ORIGIN_MAIN_POLICY_PR4990_SHA,
    ORIGIN_MAIN_AFTER_PR4991_NON_CLASS_D_ORIGIN_MAIN_ALLOWLIST_FIX_SHA,
    PR4826_MERGE_COMMIT,
    PR4833_MERGE_COMMIT,
    PR4834_MERGE_COMMIT,
    MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA,
    is_accepted_origin_main_sha,
    is_class_d_binding_completion_v0,
    resolve_current_execution_origin_main_sha,
    verify_origin_main_sha_for_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
NON_CLASS_D_BINDING_PATH = (
    REPO_ROOT / "config/research/final_research_fleet_versioned_binding_completion_v0.json"
)


def test_legacy_non_class_d_origin_main_shas_remain_accepted() -> None:
    for sha in (
        PR4826_MERGE_COMMIT,
        MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA,
        PR4833_MERGE_COMMIT,
        PR4834_MERGE_COMMIT,
        ORIGIN_MAIN_AFTER_FULL_CANONICAL_BACKTEST_PARITY_CLOSEOUT_SHA,
        ORIGIN_MAIN_AFTER_NON_CLASS_D_OFFLINE_EVAL_ORIGIN_MAIN_POLICY_PR4990_SHA,
    ):
        assert is_accepted_origin_main_sha(sha)


def test_current_origin_main_accepted_for_non_class_d_policy() -> None:
    live_origin_main = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert live_origin_main == resolve_current_execution_origin_main_sha(REPO_ROOT)
    assert (
        live_origin_main == ORIGIN_MAIN_AFTER_PR4991_NON_CLASS_D_ORIGIN_MAIN_ALLOWLIST_FIX_SHA
    )
    assert is_accepted_origin_main_sha(live_origin_main)


def test_verify_origin_main_accepts_current_main_for_non_class_d_binding() -> None:
    fleet_binding_completion = json.loads(NON_CLASS_D_BINDING_PATH.read_text(encoding="utf-8"))
    assert is_class_d_binding_completion_v0(fleet_binding_completion) is False
    live_origin_main = resolve_current_execution_origin_main_sha(REPO_ROOT)
    ok, reasons = verify_origin_main_sha_for_binding_v0(
        origin_main_sha=live_origin_main,
        fleet_binding_completion=fleet_binding_completion,
    )
    assert ok is True
    assert reasons == ()
