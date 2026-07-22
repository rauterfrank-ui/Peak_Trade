"""Focused tests for VDB v1 corrective measurement reevaluation."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1, PanelBarV1
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.authorization_v1 import (
    resolve_corrective_measurement_reevaluation_authorization_v1,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.binding_v1 import (
    compute_config_digest,
    load_and_validate_entry_point_binding,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.constants_v1 import (
    BASELINE_ID,
    CORRECTIVE_AUTHORIZE_GO_TOKEN,
    CORRECTIVE_EVIDENCE_REL_PATH,
    DATASET_ID,
    ENTRY_POINT_BINDING_REL_PATH,
    EVIDENCE_REL_PATH,
    HYPOTHESIS_ID,
    MEASUREMENT_CONTRACT_REL_PATH,
    MEASUREMENT_REPAIR_MERGE_COMMIT,
    MIN_EXECUTED_TREATMENT_TRADES,
    PORTFOLIO_AGGREGATION_ID,
    PROGRAM_REL_PATH,
    STRATEGY_IDENTITY,
    TIME_SEGMENT_DEFINITION_ID,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.evaluate_path_v1 import (
    run_authorized_development_evaluation_v1,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.execution_boundary_v1 import (
    BacktestMetricsBundleV1,
    FakeExecutionBoundaryV1,
    PanelLoadResultV1,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.guards_v1 import (
    GuardError,
    assert_no_slot_reuse,
    assert_retry_forbidden,
    mutate_corrective_measurement_reevaluation_counters_v1,
    read_corrective_counters,
    read_run_counters,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.panel_wiring_v1 import (
    ArmEventSeriesV1,
    TreatmentBaselineWiringHandoffV1,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.time_segments_v1 import (
    partition_chronological_equal_duration_quarters_v1,
)

REPO = Path(__file__).resolve().parents[2]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _synthetic_panel() -> PanelLoadResultV1:
    segments = partition_chronological_equal_duration_quarters_v1()
    timestamps = tuple(seg.start_inclusive for seg in segments)
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


def _fake_boundary() -> FakeExecutionBoundaryV1:
    panel = _synthetic_panel()
    return FakeExecutionBoundaryV1(
        panel=panel,
        canonical_metrics=_fake_metrics(),
        stress_metrics=_fake_metrics(net_pf=1.1, baseline_net_pf=1.0),
        wiring_handoff=_fake_handoff(panel),
        bound_config_digest=compute_config_digest(REPO),
    )


def test_corrective_auth_rejects_wrong_token() -> None:
    decision = resolve_corrective_measurement_reevaluation_authorization_v1(
        REPO, authorize_token="WRONG_TOKEN"
    )
    assert decision.authorized is False
    assert "CORRECTIVE_AUTHORIZE_GO_TOKEN_MISMATCH" in decision.reason_codes


def test_corrective_auth_rejects_when_development_counters_not_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract_src = REPO / MEASUREMENT_CONTRACT_REL_PATH
    program_src = REPO / PROGRAM_REL_PATH
    binding_src = REPO / ENTRY_POINT_BINDING_REL_PATH
    cfg = tmp_path / "config" / "research"
    cfg.mkdir(parents=True)
    for src in (contract_src, program_src, binding_src):
        shutil.copy(src, cfg / src.name)

    bad_contract = cfg / contract_src.name
    payload = _load(bad_contract)
    payload["development_run_count"] = 0
    bad_contract.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    monkeypatch.setattr(
        "src.research.volatility_decay_breakout_v1_development_evaluation_v1.authorization_v1.MEASUREMENT_CONTRACT_REL_PATH",
        str(Path("config/research") / contract_src.name),
    )
    monkeypatch.setattr(
        "src.research.volatility_decay_breakout_v1_development_evaluation_v1.authorization_v1.PROGRAM_REL_PATH",
        str(Path("config/research") / program_src.name),
    )
    monkeypatch.setattr(
        "src.research.volatility_decay_breakout_v1_development_evaluation_v1.authorization_v1.ENTRY_POINT_BINDING_REL_PATH",
        str(Path("config/research") / binding_src.name),
    )
    decision = resolve_corrective_measurement_reevaluation_authorization_v1(
        tmp_path, authorize_token=CORRECTIVE_AUTHORIZE_GO_TOKEN
    )
    assert decision.authorized is False
    assert "DEVELOPMENT_COUNTERS_NOT_PRESERVED_AT_ONE" in decision.reason_codes


def test_corrective_auth_rejects_when_slot_exhausted_on_head() -> None:
    decision = resolve_corrective_measurement_reevaluation_authorization_v1(
        REPO, authorize_token=CORRECTIVE_AUTHORIZE_GO_TOKEN
    )
    assert decision.authorized is False
    assert "CORRECTIVE_REEVALUATION_LIMIT_EXHAUSTED" in decision.reason_codes
    assert decision.development_counters_preserved is True
    assert decision.measurement_repair_commit_bound is True
    assert decision.portfolio_aggregation_bound is True
    counters = read_corrective_counters(REPO)
    assert counters["contract_corrective_measurement_reevaluation_count"] == 1
    assert counters["contract_development_run_count"] == 1
    assert counters["contract_runner_start_count"] == 1


def test_corrective_terminal_evidence_preserves_development_artifacts() -> None:
    before = read_run_counters(REPO)
    old_summary = REPO / EVIDENCE_REL_PATH / "summary.json"
    old_registry = REPO / EVIDENCE_REL_PATH / "registry.json"
    old_claim = REPO / EVIDENCE_REL_PATH / "run_slot_claim.json"
    corrective_summary = REPO / CORRECTIVE_EVIDENCE_REL_PATH / "summary.json"
    assert corrective_summary.is_file()
    summary = _load(corrective_summary)
    assert summary["status"] == "FAIL_CLOSED"
    assert summary["corrective_measurement_reevaluation_count"] == 1
    assert summary["original_development_run_count"] == 1
    assert summary["portfolio_aggregation_id"] == PORTFOLIO_AGGREGATION_ID
    assert summary["measurement_repair_merge_commit"] == MEASUREMENT_REPAIR_MERGE_COMMIT
    assert summary["superseded_development_evidence_ref"] == EVIDENCE_REL_PATH
    assert summary["development_artifacts_preserved_unmodified"] is True
    assert summary["terminal_corrective_verdict"] == (
        "CORRECTIVE_MEASUREMENT_REEVALUATION_EXECUTED_TERMINAL/FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT"
    )
    assert (REPO / CORRECTIVE_EVIDENCE_REL_PATH / "registry.json").is_file()
    assert (REPO / CORRECTIVE_EVIDENCE_REL_PATH / "corrective_run_slot_claim.json").is_file()
    assert (REPO / CORRECTIVE_EVIDENCE_REL_PATH / "supersession.json").is_file()
    assert old_summary.is_file()
    assert old_registry.is_file()
    assert old_claim.is_file()
    assert read_run_counters(REPO) == before
    binding = load_and_validate_entry_point_binding(REPO)
    assert binding["corrective_measurement_reevaluation_count"] == 1
    assert binding["development_run_count"] == 1
    assert binding["runner_start_count"] == 1


def test_development_evaluate_still_fail_closed_on_slot_reuse() -> None:
    before = read_run_counters(REPO)
    assert before["contract_development_run_count"] == 1
    with pytest.raises(GuardError, match="RUN_LIMIT_EXHAUSTED"):
        assert_retry_forbidden(
            retry_requested=False,
            development_run_count=before["contract_development_run_count"],
            runner_start_count=before["contract_runner_start_count"],
        )
    with pytest.raises(GuardError, match="RETRY_OR_SLOT_REUSE_REJECTED"):
        assert_no_slot_reuse(REPO / EVIDENCE_REL_PATH)
    with pytest.raises(GuardError, match="RETRY_OR_SLOT_REUSE_REJECTED|RUN_LIMIT_EXHAUSTED"):
        run_authorized_development_evaluation_v1(
            REPO,
            authorize_token=HYPOTHESIS_ID,
            output_dir=REPO / EVIDENCE_REL_PATH,
            persist_evidence=False,
            execution_boundary=_fake_boundary(),
        )
    assert read_run_counters(REPO) == before


def test_mutator_preserves_development_run_count(tmp_path: Path) -> None:
    cfg = tmp_path / "config" / "research"
    cfg.mkdir(parents=True)
    for rel in (MEASUREMENT_CONTRACT_REL_PATH, PROGRAM_REL_PATH, ENTRY_POINT_BINDING_REL_PATH):
        src = REPO / rel
        shutil.copy(src, cfg / src.name)

    # Point mutator at tmp copies by rewriting relative paths under tmp_path as repo_root.
    # Use a thin wrapper that temporarily swaps files via chdir semantics:
    # implement by calling mutator with a custom repo that mirrors layout.
    (
        tmp_path
        / "src"
        / "research"
        / "volatility_compression_breakout_v1_development_evaluation_v1"
    ).mkdir(parents=True)
    pnl_src = (
        REPO / "src/research/volatility_compression_breakout_v1_development_evaluation_v1/"
        "productive_exit_pnl_evaluator_v1.py"
    )
    pnl_dst = (
        tmp_path / "src/research/volatility_compression_breakout_v1_development_evaluation_v1/"
        "productive_exit_pnl_evaluator_v1.py"
    )
    shutil.copy(pnl_src, pnl_dst)
    # Also need implementation binding + shared channel modules for materialize.
    for rel in (
        "config/research/volatility_decay_breakout_v1_strategy_implementation_binding_v1.json",
        "src/research/price_channel_breakout_core_v1.py",
        "src/research/volatility_decay_breakout_v1_strategy_v1.py",
        "src/research/unconditional_20_bar_price_channel_breakout_v1.py",
        "src/research/volatility_decay_breakout_v1_vol_state_v1.py",
    ):
        src = REPO / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            shutil.copy(src, dst)

    # Reset corrective count on tmp copies so mutator can consume 0→1 once.
    for name in (
        Path(MEASUREMENT_CONTRACT_REL_PATH).name,
        Path(PROGRAM_REL_PATH).name,
        Path(ENTRY_POINT_BINDING_REL_PATH).name,
    ):
        payload = _load(cfg / name)
        payload["corrective_measurement_reevaluation_count"] = 0
        (cfg / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # materialize imports live modules from installed package; binding rematerialize
    # only needs JSON files + productive evaluator path existence. Copy is enough.
    before_dev = _load(cfg / Path(MEASUREMENT_CONTRACT_REL_PATH).name)["development_run_count"]
    assert before_dev == 1
    assert (
        _load(cfg / Path(MEASUREMENT_CONTRACT_REL_PATH).name)[
            "corrective_measurement_reevaluation_count"
        ]
        == 0
    )

    mutate_corrective_measurement_reevaluation_counters_v1(tmp_path)

    contract = _load(cfg / Path(MEASUREMENT_CONTRACT_REL_PATH).name)
    program = _load(cfg / Path(PROGRAM_REL_PATH).name)
    binding = _load(cfg / Path(ENTRY_POINT_BINDING_REL_PATH).name)
    assert contract["development_run_count"] == 1
    assert contract["runner_start_count"] == 1
    assert program["development_run_count"] == 1
    assert program["runner_start_count"] == 1
    assert contract["corrective_measurement_reevaluation_count"] == 1
    assert program["corrective_measurement_reevaluation_count"] == 1
    assert binding["corrective_measurement_reevaluation_count"] == 1
    assert binding["development_run_count"] == 1
    assert binding["runner_start_count"] == 1
    # Durable repo remains at count 1 (this test mutated only tmp_path).
    assert read_corrective_counters(REPO)["contract_corrective_measurement_reevaluation_count"] == 1
    load_and_validate_entry_point_binding(REPO)
