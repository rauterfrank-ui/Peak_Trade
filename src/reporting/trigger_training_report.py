from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Sequence, Optional, Mapping, Any, List, Dict
from collections import defaultdict

import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class TriggerOutcome(str, Enum):
    HIT = "HIT"
    MISSED = "MISSED"
    LATE = "LATE"
    FOMO = "FOMO"
    RULE_BREAK = "RULE_BREAK"
    OTHER = "OTHER"


@dataclass
class TriggerTrainingEvent:
    """Ein einzelnes Trigger-Training-Event.

    Diese Struktur ist bewusst generisch gehalten und kann sowohl aus
    Offline-Runs als auch Live- / Paper-Trading-Sessions befüllt werden.
    """

    timestamp: pd.Timestamp
    symbol: str
    signal_state: int  # z.B. -1, 0, 1
    recommended_action: str
    user_action: str
    outcome: TriggerOutcome
    reaction_delay_s: float
    pnl_after_bars: float
    tags: List[str]
    note: str = ""


def events_to_dataframe(events: Iterable[TriggerTrainingEvent]) -> pd.DataFrame:
    """Konvertiert eine Liste von TriggerTrainingEvents in ein DataFrame."""
    records = []
    for ev in events:
        records.append(
            {
                "timestamp": ev.timestamp,
                "symbol": ev.symbol,
                "signal_state": ev.signal_state,
                "recommended_action": ev.recommended_action,
                "user_action": ev.user_action,
                "outcome": ev.outcome.value,
                "reaction_delay_s": ev.reaction_delay_s,
                "pnl_after_bars": ev.pnl_after_bars,
                "tags": ",".join(ev.tags),
                "note": ev.note,
            }
        )
    if not records:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "symbol",
                "signal_state",
                "recommended_action",
                "user_action",
                "outcome",
                "reaction_delay_s",
                "pnl_after_bars",
                "tags",
                "note",
            ]
        )
    return pd.DataFrame.from_records(records)


def _ensure_output_dir(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _aggregate_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["outcome", "count"])
    return (
        df.groupby("outcome")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )


def _plot_reaction_time_hist(df: pd.DataFrame, output_dir: Path) -> Optional[str]:
    if not HAS_MATPLOTLIB:
        return None
    if df.empty or "reaction_delay_s" not in df.columns:
        return None
    plt.figure()
    df["reaction_delay_s"].hist(bins=20)
    plt.title("Reaktionszeit-Verteilung")
    plt.xlabel("Reaktionszeit (Sekunden)")
    plt.ylabel("Anzahl Events")
    img_name = "reaction_delay_hist.png"
    img_path = output_dir / img_name
    plt.tight_layout()
    plt.savefig(img_path)
    plt.close()
    return img_name


def _find_pain_points(df: pd.DataFrame, max_items: int = 10) -> pd.DataFrame:
    """Finde 'Pain Points': Hohe pnl_after_bars bei MISSED/LATE/RULE_BREAK."""
    if df.empty:
        return df
    mask = df["outcome"].isin(
        [TriggerOutcome.MISSED.value, TriggerOutcome.LATE.value, TriggerOutcome.RULE_BREAK.value]
    )
    sub = df[mask].copy()
    if sub.empty:
        return sub
    sub = sub.sort_values("pnl_after_bars", ascending=False)
    return sub.head(max_items)


def _aggregate_tags(df: pd.DataFrame) -> pd.DataFrame:
    """Zählt Tags über alle Events hinweg."""
    if df.empty or "tags" not in df.columns:
        return pd.DataFrame(columns=["tag", "count"])
    all_tags = []
    for tags_str in df["tags"]:
        if not tags_str:
            continue
        for t in str(tags_str).split(","):
            t = t.strip()
            if t:
                all_tags.append(t)
    if not all_tags:
        return pd.DataFrame(columns=["tag", "count"])
    tag_series = pd.Series(all_tags)
    return (
        tag_series.value_counts()
        .reset_index()
        .rename(columns={"index": "tag", 0: "count"})
    )


