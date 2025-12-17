# tests/test_smoke_test_testnet_stack.py
"""
Tests für scripts/smoke_test_testnet_stack.py (Phase 39)
=========================================================

Testet das Testnet-Stack Smoke-Test-Script.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Pfad-Setup
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.smoke_test_testnet_stack import (
    SmokeTestReport,
    SmokeTestResult,
    main,
    parse_args,
    run_smoke_tests,
    smoke_test_config_load,
    smoke_test_dummy_client,
    smoke_test_exchange_executor,
    smoke_test_executor_order,
    smoke_test_order_cancel,
    smoke_test_order_placement,
    smoke_test_safety_guard,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def valid_config_path(tmp_path: Path) -> Path:
    """Erstellt eine gültige Test-Config."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[backtest]
initial_cash = 10000.0

[risk]
max_daily_loss = 0.03

[live_risk]
max_order_notional = 1000.0
max_daily_loss_abs = 500.0

[shadow]
enabled = true
fee_rate = 0.0005

[exchange]
default_type = "dummy"

[exchange.dummy]
simulated_prices = { "BTC/EUR" = 50000.0, "ETH/EUR" = 3000.0 }
fee_bps = 10.0
slippage_bps = 5.0
""")
    return config_file


@pytest.fixture
def config_without_prices(tmp_path: Path) -> Path:
    """Config ohne simulierte Preise."""
    config_file = tmp_path / "no_prices.toml"
    config_file.write_text("""
[backtest]
initial_cash = 10000.0

