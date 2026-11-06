"""Build Full-Core PRE_EXTERNAL → Capital Guard join bindings from productive evidence.

Does not mutate decisions or envelopes. RUNTIME_AUTHORIZATION_EFFECT=NONE.
"""

from __future__ import annotations

import hashlib
import json
from contextvars import ContextVar
from contextvars import Token as _CtxReset
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_full_core_capital_guard_v1 import (
    OWNER_GO_FULL_CORE_PRE_POST,
    load_full_core_capital_guard_config_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    CurrentProductiveGovernedCycleResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
    FullCorePrePostCapitalGuardJoinBindingV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

VENUE_PLAN_DIGEST_SCHEMA = "full_core_venue_plan_digest.v1"
BINDING_CONTRACT_ID = "FULL_CORE_PRE_POST_CAPITAL_GUARD_BINDING_V1"


class FullCoreCapitalGuardBindingError(RuntimeError):
    """Fail-closed binding construction."""


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_full_core_venue_plan_digest_from_envelope_v1(
    envelope: FinalOrderEnvelopeV1,
) -> str:
    """Canonical digest of venue-plan-bound fields carried by FinalOrderEnvelopeV1."""
    assert_envelope_unmodified_v1(envelope)
    payload = {
        "schema_version": VENUE_PLAN_DIGEST_SCHEMA,
        "instrument_id": envelope.instrument_id,
        "side": envelope.side,
        "order_type": envelope.order_type,
        "quantity": envelope.quantity,
        "quantity_unit": envelope.quantity_unit,
        "price": envelope.price,
        "td_mode": envelope.td_mode,
        "pos_side": envelope.pos_side,
        "reduce_only": envelope.reduce_only is True,
        "client_order_id": envelope.client_order_id,
        "path_kind": envelope.path_kind,
        "venue_plan_clordid": envelope.venue_plan_clordid,
        "quantity_source": envelope.quantity_source,
        "side_source": envelope.side_source,
        "instrument_source": envelope.instrument_source,
        "provenance_ref": envelope.provenance_ref,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FullCoreCapitalGuardInstrumentMetadataV1:
    ct_val: str
    min_sz: str
    lot_sz: str

    def to_dict(self) -> dict[str, str]:
        return {"ct_val": self.ct_val, "min_sz": self.min_sz, "lot_sz": self.lot_sz}


def extract_instrument_contract_metadata_v1(
    instruments_payload: Mapping[str, Any] | None,
    *,
    instrument_id: str,
) -> FullCoreCapitalGuardInstrumentMetadataV1:
    if instruments_payload is None:
        raise FullCoreCapitalGuardBindingError("INSTRUMENTS_PAYLOAD_MISSING")
    data = instruments_payload.get("data")
    if not isinstance(data, list):
        raise FullCoreCapitalGuardBindingError("INSTRUMENTS_DATA_MISSING")
    native = str(instrument_id or "").strip()
    row: Mapping[str, Any] | None = None
    for item in data:
        if isinstance(item, Mapping) and str(item.get("instId") or "") == native:
            row = item
            break
    if row is None:
        raise FullCoreCapitalGuardBindingError("INSTRUMENT_ROW_NOT_FOUND")
    ct_val = str(row.get("ctVal") or "").strip()
    min_sz = str(row.get("minSz") or "").strip()
    lot_sz = str(row.get("lotSz") or "").strip()
    if not ct_val or not min_sz or not lot_sz:
        raise FullCoreCapitalGuardBindingError("INSTRUMENT_METADATA_INCOMPLETE")
    return FullCoreCapitalGuardInstrumentMetadataV1(
        ct_val=ct_val,
        min_sz=min_sz,
        lot_sz=lot_sz,
    )


def _selected_direction_from_master_v2_v1(master_v2_decision: str) -> str:
    text = str(master_v2_decision or "").strip().lower()
    if text == "enter_long" or "enter_long" in text:
        return "ENTER_LONG"
    if text == "enter_short" or "enter_short" in text:
        return "ENTER_SHORT"
    return str(master_v2_decision or "").strip().upper() or "UNKNOWN"


def build_full_core_capital_guard_join_binding_v1(
    *,
    canonical_decision_id: str,
    bound_instrument: BoundInstrumentV1,
    envelope: FinalOrderEnvelopeV1,
    master_v2_decision: str,
    account_identity: str,
    environment: str,
    origin_main_sha: str,
    execution_mode: str = "PRODUCTIVE_READ_ONLY",
    guard_config_digest: str | None = None,
    instrument_metadata: FullCoreCapitalGuardInstrumentMetadataV1,
    pre_external_reached: bool,
    terminal_disposition: str,
) -> FullCorePrePostCapitalGuardJoinBindingV1:
    assert_envelope_unmodified_v1(envelope)
    cfg_digest = guard_config_digest or load_full_core_capital_guard_config_v1().config_digest
    native = str(bound_instrument.venue_native_id or bound_instrument.native_id or "").strip()
    if not native:
        raise FullCoreCapitalGuardBindingError("NATIVE_ID_MISSING")
    return FullCorePrePostCapitalGuardJoinBindingV1(
        canonical_decision_id=str(canonical_decision_id or "").strip(),
        native_id=native,
        instrument_id=str(envelope.instrument_id),
        selected_direction=_selected_direction_from_master_v2_v1(master_v2_decision),
        order_side=str(envelope.side),
        final_quantity=str(envelope.quantity),
        order_type=str(envelope.order_type),
        order_price=str(envelope.price),
        venue_plan_digest=compute_full_core_venue_plan_digest_from_envelope_v1(envelope),
        envelope_digest=str(envelope.envelope_digest),
        account_identity=str(account_identity or "").strip(),
        environment=str(environment or "").strip(),
        execution_mode=str(execution_mode or "").strip(),
        owner_go=OWNER_GO_FULL_CORE_PRE_POST,
        origin_main_sha=str(origin_main_sha or "").strip().lower(),
        guard_config_digest=str(cfg_digest).strip().lower(),
        clordid=str(envelope.client_order_id),
        pre_external_reached=pre_external_reached is True,
        terminal_disposition=str(terminal_disposition),
        ct_val=instrument_metadata.ct_val,
        min_sz=instrument_metadata.min_sz,
        lot_sz=instrument_metadata.lot_sz,
    )


@dataclass(frozen=True)
class FullCoreCapitalGuardHandoffContextV1:
    bound_instrument: BoundInstrumentV1
    canonical_decision_id: str
    account_identity: str
    environment: str
    origin_main_sha: str
    instrument_metadata: FullCoreCapitalGuardInstrumentMetadataV1 | None = None
    reference_mark_px: str | None = None


_handoff_ctx: ContextVar[FullCoreCapitalGuardHandoffContextV1 | None] = ContextVar(
    "full_core_capital_guard_handoff_ctx_v1",
    default=None,
)


def bind_full_core_capital_guard_handoff_context_v1(
    ctx: FullCoreCapitalGuardHandoffContextV1 | None,
) -> _CtxReset:
    return _handoff_ctx.set(ctx)


def reset_full_core_capital_guard_handoff_context_v1(token: _CtxReset) -> None:
    _handoff_ctx.reset(token)


def active_full_core_capital_guard_handoff_context_v1() -> (
    FullCoreCapitalGuardHandoffContextV1 | None
):
    return _handoff_ctx.get()


def try_build_binding_from_governed_cycle_pre_external_v1(
    *,
    cycle: CurrentProductiveGovernedCycleResultV1,
    bound_instrument: BoundInstrumentV1 | None,
    canonical_decision_id: str,
    account_identity: str,
    environment: str,
    origin_main_sha: str,
    instrument_metadata: FullCoreCapitalGuardInstrumentMetadataV1 | None,
) -> FullCorePrePostCapitalGuardJoinBindingV1 | None:
    if str(cycle.disposition) != DISPOSITION_PRE_EXTERNAL_EFFECT:
        return None
    envelope = cycle.final_order_envelope
    if envelope is None or not isinstance(envelope, FinalOrderEnvelopeV1):
        return None
    if bound_instrument is None or instrument_metadata is None:
        return None
    if not str(canonical_decision_id or "").strip():
        return None
    if not str(account_identity or "").strip():
        return None
    return build_full_core_capital_guard_join_binding_v1(
        canonical_decision_id=canonical_decision_id,
        bound_instrument=bound_instrument,
        envelope=envelope,
        master_v2_decision=str(cycle.master_v2_decision or ""),
        account_identity=account_identity,
        environment=environment,
        origin_main_sha=origin_main_sha,
        instrument_metadata=instrument_metadata,
        pre_external_reached=True,
        terminal_disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
    )


__all__ = [
    "BINDING_CONTRACT_ID",
    "FullCoreCapitalGuardBindingError",
    "FullCoreCapitalGuardHandoffContextV1",
    "FullCoreCapitalGuardInstrumentMetadataV1",
    "active_full_core_capital_guard_handoff_context_v1",
    "bind_full_core_capital_guard_handoff_context_v1",
    "reset_full_core_capital_guard_handoff_context_v1",
    "build_full_core_capital_guard_join_binding_v1",
    "compute_full_core_venue_plan_digest_from_envelope_v1",
    "extract_instrument_contract_metadata_v1",
    "try_build_binding_from_governed_cycle_pre_external_v1",
]