def _determine_cluster_from_tags(tags: List[str]) -> str:
    """Bestimmt Trading-Cluster basierend auf Tags."""
    tags_lower = [t.lower() for t in tags]
    tags_joined = " ".join(tags_lower)  # Join für multi-word matching
    
    # Breakout zuerst prüfen (spezifischer)
    if any(keyword in tags_joined for keyword in ["breakout", "breakdown", "break"]):
        return "breakout"
    # Counter-Trend (prüfe auch zusammengesetzte Tags)
    elif any(keyword in tags_joined for keyword in ["counter_trend", "counter", "reversal", "against_trend"]):
        return "counter_trend"
    # Exit / Take-Profit
    elif any(keyword in tags_joined for keyword in ["exit", "take_profit", "tp"]):
        return "exit"
    # Re-Entry / Scaling
    elif any(keyword in tags_joined for keyword in ["reentry", "scaling", "add"]):
        return "reentry"
    # Trend-Follow (am Ende, da "trend" auch in anderen vorkommen kann)
    elif any(keyword in tags_joined for keyword in ["trend_follow", "trend", "with_trend", "discipline"]):
        return "trend_follow"
    else:
        return "other"


def calculate_psychology_scores_from_events(
    events: Sequence[TriggerTrainingEvent],
) -> Dict[str, Dict[str, float]]:
    """
    Berechnet Psychologie-Scores aus Trigger-Training-Events.
    
    Diese Heuristik analysiert die Events und extrahiert psychologische Muster:
    - FOMO: Spät-Entries bei bereits gelaufenen Signalen
    - Verlustangst: Zu enge Stops, frühes Aussteigen
    - Impulsivität: Sehr schnelle Reaktionen (<1s)
    - Zögern: Verpasste Signale (MISSED), späte Entries (LATE)
    - Regelbruch: Trades gegen Signal-Richtung oder ohne Setup
    
    Parameters
    ----------
    events : Sequence[TriggerTrainingEvent]
        Liste von Trigger-Training-Events
    
    Returns
    -------
    Dict[str, Dict[str, float]]
        Dictionary mit Cluster-Namen als Keys und Score-Dicts als Values.
        Jeder Score liegt zwischen 0.0 und 3.0.
        
    Example
    -------
    >>> scores = calculate_psychology_scores_from_events(events)
    >>> scores["trend_follow"]["fomo"]
    2.0
    """
    # Score-Akkumulatoren pro Cluster
    cluster_scores = defaultdict(lambda: {
        "fomo": 0.0,
        "loss_fear": 0.0,
        "impulsivity": 0.0,
        "hesitation": 0.0,
        "rule_break": 0.0,
    })
    
    # Zähler für Normalisierung
    cluster_counts = defaultdict(int)
    
    for event in events:
        # Cluster bestimmen
        cluster = _determine_cluster_from_tags(event.tags)
        cluster_counts[cluster] += 1
        
        # === FOMO-Score ===
        # FOMO-Outcome direkt -> hoher Score
        if event.outcome == TriggerOutcome.FOMO:
            cluster_scores[cluster]["fomo"] += 1.0
        # Späte Entries (LATE) mit negativem PnL -> FOMO-Indikator
        elif event.outcome == TriggerOutcome.LATE and event.pnl_after_bars < 0:
            cluster_scores[cluster]["fomo"] += 0.5
        
        # === Verlustangst-Score ===
        # Frühes Aussteigen bei profitablen Setups (negative Tags)
        if "fear" in ",".join(event.tags).lower() or "loss_aversion" in ",".join(event.tags).lower():
            cluster_scores[cluster]["loss_fear"] += 0.7
        # Sehr konservative Reaktion trotz gutem Signal
        if event.reaction_delay_s > 10.0 and event.pnl_after_bars > 50.0:
            cluster_scores[cluster]["loss_fear"] += 0.3
        
        # === Impulsivität-Score ===
        # Sehr schnelle Reaktion (<1s) kann auf Impulsivität hinweisen
        if event.reaction_delay_s < 1.0:
            cluster_scores[cluster]["impulsivity"] += 0.4
        # FOMO-Trades sind oft impulsiv
        if event.outcome == TriggerOutcome.FOMO:
            cluster_scores[cluster]["impulsivity"] += 0.5
        
        # === Zögern-Score ===
        # Verpasste Signale -> direkter Indikator
        if event.outcome == TriggerOutcome.MISSED:
            cluster_scores[cluster]["hesitation"] += 1.0
        # Späte Entries (LATE) -> Zögern
        elif event.outcome == TriggerOutcome.LATE:
            cluster_scores[cluster]["hesitation"] += 0.7
        # Lange Reaktionszeit (>8s) bei gutem Signal
        elif event.reaction_delay_s > 8.0 and event.pnl_after_bars > 30.0:
            cluster_scores[cluster]["hesitation"] += 0.4
        
        # === Regelbruch-Score ===
        # RULE_BREAK-Outcome direkt
        if event.outcome == TriggerOutcome.RULE_BREAK:
            cluster_scores[cluster]["rule_break"] += 1.2
        # Tags mit "break", "violation" etc.
        if any(tag in ",".join(event.tags).lower() for tag in ["break", "violation", "no_setup"]):
            cluster_scores[cluster]["rule_break"] += 0.6
    
    # Normalisierung und Cappung auf 0-3 Skala
    normalized_scores = {}
    
    for cluster, scores in cluster_scores.items():
        count = cluster_counts[cluster]
        if count == 0:
            continue
        
        normalized = {}
        for metric, raw_score in scores.items():
            # Normalisiere durch Anzahl Events im Cluster
            # Multipliziere mit Faktor, um in 0-3 Bereich zu kommen
            normalized_value = (raw_score / count) * 2.5
            # Cappe bei 3.0
            normalized_value = min(normalized_value, 3.0)
            normalized[metric] = round(normalized_value, 2)
        
        normalized_scores[cluster] = normalized
    
    return normalized_scores


