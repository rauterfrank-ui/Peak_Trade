"""
Observability Module (P2.2)
===========================
Optional OpenTelemetry integration for tracing and metrics.

Exports:
    is_otel_available: Check if OTel deps are installed
    init_otel: Initialize OpenTelemetry with specified exporter
    get_tracer: Get a tracer instance (real or no-op)
    instrument_lake: Add tracing to LakeClient operations
    OTelHandle: Handle for managing OTel lifecycle
    OTelNotAvailableError: Raised when OTel features are unavailable
"""

from .otel import (
    is_otel_available,
    init_otel,
    get_tracer,
    instrument_lake,
    OTelHandle,
    OTelNotAvailableError,
)

from .ai_telemetry import (
    get_registry as get_ai_telemetry_registry,
    record_action,
    record_decision,
    set_heartbeat,
)

__all__ = [
    "is_otel_available",
    "init_otel",
    "get_tracer",
    "instrument_lake",
    "OTelHandle",
    "OTelNotAvailableError",
    "get_ai_telemetry_registry",
    "record_action",
    "record_decision",
    "set_heartbeat",
]
