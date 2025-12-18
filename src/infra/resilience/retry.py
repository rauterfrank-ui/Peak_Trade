"""
Retry Logic with Exponential Backoff

Automatische Wiederholung fehlgeschlagener Anfragen mit exponentiell wachsenden Wartezeiten.
"""

import asyncio
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type


@dataclass
class RetryConfig:
    """Retry Konfiguration"""
    max_attempts: int = 3
    initial_delay: float = 1.0  # Sekunden
    max_delay: float = 60.0  # Max Sekunden
    exponential_base: float = 2.0
    exceptions: Tuple[Type[Exception], ...] = (Exception,)


class MaxRetriesExceededError(Exception):
    """Raised wenn alle Retry-Versuche fehlschlagen"""
    pass


async def retry_with_backoff(
    func: Callable,
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> Any:
    """
    Führe Funktion mit Retry-Logic und Exponential Backoff aus.
    
    Args:
        func: Funktion die ausgeführt werden soll
        config: Retry-Konfiguration
        *args, **kwargs: Argumente für die Funktion
        
    Returns:
        Rückgabewert der Funktion
        
    Raises:
        MaxRetriesExceededError: Wenn alle Versuche fehlschlagen
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
                
        except config.exceptions as e:
            last_exception = e
            
            if attempt < config.max_attempts - 1:
                # Berechne Delay mit Exponential Backoff
                delay = min(
                    config.initial_delay * (config.exponential_base ** attempt),
                    config.max_delay
                )
                await asyncio.sleep(delay)
            else:
                # Letzte Versuch fehlgeschlagen
                raise MaxRetriesExceededError(
                    f"Failed after {config.max_attempts} attempts"
                ) from last_exception
    
    # Sollte nicht erreicht werden, aber für Type Checker
    raise MaxRetriesExceededError(
        f"Failed after {config.max_attempts} attempts"
    ) from last_exception


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator für Retry mit Exponential Backoff.
    
    Beispiel:
        @retry(max_attempts=3, initial_delay=1.0)
        async def fetch_data():
            # API call
            pass
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        exceptions=exceptions,
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await retry_with_backoff(func, config, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, use asyncio.run
            async def async_call():
                return await retry_with_backoff(func, config, *args, **kwargs)
            return asyncio.run(async_call())
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
