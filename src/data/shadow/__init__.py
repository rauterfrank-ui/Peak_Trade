"""
Shadow Trading Data Pipeline — Phase 2: Tick→OHLCV + Quality Monitoring.

KRITISCH: NIEMALS im Live-Modus laufen lassen.
Defense in Depth: Config, Runtime, Import Guards.
"""

from __future__ import annotations

from src.data.shadow._guards import (
    ShadowLiveForbidden,
    ShadowPipelineDisabled,
    check_import_guard,
    check_runtime_guard,
)
from src.data.shadow.models import Bar, Tick

# Import Guard: prüft beim Laden des Moduls
check_import_guard()

__all__ = [
    "Tick",
    "Bar",
    "ShadowPipelineDisabled",
    "ShadowLiveForbidden",
    "check_runtime_guard",
]
