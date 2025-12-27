"""
OfflineRealtimeFeed v0 (IDEA-DATA-010)
======================================

Synthetischer Tick-Stream aus historischen OHLCV-Daten.

v0 Features:
    - GARCH(1,1) Prozess für bedingte Volatilität
    - Student-t Innovationsverteilung (Fat Tails)
    - Markov-Regime-Switching (2-3 Regime)
    - Fixes Zeitraster (konfigurierbar, z.B. 1s)
    - Jeder Tick trägt is_synthetic=True Flag

v0 Limitierungen (für v1 geplant):
    - Kein Bid/Ask-Spread
    - Keine komplexe Microstructure
    - Vereinfachte Volume-Modellierung
    - Kein Intrabar-Pfad-Simulation

Safety-First:
    - Jeder Tick ist mit is_synthetic=True markiert
    - DataSafetyGate wird im Konstruktor geprüft
    - Synthetische Daten können NIEMALS für Live-Trading verwendet werden

Verwendung:
    from src.data.feeds import OfflineRealtimeFeed, OfflineRealtimeFeedConfig, RegimeConfig
    from src.data.safety import DataUsageContextKind

    config = OfflineRealtimeFeedConfig(
        symbol="BTC/USD",
        base_timeframe="1min",
        tick_interval_ms=1000,
        regimes=[
            RegimeConfig(regime_id=0, garch_omega=0.00001, garch_alpha=0.1, garch_beta=0.85),
            RegimeConfig(regime_id=1, garch_omega=0.00005, garch_alpha=0.15, garch_beta=0.80),
        ],
        transition_matrix=[[0.98, 0.02], [0.05, 0.95]],
        student_df=5.0,
        usage_context=DataUsageContextKind.BACKTEST,
    )

    feed = OfflineRealtimeFeed.from_ohlcv(ohlcv_df, config)
    for tick in feed:
        print(tick)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Iterator, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from scipy.stats import t as student_t

    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

from src.data.safety import (
    DataSafetyContext,
    DataSafetyGate,
    DataSourceKind,
    DataUsageContextKind,
)


@dataclass(frozen=True)
class SyntheticTick:
    """
    Ein synthetisch generierter Tick.

    Attributes:
        timestamp: Zeitstempel des Ticks.
        price: Simulierter Preis.
        volume: Simuliertes Volume (v0: vereinfacht).
        regime_id: Aktuelles Markt-Regime (0, 1, 2, ...).
        sim_run_id: Eindeutige ID des Simulations-Runs.
        is_synthetic: Immer True - Safety-Flag für synthetische Daten.
    """

    timestamp: pd.Timestamp
    price: float
    volume: float
    regime_id: int
    sim_run_id: str
    is_synthetic: bool = True

    def __post_init__(self):
        # Sicherstellen, dass is_synthetic immer True ist
        if not self.is_synthetic:
            object.__setattr__(self, "is_synthetic", True)


@dataclass
class RegimeConfig:
    """
    Konfiguration für ein Volatilitäts-Regime.

    GARCH(1,1) Update-Regel:
        sigma_t^2 = omega + alpha * r_{t-1}^2 + beta * sigma_{t-1}^2

    Attributes:
        regime_id: Eindeutige ID des Regimes (0, 1, 2, ...).
        garch_omega: GARCH Omega-Parameter (Basis-Varianz).
        garch_alpha: GARCH Alpha-Parameter (Reaktion auf Schocks).
        garch_beta: GARCH Beta-Parameter (Persistenz).
        base_vol: Optionale Basis-Volatilität für Initialisierung.
    """

    regime_id: int
    garch_omega: float
    garch_alpha: float
    garch_beta: float
    base_vol: Optional[float] = None

    def __post_init__(self):
        # Validierung
        if self.garch_omega < 0:
            raise ValueError(f"garch_omega muss >= 0 sein, ist aber {self.garch_omega}")
        if not 0 <= self.garch_alpha <= 1:
            raise ValueError(f"garch_alpha muss in [0, 1] sein, ist aber {self.garch_alpha}")
        if not 0 <= self.garch_beta <= 1:
            raise ValueError(f"garch_beta muss in [0, 1] sein, ist aber {self.garch_beta}")
        if self.garch_alpha + self.garch_beta >= 1:
            # Warnung: GARCH ist nicht stationär, aber wir erlauben es für Experimente
            pass


@dataclass
class OfflineRealtimeFeedConfig:
    """
    Konfiguration für OfflineRealtimeFeed.

    Attributes:
        symbol: Handelssymbol (z.B. "BTC/USD").
        base_timeframe: Basis-Zeitrahmen der OHLCV-Daten (z.B. "1min").
        tick_interval_ms: Zeitabstand zwischen Ticks in Millisekunden.
        regimes: Liste von RegimeConfig für Markov-Regime-Switching.
        transition_matrix: Übergangswahrscheinlichkeiten zwischen Regimes.
        student_df: Freiheitsgrade für Student-t Verteilung (Fat Tails).
        usage_context: Verwendungskontext für Safety-Gate.
        initial_regime: Optionales Start-Regime (default: 0).
        seed: Optionaler RNG-Seed für Reproduzierbarkeit.
    """

    symbol: str
    base_timeframe: str
    tick_interval_ms: int
    regimes: List[RegimeConfig]
    transition_matrix: List[List[float]]
    student_df: float
    usage_context: DataUsageContextKind
    initial_regime: int = 0
    seed: Optional[int] = None

    def __post_init__(self):
        # Validierung
        if len(self.regimes) == 0:
            raise ValueError("Mindestens ein Regime erforderlich")

        n_regimes = len(self.regimes)
        if len(self.transition_matrix) != n_regimes:
            raise ValueError(
                f"transition_matrix hat {len(self.transition_matrix)} Zeilen, "
                f"erwartet {n_regimes} (Anzahl Regimes)"
            )

        for i, row in enumerate(self.transition_matrix):
            if len(row) != n_regimes:
                raise ValueError(
                    f"transition_matrix Zeile {i} hat {len(row)} Spalten, erwartet {n_regimes}"
                )
            row_sum = sum(row)
            if not np.isclose(row_sum, 1.0, atol=1e-6):
                raise ValueError(
                    f"transition_matrix Zeile {i} summiert sich zu {row_sum}, erwartet 1.0"
                )

        if self.student_df <= 2:
            raise ValueError(
                f"student_df muss > 2 sein für endliche Varianz, ist aber {self.student_df}"
            )

        if self.tick_interval_ms <= 0:
            raise ValueError(f"tick_interval_ms muss > 0 sein, ist aber {self.tick_interval_ms}")


class RegimeSwitchingVolModel:
    """
    Markov-Regime-Switching Volatilitäts-Modell mit GARCH(1,1).

    Kombiniert:
        - Diskrete Markov-Kette für Regime-Switching
        - GARCH(1,1) pro Regime für bedingte Volatilität
        - Student-t Innovationen für Fat Tails

    Attributes:
        regimes: Liste von RegimeConfig.
        transition_matrix: Numpy-Array der Übergangswahrscheinlichkeiten.
        student_df: Freiheitsgrade der Student-t Verteilung.
        rng: Numpy RandomGenerator.
    """

    def __init__(
        self,
        regimes: List[RegimeConfig],
        transition_matrix: List[List[float]],
        student_df: float,
        seed: Optional[int] = None,
        initial_regime: int = 0,
    ):
        """
        Initialisiert das Regime-Switching Volatilitäts-Modell.

        Args:
            regimes: Liste von RegimeConfig.
            transition_matrix: Übergangswahrscheinlichkeiten [n_regimes x n_regimes].
            student_df: Freiheitsgrade für Student-t Verteilung.
            seed: Optionaler RNG-Seed.
            initial_regime: Start-Regime (default: 0).
        """
        self.regimes = regimes
        self.transition_matrix = np.array(transition_matrix)
        self.student_df = student_df
        self.rng = np.random.default_rng(seed)
        self.initial_regime = initial_regime

        # Zustand
        self._current_regime = initial_regime
        self._prev_return = 0.0
        self._sigma_sq = self._init_sigma_sq()

    def _init_sigma_sq(self) -> float:
        """Initialisiert die Varianz aus dem aktuellen Regime."""
        regime = self.regimes[self._current_regime]
        if regime.base_vol is not None:
            return regime.base_vol**2
        # Stationäre Varianz (falls GARCH stationär ist)
        omega = regime.garch_omega
        alpha = regime.garch_alpha
        beta = regime.garch_beta
        denom = 1 - alpha - beta
        if denom > 0:
            return omega / denom
        # Fallback für nicht-stationären GARCH
        return omega * 100

    def reset(self) -> None:
        """Setzt das Modell auf den Anfangszustand zurück."""
        self._current_regime = self.initial_regime
        self._prev_return = 0.0
        self._sigma_sq = self._init_sigma_sq()

    def step(self) -> Tuple[int, float, float]:
        """
        Führt einen Zeitschritt durch.

        Returns:
            Tuple (regime_id, sigma_t, return_t):
                - regime_id: Aktuelles Regime nach Transition.
                - sigma_t: Bedingte Volatilität (Standardabweichung).
                - return_t: Generierter Return.
        """
        # 1. Regime-Transition (Markov-Kette)
        transition_probs = self.transition_matrix[self._current_regime]
        self._current_regime = self.rng.choice(len(self.regimes), p=transition_probs)

        # 2. GARCH(1,1) Update für das aktuelle Regime
        regime = self.regimes[self._current_regime]
        omega = regime.garch_omega
        alpha = regime.garch_alpha
        beta = regime.garch_beta

        # sigma_t^2 = omega + alpha * r_{t-1}^2 + beta * sigma_{t-1}^2
        self._sigma_sq = omega + alpha * (self._prev_return**2) + beta * self._sigma_sq

        # Sicherstellen, dass Varianz positiv bleibt
        self._sigma_sq = max(self._sigma_sq, 1e-12)
        sigma_t = np.sqrt(self._sigma_sq)

        # 3. Ziehe Innovation aus Student-t Verteilung
        if _HAS_SCIPY:
            # Standardisierte Student-t (Varianz = df / (df - 2))
            # Normalisieren für Varianz = 1
            scale = np.sqrt((self.student_df - 2) / self.student_df)
            eps_t = student_t.rvs(df=self.student_df, random_state=self.rng) * scale
        else:
            # Fallback: Approximation mit normalverteilten Innovationen
            # TODO: scipy.stats.t verwenden für korrekte Fat Tails
            eps_t = self.rng.standard_normal()

        # 4. Return berechnen
        return_t = sigma_t * eps_t
        self._prev_return = return_t

        return self._current_regime, sigma_t, return_t

    @property
    def current_regime(self) -> int:
        """Gibt das aktuelle Regime zurück."""
        return self._current_regime


class OfflineRealtimeFeed:
    """
    Synthetischer Tick-Feed aus historischen OHLCV-Daten.

    Generiert einen Strom von SyntheticTick-Objekten basierend auf:
        - Historischen OHLCV-Daten als Basis-Preisniveau
        - GARCH(1,1) für Volatilitäts-Clustering
        - Markov-Regime-Switching für verschiedene Marktphasen
        - Student-t Innovationen für Fat Tails

    Safety-First:
        - Prüft DataSafetyGate im Konstruktor
        - Alle Ticks sind mit is_synthetic=True markiert
        - Kann NICHT für Live-Trading verwendet werden

    Attributes:
        config: OfflineRealtimeFeedConfig.
        sim_run_id: Eindeutige ID des Simulations-Runs.
        vol_model: RegimeSwitchingVolModel.
    """

    def __init__(
        self,
        ohlcv: pd.DataFrame,
        config: OfflineRealtimeFeedConfig,
        *,
        safety_gate: Optional[DataSafetyGate] = None,
    ):
        """
        Initialisiert den OfflineRealtimeFeed.

        Args:
            ohlcv: OHLCV DataFrame im Peak_Trade Standardformat.
            config: OfflineRealtimeFeedConfig.
            safety_gate: Optionaler DataSafetyGate (default: Standardinstanz).

        Raises:
            DataSafetyViolationError: Wenn usage_context nicht erlaubt ist.
            ValueError: Bei ungültigen OHLCV-Daten.
        """
        self.config = config

        # Safety-Gate prüfen (IMMER)
        safety_context = DataSafetyContext(
            source_kind=DataSourceKind.SYNTHETIC_OFFLINE_RT,
            usage=config.usage_context,
        )
        DataSafetyGate.ensure_allowed(safety_context)

        # Validierung OHLCV
        self._validate_ohlcv(ohlcv)
        self._ohlcv = ohlcv.copy()

        # Simulations-ID
        self.sim_run_id = str(uuid.uuid4())

        # Volatilitäts-Modell
        self.vol_model = RegimeSwitchingVolModel(
            regimes=config.regimes,
            transition_matrix=config.transition_matrix,
            student_df=config.student_df,
            seed=config.seed,
            initial_regime=config.initial_regime,
        )

        # Precompute Basis-Preis-Pfad
        self._base_prices = self._compute_base_prices()

        # Iterator-Zustand
        self._current_idx = 0
        self._current_price: Optional[float] = None
        self._current_timestamp: Optional[pd.Timestamp] = None

    def _validate_ohlcv(self, ohlcv: pd.DataFrame) -> None:
        """Validiert den OHLCV DataFrame."""
        if ohlcv.empty:
            raise ValueError("OHLCV DataFrame darf nicht leer sein")

        required_cols = ["open", "high", "low", "close", "volume"]
        missing = set(required_cols) - set(ohlcv.columns)
        if missing:
            raise ValueError(f"Fehlende OHLCV-Spalten: {missing}")

        if not isinstance(ohlcv.index, pd.DatetimeIndex):
            raise ValueError("OHLCV Index muss DatetimeIndex sein")

    def _compute_base_prices(self) -> np.ndarray:
        """
        Berechnet Basis-Preise aus OHLCV Close.

        Für v0: Einfaches Forward-Fill der Close-Preise.
        """
        return self._ohlcv["close"].values.astype(float)

    @classmethod
    def from_ohlcv(
        cls,
        ohlcv: pd.DataFrame,
        config: OfflineRealtimeFeedConfig,
    ) -> "OfflineRealtimeFeed":
        """
        Factory-Methode: Erstellt einen OfflineRealtimeFeed aus OHLCV-Daten.

        Args:
            ohlcv: OHLCV DataFrame im Peak_Trade Standardformat.
            config: OfflineRealtimeFeedConfig.

        Returns:
            OfflineRealtimeFeed Instanz.
        """
        return cls(ohlcv=ohlcv, config=config)

    def reset(self) -> None:
        """Setzt den Feed auf den Anfangszustand zurück."""
        self._current_idx = 0
        self._current_price = None
        self._current_timestamp = None
        self.vol_model.reset()

    def _compute_ticks_per_candle(self) -> int:
        """Berechnet die Anzahl Ticks pro OHLCV-Kerze."""
        # Timeframe parsen (vereinfacht)
        tf = self.config.base_timeframe.lower()
        if tf in ("1m", "1min"):
            candle_ms = 60 * 1000
        elif tf in ("5m", "5min"):
            candle_ms = 5 * 60 * 1000
        elif tf in ("15m", "15min"):
            candle_ms = 15 * 60 * 1000
        elif tf in ("1h", "1hour"):
            candle_ms = 60 * 60 * 1000
        else:
            # Fallback: 1 Minute
            candle_ms = 60 * 1000

        return max(1, candle_ms // self.config.tick_interval_ms)

    def __iter__(self) -> Iterator[SyntheticTick]:
        """Gibt einen Iterator über alle Ticks zurück."""
        self.reset()
        return self

    def __next__(self) -> SyntheticTick:
        """Generiert den nächsten Tick."""
        return self.next_tick()

    def next_tick(self) -> SyntheticTick:
        """
        Generiert den nächsten synthetischen Tick.

        Returns:
            SyntheticTick mit is_synthetic=True.

        Raises:
            StopIteration: Wenn alle OHLCV-Daten verarbeitet wurden.
        """
        ticks_per_candle = self._compute_ticks_per_candle()
        n_candles = len(self._ohlcv)
        max_ticks = n_candles * ticks_per_candle

        if self._current_idx >= max_ticks:
            raise StopIteration

        # Bestimme aktuelle Kerze
        candle_idx = self._current_idx // ticks_per_candle
        tick_in_candle = self._current_idx % ticks_per_candle

        # Initialisiere Preis bei erstem Tick
        if self._current_price is None:
            self._current_price = self._base_prices[0]

        # Berechne Timestamp
        base_ts = self._ohlcv.index[candle_idx]
        tick_offset = pd.Timedelta(milliseconds=tick_in_candle * self.config.tick_interval_ms)
        current_ts = base_ts + tick_offset

        # Generiere Return via Vol-Modell
        regime_id, sigma_t, return_t = self.vol_model.step()

        # Update Preis (log-return Modell)
        self._current_price = self._current_price * np.exp(return_t)

        # Volume (v0: vereinfacht - proportional zur Volatilität)
        base_volume = self._ohlcv["volume"].iloc[candle_idx] / ticks_per_candle
        volume = base_volume * (1 + abs(return_t) * 10)

        # Erstelle Tick
        tick = SyntheticTick(
            timestamp=current_ts,
            price=self._current_price,
            volume=volume,
            regime_id=regime_id,
            sim_run_id=self.sim_run_id,
            is_synthetic=True,
        )

        self._current_idx += 1
        return tick

    @property
    def total_ticks(self) -> int:
        """Gibt die geschätzte Gesamtanzahl der Ticks zurück."""
        ticks_per_candle = self._compute_ticks_per_candle()
        return len(self._ohlcv) * ticks_per_candle

    @property
    def remaining_ticks(self) -> int:
        """Gibt die verbleibende Anzahl Ticks zurück."""
        return max(0, self.total_ticks - self._current_idx)
