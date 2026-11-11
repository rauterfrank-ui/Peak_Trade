"""Bounded Execution GHOSV incident handoff to the original Safety owner.

Only an explicitly isolated, offline reconciliation profile can use this entry
point. The journal records incident acceptance. FILEGATE remains the authority
for the POST veto and is independently read by the reaction observer.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    atomic_write_json,
    canonical_json_dumps,
)
from src.ops.execution_ghosv_fill_quantity_v1 import (
    ExecutionFillQuantityIncidentV1,
    build_offline_execution_fill_quantity_incident_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_safety_veto_v1 import (
    CurrentPostSafetyContextV1,
    CurrentPostSafetyVetoError,
)
from src.ops.full_core_live_path_composition_root_v1.durable_filegate_join_v1 import (
    read_durable_filegate_join_evidence_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    SIMULATION_OFFLINE,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    RECONCILIATION_PROVIDER_OFFLINE_STUB,
    FullCoreExchangeReconciliationIdentityV1,
    FullCoreExchangeReconciliationSnapshotV1,
    LocalSubmitOutcome,
    PortfolioExecutionReconciliationIdentityV2,
    adjudicate_full_core_exchange_reconciliation_v1,
)
from src.ops.gates.risk_gate import kill_switch_state_path_from_env
from src.risk_layer.kill_switch.core import KillSwitch
from src.risk_layer.kill_switch.persistence import StatePersistence

_SCHEMA = "offline_execution_incident_safety.v1"
_APPLIED = "KILL_PERSISTED"
_ALREADY_BLOCKED = "ALREADY_BLOCKED"
_ENVIRONMENT = "SHADOW"
_VETO_STAGE = "INCIDENT_REACTION_READBACK"
_INCIDENT_REASON_PREFIX = "EXECUTION_GHOSV:"


class ExecutionIncidentSafetyError(ValueError):
    pass


class ExecutionIncidentObservationError(ExecutionIncidentSafetyError):
    """The reader could not bind one observation to a consistent state."""


def _digest(value):
    return hashlib.sha256(canonical_json_dumps(value).encode("utf-8")).hexdigest()


def _aware(value):
    if type(value) is not datetime or value.utcoffset() is None:
        raise ExecutionIncidentSafetyError("INCIDENT_AWARE_CLOCK_REQUIRED")
    return value


@dataclass(frozen=True)
class OfflineExecutionIncidentScopeV1:
    root: Path
    account: str
    session_id: str
    started_at: datetime

    def __post_init__(self):
        if (
            not self.root.is_absolute()
            or self.root.resolve() != self.root
            or not self.root.is_dir()
        ):
            raise ExecutionIncidentSafetyError("INCIDENT_CANONICAL_ISOLATED_ROOT_REQUIRED")
        if any(
            type(x) is not str or not x or x.strip() != x for x in (self.account, self.session_id)
        ):
            raise ExecutionIncidentSafetyError("INCIDENT_EXACT_SCOPE_REQUIRED")
        _aware(self.started_at)

    @property
    def state_path(self):
        return self.root / "execution-incident-filegate.json"

    @property
    def journal_path(self):
        return self.root / "execution-incident-receipts.json"

    def binding(self):
        return {
            "root": str(self.root),
            "account": self.account,
            "session_id": self.session_id,
            "environment": _ENVIRONMENT,
            "started_at": self.started_at.isoformat(),
        }


@dataclass(frozen=True)
class OfflineExecutionIncidentDeliveryV1:
    """Explicit request for an offline reconciliation cycle to deliver its incident."""

    scope: OfflineExecutionIncidentScopeV1
    observed_at: datetime
    evaluated_at: datetime

    def __post_init__(self):
        if type(self.scope) is not OfflineExecutionIncidentScopeV1:
            raise ExecutionIncidentSafetyError("INCIDENT_EXACT_SCOPE_REQUIRED")
        if not self.scope.started_at <= _aware(self.observed_at) <= _aware(self.evaluated_at):
            raise ExecutionIncidentSafetyError("INCIDENT_OBSERVATION_OUTSIDE_SESSION")


def _require_isolated_scope(scope):
    if (
        type(scope) is not OfflineExecutionIncidentScopeV1
        or kill_switch_state_path_from_env() != str(scope.state_path)
        or scope.root.resolve() != scope.root
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_FILEGATE_SCOPE_MISMATCH")
    protected_paths = (
        scope.state_path,
        scope.state_path.with_suffix(".tmp"),
        scope.journal_path,
        scope.journal_path.with_suffix(".json.tmp"),
        scope.root / "execution-incident.lock",
        scope.root / "backups",
    )
    if any(path.is_symlink() for path in protected_paths):
        raise ExecutionIncidentSafetyError("INCIDENT_FOREIGN_STORE_PATH")


def _read_journal(scope):
    binding = {"schema": _SCHEMA, "scope": scope.binding()}
    try:
        contents = scope.journal_path.read_text()
    except FileNotFoundError:
        return {**binding, "receipts": {}}
    try:
        journal = json.loads(contents)
        receipts = journal["receipts"]
        if (
            set(journal) != {*binding, "receipts"}
            or any(journal[k] != v for k, v in binding.items())
            or not isinstance(receipts, dict)
        ):
            raise ValueError("foreign journal")
        for incident_id, entry in receipts.items():
            body = entry["receipt"]
            if (
                body["incident_id"] != incident_id
                or body["disposition"] not in {_APPLIED, _ALREADY_BLOCKED}
                or _digest(body) != entry["sha256"]
            ):
                raise ValueError("invalid receipt")
            _aware(datetime.fromisoformat(body["observed_at"]))
        return journal
    except (KeyError, ValueError, TypeError) as exc:
        raise ExecutionIncidentSafetyError("INCIDENT_JOURNAL_UNPROVEN") from exc


def _state_observation(scope):
    path = scope.state_path

    def read():
        try:
            return path.read_bytes()
        except FileNotFoundError:
            return None

    before = read()
    evidence = read_durable_filegate_join_evidence_v1(state_path=str(path))
    if read() != before:
        raise ExecutionIncidentObservationError("INCIDENT_FILEGATE_CHANGED_DURING_READ")
    if evidence.evidence_status != "TRUSTED_PRESENT":
        return evidence, {}
    try:
        payload = json.loads(before or b"{}")
        if type(payload) is not dict or payload.get("state") != evidence.state_name:
            raise ValueError("state mismatch")
    except (TypeError, ValueError) as exc:
        raise ExecutionIncidentObservationError("INCIDENT_FILEGATE_UNPROVEN") from exc
    return evidence, payload


def _kill_revision(payload):
    if payload.get("state") != "KILLED" or not payload.get("killed_at"):
        return None
    return _digest(
        {"killed_at": payload["killed_at"], "trigger_reason": payload.get("trigger_reason")}
    )


def accept_offline_execution_incident_v1(
    *,
    scope: OfflineExecutionIncidentScopeV1,
    session_id: str,
    identity: FullCoreExchangeReconciliationIdentityV1 | PortfolioExecutionReconciliationIdentityV2,
    snapshot: FullCoreExchangeReconciliationSnapshotV1,
    local_submit_outcome: LocalSubmitOutcome,
    observed_at: datetime,
    evaluated_at: datetime,
    source_incident: ExecutionFillQuantityIncidentV1 | None,
) -> dict | None:
    """Validate the producer's incident against its original evidence before writing."""
    _require_isolated_scope(scope)
    if (
        type(identity)
        not in (
            FullCoreExchangeReconciliationIdentityV1,
            PortfolioExecutionReconciliationIdentityV2,
        )
        or session_id != scope.session_id
        or identity.account_identity != scope.account
        or identity.execution_environment != _ENVIRONMENT
        or type(snapshot) is not FullCoreExchangeReconciliationSnapshotV1
        or snapshot.simulation_mode != SIMULATION_OFFLINE
        or snapshot.provider != RECONCILIATION_PROVIDER_OFFLINE_STUB
        or type(local_submit_outcome) is not LocalSubmitOutcome
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_FOREIGN_OR_NON_OFFLINE_EVIDENCE")
    if not all(
        type(value) is str and value and value == value.strip()
        for value in (
            identity.instrument_id,
            identity.clordid,
            identity.submit_attempt_id,
            identity.envelope_identity,
            identity.envelope_digest,
        )
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_ORIGINAL_IDENTITY_INCOMPLETE")
    if not scope.started_at <= _aware(observed_at) <= _aware(evaluated_at):
        raise ExecutionIncidentSafetyError("INCIDENT_OBSERVATION_OUTSIDE_SESSION")
    decision = adjudicate_full_core_exchange_reconciliation_v1(
        identity=identity, snapshot=snapshot, local_submit_outcome=local_submit_outcome
    )
    expected = build_offline_execution_fill_quantity_incident_v1(
        session_id=session_id,
        observed_at=observed_at,
        identity=identity,
        snapshot=snapshot,
        decision=decision,
        local_submit_outcome=local_submit_outcome,
    )
    if type(source_incident) is not type(expected) or source_incident != expected:
        raise ExecutionIncidentSafetyError("INCIDENT_SOURCE_EVIDENCE_MISMATCH")
    if expected is None:
        return None
    return _apply_confirmed_execution_incident_v1(scope=scope, identity=identity, expected=expected)


def _apply_confirmed_execution_incident_v1(
    *, scope, identity, expected: ExecutionFillQuantityIncidentV1, reconciliation_source=None
) -> dict:
    _require_isolated_scope(scope)
    if (
        identity.execution_environment != _ENVIRONMENT
        or identity.account_identity != scope.account
        or expected.session_id != scope.session_id
        or expected.identity_digest != identity.identity_digest()
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_FILEGATE_SOURCE_SCOPE_MISMATCH")
    observed_at = expected.observed_at
    original = {
        "identity_digest": expected.identity_digest,
        "envelope_id": identity.envelope_identity,
        "envelope_digest": identity.envelope_digest,
        "evidence_sha256": expected.snapshot_sha256,
        "incident_type": expected.incident_type,
        "reconciliation_reason": expected.reconciliation_reason,
    }
    if reconciliation_source is not None:
        original["reconciliation_source"] = reconciliation_source
    incident_id = _digest({"scope": scope.binding(), **original})
    reason = _INCIDENT_REASON_PREFIX + incident_id

    with (scope.root / "execution-incident.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        _require_isolated_scope(scope)
        journal = _read_journal(scope)
        entries = journal["receipts"]
        if incident_id in entries:
            return entries[incident_id]["receipt"]
        if any(
            datetime.fromisoformat(e["receipt"]["observed_at"]) >= observed_at
            for e in entries.values()
        ):
            raise ExecutionIncidentSafetyError("INCIDENT_STALE_OR_AMBIGUOUS_ORDER")
        evidence, payload = _state_observation(scope)
        if evidence.evidence_status != "TRUSTED_PRESENT" or evidence.state_name == "DISABLED":
            raise ExecutionIncidentSafetyError("INCIDENT_FILEGATE_UNPROVEN")
        if evidence.state_name != "KILLED":
            writer = KillSwitch({}, persistence=StatePersistence(str(scope.state_path)))
            if writer.state.name != evidence.state_name:
                raise ExecutionIncidentSafetyError("INCIDENT_FILEGATE_CHANGED_BEFORE_WRITE")
            if not writer.trigger(reason, triggered_by="execution_ghosv"):
                raise ExecutionIncidentSafetyError("INCIDENT_KILL_REFUSED")
            evidence, payload = _state_observation(scope)
            if evidence.state_name != "KILLED" or payload.get("trigger_reason") != reason:
                raise ExecutionIncidentSafetyError("INCIDENT_KILL_READBACK_UNPROVEN")
        revision = _kill_revision(payload)
        disposition = (
            _APPLIED if revision and payload.get("trigger_reason") == reason else _ALREADY_BLOCKED
        )
        receipt = {
            **original,
            "incident_id": incident_id,
            "observed_at": observed_at.isoformat(),
            "source_check_id": expected.check_id,
            "source_traffic": expected.traffic,
            "source_outcome": expected.outcome,
            "local_submit_outcome": expected.local_submit_outcome.value,
            "venue_order_id": expected.venue_order_id,
            "evidence_refs": list(expected.evidence_refs),
            "disposition": disposition,
            "kill_revision": revision,
        }
        entries[incident_id] = {"receipt": receipt, "sha256": _digest(receipt)}
        atomic_write_json(path=scope.journal_path, payload=journal)
        if _read_journal(scope) != journal:
            raise ExecutionIncidentSafetyError("INCIDENT_RECEIPT_READBACK_UNPROVEN")
        return receipt


def observe_offline_execution_incident_v1(
    *,
    scope: OfflineExecutionIncidentScopeV1,
    envelope: FinalOrderEnvelopeV1,
    incident_id: str | None = None,
) -> dict:
    """Read the current FILEGATE and discover its incident when no ID is supplied."""
    _require_isolated_scope(scope)
    evidence, payload = _state_observation(scope)
    veto_reason = None
    try:
        CurrentPostSafetyContextV1(envelope, str(scope.state_path)).inspect_v1(stage=_VETO_STAGE)
    except CurrentPostSafetyVetoError as exc:
        veto_reason = str(exc)

    requested_id = incident_id
    reason = payload.get("trigger_reason")
    if (
        incident_id is None
        and isinstance(reason, str)
        and reason.startswith(_INCIDENT_REASON_PREFIX)
    ):
        found = reason.removeprefix(_INCIDENT_REASON_PREFIX)
        if re.fullmatch(r"[0-9a-f]{64}", found):
            incident_id = found
    receipt = None
    receipt_error = None
    if incident_id is not None:
        try:
            entry = _read_journal(scope)["receipts"].get(incident_id)
        except (ExecutionIncidentSafetyError, OSError):
            receipt_error = "INCIDENT_JOURNAL_UNPROVEN"
        else:
            if entry is None:
                receipt_error = "INCIDENT_RECEIPT_MISSING"
            else:
                receipt = entry["receipt"]
                if (
                    receipt["envelope_id"] != envelope.envelope_id
                    or receipt["envelope_digest"] != envelope.envelope_digest
                ):
                    receipt_error = "INCIDENT_REACTION_ENVELOPE_MISMATCH"
                    if requested_id is not None:
                        raise ExecutionIncidentSafetyError(receipt_error)
                    receipt = None

    if _state_observation(scope) != (evidence, payload):
        raise ExecutionIncidentObservationError("INCIDENT_FILEGATE_CHANGED_DURING_VETO")
    _require_isolated_scope(scope)
    revision = _kill_revision(payload)
    return {
        "incident_id": incident_id,
        "acceptance": None if receipt is None else receipt["disposition"],
        "evidence_status": evidence.evidence_status,
        "state_name": evidence.state_name,
        "kill_revision": revision,
        "post_safety_veto": veto_reason,
        "incident_evidence_error": receipt_error,
        "correlated_incident_veto": bool(
            receipt
            and receipt["disposition"] == _APPLIED
            and revision is not None
            and receipt["kill_revision"] == revision
            and veto_reason == f"POST_SAFETY_DURABLE_VETO:{_VETO_STAGE}:TRUSTED_PRESENT:KILLED"
        ),
    }
