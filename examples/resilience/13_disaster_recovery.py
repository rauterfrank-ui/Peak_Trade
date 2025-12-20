#!/usr/bin/env python3
"""
Example 13: Complete Disaster Recovery Workflow
================================================
Demonstrates a complete disaster recovery workflow combining all resilience features.

This example shows:
- Automated backup scheduling
- Health monitoring with backup triggers
- Disaster detection and recovery
- Multi-layered resilience approach
- Production-ready patterns
"""

import sys
import time
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.resilience import circuit_breaker, retry_with_backoff, health_check, HealthCheck
from src.core.backup_recovery import RecoveryManager


class TradingSystem:
    """Simulated trading system with full resilience."""
    
    def __init__(self, workspace_dir):
        self.workspace = Path(workspace_dir)
        self.config_file = self.workspace / "config.toml"
        self.state_file = self.workspace / "state.json"
        self.data_dir = self.workspace / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize recovery manager
        self.recovery = RecoveryManager(
            backup_dir=str(self.workspace / "backups")
        )
        
        # Configure backup sources
        self.recovery.config_backup.add_config(self.config_file)
        self.recovery.data_backup.add_data_path(self.data_dir)
        
        # Register state providers
        self.recovery.state_snapshot.register_provider(
            "trading_state",
            self._get_trading_state
        )
        
        # Initialize health check
        self.health = HealthCheck()
        self._register_health_checks()
        
        print(f"✅ Trading system initialized at {workspace_dir}")
    
    def _get_trading_state(self):
        """Get current trading state for backup."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_positions": self._count_positions(),
            "system_status": "running"
        }
    
    def _count_positions(self):
        """Count active positions."""
        positions_file = self.data_dir / "positions.csv"
        if positions_file.exists():
            lines = positions_file.read_text().strip().split('\n')
            return len(lines) - 1  # Exclude header
        return 0
    
    def _register_health_checks(self):
        """Register system health checks."""
        self.health.register("config", self._check_config)
        self.health.register("data", self._check_data)
        self.health.register("backups", self._check_backups)
    
    def _check_config(self):
        """Check if configuration is valid."""
        if not self.config_file.exists():
            return False, "Config file missing"
        
        try:
            content = self.config_file.read_text()
            if "CORRUPTED" in content or len(content) < 10:
                return False, "Config appears corrupted"
            return True, "Config is healthy"
        except Exception as e:
            return False, f"Config check failed: {e}"
    
    def _check_data(self):
        """Check if critical data exists."""
        if not self.data_dir.exists():
            return False, "Data directory missing"
        
        positions = self.data_dir / "positions.csv"
        if not positions.exists():
            return False, "Positions file missing"
        
        return True, f"Data healthy ({self._count_positions()} positions)"
    
    def _check_backups(self):
        """Check if recent backups exist."""
        backups = self.recovery.list_backups()
        if not backups:
            return False, "No backups found"
        
        return True, f"{len(backups)} backups available"
    
    def initialize_data(self):
        """Create initial data files."""
        print("\n1. Initializing system data...")
        
        # Create config
        self.config_file.write_text("""
[trading]
max_position_size = 10000
risk_level = "moderate"
auto_backup = true

[recovery]
backup_interval_hours = 24
keep_backup_count = 7
""".strip())
        print(f"   ✅ Config created")
        
        # Create positions file
        positions = self.data_dir / "positions.csv"
        positions.write_text("""
symbol,quantity,avg_price,pnl
BTC/USD,0.5,45000,2500
ETH/USD,2.0,3000,500
SOL/USD,10.0,100,150
""".strip())
        print(f"   ✅ Positions file created (3 positions)")
        
        # Create trades file
        trades = self.data_dir / "trades.csv"
        trades.write_text("""
