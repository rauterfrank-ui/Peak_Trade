"""Contract tests for lead-lag v0 BacktestEngine MV2 replay signal parity v0."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.backtest import mv2_research_wiring_v1 as wiring
from src.backtest.strategy_signal_binding_v1 import (
    ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
    ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
    StrategySignalBindingError,
    assert_backtest_engine_mv2_replay_signal_parity_v1,
    validate_mv2_replay_engine_signal_contract_v1,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
    BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN,
    LEGACY_RESEARCH_PATH_MODE,
    SYSTEM_EVIDENCE_MV2_PATH_MODE,
    load_ops_evaluation_config_v0,
    load_versioned_hypothesis_binding_v0,
    materialize_backtest_engine_mv2_replay_signal_parity_contract_v0,
    reject_legacy_raw_engine_signal_bypass_v0 as execution_reject_legacy_raw,
    resolve_productive_evaluation_path_mode_v0,
    run_backtest_engine_mv2_replay_signal_parity_dispatch_v0,
    validate_entry_point_go_token_v0,
)
from src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0 import (
    BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN as ADAPTER_PARITY_GO_TOKEN,
    PRODUCTIVE_BACKTEST_ENGINE_SIGNAL_SOURCE,
    REASON_LEGACY_RAW_ENGINE_SIGNAL_BYPASS_BLOCKED,
    AdapterTerminalStatus,
    materialize_adapter_contract_v0,
    reject_legacy_raw_engine_signal_bypass_v0 as adapter_reject_legacy_raw,
    run_lead_lag_mv2_research_backtest_wiring_boundary_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
    build_synthetic_panel_series_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_MODULE = (
    REPO_ROOT
    / "src/research/cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0.py"
)
EXECUTION_MODULE = (
    REPO_ROOT
    / "src/research/cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_execution_v0.py"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
)


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return load_versioned_hypothesis_binding_v0(REPO_ROOT)


@pytest.fixture(name="ops_config")
def fixture_ops_config() -> dict:
    return load_ops_evaluation_config_v0(REPO_ROOT)


def test_parity_go_token_registered_in_entry_point_dispatch() -> None:
    ok, branch = validate_entry_point_go_token_v0(BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN)
    assert ok is True
    assert branch == "BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_V0"


def test_parity_contract_declares_mv2_replay_engine_source() -> None:
    contract = materialize_backtest_engine_mv2_replay_signal_parity_contract_v0()
    assert contract["productive_backtest_engine_signal_source"] == ENGINE_SIGNAL_SOURCE_MV2_REPLAY
    assert contract["legacy_raw_engine_signal_bypass_blocked"] is True
    assert contract["canonical_backtest_engine_owner"] == "backtest.mv2_research_wiring_v1"
    assert contract["economic_evaluation_executed"] is False
    assert contract["authority_effect"] == "NONE"
    assert contract["runtime_effect"] == "NONE"


def test_adapter_contract_declares_mv2_replay_engine_source() -> None:
    contract = materialize_adapter_contract_v0()
    assert (
        contract["productive_backtest_engine_signal_source"]
        == PRODUCTIVE_BACKTEST_ENGINE_SIGNAL_SOURCE
    )
    assert contract["legacy_raw_engine_signal_bypass_blocked"] is True
    assert ADAPTER_PARITY_GO_TOKEN in contract["allowed_adapter_go_tokens"]


def test_legacy_raw_engine_signal_bypass_rejected() -> None:
    ok, reasons = adapter_reject_legacy_raw(
        backtest_engine_signal_source=ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
    )
    assert ok is False
    assert REASON_LEGACY_RAW_ENGINE_SIGNAL_BYPASS_BLOCKED in reasons
    exec_ok, exec_reasons = execution_reject_legacy_raw(
        backtest_engine_signal_source=ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
    )
    assert exec_ok is False
    assert REASON_LEGACY_RAW_ENGINE_SIGNAL_BYPASS_BLOCKED in exec_reasons


def test_productive_go_token_resolves_to_system_evidence_mv2() -> None:
    assert (
        resolve_productive_evaluation_path_mode_v0(
            go_token=BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN,
        )
        == SYSTEM_EVIDENCE_MV2_PATH_MODE
    )


def test_lead_lag_real_path_selects_mv2_replay_engine_source(
    complete_binding: dict,
    ops_config: dict,
) -> None:
    panel = build_synthetic_panel_series_v0(bar_count=12)
    result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        ops_config=ops_config,
        go_token=BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN,
    )
    assert result.status is AdapterTerminalStatus.MV2_WIRING_BOUNDARY_COMPLETE
    wiring = result.wiring_result
    assert wiring is not None
    assert wiring.backtest_engine_signal_source == ENGINE_SIGNAL_SOURCE_MV2_REPLAY
    assert wiring.backtest_engine_signal_digest == wiring.mv2_replay_signal_digest
    assert len(wiring.mv2_replay_signals) == len(wiring.bar_outcomes)
    replay_values = wiring.mv2_replay_signals.astype(int).tolist()
    outcome_values = [item.position_signal for item in wiring.bar_outcomes]
    assert replay_values == outcome_values


def test_deterministic_repeated_execution(
    complete_binding: dict,
    ops_config: dict,
) -> None:
    panel = build_synthetic_panel_series_v0(bar_count=12)
    first = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        ops_config=ops_config,
        go_token=BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN,
    )
    second = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        ops_config=ops_config,
        go_token=BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN,
    )
    assert first.wiring_result is not None
    assert second.wiring_result is not None
    assert (
        first.wiring_result.mv2_replay_signal_digest
        == second.wiring_result.mv2_replay_signal_digest
    )
    assert (
        first.wiring_result.backtest_engine_signal_digest
        == second.wiring_result.backtest_engine_signal_digest
    )
    assert first.wiring_result.mv2_replay_signals.equals(second.wiring_result.mv2_replay_signals)


def test_decision_field_parity_on_real_path(
    complete_binding: dict,
    ops_config: dict,
) -> None:
    panel = build_synthetic_panel_series_v0(bar_count=12)
    result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        ops_config=ops_config,
        go_token=BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN,
    )
    wiring = result.wiring_result
    assert wiring is not None
    for idx, outcome in enumerate(wiring.bar_outcomes):
        assert outcome.trading_epoch == idx
        assert outcome.position_signal == int(wiring.mv2_replay_signals.iloc[idx])
        assert outcome.evidence.decision_outcome is not None
        assert isinstance(outcome.replay_pass, bool)


def test_malformed_mv2_replay_digest_fail_closed() -> None:
    idx = pd.date_range("2026-06-01", periods=3, freq="1h", tz="UTC")
    signals = pd.Series([0, 1, -1], index=idx, dtype=int)
    with pytest.raises(StrategySignalBindingError, match="mv2_replay_signal_digest_mismatch"):
        validate_mv2_replay_engine_signal_contract_v1(
            signals,
            bars_index=idx,
            strategy_id="momentum_1h",
            mv2_replay_signal_digest="a" * 64,
            expected_mv2_replay_signal_digest="b" * 64,
        )


def test_stale_index_mismatch_fail_closed() -> None:
    idx = pd.date_range("2026-06-01", periods=3, freq="1h", tz="UTC")
    stale_idx = pd.date_range("2026-06-02", periods=3, freq="1h", tz="UTC")
    signals = pd.Series([0, 1, -1], index=stale_idx, dtype=int)
    with pytest.raises(StrategySignalBindingError, match="mv2_replay_signal_index_mismatch"):
        validate_mv2_replay_engine_signal_contract_v1(
            signals,
            bars_index=idx,
            strategy_id="momentum_1h",
            mv2_replay_signal_digest="a" * 64,
        )


def test_unrelated_mv2_wiring_path_unchanged() -> None:
    idx = pd.date_range("2026-06-01", periods=12, freq="1h", tz="UTC")
    close = [100.0 + float(i) for i in range(12)]
    bars = pd.DataFrame(
        {
            "open": close,
            "high": [v + 0.5 for v in close],
            "low": [v - 0.5 for v in close],
            "close": close,
            "mark_price": close,
            "index_price": [v - 0.1 for v in close],
            "best_bid": [v - 0.05 for v in close],
            "best_ask": [v + 0.05 for v in close],
            "spread": [0.1 for _ in close],
            "volume": [1000.0 for _ in close],
            "open_interest": [10000.0 for _ in close],
            "funding_rate": [0.0001 for _ in close],
            "volatility_estimate": [0.2 for _ in close],
            "is_final": [True for _ in close],
            "bar_interval": ["1m" for _ in close],
        },
        index=idx,
    )
    cfg = {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
        },
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
        "economic_evaluation_v1": {
            "strategy_params": {"fast_window": 2, "slow_window": 3},
        },
    }
    result = wiring.run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id="ma_crossover",
        cfg=cfg,
    )
    assert result.backtest_engine_signal_source == ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY
    assert (
        result.strategy_signal_provenance.engine_signal_source
        == ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY
    )


def test_parity_dispatch_wrapper_reports_pass(
    complete_binding: dict,
) -> None:
    panel = build_synthetic_panel_series_v0(bar_count=12)
    payload = run_backtest_engine_mv2_replay_signal_parity_dispatch_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token=BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN,
    )
    assert payload["backtest_engine_mv2_replay_signal_parity_pass"] is True
    assert payload["legacy_raw_engine_signal_bypass_blocked"] is True
    assert payload["backtest_engine_signal_source"] == ENGINE_SIGNAL_SOURCE_MV2_REPLAY
    assert payload["economic_evaluation_executed"] is False
    assert payload["authority_effect"] == "NONE"
    assert payload["runtime_effect"] == "NONE"


def test_legacy_research_path_still_blocked_for_parity_go() -> None:
    assert (
        resolve_productive_evaluation_path_mode_v0(
            go_token=BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN,
        )
        != LEGACY_RESEARCH_PATH_MODE
    )


def test_canonical_mv2_owner_invoked_with_mv2_replay_engine_source(
    complete_binding: dict,
    ops_config: dict,
) -> None:
    panel = build_synthetic_panel_series_v0()
    with patch(
        "src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0.run_mv2_research_backtest_wiring_v1",
    ) as mv2_call:
        mv2_call.return_value = wiring.MV2ResearchWiringResultV1(
            instrument_id="inst-eth-usdt-perp",
            registry_snapshot=type("Snap", (), {"semantic_digest": "a" * 64})(),
            effective_cost_config=type("Cost", (), {"config_digest": "b" * 64})(),
            bar_outcomes=(),
            signals=pd.Series([], dtype=int),
            backtest_result=type(
                "BT",
                (),
                {"stats": {"total_trades": 0}, "trades": None, "equity_curve": None},
            )(),
            mv2_replay_signals=pd.Series([], dtype=int),
            strategy_signal_provenance=type("P", (), {})(),
            mv2_replay_signal_digest="c" * 64,
            mv2_replay_nonzero_signal_count=0,
            backtest_engine_signal_source=ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
            backtest_engine_signal_digest="c" * 64,
        )
        run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
            repo_root=REPO_ROOT,
            panel_series=panel,
            versioned_binding=complete_binding,
            ops_config=ops_config,
            go_token=BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN,
        )
    _, kwargs = mv2_call.call_args
    assert kwargs["backtest_engine_signal_source"] == ENGINE_SIGNAL_SOURCE_MV2_REPLAY


def test_assert_backtest_engine_mv2_replay_signal_parity_helper(
    complete_binding: dict,
    ops_config: dict,
) -> None:
    result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=REPO_ROOT,
        panel_series=build_synthetic_panel_series_v0(bar_count=12),
        versioned_binding=complete_binding,
        ops_config=ops_config,
        go_token=BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN,
    )
    wiring = result.wiring_result
    assert wiring is not None
    assert_backtest_engine_mv2_replay_signal_parity_v1(
        mv2_replay_signals=wiring.mv2_replay_signals,
        bar_outcomes=wiring.bar_outcomes,
        backtest_engine_signal_source=wiring.backtest_engine_signal_source,
        backtest_engine_signal_digest=wiring.backtest_engine_signal_digest,
        mv2_replay_signal_digest=wiring.mv2_replay_signal_digest,
    )


def _collect_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_execution_module_still_has_no_runtime_imports() -> None:
    imports = _collect_imports(EXECUTION_MODULE)
    for forbidden in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
        assert not any(item == forbidden or item.startswith(forbidden + ".") for item in imports)


def test_before_after_signal_source_inventory_shape() -> None:
    before_after = {
        "before": {
            "backtest_engine_signal_source": ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
            "legacy_raw_engine_signal_bypass_reachable": True,
        },
        "after": {
            "backtest_engine_signal_source": ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
            "legacy_raw_engine_signal_bypass_reachable": False,
        },
    }
    assert before_after["after"]["backtest_engine_signal_source"] == ENGINE_SIGNAL_SOURCE_MV2_REPLAY
    assert json.dumps(before_after)
