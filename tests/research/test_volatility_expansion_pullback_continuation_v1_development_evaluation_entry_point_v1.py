"""Entry-point binding / preflight tests for VEPC v1 (no evaluation execution)."""

from __future__ import annotations

from pathlib import Path

from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.binding_v1 import (
    load_and_validate_entry_point_binding,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    PRODUCTIVE_PNL_EVALUATOR_REL_PATH,
    STRATEGY_IDENTITY,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.entry_point_v1 import (
    run_dry_validate,
    run_preflight_only,
    validate_repo_entry_point,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.guards_v1 import (
    read_run_counters,
)

REPO = Path(__file__).resolve().parents[2]


def test_entry_point_productively_bound_slot_unused() -> None:
    binding = load_and_validate_entry_point_binding(REPO)
    assert binding["strategy_identity"] == STRATEGY_IDENTITY
    assert binding["dataset_binding"]["dataset_id"] == DATASET_ID
    assert binding["dataset_binding"]["dataset_class"] == "DEVELOPMENT_ONLY"
    assert binding["holdout_forbidden"] is True
    assert binding["development_run_count"] == 0
    assert binding["runner_start_count"] == 0
    assert binding["development_evaluation_executed"] is False
    assert binding["productive_pnl_evaluator_duplicated"] is False
    assert (REPO / PRODUCTIVE_PNL_EVALUATOR_REL_PATH).is_file()
    assert binding["status"] == "EXECUTABLE_EVALUATE_PATH_PRESENT_EVALUATION_UNAUTHORIZED"


def test_preflight_dry_validate_do_not_consume_slot() -> None:
    before = read_run_counters(REPO)
    pre = run_preflight_only(REPO)
    dry = run_dry_validate(REPO)
    after = read_run_counters(REPO)
    assert before == after
    assert pre["runner_started"] is False
    assert dry["runner_started"] is False
    assert dry["evaluation_executed"] is False
    report = validate_repo_entry_point(REPO)
    assert report["valid"] is True
    assert report["evaluation_executed"] is False
    assert report["run_counters"]["contract_development_run_count"] == 0
