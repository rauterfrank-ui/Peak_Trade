"""
Performance Metrics

Sammelt und aggregiert Performance-Metriken (Latency, Throughput, Error-Rate).
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, List, Optional


@dataclass
class MetricStats:
    """Statistiken für eine Metrik"""
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = float('-inf')
    values: List[float] = field(default_factory=list)
    
    def add(self, value: float):
        """Füge Wert hinzu"""
        self.count += 1
        self.sum += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)
        self.values.append(value)
        
        # Behalte nur letzte 1000 Werte für Percentiles
        if len(self.values) > 1000:
            self.values = self.values[-1000:]
    
    def get_stats(self) -> Dict[str, float]:
        """Berechne Statistiken"""
        if self.count == 0:
            return {
                "count": 0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
            }
        
        stats = {
            "count": self.count,
            "sum": self.sum,
            "mean": self.sum / self.count,
            "min": self.min,
            "max": self.max,
        }
        
        # Percentiles
        if self.values:
            sorted_values = sorted(self.values)
            n = len(sorted_values)
            stats["p50"] = sorted_values[int(n * 0.5)]
            stats["p95"] = sorted_values[int(n * 0.95)]
            stats["p99"] = sorted_values[int(n * 0.99)]
        
        return stats


class MetricsCollector:
    """
    Performance Metriken Collector.
    
    Beispiel:
        collector = MetricsCollector()
        
        # Latency messen
        with collector.timer("api_call"):
            result = api_call()
        
        # Counter
        collector.increment("requests")
        
        # Gauge
        collector.set_gauge("queue_size", 42)
    """

    def __init__(self):
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._timers: Dict[str, MetricStats] = defaultdict(MetricStats)
        self._lock = Lock()

    def increment(self, name: str, value: int = 1):
        """Erhöhe Counter"""
        with self._lock:
            self._counters[name] += value

    def decrement(self, name: str, value: int = 1):
        """Verringere Counter"""
        with self._lock:
            self._counters[name] -= value

    def set_gauge(self, name: str, value: float):
        """Setze Gauge-Wert"""
        with self._lock:
            self._gauges[name] = value

    def record_time(self, name: str, duration: float):
        """Zeichne Zeitdauer auf"""
        with self._lock:
            self._timers[name].add(duration)

    def timer(self, name: str):
        """Context Manager für Zeit-Messung"""
        return TimerContext(self, name)

    def get_metrics(self) -> Dict[str, Any]:
        """Hole alle Metriken"""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timers": {
                    name: stats.get_stats()
                    for name, stats in self._timers.items()
                },
            }

    def reset(self):
        """Reset alle Metriken"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._timers.clear()


class TimerContext:
    """Context Manager für Zeit-Messung"""

    def __init__(self, collector: MetricsCollector, name: str):
        self.collector = collector
        self.name = name
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.collector.record_time(self.name, duration)


# Global Metrics Collector
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Hole globalen Metrics Collector"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector
