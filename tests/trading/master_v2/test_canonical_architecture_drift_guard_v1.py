"""Canonical Architecture Drift Guard v1 — three SSOT invariant rails.

Protects already-achieved invariants only:
  A) single productive canonical total decision owner
  B) single productive IntegratedOfflineReplayInputV1 constructor (builder)
  C) no productive direct strategy→position/trade/order authority bypass

Not an architecture freeze: Runbook-4.4.11 extensions and new strategy /
parameter work remain allowed while these rails hold.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.trading.master_v2._canonical_architecture_drift_guard_helpers_v1 import (
    REPO_ROOT,
    SRC_ROOT,
    assert_no_direct_strategy_authority_bypass,
    assert_single_canonical_total_decision_owner,
    assert_single_productive_replay_input_constructor,
    collect_competing_total_orchestrator_definitions,
    collect_direct_replay_input_constructions,
    collect_direct_strategy_authority_bypass_hits,
    collect_total_decision_owner_definitions,
    count_strategy_bypass_paths_by_kind,
)
from tests.trading.master_v2.test_canonical_replay_input_builder_ssot_contract_v1 import (
    unauthorized_direct_replay_input_constructions,
)

_AUTHORIZED_OWNER_REL = "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_OWNER_NAME = "run_integrated_offline_trading_logic_replay_v1"
_BUILDER_NAME = "build_integrated_offline_replay_input_v1"


# ---------------------------------------------------------------------------
# Positive rails — current productive tree
# ---------------------------------------------------------------------------


def test_invariant_a_single_canonical_total_decision_owner() -> None:
    sole = assert_single_canonical_total_decision_owner()
    assert sole.relative_path == _AUTHORIZED_OWNER_REL
    assert sole.kind == "sync"
    defs = collect_total_decision_owner_definitions(scan_root=SRC_ROOT, path_root=REPO_ROOT)
    assert len(defs) == 1
    competing = collect_competing_total_orchestrator_definitions(
        scan_root=SRC_ROOT,
        path_root=REPO_ROOT,
    )
    assert len(competing) == 1
    assert competing[0].function_name == _OWNER_NAME


def test_invariant_b_single_productive_replay_input_constructor() -> None:
    sole = assert_single_productive_replay_input_constructor()
    assert sole.relative_path == _AUTHORIZED_OWNER_REL
    assert sole.enclosing_function == _BUILDER_NAME
    hits = collect_direct_replay_input_constructions(scan_root=SRC_ROOT, path_root=REPO_ROOT)
    assert unauthorized_direct_replay_input_constructions(hits) == []
    assert len(hits) == 1


def test_invariant_c_no_direct_strategy_authority_bypass() -> None:
    assert_no_direct_strategy_authority_bypass()
    counts = count_strategy_bypass_paths_by_kind()
    assert counts["DIRECT_STRATEGY_TO_POSITION_PATH_COUNT"] == 0
    assert counts["DIRECT_STRATEGY_TO_ORDER_INTENT_PATH_COUNT"] == 0
    assert counts["SYSTEM_RELEVANT_DIRECT_STRATEGY_TO_TRADE_PATH_COUNT"] == 0


def test_drift_guard_documents_non_freeze_posture() -> None:
    """Light rail only — evolution inside the canonical chain stays allowed."""
    helper = (
        REPO_ROOT / "tests/trading/master_v2/_canonical_architecture_drift_guard_helpers_v1.py"
    ).read_text(encoding="utf-8")
    self_src = Path(__file__).read_text(encoding="utf-8")
    for text in (helper, self_src):
        assert "not an architecture freeze" in text.lower()
        assert "Runbook-4.4.11" in text or "runbook-4.4.11" in text.lower()


# ---------------------------------------------------------------------------
# Negative fixtures — tmp AST sources only (no productive mutation)
# ---------------------------------------------------------------------------


def test_negative_fixture_second_total_decision_owner_rejected(tmp_path: Path) -> None:
    (tmp_path / "authorized_owner.py").write_text(
        "def run_integrated_offline_trading_logic_replay_v1(replay_input):\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "rogue_second_owner.py").write_text(
        "def run_integrated_offline_trading_logic_replay_v1(replay_input):\n    return None\n",
        encoding="utf-8",
    )
    hits = collect_total_decision_owner_definitions(scan_root=tmp_path, path_root=tmp_path)
    assert len(hits) == 2
    with pytest.raises(AssertionError, match="INVARIANT_A_TOTAL_DECISION_OWNER|must be 1"):
        assert_single_canonical_total_decision_owner(
            scan_root=tmp_path,
            path_root=tmp_path,
        )


def test_negative_fixture_competing_partial_stage_orchestrator_rejected(
    tmp_path: Path,
) -> None:
    """Competing orchestrator with a new name still fails via partial-stage composition."""
    owner_rel = Path(_AUTHORIZED_OWNER_REL)
    owner_dir = tmp_path.joinpath(*owner_rel.parts[:-1])
    owner_dir.mkdir(parents=True)
    (owner_dir / owner_rel.name).write_text(
        "def run_integrated_offline_trading_logic_replay_v1(replay_input):\n"
        "    evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1()\n"
        "    evaluate_survival_assessment_v1()\n"
        "    evaluate_suitability_binding_v1()\n"
        "    evaluate_double_play_composition_matrix_v1()\n"
        "    evaluate_double_play_entry_exit_policy_v0()\n"
        "    return None\n",
        encoding="utf-8",
    )
    rogue = tmp_path / "src" / "trading" / "master_v2" / "rogue_total_orchestrator_v0.py"
    rogue.parent.mkdir(parents=True, exist_ok=True)
    rogue.write_text(
        "def run_parallel_total_decision_v0(replay_input):\n"
        "    evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1()\n"
        "    evaluate_survival_assessment_v1()\n"
        "    evaluate_suitability_binding_v1()\n"
        "    evaluate_double_play_composition_matrix_v1()\n"
        "    return None\n",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="INVARIANT_A_TOTAL_DECISION_OWNER"):
        assert_single_canonical_total_decision_owner(
            scan_root=tmp_path / "src",
            path_root=tmp_path,
        )


def test_negative_fixture_second_replay_input_constructor_rejected(tmp_path: Path) -> None:
    rogue = tmp_path / "rogue_replay_input_constructor_v0.py"
    rogue.write_text(
        "def build_rogue_input():\n    return IntegratedOfflineReplayInputV1()\n",
        encoding="utf-8",
    )
    hits = collect_direct_replay_input_constructions(scan_root=tmp_path, path_root=tmp_path)
    assert len(hits) == 1
    assert unauthorized_direct_replay_input_constructions(hits)
    with pytest.raises(AssertionError, match="INVARIANT_B_REPLAY_INPUT_CONSTRUCTOR"):
        assert_single_productive_replay_input_constructor(
            scan_root=tmp_path,
            path_root=tmp_path,
        )


def test_negative_fixture_strategy_signal_to_position_bypass_rejected(
    tmp_path: Path,
) -> None:
    rogue = tmp_path / "rogue_strategy_position_bypass_v0.py"
    rogue.write_text(
        "from somewhere import StrategySignalBindingResultV1\n"
        "\n"
        "def build_positions_from_raw_strategy_signals(binding: StrategySignalBindingResultV1):\n"
        "    return pack_portfolio(position_series=binding.signals)\n",
        encoding="utf-8",
    )
    hits = collect_direct_strategy_authority_bypass_hits(scan_root=tmp_path, path_root=tmp_path)
    assert hits
    assert any(h.kind == "position" for h in hits)
    with pytest.raises(AssertionError, match="INVARIANT_C_STRATEGY_AUTHORITY_BYPASS"):
        assert_no_direct_strategy_authority_bypass(
            scan_root=tmp_path,
            path_root=tmp_path,
        )


def test_negative_fixture_strategy_signal_to_order_intent_bypass_rejected(
    tmp_path: Path,
) -> None:
    rogue = tmp_path / "rogue_strategy_order_bypass_v0.py"
    rogue.write_text(
        "def emit_orders_from_strategy_binding(binding):\n"
        "    signals = binding.signals\n"
        "    return OrderIntentV1(side=signals.iloc[-1])\n"
        "\n"
        "StrategySignalBindingResultV1  # marker kept for source classification\n",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="INVARIANT_C_STRATEGY_AUTHORITY_BYPASS"):
        assert_no_direct_strategy_authority_bypass(
            scan_root=tmp_path,
            path_root=tmp_path,
        )


def test_negative_fixture_strategy_to_run_realistic_authority_bypass_rejected(
    tmp_path: Path,
) -> None:
    rogue = tmp_path / "rogue_strategy_engine_bypass_v0.py"
    rogue.write_text(
        "def run_system_evidence_from_configured_strategy(engine, bars):\n"
        "    binding = execute_configured_strategy_signal_series_v1(bars)\n"
        "    return engine.run_realistic(signals=binding.signals)\n",
        encoding="utf-8",
    )
    hits = collect_direct_strategy_authority_bypass_hits(scan_root=tmp_path, path_root=tmp_path)
    assert any(h.kind == "authoritative_engine" for h in hits)
    with pytest.raises(AssertionError, match="INVARIANT_C_STRATEGY_AUTHORITY_BYPASS"):
        assert_no_direct_strategy_authority_bypass(
            scan_root=tmp_path,
            path_root=tmp_path,
        )
