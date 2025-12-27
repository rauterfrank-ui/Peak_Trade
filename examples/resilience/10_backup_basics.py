#!/usr/bin/env python3
"""
Example 10: Backup & Recovery Basics
=====================================
Demonstrates basic backup and recovery operations for disaster recovery.

This example shows:
- Creating backups (config, state, data)
- Listing and managing backups
- Restoring from backups
- Backup metadata and organization
"""

import sys
import json
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.backup_recovery import RecoveryManager, BackupType, StateSnapshot


def example_1_basic_backup_restore():
    """Basic backup and restore workflow."""
    print("=" * 60)
    print("Example 1: Basic Backup & Restore")
    print("=" * 60)

    # Create temporary workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / "workspace"
        workspace.mkdir()

        # Create a config file
        config_file = workspace / "config.toml"
        config_file.write_text(
            """
[settings]
trading_enabled = true
max_position_size = 10000
risk_level = "moderate"
"""
        )

        print("\n1. Original configuration:")
        print(f"   {config_file.read_text().strip()}")

        # Initialize recovery manager
        recovery = RecoveryManager(backup_dir=str(workspace / "backups"))
        recovery.config_backup.add_config(config_file)

        # Create backup
        print("\n2. Creating backup...")
        backup_id = recovery.create_backup(
            include_config=True, description="Initial configuration backup"
        )
        print(f"   ✅ Backup created: {backup_id}")

        # Simulate config corruption
        print("\n3. Simulating configuration corruption...")
        config_file.write_text("CORRUPTED_DATA_#$%^&*()")
        print(f"   Config after corruption: {config_file.read_text()[:30]}...")

        # Restore from backup
        print("\n4. Restoring from backup...")
        success = recovery.restore_backup(backup_id, restore_config=True)

        if success:
            print("   ✅ Restore successful!")
            print(f"\n5. Restored configuration:")
            print(f"   {config_file.read_text().strip()}")
        else:
            print("   ❌ Restore failed!")

    print("=" * 60)


def example_2_state_snapshots():
    """Working with state snapshots."""
    print("\n" + "=" * 60)
    print("Example 2: State Snapshots")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create recovery manager
        recovery = RecoveryManager(backup_dir=str(workspace / "backups"))

        # Register state providers
        print("\n1. Registering state providers...")

        recovery.state_snapshot.register_provider(
            "system_metrics",
            lambda: {"cpu_usage": 45.2, "memory_mb": 2048, "active_connections": 12},
        )

        recovery.state_snapshot.register_provider(
            "trading_state",
            lambda: {
                "active_positions": 3,
                "pending_orders": 1,
                "last_trade_time": "2024-12-17T10:30:00Z",
            },
        )

        print("   ✅ Registered 2 state providers")

        # Create backup with state
        print("\n2. Creating backup with state snapshot...")
        backup_id = recovery.create_backup(
            include_state=True, description="State snapshot backup", tags=["state", "metrics"]
        )
        print(f"   ✅ Backup created: {backup_id}")

        # List backups
        print("\n3. Listing backups:")
        backups = recovery.list_backups()
        for backup in backups:
            print(f"   • {backup.backup_id}")
            print(f"     Type: {backup.backup_type.value}")
            print(f"     Created: {backup.created_at}")
            print(f"     Tags: {', '.join(backup.tags)}")
            print(f"     Files: {backup.files_count}")

        # Load and inspect state
        print("\n4. Loading state snapshot...")
        backup_dir = recovery._get_backup_dir(backup_id)
        state_file = backup_dir / "state.json"

        with open(state_file) as f:
            state = json.load(f)

        print(f"   Timestamp: {state['timestamp']}")
        print(f"   Providers: {len(state['providers'])}")
        print(f"\n   System Metrics:")
        for key, value in state["providers"]["system_metrics"].items():
            print(f"     - {key}: {value}")
        print(f"\n   Trading State:")
        for key, value in state["providers"]["trading_state"].items():
            print(f"     - {key}: {value}")

    print("=" * 60)


def example_3_data_backup():
    """Backing up data files and directories."""
    print("\n" + "=" * 60)
    print("Example 3: Data Backup")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create sample data files
        data_dir = workspace / "data"
        data_dir.mkdir()

        # Create sample CSV files
        (data_dir / "trades.csv").write_text(
            """
timestamp,symbol,side,price,quantity
2024-12-17T10:00:00,BTC/USD,buy,45000,0.1
2024-12-17T11:00:00,ETH/USD,sell,3000,1.5
""".strip()
        )

        (data_dir / "positions.csv").write_text(
            """
symbol,quantity,avg_price,unrealized_pnl
BTC/USD,0.1,45000,500.00
""".strip()
        )

        # Create subdirectory
        reports_dir = data_dir / "reports"
        reports_dir.mkdir()
        (reports_dir / "daily_report.json").write_text('{"pnl": 500, "trades": 2}')

        print("\n1. Data structure:")
        print("   data/")
        print("   ├── trades.csv (2 records)")
        print("   ├── positions.csv (1 position)")
        print("   └── reports/")
        print("       └── daily_report.json")

        # Setup recovery manager
        recovery = RecoveryManager(backup_dir=str(workspace / "backups"))
        recovery.data_backup.add_data_path(data_dir)

        # Create backup
        print("\n2. Creating data backup...")
        backup_id = recovery.create_backup(
            include_data=True,
            description="Data backup with trades and positions",
            tags=["data", "trades"],
        )
        print(f"   ✅ Backup created: {backup_id}")

        # Get backup metadata
        backups = recovery.list_backups()
        metadata = backups[0]
        print(f"   Files backed up: {metadata.files_count}")
        print(f"   Total size: {metadata.size_bytes} bytes")

        # Simulate data loss
        print("\n3. Simulating data loss...")
        import shutil

        shutil.rmtree(data_dir)
        print("   ❌ Data directory deleted!")

        # Restore
        print("\n4. Restoring data...")
        success = recovery.restore_backup(backup_id, restore_data=True)

        if success:
            print("   ✅ Data restored successfully!")
            print(f"\n5. Verifying restored data:")
            print(f"   - trades.csv exists: {(data_dir / 'trades.csv').exists()}")
            print(f"   - positions.csv exists: {(data_dir / 'positions.csv').exists()}")
            print(
                f"   - reports/daily_report.json exists: {(reports_dir / 'daily_report.json').exists()}"
            )

            # Verify content
            trades_content = (data_dir / "trades.csv").read_text()
            print(f"\n   trades.csv content (first 100 chars):")
            print(f"   {trades_content[:100]}...")

    print("=" * 60)


