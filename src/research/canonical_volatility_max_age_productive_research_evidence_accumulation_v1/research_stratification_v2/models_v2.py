"""Typed models for research stratification v2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class CmcVolatilityInputProvenanceV2:
    volatility_value: float
    volatility_unit: str
    volatility_horizon_seconds: float
    volatility_estimator: str
    volatility_observation_count: int
    volatility_source_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "volatility_estimator": self.volatility_estimator,
            "volatility_horizon_seconds": self.volatility_horizon_seconds,
            "volatility_observation_count": self.volatility_observation_count,
            "volatility_source_digest": self.volatility_source_digest,
            "volatility_unit": self.volatility_unit,
            "volatility_value": self.volatility_value,
        }


@dataclass(frozen=True)
class ResearchStratificationResultV2:
    research_stratification_version: str
    volatility_regime_stratum_v2: str
    market_state_stratum_v2: str
    stratification_key_v2: str
    stratification_ok: bool
    stratification_blockers: tuple[str, ...]
    input_provenance: Mapping[str, Any]
    parameter_authority_provenance: Mapping[str, Any]
    legacy_regime_label_v1: Optional[str] = None
    legacy_regime_label_is_v1: bool = True

    def to_evidence_fields_v2(self) -> dict[str, Any]:
        status = "CLASSIFIED" if self.stratification_ok else "FAIL_CLOSED"
        return {
            "legacy_regime_label_is_v1": self.legacy_regime_label_is_v1,
            "legacy_regime_label_v1": self.legacy_regime_label_v1,
            "market_state_stratum_v2": self.market_state_stratum_v2,
            "research_stratification_version": self.research_stratification_version,
            "stratification_blockers": list(self.stratification_blockers),
            "stratification_input_provenance": dict(self.input_provenance),
            "stratification_key_v2": self.stratification_key_v2,
            "stratification_ok": self.stratification_ok,
            "stratification_parameter_digest": self.parameter_authority_provenance.get(
                "parameter_digest"
            ),
            "stratification_status": status,
            "volatility_regime_stratum_v2": self.volatility_regime_stratum_v2,
        }


@dataclass(frozen=True)
class ResearchStratificationBindingV2:
    """Campaign/session binding for v2 stratification on evidence production."""

    research_stratification_contract_version: str
    research_stratification_parameter_digest: str
    campaign_id: str
    enabled: bool = True
    # When None, production UNSET parameter surface is used (fail-closed).
    parameter_entries_override: Tuple[Any, ...] | None = None
