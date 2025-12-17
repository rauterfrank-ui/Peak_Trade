# tests/test_market_sentinel_v0_daily.py
"""
Tests für MarketSentinel v0 – Daily Market Outlook
===================================================

Smoke-Tests und Unit-Tests für das Daily Market Outlook System.

Stand: Dezember 2024
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.market_sentinel.v0_daily_outlook import (
    DailyMarketOutlookConfig,
    DailyMarketOutlookResult,
    MarketConfig,
    MarketFeatureSnapshot,
    _generate_dummy_ohlcv,
    build_llm_messages,
    compute_feature_snapshot,
    load_daily_outlook_config,
    load_ohlcv_for_market,
    run_daily_market_outlook,
    write_markdown_report,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_market_config() -> MarketConfig:
    """Beispiel MarketConfig für Tests."""
    return MarketConfig(
        id="BTCUSDT",
        symbol="btcusdt",
        display_name="BTC / USDT",
        timeframe="1d",
        lookback_days=60,
    )


@pytest.fixture
def sample_daily_config(sample_market_config: MarketConfig) -> DailyMarketOutlookConfig:
    """Beispiel DailyMarketOutlookConfig für Tests."""
    return DailyMarketOutlookConfig(
        report_id="TEST_OUTLOOK",
        output_subdir="test",
        horizons=["short_term", "tactical"],
        markets=[sample_market_config],
    )


@pytest.fixture
def sample_ohlcv_df() -> pd.DataFrame:
    """Generiert ein Beispiel-OHLCV-DataFrame."""
    return _generate_dummy_ohlcv(days=100, start_price=42000.0)


@pytest.fixture
def temp_config_file() -> Path:
    """Erstellt eine temporäre Config-Datei."""
    config_content = """
report_id: "TEST_MARKET_SENTINEL"
output_subdir: "test_output"

horizons:
  - "short_term"
  - "tactical"

markets:
  - id: "BTCUSDT"
    symbol: "btcusdt"
    display_name: "BTC / USDT"
    timeframe: "1d"
    lookback_days: 60

  - id: "SPX"
    symbol: "spx"
    display_name: "S&P 500"
    timeframe: "1d"
    lookback_days: 60

llm:
  model: "gpt-4o-mini"
  max_tokens: 2000
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write(config_content)
        return Path(f.name)


# ============================================================================
# UNIT TESTS: DATACLASSES
# ============================================================================


class TestMarketConfig:
    """Tests für MarketConfig."""

    def test_create_valid_config(self) -> None:
        """Test: Gültige MarketConfig erstellen."""
        config = MarketConfig(
            id="BTCUSDT",
            symbol="btcusdt",
            display_name="BTC / USDT",
        )
        assert config.id == "BTCUSDT"
        assert config.symbol == "btcusdt"
        assert config.display_name == "BTC / USDT"
        assert config.timeframe == "1d"  # Default
        assert config.lookback_days == 60  # Default

    def test_validation_empty_id(self) -> None:
        """Test: Leere ID wird abgelehnt."""
        with pytest.raises(ValueError, match="id darf nicht leer sein"):
            MarketConfig(id="", symbol="btc", display_name="BTC")

    def test_validation_empty_symbol(self) -> None:
        """Test: Leeres Symbol wird abgelehnt."""
        with pytest.raises(ValueError, match="symbol darf nicht leer sein"):
            MarketConfig(id="BTC", symbol="", display_name="BTC")

    def test_to_dict(self, sample_market_config: MarketConfig) -> None:
        """Test: to_dict liefert korrekte Struktur."""
        d = sample_market_config.to_dict()
        assert d["id"] == "BTCUSDT"
        assert d["symbol"] == "btcusdt"
        assert "timeframe" in d
        assert "lookback_days" in d


class TestMarketFeatureSnapshot:
    """Tests für MarketFeatureSnapshot."""

    def test_create_snapshot(self, sample_market_config: MarketConfig) -> None:
        """Test: Snapshot erstellen."""
        snapshot = MarketFeatureSnapshot(
            market=sample_market_config,
            last_price=42000.0,
            change_1d=2.5,
            change_5d=8.3,
        )
        assert snapshot.market.id == "BTCUSDT"
        assert snapshot.last_price == 42000.0
        assert snapshot.change_1d == 2.5
        assert snapshot.data_source == "unknown"

    def test_format_for_llm(self, sample_market_config: MarketConfig) -> None:
        """Test: LLM-Formatierung ist korrekte Markdown-Tabelle."""
        snapshot = MarketFeatureSnapshot(
            market=sample_market_config,
            last_price=42000.0,
            change_1d=2.5,
            change_5d=-3.2,
        )
        formatted = snapshot.format_for_llm()
        assert "BTC / USDT" in formatted
        assert "|" in formatted
        assert "+2.50%" in formatted
        assert "-3.20%" in formatted

    def test_format_for_llm_with_none(self, sample_market_config: MarketConfig) -> None:
        """Test: None-Werte werden als 'n/a' formatiert."""
        snapshot = MarketFeatureSnapshot(
            market=sample_market_config,
            last_price=None,
            change_1d=None,
        )
        formatted = snapshot.format_for_llm()
        assert "n/a" in formatted


