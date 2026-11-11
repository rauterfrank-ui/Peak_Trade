"""Bound Execution GHOSV incident acceptance and FILEGATE reaction readback."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import sqlite3
import stat
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
    FullCoreFinalOrderEnvelopeError,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    SIMULATION_OFFLINE,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    RECONCILIATION_PROVIDER_OFFLINE_STUB,
    OUTCOME_HALTED_UNRESOLVED,
    REASON_FILL_EXCEEDS_ORDER,
    REASON_NEGATIVE_REMAINING,
    FullCoreExchangeReconciliationIdentityV1,
    FullCoreExchangeReconciliationSnapshotV1,
    LocalSubmitOutcome,
    PortfolioExecutionReconciliationIdentityV2,
    adjudicate_full_core_exchange_reconciliation_v1,
    parse_exchange_reconciliation_identity_v1,
)
from src.ops.gates.risk_gate import (
    canonical_kill_switch_state_path,
    kill_switch_state_path_from_env,
)
from src.ops.managed_filegate_v1 import configured_filegate_writer_v1
from src.risk_layer.kill_switch.core import KillSwitch
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
    read_budget_revision_read_only_v1,
)

_SCHEMA = "offline_execution_incident_safety.v1"
_AUTHENTICATED_SCHEMA = "authenticated_execution_incident_safety.v1"
_APPLIED = "KILL_PERSISTED"
_ALREADY_BLOCKED = "ALREADY_BLOCKED"
_ENVIRONMENT = "SHADOW"
_VETO_STAGE = "INCIDENT_REACTION_READBACK"
_INCIDENT_REASON_PREFIX = "EXECUTION_GHOSV:"
_LATEST_EXECUTION_INCIDENT = "latest_authenticated_execution_incident"
_INCIDENT_ORIGIN_FIELDS = (
    "identity_digest",
    "envelope_id",
    "envelope_digest",
    "evidence_sha256",
    "incident_type",
    "reconciliation_reason",
)


class ExecutionIncidentSafetyError(ValueError):
    pass


class ExecutionIncidentObservationError(ExecutionIncidentSafetyError):
    """The reader could not bind one observation to a consistent state."""


class ExecutionIncidentHaltV1(RuntimeError):
    """Stop the standing cycle after the original Safety writer accepts an incident."""

    reason_code = "EXECUTION_GHOSV_SAFETY_HALT"

    def __init__(self, receipt: dict, *, raw_get_proof_status: str):
        self.receipt = receipt
        self.raw_get_proof_status = raw_get_proof_status
        self.detail = receipt["incident_id"]
        super().__init__(f"{self.reason_code}:{self.detail}")


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


@dataclass(frozen=True)
class AuthenticatedExecutionIncidentScopeV1:
    root: Path
    account: str
    state_path: Path

    @property
    def journal_path(self):
        return self.root / "execution-incident-receipts.json"

    @property
    def get_proof_root(self):
        return self.root / "authenticated-get-proofs"

    @property
    def lock_path(self):
        return self.state_path.with_name(self.state_path.name + ".execution-incident.lock")

    def binding(self):
        return {
            "root": str(self.root),
            "account": self.account,
            "environment": "LIVE",
            "filegate": str(self.state_path),
        }


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


def _require_authenticated_scope(scope):
    if (
        type(scope) is not AuthenticatedExecutionIncidentScopeV1
        or not scope.state_path.is_absolute()
        or scope.state_path.resolve() != scope.state_path
        or Path(canonical_kill_switch_state_path()).resolve() != scope.state_path
        or type(scope.account) is not str
        or not scope.account
        or scope.account.strip() != scope.account
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_FILEGATE_SCOPE_MISMATCH")
    if any(
        path.is_symlink()
        for path in (
            scope.state_path.with_suffix(".tmp"),
            scope.state_path.with_suffix(scope.state_path.suffix + ".tmp"),
            scope.state_path.parent / "backups",
        )
    ) or (scope.state_path.exists() and not scope.state_path.is_file()):
        raise ExecutionIncidentSafetyError("INCIDENT_FOREIGN_STORE_PATH")


def _require_private_incident_journal(scope):
    if (
        not scope.root.is_absolute()
        or scope.root.resolve() != scope.root
        or not scope.root.is_dir()
        or scope.root.stat().st_uid != os.getuid()
        or scope.root.stat().st_mode & 0o077
        or (scope.journal_path.exists() and not scope.journal_path.is_file())
        or any(
            path.is_symlink()
            for path in (
                scope.journal_path,
                scope.journal_path.with_suffix(".json.tmp"),
            )
        )
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_FOREIGN_STORE_PATH")


def _read_journal(scope):
    schema = _SCHEMA
    if type(scope) is AuthenticatedExecutionIncidentScopeV1:
        _require_private_incident_journal(scope)
        schema = _AUTHENTICATED_SCHEMA
    binding = {"schema": schema, "scope": scope.binding()}
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


def _kill_revision(payload, *, include_recovering=False):
    states = {"KILLED", "RECOVERING"} if include_recovering else {"KILLED"}
    if payload.get("state") not in states or not payload.get("killed_at"):
        return None
    generation = {
        "killed_at": payload["killed_at"],
        "trigger_reason": payload.get("trigger_reason"),
    }
    if _LATEST_EXECUTION_INCIDENT in payload:
        generation[_LATEST_EXECUTION_INCIDENT] = payload[_LATEST_EXECUTION_INCIDENT]
    if "filegate_generation" in payload:
        generation["filegate_generation"] = payload["filegate_generation"]
    return _digest(generation)


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
    live = type(scope) is AuthenticatedExecutionIncidentScopeV1
    require_scope = _require_authenticated_scope if live else _require_isolated_scope
    require_scope(scope)
    if (
        identity.execution_environment != ("LIVE" if live else _ENVIRONMENT)
        or identity.account_identity != scope.account
        or (not live and expected.session_id != scope.session_id)
        or (live and reconciliation_source is None)
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
    if live:
        original["session_id"] = expected.session_id
    incident_id = _digest({"scope": scope.binding(), **original})
    reason = _INCIDENT_REASON_PREFIX + incident_id

    if live:
        flags = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK
        lock_file = os.fdopen(os.open(scope.lock_path, flags, 0o600), "r+b")
    else:
        lock_file = (scope.root / "execution-incident.lock").open("a+b")
    with lock_file as lock:
        if live:
            info = os.fstat(lock.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise ExecutionIncidentSafetyError("INCIDENT_FILEGATE_LOCK_UNPROVEN")
        fcntl.flock(lock, fcntl.LOCK_EX)
        require_scope(scope)
        try:
            if live:
                scope.root.mkdir(mode=0o700, exist_ok=True)
            journal = _read_journal(scope)
        except (ExecutionIncidentSafetyError, OSError):
            if live:
                _ensure_incident_kill_v1(scope, reason, native_id=identity.native_id)
            raise
        entries = journal["receipts"]
        if incident_id in entries:
            return entries[incident_id]["receipt"]
        if any(
            datetime.fromisoformat(e["receipt"]["observed_at"]) >= observed_at
            for e in entries.values()
        ):
            raise ExecutionIncidentSafetyError("INCIDENT_STALE_OR_AMBIGUOUS_ORDER")
        payload = _ensure_incident_kill_v1(scope, reason, native_id=identity.native_id)
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


def _ensure_incident_kill_v1(scope, reason, *, native_id):
    if type(scope) is AuthenticatedExecutionIncidentScopeV1:
        writer = configured_filegate_writer_v1(scope.state_path)
        if writer is not None:
            writer.kill_v1(
                cause="R04",
                reason=reason,
                incident_id=reason.removeprefix(_INCIDENT_REASON_PREFIX),
                incident_scope={
                    "account": scope.account,
                    "environment": "LIVE",
                    "host": str(scope.root.parent),
                    "instrument": native_id,
                },
            )
            evidence, payload = _state_observation(scope)
            if evidence.state_name != "KILLED" or payload.get(_LATEST_EXECUTION_INCIDENT) != (
                reason.removeprefix(_INCIDENT_REASON_PREFIX)
            ):
                raise ExecutionIncidentSafetyError("INCIDENT_KILL_READBACK_UNPROVEN")
            return payload
    evidence, payload = _state_observation(scope)
    if evidence.evidence_status != "TRUSTED_PRESENT" or evidence.state_name == "DISABLED":
        raise ExecutionIncidentSafetyError("INCIDENT_FILEGATE_UNPROVEN")
    if evidence.state_name == "KILLED":
        if type(scope) is AuthenticatedExecutionIncidentScopeV1:
            incident_id = reason.removeprefix(_INCIDENT_REASON_PREFIX)
            if payload.get(_LATEST_EXECUTION_INCIDENT) != incident_id and (
                payload.get("trigger_reason") != reason or _LATEST_EXECUTION_INCIDENT in payload
            ):
                # The authenticated incident writer lock is held. Keep the
                # original Safety cause, but fence any earlier recovery scope.
                if _kill_revision(payload) is None or _state_observation(scope) != (
                    evidence,
                    payload,
                ):
                    raise ExecutionIncidentSafetyError("INCIDENT_FILEGATE_CHANGED_BEFORE_WRITE")
                updated = {**payload, _LATEST_EXECUTION_INCIDENT: incident_id}
                _require_authenticated_scope(scope)
                atomic_write_json(path=scope.state_path, payload=updated)
                if _state_observation(scope) != (evidence, updated):
                    raise ExecutionIncidentSafetyError("INCIDENT_KILL_READBACK_UNPROVEN")
                return updated
        return payload
    writer = KillSwitch({}, persistence=StatePersistence(str(scope.state_path)))
    if writer.state.name != evidence.state_name:
        raise ExecutionIncidentSafetyError("INCIDENT_FILEGATE_CHANGED_BEFORE_WRITE")
    if not writer.trigger(reason, triggered_by="execution_ghosv"):
        raise ExecutionIncidentSafetyError("INCIDENT_KILL_REFUSED")
    evidence, payload = _state_observation(scope)
    if evidence.state_name != "KILLED" or payload.get("trigger_reason") != reason:
        raise ExecutionIncidentSafetyError("INCIDENT_KILL_READBACK_UNPROVEN")
    return payload


def observe_offline_execution_incident_v1(
    *,
    scope: OfflineExecutionIncidentScopeV1,
    envelope: FinalOrderEnvelopeV1,
    incident_id: str | None = None,
) -> dict:
    """Read the current FILEGATE and discover its incident when no ID is supplied."""
    return _observe_execution_incident_v1(scope, envelope, incident_id, _require_isolated_scope)


def observe_authenticated_execution_incident_v1(
    *,
    scope: AuthenticatedExecutionIncidentScopeV1,
    envelope: FinalOrderEnvelopeV1,
    incident_id: str | None = None,
) -> dict:
    """Independently read the live-shaped FILEGATE and its bound incident receipt."""
    return _observe_execution_incident_v1(
        scope, envelope, incident_id, _require_authenticated_scope
    )


def observe_standing_execution_incident_v1(*, scope: AuthenticatedExecutionIncidentScopeV1) -> dict:
    """Read the current FILEGATE and recover its original envelope without a host."""
    return _observe_execution_incident_v1(
        scope, None, None, _require_authenticated_scope, recover_envelope=True
    )


def read_authenticated_execution_incident_origin_v1(
    *, scope: AuthenticatedExecutionIncidentScopeV1, incident_id: str
) -> dict:
    """Re-read the original Incident, budget revision and authenticated GETs by ID."""
    _require_authenticated_scope(scope)
    receipt = _read_journal(scope)["receipts"].get(incident_id)
    if receipt is None:
        raise ExecutionIncidentObservationError("INCIDENT_RECEIPT_MISSING")
    receipt = receipt["receipt"]
    if receipt["incident_id"] != incident_id:
        raise ExecutionIncidentObservationError("INCIDENT_RECEIPT_IDENTITY_CHANGED")
    _, _, identity = _recover_standing_incident_execution_v1(scope, receipt)
    if _standing_raw_get_proof_status_v1(scope, receipt) != "VERIFIED":
        raise ExecutionIncidentObservationError("INCIDENT_ORIGINAL_GETS_UNPROVEN")
    return {
        "incident_id": incident_id,
        "reservation_id": identity.portfolio_reservation_id,
        "identity_digest": identity.identity_digest(),
        "native_id": identity.native_id,
        "incident_receipt_sha256": _digest(receipt),
    }


def _recover_standing_incident_execution_v1(scope, receipt):
    """Bind the historical incident revision using only the configured owner root."""
    source = receipt["reconciliation_source"]
    origin = {
        key: receipt[key]
        for key in (*_INCIDENT_ORIGIN_FIELDS, "session_id", "reconciliation_source")
    }
    budget_root = scope.root.parent / "owner"
    reservation_id = source["reservation_id"]
    sequence, checksum = source["revision_ref"]
    if (
        scope.root.name != "execution-incident-safety"
        or source["budget_owner_root"] != str(budget_root)
        or receipt["incident_id"] != _digest({"scope": scope.binding(), **origin})
        or receipt["incident_type"] != ExecutionFillQuantityIncidentV1.incident_type
        or receipt["reconciliation_reason"]
        not in {REASON_FILL_EXCEEDS_ORDER, REASON_NEGATIVE_REMAINING}
    ):
        raise ExecutionIncidentObservationError("INCIDENT_BUDGET_SCOPE_UNPROVEN")
    state = read_budget_revision_read_only_v1(
        budget_root, account_identity=scope.account, sequence=sequence, expected_digest=checksum
    )["state"]
    link = state["execution_links"][reservation_id]
    identity = parse_exchange_reconciliation_identity_v1(link["identity"])
    envelope = FinalOrderEnvelopeV1(**link["envelope"])
    assert_envelope_unmodified_v1(
        envelope, expected_id=receipt["envelope_id"], expected_digest=receipt["envelope_digest"]
    )
    reconciliation = link["reconciliation"]
    if (
        type(identity) is not PortfolioExecutionReconciliationIdentityV2
        or identity.execution_environment != "LIVE"
        or identity.account_identity != scope.account
        or identity.budget_owner_root != str(budget_root)
        or identity.portfolio_reservation_id != reservation_id
        or identity.envelope_identity != envelope.envelope_id
        or identity.envelope_digest != envelope.envelope_digest
        or identity.identity_digest() != receipt["identity_digest"]
        or link["phase"] != "SUBMIT_MAY_HAVE_OCCURRED"
        or reconciliation["identity_digest"] != receipt["identity_digest"]
        or reconciliation["snapshot_digest"] != source["snapshot_digest"]
        or reconciliation["decision"]["outcome"] != OUTCOME_HALTED_UNRESOLVED
        or reconciliation["decision"]["reasons"] != [receipt["reconciliation_reason"]]
        or reconciliation["matched"] is not False
        or reconciliation["local_submit_outcome"] != LocalSubmitOutcome.TRANSPORT_UNKNOWN.value
        or reconciliation["reservation_released"] is not False
    ):
        raise ExecutionIncidentObservationError("INCIDENT_BUDGET_REVISION_UNPROVEN")
    return envelope, link, identity


def _standing_transport_abort_v1(link, identity):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        durable_consume_path_v1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.execution_v1 import (
        _original_never_submitted_v1,
    )

    original_root = link.get("transport_store_root")
    if not isinstance(original_root, str):
        return None
    root = Path(original_root)
    try:
        if not root.is_absolute() or root.resolve() != root:
            return None
        directory = root.stat()
        record_file = durable_consume_path_v1(root).lstat()
        if (
            not stat.S_ISDIR(directory.st_mode)
            or not stat.S_ISREG(record_file.st_mode)
            or record_file.st_nlink != 1
            or any(
                info.st_uid != os.getuid() or info.st_mode & 0o022
                for info in (directory, record_file)
            )
        ):
            return None
    except (OSError, RuntimeError, ValueError):
        return None
    proof = _original_never_submitted_v1(link, identity)
    if proof is None:
        return None
    record = proof["record"]
    attempt = record["transport_attempt"]
    return {
        "state": record["durable_state"],
        "reason_code": attempt["reason_code"],
        "aborted_at_utc": attempt["aborted_at_utc"],
        "record_sha256": proof["record_digest"],
        "kill_revision": None,
    }


def _original_post_veto_reason_v1(scope, envelope):
    try:
        CurrentPostSafetyContextV1(envelope, str(scope.state_path)).inspect_v1(stage=_VETO_STAGE)
    except CurrentPostSafetyVetoError as exc:
        return str(exc)
    return None


def _standing_raw_get_proof_status_v1(scope, receipt):
    from src.ops.execution_reconciliation_proof_store_v1 import (
        ExecutionReconciliationProofStoreError,
        read_authenticated_execution_reconciliation_proof_v1,
    )

    source = receipt["reconciliation_source"]
    try:
        proof = read_authenticated_execution_reconciliation_proof_v1(
            root=scope.get_proof_root,
            budget_owner_root=scope.root.parent / "owner",
            account=scope.account,
            session_id=receipt["session_id"],
            reservation_id=source["reservation_id"],
            revision_ref=tuple(source["revision_ref"]),
        )
        finding = proof.quantity_incident
        if (
            finding is None
            or proof.venue_host != source["venue_host"]
            or proof.snapshot_digest != source["snapshot_digest"]
            or [read.to_reference_v1() for read in proof.gets] != source["gets"]
            or finding.observed_at.isoformat() != receipt["observed_at"]
            or finding.identity_digest != receipt["identity_digest"]
            or finding.venue_order_id != receipt["venue_order_id"]
            or finding.snapshot_sha256 != receipt["evidence_sha256"]
            or list(finding.evidence_refs) != receipt["evidence_refs"]
            or finding.reconciliation_reason != receipt["reconciliation_reason"]
        ):
            return "UNPROVEN"
    except (ExecutionReconciliationProofStoreError, KeyError, TypeError):
        return "UNPROVEN"
    return "VERIFIED"


def _observe_execution_incident_v1(
    scope, envelope, incident_id, require_scope, *, recover_envelope=False
):
    require_scope(scope)
    evidence, payload = _state_observation(scope)
    veto_reason = None if recover_envelope else _original_post_veto_reason_v1(scope, envelope)

    requested_id = incident_id
    reason = payload.get("trigger_reason")
    latest = payload.get(_LATEST_EXECUTION_INCIDENT)
    if (
        incident_id is None
        and type(scope) is AuthenticatedExecutionIncidentScopeV1
        and evidence.state_name in {"KILLED", "RECOVERING"}
        and isinstance(latest, str)
        and re.fullmatch(r"[0-9a-f]{64}", latest)
    ):
        incident_id = latest
    if (
        incident_id is None
        and (not recover_envelope or evidence.state_name in {"KILLED", "RECOVERING"})
        and isinstance(reason, str)
        and reason.startswith(_INCIDENT_REASON_PREFIX)
    ):
        found = reason.removeprefix(_INCIDENT_REASON_PREFIX)
        if re.fullmatch(r"[0-9a-f]{64}", found):
            incident_id = found
    receipt = None
    receipt_error = None
    transport_abort = None
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
                if recover_envelope:
                    try:
                        envelope, link, identity = _recover_standing_incident_execution_v1(
                            scope, receipt
                        )
                    except (
                        KeyError,
                        TypeError,
                        ValueError,
                        OSError,
                        sqlite3.Error,
                        FullCoreFinalOrderEnvelopeError,
                    ):
                        receipt_error = "INCIDENT_BUDGET_REVISION_UNPROVEN"
                    else:
                        transport_abort = _standing_transport_abort_v1(link, identity)
                elif (
                    receipt["envelope_id"] != envelope.envelope_id
                    or receipt["envelope_digest"] != envelope.envelope_digest
                ):
                    receipt_error = "INCIDENT_REACTION_ENVELOPE_MISMATCH"
                    if requested_id is not None:
                        raise ExecutionIncidentSafetyError(receipt_error)
                    receipt = None

    if recover_envelope and envelope is not None:
        veto_reason = _original_post_veto_reason_v1(scope, envelope)
    raw_get_proof_status = None
    if recover_envelope and envelope is not None and receipt is not None:
        raw_get_proof_status = _standing_raw_get_proof_status_v1(scope, receipt)
    if _state_observation(scope) != (evidence, payload):
        raise ExecutionIncidentObservationError("INCIDENT_FILEGATE_CHANGED_DURING_VETO")
    require_scope(scope)
    revision = _kill_revision(payload, include_recovering=recover_envelope)
    if recover_envelope and receipt is not None and receipt.get("kill_revision") != revision:
        receipt_error = "INCIDENT_KILL_GENERATION_MISMATCH"
        raw_get_proof_status = None
        transport_abort = None
    result = {
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
            and receipt.get("kill_revision") == revision
            and veto_reason == f"POST_SAFETY_DURABLE_VETO:{_VETO_STAGE}:TRUSTED_PRESENT:KILLED"
        ),
    }
    if recover_envelope:
        incident_source = None
        if receipt is not None and envelope is not None and receipt_error is None:
            source = receipt["reconciliation_source"]
            incident_source = {
                "reservation_id": source["reservation_id"],
                "budget_revision_ref": source["revision_ref"],
                "session_id": receipt["session_id"],
                "snapshot_digest": source["snapshot_digest"],
                "envelope_digest": envelope.envelope_digest,
            }
        result.update(
            filegate_blocked=evidence.blocked,
            original_post_veto_checked=envelope is not None,
            incident_type=None if receipt is None else receipt.get("incident_type"),
            reconciliation_reason=None if receipt is None else receipt.get("reconciliation_reason"),
            incident_source=incident_source,
            raw_get_proof_status=raw_get_proof_status,
            transport_abort=transport_abort,
        )
    return result
