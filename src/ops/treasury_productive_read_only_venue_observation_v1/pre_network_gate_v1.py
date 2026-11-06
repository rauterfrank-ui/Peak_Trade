"""Pre-network capability gate for productive Treasury read-only observation."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FORBIDDEN_ENDPOINTS as TRANSPORT_FORBIDDEN,
)
from src.ops.offline_funding_balance_read_producer_v1.constants_v1 import (
    FORBIDDEN_TRANSFER_ENDPOINT,
    FORBIDDEN_WITHDRAWAL_ENDPOINT,
)
from src.ops.pl_tf_002_network_evidence_contract_v1.constants_v1 import (
    NE_TF_001_HTTP_METHOD,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.constants_v1 import (
    FORBIDDEN_HTTP_METHODS,
    FORBIDDEN_MUTATION_ENDPOINTS,
    METHOD_ALLOWLIST,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.session_executor_v1 import (
    build_pl_tf_002_read_only_get_session_preflight_v1,
    prove_pl_tf_002_session_does_not_authorize_post_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    GET_ENDPOINTS_PRIVATE,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.constants_v1 import (
    ACCOUNT_CONFIG_ENDPOINT,
    ALLOWED_WP_OWNER_GOS,
    AUTHORIZED_NETWORK_HOST,
    FUNDING_GET_ENDPOINT,
    FUNDING_GET_METHOD,
    OWNER_GO,
    PRODUCTIVE_TRANSPORT_CLASS,
    SESSION_OWNER_GO,
    WP_ID,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.errors_v1 import (
    TreasuryProductiveReadOnlyVenueObservationError,
)


def _assert_read_only_endpoint_v1(*, endpoint_path: str, method: str) -> None:
    method_u = str(method or "").upper()
    if method_u not in METHOD_ALLOWLIST:
        raise TreasuryProductiveReadOnlyVenueObservationError(f"HTTP_METHOD_FORBIDDEN:{method_u}")
    if method_u in FORBIDDEN_HTTP_METHODS:
        raise TreasuryProductiveReadOnlyVenueObservationError(f"HTTP_METHOD_FORBIDDEN:{method_u}")
    path = str(endpoint_path or "").split("?", 1)[0]
    if path in FORBIDDEN_MUTATION_ENDPOINTS or path in TRANSPORT_FORBIDDEN:
        raise TreasuryProductiveReadOnlyVenueObservationError("MUTATION_ENDPOINT_FORBIDDEN")
    if path in {FORBIDDEN_TRANSFER_ENDPOINT, FORBIDDEN_WITHDRAWAL_ENDPOINT}:
        raise TreasuryProductiveReadOnlyVenueObservationError(
            "TREASURY_MUTATION_ENDPOINT_FORBIDDEN"
        )
    if path not in GET_ENDPOINTS_PRIVATE:
        raise TreasuryProductiveReadOnlyVenueObservationError(
            "ENDPOINT_NOT_ON_PRIVATE_READ_ALLOWLIST"
        )


def build_treasury_productive_pre_network_gate_proof_v1(
    *,
    wp_owner_go: str,
    session_owner_go: str,
    origin_main_sha: str,
    integrity_backend: object | None = None,
) -> dict[str, Any]:
    """Non-secret gate proof. No network. No credential load."""

    owned = str(wp_owner_go or "").strip()
    if owned not in ALLOWED_WP_OWNER_GOS:
        raise TreasuryProductiveReadOnlyVenueObservationError(f"WP_OWNER_GO_NOT_AUTHORIZED:{owned}")
    if str(session_owner_go or "").strip() != SESSION_OWNER_GO:
        raise TreasuryProductiveReadOnlyVenueObservationError("SESSION_OWNER_GO_MISMATCH")
    if (
        EXTERNAL_EFFECT_AUTHORIZED is True
        or POST_ALLOWED is True
        or REAL_VENUE_POST_ALLOWED is True
    ):
        raise TreasuryProductiveReadOnlyVenueObservationError(
            "STANDING_POST_OR_EXTERNAL_EFFECT_FORBIDDEN"
        )

    _assert_read_only_endpoint_v1(endpoint_path=FUNDING_GET_ENDPOINT, method=FUNDING_GET_METHOD)
    _assert_read_only_endpoint_v1(
        endpoint_path=ACCOUNT_CONFIG_ENDPOINT,
        method=NE_TF_001_HTTP_METHOD,
    )

    preflight = build_pl_tf_002_read_only_get_session_preflight_v1(
        owner_go=session_owner_go,
        origin_main_sha=origin_main_sha,
        integrity_backend=integrity_backend,  # type: ignore[arg-type]
    )
    post_proof = prove_pl_tf_002_session_does_not_authorize_post_v1()
    return {
        "WP_ID": WP_ID,
        "WP_OWNER_GO_ACCEPTED": owned in ALLOWED_WP_OWNER_GOS,
        "WP_OWNER_GO_CANONICAL": OWNER_GO,
        "SESSION_OWNER_GO_REQUIRED": SESSION_OWNER_GO,
        "SESSION_OWNER_GO_ACCEPTED": session_owner_go == SESSION_OWNER_GO,
        "HOST": AUTHORIZED_NETWORK_HOST,
        "TRANSPORT": PRODUCTIVE_TRANSPORT_CLASS,
        "FUNDING_GET_ENDPOINT": FUNDING_GET_ENDPOINT,
        "ACCOUNT_CONFIG_ENDPOINT": ACCOUNT_CONFIG_ENDPOINT,
        "HTTP_METHOD_ALLOWLIST": list(METHOD_ALLOWLIST),
        "READ_ONLY_ENDPOINT_CLASSES": list(
            (
                "PRIVATE_READ_ONLY_FUNDING_BALANCE",
                "PRIVATE_READ_ONLY_ACCOUNT_CONFIG_IDENTITY",
            )
        ),
        "TREASURY_MUTATION": False,
        "WITHDRAWAL": False,
        "TRANSFER": False,
        "POST": False,
        "ORDER": False,
        "NETWORK_READ_ONLY_AUTHORIZED": True,
        "NETWORK_EXECUTION_AUTHORIZED_STANDING": False,
        "CREDENTIAL_LOAD_PERFORMED": False,
        "PL_TF_002_PREFLIGHT": preflight.to_dict(),
        "POST_STANDING_PROOF": post_proof,
        "UNEXPECTED_MUTATION_CAPABILITY_DETECTED": False,
    }


def merge_session_gate_facts_v1(
    gate: Mapping[str, Any],
    *,
    credential_acquired: bool,
    k1_handle_bound: bool,
) -> dict[str, Any]:
    out = dict(gate)
    out["CREDENTIAL_LOAD_PERFORMED"] = credential_acquired is True
    out["K1_HANDLE_BOUND"] = k1_handle_bound is True
    out["K1_ACQUISITION"] = "PASS" if credential_acquired else "FAIL_CLOSED"
    return out
