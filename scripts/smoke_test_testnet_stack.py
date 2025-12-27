#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/smoke_test_testnet_stack.py
"""
Peak_Trade: Testnet-Stack Smoke-Test (Phase 39)
===============================================

Führt einen minimalen "Smoke-Test" für den Testnet-Stack aus,
ohne echte Orders zu platzieren.

Geprüft wird:
1. Config laden
2. TradingExchangeClient (DummyClient) instanziieren
3. ExchangeOrderExecutor initialisieren
4. Simulierte Order-Platzierung (nur lokal, keine API)
5. Order-Status prüfen

WICHTIG: Keine echten Netzwerk-Calls! Nur lokale Simulation.

Usage:
    python scripts/smoke_test_testnet_stack.py
    python scripts/smoke_test_testnet_stack.py --verbose
    python scripts/smoke_test_testnet_stack.py --config config/config.test.toml

Exit Codes:
    0 = Smoke-Test bestanden
    1 = Smoke-Test fehlgeschlagen
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# Pfad-Setup
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.peak_config import load_config
from src.core.environment import EnvironmentConfig, TradingEnvironment

# =============================================================================
# Smoke Test Results
# =============================================================================


@dataclass
class SmokeTestResult:
    """Ergebnis eines einzelnen Smoke-Tests."""

    name: str
    passed: bool
    message: str
    duration_ms: float = 0.0
    details: List[str] = field(default_factory=list)


@dataclass
class SmokeTestReport:
    """Gesamtbericht aller Smoke-Tests."""

    tests: List[SmokeTestResult]
    total_duration_ms: float = 0.0

    @property
    def all_passed(self) -> bool:
        return all(t.passed for t in self.tests)

    @property
    def passed_count(self) -> int:
        return sum(1 for t in self.tests if t.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for t in self.tests if not t.passed)


# =============================================================================
# Individual Smoke Tests
# =============================================================================


def smoke_test_config_load(config_path: Path) -> SmokeTestResult:
    """Test 1: Config laden."""
    start = time.perf_counter()
    try:
        cfg = load_config(config_path)
        duration = (time.perf_counter() - start) * 1000

        # Basis-Checks
        details = [
            f"exchange.default_type: {cfg.get('exchange.default_type', 'N/A')}",
        ]

        return SmokeTestResult(
            name="Config laden",
            passed=True,
            message=f"Config erfolgreich geladen: {config_path.name}",
            duration_ms=duration,
            details=details,
        )
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        return SmokeTestResult(
            name="Config laden",
            passed=False,
            message=f"Fehler: {e}",
            duration_ms=duration,
        )


def smoke_test_dummy_client(config_path: Path) -> SmokeTestResult:
    """Test 2: DummyExchangeClient instanziieren."""
    start = time.perf_counter()
    try:
        from src.exchange.dummy_client import DummyExchangeClient

        cfg = load_config(config_path)

        # Preise aus Config oder Defaults
        prices = cfg.get("exchange.dummy.simulated_prices", {})
        if not prices:
            prices = {"BTC/EUR": 50000.0, "ETH/EUR": 3000.0}

        fee_bps = cfg.get("exchange.dummy.fee_bps", 10.0)
        slippage_bps = cfg.get("exchange.dummy.slippage_bps", 5.0)

        client = DummyExchangeClient(
            simulated_prices=prices,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
        )

        duration = (time.perf_counter() - start) * 1000

        return SmokeTestResult(
            name="DummyExchangeClient",
            passed=True,
            message=f"Client initialisiert: {client.get_name()}",
            duration_ms=duration,
            details=[
                f"Preise: {list(prices.keys())}",
                f"Fee: {fee_bps} bps",
                f"Slippage: {slippage_bps} bps",
            ],
        )
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        return SmokeTestResult(
            name="DummyExchangeClient",
            passed=False,
            message=f"Fehler: {e}",
            duration_ms=duration,
        )


def smoke_test_safety_guard(config_path: Path) -> SmokeTestResult:
    """Test 3: SafetyGuard initialisieren."""
    start = time.perf_counter()
    try:
        from src.live.safety import SafetyGuard

        cfg = load_config(config_path)
        env_config = EnvironmentConfig(
            environment=TradingEnvironment.TESTNET,
            enable_live_trading=False,
        )

        guard = SafetyGuard(env_config=env_config)

        duration = (time.perf_counter() - start) * 1000

        return SmokeTestResult(
            name="SafetyGuard",
            passed=True,
            message=f"SafetyGuard initialisiert (Mode: {env_config.environment.value})",
            duration_ms=duration,
        )
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        return SmokeTestResult(
            name="SafetyGuard",
            passed=False,
            message=f"Fehler: {e}",
            duration_ms=duration,
        )


def smoke_test_exchange_executor(config_path: Path) -> SmokeTestResult:
    """Test 4: ExchangeOrderExecutor mit DummyClient."""
    start = time.perf_counter()
    try:
        from src.exchange.dummy_client import DummyExchangeClient
        from src.orders.exchange import ExchangeOrderExecutor
        from src.live.safety import SafetyGuard

        cfg = load_config(config_path)
        env_config = EnvironmentConfig(
            environment=TradingEnvironment.TESTNET,
            enable_live_trading=False,
        )
        guard = SafetyGuard(env_config=env_config)

        prices = cfg.get("exchange.dummy.simulated_prices", {"BTC/EUR": 50000.0})
        client = DummyExchangeClient(simulated_prices=prices)

        executor = ExchangeOrderExecutor(
            safety_guard=guard,
            trading_client=client,
        )

        duration = (time.perf_counter() - start) * 1000

        return SmokeTestResult(
            name="ExchangeOrderExecutor",
            passed=True,
            message="Executor mit DummyClient initialisiert",
            duration_ms=duration,
            details=[f"Execution-Count: {executor.get_execution_count()}"],
        )
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        return SmokeTestResult(
            name="ExchangeOrderExecutor",
            passed=False,
            message=f"Fehler: {e}",
            duration_ms=duration,
        )


def smoke_test_order_placement(config_path: Path) -> SmokeTestResult:
    """Test 5: Simulierte Order-Platzierung über DummyClient."""
    start = time.perf_counter()
    try:
        from src.exchange.dummy_client import DummyExchangeClient
        from src.exchange.base import ExchangeOrderStatus

        cfg = load_config(config_path)
        prices = cfg.get("exchange.dummy.simulated_prices", {"BTC/EUR": 50000.0})

        client = DummyExchangeClient(simulated_prices=prices)

        # Market-Order platzieren
        symbol = list(prices.keys())[0] if prices else "BTC/EUR"
        order_id = client.place_order(
            symbol=symbol,
            side="buy",
            quantity=0.001,
            order_type="market",
        )

        # Status prüfen
        status = client.get_order_status(order_id)

        duration = (time.perf_counter() - start) * 1000

        if status.status == ExchangeOrderStatus.FILLED:
            return SmokeTestResult(
                name="Order-Platzierung",
                passed=True,
                message=f"Market-Order gefüllt: {order_id}",
                duration_ms=duration,
                details=[
                    f"Symbol: {symbol}",
                    f"Status: {status.status.value}",
                    f"Filled: {status.filled_qty}",
                    f"Price: {status.avg_price:.2f}" if status.avg_price else "N/A",
                ],
            )
        else:
            return SmokeTestResult(
                name="Order-Platzierung",
                passed=False,
                message=f"Order nicht gefüllt: Status = {status.status.value}",
                duration_ms=duration,
            )
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        return SmokeTestResult(
            name="Order-Platzierung",
            passed=False,
            message=f"Fehler: {e}",
            duration_ms=duration,
        )


def smoke_test_executor_order(config_path: Path) -> SmokeTestResult:
    """Test 6: Order über ExchangeOrderExecutor mit DummyClient."""
    start = time.perf_counter()
    try:
        from src.exchange.dummy_client import DummyExchangeClient
        from src.orders.exchange import ExchangeOrderExecutor
        from src.orders.base import OrderRequest
        from src.live.safety import SafetyGuard

        cfg = load_config(config_path)
        env_config = EnvironmentConfig(
            environment=TradingEnvironment.TESTNET,
            enable_live_trading=False,
        )
        guard = SafetyGuard(env_config=env_config)

        prices = cfg.get("exchange.dummy.simulated_prices", {"BTC/EUR": 50000.0})
        client = DummyExchangeClient(simulated_prices=prices)

        executor = ExchangeOrderExecutor(
            safety_guard=guard,
            trading_client=client,
        )

        # Order erstellen
        symbol = list(prices.keys())[0] if prices else "BTC/EUR"
        order = OrderRequest(
            symbol=symbol,
            side="buy",
            quantity=0.001,
            order_type="market",
        )

        # Ausführen
        result = executor.execute_order(order)

        duration = (time.perf_counter() - start) * 1000

        if result.status == "filled":
            return SmokeTestResult(
                name="Executor-Order",
                passed=True,
                message=f"Order über Executor gefüllt",
                duration_ms=duration,
                details=[
                    f"Symbol: {symbol}",
                    f"Status: {result.status}",
                    f"Fill: {result.fill.quantity if result.fill else 'N/A'}",
                    f"Execution-Count: {executor.get_execution_count()}",
                ],
            )
        else:
            return SmokeTestResult(
                name="Executor-Order",
                passed=False,
                message=f"Order nicht gefüllt: {result.status} - {result.reason}",
                duration_ms=duration,
            )
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        return SmokeTestResult(
            name="Executor-Order",
            passed=False,
            message=f"Fehler: {e}",
            duration_ms=duration,
        )


def smoke_test_order_cancel(config_path: Path) -> SmokeTestResult:
    """Test 7: Order-Stornierung."""
    start = time.perf_counter()
    try:
        from src.exchange.dummy_client import DummyExchangeClient
        from src.exchange.base import ExchangeOrderStatus

        cfg = load_config(config_path)
        prices = cfg.get("exchange.dummy.simulated_prices", {"BTC/EUR": 50000.0})

        client = DummyExchangeClient(simulated_prices=prices)

        # Limit-Order platzieren (bleibt offen)
        symbol = list(prices.keys())[0] if prices else "BTC/EUR"
        order_id = client.place_order(
            symbol=symbol,
            side="buy",
            quantity=0.001,
            order_type="limit",
            limit_price=40000.0,  # Unter aktuellem Preis
        )

        # Stornieren
        cancelled = client.cancel_order(order_id)

        # Status prüfen
        status = client.get_order_status(order_id)

        duration = (time.perf_counter() - start) * 1000

        if cancelled and status.status == ExchangeOrderStatus.CANCELLED:
            return SmokeTestResult(
                name="Order-Cancel",
                passed=True,
                message="Limit-Order erfolgreich storniert",
                duration_ms=duration,
                details=[f"Order-ID: {order_id}"],
            )
        else:
            return SmokeTestResult(
                name="Order-Cancel",
                passed=False,
                message=f"Stornierung fehlgeschlagen: Status = {status.status.value}",
                duration_ms=duration,
            )
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        return SmokeTestResult(
            name="Order-Cancel",
            passed=False,
            message=f"Fehler: {e}",
            duration_ms=duration,
        )


# =============================================================================
# Main Test Runner
# =============================================================================


def run_smoke_tests(config_path: Path) -> SmokeTestReport:
    """
    Führt alle Smoke-Tests aus.

    Args:
        config_path: Pfad zur Config-Datei

    Returns:
        SmokeTestReport mit allen Ergebnissen
    """
    total_start = time.perf_counter()
    tests: List[SmokeTestResult] = []

    # Tests ausführen
    tests.append(smoke_test_config_load(config_path))
    tests.append(smoke_test_dummy_client(config_path))
    tests.append(smoke_test_safety_guard(config_path))
    tests.append(smoke_test_exchange_executor(config_path))
    tests.append(smoke_test_order_placement(config_path))
    tests.append(smoke_test_executor_order(config_path))
    tests.append(smoke_test_order_cancel(config_path))

    total_duration = (time.perf_counter() - total_start) * 1000

    return SmokeTestReport(tests=tests, total_duration_ms=total_duration)


# =============================================================================
# CLI
# =============================================================================


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Testnet-Stack Smoke-Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Dieser Smoke-Test prüft die grundlegende Funktionalität des Testnet-Stacks
OHNE echte Netzwerk-Calls. Es wird nur der DummyExchangeClient verwendet.

Tests:
  1. Config laden
  2. DummyExchangeClient instanziieren
  3. SafetyGuard initialisieren
  4. ExchangeOrderExecutor initialisieren
  5. Simulierte Order-Platzierung
  6. Order über Executor ausführen
  7. Order-Stornierung

Beispiele:
  python scripts/smoke_test_testnet_stack.py
  python scripts/smoke_test_testnet_stack.py --verbose
  python scripts/smoke_test_testnet_stack.py --config config/config.test.toml
        """,
    )

    parser.add_argument(
        "--config",
        dest="config_path",
        default=None,
        help="Pfad zur Config-Datei (Default: config/config.toml)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Ausführliche Ausgabe mit Details",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Nur Ergebnis (PASSED/FAILED) ausgeben",
    )

    return parser.parse_args(argv)


