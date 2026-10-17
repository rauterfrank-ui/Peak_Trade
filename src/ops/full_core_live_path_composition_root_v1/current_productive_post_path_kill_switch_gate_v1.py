"""Typed durable kill-switch gate for the CURRENT productive one-shot venue POST path.

Reuses ``durable_filegate_join_v1.read_durable_filegate_join_evidence_v1`` (typed
MISSING / UNKNOWN_BLOCKED / CONTRADICTORY / TRUSTED_PRESENT) on the single
canonical state path shared with the ``KillSwitch`` writer
(``risk_gate.canonical_kill_switch_state_path``), which never depends on the
process working directory.

Decision semantics (fail-closed):

- ``PEAK_KILL_SWITCH=1`` emergency deny      -> DENY (no state file and no
                                               risk-reduction proof overrides it)
- env path override set                      -> DENY
- evidence not TRUSTED_PRESENT              -> DENY
- state DISABLED (backtest-only enum value) -> DENY
- state ACTIVE written by the canonical writer (schema ``version`` + ``saved_at``)
  AND carrying a verified recovery attestation (HMAC bound to the signed journal
  REQUESTED/COMPLETED pair, last transition in the journal)
                                            -> ALLOW (kill-switch only; every other
                                               POST gate still applies)
- state ACTIVE without the writer schema    -> DENY
- state ACTIVE without verified attestation -> DENY (forged, copied, restored or
                                               superseded ACTIVE files)
- state KILLED / RECOVERING                 -> ALLOW only for a verified, fresh,
                                               envelope-bound risk-reduction proof
- any other combination                     -> DENY

The canonical file (when an explicit ``state_path`` is read instead) and the
CWD-relative legacy file, when they differ from the primary path, are read as
additional deny signals only: they can block, never admit.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Mapping, Optional, Tuple

from src.ops.full_core_live_path_composition_root_v1.current_productive_global_venue_effect_authority_ledger_v1 import (
    GlobalVenueEffectAuthorityLedgerV1,
    GlobalVenueEffectLedgerError,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_risk_reduction_venue_proof_v1 import (
    RiskReductionNotProvenError,
    RiskReductionVenueProofV1,
    assert_risk_reduction_proof_valid_for_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.durable_filegate_join_v1 import (
    read_durable_filegate_join_evidence_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    DurableKillSwitchEvidenceStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.gates.risk_gate import (
    _anchor_kill_switch_path,
    canonical_kill_switch_state_path,
    kill_switch_emergency_env_deny,
    kill_switch_env_override_rejected,
    legacy_cwd_kill_switch_state_paths,
)
from src.risk_layer.kill_switch.recovery_attestation import verify_active_attestation_from_env

CONTRACT_ID = "CURRENT_PRODUCTIVE_POST_PATH_KILL_SWITCH_GATE_V1"
WRITER_SCHEMA_VERSION = "1.0"
_TRUSTED = DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
_STATE_ACTIVE = "ACTIVE"
_STATE_DISABLED = "DISABLED"
_BLOCKING_STATES = frozenset({"KILLED", "RECOVERING"})

DENY_EVIDENCE_NOT_TRUSTED = "KILL_SWITCH_EVIDENCE_NOT_TRUSTED"
DENY_DISABLED_NOT_LIVE_STATE = "KILL_SWITCH_DISABLED_IS_BACKTEST_ONLY"
DENY_BLOCKED = "KILL_SWITCH_BLOCKED"
DENY_BLOCKED_RISK_REDUCTION_NOT_PROVEN = "KILL_SWITCH_BLOCKED_RISK_REDUCTION_NOT_PROVEN"
DENY_INCONSISTENT = "KILL_SWITCH_STATE_INCONSISTENT"
DENY_SECONDARY_SIGNAL = "KILL_SWITCH_SECONDARY_PATH_DENY_SIGNAL"
DENY_EVIDENCE_STALE = "KILL_SWITCH_EVIDENCE_STALE"
DENY_ENV_OVERRIDE_REJECTED = "KILL_SWITCH_ENV_OVERRIDE_REJECTED"
DENY_ACTIVE_NOT_CANONICAL_WRITER = "KILL_SWITCH_ACTIVE_NOT_WRITTEN_BY_CANONICAL_WRITER"
DENY_ACTIVE_ATTESTATION_NOT_VERIFIED = "KILL_SWITCH_ACTIVE_ATTESTATION_NOT_VERIFIED"
DENY_EMERGENCY_ENV = "KILL_SWITCH_EMERGENCY_ENV_DENY"
MAX_KILL_SWITCH_EVIDENCE_AGE_SECONDS = 15.0
MAX_FUTURE_SKEW_SECONDS = 1.0


class PostPathKillSwitchGateError(RuntimeError):
    """Fail-closed: kill-switch evidence does not admit this venue POST."""


class PostPathKillSwitchDecisionV1(str, Enum):
    ALLOW = "ALLOW"
    ALLOW_PROVEN_RISK_REDUCTION_ONLY = "ALLOW_PROVEN_RISK_REDUCTION_ONLY"
    DENY = "DENY"


@dataclass(frozen=True)
class PostPathKillSwitchEvidenceV1:
    evidence_status: str
    state_name: Optional[str]
    blocked: Optional[bool]
    state_path: str
    reason_codes: Tuple[str, ...]
    secondary_deny_paths: Tuple[str, ...]
    read_at_epoch_s: float
    env_override_rejected: bool = False
    writer_schema_state: Optional[str] = None
    writer_saved_at: Optional[str] = None
    contract_id: str = CONTRACT_ID
    emergency_env_deny: bool = True
    active_attestation_verified: bool = False
    active_attestation_reason: Optional[str] = None


@dataclass(frozen=True)
class PostPathKillSwitchAdmissionV1:
    decision: PostPathKillSwitchDecisionV1
    reason_codes: Tuple[str, ...]
    evidence: PostPathKillSwitchEvidenceV1

    @property
    def admitted(self) -> bool:
        return self.decision is not PostPathKillSwitchDecisionV1.DENY


def resolve_post_path_kill_switch_state_path_v1() -> Path:
    """The canonical absolute state path shared with the KillSwitch writer."""
    return Path(canonical_kill_switch_state_path())


def _secondary_candidate_paths_v1(primary: Path) -> tuple[Path, ...]:
    out: list[Path] = []
    for raw in (canonical_kill_switch_state_path(), *legacy_cwd_kill_switch_state_paths()):
        candidate = Path(raw).resolve()
        if candidate != primary and candidate not in out:
            out.append(candidate)
    return tuple(out)


def _read_writer_schema_v1(
    path: Path,
) -> tuple[Optional[str], Optional[str], Optional[dict]]:
    """(state, saved_at, payload) when the file carries the canonical StatePersistence schema."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, None, None
    if not isinstance(payload, dict) or payload.get("version") != WRITER_SCHEMA_VERSION:
        return None, None, None
    saved_at = str(payload.get("saved_at") or "").strip()
    try:
        datetime.fromisoformat(saved_at)
    except ValueError:
        return None, None, None
    return str(payload.get("state") or "").strip().upper() or None, saved_at, payload


