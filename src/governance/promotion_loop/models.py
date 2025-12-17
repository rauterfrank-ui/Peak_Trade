"""
Data models for the Promotion Loop v0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from src.meta.learning_loop.models import ConfigPatch


class DecisionStatus(str, Enum):
    """Governance decision state for a promotion candidate."""

    PENDING = "PENDING"
    REJECTED_BY_POLICY = "REJECTED_BY_POLICY"
    REJECTED_BY_SANITY_CHECK = "REJECTED_BY_SANITY_CHECK"
    ACCEPTED_FOR_PROPOSAL = "ACCEPTED_FOR_PROPOSAL"


@dataclass
class PromotionCandidate:
    """
    Wrapper around a ConfigPatch with additional governance metadata.
    """

    patch: ConfigPatch
    tags: list[str] = field(default_factory=list)
    eligible_for_live: bool = False
    notes: str | None = None
    safety_flags: list[str] = field(default_factory=list)  # P0/P1 safety violations


@dataclass
class PromotionDecision:
    """
    Result of running governance filters on a PromotionCandidate.
    """

    candidate: PromotionCandidate
    status: DecisionStatus
    reasons: list[str] = field(default_factory=list)


@dataclass
class PromotionProposal:
    """
    A collection of accepted candidates bundled into a single promotion unit.
    """

    proposal_id: str
    title: str
    description: str
    decisions: list[PromotionDecision] = field(default_factory=list)

    meta: dict[str, Any] = field(default_factory=dict)
    output_dir: Path | None = None
