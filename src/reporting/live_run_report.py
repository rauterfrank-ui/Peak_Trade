from __future__ import annotations

# src/reporting/live_run_report.py
"""
Peak_Trade: Live Run Report (Phase 32)
======================================

Report-Generierung für Shadow-/Paper-Runs basierend auf Run-Logs.

Dieses Modul erstellt Markdown- und HTML-Reports aus den von LiveRunLogger
erzeugten Dateien (meta.json, events.parquet/csv).

Features:
- Summary-Metriken (Total Orders, Fills, PnL, etc.)
- Equity-Kurve als Text-Chart (optional)
- Signal-Statistiken
- Risk-Events
- Trade-Liste

Usage:
    from src.reporting.live_run_report import build_live_run_report

    report = build_live_run_report(
        meta_path="live_runs/20251204_180000_paper_ma_crossover_BTC-EUR_1m/meta.json",
        events_path="live_runs/20251204_180000_paper_ma_crossover_BTC-EUR_1m/events.parquet"
    )
    print(report.to_markdown())

See also:
    - src/live/run_logging.py (LiveRunLogger, LiveRunMetadata, LiveRunEvent)
    - src/reporting/base.py (Report, ReportSection)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .base import Report, ReportSection, df_to_markdown, dict_to_markdown_table, format_metric


# =============================================================================
# Report Builder
# =============================================================================


def build_live_run_report(
    meta_path: str | Path,
    events_path: str | Path,
    include_trade_list: bool = True,
    max_trades_shown: int = 50,
) -> Report:
    """
    Erstellt einen Report aus Run-Logs.

    Args:
        meta_path: Pfad zur meta.json Datei
        events_path: Pfad zur events.parquet/csv Datei
        include_trade_list: Trade-Liste einschließen
        max_trades_shown: Maximale Anzahl angezeigter Trades

    Returns:
        Report-Objekt mit allen Sections

    Raises:
        FileNotFoundError: Wenn Dateien nicht gefunden werden
        ValueError: Wenn Daten ungültig sind
    """
    meta_path = Path(meta_path)
    events_path = Path(events_path)

    if not meta_path.exists():
        raise FileNotFoundError(f"meta.json nicht gefunden: {meta_path}")
    if not events_path.exists():
        raise FileNotFoundError(f"Events-Datei nicht gefunden: {events_path}")

    # Metadaten laden
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # Events laden
    if str(events_path).endswith(".parquet"):
        events_df = pd.read_parquet(events_path)
    else:
        events_df = pd.read_csv(events_path)

    # Report erstellen
    report = Report(
        title=f"Live Run Report: {meta.get('run_id', 'Unknown')}",
        metadata={
            "run_id": meta.get("run_id"),
            "mode": meta.get("mode"),
            "strategy": meta.get("strategy_name"),
            "symbol": meta.get("symbol"),
            "timeframe": meta.get("timeframe"),
            "started_at": meta.get("started_at"),
            "ended_at": meta.get("ended_at"),
        },
    )

    # Sections hinzufügen
    report.add_section(_build_summary_section(meta, events_df))
    report.add_section(_build_session_info_section(meta))
    report.add_section(_build_signal_stats_section(events_df))
    report.add_section(_build_order_stats_section(events_df))
    report.add_section(_build_risk_events_section(events_df))

    if include_trade_list:
        report.add_section(_build_trade_list_section(events_df, max_trades_shown))

    report.add_section(_build_config_section(meta))

    return report


# =============================================================================
# Section Builders
# =============================================================================


def _build_summary_section(meta: Dict[str, Any], events_df: pd.DataFrame) -> ReportSection:
    """Baut die Summary-Section."""
    total_steps = len(events_df)

    # Orders summieren
    total_orders = (
        events_df["orders_generated"].sum() if "orders_generated" in events_df.columns else 0
    )
    total_filled = events_df["orders_filled"].sum() if "orders_filled" in events_df.columns else 0
    total_rejected = (
        events_df["orders_rejected"].sum() if "orders_rejected" in events_df.columns else 0
    )
    total_blocked = (
        events_df["orders_blocked"].sum() if "orders_blocked" in events_df.columns else 0
    )

    # Signal-Änderungen
    signal_changes = (
        events_df["signal_changed"].sum() if "signal_changed" in events_df.columns else 0
    )

    # Position
    final_position = (
        events_df["position_size"].iloc[-1]
        if "position_size" in events_df.columns and len(events_df) > 0
        else 0.0
    )

    # Laufzeit berechnen
    started_at = meta.get("started_at")
    ended_at = meta.get("ended_at")
    duration_str = "N/A"
    if started_at and ended_at:
        try:
            start_dt = datetime.fromisoformat(started_at)
            end_dt = datetime.fromisoformat(ended_at)
            duration = end_dt - start_dt
            duration_str = str(duration).split(".")[0]  # Ohne Mikrosekunden
        except (ValueError, TypeError):
            pass

    summary_data = {
        "Total Steps": total_steps,
        "Signal Changes": int(signal_changes),
        "Total Orders Generated": int(total_orders),
        "Orders Filled": int(total_filled),
        "Orders Rejected": int(total_rejected),
        "Orders Blocked (Risk)": int(total_blocked),
        "Fill Rate": f"{total_filled / total_orders * 100:.1f}%" if total_orders > 0 else "N/A",
        "Final Position": f"{final_position:.6f}",
        "Run Duration": duration_str,
    }

    return ReportSection(
        title="Summary",
        content_markdown=dict_to_markdown_table(
            summary_data, key_header="Metric", value_header="Value"
        ),
    )


def _build_session_info_section(meta: Dict[str, Any]) -> ReportSection:
    """Baut die Session-Info-Section."""
    info = {
        "Run ID": meta.get("run_id", "N/A"),
        "Mode": meta.get("mode", "N/A"),
        "Strategy": meta.get("strategy_name", "N/A"),
        "Symbol": meta.get("symbol", "N/A"),
        "Timeframe": meta.get("timeframe", "N/A"),
        "Started At": meta.get("started_at", "N/A"),
        "Ended At": meta.get("ended_at", "N/A"),
        "Notes": meta.get("notes", ""),
    }

    return ReportSection(
        title="Session Info",
        content_markdown=dict_to_markdown_table(info, key_header="Property", value_header="Value"),
    )


def _build_signal_stats_section(events_df: pd.DataFrame) -> ReportSection:
    """Baut die Signal-Statistik-Section."""
    if "signal" not in events_df.columns:
        return ReportSection(
            title="Signal Statistics",
            content_markdown="*No signal data available*",
        )

    signal_counts = events_df["signal"].value_counts().to_dict()

    # Signale interpretieren
    signal_labels = {-1: "Sell", 0: "Neutral", 1: "Buy"}
    labeled_counts = {signal_labels.get(k, str(k)): v for k, v in signal_counts.items()}

    content_lines = ["**Signal Distribution:**", ""]
    content_lines.append(
        dict_to_markdown_table(labeled_counts, key_header="Signal", value_header="Count")
    )

    # Signal-Änderungen zählen
    if "signal_changed" in events_df.columns:
        changes = int(events_df["signal_changed"].sum())
        content_lines.append("")
        content_lines.append(f"**Total Signal Changes:** {changes}")

    return ReportSection(
        title="Signal Statistics",
        content_markdown="\n".join(content_lines),
    )


def _build_order_stats_section(events_df: pd.DataFrame) -> ReportSection:
    """Baut die Order-Statistik-Section."""
    required_cols = ["orders_generated", "orders_filled", "orders_rejected", "orders_blocked"]
    available_cols = [c for c in required_cols if c in events_df.columns]

    if not available_cols:
        return ReportSection(
            title="Order Statistics",
            content_markdown="*No order data available*",
        )

    # Nur Zeilen mit Orders
    orders_mask = (
        events_df["orders_generated"] > 0
        if "orders_generated" in events_df.columns
        else pd.Series([False] * len(events_df))
    )
    order_events = events_df[orders_mask]

    if len(order_events) == 0:
        return ReportSection(
            title="Order Statistics",
            content_markdown="*No orders were generated during this run*",
        )

    stats = {
        "Events with Orders": len(order_events),
        "Total Orders Generated": (
            int(events_df["orders_generated"].sum())
            if "orders_generated" in events_df.columns
            else 0
        ),
        "Total Filled": (
            int(events_df["orders_filled"].sum()) if "orders_filled" in events_df.columns else 0
        ),
        "Total Rejected": (
            int(events_df["orders_rejected"].sum()) if "orders_rejected" in events_df.columns else 0
        ),
        "Total Blocked (Risk)": (
            int(events_df["orders_blocked"].sum()) if "orders_blocked" in events_df.columns else 0
        ),
    }

    return ReportSection(
        title="Order Statistics",
        content_markdown=dict_to_markdown_table(stats, key_header="Metric", value_header="Value"),
    )


def _build_risk_events_section(events_df: pd.DataFrame) -> ReportSection:
    """Baut die Risk-Events-Section."""
    if "risk_allowed" not in events_df.columns:
        return ReportSection(
            title="Risk Events",
            content_markdown="*No risk data available*",
        )

    # Risk-Blocks
    blocked_events = events_df[events_df["risk_allowed"] == False]  # noqa: E712

    if len(blocked_events) == 0:
        return ReportSection(
            title="Risk Events",
            content_markdown="**No risk violations during this run.**",
        )

    content_lines = [
        f"**Risk Violations:** {len(blocked_events)}",
        "",
    ]

    # Reasons sammeln (falls vorhanden)
    if "risk_reasons" in blocked_events.columns:
        all_reasons = blocked_events["risk_reasons"].dropna().unique()
        if len(all_reasons) > 0:
            content_lines.append("**Violation Reasons:**")
            for reason in all_reasons[:10]:  # Max 10 anzeigen
                if reason:
                    content_lines.append(f"- {reason}")

    return ReportSection(
        title="Risk Events",
        content_markdown="\n".join(content_lines),
    )


def _build_trade_list_section(events_df: pd.DataFrame, max_trades: int) -> ReportSection:
    """Baut die Trade-Liste-Section."""
    # Nur Events mit gefüllten Orders
    if "orders_filled" not in events_df.columns:
        return ReportSection(
            title="Trade List",
            content_markdown="*No trade data available*",
        )

    trade_events = events_df[events_df["orders_filled"] > 0].copy()

    if len(trade_events) == 0:
        return ReportSection(
            title="Trade List",
            content_markdown="*No trades were executed during this run*",
        )

    # Relevante Spalten auswählen
    display_cols = []
    col_mapping = {
        "step": "Step",
        "ts_bar": "Bar Time",
        "signal": "Signal",
        "price": "Price",
        "orders_filled": "Filled",
        "position_size": "Position",
    }

    for col, label in col_mapping.items():
        if col in trade_events.columns:
            display_cols.append(col)

    if not display_cols:
        return ReportSection(
            title="Trade List",
            content_markdown="*No displayable trade data*",
        )

    display_df = trade_events[display_cols].head(max_trades).copy()
    display_df.columns = [col_mapping.get(c, c) for c in display_cols]

    content = df_to_markdown(display_df, float_format=".4f")

    if len(trade_events) > max_trades:
        content += f"\n\n*... and {len(trade_events) - max_trades} more trades*"

    return ReportSection(
        title="Trade List",
        content_markdown=content,
    )


def _build_config_section(meta: Dict[str, Any]) -> ReportSection:
    """Baut die Config-Section."""
    config_snapshot = meta.get("config_snapshot", {})

    if not config_snapshot:
        return ReportSection(
            title="Configuration",
            content_markdown="*No configuration snapshot available*",
        )

    content_lines = []

    for section_name, section_data in config_snapshot.items():
        content_lines.append(f"**{section_name}:**")
        if isinstance(section_data, dict):
            for key, value in section_data.items():
                content_lines.append(f"- {key}: {value}")
        else:
            content_lines.append(f"- {section_data}")
        content_lines.append("")

    return ReportSection(
        title="Configuration",
        content_markdown="\n".join(content_lines),
    )


# =============================================================================
# Utility Functions
# =============================================================================


def load_and_build_report(run_dir: str | Path) -> Report:
    """
    Lädt Run-Logs aus einem Verzeichnis und erstellt Report.

    Args:
        run_dir: Pfad zum Run-Verzeichnis

    Returns:
        Report-Objekt
    """
    run_dir = Path(run_dir)
    meta_path = run_dir / "meta.json"

    # Events-Datei finden (parquet bevorzugt)
    events_path = run_dir / "events.parquet"
    if not events_path.exists():
        events_path = run_dir / "events.csv"

    return build_live_run_report(meta_path=meta_path, events_path=events_path)


def save_report(report: Report, output_path: str | Path, format: str = "markdown") -> None:
    """
    Speichert einen Report in eine Datei.

    Args:
        report: Das Report-Objekt
        output_path: Ziel-Pfad
        format: "markdown" oder "html"
    """
    output_path = Path(output_path)

    if format == "html":
        content = report.to_html()
    else:
        content = report.to_markdown()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
