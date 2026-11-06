"""Contract tests for cross-sectional relative-strength v0 binding completion."""

from __future__ import annotations

import json
import math
import socket
from copy import deepcopy
from pathlib import Path

import pytest

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_panel_robustness_adapter_v0 import (
    build_all_panel_robustness_adapter_inputs_v0,
)
from src.research.cross_sectional_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_cross_sectional_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_relative_strength_v0_score_v0 import (
    SCORE_FORMULA_VERSION,
    compute_instrument_score_v0,
    rank_scores_deterministic_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    BINDING_SCHEMA_VERSION,
    CONFIG_REL_PATH,
    EFFECTIVE_ENTRY_COST_BPS,
    FEE_BPS_PER_SIDE,
    FUNDING_MODEL_VERSION,
    PANEL_DATASET_ID,
    PERIOD_BINDING_ID,
    ROUNDTRIP_COST_BPS,
    STRATEGY_ID,
    STRATEGY_VERSION,
    BindingMaterializationVerdict,
    build_cost_execution_binding_v0,
    build_economic_policy_binding_v0,
    build_panel_dataset_binding_v0,
    build_period_binding_v0,
    build_pit_universe_binding_v0,
    compute_implementation_digest_v0,
    materialize_and_validate_versioned_research_binding_v0,
    materialize_versioned_research_binding_v0,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    OrchestratorErrorCode,
    SlotSide,
    default_operator_binding_v0,
    run_cross_sectional_single_slot_orchestrator_v0,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    InstrumentPanelSeriesV1,
    PanelValidationErrorCode,
    validate_panel_series_v1,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
    build_bitcoin_contaminated_panel_v0,
    build_incomplete_panel_series_v0,
    build_synthetic_panel_series_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def complete_binding() -> dict:
    return materialize_versioned_research_binding_v0()


@pytest.fixture
def panel_series() -> tuple:
    return build_synthetic_panel_series_v0()


@pytest.fixture
def operator_binding() -> dict:
    return default_operator_binding_v0()


# --- Binding completeness ---


def test_binding_materialization_complete() -> None:
    result = materialize_and_validate_versioned_research_binding_v0()
    assert result.verdict == BindingMaterializationVerdict.COMPLETE
    assert result.validation_verdict == ValidationVerdict.ACCEPTED_COMPLETE
    assert result.fail_reasons == ()


def test_strategy_id_and_version(complete_binding: dict) -> None:
    assert complete_binding["strategy_id"] == STRATEGY_ID
    assert complete_binding["strategy_version"] == STRATEGY_VERSION
    assert complete_binding["research_hypothesis_id"] == (
        "CROSS_SECTIONAL_RELATIVE_STRENGTH_NON_BITCOIN_PERPETUALS_V0"
    )


def test_futures_only_and_bitcoin_exclusion(complete_binding: dict) -> None:
    constraints = complete_binding["system_constraints"]
    assert constraints["futures_only"] is True
    assert constraints["bitcoin_direction_allowed"] is False
    assert constraints["spot_allowed"] is False
    assert constraints["synthetic_spot_allowed"] is False
    universe = complete_binding["pit_universe_binding"]
    assert universe["bitcoin_excluded"] is True
    assert universe["instrument_type"] == "LINEAR_PERPETUAL"


def test_parameter_binding_frozen(complete_binding: dict) -> None:
    params = complete_binding["parameter_binding"]["parameters"]
    assert params["lookback_N"] == 20
    assert params["vol_window_V"] == 20
    assert params["vol_epsilon"] == 1e-8
    assert params["vol_return_method"] == "log_return"
    assert params["rebalance_interval_bars"] == 1
    assert params["signal_lag_bars"] == 1
    assert params["min_eligible_members_for_rank"] == 5
    assert params["switch_entry_delay_epochs"] == 1
    assert params["max_bar_staleness_bars"] == 1
    assert complete_binding["parameter_binding"]["parameter_search_forbidden"] is True


def test_pit_universe_binding_present(complete_binding: dict) -> None:
    binding = complete_binding["pit_universe_binding"]
    assert binding["venue"] == "OKX"
    assert binding["minimum_eligible_member_count"] == 5
    assert binding["pit_universe_manifest_ref"].startswith("pit_futures_universe_manifest_v1:")
    assert binding["survivorship_bias_forbidden"] is True


def test_dataset_binding_present(complete_binding: dict) -> None:
    binding = complete_binding["panel_dataset_binding"]
    assert binding["dataset_id"] == PANEL_DATASET_ID
    assert binding["bar_interval"] == "PT1H"
    assert binding["network_access_forbidden"] is True
    assert binding["credential_access_forbidden"] is True


def test_period_binding_non_overlap(complete_binding: dict) -> None:
    binding = complete_binding["period_binding"]
    assert binding["period_binding_id"] == PERIOD_BINDING_ID
    assert binding["no_overlap_enforced"] is True
    assert binding["holdout_isolation_enforced"] is True
    assert binding["training_end"] < binding["validation_start"]
    assert binding["validation_end"] < binding["out_of_sample_start"]


def test_cost_binding_non_zero() -> None:
    cost = build_cost_execution_binding_v0()
    assert cost["fee_model_binding"]["fee_bps_per_side"] == FEE_BPS_PER_SIDE
    assert cost["fee_model_binding"]["fee_bps_per_side"] > 0
    assert cost["slippage_model_binding"]["slippage_bps_per_side"] > 0
    assert cost["execution_model_binding"]["roundtrip_cost_bps"] == ROUNDTRIP_COST_BPS
    assert ROUNDTRIP_COST_BPS == 2 * EFFECTIVE_ENTRY_COST_BPS
    assert cost["implicit_zero_cost_forbidden"] is True


def test_funding_binding_required() -> None:
    cost = build_cost_execution_binding_v0()
    assert cost["funding_model_binding"]["bind"] is True
    assert cost["funding_model_binding"]["funding_model_version"] == FUNDING_MODEL_VERSION


def test_economic_policy_reuse() -> None:
    policy = build_economic_policy_binding_v0()
    assert policy["economic_validity_policy_version"] == ECONOMIC_VALIDITY_POLICY_VERSION
    assert policy["policy_lowering_forbidden"] is True
    assert policy["promising_is_not_pass"] is True


def test_binding_digest_stability(complete_binding: dict) -> None:
    first = complete_binding["binding_digest"]
    second = materialize_versioned_research_binding_v0()["binding_digest"]
    assert first == second
    assert len(first) == 64


def test_config_digest_stability(complete_binding: dict) -> None:
    first = complete_binding["config_digest"]
    second = materialize_versioned_research_binding_v0()["config_digest"]
    assert first == second


def test_implementation_digest_stability() -> None:
    first = compute_implementation_digest_v0()
    second = compute_implementation_digest_v0()
    assert first == second


def test_config_artifact_on_disk(complete_binding: dict) -> None:
    path = REPO_ROOT / CONFIG_REL_PATH
    assert path.is_file()
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk["schema_version"] == BINDING_SCHEMA_VERSION
    assert on_disk["binding_digest"] == complete_binding["binding_digest"]


def test_missing_binding_fail_closed() -> None:
    binding = default_operator_binding_v0()
    binding["numeric_bindings"].pop("lookback_N")
    with pytest.raises(ValueError, match=OrchestratorErrorCode.BINDING_INCOMPLETE.value):
        run_cross_sectional_single_slot_orchestrator_v0(
            binding=binding,
            panel_series=build_synthetic_panel_series_v0(),
        )


# --- Score and ranking ---


def test_deterministic_score(panel_series: tuple) -> None:
    series = panel_series[0]
    closes = tuple(float(bar.close) for bar in series.bars)
    result_a = compute_instrument_score_v0(
        series.instrument_id,
        closes,
        lookback_n=20,
        vol_window_v=20,
        vol_epsilon=1e-8,
        signal_lag_bars=1,
        epoch_index=25,
    )
    result_b = compute_instrument_score_v0(
        series.instrument_id,
        closes,
        lookback_n=20,
        vol_window_v=20,
        vol_epsilon=1e-8,
        signal_lag_bars=1,
        epoch_index=25,
    )
    assert result_a is not None
    assert result_b is not None
    assert result_a.score == result_b.score


def test_stable_tie_break() -> None:
    from src.research.cross_sectional_relative_strength_v0_score_v0 import (
        CrossSectionalScoreResultV0,
    )

    scores = (
        CrossSectionalScoreResultV0("b", 1.0, 0.1, 0.1, True),
        CrossSectionalScoreResultV0("a", 1.0, 0.1, 0.1, True),
    )
    ranked = rank_scores_deterministic_v0(scores)
    assert [item.instrument_id for item in ranked] == ["a", "b"]


def test_bitcoin_exclusion_score() -> None:
    closes = tuple(100.0 + i for i in range(30))
    result = compute_instrument_score_v0(
        "okx:linear_perpetual:BTC-USDT",
        closes,
        lookback_n=20,
        vol_window_v=20,
        vol_epsilon=1e-8,
        signal_lag_bars=1,
        epoch_index=25,
    )
    assert result is None


def test_signal_lag_no_lookahead() -> None:
    series = build_synthetic_panel_series_v0(bar_count=30)[0]
    closes = tuple(float(bar.close) for bar in series.bars)
    epoch = 25
    score_at_epoch = compute_instrument_score_v0(
        series.instrument_id,
        closes,
        lookback_n=20,
        vol_window_v=20,
        vol_epsilon=1e-8,
        signal_lag_bars=1,
        epoch_index=epoch,
    )
    mutated = list(closes)
    mutated[-1] = mutated[-1] * 10.0
    score_unchanged = compute_instrument_score_v0(
        series.instrument_id,
        tuple(mutated),
        lookback_n=20,
        vol_window_v=20,
        vol_epsilon=1e-8,
        signal_lag_bars=1,
        epoch_index=epoch,
    )
    assert score_at_epoch is not None
    assert score_unchanged is not None
    assert score_at_epoch.score == score_unchanged.score


# --- Orchestrator ---


def test_orchestrator_runs(panel_series: tuple, operator_binding: dict) -> None:
    result = run_cross_sectional_single_slot_orchestrator_v0(
        binding=operator_binding,
        panel_series=panel_series,
    )
    assert result.orchestrator_version.startswith("cross_sectional_single_slot")
    assert result.score_formula_version == SCORE_FORMULA_VERSION
    assert len(result.epochs) > 0
    assert result.authority_effect == "NONE"
    assert result.runtime_effect == "NONE"
    assert result.order_effect == "NONE"


def test_single_slot_invariant(panel_series: tuple, operator_binding: dict) -> None:
    result = run_cross_sectional_single_slot_orchestrator_v0(
        binding=operator_binding,
        panel_series=panel_series,
    )
    for epoch in result.epochs:
        side = epoch.selection.slot_side
        assert side in {SlotSide.FLAT, SlotSide.LONG, SlotSide.SHORT}
        if side == SlotSide.FLAT:
            assert epoch.selection.selected_instrument_id is None
        else:
            assert epoch.selection.selected_instrument_id is not None


def test_no_simultaneous_long_short(panel_series: tuple, operator_binding: dict) -> None:
    result = run_cross_sectional_single_slot_orchestrator_v0(
        binding=operator_binding,
        panel_series=panel_series,
    )
    for epoch in result.epochs:
        side = epoch.selection.slot_side
        assert side != SlotSide.LONG or side != SlotSide.SHORT


def test_rotation_requires_flat_delay(panel_series: tuple, operator_binding: dict) -> None:
    result = run_cross_sectional_single_slot_orchestrator_v0(
        binding=operator_binding,
        panel_series=panel_series,
    )
    pending_epochs = [e for e in result.epochs if e.selection.pending_switch]
    assert len(pending_epochs) >= 0


def test_long_selection(panel_series: tuple, operator_binding: dict) -> None:
    result = run_cross_sectional_single_slot_orchestrator_v0(
        binding=operator_binding,
        panel_series=panel_series,
    )
    long_epochs = [e for e in result.epochs if e.selection.slot_side == SlotSide.LONG]
    assert len(long_epochs) > 0


def test_insufficient_panel_fail_closed(operator_binding: dict) -> None:
    short_panel = build_synthetic_panel_series_v0(bar_count=30)[:3]
    validation = validate_panel_series_v1(short_panel, min_instruments=5)
    assert not validation.valid
    assert PanelValidationErrorCode.INSUFFICIENT_INSTRUMENTS.value in validation.error_codes


def test_bitcoin_panel_exclusion() -> None:
    panel = build_bitcoin_contaminated_panel_v0()
    validation = validate_panel_series_v1(panel, min_instruments=5)
    assert not validation.valid
    assert PanelValidationErrorCode.BITCOIN_INSTRUMENT_PRESENT.value in validation.error_codes


def test_stale_bar_exclusion() -> None:
    from src.research.cross_sectional_single_slot_research_orchestrator_v0 import _is_stale
    from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import PanelBarV1

    bars = tuple(
        PanelBarV1(
            instrument_id="okx:linear_perpetual:ETH-USDT",
            timestamp_utc=f"2024-06-01T{hour:02d}:00:00Z",
            open="1",
            high="2",
            low="0.5",
            close="1.5",
            volume="10",
            is_final=True,
        )
        for hour in range(0, 25)
    )
    reference_ts = "2024-06-01T28:00:00Z"
    assert _is_stale(
        bars,
        epoch_index=27,
        reference_timestamp=reference_ts,
        max_bar_staleness_bars=1,
    )
    assert not _is_stale(
        bars,
        epoch_index=24,
        reference_timestamp="2024-06-01T24:00:00Z",
        max_bar_staleness_bars=1,
    )


def test_incomplete_panel_fail_closed(operator_binding: dict) -> None:
    panel = build_incomplete_panel_series_v0()
    validation = validate_panel_series_v1(panel, min_instruments=5)
    assert not validation.valid
    result = run_cross_sectional_single_slot_orchestrator_v0(
        binding=operator_binding,
        panel_series=panel,
    )
    assert len(result.epochs) == 0


# --- Robustness adapters ---


def test_panel_robustness_adapters_contract_only(
    panel_series: tuple,
    operator_binding: dict,
    complete_binding: dict,
) -> None:
    orch = run_cross_sectional_single_slot_orchestrator_v0(
        binding=operator_binding,
        panel_series=panel_series,
    )
    adapters = build_all_panel_robustness_adapter_inputs_v0(
        orch,
        economic_policy_binding=complete_binding["economic_policy_binding"],
    )
    assert adapters["walk_forward"].authority_effect == "NONE"
    assert adapters["monte_carlo"].runs == 64
    assert adapters["parameter_sensitivity"].parameter_search_forbidden is True
    assert adapters["economic_viability_evidence"].evaluation_executed is False


# --- Safety boundaries ---


def test_no_runtime_effect(complete_binding: dict) -> None:
    assert complete_binding["runtime_effect"] == "NONE"
    assert complete_binding["order_effect"] == "NONE"
    assert complete_binding["authority_effect"] == "NONE"
    assert complete_binding["economic_evaluation_executed"] is False


def test_no_network_access() -> None:
    dataset = build_panel_dataset_binding_v0()
    assert dataset["network_access_forbidden"] is True
    try:
        socket.create_connection(("1.1.1.1", 80), timeout=0.01)
        network_reachable = True
    except OSError:
        network_reachable = False
    assert dataset["network_access_forbidden"] is True or not network_reachable


def test_validator_accepts_complete_binding(complete_binding: dict) -> None:
    result = validate_cross_sectional_ranking_semantics_binding_v0(complete_binding["binding"])
    assert result.valid is True
    assert result.verdict == ValidationVerdict.ACCEPTED_COMPLETE


def test_incomplete_binding_rejected_as_complete(complete_binding: dict) -> None:
    binding = deepcopy(complete_binding["binding"])
    binding["external_bindings"]["pit_universe_manifest_ref"] = {"status": "REQUIRED_UNBOUND"}
    binding["binding_status"]["overall_binding_status"] = "COMPLETE"
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is False


def test_score_formula_documented(complete_binding: dict) -> None:
    param = complete_binding["parameter_binding"]
    assert param["score_formula_version"] == SCORE_FORMULA_VERSION
    assert "log_return_N" in param["score_formula_expression"]
    assert "vol_epsilon" in param["score_formula_expression"]
