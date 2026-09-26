"""Operator-visible effective authorization: observation capability ≠ send authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    POST_ALLOWED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    REAL_EXTERNAL_EFFECT_AUTHORIZED,
    REAL_VENUE_POST_ALLOWED,
    SUBMISSION_AUTHORIZED,
    WIRE_SEND_PERMITTED,
)
from src.ops.market_data_private_state_runtime_convergence_v1.constants_v1 import (
    K2_STATUS,
    LIVE_EXTERNAL_EFFECT_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PRIVATE_WS_ORDER_SEND_AUTHORIZED,
    REST_POST_PERMIT_CHANGE,
)
from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    PRIVATE_WS_ORDER_SEND_AUTHORIZED as WP_B_WS_SEND,
)
from src.ops.peak_trade_public_market_data_runtime_v1.safety_boundary_v1 import (
    public_runtime_safety_attestation_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.safety_boundary_v1 import (
    private_runtime_safety_attestation_v1,
)


@dataclass(frozen=True)
class ObservationCapabilitySignalsV1:
    public_ws_connected: bool = False
    private_ws_connected: bool = False
    private_ws_logged_in: bool = False
    rest_get_success: bool = False
    credential_sign_capable: bool = False
    authenticated_connectivity: bool = False


class EffectiveAuthorizationError(RuntimeError):
    pass


def _infer_send_from_observation_forbidden_v1(signals: ObservationCapabilitySignalsV1) -> None:
    """Mechanical proof: no observation signal may imply send authority."""
    observation_only = (
        signals.public_ws_connected
        or signals.private_ws_connected
        or signals.private_ws_logged_in
        or signals.rest_get_success
        or signals.credential_sign_capable
        or signals.authenticated_connectivity
    )
    if not observation_only:
        return
    if PRIVATE_WS_ORDER_SEND_AUTHORIZED or WP_B_WS_SEND:
        raise EffectiveAuthorizationError("PRIVATE_WS_SEND_INFERRED_FROM_OBSERVATION")
    if REST_POST_PERMIT_CHANGE:
        raise EffectiveAuthorizationError("REST_POST_INFERRED_FROM_OBSERVATION")
    if LIVE_EXTERNAL_EFFECT_AUTHORIZED or REAL_EXTERNAL_EFFECT_AUTHORIZED:
        raise EffectiveAuthorizationError("EXTERNAL_EFFECT_INFERRED_FROM_OBSERVATION")


def build_effective_authorization_readmodel_v1(
    *,
    observation: ObservationCapabilitySignalsV1 | None = None,
    extra_pins: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    obs = observation or ObservationCapabilitySignalsV1()
    _infer_send_from_observation_forbidden_v1(obs)

    public_att = public_runtime_safety_attestation_v1()
    private_att = private_runtime_safety_attestation_v1()

    effective_external_effect = (
        EXTERNAL_EFFECT_AUTHORIZED is True
        and REAL_EXTERNAL_EFFECT_AUTHORIZED is True
        and LIVE_EXTERNAL_EFFECT_AUTHORIZED is True
    )

    readmodel = {
        "schema_name": "wp_c_effective_authorization_readmodel.v1",
        "authority_minted_by_wp_c": False,
        "observation_capability": {
            "public_ws_connected": obs.public_ws_connected,
            "private_ws_connected": obs.private_ws_connected,
            "private_ws_logged_in": obs.private_ws_logged_in,
            "rest_get_success": obs.rest_get_success,
            "credential_sign_capable": obs.credential_sign_capable,
            "authenticated_connectivity": obs.authenticated_connectivity,
            "implies_send_authority": False,
        },
        "standing_admission_seams": {
            "LIVE_ENABLED": LIVE_ENABLED is True,
            "LIVE_ARMED": LIVE_ARMED is True,
            "LIVE_AUTHORIZED": LIVE_AUTHORIZED is True,
            "SUBMISSION_AUTHORIZED": SUBMISSION_AUTHORIZED is True,
            "PRODUCTIVE_WIRE_SEND_REACHABLE": PRODUCTIVE_WIRE_SEND_REACHABLE is True,
            "standing_admission_implies_post": False,
        },
        "external_effect_authorization": {
            "WIRE_SEND_PERMITTED": WIRE_SEND_PERMITTED is True,
            "POST_ALLOWED": POST_ALLOWED,
            "REAL_VENUE_POST_ALLOWED": REAL_VENUE_POST_ALLOWED,
            "LIVE_EXTERNAL_EFFECT_AUTHORIZED": LIVE_EXTERNAL_EFFECT_AUTHORIZED,
            "REAL_EXTERNAL_EFFECT_AUTHORIZED": REAL_EXTERNAL_EFFECT_AUTHORIZED,
            "EXTERNAL_EFFECT_AUTHORIZED": EXTERNAL_EFFECT_AUTHORIZED,
            "effective_external_effect_authorized": effective_external_effect,
        },
        "private_send_pins": {
            "PRIVATE_WS_ORDER_SEND_AUTHORIZED": PRIVATE_WS_ORDER_SEND_AUTHORIZED,
            "REST_POST_PERMIT_CHANGE": REST_POST_PERMIT_CHANGE,
        },
        "multi_future_pins": {
            "MULTI_FUTURE_RUNTIME_AUTHORIZED": MULTI_FUTURE_RUNTIME_AUTHORIZED,
            "MAX_POSITIONS_EFFECTIVE": MAX_POSITIONS_EFFECTIVE,
        },
        "k2_status": K2_STATUS,
        "wp_a_attestation": public_att,
        "wp_b_attestation": private_att,
    }
    if extra_pins:
        readmodel["extra_pins"] = dict(extra_pins)
    return readmodel
