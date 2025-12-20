"""
Asynchronous Data Loading
==========================

Async data loader for concurrent API requests and data loading.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
import pandas as pd

logger = logging.getLogger(__name__)


class AsyncDataLoader:
    """
    Asynchronous data loading.
    
    Features:
    - Concurrent API requests
    - Connection pooling
    - Rate limiting
    - Error handling
    """
    
    def __init__(
        self,
        max_concurrent: int = 10,
        rate_limit_per_second: Optional[float] = None
    ):
        """
        Initialize async data loader.
        
        Args:
            max_concurrent: Maximum concurrent requests
            rate_limit_per_second: Rate limit (requests per second)
        """
        self.max_concurrent = max_concurrent
        self.rate_limit_per_second = rate_limit_per_second
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._rate_limiter = None
        
        if rate_limit_per_second:
            self._rate_limiter = asyncio.Semaphore(1)
            self._last_request_time = 0.0
    
    async def load_multiple_symbols(
        self,
        symbols: List[str],
        timeframe: str,
        loader_func: callable
    ) -> Dict[str, pd.DataFrame]:
        """
        Load data for multiple symbols concurrently.
        
        Args:
            symbols: List of symbols
            timeframe: Timeframe (e.g., "1h", "1d")
            loader_func: Function to load data for a single symbol
            
        Returns:
            Dict mapping symbols to DataFrames
        """
        tasks = [
            self._load_single(symbol, timeframe, loader_func)
            for symbol in symbols
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        output = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to load {symbol}: {result}")
                output[symbol] = None
            else:
                output[symbol] = result
        
        return output
    
    async def _load_single(
        self,
        symbol: str,
        timeframe: str,
        loader_func: callable
    ) -> pd.DataFrame:
        """Load data for a single symbol."""
        async with self._semaphore:
            # Rate limiting
            if self._rate_limiter:
                await self._apply_rate_limit()
            
            # Load data (synchronous function in executor)
            loop = asyncio.get_event_loop()
            try:
                data = await loop.run_in_executor(
                    None,
                    loader_func,
                    symbol,
                    timeframe
                )
                return data
            except Exception as e:
                logger.error(f"Error loading {symbol}: {e}")
                raise
    
    async def _apply_rate_limit(self):
        """Apply rate limiting."""
        if not self.rate_limit_per_second:
            return
        
        async with self._rate_limiter:
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self._last_request_time
            min_interval = 1.0 / self.rate_limit_per_second
            
            if time_since_last < min_interval:
                wait_time = min_interval - time_since_last
                await asyncio.sleep(wait_time)
            
            self._last_request_time = asyncio.get_event_loop().time()


class AsyncTaskQueue:
    """
    Async task queue for background processing.
    
    Use Cases:
    - Report generation
    - Cache warming
    - Backtest queue
    """
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize task queue.
        
        Args:
            max_workers: Maximum concurrent workers
        """
        self.queue: asyncio.Queue = asyncio.Queue()
        self.max_workers = max_workers
        self._running = False
        self._workers = []
    
    async def add_task(self, task: callable, *args, **kwargs):
        """
        Add task to queue.
        
        Args:
            task: Callable task
            args: Positional arguments
            kwargs: Keyword arguments
        """
        await self.queue.put((task, args, kwargs))
    
    async def process_queue(self):
        """Process tasks from queue."""
        self._running = True
        
        while self._running:
            try:
                # Get task with timeout
                task, args, kwargs = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )
                
                try:
                    await self._process_task(task, args, kwargs)
                except Exception as e:
                    logger.error(f"Task failed: {e}")
                finally:
                    self.queue.task_done()
            except asyncio.TimeoutError:
                # No task available, continue
                continue
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
    
    async def _process_task(self, task: callable, args: tuple, kwargs: dict):
        """Process a single task."""
        if asyncio.iscoroutinefunction(task):
            await task(*args, **kwargs)
        else:
            # Run sync function in executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, task, *args, **kwargs)
    
    async def start(self):
        """Start workers."""
        self._workers = [
            asyncio.create_task(self.process_queue())
            for _ in range(self.max_workers)
        ]
        logger.info(f"Started {self.max_workers} task queue workers")
    
    async def stop(self):
        """Stop workers."""
        self._running = False
        
        # Wait for workers to finish
        for worker in self._workers:
            worker.cancel()
        
        await asyncio.gather(*self._workers, return_exceptions=True)
        logger.info("Stopped task queue workers")
    
    async def wait_completion(self):
        """Wait for all tasks to complete."""
        await self.queue.join()


# Convenience function for loading multiple symbols
async def load_multiple_symbols_async(
    symbols: List[str],
    timeframe: str,
    loader_func: callable,
    max_concurrent: int = 10
) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to load multiple symbols asynchronously.
    
    Args:
        symbols: List of symbols
        timeframe: Timeframe
        loader_func: Sync function to load data for a single symbol
        max_concurrent: Maximum concurrent requests
        
    Returns:
        Dict mapping symbols to DataFrames
    """
    loader = AsyncDataLoader(max_concurrent=max_concurrent)
    return await loader.load_multiple_symbols(symbols, timeframe, loader_func)
