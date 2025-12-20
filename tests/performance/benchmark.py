"""
Performance Benchmark Framework
================================

Framework for performance benchmarking with sub-millisecond precision,
memory profiling, and regression detection.
"""

import time
import gc
import statistics
import tracemalloc
from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result from a benchmark run."""
    
    name: str
    iterations: int
    times: List[float] = field(default_factory=list)
    memory_peak: Optional[int] = None  # bytes
    
    @property
    def mean_time(self) -> float:
        """Mean execution time in seconds."""
        return statistics.mean(self.times) if self.times else 0.0
    
    @property
    def median_time(self) -> float:
        """Median execution time in seconds."""
        return statistics.median(self.times) if self.times else 0.0
    
    @property
    def std_time(self) -> float:
        """Standard deviation of execution time."""
        return statistics.stdev(self.times) if len(self.times) > 1 else 0.0
    
    @property
    def min_time(self) -> float:
        """Minimum execution time."""
        return min(self.times) if self.times else 0.0
    
    @property
    def max_time(self) -> float:
        """Maximum execution time."""
        return max(self.times) if self.times else 0.0
    
    @property
    def memory_peak_mb(self) -> float:
        """Peak memory usage in MB."""
        return self.memory_peak / (1024 * 1024) if self.memory_peak else 0.0
    
    def __str__(self) -> str:
        """String representation of benchmark result."""
        return (
            f"BenchmarkResult(name={self.name}, "
            f"mean={self.mean_time:.6f}s, "
            f"median={self.median_time:.6f}s, "
            f"std={self.std_time:.6f}s, "
            f"min={self.min_time:.6f}s, "
            f"max={self.max_time:.6f}s, "
            f"memory={self.memory_peak_mb:.2f}MB)"
        )


class PerformanceBenchmark:
    """
    Framework for Performance-Benchmarking.
    
    Features:
    - Sub-millisecond precision timing
    - Memory profiling
    - Warmup iterations
    - Statistical analysis
    - Regression detection
    """
    
    def __init__(self, baseline: Optional[Dict[str, BenchmarkResult]] = None):
        """
        Initialize benchmark framework.
        
        Args:
            baseline: Optional baseline results for regression detection
        """
        self.baseline = baseline or {}
        self.results: Dict[str, BenchmarkResult] = {}
    
    def benchmark(
        self,
        func: Callable,
        name: str = "benchmark",
        iterations: int = 100,
        warmup: int = 10,
        profile_memory: bool = True
    ) -> BenchmarkResult:
        """
        Run benchmark with statistics.
        
        Args:
            func: Function to benchmark
            name: Benchmark name
            iterations: Number of iterations
            warmup: Number of warmup iterations
            profile_memory: Whether to profile memory usage
            
        Returns:
            BenchmarkResult with timing and memory statistics
        """
        logger.info(f"Running benchmark: {name} (warmup={warmup}, iterations={iterations})")
        
        # Warmup phase
        for _ in range(warmup):
            func()
        
        # Force garbage collection before measurement
        gc.collect()
        
        # Benchmark phase
        times = []
        memory_peak = None
        
        if profile_memory:
            tracemalloc.start()
        
        for i in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append(end - start)
        
        if profile_memory:
            _, peak = tracemalloc.get_traced_memory()
            memory_peak = peak
            tracemalloc.stop()
        
        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            times=times,
            memory_peak=memory_peak
        )
        
        self.results[name] = result
        logger.info(str(result))
        
        return result
    
    def run(
        self,
        func: Callable,
        name: str = "benchmark",
        iterations: int = 100,
        warmup: int = 10
    ) -> BenchmarkResult:
        """Alias for benchmark() method."""
        return self.benchmark(func, name, iterations, warmup)
    
    def compare_with_baseline(
        self,
        name: str,
        threshold: float = 0.2
    ) -> Dict[str, Any]:
        """
        Compare benchmark result with baseline.
        
        Args:
            name: Benchmark name
            threshold: Regression threshold (0.2 = 20% slower)
            
        Returns:
            Comparison results dict
        """
        if name not in self.results:
            raise ValueError(f"No result found for benchmark: {name}")
        
        if name not in self.baseline:
            return {
                "status": "no_baseline",
                "message": "No baseline available for comparison"
            }
        
        current = self.results[name]
        baseline = self.baseline[name]
        
        time_diff = current.mean_time - baseline.mean_time
        time_ratio = current.mean_time / baseline.mean_time if baseline.mean_time > 0 else float('inf')
        
        is_regression = time_ratio > (1 + threshold)
        
        return {
            "status": "regression" if is_regression else "ok",
            "current_time": current.mean_time,
            "baseline_time": baseline.mean_time,
            "time_diff": time_diff,
            "time_ratio": time_ratio,
            "threshold": threshold,
            "is_regression": is_regression
        }
    
    def assert_no_regression(
        self,
        name: str,
        threshold: float = 0.2
    ):
        """
        Assert that benchmark has not regressed.
        
        Args:
            name: Benchmark name
            threshold: Regression threshold
            
        Raises:
            AssertionError: If regression detected
        """
        comparison = self.compare_with_baseline(name, threshold)
        
        if comparison["status"] == "regression":
            raise AssertionError(
                f"Performance regression detected for {name}: "
                f"{comparison['time_ratio']:.2%} slower than baseline "
                f"(threshold: {threshold:.0%})"
            )


# Global benchmark instance for convenience
_global_benchmark = PerformanceBenchmark()


def benchmark(
    func: Callable,
    name: str = "benchmark",
    iterations: int = 100,
    warmup: int = 10
) -> BenchmarkResult:
    """
    Convenience function for running a benchmark.
    
    Args:
        func: Function to benchmark
        name: Benchmark name
        iterations: Number of iterations
        warmup: Number of warmup iterations
        
    Returns:
        BenchmarkResult
    """
    return _global_benchmark.benchmark(func, name, iterations, warmup)
