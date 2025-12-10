from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Sequence, Optional, Mapping, Any, List

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

    html_parts.append("</body></html>")

    report_path.write_text("".join(html_parts), encoding="utf-8")
    return report_path
