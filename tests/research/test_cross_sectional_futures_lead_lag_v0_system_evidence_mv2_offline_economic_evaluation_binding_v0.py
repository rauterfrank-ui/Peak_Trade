"""Contract tests for lead-lag v0 SYSTEM_EVIDENCE_MV2 offline economic evaluation binding v0."""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import patch

import pytest

from src.backtest.mv2_research_wiring_v1 import MV2ResearchWiringResultV1
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
    ALLOWED_FULL_EVALUATION_GO_TOKENS,
    LEGACY_RESEARCH_PATH_MODE,
    SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN,
    SYSTEM_EVIDENCE_MV2_PATH_MODE,
    load_ops_evaluation_config_v0,
    load_versioned_hypothesis_binding_v0,
    materialize_system_evidence_mv2_offline_economic_evaluation_binding_v0,
    run_full_offline_economic_evaluation_v0,
    single_slot_backtest_from_mv2_wiring_v0,
    build_stage_wiring_status_v1,
)
from src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0 import (
    ALLOWED_ADAPTER_GO_TOKENS,
    GO_TOKEN as ADAPTER_IMPLEMENTATION_GO_TOKEN,
    verify_adapter_go_token_v0,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_scope_ratification_v0 import (
    materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_panel_economic_evaluation_wiring_v0 import (
    RobustnessStageResultsV0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
    build_synthetic_panel_series_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
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


def test_binding_contract_declares_mv2_path_mode() -> None:
    contract = materialize_system_evidence_mv2_offline_economic_evaluation_binding_v0()
    assert contract["evaluation_path_mode"] == SYSTEM_EVIDENCE_MV2_PATH_MODE
    assert contract["legacy_research_path_mode"] == LEGACY_RESEARCH_PATH_MODE
    assert contract["score_to_final_side_shortcut_allowed"] is False
    assert contract["system_evidence_mv2_binding_go_token"] == SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN


def test_binding_go_token_in_allowed_full_evaluation_tokens() -> None:
    assert SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN in ALLOWED_FULL_EVALUATION_GO_TOKENS


def test_adapter_accepts_binding_go_token() -> None:
    ok, reasons = verify_adapter_go_token_v0(SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN)
    assert ok is True
    assert reasons == ()
    assert SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN in ALLOWED_ADAPTER_GO_TOKENS
    assert ADAPTER_IMPLEMENTATION_GO_TOKEN in ALLOWED_ADAPTER_GO_TOKENS


def test_stage_wiring_uses_mv2_owner_in_system_evidence_mode() -> None:
    wiring = build_stage_wiring_status_v1(
        orchestrator_result=None,
        economic_policy_binding={},
        evaluation_path_mode=SYSTEM_EVIDENCE_MV2_PATH_MODE,
    )
    backtest_stage = next(item for item in wiring if item.stage_name == "OFFLINE_BACKTEST")
    assert "mv2_research_backtest_wiring_boundary_adapter_v0" in backtest_stage.owner


def test_single_slot_backtest_from_mv2_wiring_maps_stats() -> None:
    wiring = MV2ResearchWiringResultV1(
        instrument_id="inst-eth-usdt-perp",
        registry_snapshot=type("Snap", (), {"semantic_digest": "a" * 64})(),
        effective_cost_config=type("Cost", (), {"config_digest": "b" * 64})(),
        bar_outcomes=(),
        signals=type("S", (), {"empty": True})(),
        backtest_result=type(
            "BT",
            (),
            {
                "equity_curve": __import__("pandas").Series([10_000.0, 9_500.0]),
                "trades": None,
                "stats": {
                    "total_return": -0.05,
                    "total_trades": 2,
                    "turnover": 2.0,
                    "fee_drag": 10.0,
                    "slippage_impact": 5.0,
                },
            },
        )(),
        mv2_replay_signals=type("S2", (), {"empty": True})(),
        strategy_signal_provenance=type("P", (), {})(),
        mv2_replay_signal_digest="c" * 64,
        mv2_replay_nonzero_signal_count=0,
    )
    result = single_slot_backtest_from_mv2_wiring_v0(
        wiring_result=wiring,
        initial_cash=10_000.0,
        roundtrip_cost_bps=30.0,
    )
    assert result.net_return == pytest.approx(-0.05)
    assert result.trade_count == 2
    assert result.roundtrip_cost_bps == 30.0


def test_mv2_binding_evaluation_executes_on_synthetic_panel(
    complete_binding: dict,
) -> None:
    ratification = materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )
    panel = build_synthetic_panel_series_v0(bar_count=12)
    materialization = type(
        "MaterializationProxy",
        (),
        {
            "status": __import__(
                "src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0",
                fromlist=["MaterializationTerminalStatus"],
            ).MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE,
            "panel_data_digest": "b" * 64,
            "reason_codes": (),
        },
    )()
    with patch(
        "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0.verify_full_evaluation_precheck_v1",
        return_value=(True, (), materialization),
    ):
        with patch(
            "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0.load_panel_series_from_staging",
            return_value=((), {}),
        ):
            with patch(
                "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0.wire_robustness_stages_v0",
            ) as robustness_patch:
                robustness_patch.return_value = RobustnessStageResultsV0(
                    wiring_version="test.v0",
                    walk_forward_results=(),
                    monte_carlo_summary={"metric_quantiles": {"total_return": {"p50": -0.02}}},
                    stress_results={"scenarios": []},
                    parameter_sensitivity_status="BOUND",
                    authority_effect="NONE",
                )
                with patch(
                    "src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0.run_mv2_research_backtest_wiring_v1",
                ) as mv2_call:
                    mv2_call.return_value = MV2ResearchWiringResultV1(
                        instrument_id="inst-eth-usdt-perp",
                        registry_snapshot=type("Snap", (), {"semantic_digest": "a" * 64})(),
                        effective_cost_config=type("Cost", (), {"config_digest": "b" * 64})(),
                        bar_outcomes=(),
                        signals=type("S", (), {"empty": True})(),
                        backtest_result=type(
                            "BT",
                            (),
                            {
                                "equity_curve": __import__("pandas").Series(
                                    [10_000.0, 9_800.0],
                                    index=__import__("pandas").to_datetime(
                                        ["2024-01-01T00:00:00Z", "2024-06-01T00:00:00Z"],
                                        utc=True,
                                    ),
                                ),
                                "trades": None,
                                "stats": {
                                    "total_return": -0.02,
                                    "total_trades": 1,
                                    "turnover": 1.0,
                                },
                            },
                        )(),
                        mv2_replay_signals=type("S2", (), {"empty": True})(),
                        strategy_signal_provenance=type("P", (), {})(),
                        mv2_replay_signal_digest="c" * 64,
                        mv2_replay_nonzero_signal_count=0,
                    )
                    result = run_full_offline_economic_evaluation_v0(
                        repo_root=REPO_ROOT,
                        ratification=ratification,
                        staging_root=REPO_ROOT,
                        panel_series=panel,
                        versioned_binding=complete_binding,
                        go_token=SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN,
                    )
    assert result.economic_evaluation_executed is True
    assert result.backtest is not None
    assert any(
        "mv2_research_backtest_wiring_boundary_adapter_v0" in item.owner
        for item in result.stage_wiring
        if item.stage_name == "OFFLINE_BACKTEST"
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