def print_report(report: SmokeTestReport, verbose: bool, quiet: bool) -> None:
    """Gibt den Report aus."""

    if quiet:
        if report.all_passed:
            print("PASSED")
        else:
            print("FAILED")
        return

    # Header
    print()
    print("=" * 70)
    print("  Peak_Trade Testnet-Stack Smoke-Test")
    print("=" * 70)
    print()

    # Tests
    for test in report.tests:
        icon = "✅" if test.passed else "❌"
        time_str = f"({test.duration_ms:.1f}ms)" if test.duration_ms else ""
        print(f"  {icon} {test.name}: {test.message} {time_str}")

        if verbose and test.details:
            for detail in test.details:
                print(f"      └─ {detail}")

    # Summary
    print()
    print("-" * 70)
    if report.all_passed:
        print(f"  ✅ Smoke-Test BESTANDEN ({report.passed_count}/{len(report.tests)} Tests)")
    else:
        print(
            f"  ❌ Smoke-Test FEHLGESCHLAGEN ({report.failed_count} von {len(report.tests)} Tests fehlgeschlagen)"
        )
    print(f"  ⏱  Gesamtzeit: {report.total_duration_ms:.1f}ms")
    print()


def main(argv: Optional[List[str]] = None) -> int:
    """
    Hauptfunktion.

    Returns:
        Exit-Code: 0 = alle Tests bestanden, 1 = mindestens ein Test fehlgeschlagen
    """
    args = parse_args(argv)

    # Logging reduzieren
    logging.getLogger("src").setLevel(logging.WARNING)
    logging.getLogger("src.exchange").setLevel(logging.WARNING)

    # Config-Pfad bestimmen
    if args.config_path:
        config_path = Path(args.config_path)
    else:
        config_path = ROOT_DIR / "config" / "config.toml"

    # Smoke-Tests ausführen
    report = run_smoke_tests(config_path)

    # Report ausgeben
    print_report(report, verbose=args.verbose, quiet=args.quiet)

    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
