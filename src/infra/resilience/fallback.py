"""
Fallback Strategies

Fallback-Werte oder -Funktionen bei Fehlern.
"""

import asyncio
from functools import wraps
from typing import Any, Callable, Optional


class Fallback:
    """
    Fallback-Strategie für fehlerhafte Funktionen.
    
    Beispiel:
        fb = Fallback(default_value={"status": "unavailable"})
        result = await fb.call(fetch_data)
    """

    def __init__(
        self,
        default_value: Any = None,
        fallback_func: Optional[Callable] = None,
    ):
        """
        Initialisiere Fallback.
        
        Args:
            default_value: Default-Wert bei Fehler
            fallback_func: Alternative Funktion bei Fehler
        """
        self.default_value = default_value
        self.fallback_func = fallback_func

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Führe Funktion mit Fallback aus.
        
        Args:
            func: Haupt-Funktion
            *args, **kwargs: Argumente für die Funktion
            
        Returns:
            Rückgabewert der Funktion oder Fallback
        """
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception:
            # Bei Fehler: Fallback verwenden
            if self.fallback_func is not None:
                if asyncio.iscoroutinefunction(self.fallback_func):
                    return await self.fallback_func(*args, **kwargs)
                else:
                    return self.fallback_func(*args, **kwargs)
            else:
                return self.default_value


def fallback(
    default_value: Any = None,
    fallback_func: Optional[Callable] = None,
):
    """
    Decorator für Fallback-Strategie.
    
    Beispiel:
        @fallback(default_value={"status": "unavailable"})
        async def fetch_data():
            # API call
            pass
    """
    fb = Fallback(default_value=default_value, fallback_func=fallback_func)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await fb.call(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, use asyncio.run
            async def async_call():
                return await fb.call(func, *args, **kwargs)
            return asyncio.run(async_call())
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
