"""Offline post-action flatten proof contract for §11.13.5.

Evaluates caller-supplied snapshots only. Never GETs, never POSTs, never
enables live wire, and never claims LIVE_FLATTEN_PROVABILITY=PROVEN.
Required productive proof sequence remains:

PRE_POS != 0 then POS == 0, PENDING == EMPTY, NO_FLIP,
NO_UNEXPECTED_RELATED_INSTRUMENT_POSITION.

§11.13.5.Z2CL CHOICE_B: after an explicitly proven pre-target nonzero
and a later authorized flatten mutation that is causally bound to this
evaluation, absence of a target nonzero row in a valid post envelope
may satisfy the POS==0 predicate. That rule is scoped to this consumer
only. Missing target does not prove NO_FLIP. Pre-send missing remains
TARGET_INSTRUMENT_NOT_OBSERVED and is not zero. Empty pre+post remains
ALREADY_FLAT_NOOP, not productive success. data=None / parse failure
cannot become empty success.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
    ORDER_COUNT_LIMIT,
    POSITION_COUNT_LIMIT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    LIVE_FLATTEN_PROVABILITY_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    POSITION_OBSERVATION_FRESHNESS_POLICY as _POSITION_OBSERVATION_FRESHNESS_POLICY,
    PositionObservationFreshnessEvidenceV1,
    REASON_POST_ACTION_CONSUME,
    REASON_SAME_GET_DUAL_USE,
    reject_same_get_pre_send_and_post_readback_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPositionObservationError,
    LiveCanaryPreSubmitStateError,
    open_order_instruments_v1,
)


class LiveCanaryFlattenPostActionProofError(RuntimeError):
    """Fail-closed post-action flatten proof-contract violation."""


FLATTEN_POST_ACTION_PROOF_CONTRACT_IMPLEMENTED = True
FLATTEN_POST_ACTION_PROOF_PRODUCTIVE_SEQUENCE_REQUIRED = True
POST_ACTION_SUCCESS_PREDICATE_STATUS = "BOUND_CHOICE_B"
POST_ACTION_MISSING_TARGET_MAY_SATISFY_POS_EQ_0 = True
POST_ACTION_SCOPE = "FLATTEN_POST_ACTION_SUCCESS_EVALUATOR_ONLY"
POST_ACTION_REQUIRES_EXPLICIT_PRE_NONZERO = True
POST_ACTION_REQUIRES_CAUSAL_SUBMIT_BINDING = True
P7_3_EMPTY_DATA_IS_ZERO = False
POSITION_OBSERVATION_FRESHNESS_POLICY = _POSITION_OBSERVATION_FRESHNESS_POLICY
NETWORK_EFFECT_NONE = "none"
ORDER_EFFECT_NONE = "none"
ACCOUNT_MUTATION_EFFECT_NONE = "none"


@dataclass(frozen=True)
class FlattenPostActionSubmitEvidenceV1:
    """Caller-supplied submit linkage. Does not invent a GET or venue proof."""

    receipt_allowed: bool
    approved_request_identity: str
    gate_digest: str
    instrument_id: str
    send_attempted: bool
    wire_attempted: bool
    transport_call_completed: bool
    send_completed: bool
    http_status: int | None
    post_readback_after_submit: bool
    flatten_position_proven: bool = False
    venue_acceptance_proven: bool = False
    pre_send_freshness_evidence: PositionObservationFreshnessEvidenceV1 | None = None
    pre_send_get_identity: str | None = None
    post_readback_get_identity: str | None = None


def flatten_post_action_submit_evidence_from_submit_result_v1(
    result: Any,
    *,
    post_readback_after_submit: bool,
) -> FlattenPostActionSubmitEvidenceV1:
    """Project a gated-submit result into post-action causal evidence."""
    receipt = getattr(result, "receipt", None)
    instrument_id = DEFAULT_INSTRUMENT_ID
    if receipt is not None and isinstance(getattr(receipt, "request_body", None), dict):
        instrument_id = str(receipt.request_body.get("instId") or DEFAULT_INSTRUMENT_ID)
    return FlattenPostActionSubmitEvidenceV1(
        receipt_allowed=bool(getattr(result, "allowed", False))
        and bool(getattr(receipt, "allowed", False)),
        approved_request_identity=str(getattr(receipt, "approved_request_identity", "") or ""),
        gate_digest=str(getattr(receipt, "gate_digest", "") or ""),
        instrument_id=instrument_id,
        send_attempted=bool(getattr(result, "send_attempted", False)),
        wire_attempted=bool(getattr(result, "wire_attempted", False))
        or bool(getattr(result, "network_used", False)),
        transport_call_completed=bool(getattr(result, "transport_call_completed", False)),
        send_completed=bool(getattr(result, "send_completed", False)),
        http_status=getattr(result, "http_status", None),
        post_readback_after_submit=bool(post_readback_after_submit),
        flatten_position_proven=bool(getattr(result, "flatten_position_proven", False)),
        venue_acceptance_proven=bool(getattr(result, "venue_acceptance_proven", False)),
        pre_send_freshness_evidence=getattr(result, "pre_send_freshness_evidence", None),
        pre_send_get_identity=getattr(result, "pre_send_get_identity", None),
        post_readback_get_identity=getattr(result, "post_readback_get_identity", None),
    )


@dataclass(frozen=True)
class CanaryFlattenPostActionProofVerdictV1:
    """Offline classification. Fixture satisfaction is not productive proof."""

    instrument_id: str
    contract_state: str
    already_flat_noop: bool
    offline_contract_satisfied: bool
    pre_pos_nonzero: bool
    post_pos_zero: bool
    pending_empty: bool
    no_flip: bool
    no_unexpected_related_instrument_position: bool
    submit_authorized: bool
    submit_reachable: bool
    live_wire_enabled: bool
    live_authorized: bool
    live_flatten_provability: str
    productive_sequence_required: bool
    network_effect: str
    order_effect: str
    account_mutation_effect: str
    blocking_reasons: tuple[str, ...]
    pre_signed_pos: str
    post_signed_pos: str
    related_nonzero_instruments: tuple[str, ...]
    open_order_instruments: tuple[str, ...]
    post_target_observed: bool = False
    causal_submit_bound: bool = False
    choice_b_pos_eq_0: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "contract_state": self.contract_state,
            "already_flat_noop": self.already_flat_noop,
            "offline_contract_satisfied": self.offline_contract_satisfied,
            "pre_pos_nonzero": self.pre_pos_nonzero,
            "post_pos_zero": self.post_pos_zero,
            "pending_empty": self.pending_empty,
            "no_flip": self.no_flip,
            "no_unexpected_related_instrument_position": (
                self.no_unexpected_related_instrument_position
            ),
            "submit_authorized": self.submit_authorized,
            "submit_reachable": self.submit_reachable,
            "live_wire_enabled": self.live_wire_enabled,
            "live_authorized": self.live_authorized,
            "live_flatten_provability": self.live_flatten_provability,
            "productive_sequence_required": self.productive_sequence_required,
            "network_effect": self.network_effect,
            "order_effect": self.order_effect,
            "account_mutation_effect": self.account_mutation_effect,
            "blocking_reasons": list(self.blocking_reasons),
            "pre_signed_pos": self.pre_signed_pos,
            "post_signed_pos": self.post_signed_pos,
            "related_nonzero_instruments": list(self.related_nonzero_instruments),
            "open_order_instruments": list(self.open_order_instruments),
            "post_target_observed": self.post_target_observed,
            "causal_submit_bound": self.causal_submit_bound,
            "choice_b_pos_eq_0": self.choice_b_pos_eq_0,
        }


def _require_valid_envelope_rows(
    payload: Mapping[str, Any],
    *,
    label: str,
) -> tuple[list[Mapping[str, Any]] | None, str | None]:
    """Valid code==0 list envelope. data=None / missing data is not empty success."""
    if not isinstance(payload, Mapping):
        return None, f"{label}_PAYLOAD_NOT_MAPPING"
    if "code" not in payload:
        return None, f"{label}_CODE_MISSING"
    if str(payload.get("code") or "") != "0":
        return None, f"{label}_EXCHANGE_STATE_PAYLOAD_NOT_OK"
    if "data" not in payload:
        return None, f"{label}_DATA_MISSING"
    data = payload["data"]
    if data is None:
        return None, f"{label}_DATA_NONE"
    if not isinstance(data, list):
        return None, f"{label}_DATA_NOT_LIST"
    rows: list[Mapping[str, Any]] = []
    for row in data:
        if not isinstance(row, Mapping):
            return None, f"{label}_ROW_NOT_MAPPING"
        rows.append(row)
    return rows, None


def _signed_from_row(row: Mapping[str, Any]) -> tuple[Decimal | None, str | None]:
    if "pos" in row and row["pos"] is not None:
        raw = row["pos"]
    elif "posSize" in row and row["posSize"] is not None:
        raw = row["posSize"]
    else:
        return None, "POSITION_SIZE_MISSING"
    text = str(raw).strip()
    if not text:
        return None, "POSITION_SIZE_MISSING"
    try:
        return Decimal(text), None
    except (InvalidOperation, TypeError, ValueError):
        return None, "POSITION_SIZE_UNPARSEABLE"


def _nonzero_map_and_seen(
    rows: list[Mapping[str, Any]],
) -> tuple[dict[str, Decimal] | None, set[str], str | None]:
    out: dict[str, Decimal] = {}
    seen: dict[str, int] = {}
    observed: set[str] = set()
    for row in rows:
        inst = str(row.get("instId") or "").strip()
        if not inst:
            return None, set(), "POSITION_INSTID_MISSING"
        seen[inst] = seen.get(inst, 0) + 1
        observed.add(inst)
        signed, err = _signed_from_row(row)
        if err:
            return None, set(), err
        assert signed is not None
        if signed != 0:
            out[inst] = signed
    for inst, count in seen.items():
        if count != 1:
            return None, set(), "AMBIGUOUS_TARGET_POSITION_ROWS"
    return out, observed, None


def _causal_submit_bound(
    evidence: FlattenPostActionSubmitEvidenceV1 | None,
    *,
    instrument_id: str,
) -> tuple[bool, tuple[str, ...]]:
    if evidence is None:
        return False, ("AUTHORIZED_FLATTEN_MUTATION_UNPROVEN",)
    reasons: list[str] = []
    if not evidence.receipt_allowed:
        reasons.append("AUTHORIZED_FLATTEN_MUTATION_UNPROVEN")
    if not str(evidence.approved_request_identity or "").strip():
        reasons.append("SUBMIT_RECEIPT_IDENTITY_MISSING")
    if str(evidence.instrument_id or "").strip() != instrument_id:
        reasons.append("TARGET_INSTRUMENT_PRE_POST_MISMATCH")
    if not evidence.send_attempted:
        reasons.append("SUBMIT_NOT_ATTEMPTED")
    if not evidence.wire_attempted:
        reasons.append("TRANSPORT_FAILURE_BEFORE_WIRE")
    if not evidence.send_completed:
        reasons.append("TRANSPORT_SEND_NOT_COMPLETED")
    status = evidence.http_status
    if status is None or not (200 <= int(status) < 300):
        reasons.append("TRANSPORT_HTTP_NOT_2XX")
    if not evidence.post_readback_after_submit:
        reasons.append("POST_READBACK_NOT_AFTER_SUBMIT")
    if evidence.flatten_position_proven:
        reasons.append("FLATTEN_POSITION_MUST_REMAIN_UNPROVEN_ON_SUBMIT_EVIDENCE")
    return (not reasons, tuple(reasons))


def _verdict(
    *,
    instrument_id: str,
    contract_state: str,
    already_flat_noop: bool,
    offline_contract_satisfied: bool,
    pre_pos: Decimal,
    post_pos: Decimal,
    pending_empty: bool,
    no_flip: bool,
    no_related: bool,
    related: tuple[str, ...],
    open_orders: tuple[str, ...],
    blocking_reasons: tuple[str, ...],
    post_target_observed: bool = False,
    causal_submit_bound: bool = False,
    choice_b_pos_eq_0: bool = False,
) -> CanaryFlattenPostActionProofVerdictV1:
    if LIVE_AUTHORIZED or DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED:
        raise LiveCanaryFlattenPostActionProofError("LIVE_WIRE_MUST_REMAIN_DISABLED")
    if ORDER_COUNT_LIMIT != 1 or POSITION_COUNT_LIMIT != 1:
        raise LiveCanaryFlattenPostActionProofError("COUNT_LIMITS_MUST_REMAIN_1")
    post_pos_zero_proven = bool(choice_b_pos_eq_0) or (bool(post_target_observed) and post_pos == 0)
    return CanaryFlattenPostActionProofVerdictV1(
        instrument_id=instrument_id,
        contract_state=contract_state,
        already_flat_noop=already_flat_noop,
        offline_contract_satisfied=offline_contract_satisfied,
        pre_pos_nonzero=pre_pos != 0,
        post_pos_zero=post_pos_zero_proven,
        pending_empty=pending_empty,
        no_flip=no_flip,
        no_unexpected_related_instrument_position=no_related,
        submit_authorized=False,
        submit_reachable=False,
        live_wire_enabled=False,
        live_authorized=False,
        live_flatten_provability=LIVE_FLATTEN_PROVABILITY_STATUS,
        productive_sequence_required=FLATTEN_POST_ACTION_PROOF_PRODUCTIVE_SEQUENCE_REQUIRED,
        network_effect=NETWORK_EFFECT_NONE,
        order_effect=ORDER_EFFECT_NONE,
        account_mutation_effect=ACCOUNT_MUTATION_EFFECT_NONE,
        blocking_reasons=blocking_reasons,
        pre_signed_pos=format(pre_pos, "f"),
        post_signed_pos=format(post_pos, "f"),
        related_nonzero_instruments=related,
        open_order_instruments=open_orders,
        post_target_observed=post_target_observed,
        causal_submit_bound=causal_submit_bound,
        choice_b_pos_eq_0=choice_b_pos_eq_0,
    )


def evaluate_canary_flatten_post_action_proof_contract_v1(
    *,
    pre_positions_payload: Mapping[str, Any],
    post_positions_payload: Mapping[str, Any],
    post_pending_orders_payload: Mapping[str, Any],
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    pre_pending_orders_payload: Mapping[str, Any] | None = None,
    submit_evidence: FlattenPostActionSubmitEvidenceV1 | None = None,
) -> CanaryFlattenPostActionProofVerdictV1:
    """Classify pre/post snapshots against the flatten proof contract.

    Never authorizes submit. Offline satisfaction is not productive proof.
    Choice-B missing-target POS==0 requires causal submit evidence.
    """
    target = str(instrument_id or "").strip()
    if not target:
        raise LiveCanaryFlattenPostActionProofError("TARGET_INSTRUMENT_REQUIRED")
    if target != DEFAULT_INSTRUMENT_ID:
        raise LiveCanaryFlattenPostActionProofError("INSTRUMENT_BINDING_MISMATCH")

    if submit_evidence is not None and submit_evidence.pre_send_freshness_evidence is not None:
        return _verdict(
            instrument_id=target,
            contract_state="FLATTEN_PROOF_FAIL_CLOSED",
            already_flat_noop=False,
            offline_contract_satisfied=False,
            pre_pos=Decimal("0"),
            post_pos=Decimal("0"),
            pending_empty=False,
            no_flip=False,
            no_related=False,
            related=(),
            open_orders=(),
            blocking_reasons=(REASON_POST_ACTION_CONSUME,),
        )
    if submit_evidence is not None:
        dual = reject_same_get_pre_send_and_post_readback_v1(
            pre_send_get_identity=submit_evidence.pre_send_get_identity,
            post_readback_get_identity=submit_evidence.post_readback_get_identity,
        )
        if dual == REASON_SAME_GET_DUAL_USE:
            return _verdict(
                instrument_id=target,
                contract_state="FLATTEN_PROOF_FAIL_CLOSED",
                already_flat_noop=False,
                offline_contract_satisfied=False,
                pre_pos=Decimal("0"),
                post_pos=Decimal("0"),
                pending_empty=False,
                no_flip=False,
                no_related=False,
                related=(),
                open_orders=(),
                blocking_reasons=(REASON_SAME_GET_DUAL_USE,),
            )

    pre_rows, pre_err = _require_valid_envelope_rows(pre_positions_payload, label="PRE")
    if pre_err:
        return _verdict(
            instrument_id=target,
            contract_state="FLATTEN_PROOF_FAIL_CLOSED",
            already_flat_noop=False,
            offline_contract_satisfied=False,
            pre_pos=Decimal("0"),
            post_pos=Decimal("0"),
            pending_empty=False,
            no_flip=False,
            no_related=False,
            related=(),
            open_orders=(),
            blocking_reasons=(pre_err,),
        )
    post_rows, post_err = _require_valid_envelope_rows(post_positions_payload, label="POST")
    if post_err:
        return _verdict(
            instrument_id=target,
            contract_state="FLATTEN_PROOF_FAIL_CLOSED",
            already_flat_noop=False,
            offline_contract_satisfied=False,
            pre_pos=Decimal("0"),
            post_pos=Decimal("0"),
            pending_empty=False,
            no_flip=False,
            no_related=False,
            related=(),
            open_orders=(),
            blocking_reasons=(post_err,),
        )
    pending_rows, pending_err = _require_valid_envelope_rows(
        post_pending_orders_payload, label="POST_PENDING"
    )
    if pending_err:
        return _verdict(
            instrument_id=target,
            contract_state="FLATTEN_PROOF_FAIL_CLOSED",
            already_flat_noop=False,
            offline_contract_satisfied=False,
            pre_pos=Decimal("0"),
            post_pos=Decimal("0"),
            pending_empty=False,
            no_flip=False,
            no_related=False,
            related=(),
            open_orders=(),
            blocking_reasons=(pending_err,),
        )

    try:
        assert pre_rows is not None and post_rows is not None and pending_rows is not None
        pre_positions, pre_seen, pre_map_err = _nonzero_map_and_seen(pre_rows)
        if pre_map_err:
            raise LiveCanaryPositionObservationError(pre_map_err)
        post_positions, post_seen, post_map_err = _nonzero_map_and_seen(post_rows)
        if post_map_err:
            raise LiveCanaryPositionObservationError(post_map_err)
        assert pre_positions is not None and post_positions is not None
        open_orders = tuple(
            str(row.get("instId") or row.get("instID") or "").strip()
            for row in pending_rows
            if str(row.get("instId") or row.get("instID") or "").strip()
        )
        if any(
            not str(row.get("instId") or row.get("instID") or "").strip() for row in pending_rows
        ):
            raise LiveCanaryPreSubmitStateError("OPEN_ORDER_INSTID_MISSING")
        pre_open_orders: tuple[str, ...] = ()
        if pre_pending_orders_payload is not None:
            pre_open_orders = open_order_instruments_v1(pre_pending_orders_payload)
    except (LiveCanaryPositionObservationError, LiveCanaryPreSubmitStateError) as exc:
        return _verdict(
            instrument_id=target,
            contract_state="FLATTEN_PROOF_FAIL_CLOSED",
            already_flat_noop=False,
            offline_contract_satisfied=False,
            pre_pos=Decimal("0"),
            post_pos=Decimal("0"),
            pending_empty=False,
            no_flip=False,
            no_related=False,
            related=(),
            open_orders=(),
            blocking_reasons=(str(exc),),
        )

    pre_target_observed = target in pre_seen
    post_target_observed = target in post_seen
    pre_pos = pre_positions.get(target, Decimal("0")) if pre_target_observed else Decimal("0")
    post_nonzero = post_positions.get(target, Decimal("0")) if target in post_positions else None
    related = tuple(sorted(inst for inst in post_positions if inst != target))
    pre_related = tuple(sorted(inst for inst in pre_positions if inst != target))
    pending_empty = len(open_orders) == 0
    no_related = len(related) == 0
    reasons: list[str] = []
    causal_ok, causal_reasons = _causal_submit_bound(submit_evidence, instrument_id=target)

    choice_b_pos_eq_0 = False
    if post_nonzero is not None:
        post_pos = post_nonzero
    elif post_target_observed:
        post_pos = Decimal("0")
    elif causal_ok and pre_pos != 0:
        post_pos = Decimal("0")
        choice_b_pos_eq_0 = True
    else:
        post_pos = Decimal("0")
        if pre_pos != 0:
            reasons.append("POST_TARGET_NOT_OBSERVED")
            if submit_evidence is None:
                reasons.append("AUTHORIZED_FLATTEN_MUTATION_UNPROVEN")
            else:
                reasons.extend(causal_reasons)

    if post_target_observed:
        no_flip = not (pre_pos != 0 and post_pos != 0 and (pre_pos > 0) != (post_pos > 0))
        if not no_flip:
            reasons.append("FLIP_DETECTED")
    else:
        no_flip = False
        if pre_pos != 0:
            reasons.append("NO_FLIP_UNPROVEN_TARGET_MISSING")

    if pre_related:
        reasons.append("UNEXPECTED_RELATED_INSTRUMENT_POSITION_PRE")
    if related:
        reasons.append("UNEXPECTED_RELATED_INSTRUMENT_POSITION")
    if pre_open_orders:
        reasons.append("OPEN_ORDER_PRESENT_BEFORE_FLATTEN")
    if not pending_empty:
        reasons.append("PENDING_NOT_EMPTY")

    already_flat_eligible = (
        (not pre_target_observed or pre_pos == 0)
        and (not post_target_observed or post_pos == 0)
        and pending_empty
        and no_related
        and not pre_related
        and not choice_b_pos_eq_0
    )
    if already_flat_eligible:
        if pre_open_orders:
            reasons.append("ALREADY_FLAT_BUT_OPEN_ORDER_PRESENT")
            return _verdict(
                instrument_id=target,
                contract_state="FLATTEN_PROOF_FAIL_CLOSED",
                already_flat_noop=False,
                offline_contract_satisfied=False,
                pre_pos=pre_pos,
                post_pos=post_pos,
                pending_empty=pending_empty,
                no_flip=True,
                no_related=no_related,
                related=related,
                open_orders=open_orders,
                blocking_reasons=tuple(reasons),
                post_target_observed=post_target_observed,
                causal_submit_bound=causal_ok,
                choice_b_pos_eq_0=False,
            )
        return _verdict(
            instrument_id=target,
            contract_state="ALREADY_FLAT_NOOP",
            already_flat_noop=True,
            offline_contract_satisfied=False,
            pre_pos=pre_pos,
            post_pos=post_pos,
            pending_empty=True,
            no_flip=True,
            no_related=True,
            related=(),
            open_orders=open_orders,
            blocking_reasons=("ZERO_POSITION_NO_FLATTEN_ORDER",),
            post_target_observed=post_target_observed,
            causal_submit_bound=causal_ok,
            choice_b_pos_eq_0=False,
        )

    if pre_pos == 0:
        reasons.append("PRE_POS_ZERO")
    if post_pos != 0:
        reasons.append("POST_NOT_FLAT")

    unique_reasons = tuple(dict.fromkeys(reasons))
    if (
        pre_pos != 0
        and post_pos == 0
        and pending_empty
        and no_flip
        and no_related
        and not pre_related
        and not pre_open_orders
        and post_target_observed
    ):
        return _verdict(
            instrument_id=target,
            contract_state="OFFLINE_CONTRACT_SATISFIED_PRODUCTIVE_SEQUENCE_REQUIRED",
            already_flat_noop=False,
            offline_contract_satisfied=True,
            pre_pos=pre_pos,
            post_pos=post_pos,
            pending_empty=True,
            no_flip=True,
            no_related=True,
            related=(),
            open_orders=open_orders,
            blocking_reasons=("PRODUCTIVE_LIVE_FLATTEN_SEQUENCE_NOT_EXECUTED",),
            post_target_observed=True,
            causal_submit_bound=causal_ok,
            choice_b_pos_eq_0=False,
        )

    if not unique_reasons:
        unique_reasons = ("FLATTEN_PROOF_FAIL_CLOSED",)
    return _verdict(
        instrument_id=target,
        contract_state="FLATTEN_PROOF_FAIL_CLOSED",
        already_flat_noop=False,
        offline_contract_satisfied=False,
        pre_pos=pre_pos,
        post_pos=post_pos,
        pending_empty=pending_empty,
        no_flip=no_flip,
        no_related=no_related and not pre_related,
        related=related or pre_related,
        open_orders=open_orders,
        blocking_reasons=unique_reasons,
        post_target_observed=post_target_observed,
        causal_submit_bound=causal_ok,
        choice_b_pos_eq_0=choice_b_pos_eq_0,
    )
