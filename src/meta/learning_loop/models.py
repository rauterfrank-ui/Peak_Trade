"""
Core data models for the Learning Loop v0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PatchStatus(str, Enum):
    """Status of a configuration patch in the Learning Loop lifecycle."""

    PROPOSED = "PROPOSED"  # Initial recommendation from Learning Loop
    APPLIED_OFFLINE = "APPLIED_OFFLINE"  # Applied in offline/research environment
    PROMOTED = "PROMOTED"  # Approved for live consideration
    REJECTED = "REJECTED"  # Rejected by governance or operator
    RETIRED = "RETIRED"  # No longer relevant


@dataclass
class ConfigPatch:
    """
    Represents a proposed or applied configuration change from the Learning Loop.

    A ConfigPatch encapsulates a single atomic change to a configuration parameter,
    along with metadata about its origin, justification, and lifecycle status.
    """

    id: str
    target: str  # Configuration path (e.g., "portfolio.leverage" or "strategy.trigger_delay")
    old_value: Any
    new_value: Any
    status: PatchStatus = PatchStatus.PROPOSED

    # Metadata
    generated_at: datetime | None = None
    applied_at: datetime | None = None
    promoted_at: datetime | None = None

    # Justification / provenance
    reason: str | None = None
    source_experiment_id: str | None = None
    confidence_score: float | None = None

    # Additional context
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure generated_at is set if not provided."""
        if self.generated_at is None:
            self.generated_at = datetime.utcnow()
