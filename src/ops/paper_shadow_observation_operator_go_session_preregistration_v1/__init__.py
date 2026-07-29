"""PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1.

Non-executing Operator-GO / Session-Preregistration surfaces for the integrated
Paper-Shadow Observation pipeline. Never starts sessions, never contacts OKX,
never grants Orders/Testnet/Live authority.
"""

from __future__ import annotations

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1 import (
    build_authorization_artifact_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_readiness_producer_v1 import (
    produce_paper_shadow_observation_authorization_readiness_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
    PACKAGE_MARKER,
    PRODUCER_FAMILY,
    SCHEMA_VERSION,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.discovery_v1 import (
    discover_session_preregistration_and_operator_go_contract_present_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.verifier_v1 import (
    verify_paper_shadow_observation_authorization_bundle_v1,
)

__all__ = (
    "AUTHORITY_EFFECT_NONE",
    "CAPABILITY_ID",
    "PACKAGE_MARKER",
    "PRODUCER_FAMILY",
    "SCHEMA_VERSION",
    "build_authorization_artifact_v1",
    "discover_session_preregistration_and_operator_go_contract_present_v1",
    "produce_paper_shadow_observation_authorization_readiness_v1",
    "verify_paper_shadow_observation_authorization_bundle_v1",
)
