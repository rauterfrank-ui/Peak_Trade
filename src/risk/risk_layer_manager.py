"""
Risk Layer Manager v1.0
========================

Agent A6 Implementation: Central orchestration of all Risk Layer v1.0 components.

Integrates:
- VaR/CVaR (Historical, Parametric, Cornish-Fisher, EWMA)
- Component VaR (Marginal, Incremental, Diversification)
- VaR Backtesting (Kupiec POF, Christoffersen, Basel Traffic Light)
- Monte Carlo VaR (Bootstrap, Normal, Student-t)
- Stress Testing (Historical Scenarios + Reverse Stress)

Usage:
------
>>> from src.risk import RiskLayerManager
>>> from src.core.peak_config import load_config
>>>
>>> config = load_config()
>>> manager = RiskLayerManager(config)
>>>
>>> assessment = manager.full_risk_assessment(
...     returns_df=returns,
...     weights={"BTC-EUR": 0.6, "ETH-EUR": 0.4},
...     portfolio_value=100000
... )
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class RiskAssessmentResult:
    """
    Complete risk assessment result.

    Attributes:
        var: Value at Risk (dict of method -> value)
        cvar: Conditional VaR (dict of method -> value)
        component_var: Component VaR results (if enabled)
        monte_carlo: Monte Carlo VaR results (if enabled)
        stress_test: Stress test results (if enabled)
        backtest: VaR backtest results (if enabled)
        warnings: List of warning messages
        enabled_features: List of enabled features
    """

    var: Dict[str, float] = field(default_factory=dict)
    cvar: Dict[str, float] = field(default_factory=dict)
    component_var: Optional[Any] = None
    monte_carlo: Optional[Any] = None
    stress_test: Optional[List[Any]] = None
    backtest: Optional[Any] = None
    warnings: List[str] = field(default_factory=list)
    enabled_features: List[str] = field(default_factory=list)

    def summary(self) -> Dict:
        """Return summary dictionary."""
        return {
            "var": self.var,
            "cvar": self.cvar,
            "enabled_features": self.enabled_features,
            "warnings": self.warnings,
            "has_component_var": self.component_var is not None,
            "has_monte_carlo": self.monte_carlo is not None,
            "has_stress_test": self.stress_test is not None,
            "has_backtest": self.backtest is not None,
        }


class RiskLayerManager:
    """
    Central Risk Layer Manager v1.0.

    Orchestrates all risk components based on config.

    Agent A6 Implementation: Config-driven, graceful degradation.

    Config Example (config.toml):
    ------------------------------
    [risk_layer_v1]
    enabled = true

    [risk_layer_v1.var]
    enabled = true
    methods = ["historical", "parametric", "ewma"]
    confidence_level = 0.95
    window = 252

    [risk_layer_v1.component_var]
    enabled = true

    [risk_layer_v1.monte_carlo]
    enabled = true
    n_simulations = 10000
    method = "normal"
    seed = 42

    [risk_layer_v1.stress_test]
    enabled = true
    scenarios_dir = "data/scenarios"

    [risk_layer_v1.backtest]
    enabled = false  # Requires historical data
    """

    def __init__(self, config: Any):
        """
        Initialize Risk Layer Manager.

        Args:
            config: Config object (PeakConfig or dict)
        """
        # Store config as instance variable
        self._config = config

        # Initialize component placeholders
        self.component_var_calculator = None
        self.monte_carlo_calculator_class = None
        self.monte_carlo_config_class = None
        self.monte_carlo_method_enum = None
        self.stress_tester = None
        self.var_functions = {}
        self.cvar_functions = {}

        # Central portfolio VaR components (shared across features)
        self._cov_estimator = None
        self._parametric_var_engine = None

        self._parse_config()
        self._set_feature_flags()
        self._initialize_components()

        logger.info(
            f"RiskLayerManager initialized with features: {self.enabled_features}"
        )

    def _parse_config(self):
        """Parse config and set flags."""
        # Config accessor (check dict first, then PeakConfig)
        if isinstance(self._config, dict):
            # Create method that accesses self._config
            self.get_fn = self._get_from_dict
        elif hasattr(self._config, "get"):
            self.get_fn = self._config.get
        else:
            raise TypeError(f"Unsupported config type: {type(self._config)}")

    def _get_from_dict(self, path: str, default=None):
        """Get value from config dict by dot-separated path."""
        keys = path.split(".")
        node = self._config
        for key in keys:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                return default
        return node

    def _set_feature_flags(self):
        """Set feature flags based on config."""
        # Check if Risk Layer v1.0 is enabled
        enabled_value = self.get_fn("risk_layer_v1.enabled", False)
        self.enabled = bool(enabled_value)

        # Feature flags
        self.var_enabled = bool(self.get_fn("risk_layer_v1.var.enabled", True)) if self.enabled else False
        self.component_var_enabled = bool(
            self.get_fn("risk_layer_v1.component_var.enabled", False)
        ) if self.enabled else False
        self.monte_carlo_enabled = bool(
            self.get_fn("risk_layer_v1.monte_carlo.enabled", False)
        ) if self.enabled else False
        self.stress_test_enabled = bool(
            self.get_fn("risk_layer_v1.stress_test.enabled", False)
        ) if self.enabled else False
        self.backtest_enabled = bool(
            self.get_fn("risk_layer_v1.backtest.enabled", False)
        ) if self.enabled else False

        # Collect enabled features
        self.enabled_features = []
        if self.enabled:
            if self.var_enabled:
                self.enabled_features.append("var")
            if self.component_var_enabled:
                self.enabled_features.append("component_var")
            if self.monte_carlo_enabled:
                self.enabled_features.append("monte_carlo")
            if self.stress_test_enabled:
                self.enabled_features.append("stress_test")
            if self.backtest_enabled:
                self.enabled_features.append("backtest")

    def _get_or_create_cov_estimator(self):
        """Get or create the central covariance estimator (lazy init, DRY)."""
        if self._cov_estimator is None:
            from src.risk.covariance import CovarianceEstimator, CovarianceEstimatorConfig, CovarianceMethod

            cov_method_str = self._get_from_dict("risk_layer_v1.component_var.covariance_method", "sample")
            cov_config = CovarianceEstimatorConfig(
                method=CovarianceMethod(cov_method_str),
                min_history=self._get_from_dict("risk_layer_v1.component_var.min_history", 60)
            )
            self._cov_estimator = CovarianceEstimator(cov_config)
            logger.debug("Central CovarianceEstimator created")
        return self._cov_estimator

    def _get_or_create_parametric_var_engine(self):
        """Get or create the central parametric VaR engine (lazy init, DRY)."""
        if self._parametric_var_engine is None:
            from src.risk.parametric_var import ParametricVaR, ParametricVaRConfig

            var_config = ParametricVaRConfig(
                confidence_level=self._get_from_dict("risk_layer_v1.var.confidence_level", 0.95),
                horizon_days=self._get_from_dict("risk_layer_v1.var.horizon_days", 1)
            )
            self._parametric_var_engine = ParametricVaR(var_config)
            logger.debug("Central ParametricVaR engine created")
        return self._parametric_var_engine

    def _initialize_components(self):
        """Initialize enabled components."""
        # Only initialize if Risk Layer is enabled
        if not self.enabled:
            return

        # We'll rebuild enabled_features after initialization
        self.enabled_features = []

        # Import conditionally to avoid circular imports
        from src.risk.var import (
            historical_var,
            historical_cvar,
            parametric_var,
            parametric_cvar,
            ewma_var,
            ewma_cvar,
        )

        self.var_functions = {
            "historical": historical_var,
            "parametric": parametric_var,
            "ewma": ewma_var,
        }

        self.cvar_functions = {
            "historical": historical_cvar,
            "parametric": parametric_cvar,
            "ewma": ewma_cvar,
        }

        # Component VaR
        if self.component_var_enabled:
            try:
                from src.risk import ComponentVaRCalculator

                # Reuse central covariance estimator and parametric VaR engine (DRY)
                cov_estimator = self._get_or_create_cov_estimator()
                var_engine = self._get_or_create_parametric_var_engine()

                # Create ComponentVaRCalculator with shared instances
                self.component_var_calculator = ComponentVaRCalculator(cov_estimator, var_engine)
                logger.debug("Component VaR initialized (reusing central cov + var engine)")
            except Exception as e:
                logger.warning(f"Component VaR initialization failed: {e}")
                self.component_var_calculator = None
                self.component_var_enabled = False

        # Monte Carlo VaR
        if self.monte_carlo_enabled:
            try:
                from src.risk import MonteCarloVaRCalculator, MonteCarloVaRConfig, MonteCarloMethod

                # Store classes for later instantiation (needs returns data)
                self.monte_carlo_calculator_class = MonteCarloVaRCalculator
                self.monte_carlo_config_class = MonteCarloVaRConfig
                self.monte_carlo_method_enum = MonteCarloMethod
                logger.debug("Monte Carlo VaR initialized")
            except ImportError as e:
                logger.warning(f"Monte Carlo VaR import failed: {e}")
                self.monte_carlo_calculator_class = None
                self.monte_carlo_enabled = False

        # Stress Tester
        if self.stress_test_enabled:
            try:
                from src.risk import StressTester

                scenarios_dir = str(
                    self.get_fn("risk_layer_v1.stress_test.scenarios_dir", "data/scenarios")
                )
                self.stress_tester = StressTester(scenarios_dir=scenarios_dir)

                # Check if scenarios loaded successfully
                if not self.stress_tester.scenarios:
                    logger.warning(f"No scenarios loaded from {scenarios_dir}, disabling stress testing")
                    self.stress_tester = None
                    self.stress_test_enabled = False
                else:
                    logger.debug(f"Stress Tester initialized with {len(self.stress_tester.scenarios)} scenarios")
            except Exception as e:
                logger.warning(f"Stress Tester initialization failed: {e}")
                self.stress_tester = None
                self.stress_test_enabled = False

        # VaR Backtester
        if self.backtest_enabled:
            try:
                from src.risk_layer.var_backtest import VaRBacktestRunner

                self.backtest_runner = VaRBacktestRunner
                logger.debug("VaR Backtester initialized")
            except ImportError as e:
                logger.warning(f"VaR Backtester import failed: {e}")
                self.backtest_enabled = False

        # Rebuild enabled_features based on actual initialization
        if self.var_enabled and self.var_functions:
            self.enabled_features.append("var")
        if self.component_var_enabled and self.component_var_calculator:
            self.enabled_features.append("component_var")
        if self.monte_carlo_enabled and self.monte_carlo_calculator_class:
            self.enabled_features.append("monte_carlo")
        if self.stress_test_enabled and self.stress_tester:
            self.enabled_features.append("stress_test")
        if self.backtest_enabled:
            self.enabled_features.append("backtest")

    def full_risk_assessment(
        self,
        returns_df: pd.DataFrame,
        weights: Dict[str, float],
        portfolio_value: float,
        alpha: float = 0.05,
    ) -> RiskAssessmentResult:
        """
        Perform full risk assessment.

        Args:
            returns_df: Historical returns DataFrame (assets as columns)
            weights: Portfolio weights (must sum to ~1)
            portfolio_value: Total portfolio value
            alpha: VaR significance level (default: 0.05 = 95% VaR)

        Returns:
            RiskAssessmentResult with all enabled components

        Example:
            >>> assessment = manager.full_risk_assessment(
            ...     returns_df=returns,
            ...     weights={"BTC-EUR": 0.6, "ETH-EUR": 0.4},
            ...     portfolio_value=100000
            ... )
            >>> print(f"VaR (historical): ${assessment.var['historical']:,.2f}")
        """
        if not self.enabled:
            logger.info("Risk Layer v1.0 disabled in config")
            return RiskAssessmentResult(
                warnings=["Risk Layer v1.0 disabled in config"],
                enabled_features=[]
            )

        result = RiskAssessmentResult(enabled_features=self.enabled_features)

        # Calculate portfolio returns
        weights_series = pd.Series(weights)
        portfolio_returns = returns_df @ weights_series

        # 1. VaR/CVaR
        if self.var_enabled:
            methods = self.get_fn("risk_layer_v1.var.methods", ["historical", "parametric"])
            for method in methods:
                if method in self.var_functions:
                    try:
                        var_pct = self.var_functions[method](portfolio_returns, alpha=alpha)
                        cvar_pct = self.cvar_functions[method](portfolio_returns, alpha=alpha)

                        result.var[method] = var_pct * portfolio_value
                        result.cvar[method] = cvar_pct * portfolio_value
                    except Exception as e:
                        logger.error(f"VaR calculation failed for method {method}: {e}")
                        result.warnings.append(f"VaR ({method}) failed: {e}")

        # 2. Component VaR
        if self.component_var_enabled and self.component_var_calculator:
            try:
                result.component_var = self.component_var_calculator.calculate(
                    returns_df=returns_df,
                    weights=weights,
                    portfolio_value=portfolio_value,
                )
            except Exception as e:
                logger.error(f"Component VaR calculation failed: {e}")
                result.warnings.append(f"Component VaR failed: {e}")

        # 3. Monte Carlo VaR
        if self.monte_carlo_enabled and self.monte_carlo_calculator_class:
            try:
                # Parse method enum
                method_str = str(self.get_fn("risk_layer_v1.monte_carlo.method", "normal"))
                mc_method = self.monte_carlo_method_enum(method_str)

                mc_config = self.monte_carlo_config_class(
                    n_simulations=int(
                        self.get_fn("risk_layer_v1.monte_carlo.n_simulations", 10000)
                    ),
                    method=mc_method,
                    seed=int(self.get_fn("risk_layer_v1.monte_carlo.seed", 42)),
                    confidence_level=float(
                        self.get_fn("risk_layer_v1.monte_carlo.confidence_level", 0.95)
                    ),
                    horizon_days=int(
                        self.get_fn("risk_layer_v1.monte_carlo.horizon_days", 1)
                    ),
                )
                mc_calc = self.monte_carlo_calculator_class(returns_df, mc_config)
                result.monte_carlo = mc_calc.calculate(weights=weights, portfolio_value=portfolio_value)
            except Exception as e:
                logger.error(f"Monte Carlo VaR calculation failed: {e}")
                result.warnings.append(f"Monte Carlo VaR failed: {e}")

        # 4. Stress Testing
        if self.stress_test_enabled and self.stress_tester:
            try:
                result.stress_test = self.stress_tester.run_all_scenarios(
                    portfolio_weights=weights,
                    portfolio_value=portfolio_value
                )
            except Exception as e:
                logger.error(f"Stress testing failed: {e}")
                result.warnings.append(f"Stress testing failed: {e}")

        # 5. VaR Backtesting (requires historical violation data, skip for now)
        if self.backtest_enabled:
            result.warnings.append("VaR Backtesting requires historical violation data (not implemented in full_risk_assessment)")

        return result

    def generate_report(
        self,
        assessment: RiskAssessmentResult,
        format: str = "markdown",
    ) -> str:
        """
        Generate risk assessment report.

        Args:
            assessment: RiskAssessmentResult from full_risk_assessment()
            format: Report format ("markdown", "html", "json")

        Returns:
            Formatted report string
        """
        if format == "json":
            import json

            return json.dumps(assessment.summary(), indent=2)
        elif format == "html":
            return self._generate_html_report(assessment)
        else:  # markdown
            return self._generate_markdown_report(assessment)

    def _generate_markdown_report(self, assessment: RiskAssessmentResult) -> str:
        """Generate Markdown report."""
        lines = [
            "# Risk Assessment Report",
            "",
            f"**Enabled Features:** {', '.join(assessment.enabled_features)}",
            "",
        ]

        # VaR/CVaR
        if assessment.var:
            lines.append("## Value at Risk (VaR)")
            lines.append("")
            for method, value in assessment.var.items():
                cvar = assessment.cvar.get(method, 0)
                lines.append(f"- **{method.capitalize()}:** VaR = ${value:,.2f}, CVaR = ${cvar:,.2f}")
            lines.append("")

        # Component VaR
        if assessment.component_var:
            lines.append("## Component VaR")
            lines.append("")
            lines.append(f"- Total VaR: ${assessment.component_var.total_var:,.2f}")
            component_sum = assessment.component_var.component_var.sum()
            lines.append(f"- Sum of Component VaRs: ${component_sum:,.2f}")
            lines.append("")

        # Monte Carlo VaR
        if assessment.monte_carlo:
            lines.append("## Monte Carlo VaR")
            lines.append("")
            lines.append(f"- VaR: ${assessment.monte_carlo.var:,.2f}")
            lines.append(f"- CVaR: ${assessment.monte_carlo.cvar:,.2f}")
            lines.append(f"- Method: {assessment.monte_carlo.simulation_metadata.get('method', 'unknown')}")
            lines.append("")

        # Stress Testing
        if assessment.stress_test:
            lines.append("## Stress Test Results")
            lines.append("")
            for result in assessment.stress_test:
                lines.append(f"### {result.scenario_name}")
                lines.append(f"- Loss: {result.portfolio_loss_pct:.2%} (${result.portfolio_loss_abs:,.2f})")
                lines.append(f"- Largest Contributor: {result.largest_contributor}")
                lines.append("")

        # Warnings
        if assessment.warnings:
            lines.append("## Warnings")
            lines.append("")
            for warning in assessment.warnings:
                lines.append(f"- {warning}")
            lines.append("")

        return "\n".join(lines)

    def _generate_html_report(self, assessment: RiskAssessmentResult) -> str:
        """Generate HTML report."""
        # Simplified HTML report
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Risk Assessment Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .feature {{ background: #f0f0f0; padding: 10px; margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>Risk Assessment Report</h1>
    <p><strong>Enabled Features:</strong> {', '.join(assessment.enabled_features)}</p>
    <div class="feature">
        <h2>Summary</h2>
        <p>VaR Methods: {len(assessment.var)}</p>
        <p>Component VaR: {'Yes' if assessment.component_var else 'No'}</p>
        <p>Monte Carlo: {'Yes' if assessment.monte_carlo else 'No'}</p>
        <p>Stress Tests: {len(assessment.stress_test) if assessment.stress_test else 0}</p>
    </div>
</body>
</html>
"""

    def __repr__(self) -> str:
        return f"<RiskLayerManager(enabled={self.enabled}, features={self.enabled_features})>"


