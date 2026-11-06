"""Authority separation: trading cannot mint Treasury, Treasury cannot mint Live/wire."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    TREASURY_MUTATION_AUTHORIZED,
    TREASURY_OBSERVER_CAN_AUTHORIZE_MUTATION,
    TREASURY_PHASE_1_CAN_ARM_LIVE,
    TREASURY_PHASE_1_CAN_ENABLE_LIVE,
    TREASURY_PHASE_1_CAN_ENABLE_WIRE,
    TREASURY_PHASE_1_CAN_MINT_TRADING_AUTHORITY,
    WIRE_SEND_PERMITTED,
)
from src.ops.treasury_phase_1_offline_contracts_v1.errors_v1 import TreasuryPhase1ContractError
from src.ops.treasury_phase_1_offline_contracts_v1.models_v1 import TreasuryAuthorizationClassV1

_TRADING_AUTHORITY_KEYS = frozenset(
    {
        "live_enabled",
        "live_armed",
        "wire_send_permitted",
        "owner_one_shot_permit",
        "trading_owner_permit",
        "strategy_decision",
        "double_play_state",
        "planner_result",
        "learner_output",
        "scheduler",
        "generic_execution_token",
        "canonical_order_intent",
    }
)


def trading_authority_cannot_mint_treasury_authority_v1(
    trading_inputs: Mapping[str, Any] | None = None,
) -> bool:
    payload = dict(trading_inputs or {})
    if LIVE_ENABLED is True or LIVE_ARMED is True or WIRE_SEND_PERMITTED is True:
        raise TreasuryPhase1ContractError("STANDING_LIVE_GATE_TRUE")
    for key in _TRADING_AUTHORITY_KEYS:
        value = payload.get(key)
        if value is True or (
            isinstance(value, str) and value.strip() != "" and key != "live_enabled"
        ):
            if key in {"live_enabled", "live_armed", "wire_send_permitted"} and value is True:
                raise TreasuryPhase1ContractError("TRADING_FLAG_CANNOT_MINT_TREASURY")
            if key not in {"live_enabled", "live_armed", "wire_send_permitted"} and value not in (
                None,
                False,
                "",
            ):
                raise TreasuryPhase1ContractError("TRADING_SURFACE_CANNOT_MINT_TREASURY")
    return True


def treasury_authorization_cannot_mint_wire_or_live_v1(authorization_class: str) -> bool:
    allowed = {item.value for item in TreasuryAuthorizationClassV1}
    if authorization_class not in allowed:
        raise TreasuryPhase1ContractError("AUTHORIZATION_CLASS_UNKNOWN")
    if authorization_class == TreasuryAuthorizationClassV1.MUTATION_PERMIT_TYPED_OFFLINE.value:
        if TREASURY_MUTATION_AUTHORIZED is True:
            raise TreasuryPhase1ContractError("TYPED_PERMIT_MUST_NOT_AUTHORIZE_MUTATION")
    if TREASURY_PHASE_1_CAN_ENABLE_LIVE or TREASURY_PHASE_1_CAN_ARM_LIVE:
        raise TreasuryPhase1ContractError("TREASURY_CANNOT_ENABLE_LIVE")
    if TREASURY_PHASE_1_CAN_ENABLE_WIRE or TREASURY_PHASE_1_CAN_MINT_TRADING_AUTHORITY:
        raise TreasuryPhase1ContractError("TREASURY_CANNOT_MINT_WIRE_OR_TRADING")
    return False


def treasury_observer_cannot_authorize_mutation_v1(authorization_class: str) -> bool:
    if authorization_class == TreasuryAuthorizationClassV1.OBSERVER_CONTRACT.value:
        if TREASURY_OBSERVER_CAN_AUTHORIZE_MUTATION is True:
            raise TreasuryPhase1ContractError("OBSERVER_MUTATION_AUTHORITY_DRIFT")
        return True
    return TREASURY_OBSERVER_CAN_AUTHORIZE_MUTATION is False


def phase_1_no_authority_proof_v1() -> dict[str, bool]:
    from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
        TREASURY_PHASE_1_CAN_GENERATE_DEPOSIT_ADDRESS,
        TREASURY_PHASE_1_CAN_INTERNAL_TRANSFER,
        TREASURY_PHASE_1_CAN_MINT_RISK_ADMISSIBLE_CAPITAL,
        TREASURY_PHASE_1_CAN_MOVE_FUNDS,
        TREASURY_PHASE_1_CAN_SEND_NETWORK_REQUEST,
        TREASURY_PHASE_1_CAN_SUBMIT_ORDER,
        TREASURY_PHASE_1_CAN_WITHDRAW,
    )

    proof = {
        "TREASURY_PHASE_1_CAN_MOVE_FUNDS": TREASURY_PHASE_1_CAN_MOVE_FUNDS,
        "TREASURY_PHASE_1_CAN_SEND_NETWORK_REQUEST": TREASURY_PHASE_1_CAN_SEND_NETWORK_REQUEST,
        "TREASURY_PHASE_1_CAN_WITHDRAW": TREASURY_PHASE_1_CAN_WITHDRAW,
        "TREASURY_PHASE_1_CAN_INTERNAL_TRANSFER": TREASURY_PHASE_1_CAN_INTERNAL_TRANSFER,
        "TREASURY_PHASE_1_CAN_GENERATE_DEPOSIT_ADDRESS": TREASURY_PHASE_1_CAN_GENERATE_DEPOSIT_ADDRESS,
        "TREASURY_PHASE_1_CAN_ENABLE_LIVE": TREASURY_PHASE_1_CAN_ENABLE_LIVE,
        "TREASURY_PHASE_1_CAN_ARM_LIVE": TREASURY_PHASE_1_CAN_ARM_LIVE,
        "TREASURY_PHASE_1_CAN_ENABLE_WIRE": TREASURY_PHASE_1_CAN_ENABLE_WIRE,
        "TREASURY_PHASE_1_CAN_SUBMIT_ORDER": TREASURY_PHASE_1_CAN_SUBMIT_ORDER,
        "TREASURY_PHASE_1_CAN_MINT_RISK_ADMISSIBLE_CAPITAL": (
            TREASURY_PHASE_1_CAN_MINT_RISK_ADMISSIBLE_CAPITAL
        ),
        "TREASURY_PHASE_1_CAN_MINT_TRADING_AUTHORITY": TREASURY_PHASE_1_CAN_MINT_TRADING_AUTHORITY,
    }
    if any(proof.values()):
        raise TreasuryPhase1ContractError("PHASE_1_NO_AUTHORITY_PROOF_FAILED")
    return proof