def read_post_path_kill_switch_evidence_v1(
    *,
    state_path: Optional[Path | str] = None,
) -> PostPathKillSwitchEvidenceV1:
    primary = (
        _anchor_kill_switch_path(str(state_path))
        if state_path is not None
        else resolve_post_path_kill_switch_state_path_v1()
    )
    writer_state, writer_saved_at, payload = _read_writer_schema_v1(primary)
    attestation_verified = False
    attestation_reason: Optional[str] = None
    if writer_state == _STATE_ACTIVE and payload is not None:
        check = verify_active_attestation_from_env(primary, payload)
        attestation_verified = check.verified is True
        attestation_reason = check.reason
    joined = read_durable_filegate_join_evidence_v1(state_path=str(primary))
    secondary_deny: list[str] = []
    for candidate in _secondary_candidate_paths_v1(primary):
        if not candidate.is_file():
            continue
        other = read_durable_filegate_join_evidence_v1(state_path=str(candidate))
        if other.evidence_status != _TRUSTED or other.blocked is not False:
            secondary_deny.append(str(candidate))
    return PostPathKillSwitchEvidenceV1(
        evidence_status=str(joined.evidence_status),
        state_name=joined.state_name,
        blocked=joined.blocked,
        state_path=str(primary),
        reason_codes=tuple(joined.reason_codes),
        secondary_deny_paths=tuple(secondary_deny),
        read_at_epoch_s=time.time(),
        env_override_rejected=kill_switch_env_override_rejected(),
        writer_schema_state=writer_state,
        writer_saved_at=writer_saved_at,
        emergency_env_deny=kill_switch_emergency_env_deny(),
        active_attestation_verified=attestation_verified,
        active_attestation_reason=attestation_reason,
    )


