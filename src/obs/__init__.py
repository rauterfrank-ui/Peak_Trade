"""Observability helpers (optional).

This package is optional and designed for graceful degradation when dependencies
are missing.
"""

from .otel import (
    OTelHandle,
    OTelNotAvailableError,
    get_tracer,
    init_otel,
    instrument_lake,
    is_otel_available,
)

__all__ = [
    "OTelHandle",
    "OTelNotAvailableError",
    "get_tracer",
    "init_otel",
    "instrument_lake",
    "is_otel_available",
]
