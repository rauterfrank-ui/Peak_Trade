from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from src.reporting.trigger_training_report import TriggerOutcome, TriggerTrainingEvent


def _events_to_dataframe_with_session(
    sessions: Sequence[tuple[str, Sequence[TriggerTrainingEvent]]]
) -> pd.DataFrame:
    """Konvertiert (session_id, Events) in ein gemeinsames DataFrame mit session_id-Spalte."""
    records: list[Mapping[str, Any]] = []

    for session_id, events in sessions:
        for ev in events:
            records.append(
                {
                    "session_id": session_id,
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
                "session_id",
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


def build_operator_meta_report(
    sessions: Sequence[tuple[str, Sequence[TriggerTrainingEvent]]],
    output_path: Path,
) -> Path:
    """Erzeugt einen Trigger-Training Operator-Meta-Report (HTML) über mehrere Sessions.

    Parameters
    ----------
    sessions:
        Liste von Tupeln (session_id, events), wobei events eine Sequenz von
        TriggerTrainingEvent-Objekten ist.
    output_path:
        Zieldatei für den HTML-Report. Das übergeordnete Verzeichnis wird bei Bedarf angelegt.

    Returns
    -------
    Path
        Pfad zur erzeugten HTML-Datei.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = _events_to_dataframe_with_session(sessions)
    if df.empty:
        # Minimaler Report, wenn keine Events vorhanden sind.
        html = (
            "<html><head><meta charset='utf-8'><title>Trigger Training – Operator Meta Report</title>"
            "<style>"
            "body { font-family: sans-serif; margin: 20px; }"
            "h1, h2, h3 { font-family: sans-serif; }"
            ".note { font-size: 11px; color: #666; }"
            "</style></head><body>"
            "<h1>Trigger Training – Operator Meta Report</h1>"
            "<p class='note'>Keine Events vorhanden. Es wurden keine Trigger-Training-Daten übergeben.</p>"
            "</body></html>"
        )
        output_path.write_text(html, encoding="utf-8")
        return output_path

    # Basis-Aggregationen
    df["reaction_delay_s"] = pd.to_numeric(df["reaction_delay_s"], errors="coerce").fillna(0.0)
    df["pnl_after_bars"] = pd.to_numeric(df["pnl_after_bars"], errors="coerce").fillna(0.0)

    # Outcome-Verteilung pro Session
    (
        df.groupby(["session_id", "outcome"])
        .size()
        .reset_index(name="count")
    )

    # Globale Outcome-Verteilung
    global_outcome = (
        df.groupby("outcome")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    # Durchschnittliche Reaktionszeit pro Session
    session_reaction = (
        df.groupby("session_id")["reaction_delay_s"]
        .mean()
        .reset_index(name="avg_reaction_delay_s")
    )

    # Pain Score pro Session: Summe pnl_after_bars für MISSED/LATE/RULE_BREAK
    pain_mask = df["outcome"].isin(
        [
            TriggerOutcome.MISSED.value,
            TriggerOutcome.LATE.value,
            TriggerOutcome.RULE_BREAK.value,
        ]
    )
    pain_df = (
        df[pain_mask]
        .groupby("session_id")["pnl_after_bars"]
        .sum()
        .reset_index(name="pain_score")
    )

    # Anzahl Events pro Session
    n_events_df = (
        df.groupby("session_id")
        .size()
        .reset_index(name="n_events")
    )

    # HIT/MISSED-Rates pro Session
    hit_df = (
        df[df["outcome"] == TriggerOutcome.HIT.value]
        .groupby("session_id")
        .size()
        .reset_index(name="n_hit")
    )
    missed_df = (
        df[df["outcome"] == TriggerOutcome.MISSED.value]
        .groupby("session_id")
        .size()
        .reset_index(name="n_missed")
    )

    # Zusammenführen
    overview = n_events_df.merge(session_reaction, on="session_id", how="left")
    overview = overview.merge(pain_df, on="session_id", how="left")
    overview = overview.merge(hit_df, on="session_id", how="left")
    overview = overview.merge(missed_df, on="session_id", how="left")

    overview["n_hit"] = overview["n_hit"].fillna(0).astype(int)
    overview["n_missed"] = overview["n_missed"].fillna(0).astype(int)
    overview["pain_score"] = overview["pain_score"].fillna(0.0)

    # Raten berechnen
    overview["hit_rate"] = overview["n_hit"] / overview["n_events"].where(overview["n_events"] > 0, 1)
    overview["missed_rate"] = overview["n_missed"] / overview["n_events"].where(overview["n_events"] > 0, 1)

    # Top-Sessions nach Pain Score
    top_pain = overview.sort_values("pain_score", ascending=False).head(5)

    # HTML aufbauen
    html_parts: list[str] = []
    html_parts.append(
        "<html><head><meta charset='utf-8'><title>Trigger Training – Operator Meta Report</title>"
    )
    html_parts.append(
        "<style>"
        "body { font-family: sans-serif; margin: 20px; }"
        "h1, h2, h3 { font-family: sans-serif; }"
        "table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }"
        "th, td { border: 1px solid #ccc; padding: 4px 6px; font-size: 12px; }"
        ".note { font-size: 11px; color: #666; }"
        "</style></head><body>"
    )

    html_parts.append("<h1>Trigger Training – Operator Meta Report</h1>")
    html_parts.append(
        "<p class='note'>Übersicht über mehrere Trigger-Training-Sessions (Drills). "
        "Ziel: Entwicklung von Reaktionsqualität, Disziplin und Pain Points über die Zeit sichtbar machen.</p>"
    )

    # Sessions Overview
    html_parts.append("<h2>Sessions Overview</h2>")
    html_parts.append("<table>")
    html_parts.append(
        "<tr>"
        "<th>session_id</th>"
        "<th>n_events</th>"
        "<th>hit_rate</th>"
        "<th>missed_rate</th>"
        "<th>avg_reaction_delay_s</th>"
        "<th>pain_score</th>"
        "</tr>"
    )
    for _, row in overview.sort_values("session_id").iterrows():
        html_parts.append("<tr>")
        html_parts.append(f"<td>{row['session_id']}</td>")
        html_parts.append(f"<td>{int(row['n_events'])}</td>")
        html_parts.append(f"<td>{row['hit_rate']:.2f}</td>")
        html_parts.append(f"<td>{row['missed_rate']:.2f}</td>")
        html_parts.append(f"<td>{row['avg_reaction_delay_s']:.2f}</td>")
        html_parts.append(f"<td>{row['pain_score']:.2f}</td>")
        html_parts.append("</tr>")
    html_parts.append("</table>")

    # Globale Outcome-Verteilung
    html_parts.append("<h2>Globale Outcome-Verteilung</h2>")
    html_parts.append("<table>")
    html_parts.append("<tr><th>Outcome</th><th>Anzahl</th></tr>")
    for _, row in global_outcome.iterrows():
        html_parts.append(f"<tr><td>{row['outcome']}</td><td>{int(row['count'])}</td></tr>")
    html_parts.append("</table>")

    # Top Pain-Sessions
    html_parts.append("<h2>Top Pain Sessions</h2>")
    if top_pain.empty:
        html_parts.append("<p>Keine Pain-Sessions erkannt.</p>")
    else:
        html_parts.append("<table>")
        html_parts.append(
            "<tr><th>session_id</th><th>n_events</th><th>pain_score</th>"
            "<th>hit_rate</th><th>missed_rate</th><th>avg_reaction_delay_s</th></tr>"
        )
        for _, row in top_pain.iterrows():
            html_parts.append("<tr>")
            html_parts.append(f"<td>{row['session_id']}</td>")
            html_parts.append(f"<td>{int(row['n_events'])}</td>")
            html_parts.append(f"<td>{row['pain_score']:.2f}</td>")
            html_parts.append(f"<td>{row['hit_rate']:.2f}</td>")
            html_parts.append(f"<td>{row['missed_rate']:.2f}</td>")
            html_parts.append(f"<td>{row['avg_reaction_delay_s']:.2f}</td>")
            html_parts.append("</tr>")
        html_parts.append("</table>")

    html_parts.append("</body></html>")

    output_path.write_text("".join(html_parts), encoding="utf-8")
    return output_path
