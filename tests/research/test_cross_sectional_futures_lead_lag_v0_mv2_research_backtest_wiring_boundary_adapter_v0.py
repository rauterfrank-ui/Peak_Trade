"""Contract tests for lead-lag v0 MV2 research backtest wiring boundary adapter v0."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.backtest.mv2_research_wiring_v1 import MV2ResearchWiringResultV1
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
    LEGACY_RESEARCH_PATH_MODE,
    SYSTEM_EVIDENCE_MV2_PATH_MODE,
    load_ops_evaluation_config_v0,
    load_versioned_hypothesis_binding_v0,
    run_mv2_system_evidence_wiring_dispatch_v0,
)
from src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0 import (
    GO_TOKEN,
    MV2_CANONICAL_CALLABLE,
    MV2_CANONICAL_OWNER,
    MV2_ENGINE_SIGNAL_STRATEGY_ID,
    REASON_GO_TOKEN_INVALID,
    REASON_MANDATORY_STATE_FILE_BINDING_MISSING,
    REASON_MANDATORY_STATE_FILE_BINDING_SECTION_MISSING,
    REASON_MANDATORY_STATE_FILE_PATH_UNREADABLE,
    REASON_MANDATORY_STATE_FILE_VALIDATION_FAILED,
    REASON_SCORE_SIDE_SHORTCUT_FORBIDDEN,
    AdapterTerminalStatus,
    MANDATORY_BOUNDARY_STATE_FILE_BINDING_KEYS,
    MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION,
    adapter_result_to_dict,
    extract_lead_lag_score_feature_rows_v0,
    mandatory_bindings_to_mv2_wiring_kwargs_v0,
    materialize_adapter_contract_v0,
    materialize_mv2_bars_with_score_features_v0,
    reject_score_to_final_side_shortcut_v0,
    resolve_mandatory_mv2_backtest_boundary_state_file_bindings_v0,
    run_lead_lag_mv2_research_backtest_wiring_boundary_v0,
    verify_adapter_go_token_v0,
    verify_binding_digests_unchanged_v0,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    SlotSide,
    run_cross_sectional_single_slot_orchestrator_v0,
    default_lead_lag_operator_binding_v0,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_score_v0 import (
    SCORE_FORMULA_VERSION,
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


def test_go_token_validation() -> None:
    ok, reasons = verify_adapter_go_token_v0(GO_TOKEN)
    assert ok is True
    assert reasons == ()
    bad, bad_reasons = verify_adapter_go_token_v0("INVALID")
    assert bad is False
    assert REASON_GO_TOKEN_INVALID in bad_reasons


def test_score_side_shortcut_rejected_in_system_evidence_mode() -> None:
    ok, reasons = reject_score_to_final_side_shortcut_v0(
        evaluation_path_mode=SYSTEM_EVIDENCE_MV2_PATH_MODE,
        resolved_side=SlotSide.LONG,
    )
    assert ok is False
    assert REASON_SCORE_SIDE_SHORTCUT_FORBIDDEN in reasons


def test_binding_digests_unchanged_pass(complete_binding: dict, ops_config: dict) -> None:
    ok, reasons = verify_binding_digests_unchanged_v0(
        complete_binding,
        expected_binding_digest=str(ops_config.get("binding_digest", "")),
        expected_dataset_digest=str(
            ops_config.get("cross_sectional_evaluation_binding_v1", {})
            .get("dataset_binding", {})
            .get("dataset_digest", "")
        ),
        expected_universe_digest=str(
            ops_config.get("cross_sectional_evaluation_binding_v1", {})
            .get("instrument_universe_binding", {})
            .get("universe_digest", "")
        ),
    )
    assert ok is True
    assert reasons == ()


def test_score_features_extracted_without_slot_side(complete_binding: dict) -> None:
    panel = build_synthetic_panel_series_v0()
    binding = default_lead_lag_operator_binding_v0(complete_binding)
    orchestrator = run_cross_sectional_single_slot_orchestrator_v0(
        binding=binding,
        panel_series=panel,
        score_formula_version=SCORE_FORMULA_VERSION,
    )
    rows = extract_lead_lag_score_feature_rows_v0(orchestrator)
    assert rows
    assert all(hasattr(row, "diffusion_score") for row in rows)
    assert all(not hasattr(row, "slot_side") for row in rows)


def test_mv2_bars_carry_score_features_not_final_side(complete_binding: dict) -> None:
    panel = build_synthetic_panel_series_v0()
    binding = default_lead_lag_operator_binding_v0(complete_binding)
    orchestrator = run_cross_sectional_single_slot_orchestrator_v0(
        binding=binding,
        panel_series=panel,
        score_formula_version=SCORE_FORMULA_VERSION,
    )
    rows = extract_lead_lag_score_feature_rows_v0(orchestrator)
    member = panel[0]
    bars = materialize_mv2_bars_with_score_features_v0(
        panel_member_bars=member.bars,
        score_rows=rows,
    )
    assert not bars.empty
    assert "lead_lag_diffusion_score" in bars.columns
    assert "momentum" in bars.columns
    assert "slot_side" not in bars.columns


def test_adapter_contract_declares_mv2_owner() -> None:
    contract = materialize_adapter_contract_v0()
    assert contract["canonical_mv2_owner"] == MV2_CANONICAL_OWNER
    assert contract["canonical_mv2_callable"] == MV2_CANONICAL_CALLABLE
    assert contract["score_to_final_side_shortcut_allowed"] is False
    assert contract["mandatory_boundary_state_file_binding_count"] == len(
        MANDATORY_BOUNDARY_STATE_FILE_BINDING_KEYS
    )
    assert contract["synthetic_defaults_allowed"] is False
    assert (
        MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION
        in contract["mandatory_boundary_state_file_binding_section"]
    )


def _ops_config_without_binding_key(ops_config: dict, key: str) -> dict:
    cfg = json.loads(json.dumps(ops_config))
    section = dict(cfg[MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION])
    section.pop(key, None)
    cfg[MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION] = section
    return cfg


def test_resolve_mandatory_bindings_from_ops_config(ops_config: dict) -> None:
    bindings, reasons = resolve_mandatory_mv2_backtest_boundary_state_file_bindings_v0(
        REPO_ROOT,
        ops_config,
    )
    assert reasons == ()
    assert bindings is not None
    kwargs = mandatory_bindings_to_mv2_wiring_kwargs_v0(bindings)
    assert set(kwargs) == {
        "capital_risk_sizing_state_file_binding",
        "canonical_order_intent_state_file_binding",
        "safety_kernel_state_file_binding",
        "killswitch_state_file_binding",
        "reconciliation_state_file_binding",
    }


@pytest.mark.parametrize("binding_key", MANDATORY_BOUNDARY_STATE_FILE_BINDING_KEYS)
def test_adapter_fail_closed_on_each_missing_mandatory_binding(
    complete_binding: dict,
    ops_config: dict,
    binding_key: str,
) -> None:
    panel = build_synthetic_panel_series_v0()
    cfg = _ops_config_without_binding_key(ops_config, binding_key)
    result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        ops_config=cfg,
        go_token=GO_TOKEN,
    )
    assert result.status is AdapterTerminalStatus.FAIL_CLOSED
    assert result.wiring_result is None
    assert any(
        code == f"{REASON_MANDATORY_STATE_FILE_BINDING_MISSING}:{binding_key}"
        for code in result.reason_codes
    )


def test_adapter_fail_closed_on_missing_binding_section(
    complete_binding: dict,
    ops_config: dict,
) -> None:
    panel = build_synthetic_panel_series_v0()
    cfg = json.loads(json.dumps(ops_config))
    cfg.pop(MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION, None)
    result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        ops_config=cfg,
        go_token=GO_TOKEN,
    )
    assert result.status is AdapterTerminalStatus.FAIL_CLOSED
    assert REASON_MANDATORY_STATE_FILE_BINDING_SECTION_MISSING in result.reason_codes


def test_adapter_fail_closed_on_unreadable_state_file_path(
    complete_binding: dict,
    ops_config: dict,
) -> None:
    panel = build_synthetic_panel_series_v0()
    cfg = json.loads(json.dumps(ops_config))
    section = dict(cfg[MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION])
    section["capital_risk_sizing"] = {
        "state_file_path": "config/research/does_not_exist/capital_risk_sizing.json",
        "expected_state_file_digest_ref": "0" * 64,
    }
    cfg[MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION] = section
    result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        ops_config=cfg,
        go_token=GO_TOKEN,
    )
    assert result.status is AdapterTerminalStatus.FAIL_CLOSED
    assert any(
        code.startswith(f"{REASON_MANDATORY_STATE_FILE_PATH_UNREADABLE}:capital_risk_sizing")
        for code in result.reason_codes
    )


def test_adapter_fail_closed_on_malformed_state_file_digest(
    complete_binding: dict,
    ops_config: dict,
) -> None:
    panel = build_synthetic_panel_series_v0()
    cfg = json.loads(json.dumps(ops_config))
    section = dict(cfg[MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION])
    crs_entry = dict(section["capital_risk_sizing"])
    crs_entry["expected_state_file_digest_ref"] = "0" * 64
    section["capital_risk_sizing"] = crs_entry
    cfg[MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION] = section
    result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        ops_config=cfg,
        go_token=GO_TOKEN,
    )
    assert result.status is AdapterTerminalStatus.FAIL_CLOSED
    assert any(
        code.startswith(REASON_MANDATORY_STATE_FILE_VALIDATION_FAILED)
        for code in result.reason_codes
    )


def test_canonical_mv2_owner_invoked(complete_binding: dict, ops_config: dict) -> None:
    panel = build_synthetic_panel_series_v0()
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
        result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
            repo_root=REPO_ROOT,
            panel_series=panel,
            versioned_binding=complete_binding,
            ops_config=ops_config,
            go_token=GO_TOKEN,
        )
    mv2_call.assert_called_once()
    _, kwargs = mv2_call.call_args
    assert kwargs["strategy_id"] == MV2_ENGINE_SIGNAL_STRATEGY_ID
    assert kwargs["capital_risk_sizing_state_file_binding"] is not None
    assert kwargs["canonical_order_intent_state_file_binding"] is not None
    assert kwargs["safety_kernel_state_file_binding"] is not None
    assert kwargs["killswitch_state_file_binding"] is not None
    assert kwargs["reconciliation_state_file_binding"] is not None
    assert result.status is AdapterTerminalStatus.MV2_WIRING_BOUNDARY_COMPLETE


def test_mv2_wiring_reaches_canonical_chain_components(
    complete_binding: dict, ops_config: dict
) -> None:
    panel = build_synthetic_panel_series_v0(bar_count=12)
    result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        ops_config=ops_config,
        go_token=GO_TOKEN,
    )
    assert result.status is AdapterTerminalStatus.MV2_WIRING_BOUNDARY_COMPLETE
    wiring = result.wiring_result
    assert wiring is not None
    assert len(wiring.bar_outcomes) > 0
    outcome = wiring.bar_outcomes[0]
    assert outcome.context.instrument_id == "inst-eth-usdt-perp"
    assert outcome.evidence.decision_outcome is not None
    assert isinstance(outcome.replay_pass, bool)
    assert outcome.capital_risk_sizing_backtest_state_file_evidence is not None
    assert outcome.canonical_order_intent_backtest_state_file_evidence is not None
    assert outcome.safety_kernel_backtest_state_file_evidence is not None
    assert outcome.killswitch_backtest_state_file_evidence is not None
    assert outcome.reconciliation_backtest_state_file_evidence is not None


def test_dispatch_wrapper_preserves_no_runtime_effect(
    complete_binding: dict,
    ops_config: dict,
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
        payload = run_mv2_system_evidence_wiring_dispatch_v0(
            repo_root=REPO_ROOT,
            panel_series=panel,
            versioned_binding=complete_binding,
            go_token=GO_TOKEN,
        )
    assert payload["evaluation_path_mode"] == SYSTEM_EVIDENCE_MV2_PATH_MODE
    assert payload["legacy_research_path_mode"] == LEGACY_RESEARCH_PATH_MODE
    assert payload["economic_evaluation_executed"] is False
    assert payload["authority_effect"] == "NONE"
    assert payload["runtime_effect"] == "NONE"


def test_adapter_fail_closed_on_invalid_go(complete_binding: dict, ops_config: dict) -> None:
    panel = build_synthetic_panel_series_v0()
    result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=complete_binding,
        ops_config=ops_config,
        go_token="INVALID",
    )
    assert result.status is AdapterTerminalStatus.FAIL_CLOSED
    assert result.wiring_result is None


def test_deterministic_double_adapter_materialization(
    complete_binding: dict, ops_config: dict
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
        first = adapter_result_to_dict(
            run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
                repo_root=REPO_ROOT,
                panel_series=panel,
                versioned_binding=complete_binding,
                ops_config=ops_config,
                go_token=GO_TOKEN,
            )
        )
        second = adapter_result_to_dict(
            run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
                repo_root=REPO_ROOT,
                panel_series=panel,
                versioned_binding=complete_binding,
                ops_config=ops_config,
                go_token=GO_TOKEN,
            )
        )
    assert first == second


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


def test_adapter_module_has_no_runtime_imports() -> None:
    imports = _collect_imports(ADAPTER_MODULE)
    for forbidden in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
        assert not any(item == forbidden or item.startswith(forbidden + ".") for item in imports)


def test_execution_module_still_has_no_runtime_imports() -> None:
    imports = _collect_imports(EXECUTION_MODULE)
    for forbidden in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
        assert not any(item == forbidden or item.startswith(forbidden + ".") for item in imports)
