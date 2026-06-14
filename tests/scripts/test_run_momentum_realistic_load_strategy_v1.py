"""
run_momentum_realistic: canonical load_strategy() migration (offline, fail-closed).
"""

from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

TARGET_SCRIPT = project_root / "scripts/run_momentum_realistic.py"
MOMENTUM_KEY = "momentum_1h"


def _read_source() -> str:
    return TARGET_SCRIPT.read_text(encoding="utf-8")


def test_module_imports_without_main_side_effects() -> None:
    module = importlib.import_module("scripts.run_momentum_realistic")
    with patch.object(module, "main") as main_mock:
        importlib.reload(module)
    main_mock.assert_not_called()


def test_source_has_no_direct_momentum_module_import() -> None:
    tree = ast.parse(_read_source())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "src.strategies.momentum":
            pytest.fail("direct momentum module import remains")


def test_source_uses_load_strategy_and_registry_key() -> None:
    source = _read_source()
    assert "load_strategy" in source
    assert MOMENTUM_KEY in source
    assert "MOMENTUM_STRATEGY_KEY" in source
    assert "STRATEGY_REGISTRY" in source


def test_strategy_module_resolver_uses_registry_path() -> None:
    import scripts.run_momentum_realistic as momentum_script

    mod = momentum_script._strategy_module(MOMENTUM_KEY)
    assert mod.__name__ == "src.strategies.momentum"
    assert hasattr(mod, "get_strategy_description")


def test_get_strategy_description_equivalence_via_registry_module() -> None:
    import scripts.run_momentum_realistic as momentum_script
    from src.strategies.momentum import get_strategy_description as direct

    params = {
        "lookback_period": 20,
        "entry_threshold": 0.02,
        "exit_threshold": -0.01,
        "stop_pct": 0.025,
    }
    assert momentum_script._strategy_module(MOMENTUM_KEY).get_strategy_description(
        params
    ) == direct(params)


def test_load_strategy_momentum_key_resolves() -> None:
    from src.strategies import load_strategy

    assert callable(load_strategy(MOMENTUM_KEY))


def test_unknown_strategy_fails_closed() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_strategy_xyz")


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import scripts.run_momentum_realistic"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
