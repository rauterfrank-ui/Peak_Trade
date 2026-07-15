# tests/trading/master_v2/test_strategy_suitability_agreement_static_contract_v1.py
"""Static contracts for Decision-D strategy suitability agreement binding."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MASTER_V2_ROOT = REPO_ROOT / "src" / "trading" / "master_v2"
BACKTEST_ROOT = REPO_ROOT / "src" / "backtest"

_OWNER_REPLAY = MASTER_V2_ROOT / "integrated_offline_trading_logic_replay_v1.py"
_OWNER_SUITABILITY = MASTER_V2_ROOT / "suitability_binding_v1.py"
_OWNER_MATERIAL = MASTER_V2_ROOT / "strategy_suitability_agreement_material_v1.py"
_ADAPTER = BACKTEST_ROOT / "strategy_signal_suitability_agreement_adapter_v1.py"
_WIRING = BACKTEST_ROOT / "mv2_research_wiring_v1.py"

_FORBIDDEN_BACKTEST_SIGNAL_TYPES = frozenset(
    {
        "StrategySignalBindingResultV1",
        "StrategySignalProvenanceV1",
    }
)
_FORBIDDEN_AUTHORITY_PATHS = (
    REPO_ROOT / "src" / "execution",
    REPO_ROOT / "src" / "risk",
    REPO_ROOT / "src" / "governance" / "capital_risk_sizing_v1.py",
)


def _imported_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[-1])
    return names


def _source_mentions(path: Path, needle: str) -> bool:
    return needle in path.read_text(encoding="utf-8")


def test_master_v2_does_not_import_backtest_signal_types() -> None:
    for path in MASTER_V2_ROOT.rglob("*.py"):
        imported = _imported_names(path)
        leaked = imported & _FORBIDDEN_BACKTEST_SIGNAL_TYPES
        assert not leaked, f"{path.relative_to(REPO_ROOT)} imports {sorted(leaked)}"


def test_canonical_total_decision_owner_unchanged() -> None:
    source = _OWNER_REPLAY.read_text(encoding="utf-8")
    assert "def run_integrated_offline_trading_logic_replay_v1(" in source
    assert "def build_integrated_offline_replay_input_v1(" in source
    assert source.count("def run_integrated_offline_trading_logic_replay_v1(") == 1


def test_no_parallel_decision_stage_symbol_introduced() -> None:
    for path in (_OWNER_REPLAY, _OWNER_SUITABILITY, _OWNER_MATERIAL, _ADAPTER, _WIRING):
        text = path.read_text(encoding="utf-8")
        assert "ParallelDecisionStage" not in text
        assert "evaluate_strategy_signal_parallel" not in text


def test_consumer_path_mentions_suitability_and_agreement_material() -> None:
    assert _source_mentions(_OWNER_SUITABILITY, "strategy_suitability_agreement_material")
    assert _source_mentions(_OWNER_SUITABILITY, "apply_strategy_suitability_agreement_material_v1")
    assert _source_mentions(_OWNER_REPLAY, "strategy_suitability_agreement_material")
    assert _source_mentions(
        _WIRING, "normalize_strategy_signal_to_suitability_agreement_material_v1"
    )
    assert _source_mentions(
        _ADAPTER, "normalize_strategy_signal_to_suitability_agreement_material_v1"
    )


def test_raw_signal_not_forwarded_to_entry_exit_or_position_inputs() -> None:
    replay_src = _OWNER_REPLAY.read_text(encoding="utf-8")
    assert "cycle_signal_value=" not in replay_src
    tree = ast.parse(replay_src)
    forbidden_kw = {"cycle_signal_value", "strategy_signal_value", "raw_strategy_signal"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            assert kw.arg not in forbidden_kw


def test_out_of_scope_owners_untouched_by_this_slice_files() -> None:
    decision_d_files = (
        _OWNER_REPLAY,
        _OWNER_SUITABILITY,
        _OWNER_MATERIAL,
        _ADAPTER,
        _WIRING,
    )
    for path in decision_d_files:
        for forbidden in _FORBIDDEN_AUTHORITY_PATHS:
            if forbidden.is_dir():
                assert forbidden not in path.parents and path != forbidden
            else:
                assert path != forbidden


def test_productive_direct_constructor_count_remains_one() -> None:
    tree = ast.parse(_OWNER_REPLAY.read_text(encoding="utf-8"))
    hits = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Name) and node.func.id == "IntegratedOfflineReplayInputV1")
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "IntegratedOfflineReplayInputV1"
            )
        )
    ]
    assert len(hits) == 1