def build_risk_layer_manager_from_config(config: Any) -> Optional[RiskLayerManager]:
    """
    Factory function to build RiskLayerManager from config.

    Args:
        config: Config object (PeakConfig or dict)

    Returns:
        RiskLayerManager if enabled, else None

    Example Config (config.toml):
    ------------------------------
    [risk_layer_v1]
    enabled = true

    [risk_layer_v1.var]
    enabled = true
    methods = ["historical", "parametric", "ewma"]

    [risk_layer_v1.component_var]
    enabled = true

    [risk_layer_v1.monte_carlo]
    enabled = true
    n_simulations = 10000
    method = "normal"

    [risk_layer_v1.stress_test]
    enabled = true
    scenarios_dir = "data/scenarios"
    """
    # Check if enabled
    if hasattr(config, "get"):
        get_fn = config.get
    elif isinstance(config, dict):

        def get_fn(path, default=None):
            keys = path.split(".")
            node = config
            for key in keys:
                if isinstance(node, dict) and key in node:
                    node = node[key]
                else:
                    return default
            return node

    else:
        raise TypeError(f"Unsupported config type: {type(config)}")

    enabled = bool(get_fn("risk_layer_v1.enabled", False))
    if not enabled:
        logger.info("Risk Layer v1.0 disabled in config")
        return None

    return RiskLayerManager(config)
