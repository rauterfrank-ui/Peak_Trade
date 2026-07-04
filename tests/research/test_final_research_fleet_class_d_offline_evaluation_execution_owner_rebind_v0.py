"""Contract tests for Class-D offline evaluation execution owner rebind v0."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    CLASS_D_BINDING_COMPLETION_DIGEST,
    DURABLE_EVIDENCE_BUNDLE_PREFIX,
    DURABLE_EVIDENCE_SUBDIR,
    GO_TOKEN_OPERATOR_ALIAS,
    LEGACY_DURABLE_EVIDENCE_BUNDLE_PREFIX,
    LEGACY_DURABLE_EVIDENCE_SUBDIR,
    LEGACY_STATIC_EXECUTION_ORIGIN_MAIN_SHA,
    MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA,
    ORDER_EFFECT,
    PR4826_MERGE_COMMIT,
    PR4832_MERGE_COMMIT,
    PR4834_MERGE_COMMIT,
    RUNTIME_EFFECT,
    is_accepted_go_token,
    is_accepted_origin_main_sha,
    is_class_d_binding_completion_v0,
    load_scope_ratification_for_execution_v0,
    resolve_current_execution_origin_main_sha,
    resolve_expected_origin_main_sha,
    resolve_durable_evidence_bundle_dir_v0,
    resolve_legacy_durable_evidence_bundle_dir_v0,
    validate_binding_completion_for_execution_v0,
    verify_execution_start_state_v0,
    verify_origin_main_sha_for_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLASS_D_BINDING_PATH = (
    REPO_ROOT / "config/research/final_research_fleet_class_d_versioned_binding_completion_v0.json"
)
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")


@pytest.fixture(name="class_d_binding_completion")
def fixture_class_d_binding_completion() -> dict:
    assert CLASS_D_BINDING_PATH.is_file(), f"missing: {CLASS_D_BINDING_PATH}"
    return json.loads(CLASS_D_BINDING_PATH.read_text(encoding="utf-8"))


def test_execution_origin_resolves_from_live_origin_main() -> None:
    live = resolve_current_execution_origin_main_sha(REPO_ROOT)
    assert live == resolve_expected_origin_main_sha(REPO_ROOT)
    assert live == PR4834_MERGE_COMMIT
    assert live != LEGACY_STATIC_EXECUTION_ORIGIN_MAIN_SHA


def test_materialization_sha_retained_but_not_current_execution_pin() -> None:
    assert MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA == PR4832_MERGE_COMMIT
    assert MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA == "ddce9c508158b89fa225c381436e2d1efced7328"
    assert is_accepted_origin_main_sha(MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA)
    assert (
        resolve_current_execution_origin_main_sha(REPO_ROOT) != MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA
    )


def test_legacy_pr4826_sha_still_accepted_for_non_class_d_set() -> None:
    assert is_accepted_origin_main_sha(PR4826_MERGE_COMMIT)
    assert resolve_current_execution_origin_main_sha(REPO_ROOT) != PR4826_MERGE_COMMIT


def test_class_d_completion_digest_accepted(class_d_binding_completion: dict) -> None:
    assert is_class_d_binding_completion_v0(class_d_binding_completion)
    assert class_d_binding_completion["completion_digest"] == CLASS_D_BINDING_COMPLETION_DIGEST
    ok, reasons = validate_binding_completion_for_execution_v0(
        class_d_binding_completion,
        repo_root=REPO_ROOT,
        require_ready_for_eval=True,
    )
    assert ok is True
    assert reasons == ()


def test_class_d_start_state_accepts_live_origin_main(class_d_binding_completion: dict) -> None:
    ratification = load_scope_ratification_for_execution_v0(
        repo_root=REPO_ROOT,
        fleet_binding_completion=class_d_binding_completion,
    )
    live = resolve_current_execution_origin_main_sha(REPO_ROOT)
    result = verify_execution_start_state_v0(
        repo_root=REPO_ROOT,
        ratification=ratification,
        fleet_binding_completion=class_d_binding_completion,
        origin_main_sha=live,
    )
    assert result.valid is True
    assert result.fail_reasons == ()


def test_class_d_start_state_rejects_materialization_sha_as_current_execution_origin(
    class_d_binding_completion: dict,
) -> None:
    ratification = load_scope_ratification_for_execution_v0(
        repo_root=REPO_ROOT,
        fleet_binding_completion=class_d_binding_completion,
    )
    ok, reasons = verify_origin_main_sha_for_binding_v0(
        origin_main_sha=MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA,
        fleet_binding_completion=class_d_binding_completion,
        live_origin_main_sha=MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA,
    )
    assert ok is False
    assert any("ORIGIN_MAIN_SHA_MISMATCH" in reason for reason in reasons)
    result = verify_execution_start_state_v0(
        repo_root=REPO_ROOT,
        ratification=ratification,
        fleet_binding_completion=class_d_binding_completion,
        origin_main_sha=MATERIALIZED_CLASS_D_ORIGIN_MAIN_SHA,
    )
    assert result.valid is False


def test_class_d_start_state_rejects_stale_pr4826_origin_only(
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
        origin_main_sha=PR4826_MERGE_COMMIT,
    )
    assert result.valid is False
    assert any(
        token in reason
        for reason in result.fail_reasons
        for token in ("ORIGIN_MAIN_SHA_MISMATCH", "CURRENT_MAIN_SHA_DRIFT_AFTER_SQUASH_MERGE")
    )


def test_live_origin_main_sha_accepted_for_class_d_execution(
    class_d_binding_completion: dict,
) -> None:
    live_origin_main = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert live_origin_main == resolve_current_execution_origin_main_sha(REPO_ROOT)
    ratification = load_scope_ratification_for_execution_v0(
        repo_root=REPO_ROOT,
        fleet_binding_completion=class_d_binding_completion,
    )
    result = verify_execution_start_state_v0(
        repo_root=REPO_ROOT,
        ratification=ratification,
        fleet_binding_completion=class_d_binding_completion,
        origin_main_sha=live_origin_main,
    )
    assert result.valid is True
    assert result.fail_reasons == ()


def test_durable_evidence_path_owner_contract() -> None:
    bundle = resolve_durable_evidence_bundle_dir_v0(
        durable_evidence_root=ARCHIVE_ROOT,
        timestamp_slug="20260704T231500Z",
    )
    legacy = resolve_legacy_durable_evidence_bundle_dir_v0(
        durable_evidence_root=ARCHIVE_ROOT,
        timestamp_slug="20260704T231500Z",
    )
    assert bundle.parts[-2:] == (
        DURABLE_EVIDENCE_SUBDIR,
        f"{DURABLE_EVIDENCE_BUNDLE_PREFIX}_20260704T231500Z",
    )
    assert legacy.parts[-2:] == (
        LEGACY_DURABLE_EVIDENCE_SUBDIR,
        f"{LEGACY_DURABLE_EVIDENCE_BUNDLE_PREFIX}_20260704T231500Z",
    )


def test_evaluation_not_started_without_go_token() -> None:
    assert is_accepted_go_token(GO_TOKEN_OPERATOR_ALIAS) is True
    assert is_accepted_go_token("GO_UNKNOWN") is False


def test_runtime_authority_flags_remain_false() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"
