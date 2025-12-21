#!/usr/bin/env python3
"""
Example 6: Combining Circuit Breaker and Retry Patterns
========================================================
Demonstrates combining circuit breaker with retry logic for maximum resilience.

This example shows:
- Stacking decorators correctly
- Circuit breaker preventing unnecessary retries
- Optimal configuration for combined patterns
- Real-world failure scenarios
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.resilience import circuit_breaker, retry_with_backoff, CircuitBreaker


def example_1_basic_combination():
    """Basic combination of circuit breaker and retry."""
    print("=" * 60)
    print("Example 1: Basic Combination")
    print("=" * 60)

    call_count = [0]

    @circuit_breaker(failure_threshold=5, recovery_timeout=10.0, name="combined_cb")
    @retry_with_backoff(max_attempts=3, base_delay=0.5, exponential=True)
    def resilient_api_call():
        """API call with retry and circuit breaker protection."""
        call_count[0] += 1
        print(f"  Attempt #{call_count[0]}")

        # Fail first 2 attempts (will be retried)
        if call_count[0] <= 2:
            raise ConnectionError("Transient network error")

        return {"status": "success", "data": "Hello"}

    print("\n1. Calling API with combined protection:")
    print("   - Retry will attempt up to 3 times")
    print("   - Circuit breaker monitors overall failures")

    try:
        result = resilient_api_call()
        print(f"\n  ✅ Success: {result}")
        print(f"  Total attempts: {call_count[0]}")
    except Exception as e:
        print(f"\n  ❌ Failed: {e}")

    print("=" * 60)


def example_2_decorator_order_matters():
    """Demonstrating why decorator order matters."""
    print("\n" + "=" * 60)
    print("Example 2: Decorator Order Matters")
    print("=" * 60)

    print("\n1. CORRECT ORDER (Circuit Breaker OUTER, Retry INNER):")
    print("   @circuit_breaker")
    print("   @retry_with_backoff")
    print("   def function():")
    print()
    print("   Benefits:")
    print("   - Circuit breaker sees aggregate failures")
    print("   - When circuit opens, retries are skipped (fail fast)")
    print("   - More efficient - stops unnecessary retry attempts")

    print("\n2. WRONG ORDER (Retry OUTER, Circuit Breaker INNER):")
    print("   @retry_with_backoff")
    print("   @circuit_breaker")
    print("   def function():")
    print()
    print("   Problems:")
    print("   - Retry wraps circuit breaker exceptions")
    print("   - May retry even when circuit is open")
    print("   - Less efficient")

    print("\n3. Demonstration:")

    # Create shared breaker to show state
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=5.0, name="demo_breaker")

    @breaker.call
    @retry_with_backoff(max_attempts=2, base_delay=0.1)
    def protected_call():
        print(f"    Circuit state: {breaker.state.value}")
        raise Exception("Service error")

    print("\n   Making calls that will fail:")
    for i in range(3):
        try:
            protected_call()
        except Exception:
            print(f"   Call {i + 1}: Failed (expected)")

    print(f"\n   Final circuit state: {breaker.state.value}")
    print("   Circuit opened after threshold, stopping further attempts")

    print("=" * 60)


def example_3_transient_vs_permanent_failures():
    """Handling transient vs permanent failures."""
    print("\n" + "=" * 60)
    print("Example 3: Transient vs Permanent Failures")
    print("=" * 60)

    class PermanentError(Exception):
        """Non-retryable error."""

        pass

    call_count = [0]

    @circuit_breaker(failure_threshold=3, recovery_timeout=5.0, name="smart_cb")
    @retry_with_backoff(
        max_attempts=3,
        base_delay=0.3,
        expected_exception=ConnectionError,  # Only retry ConnectionError
    )
    def smart_api_call(scenario="transient"):
        """API call that handles different failure types."""
        call_count[0] += 1
        print(f"  Attempt #{call_count[0]}")

        if scenario == "transient":
            # Transient error (will be retried)
            if call_count[0] < 2:
                raise ConnectionError("Network blip")
            return "success"

        elif scenario == "permanent":
            # Permanent error (won't be retried)
            raise PermanentError("Invalid API key")

    print("\n1. Transient failure (will retry):")
    call_count[0] = 0
    try:
        result = smart_api_call("transient")
        print(f"  ✅ {result} after {call_count[0]} attempts")
    except Exception as e:
        print(f"  ❌ {e}")

    print("\n2. Permanent failure (no retry):")
    call_count[0] = 0
    try:
        result = smart_api_call("permanent")
        print(f"  ✅ {result}")
    except PermanentError as e:
        print(f"  ❌ Failed immediately (no retry): {e}")
        print(f"  Attempts: {call_count[0]} (not retried as expected)")

    print("=" * 60)


def example_4_realistic_scenario():
    """Realistic scenario with multiple services."""
    print("\n" + "=" * 60)
    print("Example 4: Realistic Multi-Service Scenario")
    print("=" * 60)

    # Shared state
    service_health = {
        "api": {"status": "healthy", "failures": 0},
        "db": {"status": "healthy", "failures": 0},
        "cache": {"status": "healthy", "failures": 0},
    }

    @circuit_breaker(failure_threshold=3, recovery_timeout=5.0, name="api_cb")
    @retry_with_backoff(max_attempts=3, base_delay=0.5)
    def call_api():
        """Call external API."""
        if service_health["api"]["failures"] < 2:
            service_health["api"]["failures"] += 1
            raise ConnectionError("API timeout")
        service_health["api"]["status"] = "healthy"
        return {"data": "api_result"}

    @circuit_breaker(failure_threshold=2, recovery_timeout=3.0, name="db_cb")
    @retry_with_backoff(max_attempts=2, base_delay=0.2)
    def query_database():
        """Query database."""
        if service_health["db"]["failures"] < 1:
            service_health["db"]["failures"] += 1
            raise ConnectionError("DB connection lost")
        service_health["db"]["status"] = "healthy"
        return {"records": [1, 2, 3]}

    @circuit_breaker(failure_threshold=5, recovery_timeout=2.0, name="cache_cb")
    @retry_with_backoff(max_attempts=2, base_delay=0.1)
    def get_from_cache(key):
        """Get value from cache."""
        if service_health["cache"]["failures"] < 1:
            service_health["cache"]["failures"] += 1
            raise ConnectionError("Cache miss")
        service_health["cache"]["status"] = "healthy"
        return f"cached_{key}"

    print("\n1. Processing request with multiple service calls:")

    services = [
        ("API", call_api),
        ("Database", query_database),
        ("Cache", get_from_cache, "user_123"),
    ]

    results = {}
    for service_info in services:
        service_name = service_info[0]
        service_func = service_info[1]
        args = service_info[2:] if len(service_info) > 2 else []

        print(f"\n  Calling {service_name}...")
        try:
            result = service_func(*args)
            results[service_name] = result
            print(f"  ✅ {service_name} succeeded: {result}")
        except Exception as e:
            results[service_name] = None
            print(f"  ❌ {service_name} failed: {e}")

    print("\n2. Service Health Status:")
    for service, health in service_health.items():
        status_emoji = "✅" if health["status"] == "healthy" else "❌"
        print(
            f"  {status_emoji} {service.upper()}: {health['status']} "
            f"(failures: {health['failures']})"
        )

    print("\n3. Request Results:")
    success_count = sum(1 for r in results.values() if r is not None)
    print(f"  Successful: {success_count}/{len(results)}")
    print(f"  Resilience patterns prevented cascading failures")

    print("=" * 60)


def example_5_configuration_guidelines():
    """Best practices for configuring combined patterns."""
    print("\n" + "=" * 60)
    print("Example 5: Configuration Guidelines")
    print("=" * 60)

    print("\n1. RECOMMENDED CONFIGURATIONS:\n")

    print("   A. Critical External API:")
    print("      @circuit_breaker(failure_threshold=5, recovery_timeout=60)")
    print("      @retry_with_backoff(max_attempts=3, base_delay=2.0)")
    print("      - Higher threshold (service may be flaky)")
    print("      - Longer recovery (external service)")
    print("      - Moderate retries with delay")

    print("\n   B. Internal Microservice:")
    print("      @circuit_breaker(failure_threshold=3, recovery_timeout=30)")
    print("      @retry_with_backoff(max_attempts=2, base_delay=0.5)")
    print("      - Lower threshold (should be reliable)")
    print("      - Faster recovery")
    print("      - Fewer, quicker retries")

    print("\n   C. Database Operations:")
    print("      @circuit_breaker(failure_threshold=5, recovery_timeout=45)")
    print("      @retry_with_backoff(max_attempts=3, base_delay=1.0)")
    print("      - Higher threshold (DB should be stable)")
    print("      - Medium recovery time")
    print("      - Standard retry pattern")

    print("\n   D. Fast Cache Operations:")
    print("      @circuit_breaker(failure_threshold=10, recovery_timeout=15)")
    print("      @retry_with_backoff(max_attempts=2, base_delay=0.1)")
    print("      - High threshold (cache failures common)")
    print("      - Quick recovery")
    print("      - Fast, minimal retries")

    print("\n2. TUNING TIPS:")
    print("   - Start conservative, loosen based on metrics")
    print("   - failure_threshold: 3-5 for most services")
    print("   - recovery_timeout: 30-60s typical")
    print("   - max_attempts: 2-3 usually sufficient")
    print("   - base_delay: Match expected recovery time")

    print("=" * 60)


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" Combining Circuit Breaker & Retry Patterns ".center(70))
    print("=" * 70)

    try:
        example_1_basic_combination()
        time.sleep(1)

        example_2_decorator_order_matters()
        time.sleep(1)

        example_3_transient_vs_permanent_failures()
        time.sleep(1)

        example_4_realistic_scenario()
        time.sleep(1)

        example_5_configuration_guidelines()

        print("\n" + "=" * 70)
        print(" All examples completed successfully! ".center(70))
        print("=" * 70)
        print("\nKey Takeaways:")
        print("  1. Always put @circuit_breaker BEFORE @retry_with_backoff")
        print("  2. Circuit breaker provides fast-fail when service is down")
        print("  3. Retry handles transient failures within healthy service")
        print("  4. Together they provide comprehensive resilience")
        print("  5. Configure based on service characteristics")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
