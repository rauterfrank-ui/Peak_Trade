# src/reporting/live_session_report.py
"""
Peak_Trade: Live Session Report (Phase 81)
==========================================

Report-Generierung für Live-Session-Runs aus der Experiment-Registry.

Dieses Modul erstellt Markdown- und JSON-Reports aus LiveSessionRecords,
die vom `live_session_registry`-Modul erzeugt werden.

Features:
- Summary-Metriken (Steps, Orders, Fill-Rate, etc.)
- Session-Konfiguration
- CLI-Argumente
- Optional: Multi-Session-Übersicht

Usage:
    >>> from src.reporting.live_session_report import build_session_report
    >>> from src.experiments.live_session_registry import load_session_record
    >>>
    >>> record = load_session_record("reports/experiments/live_sessions/run_xyz.json")
    >>> report = build_session_report(record)
    >>> print(report.to_markdown())

See also:
    - src/experiments/live_session_registry.py (LiveSessionRecord)
    - src/reporting/base.py (Report, ReportSection)
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .base import Report, ReportSection, df_to_markdown, dict_to_markdown_table

# Type hint für LiveSessionRecord (um zirkuläre Imports zu vermeiden)
try:
    from ..experiments.live_session_registry import LiveSessionRecord
except ImportError:
    LiveSessionRecord = Any  # type: ignore


# =============================================================================
# Report Builder
# =============================================================================


def build_session_report(
    record: LiveSessionRecord,
    include_config: bool = True,
    include_cli_args: bool = True,
) -> Report:
    """
    Erstellt einen Report aus einem LiveSessionRecord.

    Args:
        record: LiveSessionRecord aus der Registry
        include_config: Session-Config einschließen
        include_cli_args: CLI-Argumente einschließen

    Returns:
        Report-Objekt mit allen Sections

    Example:
        >>> record = load_session_record("path/to/record.json")
        >>> report = build_session_report(record)
        >>> print(report.to_markdown())
    """
    # Report erstellen
    report = Report(
        title=f"Live Session Report: {record.run_id}",
        metadata={
            "run_id": record.run_id,
            "run_type": record.run_type,
            "mode": record.mode,
            "strategy": record.strategy_name,
            "symbol": record.symbol,
            "timeframe": record.timeframe,
            "success": record.success,
            "timestamp": record.timestamp,
        },
    )

    # Sections hinzufügen
    report.add_section(_build_summary_section(record))
    report.add_section(_build_metrics_section(record))

    if include_config:
        report.add_section(_build_config_section(record))

    if include_cli_args:
        report.add_section(_build_cli_args_section(record))

    if record.tags:
        report.add_section(_build_tags_section(record))

    if not record.success:
        report.add_section(_build_error_section(record))

    return report


def build_multi_session_report(
    records: list[LiveSessionRecord],
    title: str = "Live Session Summary",
) -> Report:
    """
    Erstellt einen Übersichts-Report für mehrere Sessions.

    Args:
        records: Liste von LiveSessionRecords
        title: Report-Titel

    Returns:
        Report-Objekt

    Example:
        >>> records = list_session_records(limit=10)
        >>> report = build_multi_session_report(records)
        >>> print(report.to_markdown())
    """
    report = Report(
        title=title,
        metadata={
            "total_sessions": len(records),
            "successful": sum(1 for r in records if r.success),
            "failed": sum(1 for r in records if not r.success),
            "generated_at": datetime.now().isoformat(),
        },
    )

    # Overview Section
    overview_data = _aggregate_records(records)
    report.add_section(ReportSection(
        title="Overview",
        content_markdown=dict_to_markdown_table(
            overview_data,
            key_header="Metric",
            value_header="Value",
        ),
    ))

    # Session-Liste
    if records:
        import pandas as pd

        rows = []
        for r in records:
            rows.append({
                "run_id": r.run_id[:40] + "..." if len(r.run_id) > 40 else r.run_id,
                "mode": r.mode,
                "strategy": r.strategy_name,
                "symbol": r.symbol,
                "success": "✓" if r.success else "✗",
                "steps": r.metrics.get("steps", 0),
                "orders": r.metrics.get("total_orders_generated", 0),
            })

        df = pd.DataFrame(rows)
        report.add_section(ReportSection(
            title="Session List",
            content_markdown=df_to_markdown(df, max_rows=50),
        ))

    return report


# =============================================================================
# Section Builders
# =============================================================================


def _build_summary_section(record: LiveSessionRecord) -> ReportSection:
    """Baut die Summary-Section."""
    summary_data = {
        "Run ID": record.run_id,
        "Run Type": record.run_type,
        "Mode": record.mode,
        "Strategy": record.strategy_name,
        "Symbol": record.symbol,
        "Timeframe": record.timeframe,
        "Status": "✓ Success" if record.success else "✗ Failed",
        "Duration": f"{record.duration_seconds:.1f}s" if record.duration_seconds else "N/A",
        "Start Time": record.start_time or "N/A",
        "End Time": record.end_time or "N/A",
    }

    if record.notes:
        summary_data["Notes"] = record.notes

    return ReportSection(
        title="Summary",
        content_markdown=dict_to_markdown_table(
            summary_data,
            key_header="Property",
            value_header="Value",
        ),
    )


def _build_metrics_section(record: LiveSessionRecord) -> ReportSection:
    """Baut die Metrics-Section."""
    metrics = record.metrics

    if not metrics:
        return ReportSection(
            title="Session Metrics",
            content_markdown="*No metrics available*",
        )

    # Metriken formatieren
    formatted_metrics: dict[str, Any] = {}

    metric_labels = {
        "steps": "Total Steps",
        "total_orders_generated": "Orders Generated",
        "orders_executed": "Orders Executed",
        "orders_rejected": "Orders Rejected",
        "orders_blocked_risk": "Orders Blocked (Risk)",
        "fill_rate": "Fill Rate",
        "current_position": "Final Position",
        "last_signal": "Last Signal",
    }

    for key, label in metric_labels.items():
        if key in metrics:
            value = metrics[key]
            if key == "fill_rate" and isinstance(value, (int, float)):
                formatted_metrics[label] = f"{value * 100:.1f}%"
            elif key == "current_position" and isinstance(value, (int, float)):
                formatted_metrics[label] = f"{value:.6f}"
            else:
                formatted_metrics[label] = value

    # Zusätzliche Metriken die nicht im Standard-Set sind
    for key, value in metrics.items():
        if key not in metric_labels:
            formatted_metrics[key] = value

    return ReportSection(
        title="Session Metrics",
        content_markdown=dict_to_markdown_table(
            formatted_metrics,
            key_header="Metric",
            value_header="Value",
        ),
    )


def _build_config_section(record: LiveSessionRecord) -> ReportSection:
    """Baut die Config-Section."""
    config = record.config

    if not config:
        return ReportSection(
            title="Session Configuration",
            content_markdown="*No configuration available*",
        )

    # Config formatieren
    formatted_config: dict[str, Any] = {}

    config_labels = {
        "mode": "Mode",
        "strategy_key": "Strategy Key",
        "symbol": "Symbol",
        "timeframe": "Timeframe",
        "warmup_candles": "Warmup Candles",
        "position_fraction": "Position Fraction",
        "poll_interval_seconds": "Poll Interval (s)",
        "fee_rate": "Fee Rate",
        "slippage_bps": "Slippage (bps)",
        "start_balance": "Start Balance",
        "enable_risk_limits": "Risk Limits Enabled",
        "config_path": "Config Path",
    }

    for key, label in config_labels.items():
        if key in config:
            value = config[key]
            if key == "fee_rate" and isinstance(value, (int, float)):
                formatted_config[label] = f"{value * 100:.2f}%"
            elif key == "position_fraction" and isinstance(value, (int, float)):
                formatted_config[label] = f"{value * 100:.0f}%"
            else:
                formatted_config[label] = value

    return ReportSection(
        title="Session Configuration",
        content_markdown=dict_to_markdown_table(
            formatted_config,
            key_header="Parameter",
            value_header="Value",
        ),
    )


def _build_cli_args_section(record: LiveSessionRecord) -> ReportSection:
    """Baut die CLI-Arguments-Section."""
    cli_args = record.cli_args

    if not cli_args:
        return ReportSection(
            title="CLI Arguments",
            content_markdown="*No CLI arguments recorded*",
        )

    return ReportSection(
        title="CLI Arguments",
        content_markdown=dict_to_markdown_table(
            cli_args,
            key_header="Argument",
            value_header="Value",
        ),
    )


def _build_tags_section(record: LiveSessionRecord) -> ReportSection:
    """Baut die Tags-Section."""
    tags = record.tags

    if not tags:
        return ReportSection(
            title="Tags",
            content_markdown="*No tags*",
        )

    content = "**Tags:** " + ", ".join(f"`{tag}`" for tag in tags)

    return ReportSection(
        title="Tags",
        content_markdown=content,
    )


def _build_error_section(record: LiveSessionRecord) -> ReportSection:
    """Baut die Error-Section für fehlgeschlagene Sessions."""
    if record.success:
        return ReportSection(
            title="Error Details",
            content_markdown="*No errors*",
        )

    content_lines = [
        "**Status:** ❌ Session failed",
        "",
    ]

    if record.error_message:
        content_lines.append("**Error Message:**")
        content_lines.append("```")
        content_lines.append(record.error_message)
        content_lines.append("```")

    return ReportSection(
        title="Error Details",
        content_markdown="\n".join(content_lines),
    )


# =============================================================================
# Helper Functions
# =============================================================================


def _aggregate_records(records: list[LiveSessionRecord]) -> dict[str, Any]:
    """Aggregiert Metriken über mehrere Records."""
    if not records:
        return {"total_sessions": 0}

    total_steps = sum(r.metrics.get("steps", 0) for r in records)
    total_orders = sum(r.metrics.get("total_orders_generated", 0) for r in records)
    total_executed = sum(r.metrics.get("orders_executed", 0) for r in records)
    total_blocked = sum(r.metrics.get("orders_blocked_risk", 0) for r in records)
    total_duration = sum(r.duration_seconds for r in records)

    by_mode: dict[str, int] = {}
    by_strategy: dict[str, int] = {}
    by_tier: dict[str, int] = {}

    # Tier-Label-Mapping
    tier_labels = {
        "core": "Core",
        "aux": "Auxiliary",
        "legacy": "Legacy",
        "r_and_d": "R&D / Research",
        "unclassified": "Unclassified",
    }

    for r in records:
        by_mode[r.mode] = by_mode.get(r.mode, 0) + 1
        by_strategy[r.strategy_name] = by_strategy.get(r.strategy_name, 0) + 1
        # Tier aggregieren (falls verfügbar in metadata oder config)
        tier = getattr(r, "strategy_tier", None) or r.metadata.get("strategy_tier", "unclassified")
        by_tier[tier] = by_tier.get(tier, 0) + 1

    result = {
        "Total Sessions": len(records),
        "Successful": sum(1 for r in records if r.success),
        "Failed": sum(1 for r in records if not r.success),
        "Total Steps": total_steps,
        "Total Orders Generated": total_orders,
        "Total Orders Executed": total_executed,
        "Total Orders Blocked": total_blocked,
        "Total Duration": f"{total_duration:.1f}s",
        "Modes": ", ".join(f"{k}({v})" for k, v in by_mode.items()),
        "Strategies": ", ".join(f"{k}({v})" for k, v in by_strategy.items()),
    }

    # Tier-Breakdown hinzufügen (mit lesbaren Labels)
    if by_tier:
        tier_display = ", ".join(
            f"{tier_labels.get(k, k)}({v})"
            for k, v in sorted(by_tier.items())
        )
        result["By Tier"] = tier_display

        # R&D-Warnung wenn R&D-Sessions vorhanden
        if "r_and_d" in by_tier:
            result["R&D Notice"] = f"⚠️ {by_tier['r_and_d']} R&D-Sessions (nur Research)"

    return result


def save_session_report(
    report: Report,
    output_path: str | Path,
    format: str = "markdown",
) -> str:
    """
    Speichert einen Session-Report als Datei.

    Args:
        report: Report-Objekt
        output_path: Ausgabe-Pfad
        format: "markdown" oder "html"

    Returns:
        Pfad zur gespeicherten Datei
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format == "html":
        content = report.to_html()
    else:
        content = report.to_markdown()

    output_path.write_text(content, encoding="utf-8")
    return str(output_path)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "build_multi_session_report",
    "build_session_report",
    "save_session_report",
]
