"""Separate future Owner-GO gates for R6 S5 preparation.

Each later grant remains an independent false flag. One boolean cannot
unlock authorization, N>1, G13, productive activation, and submit.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.constants_v1 import (
    FUTURE_OWNER_GATE_IDS,
    OWNER_GO_G13_CONTROLLED_UNLOCK,
    OWNER_GO_N_GREATER_THAN_ONE_POLICY,
    OWNER_GO_PRODUCTIVE_MF_ACTIVATION,
    OWNER_GO_S5_AUTHORIZATION_GRANT,
    OWNER_GO_SUBMIT_UNLOCK,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.models_v1 import (
    R6S5BoundedAuthorizationPreparationError,
)

_GATE_VALUES = {
    "OWNER_GO_S5_AUTHORIZATION_GRANT": OWNER_GO_S5_AUTHORIZATION_GRANT,
    "OWNER_GO_N_GREATER_THAN_ONE_POLICY": OWNER_GO_N_GREATER_THAN_ONE_POLICY,
    "OWNER_GO_G13_CONTROLLED_UNLOCK": OWNER_GO_G13_CONTROLLED_UNLOCK,
    "OWNER_GO_PRODUCTIVE_MF_ACTIVATION": OWNER_GO_PRODUCTIVE_MF_ACTIVATION,
    "OWNER_GO_SUBMIT_UNLOCK": OWNER_GO_SUBMIT_UNLOCK,
}


def _reject(message: str) -> None:
    raise R6S5BoundedAuthorizationPreparationError(message)


def future_owner_gates_v1() -> Mapping[str, Any]:
    if tuple(_GATE_VALUES) != FUTURE_OWNER_GATE_IDS:
        _reject("future_owner_gate_id_drift")
    if any(value is True for value in _GATE_VALUES.values()):
        _reject("future_owner_gate_granted")
    if any(value is not False for value in _GATE_VALUES.values()):
        _reject("future_owner_gate_unknown")
    payload = {gate_id: False for gate_id in FUTURE_OWNER_GATE_IDS}
    payload["any_future_owner_gate_granted"] = False
    payload["gates_are_independent"] = True
    payload["one_bool_cannot_unlock_all"] = True
    return MappingProxyType(payload)


def reject_if_any_gate_granted_v1(gates: Mapping[str, Any]) -> None:
    for gate_id in FUTURE_OWNER_GATE_IDS:
        if gates.get(gate_id) is True:
            _reject(f"future_owner_gate_granted:{gate_id}")
        if gates.get(gate_id) is not False:
            _reject(f"future_owner_gate_unknown:{gate_id}")
    if gates.get("any_future_owner_gate_granted") is not False:
        _reject("any_future_owner_gate_granted_not_false")
