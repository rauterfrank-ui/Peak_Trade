#!/usr/bin/env python3
"""
Example 1: Circuit Breaker Basics
==================================
Demonstrates basic circuit breaker usage to prevent cascading failures.

This example shows:
- How to use the circuit breaker decorator
- Circuit breaker states (CLOSED, OPEN, HALF_OPEN)
- Automatic recovery after timeout
- Monitoring circuit breaker statistics
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.resilience import CircuitBreaker, CircuitState

def example_1_basic_circuit_breaker():
    """Basic circuit breaker protecting a function."""
    print("="*60)
    print("Example 1: Basic Circuit Breaker")
    print("="*60)
    
    # Create circuit breaker
    breaker = CircuitBreaker(
        failure_threshold=3,      # Open after 3 failures
        recovery_timeout=5.0,     # Try recovery after 5 seconds
        name="example_breaker"
    )
    
    # Track call attempts
    call_count = [0]
    
    @breaker.call
    def unstable_service():
        """Simulated service that fails first 3 times."""
        call_count[0] += 1
        print(f"\n  Call #{call_count[0]}")
        
        if call_count[0] <= 3:
            print(f"  ❌ Service failed")
            raise Exception("Service unavailable")
        
        print(f"  ✅ Service succeeded")
        return "success"
    
    print("\n1. Circuit starts in CLOSED state:")
    print(f"   State: {breaker.state.value}")
    
    print("\n2. Making calls that will fail:")
    for i in range(3):
        try:
            unstable_service()
        except Exception as e:
            print(f"   Caught: {e}")
    
    print(f"\n3. After {breaker.failure_threshold} failures:")
    print(f"   State: {breaker.state.value}")
    print(f"   Failures: {breaker.stats.failure_count}")
    
    print("\n4. Circuit is now OPEN - calls fail immediately:")
    try:
        unstable_service()
    except Exception as e:
        print(f"   ⚡ Fast fail: {e}")
    
    print(f"\n5. Waiting {breaker.recovery_timeout}s for recovery timeout...")
    time.sleep(breaker.recovery_timeout + 0.5)
    
    print("\n6. After timeout, circuit enters HALF_OPEN state:")
    print("   One test call is allowed through...")
    
    try:
        result = unstable_service()
        print(f"   ✅ Call succeeded: {result}")
        print(f"   State: {breaker.state.value} (recovered!)")
    except Exception as e:
        print(f"   ❌ Recovery failed: {e}")
        print(f"   State: {breaker.state.value}")
    
    print("\n7. Statistics:")
    print(f"   Total failures: {breaker.stats.failure_count}")
    print(f"   Total successes: {breaker.stats.success_count}")
    print(f"   State changes: {breaker.stats.state_changes}")
    print("="*60)


def example_2_decorator_pattern():
    """Using circuit breaker as a decorator."""
    print("\n" + "="*60)
    print("Example 2: Decorator Pattern")
    print("="*60)
    
    from src.core.resilience import circuit_breaker
    
    call_count = [0]
    
    @circuit_breaker(
        failure_threshold=2,
        recovery_timeout=3.0,
        name="api_breaker"
    )
    def call_api():
        """Simulated API call."""
        call_count[0] += 1
        print(f"\n  API call #{call_count[0]}")
        
        if call_count[0] <= 2:
            raise ConnectionError("API connection failed")
        
        return {"status": "ok", "data": [1, 2, 3]}
    
    print("\n1. Making API calls with circuit breaker protection:")
    
    for i in range(4):
        try:
            result = call_api()
            print(f"   ✅ Success: {result}")
        except Exception as e:
            print(f"   ❌ Error: {type(e).__name__}: {e}")
        
        time.sleep(0.5)
    
    print("="*60)


def example_3_manual_reset():
    """Manually resetting circuit breaker."""
    print("\n" + "="*60)
    print("Example 3: Manual Reset")
    print("="*60)
    
    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=60.0,  # Long timeout
        name="manual_reset_breaker"
    )
    
    @breaker.call
    def flaky_operation():
        raise Exception("Operation failed")
    
    print("\n1. Causing failures to open circuit:")
    for _ in range(2):
        try:
            flaky_operation()
        except Exception:
            pass
    
    print(f"   State: {breaker.state.value}")
    print(f"   Recovery timeout: {breaker.recovery_timeout}s")
    
    print("\n2. Manually resetting circuit (no need to wait):")
    breaker.reset()
    print(f"   State after reset: {breaker.state.value}")
    print(f"   Failure count: {breaker.stats.failure_count}")
    print("   ✅ Circuit ready for new attempts")
    
    print("="*60)


def example_4_monitoring_stats():
    """Monitoring circuit breaker statistics."""
    print("\n" + "="*60)
    print("Example 4: Monitoring Statistics")
    print("="*60)
    
    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=2.0,
        name="monitored_breaker"
    )
    
    call_count = [0]
    
    @breaker.call
    def monitored_service():
        call_count[0] += 1
        # Fail every 3rd call
        if call_count[0] % 3 == 0:
            raise Exception("Intermittent failure")
        return "ok"
    
    print("\n1. Making multiple calls with intermittent failures:")
    
    for i in range(8):
        try:
            result = monitored_service()
            print(f"   Call #{i+1}: ✅ {result}")
        except Exception as e:
            print(f"   Call #{i+1}: ❌ {e}")
        
        # Print stats
        stats = breaker.stats
        print(f"      Stats: Success={stats.success_count}, "
              f"Fail={stats.failure_count}, "
              f"State={breaker.state.value}")
        
        time.sleep(0.2)
    
    print("\n2. Final Statistics:")
    print(f"   Total Successes: {breaker.stats.success_count}")
    print(f"   Total Failures: {breaker.stats.failure_count}")
    print(f"   State Changes: {breaker.stats.state_changes}")
    print(f"   Last Failure Time: {breaker.stats.last_failure_time}")
    print(f"   Last Success Time: {breaker.stats.last_success_time}")
    
    print("="*60)


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print(" Circuit Breaker Basics Examples".center(70))
    print("="*70)
    
    try:
        example_1_basic_circuit_breaker()
        time.sleep(1)
        
        example_2_decorator_pattern()
        time.sleep(1)
        
        example_3_manual_reset()
        time.sleep(1)
        
        example_4_monitoring_stats()
        
        print("\n" + "="*70)
        print(" All examples completed successfully! ".center(70))
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
