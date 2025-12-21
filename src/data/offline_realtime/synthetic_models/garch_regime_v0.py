"""
GARCH(1,1) + Markov-Regime-Switching Model v0
==============================================

Stochastisches Volatilitätsmodell für synthetische Preis-Generierung.

WICHTIG: Dieses Modul ist NUR für Offline-Simulation gedacht!
         Niemals für Live-Trading oder echte Handelsentscheidungen verwenden.

Modell-Beschreibung:
    - Diskrete Markov-Kette für Regime-Switching
    - GARCH(1,1) für bedingte Varianz pro Regime:
        σ²_t = ω + α * r²_{t-1} + β * σ²_{t-1}
    - Student-t Innovationen für Fat Tails:
        ε_t ~ t_ν(0, 1)
        r_t = σ_t * ε_t

Verwendung:
    from src.data.offline_realtime.synthetic_models import GarchRegimeModelV0

    model = GarchRegimeModelV0(
        regime_params=[
            {"omega": 0.00001, "alpha": 0.05, "beta": 0.90, "nu": 5.0},
            {"omega": 0.00005, "alpha": 0.10, "beta": 0.85, "nu": 4.0},
        ],
        transition_matrix=[[0.98, 0.02], [0.05, 0.95]],
        seed=42,
    )

    for _ in range(1000):
        state = model.step()
        print(f"Regime: {state.regime_id}, Return: {state.return_t:.6f}")
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

try:
    from scipy.stats import t as student_t_dist

    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


@dataclass(frozen=True)
class GarchRegimeState:
    """
    Zustand des GARCH-Regime-Modells nach einem Zeitschritt.

    Attributes:
        regime_id: Aktuelles Regime (0, 1, 2, ...).
        sigma_t: Bedingte Volatilität (Standardabweichung).
        sigma_sq_t: Bedingte Varianz (σ²_t).
        epsilon_t: Standardisierte Innovation (aus Student-t).
        return_t: Generierter Return (r_t = σ_t * ε_t).
        step_idx: Index des Zeitschritts (0-basiert).
    """

    regime_id: int
    sigma_t: float
    sigma_sq_t: float
    epsilon_t: float
    return_t: float
    step_idx: int


class GarchRegimeModelV0:
    """
    GARCH(1,1) + Markov-Regime-Switching Modell.

    Kombiniert:
        - Diskrete Markov-Kette für Regime-Wechsel
        - GARCH(1,1) pro Regime für bedingte Varianz
        - Student-t Innovationen für Fat Tails

    GARCH(1,1) Update-Regel:
        σ²_t = ω + α * r²_{t-1} + β * σ²_{t-1}

    Student-t Innovation:
        ε_t ~ t_ν(0, 1), standardisiert auf Varianz 1
        r_t = σ_t * ε_t

    Attributes:
        n_regimes: Anzahl der Regime.
        regime_params: Liste von Dict mit GARCH-Parametern pro Regime.
        transition_matrix: Markov-Übergangsmatrix [K x K].
        rng: Numpy RandomGenerator für Reproduzierbarkeit.

    Example:
        model = GarchRegimeModelV0(
            regime_params=[
                {"omega": 1e-5, "alpha": 0.05, "beta": 0.90, "nu": 5.0},
                {"omega": 5e-5, "alpha": 0.10, "beta": 0.85, "nu": 4.0},
            ],
            transition_matrix=[[0.98, 0.02], [0.05, 0.95]],
            seed=42,
        )
        state = model.step()
    """

    def __init__(
        self,
        regime_params: List[dict],
        transition_matrix: List[List[float]],
        seed: Optional[int] = None,
        initial_regime: int = 0,
    ):
        """
        Initialisiert das GARCH-Regime-Modell.

        Args:
            regime_params: Liste von Dicts mit GARCH-Parametern pro Regime.
                Jedes Dict muss enthalten:
                    - omega: float (GARCH ω, Basis-Varianz)
                    - alpha: float (GARCH α, Reaktion auf Schocks)
                    - beta: float (GARCH β, Persistenz)
                    - nu: float (Student-t Freiheitsgrade, muss > 2 sein)
            transition_matrix: Markov-Übergangsmatrix [K x K].
                P[i][j] = P(Regime_t = j | Regime_{t-1} = i)
                Jede Zeile muss sich zu 1 summieren.
            seed: Optionaler RNG-Seed für Reproduzierbarkeit.
            initial_regime: Start-Regime (default: 0).

        Raises:
            ValueError: Bei ungültigen Parametern.
        """
        self._validate_params(regime_params, transition_matrix)

        self.regime_params = regime_params
        self.n_regimes = len(regime_params)
        self.transition_matrix = np.array(transition_matrix, dtype=np.float64)
        self.initial_regime = initial_regime
        self._seed = seed
        self.rng = np.random.default_rng(seed)

        # Interner Zustand
        self._current_regime = initial_regime
        self._sigma_sq = self._compute_initial_variance()
        self._prev_return = 0.0
        self._step_idx = 0

    def _validate_params(
        self,
        regime_params: List[dict],
        transition_matrix: List[List[float]],
    ) -> None:
        """Validiert die Modell-Parameter."""
        if len(regime_params) == 0:
            raise ValueError("Mindestens ein Regime erforderlich")

        n_regimes = len(regime_params)

        for i, params in enumerate(regime_params):
            required = {"omega", "alpha", "beta", "nu"}
            missing = required - set(params.keys())
            if missing:
                raise ValueError(f"Regime {i}: Fehlende Parameter: {missing}")

            omega = params["omega"]
            alpha = params["alpha"]
            beta = params["beta"]
            nu = params["nu"]

            if omega < 0:
                raise ValueError(f"Regime {i}: omega muss >= 0 sein, ist {omega}")
            if not 0 <= alpha <= 1:
                raise ValueError(f"Regime {i}: alpha muss in [0, 1] sein, ist {alpha}")
            if not 0 <= beta <= 1:
                raise ValueError(f"Regime {i}: beta muss in [0, 1] sein, ist {beta}")
            if nu <= 2:
                raise ValueError(f"Regime {i}: nu muss > 2 sein für endliche Varianz, ist {nu}")

        if len(transition_matrix) != n_regimes:
            raise ValueError(
                f"transition_matrix hat {len(transition_matrix)} Zeilen, erwartet {n_regimes}"
            )

        for i, row in enumerate(transition_matrix):
            if len(row) != n_regimes:
                raise ValueError(
                    f"transition_matrix Zeile {i} hat {len(row)} Spalten, erwartet {n_regimes}"
                )
            row_sum = sum(row)
            if not np.isclose(row_sum, 1.0, atol=1e-6):
                raise ValueError(f"transition_matrix Zeile {i} summiert zu {row_sum}, erwartet 1.0")

    def _compute_initial_variance(self) -> float:
        """Berechnet die initiale Varianz aus dem Start-Regime."""
        params = self.regime_params[self._current_regime]
        omega = params["omega"]
        alpha = params["alpha"]
        beta = params["beta"]

        # Stationäre Varianz (falls GARCH stationär ist)
        denom = 1 - alpha - beta
        if denom > 0:
            return omega / denom
        # Fallback für nicht-stationären GARCH
        return omega * 100

    def _sample_student_t(self, nu: float) -> float:
        """
        Zieht eine standardisierte Student-t Innovation.

        Die Innovation wird auf Varianz 1 normalisiert:
            scale = sqrt((nu - 2) / nu)
            ε = t_ν * scale

        Args:
            nu: Freiheitsgrade der Student-t Verteilung.

        Returns:
            Standardisierte Innovation mit Varianz ≈ 1.
        """
        if _HAS_SCIPY:
            # Standardisierte Student-t mit Varianz = 1
            scale = np.sqrt((nu - 2) / nu)
            return float(student_t_dist.rvs(df=nu, random_state=self.rng)) * scale
        else:
            # Fallback: Normal-Approximation
            # TODO: scipy.stats.t installieren für korrekte Fat Tails
            return float(self.rng.standard_normal())

    def reset(self, seed: Optional[int] = None) -> None:
        """
        Setzt das Modell auf den Anfangszustand zurück.

        Args:
            seed: Optionaler neuer Seed. Wenn None, wird der Original-Seed verwendet.
        """
        if seed is not None:
            self._seed = seed
        self.rng = np.random.default_rng(self._seed)
        self._current_regime = self.initial_regime
        self._sigma_sq = self._compute_initial_variance()
        self._prev_return = 0.0
        self._step_idx = 0

    def step(self) -> GarchRegimeState:
        """
        Führt einen Zeitschritt durch.

        Ablauf:
            1. Regime-Transition (Markov-Kette)
            2. GARCH(1,1) Varianz-Update
            3. Student-t Innovation ziehen
            4. Return berechnen

        Returns:
            GarchRegimeState mit allen Details des Zeitschritts.
        """
        # 1. Regime-Transition
        transition_probs = self.transition_matrix[self._current_regime]
        self._current_regime = int(self.rng.choice(self.n_regimes, p=transition_probs))

        # 2. GARCH(1,1) Update für aktuelles Regime
        params = self.regime_params[self._current_regime]
        omega = params["omega"]
        alpha = params["alpha"]
        beta = params["beta"]
        nu = params["nu"]

        # σ²_t = ω + α * r²_{t-1} + β * σ²_{t-1}
        self._sigma_sq = omega + alpha * (self._prev_return**2) + beta * self._sigma_sq

        # Numerische Stabilität
        self._sigma_sq = max(self._sigma_sq, 1e-12)
        sigma_t = np.sqrt(self._sigma_sq)

        # 3. Student-t Innovation
        epsilon_t = self._sample_student_t(nu)

        # 4. Return berechnen
        return_t = sigma_t * epsilon_t
        self._prev_return = return_t

        # State erstellen
        state = GarchRegimeState(
            regime_id=self._current_regime,
            sigma_t=sigma_t,
            sigma_sq_t=self._sigma_sq,
            epsilon_t=epsilon_t,
            return_t=return_t,
            step_idx=self._step_idx,
        )

        self._step_idx += 1
        return state

    def generate_returns(self, n_steps: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generiert eine Sequenz von Returns und Regime-IDs.

        Args:
            n_steps: Anzahl der zu generierenden Schritte.

        Returns:
            Tuple (returns, regime_ids):
                - returns: np.ndarray der generierten Returns
                - regime_ids: np.ndarray der Regime-IDs
        """
        returns = np.zeros(n_steps)
        regime_ids = np.zeros(n_steps, dtype=np.int32)

        for i in range(n_steps):
            state = self.step()
            returns[i] = state.return_t
            regime_ids[i] = state.regime_id

        return returns, regime_ids

    @property
    def current_regime(self) -> int:
        """Aktuelles Regime."""
        return self._current_regime

    @property
    def current_sigma(self) -> float:
        """Aktuelle Volatilität (Standardabweichung)."""
        return np.sqrt(self._sigma_sq)

    @property
    def current_variance(self) -> float:
        """Aktuelle Varianz."""
        return self._sigma_sq

    def __repr__(self) -> str:
        return (
            f"GarchRegimeModelV0(n_regimes={self.n_regimes}, "
            f"current_regime={self._current_regime}, "
            f"sigma={self.current_sigma:.6f}, "
            f"step={self._step_idx})"
        )