def example_4_full_backup():
    """Creating a complete full backup."""
    print("\n" + "=" * 60)
    print("Example 4: Full System Backup")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Setup workspace
        config_file = workspace / "config.toml"
        config_file.write_text("[settings]\nversion = '1.0'")

        data_file = workspace / "data.csv"
        data_file.write_text("col1,col2\n1,2")

        # Initialize recovery manager
        recovery = RecoveryManager(backup_dir=str(workspace / "backups"))

        # Configure what to backup
        recovery.config_backup.add_config(config_file)
        recovery.data_backup.add_data_path(data_file)
        recovery.state_snapshot.register_provider(
            "app_state", lambda: {"version": "1.0", "uptime_seconds": 3600}
        )

        print("\n1. Creating FULL backup (config + state + data)...")
        backup_id = recovery.create_backup(
            include_config=True,
            include_state=True,
            include_data=True,
            description="Complete system backup",
            tags=["full", "production", "critical"],
        )
        print(f"   ✅ Backup created: {backup_id}")

        # Inspect backup
        print("\n2. Backup details:")
        backups = recovery.list_backups()
        metadata = backups[0]

        print(f"   ID: {metadata.backup_id}")
        print(f"   Type: {metadata.backup_type.value}")
        print(f"   Status: {metadata.status.value}")
        print(f"   Description: {metadata.description}")
        print(f"   Tags: {', '.join(metadata.tags)}")
        print(f"   Files: {metadata.files_count}")
        print(f"   Size: {metadata.size_bytes} bytes")
        print(f"   Created: {metadata.created_at}")

        # Show backup structure
        print("\n3. Backup directory structure:")
        backup_dir = recovery._get_backup_dir(backup_id)
        for item in sorted(backup_dir.rglob("*")):
            if item.is_file():
                rel_path = item.relative_to(backup_dir)
                print(f"   {rel_path}")

    print("=" * 60)


def example_5_backup_management():
    """Managing multiple backups."""
    print("\n" + "=" * 60)
    print("Example 5: Backup Management")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create config
        config_file = workspace / "config.toml"
        config_file.write_text("[settings]\nkey = 'value'")

        recovery = RecoveryManager(backup_dir=str(workspace / "backups"))
        recovery.config_backup.add_config(config_file)

        print("\n1. Creating multiple backups...")
        backup_ids = []
        for i in range(5):
            backup_id = recovery.create_backup(
                include_config=True,
                description=f"Backup #{i + 1}",
                tags=["daily"] if i % 2 == 0 else ["hourly"],
            )
            backup_ids.append(backup_id)
            print(f"   ✅ Created backup {i + 1}: {backup_id[:20]}...")

        # List all backups
        print("\n2. All backups:")
        all_backups = recovery.list_backups()
        print(f"   Total backups: {len(all_backups)}")

        # Filter by tags
        print("\n3. Filtering by tags:")
        daily_backups = recovery.list_backups(tags=["daily"])
        hourly_backups = recovery.list_backups(tags=["hourly"])
        print(f"   Daily backups: {len(daily_backups)}")
        print(f"   Hourly backups: {len(hourly_backups)}")

        # Delete specific backup
        print("\n4. Deleting oldest backup...")
        oldest_backup = all_backups[-1]  # List is sorted newest first
        success = recovery.delete_backup(oldest_backup.backup_id)
        print(f"   ✅ Deleted: {oldest_backup.backup_id[:20]}...")

        # Cleanup old backups
        print("\n5. Cleaning up old backups (keep 3)...")
        deleted = recovery.cleanup_old_backups(keep_count=3)
        print(f"   ✅ Deleted {deleted} old backups")

        remaining = recovery.list_backups()
        print(f"   Remaining backups: {len(remaining)}")

    print("=" * 60)


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" Backup & Recovery Basics ".center(70))
    print("=" * 70)

    try:
        example_1_basic_backup_restore()

        example_2_state_snapshots()

        example_3_data_backup()

        example_4_full_backup()

        example_5_backup_management()

        print("\n" + "=" * 70)
        print(" All examples completed successfully! ".center(70))
        print("=" * 70)
        print("\nKey Takeaways:")
        print("  1. RecoveryManager orchestrates all backup operations")
        print("  2. Support for config, state, and data backups")
        print("  3. Metadata tracking with tags and descriptions")
        print("  4. Easy restore with dry-run capability")
        print("  5. Automated backup management and cleanup")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
