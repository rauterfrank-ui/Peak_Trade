"""Immutable DTO for explicit naked-L6 D_t proposals (transport only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from src.ops.p4_l6_explicit_d_t_proposal_v1.constants_v1 import SCHEMA_VERSION


@dataclass(frozen=True)
class ExplicitDtProposalV1:
    """External explicit D_t proposal. Does not imply formula authority."""

    value: float
    producer_id: str
    instrument_id: str
    venue: str
    venue_instrument_id: str
    observation_lineage_id: str
    proposal_id: str
    schema_version: str = SCHEMA_VERSION
    parameter_provenance: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": float(self.value),
            "producer_id": self.producer_id,
            "instrument_id": self.instrument_id,
            "venue": self.venue,
            "venue_instrument_id": self.venue_instrument_id,
            "observation_lineage_id": self.observation_lineage_id,
            "proposal_id": self.proposal_id,
            "schema_version": self.schema_version,
            "parameter_provenance": dict(self.parameter_provenance),
        }


@dataclass(frozen=True)
class P4ExplicitDtProposalIdentityContextV1:
    """Expected P4 L1-aligned instrument identity (O1 adjudicated)."""

    instrument_id: str
    venue: str
    venue_instrument_id: str


@dataclass(frozen=True)
class ExplicitDtProposalValidationResultV1:
    ok: bool
    failure_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExplicitDtProposalTransportResultV1:
    ok: bool
    proposed_d_t: float | None
    failure_codes: tuple[str, ...] = ()
