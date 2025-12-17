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
from .backtest_report import (
    build_backtest_report,
    build_backtest_summary_section,
    build_drawdown_plot,
    build_equity_plot,
    build_parameters_section,
    build_quick_backtest_report,
    build_trade_stats_section,
    save_backtest_report,
)

# Phase 30: Markdown Reporting
from .base import (
    Report,
    ReportSection,
    df_to_markdown,
    dict_to_markdown_table,
    format_metric,
)
from .execution_reports import (
    ExecutionStats,
    format_execution_stats,
    from_backtest_result,
    from_execution_logs,
    from_execution_results,
)
from .experiment_report import (
    build_best_params_section,
    build_experiment_report,
    build_experiment_summary_section,
    build_top_runs_section,
    find_best_params,
    load_experiment_results,
    save_experiment_report,
    summarize_experiment_results,
)

# Phase 21: HTML Reporting v2
from .html_reports import (
    HtmlReport,
    HtmlReportBuilder,
    ReportFigure,
    ReportTable,
    build_quick_experiment_report,
    build_quick_sweep_report,
    plot_drawdown,
    plot_equity_curve,
    plot_metric_distribution,
    plot_sweep_scatter,
)
from .html_reports import (
    ReportSection as HtmlReportSection,
)

# Phase 32: Live Run Reports
from .live_run_report import (
    build_live_run_report,
    load_and_build_report,
    save_report,
)

# Phase 81: Live Session Reports
from .live_session_report import (
    build_multi_session_report,
    build_session_report,
    save_session_report,
)

# Phase 57: Live Status Reports
from .live_status_report import (
    LiveStatusInput,
)
from .live_status_report import (
    build_html_report as build_live_status_html_report,
)
from .live_status_report import (
    build_markdown_report as build_live_status_markdown_report,
)

# Phase 45: Monte-Carlo Reports
from .monte_carlo_report import (
    build_monte_carlo_report,
)

# Offline Paper Trade Integration
from .offline_paper_trade_integration import (
    OfflinePaperTradeReportConfig,
    generate_reports_for_offline_paper_trade,
)

# Offline Paper Trade Reports
from .offline_paper_trade_report import (
    OfflinePaperTradeSessionMeta,
    build_offline_paper_trade_report,
)
from .plots import (
    save_drawdown_plot,
    save_equity_plot,
    save_equity_with_regimes,
    save_heatmap,
    save_histogram,
    save_line_plot,
    save_scatter_plot,
)

# Phase 47: Portfolio-Robustness Reports
from .portfolio_robustness_report import (
    build_portfolio_robustness_report,
)

# Psychology Heatmap
from .psychology_heatmap import (
    PsychologyHeatmapCell,
    PsychologyHeatmapRow,
    build_example_psychology_heatmap_data,
    build_psychology_heatmap_rows,
    calculate_cluster_statistics,
    extract_psychology_scores_from_events,
    serialize_psychology_heatmap_rows,
)

# Phase 46: Stress-Test Reports
from .stress_test_report import (
    build_stress_test_report,
)

# Trigger Training Reports
from .trigger_training_report import (
    TriggerOutcome,
    TriggerTrainingEvent,
    build_trigger_training_report,
    events_to_dataframe,
)

__all__ = [
    # Execution Reports (Phase 16D)
    "ExecutionStats",
    "HtmlReport",
    "HtmlReportBuilder",
    "HtmlReportSection",
    # Phase 57: Live Status Reports
    "LiveStatusInput",
    # Offline Paper Trade Integration
    "OfflinePaperTradeReportConfig",
    # Offline Paper Trade Reports
    "OfflinePaperTradeSessionMeta",
    # Psychology Heatmap
    "PsychologyHeatmapCell",
    "PsychologyHeatmapRow",
    # Phase 30: Markdown Reporting - Base
    "Report",
    # HTML Reports (Phase 21)
    "ReportFigure",
    "ReportSection",
    "ReportTable",
    # Trigger Training Reports
    "TriggerOutcome",
    "TriggerTrainingEvent",
    "build_backtest_report",
    # Phase 30: Backtest Reports
    "build_backtest_summary_section",
    "build_best_params_section",
    "build_drawdown_plot",
    "build_equity_plot",
    "build_example_psychology_heatmap_data",
    "build_experiment_report",
    "build_experiment_summary_section",
    # Phase 32: Live Run Reports
    "build_live_run_report",
    "build_live_status_html_report",
    "build_live_status_markdown_report",
    # Phase 45: Monte-Carlo Reports
    "build_monte_carlo_report",
    "build_multi_session_report",
    "build_offline_paper_trade_report",
    "build_parameters_section",
    # Phase 47: Portfolio-Robustness Reports
    "build_portfolio_robustness_report",
    "build_psychology_heatmap_rows",
    "build_quick_backtest_report",
    "build_quick_experiment_report",
    "build_quick_sweep_report",
    # Phase 81: Live Session Reports
    "build_session_report",
    # Phase 46: Stress-Test Reports
    "build_stress_test_report",
    "build_top_runs_section",
    "build_trade_stats_section",
    "build_trigger_training_report",
    "calculate_cluster_statistics",
    "df_to_markdown",
    "dict_to_markdown_table",
    "events_to_dataframe",
    "extract_psychology_scores_from_events",
    "find_best_params",
    "format_execution_stats",
    "format_metric",
    "from_backtest_result",
    "from_execution_logs",
    "from_execution_results",
    "generate_reports_for_offline_paper_trade",
    "load_and_build_report",
    "load_experiment_results",
    "plot_drawdown",
    "plot_equity_curve",
    "plot_metric_distribution",
    "plot_sweep_scatter",
    "save_backtest_report",
    "save_drawdown_plot",
    "save_equity_plot",
    "save_equity_with_regimes",
    "save_experiment_report",
    "save_heatmap",
    "save_histogram",
    # Phase 30: Plots
    "save_line_plot",
    "save_report",
    "save_scatter_plot",
    "save_session_report",
    "serialize_psychology_heatmap_rows",
    # Phase 30: Experiment Reports
    "summarize_experiment_results",
]
