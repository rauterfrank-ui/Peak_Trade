"""
Peak_Trade ECM Strategy
========================
Armstrong's Economic Confidence Model (ECM) basierte Trading-Strategie.

Konzept:
- ECM-Zyklus: 8.6 Jahre = Pi * 1000 Tage = 3141 Tage
- Turning Points: Peaks und Troughs im Zyklus
- Pi-Harmonics: 1/4, 1/2, 3/4 Punkte im Zyklus
- Entry bei Nähe zu wichtigen ECM-Wendepunkten + Trend

Quellen:
- docs/armstrong_notes.md
- Martin Armstrong's ECM-Theorie
"""

from datetime import datetime

import pandas as pd

# ECM-Konstanten
ECM_CYCLE_DAYS = 3141  # Pi * 1000
ECM_YEARS = 8.6
PI = 3.141592653589793


def calculate_ecm_phase(
    current_date: datetime,
    reference_date: datetime,
    cycle_days: int = ECM_CYCLE_DAYS
) -> dict[str, float]:
    """
    Berechnet aktuelle ECM-Phase.

    Args:
        current_date: Aktuelles Datum
        reference_date: Bekannter ECM-Turning-Point
        cycle_days: Länge eines ECM-Zyklus

    Returns:
        Dict mit phase, days_into_cycle, confidence
    """
    # Tage seit Referenz
    delta_days = (current_date - reference_date).days

    # Position im aktuellen Zyklus
    days_into_cycle = delta_days % cycle_days

    # Phase (0.0 = Start, 1.0 = Ende des Zyklus)
    phase = days_into_cycle / cycle_days

    # Confidence: Wie nah sind wir an wichtigen Punkten?
    # Wichtige Punkte: 0 (Start), 0.25, 0.5, 0.75, 1.0 (Ende)
    important_points = [0.0, 0.25, 0.5, 0.75, 1.0]

    # Minimale Distanz zu wichtigem Punkt
    min_distance = min(abs(phase - p) for p in important_points)

    # Confidence = 1 wenn sehr nah, 0 wenn weit weg
    # Threshold: 5% des Zyklus = hohe Confidence
    confidence = max(0, 1 - (min_distance / 0.05))

    return {
        'phase': phase,
        'days_into_cycle': days_into_cycle,
        'confidence': confidence,
        'nearest_turning_point': min(important_points, key=lambda p: abs(phase - p))
    }


def generate_signals(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Generiert ECM-basierte Signale.

    Args:
        df: OHLCV-DataFrame mit DatetimeIndex
        params: Dict mit ECM-Parametern

    Returns:
        Series mit Signalen (1 = Long, 0 = Neutral, -1 = Exit)

    Strategy:
        - Entry: Hohe ECM-Confidence + Bullish Trend
        - Exit: Niedrige ECM-Confidence ODER Bearish Trend
    """
    # Parameter
    ecm_cycle_days = params.get('ecm_cycle_days', ECM_CYCLE_DAYS)
    confidence_threshold = params.get('ecm_confidence_threshold', 0.6)
    lookback = params.get('lookback_bars', 100)
    ref_date_str = params.get('ecm_reference_date', '2020-01-18')

    # Referenz-Datum parsen
    try:
        ref_date = datetime.strptime(ref_date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        ref_date = datetime(2020, 1, 18)  # Fallback

    # ECM-Phase für jeden Bar berechnen
    ecm_data = []
    for date in df.index:
        phase_info = calculate_ecm_phase(date, ref_date, ecm_cycle_days)
        ecm_data.append(phase_info['confidence'])

    ecm_confidence = pd.Series(ecm_data, index=df.index)

    # Trend-Indikator (Simple: Preis über/unter MA)
    ma_trend = df['close'].rolling(window=lookback).mean()
    bullish_trend = df['close'] > ma_trend

    # Signale initialisieren
    signals = pd.Series(0, index=df.index, dtype=int)

    # Entry: Hohe ECM-Confidence + Bullish Trend
    entry_condition = (ecm_confidence > confidence_threshold) & bullish_trend

    # Entry nur bei Crossover (nicht permanent)
    entry_crossover = entry_condition & (~entry_condition.shift(1).fillna(False).astype(bool))
    signals[entry_crossover] = 1

    # Exit: Confidence fällt ODER Trend dreht
    exit_condition = (ecm_confidence < confidence_threshold * 0.5) | (~bullish_trend)
    exit_crossover = exit_condition & (~exit_condition.shift(1).fillna(False).astype(bool))
    signals[exit_crossover] = -1

    return signals



def add_ecm_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Fügt ECM-Indikatoren zum DataFrame hinzu."""
    df = df.copy()

    ecm_cycle_days = params.get('ecm_cycle_days', ECM_CYCLE_DAYS)
    ref_date_str = params.get('ecm_reference_date', '2020-01-18')

    try:
        ref_date = datetime.strptime(ref_date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        ref_date = datetime(2020, 1, 18)

    # ECM-Metriken für jeden Bar
    phases = []
    confidences = []
    nearest_points = []

    for date in df.index:
        phase_info = calculate_ecm_phase(date, ref_date, ecm_cycle_days)
        phases.append(phase_info['phase'])
        confidences.append(phase_info['confidence'])
        nearest_points.append(phase_info['nearest_turning_point'])

    df['ecm_phase'] = phases
    df['ecm_confidence'] = confidences
    df['ecm_nearest_tp'] = nearest_points

    return df


def get_strategy_description(params: dict) -> str:
    """Gibt Strategie-Beschreibung zurück."""
    return f"""
ECM (Economic Confidence Model)
=================================
Zyklus-Länge:      {params.get('ecm_cycle_days', ECM_CYCLE_DAYS)} Tage (8.6 Jahre)
Confidence-Level:  {params.get('ecm_confidence_threshold', 0.6):.0%}
Referenz-Datum:    {params.get('ecm_reference_date', '2020-01-18')}
Lookback:          {params.get('lookback_bars', 100)} Bars
Stop-Loss:         {params.get('stop_pct', 0.03):.1%}

Konzept (Armstrong):
- Pi-basierter Zyklus (3.141... * 1000 Tage)
- Turning Points bei 0%, 25%, 50%, 75%, 100%
- Entry bei hoher Confidence + Bullish Trend
- Exit bei niedriger Confidence ODER Bearish Trend
"""