def _build_psychology_heatmap_html(
    psychology_scores: Dict[str, Dict[str, float]],
) -> str:
    """
    Erzeugt HTML für Psychologie-Heatmap (inline, ohne Template-System).
    
    Parameters
    ----------
    psychology_scores : Dict[str, Dict[str, float]]
        Psychologie-Scores pro Cluster
    
    Returns
    -------
    str
        HTML-String mit der Heatmap
    """
    # Mapping von Cluster-Namen zu Display-Namen
    cluster_labels = {
        "trend_follow": "Trend-Folge Einstiege",
        "counter_trend": "Counter-Trend Einstiege",
        "breakout": "Breakout / Breakdowns",
        "exit": "Take-Profit / Exits",
        "reentry": "Re-Entries / Scaling",
        "other": "Sonstige Setups",
    }
    
    def _get_heat_class(value: float) -> str:
        """Bestimmt CSS-Klasse basierend auf Score."""
        if value < 0.5:
            return "heat-0"
        elif value < 1.5:
            return "heat-1"
        elif value < 2.5:
            return "heat-2"
        else:
            return "heat-3"
    
    html_parts = []
    
    # Styles für Heatmap
    html_parts.append("""
    <style>
        .psychology-heatmap {
            margin: 20px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            background: #f9f9f9;
        }
        .psychology-heatmap h2 {
            margin-top: 0;
            color: #333;
        }
        .heatmap-legend {
            margin: 10px 0;
            font-size: 12px;
            color: #666;
        }
        .legend-item {
            display: inline-block;
            margin-right: 15px;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
        }
        .heatmap-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            font-size: 12px;
        }
        .heatmap-table th {
            background: #e9ecef;
            padding: 10px 8px;
            text-align: center;
            font-weight: 600;
            border: 1px solid #ddd;
        }
        .heatmap-table td {
            padding: 10px 8px;
            text-align: center;
            border: 1px solid #ddd;
            font-weight: 600;
        }
        .heatmap-table .row-label {
            text-align: left;
            font-weight: 500;
            background: #f8f9fa;
        }
        .heat-0 { background: #e9ecef; color: #6c757d; }
        .heat-1 { background: #cfe2ff; color: #084298; }
        .heat-2 { background: #ffe69c; color: #664d03; }
        .heat-3 { background: #f8d7da; color: #842029; }
        .heatmap-note {
            margin-top: 15px;
            padding: 12px;
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            font-size: 11px;
            color: #856404;
        }
    </style>
    """)
    
    # Heatmap-Container
    html_parts.append('<div class="psychology-heatmap">')
    html_parts.append('<h2>🧠 Psychologie-Heatmap</h2>')
    html_parts.append(
        '<p style="font-size: 12px; color: #666;">Diese Heatmap zeigt psychologische Muster '
        'über die analysierten Trigger-Training-Events. Höhere Werte bedeuten stärkere Ausprägung.</p>'
    )
    
    # Legende
    html_parts.append('<div class="heatmap-legend">')
    html_parts.append('<strong>Skala:</strong> ')
    html_parts.append('<span class="legend-item heat-0">0 – kein Thema</span>')
    html_parts.append('<span class="legend-item heat-1">1 – leicht</span>')
    html_parts.append('<span class="legend-item heat-2">2 – mittel</span>')
    html_parts.append('<span class="legend-item heat-3">3 – stark</span>')
    html_parts.append('</div>')
    
    # Tabelle
    if not psychology_scores:
        html_parts.append('<p style="color: #999;">Keine Psychologie-Daten verfügbar.</p>')
    else:
        html_parts.append('<table class="heatmap-table">')
        
        # Header
        html_parts.append('<thead><tr>')
        html_parts.append('<th class="row-label">Kontext / Cluster</th>')
        html_parts.append('<th>FOMO<br><span style="font-size: 10px; font-weight: normal;">Hinterherjagen</span></th>')
        html_parts.append('<th>Verlustangst<br><span style="font-size: 10px; font-weight: normal;">Nicht verlieren</span></th>')
        html_parts.append('<th>Impulsivität<br><span style="font-size: 10px; font-weight: normal;">Spontan-Trades</span></th>')
        html_parts.append('<th>Zögern<br><span style="font-size: 10px; font-weight: normal;">Signale verpasst</span></th>')
        html_parts.append('<th>Regelbruch<br><span style="font-size: 10px; font-weight: normal;">Setup ignoriert</span></th>')
        html_parts.append('</tr></thead>')
        
        # Body
        html_parts.append('<tbody>')
        for cluster, scores in sorted(psychology_scores.items()):
            label = cluster_labels.get(cluster, cluster.replace("_", " ").title())
            html_parts.append('<tr>')
            html_parts.append(f'<td class="row-label">{label}</td>')
            
            for metric in ["fomo", "loss_fear", "impulsivity", "hesitation", "rule_break"]:
                value = scores.get(metric, 0.0)
                heat_class = _get_heat_class(value)
                display_value = f"{value:.1f}" if value > 0 else "0"
                html_parts.append(f'<td class="{heat_class}">{display_value}</td>')
            
            html_parts.append('</tr>')
        html_parts.append('</tbody>')
        html_parts.append('</table>')
    
    # Hinweis
    html_parts.append(
        '<div class="heatmap-note">'
        '<strong>💡 Interpretation:</strong> '
        'Ziel ist nicht "alles auf 0", sondern Bewusstsein über typische Trigger. '
        'Nutze die Heatmap, um gezielt Drills für Cluster mit hohen Werten zu planen.'
        '</div>'
    )
    
    html_parts.append('</div>')
    
    return "".join(html_parts)


