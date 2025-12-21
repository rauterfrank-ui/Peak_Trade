"""
Psychology Heatmap Module
=========================

Dieses Modul verarbeitet psychologische Trigger-Training-Scores und bereitet sie
für die Visualisierung als Heatmap auf.

Die Heatmap zeigt psychologische Muster über verschiedene Trading-Cluster hinweg:
- FOMO (Fear of Missing Out) - "Hinterherjagen"
- Verlustangst - "Nicht verlieren dürfen"
- Impulsivität - Spontan-Trades
- Zögern - Signale verpasst
- Regelbruch - Setup ignoriert

Jeder Score liegt zwischen 0 und 3:
- 0: kein Thema
- 1: leicht
- 2: mittel
- 3: stark
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class PsychologyHeatmapCell:
    """Einzelne Zelle in der Heatmap."""

    value: float  # Rohwert (0-3+)
    heat_level: int  # Diskrete Heat-Level: 0, 1, 2, 3
    display_value: str  # Formatierter Wert für Anzeige
    css_class: str  # CSS-Klasse für Styling (heat-0, heat-1, heat-2, heat-3)


@dataclass
class PsychologyHeatmapRow:
    """Eine Zeile in der Heatmap (ein Trading-Cluster)."""

    name: str  # z.B. "Trend-Folge Einstiege"
    fomo: PsychologyHeatmapCell
    loss_fear: PsychologyHeatmapCell
    impulsivity: PsychologyHeatmapCell
    hesitation: PsychologyHeatmapCell
    rule_break: PsychologyHeatmapCell


def _score_to_heat_level(score: float) -> int:
    """
    Konvertiert einen kontinuierlichen Score in ein diskretes Heat-Level (0-3).

    Mapping:
    - 0.0 - 0.4: Level 0 (kein Thema)
    - 0.5 - 1.4: Level 1 (leicht)
    - 1.5 - 2.4: Level 2 (mittel)
    - 2.5+:      Level 3 (stark)
    """
    if score < 0.5:
        return 0
    elif score < 1.5:
        return 1
    elif score < 2.5:
        return 2
    else:
        return 3


def _create_heatmap_cell(value: float) -> PsychologyHeatmapCell:
    """Erstellt eine Heatmap-Zelle aus einem Rohwert."""
    heat_level = _score_to_heat_level(value)

    # Wert runden für Anzeige
    display_value = str(round(value))

    # CSS-Klasse
    css_class = f"heat-{heat_level}"

    return PsychologyHeatmapCell(
        value=value,
        heat_level=heat_level,
        display_value=display_value,
        css_class=css_class,
    )


def build_psychology_heatmap_rows(raw_rows: List[Dict[str, Any]]) -> List[PsychologyHeatmapRow]:
    """
    Baut strukturierte Heatmap-Rows aus Roh-Daten.

    Args:
        raw_rows: Liste von Dictionaries mit folgenden Keys:
            - name: str (Name des Clusters)
            - fomo: float (0-3+)
            - loss_fear: float (0-3+)
            - impulsivity: float (0-3+)
            - hesitation: float (0-3+)
            - rule_break: float (0-3+)

    Returns:
        Liste von PsychologyHeatmapRow-Objekten

    Beispiel:
        >>> raw = [
        ...     {
        ...         "name": "Trend-Folge Einstiege",
        ...         "fomo": 2.0,
        ...         "loss_fear": 1.0,
        ...         "impulsivity": 1.0,
        ...         "hesitation": 0.0,
        ...         "rule_break": 1.0,
        ...     }
        ... ]
        >>> rows = build_psychology_heatmap_rows(raw)
        >>> rows[0].name
        'Trend-Folge Einstiege'
        >>> rows[0].fomo.heat_level
        2
    """
    result = []

    for raw_row in raw_rows:
        row = PsychologyHeatmapRow(
            name=raw_row["name"],
            fomo=_create_heatmap_cell(raw_row.get("fomo", 0.0)),
            loss_fear=_create_heatmap_cell(raw_row.get("loss_fear", 0.0)),
            impulsivity=_create_heatmap_cell(raw_row.get("impulsivity", 0.0)),
            hesitation=_create_heatmap_cell(raw_row.get("hesitation", 0.0)),
            rule_break=_create_heatmap_cell(raw_row.get("rule_break", 0.0)),
        )
        result.append(row)

    return result


def serialize_psychology_heatmap_rows(rows: List[PsychologyHeatmapRow]) -> List[Dict[str, Any]]:
    """
    Serialisiert Heatmap-Rows für Template-Rendering.

    Konvertiert die strukturierten Row-Objekte in einfache Dictionaries,
    die direkt im Jinja2-Template verwendet werden können.

    Args:
        rows: Liste von PsychologyHeatmapRow-Objekten

    Returns:
        Liste von Dictionaries mit serialisierten Daten

    Beispiel:
        >>> rows = build_psychology_heatmap_rows([...])
        >>> serialized = serialize_psychology_heatmap_rows(rows)
        >>> serialized[0]["name"]
        'Trend-Folge Einstiege'
        >>> serialized[0]["fomo"]["css_class"]
        'heat-2'
    """
    result = []

    for row in rows:
        serialized = {
            "name": row.name,
            "fomo": asdict(row.fomo),
            "loss_fear": asdict(row.loss_fear),
            "impulsivity": asdict(row.impulsivity),
            "hesitation": asdict(row.hesitation),
            "rule_break": asdict(row.rule_break),
        }
        result.append(serialized)

    return result


def build_example_psychology_heatmap_data() -> List[Dict[str, Any]]:
    """
    Erzeugt Beispieldaten für die Heatmap (zu Testzwecken).

    Returns:
        Liste von Dictionaries mit Beispiel-Scores
    """
    return [
        {
            "name": "Trend-Folge Einstiege",
            "fomo": 2.0,
            "loss_fear": 1.0,
            "impulsivity": 1.0,
            "hesitation": 0.0,
            "rule_break": 1.0,
        },
        {
            "name": "Counter-Trend Einstiege",
            "fomo": 1.0,
            "loss_fear": 3.0,
            "impulsivity": 2.0,
            "hesitation": 1.0,
            "rule_break": 2.0,
        },
        {
            "name": "Breakout / Breakdowns",
            "fomo": 3.0,
            "loss_fear": 2.0,
            "impulsivity": 2.0,
            "hesitation": 1.0,
            "rule_break": 2.0,
        },
        {
            "name": "Take-Profit / Exits",
            "fomo": 1.0,
            "loss_fear": 2.0,
            "impulsivity": 1.0,
            "hesitation": 2.0,
            "rule_break": 1.0,
        },
        {
            "name": "Re-Entries / Scaling",
            "fomo": 2.0,
            "loss_fear": 1.0,
            "impulsivity": 3.0,
            "hesitation": 1.0,
            "rule_break": 3.0,
        },
    ]


def calculate_cluster_statistics(rows: List[PsychologyHeatmapRow]) -> Dict[str, Any]:
    """
    Berechnet aggregierte Statistiken über alle Cluster hinweg.

    Args:
        rows: Liste von PsychologyHeatmapRow-Objekten

    Returns:
        Dictionary mit aggregierten Metriken:
        - total_clusters: Anzahl der Cluster
        - avg_scores: Durchschnittswerte für jede Kategorie
        - max_scores: Maximalwerte für jede Kategorie
        - problem_clusters: Liste der Cluster mit hohen Scores (>=2.5)
    """
    if not rows:
        return {
            "total_clusters": 0,
            "avg_scores": {},
            "max_scores": {},
            "problem_clusters": [],
        }

    # Sammle alle Werte
    fomo_values = [row.fomo.value for row in rows]
    loss_fear_values = [row.loss_fear.value for row in rows]
    impulsivity_values = [row.impulsivity.value for row in rows]
    hesitation_values = [row.hesitation.value for row in rows]
    rule_break_values = [row.rule_break.value for row in rows]

    avg_scores = {
        "fomo": sum(fomo_values) / len(fomo_values),
        "loss_fear": sum(loss_fear_values) / len(loss_fear_values),
        "impulsivity": sum(impulsivity_values) / len(impulsivity_values),
        "hesitation": sum(hesitation_values) / len(hesitation_values),
        "rule_break": sum(rule_break_values) / len(rule_break_values),
    }

    max_scores = {
        "fomo": max(fomo_values),
        "loss_fear": max(loss_fear_values),
        "impulsivity": max(impulsivity_values),
        "hesitation": max(hesitation_values),
        "rule_break": max(rule_break_values),
    }

    # Finde Problem-Cluster (mindestens ein Score >= 2.5)
    problem_clusters = []
    for row in rows:
        max_value_in_row = max(
            row.fomo.value,
            row.loss_fear.value,
            row.impulsivity.value,
            row.hesitation.value,
            row.rule_break.value,
        )
        if max_value_in_row >= 2.5:
            problem_clusters.append(
                {
                    "name": row.name,
                    "max_score": max_value_in_row,
                }
            )

    return {
        "total_clusters": len(rows),
        "avg_scores": avg_scores,
        "max_scores": max_scores,
        "problem_clusters": problem_clusters,
    }


# ============================================================================
# Integration Helper für Trigger-Training-Report
# ============================================================================


def extract_psychology_scores_from_events(
    events: List[Any],  # TriggerTrainingEvent
) -> Dict[str, Dict[str, float]]:
    """
    Extrahiert Psychologie-Scores aus Trigger-Training-Events.

    Diese Funktion analysiert die Tags und Outcomes der Events und berechnet
    aggregierte Scores für verschiedene Trading-Cluster.

    Args:
        events: Liste von TriggerTrainingEvent-Objekten

    Returns:
        Dictionary mit Cluster-Namen als Keys und Score-Dicts als Values

    Beispiel:
        >>> scores = extract_psychology_scores_from_events(events)
        >>> scores["trend_follow"]["fomo"]
        2.0

    Hinweis:
        Dies ist eine vereinfachte Implementierung. In der Praxis sollte hier
        eine ausgefeilte Analyse der Event-Daten stattfinden, die z.B.:
        - Tag-Häufigkeiten auswertet
        - Outcome-Muster erkennt
        - Zeitliche Trends berücksichtigt
        - Reaktionszeiten analysiert
    """
    # TODO: Implementiere echte Analyse-Logik
    # Für jetzt: Dummy-Implementation als Platzhalter

    from collections import defaultdict

    cluster_scores = defaultdict(
        lambda: {
            "fomo": 0.0,
            "loss_fear": 0.0,
            "impulsivity": 0.0,
            "hesitation": 0.0,
            "rule_break": 0.0,
        }
    )

    # Beispiel-Analyse: Zähle bestimmte Outcomes und Tags
    for event in events:
        # Vereinfachte Cluster-Zuordnung basierend auf Tags
        cluster = _determine_cluster_from_tags(event.tags)

        # Erhöhe Scores basierend auf Outcome
        if hasattr(event, "outcome"):
            if event.outcome.value == "FOMO":
                cluster_scores[cluster]["fomo"] += 0.5
            elif event.outcome.value == "MISSED":
                cluster_scores[cluster]["hesitation"] += 0.5
            elif event.outcome.value == "LATE":
                cluster_scores[cluster]["hesitation"] += 0.3
            elif event.outcome.value == "RULE_BREAK":
                cluster_scores[cluster]["rule_break"] += 0.5

        # Impulsivität basierend auf Reaktionszeit
        if hasattr(event, "reaction_delay_s"):
            if event.reaction_delay_s < 1.0:  # Sehr schnelle Reaktion
                cluster_scores[cluster]["impulsivity"] += 0.2

    # Normalisiere Scores auf 0-3 Skala
    for cluster in cluster_scores:
        for metric in cluster_scores[cluster]:
            # Cappung bei 3.0
            cluster_scores[cluster][metric] = min(cluster_scores[cluster][metric], 3.0)

    return dict(cluster_scores)


def _determine_cluster_from_tags(tags: List[str]) -> str:
    """Bestimmt den Trading-Cluster basierend auf Tags."""
    tags_lower = [t.lower() for t in tags]

    if any(t in tags_lower for t in ["trend", "trend_follow", "with_trend"]):
        return "trend_follow"
    elif any(t in tags_lower for t in ["counter", "reversal", "against_trend"]):
        return "counter_trend"
    elif any(t in tags_lower for t in ["breakout", "breakdown", "break"]):
        return "breakout"
    elif any(t in tags_lower for t in ["exit", "take_profit", "tp"]):
        return "exit"
    elif any(t in tags_lower for t in ["reentry", "scaling", "add"]):
        return "reentry"
    else:
        return "other"
