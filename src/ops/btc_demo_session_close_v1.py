"""Explicit bounded-session close, separate from the Core's L10/net switch.

Preparation has no send effect. Dispatch requires a distinct signed TESTNET
grant and the original one-shot transport. Only authenticated settlement and
complete flat account custody can release the original reservation.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.btc_demo_budget_owner_v3 import BtcDemoBudgetOwnerV3
from src.ops.btc_demo_session_control_v1 import utc_v1, validate_session_control_v1
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1BoundVenueAuthHandleV1,
    require_same_k1_venue_credential_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
    build_final_order_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.pretrade_acquisition_v1 import (
    acquisition_age_seconds_v1,
    utc_now_iso_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import canonical, digest
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    AuthenticatedEntryEpisodeRequestV1,
    HostBudgetRecoveryContextV1,
    PortfolioBudgetHostV1,
)

BOUNDED_SESSION_CLOSE = "BOUNDED_SESSION_CLOSE"


def _need(value, reason):
    if not value:
        raise ValueError("BTC_DEMO_SESSION_CLOSE:" + reason)


def close_root_v1(owner, registration):
    root = (
        demo._demo_lane_root(owner._store.root.parents[2])
        / "session-close"
        / registration.digest_v1()
    )
    _need(root.resolve() == root, "ORIGINAL_ROOT_REQUIRED")
    return root


def _position_parent_v1(owner, rid):
    # Restore runs inside the original writer before the subclass RLock is
    # installed. Re-entering public readers here would deadlock its base lock.
    link = owner._execution_links[rid]
    series = owner._live_net_reversal_bookings.get(rid, ())
    prior = None if not series else series[-1]
    return (
        link["reconciliation"]["identity_digest"] if prior is None else prior["envelope_digest"]
    ), prior


def _inspect_position_v1(recovery, request, *, signing_handle=None):
    from src.ops.execution_reconciliation_get_provenance_v1 import AuthenticatedReconciliationGetV1
    from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
        K1AccountObservationSourceV1,
    )
    from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
        read_occupied_scope_mark_snapshot_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_double_play_reversal_v1 import (
        _net_reversal_submit_root_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    _need(
        type(recovery) is HostBudgetRecoveryContextV1
        and type(request) is AuthenticatedEntryEpisodeRequestV1,
        "ORIGINAL_POSITION_CONTEXT_REQUIRED",
    )
    host = recovery.host
    _need(
        type(host) is PortfolioBudgetHostV1
        and type(host.owner) is BtcDemoBudgetOwnerV3
        and not host.closed
        and host.execution_environment == "TESTNET",
        "ORIGINAL_TESTNET_HOST_REQUIRED",
    )
    owner = host.owner
    registration = validate_session_control_v1(owner, owner._bounded_demo_session_control)
    _need(
        registration is not None and utc_v1(utc_now_iso_v1()) >= utc_v1(registration.deadline_utc),
        "SESSION_DEADLINE_NOT_REACHED",
    )
    _need(
        host.bindings is not None and set(host.bindings) == {"LANE_3"}, "ORIGINAL_BINDING_REQUIRED"
    )
    bound = host.bindings["LANE_3"]
    proof = request.proof
    link = recovery.inspect_current_authenticated_entry_v1(lane_id="LANE_3", proof=proof)
    parent, prior = _position_parent_v1(owner, proof.reservation_id)
    account_source, source = (
        recovery.account_inventory_source,
        recovery.authenticated_reconciliation,
    )
    _need(
        type(account_source) is K1AccountObservationSourceV1
        and account_source.account_inventory_guard
        and account_source.inventory_inst_type == "FUTURES"
        and account_source.credential.execution_environment == "TESTNET"
        and type(source) is AuthenticatedReconciliationGetV1
        and source.transport is host.reconciliation_transport
        and source.evidence.get(proof.reservation_id) == proof
        and source.account_position_mode == "net_mode"
        and source.position_margin_modes.get(proof.reservation_id) == ("cross",)
        and registration.account_identity == recovery.account == host.account
        and registration.instrument_id == bound.instrument_id
        and proof.identity_digest == parent
        and link["reconciliation"]["matched"] is True
        and link["reconciliation"]["reservation_released"] is False,
        "CURRENT_ORIGINAL_POSITION_UNPROVEN",
    )
    account_source.inspect_pending_observation_v1(account_source.pending_observation_v1())
    for handle in (account_source.credential, signing_handle):
        if handle is not None:
            require_same_k1_venue_credential_v1(source.original_handle_v1(), handle)
    now = utc_now_iso_v1()
    for stamp in (
        proof.gets[0].acquired_at.isoformat(),
        datetime.fromtimestamp(recovery.observed.event_time_unix, timezone.utc).isoformat(),
    ):
        acquisition_age_seconds_v1(acquired_at_utc=stamp, now_utc=now)
    positions = recovery.occupancy_payloads["POSITIONS"]["data"]
    _need(len(positions) == 1, "EXACT_SINGLE_POSITION_REQUIRED")
    position = positions[0]
    signed = Decimal(position["pos"])
    _need(
        tuple((p.instrument_id, p.signed_quantity) for p in recovery.observed.positions)
        == ((bound.instrument_id, signed),),
        "ORIGINAL_POSITION_SNAPSHOT_CHANGED",
    )
    _need(
        signed.is_finite()
        and signed != 0
        and (
            position.get("instId"),
            position.get("instType"),
            position.get("ccy"),
            position.get("posSide"),
            position.get("mgnMode"),
        )
        == (demo._NATIVE, "FUTURES", "USDC", "net", "cross"),
        "NATIVE_POSITION_SCOPE_MISMATCH",
    )
    if prior is not None:
        _need(
            (position["posId"], position["cTime"], signed, Decimal(position["fee"]))
            == (
                prior["position_id"],
                prior["position_created_ms"],
                Decimal(prior["position_contracts"]),
                Decimal(prior["position_fee"]),
            ),
            "LATEST_NET_POSITION_MISMATCH",
        )
    cursor = demo._demo_lane_root(owner._store.root.parents[2]) / "cursor" / "LANE_3"
    scope = read_occupied_scope_mark_snapshot_v1(cursor)
    pending = None if scope is None else scope["mark"].get("pending_reversal_episode_id")
    if pending:
        send = load_external_effect_durable_consume_v1(
            store_root=_net_reversal_submit_root_v1(host.root, pending)
        )
        if (
            send["present"]
            and send["record"].get("transport_attempt", {}).get("phase") != "ABORTED"
        ):
            _need(
                prior is not None
                and prior["previous_episode_id"] == pending
                and prior["envelope_digest"] == send["record"]["envelope_digest"],
                "UNRESOLVED_REVERSAL_MUST_RECONCILE_FIRST",
            )
    return registration, bound, deepcopy(position)


def _quote_v1(owner, *, plan, packet, now_utc):
    from src.ops.portfolio_capital_reservation_budget_v1.entry_execution_cost_v1 import (
        FreshPretradeGetTransportResultV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.position_close_quote_v1 import (
        quote_btc_demo_position_close_v1,
    )

    _need(
        set(packet) == {"sources", "original_bodies_hex"}
        and set(packet["sources"])
        == set(packet["original_bodies_hex"])
        == {"account", "instruments", "fees", "book"},
        "QUOTE_ORIGINALS_REQUIRED",
    )
    sources = {}
    for key, row in packet["sources"].items():
        raw = bytes.fromhex(packet["original_bodies_hex"][key])
        _need(
            sha256(raw).hexdigest() == row["body_sha256"] and json.loads(raw) == row["payload"],
            "QUOTE_BODY_MISMATCH",
        )
        sources[key] = FreshPretradeGetTransportResultV1(**row)
    return quote_btc_demo_position_close_v1(
        owner,
        reservation_id=plan["reservation_id"],
        sources=sources,
        acquisition_id=plan["acquisition_id"],
        quantity=str(abs(Decimal(plan["position"]["pos"]))),
        position_side="long" if Decimal(plan["position"]["pos"]) > 0 else "short",
        now_utc=now_utc,
    )


def validate_close_plan_v1(owner, registration, plan):
    _need(
        type(plan) is dict
        and set(plan)
        == {
            "registration_digest",
            "reservation_id",
            "episode_id",
            "position",
            "position_proof_digest",
            "acquisition_id",
            "quote",
            "packet_digest",
            "envelope",
            "repository_sha",
            "plan_digest",
        },
        "PLAN_SHAPE_INVALID",
    )
    body = {k: v for k, v in plan.items() if k != "plan_digest"}
    _need(
        digest(body) == plan["plan_digest"]
        and registration.digest_v1() == plan["registration_digest"],
        "PLAN_DIGEST_MISMATCH",
    )
    parent, _ = _position_parent_v1(owner, plan["reservation_id"])
    envelope = FinalOrderEnvelopeV1(**plan["envelope"])
    assert_envelope_unmodified_v1(envelope)
    signed = Decimal(plan["position"]["pos"])
    _need(
        signed.is_finite()
        and signed != 0
        and parent == plan["episode_id"]
        and (
            envelope.instrument_id,
            envelope.path_kind,
            envelope.side,
            envelope.reduce_only,
            envelope.order_type,
            envelope.pos_side,
            envelope.td_mode,
            envelope.quantity_unit,
            Decimal(envelope.quantity),
            envelope.provenance_ref,
            envelope.admission_ref,
        )
        == (
            demo._NATIVE,
            BOUNDED_SESSION_CLOSE,
            "sell" if signed > 0 else "buy",
            True,
            "market",
            "net",
            "cross",
            "CONTRACTS",
            abs(signed),
            plan["position_proof_digest"],
            registration.digest_v1(),
        )
        and utc_v1(envelope.creation_epoch) >= utc_v1(registration.deadline_utc),
        "PLAN_ORIGINAL_SCOPE_MISMATCH",
    )
    packet = json.loads((close_root_v1(owner, registration) / "quote-sources.json").read_bytes())
    _need(
        digest(packet) == plan["packet_digest"]
        and _quote_v1(owner, plan=plan, packet=packet, now_utc=envelope.creation_epoch)
        == plan["quote"],
        "PLAN_QUOTE_MISMATCH",
    )
    return envelope


@dataclass(frozen=True)
class BtcDemoSessionCloseContextV1:
    recovery: HostBudgetRecoveryContextV1
    entry_request: AuthenticatedEntryEpisodeRequestV1
    plan: dict

    @property
    def envelope(self):
        return FinalOrderEnvelopeV1(**self.plan["envelope"])

    def store_root_v1(self):
        owner = self.recovery.host.owner
        return close_root_v1(
            owner, validate_session_control_v1(owner, owner._bounded_demo_session_control)
        )

    def inspect_v1(self, *, signing_handle, claim=None):
        _need(
            type(signing_handle) is FullCoreK1BoundVenueAuthHandleV1
            and signing_handle.execution_environment == "TESTNET",
            "ORIGINAL_TESTNET_SIGNER_REQUIRED",
        )
        registration, _, position = _inspect_position_v1(
            self.recovery, self.entry_request, signing_handle=signing_handle
        )
        owner = self.recovery.host.owner
        envelope = validate_close_plan_v1(owner, registration, self.plan)
        _need(
            position == self.plan["position"]
            and self.recovery.host.repository_sha == self.plan["repository_sha"]
            and self.entry_request.proof.snapshot_digest == self.plan["position_proof_digest"],
            "PLAN_POSITION_CHANGED",
        )
        control = owner._bounded_demo_session_control
        _need(
            control["phase"] in {"RUNNING", "CLOSING"}
            and (control["phase"] == "RUNNING" or control["close_plan"] == self.plan),
            "SESSION_CLOSE_ALREADY_FROZEN",
        )
        acquisition_age_seconds_v1(
            acquired_at_utc=envelope.creation_epoch, now_utc=utc_now_iso_v1()
        )
        packet = json.loads((self.store_root_v1() / "quote-sources.json").read_bytes())
        _quote_v1(owner, plan=self.plan, packet=packet, now_utc=utc_now_iso_v1())
        if claim is not None:
            _need(control["phase"] == "CLOSING", "ORIGINAL_CLOSE_WRITER_REQUIRED")
            claim.inspect_v1(
                envelope_digest=envelope.envelope_digest,
                attempt_root=self.store_root_v1(),
                account=registration.account_identity,
                action=BOUNDED_SESSION_CLOSE,
                execution_environment="TESTNET",
            )
        return registration


def prepare_btc_demo_session_close_v1(*, recovery, entry_request, reads):
    """Reviewable reduce-only envelope and original book/fee quote; no permit."""
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
        immutable_json_v1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.entry_execution_cost_v1 import (
        FreshPretradeGetTransportResultV1,
    )

    registration, bound, position = _inspect_position_v1(recovery, entry_request)
    _need(type(reads) is demo.OkxEeaDemoReadsV1, "ORIGINAL_QUOTE_READER_REQUIRED")
    require_same_k1_venue_credential_v1(
        recovery.authenticated_reconciliation.original_handle_v1(),
        getattr(reads, "_entry_signing_handle_v1", None),
    )
    now = utc_now_iso_v1()
    acquisition_id = "bounded-session-close:" + digest(
        dict(
            registration=registration.digest_v1(),
            episode=entry_request.proof.identity_digest,
            acquired_at=now,
        )
    )
    packet = dict(sources={}, original_bodies_hex={})
    for name, path, query in (
        ("account", "/api/v5/account/config", {}),
        (
            "instruments",
            "/api/v5/account/instruments",
            dict(instType="FUTURES", instId=demo._NATIVE),
        ),
        (
            "fees",
            "/api/v5/account/trade-fee",
            dict(instType="FUTURES", instFamily="BTC-USD_UM_XPERP"),
        ),
        ("book", "/api/v5/market/books", dict(instId=demo._NATIVE, sz="20")),
    ):
        payload, acquired, raw = reads.read_original_v1(path, **query)
        packet["original_bodies_hex"][name] = raw.hex()
        packet["sources"][name] = asdict(
            FreshPretradeGetTransportResultV1(
                get_performed=True,
                method="GET",
                endpoint=path + ("?" + demo.urlencode(query) if query else ""),
                http_status=200,
                payload=payload,
                auth_header_sent=name != "book",
                transport_class="OKX_EEA_DEMO_READ_ONLY_GET",
                venue_live_contact=True,
                historical_reuse=False,
                error_class="",
                body_sha256=sha256(raw).hexdigest(),
                pretrade_decision_id=acquisition_id,
                acquired_at_utc=acquired.isoformat(),
            )
        )
    now = utc_now_iso_v1()
    plan = dict(
        registration_digest=registration.digest_v1(),
        reservation_id=entry_request.proof.reservation_id,
        episode_id=entry_request.proof.identity_digest,
        position=position,
        position_proof_digest=entry_request.proof.snapshot_digest,
        acquisition_id=acquisition_id,
        packet_digest=digest(packet),
        repository_sha=recovery.host.repository_sha,
    )
    quote = _quote_v1(recovery.host.owner, plan=plan, packet=packet, now_utc=now)
    clordid = (
        "ptsc"
        + digest(dict(registration=registration.digest_v1(), episode=plan["episode_id"]))[:28]
    )
    envelope = build_final_order_envelope_v1(
        instrument_id=bound.venue_native_id,
        side="sell" if Decimal(position["pos"]) > 0 else "buy",
        order_type="market",
        quantity=quote["quantity"],
        quantity_unit="CONTRACTS",
        td_mode="cross",
        pos_side="net",
        reduce_only=True,
        client_order_id=clordid,
        path_kind=BOUNDED_SESSION_CLOSE,
        venue_plan_clordid=clordid,
        quantity_source="ORIGINAL_AUTHENTICATED_OCCUPIED_POSITION",
        side_source="BOUNDED_SESSION_CLOSE_OPPOSITE_POSITION",
        instrument_source=bound.selection_integrity_digest,
        admission_ref=registration.digest_v1(),
        provenance_ref=plan["position_proof_digest"],
        creation_epoch=now,
    )
    plan.update(quote=quote, envelope=asdict(envelope))
    plan["plan_digest"] = digest(plan)
    root = close_root_v1(recovery.host.owner, registration)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    immutable_json_v1(root / "quote-sources.json", packet)
    immutable_json_v1(root / "close-plan.json", plan)
    context = BtcDemoSessionCloseContextV1(recovery, entry_request, plan)
    context.inspect_v1(signing_handle=reads._entry_signing_handle_v1)
    return context
