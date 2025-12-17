"""
Base Health Check

Basis-Klasse für alle Health-Checks mit Ampel-System (GREEN/YELLOW/RED).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class HealthStatus(str, Enum):
    """Health Status Ampel-System"""
    GREEN = "green"    # Alles OK
    YELLOW = "yellow"  # Warnung, funktioniert aber noch
    RED = "red"        # Kritischer Fehler


@dataclass
class HealthCheckResult:
    """Ergebnis eines Health-Checks"""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für JSON-Export"""
        # Convert Path objects to strings for JSON serialization
        details_clean = {}
        if self.details:
            for key, value in self.details.items():
                if isinstance(value, Path):
                    details_clean[key] = str(value)
                else:
                    details_clean[key] = value
        
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": details_clean,
            "error": self.error,
        }


class BaseHealthCheck(ABC):
    """Basis-Klasse für alle Health-Checks"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def check(self) -> HealthCheckResult:
        """
        Führe Health-Check aus.
        
        Returns:
            HealthCheckResult mit Status und Details
        """
        pass

    def _create_result(
        self,
        status: HealthStatus,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> HealthCheckResult:
        """Helper-Methode zum Erstellen von Results"""
        return HealthCheckResult(
            name=self.name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            details=details,
            error=error,
        )
