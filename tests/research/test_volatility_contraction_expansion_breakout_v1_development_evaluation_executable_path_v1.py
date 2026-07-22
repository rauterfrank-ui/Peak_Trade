"""Executable-path / panel-boundary tests for VCEB v1 (no real panel or evaluation run)."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1, PanelBarV1
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.panel_wiring_v1 import (
    ArmEventSeriesV1,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.authorization_v1 import (
    AuthorizationDecisionV1,
    resolve_authorization_decision_v1,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.binding_v1 import (
    compute_config_digest,
    load_and_validate_entry_point_binding,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.constants_v1 import (
    BASELINE_ID,
    DATASET_ID,
    HYPOTHESIS_ID,
    MIN_EXECUTED_TREATMENT_TRADES,
    PRODUCTIVE_PNL_EVALUATOR_REL_PATH,
    STRATEGY_IDENTITY,
    TIME_SEGMENT_DEFINITION_ID,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.entry_point_v1 import (
    run_evaluate_fail_closed,
    run_preflight_only,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.evaluate_path_v1 import (
    dry_validate_evaluate_path_v1,
    run_authorized_development_evaluation_v1,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.execution_boundary_v1 import (
    BacktestMetricsBundleV1,
    FakeExecutionBoundaryV1,
    PanelLoadResultV1,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.guards_v1 import (
    GuardError,
    read_run_counters,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.panel_wiring_v1 import (
    StrategyEmittedRoundtripHandoffV1,
    VcebTreatmentBaselineWiringHandoffV1,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.time_segments_v1 import (
    partition_chronological_equal_duration_quarters_v1,
)

REPO = Path(__file__).resolve().parents[2]


def _authorized_decision() -> AuthorizationDecisionV1:
    return AuthorizationDecisionV1(
        authorized=True,
        authorize_token_valid=True,
        repo_development_evaluation_authorized=True,
        program_development_evaluation_authorized=True,
        entry_point_binding_authorized=True,
        reason_codes=(),
    )


def _synthetic_panel(*, empty: bool = False) -> PanelLoadResultV1:
    segments = partition_chronological_equal_duration_quarters_v1()
    timestamps = tuple(seg.start_inclusive for seg in segments)
    if empty:
        return PanelLoadResultV1(
            dataset_id=DATASET_ID,
            dataset_digest="fake_dataset_digest",
            panel_series=(),
            timestamps_utc=(),
            instrument_count=0,
            holdout_accessed=False,
        )
    bars = tuple(
        PanelBarV1(
            instrument_id="INST_A",
            timestamp_utc=ts,
            open="100",
            high="101",
            low="99",
            close="100.5",
            volume="1",
            is_final=True,
        )
        for ts in timestamps
    )
    series = InstrumentPanelSeriesV1(
        instrument_id="INST_A",
        native_instrument_id="INST_A",
        bars=bars,
        series_digest="fake_dataset_digest",
    )
    return PanelLoadResultV1(
        dataset_id=DATASET_ID,
        dataset_digest="fake_dataset_digest",
        panel_series=(series,),
        timestamps_utc=timestamps,
        instrument_count=1,
        holdout_accessed=False,
    )


def _fake_handoff(panel: PanelLoadResultV1) -> VcebTreatmentBaselineWiringHandoffV1:
    n = len(panel.timestamps_utc)
    mask = tuple(i == 0 for i in range(n))
    sides = tuple("LONG" if i == 0 else "NONE" for i in range(n))
    arm = ArmEventSeriesV1(
        arm_id="TREATMENT",
        instrument_id="INST_A",
        timestamps_utc=panel.timestamps_utc,
        entry_sides=sides,
        entry_event_mask=mask,
    )
    baseline = ArmEventSeriesV1(
        arm_id="BASELINE",
        instrument_id="INST_A",
        timestamps_utc=panel.timestamps_utc,
        entry_sides=sides,
        entry_event_mask=mask,
    )
    exit_i = min(2, n - 1) if n > 1 else 0
    roundtrips = (
        StrategyEmittedRoundtripHandoffV1(
            instrument_id="INST_A",
            side="LONG",
            signal_index=0,
            fill_index=1 if n > 1 else 0,
            exit_index=exit_i,
            entry_price=100.0,
            exit_price=100.5,
            exit_reason="TIME_EXIT",
            stop_price_at_entry=98.5,
        ),
    )
    return VcebTreatmentBaselineWiringHandoffV1(
        treatment=(arm,),
        baseline=(baseline,),
        treatment_strategy_roundtrips=roundtrips,
        shared_channel_core_bound=True,
        time_segment_definition_id=TIME_SEGMENT_DEFINITION_ID,
        baseline_id=BASELINE_ID,
        strategy_identity=STRATEGY_IDENTITY,
        timestamps_utc=panel.timestamps_utc,
        strategy_emitted_exits_bound=True,
        evaluator_reconstruction_forbidden=True,
    )


def _fake_metrics(*, net_pf: float = 1.5, baseline_net_pf: float = 1.1) -> BacktestMetricsBundleV1:
    return BacktestMetricsBundleV1(
        gross_return=0.1,
        net_return=0.08,
        gross_profit_factor=1.6,
        net_profit_factor=net_pf,
        gross_pnl=100.0,
        net_expectancy=0.01,
        sharpe=1.0,
        max_drawdown=0.1,
        trade_count=max(35, MIN_EXECUTED_TREATMENT_TRADES),
        evaluable_treatment_breakout_events=60,
        baseline_net_profit_factor=baseline_net_pf,
        baseline_gross_profit_factor=1.2,
        baseline_trade_count=40,
        cost_multiplier=1.0,
        extras={
            "productive_exit_pnl_evaluator_bound": True,
            "strategy_emitted_exits_used_for_treatment": True,
            "evaluator_reconstruction_used_for_treatment": False,
            "long_trade_count": 20,
            "short_trade_count": 15,
            "baseline_net_return": 0.05,
            "exit_reason_attribution": {"TIME_EXIT": 35},
        },
    )


def _fake_boundary(*, empty_panel: bool = False) -> FakeExecutionBoundaryV1:
    panel = _synthetic_panel(empty=empty_panel)
    return FakeExecutionBoundaryV1(
        panel=panel,
        canonical_metrics=_fake_metrics(),
        stress_metrics=_fake_metrics(net_pf=1.1, baseline_net_pf=1.0),
        wiring_handoff=None if empty_panel else _fake_handoff(panel),
        bound_config_digest=compute_config_digest(REPO),
    )


def test_import_safe_and_panel_modules_present() -> None:
    before = read_run_counters(REPO)
    mod = importlib.import_module(
        "src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1"
    )
    importlib.reload(mod)
    pkg = (
        REPO / "src/research/volatility_contraction_expansion_breakout_v1_development_evaluation_v1"
    )
    assert (pkg / "panel_loader_v1.py").is_file()
    assert (pkg / "panel_wiring_v1.py").is_file()
    assert (pkg / "execution_boundary_v1.py").is_file()
    assert (pkg / "admission_gates_v1.py").is_file()
    assert (pkg / "evidence_materialization_v1.py").is_file()
    after = read_run_counters(REPO)
    assert after == before
    assert before["contract_development_run_count"] == 0
    assert before["contract_runner_start_count"] == 0


def test_development_dataset_id_bound() -> None:
    assert DATASET_ID == ("pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1")
    binding = load_and_validate_entry_point_binding(REPO)
    assert binding["dataset_binding"]["dataset_id"] == DATASET_ID
    assert binding["baseline_id"] == BASELINE_ID
    assert binding["time_segment_definition_id"] == TIME_SEGMENT_DEFINITION_ID
    assert binding["productive_exit_pnl_evaluator_ref"] == PRODUCTIVE_PNL_EVALUATOR_REL_PATH
    assert binding["productive_pnl_evaluator_duplicated"] is False


def test_repo_authorization_authorized_on_head() -> None:
    decision = resolve_authorization_decision_v1(REPO, authorize_token=HYPOTHESIS_ID)
    assert decision.authorized is True
    assert decision.reason_codes == ()


def test_dry_validate_no_runner_no_counter_mutation() -> None:
    before = read_run_counters(REPO)
    result = dry_validate_evaluate_path_v1(REPO)
    assert result.status == "DRY_VALIDATE_PASS_EXECUTABLE_PATH_PRESENT"
    assert result.runner_started is False
    assert result.evaluation_executed is False
    assert result.development_dataset_loaded is False
    after = read_run_counters(REPO)
    assert after == before


def test_fake_boundary_evaluate_writes_slot_claim_then_blocks_reuse(tmp_path: Path) -> None:
    before = read_run_counters(REPO)
    assert before["contract_development_run_count"] == 0
    out = tmp_path / "evidence"
    result = run_authorized_development_evaluation_v1(
        REPO,
        authorize_token=HYPOTHESIS_ID,
        output_dir=out,
        execution_boundary=_fake_boundary(),
        authorization_decision=_authorized_decision(),
        persist_evidence=True,
    )
    assert result.evaluation_executed is True
    assert result.runner_started is True
    assert (out / "run_slot_claim.json").is_file()
    assert (out / "summary.json").is_file()
    # Repo counters remain zero until a separate productive execution GO mutates them.
    assert read_run_counters(REPO) == before
    with pytest.raises(GuardError, match="RETRY_OR_SLOT_REUSE_REJECTED"):
        run_authorized_development_evaluation_v1(
            REPO,
            authorize_token=HYPOTHESIS_ID,
            output_dir=out,
            execution_boundary=_fake_boundary(),
            authorization_decision=_authorized_decision(),
            persist_evidence=True,
        )


def test_empty_panel_fail_closed_no_slot_claim(tmp_path: Path) -> None:
    out = tmp_path / "evidence_empty"
    with pytest.raises((GuardError, ValueError)):
        run_authorized_development_evaluation_v1(
            REPO,
            authorize_token=HYPOTHESIS_ID,
            output_dir=out,
            execution_boundary=_fake_boundary(empty_panel=True),
            authorization_decision=_authorized_decision(),
            persist_evidence=True,
        )
    assert not (out / "run_slot_claim.json").is_file()
    assert read_run_counters(REPO)["contract_development_run_count"] == 0


def test_preflight_still_safe_with_executable_path() -> None:
    before = read_run_counters(REPO)
    report = run_preflight_only(REPO)
    assert report["executable_evaluate_path_present"] is True
    assert report["runner_started"] is False
    assert report["evaluation_executed"] is False
    assert read_run_counters(REPO) == before


def test_unauthorized_evaluate_via_entry_point() -> None:
    before = read_run_counters(REPO)
    with pytest.raises(GuardError, match="EVALUATION_UNAUTHORIZED"):
        run_evaluate_fail_closed(
            REPO,
            authorize_token="BAD",
            output_dir=REPO
            / "docs/evidence/evaluate_volatility_contraction_expansion_breakout_development_v1",
        )
    assert read_run_counters(REPO) == before
