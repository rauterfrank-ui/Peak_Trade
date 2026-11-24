"""Single TESTNET session-close dispatch through the original POST transport."""

from copy import deepcopy

from src.governance.current_productive_real_venue_post_admission_v1 import (
    evaluate_real_venue_post_admission_v1,
)
from src.ops.btc_demo_session_close_v1 import BOUNDED_SESSION_CLOSE, BtcDemoSessionCloseContextV1
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.lifecycle_lock_v1 import (
    AuthorizationLifecycleLockV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
    resolve_and_assert_live_post_execution_baseline_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
    POST_OWNER_GO,
    load_durable_post_owner_go_consume_v1,
    persist_durable_post_owner_go_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    assert_one_shot_join_permit_constraints_v1,
    mint_current_productive_one_shot_post_permit_v1,
    prove_one_shot_join_standing_boundary_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_safety_veto_v1 import (
    resolve_current_post_safety_context_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_shared_post_owner_authority_v1 import (
    SharedPostOwnerAuthorizationV1,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    _payload_from_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    DURABLE_STATE_SENT_INITIATED,
    claim_original_permit_transport_attempt_v1,
    finalize_external_effect_durable_consume_v1,
    load_external_effect_durable_consume_v1,
    persist_external_effect_durable_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
    classify_full_core_post_result_v1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    FullCoreSendCredentialHandleV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.pre_live_fresh_runtime_root_isolation_v1 import (
    assert_post_durable_store_root_isolation_v1,
)


def execute_btc_demo_session_close_v1(
    *,
    context,
    authorization,
    signing_handle,
    baseline_origin_main_sha,
    perform_real_venue_post,
    execution_integrity_backend=None,
    opener_factory=None,
):
    """Explicit caller-owned send. An ACK/timeout never closes or releases a hold."""
    if (
        perform_real_venue_post is not True
        or type(context) is not BtcDemoSessionCloseContextV1
        or type(authorization) is not SharedPostOwnerAuthorizationV1
        or authorization.grant.environment != "TESTNET"
    ):
        raise ValueError("BTC_DEMO_SESSION_CLOSE_EXPLICIT_TESTNET_GRANT_REQUIRED")
    prove_one_shot_join_standing_boundary_v1()
    live_sha = resolve_and_assert_live_post_execution_baseline_v1(
        declared_baseline_origin_main_sha=baseline_origin_main_sha,
        integrity_backend=execution_integrity_backend,
    )
    host = context.recovery.host
    if host.repository_sha != live_sha:
        raise ValueError("BTC_DEMO_SESSION_CLOSE_REPOSITORY_MISMATCH")
    root = context.store_root_v1()
    assert_post_durable_store_root_isolation_v1(store_root=root)
    envelope = context.envelope
    safety = resolve_current_post_safety_context_v1(envelope, stage="BEFORE_SESSION_CLOSE")
    if host.execution_incident_state_path != safety.state_path:
        raise ValueError("BTC_DEMO_SESSION_CLOSE_SAFETY_SOURCE_MISMATCH")
    lock = AuthorizationLifecycleLockV1.for_evidence_root(
        evidence_root=root, authorization_id=envelope.envelope_digest, owner=BOUNDED_SESSION_CLOSE
    )
    lock.acquire()
    attempt = None
    try:
        with host.owner._lock:
            if (
                load_durable_post_owner_go_consume_v1(store_root=root)["consumed"]
                or load_external_effect_durable_consume_v1(store_root=root)["durable_consumed"]
            ):
                raise ValueError("BTC_DEMO_SESSION_CLOSE_ALREADY_CONSUMED")
            registration = context.inspect_v1(signing_handle=signing_handle)
            veto = safety.inspect_v1(stage="BEFORE_SESSION_CLOSE_POST_GO")
            permit = mint_current_productive_one_shot_post_permit_v1(envelope, veto=veto)
            assert_one_shot_join_permit_constraints_v1(permit, envelope)
            control = host.owner._bounded_demo_session_control
            if control["phase"] == "RUNNING":
                host.owner._bounded_demo_session_control = dict(
                    deepcopy(control), phase="CLOSING", close_plan=deepcopy(context.plan)
                )
                host.owner._persist_locked()
            claim = authorization.consume_v1(
                account=registration.account_identity,
                action=BOUNDED_SESSION_CLOSE,
                envelope_digest=envelope.envelope_digest,
                attempt_root=root,
                execution_environment="TESTNET",
            )
            persist_durable_post_owner_go_consume_v1(
                store_root=root,
                owner_go_token=POST_OWNER_GO,
                baseline_origin_main_sha=live_sha,
                shared_post_owner_claim_digest=claim.receipt_digest_v1(),
            )
            admission = evaluate_real_venue_post_admission_v1(
                post_owner_go=POST_OWNER_GO,
                one_shot_real_post=True,
                permit=permit,
                store_root=root,
                shared_post_owner_claim_digest=claim.receipt_digest_v1(),
            )
            if not admission.post_admission_granted:
                raise ValueError(
                    "BTC_DEMO_SESSION_CLOSE_ADMISSION_DENIED:" + ",".join(admission.reason_codes)
                )
            persist_external_effect_durable_consume_v1(
                store_root=root,
                permit=permit,
                envelope=envelope,
                durable_state=DURABLE_STATE_SENT_INITIATED,
                post_count=0,
                outcome="BOUNDED_SESSION_CLOSE_PRE_SOCKET",
            )
            attempt = claim_original_permit_transport_attempt_v1(
                store_root=root,
                permit_id=permit.permit_id,
                envelope_id=envelope.envelope_id,
                envelope_digest=envelope.envelope_digest,
            )
            sender = FullCoreProductiveHttpTradeOrderTransportV1(
                handle=FullCoreSendCredentialHandleV1(
                    handle_id=signing_handle.handle_id, bound=True, material_loaded=False
                ),
                signing_handle=signing_handle,
                opener_factory=opener_factory,
                post_safety_context=safety,
                transport_attempt=attempt,
                shared_post_owner_claim=claim,
                testnet_session_close_context=context,
            )
            result = sender.post_trade_order(
                payload=_payload_from_envelope_v1(envelope),
                permit_id=attempt.permit_id,
                envelope_id=envelope.envelope_id,
                envelope_digest=envelope.envelope_digest,
                one_shot_real_post=True,
            )
            outcome = classify_full_core_post_result_v1(
                result=result, sent_clordid=envelope.client_order_id
            )
            finalize_external_effect_durable_consume_v1(
                store_root=root,
                permit_id=attempt.permit_id,
                envelope_id=envelope.envelope_id,
                envelope_digest=envelope.envelope_digest,
                outcome=outcome["classification"],
                observed_post_count=sender.post_count,
            )
            return result
    except (ValueError, RuntimeError, OSError):
        if attempt is not None:
            record = load_external_effect_durable_consume_v1(store_root=root)["record"]
            if record["transport_attempt"]["phase"] == "PRE_SOCKET":
                attempt.abort_before_transport_v1(reason_code="POST_AUTHORITY_SESSION_CLOSE_DENIED")
        raise
    finally:
        lock.release()
