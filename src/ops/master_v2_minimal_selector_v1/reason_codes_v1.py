"""Candidate-level structural exclusion codes for Master V2 minimal selector V1.

OWNER_POLICY_VERSION=V1
HISTORICAL_CLAIM=false

These codes classify individual census rows. They are not Cap 2.1 GFU
eligibility semantics and do not encode BTC/asset exclusion.
"""

from __future__ import annotations

from enum import Enum


class StructuralExclusionCodeV1(str, Enum):
    MISSING_NATIVE_INST_ID = "MISSING_NATIVE_INST_ID"
    VENUE_NOT_OKX_EEA = "VENUE_NOT_OKX_EEA"
    SPOT_INSTRUMENT = "SPOT_INSTRUMENT"
    DATED_FUTURES_INSTRUMENT = "DATED_FUTURES_INSTRUMENT"
    SWAP_WITH_EXPIRY = "SWAP_WITH_EXPIRY"
    UNSUPPORTED_INSTRUMENT_TYPE = "UNSUPPORTED_INSTRUMENT_TYPE"
    MISSING_REQUIRED_METADATA = "MISSING_REQUIRED_METADATA"
    INVALID_REQUIRED_METADATA = "INVALID_REQUIRED_METADATA"
    MISSING_MARK_PRESENCE = "MISSING_MARK_PRESENCE"
    INACTIVE_OR_SUSPENDED = "INACTIVE_OR_SUSPENDED"
    UNKNOWN_TRADING_STATUS = "UNKNOWN_TRADING_STATUS"
    DUPLICATE_NATIVE_ID = "DUPLICATE_NATIVE_ID"


ALL_STRUCTURAL_EXCLUSION_CODES: frozenset[str] = frozenset(
    code.value for code in StructuralExclusionCodeV1
)
