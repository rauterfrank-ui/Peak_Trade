"""Contract tests for Class-D squash-merge identity-gated current-main acceptance v0."""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import pytest

from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    CLASS_D_BINDING_COMPLETION_DIGEST,
    GO_TOKEN_OPERATOR_ALIAS,
    LEGACY_STATIC_EXECUTION_ORIGIN_MAIN_SHA,
    MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA,
    ORDER_EFFECT,
    PR4834_MERGE_COMMIT,
    REASON_BINDING_IDENTITY_MISMATCH,
    REASON_CURRENT_MAIN_SHA_DRIFT_AFTER_SQUASH_MERGE,
    REASON_EVALUATION_ALREADY_EXECUTED,
    REASON_ORIGIN_MAIN_MISMATCH,
    RUNTIME_EFFECT,
    is_accepted_go_token,
    load_scope_ratification_for_execution_v0,
    resolve_current_execution_origin_main_sha,
    validate_current_main_against_immutable_binding_identity,
    verify_execution_start_state_v0,
    verify_origin_main_sha_for_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLASS_D_BINDING_PATH = (
    REPO_ROOT / "config/research/final_research_fleet_class_d_versioned_binding_completion_v0.json"
)
HYPOTHETICAL_POST_SQUASH_MAIN_SHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
STALE_PR4833_SHA = LEGACY_STATIC_EXECUTION_ORIGIN_MAIN_SHA


@pytest.fixture(name="class_d_binding_completion")
def fixture_class_d_binding_completion() -> dict:
    assert CLASS_D_BINDING_PATH.is_file(), f"missing: {CLASS_D_BINDING_PATH}"
    return json.loads(CLASS_D_BINDING_PATH.read_text(encoding="utf-8"))


def test_live_origin_main_resolves_to_current_execution_candidate() -> None:
    live = resolve_current_execution_origin_main_sha(REPO_ROOT)
    expected = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert live == expected
    assert live == PR4834_MERGE_COMMIT


def test_new_squash_merge_sha_accepted_when_binding_identity_unchanged(
    class_d_binding_completion: dict,
) -> None:
    ok, reasons = validate_current_main_against_immutable_binding_identity(
        origin_main_sha=HYPOTHETICAL_POST_SQUASH_MAIN_SHA,
        fleet_binding_completion=class_d_binding_completion,
        live_origin_main_sha=HYPOTHETICAL_POST_SQUASH_MAIN_SHA,
    )
    assert ok is True
    assert reasons == ()


def test_stale_pinned_pr4833_sha_rejected_when_live_main_advanced(
    class_d_binding_completion: dict,
) -> None:
    ok, reasons = validate_current_main_against_immutable_binding_identity(
        origin_main_sha=STALE_PR4833_SHA,
        fleet_binding_completion=class_d_binding_completion,
        live_origin_main_sha=PR4834_MERGE_COMMIT,
    )
    assert ok is False
    assert any(REASON_CURRENT_MAIN_SHA_DRIFT_AFTER_SQUASH_MERGE in reason for reason in reasons)


def test_exclusive_static_pin_regression_no_longer_accepts_stale_main(
    class_d_binding_completion: dict,
) -> None:
    ok, reasons = verify_origin_main_sha_for_binding_v0(
        origin_main_sha=STALE_PR4833_SHA,
        fleet_binding_completion=class_d_binding_completion,
        live_origin_main_sha=PR4834_MERGE_COMMIT,
    )
    assert ok is False
    assert STALE_PR4833_SHA != PR4834_MERGE_COMMIT
    assert any(REASON_CURRENT_MAIN_SHA_DRIFT_AFTER_SQUASH_MERGE in reason for reason in reasons)


def test_materialization_sha_rejected_as_execution_origin(
    class_d_binding_completion: dict,
) -> None:
    ok, reasons = validate_current_main_against_immutable_binding_identity(
        origin_main_sha=MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA,
        fleet_binding_completion=class_d_binding_completion,
        live_origin_main_sha=MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA,
    )
    assert ok is False
    assert any(REASON_ORIGIN_MAIN_MISMATCH in reason for reason in reasons)


def test_changed_completion_digest_rejected(
    class_d_binding_completion: dict,
) -> None:
    tampered = copy.deepcopy(class_d_binding_completion)
    tampered["completion_digest"] = "0" * 64
    ok, reasons = validate_current_main_against_immutable_binding_identity(
        origin_main_sha=PR4834_MERGE_COMMIT,
        fleet_binding_completion=tampered,
        live_origin_main_sha=PR4834_MERGE_COMMIT,
    )
    assert ok is False
    assert any(REASON_BINDING_IDENTITY_MISMATCH in reason for reason in reasons)


def test_live_origin_main_accepted_for_class_d_start_state(
    class_d_binding_completion: dict,
) -> None:
    ratification = load_scope_ratification_for_execution_v0(
        repo_root=REPO_ROOT,
        fleet_binding_completion=class_d_binding_completion,
    )
    result = verify_execution_start_state_v0(
        repo_root=REPO_ROOT,
        ratification=ratification,
        fleet_binding_completion=class_d_binding_completion,
    )
    assert result.valid is True
    assert result.origin_main_sha == PR4834_MERGE_COMMIT
    assert class_d_binding_completion["completion_digest"] == CLASS_D_BINDING_COMPLETION_DIGEST


def test_evaluation_authorization_still_blocked_without_go_token() -> None:
    assert is_accepted_go_token(GO_TOKEN_OPERATOR_ALIAS) is True
    assert is_accepted_go_token("GO_UNKNOWN") is False


def test_changed_scope_ratification_rejects_execution_without_go(
    class_d_binding_completion: dict,
) -> None:
    ratification = load_scope_ratification_for_execution_v0(
        repo_root=REPO_ROOT,
        fleet_binding_completion=class_d_binding_completion,
    )
    tampered = copy.deepcopy(ratification)
    tampered["economic_evaluation_executed"] = True
    result = verify_execution_start_state_v0(
        repo_root=REPO_ROOT,
        ratification=tampered,
        fleet_binding_completion=class_d_binding_completion,
        origin_main_sha=PR4834_MERGE_COMMIT,
    )
    assert result.valid is False
    assert any(REASON_EVALUATION_ALREADY_EXECUTED in reason for reason in result.fail_reasons)


def test_runtime_authority_flags_remain_false() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"
