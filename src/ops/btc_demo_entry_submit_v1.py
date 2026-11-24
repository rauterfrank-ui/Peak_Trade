"""Explicit Slot-3 Demo dispatch through the original permit and budget barriers.

No scheduler, credential lookup, implicit grant, new sizing or fill accounting.
The caller supplies a decision-bound plan, original signed account inventory,
current venue limits and an independently issued TESTNET ENTER authorization.
"""

from dataclasses import asdict, dataclass, replace
import json
from pathlib import Path

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.btc_demo_budget_owner_v3 import BtcDemoBudgetOwnerV3
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1BoundVenueAuthHandleV1,
    require_same_k1_venue_credential_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_pending_observation_v1 import (
    inspect_current_post_pending_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    exclusive_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest


def btc_demo_entry_reader_v1(*, signing_handle):
    """Bind bounded Demo GETs to the same already-held opaque account credential."""
    from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
        build_k1_okx_demo_auth_headers_v1,
    )

    if (
        type(signing_handle) is not FullCoreK1BoundVenueAuthHandleV1
        or signing_handle.execution_environment != "TESTNET"
    ):
        raise ValueError("BTC_DEMO_ENTRY_TESTNET_SIGNER_REQUIRED")

    def sign_get(endpoint):
        headers = build_k1_okx_demo_auth_headers_v1(
            handle=signing_handle, url=demo._DEMO.rest_base + endpoint, method="GET", body=""
        )
        return {k: v for k, v in headers.items() if k in demo._AUTH_FIELDS}

    reader = demo.OkxEeaDemoReadsV1(secret_reference=demo._DEMO.secret_reference, sign_get=sign_get)
    reader._entry_signing_handle_v1 = signing_handle
    return reader


