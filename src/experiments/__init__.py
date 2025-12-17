# src/experiments/__init__.py
"""
Peak_Trade Experiments Package (Phase 29)
==========================================

Dieses Package implementiert einen Experiment-Layer für Parameter-Sweeps
über Strategien und Regime-Detection-Konfigurationen.

Kernkomponenten:
- ParamSweep: Definiert einen Parameter-Bereich für Sweeps
- ExperimentConfig: Konfiguration für einen Experiment-Durchlauf
- SweepResultRow: Ein einzelnes Ergebnis aus dem Sweep
- ExperimentRunner: Führt Sweeps aus und sammelt Ergebnisse

Helper-Module:
- strategy_sweeps: Vordefinierte Sweeps für Strategie-Parameter
- regime_sweeps: Vordefinierte Sweeps für Regime-Detection-Parameter

Example:
    >>> from src.experiments import ExperimentRunner, ExperimentConfig, ParamSweep
    >>>
    >>> config = ExperimentConfig(
    ...     name="MA Crossover Sweep",
    ...     strategy_name="ma_crossover",
    ...     param_sweeps=[
    ...         ParamSweep("fast_period", [5, 10, 20]),
    ...         ParamSweep("slow_period", [50, 100, 200]),
    ...     ],
    ...     symbols=["BTC/EUR"],
    ...     timeframe="1h",
    ... )
    >>>
    >>> runner = ExperimentRunner()
    >>> results = runner.run(config)
    >>> print(results.to_dataframe())
"""
from __future__ import annotations

from .armstrong_elkaroui_combi_experiment import (
    ALLOWED_ENVIRONMENTS as ARMSTRONG_ELKAROUI_ALLOWED_ENVIRONMENTS,
)

# Armstrong × El-Karoui Kombi-Experiment (R&D)
from .armstrong_elkaroui_combi_experiment import (
    RUN_TYPE_ARMSTRONG_ELKAROUI_COMBI,
    ArmstrongElKarouiCombiConfig,
    ArmstrongEventState,
    CombiExperimentResult,
    ElKarouiRegime,
    compute_armstrong_event_labels,
    compute_combo_stats,
    compute_elkaroui_regime_labels,
    compute_forward_returns,
    create_combo_state_labels,
    generate_armstrong_elkaroui_combi_report,
    run_armstrong_elkaroui_combi_experiment,
)
from .base import (
    ExperimentConfig,
    ExperimentResult,
    ExperimentRunner,
    ParamSweep,
    SweepResultRow,
)

# Live Session Registry (Phase 81)
from .live_session_registry import (
    # Constants
    DEFAULT_LIVE_SESSION_DIR,
    RUN_TYPE_LIVE_SESSION,
    RUN_TYPE_LIVE_SESSION_LIVE,
    RUN_TYPE_LIVE_SESSION_PAPER,
    RUN_TYPE_LIVE_SESSION_SHADOW,
    RUN_TYPE_LIVE_SESSION_TESTNET,
    STATUS_ABORTED,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_STARTED,
    LiveSessionRecord,
    generate_session_run_id,
    get_session_summary,
    list_session_records,
    load_session_record,
    register_live_session_run,
    render_session_html,
    # Report Renderers
    render_session_markdown,
    render_sessions_html,
    render_sessions_markdown,
)
from .regime_aware_portfolio_sweeps import (
    REGIME_AWARE_PORTFOLIO_SWEEP_REGISTRY,
    get_regime_aware_aggressive_sweeps,
    get_regime_aware_combined_sweeps,
    get_regime_aware_conservative_sweeps,
    get_regime_aware_portfolio_sweeps,
    get_regime_aware_sweep,
    get_regime_aware_volmetric_sweeps,
    list_available_regime_aware_sweeps,
)
from .regime_sweeps import (
    REGIME_SWEEP_REGISTRY,
    get_combined_regime_strategy_sweeps,
    get_range_compression_detector_sweeps,
    get_regime_detector_sweeps,
    get_strategy_switching_sweeps,
    get_volatility_detector_sweeps,
)
from .research_playground import (
    ParamConstraint,
    StrategySweepConfig,
    create_custom_sweep,
    get_all_predefined_sweeps,
    get_predefined_sweep,
    get_sweeps_by_tag,
    get_sweeps_for_strategy,
    list_predefined_sweeps,
    print_sweep_catalog,
    run_sweep_batch,
)