def build_trigger_training_report(
    events: Sequence[TriggerTrainingEvent],
    output_dir: Path,
    *,
    session_meta: Optional[Mapping[str, Any]] = None,
    report_filename: str = "trigger_training_report.html",
) -> Path:
    """Erzeugt einen Trigger-Training-HTML-Report.

    Die Funktion nimmt eine Liste von Events und erzeugt einen Report, der:
      - Outcome-Verteilung zeigt
      - Reaktionszeit-Verteilung visualisiert
      - Pain Points hervorhebt
      - Tag-basierte Muster zusammenfasst
    """
    output_dir = _ensure_output_dir(output_dir)
    df = events_to_dataframe(events)
    report_path = output_dir / report_filename

    outcome_agg = _aggregate_outcomes(df)
    reaction_hist_img = _plot_reaction_time_hist(df, output_dir)
    pain_points = _find_pain_points(df)
    tag_agg = _aggregate_tags(df)

    html_parts: list[str] = []
    html_parts.append("<html><head><meta charset='utf-8'><title>Trigger Training Report</title>")
    html_parts.append(
        "<style>"
        "body { font-family: sans-serif; margin: 20px; }"
        "h1, h2, h3 { font-family: sans-serif; }"
        "table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }"
        "th, td { border: 1px solid #ccc; padding: 4px 6px; font-size: 12px; }"
        ".note { font-size: 11px; color: #666; }"
        "</style></head><body>"
    )

    html_parts.append("<h1>Trigger Training Report</h1>")

    # Meta
    html_parts.append("<h2>Session Meta</h2>")
    html_parts.append("<table>")
    if session_meta:
        for k, v in session_meta.items():
            html_parts.append(f"<tr><td>{k}</td><td>{v}</td></tr>")
    else:
        html_parts.append("<tr><td colspan='2'>Keine Meta-Daten angegeben.</td></tr>")
    html_parts.append("</table>")

    html_parts.append(
        "<p class='note'>Hinweis: Dieser Report dient dem psychologischen Training "
        "und der Verbesserung von Reaktionsmustern. Er ist kein Performance-Report "
        "im klassischen Sinne.</p>"
    )

    # Outcome-Übersicht
    html_parts.append("<h2>Outcome Übersicht</h2>")
    if outcome_agg.empty:
        html_parts.append("<p>Keine Events vorhanden.</p>")
    else:
        html_parts.append("<table>")
        html_parts.append("<tr><th>Outcome</th><th>Anzahl</th></tr>")
        for _, row in outcome_agg.iterrows():
            html_parts.append(f"<tr><td>{row['outcome']}</td><td>{row['count']}</td></tr>")
        html_parts.append("</table>")

    # Reaktionszeiten
    if reaction_hist_img:
        html_parts.append("<h2>Reaktionszeiten</h2>")
        html_parts.append(f"<img src='{reaction_hist_img}' alt='Reaction Delay Histogram' />")

    # Pain Points
    html_parts.append("<h2>Pain Points (verpasste/zu späte Chancen)</h2>")
    if pain_points.empty:
        html_parts.append("<p>Keine Pain Points gefunden.</p>")
    else:
        html_parts.append("<table>")
        html_parts.append(
            "<tr><th>timestamp</th><th>symbol</th><th>outcome</th>"
            "<th>reaction_delay_s</th><th>pnl_after_bars</th><th>tags</th><th>note</th></tr>"
        )
        for _, row in pain_points.iterrows():
            html_parts.append("<tr>")
            for col in [
                "timestamp",
                "symbol",
                "outcome",
                "reaction_delay_s",
                "pnl_after_bars",
                "tags",
                "note",
            ]:
                html_parts.append(f"<td>{row.get(col, '')}</td>")
            html_parts.append("</tr>")
        html_parts.append("</table>")

    # Tag-Analyse
    html_parts.append("<h2>Tag-basierte Analyse</h2>")
    if tag_agg.empty:
        html_parts.append("<p>Keine Tags vorhanden.</p>")
    else:
        html_parts.append("<table>")
        html_parts.append("<tr><th>Tag</th><th>Anzahl</th></tr>")
        for _, row in tag_agg.iterrows():
            html_parts.append(f"<tr><td>{row['tag']}</td><td>{row['count']}</td></tr>")
        html_parts.append("</table>")

    # Psychologie-Heatmap
    if events:
        psychology_scores = calculate_psychology_scores_from_events(events)
        if psychology_scores:
            psychology_html = _build_psychology_heatmap_html(psychology_scores)
            html_parts.append(psychology_html)

    html_parts.append("</body></html>")

    report_path.write_text("".join(html_parts), encoding="utf-8")
    return report_path
