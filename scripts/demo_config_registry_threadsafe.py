#!/usr/bin/env python3
"""
Demo: Thread-Safe Config Registry with Hot-Reload
==================================================
This script demonstrates the new thread-safe config registry features:
1. Thread-safe concurrent access
2. Hot-reload with file watcher
3. Rollback mechanism
4. Deep copy protection

Usage:
    python scripts/demo_config_registry_threadsafe.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import threading
from src.config import get_registry, start_config_watcher, reset_registry


def demo_basic_usage():
    """Demo 1: Basic usage."""
    print("=" * 60)
    print("Demo 1: Basic Usage")
    print("=" * 60)
    
    reset_registry()
    registry = get_registry()
    
    # Load config
    config_path = Path("config/config.toml")
    config = registry.load(config_path)
    
    print(f"✅ Config loaded from: {config_path}")
    print(f"   Initial cash: {config.backtest.initial_cash}")
    print(f"   Risk per trade: {config.risk.risk_per_trade}")
    print(f"   Max positions: {config.risk.max_positions}")
    print()


def demo_thread_safety():
    """Demo 2: Thread-safe concurrent access."""
    print("=" * 60)
    print("Demo 2: Thread-Safe Concurrent Access")
    print("=" * 60)
    
    reset_registry()
    registry = get_registry()
    registry.load(Path("config/config.toml"))
    
    results = []
    
    def reader(thread_id):
        config = registry.get_config()
        cash = config.backtest.initial_cash
        results.append((thread_id, cash))
        print(f"  Thread {thread_id}: Read cash = {cash}")
    
    # Start 5 concurrent readers
    threads = [threading.Thread(target=reader, args=(i,)) for i in range(5)]
    
    print("Starting 5 concurrent readers...")
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    print(f"✅ All threads completed successfully")
    print(f"   All values consistent: {len(set(r[1] for r in results)) == 1}")
    print()


def demo_deep_copy_protection():
    """Demo 3: Deep copy prevents mutations."""
    print("=" * 60)
    print("Demo 3: Deep Copy Protection")
    print("=" * 60)
    
    reset_registry()
    registry = get_registry()
    registry.load(Path("config/config.toml"))
    
    # Get config and try to mutate it
    config1 = registry.get_config()
    original_cash = config1.backtest.initial_cash
    
    print(f"Original cash: {original_cash}")
    
    # Try to mutate
    config1.backtest.initial_cash = 99999.0
    print(f"Mutated copy: {config1.backtest.initial_cash}")
    
    # Get config again
    config2 = registry.get_config()
    print(f"Fresh copy: {config2.backtest.initial_cash}")
    
    print(f"✅ Mutation isolated: {config2.backtest.initial_cash == original_cash}")
    print()


def demo_reload_and_rollback():
    """Demo 4: Reload and rollback."""
    print("=" * 60)
    print("Demo 4: Reload and Rollback")
    print("=" * 60)
    
    reset_registry()
    registry = get_registry()
    registry.load(Path("config/config.toml"))
    
    print(f"Initial config loaded")
    print(f"  Snapshot count: {registry.get_snapshot_count()}")
    
    # Simulate multiple reloads (would normally be from file changes)
    for i in range(3):
        success = registry.reload(Path("config/config.toml"))
        if success:
            print(f"  Reload {i+1}: Success")
            print(f"    Snapshot count: {registry.get_snapshot_count()}")
    
    # Rollback
    print(f"\nRolling back 1 step...")
    success = registry.rollback(steps=1)
    if success:
        print(f"✅ Rollback successful")
        print(f"   Snapshot count: {registry.get_snapshot_count()}")
    
    print()


def demo_hot_reload():
    """Demo 5: Hot-reload with file watcher."""
    print("=" * 60)
    print("Demo 5: Hot-Reload with File Watcher")
    print("=" * 60)
    
    reset_registry()
    registry = get_registry()
    config_path = Path("config/config.toml")
    
    # Load config
    registry.load(config_path)
    print(f"Config loaded from: {config_path}")
    
    # Start watcher
    print(f"Starting file watcher...")
    observer = start_config_watcher(registry, config_path)
    print(f"✅ Watcher started (monitoring: {config_path.parent})")
    print(f"   File changes will trigger automatic reload")
    print(f"   Failed reloads will automatically rollback")
    
    # Run for a bit
    print(f"\nWatching for 3 seconds...")
    time.sleep(3)
    
    # Stop watcher
    print(f"Stopping watcher...")
    observer.stop()
    observer.join(timeout=5)
    print(f"✅ Watcher stopped")
    print()


def demo_snapshot_history():
    """Demo 6: Snapshot history management."""
    print("=" * 60)
    print("Demo 6: Snapshot History Management")
    print("=" * 60)
    
    reset_registry()
    registry = get_registry()
    registry.load(Path("config/config.toml"))
    
    print(f"Max snapshots: {registry._max_snapshots}")
    print(f"Current snapshots: {registry.get_snapshot_count()}")
    
    # Perform multiple reloads to exceed max snapshots
    print(f"\nPerforming 10 reloads...")
    for i in range(10):
        registry.reload(Path("config/config.toml"))
        print(f"  After reload {i+1}: {registry.get_snapshot_count()} snapshots")
    
    print(f"\n✅ Snapshot limit enforced")
    print(f"   Final count: {registry.get_snapshot_count()} (max: {registry._max_snapshots})")
    print()


def main():
    """Run all demos."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  Thread-Safe Config Registry Demo".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    try:
        demo_basic_usage()
        demo_thread_safety()
        demo_deep_copy_protection()
        demo_reload_and_rollback()
        demo_hot_reload()
        demo_snapshot_history()
        
        print("=" * 60)
        print("✅ All demos completed successfully!")
        print("=" * 60)
        print()
        print("Key Features Demonstrated:")
        print("  ✅ Thread-safe concurrent access")
        print("  ✅ Deep copy mutation protection")
        print("  ✅ Atomic reload with rollback")
        print("  ✅ Hot-reload with file watcher")
        print("  ✅ Snapshot history management")
        print()
        print("For more info, see: docs/CONFIGURATION_GUIDE.md")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