def capture_btc_demo_entry_quantity_v1(*, context, reads):
    """Acquire the two original Demo venue-limit responses; no sizing or send."""
    from dataclasses import asdict
    from hashlib import sha256
    from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
        FreshPretradeGetTransportResultV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_venue_quantity_v1 import (
        CurrentPostVenueQuantityContextV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_n1_venue_quantity_limit_admission_v1 import (
        capture_n1_venue_quantity_limits_v1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import canonical
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
        immutable_json_v1,
    )

    if type(context) is not BtcDemoEntryPostContextV1 or type(reads) is not demo.OkxEeaDemoReadsV1:
        raise ValueError("BTC_DEMO_ENTRY_QUANTITY_ORIGINAL_READER_REQUIRED")
    require_same_k1_venue_credential_v1(
        context.pending_context.source.credential, getattr(reads, "_entry_signing_handle_v1", None)
    )
    cycle = context.host._original_entry_cycle(context.entry)
    acquisition_id = canonical(
        dict(
            decision_epoch=cycle.replay.intermediate.market_context.decision_time,
            cycle_id=cycle.cycle_id,
        )
    )
    results, originals = {}, {}
    for name, path, query, private in (
        (
            "instruments",
            "/api/v5/public/instruments",
            dict(instType="FUTURES", instId=demo._NATIVE),
            False,
        ),
        ("max_size", "/api/v5/account/max-size", dict(instId=demo._NATIVE, tdMode="cross"), True),
    ):
        payload, acquired, raw = reads.read_original_v1(path, **query)
        results[name] = FreshPretradeGetTransportResultV1(
            get_performed=True,
            method="GET",
            endpoint=path + "?" + demo.urlencode(query),
            http_status=200,
            payload=payload,
            auth_header_sent=private,
            transport_class="OKX_EEA_DEMO_READ_ONLY_GET",
            venue_live_contact=True,
            historical_reuse=False,
            error_class="",
            body_sha256=sha256(raw).hexdigest(),
            pretrade_decision_id=acquisition_id,
            acquired_at_utc=acquired.isoformat(),
        )
        originals[name] = raw.hex()
    limits = capture_n1_venue_quantity_limits_v1(
        results=results,
        acquisition_decision_id=acquisition_id,
        account_identity=context.host.budget.account,
        bound_instrument=context.host.budget.bound,
        decision_epoch=cycle.replay.intermediate.market_context.decision_time,
        cycle_id=cycle.cycle_id,
        execution_environment="TESTNET",
    )
    if context.envelope.order_type != "market":
        raise ValueError("BTC_DEMO_ENTRY_MARKET_PLAN_REQUIRED")
    result = CurrentPostVenueQuantityContextV1(
        context.envelope, acquisition_id, limits.public_source, limits.private_source
    )
    packet = dict(
        sources={k: asdict(v) for k, v in results.items()},
        original_bodies_hex=originals,
        envelope_digest=context.envelope.envelope_digest,
    )
    root = context.store_root_v1()
    root.mkdir(parents=True, mode=0o700, exist_ok=True)
    immutable_json_v1(root / "quantity-sources.json", packet)
    return result


@dataclass(frozen=True)
class BtcDemoEntryPostContextV1:
    host: object
    entry: object
    reservation_id: str
    envelope: object
    plan_context: object
    pending_context: object
    quantity_context: object = None

    def store_root_v1(self):
        root = (
            demo._demo_lane_root(self.host.budget.root)
            / "entry-submit"
            / self.envelope.envelope_digest
        )
        if root.resolve() != root:
            raise ValueError("BTC_DEMO_ENTRY_SUBMIT_PATH_INVALID")
        return root

    def inspect_v1(self, *, envelope, signing_handle, claim=None, stage):
        from src.ops.btc_demo_offline_trading_host_v1 import BtcDemoOfflineTradingHostV1
        from src.ops.btc_demo_entry_reservation_v1 import _validate_sources
        from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
            FreshPretradeGetTransportResultV1,
        )
        from src.ops.full_core_live_path_composition_root_v1.pretrade_acquisition_v1 import (
            utc_now_iso_v1,
        )

        host = self.host
        if (
            type(host) is not BtcDemoOfflineTradingHostV1
            or type(host.budget.owner) is not BtcDemoBudgetOwnerV3
            or envelope != self.envelope
            or envelope.instrument_id != demo._NATIVE
            or envelope.reduce_only is not False
            or self.plan_context.order_environment != "TESTNET"
            or type(signing_handle) is not FullCoreK1BoundVenueAuthHandleV1
            or signing_handle.execution_environment != "TESTNET"
        ):
            raise ValueError("BTC_DEMO_ENTRY_ORIGINAL_TESTNET_CONTEXT_REQUIRED")
        cycle = host._original_entry_cycle(self.entry)
        owner = host.budget.owner
        link = owner.execution_links_v1().get(self.reservation_id)
        if link is None or link["envelope"] != asdict(envelope):
            raise ValueError("BTC_DEMO_ENTRY_ORIGINAL_PLAN_REQUIRED")
        sizing = owner.risk_snapshot_v1()["state"]["sizing_bindings"][self.reservation_id]
        checksum = sizing["applied_input"]["config_digest"]
        path = (
            demo._demo_lane_root(host.budget.root)
            / "entry-reservation-sources"
            / (checksum + ".json")
        )
        if path.resolve() != path:
            raise ValueError("BTC_DEMO_ENTRY_SOURCE_PATH_INVALID")
        packet = json.loads(path.read_bytes())
        if (
            digest(packet) != checksum
            or packet["policy_digest"] != owner.entry_budget_policy_v1().digest_v1()
        ):
            raise ValueError("BTC_DEMO_ENTRY_ORIGINAL_SOURCE_MISMATCH")
        _validate_sources(
            dict(
                packet,
                lane_id="LANE_3",
                authority="NONE",
                instrument_id=host.budget.bound.instrument_id,
                sources={
                    k: FreshPretradeGetTransportResultV1(**v) for k, v in packet["sources"].items()
                },
            ),
            budget=host.budget,
            cycle=cycle,
            now=utc_now_iso_v1(),
        )
        owner.inspect_current_entry_budget_policy_v1(self.reservation_id, envelope)
        owner.inspect_current_core_cursor_v1(self.reservation_id, envelope)
        proof = inspect_current_post_pending_v1(
            self.pending_context,
            envelope=envelope,
            stage=stage,
            expected_account=host.budget.account,
            execution_environment="TESTNET",
        )
        require_same_k1_venue_credential_v1(self.pending_context.source.credential, signing_handle)
        if claim is not None:
            claim.inspect_v1(
                envelope_digest=envelope.envelope_digest,
                attempt_root=self.store_root_v1(),
                account=proof["account"],
                action="ENTER",
                execution_environment="TESTNET",
            )
        quantity = self.quantity_context
        if quantity is None or quantity.envelope != envelope:
            raise ValueError("BTC_DEMO_ENTRY_QUANTITY_SOURCE_REQUIRED")
        retained = json.loads((self.store_root_v1() / "quantity-sources.json").read_bytes())
        if retained["envelope_digest"] != envelope.envelope_digest:
            raise ValueError("BTC_DEMO_ENTRY_QUANTITY_SOURCE_MISMATCH")
        from hashlib import sha256
        from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import canonical

        acquisition_id = canonical(
            dict(
                decision_epoch=cycle.replay.intermediate.market_context.decision_time,
                cycle_id=cycle.cycle_id,
            )
        )
        if quantity.acquisition_decision_id != acquisition_id:
            raise ValueError("BTC_DEMO_ENTRY_QUANTITY_DECISION_MISMATCH")
        for name, source in (
            ("instruments", quantity.public_source),
            ("max_size", quantity.private_source),
        ):
            raw = bytes.fromhex(retained["original_bodies_hex"][name])
            row = retained["sources"][name]
            if (
                source.acquisition_decision_id != acquisition_id
                or row["pretrade_decision_id"] != acquisition_id
                or source.endpoint != row["endpoint"]
                or source.acquired_at_utc != row["acquired_at_utc"]
                or sha256(raw).hexdigest() != row["body_sha256"]
                or source.response_body_sha256 != row["body_sha256"]
                or json.loads(raw) != row["payload"]
                or json.loads(source.payload_json) != row["payload"]
                or row["transport_class"] != "OKX_EEA_DEMO_READ_ONLY_GET"
                or row["get_performed"] is not True
                or row["method"] != "GET"
                or row["http_status"] != 200
                or row["auth_header_sent"] is not (name == "max_size")
                or row["error_class"] != ""
                or row["venue_live_contact"] is not True
                or row["historical_reuse"] is not False
                or row["data_safety_source_kind"] is not None
            ):
                raise ValueError("BTC_DEMO_ENTRY_QUANTITY_ORIGINAL_MISMATCH")
        if claim is not None:
            from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
                load_durable_post_owner_go_consume_v1,
            )

            mandate = load_durable_post_owner_go_consume_v1(store_root=self.store_root_v1())
            if mandate["record"]["baseline_origin_main_sha"] != host.repository_sha:
                raise ValueError("BTC_DEMO_ENTRY_MANDATE_BASELINE_MISMATCH")
        return proof