def evaluate_post_path_kill_switch_v1(
    *,
    evidence: PostPathKillSwitchEvidenceV1,
    envelope: FinalOrderEnvelopeV1,
    risk_reduction_proof: Optional[RiskReductionVenueProofV1],
    now_epoch_s: Optional[float] = None,
) -> PostPathKillSwitchAdmissionV1:
    if not isinstance(evidence, PostPathKillSwitchEvidenceV1):
        raise PostPathKillSwitchGateError("KILL_SWITCH_EVIDENCE_TYPE_REQUIRED")
    assert_envelope_unmodified_v1(envelope)

    def _deny(*codes: str) -> PostPathKillSwitchAdmissionV1:
        return PostPathKillSwitchAdmissionV1(
            decision=PostPathKillSwitchDecisionV1.DENY,
            reason_codes=tuple(dict.fromkeys(codes)),
            evidence=evidence,
        )

    if evidence.contract_id != CONTRACT_ID:
        return _deny(f"{DENY_EVIDENCE_NOT_TRUSTED}:CONTRACT_MISMATCH")
    if evidence.emergency_env_deny is not False or kill_switch_emergency_env_deny():
        return _deny(DENY_EMERGENCY_ENV)
    if evidence.env_override_rejected is not False:
        return _deny(DENY_ENV_OVERRIDE_REJECTED)
    if evidence.evidence_status != _TRUSTED:
        return _deny(f"{DENY_EVIDENCE_NOT_TRUSTED}:{evidence.evidence_status or 'EMPTY'}")
    now = float(time.time() if now_epoch_s is None else now_epoch_s)
    age = now - float(evidence.read_at_epoch_s)
    if age < -MAX_FUTURE_SKEW_SECONDS or age > MAX_KILL_SWITCH_EVIDENCE_AGE_SECONDS:
        return _deny(DENY_EVIDENCE_STALE)
    if evidence.secondary_deny_paths:
        return _deny(DENY_SECONDARY_SIGNAL)
    state = str(evidence.state_name or "").upper()
    if state == _STATE_DISABLED:
        return _deny(DENY_DISABLED_NOT_LIVE_STATE)
    if state == _STATE_ACTIVE and evidence.blocked is False:
        if evidence.writer_schema_state != _STATE_ACTIVE or not evidence.writer_saved_at:
            return _deny(DENY_ACTIVE_NOT_CANONICAL_WRITER)
        if evidence.active_attestation_verified is not True:
            return _deny(
                DENY_ACTIVE_ATTESTATION_NOT_VERIFIED,
                str(evidence.active_attestation_reason or "ACTIVE_ATTESTATION_ABSENT"),
            )
        return PostPathKillSwitchAdmissionV1(
            decision=PostPathKillSwitchDecisionV1.ALLOW,
            reason_codes=("KILL_SWITCH_ACTIVE_TRUSTED",),
            evidence=evidence,
        )
    if state in _BLOCKING_STATES and evidence.blocked is True:
        if risk_reduction_proof is None:
            return _deny(DENY_BLOCKED)
        try:
            assert_risk_reduction_proof_valid_for_envelope_v1(
                proof=risk_reduction_proof,
                envelope=envelope,
                now_epoch_s=now_epoch_s,
            )
        except RiskReductionNotProvenError as exc:
            return _deny(DENY_BLOCKED_RISK_REDUCTION_NOT_PROVEN, str(exc))
        return PostPathKillSwitchAdmissionV1(
            decision=PostPathKillSwitchDecisionV1.ALLOW_PROVEN_RISK_REDUCTION_ONLY,
            reason_codes=(f"KILL_SWITCH_{state}_PROVEN_RISK_REDUCTION_EXCEPTION",),
            evidence=evidence,
        )
    return _deny(DENY_INCONSISTENT)


