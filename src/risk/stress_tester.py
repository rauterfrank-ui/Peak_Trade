"""
Portfolio Stress Tester
========================

Agent A5 Implementation: Portfolio-level stress testing with historical scenarios.

Features:
---------
- Load historical stress scenarios from JSON files
- Apply asset-level shocks to portfolio
- Reverse stress testing (find shock for target loss)
- Report generation (HTML, JSON, Markdown)

Usage:
------
>>> tester = StressTester(scenarios_dir="data/scenarios")
>>> result = tester.run_stress(
...     portfolio_weights={"BTC-EUR": 0.6, "ETH-EUR": 0.4},
...     portfolio_value=100000
... )
>>> print(result.summary())
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Epsilon for numerical stability
EPS = 1e-12


@dataclass
class StressScenarioData:
    """
    Historical stress scenario loaded from JSON.

    Attributes:
        name: Scenario name
        date: Historical date (YYYY-MM-DD)
        description: Event description
        asset_shocks: Dict of asset -> shock (negative = loss)
        default_shock: Fallback shock for missing assets
        probability: Qualitative probability (extreme, rare, moderate)
        historical_frequency: Event type classification
    """

    name: str
    date: str
    description: str
    asset_shocks: Dict[str, float]
    default_shock: float
    probability: str = "unknown"
    historical_frequency: str = "unknown"

    @classmethod
    def from_json(cls, filepath: Path) -> "StressScenarioData":
        """Load scenario from JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)

        # Extract default shock
        asset_shocks = data.get("asset_shocks", {})
        default_shock = asset_shocks.pop("default", -0.30)

        return cls(
            name=data.get("name", filepath.stem),
            date=data.get("date", "unknown"),
            description=data.get("description", ""),
            asset_shocks=asset_shocks,
            default_shock=default_shock,
            probability=data.get("probability", "unknown"),
            historical_frequency=data.get("historical_frequency", "unknown"),
        )


@dataclass
class StressTestResult:
    """
    Result of portfolio stress test.

    Attributes:
        scenario_name: Name of scenario
        portfolio_value: Original portfolio value
        stressed_value: Portfolio value after shock
        portfolio_loss_pct: Total portfolio loss percentage
        portfolio_loss_abs: Absolute portfolio loss
        asset_losses: Dict of asset -> absolute loss
        largest_contributor: Asset with largest loss contribution
        weights: Portfolio weights used
    """

    scenario_name: str
    portfolio_value: float
    stressed_value: float
    portfolio_loss_pct: float
    portfolio_loss_abs: float
    asset_losses: Dict[str, float]
    largest_contributor: str
    weights: Dict[str, float]

    def summary(self) -> Dict:
        """Return summary dictionary."""
        return {
            "scenario": self.scenario_name,
            "portfolio_value": f"${self.portfolio_value:,.2f}",
            "stressed_value": f"${self.stressed_value:,.2f}",
            "loss_pct": f"{self.portfolio_loss_pct:.2%}",
            "loss_abs": f"${self.portfolio_loss_abs:,.2f}",
            "largest_contributor": self.largest_contributor,
            "largest_loss": f"${abs(self.asset_losses[self.largest_contributor]):,.2f}",
        }


@dataclass
class ReverseStressResult:
    """
    Result of reverse stress test.

    Attributes:
        target_loss_pct: Target portfolio loss percentage
        uniform_shock: Uniform shock across all assets
        btc_shock: BTC-specific shock (others unchanged)
        probability_assessment: Qualitative probability
        comparable_scenarios: List of similar historical scenarios
    """

    target_loss_pct: float
    uniform_shock: float
    btc_shock: Optional[float]
    probability_assessment: str
    comparable_scenarios: List[str] = field(default_factory=list)

    def summary(self) -> Dict:
        """Return summary dictionary."""
        return {
            "target_loss_pct": f"{self.target_loss_pct:.2%}",
            "uniform_shock": f"{self.uniform_shock:.2%}",
            "btc_shock": f"{self.btc_shock:.2%}" if self.btc_shock else "N/A",
            "probability": self.probability_assessment,
            "comparable_scenarios": self.comparable_scenarios,
        }


