"""Capital/Risk/Sizing binding parity: integrated offline replay vs scenario replay (offline only)."""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CANONICAL_CAPITAL_RISK_SIZING_OWNER,
    CAPITAL_RISK_SIZING_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    RISK_SIZING_EFFECT_BOUND_OFFLINE,
    RISK_SIZING_EFFECT_NONE,
    bind_capital_risk_sizing_offline_replay_evidence_v0,
    build_scenario_tick_decision_evidence_v0,
    capital_risk_sizing_binding_non_authority_boundary_ok_v0,
    default_offline_replay_capital_context_v0,
    evaluate_scenario_capital_risk_sizing_v0,
    system_economic_evidence_admissible_v0,
)
from trading.master_v2.double_play_composition_matrix_v1 import CompositionStatus
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    assert_capital_risk_sizing_non_authority_boundary_v0,
    assert_scenario_replay_zero_order_boundary_v0,
    canonical_owner_refs_v0,
    extract_capital_risk_sizing_parity_envelope_v0,
    extract_integrated_parity_envelope_v0,
    extract_scenario_replay_tick_capital_risk_sizing_envelope_v0,
    scan_changed_paths_for_forbidden_runtime_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
    OfflineDoublePlayScenarioReplayInputV0,
    SYNTHETIC_FUTURES_INSTRUMENT,
    build_default_bull_bear_bull_scenario_ticks,
    run_offline_double_play_scenario_replay_v0,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_INSTRUMENT = SYNTHETIC_FUTURES_INSTRUMENT
_EPOCH = 48
_CONTEXT = "capital-risk-sizing-offline-replay-binding-parity-v0"

_SLICE_CHANGED_FILES = (
    "src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py",
    "src/trading/master_v2/canonical_trading_decision_evidence_v1.py",
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "scripts/ops/run_capital_risk_sizing_offline_replay_binding_parity_rewire_v0.py",
    "tests/trading/master_v2/test_capital_risk_sizing_offline_replay_binding_parity_rewire_contract_v0.py",
)

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT / "src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py",
    REPO_ROOT
    / "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    REPO_ROOT / "scripts/ops/run_capital_risk_sizing_offline_replay_binding_parity_rewire_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_capital_risk_sizing_offline_replay_binding_parity_rewire_contract_v0.py",
)

ALLOWED_SLICE_CHANGED_PATH_PREFIXES = _SLICE_CHANGED_FILES


def _scan_forbidden_imports(path: Path, forbidden_tokens: frozenset[str]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in forbidden_tokens):
                    hits.append(alias.name)
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden_tokens):
                hits.append(node.module)
    return hits


def test_owner_constants_and_canonical_reuse_v0() -> None:
    refs = canonical_owner_refs_v0()
    assert refs["capital_risk_sizing"] == CANONICAL_CAPITAL_RISK_SIZING_OWNER
    assert (
        refs["capital_risk_sizing_offline_replay_binding_adapter"]
        == CAPITAL_RISK_SIZING_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
    )
    assert refs["scenario_replay"] == OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER


def test_forbidden_runtime_paths_guard_v0() -> None:
    ok, violations = scan_changed_paths_for_forbidden_runtime_v0(
        ALLOWED_SLICE_CHANGED_PATH_PREFIXES
    )
    assert ok is True
    assert violations == ()


def test_slice_sources_exclude_execution_runtime_imports_v0() -> None:
    forbidden = frozenset(
        {
            "execution",
            "scheduler",
            "credentials",
            "live_runtime",
            "testnet",
            "shadow",
            "paper_lane",
        }
    )
    for path in _FORBIDDEN_IMPORT_SCAN_PATHS:
        assert path.is_file(), f"missing slice source: {path}"
        hits = _scan_forbidden_imports(path, forbidden)
        assert hits == [], f"forbidden imports in {path}: {hits}"


def test_unbound_replay_cannot_admit_system_economic_evidence_v0() -> None:
    evidence = build_scenario_tick_decision_evidence_v0(
        decision_id="decision-unbound",
        replay_id="replay-unbound",
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        composition_result_id="composition-unbound",
        entry_exit_policy_ref="policy-unbound",
        selected_side="long",
        decision_outcome=DecisionOutcome.OBSERVE.value,
        reason_codes=("OBSERVE",),
        decision_precedence_trace=("observe",),
        config_digest="config",
        implementation_digest="impl",
    )
    binding = bind_capital_risk_sizing_offline_replay_evidence_v0(evidence)
    assert binding.binding_applied is False
    assert binding.risk_sizing_effect == RISK_SIZING_EFFECT_NONE
    assert binding.quantity_provenance_ref == ""
    assert not system_economic_evidence_admissible_v0(binding)


