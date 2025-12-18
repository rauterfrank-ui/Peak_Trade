"""
Circuit Breaker Pattern

Schützt vor kaskadierenden Fehlern bei externen Abhängigkeiten.
Drei Zustände: CLOSED (normal), OPEN (fehlerhaft), HALF_OPEN (test recovery).
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict, Optional


class CircuitBreakerState(str, Enum):
    """Circuit Breaker Zustände"""
    CLOSED = "closed"      # Normal, Anfragen durchlassen
    OPEN = "open"          # Fehler-Zustand, Anfragen blockieren
    HALF_OPEN = "half_open"  # Test-Zustand, limitierte Anfragen


@dataclass
class CircuitBreakerConfig:
    """Circuit Breaker Konfiguration"""
    name: str
    failure_threshold: int = 5  # Anzahl Fehler bis OPEN
    timeout_seconds: float = 60.0  # Zeit bis HALF_OPEN Versuch
    half_open_max_calls: int = 3  # Max Anfragen in HALF_OPEN
    expected_exception: type = Exception  # Welche Exceptions zählen


@dataclass
class CircuitBreakerMetrics:
    """Circuit Breaker Metriken"""
    total_calls: int = 0
    success_calls: int = 0
    failure_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: Optional[float] = None
    state_changed_at: float = field(default_factory=time.time)


class CircuitBreakerOpenError(Exception):
    """Raised wenn Circuit Breaker OPEN ist"""
    pass


class CircuitBreaker:
    """
    Circuit Breaker für externe Abhängigkeiten.
    
    Beispiel:
        cb = CircuitBreaker(name="kraken_api", failure_threshold=5)
        
        @cb.call
        async def fetch_data():
            # API call
            pass
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self._lock = Lock()
        self._failure_count = 0
        self._half_open_calls = 0

    def _should_attempt_reset(self) -> bool:
        """Prüfe ob Reset-Versuch erlaubt ist"""
        if self.state != CircuitBreakerState.OPEN:
            return False
        
        if self.metrics.last_failure_time is None:
            return False
        
        time_since_failure = time.time() - self.metrics.last_failure_time
        return time_since_failure >= self.config.timeout_seconds

    def _on_success(self):
        """Handle erfolgreiche Anfrage"""
        with self._lock:
            self.metrics.success_calls += 1
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                # Nach erfolgreicher Test-Anfrage zurück zu CLOSED
                self._transition_to_closed()
            
            self._failure_count = 0

    def _on_failure(self):
        """Handle fehlgeschlagene Anfrage"""
        with self._lock:
            self.metrics.failure_calls += 1
            self.metrics.last_failure_time = time.time()
            self._failure_count += 1
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                # Bei Fehler in HALF_OPEN direkt zurück zu OPEN
                self._transition_to_open()
            elif self._failure_count >= self.config.failure_threshold:
                self._transition_to_open()

    def _transition_to_open(self):
        """Wechsel zu OPEN State"""
        self.state = CircuitBreakerState.OPEN
        self.metrics.state_changed_at = time.time()
        self._half_open_calls = 0

    def _transition_to_half_open(self):
        """Wechsel zu HALF_OPEN State"""
        self.state = CircuitBreakerState.HALF_OPEN
        self.metrics.state_changed_at = time.time()
        self._half_open_calls = 0

    def _transition_to_closed(self):
        """Wechsel zu CLOSED State"""
        self.state = CircuitBreakerState.CLOSED
        self.metrics.state_changed_at = time.time()
        self._failure_count = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Führe Funktion mit Circuit Breaker Protection aus.
        
        Args:
            func: Funktion die ausgeführt werden soll
            *args, **kwargs: Argumente für die Funktion
            
        Returns:
            Rückgabewert der Funktion
            
        Raises:
            CircuitBreakerOpenError: Wenn Circuit Breaker OPEN ist
        """
        with self._lock:
            self.metrics.total_calls += 1
            
            # Prüfe ob Reset-Versuch möglich ist
            if self._should_attempt_reset():
                self._transition_to_half_open()
            
            # Blockiere wenn OPEN
            if self.state == CircuitBreakerState.OPEN:
                self.metrics.rejected_calls += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.config.name}' is OPEN. "
                    f"Retry after {self.config.timeout_seconds}s"
                )
            
            # Limitiere Anfragen in HALF_OPEN
            if self.state == CircuitBreakerState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self.metrics.rejected_calls += 1
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.config.name}' is HALF_OPEN. "
                        f"Max test calls reached"
                    )
                self._half_open_calls += 1
        
        # Führe Funktion aus
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self._on_success()
            return result
            
        except self.config.expected_exception as e:
            self._on_failure()
            raise

    def get_state(self) -> Dict[str, Any]:
        """Hole aktuellen State und Metriken"""
        return {
            "name": self.config.name,
            "state": self.state.value,
            "metrics": {
                "total_calls": self.metrics.total_calls,
                "success_calls": self.metrics.success_calls,
                "failure_calls": self.metrics.failure_calls,
                "rejected_calls": self.metrics.rejected_calls,
                "success_rate": (
                    self.metrics.success_calls / self.metrics.total_calls
                    if self.metrics.total_calls > 0
                    else 0.0
                ),
            },
            "failure_count": self._failure_count,
            "threshold": self.config.failure_threshold,
        }

    def reset(self):
        """Manueller Reset zu CLOSED State"""
        with self._lock:
            self._transition_to_closed()


# Global registry für Circuit Breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """
    Hole oder erstelle Circuit Breaker.
    
    Args:
        name: Name des Circuit Breakers
        config: Optionale Konfiguration (nur bei Erstellung)
        
    Returns:
        CircuitBreaker Instance
    """
    if name not in _circuit_breakers:
        if config is None:
            config = CircuitBreakerConfig(name=name)
        _circuit_breakers[name] = CircuitBreaker(config)
    
    return _circuit_breakers[name]


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout_seconds: float = 60.0,
    half_open_max_calls: int = 3,
):
    """
    Decorator für Circuit Breaker Protection.
    
    Beispiel:
        @circuit_breaker(name="kraken_api", failure_threshold=5)
        async def fetch_kraken_data():
            # API call
            pass
    """
    config = CircuitBreakerConfig(
        name=name,
        failure_threshold=failure_threshold,
        timeout_seconds=timeout_seconds,
        half_open_max_calls=half_open_max_calls,
    )
    cb = get_circuit_breaker(name, config)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await cb.call(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, use asyncio.run
            async def async_call():
                return await cb.call(func, *args, **kwargs)
            return asyncio.run(async_call())
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
