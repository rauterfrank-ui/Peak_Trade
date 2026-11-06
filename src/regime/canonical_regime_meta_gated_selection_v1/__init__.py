"""Canonical Regime/Meta gated selection v1 (R3 / I40 / I83 / UQ2).

Additive, fail-closed, non-activating. Not a second registry, selection owner,
or regime/meta authority. LLM remains permanent non-authority.
"""

from __future__ import annotations

from src.regime.canonical_regime_meta_gated_selection_v1.constants_v1 import (
    CAPABILITY_ID,
    CONTRACT_VERSION,
    PACKAGE_MARKER,
    RAW_LLM_TRADING_AUTHORITY,
    REMEDIATION_ID,
)
from src.regime.canonical_regime_meta_gated_selection_v1.gate_v1 import (
    apply_regime_meta_gate_v1,
)
from src.regime.canonical_regime_meta_gated_selection_v1.models_v1 import (
    GateIntent,
    RegimeMetaGateInputV1,
    RegimeMetaGatedSelectionError,
    SourceClass,
)
from src.regime.canonical_regime_meta_gated_selection_v1.verifier_v1 import (
    evaluate_r3_regime_meta_gated_selection_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "CONTRACT_VERSION",
    "PACKAGE_MARKER",
    "RAW_LLM_TRADING_AUTHORITY",
    "REMEDIATION_ID",
    "GateIntent",
    "RegimeMetaGateInputV1",
    "RegimeMetaGatedSelectionError",
    "SourceClass",
    "apply_regime_meta_gate_v1",
    "evaluate_r3_regime_meta_gated_selection_v1",
]