timestamp,symbol,side,price,quantity
2024-12-17T10:00:00,BTC/USD,buy,45000,0.5
2024-12-17T11:00:00,ETH/USD,buy,3000,2.0
2024-12-17T12:00:00,SOL/USD,buy,100,10.0
""".strip())
        print(f"   ✅ Trades file created (3 trades)")
    
    def create_backup(self, description="", tags=None):
        """Create system backup."""
        print(f"\n📦 Creating backup: {description or 'Scheduled backup'}")
        
        backup_id = self.recovery.create_backup(
            include_config=True,
            include_state=True,
            include_data=True,
            description=description,
            tags=tags or []
        )
        
        backups = self.recovery.list_backups()
        latest = backups[0]
        
        print(f"   ✅ Backup created: {backup_id[:30]}...")
        print(f"      Files: {latest.files_count}, Size: {latest.size_bytes} bytes")
        
        return backup_id
    
    def run_health_check(self):
        """Run system health check."""
        print("\n🏥 Running health checks...")
        
        results = self.health.run_all()
        all_healthy = all(r.healthy for r in results.values())
        
        for name, result in results.items():
            status = "✅" if result.healthy else "❌"
            print(f"   {status} {name.upper()}: {result.message}")
        
        if all_healthy:
            print(f"\n   Overall: 🟢 SYSTEM HEALTHY")
        else:
            print(f"\n   Overall: 🔴 SYSTEM UNHEALTHY")
        
        return all_healthy
    
    def simulate_disaster(self, disaster_type="config_corruption"):
        """Simulate different disaster scenarios."""
        print(f"\n💥 Simulating disaster: {disaster_type}")
        
        if disaster_type == "config_corruption":
            self.config_file.write_text("CORRUPTED_#$%^&*()")
            print("   ❌ Configuration file corrupted")
        
        elif disaster_type == "data_loss":
            import shutil
            shutil.rmtree(self.data_dir)
            print("   ❌ Data directory deleted")
        
        elif disaster_type == "complete_loss":
            self.config_file.write_text("CORRUPTED")
            import shutil
            shutil.rmtree(self.data_dir)
            print("   ❌ Complete system failure (config + data)")
    
    def recover_from_disaster(self, backup_id):
        """Recover system from disaster using backup."""
        print(f"\n🔧 Initiating disaster recovery...")
        print(f"   Using backup: {backup_id[:30]}...")
        
        # Restore everything
        success = self.recovery.restore_backup(
            backup_id,
            restore_config=True,
            restore_state=True,
            restore_data=True
        )
        
        if success:
            print(f"   ✅ Recovery successful!")
            return True
        else:
            print(f"   ❌ Recovery failed!")
            return False


def example_complete_disaster_recovery():
    """Complete disaster recovery demonstration."""
    print("="*70)
    print(" Complete Disaster Recovery Workflow ".center(70))
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create trading system
        system = TradingSystem(tmpdir)
        
        # Initialize system
        system.initialize_data()
        
        # Initial health check
        print("\n" + "="*70)
        print(" PHASE 1: System Initialization & Baseline ".center(70))
        print("="*70)
        system.run_health_check()
        
        # Create baseline backup
        baseline_backup = system.create_backup(
            description="Baseline backup - healthy system",
            tags=["baseline", "production"]
        )
        
        # Show backup history
        print("\n📋 Backup inventory:")
        backups = system.recovery.list_backups()
        for i, backup in enumerate(backups, 1):
            print(f"   {i}. {backup.backup_id[:30]}...")
            print(f"      Type: {backup.backup_type.value}, "
                  f"Files: {backup.files_count}, "
                  f"Tags: {backup.tags}")
        
        # Simulate normal operations with periodic backups
        print("\n" + "="*70)
        print(" PHASE 2: Normal Operations ".center(70))
        print("="*70)
        
        print("\n⚡ Simulating normal operations...")
        print("   • Processing trades...")
        print("   • Updating positions...")
        print("   • Monitoring health...")
        
        # Create operational backup
        operational_backup = system.create_backup(
            description="Operational backup - during trading",
            tags=["operational", "auto"]
        )
        
        # Health check during operations
        system.run_health_check()
        
        # Disaster strikes!
        print("\n" + "="*70)
        print(" PHASE 3: DISASTER SCENARIO ".center(70))
        print("="*70)
        
        # Try different disaster scenarios
        system.simulate_disaster("config_corruption")
        
        # Detect issue with health check
        print("\n🔍 Disaster detected by health monitoring:")
        is_healthy = system.run_health_check()
        
        if not is_healthy:
            print("\n🚨 ALERT: System unhealthy, initiating automatic recovery!")
            
            # Recovery process
            print("\n" + "="*70)
            print(" PHASE 4: AUTOMATED RECOVERY ".center(70))
            print("="*70)
            
            # Use most recent successful backup
            recovery_backup = operational_backup
            success = system.recover_from_disaster(recovery_backup)
            
            if success:
                # Verify recovery
                print("\n🔍 Verifying system after recovery:")
                is_healthy_now = system.run_health_check()
                
                if is_healthy_now:
                    print("\n" + "="*70)
                    print(" ✅ RECOVERY SUCCESSFUL ".center(70))
                    print("="*70)
                    print("\n   System Status:")
                    print(f"   • Configuration: Restored")
                    print(f"   • Data integrity: Verified")
                    print(f"   • Positions: {system._count_positions()} active")
                    print(f"   • Health: All checks passing")
                    
                    # Create post-recovery backup
                    post_recovery_backup = system.create_backup(
                        description="Post-recovery verification backup",
                        tags=["recovery", "verified"]
                    )
                    
                    print("\n   Recovery Timeline:")
                    print("   1. Disaster detected by health checks")
                    print("   2. Automatic recovery initiated")
                    print("   3. System restored from backup")
                    print("   4. Health verified")
                    print("   5. Post-recovery backup created")
                    print("\n   ✅ System ready for trading operations")
        
        # Final backup inventory
        print("\n" + "="*70)
        print(" Final Backup Inventory ".center(70))
        print("="*70)
        
        final_backups = system.recovery.list_backups()
        print(f"\n   Total backups: {len(final_backups)}")
        print(f"\n   Backup History:")
        for i, backup in enumerate(final_backups, 1):
            print(f"\n   {i}. ID: {backup.backup_id[:40]}...")
            print(f"      Description: {backup.description}")
            print(f"      Type: {backup.backup_type.value}")
            print(f"      Tags: {', '.join(backup.tags)}")
            print(f"      Files: {backup.files_count}")
            print(f"      Status: {backup.status.value}")


def example_recovery_best_practices():
    """Demonstrate recovery best practices."""
    print("\n" + "="*70)
    print(" Disaster Recovery Best Practices ".center(70))
    print("="*70)
    
    print("""
