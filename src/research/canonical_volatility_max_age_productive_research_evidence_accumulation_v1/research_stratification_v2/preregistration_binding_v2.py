"""Preregistration binding surface for research stratification v2 (no active campaign)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    sha256_hex,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.constants_v2 import (
    CROSS_CAMPAIGN_STATE_POLICY,
    CROSS_SESSION_STATE_POLICY,
    RESEARCH_STRATIFICATION_CONTRACT_VERSION,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.parameter_authority_v2 import (
    build_production_parameter_authority_surface_v2,
    parameter_authority_digest_v2,
)


@dataclass(frozen=True)
class ResearchStratificationPreregistrationV2:
    research_stratification_contract_version: str
    research_stratification_parameter_digest: str
    market_state_dimension: str
    volatility_dimension: str
    minimum_market_regimes: int
    minimum_volatility_regimes: int
    cross_session_state_policy: str
    cross_campaign_state_policy: str
    research_stratification_preregistration_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "cross_campaign_state_policy": self.cross_campaign_state_policy,
            "cross_session_state_policy": self.cross_session_state_policy,
            "market_state_dimension": self.market_state_dimension,
            "minimum_market_regimes": self.minimum_market_regimes,
            "minimum_volatility_regimes": self.minimum_volatility_regimes,
            "research_stratification_contract_version": self.research_stratification_contract_version,
            "research_stratification_parameter_digest": self.research_stratification_parameter_digest,
            "research_stratification_preregistration_digest": (
                self.research_stratification_preregistration_digest
            ),
            "volatility_dimension": self.volatility_dimension,
        }


def build_research_stratification_preregistration_v2() -> ResearchStratificationPreregistrationV2:
    """Build v2 preregistration template — production parameter digest is UNSET-only."""
    entries = build_production_parameter_authority_surface_v2()
    param_digest = parameter_authority_digest_v2(entries)
    body: dict[str, Any] = {
        "research_stratification_contract_version": RESEARCH_STRATIFICATION_CONTRACT_VERSION,
        "research_stratification_parameter_digest": param_digest,
        "market_state_dimension": "MARKET_STATE_STRATA",
        "volatility_dimension": "VOLATILITY_REGIME_STRATA",
        "minimum_market_regimes": 2,
        "minimum_volatility_regimes": 1,
        "cross_session_state_policy": CROSS_SESSION_STATE_POLICY,
        "cross_campaign_state_policy": CROSS_CAMPAIGN_STATE_POLICY,
    }
    digest = sha256_hex(body)
    return ResearchStratificationPreregistrationV2(
        research_stratification_contract_version=RESEARCH_STRATIFICATION_CONTRACT_VERSION,
        research_stratification_parameter_digest=param_digest,
        market_state_dimension="MARKET_STATE_STRATA",
        volatility_dimension="VOLATILITY_REGIME_STRATA",
        minimum_market_regimes=2,
        minimum_volatility_regimes=1,
        cross_session_state_policy=CROSS_SESSION_STATE_POLICY,
        cross_campaign_state_policy=CROSS_CAMPAIGN_STATE_POLICY,
        research_stratification_preregistration_digest=digest,
    )


def verify_preregistration_binding_v2(payload: Mapping[str, Any]) -> bool:
    expected = build_research_stratification_preregistration_v2()
    return (
        payload.get("research_stratification_contract_version")
        == expected.research_stratification_contract_version
        and payload.get("research_stratification_preregistration_digest")
        == expected.research_stratification_preregistration_digest
    )
