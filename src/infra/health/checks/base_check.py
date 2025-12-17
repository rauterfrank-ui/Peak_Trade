"""
Base Health Check
==================

Abstract base class for all health checks in Peak Trade.
Provides common interface and utilities for implementing health checks.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class HealthStatus(str, Enum):
    """Health status levels using traffic light system."""
    
    GREEN = "GREEN"    # Everything operational
    YELLOW = "YELLOW"  # Warning condition, still functional
    RED = "RED"        # Critical issue, not operational


@dataclass
class CheckResult:
    """Result of a health check."""
    
    component_name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "component_name": self.component_name,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details or {},
            "response_time_ms": self.response_time_ms,
        }


class BaseHealthCheck(ABC):
    """
    Abstract base class for health checks.
    
    All component health checks should inherit from this class
    and implement the check() method.
    """
    
    def __init__(self, component_name: str):
        """
        Initialize health check.
        
        Args:
            component_name: Name of the component being checked
        """
        self.component_name = component_name
    
    @abstractmethod
    def check(self) -> CheckResult:
        """
        Perform the health check.
        
        Returns:
            CheckResult with status and details
        """
        pass
    
    def _create_result(
        self,
        status: HealthStatus,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[float] = None,
    ) -> CheckResult:
        """
        Helper to create a CheckResult.
        
        Args:
            status: Health status
            message: Status message
            details: Optional additional details
            response_time_ms: Optional response time
            
        Returns:
            CheckResult instance
        """
        return CheckResult(
            component_name=self.component_name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            details=details,
            response_time_ms=response_time_ms,
        )
    
    def _measure_time(self) -> float:
        """
        Get current time in milliseconds.
        
        Returns:
            Current time in ms
        """
        return time.time() * 1000
