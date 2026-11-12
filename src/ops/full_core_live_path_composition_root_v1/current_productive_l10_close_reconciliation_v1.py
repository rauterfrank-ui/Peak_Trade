"""Authenticated readback of the original one-shot L10 close."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
    read_submitted_occupied_scope_close_v1,
)
from src.ops.execution_reconciliation_get_provenance_v1 import (
    AuthenticatedReconciliationGetV1,
    require_futures_reconciliation_product_v1,
    resolve_reconciliation_query_options_v1,
)
from src.ops.execution_reconciliation_proof_store_v1 import (
    publish_authenticated_close_readback_v1,
    require_private_proof_root_v1,
)
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    PositionEpisodeScopeV1,
)
from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
    read_occupied_scope_mark_snapshot_v1,
)

from .current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
    POST_OWNER_GO,
    load_durable_post_owner_go_consume_v1,
)
from .current_productive_post_close_feedback_v1 import (
    PostCloseFeedbackRequestV1,
    _utc_ms,
    verify_post_close_position_v1,
)
from .current_productive_post_position_close_v1 import occupied_close_submit_root_v1
from .external_effect_permit_durable_consume_v1 import load_external_effect_durable_consume_v1
from .fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
)
from .full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    fetch_okx_read_only_reconciliation_snapshot_v1,
)
from .full_core_exchange_reconciliation_v1 import (
    EvidenceLayer,
    FullCoreExchangeReconciliationIdentityV1,
    LocalSubmitOutcome,
    OUTCOME_CONFIRMED_FILLED,
    OUTCOME_CONFIRMED_OPEN,
    OUTCOME_CONFIRMED_PARTIALLY_FILLED,
    REASON_TRANSPORT_UNKNOWN,
    adjudicate_full_core_exchange_reconciliation_v1,
)


@dataclass(frozen=True)
class AuthenticatedL10CloseReadbackV1:
    status: str
    envelope_digest: str
    reason_codes: tuple[str, ...] = ()
    filled_quantity: Decimal | None = None
    remaining_quantity: Decimal | None = None
    proof_path: Path | None = None


def _validate_close_order_and_fills_v1(
    *, snapshot, decision, envelope, inst_type, socket_ms, observed_ms
) -> Decimal:
    exact_rows = [
        item.payload for item in snapshot.evidence_items if item.source == "exact-order-lookup"
    ]
    if len(exact_rows) != 1 or not decision.venue_ord_id:
        raise ValueError("L10_CLOSE_EXACT_ORDER_UNPROVEN")
    order = exact_rows[0]
    state = order.get("state")
    if state in ("cancelled", "mmp_canceled"):
        state = "canceled"
    if (
        order.get("instId") != envelope.instrument_id
        or order.get("instType") != inst_type
        or order.get("clOrdId") != envelope.client_order_id
        or order.get("ordId") != decision.venue_ord_id
        or order.get("side") != envelope.side
        or order.get("posSide") != "net"
        or order.get("tdMode") != envelope.td_mode
        or order.get("ordType") != envelope.order_type
        or not (order.get("reduceOnly") is True or order.get("reduceOnly") == "true")
        or state != decision.order_state
        or Decimal(order["sz"]) != Decimal(envelope.quantity)
        or Decimal(order["accFillSz"]) != Decimal(decision.cumulative_filled_qty)
    ):
        raise ValueError("L10_CLOSE_EXACT_ORDER_MISMATCH")
    earliest = max(_utc_ms(envelope.creation_epoch), int(socket_ms))
    updated = Decimal(order["uTime"])
    if not updated.is_finite() or not earliest <= updated <= observed_ms:
        raise ValueError("L10_CLOSE_ORDER_TIME_UNPROVEN")
    fills = {}
    for item in snapshot.evidence_items:
        if item.layer is not EvidenceLayer.EXCHANGE_FILL_STATE:
            continue
        row = item.payload
        trade = row.get("tradeId", "")
        if (
            not isinstance(trade, str)
            or not trade.strip()
            or row.get("instId") != envelope.instrument_id
            or row.get("instType") != inst_type
            or row.get("clOrdId") != envelope.client_order_id
            or row.get("ordId") != decision.venue_ord_id
            or row.get("side") != envelope.side
            or row.get("posSide") != "net"
            or fills.setdefault(trade, row) != row
        ):
            raise ValueError("L10_CLOSE_FILL_IDENTITY_UNPROVEN")
        size, price, fill_time = map(Decimal, (row["fillSz"], row["fillPx"], row["fillTime"]))
        if not (
            all(value.is_finite() for value in (size, price, fill_time))
            and size > 0
            and price > 0
            and earliest <= fill_time <= updated
        ):
            raise ValueError("L10_CLOSE_FILL_VALUE_OR_TIME_UNPROVEN")
    if not fills or sum(Decimal(row["fillSz"]) for row in fills.values()) != Decimal(
        decision.cumulative_filled_qty
    ):
        raise ValueError("L10_CLOSE_FILL_SET_INCOMPLETE")
    return max(Decimal(row["fillTime"]) for row in fills.values())


def reconcile_submitted_occupied_scope_close_v1(
    *, lane_pair, budget_host, proof_root: Path
) -> AuthenticatedL10CloseReadbackV1 | None:
    """Recover a pending close before touching current entry or budget admission."""
    slot, bound = lane_pair
    scope = read_occupied_scope_mark_snapshot_v1(Path(slot.lane_state_root))
    if scope is None or scope["mark"]["pending_close_episode_id"] is None:
        return None
    if budget_host.closed or budget_host.execution_environment != "LIVE":
        raise ValueError("L10_CLOSE_ORIGINAL_HOST_REQUIRED")
    episode_id = scope["mark"]["pending_close_episode_id"]
    root = occupied_close_submit_root_v1(budget_host.root, episode_id)
    send = load_external_effect_durable_consume_v1(store_root=root)
    mandate = load_durable_post_owner_go_consume_v1(store_root=root)
    if not send["present"] and not mandate["present"]:
        return None
    close_args = dict(
        lane_pair=lane_pair,
        episode_id=episode_id,
        episode_root=root.parent,
        expected_scope=PositionEpisodeScopeV1(budget_host.expected_account_identity, "LIVE"),
        repository_sha=budget_host.repository_sha,
        session_id=budget_host.session_id,
    )
    execution = read_submitted_occupied_scope_close_v1(**close_args)
    envelope = execution.envelope
    digest = envelope.envelope_digest
    if not send["present"]:
        return AuthenticatedL10CloseReadbackV1("CLOSE_SUBMIT_NOT_PROVEN", digest)
    record = send["record"]
    if (
        send["durable_consumed"] is not True
        or record["envelope_id"] != envelope.envelope_id
        or record["envelope_digest"] != digest
        or record["authority_ref"] != POST_OWNER_GO
        or not mandate["record"]
        or mandate["record"].get("consumed") is not True
        or mandate["owner_go_token"] != POST_OWNER_GO
        or mandate["record"].get("baseline_origin_main_sha") != budget_host.repository_sha
        or mandate["record"].get("retry_authorized") is not False
        or mandate["record"].get("second_post_authorized") is not False
    ):
        raise ValueError("L10_CLOSE_ORIGINAL_SUBMIT_IDENTITY_UNPROVEN")
    attempt = record.get("transport_attempt", {})
    if attempt.get("phase") != "MAY_HAVE_SENT":
        return AuthenticatedL10CloseReadbackV1("CLOSE_SUBMIT_NOT_PROVEN", digest)
    socket_ms = _utc_ms(attempt["socket_boundary_at_utc"])

    root = require_private_proof_root_v1(proof_root)
    source = AuthenticatedReconciliationGetV1(
        budget_host.reconciliation_transport,
        account=budget_host.expected_account_identity,
        clock=budget_host.clock,
        retain_response_bodies=True,
    )
    identity = FullCoreExchangeReconciliationIdentityV1(
        canonical_decision_id=execution.source.quantity_handoff.decision_id,
        decision_outcome="EXIT",
        selected_side=execution.l10_close.episode.position_side.upper(),
        instrument_id=bound.instrument_id,
        native_id=bound.venue_native_id,
        account_identity=budget_host.expected_account_identity,
        execution_environment="LIVE",
        venue="OKX",
        venue_plan_identity=envelope.venue_plan_clordid,
        venue_plan_digest="",
        envelope_identity=envelope.envelope_id,
        envelope_digest=digest,
        final_quantity=envelope.quantity,
        quantity_unit=envelope.quantity_unit,
        order_type=envelope.order_type,
        order_price=envelope.price,
        clordid=envelope.client_order_id,
        exchange_ord_id=None,
        owner_go=POST_OWNER_GO,
        atomic_consumption_key=record["permit_id"],
        submit_attempt_id=attempt["claim_id"],
        local_durable_state_version="full_core_external_effect_permit_consume_v1",
    )

    def utc_now():
        return datetime.fromtimestamp(budget_host.clock(), timezone.utc)

    account_id = f"{budget_host.session_id}:close-account:{digest}"
    order_id = f"{budget_host.session_id}:close-order:{digest}"
    source.get(
        endpoint=ENDPOINT_ACCOUNT_CONFIG,
        auth_required=True,
        pretrade_decision_id=account_id,
        get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )
    observed = utc_now()
    options = resolve_reconciliation_query_options_v1(
        instrument_id=identity.instrument_id, native_id=identity.native_id
    )
    snapshot = fetch_okx_read_only_reconciliation_snapshot_v1(
        identity=identity,
        read_only_get_transport=source,
        pretrade_decision_id=order_id,
        options=options,
        received_at=observed.isoformat(),
        acquisition_clock=lambda: utc_now().isoformat(),
    )
    reads, bodies = source.completed_order_read_set_v1(
        account_decision_id=account_id,
        order_decision_id=order_id,
        observed_at=observed,
    )
    if (
        source.account_position_mode != "net_mode"
        or socket_ms > _utc_ms(reads[0].acquired_at.isoformat())
        or read_submitted_occupied_scope_close_v1(**close_args) != execution
    ):
        raise ValueError("L10_CLOSE_POST_SUBMIT_SCOPE_OR_TIME_UNPROVEN")
    if options.inst_type == "FUTURES":
        require_futures_reconciliation_product_v1(snapshot)
    decision = adjudicate_full_core_exchange_reconciliation_v1(
        identity=identity,
        snapshot=snapshot,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_UNKNOWN,
    )
    if decision.outcome not in {OUTCOME_CONFIRMED_FILLED, OUTCOME_CONFIRMED_PARTIALLY_FILLED}:
        awaiting = decision.outcome == OUTCOME_CONFIRMED_OPEN or decision.reasons == (
            REASON_TRANSPORT_UNKNOWN,
        )
        return AuthenticatedL10CloseReadbackV1(
            "CLOSE_AWAITING_VENUE" if awaiting else "CLOSE_READBACK_BLOCKED",
            digest,
            decision.reasons or (decision.outcome,),
        )
    try:
        observed_ms = _utc_ms(reads[-1].acquired_at.isoformat())
        latest_fill = _validate_close_order_and_fills_v1(
            snapshot=snapshot,
            decision=decision,
            envelope=envelope,
            inst_type=options.inst_type,
            socket_ms=socket_ms,
            observed_ms=observed_ms,
        )
        positions = snapshot.positions_observation["response"]["data"]
        for position in positions:
            position_time = Decimal(position["uTime"])
            if (
                position.get("instId") != envelope.instrument_id
                or position.get("instType") != options.inst_type
                or position.get("posSide") != "net"
                or position.get("mgnMode") != envelope.td_mode
                or not position_time.is_finite()
                or not latest_fill <= position_time <= observed_ms
            ):
                raise ValueError("L10_CLOSE_POSITION_SCOPE_OR_TIME_UNPROVEN")
    except (InvalidOperation, KeyError, TypeError, ValueError) as exc:
        return AuthenticatedL10CloseReadbackV1("CLOSE_READBACK_BLOCKED", digest, (str(exc),))
    verified = verify_post_close_position_v1(
        snapshot=snapshot.to_dict(),
        decision=decision,
        identity=identity,
        request=PostCloseFeedbackRequestV1(execution, bound, reads[-1].acquired_at.isoformat()),
        submitted_clordid=envelope.client_order_id,
        reconciliation_proven=True,
    )
    filled = Decimal(decision.cumulative_filled_qty)
    if (
        decision.outcome == OUTCOME_CONFIRMED_PARTIALLY_FILLED
        and verified.status == "POSITION_REMAINS_OPEN"
        and verified.remaining_quantity == Decimal(envelope.quantity) - filled
    ):
        return AuthenticatedL10CloseReadbackV1(
            "CLOSE_PARTIAL", digest, (), filled, verified.remaining_quantity
        )
    if verified.status != "RECONCILED_FLAT":
        reasons = verified.reason_codes
        if verified.status == "POSITION_REMAINS_OPEN":
            reasons = ("L10_CLOSE_RESIDUAL_POSITION_MISMATCH",)
        return AuthenticatedL10CloseReadbackV1("CLOSE_READBACK_BLOCKED", digest, reasons)
    proof = publish_authenticated_close_readback_v1(
        root=root,
        reads=reads,
        bodies=bodies,
        close_record={
            "identity": identity.to_dict(),
            "position_episode_id": episode_id,
            "scope_digest": execution.l10_close.scope_digest,
            "envelope": envelope.to_runtime_json_v1(),
            "decision": decision.to_dict(),
            "position_time_ms": str(verified.confirmed_position_time_ms),
            "evidence_digest": verified.evidence_digest,
            "position_coverage": (snapshot.positions_observation or {}).get("query_coverage"),
            "socket_boundary_at_utc": attempt["socket_boundary_at_utc"],
        },
    )
    return AuthenticatedL10CloseReadbackV1(
        "CLOSE_FLAT_CONFIRMED", digest, (), filled, Decimal(0), proof
    )
