"""Contract suite for lead-lag v0 research-eval decision parity v0."""

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
    validate_mv2_replay_engine_signal_contract_v1,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
    LEGACY_RESEARCH_PATH_MODE,
    RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_GO_TOKEN,
    SYSTEM_EVIDENCE_MV2_PATH_MODE,
    load_ops_evaluation_config_v0,
    load_versioned_hypothesis_binding_v0,
    resolve_productive_evaluation_path_mode_v0,
    run_research_eval_decision_parity_contract_suite_dispatch_v0,
    validate_entry_point_go_token_v0,
)
from src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0 import (
    PRODUCTIVE_BACKTEST_ENGINE_SIGNAL_SOURCE,
    REASON_LEGACY_RAW_ENGINE_SIGNAL_BYPASS_BLOCKED,
    AdapterTerminalStatus,
    reject_legacy_raw_engine_signal_bypass_v0,
    run_lead_lag_mv2_research_backtest_wiring_boundary_v0,
)
from src.research.cross_sectional_lead_lag_v0_research_eval_decision_parity_contract_v0 import (
    CANONICAL_FIXTURE_OWNER,
    CANONICAL_PARITY_HARNESS_OWNER,
    CANONICAL_RESEARCH_EVAL_ENTRY_POINT,
    CANONICAL_RESEARCH_EVAL_OWNER,
    FixtureClassKind,
    GO_TOKEN,
    LEAD_LAG_FIXTURE_CLASS_BINDINGS,
    evaluate_harness_fixture_class_matrix_v0,
    evaluate_lead_lag_research_eval_decision_parity_suite_v0,
    evaluate_negative_path_fail_closed_v0,
    execute_parity_harness_fixture_matrix_v0,
    execute_productive_lead_lag_research_eval_path_v0,
    materialize_parity_contract_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
    build_synthetic_panel_series_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_MODULE = REPO_ROOT / (
    "src/research/cross_sectional_lead_lag_v0_research_eval_decision_parity_contract_v0.py"
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


def test_go_token_registered_in_entry_point_dispatch() -> None:
    ok, branch = validate_entry_point_go_token_v0(
        RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_GO_TOKEN
    )
    assert ok is True
    assert branch == "RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_V0"


def test_parity_contract_declares_canonical_owners() -> None:
    contract = materialize_parity_contract_v0()
    assert contract["go_token"] == GO_TOKEN
    assert contract["canonical_research_eval_entry_point"] == CANONICAL_RESEARCH_EVAL_ENTRY_POINT
    assert contract["canonical_research_eval_owner"] == CANONICAL_RESEARCH_EVAL_OWNER
    assert contract["canonical_parity_harness_owner"] == CANONICAL_PARITY_HARNESS_OWNER
    assert contract["canonical_fixture_owner"] == CANONICAL_FIXTURE_OWNER
    assert (
        contract["productive_backtest_engine_signal_source"]
        == PRODUCTIVE_BACKTEST_ENGINE_SIGNAL_SOURCE
    )
    assert contract["legacy_raw_engine_signal_bypass_blocked"] is True
    assert contract["economic_evaluation_executed"] is False
    assert contract["authority_effect"] == "NONE"
    assert contract["runtime_effect"] == "NONE"


def test_fixture_class_matrix_covers_required_classes() -> None:
    classes = {binding.fixture_class for binding in LEAD_LAG_FIXTURE_CLASS_BINDINGS}
    required = set(FixtureClassKind)
    assert classes == required
    assert len(classes) == 15


def test_productive_research_eval_path_executed_on_real_input(
    complete_binding: dict,
    ops_config: dict,
) -> None:
    panel = build_synthetic_panel_series_v0(bar_count=12)
    productive = execute_productive_lead_lag_research_eval_path_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        ops_config=ops_config,
        go_token=GO_TOKEN,
    )
    assert productive.executed is True
    assert productive.backtest_engine_signal_source == ENGINE_SIGNAL_SOURCE_MV2_REPLAY
    assert len(productive.records) == len(productive.bar_outcomes)
    assert len(productive.records) > 0


def test_parity_harness_fixture_matrix_executed() -> None:
    harness = execute_parity_harness_fixture_matrix_v0()
    assert harness.executed is True
    assert harness.canonical_fixtures_reused is True
    assert harness.assessment is not None
    assert harness.assessment.fixtures_complete is True


def test_harness_fixture_class_matrix_four_way_bound() -> None:
    matrix = evaluate_harness_fixture_class_matrix_v0()
    for binding in LEAD_LAG_FIXTURE_CLASS_BINDINGS:
        if binding.negative_path_only:
            assert matrix[binding.fixture_class.value]["negative_path_only"] is True
            continue
        item = matrix[binding.fixture_class.value]
        assert item["harness_executed"] is True
        assert item["four_way_bound"] is True


def test_research_eval_decision_parity_suite_pass(
    complete_binding: dict,
    ops_config: dict,
) -> None:
    panel = build_synthetic_panel_series_v0(bar_count=12)
    suite = evaluate_lead_lag_research_eval_decision_parity_suite_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        ops_config=ops_config,
        go_token=GO_TOKEN,
    )
    assert suite.suite_pass is True
    assert suite.productive_path_executed is True
    assert suite.parity_harness_path_executed is True
    assert suite.canonical_fixtures_reused is True
    assert suite.decision_field_parity_pass is True
    assert suite.reason_code_parity_pass is True
    assert suite.decision_order_parity_pass is True
    assert suite.deterministic_double_execution_pass is True
    assert suite.negative_path_fail_closed_pass is True
    assert suite.legacy_raw_signal_bypass_reachable is False
    assert suite.fixture_class_count == 15


