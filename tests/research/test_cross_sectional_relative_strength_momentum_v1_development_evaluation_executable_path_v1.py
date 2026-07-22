"""Tests for executable CS RS momentum v1 development-evaluation path (no real run)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.authorization_v1 import (
    authorization_decision_from_mapping,
    resolve_authorization_decision_v1,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.binding_v1 import (
    compute_config_digest,
    compute_strategy_params_digest,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    DEVELOPMENT_RUN_LIMIT,
    HOLDOUT_OPAQUE_ID,
    HYPOTHESIS_ID,
    MINIMUM_REBALANCE_OBSERVATIONS,
    TIME_SEGMENT_DEFINITION_ID,
    TIME_SEGMENT_ROBUSTNESS_PASS_RATIO,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.entry_point_v1 import (
    run_dry_validate,
    run_evaluate_fail_closed,
    run_preflight_only,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.evaluate_path_v1 import (
    dry_validate_evaluate_path_v1,
    run_authorized_development_evaluation_v1,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.evidence_materialization_v1 import (
    build_registry_metadata_v1,
    validate_evidence_and_registry_contracts_v1,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.evidence_schema_v1 import (
    empty_evidence_surface_template,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.execution_boundary_v1 import (
    BacktestMetricsBundleV1,
    FakeExecutionBoundaryV1,
    PanelLoadResultV1,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.guards_v1 import (
    GuardError,
    assert_exactly_one_run_limit,
    assert_retry_forbidden,
    read_run_counters,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.time_segments_v1 import (
    partition_chronological_equal_duration_quarters_v1,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1, PanelBarV1

REPO = Path(__file__).resolve().parents[2]


def _closes(start: float, n: int, step: float) -> tuple[float, ...]:
    values = [start]
    for _ in range(n - 1):
        values.append(values[-1] * step)
    return tuple(values)


def _fake_metrics(*, net_pf: float = 1.5, gross_pf: float = 1.8) -> BacktestMetricsBundleV1:
    return BacktestMetricsBundleV1(
        gross_return=0.12,
        net_return=0.08,
        gross_profit_factor=gross_pf,
        net_profit_factor=net_pf,
        gross_pnl=100.0,
        net_expectancy=0.01,
        sharpe=1.0,
        max_drawdown=-0.05,
        turnover=10.0,
        fees=1.0,
        slippage=0.5,
        total_cost_drag=1.5,
        trade_count=60,
        worst1_abs_net_share=0.05,
        cost_multiplier=1.0,
    )


def _panel_spanning_quarters(n_per_segment: int = 40) -> PanelLoadResultV1:
    segments = partition_chronological_equal_duration_quarters_v1()
    timestamps: list[str] = []
    for seg in segments:
        start = datetime.fromisoformat(seg.start_inclusive.replace("Z", "+00:00"))
        for i in range(n_per_segment):
            timestamps.append((start + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    n_bars = len(timestamps)
    instruments = {
        "okx:linear_perpetual:ETH-USDT": _closes(100.0, n_bars, 1.01),
        "okx:linear_perpetual:SOL-USDT": _closes(50.0, n_bars, 1.005),
        "okx:linear_perpetual:XRP-USDT": _closes(1.0, n_bars, 0.999),
        "okx:linear_perpetual:ADA-USDT": _closes(2.0, n_bars, 1.002),
        "okx:linear_perpetual:DOGE-USDT": _closes(0.1, n_bars, 0.998),
        "okx:linear_perpetual:LINK-USDT": _closes(10.0, n_bars, 1.003),
    }
    series: list[InstrumentPanelSeriesV1] = []
    for iid, closes in instruments.items():
        bars = tuple(
            PanelBarV1(
                instrument_id=iid,
                timestamp_utc=timestamps[i],
                open=str(closes[i]),
                high=str(closes[i]),
                low=str(closes[i]),
                close=str(closes[i]),
                volume="1.0",
                is_final=True,
            )
            for i in range(n_bars)
        )
        series.append(
            InstrumentPanelSeriesV1(
                instrument_id=iid,
                native_instrument_id=iid,
                bars=bars,
                series_digest="fake_test_panel",
            )
        )
    return PanelLoadResultV1(
        dataset_id=DATASET_ID,
        dataset_digest="fake_dataset_digest",
        panel_series=tuple(series),
        timestamps_utc=tuple(timestamps),
        instrument_count=len(series),
        holdout_accessed=False,
    )


def _authorized_decision():
    return authorization_decision_from_mapping(
        {
            "authorized": True,
            "authorize_token_valid": True,
            "repo_development_evaluation_authorized": True,
            "program_development_evaluation_authorized": True,
            "entry_point_binding_authorized": True,
            "reason_codes": (),
        }
    )


def test_repo_authorization_fail_closed_on_head() -> None:
    decision = resolve_authorization_decision_v1(REPO, authorize_token=HYPOTHESIS_ID)
    assert decision.authorized is False
    assert decision.authorize_token_valid is True
    assert "CONTRACT_DEVELOPMENT_EVALUATION_AUTHORIZED_FALSE" in decision.reason_codes


def test_unauthorized_blocks_before_runner_start(tmp_path: Path) -> None:
    before = read_run_counters(REPO)
    fake = FakeExecutionBoundaryV1(
        panel=_panel_spanning_quarters(),
        canonical_metrics=_fake_metrics(),
        stress_metrics=_fake_metrics(net_pf=1.1),
    )
    result = run_authorized_development_evaluation_v1(
        REPO,
        authorize_token=HYPOTHESIS_ID,
        output_dir=tmp_path,
        execution_boundary=fake,
        persist_evidence=False,
    )
    assert result.status == "FAIL_CLOSED"
    assert result.runner_started is False
    assert result.evaluation_executed is False
    assert result.executable_path_reached is False
    assert fake.load_calls == 0
    assert fake.backtest_calls == 0
    assert read_run_counters(REPO) == before
    with pytest.raises(GuardError, match="EVALUATION_UNAUTHORIZED"):
        run_evaluate_fail_closed(
            REPO,
            authorize_token=HYPOTHESIS_ID,
            output_dir=tmp_path,
        )
    assert read_run_counters(REPO) == before


def test_authorized_reaches_executable_path_via_fake_boundary_only(tmp_path: Path) -> None:
    before = read_run_counters(REPO)
    fake = FakeExecutionBoundaryV1(
        panel=_panel_spanning_quarters(),
        canonical_metrics=_fake_metrics(),
        stress_metrics=_fake_metrics(net_pf=1.1),
    )
    result = run_authorized_development_evaluation_v1(
        REPO,
        authorize_token=HYPOTHESIS_ID,
        output_dir=tmp_path,
        execution_boundary=fake,
        authorization_decision=_authorized_decision(),
        persist_evidence=True,
    )
    assert result.status == "EVALUATION_COMPLETE"
    assert result.executable_path_reached is True
    assert result.runner_started is True
    assert result.evaluation_executed is True
    assert result.holdout_accessed is False
    assert fake.load_calls == 1
    assert fake.backtest_calls == 2  # canonical + 1.5x stress
    assert result.evidence_surface is not None
    assert result.registry is not None
    assert result.gates is not None
    assert (tmp_path / "summary.json").is_file()
    assert (tmp_path / "registry.json").is_file()
    assert (tmp_path / "run_slot_claim.json").is_file()
    # Repo counters unchanged without counter_mutator (implementation-only tests).
    assert read_run_counters(REPO) == before


def test_run_limit_exactly_one_and_second_start_fail_closed(tmp_path: Path, monkeypatch) -> None:
    assert DEVELOPMENT_RUN_LIMIT == 1
    assert_exactly_one_run_limit(1)
    with pytest.raises(GuardError):
        assert_exactly_one_run_limit(2)
    assert_retry_forbidden(retry_requested=False, development_run_count=0, runner_start_count=0)
    with pytest.raises(GuardError, match="RUN_LIMIT_EXHAUSTED"):
        assert_retry_forbidden(retry_requested=False, development_run_count=1, runner_start_count=0)
    with pytest.raises(GuardError, match="RUNNER_START_LIMIT_EXHAUSTED"):
        assert_retry_forbidden(retry_requested=False, development_run_count=0, runner_start_count=1)

    fake = FakeExecutionBoundaryV1(
        panel=_panel_spanning_quarters(),
        canonical_metrics=_fake_metrics(),
        stress_metrics=_fake_metrics(net_pf=1.1),
    )
    first = run_authorized_development_evaluation_v1(
        REPO,
        authorize_token=HYPOTHESIS_ID,
        output_dir=tmp_path,
        execution_boundary=fake,
        authorization_decision=_authorized_decision(),
        persist_evidence=True,
    )
    assert first.status == "EVALUATION_COMPLETE"
    # Slot reuse: second start against same evidence dir fails before boundary.
    fake2 = FakeExecutionBoundaryV1(
        panel=_panel_spanning_quarters(),
        canonical_metrics=_fake_metrics(),
        stress_metrics=_fake_metrics(net_pf=1.1),
    )
    with pytest.raises(GuardError, match="RETRY_OR_SLOT_REUSE_REJECTED"):
        run_authorized_development_evaluation_v1(
            REPO,
            authorize_token=HYPOTHESIS_ID,
            output_dir=tmp_path,
            execution_boundary=fake2,
            authorization_decision=_authorized_decision(),
            persist_evidence=True,
        )
    assert fake2.load_calls == 0

    # Exhausted counters also fail closed before runner start.
    monkeypatch.setattr(
        "src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1."
        "evaluate_path_v1.read_run_counters",
        lambda _repo: {
            "contract_development_run_count": 1,
            "contract_runner_start_count": 1,
            "program_development_run_count": 1,
            "program_runner_start_count": 1,
        },
    )
    with pytest.raises(GuardError, match="RUN_LIMIT_EXHAUSTED|RUNNER_START_LIMIT_EXHAUSTED"):
        run_authorized_development_evaluation_v1(
            REPO,
            authorize_token=HYPOTHESIS_ID,
            output_dir=tmp_path / "second_slot",
            execution_boundary=fake2,
            authorization_decision=_authorized_decision(),
            persist_evidence=False,
        )
    assert fake2.load_calls == 0


def test_dataset_config_digest_and_time_segment_bindings() -> None:
    preflight = run_preflight_only(REPO)
    assert preflight["dataset_id"] == DATASET_ID
    assert preflight["config_digest"] == compute_config_digest(REPO)
    assert preflight["strategy_params_digest"] == compute_strategy_params_digest()
    assert preflight["time_segment_definition_id"] == TIME_SEGMENT_DEFINITION_ID
    assert MINIMUM_REBALANCE_OBSERVATIONS == 30
    assert TIME_SEGMENT_ROBUSTNESS_PASS_RATIO == 0.5
    binding = preflight["entry_point_binding"]
    assert binding["dataset_binding"]["dataset_id"] == DATASET_ID
    assert binding["time_segment_definition_id"] == TIME_SEGMENT_DEFINITION_ID
    assert binding["config_digest"] == preflight["config_digest"]
    assert binding["status"] == "EXECUTABLE_EVALUATE_PATH_PRESENT_EVALUATION_UNAUTHORIZED"
    assert binding["development_evaluation_authorized"] is False


def test_holdout_forbidden_on_fake_boundary_and_guards(tmp_path: Path) -> None:
    fake = FakeExecutionBoundaryV1(
        panel=_panel_spanning_quarters(),
        canonical_metrics=_fake_metrics(),
        stress_metrics=_fake_metrics(net_pf=1.1),
    )
    with pytest.raises(ValueError, match="HOLDOUT_PATH_REJECTED"):
        fake.load_development_panel(
            repo_root=REPO, archive_root=tmp_path / f"sealed_{HOLDOUT_OPAQUE_ID}"
        )


def test_dry_validate_and_unauthorized_leave_counters_unchanged() -> None:
    before = read_run_counters(REPO)
    dry = dry_validate_evaluate_path_v1(REPO)
    assert dry.status == "DRY_VALIDATE_PASS_EXECUTABLE_PATH_PRESENT"
    assert dry.runner_started is False
    assert dry.evaluation_executed is False
    assert dry.executable_path_reached is True
    cli_dry = run_dry_validate(REPO)
    assert cli_dry["runner_started"] is False
    assert read_run_counters(REPO) == before
    unauthorized = run_authorized_development_evaluation_v1(
        REPO,
        authorize_token="WRONG_TOKEN",
        output_dir=REPO
        / "docs/evidence/evaluate_cross_sectional_relative_strength_momentum_development_v1",
        persist_evidence=False,
    )
    assert unauthorized.runner_started is False
    assert read_run_counters(REPO) == before


def test_evidence_and_registry_contracts() -> None:
    evidence = empty_evidence_surface_template(
        config_digest=compute_config_digest(REPO),
        strategy_params_digest=compute_strategy_params_digest(),
        dataset_id=DATASET_ID,
        dataset_digest="NOT_RESOLVED",
    )
    registry = build_registry_metadata_v1(
        evaluation_executed=False,
        runner_started=False,
        evaluation_run_count=0,
        runner_start_count=0,
        development_evaluation_authorized=False,
        config_digest=evidence["config_digest"],
        strategy_params_digest=evidence["strategy_params_digest"],
        dataset_id=DATASET_ID,
        dataset_digest="NOT_RESOLVED",
        terminal_development_verdict="NOT_EXECUTED",
    )
    report = validate_evidence_and_registry_contracts_v1(evidence, registry)
    assert report["valid"] is True
    assert json.dumps(registry, sort_keys=True)


def test_implementation_only_head_flags_remain_closed() -> None:
    contract = json.loads(
        (
            REPO / "config/research/"
            "cross_sectional_relative_strength_momentum_v1_preregistered_economic_hypothesis_"
            "measurement_contract_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert contract["development_evaluation_authorized"] is False
    assert contract["development_run_count"] == 0
    assert contract["runner_start_count"] == 0
    assert contract["holdout_authorized"] is False
    runtime = contract["runtime_policy"]
    assert runtime["live_authorized"] is False
    assert runtime["orders_allowed"] is False
    assert runtime["shadow_activated"] is False
    assert runtime["testnet_activated"] is False
