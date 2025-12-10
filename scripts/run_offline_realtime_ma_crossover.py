#!/usr/bin/env python3
"""
Offline-Realtime MA-Crossover Pipeline mit CLI-Flags
=====================================================

Führt eine MA-Crossover-Strategie im offline_realtime_pipeline-Modus aus.

Features:
- CLI-Parameter für Symbol, n-steps, n-regimes, MA-Fenster
- Synth-Session für synthetische Marktdaten
- OfflineRealtimeFeed für realistische Daten-Wiedergabe
- ExecutionPipeline mit PaperOrderExecutor
- HTML-Report-Generierung

Workflow:
    1. CLI-Args parsen
    2. Synth-Session bauen (n_steps, n_regimes)
    3. OfflineRealtimeFeed aus Synth-Result erstellen
    4. MACrossoverStrategy mit CLI-Parametern instanziieren
    5. ExecutionPipeline aufsetzen
    6. Pipeline ausführen
    7. Report generieren

Usage:
    python scripts/run_offline_realtime_ma_crossover.py \
        --symbol BTC/EUR \
        --n-steps 1000 \
        --n-regimes 5 \
        --fast-window 10 \
        --slow-window 30
"""
from __future__ import annotations

import argparse
import logging
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Python-Path anpassen für src-Import
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd

# Core imports
from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.strategies.ma_crossover import MACrossoverStrategy
from src.orders.paper import PaperOrderExecutor, PaperMarketContext
from src.execution.pipeline import ExecutionPipeline, ExecutionPipelineConfig

logger = logging.getLogger(__name__)


# =============================================================================
# Symbol-Normalisierung
# =============================================================================


def normalize_symbol(symbol: str) -> str:
    """
    Normalisiert ein Trading-Symbol für interne Verwendung.
    
    Konvertiert z.B. "BTC/EUR" -> "BTCEUR" für Exchange-API-Kompatibilität.
    
    Args:
        symbol: Symbol im Format "BASE/QUOTE" (z.B. "BTC/EUR")
    
    Returns:
        Normalisiertes Symbol ohne "/" (z.B. "BTCEUR")
    
    Example:
        >>> normalize_symbol("BTC/EUR")
        'BTCEUR'
        >>> normalize_symbol("ETH/USD")
        'ETHUSD'
    """
    return symbol.replace("/", "").upper()


# =============================================================================
# Offline-Synth-Session (Platzhalter-Implementierung)
# =============================================================================


@dataclass
class OfflineSynthSessionConfig:
    """
    Konfiguration für Offline-Synth-Session.
    
    Attributes:
        n_steps: Anzahl der zu generierenden Ticks/Bars
        n_regimes: Anzahl der Regime-Wechsel im synthetischen Verlauf
        seed: Random-Seed für Reproduzierbarkeit
        base_price: Start-Preis
        volatility: Volatilität für Preis-Simulation
    """
    n_steps: int = 1000
    n_regimes: int = 3
    seed: int = 42
    base_price: float = 50000.0
    volatility: float = 0.02