# Strategy Profiles (Phase 41B)
from .strategy_profiles import (
    PROFILE_VERSION,
    Metadata,
    PerformanceMetrics,
    RegimeProfile,
    RobustnessMetrics,
    SingleRegimeProfile,
    StrategyProfile,
    StrategyProfileBuilder,
    StrategyTieringInfo,
    generate_markdown_profile,
    get_tiering_for_strategy,
    load_tiering_config,
)
from .strategy_sweeps import (
    STRATEGY_SWEEP_REGISTRY,
    get_bollinger_sweeps,
    get_breakout_sweeps,
    get_donchian_sweeps,
    get_ma_crossover_sweeps,
    get_macd_sweeps,
    get_mean_reversion_sweeps,
    get_momentum_sweeps,
    get_rsi_reversion_sweeps,
    get_strategy_sweeps,
    get_trend_following_sweeps,
    get_vol_breakout_sweeps,
    get_vol_regime_filter_sweeps,
    list_available_strategies,
)

# Backward compatibility alias
DEFAULT_SESSIONS_DIR = DEFAULT_LIVE_SESSION_DIR

__all__ = [
    "ARMSTRONG_ELKAROUI_ALLOWED_ENVIRONMENTS",
    # Constants
    "DEFAULT_LIVE_SESSION_DIR",
    "DEFAULT_SESSIONS_DIR",  # Backward compatibility
    "PROFILE_VERSION",
    "REGIME_AWARE_PORTFOLIO_SWEEP_REGISTRY",
    "REGIME_SWEEP_REGISTRY",
    "RUN_TYPE_ARMSTRONG_ELKAROUI_COMBI",
    "RUN_TYPE_LIVE_SESSION",
    "RUN_TYPE_LIVE_SESSION_LIVE",
    "RUN_TYPE_LIVE_SESSION_PAPER",
    "RUN_TYPE_LIVE_SESSION_SHADOW",
    "RUN_TYPE_LIVE_SESSION_TESTNET",
    "STATUS_ABORTED",
    "STATUS_COMPLETED",
    "STATUS_FAILED",
    "STATUS_STARTED",
    "STRATEGY_SWEEP_REGISTRY",
    # Armstrong × El-Karoui Kombi-Experiment (R&D)
    "ArmstrongElKarouiCombiConfig",
    "ArmstrongEventState",
    "CombiExperimentResult",
    "ElKarouiRegime",
    "ExperimentConfig",
    "ExperimentResult",
    "ExperimentRunner",
    # Live Session Registry (Phase 81)
    "LiveSessionRecord",
    "Metadata",
    "ParamConstraint",
    # Base types
    "ParamSweep",
    "PerformanceMetrics",
    "RegimeProfile",
    "RobustnessMetrics",
    "SingleRegimeProfile",
    # Strategy Profiles (Phase 41B)
    "StrategyProfile",
    "StrategyProfileBuilder",
    # Research Playground (Phase 41)
    "StrategySweepConfig",
    "StrategyTieringInfo",
    "SweepResultRow",
    "compute_armstrong_event_labels",
    "compute_combo_stats",
    "compute_elkaroui_regime_labels",
    "compute_forward_returns",
    "create_combo_state_labels",
    "create_custom_sweep",
    "generate_armstrong_elkaroui_combi_report",
    "generate_markdown_profile",
    "generate_session_run_id",
    "get_all_predefined_sweeps",
    "get_bollinger_sweeps",
    "get_breakout_sweeps",
    "get_combined_regime_strategy_sweeps",
    "get_donchian_sweeps",
    # Strategy sweeps
    "get_ma_crossover_sweeps",
    "get_macd_sweeps",
    "get_mean_reversion_sweeps",
    "get_momentum_sweeps",
    "get_predefined_sweep",
    "get_range_compression_detector_sweeps",
    "get_regime_aware_aggressive_sweeps",
    "get_regime_aware_combined_sweeps",
    "get_regime_aware_conservative_sweeps",
    # Regime-Aware Portfolio Sweeps
    "get_regime_aware_portfolio_sweeps",
    "get_regime_aware_sweep",
    "get_regime_aware_volmetric_sweeps",
    "get_regime_detector_sweeps",
    "get_rsi_reversion_sweeps",
    "get_session_summary",
    "get_strategy_sweeps",
    "get_strategy_switching_sweeps",
    "get_sweeps_by_tag",
    "get_sweeps_for_strategy",
    "get_tiering_for_strategy",
    "get_trend_following_sweeps",
    "get_vol_breakout_sweeps",
    "get_vol_regime_filter_sweeps",
    # Regime sweeps
    "get_volatility_detector_sweeps",
    "list_available_regime_aware_sweeps",
    "list_available_strategies",
    "list_predefined_sweeps",
    "list_session_records",
    "load_session_record",
    "load_tiering_config",
    "print_sweep_catalog",
    "register_live_session_run",
    "render_session_html",
    # Report Renderers
    "render_session_markdown",
    "render_sessions_html",
    "render_sessions_markdown",
    "run_armstrong_elkaroui_combi_experiment",
    "run_sweep_batch",
]
