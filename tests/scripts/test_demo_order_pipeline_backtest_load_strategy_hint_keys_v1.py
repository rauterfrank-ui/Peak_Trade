"""
demo_order_pipeline_backtest: canonical load_strategy() hint-key migration (offline).
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.demo_order_pipeline_backtest as demo_script
from scripts.demo_order_pipeline_backtest import (
    ORDER_PIPELINE_DEMO_AVAILABLE_STRATEGY_KEYS,
    format_available_strategy_hints,
    get_available_strategy_hint_keys,
    main,
)
from src.strategies import STRATEGY_REGISTRY, load_strategy

TARGET_SCRIPT = project_root / "scripts/demo_order_pipeline_backtest.py"


def _read_source() -> str:
    return TARGET_SCRIPT.read_text(encoding="utf-8")


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(demo_script, "main") as main_mock:
        importlib.reload(demo_script)
    main_mock.assert_not_called()


def test_source_has_no_strategy_registry_import_or_access() -> None:
    tree = ast.parse(_read_source())
    imported = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module
        for alias in node.names
    }
    assert "STRATEGY_REGISTRY" not in imported
    assert "STRATEGY_REGISTRY" not in {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    }
    assert "STRATEGY_REGISTRY.keys" not in _read_source()


def test_source_uses_load_strategy() -> None:
    assert "load_strategy" in _read_source()


def test_source_declares_canonical_hint_key_tuple() -> None:
    assert "ORDER_PIPELINE_DEMO_AVAILABLE_STRATEGY_KEYS" in _read_source()


def test_source_has_no_strategy_map() -> None:
    assert "strategy_map" not in _read_source()


def test_source_has_no_parallel_strategy_registry_assignment() -> None:
    tree = ast.parse(_read_source())
    assigned_names = {
        node.targets[0].id
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    assert "STRATEGY_REGISTRY" not in assigned_names


def test_hint_keys_match_canonical_registry() -> None:
    hints = get_available_strategy_hint_keys()
    assert hints == sorted(STRATEGY_REGISTRY.keys())


def test_hint_keys_deterministically_sorted() -> None:
    hints = get_available_strategy_hint_keys()
    assert hints == sorted(hints)


def test_obsolete_non_canonical_names_not_in_hints() -> None:
    hints = get_available_strategy_hint_keys()
    assert "momentum" not in hints
    assert "bollinger" not in hints
    assert "momentum_1h" in hints
    assert "bollinger_bands" in hints


def test_format_available_strategy_hints_matches_registry() -> None:
    expected = ", ".join(sorted(STRATEGY_REGISTRY.keys()))
    assert format_available_strategy_hints() == expected


def test_hint_keys_preserve_canonical_tuple_order_semantics() -> None:
    assert tuple(sorted(ORDER_PIPELINE_DEMO_AVAILABLE_STRATEGY_KEYS)) == tuple(
        sorted(STRATEGY_REGISTRY.keys())
    )


def test_get_available_strategy_hint_keys_does_not_call_load_strategy() -> None:
    with patch.object(demo_script, "load_strategy") as load_mock:
        hints = get_available_strategy_hint_keys()
    load_mock.assert_not_called()
    assert hints == sorted(ORDER_PIPELINE_DEMO_AVAILABLE_STRATEGY_KEYS)


def test_format_available_strategy_hints_does_not_call_load_strategy() -> None:
    with patch.object(demo_script, "load_strategy") as load_mock:
        formatted = format_available_strategy_hints()
    load_mock.assert_not_called()
    assert formatted == ", ".join(sorted(ORDER_PIPELINE_DEMO_AVAILABLE_STRATEGY_KEYS))


def test_unknown_strategy_main_returns_non_zero_exit_with_hint_list() -> None:
    with (
        patch.object(demo_script, "load_strategy") as load_mock,
        patch.object(demo_script, "BacktestEngine") as engine_mock,
    ):
        load_mock.side_effect = ValueError("Unbekannte Strategie 'bad_name'")
        exit_code = main(["--strategy", "bad_name", "--bars", "50"])
    load_mock.assert_called_once_with("bad_name")
    engine_mock.assert_not_called()
    assert exit_code == 1


def test_unknown_strategy_fails_closed_via_load_strategy() -> None:
    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_strategy_xyz")


def test_resolve_strategy_no_network_calls() -> None:
    with patch("urllib.request.urlopen") as urlopen:
        load_strategy("ma_crossover")
    urlopen.assert_not_called()