@dataclass
class OfflineSynthSessionResult:
    """
    Ergebnis einer Offline-Synth-Session.
    
    Attributes:
        df: DataFrame mit OHLCV-Daten (timestamp, open, high, low, close, volume)
        config: Verwendete Config
        symbol: Trading-Symbol
        run_id: Eindeutige Run-ID
        metadata: Zusätzliche Metadaten
    """
    df: pd.DataFrame
    config: OfflineSynthSessionConfig
    symbol: str
    run_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def run_offline_synth_session(
    config: OfflineSynthSessionConfig,
    symbol: str,
) -> OfflineSynthSessionResult:
    """
    Führt eine Offline-Synth-Session aus und generiert synthetische Marktdaten.
    
    Diese Implementierung ist ein Platzhalter und generiert einfache
    synthetische OHLCV-Daten mit Random-Walk und Regime-Switching.
    
    Args:
        config: Synth-Session-Konfiguration
        symbol: Trading-Symbol
    
    Returns:
        OfflineSynthSessionResult mit generierten Daten
    """
    logger.info(
        f"[SYNTH] Starting offline synth session: "
        f"symbol={symbol}, n_steps={config.n_steps}, n_regimes={config.n_regimes}, seed={config.seed}"
    )
    
    np.random.seed(config.seed)
    
    # Timestamps generieren (minütliche Bars)
    start_time = pd.Timestamp("2024-01-01", tz="UTC")
    timestamps = pd.date_range(start=start_time, periods=config.n_steps, freq="1min")
    
    # Regime-Wechsel einbauen
    regime_lengths = np.diff(
        np.linspace(0, config.n_steps, config.n_regimes + 1, dtype=int)
    )
    regimes = np.repeat(np.arange(config.n_regimes), regime_lengths)
    
    # Regime-spezifische Drifts und Volatilitäten
    regime_drift = np.random.randn(config.n_regimes) * 0.0001
    regime_vol = np.abs(np.random.randn(config.n_regimes)) * config.volatility
    
    # Preis-Pfad generieren (Random Walk mit Regime-Switching)
    returns = np.zeros(config.n_steps)
    for i in range(config.n_steps):
        regime = regimes[i]
        returns[i] = regime_drift[regime] + regime_vol[regime] * np.random.randn()
    
    prices = config.base_price * np.exp(np.cumsum(returns))
    
    # OHLCV-Daten generieren (vereinfacht)
    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": prices * (1 + np.random.randn(config.n_steps) * 0.0001),
        "high": prices * (1 + np.abs(np.random.randn(config.n_steps)) * 0.0005),
        "low": prices * (1 - np.abs(np.random.randn(config.n_steps)) * 0.0005),
        "close": prices,
        "volume": np.random.uniform(0.1, 10.0, config.n_steps),
    })
    
    # High/Low korrigieren (müssen Open/Close umfassen)
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    
    run_id = f"synth_{symbol}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    logger.info(
        f"[SYNTH] Generated {len(df)} bars. "
        f"Price range: {df['close'].min():.2f} - {df['close'].max():.2f}"
    )
    
    return OfflineSynthSessionResult(
        df=df,
        config=config,
        symbol=symbol,
        run_id=run_id,
        metadata={
            "start_time": timestamps[0].isoformat(),
            "end_time": timestamps[-1].isoformat(),
            "n_bars": len(df),
        },
    )


# =============================================================================
# Offline-Realtime-Feed (Platzhalter-Implementierung)
# =============================================================================


@dataclass
class OfflineRealtimeFeedConfig:
    """
    Konfiguration für Offline-Realtime-Feed.
    
    Attributes:
        symbol: Trading-Symbol
        playback_mode: "fast_forward" (ohne Delays) oder "realtime" (mit Delays)
        speed_factor: Geschwindigkeitsfaktor (nur für "realtime"-Modus)
    """
    symbol: str
    playback_mode: str = "fast_forward"
    speed_factor: float = 10.0


class OfflineRealtimeFeed:
    """
    Feed für Offline-Realtime-Wiedergabe von Synth-Daten.
    
    Simuliert einen Live-Feed durch sequentielle Wiedergabe
    von vorab generierten Daten.
    """
    
    def __init__(
        self,
        df: pd.DataFrame,
        config: OfflineRealtimeFeedConfig,
    ) -> None:
        """
        Initialisiert den Offline-Realtime-Feed.
        
        Args:
            df: DataFrame mit OHLCV-Daten
            config: Feed-Konfiguration
        """
        self.df = df
        self.config = config
        self._current_idx = 0
    
    @classmethod
    def from_synth_session_result(
        cls,
        result: OfflineSynthSessionResult,
        config: OfflineRealtimeFeedConfig,
    ) -> "OfflineRealtimeFeed":
        """
        Factory-Methode: Erstellt Feed aus Synth-Session-Result.
        
        Args:
            result: Synth-Session-Result
            config: Feed-Konfiguration
        
        Returns:
            OfflineRealtimeFeed-Instanz
        """
        return cls(df=result.df, config=config)
    
    def get_data(self) -> pd.DataFrame:
        """Gibt die kompletten Daten zurück (für Backtest-Modus)."""
        return self.df.copy()
    
    def reset(self) -> None:
        """Setzt den Feed zurück auf den Anfang."""
        self._current_idx = 0