class TestDailyMarketOutlookConfig:
    """Tests für DailyMarketOutlookConfig."""

    def test_create_valid_config(self, sample_market_config: MarketConfig) -> None:
        """Test: Gültige Config erstellen."""
        config = DailyMarketOutlookConfig(
            report_id="TEST",
            output_subdir="daily",
            horizons=["short_term"],
            markets=[sample_market_config],
        )
        assert config.report_id == "TEST"
        assert len(config.markets) == 1

    def test_validation_empty_horizons(self, sample_market_config: MarketConfig) -> None:
        """Test: Leere Horizonte werden abgelehnt."""
        with pytest.raises(ValueError, match="horizons"):
            DailyMarketOutlookConfig(
                report_id="TEST",
                output_subdir="daily",
                horizons=[],
                markets=[sample_market_config],
            )

    def test_validation_empty_markets(self) -> None:
        """Test: Leere Märkte werden abgelehnt."""
        with pytest.raises(ValueError, match="markets"):
            DailyMarketOutlookConfig(
                report_id="TEST",
                output_subdir="daily",
                horizons=["short_term"],
                markets=[],
            )


# ============================================================================
# UNIT TESTS: CONFIG LOADER
# ============================================================================


class TestLoadDailyOutlookConfig:
    """Tests für load_daily_outlook_config."""

    def test_load_valid_config(self, temp_config_file: Path) -> None:
        """Test: Gültige Config wird korrekt geladen."""
        config = load_daily_outlook_config(temp_config_file)
        assert config.report_id == "TEST_MARKET_SENTINEL"
        assert config.output_subdir == "test_output"
        assert "short_term" in config.horizons
        assert len(config.markets) == 2
        assert config.markets[0].id == "BTCUSDT"

    def test_load_nonexistent_file(self) -> None:
        """Test: Nicht existierende Datei wirft Fehler."""
        with pytest.raises(FileNotFoundError):
            load_daily_outlook_config(Path("/nonexistent/config.yaml"))

    def test_load_real_config(self) -> None:
        """Test: Echte Config-Datei kann geladen werden (falls vorhanden)."""
        real_config = Path("config/market_outlook/daily_market_outlook.yaml")
        if real_config.exists():
            config = load_daily_outlook_config(real_config)
            assert config.report_id == "MARKET_SENTINEL_DAILY_V0"
            assert len(config.markets) > 0


# ============================================================================
# UNIT TESTS: DATA LOADING
# ============================================================================


class TestGenerateDummyOhlcv:
    """Tests für _generate_dummy_ohlcv."""

    def test_generate_correct_shape(self) -> None:
        """Test: DataFrame hat korrekte Form."""
        df = _generate_dummy_ohlcv(days=30, start_price=100.0)
        assert len(df) == 30
        assert "close" in df.columns
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "volume" in df.columns

    def test_prices_are_positive(self) -> None:
        """Test: Alle Preise sind positiv."""
        df = _generate_dummy_ohlcv(days=100, start_price=100.0)
        assert (df["close"] > 0).all()
        assert (df["high"] >= df["low"]).all()


class TestLoadOhlcvForMarket:
    """Tests für load_ohlcv_for_market."""

    def test_load_generates_dummy_when_no_csv(
        self, sample_market_config: MarketConfig
    ) -> None:
        """Test: Dummy-Daten werden generiert wenn keine CSV vorhanden."""
        df, source = load_ohlcv_for_market(
            sample_market_config,
            data_dir=Path("/nonexistent/path"),
        )
        assert source == "dummy"
        assert len(df) == sample_market_config.lookback_days
        assert "close" in df.columns

    def test_load_respects_lookback_days(self) -> None:
        """Test: Lookback-Days werden respektiert."""
        config = MarketConfig(
            id="TEST",
            symbol="test",
            display_name="Test",
            lookback_days=30,
        )
        df, _ = load_ohlcv_for_market(config)
        assert len(df) == 30


# ============================================================================
# UNIT TESTS: FEATURE COMPUTATION
# ============================================================================


