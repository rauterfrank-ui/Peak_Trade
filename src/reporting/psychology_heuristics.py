"""
Psychologie-Heuristik-Modul für Trigger-Training
=================================================

Dieses Modul implementiert konkrete Heuristik-Formeln zur Berechnung von
Psychologie-Scores (0-3) aus Trigger-Training-Events.

Die 5 Kern-Achsen:
- FOMO (Fear of Missing Out) - Hinterherjagen von Moves
- Verlustangst (Loss Fear) - Zu frühe Exits, Vermeidung nach Verlusten
- Impulsivität (Impulsivity) - Spontan-Trades ohne Setup
- Zögern (Hesitation) - Zu späte oder verpasste Actions
- Regelbruch (Rule Break) - Bewusste Verletzung von System-Regeln

Workflow:
1. Event-Features sammeln (TriggerTrainingPsychEventFeatures)
2. Pro Event & Achse: Score berechnen (score_fomo, score_loss_fear, ...)
3. Events nach Cluster aggregieren (aggregate_cluster_scores)
4. In Heatmap-Format konvertieren (compute_psychology_heatmap_from_events)

Autor: Peak_Trade Quant-Psychologie-Heuristik-Designer
Datum: Dezember 2025
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence, Dict, List, Optional
from collections import defaultdict


# ============================================================================
# Type Definitions
# ============================================================================

Side = Literal["LONG", "SHORT"]
EventType = Literal["ENTER", "EXIT", "NO_ACTION", "SKIP"]


# ============================================================================
# Globale Schwellenwerte & Konfiguration
# ============================================================================

# Zeit-Schwellwerte (Sekunden)
LATENCY_OK_S = 3.0  # <= diese Zeit = "okay"
LATENCY_HESITATION_S = 8.0  # > = starke Zögerlichkeit

# Preisbewegungs-Schwellen (%)
MOVE_SMALL_PCT = 0.10  # 0.10% ~ "kleiner Move"
MOVE_MEDIUM_PCT = 0.30
MOVE_LARGE_PCT = 0.70

# PnL-Schwellwerte (Basis-Punkte)
PNL_SMALL_BP = 5.0
PNL_MEDIUM_BP = 15.0
PNL_LARGE_BP = 30.0

# Streak-Schwellen
LOSS_STREAK_MEDIUM = 2
LOSS_STREAK_HIGH = 4
SKIP_STREAK_MEDIUM = 2
SKIP_STREAK_HIGH = 4


# ============================================================================
# Helper Functions
# ============================================================================

def clamp_0_3(x: float) -> int:
    """
    Begrenzt einen Float-Wert auf den Bereich [0, 3] und rundet auf int.
    
    Args:
        x: Beliebiger Float-Wert
    
    Returns:
        Integer im Bereich 0-3
    
    Beispiele:
        >>> clamp_0_3(-1.5)
        0
        >>> clamp_0_3(1.7)
        2
        >>> clamp_0_3(5.0)
        3
    """
    return max(0, min(3, int(round(x))))


# ============================================================================
# Dataclasses
# ============================================================================

@dataclass
class TriggerTrainingPsychEventFeatures:
    """
    Abgeleitete Features für ein Trigger-Training-Event, speziell
    für die Psychologie-Heuristiken.
    
    Ein "Event" ist typischerweise:
      - ein Signal mit optionaler Action
      - oder eine Action (Entry/Exit/Re-Entry/Scale) im Kontext eines Signals
    
    Alle numerischen Werte sind bereits auf sinnvolle Einheiten normiert.
    """
    
    # ========================================================================
    # Cluster & Klassifikation
    # ========================================================================
    cluster: str  # z.B. "Breakout / Breakdowns"
    event_type: EventType  # "ENTER", "EXIT", "NO_ACTION", "SKIP"
    side: Optional[Side]  # LONG/SHORT oder None bei NO_ACTION/neutral
    signal_strength: float  # 0.0–1.0 (intern normalisiert)
    
    # ========================================================================
    # Zeitliche Komponente
    # ========================================================================
    latency_s: float  # Sek. zwischen Signal und Action oder Ende des Action-Fensters
    latency_window_s: float  # Soll-Fenster für "rechtzeitiges" Handeln (z.B. 3s)
    
    # ========================================================================
    # Marktdynamik relativ zum Signal
    # ========================================================================
    price_move_since_signal_pct: float  # % Move vom Signalpreis bis zur Action oder Fensterende
    price_max_favorable_pct: float  # max. günstige Bewegung im Fenster
    price_max_adverse_pct: float  # max. ungünstige Bewegung im Fenster
    
    # ========================================================================
    # PnL / Qualität relativ zu Ideal-Execution
    # ========================================================================
    pnl_vs_ideal_bp: float  # PnL-Differenz in Basis-Punkten ggü. idealer Entry/Exit
    
    # ========================================================================
    # Kontextflags
    # ========================================================================
    had_valid_setup: bool  # ob laut Regelwerk ein Setup aktiv war
    entered_without_signal: bool  # Entry ohne vorher gültiges Setup
    opposite_to_signal: bool  # Entry in entgegengesetzte Richtung zum Signal
    size_violation: bool  # Positionsgröße > erlaubter Size
    risk_violation: bool  # Stop/Risk-Regel verletzt
    
    # ========================================================================
    # Historie / Serie
    # ========================================================================
    recent_loss_streak: int  # Anzahl vorheriger Verlust-Trades im relevanten Fenster
    recent_skip_streak: int  # Anzahl verpasster Setups davor
    
    # ========================================================================
    # Manuelle Markierungen
    # ========================================================================
    manually_marked_fomo: bool  # vom Trader manuell als FOMO markiert
    manually_marked_fear: bool  # vom Trader manuell als Angst markiert
    manually_marked_impulsive: bool  # vom Trader als impulsiv markiert


@dataclass
class TriggerTrainingPsychClusterScores:
    """
    Aggregierte Psychologie-Scores für einen Trading-Cluster.
    
    Alle Scores liegen im Bereich [0, 3]:
    - 0: kein Thema
    - 1: leicht
    - 2: mittel
    - 3: stark
    """
    
    cluster: str
    fomo: int  # 0-3
    loss_fear: int  # 0-3
    impulsivity: int  # 0-3
    hesitation: int  # 0-3
    rule_break: int  # 0-3


# ============================================================================
# Event-Level Scoring Functions
# ============================================================================

def score_fomo(ev: TriggerTrainingPsychEventFeatures) -> int:
    """
    Berechnet FOMO-Score (Hinterherjagen) für ein Event.
    
    Intuition:
    - Spät in einen schon gelaufenen Move hinterher springen
    - Entry nach signifikanter Preisbewegung
    - Kombiniert Latenz + Move-Größe
    
    Args:
        ev: Event-Features
    
    Returns:
        Score 0-3
    
    Formel-Details:
    - late_factor: (latency - LATENCY_OK_S) / (LATENCY_HESITATION_S - LATENCY_OK_S)
    - move_component: Stufenfunktion basierend auf price_move_since_signal_pct
    - base = late_factor * 1.5 + move_component
    - manuelle Markierung: +1.0
    
    Beispiele:
        >>> ev = TriggerTrainingPsychEventFeatures(
        ...     cluster="Breakout", event_type="ENTER", side="LONG",
        ...     signal_strength=0.8, latency_s=5.0, latency_window_s=3.0,
        ...     price_move_since_signal_pct=0.5, price_max_favorable_pct=0.6,
        ...     price_max_adverse_pct=0.1, pnl_vs_ideal_bp=-20.0,
        ...     had_valid_setup=True, entered_without_signal=False,
        ...     opposite_to_signal=False, size_violation=False,
        ...     risk_violation=False, recent_loss_streak=0,
        ...     recent_skip_streak=0, manually_marked_fomo=True,
        ...     manually_marked_fear=False, manually_marked_impulsive=False
        ... )
        >>> score_fomo(ev)  # Hoher Score wegen Latenz + Move + manueller Markierung
        3
    """
    if ev.event_type != "ENTER":
        # FOMO primär bei Entries relevant
        base = 0.0
    else:
        # Latenz-Komponente: wie spät ist der Entry?
        late_factor = max(0.0, (ev.latency_s - LATENCY_OK_S) / (LATENCY_HESITATION_S - LATENCY_OK_S))
        late_factor = min(late_factor, 1.5)  # Deckelung
        
        # Move-Komponente: wie stark ist der Move schon gelaufen?
        move = abs(ev.price_move_since_signal_pct)
        if move < MOVE_SMALL_PCT:
            move_component = 0.0
        elif move < MOVE_MEDIUM_PCT:
            move_component = 0.8
        elif move < MOVE_LARGE_PCT:
            move_component = 1.5
        else:
            move_component = 2.2
        
        base = 0.0
        base += late_factor * 1.5
        base += move_component
    
    # Manuelle Markierung verstärkt
    if ev.manually_marked_fomo:
        base += 1.0
    
    return clamp_0_3(base)


def score_loss_fear(ev: TriggerTrainingPsychEventFeatures) -> int:
    """
    Berechnet Verlustangst-Score für ein Event.
    
    Intuition:
    - Zu frühes Wegklicken von Trades
    - Kein Entry nach Verlustserie
    - Exit bei minimalem Adverse Move
    
    Args:
        ev: Event-Features
    
    Returns:
        Score 0-3
    
    Formel-Details:
    - Für Exits: adverse < MOVE_SMALL_PCT && favorable > MOVE_SMALL_PCT → +1.0
    - PnL-Differenz zu ideal: < -MEDIUM_BP → +1.0, < -LARGE_BP → +0.5 extra
    - Für NO_ACTION/SKIP: loss_streak >= MEDIUM → +1.0, >= HIGH → +0.7
    - Manuelle Markierung: +1.0
    
    Beispiele:
        >>> ev = TriggerTrainingPsychEventFeatures(
        ...     cluster="Exit", event_type="EXIT", side="LONG",
        ...     signal_strength=0.5, latency_s=2.0, latency_window_s=3.0,
        ...     price_move_since_signal_pct=0.05, price_max_favorable_pct=0.3,
        ...     price_max_adverse_pct=0.08, pnl_vs_ideal_bp=-25.0,
        ...     had_valid_setup=True, entered_without_signal=False,
        ...     opposite_to_signal=False, size_violation=False,
        ...     risk_violation=False, recent_loss_streak=3,
        ...     recent_skip_streak=0, manually_marked_fomo=False,
        ...     manually_marked_fear=True, manually_marked_impulsive=False
        ... )
        >>> score_loss_fear(ev)  # Früher Exit + schlechter PnL + manuell
        3
    """
    base = 0.0
    
    # 1) Exits, die "zu früh" wirken
    if ev.event_type == "EXIT":
        adverse = ev.price_max_adverse_pct
        favorable = ev.price_max_favorable_pct
        pnl = ev.pnl_vs_ideal_bp
        
        # Früher Exit trotz geringen Adverse-Moves
        if adverse < MOVE_SMALL_PCT and favorable > MOVE_SMALL_PCT:
            base += 1.0
        
        # Starker Unterschied zu idealem Exit
        if pnl < -PNL_MEDIUM_BP:
            base += 1.0
        if pnl < -PNL_LARGE_BP:
            base += 0.5
    
    # 2) Kein Entry wegen Verlustserie (NO_ACTION / SKIP)
    if ev.event_type in ("NO_ACTION", "SKIP") and ev.had_valid_setup:
        if ev.recent_loss_streak >= LOSS_STREAK_MEDIUM:
            base += 1.0
        if ev.recent_loss_streak >= LOSS_STREAK_HIGH:
            base += 0.7
    
    # 3) Manuelle Markierung
    if ev.manually_marked_fear:
        base += 1.0
    
    return clamp_0_3(base)


def score_impulsivity(ev: TriggerTrainingPsychEventFeatures) -> int:
    """
    Berechnet Impulsivitäts-Score für ein Event.
    
    Intuition:
    - Hyper-schnelle Entries/Exits ohne Setup
    - Action ohne Regelwerk-Konformität
    - "Spontan-Trades"
    
    Args:
        ev: Event-Features
    
    Returns:
        Score 0-3
    
    Formel-Details:
    - Action ohne gültiges Setup: +1.5
    - Extrem schnelle Latenz (< 0.2 * LATENCY_OK_S): +1.0
    - Entry ohne Signal-Flag: +1.5
    - Manuelle Markierung: +1.0
    
    Beispiele:
        >>> ev = TriggerTrainingPsychEventFeatures(
        ...     cluster="Impuls", event_type="ENTER", side="LONG",
        ...     signal_strength=0.3, latency_s=0.5, latency_window_s=3.0,
        ...     price_move_since_signal_pct=0.1, price_max_favorable_pct=0.2,
        ...     price_max_adverse_pct=0.1, pnl_vs_ideal_bp=-10.0,
        ...     had_valid_setup=False, entered_without_signal=True,
        ...     opposite_to_signal=False, size_violation=False,
        ...     risk_violation=False, recent_loss_streak=0,
        ...     recent_skip_streak=0, manually_marked_fomo=False,
        ...     manually_marked_fear=False, manually_marked_impulsive=True
        ... )
        >>> score_impulsivity(ev)  # Kein Setup + ohne Signal + manuell
        3
    """
    base = 0.0
    
    # 1) Action ohne gültiges Setup
    if ev.event_type in ("ENTER", "EXIT") and not ev.had_valid_setup:
        base += 1.5
    
    # 2) Entry/Exit extrem schnell nach Signal (Flip-Seite von Zögern)
    if ev.event_type in ("ENTER", "EXIT"):
        if ev.latency_s < 0.2 * LATENCY_OK_S:
            base += 1.0
    
    # 3) Flag: entered_without_signal
    if ev.entered_without_signal:
        base += 1.5
    
    # 4) Manuelle Markierung
    if ev.manually_marked_impulsive:
        base += 1.0
    
    return clamp_0_3(base)


def score_hesitation(ev: TriggerTrainingPsychEventFeatures) -> int:
    """
    Berechnet Zögerungs-Score für ein Event.
    
    Intuition:
    - Zu spät oder gar nicht handeln, obwohl Setup da ist
    - Signal verpasst
    - Lange Reaktionszeit
    
    Args:
        ev: Event-Features
    
    Returns:
        Score 0-3
    
    Formel-Details:
    - Späte Action (> LATENCY_OK_S): +1.0
    - Sehr späte Action (> LATENCY_HESITATION_S): +1.0 extra
    - NO_ACTION/SKIP bei Setup: +1.0
    - NO_ACTION/SKIP + großer favorable Move verpasst: +0.5
    - Skip-Streak >= MEDIUM: +0.5, >= HIGH: +0.5 extra
    
    Beispiele:
        >>> ev = TriggerTrainingPsychEventFeatures(
        ...     cluster="Zögern", event_type="NO_ACTION", side=None,
        ...     signal_strength=0.8, latency_s=10.0, latency_window_s=3.0,
        ...     price_move_since_signal_pct=0.4, price_max_favorable_pct=0.5,
        ...     price_max_adverse_pct=0.05, pnl_vs_ideal_bp=-40.0,
        ...     had_valid_setup=True, entered_without_signal=False,
        ...     opposite_to_signal=False, size_violation=False,
        ...     risk_violation=False, recent_loss_streak=0,
        ...     recent_skip_streak=5, manually_marked_fomo=False,
        ...     manually_marked_fear=False, manually_marked_impulsive=False
        ... )
        >>> score_hesitation(ev)  # NO_ACTION + Setup + großer Move + Skip-Streak
        3
    """
    base = 0.0
    
    # 1) Späte Action
    if ev.event_type in ("ENTER", "EXIT") and ev.had_valid_setup:
        if ev.latency_s > LATENCY_OK_S:
            base += 1.0
        if ev.latency_s > LATENCY_HESITATION_S:
            base += 1.0
    
    # 2) NO_ACTION/ SKIP bei Setup innerhalb Fenster
    if ev.event_type in ("NO_ACTION", "SKIP") and ev.had_valid_setup:
        base += 1.0
        if ev.price_max_favorable_pct > MOVE_MEDIUM_PCT:
            base += 0.5
    
    # 3) Skip-Streak verstärkt
    if ev.recent_skip_streak >= SKIP_STREAK_MEDIUM:
        base += 0.5
    if ev.recent_skip_streak >= SKIP_STREAK_HIGH:
        base += 0.5
    
    return clamp_0_3(base)


def score_rule_break(ev: TriggerTrainingPsychEventFeatures) -> int:
    """
    Berechnet Regelbruch-Score für ein Event.
    
    Intuition:
    - Bewusst gegen System-Regeln handeln
    - Richtung gegen Signal
    - Size/Risk-Violations
    
    Args:
        ev: Event-Features
    
    Returns:
        Score 0-3
    
    Formel-Details:
    - Richtung gegen Signal: +1.5
    - Size-Violation: +1.0
    - Risk-Violation: +1.0
    - Entry ohne Setup: +1.0
    - PnL << ideal (< -LARGE_BP): +0.5
    
    Beispiele:
        >>> ev = TriggerTrainingPsychEventFeatures(
        ...     cluster="Regelbruch", event_type="ENTER", side="SHORT",
        ...     signal_strength=0.9, latency_s=2.0, latency_window_s=3.0,
        ...     price_move_since_signal_pct=0.2, price_max_favorable_pct=0.3,
        ...     price_max_adverse_pct=0.1, pnl_vs_ideal_bp=-35.0,
        ...     had_valid_setup=False, entered_without_signal=True,
        ...     opposite_to_signal=True, size_violation=True,
        ...     risk_violation=True, recent_loss_streak=0,
        ...     recent_skip_streak=0, manually_marked_fomo=False,
        ...     manually_marked_fear=False, manually_marked_impulsive=False
        ... )
        >>> score_rule_break(ev)  # Gegen Signal + Size + Risk + ohne Setup
        3
    """
    base = 0.0
    
    # Richtung gegen Signal
    if ev.opposite_to_signal:
        base += 1.5
    
    # Größe / Risk
    if ev.size_violation:
        base += 1.0
    if ev.risk_violation:
        base += 1.0
    
    # Entry ohne Setup
    if ev.entered_without_signal and not ev.had_valid_setup:
        base += 1.0
    
    # PnL als Indikator für "teuren" Regelbruch
    if ev.pnl_vs_ideal_bp < -PNL_LARGE_BP:
        base += 0.5
    
    return clamp_0_3(base)


# ============================================================================
# Aggregation: Events → Cluster-Scores
# ============================================================================

def aggregate_cluster_scores(
    events: Sequence[TriggerTrainingPsychEventFeatures],
) -> List[TriggerTrainingPsychClusterScores]:
    """
    Aggregiert Event-Scores zu Cluster-Scores.
    
    Vorgehen:
    1. Events nach Cluster gruppieren
    2. Pro Event: Alle 5 Achsen-Scores berechnen
    3. Pro Cluster & Achse: Gewichtetes Mittel bilden
       - Top-3-Events bekommen 50% Gewicht
       - Alle Events bekommen 50% Gewicht
    4. Ergebnis clampen auf [0, 3]
    
    Args:
        events: Liste von Event-Features
    
    Returns:
        Liste von Cluster-Scores
    
    Beispiel:
        >>> events = [
        ...     TriggerTrainingPsychEventFeatures(
        ...         cluster="Trend-Folge", event_type="ENTER", side="LONG",
        ...         signal_strength=0.8, latency_s=5.0, latency_window_s=3.0,
        ...         price_move_since_signal_pct=0.4, price_max_favorable_pct=0.5,
        ...         price_max_adverse_pct=0.1, pnl_vs_ideal_bp=-20.0,
        ...         had_valid_setup=True, entered_without_signal=False,
        ...         opposite_to_signal=False, size_violation=False,
        ...         risk_violation=False, recent_loss_streak=0,
        ...         recent_skip_streak=0, manually_marked_fomo=True,
        ...         manually_marked_fear=False, manually_marked_impulsive=False
        ...     ),
        ... ]
        >>> scores = aggregate_cluster_scores(events)
        >>> scores[0].cluster
        'Trend-Folge'
        >>> scores[0].fomo >= 2  # High FOMO expected
        True
    """
    if not events:
        return []
    
    # 1. Gruppierung nach Cluster
    cluster_events: Dict[str, List[TriggerTrainingPsychEventFeatures]] = defaultdict(list)
    for ev in events:
        cluster_events[ev.cluster].append(ev)
    
    # 2. Pro Cluster: Scores aggregieren
    result = []
    for cluster_name, cluster_evs in sorted(cluster_events.items()):
        # Pro Event: alle Achsen-Scores berechnen
        fomo_scores = [score_fomo(ev) for ev in cluster_evs]
        loss_fear_scores = [score_loss_fear(ev) for ev in cluster_evs]
        impulsivity_scores = [score_impulsivity(ev) for ev in cluster_evs]
        hesitation_scores = [score_hesitation(ev) for ev in cluster_evs]
        rule_break_scores = [score_rule_break(ev) for ev in cluster_evs]
        
        # Aggregationsstrategie: Gewichteter Mix aus avg_all und avg_top3
        def aggregate_scores(scores: List[int]) -> int:
            if not scores:
                return 0
            
            # Durchschnitt aller Scores
            avg_all = sum(scores) / len(scores)
            
            # Durchschnitt der Top-3 Scores (wenn genug vorhanden)
            if len(scores) >= 3:
                top_3 = sorted(scores, reverse=True)[:3]
                avg_top = sum(top_3) / len(top_3)
                # 50/50 Mix
                combined = 0.5 * avg_all + 0.5 * avg_top
            else:
                # Zu wenig Events: nur avg_all nutzen
                combined = avg_all
            
            return clamp_0_3(combined)
        
        cluster_score = TriggerTrainingPsychClusterScores(
            cluster=cluster_name,
            fomo=aggregate_scores(fomo_scores),
            loss_fear=aggregate_scores(loss_fear_scores),
            impulsivity=aggregate_scores(impulsivity_scores),
            hesitation=aggregate_scores(hesitation_scores),
            rule_break=aggregate_scores(rule_break_scores),
        )
        result.append(cluster_score)
    
    return result


def build_heatmap_input_from_clusters(
    clusters: Sequence[TriggerTrainingPsychClusterScores],
) -> List[Dict[str, float]]:
    """
    Konvertiert Cluster-Scores in Heatmap-Input-Format.
    
    Args:
        clusters: Liste von Cluster-Scores
    
    Returns:
        Liste von Dictionaries kompatibel mit build_psychology_heatmap_rows()
    
    Beispiel:
        >>> clusters = [
        ...     TriggerTrainingPsychClusterScores(
        ...         cluster="Trend-Folge",
        ...         fomo=2, loss_fear=1, impulsivity=1,
        ...         hesitation=0, rule_break=1
        ...     )
        ... ]
        >>> result = build_heatmap_input_from_clusters(clusters)
        >>> result[0]["name"]
        'Trend-Folge'
        >>> result[0]["fomo"]
        2
    """
    return [
        {
            "name": c.cluster,
            "fomo": c.fomo,
            "loss_fear": c.loss_fear,
            "impulsivity": c.impulsivity,
            "hesitation": c.hesitation,
            "rule_break": c.rule_break,
        }
        for c in clusters
    ]


# ============================================================================
# End-to-End Helper
# ============================================================================

def compute_psychology_heatmap_from_events(
    events: Sequence[TriggerTrainingPsychEventFeatures],
) -> List[Dict[str, any]]:
    """
    End-to-End: Event-Features → Cluster-Scores → Heatmap-kompatibles Dict.
    
    Dies ist die Haupt-Convenience-Funktion für die Integration.
    
    Args:
        events: Liste von Event-Features
    
    Returns:
        Serialisierte Heatmap-Rows (ready für Template-Rendering)
    
    Workflow:
    1. Events → Cluster-Scores (aggregate_cluster_scores)
    2. Cluster-Scores → Raw-Dicts (build_heatmap_input_from_clusters)
    3. Raw-Dicts → Heatmap-Rows (build_psychology_heatmap_rows)
    4. Rows → Serialisiert (serialize_psychology_heatmap_rows)
    
    Beispiel:
        >>> events = [...]  # Liste von TriggerTrainingPsychEventFeatures
        >>> heatmap_data = compute_psychology_heatmap_from_events(events)
        >>> # heatmap_data kann direkt ans Template übergeben werden
        >>> # render_template("psychology.html", heatmap_rows=heatmap_data)
    """
    # Import hier, um zirkuläre Dependencies zu vermeiden
    from src.reporting.psychology_heatmap import (
        build_psychology_heatmap_rows,
        serialize_psychology_heatmap_rows,
    )
    
    # 1. Aggregation
    clusters = aggregate_cluster_scores(events)
    
    # 2. Raw-Format
    raw_rows = build_heatmap_input_from_clusters(clusters)
    
    # 3. Heatmap-Rows bauen
    rows = build_psychology_heatmap_rows(raw_rows)
    
    # 4. Serialisieren
    return serialize_psychology_heatmap_rows(rows)


# ============================================================================
# Beispiel-Event-Generator (für Testing)
# ============================================================================

def create_example_fomo_event() -> TriggerTrainingPsychEventFeatures:
    """
    Erzeugt ein Beispiel-Event mit hohem FOMO-Score.
    
    Charakteristik:
    - ENTER-Event
    - Hohe Latenz (spät)
    - Großer Price-Move bereits gelaufen
    - Manuell als FOMO markiert
    """
    return TriggerTrainingPsychEventFeatures(
        cluster="Breakout / Breakdowns",
        event_type="ENTER",
        side="LONG",
        signal_strength=0.8,
        latency_s=6.0,  # Spät
        latency_window_s=3.0,
        price_move_since_signal_pct=0.8,  # Großer Move
        price_max_favorable_pct=0.9,
        price_max_adverse_pct=0.1,
        pnl_vs_ideal_bp=-25.0,
        had_valid_setup=True,
        entered_without_signal=False,
        opposite_to_signal=False,
        size_violation=False,
        risk_violation=False,
        recent_loss_streak=0,
        recent_skip_streak=0,
        manually_marked_fomo=True,
        manually_marked_fear=False,
        manually_marked_impulsive=False,
    )


def create_example_loss_fear_event() -> TriggerTrainingPsychEventFeatures:
    """
    Erzeugt ein Beispiel-Event mit hohem Verlustangst-Score.
    
    Charakteristik:
    - EXIT-Event
    - Kleiner Adverse-Move, aber früher Exit
    - Schlechter PnL vs. Ideal
    - Nach Verlust-Streak
    """
    return TriggerTrainingPsychEventFeatures(
        cluster="Take-Profit / Exits",
        event_type="EXIT",
        side="LONG",
        signal_strength=0.6,
        latency_s=1.5,
        latency_window_s=3.0,
        price_move_since_signal_pct=0.05,
        price_max_favorable_pct=0.4,
        price_max_adverse_pct=0.08,  # Klein
        pnl_vs_ideal_bp=-30.0,  # Schlecht
        had_valid_setup=True,
        entered_without_signal=False,
        opposite_to_signal=False,
        size_violation=False,
        risk_violation=False,
        recent_loss_streak=3,  # Streak
        recent_skip_streak=0,
        manually_marked_fomo=False,
        manually_marked_fear=True,
        manually_marked_impulsive=False,
    )


def create_example_impulsivity_event() -> TriggerTrainingPsychEventFeatures:
    """
    Erzeugt ein Beispiel-Event mit hohem Impulsivitäts-Score.
    
    Charakteristik:
    - ENTER-Event ohne Setup
    - Sehr schnelle Reaktion
    - Entry ohne Signal
    """
    return TriggerTrainingPsychEventFeatures(
        cluster="Counter-Trend Einstiege",
        event_type="ENTER",
        side="SHORT",
        signal_strength=0.3,
        latency_s=0.4,  # Sehr schnell
        latency_window_s=3.0,
        price_move_since_signal_pct=0.1,
        price_max_favorable_pct=0.2,
        price_max_adverse_pct=0.15,
        pnl_vs_ideal_bp=-15.0,
        had_valid_setup=False,  # Kein Setup
        entered_without_signal=True,  # Ohne Signal
        opposite_to_signal=False,
        size_violation=False,
        risk_violation=False,
        recent_loss_streak=0,
        recent_skip_streak=0,
        manually_marked_fomo=False,
        manually_marked_fear=False,
        manually_marked_impulsive=True,
    )


def create_example_hesitation_event() -> TriggerTrainingPsychEventFeatures:
    """
    Erzeugt ein Beispiel-Event mit hohem Zögerungs-Score.
    
    Charakteristik:
    - NO_ACTION bei gültigem Setup
    - Großer favorable Move verpasst
    - Hoher Skip-Streak
    """
    return TriggerTrainingPsychEventFeatures(
        cluster="Trend-Folge Einstiege",
        event_type="NO_ACTION",
        side=None,
        signal_strength=0.9,
        latency_s=12.0,  # Sehr spät
        latency_window_s=3.0,
        price_move_since_signal_pct=0.6,
        price_max_favorable_pct=0.7,  # Großer Move verpasst
        price_max_adverse_pct=0.05,
        pnl_vs_ideal_bp=-50.0,
        had_valid_setup=True,  # Setup war da
        entered_without_signal=False,
        opposite_to_signal=False,
        size_violation=False,
        risk_violation=False,
        recent_loss_streak=0,
        recent_skip_streak=6,  # Hoher Streak
        manually_marked_fomo=False,
        manually_marked_fear=False,
        manually_marked_impulsive=False,
    )


def create_example_rule_break_event() -> TriggerTrainingPsychEventFeatures:
    """
    Erzeugt ein Beispiel-Event mit hohem Regelbruch-Score.
    
    Charakteristik:
    - ENTER gegen Signal-Richtung
    - Size + Risk Violations
    - Ohne Setup
    """
    return TriggerTrainingPsychEventFeatures(
        cluster="Re-Entries / Scaling",
        event_type="ENTER",
        side="SHORT",
        signal_strength=0.8,
        latency_s=2.0,
        latency_window_s=3.0,
        price_move_since_signal_pct=0.2,
        price_max_favorable_pct=0.3,
        price_max_adverse_pct=0.1,
        pnl_vs_ideal_bp=-40.0,
        had_valid_setup=False,
        entered_without_signal=True,
        opposite_to_signal=True,  # Gegen Signal
        size_violation=True,  # Zu groß
        risk_violation=True,  # Risk verletzt
        recent_loss_streak=0,
        recent_skip_streak=0,
        manually_marked_fomo=False,
        manually_marked_fear=False,
        manually_marked_impulsive=False,
    )


def create_example_mixed_events() -> List[TriggerTrainingPsychEventFeatures]:
    """
    Erzeugt eine gemischte Liste von Beispiel-Events für alle Cluster.
    
    Returns:
        Liste mit je 1-2 Events pro Standard-Cluster
    """
    return [
        create_example_fomo_event(),
        create_example_loss_fear_event(),
        create_example_impulsivity_event(),
        create_example_hesitation_event(),
        create_example_rule_break_event(),
        # Zusätzliche Events für Diversität
        TriggerTrainingPsychEventFeatures(
            cluster="Trend-Folge Einstiege",
            event_type="ENTER",
            side="LONG",
            signal_strength=0.9,
            latency_s=2.5,
            latency_window_s=3.0,
            price_move_since_signal_pct=0.15,
            price_max_favorable_pct=0.3,
            price_max_adverse_pct=0.05,
            pnl_vs_ideal_bp=-5.0,
            had_valid_setup=True,
            entered_without_signal=False,
            opposite_to_signal=False,
            size_violation=False,
            risk_violation=False,
            recent_loss_streak=0,
            recent_skip_streak=0,
            manually_marked_fomo=False,
            manually_marked_fear=False,
            manually_marked_impulsive=False,
        ),
        TriggerTrainingPsychEventFeatures(
            cluster="Breakout / Breakdowns",
            event_type="ENTER",
            side="LONG",
            signal_strength=0.7,
            latency_s=4.0,
            latency_window_s=3.0,
            price_move_since_signal_pct=0.4,
            price_max_favorable_pct=0.5,
            price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-18.0,
            had_valid_setup=True,
            entered_without_signal=False,
            opposite_to_signal=False,
            size_violation=False,
            risk_violation=False,
            recent_loss_streak=0,
            recent_skip_streak=0,
            manually_marked_fomo=False,
            manually_marked_fear=False,
            manually_marked_impulsive=False,
        ),
    ]