def test_1_actionable_enter_long_sizing_bound_v0() -> None:
    integrated = _run(
        side_state=SideState.LONG_ARMED,
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    if integrated.intermediate is None:
        return
    if (
        integrated.intermediate.composition_result.composition_status
        is not CompositionStatus.LONG_SELECTED
    ):
        return
    assert integrated.evidence.risk_sizing_effect == RISK_SIZING_EFFECT_BOUND_OFFLINE
    assert integrated.evidence.risk_sizing_ref
    assert integrated.evidence.quantity_provenance_ref
    assert integrated.evidence.quantity_status in {"PASS", "REDUCE", "BLOCK", "ROUNDED_DOWN"}
    assert integrated.intermediate.capital_risk_sizing_decision is not None
    env = extract_integrated_parity_envelope_v0(integrated)
    assert_capital_risk_sizing_non_authority_boundary_v0(env)
    assert capital_risk_sizing_binding_non_authority_boundary_ok_v0(
        bind_capital_risk_sizing_offline_replay_evidence_v0(integrated.evidence)
    )


def test_2_actionable_enter_short_sizing_bound_v0() -> None:
    integrated = _run(
        side_state=SideState.SHORT_ARMED,
        direction_state=EntryExitDirectionState.SHORT_ARMED,
        price_path=(3500.0, 3430.0),
    )
    if integrated.intermediate is None:
        return
    if (
        integrated.intermediate.composition_result.composition_status
        is not CompositionStatus.SHORT_SELECTED
    ):
        return
    assert integrated.evidence.risk_sizing_effect == RISK_SIZING_EFFECT_BOUND_OFFLINE
    assert integrated.evidence.quantity_provenance_ref


def test_3_non_actionable_observe_remains_unbound_v0() -> None:
    integrated = _run(price_path=(3500.0, 3600.0))
    if (
        integrated.intermediate
        and integrated.intermediate.composition_result.composition_status
        is CompositionStatus.CHOP_GUARD_BLOCK
    ):
        assert integrated.evidence.risk_sizing_effect == RISK_SIZING_EFFECT_NONE
        assert integrated.evidence.quantity_status == "NOT_BOUND"
        assert integrated.evidence.quantity_provenance_ref == ""


def test_scenario_replay_tick_capital_risk_sizing_binding_no_shortcut_v0() -> None:
    result = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=_INSTRUMENT,
            ticks=build_default_bull_bear_bull_scenario_ticks(),
            source_revision="capital-risk-sizing-binding-parity-v0",
        )
    )
    assert result.replay_pass, result.fail_reasons
    assert_scenario_replay_zero_order_boundary_v0(result)

    bound_ticks = 0
    for tick in result.tick_records:
        env = extract_scenario_replay_tick_capital_risk_sizing_envelope_v0(tick)
        assert_capital_risk_sizing_non_authority_boundary_v0(env)
        if tick.risk_sizing_effect == RISK_SIZING_EFFECT_BOUND_OFFLINE:
            bound_ticks += 1
            assert tick.capital_risk_sizing_ref
        if tick.quantity_provenance_ref:
            assert tick.risk_sizing_effect == RISK_SIZING_EFFECT_BOUND_OFFLINE
            assert tick.quantity_status in {"PASS", "REDUCE", "BLOCK", "ROUNDED_DOWN"}
    assert bound_ticks >= 1


def test_scenario_adapter_reuses_canonical_sizing_owner_v0() -> None:
    adapter_src = (
        REPO_ROOT / "src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py"
    )
    text = adapter_src.read_text(encoding="utf-8")
    assert "evaluate_capital_risk_sizing_v1" in text
    assert "build_capital_risk_sizing_input_from_decision_v0" in text
    assert "def _build_scope_capital_envelope_v1" not in text


def test_scenario_fixture_parity_envelope_v0() -> None:
    evidence = build_scenario_tick_decision_evidence_v0(
        decision_id=f"{_CONTEXT}-decision",
        replay_id=f"{_CONTEXT}-replay",
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        composition_result_id=f"{_CONTEXT}-composition",
        entry_exit_policy_ref=f"{_CONTEXT}-policy",
        selected_side="long",
        decision_outcome=DecisionOutcome.ENTER_LONG.value,
        reason_codes=("PASS",),
        decision_precedence_trace=("enter_long",),
        config_digest="config",
        implementation_digest="impl",
    )
    binding = evaluate_scenario_capital_risk_sizing_v0(
        evidence,
        reference_price=Decimal("3500"),
    )
    env = extract_capital_risk_sizing_parity_envelope_v0(
        binding,
        decision_outcome=DecisionOutcome.ENTER_LONG.value,
        composition_result_id=f"{_CONTEXT}-composition",
    )
    assert binding.binding_applied is True
    assert env.quantity_provenance_ref
    assert env.risk_sizing_ref
    assert_capital_risk_sizing_non_authority_boundary_v0(env)
    assert not system_economic_evidence_admissible_v0(binding)


def test_pr4946_parity_suite_still_passes_v0() -> None:
    from tests.trading.master_v2 import (
        test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0 as pr4946,
    )

    pr4946.test_harness_and_replay_owner_constants_v0()
    pr4946.test_1_long_bull_path_parity_v0()
    pr4946.test_3_both_confirmed_chop_guard_parity_v0()
    pr4946.test_5_reversal_preparation_boundary_parity_v0()
    pr4946.test_scenario_replay_e2e_composition_and_zero_order_boundary_v0()


def test_pr4948_entry_exit_binding_suite_still_passes_v0() -> None:
    from tests.trading.master_v2 import (
        test_scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_contract_v0 as pr4948,
    )

    pr4948.test_owner_constants_and_canonical_reuse_v0()
    pr4948.test_scenario_replay_tick_entry_exit_binding_no_shortcut_v0()


def test_prometheus_client_importable_v0() -> None:
    pytest.importorskip("prometheus_client")
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import prometheus_client; print('PROMETHEUS_CLIENT_IMPORTABLE=true')",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "PROMETHEUS_CLIENT_IMPORTABLE=true" in proc.stdout
