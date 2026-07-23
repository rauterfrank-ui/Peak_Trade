"""Contract tests for CS intrabar CLV pressure continuation v1 DEVELOPMENT evaluation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.cross_sectional_intrabar_close_location_pressure_continuation_v1_development_evaluation_v1.binding_v1 import (
    compute_strategy_params_digest,
    load_and_validate_entry_point_binding,
)
from src.research.cross_sectional_intrabar_close_location_pressure_continuation_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    DEFAULT_LOOKBACK_N,
    DEFAULT_REBALANCE_INTERVAL_BARS,
    DEVELOPMENT_RUN_LIMIT,
    FROZEN_MEASUREMENT_CONTRACT_DIGEST,
    HYPOTHESIS_ID,
    SCOPE_ID,
)
from src.research.cross_sectional_intrabar_close_location_pressure_continuation_v1_development_evaluation_v1.guards_v1 import (
    GuardError,
    assert_retry_forbidden,
    read_run_counters,
)
from src.research.cross_sectional_intrabar_close_location_pressure_continuation_v1_hypothesis_preregistration_v1 import (
    load_and_validate_repo_contract,
)
from src.research.cross_sectional_intrabar_close_location_pressure_continuation_research_program_v1 import (
    load_and_validate_repo_program,
)
from src.research.cross_sectional_intrabar_close_location_pressure_continuation_hypothesis_backlog_v1 import (
    load_and_validate_repo_backlog,
)

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = (
    REPO
    / "docs/evidence/evaluate_cross_sectional_intrabar_close_location_pressure_continuation_development_v1"
)
CSRHR = (
    REPO
    / "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
)


def test_frozen_params_and_scope() -> None:
    assert DEFAULT_LOOKBACK_N == 36
    assert DEFAULT_REBALANCE_INTERVAL_BARS == 6
    assert DEVELOPMENT_RUN_LIMIT == 1
    assert DATASET_ID == "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
    assert (
        SCOPE_ID
        == "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1_BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION_V1"
    )
    assert compute_strategy_params_digest() == (
        "4240d4ad99bec9feb2e9f18a6d09d266408f349c401d4283d4553437f0db3216"
    )


def test_slot_consumed_and_retry_forbidden() -> None:
    counters = read_run_counters(REPO)
    assert counters["contract_development_run_count"] == 1
    assert counters["contract_runner_start_count"] == 1
    with pytest.raises(GuardError, match="RUN_LIMIT_EXHAUSTED"):
        assert_retry_forbidden(development_run_count=1, runner_start_count=1)


def test_ssot_validators_post_execution() -> None:
    contract = load_and_validate_repo_contract(REPO)
    assert contract["development_run_count"] == 1
    assert contract["evaluation_authorized"] is False
    program = load_and_validate_repo_program(REPO)
    assert program["development_run_count"] == 1
    backlog = load_and_validate_repo_backlog(REPO)
    assert backlog["development_run_count"] == 1
    binding = load_and_validate_entry_point_binding(REPO)
    assert binding["development_run_count"] == 1
    assert binding["frozen_measurement_contract_digest"] == FROZEN_MEASUREMENT_CONTRACT_DIGEST


def test_evidence_development_fail_and_csrhr_unchanged() -> None:
    summary = json.loads((EVIDENCE / "summary.json").read_text(encoding="utf-8"))
    assert summary["development_result"] == "DEVELOPMENT_FAIL"
    assert summary["evaluation_executed"] is True
    assert summary["development_run_count_after"] == 1
    assert summary["holdout_touched"] is False
    assert summary["economic_gate_open"] is False
    assert summary["live"] is False
    assert summary["orders"] is False
    assert summary["gates"]["all_pass"] is False
    assert summary["hypothesis_id"] == HYPOTHESIS_ID
    csrhr = json.loads(CSRHR.read_text(encoding="utf-8"))
    assert csrhr["status"] == "OPEN_BACKLOG"
    assert csrhr["development_run_count"] == 0


def test_no_second_evaluation_runner_in_evidence_dir() -> None:
    assert (EVIDENCE / "run_slot_claim.json").is_file()
    claim = json.loads((EVIDENCE / "run_slot_claim.json").read_text(encoding="utf-8"))
    assert claim["run_slot_consumed"] is True
    assert claim["development_run_count"] == 1
