"""Bounded CURRENT productive Enter-order actual venue POST (one-shot).

Consumes Owner-GO
OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1.

Fresh final-order envelope → durable POST Owner-GO consume → canonical admission →
one-shot join (permit, SENT_INITIATED, K1 opaque signing, urllib POST to
eea.okx.com /api/v5/trade/order). At most one real POST. No standing POST pins.

RUNTIME_AUTHORIZATION_EFFECT=SCOPED_SINGLE_ENTER_POST_ONLY_WHEN_EXPLICITLY_INVOKED
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlencode
from urllib.request import OpenerDirector

from src.governance.current_productive_real_venue_post_admission_v1 import (
    evaluate_real_venue_post_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    OsNativeStoreLookupBackendV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    FIRST_BOUNDED_REAL_ENTER_VENUE_POST_PROVEN,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
    load_durable_post_owner_go_consume_v1,
    persist_durable_post_owner_go_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    POST_OWNER_GO,
    CurrentProductiveOneShotFreshEnvelopeJoinError,
    OneShotJoinProbeV1,
    attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1,
    prove_one_shot_join_standing_boundary_v1,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    prove_follow_on_submit_isolated_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    TRADE_ORDER_PATH,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    finalize_external_effect_durable_consume_v1,
    load_external_effect_durable_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    issue_external_effect_permit_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_POSITIONS,
    FullCoreFreshPretradeGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    AUTHORIZED_HOST,
    FullCoreSendCredentialHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    CurrentProductiveActualVenuePostBaselineError,
    assert_declared_baseline_matches_slice_pin_v1,
    resolve_and_assert_live_post_execution_baseline_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_immediate_pre_mutation_freshness_v1 import (
    CurrentProductiveActualVenuePostPreMutationFreshnessError,
    prove_immediate_pre_mutation_freshness_for_actual_venue_post_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_fresh_executable_enter_final_order_envelope_runtime_reach_to_one_shot_post_join_boundary_v1 import (
    resolve_fresh_executable_enter_final_order_envelope_from_pre_external_closure_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    CurrentProductiveFullCorePreExternalClosureResultV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1 import (
    _assert_no_secrets,
    _persist_json,
    _token,
    _utc_now_iso_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)

OWNER_GO = POST_OWNER_GO
THIS_SLICE = (
    "11.2.1.DM.FULL_CORE_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_"
    "BOUND_SINGLE_USE_PERMIT_V1"
)
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_actual_venue_post_with_fresh_envelope_"
    "bound_single_use_permit_v1"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
_REPO_ROOT = Path(__file__).resolve().parents[3]


class CurrentProductiveActualVenuePostError(RuntimeError):
    """Fail-closed actual-venue Enter POST violation."""


@dataclass(frozen=True)
class CurrentProductiveActualVenuePostResultV1:
    store_root: str
    evidence_root: str
    owner_go_consumed: str
    post_admission_granted: str
    fresh_envelope_validated: str
    single_use_permit_minted: str
    permit_bound_to_envelope: str
    permit_unused_before_attempt: str
    pre_live_proof_complete: str
    real_venue_post_attempted: str
    real_venue_post_performed: str
    post_outcome: str
    real_order_submission: str
    live_funds_exposure: str
    permit_completed: str
    permit_reusable: str
    second_post_performed: str
    replay_attempt_blocked: str
    enter_reconciliation_status: str
    secret_disclosed: str
    secret_persisted: str
    post_allowed_standing: str
    real_venue_post_allowed_standing: str
    envelope_id: str
    envelope_digest: str
    permit_id: str
    http_status: str
    venue_ack_validated: str
    evidence_manifest: str
    manifest_verify_rc: int


def _assert_global_standing_pins_v1() -> None:
    prove_one_shot_join_standing_boundary_v1()
    if (
        EXTERNAL_EFFECT_AUTHORIZED is True
        or POST_ALLOWED is True
        or REAL_VENUE_POST_ALLOWED is True
    ):
        raise CurrentProductiveActualVenuePostError("STANDING_POST_PINS_MUST_REMAIN_FALSE")
    if FIRST_BOUNDED_REAL_ENTER_VENUE_POST_PROVEN is True:
        raise CurrentProductiveActualVenuePostError("ENTER_POST_MILESTONE_ALREADY_PROVEN")
    if str(STEP_29Q_PLAN_ONLY) != "PLAN_ONLY":
        raise CurrentProductiveActualVenuePostError("STEP_29Q_MUST_REMAIN_PLAN_ONLY")
    if int(MAX_POSITIONS_EFFECTIVE) != 1:
        raise CurrentProductiveActualVenuePostError("MAX_POSITIONS_EFFECTIVE_MUST_REMAIN_ONE")
    blocker = current_productive_first_real_blocker_v1()
    if blocker != (
        "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
    ):
        raise CurrentProductiveActualVenuePostError("FIRST_REAL_BLOCKER_DRIFT")


def _sanitized_ack_payload_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed = ("code", "msg", "data", "sCode", "sMsg", "ordId", "clOrdId", "ts")
    out: dict[str, Any] = {}
    for key in allowed:
        if key in payload:
            out[key] = payload[key]
    _assert_no_secrets(out)
    return out


def _enter_reconciliation_v1(
    *,
    envelope: FinalOrderEnvelopeV1,
    transport: FullCoreFreshPretradeGetTransportV1 | None,
) -> str:
    if transport is None:
        return "NOT_ATTEMPTED_NO_READ_TRANSPORT"
    query = {"instType": "SWAP", "instId": envelope.instrument_id}
    endpoint = f"{ENDPOINT_ACCOUNT_POSITIONS}?{urlencode(query)}"
    try:
        result = transport.get(
            endpoint=endpoint,
            auth_required=True,
            pretrade_decision_id=envelope.instrument_id,
        )
    except Exception:
        return "READ_FAIL_CLOSED"
    if result.get_performed is not True or result.payload is None:
        return "READ_INCOMPLETE"
    blob = json.dumps(result.payload, sort_keys=True, default=str)[:4096]
    _assert_no_secrets({"preview": blob})
    return "READ_ONLY_POSITION_SNAPSHOT_RECORDED"


def prove_pre_live_actual_venue_post_readiness_from_pre_external_closure_v1(
    *,
    owner_go: str,
    baseline_origin_main_sha: str,
    closure: CurrentProductiveFullCorePreExternalClosureResultV1,
    store_root: Path | str,
    k1_backend: OsNativeStoreLookupBackendV1 | None = None,
) -> dict[str, str]:
    """Resolve fresh EXECUTABLE envelope from PRE_EXTERNAL closure; pre-live only."""
    envelope = resolve_fresh_executable_enter_final_order_envelope_from_pre_external_closure_v1(
        closure
    )
    return prove_pre_live_actual_venue_post_readiness_v1(
        owner_go=owner_go,
        baseline_origin_main_sha=baseline_origin_main_sha,
        envelope=envelope,
        store_root=store_root,
        k1_backend=k1_backend,
    )


def prove_pre_live_actual_venue_post_readiness_v1(
    *,
    owner_go: str,
    baseline_origin_main_sha: str,
    envelope: FinalOrderEnvelopeV1,
    store_root: Path | str,
    k1_backend: OsNativeStoreLookupBackendV1 | None = None,
) -> dict[str, str]:
    """Runtime pre-live checklist. Does not consume Owner-GO or POST."""
    if str(owner_go or "") != OWNER_GO:
        raise CurrentProductiveActualVenuePostError("OWNER_GO_MISMATCH")
    try:
        assert_declared_baseline_matches_slice_pin_v1(
            declared_baseline_origin_main_sha=baseline_origin_main_sha
        )
    except CurrentProductiveActualVenuePostBaselineError as exc:
        raise CurrentProductiveActualVenuePostError(str(exc)) from exc
    _assert_global_standing_pins_v1()
    assert_envelope_unmodified_v1(envelope)
    if load_durable_post_owner_go_consume_v1(store_root=store_root).get("consumed") is True:
        raise CurrentProductiveActualVenuePostError("POST_OWNER_GO_ALREADY_DURABLE_CONSUMED")
    permit = issue_external_effect_permit_v1(envelope, authority_ref=OWNER_GO)
    admission = evaluate_real_venue_post_admission_v1(
        post_owner_go=OWNER_GO,
        one_shot_real_post=True,
        permit=permit,
        store_root=store_root,
    )
    host_ok = AUTHORIZED_HOST == "eea.okx.com"
    path_ok = TRADE_ORDER_PATH == "/api/v5/trade/order"
    k1_ok = k1_backend is not None
    pre_live_ok = host_ok and path_ok and k1_ok
    return {
        "OWNER_GO_CONSUMED": "false",
        "POST_ADMISSION_GRANTED": "false",
        "FRESH_ENVELOPE_VALIDATED": "true",
        "SINGLE_USE_PERMIT_MINTED": "true",
        "PERMIT_BOUND_TO_ENVELOPE": "true",
        "PERMIT_UNUSED_BEFORE_ATTEMPT": "true",
        "EXPECTED_HOST_EEA_OKX": _token(host_ok),
        "EXPECTED_TRADE_ORDER_PATH": _token(path_ok),
        "K1_BACKEND_AVAILABLE": _token(k1_ok),
        "PRE_LIVE_PROOF_COMPLETE": _token(pre_live_ok),
        "POST_ADMISSION_PENDING_DURABLE_GO_CONSUME": _token(
            admission.post_admission_granted is not True
        ),
        "SECRET_DISCLOSED": "false",
        "SECRET_PERSISTED": "false",
    }


def execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
    *,
    owner_go: str,
    baseline_origin_main_sha: str,
    envelope: FinalOrderEnvelopeV1,
    store_root: Path | str,
    evidence_root: Path | str | None = None,
    perform_real_venue_post: bool,
    k1_backend: OsNativeStoreLookupBackendV1 | None = None,
    opener_factory: Callable[[], OpenerDirector] | None = None,
    read_only_get_transport: FullCoreFreshPretradeGetTransportV1 | None = None,
) -> CurrentProductiveActualVenuePostResultV1:
    if str(owner_go or "") != OWNER_GO:
        raise CurrentProductiveActualVenuePostError("OWNER_GO_MISMATCH")
    if perform_real_venue_post is not True:
        raise CurrentProductiveActualVenuePostError("PERFORM_REAL_VENUE_POST_REQUIRED")
    try:
        resolve_and_assert_live_post_execution_baseline_v1(
            declared_baseline_origin_main_sha=baseline_origin_main_sha,
            repo_root=_REPO_ROOT,
        )
    except CurrentProductiveActualVenuePostBaselineError as exc:
        raise CurrentProductiveActualVenuePostError(str(exc)) from exc
    _assert_global_standing_pins_v1()
    assert_envelope_unmodified_v1(envelope)
    root = Path(store_root)
    root.mkdir(parents=True, exist_ok=True)
    pre = prove_pre_live_actual_venue_post_readiness_v1(
        owner_go=owner_go,
        baseline_origin_main_sha=baseline_origin_main_sha,
        envelope=envelope,
        store_root=root,
        k1_backend=k1_backend,
    )
    if pre.get("PRE_LIVE_PROOF_COMPLETE") != "true":
        raise CurrentProductiveActualVenuePostError("PRE_LIVE_PROOF_INCOMPLETE")
    pre_mutation_id = f"actual-venue-post:{envelope.envelope_id}"
    try:
        freshness = prove_immediate_pre_mutation_freshness_for_actual_venue_post_v1(
            envelope=envelope,
            read_only_get_transport=read_only_get_transport,
            pretrade_decision_id=pre_mutation_id,
        )
    except CurrentProductiveActualVenuePostPreMutationFreshnessError as exc:
        raise CurrentProductiveActualVenuePostError(str(exc)) from exc
    if freshness.all_required_pre_post_gates_pass is not True:
        raise CurrentProductiveActualVenuePostError("PRE_MUTATION_FRESHNESS_FAIL_CLOSED")
    persist_durable_post_owner_go_consume_v1(
        store_root=root,
        owner_go_token=OWNER_GO,
        baseline_origin_main_sha=baseline_origin_main_sha,
    )
    durable_before = load_external_effect_durable_consume_v1(store_root=root)
    permit_unused = durable_before.get("durable_consumed") is not True
    probe = OneShotJoinProbeV1()
    post_outcome = "NOT_ATTEMPTED"
    real_attempted = False
    real_performed = False
    real_submission = False
    live_exposure = False
    permit_completed = False
    second_post = False
    replay_blocked = False
    http_status = "0"
    venue_ack = "false"
    permit_id = ""
    join_outcome = ""
    ack_payload: dict[str, Any] = {}
    join_error: str | None = None
    try:
        join = attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
            envelope=envelope,
            post_owner_go=OWNER_GO,
            store_root=root,
            k1_backend=k1_backend,
            opener_factory=opener_factory,
            probe=probe,
        )
        real_attempted = probe.http_post_attempts >= 1
        real_performed = (
            probe.external_effect_count >= 1 or join.outcome == "ONE_SHOT_REAL_POST_RECORDED"
        )
        real_submission = real_performed or join.unknown_outcome is True
        live_exposure = real_attempted
        post_outcome = str(join.outcome)
        permit_id = join.permit_id
        join_outcome = join.outcome
        if join.http_status:
            http_status = str(join.http_status)
        if join.unknown_outcome is True:
            post_outcome = "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
        elif real_performed:
            post_outcome = "VENUE_ACK_RECORDED"
            venue_ack = "true"
            finalize_external_effect_durable_consume_v1(
                store_root=root,
                permit_id=join.permit_id,
                envelope_id=join.envelope_id,
                envelope_digest=join.envelope_digest,
                outcome=post_outcome,
            )
            permit_completed = True
    except CurrentProductiveOneShotFreshEnvelopeJoinError as exc:
        msg = str(exc)
        join_error = msg
        if "UNKNOWN_OUTCOME" in msg:
            real_attempted = probe.http_post_attempts >= 1
            post_outcome = "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
            live_exposure = real_attempted
            real_submission = real_attempted
            real_performed = False
        else:
            raise CurrentProductiveActualVenuePostError(msg) from exc
    handle = FullCoreSendCredentialHandleV1(
        handle_id="replay-proof-handle",
        bound=True,
        material_loaded=False,
    )
    permit_replay = issue_external_effect_permit_v1(envelope, authority_ref=OWNER_GO)
    replay_blocked = prove_follow_on_submit_isolated_v1(
        envelope=envelope,
        permit=permit_replay,
        store_root=root,
        transport=_ReplayBlockedTransportV1(),
        handle=handle,
    )
    second_post = probe.http_post_attempts > 1
    recon = _enter_reconciliation_v1(envelope=envelope, transport=read_only_get_transport)
    ev_root = (
        Path(evidence_root) if evidence_root is not None else _REPO_ROOT / CANONICAL_PACK_RELPATH
    )
    ts = _utc_now_iso_v1().replace(":", "").replace("-", "")[:15] + "Z"
    pack = ev_root / ts
    pack.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {
        "DOCUMENT_CLASS": THIS_SLICE,
        "BASELINE_ORIGIN_MAIN_SHA": baseline_origin_main_sha,
        "OWNER_GO_CONSUMED": TRUE_TOKEN,
        "POST_ADMISSION_GRANTED": TRUE_TOKEN,
        "FRESH_ENVELOPE_VALIDATED": TRUE_TOKEN,
        "REAL_VENUE_POST_ATTEMPTED": _token(real_attempted),
        "REAL_VENUE_POST_PERFORMED": _token(real_performed),
        "POST_OUTCOME": post_outcome,
        "REAL_ORDER_SUBMISSION": _token(real_submission),
        "LIVE_FUNDS_EXPOSURE": _token(live_exposure),
        "SECOND_POST_PERFORMED": _token(second_post),
        "RETRY_AUTHORIZED": FALSE_TOKEN,
        "PERMIT_REUSABLE": FALSE_TOKEN,
        "PERMIT_COMPLETED": _token(permit_completed),
        "REPLAY_ATTEMPT_BLOCKED": _token(replay_blocked),
        "ENTER_RECONCILIATION_STATUS": recon,
        "CREDENTIAL_MATERIAL_DISCLOSED": FALSE_TOKEN,
        "CREDENTIAL_MATERIAL_PERSISTED": FALSE_TOKEN,
        "POST_ALLOWED_STANDING": FALSE_TOKEN,
        "REAL_VENUE_POST_ALLOWED_STANDING": FALSE_TOKEN,
        "ENVELOPE_ID": envelope.envelope_id,
        "ENVELOPE_DIGEST": envelope.envelope_digest,
        "PERMIT_ID": permit_id,
        "HTTP_STATUS": http_status,
        "VENUE_ACK_VALIDATED": venue_ack,
        "JOIN_OUTCOME": join_outcome,
        "ACK_PAYLOAD": ack_payload,
    }
    _assert_no_secrets(summary)
    _persist_json(path=pack / "SUMMARY.json", payload=summary)
    manifest_path = persist_manifest_sha256_v1(store_root=pack)
    manifest_rc = verify_manifest_sha256_v1(store_root=pack)
    return CurrentProductiveActualVenuePostResultV1(
        store_root=str(root),
        evidence_root=str(pack),
        owner_go_consumed=TRUE_TOKEN,
        post_admission_granted=TRUE_TOKEN,
        fresh_envelope_validated=TRUE_TOKEN,
        single_use_permit_minted=TRUE_TOKEN,
        permit_bound_to_envelope=TRUE_TOKEN,
        permit_unused_before_attempt=_token(permit_unused),
        pre_live_proof_complete=TRUE_TOKEN,
        real_venue_post_attempted=_token(real_attempted),
        real_venue_post_performed=_token(real_performed),
        post_outcome=post_outcome,
        real_order_submission=_token(real_submission),
        live_funds_exposure=_token(live_exposure),
        permit_completed=_token(permit_completed),
        permit_reusable=FALSE_TOKEN,
        second_post_performed=_token(second_post),
        replay_attempt_blocked=_token(replay_blocked),
        enter_reconciliation_status=recon,
        secret_disclosed=FALSE_TOKEN,
        secret_persisted=FALSE_TOKEN,
        post_allowed_standing=FALSE_TOKEN,
        real_venue_post_allowed_standing=FALSE_TOKEN,
        envelope_id=envelope.envelope_id,
        envelope_digest=envelope.envelope_digest,
        permit_id=permit_id,
        http_status=http_status,
        venue_ack_validated=venue_ack,
        evidence_manifest=str(manifest_path),
        manifest_verify_rc=int(manifest_rc),
    )


class _ReplayBlockedTransportV1:
    def post_trade_order(self, **_kwargs: Any) -> Any:
        raise RuntimeError("REPLAY_TRANSPORT_MUST_NOT_RUN")


__all__ = [
    "CANONICAL_PACK_RELPATH",
    "EXPECTED_BASELINE_ORIGIN_MAIN_SHA",
    "OWNER_GO",
    "THIS_SLICE",
    "CurrentProductiveActualVenuePostError",
    "CurrentProductiveActualVenuePostResultV1",
    "execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1",
    "prove_pre_live_actual_venue_post_readiness_from_pre_external_closure_v1",
    "prove_pre_live_actual_venue_post_readiness_v1",
]
