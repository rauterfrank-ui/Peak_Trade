"""
Health Checker
===============

Central health checker that coordinates all component health checks.
Provides aggregated status and detailed reporting.

Usage:
    from src.infra.health import HealthChecker
    
    checker = HealthChecker()
    status = checker.check_all()
    print(status.to_json())
    
CLI:
    python -m src.infra.health.health_checker
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from src.infra.health.checks.base_check import CheckResult, HealthStatus
from src.infra.health.checks.backtest_check import BacktestHealthCheck
from src.infra.health.checks.exchange_check import ExchangeHealthCheck
from src.infra.health.checks.portfolio_check import PortfolioHealthCheck
from src.infra.health.checks.risk_check import RiskHealthCheck
from src.infra.health.checks.live_check import LiveHealthCheck


@dataclass
class ComponentStatus:
    """Status of an individual component."""
    
    name: str
    status: HealthStatus
    message: str
    details: Dict
    timestamp: datetime
    response_time_ms: float


class HealthChecker:
    """
    Central health checker for all Peak Trade components.
    
    Runs health checks on all critical systems and provides
    aggregated status using traffic light system.
    """
    
    def __init__(self):
        """Initialize health checker with all component checks."""
        self.checks = [
            BacktestHealthCheck(),
            ExchangeHealthCheck(),
            PortfolioHealthCheck(),
            RiskHealthCheck(),
            LiveHealthCheck(),
        ]
    
    def check_all(self) -> HealthCheckerResult:
        """
        Run all health checks.
        
        Returns:
            HealthCheckerResult with aggregated status
        """
        results: List[CheckResult] = []
        
        for check in self.checks:
            try:
                result = check.check()
                results.append(result)
            except Exception as e:
                # If a check itself fails, create a RED result
                from src.infra.health.checks.base_check import CheckResult, HealthStatus
                results.append(
                    CheckResult(
                        component_name=check.component_name,
                        status=HealthStatus.RED,
                        message=f"Health check failed with exception: {e}",
                        timestamp=datetime.now(),
                        details={"exception": str(e)},
                    )
                )
        
        return HealthCheckerResult(results)
    
    def check_component(self, component_name: str) -> CheckResult:
        """
        Run health check for a specific component.
        
        Args:
            component_name: Name of component to check
            
        Returns:
            CheckResult for the component
            
        Raises:
            ValueError: If component not found
        """
        for check in self.checks:
            if check.component_name == component_name:
                return check.check()
        
        raise ValueError(f"Component '{component_name}' not found")


class HealthCheckerResult:
    """
    Result of running all health checks.
    
    Provides aggregated status and detailed component results.
    """
    
    def __init__(self, results: List[CheckResult]):
        """
        Initialize result.
        
        Args:
            results: List of individual check results
        """
        self.results = results
        self.timestamp = datetime.now()
    
    @property
    def overall_status(self) -> HealthStatus:
        """
        Calculate overall status based on all component statuses.
        
        Rules:
        - Any RED -> Overall RED
        - Any YELLOW (no RED) -> Overall YELLOW
        - All GREEN -> Overall GREEN
        
        Returns:
            Overall health status
        """
        statuses = [r.status for r in self.results]
        
        if HealthStatus.RED in statuses:
            return HealthStatus.RED
        elif HealthStatus.YELLOW in statuses:
            return HealthStatus.YELLOW
        else:
            return HealthStatus.GREEN
    
    @property
    def green_count(self) -> int:
        """Number of GREEN components."""
        return sum(1 for r in self.results if r.status == HealthStatus.GREEN)
    
    @property
    def yellow_count(self) -> int:
        """Number of YELLOW components."""
        return sum(1 for r in self.results if r.status == HealthStatus.YELLOW)
    
    @property
    def red_count(self) -> int:
        """Number of RED components."""
        return sum(1 for r in self.results if r.status == HealthStatus.RED)
    
    def to_dict(self) -> Dict:
        """
        Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "overall_status": self.overall_status.value,
            "summary": {
                "total_components": len(self.results),
                "green": self.green_count,
                "yellow": self.yellow_count,
                "red": self.red_count,
            },
            "components": [r.to_dict() for r in self.results],
        }
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert to JSON string.
        
        Args:
            indent: JSON indentation level
            
        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=indent)
    
    def print_summary(self) -> None:
        """Print human-readable summary to stdout."""
        print("\n" + "=" * 70)
        print("Peak Trade Health Check Summary")
        print("=" * 70)
        print(f"Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nOverall Status: {self._format_status(self.overall_status)}")
        print(f"\nComponents: {self.green_count} GREEN / {self.yellow_count} YELLOW / {self.red_count} RED")
        print("\n" + "-" * 70)
        print("Component Details:")
        print("-" * 70)
        
        for result in self.results:
            status_str = self._format_status(result.status)
            print(f"\n[{status_str}] {result.component_name}")
            print(f"  Message: {result.message}")
            if result.response_time_ms:
                print(f"  Response Time: {result.response_time_ms:.2f}ms")
            if result.details:
                print(f"  Details: {json.dumps(result.details, indent=4)}")
        
        print("\n" + "=" * 70 + "\n")
    
    def _format_status(self, status: HealthStatus) -> str:
        """Format status with color/emoji."""
        symbols = {
            HealthStatus.GREEN: "🟢 GREEN",
            HealthStatus.YELLOW: "🟡 YELLOW",
            HealthStatus.RED: "🔴 RED",
        }
        return symbols.get(status, str(status))


def main() -> int:
    """
    CLI entry point for health checker.
    
    Returns:
        Exit code (0 for GREEN, 1 for YELLOW, 2 for RED)
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Peak Trade Health Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all health checks
  python -m src.infra.health.health_checker
  
  # Output as JSON
  python -m src.infra.health.health_checker --json
  
  # Save to file
  python -m src.infra.health.health_checker --json > health_status.json
        """,
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of human-readable format",
    )
    
    parser.add_argument(
        "--component",
        type=str,
        help="Check only specific component",
    )
    
    args = parser.parse_args()
    
    checker = HealthChecker()
    
    if args.component:
        try:
            result = checker.check_component(args.component)
            if args.json:
                print(json.dumps(result.to_dict(), indent=2))
            else:
                status_str = {
                    HealthStatus.GREEN: "🟢 GREEN",
                    HealthStatus.YELLOW: "🟡 YELLOW",
                    HealthStatus.RED: "🔴 RED",
                }[result.status]
                print(f"\n[{status_str}] {result.component_name}")
                print(f"Message: {result.message}")
                if result.details:
                    print(f"Details: {json.dumps(result.details, indent=2)}")
            
            # Return exit code based on status
            exit_codes = {
                HealthStatus.GREEN: 0,
                HealthStatus.YELLOW: 1,
                HealthStatus.RED: 2,
            }
            return exit_codes[result.status]
            
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 3
    else:
        result = checker.check_all()
        
        if args.json:
            print(result.to_json())
        else:
            result.print_summary()
        
        # Return exit code based on overall status
        exit_codes = {
            HealthStatus.GREEN: 0,
            HealthStatus.YELLOW: 1,
            HealthStatus.RED: 2,
        }
        return exit_codes[result.overall_status]


if __name__ == "__main__":
    sys.exit(main())
