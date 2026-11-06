"""Narrow contract tests for Non-Class-D offline evaluation live origin-main policy."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    NON_CLASS_D_OFFLINE_EVAL_ORIGIN_MAIN_POLICY_TEST_REL,
    ORIGIN_MAIN_AFTER_FULL_CANONICAL_BACKTEST_PARITY_CLOSEOUT_SHA,
    ORIGIN_MAIN_AFTER_NON_CLASS_D_OFFLINE_EVAL_ORIGIN_MAIN_POLICY_PR4990_SHA,
    ORIGIN_MAIN_AFTER_PR4991_NON_CLASS_D_ORIGIN_MAIN_ALLOWLIST_FIX_SHA,
    ORIGIN_MAIN_AFTER_PR4992_NON_CLASS_D_ORIGIN_MAIN_ALLOWLIST_FIX_SHA,
    MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA,
    PR4826_MERGE_COMMIT,
    PR4833_MERGE_COMMIT,
    PR4834_MERGE_COMMIT,
    REASON_CURRENT_MAIN_SHA_DRIFT_AFTER_SQUASH_MERGE,
    REASON_LOCAL_HEAD_NOT_ORIGIN_MAIN,
    REASON_WORKTREE_NOT_CLEAN,
    is_accepted_origin_main_sha,
    is_class_d_binding_completion_v0,
    is_non_class_d_offline_eval_origin_main_policy_test_present_v0,
    resolve_current_execution_origin_main_sha,
    resolve_non_class_d_offline_eval_origin_main_policy_test_path_v0,
    validate_non_class_d_live_post_merge_origin_main_v0,
    verify_origin_main_sha_for_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
NON_CLASS_D_BINDING_PATH = (
    REPO_ROOT / "config/research/final_research_fleet_versioned_binding_completion_v0.json"
)
STALE_PR4992_BASE_SHA = ORIGIN_MAIN_AFTER_PR4992_NON_CLASS_D_ORIGIN_MAIN_ALLOWLIST_FIX_SHA


def test_legacy_non_class_d_origin_main_shas_remain_in_historical_set() -> None:
    for sha in (
        PR4826_MERGE_COMMIT,
        MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA,
        PR4833_MERGE_COMMIT,
        PR4834_MERGE_COMMIT,
        ORIGIN_MAIN_AFTER_FULL_CANONICAL_BACKTEST_PARITY_CLOSEOUT_SHA,
        ORIGIN_MAIN_AFTER_NON_CLASS_D_OFFLINE_EVAL_ORIGIN_MAIN_POLICY_PR4990_SHA,
        ORIGIN_MAIN_AFTER_PR4991_NON_CLASS_D_ORIGIN_MAIN_ALLOWLIST_FIX_SHA,
        STALE_PR4992_BASE_SHA,
    ):
        assert is_accepted_origin_main_sha(sha)


def test_live_origin_main_accepted_after_post_merge_sync() -> None:
    live_origin_main = resolve_current_execution_origin_main_sha(REPO_ROOT)
    assert live_origin_main
    with (
        patch(
            "src.research.final_research_fleet_offline_economic_evaluation_execution_v0.resolve_local_head_sha",
            return_value=live_origin_main,
        ),
        patch(
            "src.research.final_research_fleet_offline_economic_evaluation_execution_v0.is_worktree_clean",
            return_value=True,
        ),
    ):
        ok, reasons = validate_non_class_d_live_post_merge_origin_main_v0(
            origin_main_sha=live_origin_main,
            repo_root=REPO_ROOT,
            live_origin_main_sha=live_origin_main,
        )
    assert ok is True
    assert reasons == ()


def test_stale_pr_base_sha_alone_not_live_post_merge_proof() -> None:
    live_origin_main = resolve_current_execution_origin_main_sha(REPO_ROOT)
    assert live_origin_main
    assert is_accepted_origin_main_sha(STALE_PR4992_BASE_SHA)
    if live_origin_main == STALE_PR4992_BASE_SHA:
        return
    ok, reasons = validate_non_class_d_live_post_merge_origin_main_v0(
        origin_main_sha=STALE_PR4992_BASE_SHA,
        repo_root=REPO_ROOT,
        live_origin_main_sha=live_origin_main,
    )
    assert ok is False
    assert any(REASON_CURRENT_MAIN_SHA_DRIFT_AFTER_SQUASH_MERGE in reason for reason in reasons)


def test_head_not_origin_main_blocks_fail_closed() -> None:
    live_origin_main = resolve_current_execution_origin_main_sha(REPO_ROOT)
    assert live_origin_main
    drifted_head = "deadbeef" * 5
    with patch(
        "src.research.final_research_fleet_offline_economic_evaluation_execution_v0.resolve_local_head_sha",
        return_value=drifted_head,
    ):
        ok, reasons = validate_non_class_d_live_post_merge_origin_main_v0(
            origin_main_sha=live_origin_main,
            repo_root=REPO_ROOT,
            live_origin_main_sha=live_origin_main,
        )
    assert ok is False
    assert any(REASON_LOCAL_HEAD_NOT_ORIGIN_MAIN in reason for reason in reasons)


def test_dirty_worktree_blocks_fail_closed() -> None:
    live_origin_main = resolve_current_execution_origin_main_sha(REPO_ROOT)
    assert live_origin_main
    with patch(
        "src.research.final_research_fleet_offline_economic_evaluation_execution_v0.is_worktree_clean",
        return_value=False,
    ):
        ok, reasons = validate_non_class_d_live_post_merge_origin_main_v0(
            origin_main_sha=live_origin_main,
            repo_root=REPO_ROOT,
            live_origin_main_sha=live_origin_main,
        )
    assert ok is False
    assert REASON_WORKTREE_NOT_CLEAN in reasons


def test_canonical_test_path_resolves_without_stub() -> None:
    assert is_non_class_d_offline_eval_origin_main_policy_test_present_v0(REPO_ROOT)
    path = resolve_non_class_d_offline_eval_origin_main_policy_test_path_v0(REPO_ROOT)
    assert path == REPO_ROOT / NON_CLASS_D_OFFLINE_EVAL_ORIGIN_MAIN_POLICY_TEST_REL
    assert path.is_file()


def test_verify_origin_main_accepts_synced_main_for_non_class_d_binding() -> None:
    fleet_binding_completion = json.loads(NON_CLASS_D_BINDING_PATH.read_text(encoding="utf-8"))
    assert is_class_d_binding_completion_v0(fleet_binding_completion) is False
    live_origin_main = resolve_current_execution_origin_main_sha(REPO_ROOT)
    with (
        patch(
            "src.research.final_research_fleet_offline_economic_evaluation_execution_v0.resolve_local_head_sha",
            return_value=live_origin_main,
        ),
        patch(
            "src.research.final_research_fleet_offline_economic_evaluation_execution_v0.is_worktree_clean",
            return_value=True,
        ),
    ):
        ok, reasons = verify_origin_main_sha_for_binding_v0(
            origin_main_sha=live_origin_main,
            fleet_binding_completion=fleet_binding_completion,
            repo_root=REPO_ROOT,
        )
    assert ok is True
    assert reasons == ()
