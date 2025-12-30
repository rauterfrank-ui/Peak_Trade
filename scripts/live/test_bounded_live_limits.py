#!/usr/bin/env python3
"""
Test Bounded-Live Limits Configuration

Verifies that bounded-live limits are correctly configured and enforced.
This script should be run BEFORE enabling live trading.

Usage:
    python scripts/live/test_bounded_live_limits.py
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add src to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "src"))

from core.peak_config import load_config
from live.risk_limits import LiveRiskLimits, LiveOrderRequest, LiveRiskCheckResult


def test_bounded_live_config() -> Tuple[bool, List[str]]:
    """Test bounded-live configuration."""
    errors = []

    print("\n" + "=" * 70)
    print("BOUNDED-LIVE CONFIGURATION TEST")
    print("=" * 70 + "\n")

    # Load config
    try:
        config = load_config()
        print("✅ Config loaded successfully")
    except Exception as e:
        errors.append(f"Failed to load config: {e}")
        return False, errors

    # Check bounded_live section exists
    if "bounded_live" not in config:
        errors.append("bounded_live section missing from config")
        return False, errors

    bounded_cfg = config["bounded_live"]
    print("✅ bounded_live section found in config\n")

    # Check enabled
    if not bounded_cfg.get("enabled", False):
        errors.append("bounded_live.enabled = false (should be true)")
        return False, errors

    print("✅ bounded_live.enabled = true")

    # Check limits exist
    limits = bounded_cfg.get("limits", {})
    if not limits:
        errors.append("bounded_live.limits section missing")
        return False, errors

    # Verify critical limits
    critical_limits = {
        "max_order_notional": 50.0,
        "max_total_notional": 500.0,
        "max_open_positions": 2,
        "max_daily_loss_abs": 100.0,
    }

    print("\nBounded-Live Limits:")
    print("-" * 50)

    for limit_name, expected_max in critical_limits.items():
        actual = limits.get(limit_name)
        if actual is None:
            errors.append(f"{limit_name} not configured")
            print(f"❌ {limit_name}: MISSING")
        elif actual > expected_max:
            errors.append(f"{limit_name} = {actual} exceeds Phase 1 maximum of {expected_max}")
            print(f"⚠️  {limit_name}: ${actual:.2f} (exceeds Phase 1 max: ${expected_max:.2f})")
        else:
            print(f"✅ {limit_name}: ${actual:.2f}")

    # Check enforcement
    enforcement = bounded_cfg.get("enforcement", {})
    print("\nEnforcement Settings:")
    print("-" * 50)

    enforce_checks = {
        "enforce_limits": (True, "MUST be true"),
        "allow_override": (False, "MUST be false in Phase 1"),
        "block_on_violation": (True, "MUST be true"),
    }

    for check_name, (expected, description) in enforce_checks.items():
        actual = enforcement.get(check_name)
        if actual != expected:
            errors.append(f"{check_name} = {actual}, but {description}")
            print(f"❌ {check_name}: {actual} ({description})")
        else:
            print(f"✅ {check_name}: {actual}")

    return len(errors) == 0, errors


def test_live_risk_limits_integration() -> Tuple[bool, List[str]]:
    """Test LiveRiskLimits integration with bounded-live config."""
    errors = []

    print("\n" + "=" * 70)
    print("LIVE RISK LIMITS INTEGRATION TEST")
    print("=" * 70 + "\n")

    try:
        config = load_config()
        limits = LiveRiskLimits.from_config(config, starting_cash=2000.0)
        print("✅ LiveRiskLimits instantiated successfully\n")
    except Exception as e:
        errors.append(f"Failed to create LiveRiskLimits: {e}")
        return False, errors

    # Test 1: Small order (should pass)
    print("Test 1: Small order ($30) - SHOULD PASS")
    print("-" * 50)
    order = LiveOrderRequest(
        symbol="BTC-EUR",
        side="buy",
        quantity=0.0006,
        price=50000.0,
        notional=30.0,
    )
    result = limits.check_orders([order])

    if result.allowed:
        print(f"✅ Small order ALLOWED (notional: ${result.metrics.get('total_notional', 0):.2f})")
    else:
        errors.append(f"Small order BLOCKED (should pass): {result.reasons}")
        print(f"❌ Small order BLOCKED: {result.reasons}")

    # Test 2: Large order (should fail)
    print("\nTest 2: Large order ($100) - SHOULD FAIL")
    print("-" * 50)
    order_large = LiveOrderRequest(
        symbol="BTC-EUR",
        side="buy",
        quantity=0.002,
        price=50000.0,
        notional=100.0,
    )
    result_large = limits.check_orders([order_large])

    if not result_large.allowed:
        print(f"✅ Large order BLOCKED as expected")
        print(f"   Reason: {result_large.reasons[0] if result_large.reasons else 'Unknown'}")
    else:
        errors.append("Large order ALLOWED (should fail in bounded-live)")
        print(f"❌ Large order ALLOWED (should be blocked!)")

    # Test 3: Multiple orders exceeding total limit
    print("\nTest 3: Multiple orders ($40 + $40 = $80) - SHOULD PASS")
    print("-" * 50)
    orders_multi = [
        LiveOrderRequest(
            symbol="BTC-EUR", side="buy", quantity=0.0008, price=50000.0, notional=40.0
        ),
        LiveOrderRequest(symbol="ETH-EUR", side="buy", quantity=0.02, price=2000.0, notional=40.0),
    ]
    result_multi = limits.check_orders(orders_multi)

    if result_multi.allowed:
        print(
            f"✅ Multiple orders ALLOWED (total: ${result_multi.metrics.get('total_notional', 0):.2f})"
        )
    else:
        errors.append(f"Multiple orders BLOCKED (should pass): {result_multi.reasons}")
        print(f"❌ Multiple orders BLOCKED: {result_multi.reasons}")

    # Test 4: Total exposure exceeding limit
    print("\nTest 4: Excessive total exposure ($300 + $300 = $600) - SHOULD FAIL")
    print("-" * 50)
    orders_excessive = [
        LiveOrderRequest(
            symbol="BTC-EUR", side="buy", quantity=0.006, price=50000.0, notional=300.0
        ),
        LiveOrderRequest(symbol="ETH-EUR", side="buy", quantity=0.15, price=2000.0, notional=300.0),
    ]
    result_excessive = limits.check_orders(orders_excessive)

    if not result_excessive.allowed:
        print(f"✅ Excessive exposure BLOCKED as expected")
        print(
            f"   Reason: {result_excessive.reasons[0] if result_excessive.reasons else 'Unknown'}"
        )
    else:
        errors.append("Excessive exposure ALLOWED (should fail)")
        print(f"❌ Excessive exposure ALLOWED (should be blocked!)")

    return len(errors) == 0, errors


def main():
    """Run all tests."""
    print("\n" + "#" * 70)
    print("# BOUNDED-LIVE LIMITS TEST SUITE")
    print("#" * 70)

    all_passed = True
    all_errors = []

    # Test 1: Config
    passed, errors = test_bounded_live_config()
    all_passed = all_passed and passed
    all_errors.extend(errors)

    # Test 2: Integration
    passed, errors = test_live_risk_limits_integration()
    all_passed = all_passed and passed
    all_errors.extend(errors)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70 + "\n")

    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nBounded-Live configuration is READY for live trading.")
        print("\nNext steps:")
        print("1. Review docs/runbooks/LIVE_MODE_TRANSITION_RUNBOOK.md")
        print("2. Complete pre-transition checklist")
        print("3. Obtain all required sign-offs")
        print("4. Execute transition procedure")
        return 0
    else:
        print("❌ TESTS FAILED")
        print(f"\nFound {len(all_errors)} error(s):\n")
        for i, error in enumerate(all_errors, 1):
            print(f"{i}. {error}")
        print("\n⚠️  DO NOT proceed with live trading until all errors are resolved!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