[exchange]
default_type = "dummy"
""")
    return config_file


# =============================================================================
# Tests: CLI Argument Parsing
# =============================================================================


class TestParseArgs:
    """Tests für Argument-Parsing."""

    def test_default_config(self):
        """Default-Config-Pfad ist None (wird zu config/config.toml)."""
        args = parse_args([])
        assert args.config_path is None

    def test_custom_config(self):
        """Custom Config-Pfad wird erkannt."""
        args = parse_args(["--config", "/custom/path.toml"])
        assert args.config_path == "/custom/path.toml"

    def test_verbose_flag(self):
        """--verbose Flag wird erkannt."""
        args = parse_args(["--verbose"])
        assert args.verbose is True

    def test_quiet_flag(self):
        """--quiet Flag wird erkannt."""
        args = parse_args(["--quiet"])
        assert args.quiet is True

    def test_short_verbose_flag(self):
        """-v Flag wird erkannt."""
        args = parse_args(["-v"])
        assert args.verbose is True

    def test_short_quiet_flag(self):
        """-q Flag wird erkannt."""
        args = parse_args(["-q"])
        assert args.quiet is True


# =============================================================================
# Tests: Individual Smoke Test Functions
# =============================================================================


class TestSmokeTestConfigLoad:
    """Tests für smoke_test_config_load."""

    def test_valid_config(self, valid_config_path: Path):
        """Gültige Config laden -> passed."""
        result = smoke_test_config_load(valid_config_path)
        assert result.passed is True
        assert result.name == "Config laden"
        assert result.duration_ms > 0

    def test_invalid_config(self, tmp_path: Path):
        """Ungültige Config -> failed."""
        invalid_config = tmp_path / "invalid.toml"
        invalid_config.write_text("invalid [ toml syntax")
        result = smoke_test_config_load(invalid_config)
        assert result.passed is False

    def test_nonexistent_config(self, tmp_path: Path):
        """Config existiert nicht -> failed."""
        result = smoke_test_config_load(tmp_path / "nonexistent.toml")
        assert result.passed is False


class TestSmokeTestDummyClient:
    """Tests für smoke_test_dummy_client."""

    def test_with_prices(self, valid_config_path: Path):
        """Client mit Preisen -> passed."""
        result = smoke_test_dummy_client(valid_config_path)
        assert result.passed is True
        assert "DummyExchangeClient" in result.name

    def test_without_prices_uses_defaults(self, config_without_prices: Path):
        """Client ohne Preise nutzt Defaults -> passed."""
        result = smoke_test_dummy_client(config_without_prices)
        assert result.passed is True


class TestSmokeTestSafetyGuard:
    """Tests für smoke_test_safety_guard."""

    def test_safety_guard_init(self, valid_config_path: Path):
        """SafetyGuard initialisieren -> passed."""
        result = smoke_test_safety_guard(valid_config_path)
        assert result.passed is True
        assert "SafetyGuard" in result.name


class TestSmokeTestExchangeExecutor:
    """Tests für smoke_test_exchange_executor."""

    def test_executor_init(self, valid_config_path: Path):
        """ExchangeOrderExecutor initialisieren -> passed."""
        result = smoke_test_exchange_executor(valid_config_path)
        assert result.passed is True
        assert "ExchangeOrderExecutor" in result.name


class TestSmokeTestOrderPlacement:
    """Tests für smoke_test_order_placement."""

    def test_market_order_filled(self, valid_config_path: Path):
        """Market-Order wird gefüllt -> passed."""
        result = smoke_test_order_placement(valid_config_path)
        assert result.passed is True
        assert "gefüllt" in result.message.lower() or "filled" in result.message.lower()


class TestSmokeTestExecutorOrder:
    """Tests für smoke_test_executor_order."""

    def test_executor_order_filled(self, valid_config_path: Path):
        """Order über Executor wird gefüllt -> passed."""
        result = smoke_test_executor_order(valid_config_path)
        assert result.passed is True


class TestSmokeTestOrderCancel:
    """Tests für smoke_test_order_cancel."""

    def test_limit_order_cancelled(self, valid_config_path: Path):
        """Limit-Order kann storniert werden -> passed."""
        result = smoke_test_order_cancel(valid_config_path)
        assert result.passed is True
        assert "storniert" in result.message.lower()


# =============================================================================
# Tests: SmokeTestResult and SmokeTestReport
# =============================================================================


class TestSmokeTestResult:
    """Tests für SmokeTestResult."""

    def test_result_creation(self):
        """SmokeTestResult kann erstellt werden."""
        result = SmokeTestResult(
            name="Test",
            passed=True,
            message="OK",
            duration_ms=10.5,
            details=["Detail 1"],
        )
        assert result.name == "Test"
        assert result.passed is True
        assert result.duration_ms == 10.5


class TestSmokeTestReport:
    """Tests für SmokeTestReport."""

    def test_all_passed(self):
        """Alle Tests bestanden."""
        report = SmokeTestReport(
            tests=[
                SmokeTestResult(name="T1", passed=True, message="OK"),
                SmokeTestResult(name="T2", passed=True, message="OK"),
            ],
            total_duration_ms=100.0,
        )
        assert report.all_passed is True
        assert report.passed_count == 2
        assert report.failed_count == 0

    def test_some_failed(self):
        """Einige Tests fehlgeschlagen."""
        report = SmokeTestReport(
            tests=[
                SmokeTestResult(name="T1", passed=True, message="OK"),
                SmokeTestResult(name="T2", passed=False, message="Failed"),
                SmokeTestResult(name="T3", passed=True, message="OK"),
            ],
            total_duration_ms=150.0,
        )
        assert report.all_passed is False
        assert report.passed_count == 2
        assert report.failed_count == 1


# =============================================================================
# Tests: run_smoke_tests
# =============================================================================


class TestRunSmokeTests:
    """Tests für run_smoke_tests."""

    def test_all_tests_run(self, valid_config_path: Path):
        """Alle Smoke-Tests werden ausgeführt."""
        report = run_smoke_tests(valid_config_path)
        assert len(report.tests) == 7  # 7 Tests definiert
        assert report.total_duration_ms > 0

    def test_all_tests_pass_with_valid_config(self, valid_config_path: Path):
        """Alle Tests bestehen mit gültiger Config."""
        report = run_smoke_tests(valid_config_path)
        assert report.all_passed is True

    def test_invalid_config_fails_first_test(self, tmp_path: Path):
        """Ungültige Config -> erster Test failed."""
        invalid_config = tmp_path / "invalid.toml"
        invalid_config.write_text("invalid [ syntax")
        report = run_smoke_tests(invalid_config)
        assert report.tests[0].passed is False


# =============================================================================
# Tests: main() Function
# =============================================================================


class TestMain:
    """Tests für main() Funktion."""

    def test_main_success(self, valid_config_path: Path):
        """main() mit gültiger Config -> Exit 0."""
        exit_code = main(["--config", str(valid_config_path), "--quiet"])
        assert exit_code == 0

    def test_main_invalid_config(self, tmp_path: Path):
        """main() mit ungültiger Config -> Exit 1."""
        invalid_config = tmp_path / "invalid.toml"
        invalid_config.write_text("invalid [ syntax")
        exit_code = main(["--config", str(invalid_config), "--quiet"])
        assert exit_code == 1

    def test_main_verbose_output(self, valid_config_path: Path, capsys):
        """main() mit --verbose gibt Details aus."""
        main(["--config", str(valid_config_path), "--verbose"])
        captured = capsys.readouterr()
        assert "Peak_Trade" in captured.out
        assert "Smoke-Test" in captured.out

    def test_main_quiet_output(self, valid_config_path: Path, capsys):
        """main() mit --quiet gibt nur PASSED/FAILED aus."""
        main(["--config", str(valid_config_path), "--quiet"])
        captured = capsys.readouterr()
        assert captured.out.strip() in ("PASSED", "FAILED")

    def test_main_shows_duration(self, valid_config_path: Path, capsys):
        """main() ohne --quiet zeigt Gesamtzeit."""
        main(["--config", str(valid_config_path)])
        captured = capsys.readouterr()
        assert "ms" in captured.out  # Duration wird angezeigt


# =============================================================================
# Integration Tests
# =============================================================================


class TestSmokeTestIntegration:
    """Integration-Tests für den gesamten Smoke-Test-Flow."""

    def test_full_smoke_test_workflow(self, valid_config_path: Path, capsys):
        """Vollständiger Smoke-Test-Workflow."""
        # 1. Parse args
        args = parse_args(["--config", str(valid_config_path)])
        assert args.config_path == str(valid_config_path)

        # 2. Run smoke tests
        report = run_smoke_tests(valid_config_path)

        # 3. Verify all passed
        assert report.all_passed is True
        assert len(report.tests) == 7

        # 4. Check each test type
        test_names = [t.name for t in report.tests]
        assert "Config laden" in test_names
        assert "DummyExchangeClient" in test_names
        assert "SafetyGuard" in test_names
        assert "ExchangeOrderExecutor" in test_names
        assert "Order-Platzierung" in test_names
        assert "Executor-Order" in test_names
        assert "Order-Cancel" in test_names