def execute_btc_demo_entry_post_v1(
    *,
    context,
    authorization,
    signing_handle,
    quantity_context,
    baseline_origin_main_sha,
    perform_real_venue_post,
    execution_integrity_backend=None,
    opener_factory=None,
):
    """One exact authorized attempt; an ACK is never treated as a fill."""
    from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.lifecycle_lock_v1 import (
        AuthorizationLifecycleLockV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
        resolve_and_assert_live_post_execution_baseline_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
        load_durable_post_owner_go_consume_v1,
        persist_durable_post_owner_go_consume_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
        POST_OWNER_GO,
        attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_safety_veto_v1 import (
        resolve_current_post_safety_context_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_venue_quantity_v1 import (
        inspect_current_post_venue_quantity_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_shared_post_owner_authority_v1 import (
        SharedPostOwnerAuthorizationV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
        inspect_original_portfolio_execution_context_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.pre_live_fresh_runtime_root_isolation_v1 import (
        assert_post_durable_store_root_isolation_v1,
    )

    if perform_real_venue_post is not True or type(context) is not BtcDemoEntryPostContextV1:
        raise ValueError("BTC_DEMO_ENTRY_EXPLICIT_SEND_REQUIRED")
    if (
        type(authorization) is not SharedPostOwnerAuthorizationV1
        or authorization.grant.environment != "TESTNET"
    ):
        raise ValueError("BTC_DEMO_ENTRY_TESTNET_GRANT_REQUIRED")
    context = replace(context, quantity_context=quantity_context)
    live_sha = resolve_and_assert_live_post_execution_baseline_v1(
        declared_baseline_origin_main_sha=baseline_origin_main_sha,
        integrity_backend=execution_integrity_backend,
    )
    if context.host.repository_sha != live_sha:
        raise ValueError("BTC_DEMO_ENTRY_REPOSITORY_MISMATCH")
    root = context.store_root_v1()
    assert_post_durable_store_root_isolation_v1(store_root=root)
    lock = AuthorizationLifecycleLockV1.for_evidence_root(
        evidence_root=root,
        authorization_id=context.envelope.envelope_digest,
        owner="BTC_DEMO_ENTER",
    )
    lock.acquire()
    try:
        with (
            exclusive_v1(context.host.cursor_root / "first_entry_mark_v2.lock"),
            context.host.budget.owner._lock,
        ):
            if (
                load_durable_post_owner_go_consume_v1(store_root=root)["consumed"]
                or load_external_effect_durable_consume_v1(store_root=root)["durable_consumed"]
            ):
                raise ValueError("BTC_DEMO_ENTRY_ALREADY_CONSUMED")
            proof = context.inspect_v1(
                envelope=context.envelope, signing_handle=signing_handle, stage="BEFORE_DEMO_ENTER"
            )
            owner = context.host.budget.owner
            inspect_original_portfolio_execution_context_v1(
                envelope=context.envelope,
                portfolio_budget_owner=owner,
                portfolio_reservation_id=context.reservation_id,
                execution_plan_context=context.plan_context,
                required_execution_environment="TESTNET",
            )
            inspect_current_post_venue_quantity_v1(
                quantity_context, envelope=context.envelope, stage="BEFORE_DEMO_ENTER"
            )
            safety = resolve_current_post_safety_context_v1(
                context.envelope, stage="BEFORE_DEMO_ENTER"
            )
            claim = authorization.consume_v1(
                account=proof["account"],
                action="ENTER",
                envelope_digest=context.envelope.envelope_digest,
                attempt_root=root,
                execution_environment="TESTNET",
            )
            persist_durable_post_owner_go_consume_v1(
                store_root=root,
                owner_go_token=POST_OWNER_GO,
                baseline_origin_main_sha=live_sha,
                shared_post_owner_claim_digest=claim.receipt_digest_v1(),
            )
            return attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
                envelope=context.envelope,
                post_owner_go=POST_OWNER_GO,
                store_root=root,
                k1_backend=None,
                opener_factory=opener_factory,
                portfolio_budget_owner=owner,
                portfolio_reservation_id=context.reservation_id,
                execution_plan_context=context.plan_context,
                post_safety_context=safety,
                post_quantity_context=quantity_context,
                post_pending_context=context.pending_context,
                shared_post_owner_claim=claim,
                testnet_entry_context=context,
                testnet_signing_handle=signing_handle,
            )
    finally:
        lock.release()
