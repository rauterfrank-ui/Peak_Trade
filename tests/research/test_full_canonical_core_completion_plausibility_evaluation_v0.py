"""Contract tests for full canonical core completion plausibility evaluation v0."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST,
    REASON_NEW_EVIDENCE_CLASS_REQUIRED,
    REASON_UNMODIFIED_BINDING_RETRY_BLOCKED,
    verify_unmodified_retry_admissibility_v0,
)
from src.research.full_canonical_core_completion_plausibility_evaluation_v0 import (
    DIAGNOSTIC_STATUS,
    DIAGNOSTIC_TOLERATED_UNTRACKED_PATHS,
    EVIDENCE_CLASS_ID,
    OWNER_POLICY_REL,
    REASON_OWNER_POLICY_AUTHORITY_FLAG_TRUE,
    REASON_OWNER_POLICY_DIGEST_MISMATCH,
    REASON_UNTOLERATED_UNTRACKED_PATH,
    build_diagnostic_output_v0,
    compute_owner_policy_decision_digest_v0,
    is_worktree_clean_for_diagnostic_evidence_class_v0,
    list_non_tolerated_untracked_paths_v0,
    verify_execution_start_state_v0,
    verify_historical_negative_evidence_immutable_v0,
    verify_owner_policy_v0,
    verify_unmodified_retry_for_diagnostic_evidence_class_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = REPO_ROOT / OWNER_POLICY_REL
BINDING_PATH = (
    REPO_ROOT / "config/research/final_research_fleet_versioned_binding_completion_v0.json"
)


@pytest.fixture(name="owner_policy")
def fixture_owner_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


@pytest.fixture(name="historical_binding_completion")
def fixture_historical_binding_completion() -> dict:
    payload = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
    assert payload.get("completion_digest") == HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST
    return payload


def test_owner_policy_config_digest_is_self_consistent(owner_policy: dict) -> None:
    expected = compute_owner_policy_decision_digest_v0(owner_policy)
    assert owner_policy["owner_policy_decision_digest"] == expected
    assert owner_policy["evidence_class"] == EVIDENCE_CLASS_ID
    assert owner_policy["purpose"] == "CORE_SYSTEM_COMPLETION_DIAGNOSTIC"
    assert owner_policy["unmodified_binding_retry_global_override"] is False


def test_unchanged_ordinary_binding_retry_remains_blocked() -> None:
    ok, reasons = verify_unmodified_retry_admissibility_v0(
        fleet_binding_completion={
            "completion_digest": HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST,
        },
    )
    assert ok is False
    assert REASON_UNMODIFIED_BINDING_RETRY_BLOCKED in reasons
    assert REASON_NEW_EVIDENCE_CLASS_REQUIRED in reasons


def test_diagnostic_evidence_class_with_valid_owner_policy_is_allowed(
    owner_policy: dict,
    historical_binding_completion: dict,
) -> None:
    ok, reasons = verify_unmodified_retry_admissibility_v0(
        fleet_binding_completion=historical_binding_completion,
        requested_execution_evidence_class=EVIDENCE_CLASS_ID,
        owner_policy=owner_policy,
    )
    assert ok is True
    assert reasons == ()


def test_missing_owner_policy_digest_blocks(owner_policy: dict) -> None:
    broken = dict(owner_policy)
    broken["owner_policy_decision_digest"] = "deadbeef"
    ok, reasons = verify_owner_policy_v0(broken)
    assert ok is False
    assert REASON_OWNER_POLICY_DIGEST_MISMATCH in reasons


def test_any_true_runtime_flag_blocks(owner_policy: dict) -> None:
    broken = dict(owner_policy)
    broken["live_authorized"] = True
    ok, reasons = verify_owner_policy_v0(broken)
    assert ok is False
    assert any(REASON_OWNER_POLICY_AUTHORITY_FLAG_TRUE in reason for reason in reasons)


def test_historical_negative_evidence_immutable_guard(
    historical_binding_completion: dict,
) -> None:
    ok, reasons = verify_historical_negative_evidence_immutable_v0(
        fleet_binding_completion=historical_binding_completion,
    )
    assert ok is True
    assert reasons == ()


def test_historical_negative_evidence_mutation_blocked() -> None:
    ok, reasons = verify_historical_negative_evidence_immutable_v0(
        fleet_binding_completion={
            "completion_digest": HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST,
            "economic_validity_offline_gate_pass": True,
        },
    )
    assert ok is False


def test_diagnostic_output_is_not_promotion_or_runtime_admissible(owner_policy: dict) -> None:
    output = build_diagnostic_output_v0(
        owner_policy=owner_policy,
        parity_status_counts={"PASS": 1, "PARTIAL": 2},
    )
    assert output["status"] == DIAGNOSTIC_STATUS
    assert output["promotion_admissible"] is False
    assert output["runtime_admissible"] is False
    assert output["live_authorized"] is False
    assert output["orders_allowed"] is False
    assert output["economic_validity_claim_allowed"] is False


def test_tolerated_untracked_paths_do_not_block_diagnostic_class() -> None:
    porcelain = "?? .python-version\n?? .comparison_ssot_pytest_outputs/foo/bar.json\n"
    with patch(
        "src.research.full_canonical_core_completion_plausibility_evaluation_v0._git_status_porcelain",
        return_value=[line for line in porcelain.splitlines() if line.strip()],
    ):
        ok, reasons = is_worktree_clean_for_diagnostic_evidence_class_v0(REPO_ROOT)
        assert ok is True
        assert reasons == ()


def test_arbitrary_untracked_files_still_block_diagnostic_class() -> None:
    porcelain = "?? .python-version\n?? scratch.txt\n"
    with patch(
        "src.research.full_canonical_core_completion_plausibility_evaluation_v0._git_status_porcelain",
        return_value=[line for line in porcelain.splitlines() if line.strip()],
    ):
        ok, reasons = is_worktree_clean_for_diagnostic_evidence_class_v0(REPO_ROOT)
        assert ok is False
        assert any(REASON_UNTOLERATED_UNTRACKED_PATH in reason for reason in reasons)
        assert "scratch.txt" in reasons[0]


def test_list_non_tolerated_untracked_paths() -> None:
    porcelain = "?? .python-version\n?? scratch.txt\n M README.md\n"
    with patch(
        "src.research.full_canonical_core_completion_plausibility_evaluation_v0._git_status_porcelain",
        return_value=[line for line in porcelain.splitlines() if line.strip()],
    ):
        blocked = list_non_tolerated_untracked_paths_v0(REPO_ROOT)
        assert ".python-version" not in blocked
        assert "scratch.txt" in blocked
        assert "README.md" in blocked


def test_diagnostic_unmodified_retry_without_owner_policy_still_blocked(
    historical_binding_completion: dict,
) -> None:
    ok, reasons = verify_unmodified_retry_for_diagnostic_evidence_class_v0(
        fleet_binding_completion=historical_binding_completion,
        owner_policy={"owner_policy_decision_digest": "invalid"},
    )
    assert ok is False


def test_start_state_accepts_valid_policy_and_historical_binding(
    owner_policy: dict,
    historical_binding_completion: dict,
) -> None:
    with patch(
        "src.research.full_canonical_core_completion_plausibility_evaluation_v0._git_status_porcelain",
        return_value=["?? .python-version"],
    ):
        result = verify_execution_start_state_v0(
            repo_root=REPO_ROOT,
            fleet_binding_completion=historical_binding_completion,
            owner_policy=owner_policy,
        )
    assert result.valid is True
    assert ".python-version" in result.tolerated_untracked_paths


def test_tolerated_untracked_artefacts_documented() -> None:
    assert ".python-version" in DIAGNOSTIC_TOLERATED_UNTRACKED_PATHS
    assert ".comparison_ssot_pytest_outputs/" in DIAGNOSTIC_TOLERATED_UNTRACKED_PATHS


def test_central_retry_helper_accepts_diagnostic_class_with_policy(
    owner_policy: dict,
    historical_binding_completion: dict,
) -> None:
    ok, _ = verify_unmodified_retry_admissibility_v0(
        fleet_binding_completion=historical_binding_completion,
        requested_execution_evidence_class=EVIDENCE_CLASS_ID,
        owner_policy=owner_policy,
    )
    assert ok is True


def test_central_retry_helper_rejects_diagnostic_class_without_policy(
    historical_binding_completion: dict,
) -> None:
    ok, reasons = verify_unmodified_retry_admissibility_v0(
        fleet_binding_completion=historical_binding_completion,
        requested_execution_evidence_class=EVIDENCE_CLASS_ID,
        owner_policy=None,
    )
    assert ok is False
    assert REASON_UNMODIFIED_BINDING_RETRY_BLOCKED in reasons
