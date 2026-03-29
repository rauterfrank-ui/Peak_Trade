# src/research/ml/meta/meta_labeling.py
"""
Meta-Labeling Module – Research-Only
====================================

Implementierung des Meta-Labeling-Konzepts nach López de Prado.
Ein Secondary Model entscheidet, ob Signale eines Primary Models
tatsächlich gehandelt werden sollen.

⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING ⚠️

Konzept:
- Primary Model: Basis-Strategie (Richtung)
- Secondary Model: Meta-Model (Timing/Confidence)
- Output: Gefilterte Signale mit besserem Erwartungswert

Vorteile:
- Bessere Precision durch Signal-Filterung
- Bet-Sizing basierend auf Model-Confidence
- Flexibles Framework für verschiedene ML-Modelle

Referenz:
- "Advances in Financial Machine Learning" (López de Prado), Chapter 3
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# =============================================================================
# PROTOCOLS & TYPES
# =============================================================================


class MLModel(Protocol):
    """Protocol für ML-Modelle."""

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Trainiert das Modell."""
        ...

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Gibt Predictions zurück."""
        ...

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Gibt Wahrscheinlichkeiten zurück."""
        ...


@dataclass
class MetaModelSpec:
    """
    Spezifikation für ein Meta-Modell.

    Attributes:
        model_type: Typ des Modells (z.B. "random_forest", "xgboost")
        hyperparams: Hyperparameter für das Modell
        feature_cols: Feature-Spalten für Training
        target_col: Zielvariable (typisch: triple_barrier_label)
        min_confidence: Minimale Confidence für Trade-Ausführung
    """

    model_type: str = "random_forest"
    hyperparams: Dict[str, Any] = None
    feature_cols: List[str] = None
    target_col: str = "label"
    min_confidence: float = 0.5

    def __post_init__(self):
        if self.hyperparams is None:
            self.hyperparams = {}
        if self.feature_cols is None:
            self.feature_cols = []


# =============================================================================
# META-LABELING FUNCTIONS
# =============================================================================


def _align_indices(
    signals: pd.Series,
    features: pd.DataFrame,
) -> Tuple[pd.Series, pd.DataFrame]:
    common = signals.index.intersection(features.index)
    if len(common) == 0:
        raise ValueError("signals and features must share at least one index value")
    return signals.loc[common], features.loc[common]


def _feature_frame(features: pd.DataFrame, model_spec: MetaModelSpec) -> pd.DataFrame:
    if model_spec.feature_cols:
        missing = [c for c in model_spec.feature_cols if c not in features.columns]
        if missing:
            raise ValueError(f"Unknown feature columns: {missing}")
        return features[model_spec.feature_cols]
    skip = {model_spec.target_col}
    candidates = [c for c in features.columns if c not in skip]
    num = features[candidates].select_dtypes(include=[np.number])
    if num.shape[1] == 0:
        raise ValueError(
            "No numeric feature columns for meta-model "
            "(set MetaModelSpec.feature_cols or add numeric columns besides target_col)"
        )
    return num


def _positive_class_proba(probs: np.ndarray) -> np.ndarray:
    if probs.ndim == 1:
        return probs.astype(float)
    if probs.shape[1] == 2:
        return probs[:, 1].astype(float)
    return probs.max(axis=1).astype(float)


def apply_meta_model(
    signals: pd.Series,
    features: pd.DataFrame,
    model_spec: MetaModelSpec,
    trained_model: Optional[MLModel] = None,
) -> pd.Series:
    """
    Wendet Meta-Modell auf Basis-Signale an.

    - Wenn ``trained_model`` gesetzt ist: nutzt ``predict_proba`` auf den Features
      und setzt Signale auf 0, wenn die Confidence der positiven Klasse unter
      ``min_confidence`` liegt.
    - Wenn kein Modell übergeben wird und ``model_spec.target_col`` in ``features``
      vorkommt: trainiert ein Modell (siehe ``_create_model``) auf allen Zeilen mit
      gültigem Label und filtert danach alle Zeilen mit Features.
    - Ohne Modell und ohne Zielspalte: Signale unverändert (Kompatibilität mit
      rein explorativen Aufrufen ohne Labels).

    Args:
        signals: Basis-Strategie-Signale (+1, -1, 0)
        features: Feature-DataFrame für ML-Modell
        model_spec: Spezifikation des Meta-Modells
        trained_model: Trainiertes ML-Modell (optional)

    Returns:
        Gefilterte Signale basierend auf Meta-Modell-Confidence
    """
    signals_a, features_a = _align_indices(signals, features)
    out = signals_a.copy()

    if trained_model is not None:
        X_df = _feature_frame(features_a, model_spec)
        model: Any = trained_model
    elif model_spec.target_col in features_a.columns:
        X_df = _feature_frame(features_a, model_spec)
        y_series = features_a[model_spec.target_col]
        train_mask = y_series.notna()
        if int(train_mask.sum()) < 2:
            logger.warning("meta_labeling: fewer than 2 labeled rows; returning signals unchanged")
            return out
        y_train = y_series.loc[train_mask].astype(int).to_numpy()
        if len(np.unique(y_train)) < 2:
            logger.warning("meta_labeling: target has a single class; returning signals unchanged")
            return out
        X_train = X_df.loc[train_mask].to_numpy(dtype=float)
        model = _create_model(model_spec)
        model.fit(X_train, y_train)
    else:
        return out

    X_pred = X_df.to_numpy(dtype=float)
    probs = model.predict_proba(X_pred)
    p_pos = _positive_class_proba(probs)
    take = p_pos >= float(model_spec.min_confidence)
    return out.where(take, 0)


