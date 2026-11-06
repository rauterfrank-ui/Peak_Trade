# -*- coding: utf-8 -*-
# tests/test_execution_reporting.py
"""
Tests fuer src/reporting/execution_reports.py (Phase 16D).

Testet:
- ExecutionStats Dataclass
- from_execution_logs()
- from_execution_results()
- from_backtest_result()
- format_execution_stats()
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List


class TestExecutionStatsDataclass:
    """Tests fuer ExecutionStats Dataclass."""

    def test_default_values(self):
        """ExecutionStats hat korrekte Defaults."""
        from src.reporting.execution_reports import ExecutionStats

        stats = ExecutionStats()

        assert stats.n_orders == 0
        assert stats.n_fills == 0
        assert stats.n_rejected == 0
        assert stats.fill_rate == 0.0
        assert stats.total_fees == 0.0
        assert stats.total_notional == 0.0
        assert stats.symbol is None
        assert stats.run_id is None

    def test_custom_values(self):
        """ExecutionStats akzeptiert Custom-Werte."""
        from src.reporting.execution_reports import ExecutionStats

        stats = ExecutionStats(
            n_orders=100,
            n_fills=95,
            n_rejected=5,
            total_fees=50.0,
            total_notional=10000.0,
            symbol="BTC/EUR",
            run_id="test_run",
        )

        assert stats.n_orders == 100
        assert stats.n_fills == 95
        assert stats.n_rejected == 5
        assert stats.total_fees == 50.0
        assert stats.total_notional == 10000.0
        assert stats.symbol == "BTC/EUR"
        assert stats.run_id == "test_run"

    def test_fill_rate_auto_calculation(self):
        """Fill-Rate wird automatisch berechnet."""
        from src.reporting.execution_reports import ExecutionStats

        stats = ExecutionStats(
            n_orders=100,
            n_fills=80,
        )

        assert stats.fill_rate == 0.8

    def test_avg_fee_auto_calculation(self):
        """Durchschnittliche Fees werden automatisch berechnet."""
        from src.reporting.execution_reports import ExecutionStats

        stats = ExecutionStats(
            n_orders=10,
            n_fills=10,
            total_fees=50.0,
        )

        assert stats.avg_fee_per_order == 5.0
        assert stats.avg_fee_per_fill == 5.0

    def test_fee_rate_bps_calculation(self):
        """Fee-Rate in bps wird korrekt berechnet."""
        from src.reporting.execution_reports import ExecutionStats

        stats = ExecutionStats(
            total_fees=10.0,
            total_notional=10000.0,
        )

        # 10 / 10000 * 10000 = 10 bps
        assert stats.fee_rate_bps == 10.0

    def test_trading_period_calculation(self):
        """Trading-Period wird aus Timestamps berechnet."""
        from src.reporting.execution_reports import ExecutionStats

        first = datetime(2024, 1, 1, 0, 0, 0)
        last = datetime(2024, 1, 8, 0, 0, 0)  # 7 Tage spaeter

        stats = ExecutionStats(
            first_trade_time=first,
            last_trade_time=last,
        )

        assert stats.trading_period_days == 7.0

    def test_to_dict(self):
        """to_dict() gibt korrektes Dictionary zurueck."""
        from src.reporting.execution_reports import ExecutionStats

        stats = ExecutionStats(
            n_orders=50,
            n_fills=45,
            symbol="ETH/EUR",
        )

        d = stats.to_dict()

        assert isinstance(d, dict)
        assert d["n_orders"] == 50
        assert d["n_fills"] == 45
        assert d["symbol"] == "ETH/EUR"
        assert "fill_rate" in d
        assert "total_fees" in d


class TestFromExecutionLogs:
    """Tests fuer from_execution_logs()."""

    def test_empty_logs(self):
        """Leere Logs ergeben leere Stats."""
        from src.reporting.execution_reports import from_execution_logs

        stats = from_execution_logs([])

        assert stats.n_orders == 0
        assert stats.n_fills == 0

    def test_single_log(self):
        """Einzelner Log wird korrekt verarbeitet."""
        from src.reporting.execution_reports import from_execution_logs

        logs = [
            {
                "total_orders": 10,
                "filled_orders": 8,
                "rejected_orders": 2,
                "total_fees": 5.0,
                "total_notional": 1000.0,
                "symbol": "BTC/EUR",
                "run_id": "test123",
            }
        ]

        stats = from_execution_logs(logs)

        assert stats.n_orders == 10
        assert stats.n_fills == 8
        assert stats.n_rejected == 2
        assert stats.total_fees == 5.0
        assert stats.total_notional == 1000.0
        assert stats.symbol == "BTC/EUR"
        assert stats.run_id == "test123"
        assert stats.fill_rate == 0.8

    def test_multiple_logs_aggregation(self):
        """Mehrere Logs werden aggregiert."""
        from src.reporting.execution_reports import from_execution_logs

        logs = [
            {
                "total_orders": 10,
                "filled_orders": 8,
                "rejected_orders": 2,
                "total_fees": 5.0,
                "total_notional": 1000.0,
            },
            {
                "total_orders": 20,
                "filled_orders": 18,
                "rejected_orders": 2,
                "total_fees": 10.0,
                "total_notional": 2000.0,
            },
        ]

        stats = from_execution_logs(logs)

        assert stats.n_orders == 30
        assert stats.n_fills == 26
        assert stats.n_rejected == 4
        assert stats.total_fees == 15.0
        assert stats.total_notional == 3000.0

    def test_timestamp_parsing(self):
        """Timestamps aus Logs werden korrekt geparst."""
        from src.reporting.execution_reports import from_execution_logs

        logs = [
            {
                "total_orders": 5,
                "filled_orders": 5,
                "timestamp": "2024-01-15T10:30:00",
            }
        ]

        stats = from_execution_logs(logs)

        assert stats.first_trade_time is not None
        assert stats.first_trade_time.year == 2024
        assert stats.first_trade_time.month == 1
        assert stats.first_trade_time.day == 15

    def test_missing_fields_handled(self):
        """Fehlende Felder werden graceful behandelt."""
        from src.reporting.execution_reports import from_execution_logs

        logs = [
            {
                "total_orders": 5,
                # filled_orders fehlt
            }
        ]

        stats = from_execution_logs(logs)

        assert stats.n_orders == 5
        assert stats.n_fills == 0


class TestFromExecutionResults:
    """Tests fuer from_execution_results()."""

    def _create_mock_result(
        self,
        symbol: str = "BTC/EUR",
        side: str = "buy",
        quantity: float = 0.01,
        price: float = 50000.0,
        fee: float = 0.5,
        status: str = "filled",
    ):
        """Erstellt ein Mock OrderExecutionResult."""
        from dataclasses import dataclass, field
        from datetime import datetime
        from typing import Any, Dict, Optional

        @dataclass
        class MockFill:
            symbol: str
            side: str
            quantity: float
            price: float
            timestamp: datetime
            fee: Optional[float] = None

        @dataclass
        class MockRequest:
            symbol: str
            side: str
            quantity: float
            metadata: Dict[str, Any] = field(default_factory=dict)

        @dataclass
        class MockResult:
            status: str
            request: MockRequest
            fill: Optional[MockFill] = None
            metadata: Dict[str, Any] = field(default_factory=dict)

            @property
            def is_filled(self) -> bool:
                return self.status == "filled"

            @property
            def is_rejected(self) -> bool:
                return self.status == "rejected"

        request = MockRequest(symbol=symbol, side=side, quantity=quantity)
        fill = None
        if status == "filled":
            fill = MockFill(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                timestamp=datetime.now(),
                fee=fee,
            )

        return MockResult(status=status, request=request, fill=fill)

    def test_empty_results(self):
        """Leere Results ergeben leere Stats."""
        from src.reporting.execution_reports import from_execution_results

        stats = from_execution_results([])

        assert stats.n_orders == 0
        assert stats.n_fills == 0

    def test_single_filled_result(self):
        """Einzelnes gefuelltes Result wird korrekt verarbeitet."""
        from src.reporting.execution_reports import from_execution_results

        results = [
            self._create_mock_result(
                symbol="BTC/EUR",
                side="buy",
                quantity=0.01,
                price=50000.0,
                fee=0.5,
            )
        ]

        stats = from_execution_results(results)

        assert stats.n_orders == 1
        assert stats.n_fills == 1
        assert stats.n_rejected == 0
        assert stats.total_fees == 0.5
        assert stats.total_notional == 500.0  # 0.01 * 50000
        assert stats.n_buys == 1
        assert stats.n_sells == 0
        assert stats.buy_volume == 500.0

    def test_buy_and_sell_tracking(self):
        """Buy und Sell werden separat getrackt."""
        from src.reporting.execution_reports import from_execution_results

        results = [
            self._create_mock_result(side="buy", quantity=0.01, price=50000.0, fee=0.5),
            self._create_mock_result(side="sell", quantity=0.01, price=51000.0, fee=0.5),
        ]

        stats = from_execution_results(results)

        assert stats.n_buys == 1
        assert stats.n_sells == 1
        assert stats.buy_volume == 500.0
        assert stats.sell_volume == 510.0

    def test_rejected_results_counted(self):
        """Rejected Results werden gezaehlt."""
        from src.reporting.execution_reports import from_execution_results

        results = [
            self._create_mock_result(status="filled"),
            self._create_mock_result(status="rejected"),
            self._create_mock_result(status="rejected"),
        ]

        stats = from_execution_results(results)

        assert stats.n_orders == 3
        assert stats.n_fills == 1
        assert stats.n_rejected == 2
        assert stats.fill_rate == pytest.approx(1 / 3)

    def test_notional_statistics(self):
        """Notional-Statistiken werden korrekt berechnet."""
        from src.reporting.execution_reports import from_execution_results

        results = [
            self._create_mock_result(quantity=0.01, price=50000.0),  # 500
            self._create_mock_result(quantity=0.02, price=50000.0),  # 1000
            self._create_mock_result(quantity=0.03, price=50000.0),  # 1500
        ]

        stats = from_execution_results(results)

        assert stats.total_notional == 3000.0
        assert stats.avg_trade_notional == 1000.0
        assert stats.max_trade_notional == 1500.0
        assert stats.min_trade_notional == 500.0


class TestFromBacktestResult:
    """Tests fuer from_backtest_result()."""

    def _create_mock_backtest_result(
        self,
        total_orders: int = 10,
        filled_orders: int = 8,
        total_fees: float = 5.0,
        total_trades: int = 4,
        win_rate: float = 0.5,
    ):
        """Erstellt ein Mock BacktestResult."""
        from dataclasses import dataclass
        from typing import Any, Dict, Optional

        @dataclass
        class MockResult:
            stats: Dict[str, Any]
            metadata: Dict[str, Any]
            trades: Optional[Any] = None
            equity_curve: Optional[Any] = None

        return MockResult(
            stats={
                "total_orders": total_orders,
                "filled_orders": filled_orders,
                "rejected_orders": total_orders - filled_orders,
                "total_fees": total_fees,
                "total_trades": total_trades,
                "win_rate": win_rate,
            },
            metadata={
                "symbol": "BTC/EUR",
                "run_id": "mock_run",
            },
        )

    def test_basic_extraction(self):
        """Basis-Stats werden aus Result extrahiert."""
        from src.reporting.execution_reports import from_backtest_result

        result = self._create_mock_backtest_result()
        stats = from_backtest_result(result)

        assert stats.n_orders == 10
        assert stats.n_fills == 8
        assert stats.n_rejected == 2
        assert stats.total_fees == 5.0
        assert stats.symbol == "BTC/EUR"
        assert stats.run_id == "mock_run"

    def test_hit_rate_from_win_rate(self):
        """Hit-Rate wird aus Win-Rate berechnet."""
        from src.reporting.execution_reports import from_backtest_result

        result = self._create_mock_backtest_result(
            total_trades=10,
            win_rate=0.6,
        )
        stats = from_backtest_result(result)

        assert stats.hit_rate == 0.6
        assert stats.n_winning_trades == 6
        assert stats.n_losing_trades == 4


class TestFormatExecutionStats:
    """Tests fuer format_execution_stats()."""

    def test_basic_formatting(self):
        """Basis-Formatierung funktioniert."""
        from src.reporting.execution_reports import ExecutionStats, format_execution_stats

        stats = ExecutionStats(
            n_orders=100,
            n_fills=95,
            n_rejected=5,
            total_fees=50.0,
            total_notional=10000.0,
        )

        output = format_execution_stats(stats)

        assert "Execution Statistics" in output
        assert "Orders" in output
        assert "Fills" in output
        assert "100" in output
        assert "95" in output

    def test_custom_title(self):
        """Custom-Titel wird verwendet."""
        from src.reporting.execution_reports import ExecutionStats, format_execution_stats

        stats = ExecutionStats(n_orders=10)
        output = format_execution_stats(stats, title="Custom Report")

        assert "Custom Report" in output

    def test_slippage_section_included(self):
        """Slippage-Sektion wird bei Daten angezeigt."""
        from src.reporting.execution_reports import ExecutionStats, format_execution_stats

        stats = ExecutionStats(
            n_orders=10,
            n_fills=10,
            avg_slippage_bps=5.0,
            max_slippage_bps=10.0,
            total_slippage=25.0,
        )

        output = format_execution_stats(stats, include_slippage=True)

        assert "Slippage" in output
        assert "5.00" in output  # avg slippage

    def test_buy_sell_section_included(self):
        """Buy/Sell-Sektion wird bei Daten angezeigt."""
        from src.reporting.execution_reports import ExecutionStats, format_execution_stats

        stats = ExecutionStats(
            n_orders=20,
            n_fills=20,
            n_buys=12,
            n_sells=8,
            buy_volume=6000.0,
            sell_volume=4000.0,
        )

        output = format_execution_stats(stats, include_buy_sell=True)

        assert "Buy/Sell" in output
        assert "12" in output  # n_buys
        assert "8" in output  # n_sells


class TestExecutionPlotsModule:
    """Tests fuer src/reporting/execution_plots.py."""

    def test_check_matplotlib(self):
        """check_matplotlib() gibt Boolean zurueck."""
        from src.reporting.execution_plots import check_matplotlib

        result = check_matplotlib()
        assert isinstance(result, bool)

    def test_extract_fees_from_results(self):
        """extract_fees_from_results() extrahiert Fees korrekt."""
        from src.reporting.execution_plots import extract_fees_from_results
        from dataclasses import dataclass, field
        from datetime import datetime
        from typing import Any, Dict, Optional

        @dataclass
        class MockFill:
            symbol: str
            side: str
            quantity: float
            price: float
            timestamp: datetime
            fee: Optional[float] = None

        @dataclass
        class MockRequest:
            symbol: str
            side: str
            quantity: float
            metadata: Dict[str, Any] = field(default_factory=dict)

        @dataclass
        class MockResult:
            status: str
            request: MockRequest
            fill: Optional[MockFill] = None

            @property
            def is_filled(self) -> bool:
                return self.status == "filled"

        results = [
            MockResult(
                status="filled",
                request=MockRequest("BTC/EUR", "buy", 0.01),
                fill=MockFill("BTC/EUR", "buy", 0.01, 50000, datetime.now(), fee=0.5),
            ),
            MockResult(
                status="filled",
                request=MockRequest("BTC/EUR", "sell", 0.01),
                fill=MockFill("BTC/EUR", "sell", 0.01, 51000, datetime.now(), fee=0.6),
            ),
        ]

        fees = extract_fees_from_results(results)

        assert len(fees) == 2
        assert 0.5 in fees
        assert 0.6 in fees

    def test_extract_notionals_from_results(self):
        """extract_notionals_from_results() extrahiert Notionals korrekt."""
        from src.reporting.execution_plots import extract_notionals_from_results
        from dataclasses import dataclass, field
        from datetime import datetime
        from typing import Any, Dict, Optional

        @dataclass
        class MockFill:
            symbol: str
            side: str
            quantity: float
            price: float
            timestamp: datetime
            fee: Optional[float] = None

        @dataclass
        class MockRequest:
            symbol: str
            side: str
            quantity: float
            metadata: Dict[str, Any] = field(default_factory=dict)

        @dataclass
        class MockResult:
            status: str
            request: MockRequest
            fill: Optional[MockFill] = None

            @property
            def is_filled(self) -> bool:
                return self.status == "filled"

        results = [
            MockResult(
                status="filled",
                request=MockRequest("BTC/EUR", "buy", 0.01),
                fill=MockFill("BTC/EUR", "buy", 0.01, 50000, datetime.now()),
            ),
        ]

        notionals = extract_notionals_from_results(results)

        assert len(notionals) == 1
        assert notionals[0] == 500.0  # 0.01 * 50000


class TestReportingModuleImports:
    """Tests fuer Modul-Imports."""

    def test_execution_reports_imports(self):
        """execution_reports kann importiert werden."""
        from src.reporting.execution_reports import (
            ExecutionStats,
            from_execution_logs,
            from_execution_results,
            from_backtest_result,
            format_execution_stats,
        )

        assert ExecutionStats is not None
        assert callable(from_execution_logs)
        assert callable(from_execution_results)
        assert callable(from_backtest_result)
        assert callable(format_execution_stats)

    def test_execution_plots_imports(self):
        """execution_plots kann importiert werden."""
        from src.reporting.execution_plots import (
            check_matplotlib,
            plot_slippage_histogram,
            plot_fee_histogram,
            plot_notional_histogram,
            plot_equity_with_trades,
            extract_fees_from_results,
            extract_notionals_from_results,
        )

        assert callable(check_matplotlib)
        assert callable(plot_slippage_histogram)

    def test_reporting_package_exports(self):
        """reporting Package exportiert korrekt."""
        from src.reporting import (
            ExecutionStats,
            from_execution_logs,
            from_execution_results,
            from_backtest_result,
            format_execution_stats,
        )

        assert ExecutionStats is not None
