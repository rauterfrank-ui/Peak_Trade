"""
Peak_Trade Health Check API Endpoints
====================================
REST endpoints for health monitoring and system diagnostics.

Endpoints:
- GET /health: Basic health status (200 OK if healthy)
- GET /health/detailed: Detailed diagnostics with all checks

Usage with FastAPI:
    from fastapi import FastAPI
    from src.webui.health_endpoint import router

    app = FastAPI()
    app.include_router(router)
"""

import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from src.core.resilience import health_check
from src.core.metrics import metrics

logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/health", tags=["health"])


def get_utc_now() -> datetime:
    """Get current UTC time."""
    if hasattr(datetime, "UTC"):
        return datetime.now(datetime.UTC)
    else:
        return datetime.utcnow()


@router.get("")
async def health_basic() -> JSONResponse:
    """
    Basic health check endpoint.

    Returns 200 OK if system is healthy, 503 Service Unavailable otherwise.

    Returns:
        JSON response with basic health status

    Example Response:
        {
            "status": "healthy",
            "timestamp": "2024-12-20T05:47:00.000Z"
        }
    """
    try:
        is_healthy = health_check.is_system_healthy()

        response = {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": get_utc_now().isoformat(),
        }

        status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(content=response, status_code=status_code)

    except Exception as e:
        logger.error(f"Health check failed with exception: {e}", exc_info=True)
        return JSONResponse(
            content={"status": "error", "message": str(e), "timestamp": get_utc_now().isoformat()},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@router.get("/detailed")
async def health_detailed() -> JSONResponse:
    """
    Detailed health check endpoint with diagnostics.

    Returns comprehensive health information including:
    - Individual check results
    - System metrics summary
    - Check statistics

    Returns:
        JSON response with detailed health diagnostics

    Example Response:
        {
            "healthy": true,
            "timestamp": "2024-12-20T05:47:00.000Z",
            "checks": {
                "database": {
                    "healthy": true,
                    "message": "Database is operational",
                    "timestamp": "2024-12-20T05:47:00.000Z"
                }
            },
            "summary": {
                "total": 5,
                "passed": 5,
                "failed": 0
            },
            "metrics": {
                ...
            }
        }
    """
    try:
        # Get comprehensive health status
        health_status = health_check.get_status()

        # Add metrics summary if available
        try:
            metrics_summary = metrics.get_summary()
            health_status["metrics"] = metrics_summary
        except Exception as e:
            logger.warning(f"Failed to get metrics summary: {e}")
            health_status["metrics"] = {"error": str(e)}

        # Add system information
        health_status["system"] = {
            "resilience_enabled": True,
            "circuit_breakers_active": _count_circuit_breakers(),
            "rate_limiters_active": _count_rate_limiters(),
        }

        status_code = (
            status.HTTP_200_OK if health_status["healthy"] else status.HTTP_503_SERVICE_UNAVAILABLE
        )

        return JSONResponse(content=health_status, status_code=status_code)

    except Exception as e:
        logger.error(f"Detailed health check failed: {e}", exc_info=True)
        return JSONResponse(
            content={"healthy": False, "error": str(e), "timestamp": get_utc_now().isoformat()},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@router.get("/metrics")
async def health_metrics() -> JSONResponse:
    """
    Metrics endpoint for monitoring.

    Returns current metrics in JSON format.
    Can be used by monitoring systems or for debugging.

    Returns:
        JSON response with current metrics
    """
    try:
        metrics_data = metrics.get_summary()

        # Add snapshot data
        snapshots = metrics.get_snapshots(limit=50)
        metrics_data["recent_snapshots"] = snapshots

        return JSONResponse(content=metrics_data, status_code=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}", exc_info=True)
        return JSONResponse(
            content={"error": str(e), "timestamp": get_utc_now().isoformat()},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/prometheus")
async def health_prometheus():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format for scraping.

    Returns:
        Response with Prometheus metrics
    """
    try:
        content, content_type = metrics.export_prometheus()

        return JSONResponse(
            content=content.decode("utf-8") if isinstance(content, bytes) else content,
            media_type=content_type,
            status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Failed to export Prometheus metrics: {e}", exc_info=True)
        return JSONResponse(
            content=f"# Error exporting metrics: {str(e)}\n",
            media_type="text/plain; charset=utf-8",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _count_circuit_breakers() -> int:
    """Count active circuit breakers."""
    from ..core.resilience_helpers import get_all_circuit_breakers

    return len(get_all_circuit_breakers())


def _count_rate_limiters() -> int:
    """Count active rate limiters."""
    from ..core.resilience_helpers import get_all_rate_limiters

    return len(get_all_rate_limiters())


# Health check registration helper
def register_standard_checks():
    """
    Register standard health checks for the system.

    This should be called during application startup to register
    all necessary health checks.
    """

    def check_metrics_system():
        """Check if metrics system is operational."""
        try:
            metrics.get_summary()
            return True, "Metrics system operational"
        except Exception as e:
            return False, f"Metrics system error: {str(e)}"

    def check_resilience_system():
        """Check if resilience system is operational."""
        try:
            # Basic check that resilience module is loaded
            from src.core import resilience

            return True, "Resilience system operational"
        except Exception as e:
            return False, f"Resilience system error: {str(e)}"

    # Register checks
    health_check.register("metrics", check_metrics_system)
    health_check.register("resilience", check_resilience_system)

    logger.info("Standard health checks registered")


__all__ = [
    "router",
    "register_standard_checks",
]
