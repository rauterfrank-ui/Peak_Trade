"""Executable-path / panel-boundary tests for VEP v1 (no real panel or evaluation run)."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1, PanelBarV1
from src.research.volatility_expansion_persistence_v1_development_evaluation_v1.authorization_v1 import (
    AuthorizationDecisionV1,
    resolve_authorization_decision_v1,
)
from src.research.volatility_expansion_persistence_v1_development_evaluation_v1.binding_v1 import (
    compute_config_digest,
    load_and_validate_entry_point_binding,
)
from src.research.volatility_expansion_persistence_v1_development_evaluation_v1.constants_v1 import (
    BASELINE_ID,
    DATASET_ID,
    HYPOTHESIS_ID,
    MIN_EXECUTED_TREATMENT_TRADES,
    PRODUCTIVE_PNL_EVALUATOR_REL_PATH,
    STRATEGY_IDENTITY,
    TIME_SEGMENT_DEFINITION_ID,
)
from src.research.volatility_expansion_persistence_v1_development_evaluation_v1.entry_point_v1 import (
    run_evaluate_fail_closed,
    run_preflight_only,
)
from src.research.volatility_expansion_persistence_v1_development_evaluation_v1.evaluate_path_v1 import (
    dry_validate_evaluate_path_v1,
    run_authorized_development_evaluation_v1,
)
from src.research.volatility_expansion_persistence_v1_development_evaluation_v1.execution_boundary_v1 import (
    BacktestMetricsBundleV1,
    FakeExecutionBoundaryV1,
    PanelLoadResultV1,
)
from src.research.volatility_expansion_persistence_v1_development_evaluation_v1.guards_v1 import (
    GuardError,
    read_run_counters,
)
from src.research.volatility_expansion_persistence_v1_development_evaluation_v1.panel_wiring_v1 import (
    ArmEventSeriesV1,
    TreatmentBaselineWiringHandoffV1,
    wire_treatment_and_baseline_panel_events_v1,
)
from src.research.volatility_expansion_persistence_v1_development_evaluation_v1.time_segments_v1 import (
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


def _fake_handoff(panel: PanelLoadResultV1) -> TreatmentBaselineWiringHandoffV1:
    n = len(panel.timestamps_utc)
    mask = tuple(True for _ in range(n))
    sides = tuple("LONG" for _ in range(n))
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
    return TreatmentBaselineWiringHandoffV1(
        treatment=(arm,),
        baseline=(baseline,),
        shared_channel_core_bound=True,
        time_segment_definition_id=TIME_SEGMENT_DEFINITION_ID,
        baseline_id=BASELINE_ID,
        strategy_identity=STRATEGY_IDENTITY,
        timestamps_utc=panel.timestamps_utc,
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
        "src.research.volatility_expansion_persistence_v1_development_evaluation_v1"
    )
    importlib.reload(mod)
    pkg = REPO / "src/research/volatility_expansion_persistence_v1_development_evaluation_v1"
    assert (pkg / "panel_loader_v1.py").is_file()
    assert (pkg / "panel_wiring_v1.py").is_file()
    assert (pkg / "execution_boundary_v1.py").is_file()
    assert (pkg / "admission_gates_v1.py").is_file()
    assert (pkg / "evidence_materialization_v1.py").is_file()
    after = read_run_counters(REPO)
    assert after == before
    assert before["contract_development_run_count"] == 1
    assert before["contract_runner_start_count"] == 1


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


def test_unauthorized_blocks_before_runner_start(tmp_path: Path) -> None:
    before = read_run_counters(REPO)
    fake = _fake_boundary()
    result = run_authorized_development_evaluation_v1(
        REPO,
        authorize_token="WRONG_TOKEN",
        output_dir=tmp_path,
        execution_boundary=fake,
        persist_evidence=False,
    )
    assert result.status == "FAIL_CLOSED"
    assert result.runner_started is False
    assert result.evaluation_executed is False
    assert result.development_dataset_loaded is False
    assert fake.load_calls == 0
    assert fake.backtest_calls == 0
    with pytest.raises(GuardError, match="EVALUATION_UNAUTHORIZED"):
        run_evaluate_fail_closed(REPO, authorize_token="WRONG_TOKEN", output_dir=tmp_path)
    assert read_run_counters(REPO) == before


def test_fake_boundary_rejects_holdout_dataset_digest_time_segment_and_config_digest() -> None:
    fake = _fake_boundary()
    with pytest.raises(ValueError, match="HOLDOUT_PATH_REJECTED"):
        fake.load_development_panel(
            repo_root=REPO,
            archive_root=Path("/tmp/offline_economic_reevaluation_sealed_holdout"),
        )
    with pytest.raises(ValueError, match="DATASET_ID_NOT_BOUND"):
        fake.load_development_panel(
            repo_root=REPO,
            archive_root=None,
            expected_dataset_id="wrong_dataset",
        )
    with pytest.raises(ValueError, match="DATASET_DIGEST_DRIFT"):
        fake.load_development_panel(
            repo_root=REPO,
            archive_root=None,
            expected_dataset_digest="not_the_digest",
        )
    with pytest.raises(ValueError, match="TIME_SEGMENT_BINDING_MISMATCH"):
        fake.load_development_panel(
            repo_root=REPO,
            archive_root=None,
            time_segment_definition_id="WRONG_SEGMENTS",
        )
    with pytest.raises(ValueError, match="CONFIG_DIGEST_MISMATCH"):
        fake.load_development_panel(
            repo_root=REPO,
            archive_root=None,
            expected_config_digest="not_the_config_digest",
        )


def test_empty_panel_materialization_fail_closed() -> None:
    fake = _fake_boundary(empty_panel=True)
    with pytest.raises(ValueError, match="EMPTY_PANEL_MATERIALIZATION"):
        fake.load_development_panel(repo_root=REPO, archive_root=None)
    with pytest.raises(ValueError, match="EMPTY_PANEL_SERIES"):
        wire_treatment_and_baseline_panel_events_v1(())


def test_authorized_reaches_evaluator_handoff_via_fake_boundary_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = read_run_counters(REPO)
    assert before["contract_development_run_count"] == 1
    assert before["contract_runner_start_count"] == 1
    monkeypatch.setattr(
        "src.research.volatility_expansion_persistence_v1_development_evaluation_v1.evaluate_path_v1.read_run_counters",
        lambda _repo: {
            "contract_development_run_count": 0,
            "contract_runner_start_count": 0,
            "program_development_run_count": 0,
            "program_runner_start_count": 0,
        },
    )
    fake = _fake_boundary()
    result = run_authorized_development_evaluation_v1(
        REPO,
        authorize_token=HYPOTHESIS_ID,
        output_dir=tmp_path,
        execution_boundary=fake,
        authorization_decision=_authorized_decision(),
        persist_evidence=True,
        counter_mutator=None,
    )
    assert result.status == "EVALUATION_COMPLETE"
    assert result.runner_started is True
    assert result.evaluation_executed is True
    assert result.development_dataset_loaded is True
    assert result.holdout_accessed is False
    assert fake.load_calls == 1
    assert fake.backtest_calls == 2
    assert fake.wire_calls >= 2
    assert (tmp_path / "summary.json").is_file()
    assert (tmp_path / "registry.json").is_file()
    assert (tmp_path / "run_slot_claim.json").is_file()
    # Durable repo counters must remain untouched (no counter_mutator).
    assert read_run_counters(REPO) == before


def test_boundary_error_blocks_evaluation_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "src.research.volatility_expansion_persistence_v1_development_evaluation_v1.evaluate_path_v1.read_run_counters",
        lambda _repo: {
            "contract_development_run_count": 0,
            "contract_runner_start_count": 0,
            "program_development_run_count": 0,
            "program_runner_start_count": 0,
        },
    )
    before = {
        "contract_development_run_count": 0,
        "contract_runner_start_count": 0,
        "program_development_run_count": 0,
        "program_runner_start_count": 0,
    }
    fake = _fake_boundary()

    def _boom(**_kwargs):
        raise ValueError("DATASET_DIGEST_DRIFT")

    fake.load_development_panel = _boom  # type: ignore[method-assign]
    with pytest.raises(ValueError, match="DATASET_DIGEST_DRIFT"):
        run_authorized_development_evaluation_v1(
            REPO,
            authorize_token=HYPOTHESIS_ID,
            output_dir=tmp_path,
            execution_boundary=fake,
            authorization_decision=_authorized_decision(),
            persist_evidence=False,
        )
    assert fake.backtest_calls == 0
    assert not (tmp_path / "summary.json").exists()
    assert before["contract_development_run_count"] == 0


def test_dry_validate_and_preflight_leave_counters_unchanged() -> None:
    before = read_run_counters(REPO)
    dry = dry_validate_evaluate_path_v1(REPO)
    assert dry.status == "DRY_VALIDATE_PASS_EXECUTABLE_PATH_PRESENT"
    assert dry.runner_started is False
    assert dry.evaluation_executed is False
    assert dry.development_dataset_loaded is False
    preflight = run_preflight_only(REPO)
    assert preflight["runner_started"] is False
    assert preflight["evaluation_executed"] is False
    binding = load_and_validate_entry_point_binding(REPO)
    assert binding["config_digest"] == compute_config_digest(REPO)
    assert binding["time_segment_definition_id"] == TIME_SEGMENT_DEFINITION_ID
    assert binding["dataset_binding"]["dataset_id"] == DATASET_ID
    assert read_run_counters(REPO) == before


def test_productive_pnl_evaluator_reused_no_second_truth() -> None:
    from src.research.volatility_compression_breakout_v1_development_evaluation_v1.productive_exit_pnl_evaluator_v1 import (
        productive_exit_pnl_evaluator_is_bound,
    )

    assert productive_exit_pnl_evaluator_is_bound() is True
    assert (REPO / PRODUCTIVE_PNL_EVALUATOR_REL_PATH).is_file()
    # No VEP-local PnL evaluator module may exist.
    vep_pkg = REPO / "src/research/volatility_expansion_persistence_v1_development_evaluation_v1"
    assert not (vep_pkg / "productive_exit_pnl_evaluator_v1.py").is_file()


def test_run_counters_consumed_slot_present() -> None:
    counters = read_run_counters(REPO)
    assert counters["contract_development_run_count"] == 1
    assert counters["contract_runner_start_count"] == 1
    assert counters["program_development_run_count"] == 1
    assert counters["program_runner_start_count"] == 1
    evidence = REPO / "docs/evidence/evaluate_volatility_expansion_persistence_development_v1"
    assert (evidence / "run_slot_claim.json").is_file()
    assert (evidence / "summary.json").is_file()
