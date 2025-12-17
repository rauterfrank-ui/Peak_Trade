"""
Health Check System for Peak Trade
====================================

Provides centralized health monitoring for all critical components.
Uses a traffic light system (GREEN/YELLOW/RED) for status indication.

Usage:
    from src.infra.health import HealthChecker, HealthStatus
    
    checker = HealthChecker()
    status = checker.check_all()
    print(status.overall_status)  # GREEN, YELLOW, or RED

CLI:
    python -m src.infra.health.health_checker
"""

from src.infra.health.health_checker import (
    HealthChecker,
    HealthStatus,
    ComponentStatus,
)

__all__ = [
    "HealthChecker",
    "HealthStatus",
    "ComponentStatus",
]
