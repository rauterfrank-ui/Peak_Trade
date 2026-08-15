"""R6 S2 portfolio-risk contracts v1.

Read-only forensic overlay. Does not implement Multi-Future runtime,
change G13, mutate risk/trading logic, or claim SINGLE_FUTURE_LIVE_PROOF.
"""

from __future__ import annotations

from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.constants_v1 import (
    CAPABILITY_ID,
    CONTRACT_VERSION,
    PACKAGE_MARKER,
    REMEDIATION_ID,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.dimensions_v1 import (
    S2_DIMENSIONS,
    require_item,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.intents_v1 import (
    require_intent,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.models_v1 import (
    ContractItemStatus,
    R6S2PortfolioRiskError,
)
from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.verifier_v1 import (
    evaluate_r6_s2_portfolio_risk_contracts_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "CONTRACT_VERSION",
    "ContractItemStatus",
    "PACKAGE_MARKER",
    "R6S2PortfolioRiskError",
    "REMEDIATION_ID",
    "S2_DIMENSIONS",
    "evaluate_r6_s2_portfolio_risk_contracts_v1",
    "require_intent",
    "require_item",
]
