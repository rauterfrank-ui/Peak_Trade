#!/usr/bin/env python3
"""
Demo: Trace Context Propagation
=================================
Demonstrates trace context usage with logging and error handling.

Run:
    python examples/trace_context_demo.py
"""
import logging
from datetime import datetime
import pandas as pd
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.trace_context import trace_context, get_run_id, get_trace_id
from src.core.logging_config import configure_logging
from src.core.errors import ConfigError, enrich_error_with_trace

# Configure logging with trace context
configure_logging(level=logging.INFO)

logger = logging.getLogger(__name__)


def demo_basic_usage():
    """Demo 1: Basic trace context usage."""
    print("\n" + "="*60)
    print("Demo 1: Basic Trace Context Usage")
    print("="*60 + "\n")
    
    # Without context - logs show N/A
    logger.info("Before context: This log has no trace context")
    
    # With context - logs show run_id and trace_id
    with trace_context(run_id="demo_run_001"):
        logger.info("Inside context: This log includes trace IDs")
        logger.info(f"Current run_id: {get_run_id()}")
        logger.info(f"Current trace_id: {get_trace_id()}")
    
    # After context - logs show N/A again
    logger.info("After context: Trace context cleared")


def demo_nested_operations():
    """Demo 2: Nested operations with trace context."""
    print("\n" + "="*60)
    print("Demo 2: Nested Operations")
    print("="*60 + "\n")
    
    def process_data(data_type):
        """Simulated data processing."""
        logger.info(f"Processing {data_type} data")
        # Simulate some work
        return f"{data_type}_processed"
    
    def analyze_results(results):
        """Simulated analysis."""
        logger.info(f"Analyzing results: {results}")
        return "analysis_complete"
    
    with trace_context(run_id="demo_workflow_001"):
        logger.info("Starting data workflow")
        
        # All nested calls inherit the trace context
        result1 = process_data("market")
        result2 = process_data("portfolio")
        
        final = analyze_results([result1, result2])
        
        logger.info(f"Workflow complete: {final}")


def demo_error_enrichment():
    """Demo 3: Error enrichment with trace context."""
    print("\n" + "="*60)
    print("Demo 3: Error Context Enrichment")
    print("="*60 + "\n")
    
    with trace_context(run_id="demo_error_001"):
        try:
            logger.info("Attempting risky operation")
            
            # Simulate an error
            raise ConfigError(
                "Invalid configuration parameter",
                hint="Check config.toml for valid parameter names",
                context={"parameter": "invalid_key", "section": "backtest"}
            )
        
        except ConfigError as e:
            # Enrich error with trace context
            enrich_error_with_trace(e)
            
            logger.error(f"Error occurred: {e.message}")
            logger.error(f"Error context: {e.context}")
            
            # Notice: context now includes run_id and trace_id
            print("\n📋 Error Context:")
            for key, value in e.context.items():
                print(f"  {key}: {value}")


def demo_backtest_simulation():
    """Demo 4: Simulated backtest with trace context."""
    print("\n" + "="*60)
    print("Demo 4: Backtest Simulation")
    print("="*60 + "\n")
    
    # Create sample data
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    df = pd.DataFrame({
        "close": [100.0, 101.0, 99.0, 102.0, 103.0],
    }, index=dates)
    
    def simple_strategy(df):
        """Dummy strategy."""
        return pd.Series([0] * len(df), index=df.index)
    
    # Simulate backtest with trace context
    run_id = f"backtest_{datetime.now():%Y%m%d_%H%M%S}"
    
    with trace_context(run_id=run_id):
        logger.info(f"Starting backtest")
        logger.info(f"Data shape: {df.shape}")
        
        # Generate signals
        signals = simple_strategy(df)
        logger.info(f"Generated {len(signals)} signals")
        
        # Simulate processing
        for i, (date, row) in enumerate(df.iterrows()):
            logger.debug(f"Processing bar {i+1}/{len(df)}: {date.date()}, close={row['close']:.2f}")
        
        logger.info("Backtest complete")
        logger.info(f"Results can be queried using run_id: {get_run_id()}")


def demo_concurrent_context():
    """Demo 5: Thread-safe context in concurrent operations."""
    print("\n" + "="*60)
    print("Demo 5: Thread-Safe Concurrent Operations")
    print("="*60 + "\n")
    
    import threading
    import time
    
    def worker(worker_id, delay):
        """Worker with its own trace context."""
        run_id = f"worker_{worker_id}"
        
        with trace_context(run_id=run_id):
            logger.info(f"Worker {worker_id} started")
            time.sleep(delay)
            logger.info(f"Worker {worker_id} completed")
    
    # Start multiple workers
    threads = [
        threading.Thread(target=worker, args=(1, 0.1)),
        threading.Thread(target=worker, args=(2, 0.05)),
        threading.Thread(target=worker, args=(3, 0.15)),
    ]
    
    logger.info("Starting concurrent workers")
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    logger.info("All workers completed")
    print("\n✅ Notice: Each worker had its own isolated run_id in the logs")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("🔍 Peak_Trade Trace Context Propagation Demo")
    print("="*60)
    
    try:
        demo_basic_usage()
        demo_nested_operations()
        demo_error_enrichment()
        demo_backtest_simulation()
        demo_concurrent_context()
        
        print("\n" + "="*60)
        print("✅ All demos completed successfully!")
        print("="*60 + "\n")
        
        print("💡 Key Takeaways:")
        print("  • Trace context automatically propagates through function calls")
        print("  • Logs include run_id and trace_id for correlation")
        print("  • Errors can be enriched with trace context")
        print("  • Thread-safe for concurrent operations")
        print("  • Use context managers for automatic cleanup")
        
    except Exception as e:
        logger.exception("Demo failed")
        raise


if __name__ == "__main__":
    main()