def test_dispatch_wrapper_reports_suite_pass(complete_binding: dict) -> None:
    panel = build_synthetic_panel_series_v0(bar_count=12)
    payload = run_research_eval_decision_parity_contract_suite_dispatch_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
    )
    assert payload["research_eval_decision_parity_contract_suite_pass"] is True
    assert payload["productive_research_eval_path_executed"] is True
    assert payload["parity_harness_path_executed"] is True
    assert payload["canonical_fixtures_reused"] is True
    assert payload["legacy_raw_signal_bypass_reachable"] is False
    assert payload["backtest_engine_mv2_replay_signal_parity_pass"] is True
    assert payload["full_canonical_chain_wired"] is False
    assert payload["backtest_runtime_decision_parity_pass"] is False
    assert payload["economic_evaluation_executed"] is False


def test_negative_path_fail_closed() -> None:
    ok, reasons = evaluate_negative_path_fail_closed_v0()
    assert ok is True
    assert not reasons


def test_legacy_raw_engine_signal_bypass_rejected() -> None:
    ok, reasons = reject_legacy_raw_engine_signal_bypass_v0(
        backtest_engine_signal_source=ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
    )
    assert ok is False
    assert REASON_LEGACY_RAW_ENGINE_SIGNAL_BYPASS_BLOCKED in reasons


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


def test_digest_mismatch_fail_closed() -> None:
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


def test_productive_go_token_resolves_to_system_evidence_mv2() -> None:
    assert (
        resolve_productive_evaluation_path_mode_v0(go_token=GO_TOKEN)
        == SYSTEM_EVIDENCE_MV2_PATH_MODE
    )
    assert (
        resolve_productive_evaluation_path_mode_v0(go_token=GO_TOKEN) != LEGACY_RESEARCH_PATH_MODE
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


def test_contract_module_has_no_forbidden_runtime_imports() -> None:
    tree = ast.parse(CONTRACT_MODULE.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    for imp in imports:
        normalized = imp.replace(".", "/")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert not normalized.startswith(prefix.replace(".", "/"))


def test_real_path_invokes_canonical_adapter_not_mock(
    complete_binding: dict,
    ops_config: dict,
) -> None:
    panel = build_synthetic_panel_series_v0(bar_count=12)
    with patch(
        "src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0.run_mv2_research_backtest_wiring_v1",
    ) as mv2_call:
        result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
            repo_root=REPO_ROOT,
            panel_series=panel,
            versioned_binding=complete_binding,
            ops_config=ops_config,
            go_token=GO_TOKEN,
        )
        assert result.status is AdapterTerminalStatus.MV2_WIRING_BOUNDARY_COMPLETE
        assert mv2_call.called
        kwargs = mv2_call.call_args.kwargs
        assert kwargs["backtest_engine_signal_source"] == ENGINE_SIGNAL_SOURCE_MV2_REPLAY


def test_decision_records_serializable(complete_binding: dict, ops_config: dict) -> None:
    panel = build_synthetic_panel_series_v0(bar_count=12)
    productive = execute_productive_lead_lag_research_eval_path_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        ops_config=ops_config,
        go_token=GO_TOKEN,
    )
    payload = [record.to_dict() for record in productive.records]
    encoded = json.dumps(payload)
    assert len(encoded) > 0
