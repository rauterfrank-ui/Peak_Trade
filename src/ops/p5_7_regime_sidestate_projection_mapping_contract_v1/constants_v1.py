"""P5.7 regime→SideState projection mapping contract (definition only; no cutover)."""

from __future__ import annotations

PACKAGE_MARKER = "P5_7_REGIME_SIDESTATE_PROJECTION_MAPPING_CONTRACT_V1=true"
OWNER = "ops.p5_7_regime_sidestate_projection_mapping_contract_v1"
CONTRACT_VERSION = "regime_sidestate_projection_mapping.v1"

# Contract artifact is present; productive authorization remains on P5.2 flag (still false).
MAPPING_CONTRACT_V1_DEFINED = True

from src.ops.p5_2_productive_cycle_seam_invoke_and_authority_bind_v1.constants_v1 import (  # noqa: E402
    AUTHORITY_CUTOVER_OCCURRED,
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
    REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED,
)

assert MAPPING_CONTRACT_V1_DEFINED is True
assert REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED is True
assert PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED is True
assert P5_AUTHORITY_CUTOVER_AUTHORIZED is False
assert AUTHORITY_CUTOVER_OCCURRED is False

__all__ = [
    "AUTHORITY_CUTOVER_OCCURRED",
    "CONTRACT_VERSION",
    "MAPPING_CONTRACT_V1_DEFINED",
    "OWNER",
    "P5_AUTHORITY_CUTOVER_AUTHORIZED",
    "PACKAGE_MARKER",
    "PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED",
    "REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED",
]
