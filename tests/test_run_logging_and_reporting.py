# tests/test_run_logging_and_reporting.py
"""
Peak_Trade: Tests für Run-Logging und Reporting (Phase 32)
==========================================================

Tests für:
- LiveRunLogger (Logging von Shadow-/Paper-Runs)
- LiveRunEvent (Event-Datenstruktur)
- LiveRunMetadata (Metadaten)
- build_live_run_report (Report-Generierung)
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import pandas as pd
import pytest

from src.live.run_logging import (
    ShadowPaperLoggingConfig,
    LiveRunMetadata,
    LiveRunEvent,
    LiveRunLogger,
    generate_run_id,
    load_run_metadata,
    load_run_events,
    list_runs,
)
from src.reporting.live_run_report import (
    build_live_run_report,
    load_and_build_report,
    save_report,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def temp_run_dir():
    """Temporäres Verzeichnis für Run-Logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_logging_config() -> ShadowPaperLoggingConfig:
    """Sample-Logging-Konfiguration."""
    return ShadowPaperLoggingConfig(
        enabled=True,
        base_dir="test_runs",
        flush_interval_steps=10,
        format="parquet",
        write_markdown_report_on_finish=False,
        log_ohlc_details=True,
        log_order_details=True,
        log_risk_details=True,
    )


@pytest.fixture
def sample_metadata() -> LiveRunMetadata:
    """Sample-Metadaten."""
    return LiveRunMetadata(
        run_id="20251204_120000_paper_ma_crossover_BTC-EUR_1m",
        mode="paper",
        strategy_name="ma_crossover",
        symbol="BTC/EUR",
        timeframe="1m",
        started_at=datetime(2025, 12, 4, 12, 0, 0, tzinfo=timezone.utc),
        config_snapshot={"fee_rate": 0.0026},
    )


@pytest.fixture
def sample_events() -> List[LiveRunEvent]:
    """Sample-Events."""
    base_time = datetime(2025, 12, 4, 12, 0, 0, tzinfo=timezone.utc)
    events = []
    for i in range(10):
        events.append(
            LiveRunEvent(
                step=i + 1,
                ts_bar=base_time,
                ts_event=base_time,
                price=50000.0 + i * 10,
                open=50000.0 + i * 10,
                high=50100.0 + i * 10,
                low=49900.0 + i * 10,
                close=50000.0 + i * 10,
                volume=100.0,
                position_size=0.0 if i < 5 else 0.1,
                signal=0 if i < 3 else 1,
                signal_changed=i == 3,
                orders_generated=1 if i == 3 else 0,
                orders_filled=1 if i == 3 else 0,
                orders_rejected=0,
                orders_blocked=0,
                risk_allowed=True,
                risk_reasons="",
            )
        )
    return events


# =============================================================================
# Test: ShadowPaperLoggingConfig
# =============================================================================


class TestShadowPaperLoggingConfig:
    """Tests für ShadowPaperLoggingConfig."""

    def test_default_values(self):
        """Test: Default-Werte."""
        cfg = ShadowPaperLoggingConfig()
        assert cfg.enabled is True
        assert cfg.base_dir == "live_runs"
        assert cfg.flush_interval_steps == 50
        assert cfg.format == "parquet"

    def test_custom_values(self, sample_logging_config):
        """Test: Benutzerdefinierte Werte."""
        assert sample_logging_config.flush_interval_steps == 10
        assert sample_logging_config.format == "parquet"


# =============================================================================
# Test: LiveRunMetadata
# =============================================================================


class TestLiveRunMetadata:
    """Tests für LiveRunMetadata."""

    def test_to_dict(self, sample_metadata):
        """Test: Konvertierung zu Dictionary."""
        d = sample_metadata.to_dict()
        assert d["run_id"] == "20251204_120000_paper_ma_crossover_BTC-EUR_1m"
        assert d["mode"] == "paper"
        assert d["strategy_name"] == "ma_crossover"
        assert d["symbol"] == "BTC/EUR"
        assert "started_at" in d

    def test_from_dict(self, sample_metadata):
        """Test: Erstellung aus Dictionary."""
        d = sample_metadata.to_dict()
        restored = LiveRunMetadata.from_dict(d)
        assert restored.run_id == sample_metadata.run_id
        assert restored.mode == sample_metadata.mode
        assert restored.strategy_name == sample_metadata.strategy_name


