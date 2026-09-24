"""Versioned parameter authority surface for research stratification v2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    sha256_hex,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.constants_v2 import (
    AUTHORITY_STATUS_RATIFIED,
    AUTHORITY_STATUS_UNSET,
    RESEARCH_STRATIFICATION_CONTRACT_VERSION,
)

PARAMETER_NAMES: tuple[str, ...] = (
    "research_mark_path_lookback_observations",
    "market_state_realized_vol_low_threshold",
    "market_state_realized_vol_high_threshold",
    "volatility_stratum_low_threshold",
    "volatility_stratum_high_threshold",
    "minimum_mark_path_observations",
)


@dataclass(frozen=True)
class ParameterAuthorityEntryV2:
    name: str
    value: Any
    unit: str
    semantic_purpose: str
    authority_source: str
    authority_status: str
    contract_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_source": self.authority_source,
            "authority_status": self.authority_status,
            "contract_version": self.contract_version,
            "name": self.name,
            "semantic_purpose": self.semantic_purpose,
            "unit": self.unit,
            "value": self.value,
        }


def build_production_parameter_authority_surface_v2() -> tuple[ParameterAuthorityEntryV2, ...]:
    """Production surface — all numeric authority UNSET (no silent defaults)."""
    entries: list[ParameterAuthorityEntryV2] = []
    for name in PARAMETER_NAMES:
        entries.append(
            ParameterAuthorityEntryV2(
                name=name,
                value=None,
                unit="UNSET",
                semantic_purpose=f"research_stratification_v2:{name}",
                authority_source="OWNER_RATIFICATION_REQUIRED",
                authority_status=AUTHORITY_STATUS_UNSET,
                contract_version=RESEARCH_STRATIFICATION_CONTRACT_VERSION,
            )
        )
    return tuple(entries)


def parameter_authority_digest_v2(
    entries: Sequence[ParameterAuthorityEntryV2],
) -> str:
    payload = {"contract_version": RESEARCH_STRATIFICATION_CONTRACT_VERSION, "parameters": []}
    for entry in sorted(entries, key=lambda e: e.name):
        payload["parameters"].append(entry.to_dict())
    return sha256_hex(payload)


def parameter_authority_complete_v2(entries: Sequence[ParameterAuthorityEntryV2]) -> bool:
    for entry in entries:
        if entry.authority_status != AUTHORITY_STATUS_RATIFIED:
            return False
        if entry.value is None:
            return False
    return True


def entries_as_map(
    entries: Sequence[ParameterAuthorityEntryV2],
) -> Mapping[str, ParameterAuthorityEntryV2]:
    return {e.name: e for e in entries}


def verify_parameter_digest_v2(
    *,
    entries: Sequence[ParameterAuthorityEntryV2],
    expected_digest: str,
) -> bool:
    return parameter_authority_digest_v2(entries) == expected_digest