# =============================================================================
# Reporting
# =============================================================================


@dataclass
class OfflineRealtimePipelineStats:
    """
    Performance-Statistiken für Offline-Realtime-Pipeline.
    
    Attributes:
        run_id: Eindeutige Run-ID
        run_type: Run-Typ ("offline_realtime_pipeline")
        symbol: Trading-Symbol
        strategy_id: Strategy-Identifier
        env_mode: Environment-Modus ("paper")
        
        # Synth-Settings
        synth_n_steps: Anzahl der Synth-Steps
        synth_n_regimes: Anzahl der Regime-Wechsel
        synth_seed: Random-Seed
        
        # Strategy-Settings
        fast_window: Fast-MA-Window
        slow_window: Slow-MA-Window
        
        # Performance-Metriken
        n_ticks: Anzahl der verarbeiteten Ticks
        n_orders: Anzahl der generierten Orders
        n_trades: Anzahl der ausgeführten Trades
        gross_pnl: Brutto-PnL
        net_pnl: Netto-PnL (nach Fees)
        fees_paid: Gezahlte Fees
        max_drawdown: Maximaler Drawdown
        
        # Timing
        started_at: Start-Zeitpunkt
        finished_at: End-Zeitpunkt
        duration_seconds: Laufzeit in Sekunden
        
        # Metadata
        metadata: Zusätzliche Metadaten
    """
    run_id: str
    run_type: str
    symbol: str
    strategy_id: str
    env_mode: str
    
    synth_n_steps: int
    synth_n_regimes: int
    synth_seed: int
    
    fast_window: int
    slow_window: int
    
    n_ticks: int = 0
    n_orders: int = 0
    n_trades: int = 0
    gross_pnl: float = 0.0
    net_pnl: float = 0.0
    fees_paid: float = 0.0
    max_drawdown: float = 0.0
    
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    metadata: Dict[str, Any] = field(default_factory=dict)