def compute_meta_labels(
    signals: pd.Series,
    triple_barrier_labels: pd.Series,
) -> pd.Series:
    """
    Berechnet Meta-Labels aus Basis-Signalen und Triple-Barrier-Labels.

    Das Meta-Label ist:
    - 1: Signal war profitabel (triple_barrier_label == +1)
    - 0: Signal war nicht profitabel (triple_barrier_label <= 0)

    Args:
        signals: Basis-Strategie-Signale
        triple_barrier_labels: Labels aus Triple-Barrier-Method

    Returns:
        Binary Meta-Labels (0 oder 1)
    """
    # Meta-Label: War das Signal profitabel?
    meta_labels = (triple_barrier_labels > 0).astype(int)

    # Nur für Zeitpunkte mit aktiven Signalen
    meta_labels = meta_labels.where(signals != 0, np.nan)

    return meta_labels


def compute_bet_size(
    probabilities: np.ndarray,
    method: str = "linear",
    max_bet: float = 1.0,
) -> np.ndarray:
    """
    Berechnet Bet-Sizes basierend auf Modell-Confidence.

    Args:
        probabilities: Modell-Wahrscheinlichkeiten (1d oder positiv-Klasse)
        method: Sizing-Methode ("linear", "kelly", "sigmoid")
        max_bet: Maximale Bet-Größe

    Returns:
        Bet-Sizes (0 bis max_bet)
    """
    p = np.asarray(probabilities, dtype=float)
    if method == "linear":
        return np.clip(p * max_bet, 0.0, max_bet)
    if method == "kelly":
        # Vereinfachte Kelly-Formel: bet = p - (1-p) / odds = 2p - 1 bei odds=1
        return np.clip(2.0 * p - 1.0, 0.0, max_bet)
    if method == "sigmoid":
        z = 1.0 / (1.0 + np.exp(-np.clip((p - 0.5) * 10.0, -20.0, 20.0)))
        return np.clip(z * max_bet, 0.0, max_bet)
    return np.clip(p * max_bet, 0.0, max_bet)


def _create_model(spec: MetaModelSpec) -> Any:
    """
    Erstellt ML-Modell basierend auf Spezifikation (scikit-learn / optional XGBoost).

    Args:
        spec: MetaModelSpec mit Modell-Konfiguration

    Returns:
        ML-Modell-Instanz
    """
    mt = str(spec.model_type).lower().replace("-", "_")

    if mt in ("random_forest", "rf", "randomforest"):
        from sklearn.ensemble import RandomForestClassifier

        defaults: Dict[str, Any] = {
            "n_estimators": 100,
            "max_depth": 8,
            "random_state": 42,
            "n_jobs": -1,
        }
        defaults.update(spec.hyperparams)
        return RandomForestClassifier(**defaults)

    if mt in ("xgboost", "xgb", "xgboost_classifier"):
        try:
            import xgboost as xgb
        except ImportError as e:
            raise ImportError(
                "model_type 'xgboost' requires the xgboost package to be installed"
            ) from e
        defaults = {"n_estimators": 100, "max_depth": 6, "random_state": 42}
        defaults.update(spec.hyperparams)
        return xgb.XGBClassifier(**defaults)

    raise NotImplementedError(
        f"Model type {spec.model_type!r} is not supported (use 'random_forest' or 'xgboost')"
    )
