"""CURRENT productive one-shot join. No venue socket in this work package.

Fresh final-order envelope → envelope-bound single-use permit → durable
SENT_INITIATED consume (existing send seam) → K1 opaque signing handle
(#6746 seam) → existing HTTP trade-order transport.

Actual venue POST stays unreachable unless the caller passes the exact
unconsumed POST Owner-GO. This module does not consume that GO, does not
open the real Keychain, and does not flip standing pins.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.request import OpenerDirector

from src.governance.current_productive_real_venue_post_admission_v1 import (
    evaluate_real_venue_post_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
    OsNativeStoreLookupBackendV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_dw_exchange_reconciliation_wiring_v1 import (
    DISPOSITION_SKIPPED,
    DwExchangeReconciliationWiringConfigV1,
    DwExchangeReconciliationWiringModeV1,
    run_dw_exchange_reconciliation_wiring_after_post_submit_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_post_admission_seal_v1 import (
    OneShotPostAdmissionSealError,
    prove_current_productive_one_shot_post_admission_seal_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1 import (
    OWNER_GO as K1_OPAQUE_SIGNING_OWNER_GO,
    CurrentProductiveK1OpaqueSigningHandleError,
    open_current_productive_k1_opaque_signing_handle_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    FullCoreEnvelopeBoundSendSeamError,
    _payload_from_envelope_v1,
    attempt_envelope_bound_external_effect_send_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_global_venue_effect_authority_ledger_v1 import (
    RISK_CLASS_NEW_RISK,
    RISK_CLASS_RISK_REDUCING,
    STATE_ABORTED_BEFORE_TRANSPORT,
    STATE_CLAIMED,
    STATE_COMPLETED_RESPONSE_RECEIVED,
    STATE_SENT_INITIATED,
    STATE_UNKNOWN_OUTCOME,
    GlobalVenueEffectAuthorityLedgerV1,
    GlobalVenueEffectClaimV1,
    GlobalVenueEffectIdentityV1,
    GlobalVenueEffectLedgerError,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_path_kill_switch_gate_v1 import (
    PreSendSafetyGateV1,
    evaluate_post_path_kill_switch_v1,
    read_post_path_kill_switch_evidence_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_risk_reduction_venue_proof_v1 import (
    RiskReductionNotProvenError,
    RiskReductionVenueProofV1,
    assert_risk_reduction_proof_valid_for_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    abort_external_effect_durable_consume_before_transport_v1,
    load_external_effect_durable_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ExternalEffectPermitV1,
    FullCoreExternalEffectPermitError,
    assert_permit_matches_envelope_v1,
    issue_external_effect_permit_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    ISSUED_FOR_EXACT_ACTION,
    FinalOrderEnvelopeV1,
    FullCoreFinalOrderEnvelopeError,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    PRE_SEND_GATE_DENIED_PREFIX,
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    FullCoreSendCredentialHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)

POST_OWNER_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1"
)
POST_GO_STATUS = "UNCONSUMED"
POST_GO_CONSUMED = False
THIS_SLICE = (
    "CURRENT_PRODUCTIVE_ONE_SHOT_FRESH_ENVELOPE_PERMIT_MINT_DURABLE_CONSUME_AND_POST_JOIN_V1"
)
JOIN_SEAM_ID = (
    "CURRENT_PRODUCTIVE_ONE_SHOT_FRESH_ENVELOPE_PERMIT_MINT_DURABLE_CONSUME_AND_POST_JOIN_V1"
)
_WIRE_BODY_KEYS = frozenset(
    {"clOrdId", "instId", "side", "ordType", "sz", "tdMode", "px", "posSide", "reduceOnly"}
)


class CurrentProductiveOneShotFreshEnvelopeJoinError(RuntimeError):
    """Fail-closed one-shot fresh-envelope join violation."""


@dataclass
class OneShotJoinProbeV1:
    """Non-secret call-order probe. Never stores credential material."""

    events: list[str] = field(default_factory=list)
    http_post_attempts: int = 0
    observed_transport_venue_live_contact: int = 0
    external_effect_count: int = 0
    permit_minted: bool = False
    one_shot_real_post_forwarded: bool = False


@dataclass(frozen=True)
class OneShotJoinResultV1:
    outcome: str
    permit_id: str
    envelope_id: str
    envelope_digest: str
    durable_consumed: bool
    http_post_attempts: int
    external_effect_count: int
    unknown_outcome: bool
    post_go_status: str
    step_29q_status: str
    http_status: int = 0
    post_outcome_phase: str = ""
    dw_exchange_reconciliation_wiring_mode: str = (
        DwExchangeReconciliationWiringModeV1.DISABLED.value
    )
    dw_exchange_reconciliation_invoked: bool = False
    dw_exchange_reconciliation_disposition: str = DISPOSITION_SKIPPED
    dw_exchange_reconciliation_outcome: str = ""
    dw_exchange_reconciliation_ghv_forward_join: str = ""
    dw_exchange_reconciliation_ghv_reverse_join: str = ""
    dw_exchange_reconciliation_error: str = ""


def _assert_standing_pins_v1() -> None:
    if REAL_KEYCHAIN_ACCESS_AUTHORIZED is True or REAL_KEYCHAIN_ACCESS_IMPLEMENTED is True:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError(
            "STANDING_REAL_KEYCHAIN_ACCESS_MUST_REMAIN_FALSE"
        )
    if (
        EXTERNAL_EFFECT_AUTHORIZED is True
        or POST_ALLOWED is True
        or REAL_VENUE_POST_ALLOWED is True
    ):
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("POST_STANDING_MUST_REMAIN_FALSE")
    if POST_GO_CONSUMED is True or POST_GO_STATUS != "UNCONSUMED":
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("POST_GO_MUST_REMAIN_UNCONSUMED")
    if str(STEP_29Q_PLAN_ONLY) != "PLAN_ONLY":
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("STEP_29Q_MUST_REMAIN_PLAN_ONLY")
    if int(MAX_POSITIONS_EFFECTIVE) != 1:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError(
            "MAX_POSITIONS_EFFECTIVE_MUST_REMAIN_ONE"
        )
    blocker = current_productive_first_real_blocker_v1()
    if blocker != (
        "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
    ):
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("FIRST_REAL_BLOCKER_DRIFT")


def _reject_request_shape_v1(
    *,
    retry_allowed: bool,
    second_submit_allowed: bool,
    max_post_count: int,
    rerank: bool,
    reselect: bool,
    sizing_recompute: bool,
    mv2_double_play_reevaluate: bool,
) -> None:
    if retry_allowed is True:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("RETRY_ALLOWED_FORBIDDEN")
    if second_submit_allowed is True:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("SECOND_SUBMIT_FORBIDDEN")
    if int(max_post_count) != 1:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("MAX_POST_COUNT_NOT_ONE")
    if (
        rerank is True
        or reselect is True
        or sizing_recompute is True
        or mv2_double_play_reevaluate is True
    ):
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("DECISION_BACKFLOW_FORBIDDEN")


def assert_one_shot_join_permit_constraints_v1(
    permit: ExternalEffectPermitV1,
    envelope: FinalOrderEnvelopeV1,
) -> None:
    """Deny wrong authority, digest drift, and any non-single-use shape."""

    try:
        assert_permit_matches_envelope_v1(permit, envelope)
    except FullCoreExternalEffectPermitError as exc:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError(str(exc)) from exc
    if str(permit.authority_ref or "") != POST_OWNER_GO:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("AUTHORITY_REF_MISMATCH")
    if permit.issued_for_exact_action != ISSUED_FOR_EXACT_ACTION:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("ISSUED_FOR_EXACT_ACTION_MISMATCH")
    if permit.single_use is not True or int(permit.max_post_count) != 1:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("SINGLE_USE_REQUIRED")
    if permit.retry_allowed is True or permit.second_submit_allowed is True:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("RETRY_OR_SECOND_SUBMIT_FORBIDDEN")


def build_global_venue_effect_identity_v1(
    *,
    ledger: GlobalVenueEffectAuthorityLedgerV1,
    envelope: FinalOrderEnvelopeV1,
    permit_id: str,
    post_owner_go: str,
    baseline_origin_main_sha: str = "",
) -> GlobalVenueEffectIdentityV1:
    return GlobalVenueEffectIdentityV1(
        owner_go_token=str(post_owner_go or ""),
        account_scope=ledger.account_scope,
        environment=ledger.environment,
        permit_id=str(permit_id or ""),
        envelope_id=envelope.envelope_id,
        envelope_digest=envelope.envelope_digest,
        client_order_id=envelope.client_order_id,
        risk_class=RISK_CLASS_RISK_REDUCING
        if envelope.reduce_only is True
        else RISK_CLASS_NEW_RISK,
        baseline_origin_main_sha=str(baseline_origin_main_sha or ""),
    )


def _bind_global_claim_v1(
    *,
    ledger: GlobalVenueEffectAuthorityLedgerV1,
    claim: GlobalVenueEffectClaimV1,
    envelope: FinalOrderEnvelopeV1,
    permit: ExternalEffectPermitV1,
    post_owner_go: str,
) -> GlobalVenueEffectClaimV1:
    if not isinstance(claim, GlobalVenueEffectClaimV1):
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("GLOBAL_CLAIM_REQUIRED")
    held = claim.identity
    expected = build_global_venue_effect_identity_v1(
        ledger=ledger,
        envelope=envelope,
        permit_id=permit.permit_id,
        post_owner_go=post_owner_go,
        baseline_origin_main_sha=held.baseline_origin_main_sha,
    )
    try:
        if claim.ledger_namespace != str(ledger.namespace):
            raise CurrentProductiveOneShotFreshEnvelopeJoinError("GLOBAL_CLAIM_NAMESPACE_MISMATCH")
        for actual, wanted, label in (
            (held.owner_authorization_identity(), expected.owner_authorization_identity(), "OWNER"),
            (held.permit_id, expected.permit_id, "PERMIT_ID"),
            (held.envelope_digest, expected.envelope_digest, "ENVELOPE_DIGEST"),
            (held.client_order_id, expected.client_order_id, "CLIENT_ORDER_ID"),
            (held.risk_class, expected.risk_class, "RISK_CLASS"),
        ):
            if actual != wanted:
                raise CurrentProductiveOneShotFreshEnvelopeJoinError(
                    f"GLOBAL_CLAIM_BINDING_MISMATCH:{label}"
                )
        if claim.claim_id != held.claim_id():
            raise CurrentProductiveOneShotFreshEnvelopeJoinError("GLOBAL_CLAIM_ID_MISMATCH")
        record = ledger.load_claim_v1(claim.claim_id)
        if str(record.get("state") or "") != STATE_CLAIMED:
            raise CurrentProductiveOneShotFreshEnvelopeJoinError("GLOBAL_CLAIM_NOT_CLAIMED_STATE")
        return claim
    except GlobalVenueEffectLedgerError as exc:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError(str(exc)) from exc


def _settle_global_claim_v1(
    *,
    ledger: GlobalVenueEffectAuthorityLedgerV1,
    claim_id: str,
    no_socket: bool,
    unknown: bool,
    detail: str,
) -> str:
    """Record the deterministic transport outcome. Never restores authority.

    Never raises: a failed settle leaves the claim unresolved (blocks new risk)
    and must not mask the transport outcome.
    """
    try:
        state = str(ledger.load_claim_v1(claim_id).get("state") or "")
        if state == STATE_CLAIMED:
            ledger.abandon_unsent_claim_v1(claim_id, reason=detail)
            return STATE_ABORTED_BEFORE_TRANSPORT
        if state != STATE_SENT_INITIATED:
            return state
        if no_socket:
            outcome = STATE_ABORTED_BEFORE_TRANSPORT
        elif unknown:
            outcome = STATE_UNKNOWN_OUTCOME
        else:
            outcome = STATE_COMPLETED_RESPONSE_RECEIVED
        ledger.mark_outcome_v1(claim_id, outcome_state=outcome, detail=detail)
        return outcome
    except Exception as exc:  # noqa: BLE001
        return f"GLOBAL_LEDGER_SETTLE_FAILED:{type(exc).__name__}"


class _DurableConsumeThenK1HttpTransportV1:
    """Send-seam transport. Consume is already durable before this object runs."""

    def __init__(
        self,
        *,
        envelope: FinalOrderEnvelopeV1,
        store_root: Path | str,
        k1_backend: OsNativeStoreLookupBackendV1 | None,
        opener_factory: Callable[[], OpenerDirector] | None,
        probe: OneShotJoinProbeV1,
        send_handle: FullCoreSendCredentialHandleV1,
        global_ledger: GlobalVenueEffectAuthorityLedgerV1,
        global_claim_id: str,
        risk_reduction_proof: RiskReductionVenueProofV1 | None,
    ) -> None:
        self._envelope = envelope
        self._store_root = store_root
        self._k1_backend = k1_backend
        self._opener_factory = opener_factory
        self._probe = probe
        self._send_handle = send_handle
        self._global_ledger = global_ledger
        self._global_claim_id = global_claim_id
        self._risk_reduction_proof = risk_reduction_proof
        self.pre_send_gate: PreSendSafetyGateV1 | None = None

    def post_trade_order(
        self,
        *,
        payload: Mapping[str, Any],
        permit_id: str,
        envelope_id: str,
        envelope_digest: str,
        one_shot_real_post: bool = False,
    ) -> Any:
        existing = load_external_effect_durable_consume_v1(store_root=self._store_root)
        if existing.get("durable_consumed") is not True:
            raise FullCoreProductiveHttpPostError("DURABLE_CONSUME_NOT_BEFORE_TRANSPORT")
        record = existing.get("record") or {}
        if str(record.get("durable_state") or "") != "SENT_INITIATED":
            raise FullCoreProductiveHttpPostError("DURABLE_STATE_NOT_SENT_INITIATED")
        if str(record.get("envelope_id") or "") != envelope_id:
            raise FullCoreProductiveHttpPostError("DURABLE_ENVELOPE_ID_MISMATCH")
        if str(record.get("envelope_digest") or "") != envelope_digest:
            raise FullCoreProductiveHttpPostError("DURABLE_ENVELOPE_DIGEST_MISMATCH")
        if record.get("retry_allowed") is True or record.get("resubmit_allowed") is True:
            raise FullCoreProductiveHttpPostError("DURABLE_RETRY_FORBIDDEN")
        expected = _payload_from_envelope_v1(self._envelope)
        if dict(payload) != expected or not set(payload).issubset(_WIRE_BODY_KEYS):
            raise FullCoreProductiveHttpPostError("WIRE_BODY_ENVELOPE_MISMATCH")
        self._probe.events.append("DURABLE_CONSUME_OBSERVED")
        try:
            self._global_ledger.mark_sent_initiated_v1(
                self._global_claim_id,
                permit_id=permit_id,
                envelope_digest=envelope_digest,
            )
        except GlobalVenueEffectLedgerError as exc:
            raise FullCoreProductiveHttpPostError(f"{PRE_SEND_GATE_DENIED_PREFIX}:{exc}") from exc
        self._probe.events.append("GLOBAL_SENT_INITIATED")
        self.pre_send_gate = PreSendSafetyGateV1(
            envelope=self._envelope,
            permit_id=permit_id,
            global_ledger=self._global_ledger,
            global_claim_id=self._global_claim_id,
            risk_reduction_proof=self._risk_reduction_proof,
        )
        self._probe.one_shot_real_post_forwarded = one_shot_real_post is True
        try:
            with open_current_productive_k1_opaque_signing_handle_session_v1(
                owner_go=K1_OPAQUE_SIGNING_OWNER_GO,
                backend=self._k1_backend,
            ) as session:
                self._probe.events.append("K1_BOUND")
                self._probe.events.append("HTTP_POST_ENTER")
                http = FullCoreProductiveHttpTradeOrderTransportV1(
                    handle=self._send_handle,
                    signing_handle=session.signing_handle,
                    opener_factory=self._opener_factory,
                    pre_send_safety_gate=self.pre_send_gate,
                )
                try:
                    result = http.post_trade_order(
                        payload=payload,
                        permit_id=permit_id,
                        envelope_id=envelope_id,
                        envelope_digest=envelope_digest,
                        one_shot_real_post=one_shot_real_post,
                    )
                finally:
                    self._probe.http_post_attempts += int(http.post_count)
                    if http.venue_live_contact is True:
                        self._probe.observed_transport_venue_live_contact += 1
                        if self._opener_factory is None:
                            self._probe.external_effect_count += 1
                return result
        except CurrentProductiveK1OpaqueSigningHandleError as exc:
            self._probe.events.append("K1_FAILED")
            raise FullCoreProductiveHttpPostError("K1_SIGNING_HANDLE_UNAVAILABLE") from exc


def attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
    *,
    envelope: FinalOrderEnvelopeV1,
    post_owner_go: str,
    store_root: Path | str | None,
    k1_backend: OsNativeStoreLookupBackendV1 | None,
    opener_factory: Callable[[], OpenerDirector] | None = None,
    probe: OneShotJoinProbeV1 | None = None,
    retry_allowed: bool = False,
    second_submit_allowed: bool = False,
    max_post_count: int = 1,
    rerank: bool = False,
    reselect: bool = False,
    sizing_recompute: bool = False,
    mv2_double_play_reevaluate: bool = False,
    dw_exchange_reconciliation_wiring_mode: (
        DwExchangeReconciliationWiringModeV1 | str
    ) = DwExchangeReconciliationWiringModeV1.DISABLED,
    dw_exchange_reconciliation_wiring: DwExchangeReconciliationWiringConfigV1 | None = None,
    global_authority_ledger: GlobalVenueEffectAuthorityLedgerV1,
    global_claim: GlobalVenueEffectClaimV1,
    risk_reduction_proof: RiskReductionVenueProofV1 | None = None,
) -> OneShotJoinResultV1:
    """Mint, durable-consume, then sign and post through the existing transport.

    Without the exact POST Owner-GO this returns no permit and does not touch
    transport. A passed GO is not marked consumed. The durable kill switch is
    read here (before mint) and again immediately before the socket opens. The
    global authority ledger claim must be unconsumed across all store roots.
    """

    _assert_standing_pins_v1()
    observed = probe if probe is not None else OneShotJoinProbeV1()
    _reject_request_shape_v1(
        retry_allowed=retry_allowed,
        second_submit_allowed=second_submit_allowed,
        max_post_count=max_post_count,
        rerank=rerank,
        reselect=reselect,
        sizing_recompute=sizing_recompute,
        mv2_double_play_reevaluate=mv2_double_play_reevaluate,
    )
    if str(post_owner_go or "") != POST_OWNER_GO:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("POST_GO_REQUIRED")
    if store_root is None:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("DURABLE_STORE_REQUIRED")
    try:
        assert_envelope_unmodified_v1(envelope)
    except FullCoreFinalOrderEnvelopeError as exc:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError(str(exc)) from exc
    try:
        prove_current_productive_one_shot_post_admission_seal_v1(
            envelope=envelope,
            store_root=Path(store_root),
        )
    except OneShotPostAdmissionSealError as exc:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError(str(exc)) from exc
    if envelope.issued_for_exact_action != ISSUED_FOR_EXACT_ACTION:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("ISSUED_FOR_EXACT_ACTION_MISMATCH")
    if not isinstance(global_authority_ledger, GlobalVenueEffectAuthorityLedgerV1):
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("GLOBAL_AUTHORITY_LEDGER_REQUIRED")
    if envelope.reduce_only is True:
        try:
            assert_risk_reduction_proof_valid_for_envelope_v1(
                proof=risk_reduction_proof, envelope=envelope
            )
        except RiskReductionNotProvenError as exc:
            raise CurrentProductiveOneShotFreshEnvelopeJoinError(str(exc)) from exc
    elif risk_reduction_proof is not None:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError(
            "RISK_REDUCTION_PROOF_ON_NON_REDUCE_ONLY_ENVELOPE"
        )
    kill_switch_evidence = read_post_path_kill_switch_evidence_v1()
    kill_switch_admission = evaluate_post_path_kill_switch_v1(
        evidence=kill_switch_evidence,
        envelope=envelope,
        risk_reduction_proof=risk_reduction_proof,
    )
    if not kill_switch_admission.admitted:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError(
            "KILL_SWITCH_GATE_DENIED:" + ",".join(kill_switch_admission.reason_codes)
        )
    observed.events.append("KILL_SWITCH_ADMITTED_PRE_MINT")
    try:
        permit = issue_external_effect_permit_v1(
            envelope,
            authority_ref=POST_OWNER_GO,
            kill_switch_evidence=kill_switch_evidence,
            risk_reduction_proof=risk_reduction_proof,
        )
    except FullCoreExternalEffectPermitError as exc:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError(
            f"PERMIT_ISSUANCE_DENIED:{exc}"
        ) from exc
    observed.permit_minted = True
    observed.events.append("PERMIT_MINTED")
    assert_one_shot_join_permit_constraints_v1(permit, envelope)
    admission = evaluate_real_venue_post_admission_v1(
        post_owner_go=post_owner_go,
        one_shot_real_post=True,
        permit=permit,
        store_root=store_root,
    )
    if admission.post_admission_granted is not True:
        codes = ",".join(admission.reason_codes) or admission.admission_status
        raise CurrentProductiveOneShotFreshEnvelopeJoinError(
            f"REAL_VENUE_POST_ADMISSION_DENIED:{codes}"
        )
    observed.events.append("POST_ADMISSION_GRANTED")
    claim = _bind_global_claim_v1(
        ledger=global_authority_ledger,
        claim=global_claim,
        envelope=envelope,
        permit=permit,
        post_owner_go=post_owner_go,
    )
    observed.events.append("GLOBAL_CLAIM_BOUND")
    send_handle = FullCoreSendCredentialHandleV1(
        handle_id="full-core-one-shot-join-send-handle",
        bound=True,
        material_loaded=False,
    )
    transport = _DurableConsumeThenK1HttpTransportV1(
        envelope=envelope,
        store_root=store_root,
        k1_backend=k1_backend,
        opener_factory=opener_factory,
        probe=observed,
        send_handle=send_handle,
        global_ledger=global_authority_ledger,
        global_claim_id=claim.claim_id,
        risk_reduction_proof=risk_reduction_proof,
    )
    try:
        seam = attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope,
            permit=permit,
            store_root=store_root,
            transport=transport,
            handle=send_handle,
        )
    except FullCoreEnvelopeBoundSendSeamError as exc:
        msg = str(exc)
        no_socket = int(observed.http_post_attempts) == 0
        if no_socket and msg.startswith(f"{PRE_SEND_GATE_DENIED_PREFIX}:"):
            try:
                abort_external_effect_durable_consume_before_transport_v1(
                    store_root=store_root,
                    permit_id=permit.permit_id,
                    envelope_id=envelope.envelope_id,
                    envelope_digest=envelope.envelope_digest,
                    outcome=msg,
                )
                observed.events.append("DURABLE_ABORTED_BEFORE_TRANSPORT")
            except Exception as abort_exc:  # noqa: BLE001
                observed.events.append(f"DURABLE_ABORT_NOT_RECORDED:{type(abort_exc).__name__}")
        observed.events.append(
            "GLOBAL_CLAIM_SETTLED:"
            + _settle_global_claim_v1(
                ledger=global_authority_ledger,
                claim_id=claim.claim_id,
                no_socket=no_socket,
                unknown=not no_socket,
                detail=msg,
            )
        )
        raise CurrentProductiveOneShotFreshEnvelopeJoinError(msg) from exc
    observed.events.append(
        "GLOBAL_CLAIM_SETTLED:"
        + _settle_global_claim_v1(
            ledger=global_authority_ledger,
            claim_id=claim.claim_id,
            no_socket=int(observed.http_post_attempts) == 0,
            unknown=seam.unknown_outcome is True,
            detail=str(seam.outcome),
        )
    )
    join_http = 0
    join_phase = ""
    if seam.post_submit_join is not None:
        join_http = int(seam.post_submit_join.http_status)
        join_phase = str(seam.post_submit_join.recon_class or "")
    wiring = run_dw_exchange_reconciliation_wiring_after_post_submit_v1(
        wiring_mode=dw_exchange_reconciliation_wiring_mode,
        wiring_config=dw_exchange_reconciliation_wiring,
        post_submit_join=seam.post_submit_join,
    )
    return OneShotJoinResultV1(
        outcome=str(seam.outcome),
        permit_id=permit.permit_id,
        envelope_id=envelope.envelope_id,
        envelope_digest=envelope.envelope_digest,
        durable_consumed=seam.durable_consumed is True,
        http_post_attempts=int(observed.http_post_attempts),
        external_effect_count=int(observed.external_effect_count),
        unknown_outcome=seam.unknown_outcome is True,
        post_go_status=POST_GO_STATUS,
        step_29q_status=STEP_29Q_PLAN_ONLY,
        http_status=join_http,
        post_outcome_phase=join_phase,
        dw_exchange_reconciliation_wiring_mode=wiring.wiring_mode,
        dw_exchange_reconciliation_invoked=wiring.invoked is True,
        dw_exchange_reconciliation_disposition=wiring.disposition,
        dw_exchange_reconciliation_outcome=wiring.reconciliation_outcome,
        dw_exchange_reconciliation_ghv_forward_join=wiring.ghv_forward_join,
        dw_exchange_reconciliation_ghv_reverse_join=wiring.ghv_reverse_join,
        dw_exchange_reconciliation_error=wiring.error,
    )


def prove_one_shot_join_standing_boundary_v1() -> dict[str, str]:
    _assert_standing_pins_v1()
    return {
        "POST_GO_STATUS": POST_GO_STATUS,
        "POST_GO_CONSUMED": "false",
        "EXTERNAL_EFFECT_AUTHORIZED": "false",
        "POST_ALLOWED": "false",
        "REAL_VENUE_POST_ALLOWED": "false",
        "REAL_KEYCHAIN_ACCESS_AUTHORIZED": "false",
        "REAL_KEYCHAIN_ACCESS_IMPLEMENTED": "false",
        "STEP_29Q_STATUS": STEP_29Q_PLAN_ONLY,
        "EXTERNAL_EFFECT_COUNT": "0",
        "FIRST_REAL_BLOCKER": current_productive_first_real_blocker_v1(),
        "MAX_POSITIONS_EFFECTIVE": str(int(MAX_POSITIONS_EFFECTIVE)),
        "JOIN_SEAM_ID": JOIN_SEAM_ID,
    }
