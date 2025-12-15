# tests/smoke/test_imports_smoke.py
"""
Smoke Test: Core Imports.

Stellt sicher, dass alle kritischen Module importierbar sind ohne Syntax-Fehler.
Kein vollständiger Test, nur Import-Sanity.
"""
import pytest


def test_core_imports():
    """Test dass Core-Module importierbar sind."""
    from src.core import environment, experiments, peak_config, risk


def test_live_imports():
    """Test dass Live-Module importierbar sind."""
    from src.live import (
        alerts,
        orders,
        risk_limits,
        safety,
    )


def test_execution_imports():
    """Test dass Execution-Module importierbar sind."""
    from src.execution import pipeline
    from src.orders import base, paper


def test_governance_imports():
    """Test dass Governance-Module importierbar sind."""
    from src.governance import go_no_go


def test_strategy_imports():
    """Test dass mindestens eine Strategie importierbar ist."""
    from src.strategies import ma_crossover


def test_backtest_imports():
    """Test dass Backtest-Engine importierbar ist."""
    from src.backtest import engine


def test_data_imports():
    """Test dass Data-Module importierbar sind."""
    from src.data import loader


def test_analytics_imports():
    """Test dass Analytics-Module importierbar sind."""
    from src.analytics import regimes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
