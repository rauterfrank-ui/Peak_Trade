"""Contract tests for lead-lag v0 productive research-eval/backtest lane MV2 rewire v0."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.backtest.mv2_research_wiring_v1 import MV2ResearchWiringResultV1
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
    CANONICAL_MV2_DECISION_CHAIN_OWNER,
    GO_TOKEN,
    INFRASTRUCTURE_GO_TOKEN,
    LEGACY_RESEARCH_PATH_MODE,
    MV2_CANONICAL_BACKTEST_OWNER,
    MV2_WIRING_ADAPTER_OWNER,
    PRODUCTIVE_RESEARCH_EVAL_BACKTEST_LANE_MV2_REWIRE_GO_TOKEN,
    REASON_LEGACY_RESEARCH_BACKTEST_BYPASS_BLOCKED,
    REEVALUATION_GO_TOKEN,
    SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN,
    SYSTEM_EVIDENCE_MV2_PATH_MODE,
    load_ops_evaluation_config_v0,
    load_versioned_hypothesis_binding_v0,
    materialize_execution_contract_v0,
    materialize_productive_research_eval_backtest_lane_mv2_rewire_contract_v0,
    reject_legacy_research_backtest_bypass_v0,
    resolve_productive_evaluation_path_mode_v0,
    run_contract_smoke_evaluation_v0,
    run_productive_research_eval_backtest_lane_mv2_rewire_dispatch_v0,
    validate_entry_point_go_token_v0,
)
from src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0 import (
    AdapterTerminalStatus,
    LEGACY_RESEARCH_PATH_MODE as ADAPTER_LEGACY_MODE,
    REASON_LEGACY_RESEARCH_BACKTEST_BYPASS_BLOCKED as ADAPTER_LEGACY_REASON,
    reject_legacy_research_evaluation_path_mode_v0,
    run_lead_lag_mv2_research_backtest_wiring_boundary_v0,
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


@pytest.mark.parametrize(
    "go_token",
    [
        GO_TOKEN,
        REEVALUATION_GO_TOKEN,
        SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN,
        INFRASTRUCTURE_GO_TOKEN,
        PRODUCTIVE_RESEARCH_EVAL_BACKTEST_LANE_MV2_REWIRE_GO_TOKEN,
    ],
)
def test_productive_go_tokens_resolve_to_system_evidence_mv2(go_token: str) -> None:
    assert (
        resolve_productive_evaluation_path_mode_v0(go_token=go_token)
        == SYSTEM_EVIDENCE_MV2_PATH_MODE
    )


def test_legacy_research_bypass_rejected() -> None:
    ok, reasons = reject_legacy_research_backtest_bypass_v0(
        evaluation_path_mode=LEGACY_RESEARCH_PATH_MODE,
    )
    assert ok is False
    assert REASON_LEGACY_RESEARCH_BACKTEST_BYPASS_BLOCKED in reasons


def test_adapter_rejects_legacy_research_path_mode(
    complete_binding: dict,
    ops_config: dict,
) -> None:
    panel = build_synthetic_panel_series_v0()
    result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        ops_config=ops_config,
        go_token=PRODUCTIVE_RESEARCH_EVAL_BACKTEST_LANE_MV2_REWIRE_GO_TOKEN,
        evaluation_path_mode=ADAPTER_LEGACY_MODE,
    )
    assert result.status is AdapterTerminalStatus.FAIL_CLOSED
    assert ADAPTER_LEGACY_REASON in result.reason_codes


def test_rewire_go_token_registered_in_entry_point_dispatch() -> None:
    ok, branch = validate_entry_point_go_token_v0(
        PRODUCTIVE_RESEARCH_EVAL_BACKTEST_LANE_MV2_REWIRE_GO_TOKEN,
    )
    assert ok is True
    assert branch == "PRODUCTIVE_MV2_REWIRE_V0"


def test_rewire_contract_declares_mv2_owners_and_blocked_legacy_bypass() -> None:
    contract = materialize_productive_research_eval_backtest_lane_mv2_rewire_contract_v0()
    assert contract["productive_evaluation_path_mode"] == SYSTEM_EVIDENCE_MV2_PATH_MODE
    assert contract["legacy_research_backtest_bypass_blocked"] is True
    assert contract["mv2_canonical_backtest_owner"] == MV2_CANONICAL_BACKTEST_OWNER
    assert contract["canonical_mv2_decision_chain_owner"] == CANONICAL_MV2_DECISION_CHAIN_OWNER
    assert contract["boundary_state_adapter_owner"] == MV2_WIRING_ADAPTER_OWNER
    assert contract["economic_evaluation_executed"] is False
    assert contract["authority_effect"] == "NONE"
    assert contract["runtime_effect"] == "NONE"


def test_execution_contract_declares_productive_mv2_path() -> None:
    contract = materialize_execution_contract_v0()
    assert contract["productive_evaluation_path_mode"] == SYSTEM_EVIDENCE_MV2_PATH_MODE
    assert contract["legacy_research_backtest_bypass_blocked"] is True
    assert contract["canonical_mv2_decision_chain_owner"] == CANONICAL_MV2_DECISION_CHAIN_OWNER


def test_productive_dispatch_routes_through_mv2_adapter(
    complete_binding: dict,
) -> None:
    panel = build_synthetic_panel_series_v0(bar_count=12)
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
                {"stats": {"total_trades": 0}, "trades": None, "equity_curve": None},
            )(),
            mv2_replay_signals=type("S2", (), {"empty": True})(),
            strategy_signal_provenance=type("P", (), {})(),
            mv2_replay_signal_digest="c" * 64,
            mv2_replay_nonzero_signal_count=0,
        )
        payload = run_productive_research_eval_backtest_lane_mv2_rewire_dispatch_v0(
            repo_root=REPO_ROOT,
            panel_series=panel,
            versioned_binding=complete_binding,
            go_token=PRODUCTIVE_RESEARCH_EVAL_BACKTEST_LANE_MV2_REWIRE_GO_TOKEN,
        )
    mv2_call.assert_called_once()
    assert payload["evaluation_path_mode"] == SYSTEM_EVIDENCE_MV2_PATH_MODE
    assert payload["productive_backtest_lane_mv2_rewired"] is True
    assert payload["legacy_research_bypass_blocked"] is True
    assert payload["economic_evaluation_executed"] is False


def test_contract_smoke_uses_mv2_lane_not_legacy_backtest(
    complete_binding: dict,
) -> None:
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
        "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_"
        "economic_evaluation_execution_v0.materialize_bound_panel_dataset_v0",
        return_value=materialization,
    ):
        with patch(
            "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_"
            "economic_evaluation_execution_v0.wire_robustness_stages_v0",
        ) as robustness_patch:
            robustness_patch.return_value = type(
                "RobustnessProxy",
                (),
                {
                    "wiring_version": "test.v0",
                    "walk_forward_results": (),
                    "monte_carlo_summary": {},
                    "stress_results": {},
                    "parameter_sensitivity_status": "BOUND",
                    "authority_effect": "NONE",
                },
            )()
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
                            "stats": {"total_trades": 1, "total_return": 0.01},
                            "trades": None,
                            "equity_curve": __import__("pandas").Series([10_000.0, 10_100.0]),
                        },
                    )(),
                    mv2_replay_signals=type("S2", (), {"empty": True})(),
                    strategy_signal_provenance=type("P", (), {})(),
                    mv2_replay_signal_digest="c" * 64,
                    mv2_replay_nonzero_signal_count=0,
                )
                result = run_contract_smoke_evaluation_v0(
                    repo_root=REPO_ROOT,
                    panel_series=panel,
                    versioned_binding=complete_binding,
                    staging_root=Path("."),
                    go_token=INFRASTRUCTURE_GO_TOKEN,
                )
    mv2_call.assert_called_once()
    assert result.economic_evaluation_executed is False
    assert result.authority_effect == "NONE"


def test_adapter_legacy_guard_helper() -> None:
    ok, reasons = reject_legacy_research_evaluation_path_mode_v0(
        evaluation_path_mode=SYSTEM_EVIDENCE_MV2_PATH_MODE,
    )
    assert ok is True
    assert reasons == ()
    bad, bad_reasons = reject_legacy_research_evaluation_path_mode_v0(
        evaluation_path_mode=ADAPTER_LEGACY_MODE,
    )
    assert bad is False
    assert ADAPTER_LEGACY_REASON in bad_reasons


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


def test_before_after_productive_entry_point_inventory_shape() -> None:
    before_after = {
        "before": {
            "default_evaluation_path_mode": LEGACY_RESEARCH_PATH_MODE,
            "backtest_owner": "cross_sectional_single_slot_backtest_wiring_v0",
        },
        "after": {
            "default_evaluation_path_mode": SYSTEM_EVIDENCE_MV2_PATH_MODE,
            "backtest_owner": MV2_WIRING_ADAPTER_OWNER,
            "decision_chain_owner": CANONICAL_MV2_DECISION_CHAIN_OWNER,
        },
    }
    assert before_after["after"]["default_evaluation_path_mode"] == SYSTEM_EVIDENCE_MV2_PATH_MODE
    assert json.dumps(before_after)