def write_offline_realtime_report(
    stats: OfflineRealtimePipelineStats,
    output_dir: Path,
) -> Path:
    """
    Schreibt einen HTML-Report für Offline-Realtime-Pipeline.
    
    Args:
        stats: Pipeline-Statistiken
        output_dir: Output-Verzeichnis
    
    Returns:
        Pfad zum generierten HTML-Report
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "summary.html"
    
    # HTML-Report generieren (vereinfacht)
    html_content = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offline-Realtime-Pipeline Report - {stats.run_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            margin: 40px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }}
        .section {{
            margin: 20px 0;
        }}
        .metric {{
            display: grid;
            grid-template-columns: 250px 1fr;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .metric-label {{
            font-weight: 600;
            color: #666;
        }}
        .metric-value {{
            color: #333;
        }}
        .metric-value.positive {{
            color: #28a745;
        }}
        .metric-value.negative {{
            color: #dc3545;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.9em;
            font-weight: 600;
        }}
        .status-badge.success {{
            background: #d4edda;
            color: #155724;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Offline-Realtime-Pipeline Report</h1>
        
        <div class="section">
            <h2>📊 Run-Informationen</h2>
            <div class="metric">
                <div class="metric-label">Run-ID:</div>
                <div class="metric-value"><code>{stats.run_id}</code></div>
            </div>
            <div class="metric">
                <div class="metric-label">Run-Type:</div>
                <div class="metric-value"><span class="status-badge success">{stats.run_type}</span></div>
            </div>
            <div class="metric">
                <div class="metric-label">Symbol:</div>
                <div class="metric-value"><strong>{stats.symbol}</strong></div>
            </div>
            <div class="metric">
                <div class="metric-label">Strategie:</div>
                <div class="metric-value">{stats.strategy_id}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Environment:</div>
                <div class="metric-value">{stats.env_mode}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Started:</div>
                <div class="metric-value">{stats.started_at.strftime('%Y-%m-%d %H:%M:%S UTC') if stats.started_at else 'N/A'}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Finished:</div>
                <div class="metric-value">{stats.finished_at.strftime('%Y-%m-%d %H:%M:%S UTC') if stats.finished_at else 'N/A'}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Duration:</div>
                <div class="metric-value">{stats.duration_seconds:.2f}s</div>
            </div>
        </div>
        
        <div class="section">
            <h2>🎲 Synth-Session-Einstellungen</h2>
            <div class="metric">
                <div class="metric-label">N-Steps:</div>
                <div class="metric-value">{stats.synth_n_steps:,}</div>
            </div>
            <div class="metric">
                <div class="metric-label">N-Regimes:</div>
                <div class="metric-value">{stats.synth_n_regimes}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Seed:</div>
                <div class="metric-value">{stats.synth_seed}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Strategie-Parameter</h2>
            <div class="metric">
                <div class="metric-label">Fast-Window:</div>
                <div class="metric-value">{stats.fast_window}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Slow-Window:</div>
                <div class="metric-value">{stats.slow_window}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>💰 Performance-Metriken</h2>
            <div class="metric">
                <div class="metric-label">Verarbeitete Ticks:</div>
                <div class="metric-value">{stats.n_ticks:,}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Generierte Orders:</div>
                <div class="metric-value">{stats.n_orders}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Ausgeführte Trades:</div>
                <div class="metric-value">{stats.n_trades}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Brutto-PnL:</div>
                <div class="metric-value {'positive' if stats.gross_pnl >= 0 else 'negative'}">{stats.gross_pnl:,.2f} EUR</div>
            </div>
            <div class="metric">
                <div class="metric-label">Netto-PnL:</div>
                <div class="metric-value {'positive' if stats.net_pnl >= 0 else 'negative'}"><strong>{stats.net_pnl:,.2f} EUR</strong></div>
            </div>
            <div class="metric">
                <div class="metric-label">Gezahlte Fees:</div>
                <div class="metric-value">{stats.fees_paid:,.2f} EUR</div>
            </div>
            <div class="metric">
                <div class="metric-label">Max-Drawdown:</div>
                <div class="metric-value negative">{stats.max_drawdown:,.2f} EUR</div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Peak_Trade Offline-Realtime-Pipeline</p>
            <p>Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    report_path.write_text(html_content, encoding="utf-8")
    logger.info(f"[REPORT] HTML-Report geschrieben: {report_path}")
    
    return report_path


# =============================================================================
# Pipeline-Builder
# =============================================================================


def build_offline_ma_crossover_pipeline(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Baut die komplette Offline-MA-Crossover-Pipeline.
    
    Args:
        args: Geparste CLI-Argumente
    
    Returns:
        Dict mit Pipeline-Komponenten:
        - synth_result: Synth-Session-Result
        - feed: OfflineRealtimeFeed
        - strategy: MACrossoverStrategy
        - pipeline: ExecutionPipeline
        - env_config: EnvironmentConfig
        - run_id: Run-ID
    """
    # 1. Symbol normalisieren
    internal_symbol = normalize_symbol(args.symbol)
    logger.info(f"[BUILD] Symbol: {args.symbol} -> {internal_symbol}")
    
    # 2. Synth-Session-Config erstellen
    synth_cfg = OfflineSynthSessionConfig(
        n_steps=args.n_steps,
        n_regimes=args.n_regimes,
        seed=args.seed,
    )
    
    # 3. Synth-Session ausführen
    synth_result = run_offline_synth_session(
        config=synth_cfg,
        symbol=internal_symbol,
    )
    
    # 4. OfflineRealtimeFeed erstellen
    feed_cfg = OfflineRealtimeFeedConfig(
        symbol=internal_symbol,
        playback_mode=args.playback_mode,
        speed_factor=args.speed_factor,
    )
    feed = OfflineRealtimeFeed.from_synth_session_result(synth_result, feed_cfg)
    logger.info(f"[BUILD] Feed erstellt: {feed.config.playback_mode}-Modus")
    
    # 5. MACrossoverStrategy erstellen
    strategy = MACrossoverStrategy(
        fast_window=args.fast_window,
        slow_window=args.slow_window,
    )
    logger.info(
        f"[BUILD] Strategie erstellt: MA-Crossover "
        f"(fast={args.fast_window}, slow={args.slow_window})"
    )
    
    # 6. Environment-Config
    env_config = EnvironmentConfig(
        environment=TradingEnvironment.PAPER,
        enable_live_trading=False,
        log_all_orders=True,
    )
    
    # 7. PaperOrderExecutor & ExecutionPipeline
    market_ctx = PaperMarketContext(
        prices={internal_symbol: synth_result.df["close"].iloc[0]},
        fee_bps=10.0,  # 0.1% Fees
        slippage_bps=5.0,  # 0.05% Slippage
    )
    executor = PaperOrderExecutor(market_ctx)
    
    pipeline_cfg = ExecutionPipelineConfig(
        default_order_type="market",
        max_position_notional_pct=1.0,
        log_executions=True,
    )
    pipeline = ExecutionPipeline(
        executor=executor,
        config=pipeline_cfg,
        env_config=env_config,
    )
    logger.info("[BUILD] Execution-Pipeline erstellt")
    
    return {
        "synth_result": synth_result,
        "feed": feed,
        "strategy": strategy,
        "pipeline": pipeline,
        "env_config": env_config,
        "run_id": synth_result.run_id,
        "internal_symbol": internal_symbol,
    }


