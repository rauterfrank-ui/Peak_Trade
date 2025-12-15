"""
OfflineRealtimeFeedV0: Synthetischer Tick-Generator
====================================================

Generiert einen Stream synthetischer Ticks basierend auf:
    - GARCH(1,1) für Volatilitäts-Clustering
    - Markov-Regime-Switching für verschiedene Marktphasen
    - Student-t Innovationen für Fat Tails

WICHTIG: Dieses Modul ist NUR für Offline-Simulation und Backtesting gedacht!
         NIEMALS für Live-Trading oder echte Handelsentscheidungen verwenden!
         Alle generierten Ticks tragen is_synthetic=True.

v0 Features:
    - GARCH(1,1) pro Regime
    - Student-t Innovationen (konfigurierbare Freiheitsgrade)
    - Markov-Regime-Switching (2-4 Regime)
    - Fixes Zeitraster (konfigurierbar: 1s, 100ms, 1min, etc.)
    - Reproduzierbarkeit via Seed

v0 Limitierungen (bewusst akzeptiert):
    - Kein Bid/Ask-Spread (nur Mid/Last-Price)
    - Keine komplexe Microstructure / kein LOB
    - Vereinfachte Volume-Modellierung

Verwendung:
    from src.data.offline_realtime import (
        OfflineRealtimeFeedV0,
        OfflineRealtimeFeedV0Config,
        RegimeParams,
    )
    from datetime import datetime, timedelta

    config = OfflineRealtimeFeedV0Config(
        base_price=50000.0,
        dt=timedelta(seconds=1),
        num_ticks=10000,
        regime_params=[
            RegimeParams(omega=1e-5, alpha=0.05, beta=0.90, nu=5.0),
            RegimeParams(omega=5e-5, alpha=0.10, beta=0.85, nu=4.0),
        ],
        transition_matrix=[[0.98, 0.02], [0.05, 0.95]],
        seed=42,
    )

    feed = OfflineRealtimeFeedV0(config)
    for tick in feed.generate_ticks():
        print(tick)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, Iterator, List, Optional, Any

import numpy as np
import pandas as pd

from .synthetic_models.garch_regime_v0 import GarchRegimeModelV0


# ==============================================================================
# Data Models
# ==============================================================================


@dataclass(frozen=True)
class SyntheticTick:
    """
    Ein synthetisch generierter Tick.

    WICHTIG: is_synthetic ist IMMER True. Dieser Tick stammt aus einer
             Offline-Simulation und darf NIEMALS für Live-Trading verwendet werden!

    Attributes:
        timestamp: Zeitstempel des Ticks (timezone-aware UTC).
        price: Simulierter Preis (Mid/Last-Price).
        ret: Log-Return seit dem vorherigen Tick.
        regime_id: Aktuelles Markt-Regime (0, 1, 2, ...).
        volume: Simuliertes Volumen (v0: vereinfacht).
        is_synthetic: Immer True - Safety-Flag für synthetische Daten.
        sigma: Bedingte Volatilität zum Zeitpunkt des Ticks.
        sim_run_id: Eindeutige ID des Simulations-Runs.
        meta: Optionale zusätzliche Metadaten für Debug/Experimente.
    """

    timestamp: datetime
    price: float
    ret: float
    regime_id: int
    volume: float
    is_synthetic: bool
    sigma: float
    sim_run_id: str
    meta: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        # SAFETY: Erzwinge is_synthetic=True IMMER
        if not self.is_synthetic:
            object.__setattr__(self, "is_synthetic", True)

    def __repr__(self) -> str:
        return (
            f"SyntheticTick("
            f"ts={self.timestamp.isoformat()}, "
            f"price={self.price:.2f}, "
            f"ret={self.ret:.6f}, "
            f"regime={self.regime_id}, "
            f"vol={self.volume:.2f}, "
            f"σ={self.sigma:.6f})"
        )


@dataclass
class RegimeParams:
    """
    GARCH(1,1) + Student-t Parameter für ein Regime.

    GARCH(1,1) Varianz-Update:
        σ²_t = ω + α * r²_{t-1} + β * σ²_{t-1}

    Student-t Innovation:
        ε_t ~ t_ν(0, 1)
        r_t = σ_t * ε_t

    Attributes:
        omega: GARCH ω (Basis-Varianz, typisch: 1e-6 bis 1e-4).
        alpha: GARCH α (Reaktion auf Schocks, typisch: 0.05-0.15).
        beta: GARCH β (Persistenz, typisch: 0.80-0.95).
        nu: Student-t Freiheitsgrade (muss > 2 sein, typisch: 4-10).
        name: Optionaler Name für das Regime (z.B. "low_vol", "high_vol").
    """

    omega: float
    alpha: float
    beta: float
    nu: float
    name: Optional[str] = None

    def __post_init__(self):
        if self.omega < 0:
            raise ValueError(f"omega muss >= 0 sein, ist {self.omega}")
        if not 0 <= self.alpha <= 1:
            raise ValueError(f"alpha muss in [0, 1] sein, ist {self.alpha}")
        if not 0 <= self.beta <= 1:
            raise ValueError(f"beta muss in [0, 1] sein, ist {self.beta}")
        if self.nu <= 2:
            raise ValueError(f"nu muss > 2 sein, ist {self.nu}")

    def to_dict(self) -> dict:
        """Konvertiert zu Dict für GarchRegimeModelV0."""
        return {
            "omega": self.omega,
            "alpha": self.alpha,
            "beta": self.beta,
            "nu": self.nu,
        }


@dataclass
class OfflineRealtimeFeedV0Config:
    """
    Konfiguration für OfflineRealtimeFeedV0.

    Attributes:
        base_price: Startpreis S_0 (z.B. 50000.0 für BTC).
        dt: Zeitschritt zwischen Ticks (z.B. timedelta(seconds=1)).
        num_ticks: Anzahl der zu generierenden Ticks.
        regime_params: Liste von RegimeParams für jedes Regime.
        transition_matrix: Markov-Übergangsmatrix P[i][j].
            P[i][j] = P(Regime_t = j | Regime_{t-1} = i)
        seed: Optionaler RNG-Seed für Reproduzierbarkeit.
        start_timestamp: Optionaler Start-Zeitstempel (default: now UTC).
        initial_regime: Start-Regime (default: 0).
        volume_base: Basis-Volumen pro Tick (default: 100.0).
        volume_regime_multipliers: Optionale Volumen-Multiplikatoren pro Regime.
    """

    base_price: float
    dt: timedelta
    num_ticks: int
    regime_params: List[RegimeParams]
    transition_matrix: List[List[float]]
    seed: Optional[int] = None
    start_timestamp: Optional[datetime] = None
    initial_regime: int = 0
    volume_base: float = 100.0
    volume_regime_multipliers: Optional[List[float]] = None

    def __post_init__(self):
        if self.base_price <= 0:
            raise ValueError(f"base_price muss > 0 sein, ist {self.base_price}")
        if self.num_ticks <= 0:
            raise ValueError(f"num_ticks muss > 0 sein, ist {self.num_ticks}")
        if len(self.regime_params) == 0:
            raise ValueError("Mindestens ein Regime erforderlich")
        if self.dt.total_seconds() <= 0:
            raise ValueError(f"dt muss > 0 sein, ist {self.dt}")

        n_regimes = len(self.regime_params)

        # Transition Matrix validieren
        if len(self.transition_matrix) != n_regimes:
            raise ValueError(
                f"transition_matrix hat {len(self.transition_matrix)} Zeilen, "
                f"erwartet {n_regimes}"
            )
        for i, row in enumerate(self.transition_matrix):
            if len(row) != n_regimes:
                raise ValueError(
                    f"transition_matrix Zeile {i} hat {len(row)} Spalten, "
                    f"erwartet {n_regimes}"
                )
            if not np.isclose(sum(row), 1.0, atol=1e-6):
                raise ValueError(
                    f"transition_matrix Zeile {i} summiert zu {sum(row)}, erwartet 1.0"
                )

        # Volume Multipliers validieren
        if self.volume_regime_multipliers is not None:
            if len(self.volume_regime_multipliers) != n_regimes:
                raise ValueError(
                    f"volume_regime_multipliers hat {len(self.volume_regime_multipliers)} "
                    f"Einträge, erwartet {n_regimes}"
                )

    @property
    def n_regimes(self) -> int:
        """Anzahl der Regime."""
        return len(self.regime_params)


# ==============================================================================
# OfflineRealtimeFeedV0
# ==============================================================================


class OfflineRealtimeFeedV0:
    """
    Synthetischer Tick-Feed für Offline-Simulation.

    WICHTIG: Dieses Modul ist NUR für Offline-Simulation und Backtesting gedacht!
             NIEMALS für Live-Trading verwenden! Alle Ticks haben is_synthetic=True.

    Generiert synthetische Ticks basierend auf:
        - GARCH(1,1) für Volatilitäts-Clustering
        - Markov-Regime-Switching für verschiedene Marktphasen
        - Student-t Innovationen für Fat Tails

    Preisprozess (Log-Price):
        log(S_t) = log(S_{t-1}) + r_t
        S_t = S_{t-1} * exp(r_t)

    Attributes:
        config: OfflineRealtimeFeedV0Config mit allen Parametern.
        sim_run_id: Eindeutige ID dieses Simulations-Runs.
        model: GarchRegimeModelV0 für Return-Generierung.

    Example:
        config = OfflineRealtimeFeedV0Config(
            base_price=50000.0,
            dt=timedelta(seconds=1),
            num_ticks=10000,
            regime_params=[
                RegimeParams(omega=1e-5, alpha=0.05, beta=0.90, nu=5.0),
                RegimeParams(omega=5e-5, alpha=0.10, beta=0.85, nu=4.0),
            ],
            transition_matrix=[[0.98, 0.02], [0.05, 0.95]],
            seed=42,
        )
        feed = OfflineRealtimeFeedV0(config)

        for tick in feed.generate_ticks():
            print(tick)
    """

    def __init__(self, config: OfflineRealtimeFeedV0Config):
        """
        Initialisiert den OfflineRealtimeFeedV0.

        Args:
            config: Konfiguration für den Feed.
        """
        self.config = config
        self.sim_run_id = str(uuid.uuid4())

        # GARCH-Regime-Modell erstellen
        regime_params_dicts = [rp.to_dict() for rp in config.regime_params]
        self.model = GarchRegimeModelV0(
            regime_params=regime_params_dicts,
            transition_matrix=config.transition_matrix,
            seed=config.seed,
            initial_regime=config.initial_regime,
        )

        # Start-Zeitstempel
        if config.start_timestamp is not None:
            self._start_ts = config.start_timestamp
        else:
            self._start_ts = datetime.now(timezone.utc)

        # Volume Multipliers
        if config.volume_regime_multipliers is not None:
            self._vol_multipliers = config.volume_regime_multipliers
        else:
            # Default: höhere Volatilität = höheres Volumen
            self._vol_multipliers = [1.0 + 0.5 * i for i in range(config.n_regimes)]

    def generate_ticks(self) -> Iterable[SyntheticTick]:
        """
        Generator für synthetische Ticks.

        Generiert config.num_ticks Ticks mit dem GARCH-Regime-Modell.
        Jeder Tick hat is_synthetic=True.

        Yields:
            SyntheticTick für jeden Zeitschritt.
        """
        self.model.reset()

        current_price = self.config.base_price
        current_ts = self._start_ts

        for tick_idx in range(self.config.num_ticks):
            # Model-Step
            state = self.model.step()

            # Preis-Update (Log-Return Modell)
            current_price = current_price * np.exp(state.return_t)

            # Sicherheit: Preis muss positiv bleiben
            current_price = max(current_price, 1e-10)

            # Volume (v0: vereinfacht, abhängig von Regime)
            vol_mult = self._vol_multipliers[state.regime_id]
            # Höhere Volatilität = mehr Volumen
            vol_factor = 1.0 + abs(state.return_t) * 100
            volume = self.config.volume_base * vol_mult * vol_factor

            # Tick erstellen
            tick = SyntheticTick(
                timestamp=current_ts,
                price=current_price,
                ret=state.return_t,
                regime_id=state.regime_id,
                volume=volume,
                is_synthetic=True,  # SAFETY: IMMER True
                sigma=state.sigma_t,
                sim_run_id=self.sim_run_id,
                meta=None,
            )

            yield tick

            # Timestamp für nächsten Tick
            current_ts = current_ts + self.config.dt

    def to_dataframe(self) -> pd.DataFrame:
        """
        Konvertiert alle generierten Ticks in einen pandas DataFrame.

        Nützlich für schnelle Analyse und Visualisierung.

        Returns:
            pd.DataFrame mit Spalten:
                - timestamp (Index, DatetimeIndex UTC)
                - price
                - ret (log return)
                - regime_id
                - volume
                - sigma
                - is_synthetic
        """
        ticks = list(self.generate_ticks())

        df = pd.DataFrame(
            {
                "timestamp": [t.timestamp for t in ticks],
                "price": [t.price for t in ticks],
                "ret": [t.ret for t in ticks],
                "regime_id": [t.regime_id for t in ticks],
                "volume": [t.volume for t in ticks],
                "sigma": [t.sigma for t in ticks],
                "is_synthetic": [t.is_synthetic for t in ticks],
            }
        )

        df = df.set_index("timestamp")
        return df

    def reset(self, seed: Optional[int] = None) -> None:
        """
        Setzt den Feed zurück.

        Args:
            seed: Optionaler neuer Seed. Wenn None, wird der Original-Seed verwendet.
        """
        self.model.reset(seed=seed)
        self.sim_run_id = str(uuid.uuid4())

    def __iter__(self) -> Iterator[SyntheticTick]:
        """Ermöglicht direkte Iteration über den Feed."""
        return iter(self.generate_ticks())

    def __repr__(self) -> str:
        return (
            f"OfflineRealtimeFeedV0("
            f"base_price={self.config.base_price}, "
            f"num_ticks={self.config.num_ticks}, "
            f"n_regimes={self.config.n_regimes}, "
            f"dt={self.config.dt}, "
            f"sim_run_id={self.sim_run_id[:8]}...)"
        )

    def __str__(self) -> str:
        return (
            f"OfflineRealtimeFeedV0: {self.config.num_ticks} ticks, "
            f"{self.config.n_regimes} regimes, "
            f"base_price={self.config.base_price:.2f}, "
            f"dt={self.config.dt.total_seconds()}s"
        )
