"""Contract tests for CS short-horizon return reversal v1 DEVELOPMENT evaluation surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.cross_sectional_short_horizon_return_reversal_v1_development_evaluation_v1.authorization_v1 import (
    resolve_authorization_decision_v1,
)
from src.research.cross_sectional_short_horizon_return_reversal_v1_development_evaluation_v1.binding_v1 import (
    compute_strategy_params_digest,
    load_and_validate_entry_point_binding,
)
from src.research.cross_sectional_short_horizon_return_reversal_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    DEFAULT_LOOKBACK_N,
    DEFAULT_REBALANCE_INTERVAL_BARS,
    DEVELOPMENT_RUN_LIMIT,
    HYPOTHESIS_ID,
    PREREGISTRATION_ORIGINAL_DIGEST,
    SCOPE_ID,
)
from src.research.cross_sectional_short_horizon_return_reversal_v1_development_evaluation_v1.evaluate_path_v1 import (
    dry_validate_evaluate_path_v1,
    run_authorized_development_evaluation_v1,
)
from src.research.cross_sectional_short_horizon_return_reversal_v1_development_evaluation_v1.execution_boundary_v1 import (
    BacktestMetricsBundleV1,
    FakeExecutionBoundaryV1,
    PanelLoadResultV1,
)
from src.research.cross_sectional_short_horizon_return_reversal_v1_development_evaluation_v1.guards_v1 import (
    GuardError,
    assert_retry_forbidden,
    read_run_counters,
)
from src.research.cross_sectional_short_horizon_return_reversal_v1_development_evaluation_v1.authorization_v1 import (
    authorization_decision_from_mapping,
)

REPO = Path(__file__).resolve().parents[2]
CSRHR = (
    REPO
    / "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
)


def test_frozen_params_and_scope() -> None:
    assert DEFAULT_LOOKBACK_N == 24
    assert DEFAULT_REBALANCE_INTERVAL_BARS == 4
    assert DEVELOPMENT_RUN_LIMIT == 1
    assert DATASET_ID == "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
    assert (
        SCOPE_ID
        == "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1_BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION_V1"
    )
    assert PREREGISTRATION_ORIGINAL_DIGEST == (
        "3d983bbfa1db6c319f6c4399549679a5b7fd2d635d8e72d4452330da9059729a"
    )
    assert compute_strategy_params_digest() == (
        "c0944b9cb3c29bb6cfdb8eca72edf7d62d1ce462bfdce77c398ee4ced8fa232d"
    )


def test_slot_consumed_and_retry_forbidden() -> None:
    counters = read_run_counters(REPO)
    assert counters["contract_development_run_count"] == 1
    assert counters["contract_runner_start_count"] == 1
    with pytest.raises(GuardError, match="RUN_LIMIT_EXHAUSTED"):
        assert_retry_forbidden(development_run_count=1, runner_start_count=1)


def test_binding_terminal_and_evidence_fail() -> None:
    binding = load_and_validate_entry_point_binding(REPO)
    assert binding["development_evaluation_authorized"] is True
    assert binding["development_run_count"] == 1
    assert binding["holdout_forbidden"] is True
    assert binding["dataset_binding"]["dataset_id"] == DATASET_ID
    evidence = (
        REPO / "docs/evidence/evaluate_cross_sectional_short_horizon_return_reversal_development_v1"
    )
    summary = json.loads((evidence / "summary.json").read_text(encoding="utf-8"))
    assert summary["development_result"] == "DEVELOPMENT_FAIL"
    assert summary["evaluation_executed"] is True
    assert summary["development_run_count_after"] == 1
    assert summary["holdout_touched"] is False
    claim = json.loads((evidence / "run_slot_claim.json").read_text(encoding="utf-8"))
    assert claim["run_slot_consumed"] is True


def test_dry_validate_does_not_consume_slot() -> None:
    before = read_run_counters(REPO)
    result = dry_validate_evaluate_path_v1(REPO)
    after = read_run_counters(REPO)
    assert before == after
    assert result.runner_started is False
    assert result.evaluation_executed is False
    assert result.executable_path_reached is True


def test_fake_boundary_blocked_when_slot_already_consumed(tmp_path: Path) -> None:
    """After the sole authorized run, a further evaluate path must fail closed."""
    with pytest.raises(GuardError, match="RUN_LIMIT_EXHAUSTED|RETRY_OR_SLOT_REUSE"):
        # Direct guard: repo counters already exhausted.
        assert_retry_forbidden(development_run_count=1, runner_start_count=1)
    # Evidence-dir slot claim also blocks reuse of the canonical output directory.
    evidence = (
        REPO / "docs/evidence/evaluate_cross_sectional_short_horizon_return_reversal_development_v1"
    )
    from src.research.cross_sectional_short_horizon_return_reversal_v1_development_evaluation_v1.guards_v1 import (
        assert_no_slot_reuse,
    )

    with pytest.raises(GuardError, match="RETRY_OR_SLOT_REUSE"):
        assert_no_slot_reuse(evidence)
    csrhr = json.loads(CSRHR.read_text(encoding="utf-8"))
    assert csrhr["status"] == "OPEN_BACKLOG"
    assert csrhr["development_run_count"] == 1
