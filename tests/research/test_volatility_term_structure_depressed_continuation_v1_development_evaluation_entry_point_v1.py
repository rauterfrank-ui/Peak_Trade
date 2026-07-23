"""Focused tests for VTDC development-evaluation entry path (post DEVELOPMENT_FAIL)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.research.volatility_term_structure_depressed_continuation_v1_development_evaluation_v1.authorization_v1 import (
    resolve_authorization_decision_v1,
)
from src.research.volatility_term_structure_depressed_continuation_v1_development_evaluation_v1.binding_v1 import (
    load_and_validate_entry_point_binding,
)
from src.research.volatility_term_structure_depressed_continuation_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    FROZEN_MEASUREMENT_CONTRACT_DIGEST,
    HYPOTHESIS_ID,
)
from src.research.volatility_term_structure_depressed_continuation_v1_development_evaluation_v1.entry_point_v1 import (
    run_dry_validate,
    run_preflight_only,
)
from src.research.volatility_term_structure_depressed_continuation_v1_development_evaluation_v1.guards_v1 import (
    GuardError,
    assert_holdout_guard,
    assert_no_slot_reuse,
    assert_retry_forbidden,
)

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / (
    "docs/evidence/evaluate_volatility_term_structure_depressed_continuation_development_v1"
)


def test_entry_point_binding_slot_consumed_development_fail() -> None:
    ep = load_and_validate_entry_point_binding(REPO)
    assert ep["status"] == "RUN_SLOT_CONSUMED_DEVELOPMENT_FAIL"
    assert ep["development_evaluation_authorized"] is True
    assert ep["development_evaluation_executed"] is True
    assert ep["development_run_count"] == 1
    assert ep["runner_start_count"] == 1
    assert ep["frozen_measurement_contract_digest"] == FROZEN_MEASUREMENT_CONTRACT_DIGEST
    assert ep["dataset_binding"]["dataset_id"] == DATASET_ID
    assert ep["holdout_forbidden"] is True
    assert ep["evaluation_authorized"] is False
    assert ep["runtime_policy"]["live_authorized"] is False
    assert ep["runtime_policy"]["orders_allowed"] is False
    assert ep["verdict"] == "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL"


def test_preflight_and_dry_validate_do_not_start_runner_after_slot_consume() -> None:
    pre = run_preflight_only(REPO)
    assert pre["runner_started"] is False
    assert pre["evaluation_executed"] is False
    assert pre["holdout_accessed"] is False
    assert pre["run_counters"]["contract_development_run_count"] == 1
    dry = run_dry_validate(REPO)
    assert dry["runner_started"] is False
    assert dry["evaluation_executed"] is False
    assert dry["status"] == "DRY_VALIDATE_PASS_EXECUTABLE_PATH_PRESENT"
    assert dry["run_counters"]["contract_development_run_count"] == 1


def test_unauthorized_token_fail_closed() -> None:
    decision = resolve_authorization_decision_v1(REPO, authorize_token="WRONG")
    assert decision.authorized is False
    assert "AUTHORIZE_TOKEN_MISMATCH" in decision.reason_codes


def test_authorized_token_surfaces_still_machine_checkable() -> None:
    decision = resolve_authorization_decision_v1(REPO, authorize_token=HYPOTHESIS_ID)
    assert decision.authorize_token_valid is True
    assert decision.repo_development_evaluation_authorized is True
    assert decision.program_development_evaluation_authorized is True
    assert decision.entry_point_binding_authorized is True
    assert decision.authorized is True


def test_holdout_retry_and_slot_reuse_guards() -> None:
    assert_holdout_guard(dataset_id=DATASET_ID)
    with pytest.raises(GuardError, match="HOLDOUT"):
        assert_holdout_guard(
            dataset_id=DATASET_ID,
            attempted_holdout_ids=("offline_economic_reevaluation_sealed_long_panel_v1",),
        )
    with pytest.raises(GuardError, match="RUN_LIMIT_EXHAUSTED"):
        assert_retry_forbidden(development_run_count=1, runner_start_count=1)
    with pytest.raises(GuardError, match="SLOT"):
        assert_no_slot_reuse(EVIDENCE)