# =============================================================================
# Pipeline-Ausführung
# =============================================================================


def run_pipeline(
    pipeline: ExecutionPipeline,
    strategy: MACrossoverStrategy,
    feed: OfflineRealtimeFeed,
    symbol: str,
) -> Dict[str, Any]:
    """
    Führt die Pipeline aus.
    
    Args:
        pipeline: ExecutionPipeline
        strategy: MACrossoverStrategy
        feed: OfflineRealtimeFeed
        symbol: Trading-Symbol
    
    Returns:
        Dict mit Performance-Metriken
    """
    logger.info("[RUN] Starte Pipeline-Ausführung...")
    
    # Daten vom Feed holen
    df = feed.get_data()
    
    # Signale generieren
    logger.info("[RUN] Generiere Signale...")
    signals = strategy.generate_signals(df)
    logger.info(f"[RUN] {len(signals)} Signale generiert")
    
    # Pipeline ausführen
    logger.info("[RUN] Führe Orders aus...")
    results = pipeline.execute_from_signals(
        signals=signals,
        prices=df["close"],
        symbol=symbol,
        base_currency="EUR",
        quote_currency=symbol.replace("EUR", "").replace("/", ""),
    )
    
    logger.info(f"[RUN] {len(results)} Order-Results")
    
    # Performance-Metriken berechnen
    summary = pipeline.get_execution_summary()
    
    # PnL berechnen (vereinfacht)
    filled_results = [r for r in results if r.is_filled and r.fill]
    
    gross_pnl = 0.0
    fees_paid = 0.0
    position = 0.0
    entry_price = 0.0
    
    for result in filled_results:
        fill = result.fill
        
        if fill.side == "buy":
            if position == 0:
                # Entry Long
                position = fill.quantity
                entry_price = fill.price
            else:
                # Add to Long
                position += fill.quantity
        else:  # sell
            if position > 0:
                # Exit Long
                pnl = (fill.price - entry_price) * min(fill.quantity, position)
                gross_pnl += pnl
                position -= fill.quantity
                if position <= 0:
                    position = 0
                    entry_price = 0
        
        if fill.fee:
            fees_paid += fill.fee
    
    net_pnl = gross_pnl - fees_paid
    
    # Drawdown berechnen (vereinfacht)
    equity_curve = [0.0]
    current_equity = 0.0
    position = 0.0
    entry_price = 0.0
    
    for result in filled_results:
        fill = result.fill
        
        if fill.side == "buy":
            if position == 0:
                entry_price = fill.price
            position += fill.quantity
            current_equity -= fill.fee or 0
        else:
            if position > 0:
                pnl = (fill.price - entry_price) * min(fill.quantity, position)
                current_equity += pnl - (fill.fee or 0)
                position -= fill.quantity
        
        equity_curve.append(current_equity)
    
    # Max Drawdown
    peak = equity_curve[0]
    max_dd = 0.0
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        dd = peak - equity
        if dd > max_dd:
            max_dd = dd
    
    logger.info(
        f"[RUN] Performance: Brutto-PnL={gross_pnl:.2f}, "
        f"Netto-PnL={net_pnl:.2f}, Fees={fees_paid:.2f}, MaxDD={max_dd:.2f}"
    )
    
    return {
        "n_ticks": len(df),
        "n_orders": summary["total_orders"],
        "n_trades": summary["filled_orders"],
        "gross_pnl": gross_pnl,
        "net_pnl": net_pnl,
        "fees_paid": fees_paid,
        "max_drawdown": max_dd,
    }


