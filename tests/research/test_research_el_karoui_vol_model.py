# tests/research/test_research_el_karoui_vol_model.py
"""
Smoke-Tests für das El Karoui Research-Skript.

Diese Tests validieren die grundlegende Funktionalität des Research-Workflows,
ohne die vollständige Backtest-Integration zu erfordern.

Testet:
- Date-Range-Parsing
- Run-Config-Generierung
- Markdown-Report-Generierung
- CLI-Argument-Parsing
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

# Projekt-Root zum Path hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.research_el_karoui_vol_model import (
    DEFAULT_DATE_RANGES,
    DEFAULT_MAPPING_VARIANTS,
    DEFAULT_SYMBOLS,
    REPORT_PATH,
    BacktestResult,
    BacktestRunConfig,
    _format_float,
    _format_pct,
    _parse_cli_args,
    generate_run_configs,
    parse_date_range,
    results_to_markdown,
    run_el_karoui_backtest,
    write_report,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_config() -> BacktestRunConfig:
    """Beispiel-Konfiguration für Tests."""
    return BacktestRunConfig(
        symbol="SPY",
        start_date=date(2020, 1, 1),
        end_date=date(2024, 1, 1),
        mapping_variant="default",
    )


@pytest.fixture
def sample_results() -> list[BacktestResult]:
    """Beispiel-Ergebnisse für Report-Tests."""
    return [
        BacktestResult(
            symbol="SPY",
            date_range_label="2020-01-01 – 2024-01-01",
            mapping_variant="default",
            sharpe=1.25,
            max_drawdown=-0.18,
            annual_return=0.12,
            volatility=0.15,
            time_in_market=0.75,
        ),
        BacktestResult(
            symbol="SPY",
            date_range_label="2020-01-01 – 2024-01-01",
            mapping_variant="conservative",
            sharpe=0.95,
            max_drawdown=-0.12,
            annual_return=0.08,
            volatility=0.10,
            time_in_market=0.50,
        ),
        BacktestResult(
            symbol="QQQ",
            date_range_label="2020-01-01 – 2024-01-01",
            mapping_variant="default",
            sharpe=1.40,
            max_drawdown=-0.22,
            annual_return=0.15,
            volatility=0.18,
            time_in_market=0.80,
        ),
    ]


@pytest.fixture
def temp_report_path(tmp_path: Path) -> Path:
    """Temporärer Pfad für Report-Output."""
    return tmp_path / "test_report.md"


# =============================================================================
# DATE-RANGE PARSING TESTS
# =============================================================================


class TestDateRangeParsing:
    """Tests für parse_date_range."""

    def test_parse_date_range_valid(self) -> None:
        """Prüft Parsing eines gültigen Date-Range-Strings."""
        start, end = parse_date_range("2020-01-01:2024-12-31")

        assert start == date(2020, 1, 1)
        assert end == date(2024, 12, 31)

    def test_parse_date_range_with_whitespace(self) -> None:
        """Prüft Parsing mit Whitespace."""
        start, end = parse_date_range(" 2020-01-01 : 2024-12-31 ")

        assert start == date(2020, 1, 1)
        assert end == date(2024, 12, 31)

    def test_parse_date_range_invalid_format(self) -> None:
        """Prüft Fehlerbehandlung bei ungültigem Format."""
        with pytest.raises(ValueError, match="Ungültiges Date-Range-Format"):
            parse_date_range("2020-01-01")  # Fehlt :end_date

    def test_parse_date_range_invalid_date(self) -> None:
        """Prüft Fehlerbehandlung bei ungültigem Datum."""
        with pytest.raises(ValueError):
            parse_date_range("2020-13-01:2024-12-31")  # Monat 13 ungültig


# =============================================================================
# RUN-CONFIG GENERATION TESTS
# =============================================================================


class TestRunConfigGeneration:
    """Tests für generate_run_configs."""

    def test_generate_run_configs_cartesian_product(self) -> None:
        """Prüft, dass das kartesische Produkt korrekt erzeugt wird."""
        symbols = ["SPY", "QQQ"]
        date_ranges = ["2020-01-01:2024-01-01", "2022-01-01:2024-01-01"]
        mapping_variants = ["default", "conservative"]

        configs = generate_run_configs(symbols, date_ranges, mapping_variants)

        # 2 Symbole × 2 Date-Ranges × 2 Mappings = 8 Configs
        assert len(configs) == 8

    def test_generate_run_configs_single_combination(self) -> None:
        """Prüft eine einzelne Kombination."""
        configs = generate_run_configs(
            symbols=["SPY"],
            date_ranges=["2020-01-01:2024-01-01"],
            mapping_variants=["default"],
        )

        assert len(configs) == 1
        cfg = configs[0]
        assert cfg.symbol == "SPY"
        assert cfg.start_date == date(2020, 1, 1)
        assert cfg.end_date == date(2024, 1, 1)
        assert cfg.mapping_variant == "default"

    def test_generate_run_configs_date_range_label(self) -> None:
        """Prüft das date_range_label Property."""
        configs = generate_run_configs(
            symbols=["TEST"],
            date_ranges=["2020-01-01:2024-12-31"],
            mapping_variants=["default"],
        )

        assert configs[0].date_range_label == "2020-01-01 – 2024-12-31"

    def test_generate_run_configs_with_defaults(self) -> None:
        """Prüft Generierung mit Default-Werten."""
        configs = generate_run_configs(
            symbols=DEFAULT_SYMBOLS,
            date_ranges=DEFAULT_DATE_RANGES,
            mapping_variants=DEFAULT_MAPPING_VARIANTS,
        )

        expected_count = (
            len(DEFAULT_SYMBOLS)
            * len(DEFAULT_DATE_RANGES)
            * len(DEFAULT_MAPPING_VARIANTS)
        )
        assert len(configs) == expected_count


# =============================================================================
# BACKTEST RUN CONFIG TESTS
# =============================================================================


class TestBacktestRunConfig:
    """Tests für BacktestRunConfig Dataclass."""

    def test_backtest_run_config_frozen(self, sample_config: BacktestRunConfig) -> None:
        """Prüft, dass BacktestRunConfig immutable ist."""
        with pytest.raises(AttributeError):
            sample_config.symbol = "QQQ"  # type: ignore[misc]

    def test_backtest_run_config_date_range_label(
        self, sample_config: BacktestRunConfig
    ) -> None:
        """Prüft date_range_label Property."""
        assert sample_config.date_range_label == "2020-01-01 – 2024-01-01"


# =============================================================================
# BACKTEST RESULT TESTS
# =============================================================================


class TestBacktestResult:
    """Tests für BacktestResult Dataclass."""

    def test_backtest_result_creation(self) -> None:
        """Prüft Erstellung eines BacktestResult."""
        result = BacktestResult(
            symbol="TEST",
            date_range_label="2020-01-01 – 2024-01-01",
            mapping_variant="default",
            sharpe=1.5,
            max_drawdown=-0.20,
            annual_return=0.12,
            volatility=0.15,
            time_in_market=0.80,
        )

        assert result.symbol == "TEST"
        assert result.sharpe == 1.5
        assert result.max_drawdown == -0.20
        assert result.time_in_market == 0.80


# =============================================================================
# FORMATTING TESTS
# =============================================================================


class TestFormatting:
    """Tests für Formatierungs-Hilfsfunktionen."""

    def test_format_float_default_decimals(self) -> None:
        """Prüft _format_float mit Default-Dezimalstellen."""
        assert _format_float(1.2345) == "1.23"
        assert _format_float(0.1) == "0.10"

    def test_format_float_custom_decimals(self) -> None:
        """Prüft _format_float mit benutzerdefinierten Dezimalstellen."""
        assert _format_float(1.2345, decimals=3) == "1.234"
        assert _format_float(1.2345, decimals=0) == "1"

    def test_format_pct_default_decimals(self) -> None:
        """Prüft _format_pct mit Default-Dezimalstellen."""
        assert _format_pct(0.1234) == "12.3%"
        assert _format_pct(0.5) == "50.0%"

    def test_format_pct_custom_decimals(self) -> None:
        """Prüft _format_pct mit benutzerdefinierten Dezimalstellen."""
        assert _format_pct(0.12345, decimals=2) == "12.35%"

    def test_format_pct_negative(self) -> None:
        """Prüft _format_pct mit negativen Werten."""
        assert _format_pct(-0.20) == "-20.0%"


# =============================================================================
# MARKDOWN REPORT TESTS
# =============================================================================


class TestMarkdownReport:
    """Tests für Markdown-Report-Generierung."""

    def test_results_to_markdown_contains_header(
        self, sample_results: list[BacktestResult]
    ) -> None:
        """Prüft, dass der Report einen Header enthält."""
        markdown = results_to_markdown(
            results=sample_results,
            symbols=["SPY", "QQQ"],
            date_ranges=["2020-01-01:2024-01-01"],
            mapping_variants=["default", "conservative"],
        )

        assert "# R&D Report – El Karoui Volatility Model v1" in markdown

    def test_results_to_markdown_contains_setup(
        self, sample_results: list[BacktestResult]
    ) -> None:
        """Prüft, dass der Report das Experiment-Setup enthält."""
        symbols = ["SPY", "QQQ"]
        markdown = results_to_markdown(
            results=sample_results,
            symbols=symbols,
            date_ranges=["2020-01-01:2024-01-01"],
            mapping_variants=["default", "conservative"],
        )

        assert "## Experiment-Setup" in markdown
        assert "SPY" in markdown
        assert "QQQ" in markdown

    def test_results_to_markdown_contains_results_tables(
        self, sample_results: list[BacktestResult]
    ) -> None:
        """Prüft, dass der Report Ergebnis-Tabellen enthält."""
        markdown = results_to_markdown(
            results=sample_results,
            symbols=["SPY", "QQQ"],
            date_ranges=["2020-01-01:2024-01-01"],
            mapping_variants=["default", "conservative"],
        )

        assert "## Ergebnisse für SPY" in markdown
        assert "## Ergebnisse für QQQ" in markdown
        assert "| Date-Range | Mapping | Sharpe |" in markdown

    def test_results_to_markdown_contains_interpretation(
        self, sample_results: list[BacktestResult]
    ) -> None:
        """Prüft, dass der Report eine Interpretation enthält."""
        markdown = results_to_markdown(
            results=sample_results,
            symbols=["SPY"],
            date_ranges=["2020-01-01:2024-01-01"],
            mapping_variants=["default"],
        )

        assert "## Kurze Interpretation (generisch)" in markdown
        assert "LOW-Vol-Regime" in markdown
        assert "HIGH-Vol-Regime" in markdown

    def test_results_to_markdown_empty_results(self) -> None:
        """Prüft Report-Generierung mit leeren Ergebnissen."""
        markdown = results_to_markdown(
            results=[],
            symbols=["SPY"],
            date_ranges=["2020-01-01:2024-01-01"],
            mapping_variants=["default"],
        )

        # Header sollte trotzdem vorhanden sein
        assert "# R&D Report" in markdown
        assert "## Experiment-Setup" in markdown


# =============================================================================
# REPORT WRITING TESTS
# =============================================================================


class TestReportWriting:
    """Tests für Report-Schreiben."""

    def test_write_report_creates_file(self, temp_report_path: Path) -> None:
        """Prüft, dass write_report eine Datei erstellt."""
        markdown = "# Test Report\n\nTest content."

        write_report(markdown, temp_report_path)

        assert temp_report_path.exists()
        assert temp_report_path.read_text() == markdown

    def test_write_report_creates_parent_directories(self, tmp_path: Path) -> None:
        """Prüft, dass write_report Parent-Verzeichnisse erstellt."""
        deep_path = tmp_path / "nested" / "dir" / "report.md"
        markdown = "# Test"

        write_report(markdown, deep_path)

        assert deep_path.exists()

    def test_write_report_overwrites_existing(self, temp_report_path: Path) -> None:
        """Prüft, dass write_report bestehende Dateien überschreibt."""
        temp_report_path.write_text("Old content")

        write_report("New content", temp_report_path)

        assert temp_report_path.read_text() == "New content"


# =============================================================================
# CLI ARGUMENT PARSING TESTS
# =============================================================================


class TestCLIParsing:
    """Tests für CLI-Argument-Parsing."""

    def test_parse_cli_args_defaults(self) -> None:
        """Prüft Default-Werte für CLI-Argumente."""
        args = _parse_cli_args([])

        assert args.symbols == ",".join(DEFAULT_SYMBOLS)
        assert args.date_ranges == ",".join(DEFAULT_DATE_RANGES)
        assert args.mapping_variants == ",".join(DEFAULT_MAPPING_VARIANTS)
        assert args.output_path == str(REPORT_PATH)
        assert args.dry_run is False

    def test_parse_cli_args_custom_symbols(self) -> None:
        """Prüft Parsing von benutzerdefinierten Symbolen."""
        args = _parse_cli_args(["--symbols", "BTC,ETH"])

        assert args.symbols == "BTC,ETH"

    def test_parse_cli_args_custom_date_ranges(self) -> None:
        """Prüft Parsing von benutzerdefinierten Date-Ranges."""
        args = _parse_cli_args(["--date-ranges", "2022-01-01:2024-01-01"])

        assert args.date_ranges == "2022-01-01:2024-01-01"

    def test_parse_cli_args_dry_run(self) -> None:
        """Prüft Parsing von --dry-run Flag."""
        args = _parse_cli_args(["--dry-run"])

        assert args.dry_run is True

    def test_parse_cli_args_output_path(self) -> None:
        """Prüft Parsing von --output-path."""
        args = _parse_cli_args(["--output-path", "/tmp/custom_report.md"])

        assert args.output_path == "/tmp/custom_report.md"


# =============================================================================
# BACKTEST HOOK TESTS
# =============================================================================


class TestBacktestHook:
    """Tests für den Backtest-Hook."""

    def test_run_el_karoui_backtest_raises_not_implemented(
        self, sample_config: BacktestRunConfig
    ) -> None:
        """Prüft, dass run_el_karoui_backtest NotImplementedError raised."""
        with pytest.raises(NotImplementedError, match="Backtest-Infrastruktur"):
            run_el_karoui_backtest(sample_config)


# =============================================================================
# INTEGRATION / SMOKE TESTS
# =============================================================================


class TestSmoke:
    """Smoke-Tests für End-to-End-Funktionalität."""

    def test_full_workflow_with_mock_results(self, temp_report_path: Path) -> None:
        """Testet den Workflow mit Mock-Ergebnissen (ohne echte Backtests)."""
        # 1. Run-Configs generieren
        configs = generate_run_configs(
            symbols=["TEST"],
            date_ranges=["2023-01-01:2024-01-01"],
            mapping_variants=["default"],
        )
        assert len(configs) == 1

        # 2. Mock-Ergebnisse erstellen (simuliert erfolgreiche Backtests)
        results = [
            BacktestResult(
                symbol=cfg.symbol,
                date_range_label=cfg.date_range_label,
                mapping_variant=cfg.mapping_variant,
                sharpe=1.0,
                max_drawdown=-0.15,
                annual_return=0.10,
                volatility=0.12,
                time_in_market=0.70,
            )
            for cfg in configs
        ]

        # 3. Report generieren
        markdown = results_to_markdown(
            results=results,
            symbols=["TEST"],
            date_ranges=["2023-01-01:2024-01-01"],
            mapping_variants=["default"],
        )

        # 4. Report schreiben
        write_report(markdown, temp_report_path)

        # 5. Validierungen
        assert temp_report_path.exists()
        content = temp_report_path.read_text()
        assert "TEST" in content
        assert "El Karoui" in content
        assert "1.00" in content  # Sharpe

    def test_report_path_constant(self) -> None:
        """Prüft, dass REPORT_PATH korrekt gesetzt ist."""
        assert REPORT_PATH.name == "R_AND_D_EL_KAROUI_VOL_MODEL_V1.md"
        assert "reports" in str(REPORT_PATH)

    def test_defaults_are_valid(self) -> None:
        """Prüft, dass alle Default-Werte gültig sind."""
        assert len(DEFAULT_SYMBOLS) > 0
        assert len(DEFAULT_DATE_RANGES) > 0
        assert len(DEFAULT_MAPPING_VARIANTS) > 0

        # Alle Date-Ranges sollten parsbar sein
        for dr in DEFAULT_DATE_RANGES:
            start, end = parse_date_range(dr)
            assert start < end
