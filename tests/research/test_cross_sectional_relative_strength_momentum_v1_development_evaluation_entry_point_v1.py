"""Contract/unit tests for CS RS momentum v1 development-evaluation entry point."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.binding_v1 import (
    EntryPointBindingError,
    assert_dataset_allowed,
    compute_config_digest,
    compute_strategy_params_digest,
    load_and_validate_entry_point_binding,
    reject_holdout_reference,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.constants_v1 import (
    CLI_REL_PATH,
    DATASET_ID,
    ENTRY_POINT_BINDING_REL_PATH,
    EVIDENCE_REL_PATH,
    FROZEN_MEASUREMENT_CONTRACT_DIGEST,
    GOVERNANCE_REL_PATH,
    HOLDOUT_OPAQUE_ID,
    HYPOTHESIS_ID,
    MINIMUM_REBALANCE_OBSERVATIONS,
    OWNER_SURFACE,
    TIME_SEGMENT_COUNT,
    TIME_SEGMENT_DEFINITION_ID,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.entry_point_v1 import (
    run_evaluate_fail_closed,
    run_preflight_only,
    validate_repo_entry_point,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.evidence_schema_v1 import (
    empty_evidence_surface_template,
    validate_evidence_surface_complete,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.guards_v1 import (
    GuardError,
    assert_exactly_one_run_limit,
    assert_holdout_guard,
    assert_retry_forbidden,
    preflight_guards,
    read_run_counters,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.panel_wiring_v1 import (
    wire_selection_intents_to_orchestrator_result_v1,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.rebalance_observations_v1 import (
    collect_valid_evaluable_rebalance_observations,
    count_valid_evaluable_rebalance_observations,
    minimum_rebalance_observations_pass,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.time_segments_v1 import (
    build_canonical_pt1h_bar_starts,
    partition_chronological_equal_duration_quarters_v1,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import SlotSide
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1, PanelBarV1

REPO = Path(__file__).resolve().parents[2]
OWNER_MAP = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
CONTRACT = (
    REPO / "config/research/"
    "cross_sectional_relative_strength_momentum_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
PROGRAM = REPO / "config/research/material_different_cross_sectional_momentum_program_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _closes(start: float, n: int, step: float) -> tuple[float, ...]:
    values = [start]
    for _ in range(n - 1):
        values.append(values[-1] * step)
    return tuple(values)


def _synthetic_panel(n_bars: int = 40) -> list[InstrumentPanelSeriesV1]:
    start = datetime(2022, 6, 1, 4, 0, tzinfo=timezone.utc)
    instruments = {
        "okx:linear_perpetual:ETH-USDT": _closes(100.0, n_bars, 1.01),
        "okx:linear_perpetual:SOL-USDT": _closes(50.0, n_bars, 1.005),
        "okx:linear_perpetual:XRP-USDT": _closes(1.0, n_bars, 0.999),
        "okx:linear_perpetual:ADA-USDT": _closes(2.0, n_bars, 1.002),
        "okx:linear_perpetual:DOGE-USDT": _closes(0.1, n_bars, 0.998),
        "okx:linear_perpetual:LINK-USDT": _closes(10.0, n_bars, 1.003),
    }
    panel: list[InstrumentPanelSeriesV1] = []
    for iid, closes in instruments.items():
        bars = tuple(
            PanelBarV1(
                instrument_id=iid,
                timestamp_utc=(start + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                open=str(closes[i]),
                high=str(closes[i]),
                low=str(closes[i]),
                close=str(closes[i]),
                volume="1.0",
                is_final=True,
            )
            for i in range(n_bars)
        )
        panel.append(
            InstrumentPanelSeriesV1(
                instrument_id=iid,
                native_instrument_id=iid,
                bars=bars,
                series_digest="synthetic_test",
            )
        )
    return panel


def test_owner_registry_and_entry_point_files_bound() -> None:
    owner_map = _load(OWNER_MAP)
    owner = owner_map["allowed_optimization_surfaces"][OWNER_SURFACE]
    prefixes = owner["path_prefixes"]
    assert ENTRY_POINT_BINDING_REL_PATH in prefixes
    assert CLI_REL_PATH in prefixes
    assert EVIDENCE_REL_PATH in prefixes or any(
        p.startswith("docs/evidence/evaluate_cross_sectional_relative_strength_momentum")
        for p in prefixes
    )
    assert (REPO / CLI_REL_PATH).is_file()
    assert (REPO / ENTRY_POINT_BINDING_REL_PATH).is_file()
    assert (REPO / GOVERNANCE_REL_PATH).is_file()
    assert (REPO / EVIDENCE_REL_PATH / "README.md").is_file()
    assert (
        "src/research/cross_sectional_relative_strength_momentum_v1_development_evaluation_v1/"
        in prefixes
    )


def test_deterministic_digests_stable() -> None:
    d1 = compute_config_digest(REPO)
    d2 = compute_config_digest(REPO)
    assert d1 == d2
    assert len(d1) == 64
    p1 = compute_strategy_params_digest()
    p2 = compute_strategy_params_digest(lookback_n=20, rebalance_interval_bars=1)
    assert p1 == p2
    assert p1 != compute_strategy_params_digest(lookback_n=10)
    binding = load_and_validate_entry_point_binding(REPO)
    assert binding["config_digest"] == d1
    assert binding["strategy_params_digest"] == p1
    assert binding["frozen_measurement_contract_digest"] == FROZEN_MEASUREMENT_CONTRACT_DIGEST


def test_dataset_allowlist_and_holdout_rejection() -> None:
    assert_dataset_allowed(DATASET_ID)
    assert_holdout_guard(dataset_id=DATASET_ID)
    with pytest.raises(EntryPointBindingError):
        assert_dataset_allowed(HOLDOUT_OPAQUE_ID)
    with pytest.raises(EntryPointBindingError):
        reject_holdout_reference(HOLDOUT_OPAQUE_ID)
    with pytest.raises(GuardError):
        assert_holdout_guard(dataset_id=DATASET_ID, attempted_holdout_ids=(HOLDOUT_OPAQUE_ID,))


def test_exactly_one_run_and_retry_guards() -> None:
    assert_exactly_one_run_limit(1)
    with pytest.raises(GuardError):
        assert_exactly_one_run_limit(2)
    assert_retry_forbidden(retry_requested=False, development_run_count=0, runner_start_count=0)
    with pytest.raises(GuardError):
        assert_retry_forbidden(retry_requested=True, development_run_count=0, runner_start_count=0)
    with pytest.raises(GuardError):
        assert_retry_forbidden(retry_requested=False, development_run_count=1, runner_start_count=0)
    with pytest.raises(GuardError):
        assert_retry_forbidden(retry_requested=False, development_run_count=0, runner_start_count=1)


def test_quarter_segmentation_remainder_and_denominator() -> None:
    bars = build_canonical_pt1h_bar_starts()
    segments = partition_chronological_equal_duration_quarters_v1(bars)
    assert len(segments) == TIME_SEGMENT_COUNT
    assert sum(s.bar_count for s in segments) == len(bars)
    # Remainder assigned to earliest segments only.
    counts = [s.bar_count for s in segments]
    assert max(counts) - min(counts) <= 1
    assert counts == sorted(counts, reverse=True) or counts[0] >= counts[-1]
    assert TIME_SEGMENT_DEFINITION_ID == "CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1"
    # Tiny synthetic remainder case
    tiny = [bars[0] + timedelta(hours=i) for i in range(10)]
    tiny_segments = partition_chronological_equal_duration_quarters_v1(tiny)
    assert [s.bar_count for s in tiny_segments] == [3, 3, 2, 2]


def test_rebalance_observation_semantics_not_trades_or_bars() -> None:
    closes = {
        "okx:linear_perpetual:ETH-USDT": _closes(100.0, 40, 1.01),
        "okx:linear_perpetual:SOL-USDT": _closes(50.0, 40, 1.005),
        "okx:linear_perpetual:XRP-USDT": _closes(1.0, 40, 0.999),
        "okx:linear_perpetual:ADA-USDT": _closes(2.0, 40, 1.002),
        "okx:linear_perpetual:DOGE-USDT": _closes(0.1, 40, 0.998),
        "okx:linear_perpetual:LINK-USDT": _closes(10.0, 40, 1.003),
    }
    timestamps = [
        (datetime(2022, 6, 1, 4, tzinfo=timezone.utc) + timedelta(hours=i)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        for i in range(40)
    ]
    observations = collect_valid_evaluable_rebalance_observations(
        closes, timestamps, lookback_n=10, rebalance_interval_bars=1
    )
    # Observation count equals rebalance epochs, not bar count inventing trades.
    assert len(observations) == 40
    valid = count_valid_evaluable_rebalance_observations(observations)
    assert valid >= 1
    assert valid <= len(observations)
    assert MINIMUM_REBALANCE_OBSERVATIONS == 30
    assert minimum_rebalance_observations_pass(30) is True
    assert minimum_rebalance_observations_pass(29) is False
    # Insufficient universe -> non-evaluable, not counted as PASS sample.
    sparse = {"okx:linear_perpetual:ETH-USDT": _closes(100.0, 40, 1.01)}
    sparse_obs = collect_valid_evaluable_rebalance_observations(
        sparse, timestamps, lookback_n=10, min_eligible_members_for_rank=5
    )
    assert count_valid_evaluable_rebalance_observations(sparse_obs) == 0


def test_evidence_surface_complete() -> None:
    surface = empty_evidence_surface_template(
        config_digest="abc",
        strategy_params_digest="def",
        dataset_id=DATASET_ID,
    )
    report = validate_evidence_surface_complete(surface)
    assert report["valid"] is True


def test_panel_wiring_reuses_orchestrator_shape_without_runtime() -> None:
    result = wire_selection_intents_to_orchestrator_result_v1(_synthetic_panel())
    assert result.runtime_effect == "NONE"
    assert result.authority_effect == "NONE"
    assert result.order_effect == "NONE"
    assert result.score_formula_version == "raw_trailing_log_return_fixed_lookback_v1"
    assert len(result.epochs) == 40
    assert result.final_slot_side in {SlotSide.FLAT, SlotSide.LONG, SlotSide.SHORT}


def test_preflight_and_evaluate_fail_closed_no_run_consumption() -> None:
    before = read_run_counters(REPO)
    assert before["contract_development_run_count"] == 0
    assert before["contract_runner_start_count"] == 0
    preflight = run_preflight_only(REPO)
    assert preflight["runner_started"] is False
    assert preflight["evaluation_executed"] is False
    assert preflight["holdout_accessed"] is False
    assert preflight["time_segment_definition_id"] == TIME_SEGMENT_DEFINITION_ID
    with pytest.raises(GuardError, match="EVALUATION_UNAUTHORIZED"):
        run_evaluate_fail_closed(
            REPO,
            authorize_token=HYPOTHESIS_ID,
            output_dir=REPO / EVIDENCE_REL_PATH,
        )
    after = read_run_counters(REPO)
    assert after == before
    report = validate_repo_entry_point(REPO)
    assert report["valid"] is True
    assert report["runner_started"] is False
    guards = preflight_guards(REPO)
    assert guards["exactly_one_run_guard_present"] is True
    assert guards["retry_guard_present"] is True
    assert guards["holdout_guard_present"] is True
    contract = _load(CONTRACT)
    program = _load(PROGRAM)
    assert contract["development_run_count"] == 0
    assert contract["runner_start_count"] == 0
    assert program["development_run_count"] == 0
    assert program["runner_start_count"] == 0
    assert contract["evaluation_authorized"] is False
    assert contract["development_evaluation_authorized"] is False
    runtime = contract["runtime_policy"]
    assert runtime["live_authorized"] is False
    assert runtime["orders_allowed"] is False
    assert runtime["shadow_activated"] is False
    assert runtime["testnet_activated"] is False
    assert runtime["scheduler_authorized"] is False
