"""
Health Checker

Zentrale Health-Check-Klasse für System-Überwachung.
CLI-Command: python -m src.infra.health.health_checker
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .checks import (
    BacktestHealthCheck,
    BaseHealthCheck,
    ExchangeHealthCheck,
    HealthStatus,
    LiveHealthCheck,
    PortfolioHealthCheck,
    RiskHealthCheck,
)
from .checks.base_check import HealthCheckResult


class HealthChecker:
    """Zentrale Health-Check-Verwaltung"""

    def __init__(self, checks: Optional[List[str]] = None):
        """
        Initialisiere HealthChecker.
        
        Args:
            checks: Liste der zu prüfenden Checks (None = alle)
        """
        self.checks: Dict[str, BaseHealthCheck] = {
            "backtest": BacktestHealthCheck(),
            "exchange": ExchangeHealthCheck(),
            "portfolio": PortfolioHealthCheck(),
            "risk": RiskHealthCheck(),
            "live": LiveHealthCheck(),
        }
        
        # Filtere Checks falls angegeben
        if checks:
            self.checks = {k: v for k, v in self.checks.items() if k in checks}

    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """
        Führe alle Health-Checks aus.
        
        Returns:
            Dictionary mit Check-Namen und Results
        """
        results = {}
        
        for name, check in self.checks.items():
            try:
                result = await check.check()
                results[name] = result
            except Exception as e:
                # Fallback wenn Check selbst fehlschlägt
                results[name] = HealthCheckResult(
                    name=name,
                    status=HealthStatus.RED,
                    message=f"Check failed with exception: {str(e)}",
                    timestamp=datetime.now(),
                    error=str(e),
                )
        
        return results

    def get_overall_status(self, results: Dict[str, HealthCheckResult]) -> HealthStatus:
        """
        Bestimme Gesamt-Status aus allen Results.
        
        Args:
            results: Dictionary mit Check-Results
            
        Returns:
            Gesamt-Status (RED wenn mind. 1 RED, YELLOW wenn mind. 1 YELLOW, sonst GREEN)
        """
        statuses = [r.status for r in results.values()]
        
        if HealthStatus.RED in statuses:
            return HealthStatus.RED
        elif HealthStatus.YELLOW in statuses:
            return HealthStatus.YELLOW
        else:
            return HealthStatus.GREEN

    def format_results_json(self, results: Dict[str, HealthCheckResult]) -> str:
        """
        Formatiere Results als JSON.
        
        Args:
            results: Dictionary mit Check-Results
            
        Returns:
            JSON-String
        """
        overall_status = self.get_overall_status(results)
        
        output = {
            "overall_status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "checks": {name: result.to_dict() for name, result in results.items()},
        }
        
        return json.dumps(output, indent=2)

    def format_results_cli(self, results: Dict[str, HealthCheckResult]) -> str:
        """
        Formatiere Results für CLI-Ausgabe.
        
        Args:
            results: Dictionary mit Check-Results
            
        Returns:
            Formatierter String
        """
        overall_status = self.get_overall_status(results)
        
        # Ampel-Symbole
        symbols = {
            HealthStatus.GREEN: "✓",
            HealthStatus.YELLOW: "⚠",
            HealthStatus.RED: "✗",
        }
        
        # Colors für Terminal
        colors = {
            HealthStatus.GREEN: "\033[92m",  # Green
            HealthStatus.YELLOW: "\033[93m",  # Yellow
            HealthStatus.RED: "\033[91m",  # Red
        }
        reset_color = "\033[0m"
        
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("Peak_Trade Health Check Report")
        lines.append("=" * 60)
        
        # Overall Status
        color = colors[overall_status]
        symbol = symbols[overall_status]
        lines.append(f"\nOverall Status: {color}{symbol} {overall_status.value.upper()}{reset_color}\n")
        
        # Individual Checks
        lines.append("-" * 60)
        for name, result in results.items():
            color = colors[result.status]
            symbol = symbols[result.status]
            lines.append(f"{color}{symbol} {name.upper():<12}{reset_color} {result.message}")
            
            # Details bei Fehler
            if result.status != HealthStatus.GREEN:
                if result.error:
                    lines.append(f"   Error: {result.error}")
                if result.details:
                    lines.append(f"   Details: {result.details}")
        
        lines.append("-" * 60)
        lines.append(f"Timestamp: {datetime.now().isoformat()}")
        lines.append("=" * 60 + "\n")
        
        return "\n".join(lines)


async def main():
    """CLI Entry Point"""
    # Parse arguments
    checks = None
    output_format = "cli"
    
    if len(sys.argv) > 1:
        if "--json" in sys.argv:
            output_format = "json"
            sys.argv.remove("--json")
        
        if len(sys.argv) > 1:
            checks = sys.argv[1:]
    
    # Run health checks
    checker = HealthChecker(checks=checks)
    results = await checker.run_all_checks()
    
    # Output results
    if output_format == "json":
        print(checker.format_results_json(results))
    else:
        print(checker.format_results_cli(results))
    
    # Exit code based on overall status
    overall_status = checker.get_overall_status(results)
    if overall_status == HealthStatus.RED:
        sys.exit(1)
    elif overall_status == HealthStatus.YELLOW:
        sys.exit(0)  # Warnings don't fail
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
