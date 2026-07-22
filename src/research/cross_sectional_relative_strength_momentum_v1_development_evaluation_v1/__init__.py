"""CS RS momentum v1 development-evaluation entry-point package."""

from __future__ import annotations

from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.constants_v1 import (
    OWNER_SURFACE,
    PACKAGE_MARKER,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.entry_point_v1 import (
    run_preflight_only,
    validate_repo_entry_point,
)

__all__ = [
    "OWNER_SURFACE",
    "PACKAGE_MARKER",
    "run_preflight_only",
    "validate_repo_entry_point",
]
