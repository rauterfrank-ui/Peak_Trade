# src/reporting/__init__.py
"""
Peak_Trade Reporting Module (Phase 16D + Phase 21 + Phase 30 + Phase 32 + Phase 57 + Phase 81)
==============================================================================================

Bietet Reporting-Funktionen fuer Execution-Daten aus Backtests,
HTML-Report-Generierung und Markdown-Reports.

Module:
- execution_reports: ExecutionStats und Analyse-Funktionen (Phase 16D)
- execution_plots: Visualisierungen fuer Execution-Daten (optional)
- html_reports: HTML-Report-Generierung (Phase 21)
- base: Markdown Report-Typen und Helper (Phase 30)
- plots: Zentrale Plot-Funktionen (Phase 30)
- backtest_report: Backtest-Report-Generierung (Phase 30)
- experiment_report: Experiment/Sweep-Report-Generierung (Phase 30)
- live_run_report: Live/Shadow Run Report-Generierung (Phase 32)
- live_status_report: Live Status Report Formatter (Phase 57)
- live_session_report: Live Session Registry Reports (Phase 81)
"""

from .execution_reports import (
    ExecutionStats,
    from_execution_logs,
    from_execution_results,
    from_backtest_result,
    format_execution_stats,
)

# Phase 21: HTML Reporting v2
from .html_reports import (
    ReportFigure,
    ReportTable,
    ReportSection as HtmlReportSection,
    HtmlReport,
    HtmlReportBuilder,
    plot_equity_curve,
    plot_drawdown,
    plot_metric_distribution,
    plot_sweep_scatter,
    build_quick_experiment_report,
    build_quick_sweep_report,
)

# Phase 30: Markdown Reporting
from .base import (
    Report,
    ReportSection,
    df_to_markdown,
    dict_to_markdown_table,
    format_metric,
)

from .plots import (
    save_line_plot,
    save_equity_plot,
    save_drawdown_plot,
    save_heatmap,
    save_scatter_plot,
    save_histogram,
    save_equity_with_regimes,
)

from .backtest_report import (
    build_backtest_summary_section,
    build_trade_stats_section,
    build_parameters_section,
    build_equity_plot,
    build_drawdown_plot,
    build_backtest_report,
    save_backtest_report,
    build_quick_backtest_report,
)

from .experiment_report import (
    summarize_experiment_results,
    find_best_params,
    build_experiment_summary_section,
    build_top_runs_section,
    build_best_params_section,
    build_experiment_report,
    save_experiment_report,
    load_experiment_results,
)

# Phase 32: Live Run Reports
from .live_run_report import (
    build_live_run_report,
    load_and_build_report,
    save_report,
)

# Phase 45: Monte-Carlo Reports
from .monte_carlo_report import (
    build_monte_carlo_report,
)

# Phase 46: Stress-Test Reports
from .stress_test_report import (
    build_stress_test_report,
)

# Phase 47: Portfolio-Robustness Reports
from .portfolio_robustness_report import (
    build_portfolio_robustness_report,
)

# Phase 57: Live Status Reports
from .live_status_report import (
    LiveStatusInput,
    build_markdown_report as build_live_status_markdown_report,
    build_html_report as build_live_status_html_report,
)

# Phase 81: Live Session Reports
from .live_session_report import (
    build_session_report,
    build_multi_session_report,
    save_session_report,
)

# Offline Paper Trade Reports
from .offline_paper_trade_report import (
    OfflinePaperTradeSessionMeta,
    build_offline_paper_trade_report,
)

# Trigger Training Reports
from .trigger_training_report import (
    TriggerOutcome,
    TriggerTrainingEvent,
    events_to_dataframe,
    build_trigger_training_report,
)

# Psychology Heatmap
from .psychology_heatmap import (
    PsychologyHeatmapCell,
    PsychologyHeatmapRow,
    build_psychology_heatmap_rows,
    serialize_psychology_heatmap_rows,
    build_example_psychology_heatmap_data,
    calculate_cluster_statistics,
    extract_psychology_scores_from_events,
)

# Offline Paper Trade Integration
from .offline_paper_trade_integration import (
    OfflinePaperTradeReportConfig,
    generate_reports_for_offline_paper_trade,
)

__all__ = [
    # Execution Reports (Phase 16D)
    "ExecutionStats",
    "from_execution_logs",
    "from_execution_results",
    "from_backtest_result",
    "format_execution_stats",
    # HTML Reports (Phase 21)
    "ReportFigure",
    "ReportTable",
    "HtmlReportSection",
    "HtmlReport",
    "HtmlReportBuilder",
    "plot_equity_curve",
    "plot_drawdown",
    "plot_metric_distribution",
    "plot_sweep_scatter",
    "build_quick_experiment_report",
    "build_quick_sweep_report",
    # Phase 30: Markdown Reporting - Base
    "Report",
    "ReportSection",
    "df_to_markdown",
    "dict_to_markdown_table",
    "format_metric",
    # Phase 30: Plots
    "save_line_plot",
    "save_equity_plot",
    "save_drawdown_plot",
    "save_heatmap",
    "save_scatter_plot",
    "save_histogram",
    "save_equity_with_regimes",
    # Phase 30: Backtest Reports
    "build_backtest_summary_section",
    "build_trade_stats_section",
    "build_parameters_section",
    "build_equity_plot",
    "build_drawdown_plot",
    "build_backtest_report",
    "save_backtest_report",
    "build_quick_backtest_report",
    # Phase 30: Experiment Reports
    "summarize_experiment_results",
    "find_best_params",
    "build_experiment_summary_section",
    "build_top_runs_section",
    "build_best_params_section",
    "build_experiment_report",
    "save_experiment_report",
    "load_experiment_results",
    # Phase 32: Live Run Reports
    "build_live_run_report",
    "load_and_build_report",
    "save_report",
    # Phase 45: Monte-Carlo Reports
    "build_monte_carlo_report",
    # Phase 46: Stress-Test Reports
    "build_stress_test_report",
    # Phase 47: Portfolio-Robustness Reports
    "build_portfolio_robustness_report",
    # Phase 57: Live Status Reports
    "LiveStatusInput",
    "build_live_status_markdown_report",
    "build_live_status_html_report",
    # Phase 81: Live Session Reports
    "build_session_report",
    "build_multi_session_report",
    "save_session_report",
    # Offline Paper Trade Reports
    "OfflinePaperTradeSessionMeta",
    "build_offline_paper_trade_report",
    # Trigger Training Reports
    "TriggerOutcome",
    "TriggerTrainingEvent",
    "events_to_dataframe",
    "build_trigger_training_report",
    # Psychology Heatmap
    "PsychologyHeatmapCell",
    "PsychologyHeatmapRow",
    "build_psychology_heatmap_rows",
    "serialize_psychology_heatmap_rows",
    "build_example_psychology_heatmap_data",
    "calculate_cluster_statistics",
    "extract_psychology_scores_from_events",
    # Offline Paper Trade Integration
    "OfflinePaperTradeReportConfig",
    "generate_reports_for_offline_paper_trade",
]
