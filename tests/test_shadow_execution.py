#!/usr/bin/env python3
"""
Peak_Trade: Tests für Shadow-/Dry-Run-Execution (Phase 24)
==========================================================

Testet:
- ShadowOrderExecutor: Simulierte Order-Ausführung
- ShadowMarketContext: Preis-, Fee- und Slippage-Verwaltung
- ExecutionPipeline.for_shadow(): Factory-Methode
- CLI-Sanity: run_shadow_execution.py --help

WICHTIG: Alle Tests sind offline (keine externen Dienste)
         und testen nur simulierte (Shadow-)Ausführung.
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

# Projekt-Root zum Path hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Tests für ShadowMarketContext
# =============================================================================


class TestShadowMarketContext:
    """Tests für ShadowMarketContext."""

    def test_create_default_context(self):
        """Default-Context kann erstellt werden."""
        from src.orders.shadow import ShadowMarketContext

        ctx = ShadowMarketContext()

        assert ctx.fee_rate == 0.0005  # 5 bps default
        assert ctx.slippage_bps == 0.0
        assert ctx.base_currency == "EUR"
        assert ctx.prices == {}

    def test_set_and_get_price(self):
        """Preise können gesetzt und abgerufen werden."""
        from src.orders.shadow import ShadowMarketContext

        ctx = ShadowMarketContext()
        ctx.set_price("BTC/EUR", 50000.0)
        ctx.set_price("ETH/EUR", 3000.0)

        assert ctx.get_price("BTC/EUR") == 50000.0
        assert ctx.get_price("ETH/EUR") == 3000.0
        assert ctx.get_price("UNKNOWN") is None

    def test_set_price_validation(self):
        """Ungültige Preise werden abgelehnt."""
        from src.orders.shadow import ShadowMarketContext

        ctx = ShadowMarketContext()

        with pytest.raises(ValueError, match="muss > 0"):
            ctx.set_price("BTC/EUR", 0.0)

        with pytest.raises(ValueError, match="muss > 0"):
            ctx.set_price("BTC/EUR", -100.0)

    def test_get_fee_bps(self):
        """Fee in bps wird korrekt berechnet."""
        from src.orders.shadow import ShadowMarketContext

        ctx = ShadowMarketContext(fee_rate=0.001)  # 10 bps
        assert ctx.get_fee_bps() == 10.0

        ctx2 = ShadowMarketContext(fee_rate=0.0005)  # 5 bps
        assert ctx2.get_fee_bps() == 5.0

    def test_custom_configuration(self):
        """Benutzerdefinierte Konfiguration funktioniert."""
        from src.orders.shadow import ShadowMarketContext

        ctx = ShadowMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_rate=0.001,
            slippage_bps=5.0,
            base_currency="USD",
        )

        assert ctx.get_price("BTC/EUR") == 50000.0
        assert ctx.fee_rate == 0.001
        assert ctx.slippage_bps == 5.0
        assert ctx.base_currency == "USD"


# =============================================================================
# Tests für ShadowOrderExecutor
# =============================================================================


class TestShadowOrderExecutor:
    """Tests für ShadowOrderExecutor."""

    def test_create_executor_default(self):
        """Default-Executor kann erstellt werden."""
        from src.orders.shadow import ShadowOrderExecutor

        executor = ShadowOrderExecutor()

        assert executor.get_execution_count() == 0
        assert len(executor.get_order_log()) == 0

    def test_create_executor_with_context(self):
        """Executor mit benutzerdefiniertem Context erstellen."""
        from src.orders.shadow import ShadowMarketContext, ShadowOrderExecutor

        ctx = ShadowMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_rate=0.001,
        )
        executor = ShadowOrderExecutor(market_context=ctx)

        assert executor.get_price("BTC/EUR") == 50000.0
        assert executor.context.fee_rate == 0.001

    def test_execute_market_order_filled(self):
        """Market-Order wird korrekt gefüllt."""
        from src.orders.base import OrderRequest
        from src.orders.shadow import ShadowMarketContext, ShadowOrderExecutor

        ctx = ShadowMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_rate=0.0005,  # 5 bps
        )
        executor = ShadowOrderExecutor(market_context=ctx)

        order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
        )

        result = executor.execute_order(order)

        assert result.status == "filled"
        assert result.is_filled
        assert result.fill is not None
        assert result.fill.symbol == "BTC/EUR"
        assert result.fill.side == "buy"
        assert result.fill.quantity == 0.1
        assert result.fill.price == 50000.0
        assert result.metadata["mode"] == "shadow_run"
        assert result.metadata["shadow"] is True

    def test_execute_order_no_price(self):
        """Order ohne Preis wird rejected."""
        from src.orders.base import OrderRequest
        from src.orders.shadow import ShadowOrderExecutor

        executor = ShadowOrderExecutor()

        order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
        )

        result = executor.execute_order(order)

        assert result.status == "rejected"
        assert result.is_rejected
        assert "no_price_for_symbol" in result.reason
        assert result.metadata["mode"] == "shadow_run"

    def test_fee_calculation(self):
        """Fee wird korrekt berechnet."""
        from src.orders.base import OrderRequest
        from src.orders.shadow import ShadowMarketContext, ShadowOrderExecutor

        ctx = ShadowMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_rate=0.001,  # 10 bps = 0.1%
        )
        executor = ShadowOrderExecutor(market_context=ctx)

        order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=1.0,  # 1 BTC @ 50000 = 50000 notional
        )

        result = executor.execute_order(order)

        # Expected fee: 50000 * 0.001 = 50
        assert result.fill.fee == 50.0
        assert result.fill.fee_currency == "EUR"

    def test_slippage_buy_order(self):
        """Slippage bei Kauforder erhöht den Preis."""
        from src.orders.base import OrderRequest
        from src.orders.shadow import ShadowMarketContext, ShadowOrderExecutor

        ctx = ShadowMarketContext(
            prices={"BTC/EUR": 50000.0},
            slippage_bps=10.0,  # 10 bps = 0.1%
        )
        executor = ShadowOrderExecutor(market_context=ctx)

        order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
        )

        result = executor.execute_order(order)

        # Expected price: 50000 * (1 + 10/10000) = 50000 * 1.001 = 50050
        assert result.fill.price == pytest.approx(50050.0, rel=1e-9)

    def test_slippage_sell_order(self):
        """Slippage bei Verkaufsorder reduziert den Preis."""
        from src.orders.base import OrderRequest
        from src.orders.shadow import ShadowMarketContext, ShadowOrderExecutor

        ctx = ShadowMarketContext(
            prices={"BTC/EUR": 50000.0},
            slippage_bps=10.0,  # 10 bps = 0.1%
        )
        executor = ShadowOrderExecutor(market_context=ctx)

        order = OrderRequest(
            symbol="BTC/EUR",
            side="sell",
            quantity=0.1,
        )

        result = executor.execute_order(order)

        # Expected price: 50000 * (1 - 10/10000) = 50000 * 0.999 = 49950
        assert result.fill.price == 49950.0

    def test_limit_order_filled(self):
        """Limit-Order wird gefüllt wenn Bedingung erfüllt."""
        from src.orders.base import OrderRequest
        from src.orders.shadow import ShadowMarketContext, ShadowOrderExecutor

        ctx = ShadowMarketContext(prices={"BTC/EUR": 50000.0})
        executor = ShadowOrderExecutor(market_context=ctx)

        # Buy limit at 51000 when market is 50000 -> should fill at 50000
        order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
            order_type="limit",
            limit_price=51000.0,
        )

        result = executor.execute_order(order)

        assert result.status == "filled"
        assert result.fill.price == 50000.0  # Filled at better price

    def test_limit_order_rejected(self):
        """Limit-Order wird rejected wenn Bedingung nicht erfüllt."""
        from src.orders.base import OrderRequest
        from src.orders.shadow import ShadowMarketContext, ShadowOrderExecutor

        ctx = ShadowMarketContext(prices={"BTC/EUR": 50000.0})
        executor = ShadowOrderExecutor(market_context=ctx)

        # Buy limit at 49000 when market is 50000 -> should reject
        order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
            order_type="limit",
            limit_price=49000.0,
        )

        result = executor.execute_order(order)

        assert result.status == "rejected"
        assert "limit_not_met" in result.reason

    def test_execute_multiple_orders(self):
        """Mehrere Orders werden korrekt ausgeführt."""
        from src.orders.base import OrderRequest
        from src.orders.shadow import ShadowMarketContext, ShadowOrderExecutor

        ctx = ShadowMarketContext(prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0})
        executor = ShadowOrderExecutor(market_context=ctx)

        orders = [
            OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1),
            OrderRequest(symbol="ETH/EUR", side="sell", quantity=1.0),
            OrderRequest(symbol="UNKNOWN", side="buy", quantity=1.0),
        ]

        results = executor.execute_orders(orders)

        assert len(results) == 3
        assert results[0].status == "filled"
        assert results[1].status == "filled"
        assert results[2].status == "rejected"

        assert executor.get_execution_count() == 3

    def test_order_log(self):
        """Order-Log wird korrekt geführt."""
        from src.orders.base import OrderRequest
        from src.orders.shadow import ShadowMarketContext, ShadowOrderExecutor

        ctx = ShadowMarketContext(prices={"BTC/EUR": 50000.0})
        executor = ShadowOrderExecutor(market_context=ctx)

        order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1)
        executor.execute_order(order)
        executor.execute_order(order)

        log = executor.get_order_log()

        assert len(log) == 2
        assert log[0].request.symbol == "BTC/EUR"
        assert log[0].shadow_mode == "shadow_run"
        assert log[0].timestamp is not None

    def test_execution_summary(self):
        """Execution-Summary wird korrekt berechnet."""
        from src.orders.base import OrderRequest
        from src.orders.shadow import ShadowMarketContext, ShadowOrderExecutor

        ctx = ShadowMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_rate=0.001,  # 10 bps
        )
        executor = ShadowOrderExecutor(market_context=ctx)

        orders = [
            OrderRequest(symbol="BTC/EUR", side="buy", quantity=1.0),
            OrderRequest(symbol="BTC/EUR", side="sell", quantity=0.5),
            OrderRequest(symbol="UNKNOWN", side="buy", quantity=1.0),
        ]
        executor.execute_orders(orders)

        summary = executor.get_execution_summary()

        assert summary["total_orders"] == 3
        assert summary["filled_orders"] == 2
        assert summary["rejected_orders"] == 1
        assert summary["fill_rate"] == pytest.approx(2 / 3, rel=0.01)
        # Notional: 50000 + 25000 = 75000
        assert summary["total_notional"] == pytest.approx(75000.0, rel=0.01)
        # Fees: 75000 * 0.001 = 75
        assert summary["total_fees"] == pytest.approx(75.0, rel=0.01)
        assert summary["mode"] == "shadow_run"

    def test_reset(self):
        """Reset setzt Executor zurück."""
        from src.orders.base import OrderRequest
        from src.orders.shadow import ShadowMarketContext, ShadowOrderExecutor

        ctx = ShadowMarketContext(prices={"BTC/EUR": 50000.0})
        executor = ShadowOrderExecutor(market_context=ctx)

        executor.execute_order(OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1))
        executor.execute_order(OrderRequest(symbol="BTC/EUR", side="sell", quantity=0.1))

        assert executor.get_execution_count() == 2
        assert len(executor.get_order_log()) == 2

        executor.reset()

        assert executor.get_execution_count() == 0
        assert len(executor.get_order_log()) == 0


# =============================================================================
# Tests für Factory-Funktion
# =============================================================================


class TestCreateShadowExecutor:
    """Tests für create_shadow_executor()."""

    def test_create_with_defaults(self):
        """Factory mit Defaults erstellt gültigen Executor."""
        from src.orders.shadow import create_shadow_executor

        executor = create_shadow_executor()

        assert executor is not None
        assert executor.context.fee_rate == 0.0005
        assert executor.context.slippage_bps == 0.0

    def test_create_with_prices(self):
        """Factory mit Preisen funktioniert."""
        from src.orders.shadow import create_shadow_executor

        executor = create_shadow_executor(
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0}
        )

        assert executor.get_price("BTC/EUR") == 50000.0
        assert executor.get_price("ETH/EUR") == 3000.0

    def test_create_with_custom_params(self):
        """Factory mit benutzerdefinierten Parametern."""
        from src.orders.shadow import create_shadow_executor

        executor = create_shadow_executor(
            fee_rate=0.002,
            slippage_bps=15.0,
            base_currency="USD",
        )

        assert executor.context.fee_rate == 0.002
        assert executor.context.slippage_bps == 15.0
        assert executor.context.base_currency == "USD"


# =============================================================================
# Tests für ExecutionPipeline.for_shadow()
# =============================================================================


class TestExecutionPipelineForShadow:
    """Tests für ExecutionPipeline.for_shadow()."""

    def test_create_shadow_pipeline_default(self):
        """Shadow-Pipeline kann mit Defaults erstellt werden."""
        from src.execution.pipeline import ExecutionPipeline
        from src.orders.shadow import ShadowOrderExecutor

        pipeline = ExecutionPipeline.for_shadow()

        assert pipeline is not None
        assert isinstance(pipeline.executor, ShadowOrderExecutor)

    def test_create_shadow_pipeline_with_params(self):
        """Shadow-Pipeline mit Parametern erstellen."""
        from src.execution.pipeline import ExecutionPipeline
        from src.orders.shadow import ShadowOrderExecutor

        pipeline = ExecutionPipeline.for_shadow(
            fee_rate=0.001,
            slippage_bps=10.0,
        )

        assert isinstance(pipeline.executor, ShadowOrderExecutor)
        assert pipeline.executor.context.fee_rate == 0.001
        assert pipeline.executor.context.slippage_bps == 10.0

    def test_create_shadow_pipeline_with_context(self):
        """Shadow-Pipeline mit benutzerdefiniertem Context."""
        from src.execution.pipeline import ExecutionPipeline
        from src.orders.shadow import ShadowMarketContext, ShadowOrderExecutor

        ctx = ShadowMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_rate=0.002,
        )
        pipeline = ExecutionPipeline.for_shadow(market_context=ctx)

        assert isinstance(pipeline.executor, ShadowOrderExecutor)
        assert pipeline.executor.get_price("BTC/EUR") == 50000.0

    def test_shadow_pipeline_execute_from_signals(self):
        """Shadow-Pipeline kann Signale ausführen."""
        from src.execution.pipeline import ExecutionPipeline

        pipeline = ExecutionPipeline.for_shadow(fee_rate=0.0005)

        # Dummy-Signale und Preise
        index = pd.date_range("2024-01-01", periods=10, freq="1h", tz="UTC")
        signals = pd.Series([0, 1, 1, 0, -1, -1, 0, 1, 0, 0], index=index)
        prices = pd.Series([50000 + i * 100 for i in range(10)], index=index)

        # Preise im Context setzen
        for _ts, price in prices.items():
            pipeline.executor.context.set_price("BTC/EUR", price)

        results = pipeline.execute_from_signals(
            signals=signals,
            prices=prices,
            symbol="BTC/EUR",
        )

        # Es sollten einige Orders ausgeführt worden sein
        assert len(results) > 0

        # Alle sollten Shadow-Mode sein
        for result in results:
            assert result.metadata.get("mode") == "shadow_run"


# =============================================================================
# Tests für Module-Exports
# =============================================================================


class TestModuleExports:
    """Tests für korrekte Module-Exports."""

    def test_shadow_exports_from_orders(self):
        """Shadow-Klassen können aus src.orders importiert werden."""
        from src.orders import (
            EXECUTION_MODE_SHADOW,
            EXECUTION_MODE_SHADOW_RUN,
            ShadowMarketContext,
            ShadowOrderExecutor,
            ShadowOrderLog,
            create_shadow_executor,
        )

        assert ShadowOrderExecutor is not None
        assert ShadowMarketContext is not None
        assert ShadowOrderLog is not None
        assert create_shadow_executor is not None
        assert EXECUTION_MODE_SHADOW == "shadow"
        assert EXECUTION_MODE_SHADOW_RUN == "shadow_run"

    def test_run_type_shadow_run(self):
        """RUN_TYPE_SHADOW_RUN ist in experiments.py definiert."""
        from src.core.experiments import RUN_TYPE_SHADOW_RUN, VALID_RUN_TYPES

        assert RUN_TYPE_SHADOW_RUN == "shadow_run"
        assert RUN_TYPE_SHADOW_RUN in VALID_RUN_TYPES


# =============================================================================
# Tests für log_shadow_run()
# =============================================================================


class TestLogShadowRun:
    """Tests für log_shadow_run() Funktion."""

    def test_log_shadow_run_returns_run_id(self, tmp_path, monkeypatch):
        """log_shadow_run() gibt eine run_id zurück."""
        from src.core import experiments

        # Temporäres Verzeichnis für Experiments
        temp_experiments_dir = tmp_path / "experiments"
        temp_experiments_csv = temp_experiments_dir / "experiments.csv"

        monkeypatch.setattr(experiments, "EXPERIMENTS_DIR", temp_experiments_dir)
        monkeypatch.setattr(experiments, "EXPERIMENTS_CSV", temp_experiments_csv)

        run_id = experiments.log_shadow_run(
            strategy_key="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1h",
            stats={"total_return": 0.08, "sharpe": 1.1},
            tag="test_shadow",
        )

        assert run_id is not None
        assert len(run_id) > 0

        # CSV sollte existieren
        assert temp_experiments_csv.exists()

    def test_log_shadow_run_with_execution_summary(self, tmp_path, monkeypatch):
        """log_shadow_run() mit Execution-Summary funktioniert."""
        from src.core import experiments

        temp_experiments_dir = tmp_path / "experiments"
        temp_experiments_csv = temp_experiments_dir / "experiments.csv"

        monkeypatch.setattr(experiments, "EXPERIMENTS_DIR", temp_experiments_dir)
        monkeypatch.setattr(experiments, "EXPERIMENTS_CSV", temp_experiments_csv)

        execution_summary = {
            "total_orders": 42,
            "filled_orders": 40,
            "total_notional": 125000.0,
            "total_fees": 62.50,
        }

        run_id = experiments.log_shadow_run(
            strategy_key="rsi_strategy",
            symbol="ETH/EUR",
            timeframe="4h",
            stats={"total_return": 0.12},
            execution_summary=execution_summary,
        )

        assert run_id is not None


# =============================================================================
# CLI-Sanity-Tests
# =============================================================================


class TestCLISanity:
    """CLI-Sanity-Tests für run_shadow_execution.py."""

    def test_cli_help(self):
        """CLI --help funktioniert ohne Fehler."""
        script_path = PROJECT_ROOT / "scripts" / "run_shadow_execution.py"

        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "Shadow" in result.stdout or "shadow" in result.stdout
        assert "--strategy" in result.stdout
        assert "--config" in result.stdout

    def test_cli_version_info(self):
        """CLI zeigt relevante Optionen."""
        script_path = PROJECT_ROOT / "scripts" / "run_shadow_execution.py"

        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Sollte Shadow-spezifische Optionen haben
        assert "--fee-rate" in result.stdout
        assert "--slippage-bps" in result.stdout
        assert "--tag" in result.stdout


# =============================================================================
# Integration-Tests
# =============================================================================


class TestShadowExecutionIntegration:
    """Integrationstests für Shadow-Execution."""

    def test_full_shadow_execution_flow(self):
        """Vollständiger Shadow-Execution-Flow funktioniert."""
        from src.execution.pipeline import ExecutionPipeline
        from src.orders.base import OrderRequest

        # Pipeline erstellen
        pipeline = ExecutionPipeline.for_shadow(
            fee_rate=0.0005,
            slippage_bps=5.0,
        )

        # Preise setzen
        pipeline.executor.set_price("BTC/EUR", 50000.0)

        # Einzelne Order ausführen
        order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
            metadata={"strategy": "test"},
        )

        results = pipeline.execute_orders([order])

        assert len(results) == 1
        assert results[0].status == "filled"
        assert results[0].metadata["mode"] == "shadow_run"

        # Execution-Summary prüfen
        summary = pipeline.get_execution_summary()
        assert summary["total_orders"] == 1
        assert summary["filled_orders"] == 1

    def test_shadow_execution_no_network_calls(self):
        """Shadow-Execution macht keine Netzwerk-Calls."""
        from src.orders.base import OrderRequest
        from src.orders.shadow import ShadowMarketContext, ShadowOrderExecutor

        # Context mit Preisen
        ctx = ShadowMarketContext(prices={"BTC/EUR": 50000.0})
        executor = ShadowOrderExecutor(market_context=ctx)

        # Viele Orders ausführen (würde bei echten Calls langsam sein)
        orders = [
            OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01)
            for _ in range(100)
        ]

        # Sollte schnell sein (< 1 Sekunde)
        import time
        start = time.time()
        results = executor.execute_orders(orders)
        elapsed = time.time() - start

        assert len(results) == 100
        assert all(r.status == "filled" for r in results)
        assert elapsed < 1.0  # Sollte sehr schnell sein


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