# =============================================================================
# CLI-Parser
# =============================================================================


def parse_args() -> argparse.Namespace:
    """
    Parsed CLI-Argumente.
    
    Returns:
        argparse.Namespace mit geparsten Argumenten
    """
    parser = argparse.ArgumentParser(
        description="Offline-Realtime MA-Crossover Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic run mit Defaults
  python scripts/run_offline_realtime_ma_crossover.py
  
  # Custom Symbol und MA-Fenster
  python scripts/run_offline_realtime_ma_crossover.py \\
      --symbol BTC/EUR \\
      --fast-window 10 \\
      --slow-window 30
  
  # Lange Simulation mit vielen Regimes
  python scripts/run_offline_realtime_ma_crossover.py \\
      --symbol ETH/USD \\
      --n-steps 10000 \\
      --n-regimes 10 \\
      --fast-window 20 \\
      --slow-window 50
        """,
    )
    
    # Symbol
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTC/EUR",
        help="Trading-Symbol (z.B. BTC/EUR, ETH/USD). Default: BTC/EUR",
    )
    
    # Synth-Session-Parameter
    parser.add_argument(
        "--n-steps",
        type=int,
        default=1000,
        help="Anzahl der zu generierenden Ticks/Bars. Default: 1000",
    )
    parser.add_argument(
        "--n-regimes",
        type=int,
        default=3,
        help="Anzahl der Regime-Wechsel. Default: 3",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random-Seed für Reproduzierbarkeit. Default: 42",
    )
    
    # MA-Crossover-Parameter
    parser.add_argument(
        "--fast-window",
        type=int,
        default=20,
        help="Fast-MA-Periode. Default: 20",
    )
    parser.add_argument(
        "--slow-window",
        type=int,
        default=50,
        help="Slow-MA-Periode. Default: 50",
    )
    
    # Feed-Parameter
    parser.add_argument(
        "--playback-mode",
        type=str,
        choices=["fast_forward", "realtime"],
        default="fast_forward",
        help="Playback-Modus. Default: fast_forward",
    )
    parser.add_argument(
        "--speed-factor",
        type=float,
        default=10.0,
        help="Geschwindigkeitsfaktor für realtime-Modus. Default: 10.0",
    )
    
    # Output
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output-Verzeichnis für Reports. Default: reports/offline_realtime_pipeline/<run_id>",
    )
    
    # Logging
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Aktiviert verbose Logging",
    )
    
    args = parser.parse_args()
    
    # Validierung
    if args.fast_window >= args.slow_window:
        parser.error(
            f"fast-window ({args.fast_window}) muss < slow-window ({args.slow_window}) sein"
        )
    
    if args.n_steps < args.slow_window:
        parser.error(
            f"n-steps ({args.n_steps}) muss >= slow-window ({args.slow_window}) sein"
        )
    
    return args


# =============================================================================
# Main
# =============================================================================


def main() -> int:
    """
    Main-Einstiegspunkt.
    
    Returns:
        Exit-Code (0 = Erfolg, 1 = Fehler)
    """
    # CLI-Args parsen
    args = parse_args()
    
    # Logging konfigurieren
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    logger.info("=" * 80)
    logger.info("Offline-Realtime MA-Crossover Pipeline")
    logger.info("=" * 80)
    logger.info(f"Symbol: {args.symbol}")
    logger.info(f"N-Steps: {args.n_steps:,}")
    logger.info(f"N-Regimes: {args.n_regimes}")
    logger.info(f"Fast-Window: {args.fast_window}")
    logger.info(f"Slow-Window: {args.slow_window}")
    logger.info(f"Playback-Mode: {args.playback_mode}")
    logger.info("=" * 80)
    
    try:
        # Startzeit
        started_at = datetime.now(timezone.utc)
        
        # Pipeline bauen
        logger.info("[MAIN] Baue Pipeline...")
        components = build_offline_ma_crossover_pipeline(args)
        
        # Pipeline ausführen
        logger.info("[MAIN] Führe Pipeline aus...")
        perf_metrics = run_pipeline(
            pipeline=components["pipeline"],
            strategy=components["strategy"],
            feed=components["feed"],
            symbol=components["internal_symbol"],
        )
        
        # Endzeit
        finished_at = datetime.now(timezone.utc)
        duration = (finished_at - started_at).total_seconds()
        
        # Stats zusammenstellen
        stats = OfflineRealtimePipelineStats(
            run_id=components["run_id"],
            run_type="offline_realtime_pipeline",
            symbol=args.symbol,
            strategy_id="ma_crossover",
            env_mode="paper",
            synth_n_steps=args.n_steps,
            synth_n_regimes=args.n_regimes,
            synth_seed=args.seed,
            fast_window=args.fast_window,
            slow_window=args.slow_window,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration,
            **perf_metrics,
        )
        
        # Output-Verzeichnis bestimmen
        if args.output_dir:
            output_dir = args.output_dir
        else:
            output_dir = Path("reports") / "offline_realtime_pipeline" / components["run_id"]
        
        # Report schreiben
        logger.info("[MAIN] Schreibe Report...")
        report_path = write_offline_realtime_report(stats, output_dir)
        
        # Zusammenfassung ausgeben
        logger.info("=" * 80)
        logger.info("✓ Pipeline erfolgreich abgeschlossen")
        logger.info("=" * 80)
        logger.info(f"Run-ID: {components['run_id']}")
        logger.info(f"Symbol: {args.symbol} (intern: {components['internal_symbol']})")
        logger.info(f"Fast/Slow-Window: {args.fast_window}/{args.slow_window}")
        logger.info(f"Ticks: {perf_metrics['n_ticks']:,}")
        logger.info(f"Orders: {perf_metrics['n_orders']}")
        logger.info(f"Trades: {perf_metrics['n_trades']}")
        logger.info(f"Netto-PnL: {perf_metrics['net_pnl']:,.2f} EUR")
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Report: {report_path.absolute()}")
        logger.info("=" * 80)
        
        return 0
    
    except Exception as e:
        logger.exception(f"[MAIN] Fehler: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
