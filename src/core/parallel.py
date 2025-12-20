"""
Parallel Processing Utilities
==============================

Utilities for parallel execution of CPU-bound and I/O-bound tasks,
optimized for Apple Silicon.
"""

import multiprocessing
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import List, Callable, Any, Optional, Dict
import os

logger = logging.getLogger(__name__)


def get_cpu_info() -> Dict[str, int]:
    """
    Get CPU information.
    
    Returns:
        Dict with CPU core information
    """
    total_cores = multiprocessing.cpu_count()
    
    # Apple Silicon typically has performance and efficiency cores
    # M2 Pro: 8 performance + 4 efficiency = 12 total
    # M3 Pro: 6 performance + 6 efficiency = 12 total
    # For CPU-bound tasks, use performance cores only
    
    # Heuristic: assume ~2/3 are performance cores for Apple Silicon
    if os.uname().machine == 'arm64':
        performance_cores = max(1, int(total_cores * 2 / 3))
        efficiency_cores = total_cores - performance_cores
    else:
        performance_cores = total_cores
        efficiency_cores = 0
    
    return {
        'total_cores': total_cores,
        'performance_cores': performance_cores,
        'efficiency_cores': efficiency_cores
    }


def parallel_map(
    func: Callable,
    items: List[Any],
    max_workers: Optional[int] = None,
    use_processes: bool = True,
    show_progress: bool = False
) -> List[Any]:
    """
    Execute function in parallel on list of items.
    
    Args:
        func: Function to execute
        items: List of items to process
        max_workers: Max parallel workers (None = auto)
        use_processes: Use processes (CPU-bound) vs threads (I/O-bound)
        show_progress: Show progress (requires tqdm)
        
    Returns:
        List of results
    """
    if not items:
        return []
    
    # Determine worker count
    if max_workers is None:
        cpu_info = get_cpu_info()
        if use_processes:
            # CPU-bound: use performance cores
            max_workers = cpu_info['performance_cores']
        else:
            # I/O-bound: can use more workers
            max_workers = cpu_info['total_cores'] * 2
    
    logger.info(
        f"Parallel execution: {len(items)} items, "
        f"{max_workers} workers, "
        f"{'processes' if use_processes else 'threads'}"
    )
    
    # Select executor
    ExecutorClass = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
    
    results = []
    with ExecutorClass(max_workers=max_workers) as executor:
        futures = [executor.submit(func, item) for item in items]
        
        # Collect results
        iterator = as_completed(futures)
        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(iterator, total=len(items))
            except ImportError:
                pass
        
        for future in iterator:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Parallel task failed: {e}")
                results.append(None)
    
    return results


def parallel_backtest(
    strategies: List[Any],
    data: Any,
    backtest_func: Callable,
    max_workers: Optional[int] = None
) -> List[Any]:
    """
    Parallel backtest execution.
    
    Use ProcessPoolExecutor for CPU-bound tasks.
    
    Args:
        strategies: List of strategies to backtest
        data: Market data
        backtest_func: Backtest function(strategy, data) -> result
        max_workers: Max parallel workers
        
    Returns:
        List of backtest results
    """
    cpu_info = get_cpu_info()
    if max_workers is None:
        max_workers = cpu_info['performance_cores']
    
    logger.info(f"Running parallel backtests: {len(strategies)} strategies, {max_workers} workers")
    
    def run_single_backtest(strategy):
        try:
            return backtest_func(strategy, data)
        except Exception as e:
            logger.error(f"Backtest failed for {strategy}: {e}")
            return None
    
    return parallel_map(
        run_single_backtest,
        strategies,
        max_workers=max_workers,
        use_processes=True
    )


def parallel_apply(
    df_func: Callable,
    dfs: List[Any],
    max_workers: Optional[int] = None
) -> List[Any]:
    """
    Apply function to multiple DataFrames in parallel.
    
    Args:
        df_func: Function to apply to each DataFrame
        dfs: List of DataFrames
        max_workers: Max parallel workers
        
    Returns:
        List of results
    """
    return parallel_map(
        df_func,
        dfs,
        max_workers=max_workers,
        use_processes=True
    )


class ParallelTaskManager:
    """
    Manager for parallel task execution.
    
    Handles both CPU-bound (processes) and I/O-bound (threads) tasks.
    """
    
    def __init__(
        self,
        max_cpu_workers: Optional[int] = None,
        max_io_workers: Optional[int] = None
    ):
        """
        Initialize task manager.
        
        Args:
            max_cpu_workers: Max workers for CPU-bound tasks
            max_io_workers: Max workers for I/O-bound tasks
        """
        cpu_info = get_cpu_info()
        
        self.max_cpu_workers = max_cpu_workers or cpu_info['performance_cores']
        self.max_io_workers = max_io_workers or (cpu_info['total_cores'] * 2)
        
        logger.info(
            f"Parallel task manager initialized: "
            f"CPU workers={self.max_cpu_workers}, "
            f"I/O workers={self.max_io_workers}"
        )
    
    def execute_cpu_tasks(
        self,
        func: Callable,
        items: List[Any]
    ) -> List[Any]:
        """Execute CPU-bound tasks in parallel."""
        return parallel_map(
            func,
            items,
            max_workers=self.max_cpu_workers,
            use_processes=True
        )
    
    def execute_io_tasks(
        self,
        func: Callable,
        items: List[Any]
    ) -> List[Any]:
        """Execute I/O-bound tasks in parallel."""
        return parallel_map(
            func,
            items,
            max_workers=self.max_io_workers,
            use_processes=False
        )


# Global task manager instance
_global_task_manager: Optional[ParallelTaskManager] = None


def get_task_manager() -> ParallelTaskManager:
    """Get or create global task manager."""
    global _global_task_manager
    if _global_task_manager is None:
        _global_task_manager = ParallelTaskManager()
    return _global_task_manager
