"""Technical risk-reduction proof for a RISK_REDUCING one-shot venue POST envelope.

SELF_DECLARED_RISK_REDUCING != PROVEN_RISK_REDUCING. An envelope label,
provenance constant, or self-computed envelope digest is not a reduction proof.
The proof binds the exact envelope to fresh authenticated read-only venue
evidence (account config, positions, pending orders) obtained through the same
K1-bound read transport that precedes the POST.

Position-mode semantics are distinguished explicitly:

- ``net_mode``: exactly one open ``posSide=net`` row; order side must be the
  opposite of the signed position; venue ``reduceOnly`` prevents a flip.
- ``long_short_mode``: envelope ``posSide`` must name the open leg; the close side
  for that leg (sell/long, buy/short) cannot open exposure. OKX documents
  ``reduceOnly`` for derivatives only in net mode, so it is not relied upon here.

Missing, malformed, contradictory, or stale evidence -> RISK_REDUCTION_NOT_PROVEN.
Reuses the CURRENT exact-object flatten-plan side derivation.

Does not POST. RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Mapping, Optional
from urllib.parse import urlencode

from src.ops.full_core_live_path_composition_root_v1.current_productive_exact_object_flatten_plan_v1 import (
    CurrentProductiveExactObjectFlattenPlanError,
    flatten_side_from_net_pos_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_POSITIONS,
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    FullCoreFreshPretradeGetTransportV1,
)

CONTRACT_ID = "CURRENT_PRODUCTIVE_RISK_REDUCTION_VENUE_PROOF_V1"
ENDPOINT_ORDERS_PENDING = "/api/v5/trade/orders-pending"
MAX_PROOF_AGE_SECONDS = 15.0
MAX_FUTURE_SKEW_SECONDS = 1.0
POS_MODE_NET = "net_mode"
POS_MODE_LONG_SHORT = "long_short_mode"
SEMANTICS_NET = "NET_MODE_OPPOSITE_SIDE_REDUCE_ONLY"
SEMANTICS_LONG_SHORT = "LONG_SHORT_MODE_CLOSE_SIDE_FOR_OPEN_LEG"
NOT_PROVEN = "RISK_REDUCTION_NOT_PROVEN"


class RiskReductionNotProvenError(RuntimeError):
    """Fail-closed: risk reduction is not technically proven -> NO_POST."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"{NOT_PROVEN}:{reason}")
        self.reason = reason


@dataclass(frozen=True)
class RiskReductionVenueProofV1:
    envelope_id: str
    envelope_digest: str
    client_order_id: str
    instrument_id: str
    account_uid: str
    pos_mode: str
    position_side: str
    position_qty_abs: str
    order_side: str
    order_qty: str
    order_pos_side: str
    reduce_only_semantics: str
    pending_order_count: int
    observed_at_epoch_s: float
    proof_digest: str
    contract_id: str = CONTRACT_ID

    def material_v1(self) -> dict[str, Any]:
        material = asdict(self)
        material.pop("proof_digest", None)
        return material


def _proof_digest_v1(material: Mapping[str, Any]) -> str:
    blob = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _fail(reason: str) -> RiskReductionNotProvenError:
    return RiskReductionNotProvenError(reason)


def _ok_rows(payload: Any, label: str) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        raise _fail(f"{label}_PAYLOAD_MISSING")
    if str(payload.get("code") or "") != "0":
        raise _fail(f"{label}_VENUE_CODE_NON_ZERO")
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise _fail(f"{label}_PAYLOAD_MALFORMED")
    for row in rows:
        if not isinstance(row, Mapping):
            raise _fail(f"{label}_ROW_MALFORMED")
    return list(rows)


def _decimal(value: Any, reason: str) -> Decimal:
    text = str(value if value is not None else "").strip()
    if not text:
        raise _fail(reason)
    try:
        parsed = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise _fail(reason) from exc
    if not parsed.is_finite():
        raise _fail(reason)
    return parsed


