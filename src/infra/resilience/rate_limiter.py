"""
Rate Limiter

Token-Bucket-Algorithmus für API Rate-Limiting.
Schützt vor Überlastung externer APIs.
"""

import asyncio
import time
from dataclasses import dataclass
from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict, Optional


@dataclass
class RateLimiterConfig:
    """Rate Limiter Konfiguration"""
    name: str
    requests_per_second: float
    burst_size: Optional[int] = None  # Max Burst, default = requests_per_second


class RateLimiter:
    """
    Token-Bucket Rate Limiter für API-Schutz.
    
    Beispiel:
        limiter = RateLimiter(name="kraken", requests_per_second=10)
        
        @limiter.limit
        async def fetch_data():
            # API call
            pass
    """

    def __init__(self, config: RateLimiterConfig):
        self.config = config
        self.burst_size = config.burst_size or int(config.requests_per_second)
        
        # Token Bucket
        self._tokens = float(self.burst_size)
        self._last_update = time.time()
        self._lock = Lock()
        
        # Metriken
        self.total_requests = 0
        self.throttled_requests = 0

    def _refill_tokens(self):
        """Fülle Token-Bucket auf"""
        now = time.time()
        elapsed = now - self._last_update
        
        # Tokens basierend auf verstrichener Zeit auffüllen
        new_tokens = elapsed * self.config.requests_per_second
        self._tokens = min(self.burst_size, self._tokens + new_tokens)
        self._last_update = now

    async def acquire(self, tokens: float = 1.0) -> bool:
        """
        Versuche Tokens zu erwerben.
        
        Args:
            tokens: Anzahl benötigter Tokens
            
        Returns:
            True wenn erfolgreich, False wenn nicht genug Tokens
        """
        with self._lock:
            self._refill_tokens()
            self.total_requests += 1
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            else:
                self.throttled_requests += 1
                return False

    async def wait_for_token(self, tokens: float = 1.0):
        """
        Warte bis Tokens verfügbar sind.
        
        Args:
            tokens: Anzahl benötigter Tokens
        """
        while True:
            if await self.acquire(tokens):
                return
            
            # Berechne Wartezeit
            with self._lock:
                tokens_needed = tokens - self._tokens
                wait_time = tokens_needed / self.config.requests_per_second
            
            await asyncio.sleep(min(wait_time, 1.0))

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Führe Funktion mit Rate-Limiting aus.
        
        Args:
            func: Funktion die ausgeführt werden soll
            *args, **kwargs: Argumente für die Funktion
            
        Returns:
            Rückgabewert der Funktion
        """
        await self.wait_for_token()
        
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    def get_stats(self) -> Dict[str, Any]:
        """Hole Rate-Limiter Statistiken"""
        with self._lock:
            self._refill_tokens()
            return {
                "name": self.config.name,
                "requests_per_second": self.config.requests_per_second,
                "burst_size": self.burst_size,
                "available_tokens": self._tokens,
                "total_requests": self.total_requests,
                "throttled_requests": self.throttled_requests,
                "throttle_rate": (
                    self.throttled_requests / self.total_requests
                    if self.total_requests > 0
                    else 0.0
                ),
            }


# Global registry für Rate Limiters
_rate_limiters: Dict[str, RateLimiter] = {}


def get_rate_limiter(name: str, config: Optional[RateLimiterConfig] = None) -> RateLimiter:
    """
    Hole oder erstelle Rate Limiter.
    
    Args:
        name: Name des Rate Limiters
        config: Optionale Konfiguration (nur bei Erstellung)
        
    Returns:
        RateLimiter Instance
    """
    if name not in _rate_limiters:
        if config is None:
            config = RateLimiterConfig(name=name, requests_per_second=5.0)
        _rate_limiters[name] = RateLimiter(config)
    
    return _rate_limiters[name]


def rate_limit(
    name: str,
    requests_per_second: float,
    burst_size: Optional[int] = None,
):
    """
    Decorator für Rate-Limiting.
    
    Beispiel:
        @rate_limit(name="kraken_api", requests_per_second=10)
        async def fetch_kraken_data():
            # API call
            pass
    """
    config = RateLimiterConfig(
        name=name,
        requests_per_second=requests_per_second,
        burst_size=burst_size,
    )
    limiter = get_rate_limiter(name, config)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await limiter.call(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, use asyncio.run
            async def async_call():
                return await limiter.call(func, *args, **kwargs)
            return asyncio.run(async_call())
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
