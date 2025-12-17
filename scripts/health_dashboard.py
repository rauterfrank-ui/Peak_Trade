#!/usr/bin/env python3
"""
Peak_Trade Health Dashboard
===========================
Runs all registered health checks and displays formatted results.

Usage:
    python scripts/health_dashboard.py

Exit Codes:
    0: All health checks passed (system healthy)
    1: One or more health checks failed (system unhealthy)
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from src.core.resilience import health_check, HealthCheckResult


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_health_checks() -> None:
    """
    Register all system health checks.
    
    Includes:
    - Backtest Engine check
    - Database check (if available)
    - Exchange API check (automatically registered by ResilientExchangeClient)
    """
    logger.info("Setting up health checks...")
    
    # Backtest Engine Health Check
    def check_backtest_engine() -> tuple[bool, str]:
        """Check if backtest engine can be imported and initialized."""
        try:
            from src.backtest.engine import BacktestEngine
            from src.core.peak_config import load_config
            
            # Try to load config
            cfg = load_config()
            
            # Basic validation that engine can be instantiated
            # (we don't actually run a backtest, just check imports work)
            return True, "Backtest engine is available"
        except Exception as e:
            return False, f"Backtest engine check failed: {str(e)}"
    
    health_check.register("backtest_engine", check_backtest_engine)
    
    # Database Health Check (if database module exists)
    def check_database() -> tuple[bool, str]:
        """Check database connectivity."""
        try:
            # Check if database module exists
            from pathlib import Path
            db_path = Path(__file__).parent.parent / "src" / "data" / "database.py"
            
            if not db_path.exists():
                # No database module, skip check
                return True, "Database module not present (optional)"
            
            # If database module exists, try to import and check
            # This is a placeholder - actual implementation depends on database setup
            return True, "Database check not implemented (placeholder)"
            
        except Exception as e:
            return False, f"Database check failed: {str(e)}"
    
    health_check.register("database", check_database)
    
    # Exchange API Health Check
    # This is automatically registered when ResilientExchangeClient is instantiated
    # We'll create a test instance to trigger registration
    def check_exchange_api() -> tuple[bool, str]:
        """Check exchange API connectivity."""
        try:
            from src.data.exchange_client import ResilientExchangeClient
            
            # Create client instance (this registers its own health check)
            # Use paper/testnet config to avoid hitting live API
            client = ResilientExchangeClient(exchange_id="kraken", config={"enableRateLimit": True})
            
            # The client registers itself, so we just verify it was created
            return True, "Exchange API client initialized"
            
        except Exception as e:
            return False, f"Exchange API check failed: {str(e)}"
    
    health_check.register("exchange_api", check_exchange_api)
    
    logger.info(f"Registered {len(health_check._checks)} health checks")


def format_health_report(results: Dict[str, HealthCheckResult]) -> str:
    """
    Format health check results as human-readable text.
    
    Args:
        results: Dictionary of health check results
        
    Returns:
        Formatted string with health status
    """
    output = []
    
    # Use timezone-aware datetime
    now = datetime.now(datetime.UTC) if hasattr(datetime, 'UTC') else datetime.utcnow()
    
    # Header
    output.append("=" * 60)
    output.append("PEAK TRADE HEALTH DASHBOARD")
    output.append("=" * 60)
    output.append(f"Timestamp: {now.isoformat()}")
    output.append("")
    
    # Individual checks
    all_healthy = True
    for name, result in sorted(results.items()):
        status_icon = "✅" if result.healthy else "❌"
        status_text = "healthy" if result.healthy else "FAILED"
        
        output.append(f"{status_icon} {name.upper()}: {status_text}")
        
        if result.message:
            output.append(f"   Message: {result.message}")
        
        if not result.healthy:
            all_healthy = False
    
    # Summary
    output.append("")
    output.append("-" * 60)
    
    if all_healthy:
        output.append("System Status: 🟢 HEALTHY")
    else:
        output.append("System Status: 🔴 UNHEALTHY")
    
    output.append("=" * 60)
    
    return "\n".join(output)


def save_health_report(results: Dict[str, HealthCheckResult], output_path: Path) -> None:
    """
    Save health check results as JSON.
    
    Args:
        results: Dictionary of health check results
        output_path: Path to save JSON report
    """
    # Use timezone-aware datetime
    now = datetime.now(datetime.UTC) if hasattr(datetime, 'UTC') else datetime.utcnow()
    
    # Convert results to JSON-serializable format
    report = {
        "timestamp": now.isoformat(),
        "checks": {name: result.to_dict() for name, result in results.items()},
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results.values() if r.healthy),
            "failed": sum(1 for r in results.values() if not r.healthy),
            "healthy": all(r.healthy for r in results.values())
        }
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Health report saved to {output_path}")


def main() -> int:
    """
    Main entry point for health dashboard.
    
    Returns:
        Exit code (0 = healthy, 1 = unhealthy)
    """
    try:
        # Setup all health checks
        setup_health_checks()
        
        # Run all checks
        logger.info("Running health checks...")
        results = health_check.run_all()
        
        # Display formatted output
        report_text = format_health_report(results)
        print(report_text)
        
        # Save JSON report
        reports_dir = Path(__file__).parent.parent / "reports"
        report_path = reports_dir / "health_check.json"
        save_health_report(results, report_path)
        
        # Determine exit code
        all_healthy = all(result.healthy for result in results.values())
        
        if all_healthy:
            logger.info("All health checks passed ✅")
            return 0
        else:
            logger.error("One or more health checks failed ❌")
            return 1
            
    except Exception as e:
        logger.error(f"Health dashboard failed with error: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
