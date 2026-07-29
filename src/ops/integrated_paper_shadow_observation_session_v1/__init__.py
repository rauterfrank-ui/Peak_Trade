"""INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1.

Canonical, non-authorizing observation-session capability surfaces.

This package never starts wallclock sessions, never grants Operator-GO,
never authorizes Testnet/Live/Orders, and never contacts brokers/exchanges.
"""

from __future__ import annotations

from src.ops.integrated_paper_shadow_observation_session_v1.bundle_verifier_v1 import (
    verify_integrated_paper_shadow_observation_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
    PACKAGE_MARKER,
    PRODUCER_FAMILY,
    SCHEMA_VERSION,
)
from src.ops.integrated_paper_shadow_observation_session_v1.entrypoint_v1 import (
    run_integrated_paper_shadow_observation_cycle_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PORTFOLIO_ECONOMICS_MODEL_ID,
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.readiness_producer_v1 import (
    produce_paper_shadow_observation_readiness_v1,
)

__all__ = (
    "AUTHORITY_EFFECT_NONE",
    "CAPABILITY_ID",
    "PACKAGE_MARKER",
    "PORTFOLIO_ECONOMICS_MODEL_ID",
    "PRODUCER_FAMILY",
    "SCHEMA_VERSION",
    "SimulatedPortfolioEconomicsModelV1",
    "produce_paper_shadow_observation_readiness_v1",
    "run_integrated_paper_shadow_observation_cycle_v1",
    "verify_integrated_paper_shadow_observation_evidence_bundle_v1",
)