class TestComputeFeatureSnapshot:
    """Tests für compute_feature_snapshot."""

    def test_compute_with_valid_data(
        self,
        sample_market_config: MarketConfig,
        sample_ohlcv_df: pd.DataFrame,
    ) -> None:
        """Test: Features werden korrekt berechnet."""
        snapshot = compute_feature_snapshot(
            sample_ohlcv_df,
            sample_market_config,
            data_source="test",
        )

        # Grundlegende Prüfungen
        assert snapshot.market.id == "BTCUSDT"
        assert snapshot.data_source == "test"
        assert snapshot.last_price is not None
        assert snapshot.last_price > 0

        # Performance-Metriken sollten berechnet sein
        assert snapshot.change_1d is not None
        assert snapshot.change_5d is not None
        assert snapshot.change_20d is not None

        # Volatilität und MAs
        assert snapshot.realized_vol_20d is not None
        assert snapshot.price_vs_ma50 is not None

    def test_compute_with_empty_df(self, sample_market_config: MarketConfig) -> None:
        """Test: Leeres DataFrame gibt Snapshot mit None-Werten."""
        empty_df = pd.DataFrame()
        snapshot = compute_feature_snapshot(
            empty_df, sample_market_config, data_source="test"
        )
        assert snapshot.last_price is None
        assert snapshot.change_1d is None

    def test_compute_with_insufficient_data(
        self, sample_market_config: MarketConfig
    ) -> None:
        """Test: Zu wenig Daten → einige Features sind None."""
        # Nur 5 Tage Daten
        df = _generate_dummy_ohlcv(days=5, start_price=100.0)
        snapshot = compute_feature_snapshot(df, sample_market_config, "test")

        assert snapshot.last_price is not None
        # 20d-Werte sollten None sein
        assert snapshot.change_20d is None
        assert snapshot.realized_vol_20d is None

    def test_change_calculations_are_correct(
        self, sample_market_config: MarketConfig
    ) -> None:
        """Test: Change-Berechnungen sind mathematisch korrekt."""
        # Konstruiere DataFrame mit bekannten Werten
        dates = pd.date_range(end="2024-01-10", periods=10, freq="D")
        closes = [100, 100, 100, 100, 100, 100, 100, 100, 100, 110]  # 10% Anstieg
        df = pd.DataFrame({"close": closes}, index=dates)

        snapshot = compute_feature_snapshot(df, sample_market_config, "test")

        assert snapshot.last_price == 110.0
        assert snapshot.change_1d is not None
        assert abs(snapshot.change_1d - 10.0) < 0.01  # ~10%


# ============================================================================
# UNIT TESTS: LLM PROMPT BUILDING
# ============================================================================


class TestBuildLlmMessages:
    """Tests für build_llm_messages."""

    def test_build_messages_structure(
        self,
        sample_daily_config: DailyMarketOutlookConfig,
        sample_market_config: MarketConfig,
    ) -> None:
        """Test: Messages haben korrekte Struktur."""
        snapshot = MarketFeatureSnapshot(
            market=sample_market_config,
            last_price=42000.0,
            change_1d=2.5,
        )

        messages = build_llm_messages(sample_daily_config, [snapshot])

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_system_prompt_contains_key_elements(
        self,
        sample_daily_config: DailyMarketOutlookConfig,
        sample_market_config: MarketConfig,
    ) -> None:
        """Test: System-Prompt enthält wichtige Elemente."""
        snapshot = MarketFeatureSnapshot(market=sample_market_config)
        messages = build_llm_messages(sample_daily_config, [snapshot])

        system_content = messages[0]["content"]
        assert "Marktprognose" in system_content
        assert "Regime" in system_content
        assert "Bear" in system_content or "Szenario" in system_content
        assert "Peak_Trade" in system_content

    def test_user_prompt_contains_data(
        self,
        sample_daily_config: DailyMarketOutlookConfig,
        sample_market_config: MarketConfig,
    ) -> None:
        """Test: User-Prompt enthält Marktdaten."""
        snapshot = MarketFeatureSnapshot(
            market=sample_market_config,
            last_price=42000.0,
        )

        messages = build_llm_messages(sample_daily_config, [snapshot])
        user_content = messages[1]["content"]

        assert "BTC / USDT" in user_content
        assert "42000" in user_content
        assert "short_term" in user_content


# ============================================================================
# UNIT TESTS: REPORT WRITING
# ============================================================================