# =============================================================================
# Test: LiveRunEvent
# =============================================================================


class TestLiveRunEvent:
    """Tests für LiveRunEvent."""

    def test_to_dict(self, sample_events):
        """Test: Konvertierung zu Dictionary."""
        event = sample_events[0]
        d = event.to_dict()
        assert d["step"] == 1
        assert d["signal"] == 0
        assert "ts_bar" in d

    def test_event_with_order(self, sample_events):
        """Test: Event mit Order."""
        # Event mit Order ist bei index 3
        order_event = sample_events[3]
        assert order_event.signal_changed is True
        assert order_event.orders_generated == 1
        assert order_event.orders_filled == 1


# =============================================================================
# Test: generate_run_id
# =============================================================================


class TestGenerateRunId:
    """Tests für generate_run_id."""

    def test_basic_generation(self):
        """Test: Basis-Generierung."""
        run_id = generate_run_id(
            mode="paper",
            strategy_name="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1m",
        )
        assert "paper" in run_id
        assert "ma_crossover" in run_id
        assert "BTC-EUR" in run_id  # / wird zu - konvertiert
        assert "1m" in run_id

    def test_with_timestamp(self):
        """Test: Mit explizitem Timestamp."""
        ts = datetime(2025, 12, 4, 15, 30, 0, tzinfo=timezone.utc)
        run_id = generate_run_id(
            mode="shadow",
            strategy_name="rsi",
            symbol="ETH/USD",
            timeframe="5m",
            timestamp=ts,
        )
        assert "20251204_153000" in run_id


# =============================================================================
# Test: LiveRunLogger
# =============================================================================


class TestLiveRunLogger:
    """Tests für LiveRunLogger."""

    def test_initialization(self, temp_run_dir, sample_logging_config, sample_metadata):
        """Test: Logger-Initialisierung."""
        sample_logging_config.base_dir = str(temp_run_dir)

        logger = LiveRunLogger(
            logging_cfg=sample_logging_config,
            metadata=sample_metadata,
        )

        assert logger.run_id == sample_metadata.run_id
        assert not logger.is_initialized

    def test_initialize_creates_directory(
        self, temp_run_dir, sample_logging_config, sample_metadata
    ):
        """Test: Initialisierung erstellt Verzeichnis."""
        sample_logging_config.base_dir = str(temp_run_dir)

        logger = LiveRunLogger(
            logging_cfg=sample_logging_config,
            metadata=sample_metadata,
        )
        logger.initialize()

        assert logger.run_dir.exists()
        assert (logger.run_dir / "meta.json").exists()

    def test_log_events(self, temp_run_dir, sample_logging_config, sample_metadata, sample_events):
        """Test: Events loggen."""
        sample_logging_config.base_dir = str(temp_run_dir)
        sample_logging_config.flush_interval_steps = 5  # Flush nach 5 Events

        logger = LiveRunLogger(
            logging_cfg=sample_logging_config,
            metadata=sample_metadata,
        )
        logger.initialize()

        for event in sample_events:
            logger.log_event(event)

        assert logger.total_events_logged == len(sample_events)

    def test_finalize(self, temp_run_dir, sample_logging_config, sample_metadata, sample_events):
        """Test: Logger finalisieren."""
        sample_logging_config.base_dir = str(temp_run_dir)

        logger = LiveRunLogger(
            logging_cfg=sample_logging_config,
            metadata=sample_metadata,
        )
        logger.initialize()

        for event in sample_events:
            logger.log_event(event)

        logger.finalize()

        # Events-Datei sollte existieren
        events_path = logger.run_dir / f"events.{sample_logging_config.format}"
        assert events_path.exists()

        # Meta sollte ended_at haben
        with open(logger.run_dir / "meta.json", "r") as f:
            meta = json.load(f)
        assert meta["ended_at"] is not None

    def test_context_manager(
        self, temp_run_dir, sample_logging_config, sample_metadata, sample_events
    ):
        """Test: Kontext-Manager-Nutzung."""
        sample_logging_config.base_dir = str(temp_run_dir)

        with LiveRunLogger(sample_logging_config, sample_metadata) as logger:
            for event in sample_events:
                logger.log_event(event)

        # Nach Exit sollte finalisiert sein
        events_path = logger.run_dir / f"events.{sample_logging_config.format}"
        assert events_path.exists()

    def test_disabled_logging(self, temp_run_dir, sample_metadata):
        """Test: Deaktiviertes Logging."""
        disabled_config = ShadowPaperLoggingConfig(enabled=False, base_dir=str(temp_run_dir))

        logger = LiveRunLogger(disabled_config, sample_metadata)
        logger.initialize()

        # Sollte kein Verzeichnis erstellen
        assert not logger.run_dir.exists()


