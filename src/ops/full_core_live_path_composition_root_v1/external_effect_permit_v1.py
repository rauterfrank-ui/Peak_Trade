"""Envelope-bound single-use Full-Core external-effect permit. Offline. No POST.

Standing EXTERNAL_EFFECT_AUTHORIZED remains false. This permit is a narrow
object bound to one envelope digest. It is not STEP-29Q eligibility and not a
standing send unlock. SUBMIT_UNLOCKED alone is not permission to send.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    SUBMISSION_AUTHORIZED,
    SUBMIT_UNLOCKED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    DurableKillSwitchEvidenceStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    ISSUED_FOR_EXACT_ACTION,
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)

PERMIT_SCHEMA_VERSION = "full_core_external_effect_permit.v1"
MAX_POST_COUNT = 1
ONE_SHOT_REAL_POST_AUTHORITY_REFS: frozenset[str] = frozenset(
    {
        "OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1",
    }
)
_SECRET_TOKENS = ("secret", "passphrase", "api_key", "apikey", "private_key")
_UNKNOWN_KS = frozenset(
    {
        DurableKillSwitchEvidenceStatusV1.UNKNOWN_BLOCKED.value,
        DurableKillSwitchEvidenceStatusV1.MISSING.value,
        DurableKillSwitchEvidenceStatusV1.CONTRADICTORY.value,
        "",
        "UNKNOWN",
        "MALFORMED",
    }
)


class FullCoreExternalEffectPermitError(RuntimeError):
    """Fail-closed envelope-bound permit violation."""


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _assert_no_secrets(payload: Mapping[str, Any]) -> None:
    blob = _canonical_json(payload).lower()
    for token in _SECRET_TOKENS:
        if token in blob:
            raise FullCoreExternalEffectPermitError(f"SECRET_TOKEN_PRESENT:{token}")


@dataclass(frozen=True)
class ExternalEffectPermitV1:
    permit_id: str
    envelope_id: str
    envelope_digest: str
    authority_ref: str
    issued_for_exact_action: str
    single_use: bool = True
    max_post_count: int = MAX_POST_COUNT
    retry_allowed: bool = False
    second_submit_allowed: bool = False
    standing_external_effect_authorized: bool = False
    step_29q_status: str = STEP_29Q_PLAN_ONLY
    schema_version: str = PERMIT_SCHEMA_VERSION

    def to_canonical_payload_v1(self) -> dict[str, Any]:
        return {
            "authority_ref": self.authority_ref,
            "envelope_digest": self.envelope_digest,
            "envelope_id": self.envelope_id,
            "issued_for_exact_action": self.issued_for_exact_action,
            "max_post_count": int(self.max_post_count),
            "retry_allowed": self.retry_allowed is True,
            "schema_version": self.schema_version,
            "second_submit_allowed": self.second_submit_allowed is True,
            "single_use": self.single_use is True,
            "standing_external_effect_authorized": (
                self.standing_external_effect_authorized is True
            ),
            "step_29q_status": self.step_29q_status,
        }


def _permit_id_from_payload_v1(payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"eep-{digest[:32]}"


def issue_external_effect_permit_v1(
    envelope: FinalOrderEnvelopeV1,
    *,
    authority_ref: str,
    kill_switch_blocked: bool = False,
    durable_kill_switch_evidence_status: str = (
        DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
    ),
    filegate_denied: bool = False,
    step_29q_status: str = STEP_29Q_PLAN_ONLY,
    submission_authorized: Optional[bool] = None,
    live_authorized: Optional[bool] = None,
    live_armed: Optional[bool] = None,
    wire_send_permitted: Optional[bool] = None,
    productive_wire_send_reachable: Optional[bool] = None,
) -> ExternalEffectPermitV1:
    assert_envelope_unmodified_v1(envelope)
    reasons: list[str] = []
    submitted = (
        SUBMISSION_AUTHORIZED is True if submission_authorized is None else submission_authorized
    )
    authorized = LIVE_AUTHORIZED is True if live_authorized is None else live_authorized
    armed = LIVE_ARMED is True if live_armed is None else live_armed
    send = WIRE_SEND_PERMITTED is True if wire_send_permitted is None else wire_send_permitted
    reachable = (
        PRODUCTIVE_WIRE_SEND_REACHABLE is True
        if productive_wire_send_reachable is None
        else productive_wire_send_reachable
    )
    if submitted is not True:
        reasons.append("SUBMISSION_AUTHORIZED_FALSE")
    if authorized is not True:
        reasons.append("LIVE_AUTHORIZED_FALSE")
    if armed is not True:
        reasons.append("LIVE_ARMED_FALSE")
    if send is not True:
        reasons.append("WIRE_SEND_NOT_PERMITTED")
    if reachable is not True:
        reasons.append("PRODUCTIVE_WIRE_SEND_NOT_REACHABLE")
    if kill_switch_blocked is True:
        reasons.append("KILL_SWITCH_BLOCKED")
    elif kill_switch_blocked is None:
        reasons.append("KILL_SWITCH_UNKNOWN")
    ks_status = str(durable_kill_switch_evidence_status or "").strip()
    trusted = DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
    if ks_status in _UNKNOWN_KS or ks_status != trusted:
        reasons.append("KILL_SWITCH_EVIDENCE_NOT_TRUSTED")
    if filegate_denied is True:
        reasons.append("FILEGATE_DENY")
    if str(step_29q_status or "") != STEP_29Q_PLAN_ONLY:
        reasons.append("STEP_29Q_MUST_REMAIN_PLAN_ONLY")
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        reasons.append("STANDING_EXTERNAL_EFFECT_MUST_REMAIN_FALSE")
    if SUBMIT_UNLOCKED is True:
        reasons.append("SUBMIT_UNLOCKED_STANDING_TRUE_FORBIDDEN")
    authority = str(authority_ref or "").strip()
    if not authority or authority != str(authority_ref):
        reasons.append("AUTHORITY_REF_MISSING")
    if reasons:
        raise FullCoreExternalEffectPermitError(",".join(dict.fromkeys(reasons)))
    payload = {
        "authority_ref": authority,
        "envelope_digest": envelope.envelope_digest,
        "envelope_id": envelope.envelope_id,
        "issued_for_exact_action": ISSUED_FOR_EXACT_ACTION,
        "max_post_count": MAX_POST_COUNT,
        "retry_allowed": False,
        "schema_version": PERMIT_SCHEMA_VERSION,
        "second_submit_allowed": False,
        "single_use": True,
        "standing_external_effect_authorized": False,
        "step_29q_status": STEP_29Q_PLAN_ONLY,
    }
    _assert_no_secrets(payload)
    permit = ExternalEffectPermitV1(
        permit_id=_permit_id_from_payload_v1(payload),
        envelope_id=envelope.envelope_id,
        envelope_digest=envelope.envelope_digest,
        authority_ref=authority,
        issued_for_exact_action=ISSUED_FOR_EXACT_ACTION,
        single_use=True,
        max_post_count=MAX_POST_COUNT,
        retry_allowed=False,
        second_submit_allowed=False,
        standing_external_effect_authorized=False,
        step_29q_status=STEP_29Q_PLAN_ONLY,
    )
    if _permit_id_from_payload_v1(permit.to_canonical_payload_v1()) != permit.permit_id:
        raise FullCoreExternalEffectPermitError("PERMIT_ID_DRIFT")
    return permit


def permit_authorizes_one_shot_real_post_v1(permit: ExternalEffectPermitV1) -> bool:
    """True only for a later actual-POST Owner-GO. This readiness GO is excluded."""
    if permit is None or not isinstance(permit, ExternalEffectPermitV1):
        return False
    if permit.single_use is not True:
        return False
    if int(permit.max_post_count) != MAX_POST_COUNT:
        return False
    if permit.retry_allowed is True or permit.second_submit_allowed is True:
        return False
    if permit.standing_external_effect_authorized is True:
        return False
    return str(permit.authority_ref or "") in ONE_SHOT_REAL_POST_AUTHORITY_REFS


def assert_permit_matches_envelope_v1(
    permit: ExternalEffectPermitV1,
    envelope: FinalOrderEnvelopeV1,
) -> None:
    if permit is None or not isinstance(permit, ExternalEffectPermitV1):
        raise FullCoreExternalEffectPermitError("PERMIT_MISSING")
    assert_envelope_unmodified_v1(envelope)
    if permit.envelope_id != envelope.envelope_id:
        raise FullCoreExternalEffectPermitError("WRONG_ENVELOPE")
    if permit.envelope_digest != envelope.envelope_digest:
        raise FullCoreExternalEffectPermitError("DIGEST_MISMATCH")
    if permit.single_use is not True:
        raise FullCoreExternalEffectPermitError("SINGLE_USE_REQUIRED")
    if int(permit.max_post_count) != MAX_POST_COUNT:
        raise FullCoreExternalEffectPermitError("MAX_POST_COUNT_NOT_ONE")
    if permit.retry_allowed is True:
        raise FullCoreExternalEffectPermitError("RETRY_ALLOWED_FORBIDDEN")
    if permit.second_submit_allowed is True:
        raise FullCoreExternalEffectPermitError("SECOND_SUBMIT_FORBIDDEN")
    if permit.standing_external_effect_authorized is True:
        raise FullCoreExternalEffectPermitError("STANDING_EXTERNAL_EFFECT_MUST_REMAIN_FALSE")
    if permit.issued_for_exact_action != ISSUED_FOR_EXACT_ACTION:
        raise FullCoreExternalEffectPermitError("ISSUED_FOR_EXACT_ACTION_MISMATCH")
    if permit.step_29q_status != STEP_29Q_PLAN_ONLY:
        raise FullCoreExternalEffectPermitError("STEP_29Q_MUST_REMAIN_PLAN_ONLY")
    if _permit_id_from_payload_v1(permit.to_canonical_payload_v1()) != permit.permit_id:
        raise FullCoreExternalEffectPermitError("WRONG_PERMIT")