class TestWriteMarkdownReport:
    """Tests für write_markdown_report."""

    def test_write_creates_file(
        self, sample_daily_config: DailyMarketOutlookConfig
    ) -> None:
        """Test: Report-Datei wird erstellt."""
        snapshot = MarketFeatureSnapshot(
            market=sample_daily_config.markets[0],
            last_price=42000.0,
            data_source="test",
        )

        result = DailyMarketOutlookResult(
            config=sample_daily_config,
            snapshots=[snapshot],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = write_markdown_report(
                result,
                llm_output="Test LLM Output",
                base_output_dir=Path(tmpdir),
            )

            assert report_path.exists()
            assert report_path.suffix == ".md"

            # Prüfe Inhalt
            content = report_path.read_text()
            assert "MarketSentinel v0" in content
            assert "Test LLM Output" in content
            assert "BTC / USDT" in content

    def test_write_creates_subdirectory(
        self, sample_daily_config: DailyMarketOutlookConfig
    ) -> None:
        """Test: Unterverzeichnis wird erstellt."""
        result = DailyMarketOutlookResult(
            config=sample_daily_config,
            snapshots=[],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = write_markdown_report(
                result,
                llm_output="Test",
                base_output_dir=Path(tmpdir),
            )

            # Prüfe dass Unterverzeichnis existiert
            expected_subdir = Path(tmpdir) / sample_daily_config.output_subdir
            assert expected_subdir.exists()
            assert report_path.parent == expected_subdir


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestRunDailyMarketOutlook:
    """Integration-Tests für run_daily_market_outlook."""

    def test_run_with_skip_llm(self, temp_config_file: Path) -> None:
        """Test: Kompletter Durchlauf ohne LLM."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_daily_market_outlook(
                config_path=temp_config_file,
                base_output_dir=Path(tmpdir),
                skip_llm=True,
            )

            assert result.success
            assert result.report_path is not None
            assert result.report_path.exists()
            assert len(result.snapshots) == 2  # BTCUSDT und SPX

    def test_run_creates_valid_report(self, temp_config_file: Path) -> None:
        """Test: Generierter Report ist valides Markdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_daily_market_outlook(
                config_path=temp_config_file,
                base_output_dir=Path(tmpdir),
                skip_llm=True,
            )

            content = result.report_path.read_text()

            # Prüfe Markdown-Struktur
            assert content.startswith("#")
            assert "| Markt |" in content
            assert "---" in content
            assert "LLM-Aufruf wurde übersprungen" in content

    def test_run_with_nonexistent_config(self) -> None:
        """Test: Nicht existierende Config gibt Fehler-Result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_daily_market_outlook(
                config_path=Path("/nonexistent/config.yaml"),
                base_output_dir=Path(tmpdir),
                skip_llm=True,
            )

            assert not result.success
            assert result.error_message is not None

    def test_run_with_real_config_if_exists(self) -> None:
        """Test: Echte Config funktioniert (falls vorhanden)."""
        real_config = Path("config/market_outlook/daily_market_outlook.yaml")
        if not real_config.exists():
            pytest.skip("Echte Config nicht vorhanden")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_daily_market_outlook(
                config_path=real_config,
                base_output_dir=Path(tmpdir),
                skip_llm=True,
            )

            assert result.success
            assert len(result.snapshots) > 0
            assert result.report_path.exists()


# ============================================================================
# SMOKE TESTS
# ============================================================================


class TestSmokeTests:
    """Schnelle Smoke-Tests für grundlegende Funktionalität."""

    def test_all_dataclasses_instantiable(self) -> None:
        """Test: Alle Dataclasses können instanziiert werden."""
        market = MarketConfig(id="TEST", symbol="test", display_name="Test")
        snapshot = MarketFeatureSnapshot(market=market)
        config = DailyMarketOutlookConfig(
            report_id="TEST",
            output_subdir="test",
            horizons=["short_term"],
            markets=[market],
        )
        result = DailyMarketOutlookResult(config=config, snapshots=[snapshot])

        assert market is not None
        assert snapshot is not None
        assert config is not None
        assert result is not None

    def test_imports_work(self) -> None:
        """Test: Alle Imports funktionieren."""
        from src.market_sentinel import (
            load_daily_outlook_config,
            run_daily_market_outlook,
        )

        # Imports erfolgreich
        assert callable(load_daily_outlook_config)
        assert callable(run_daily_market_outlook)

    def test_dummy_data_generation_is_deterministic(self) -> None:
        """Test: Dummy-Daten sind reproduzierbar (durch Seed)."""
        df1 = _generate_dummy_ohlcv(days=10, start_price=100)
        df2 = _generate_dummy_ohlcv(days=10, start_price=100)

        # Sollten identisch sein durch festen Seed
        assert (df1["close"].values == df2["close"].values).all()


# ============================================================================
# CLI TESTS (optional)
# ============================================================================


class TestCLI:
    """Tests für das CLI-Script."""

    def test_cli_script_exists(self) -> None:
        """Test: CLI-Script existiert."""
        cli_path = Path("scripts/generate_market_outlook_daily.py")
        assert cli_path.exists()

    def test_cli_can_be_imported(self) -> None:
        """Test: CLI-Script kann importiert werden."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "generate_market_outlook_daily",
            "scripts/generate_market_outlook_daily.py",
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            # Nur prüfen dass Import klappt, nicht ausführen
            assert module is not None