# =============================================================================
# Test: Helper Functions
# =============================================================================


class TestHelperFunctions:
    """Tests für Helper-Funktionen."""

    def test_load_run_metadata(self, temp_run_dir, sample_logging_config, sample_metadata):
        """Test: Metadaten laden."""
        sample_logging_config.base_dir = str(temp_run_dir)

        with LiveRunLogger(sample_logging_config, sample_metadata) as logger:
            pass

        loaded_meta = load_run_metadata(logger.run_dir)
        assert loaded_meta.run_id == sample_metadata.run_id

    def test_load_run_events(
        self, temp_run_dir, sample_logging_config, sample_metadata, sample_events
    ):
        """Test: Events laden."""
        sample_logging_config.base_dir = str(temp_run_dir)

        with LiveRunLogger(sample_logging_config, sample_metadata) as logger:
            for event in sample_events:
                logger.log_event(event)

        events_df = load_run_events(logger.run_dir)
        assert len(events_df) == len(sample_events)

    def test_list_runs(self, temp_run_dir, sample_logging_config, sample_metadata):
        """Test: Runs auflisten."""
        sample_logging_config.base_dir = str(temp_run_dir)

        with LiveRunLogger(sample_logging_config, sample_metadata) as logger:
            pass

        runs = list_runs(str(temp_run_dir))
        assert len(runs) == 1
        assert sample_metadata.run_id in runs


# =============================================================================
# Test: Report Generation
# =============================================================================


class TestReportGeneration:
    """Tests für Report-Generierung."""

    def test_build_live_run_report(
        self, temp_run_dir, sample_logging_config, sample_metadata, sample_events
    ):
        """Test: Report erstellen."""
        sample_logging_config.base_dir = str(temp_run_dir)

        with LiveRunLogger(sample_logging_config, sample_metadata) as logger:
            for event in sample_events:
                logger.log_event(event)

        meta_path = logger.run_dir / "meta.json"
        events_path = logger.run_dir / f"events.{sample_logging_config.format}"

        report = build_live_run_report(meta_path, events_path)

        assert "Summary" in [s.title for s in report.sections]
        assert report.title == f"Live Run Report: {sample_metadata.run_id}"

    def test_load_and_build_report(
        self, temp_run_dir, sample_logging_config, sample_metadata, sample_events
    ):
        """Test: Report aus Verzeichnis erstellen."""
        sample_logging_config.base_dir = str(temp_run_dir)

        with LiveRunLogger(sample_logging_config, sample_metadata) as logger:
            for event in sample_events:
                logger.log_event(event)

        report = load_and_build_report(logger.run_dir)
        assert len(report.sections) > 0

    def test_report_to_markdown(
        self, temp_run_dir, sample_logging_config, sample_metadata, sample_events
    ):
        """Test: Report als Markdown."""
        sample_logging_config.base_dir = str(temp_run_dir)

        with LiveRunLogger(sample_logging_config, sample_metadata) as logger:
            for event in sample_events:
                logger.log_event(event)

        report = load_and_build_report(logger.run_dir)
        markdown = report.to_markdown()

        assert "# Live Run Report" in markdown
        assert "## Summary" in markdown

    def test_report_to_html(
        self, temp_run_dir, sample_logging_config, sample_metadata, sample_events
    ):
        """Test: Report als HTML."""
        sample_logging_config.base_dir = str(temp_run_dir)

        with LiveRunLogger(sample_logging_config, sample_metadata) as logger:
            for event in sample_events:
                logger.log_event(event)

        report = load_and_build_report(logger.run_dir)
        html = report.to_html()

        assert "<!DOCTYPE html>" in html
        assert "<h1>" in html

    def test_save_report(self, temp_run_dir, sample_logging_config, sample_metadata, sample_events):
        """Test: Report speichern."""
        sample_logging_config.base_dir = str(temp_run_dir)

        with LiveRunLogger(sample_logging_config, sample_metadata) as logger:
            for event in sample_events:
                logger.log_event(event)

        report = load_and_build_report(logger.run_dir)

        # Markdown speichern
        md_path = temp_run_dir / "test_report.md"
        save_report(report, md_path, format="markdown")
        assert md_path.exists()

        # HTML speichern
        html_path = temp_run_dir / "test_report.html"
        save_report(report, html_path, format="html")
        assert html_path.exists()


