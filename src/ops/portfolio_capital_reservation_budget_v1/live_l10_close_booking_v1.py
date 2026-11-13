"""Book a proved LIVE position episode in the original reservation store."""

from dataclasses import asdict, dataclass
from decimal import Decimal, localcontext
import re

from .durable_store_v1 import digest
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    PortfolioExecutionReconciliationIdentityV2,
    parse_exchange_reconciliation_identity_v1,
)


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def venue_decimal_v1(value):
    if not isinstance(value, str) or not re.fullmatch(r"-?[0-9]{1,24}(\.[0-9]{1,24})?", value):
        raise ValueError("L10_CLOSE_INVALID_DECIMAL")
    return Decimal(value)


@dataclass(frozen=True)
class AuthenticatedSlotCloseBookingV1:
    reservation_id: str
    episode_id: str
    account_identity: str
    slot_id: str
    native_id: str
    close_envelope_digest: str
    close_proof_digest: str
    entry_proof_digest: str
    history_proof_digest: str
    settlement_digest: str
    currency: str
    net_result: str

    def to_dict_v1(self):
        result = asdict(self)
        return {**result, "booking_digest": digest(result)}


def validate_live_l10_booking_v1(owner, row):
    result = dict(row)
    checksum = result.pop("booking_digest")
    booking = AuthenticatedSlotCloseBookingV1(**result)
    rid = booking.reservation_id
    reservation = owner._by_key.get(owner._by_id.get(rid))
    link = owner._execution_links.get(rid)
    if reservation is None or link is None or link["phase"] != "SUBMIT_MAY_HAVE_OCCURRED":
        raise ValueError("L10_CLOSE_BOOKING_ORIGINAL_RESERVATION_REQUIRED")
    identity = parse_exchange_reconciliation_identity_v1(link["identity"])
    if (
        checksum != digest(result)
        or type(identity) is not PortfolioExecutionReconciliationIdentityV2
        or identity.execution_environment != "LIVE"
        or identity.decision_outcome not in {"ENTER_LONG", "ENTER_SHORT"}
        or identity.identity_digest() != booking.episode_id
        or booking.account_identity != owner._account_identity
        or booking.slot_id != str(reservation.slot_id)
        or owner._reservation_bindings[rid]["bound"]["venue_native_id"] != booking.native_id
        or (identity.account_identity, identity.slot_id, identity.native_id)
        != (booking.account_identity, booking.slot_id, booking.native_id)
        or identity.portfolio_reservation_id != rid
        or not all(
            _sha(value)
            for value in (
                booking.close_envelope_digest,
                booking.close_proof_digest,
                booking.entry_proof_digest,
                booking.history_proof_digest,
                booking.settlement_digest,
            )
        )
        or booking.currency not in {"USDC", "USDT"}
    ):
        raise ValueError("L10_CLOSE_BOOKING_ORIGINAL_SCOPE_UNPROVEN")
    venue_decimal_v1(booking.net_result)
    return booking


def restore_live_l10_bookings_v1(owner, rows):
    if not isinstance(rows, dict):
        raise ValueError("L10_CLOSE_BOOKING_STATE_INVALID")
    seen = set()
    for episode, row in rows.items():
        booking = validate_live_l10_booking_v1(owner, row)
        if booking.episode_id != episode or booking.close_envelope_digest in seen:
            raise ValueError("L10_CLOSE_BOOKING_STATE_CONFLICT")
        seen.add(booking.close_envelope_digest)
    return rows


