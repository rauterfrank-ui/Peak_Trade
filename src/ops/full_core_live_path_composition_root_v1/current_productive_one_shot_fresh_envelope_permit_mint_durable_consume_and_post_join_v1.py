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
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
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
    ) -> None:
        self._envelope = envelope
        self._store_root = store_root
        self._k1_backend = k1_backend
        self._opener_factory = opener_factory
        self._probe = probe
        self._send_handle = send_handle

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
) -> OneShotJoinResultV1:
    """Mint, durable-consume, then sign and post through the existing transport.

    Without the exact POST Owner-GO this returns no permit and does not touch
    transport. A passed GO is not marked consumed.
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
    if envelope.issued_for_exact_action != ISSUED_FOR_EXACT_ACTION:
        raise CurrentProductiveOneShotFreshEnvelopeJoinError("ISSUED_FOR_EXACT_ACTION_MISMATCH")
    permit = issue_external_effect_permit_v1(envelope, authority_ref=POST_OWNER_GO)
    observed.permit_minted = True
    observed.events.append("PERMIT_MINTED")
    assert_one_shot_join_permit_constraints_v1(permit, envelope)
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
        raise CurrentProductiveOneShotFreshEnvelopeJoinError(str(exc)) from exc
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
