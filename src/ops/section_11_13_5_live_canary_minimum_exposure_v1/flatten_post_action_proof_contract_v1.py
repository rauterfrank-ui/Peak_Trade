"""Offline post-action flatten proof contract for §11.13.5.

Evaluates caller-supplied snapshots only. Never GETs, never POSTs, never
enables live wire, and never claims LIVE_FLATTEN_PROVABILITY=PROVEN.
Required productive proof sequence remains:

PRE_POS != 0 then POS == 0, PENDING == EMPTY, NO_FLIP,
NO_UNEXPECTED_RELATED_INSTRUMENT_POSITION.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPositionObservationError,
    LiveCanaryPreSubmitStateError,
    open_order_instruments_v1,
    signed_nonzero_positions_by_instrument_v1,
)


class LiveCanaryFlattenPostActionProofError(RuntimeError):
    """Fail-closed post-action flatten proof-contract violation."""


FLATTEN_POST_ACTION_PROOF_CONTRACT_IMPLEMENTED = True
FLATTEN_POST_ACTION_PROOF_PRODUCTIVE_SEQUENCE_REQUIRED = True
NETWORK_EFFECT_NONE = "none"
ORDER_EFFECT_NONE = "none"
ACCOUNT_MUTATION_EFFECT_NONE = "none"


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
        }


def _target_signed_pos(
    positions: Mapping[str, Decimal],
    *,
    instrument_id: str,
) -> Decimal:
    return positions.get(instrument_id, Decimal("0"))


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
) -> CanaryFlattenPostActionProofVerdictV1:
    if LIVE_AUTHORIZED or DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED:
        raise LiveCanaryFlattenPostActionProofError("LIVE_WIRE_MUST_REMAIN_DISABLED")
    if ORDER_COUNT_LIMIT != 1 or POSITION_COUNT_LIMIT != 1:
        raise LiveCanaryFlattenPostActionProofError("COUNT_LIMITS_MUST_REMAIN_1")
    return CanaryFlattenPostActionProofVerdictV1(
        instrument_id=instrument_id,
        contract_state=contract_state,
        already_flat_noop=already_flat_noop,
        offline_contract_satisfied=offline_contract_satisfied,
        pre_pos_nonzero=pre_pos != 0,
        post_pos_zero=post_pos == 0,
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
    )


def evaluate_canary_flatten_post_action_proof_contract_v1(
    *,
    pre_positions_payload: Mapping[str, Any],
    post_positions_payload: Mapping[str, Any],
    post_pending_orders_payload: Mapping[str, Any],
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    pre_pending_orders_payload: Mapping[str, Any] | None = None,
) -> CanaryFlattenPostActionProofVerdictV1:
    """Classify pre/post snapshots against the flatten proof contract.

    Never authorizes submit. Offline satisfaction is not productive proof.
    """
    target = str(instrument_id or "").strip()
    if not target:
        raise LiveCanaryFlattenPostActionProofError("TARGET_INSTRUMENT_REQUIRED")
    if target != DEFAULT_INSTRUMENT_ID:
        raise LiveCanaryFlattenPostActionProofError("INSTRUMENT_BINDING_MISMATCH")
    try:
        pre_positions = signed_nonzero_positions_by_instrument_v1(pre_positions_payload)
        post_positions = signed_nonzero_positions_by_instrument_v1(post_positions_payload)
        open_orders = open_order_instruments_v1(post_pending_orders_payload)
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

    pre_pos = _target_signed_pos(pre_positions, instrument_id=target)
    post_pos = _target_signed_pos(post_positions, instrument_id=target)
    related = tuple(sorted(inst for inst in post_positions if inst != target))
    pre_related = tuple(sorted(inst for inst in pre_positions if inst != target))
    pending_empty = len(open_orders) == 0
    no_related = len(related) == 0
    no_flip = not (pre_pos != 0 and post_pos != 0 and (pre_pos > 0) != (post_pos > 0))
    reasons: list[str] = []
    if pre_related:
        reasons.append("UNEXPECTED_RELATED_INSTRUMENT_POSITION_PRE")
    if related:
        reasons.append("UNEXPECTED_RELATED_INSTRUMENT_POSITION")
    if pre_open_orders:
        reasons.append("OPEN_ORDER_PRESENT_BEFORE_FLATTEN")
    if not pending_empty:
        reasons.append("PENDING_NOT_EMPTY")
    if not no_flip:
        reasons.append("FLIP_DETECTED")

    if pre_pos == 0 and post_pos == 0 and pending_empty and no_related and not pre_related:
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
        )

    if pre_pos == 0:
        reasons.append("PRE_POS_ZERO")
    if post_pos != 0:
        reasons.append("POST_NOT_FLAT")

    if (
        pre_pos != 0
        and post_pos == 0
        and pending_empty
        and no_flip
        and no_related
        and not pre_related
        and not pre_open_orders
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
        )

    if not reasons:
        reasons.append("FLATTEN_PROOF_FAIL_CLOSED")
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
        blocking_reasons=tuple(reasons),
    )
