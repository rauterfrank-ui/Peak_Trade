"""Observation budget: defaults, explicit bounds, fail-closed validation, propagation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_continuous_observation_budget_v1 import (
    ABSOLUTE_MAX_CYCLES_PER_RUN,
    ABSOLUTE_MAX_RUN_DURATION_SECONDS,
    ContinuousObservationBudgetError,
    PRODUCTIVE_DEFAULT_MAX_CYCLES_PER_RUN,
    PRODUCTIVE_DEFAULT_MAX_RUN_DURATION_SECONDS,
    REASON_EXCEEDS_HARD_CAP,
    REASON_NONFINITE_BOUND,
    REASON_UNBOUNDED_OR_INVALID_BOUND,
    resolve_continuous_observation_budget_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    REASON_EXCEEDS_HARD_CAP as ORCH_EXCEEDS,
    RUNTIME_OWNER_GO,
    CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    CurrentProductiveGovernedContinuousCycleOrchestratorError,
    _validate_authorization,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)


def test_default_constants_unchanged() -> None:
    assert PRODUCTIVE_DEFAULT_MAX_CYCLES_PER_RUN == 4
    assert PRODUCTIVE_DEFAULT_MAX_RUN_DURATION_SECONDS == 180.0
    assert ABSOLUTE_MAX_CYCLES_PER_RUN == 12
    assert ABSOLUTE_MAX_RUN_DURATION_SECONDS == 900.0


def test_default_behavior_parity_resolve() -> None:
    resolved = resolve_continuous_observation_budget_v1(
        max_cycles=PRODUCTIVE_DEFAULT_MAX_CYCLES_PER_RUN,
        max_run_duration_seconds=PRODUCTIVE_DEFAULT_MAX_RUN_DURATION_SECONDS,
    )
    assert resolved.effective_max_cycles == 4
    assert resolved.effective_max_run_duration_seconds == 180.0


def test_explicit_12_cycles_900_seconds_accepted() -> None:
    resolved = resolve_continuous_observation_budget_v1(
        max_cycles=12, max_run_duration_seconds=900.0
    )
    assert resolved.effective_max_cycles == 12
    assert resolved.effective_max_run_duration_seconds == 900.0


@pytest.mark.parametrize(
    ("max_cycles", "duration", "reason"),
    [
        (0, 180.0, REASON_UNBOUNDED_OR_INVALID_BOUND),
        (-1, 180.0, REASON_UNBOUNDED_OR_INVALID_BOUND),
        (4, 0.0, REASON_UNBOUNDED_OR_INVALID_BOUND),
        (4, -1.0, REASON_UNBOUNDED_OR_INVALID_BOUND),
        (13, 180.0, REASON_EXCEEDS_HARD_CAP),
        (4, 901.0, REASON_EXCEEDS_HARD_CAP),
        (4, float("nan"), REASON_NONFINITE_BOUND),
        (4, float("inf"), REASON_NONFINITE_BOUND),
    ],
)
def test_invalid_budget_rejected(max_cycles: int, duration: float, reason: str) -> None:
    with pytest.raises(ContinuousObservationBudgetError, match=reason):
        resolve_continuous_observation_budget_v1(
            max_cycles=max_cycles,
            max_run_duration_seconds=duration,
        )


def _canonical_auth(
    **overrides: object,
) -> CurrentProductiveGovernedContinuousCycleRunAuthorizationV1:
    base = dict(
        continuous_owner_go=RUNTIME_OWNER_GO,
        native_id="APR-USDT-SWAP",
        bar="1m",
        expected_cursor_floor=0.0,
        max_cycles_per_run=PRODUCTIVE_DEFAULT_MAX_CYCLES_PER_RUN,
        max_run_duration_seconds=PRODUCTIVE_DEFAULT_MAX_RUN_DURATION_SECONDS,
        wait_interval_seconds=5.0,
        max_wait_for_next_c1_seconds=60.0,
        stall_seconds=60.0,
    )
    base.update(overrides)
    return CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(**base)


def test_orchestrator_accepts_extended_budget() -> None:
    _validate_authorization(_canonical_auth(max_cycles_per_run=12, max_run_duration_seconds=900.0))


def test_orchestrator_rejects_above_absolute_ceiling() -> None:
    with pytest.raises(
        CurrentProductiveGovernedContinuousCycleOrchestratorError,
        match=ORCH_EXCEEDS,
    ):
        _validate_authorization(_canonical_auth(max_cycles_per_run=ABSOLUTE_MAX_CYCLES_PER_RUN + 1))


def test_orchestrator_rejects_nonfinite_duration() -> None:
    auth = _canonical_auth(max_run_duration_seconds=float("nan"))
    with pytest.raises(
        CurrentProductiveGovernedContinuousCycleOrchestratorError,
        match=REASON_UNBOUNDED_OR_INVALID_BOUND,
    ):
        _validate_authorization(auth)


def test_safety_and_trading_pins_unchanged() -> None:
    assert POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"


def test_launcher_cli_defaults_match_productive_policy() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--lane-state-root", type=Path)
    parser.add_argument("--productivity-root", type=Path)
    parser.add_argument("--binding-epoch", default=None)
    parser.add_argument("--wp-branch-evidence-run", action="store_true")
    parser.add_argument("--enable-natural-market-data-capture-v1", action="store_true")
    parser.add_argument(
        "--enable-golden-happy-vector-forensic-observability-v1", action="store_true"
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=PRODUCTIVE_DEFAULT_MAX_CYCLES_PER_RUN,
    )
    parser.add_argument(
        "--max-run-duration-seconds",
        type=float,
        default=PRODUCTIVE_DEFAULT_MAX_RUN_DURATION_SECONDS,
    )
    args = parser.parse_args([])
    assert args.max_cycles == 4
    assert args.max_run_duration_seconds == 180.0


def test_launcher_budget_blocker_json_shape() -> None:
    with pytest.raises(ContinuousObservationBudgetError):
        resolve_continuous_observation_budget_v1(max_cycles=0, max_run_duration_seconds=180.0)

    payload = {
        "status": "FAIL",
        "blocker": REASON_UNBOUNDED_OR_INVALID_BOUND,
        "detail": "MAX_CYCLES",
    }
    assert "MAX_CYCLES" in json.dumps(payload, sort_keys=True)