# =============================================================================
# Test: Integration with ShadowPaperSession
# =============================================================================


class TestSessionIntegration:
    """Tests für Integration mit ShadowPaperSession."""

    def test_session_with_run_logger(self, temp_run_dir, sample_logging_config, sample_metadata):
        """Test: Session mit Run-Logger erstellen."""
        from src.live.shadow_session import ShadowPaperSession
        from src.core.environment import EnvironmentConfig, TradingEnvironment
        from src.data.kraken_live import (
            ShadowPaperConfig,
            LiveExchangeConfig,
            FakeCandleSource,
            LiveCandle,
        )
        from src.execution.pipeline import ExecutionPipeline
        from src.orders.shadow import ShadowMarketContext
        from src.live.risk_limits import LiveRiskLimits, LiveRiskConfig

        # Minimal-Setup für Session
        env_config = EnvironmentConfig(
            environment=TradingEnvironment.PAPER,
            enable_live_trading=False,
        )

        shadow_cfg = ShadowPaperConfig(
            enabled=True,
            mode="paper",
            symbol="BTC/EUR",
            timeframe="1m",
            poll_interval_seconds=1.0,
            warmup_candles=10,
            start_balance=10000.0,
            position_fraction=0.1,
            fee_rate=0.0026,
            slippage_bps=5.0,
        )

        exchange_cfg = LiveExchangeConfig(
            name="test",
            use_sandbox=True,
            base_url="https://test.example.com",
        )

        # Fake-Datenquelle
        candles = [
            LiveCandle(
                timestamp=datetime(2025, 12, 4, 12, i, 0, tzinfo=timezone.utc),
                open=50000.0 + i * 10,
                high=50100.0 + i * 10,
                low=49900.0 + i * 10,
                close=50050.0 + i * 10,
                volume=100.0,
            )
            for i in range(20)
        ]
        fake_source = FakeCandleSource(candles=candles)

        # Minimal-Strategie
        class DummyStrategy:
            key = "dummy"

            def generate_signals(self, df):
                import pandas as pd

                return pd.Series([0] * len(df), index=df.index)

        strategy = DummyStrategy()

        # Pipeline
        market_context = ShadowMarketContext(fee_rate=0.0026, slippage_bps=5.0)
        pipeline = ExecutionPipeline.for_shadow(market_context=market_context)

        # Risk-Limits
        risk_config = LiveRiskConfig(
            enabled=False,
            base_currency="EUR",
            max_daily_loss_abs=None,
            max_daily_loss_pct=None,
            max_total_exposure_notional=None,
            max_symbol_exposure_notional=None,
            max_open_positions=None,
            max_order_notional=None,
            block_on_violation=False,
            use_experiments_for_daily_pnl=False,
        )
        risk_limits = LiveRiskLimits(config=risk_config)
        risk_limits.starting_cash = 10000.0

        # Run-Logger
        sample_logging_config.base_dir = str(temp_run_dir)
        run_logger = LiveRunLogger(sample_logging_config, sample_metadata)
        run_logger.initialize()

        # Session mit Logger erstellen
        session = ShadowPaperSession(
            env_config=env_config,
            shadow_cfg=shadow_cfg,
            exchange_cfg=exchange_cfg,
            data_source=fake_source,
            strategy=strategy,
            pipeline=pipeline,
            risk_limits=risk_limits,
            run_logger=run_logger,
        )

        assert session.run_logger is not None
        assert session.run_logger.run_id == sample_metadata.run_id