def _entry_source_matches_v1(source, switch):
    from src.ops.exit_policy_producer_binding_v1.authenticated_execution_entry_source_v1 import (
        _entry_anchors_v1,
    )
    from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1

    episode = switch.episode
    if (
        (source.identity.slot_id, source.identity.instrument_id, source.identity.native_id)
        != (episode.lane_id, episode.instrument_id, episode.venue_native_id)
        or source.identity.selected_side.upper() != episode.position_side.upper()
        or source.proof.identity_digest != episode.episode_id
    ):
        return False
    _, _, anchors = _entry_anchors_v1(source, side=episode.position_side)
    return switch.entry_source_ref in {
        "authenticated_execution_entry.v1:"
        + canonical_digest_v1({"attempt": episode.episode_id, "anchors": anchors}),
        "authenticated_execution_entry.v1:"
        + canonical_digest_v1(
            {
                "attempt": episode.episode_id,
                "revision": list(source.proof.revision_ref),
                "snapshot": source.proof.snapshot_digest,
            }
        ),
    }


def entry_source_v1(*, links, execution, proof_root, budget_owner_root, inst_type):
    from src.ops.execution_reconciliation_proof_store_v1 import find_authenticated_entry_sources_v1

    switch = execution.l10_close
    episode = switch.episode
    matches = [
        rid
        for rid, link in links.items()
        if link["phase"] == "SUBMIT_MAY_HAVE_OCCURRED"
        and parse_exchange_reconciliation_identity_v1(link["identity"]).identity_digest()
        == episode.episode_id
    ]
    if len(matches) != 1:
        raise ValueError("L10_CLOSE_BOOKING_ORIGINAL_ENTRY_REQUIRED")
    candidates = {}
    for source in find_authenticated_entry_sources_v1(
        root=proof_root,
        budget_owner_root=budget_owner_root,
        account=episode.account_scope.account_identity,
        reservation_id=matches[0],
        episode_id=episode.episode_id,
    ):
        if not _entry_source_matches_v1(source, switch):
            continue
        (position,) = source.snapshot.positions_observation["response"]["data"]
        if not position.get("posId") or not position.get("cTime"):
            continue
        key = (close_history_endpoint_v1(entry=source, inst_type=inst_type), position["cTime"])
        prior = candidates.get(key)
        if prior is None or source.proof.revision_ref < prior.proof.revision_ref:
            candidates[key] = source
    if len(candidates) != 1:
        raise ValueError("L10_CLOSE_BOOKING_ENTRY_EVIDENCE_UNPROVEN")
    return next(iter(candidates.values()))


def close_history_endpoint_v1(*, entry, inst_type):
    from urllib.parse import urlencode
    from src.ops.execution_reconciliation_get_provenance_v1 import (
        ENDPOINT_ACCOUNT_POSITIONS_HISTORY,
    )

    (position,) = entry.snapshot.positions_observation["response"]["data"]
    pos_id = position.get("posId")
    if not isinstance(pos_id, str) or re.fullmatch(r"[1-9][0-9]{0,29}", pos_id) is None:
        raise ValueError("L10_CLOSE_ENTRY_POSITION_ID_UNPROVEN")
    return (
        ENDPOINT_ACCOUNT_POSITIONS_HISTORY
        + "?"
        + urlencode(
            {
                "instType": inst_type,
                "instId": entry.identity.native_id,
                "mgnMode": position["mgnMode"],
                "posId": pos_id,
                "limit": "100",
            }
        )
    )


