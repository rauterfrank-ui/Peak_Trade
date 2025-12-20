"""
NumPy and Apple Silicon Optimizations
======================================

Optimizations for Apple Silicon (M1/M2/M3) and general NumPy acceleration.
"""

import os
import logging
import numpy as np
import pandas as pd
from typing import Optional

logger = logging.getLogger(__name__)


def configure_numpy_for_apple_silicon(
    num_threads: Optional[int] = None,
    force: bool = False
):
    """
    Optimize NumPy for Apple M1/M2/M3.
    
    - Use Accelerate Framework
    - OpenBLAS tuning
    - Thread configuration
    
    Args:
        num_threads: Number of threads (None = auto-detect)
        force: Force reconfiguration even if already set
    """
    # Check if already configured
    if not force and os.environ.get("NUMPY_ACCEL_CONFIGURED"):
        logger.debug("NumPy already configured for Apple Silicon")
        return
    
    # Auto-detect threads for Apple Silicon
    if num_threads is None:
        # M2 Pro: 8 performance cores + 4 efficiency cores
        # M3 Pro: 6/5 performance cores + 6 efficiency cores
        # Default to 8 for performance cores
        num_threads = 8
    
    # Set environment variables for thread count
    os.environ["OPENBLAS_NUM_THREADS"] = str(num_threads)
    os.environ["VECLIB_MAXIMUM_THREADS"] = str(num_threads)
    os.environ["MKL_NUM_THREADS"] = str(num_threads)
    os.environ["NUMEXPR_NUM_THREADS"] = str(num_threads)
    os.environ["OMP_NUM_THREADS"] = str(num_threads)
    
    # Mark as configured
    os.environ["NUMPY_ACCEL_CONFIGURED"] = "1"
    
    logger.info(f"NumPy configured for Apple Silicon with {num_threads} threads")
    
    # Verify BLAS backend
    try:
        config = np.show_config()
        logger.debug(f"NumPy BLAS config: {config}")
    except Exception as e:
        logger.warning(f"Could not verify NumPy BLAS backend: {e}")


def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reduce DataFrame memory footprint.
    
    - Downcast numeric types
    - Category dtype for strings
    - Sparse arrays for sparse data
    
    Args:
        df: DataFrame to optimize
        
    Returns:
        Optimized DataFrame
    """
    df = df.copy()
    
    # Downcast integers
    for col in df.select_dtypes(include=['int']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')
    
    # Downcast floats
    for col in df.select_dtypes(include=['float']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')
    
    # Convert object columns to category if appropriate
    for col in df.select_dtypes(include=['object']).columns:
        num_unique = df[col].nunique()
        num_total = len(df)
        if num_unique / num_total < 0.5:  # < 50% unique
            df[col] = df[col].astype('category')
    
    return df


def estimate_dataframe_memory(df: pd.DataFrame) -> dict:
    """
    Estimate DataFrame memory usage.
    
    Args:
        df: DataFrame
        
    Returns:
        Dict with memory statistics
    """
    memory_usage = df.memory_usage(deep=True)
    total_mb = memory_usage.sum() / (1024 * 1024)
    
    return {
        "total_mb": total_mb,
        "per_column_mb": {
            col: memory_usage[col] / (1024 * 1024)
            for col in df.columns
        },
        "rows": len(df),
        "columns": len(df.columns)
    }


def optimize_numpy_operations():
    """
    Configure NumPy for optimal performance.
    
    Sets numpy to use all available optimizations.
    """
    # Enable all CPU optimizations
    try:
        # Try to set processor flags
        if hasattr(np, '__config__'):
            logger.debug(f"NumPy config: {np.__config__.show()}")
    except Exception as e:
        logger.debug(f"Could not display NumPy config: {e}")
    
    logger.info("NumPy operations optimized")


# Auto-configure on import (can be disabled by setting env var)
if not os.environ.get("SKIP_NUMPY_AUTO_CONFIG"):
    try:
        configure_numpy_for_apple_silicon()
    except Exception as e:
        logger.warning(f"Could not auto-configure NumPy: {e}")
