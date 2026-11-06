"""Governed productive runtime parameter seam session bind v1.

Session/cycle ownership edge: installs an already-bound authorized productive
parameter seam onto ``HardenedBridgeSessionStateV2`` for downstream runtime
transport (#6641 join). Does not materialize, authorize, or read optimization.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.authorized_productive_parameter_seam_v1 import (
    AuthorizedProductiveParameterSeamResultV1,
    verify_seam_record_digest_v1,
)
from src.governance.governed_productive_runtime_parameter_seam_join_v1 import (
    STATUS_TRANSPORT_READY,
    resolve_governed_runtime_seam_for_presence_gate_v1,
)

SCHEMA_VERSION: Final[str] = "governed_productive_runtime_parameter_seam_session_bind_v1"
SESSION_BIND_OWNER: Final[str] = (
    "src.governance.governed_productive_runtime_parameter_seam_session_bind_v1"
)
SESSION_BIND_DISPOSITION: Final[str] = (
    "GOVERNED_PRODUCTIVE_RUNTIME_PARAMETER_SEAM_SESSION_BIND_ONLY"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/governed_productive_runtime_parameter_seam_session_bind_v1_decision_v1.json"
)

STATUS_BOUND: Final[str] = "SESSION_SEAM_BOUND"
STATUS_DENIED: Final[str] = "SESSION_SEAM_BIND_DENIED_FAIL_CLOSED"

ENFORCEMENT_AUTHORITY: Final[str] = "NONE"
TRADING_DECISION_AUTHORITY: Final[str] = "MV2_DOUBLE_PLAY"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False


@dataclass(frozen=True)
class GovernedRuntimeSeamSessionBindResultV1:
    bind_status: str
    reason_codes: tuple[str, ...]
    seam_digest: str | None
    session_id: str | None
    enforcement_authority: str = ENFORCEMENT_AUTHORITY
    trading_decision_authority: str = TRADING_DECISION_AUTHORITY
    external_effect_authorized: bool = EXTERNAL_EFFECT_AUTHORIZED


def _deny(reason_codes: list[str]) -> GovernedRuntimeSeamSessionBindResultV1:
    return GovernedRuntimeSeamSessionBindResultV1(
        bind_status=STATUS_DENIED,
        reason_codes=tuple(reason_codes),
        seam_digest=None,
        session_id=None,
    )


def _existing_seam_digest(
    record: Mapping[str, Any] | None,
) -> str | None:
    if record is None:
        return None
    digest = record.get("seam_digest")
    if isinstance(digest, str) and verify_seam_record_digest_v1(record):
        return digest
    return None


def bind_governed_authorized_productive_parameter_seam_to_hardened_bridge_session_v1(
    session_state: Any,
    seam_record: Mapping[str, Any] | None,
    *,
    session_id: str | None = None,
    seam_bind_result: AuthorizedProductiveParameterSeamResultV1 | None = None,
) -> tuple[Any, GovernedRuntimeSeamSessionBindResultV1]:
    """Fail-closed session bind: valid authorized seam only; immutable per session."""
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
        HardenedBridgeSessionStateV2,
    )

    if not isinstance(session_state, HardenedBridgeSessionStateV2):
        return session_state, _deny(["HARDENED_BRIDGE_SESSION_STATE_REQUIRED"])

    if seam_bind_result is not None and seam_record is not None:
        return session_state, _deny(["SEAM_RECORD_AND_BIND_RESULT_MUTUALLY_EXCLUSIVE"])

    if seam_bind_result is not None:
        if seam_bind_result.seam_record is None:
            return session_state, _deny(list(seam_bind_result.reason_codes) or ["SEAM_BIND_DENIED"])
        seam_record = dict(seam_bind_result.seam_record)

    transport = resolve_governed_runtime_seam_for_presence_gate_v1(seam_record)
    if transport.transport_status != STATUS_TRANSPORT_READY or transport.seam_for_consumer is None:
        return session_state, _deny(
            list(transport.reason_codes) or ["RUNTIME_SEAM_TRANSPORT_NOT_READY"]
        )

    bound = dict(transport.seam_for_consumer)
    new_digest = str(bound.get("seam_digest") or "")
    existing_digest = _existing_seam_digest(
        session_state.governed_authorized_productive_parameter_seam_record
    )
    if existing_digest is not None:
        if existing_digest == new_digest:
            resolved_session = session_state.session_id or session_id
            if session_id and session_state.session_id and session_state.session_id != session_id:
                return session_state, _deny(["SESSION_ID_MISMATCH_ON_IDEMPOTENT_REBIND"])
            if session_id and not session_state.session_id:
                session_state.session_id = session_id
            return session_state, GovernedRuntimeSeamSessionBindResultV1(
                bind_status=STATUS_BOUND,
                reason_codes=("SESSION_SEAM_ALREADY_BOUND_IDEMPOTENT",),
                seam_digest=new_digest,
                session_id=resolved_session or None,
            )
        return session_state, _deny(["SESSION_SEAM_REBIND_FORBIDDEN"])

    if session_id and session_state.session_id and session_state.session_id != session_id:
        return session_state, _deny(["SESSION_ID_MISMATCH"])

    session_state.governed_authorized_productive_parameter_seam_record = MappingProxyType(bound)
    if session_id:
        session_state.session_id = session_id

    return session_state, GovernedRuntimeSeamSessionBindResultV1(
        bind_status=STATUS_BOUND,
        reason_codes=("SESSION_SEAM_BOUND",),
        seam_digest=new_digest,
        session_id=session_state.session_id or session_id,
    )


def read_session_bound_seam_for_runtime_transport_v1(
    session_state: Any,
) -> Mapping[str, Any] | None:
    """Read-only accessor for cycle/runtime join (no mutation)."""
    record = getattr(session_state, "governed_authorized_productive_parameter_seam_record", None)
    if record is None:
        return None
    transport = resolve_governed_runtime_seam_for_presence_gate_v1(record)
    if transport.seam_for_consumer is None:
        return None
    return transport.seam_for_consumer


def optimization_can_bind_session_seam_directly_v1() -> bool:
    return False