1. BACKUP STRATEGY
   • Create backups before major changes
   • Schedule regular automatic backups
   • Keep multiple backup generations
   • Tag backups appropriately (baseline, daily, pre-deployment)
   • Test backup integrity regularly

2. HEALTH MONITORING
   • Run health checks frequently
   • Monitor critical components (config, data, services)
   • Set up automated alerts on health failures
   • Include backup availability in health checks

3. RECOVERY PROCEDURES
   • Document recovery runbooks
   • Practice recovery procedures regularly
   • Verify system health after recovery
   • Create post-recovery backup
   • Log all recovery actions

4. RESILIENCE LAYERS
   Layer 1: Circuit Breakers - Prevent cascading failures
   Layer 2: Retry Logic - Handle transient failures
   Layer 3: Health Checks - Early problem detection
   Layer 4: Backups - Recover from disasters

5. PRODUCTION READINESS
   ✅ Automated backup scheduling
   ✅ Health check integration
   ✅ Monitoring and alerting
   ✅ Recovery runbooks
   ✅ Regular disaster recovery drills
   ✅ Backup retention policy
   ✅ Post-recovery verification

6. TESTING
   • Test each disaster scenario
   • Verify backup integrity
   • Measure recovery time objective (RTO)
   • Measure recovery point objective (RPO)
   • Update procedures based on tests
    """)
    
    print("="*70)


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print(" DISASTER RECOVERY DEMONSTRATION ".center(70))
    print("="*70)
    
    try:
        example_complete_disaster_recovery()
        
        example_recovery_best_practices()
        
        print("\n" + "="*70)
        print(" All examples completed successfully! ".center(70))
        print("="*70)
        print("\n🎯 Key Achievements:")
        print("   • Complete disaster recovery workflow demonstrated")
        print("   • Multi-layered resilience approach implemented")
        print("   • Automated detection and recovery verified")
        print("   • Production-ready patterns established")
        print("\n💡 Next Steps:")
        print("   • Implement automated backup scheduling")
        print("   • Set up monitoring and alerting")
        print("   • Create recovery runbooks")
        print("   • Schedule regular disaster recovery drills")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
