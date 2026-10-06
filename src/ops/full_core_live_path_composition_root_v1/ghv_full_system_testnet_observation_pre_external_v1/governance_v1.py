"""Scoped Owner-GO for GHV Full-System Testnet Observation PRE_EXTERNAL v1."""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    ORDER_POST_ALLOWED,
    POST_ALLOWED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    TESTNET_AUTHORIZED as GLOBAL_TESTNET_AUTHORIZED,
)

OWNER_GO = "FULL_SYSTEM_TESTNET_OBSERVATION_PRE_EXTERNAL_V1"
ALLOWED_OWNER_GOS = frozenset(
    {
        OWNER_GO,
        f"OWNER_GO_{OWNER_GO}",
    }
)

AUTHORIZATION_SCOPE = "FULL_SYSTEM_TESTNET_OBSERVATION_PRE_EXTERNAL_V1"
AUTHORIZATION_ALIASES_FORBIDDEN: frozenset[str] = frozenset(
    {
        "TESTNET_AUTHORIZED",
        "LIVE_AUTHORIZED",
        "ORDERS_AUTHORIZED",
        "TESTNET_EXECUTION",
    }
)


class GhvTestnetObservationGovernanceError(RuntimeError):
    """Fail-closed scoped observation governance violation."""


def prove_standing_fail_closed_pins_v1() -> dict[str, str]:
    if POST_ALLOWED is True or ORDER_POST_ALLOWED is True:
        raise GhvTestnetObservationGovernanceError("POST_STANDING_MUST_REMAIN_FALSE")
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        raise GhvTestnetObservationGovernanceError("EXTERNAL_EFFECT_MUST_REMAIN_FALSE")
    if GLOBAL_TESTNET_AUTHORIZED is True:
        raise GhvTestnetObservationGovernanceError("GLOBAL_TESTNET_AUTHORIZED_MUST_REMAIN_FALSE")
    return {
        "AUTHORIZATION_SCOPE": AUTHORIZATION_SCOPE,
        "POST_ALLOWED": "false",
        "ORDER_POST_ALLOWED": "false",
        "EXTERNAL_EFFECT_AUTHORIZED": "false",
        "GLOBAL_TESTNET_AUTHORIZED": "false",
        "TESTNET_EXECUTION_AUTHORIZED": "false",
    }


def assert_full_system_testnet_observation_owner_go_v1(owner_go: str | None) -> dict[str, str]:
    prove_standing_fail_closed_pins_v1()
    token = str(owner_go or "").strip()
    if not token:
        raise GhvTestnetObservationGovernanceError("OWNER_GO_REQUIRED")
    if token in AUTHORIZATION_ALIASES_FORBIDDEN:
        raise GhvTestnetObservationGovernanceError("OWNER_GO_ALIAS_FORBIDDEN")
    if token not in ALLOWED_OWNER_GOS:
        raise GhvTestnetObservationGovernanceError("OWNER_GO_MISMATCH")
    return {
        **prove_standing_fail_closed_pins_v1(),
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "DEMO_CREDENTIAL_ACCESS_AUTHORIZED": "true",
        "DEMO_AUTHENTICATED_GET_AUTHORIZED": "true",
        "BOUNDED_FULL_SYSTEM_OBSERVATION_AUTHORIZED": "true",
        "ENVIRONMENT_VALIDATION_AUTHORIZED": "true",
        "EVIDENCE_WRITING_AUTHORIZED": "true",
    }