def _fmt(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def prove_risk_reduction_from_venue_evidence_v1(
    *,
    envelope: FinalOrderEnvelopeV1,
    config_payload: Any,
    positions_payload: Any,
    pending_orders_payload: Any,
    observed_at_epoch_s: float,
) -> RiskReductionVenueProofV1:
    """Pure decision over already-acquired venue evidence (no network)."""
    assert_envelope_unmodified_v1(envelope)
    if envelope.reduce_only is not True:
        raise _fail("ENVELOPE_NOT_REDUCE_ONLY")
    instrument = str(envelope.instrument_id or "").strip()
    if not instrument:
        raise _fail("INSTRUMENT_IDENTITY_MISSING")
    order_side = str(envelope.side or "").strip().lower()
    if order_side not in {"buy", "sell"}:
        raise _fail("ORDER_SIDE_INVALID")
    order_qty = _decimal(envelope.quantity, "ORDER_QTY_MALFORMED")
    if order_qty <= 0:
        raise _fail("ORDER_QTY_NOT_POSITIVE")

    config_rows = _ok_rows(config_payload, "CONFIG")
    if len(config_rows) != 1:
        raise _fail("CONFIG_ROW_COUNT_NOT_ONE")
    config = config_rows[0]
    pos_mode = str(config.get("posMode") or "").strip()
    if pos_mode not in {POS_MODE_NET, POS_MODE_LONG_SHORT}:
        raise _fail("POSITION_MODE_UNSUPPORTED")
    account_uid = str(config.get("uid") or "").strip()
    if not account_uid:
        raise _fail("ACCOUNT_SCOPE_UNPROVEN")

    pending_rows = _ok_rows(pending_orders_payload, "PENDING_ORDERS")
    for row in pending_rows:
        if str(row.get("instId") or "") != instrument:
            raise _fail("PENDING_ORDER_INSTRUMENT_IDENTITY_AMBIGUOUS")
    if pending_rows:
        raise _fail("CONFLICTING_OPEN_ORDERS")

    open_rows: list[tuple[Mapping[str, Any], Decimal]] = []
    for row in _ok_rows(positions_payload, "POSITIONS"):
        if str(row.get("instId") or "") != instrument:
            raise _fail("POSITION_INSTRUMENT_IDENTITY_AMBIGUOUS")
        pos = _decimal(row.get("pos"), "POSITION_QTY_MALFORMED")
        if pos == 0:
            continue
        mgn_mode = str(row.get("mgnMode") or "").strip()
        if mgn_mode != str(envelope.td_mode or "").strip():
            raise _fail("MARGIN_MODE_MISMATCH")
        open_rows.append((row, pos))
    if not open_rows:
        raise _fail("NO_OPEN_POSITION")

    envelope_pos_side = str(envelope.pos_side or "").strip().lower()
    if pos_mode == POS_MODE_NET:
        if envelope_pos_side not in {"", "net"}:
            raise _fail("POS_SIDE_CONTRADICTS_NET_MODE")
        if len(open_rows) != 1:
            raise _fail("POSITION_IDENTITY_AMBIGUOUS")
        row, pos = open_rows[0]
        if str(row.get("posSide") or "").strip().lower() != "net":
            raise _fail("POS_SIDE_CONTRADICTS_NET_MODE")
        try:
            required_side = flatten_side_from_net_pos_v1(pos)
        except CurrentProductiveExactObjectFlattenPlanError as exc:
            raise _fail("NO_OPEN_POSITION") from exc
        position_side = "long" if pos > 0 else "short"
        position_abs = pos.copy_abs()
        semantics = SEMANTICS_NET
    else:
        if envelope_pos_side not in {"long", "short"}:
            raise _fail("POS_SIDE_REQUIRED_IN_LONG_SHORT_MODE")
        legs: dict[str, Decimal] = {}
        for row, pos in open_rows:
            leg = str(row.get("posSide") or "").strip().lower()
            if leg not in {"long", "short"} or leg in legs:
                raise _fail("POS_SIDE_CONTRADICTS_LONG_SHORT_MODE")
            legs[leg] = pos
        if len(legs) != 1:
            raise _fail("HEDGED_POSITION_REDUCTION_NOT_PROVEN")
        if envelope_pos_side not in legs:
            raise _fail("NO_OPEN_POSITION_FOR_POS_SIDE")
        pos = legs[envelope_pos_side]
        if pos <= 0:
            raise _fail("POSITION_SIGN_CONTRADICTS_POS_SIDE")
        required_side = "sell" if envelope_pos_side == "long" else "buy"
        position_side = envelope_pos_side
        position_abs = pos
        semantics = SEMANTICS_LONG_SHORT

    if order_side != required_side:
        raise _fail("ORDER_SIDE_DOES_NOT_REDUCE_POSITION")
    if order_qty > position_abs:
        raise _fail("ORDER_QTY_EXCEEDS_POSITION")

    material = {
        "envelope_id": envelope.envelope_id,
        "envelope_digest": envelope.envelope_digest,
        "client_order_id": envelope.client_order_id,
        "instrument_id": instrument,
        "account_uid": account_uid,
        "pos_mode": pos_mode,
        "position_side": position_side,
        "position_qty_abs": _fmt(position_abs),
        "order_side": order_side,
        "order_qty": _fmt(order_qty),
        "order_pos_side": envelope_pos_side,
        "reduce_only_semantics": semantics,
        "pending_order_count": 0,
        "observed_at_epoch_s": float(observed_at_epoch_s),
        "contract_id": CONTRACT_ID,
    }
    return RiskReductionVenueProofV1(**material, proof_digest=_proof_digest_v1(material))


def _require_fresh_get_v1(
    transport: FullCoreFreshPretradeGetTransportV1,
    *,
    endpoint: str,
    pretrade_decision_id: str,
) -> Any:
    try:
        result = transport.get(
            endpoint=endpoint,
            auth_required=True,
            pretrade_decision_id=pretrade_decision_id,
            get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )
    except Exception as exc:
        raise _fail(f"VENUE_GET_FAILED:{endpoint.split('?', 1)[0]}") from exc
    if result.get_performed is not True or result.payload is None:
        raise _fail(f"VENUE_GET_INCOMPLETE:{endpoint.split('?', 1)[0]}")
    if getattr(result, "historical_reuse", False) is True:
        raise _fail("VENUE_EVIDENCE_HISTORICAL_REUSE")
    return result.payload


def collect_and_prove_risk_reduction_v1(
    *,
    envelope: FinalOrderEnvelopeV1,
    read_only_get_transport: Optional[FullCoreFreshPretradeGetTransportV1],
    pretrade_decision_id: str,
    clock: Callable[[], float] = time.time,
) -> RiskReductionVenueProofV1:
    """Three authenticated read-only GETs, then the pure proof. Never POSTs."""
    assert_envelope_unmodified_v1(envelope)
    if read_only_get_transport is None:
        raise _fail("READ_ONLY_VENUE_TRANSPORT_REQUIRED")
    decision = str(pretrade_decision_id or "").strip()
    if not decision:
        raise _fail("PRETRADE_DECISION_ID_REQUIRED")
    query = urlencode({"instId": envelope.instrument_id})
    config_payload = _require_fresh_get_v1(
        read_only_get_transport, endpoint=ENDPOINT_ACCOUNT_CONFIG, pretrade_decision_id=decision
    )
    positions_payload = _require_fresh_get_v1(
        read_only_get_transport,
        endpoint=f"{ENDPOINT_ACCOUNT_POSITIONS}?{query}",
        pretrade_decision_id=decision,
    )
    pending_payload = _require_fresh_get_v1(
        read_only_get_transport,
        endpoint=f"{ENDPOINT_ORDERS_PENDING}?{query}",
        pretrade_decision_id=decision,
    )
    return prove_risk_reduction_from_venue_evidence_v1(
        envelope=envelope,
        config_payload=config_payload,
        positions_payload=positions_payload,
        pending_orders_payload=pending_payload,
        observed_at_epoch_s=float(clock()),
    )


def assert_risk_reduction_proof_valid_for_envelope_v1(
    *,
    proof: Optional[RiskReductionVenueProofV1],
    envelope: FinalOrderEnvelopeV1,
    now_epoch_s: Optional[float] = None,
    max_age_seconds: float = MAX_PROOF_AGE_SECONDS,
) -> RiskReductionVenueProofV1:
    """Integrity, envelope binding, and freshness of an existing proof."""
    if not isinstance(proof, RiskReductionVenueProofV1):
        raise _fail("PROOF_MISSING")
    assert_envelope_unmodified_v1(envelope)
    if proof.contract_id != CONTRACT_ID:
        raise _fail("PROOF_CONTRACT_MISMATCH")
    if _proof_digest_v1(proof.material_v1()) != proof.proof_digest:
        raise _fail("PROOF_DIGEST_MISMATCH")
    for actual, expected, label in (
        (proof.envelope_id, envelope.envelope_id, "ENVELOPE_ID"),
        (proof.envelope_digest, envelope.envelope_digest, "ENVELOPE_DIGEST"),
        (proof.client_order_id, envelope.client_order_id, "CLIENT_ORDER_ID"),
        (proof.instrument_id, envelope.instrument_id, "INSTRUMENT_ID"),
        (proof.order_side, str(envelope.side or "").strip().lower(), "ORDER_SIDE"),
    ):
        if str(actual) != str(expected):
            raise _fail(f"PROOF_{label}_MISMATCH")
    if _decimal(proof.order_qty, "PROOF_QTY_MALFORMED") != _decimal(
        envelope.quantity, "ORDER_QTY_MALFORMED"
    ):
        raise _fail("PROOF_ORDER_QTY_MISMATCH")
    if envelope.reduce_only is not True:
        raise _fail("ENVELOPE_NOT_REDUCE_ONLY")
    now = float(time.time() if now_epoch_s is None else now_epoch_s)
    age = now - float(proof.observed_at_epoch_s)
    if age < -MAX_FUTURE_SKEW_SECONDS:
        raise _fail("VENUE_EVIDENCE_FROM_FUTURE")
    if age > float(max_age_seconds):
        raise _fail("VENUE_EVIDENCE_STALE")
    return proof


__all__ = [
    "CONTRACT_ID",
    "ENDPOINT_ORDERS_PENDING",
    "MAX_PROOF_AGE_SECONDS",
    "NOT_PROVEN",
    "POS_MODE_LONG_SHORT",
    "POS_MODE_NET",
    "RiskReductionNotProvenError",
    "RiskReductionVenueProofV1",
    "assert_risk_reduction_proof_valid_for_envelope_v1",
    "collect_and_prove_risk_reduction_v1",
    "prove_risk_reduction_from_venue_evidence_v1",
]
