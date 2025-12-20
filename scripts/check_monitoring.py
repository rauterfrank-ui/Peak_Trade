#!/usr/bin/env python3
"""
Monitoring Health Check Script
===============================
Checks if all monitoring services are running and accessible.
"""

import requests
import sys


def check_service(name: str, url: str) -> bool:
    """
    Check if a service is healthy.
    
    Args:
        name: Service name
        url: Health check URL
        
    Returns:
        True if healthy, False otherwise
    """
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name}: OK")
            return True
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name}: {e}")
        return False


def main():
    """Main function."""
    print("Checking monitoring services...\n")
    
    services = {
        "Prometheus": "http://localhost:9091/-/healthy",
        "Grafana": "http://localhost:3000/api/health",
        "AlertManager": "http://localhost:9093/-/healthy"
    }
    
    all_healthy = all(check_service(name, url) for name, url in services.items())
    
    print()
    if all_healthy:
        print("✅ All monitoring services are healthy")
        return 0
    else:
        print("❌ Some monitoring services are unhealthy")
        return 1


if __name__ == "__main__":
    sys.exit(main())