class StressTester:
    """
    Portfolio Stress Tester with historical scenarios.

    Agent A5 Implementation.

    Usage:
    ------
    >>> tester = StressTester(scenarios_dir="data/scenarios")
    >>> print(f"Loaded {len(tester.scenarios)} scenarios")
    >>> result = tester.run_stress(
    ...     portfolio_weights={"BTC-EUR": 0.6, "ETH-EUR": 0.4},
    ...     portfolio_value=100000,
    ...     scenario_name="COVID-19 Crash March 2020"
    ... )
    """

    def __init__(self, scenarios_dir: str = "data/scenarios"):
        """
        Initialize StressTester.

        Args:
            scenarios_dir: Directory containing scenario JSON files
        """
        self.scenarios_dir = Path(scenarios_dir)
        self.scenarios: List[StressScenarioData] = []

        # Load scenarios
        self._load_scenarios()

        logger.info(
            f"StressTester initialized with {len(self.scenarios)} scenarios from {self.scenarios_dir}"
        )

    def _load_scenarios(self):
        """Load all scenarios from JSON files."""
        if not self.scenarios_dir.exists():
            logger.warning(f"Scenarios directory not found: {self.scenarios_dir}")
            return

        json_files = list(self.scenarios_dir.glob("*.json"))

        for filepath in json_files:
            try:
                scenario = StressScenarioData.from_json(filepath)
                self.scenarios.append(scenario)
                logger.debug(f"Loaded scenario: {scenario.name}")
            except Exception as e:
                logger.error(f"Failed to load scenario from {filepath}: {e}")

        logger.info(f"Loaded {len(self.scenarios)} scenarios")

    def run_stress(
        self,
        portfolio_weights: Dict[str, float],
        portfolio_value: float,
        scenario_name: Optional[str] = None,
    ) -> StressTestResult:
        """
        Run stress test on portfolio.

        Args:
            portfolio_weights: Dict of asset -> weight (must sum to ~1)
            portfolio_value: Total portfolio value
            scenario_name: Specific scenario to run (default: first scenario)

        Returns:
            StressTestResult with losses and contributions

        Raises:
            ValueError: If no scenarios loaded or scenario not found
        """
        if not self.scenarios:
            raise ValueError("No scenarios loaded. Check scenarios directory.")

        # Validate weights
        weights_sum = sum(portfolio_weights.values())
        if abs(weights_sum - 1.0) > 1e-3:
            logger.warning(f"Weights sum to {weights_sum:.4f}, not 1.0. Normalizing...")
            portfolio_weights = {k: v / weights_sum for k, v in portfolio_weights.items()}

        # Select scenario
        if scenario_name:
            scenario = self._get_scenario_by_name(scenario_name)
            if not scenario:
                raise ValueError(f"Scenario not found: {scenario_name}")
        else:
            scenario = self.scenarios[0]

        # Apply shocks
        asset_losses = {}
        total_loss_pct = 0.0

        for asset, weight in portfolio_weights.items():
            # Get shock for this asset (or default)
            shock = scenario.asset_shocks.get(asset, scenario.default_shock)

            # Calculate loss contribution
            # portfolio_loss_pct = sum_i (w_i * shock_i)
            loss_contribution_pct = weight * (-shock)  # shock is negative, loss is positive
            total_loss_pct += loss_contribution_pct

            # Calculate absolute loss
            asset_loss_abs = portfolio_value * weight * (-shock)
            asset_losses[asset] = asset_loss_abs

        # Calculate stressed value
        # stressed_value = portfolio_value * (1 + shock_sum)
        # Since shocks are negative, total_loss_pct is the loss
        portfolio_loss_pct = total_loss_pct
        portfolio_loss_abs = portfolio_value * portfolio_loss_pct
        stressed_value = portfolio_value - portfolio_loss_abs

        # Find largest contributor
        largest_contributor = max(asset_losses.items(), key=lambda x: abs(x[1]))[0]

        return StressTestResult(
            scenario_name=scenario.name,
            portfolio_value=portfolio_value,
            stressed_value=stressed_value,
            portfolio_loss_pct=portfolio_loss_pct,
            portfolio_loss_abs=portfolio_loss_abs,
            asset_losses=asset_losses,
            largest_contributor=largest_contributor,
            weights=portfolio_weights,
        )

    def run_all_scenarios(
        self,
        portfolio_weights: Dict[str, float],
        portfolio_value: float,
    ) -> List[StressTestResult]:
        """
        Run all stress scenarios on portfolio.

        Args:
            portfolio_weights: Dict of asset -> weight
            portfolio_value: Total portfolio value

        Returns:
            List of StressTestResult for each scenario
        """
        results = []
        for scenario in self.scenarios:
            result = self.run_stress(
                portfolio_weights, portfolio_value, scenario_name=scenario.name
            )
            results.append(result)
        return results

    def reverse_stress(
        self,
        portfolio_weights: Dict[str, float],
        target_loss_pct: float,
    ) -> ReverseStressResult:
        """
        Reverse stress test: Find shock needed for target loss.

        Args:
            portfolio_weights: Dict of asset -> weight
            target_loss_pct: Target portfolio loss (e.g., 0.20 = 20% loss)

        Returns:
            ReverseStressResult with uniform and BTC-specific shocks

        Math:
        -----
        Uniform shock: sum_i(w_i) * s = target_loss
        -> s = target_loss / sum(w_i) = target_loss (if weights sum to 1)

        BTC shock: w_btc * s_btc + sum_other(w_i * 0) = target_loss
        -> s_btc = target_loss / w_btc
        """
        # Validate weights
        weights_sum = sum(portfolio_weights.values())
        if abs(weights_sum - 1.0) > 1e-3:
            logger.warning(f"Weights sum to {weights_sum:.4f}, normalizing...")
            portfolio_weights = {k: v / weights_sum for k, v in portfolio_weights.items()}
            weights_sum = 1.0

        # Uniform shock (all assets shocked equally)
        # portfolio_loss = sum(w_i * shock_i) = sum(w_i) * shock_uniform
        # shock_uniform = target_loss / sum(w_i)
        uniform_shock = -target_loss_pct / weights_sum  # Negative shock for loss

        # BTC-specific shock (only BTC shocked, others unchanged)
        btc_assets = [k for k in portfolio_weights.keys() if "BTC" in k.upper()]
        if btc_assets:
            btc_asset = btc_assets[0]  # Use first BTC asset
            w_btc = portfolio_weights[btc_asset]

            if w_btc > EPS:
                # target_loss = w_btc * (-btc_shock) => btc_shock = -target_loss / w_btc
                btc_shock = -target_loss_pct / w_btc
            else:
                btc_shock = None
        else:
            btc_shock = None

        # Probability assessment by comparing to historical scenarios
        probability, comparable = self._assess_probability(target_loss_pct)

        return ReverseStressResult(
            target_loss_pct=target_loss_pct,
            uniform_shock=uniform_shock,
            btc_shock=btc_shock,
            probability_assessment=probability,
            comparable_scenarios=comparable,
        )

    def _get_scenario_by_name(self, name: str) -> Optional[StressScenarioData]:
        """Get scenario by name."""
        for scenario in self.scenarios:
            if scenario.name == name:
                return scenario
        return None

    def _assess_probability(self, target_loss_pct: float) -> tuple[str, List[str]]:
        """
        Assess probability of target loss based on historical scenarios.

        Args:
            target_loss_pct: Target portfolio loss

        Returns:
            Tuple of (probability_assessment, comparable_scenarios)
        """
        # Find scenarios with similar or larger losses
        comparable = []

        for scenario in self.scenarios:
            # Calculate average shock magnitude for this scenario
            avg_shock = abs(sum(scenario.asset_shocks.values()) / len(scenario.asset_shocks))

            # If target loss is within 20% of average shock
            if abs(target_loss_pct - avg_shock) < 0.20:
                comparable.append(scenario.name)

        # Probability assessment
        if target_loss_pct < 0.10:
            probability = "Common (< 10% loss)"
        elif target_loss_pct < 0.25:
            probability = "Moderate (10-25% loss)"
        elif target_loss_pct < 0.50:
            probability = "Rare (25-50% loss)"
        else:
            probability = "Extreme (> 50% loss)"

        return probability, comparable

    def generate_report(
        self,
        results: List[StressTestResult],
        format: str = "markdown",
    ) -> str:
        """
        Generate stress test report.

        Args:
            results: List of StressTestResult
            format: Report format ("markdown", "html", "json")

        Returns:
            Formatted report string
        """
        if format == "json":
            return self._generate_json_report(results)
        elif format == "html":
            return self._generate_html_report(results)
        else:  # markdown
            return self._generate_markdown_report(results)

    def _generate_markdown_report(self, results: List[StressTestResult]) -> str:
        """Generate Markdown report."""
        lines = [
            "# Portfolio Stress Test Report",
            "",
            f"**Total Scenarios:** {len(results)}",
            "",
            "## Scenario Results",
            "",
        ]

        for result in results:
            lines.append(f"### {result.scenario_name}")
            lines.append("")
            lines.append(f"- **Portfolio Value:** ${result.portfolio_value:,.2f}")
            lines.append(f"- **Stressed Value:** ${result.stressed_value:,.2f}")
            lines.append(
                f"- **Loss:** {result.portfolio_loss_pct:.2%} (${result.portfolio_loss_abs:,.2f})"
            )
            lines.append(
                f"- **Largest Contributor:** {result.largest_contributor} (${abs(result.asset_losses[result.largest_contributor]):,.2f})"
            )
            lines.append("")

        return "\n".join(lines)

    def _generate_html_report(self, results: List[StressTestResult]) -> str:
        """Generate HTML report."""
        lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Stress Test Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #4CAF50; color: white; }",
            ".loss { color: red; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Portfolio Stress Test Report</h1>",
            f"<p><strong>Total Scenarios:</strong> {len(results)}</p>",
            "<table>",
            "<tr>",
            "<th>Scenario</th>",
            "<th>Portfolio Value</th>",
            "<th>Stressed Value</th>",
            "<th>Loss %</th>",
            "<th>Loss $</th>",
            "<th>Largest Contributor</th>",
            "</tr>",
        ]

        for result in results:
            lines.append("<tr>")
            lines.append(f"<td>{result.scenario_name}</td>")
            lines.append(f"<td>${result.portfolio_value:,.2f}</td>")
            lines.append(f"<td>${result.stressed_value:,.2f}</td>")
            lines.append(f"<td class='loss'>{result.portfolio_loss_pct:.2%}</td>")
            lines.append(f"<td class='loss'>${result.portfolio_loss_abs:,.2f}</td>")
            lines.append(f"<td>{result.largest_contributor}</td>")
            lines.append("</tr>")

        lines.extend(["</table>", "</body>", "</html>"])

        return "\n".join(lines)

    def _generate_json_report(self, results: List[StressTestResult]) -> str:
        """Generate JSON report."""
        import json

        report = {
            "total_scenarios": len(results),
            "results": [result.summary() for result in results],
        }

        return json.dumps(report, indent=2)

    def __repr__(self) -> str:
        return f"<StressTester(scenarios={len(self.scenarios)})>"
