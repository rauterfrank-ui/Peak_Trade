"""Gated Full-Core productive wire transport. Send-capable. No POST.

Transport reuse of EEA host identity is plumbing only. Auth-header builders
are not invoked. Credential material is never loaded. Actual POST remains
blocked by the external-effect gate.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    TRADE_ORDER_PATH,
    FullCoreExternalEffectNotAuthorizedError,
    evaluate_external_effect_v1,
    refuse_external_effect_v1,
)

AUTHORIZED_HOST = "eea.okx.com"
USER_AGENT = "PeakTrade-FullCore-CZ-Gated-Productive-Wire/1"


@dataclass(frozen=True)
class FullCoreSendCredentialHandleV1:
    handle_id: str
    bound: bool
    material_loaded: bool = False

    def __post_init__(self) -> None:
        token = str(self.handle_id or "").lower()
        for forbidden in ("secret", "passphrase", "api_key", "apikey", "private_key"):
            if forbidden in token:
                raise ValueError("SECRET_TOKEN_IN_HANDLE_ID")
        if self.material_loaded is True:
            raise ValueError("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")


class FullCoreGatedProductiveWireTransportV1:
    """Send-capable transport that never performs an HTTP POST."""

    def __init__(self, *, handle: Optional[FullCoreSendCredentialHandleV1] = None) -> None:
        self._handle = handle
        self.transport_class = "FULL_CORE_GATED_PRODUCTIVE_WIRE_V1"
        self.post_count = 0
        self.wire_send_occurred = False
        self.methods_used: list[str] = []

    @property
    def credential_handle_bound(self) -> bool:
        return self._handle is not None and self._handle.bound is True

    @property
    def material_loaded(self) -> bool:
        return False

    def attempt_trade_order_post(self, *, payload: Any = None) -> None:
        del payload
        self.methods_used.append("POST")
        decision = evaluate_external_effect_v1(attempt_external_effect=True, attempt_post=True)
        if decision.external_effect_authorized is True:
            raise FullCoreExternalEffectNotAuthorizedError("EXTERNAL_EFFECT_TRUE_UNEXPECTED")
        if self._handle is None or self._handle.bound is not True:
            refuse_external_effect_v1(reason="CREDENTIAL_HANDLE_MISSING")
        if str(TRADE_ORDER_PATH) != "/api/v5/trade/order":
            raise FullCoreExternalEffectNotAuthorizedError("TRADE_ORDER_PATH_DRIFT")
        refuse_external_effect_v1()