def build_live_l10_booking_v1(owner, *, execution, proof_path, proof_root):
    from pathlib import Path
    from src.ops.execution_reconciliation_proof_store_v1 import (
        _RecordedReconciliationGets,
        _aware,
        _decode_get,
        read_authenticated_execution_reconciliation_source_v1,
        read_private_close_document_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_l10_close_reconciliation_v1 import (
        _validate_close_order_and_fills_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_position_close_v1 import (
        occupied_close_submit_root_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
        POST_OWNER_GO,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_position_management_quantity_handoff_v1 import (
        validates_position_management_envelope_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_close_feedback_v1 import (
        PostCloseFeedbackRequestV1,
        _utc_ms,
        verify_post_close_position_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
        fetch_okx_read_only_reconciliation_snapshot_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
        EvidenceLayer,
        LocalSubmitOutcome,
        adjudicate_full_core_exchange_reconciliation_v1,
    )
    from src.ops.execution_reconciliation_get_provenance_v1 import (
        _MAX_AGE_SECONDS,
        resolve_reconciliation_query_options_v1,
    )

    if not validates_position_management_envelope_v1(execution) or execution.l10_close is None:
        raise ValueError("L10_CLOSE_BOOKING_ORIGINAL_EXECUTION_REQUIRED")
    history, history_digest = read_private_close_document_v1(
        root=proof_root,
        path=proof_path,
        prefix="close-history-",
        schema="peaktrade.authenticated_close_history.v1",
    )
    close_digest = history["close_proof_digest"]
    close, _ = read_private_close_document_v1(
        root=proof_root,
        path=Path(proof_root) / f"close-{close_digest}.json",
        prefix="close-",
        schema="peaktrade.authenticated_close_get_proof.v1",
    )
    switch, envelope = execution.l10_close, execution.envelope
    episode = switch.episode
    identity = parse_exchange_reconciliation_identity_v1(close["identity"])
    send_root = occupied_close_submit_root_v1(owner._store.root.parent, episode.episode_id)
    send = load_external_effect_durable_consume_v1(store_root=send_root)
    attempt = (send["record"] or {}).get("transport_attempt") or {}
    if (
        episode.account_scope.execution_environment != "LIVE"
        or episode.account_scope.account_identity != owner._account_identity
        or close["position_episode_id"] != episode.episode_id
        or close["scope_digest"] != switch.scope_digest
        or close["envelope"] != envelope.to_runtime_json_v1()
        or send["durable_consumed"] is not True
        or send["record"]["envelope_id"] != envelope.envelope_id
        or send["record"]["envelope_digest"] != envelope.envelope_digest
        or send["record"]["authority_ref"] != POST_OWNER_GO
        or attempt.get("phase") != "MAY_HAVE_SENT"
        or attempt.get("socket_boundary_at_utc") != close["socket_boundary_at_utc"]
        or identity.submit_attempt_id != attempt.get("claim_id")
        or identity.atomic_consumption_key != send["record"]["permit_id"]
        or (
            identity.account_identity,
            identity.execution_environment,
            identity.native_id,
            identity.envelope_digest,
            identity.clordid,
            identity.decision_outcome,
        )
        != (
            owner._account_identity,
            "LIVE",
            episode.venue_native_id,
            envelope.envelope_digest,
            envelope.client_order_id,
            "EXIT",
        )
    ):
        raise ValueError("L10_CLOSE_BOOKING_CLOSE_SCOPE_UNPROVEN")
    recorded = [_decode_get(item) for item in close["gets"]]
    if len(recorded) != 6:
        raise ValueError("L10_CLOSE_BOOKING_ORIGINAL_GETS_UNPROVEN")
    account_get, account = recorded[0]
    reads = [item[0] for item in recorded]
    received_at = _aware(close["snapshot_received_at"])
    history_get, payload = _decode_get(history["get"])
    if (
        account_get.endpoint != "/api/v5/account/config"
        or account.get("code") != "0"
        or len(account["data"]) != 1
        or account["data"][0].get("uid") != owner._account_identity
        or account["data"][0].get("posMode") != "net_mode"
        or payload["code"] != "0"
        or not reads[0].acquired_at <= received_at <= reads[1].acquired_at
        or any(a.acquired_at > b.acquired_at for a, b in zip(reads, reads[1:]))
        or not reads[-1].acquired_at <= history_get.acquired_at
        or (history_get.acquired_at - account_get.acquired_at).total_seconds() > _MAX_AGE_SECONDS
        or not history_get.decision_id.endswith(":close-history:" + envelope.envelope_digest)
    ):
        raise ValueError("L10_CLOSE_BOOKING_ORIGINAL_GETS_UNPROVEN")

    options = resolve_reconciliation_query_options_v1(
        instrument_id=episode.instrument_id,
        native_id=episode.venue_native_id,
    )
    inst_type = options.inst_type
    entry_ref = history["entry_proof"]
    entry = read_authenticated_execution_reconciliation_source_v1(
        root=proof_root,
        budget_owner_root=owner._store.root,
        account=owner._account_identity,
        session_id=entry_ref["session_id"],
        reservation_id=entry_ref["reservation_id"],
        revision_ref=tuple(entry_ref["revision_ref"]),
    )
    if (
        not _entry_source_matches_v1(entry, switch)
        or close_history_endpoint_v1(entry=entry, inst_type=inst_type) != history_get.endpoint
    ):
        raise ValueError("L10_CLOSE_BOOKING_ENTRY_EVIDENCE_UNPROVEN")
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

    rid = entry.proof.reservation_id
    bound = BoundInstrumentV1(**owner._reservation_bindings[rid]["bound"])
    if entry.lane_binding.get("bound") != bound.to_dict():
        raise ValueError("L10_CLOSE_BOOKING_ENTRY_GENERATION_UNPROVEN")
    coverage = close["position_coverage"]
    times = iter(
        (coverage["started_at_utc"], coverage["completed_at_utc"])
        if coverage is not None
        else (received_at.isoformat(),) * 2
    )
    snapshot = fetch_okx_read_only_reconciliation_snapshot_v1(
        identity=identity,
        options=options,
        read_only_get_transport=_RecordedReconciliationGets(recorded[1:]),
        pretrade_decision_id=reads[1].decision_id,
        received_at=received_at.isoformat(),
        acquisition_clock=lambda: next(times),
    )
    decision = adjudicate_full_core_exchange_reconciliation_v1(
        identity=identity,
        snapshot=snapshot,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_UNKNOWN,
    )
    verified = verify_post_close_position_v1(
        snapshot=snapshot.to_dict(),
        decision=decision,
        identity=identity,
        request=PostCloseFeedbackRequestV1(execution, bound, reads[-1].acquired_at.isoformat()),
        submitted_clordid=envelope.client_order_id,
        reconciliation_proven=True,
    )
    if (
        verified.status != "RECONCILED_FLAT"
        or verified.evidence_digest != close["evidence_digest"]
        or str(verified.confirmed_position_time_ms) != close["position_time_ms"]
        or decision.to_dict() != close["decision"]
        or snapshot.positions_observation["query_coverage"] != coverage
    ):
        raise ValueError("L10_CLOSE_BOOKING_CLOSE_READBACK_UNPROVEN")
    _validate_close_order_and_fills_v1(
        snapshot=snapshot,
        decision=decision,
        envelope=envelope,
        inst_type=inst_type,
        socket_ms=_utc_ms(close["socket_boundary_at_utc"]),
        observed_ms=_utc_ms(reads[-1].acquired_at.isoformat()),
    )
    (entry_pos,) = entry.snapshot.positions_observation["response"]["data"]
    close_fills = {
        item.payload["tradeId"]: item.payload
        for item in snapshot.evidence_items
        if item.layer is EvidenceLayer.EXCHANGE_FILL_STATE
    }
    qty = Decimal(envelope.quantity)
    if (
        abs(venue_decimal_v1(entry_pos["pos"])) != qty
        or owner._execution_links[rid]["envelope"]["envelope_digest"]
        != entry.identity.envelope_digest
    ):
        raise ValueError("L10_CLOSE_BOOKING_QUANTITY_UNPROVEN")
    latest_fill = max(venue_decimal_v1(fill["fillTime"]) for fill in close_fills.values())
    first_fill = min(venue_decimal_v1(fill["fillTime"]) for fill in close_fills.values())
    entry_fills = {
        item.payload["tradeId"]: item.payload
        for item in entry.snapshot.evidence_items
        if item.layer is EvidenceLayer.EXCHANGE_FILL_STATE
    }
    entry_time = venue_decimal_v1(entry_pos["cTime"])
    # Match the closed episode, even if the venue reuses its position ID.
    matches = [
        row
        for row in payload["data"]
        if row.get("posId") == entry_pos["posId"] and row.get("cTime") == entry_pos["cTime"]
    ]
    if len(matches) != 1:
        raise ValueError("L10_CLOSE_HISTORY_EPISODE_UNPROVEN")
    row = matches[0]
    currency = row["ccy"]
    if (
        row.get("instId") != episode.venue_native_id
        or row.get("instType") != inst_type
        or row.get("direction") != episode.position_side
        or row.get("posSide") != "net"
        or row.get("mgnMode") != envelope.td_mode
        or entry_pos.get("mgnMode") != envelope.td_mode
        or row.get("type") != "2"
        or currency != entry_pos.get("ccy")
        or currency not in {"USDC", "USDT"}
        or venue_decimal_v1(row["openMaxPos"]) != qty
        or venue_decimal_v1(row["closeTotalPos"]) != qty
        or not 0 < entry_time <= venue_decimal_v1(entry_pos["uTime"])
        or any(
            not 0 < venue_decimal_v1(fill["fillTime"]) <= venue_decimal_v1(entry_pos["uTime"])
            for fill in entry_fills.values()
        )
        or venue_decimal_v1(entry_pos["uTime"]) >= first_fill
        or not _utc_ms(close["socket_boundary_at_utc"])
        <= first_fill
        <= latest_fill
        <= venue_decimal_v1(row["uTime"])
        <= venue_decimal_v1(close["position_time_ms"])
        or any(
            fill.get("feeCcy") != currency
            for fill in (*entry_fills.values(), *close_fills.values())
        )
    ):
        raise ValueError("L10_CLOSE_HISTORY_SCOPE_UNPROVEN")
    entry_reservation = owner._by_key[owner._by_id[entry.proof.reservation_id]]
    sizing = owner._sizing_bindings[str(entry_reservation.reservation_id)]
    if sizing.monetary_source is None:
        raise ValueError("L10_CLOSE_HISTORY_ORIGINAL_MONETARY_SOURCE_REQUIRED")
    _, money, _ = sizing.monetary_source.rebuild_v1()
    if money.settle_currency != currency:
        raise ValueError("L10_CLOSE_HISTORY_SETTLEMENT_CURRENCY_MISMATCH")
    pnl = venue_decimal_v1(row["pnl"])
    fee = venue_decimal_v1(row["fee"])
    funding = venue_decimal_v1(row["fundingFee"])
    penalty = venue_decimal_v1(row["liqPenalty"])
    settled = (
        Decimal(0)
        if inst_type == "SWAP" and row.get("settledPnl") in {None, ""}
        else venue_decimal_v1(row["settledPnl"])
    )
    realized = venue_decimal_v1(row["realizedPnl"])
    with localcontext() as ctx:
        ctx.prec = 60  # Sum exact venue decimals, including small rebates and funding.
        if (
            pnl != sum(venue_decimal_v1(fill["fillPnl"]) for fill in close_fills.values())
            or fee
            != sum(
                venue_decimal_v1(fill["fee"])
                for fill in (*entry_fills.values(), *close_fills.values())
            )
            or penalty != 0
            or (inst_type == "SWAP" and settled != 0)
            or realized != pnl + fee + funding + penalty + settled
        ):
            raise ValueError("L10_CLOSE_HISTORY_NET_RESULT_UNPROVEN")
    return AuthenticatedSlotCloseBookingV1(
        reservation_id=entry.proof.reservation_id,
        episode_id=episode.episode_id,
        account_identity=owner._account_identity,
        slot_id=episode.lane_id,
        native_id=episode.venue_native_id,
        close_envelope_digest=envelope.envelope_digest,
        close_proof_digest=close_digest,
        entry_proof_digest=entry.proof.revision_ref[1],
        history_proof_digest=history_digest,
        settlement_digest=digest({"history": row, "close_fills": close_fills}),
        currency=currency,
        net_result=format(realized, "f"),
    )