def assert_post_path_kill_switch_admits_v1(
    *,
    envelope: FinalOrderEnvelopeV1,
    risk_reduction_proof: Optional[RiskReductionVenueProofV1],
    state_path: Optional[Path | str] = None,
) -> PostPathKillSwitchAdmissionV1:
    """Fresh durable read plus decision. Raises on DENY."""
    evidence = read_post_path_kill_switch_evidence_v1(state_path=state_path)
    admission = evaluate_post_path_kill_switch_v1(
        evidence=evidence,
        envelope=envelope,
        risk_reduction_proof=risk_reduction_proof,
    )
    if not admission.admitted:
        raise PostPathKillSwitchGateError(",".join(admission.reason_codes))
    return admission


class PreSendSafetyGateV1:
    """Last check before the venue socket opens (second kill-switch read).

    Re-verifies, immediately before ``opener.open``: the global authority claim is
    SENT_INITIATED for exactly this permit/envelope, the durable kill-switch state
    read fresh from disk admits the effect, and a risk-reduction proof (when the
    envelope is reduce-only) is still fresh. Any failure means no POST.

    Residual window: a kill-switch flip after this check and before the venue
    processes the request cannot be prevented client-side.
    """

    def __init__(
        self,
        *,
        envelope: FinalOrderEnvelopeV1,
        permit_id: str,
        global_ledger: GlobalVenueEffectAuthorityLedgerV1,
        global_claim_id: str,
        risk_reduction_proof: Optional[RiskReductionVenueProofV1],
    ) -> None:
        if not isinstance(global_ledger, GlobalVenueEffectAuthorityLedgerV1):
            raise PostPathKillSwitchGateError("PRE_SEND_GLOBAL_LEDGER_REQUIRED")
        if not str(global_claim_id or "").strip() or not str(permit_id or "").strip():
            raise PostPathKillSwitchGateError("PRE_SEND_BINDING_REQUIRED")
        self._envelope = envelope
        self._permit_id = str(permit_id)
        self._ledger = global_ledger
        self._claim_id = str(global_claim_id)
        self._proof = risk_reduction_proof
        self.checks_performed = 0
        self.last_admission: Optional[PostPathKillSwitchAdmissionV1] = None

    def assert_admits_send_v1(self, *, payload: Mapping[str, object]) -> None:
        self.checks_performed += 1
        assert_envelope_unmodified_v1(self._envelope)
        if str(payload.get("clOrdId") or "") != str(self._envelope.client_order_id):
            raise PostPathKillSwitchGateError("PRE_SEND_CLORDID_MISMATCH")
        try:
            self._ledger.assert_sent_initiated_for_transport_v1(
                self._claim_id,
                permit_id=self._permit_id,
                envelope_digest=self._envelope.envelope_digest,
            )
        except GlobalVenueEffectLedgerError as exc:
            raise PostPathKillSwitchGateError(str(exc)) from exc
        if self._envelope.reduce_only is True:
            try:
                assert_risk_reduction_proof_valid_for_envelope_v1(
                    proof=self._proof, envelope=self._envelope
                )
            except RiskReductionNotProvenError as exc:
                raise PostPathKillSwitchGateError(str(exc)) from exc
        self.last_admission = assert_post_path_kill_switch_admits_v1(
            envelope=self._envelope,
            risk_reduction_proof=self._proof,
        )


__all__ = [
    "CONTRACT_ID",
    "PreSendSafetyGateV1",
    "DENY_BLOCKED",
    "DENY_BLOCKED_RISK_REDUCTION_NOT_PROVEN",
    "DENY_ACTIVE_ATTESTATION_NOT_VERIFIED",
    "DENY_ACTIVE_NOT_CANONICAL_WRITER",
    "DENY_EMERGENCY_ENV",
    "DENY_DISABLED_NOT_LIVE_STATE",
    "DENY_ENV_OVERRIDE_REJECTED",
    "DENY_EVIDENCE_NOT_TRUSTED",
    "DENY_EVIDENCE_STALE",
    "DENY_INCONSISTENT",
    "MAX_KILL_SWITCH_EVIDENCE_AGE_SECONDS",
    "DENY_SECONDARY_SIGNAL",
    "PostPathKillSwitchAdmissionV1",
    "PostPathKillSwitchDecisionV1",
    "PostPathKillSwitchEvidenceV1",
    "PostPathKillSwitchGateError",
    "assert_post_path_kill_switch_admits_v1",
    "evaluate_post_path_kill_switch_v1",
    "read_post_path_kill_switch_evidence_v1",
    "resolve_post_path_kill_switch_state_path_v1",
]
