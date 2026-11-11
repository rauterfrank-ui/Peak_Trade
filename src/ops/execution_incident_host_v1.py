"""Bind the original portfolio-host GET reconciliation to Safety."""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import re

from src.ops.execution_ghosv_fill_quantity_v1 import (
    build_execution_fill_quantity_incident_v1,
)
from src.ops.execution_incident_safety_v1 import (
    AuthenticatedExecutionIncidentScopeV1,
    ExecutionIncidentSafetyError,
    OfflineExecutionIncidentScopeV1,
    _apply_confirmed_execution_incident_v1,
    _require_isolated_scope,
)
from src.ops.execution_reconciliation_get_provenance_v1 import (
    AuthenticatedExecutionReconciliationProofV1,
    AuthenticatedReconciliationGetV1,
    adjudicate_reconciliation_quantity_incident_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
    FreshPretradeGetTransportResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    SIMULATION_OKX_TRANSPORT_INJECTED,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    RECONCILIATION_PROVIDER_OKX_EEA_READ_ONLY_GET,
    FullCoreExchangeReconciliationSnapshotV1,
    LocalSubmitOutcome,
    PortfolioExecutionReconciliationIdentityV2,
    adjudicate_full_core_exchange_reconciliation_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.execution_v1 import (
    read_persisted_execution_reconciliation_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    HostBudgetRecoveryContextV1,
    PortfolioBudgetHostV1,
)


def deliver_authenticated_host_execution_incident_v1(
    *,
    host: PortfolioBudgetHostV1,
    capture: AuthenticatedReconciliationGetV1,
    reservation_id: str,
    identity: PortfolioExecutionReconciliationIdentityV2,
    snapshot: FullCoreExchangeReconciliationSnapshotV1,
    result: dict,
) -> dict | None:
    """Recheck current GET evidence and the original budget revision before the kill."""
    if (
        type(capture) is not AuthenticatedReconciliationGetV1
        or capture.transport is not host.reconciliation_transport
        or type(identity) is not PortfolioExecutionReconciliationIdentityV2
        or host.closed
        or host.execution_environment != "LIVE"
        or host.execution_incident_state_path is None
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_AUTHENTICATED_HOST_SOURCE_UNPROVEN")
    proof = capture.evidence.get(reservation_id)
    if (
        type(proof) is not AuthenticatedExecutionReconciliationProofV1
        or not (proof.account == host.account == identity.account_identity)
        or proof.session_id != host.session_id
        or proof.reservation_id != reservation_id
        or identity.portfolio_reservation_id != reservation_id
        or identity.budget_owner_root != str(host.root / "owner")
        or proof.identity_digest != identity.identity_digest()
        or len(proof.gets) != 6
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_AUTHENTICATED_HOST_SOURCE_UNPROVEN")
    if proof.quantity_incident is None:
        return None
    seq, checksum, link = read_persisted_execution_reconciliation_v1(
        host.owner, reservation_id, revision_ref=proof.revision_ref
    )
    if (
        (seq, checksum) != proof.revision_ref
        or link["identity"] != identity.to_dict()
        or link["reconciliation"] != result
        or result["snapshot_digest"] != proof.snapshot_digest
        or result["reservation_released"] is not False
        or result["matched"] is not False
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_AUTHENTICATED_BUDGET_READBACK_UNPROVEN")
    expected = adjudicate_reconciliation_quantity_incident_v1(
        session_id=host.session_id,
        observed_at=proof.gets[-1].acquired_at.astimezone(timezone.utc),
        identity=identity,
        snapshot=snapshot,
        result=result,
    )
    if (
        expected is None
        or expected != proof.quantity_incident
        or not (
            proof.gets[-1].acquired_at.timestamp()
            <= host.clock()
            <= proof.gets[0].acquired_at.timestamp()
            + POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS / 1000
        )
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_AUTHENTICATED_PROOF_STALE_OR_CHANGED")
    root = host.root / "execution-incident-safety"
    scope = AuthenticatedExecutionIncidentScopeV1(
        root, host.account, host.execution_incident_state_path
    )
    return _apply_confirmed_execution_incident_v1(
        scope=scope,
        identity=identity,
        expected=expected,
        reconciliation_source={
            "budget_owner_root": identity.budget_owner_root,
            "reservation_id": reservation_id,
            "revision_ref": list(proof.revision_ref),
            "snapshot_digest": proof.snapshot_digest,
            "venue_host": proof.venue_host,
            "gets": [
                {
                    "endpoint": read.endpoint,
                    "decision_id": read.decision_id,
                    "acquired_at": read.acquired_at.isoformat(),
                    "body_sha256": read.body_sha256,
                }
                for read in proof.gets
            ],
        },
    )


class InjectedReconciliationGetV1:
    """Preserve the injected port designation at every existing GET boundary."""

    def __init__(self, transport):
        if getattr(transport, "transport_class", None) != TRANSPORT_CLASS_INJECTED_TEST_DOUBLE:
            raise ExecutionIncidentSafetyError("HOST_EXECUTION_EVIDENCE_INJECTED_GET_REQUIRED")
        self.transport = transport
        self.evidence: dict[str, HostExecutionReconciliationEvidenceV1] = {}

    def reset_v1(self):
        self.evidence.clear()

    def get(self, **kwargs):
        result = self.transport.get(**kwargs)
        if (
            type(result) is not FreshPretradeGetTransportResultV1
            or result.transport_class != TRANSPORT_CLASS_INJECTED_TEST_DOUBLE
            or result.venue_live_contact is not False
            or result.data_safety_source_kind is not None
        ):
            raise ExecutionIncidentSafetyError("HOST_EXECUTION_EVIDENCE_FOREIGN_GET")
        return result

    def record_v1(self, host, rid, identity, snapshot, observed_at, _decision):
        sequence, checksum, _ = read_persisted_execution_reconciliation_v1(host.owner, rid)
        self.evidence[rid] = HostExecutionReconciliationEvidenceV1(
            session_id=host.session_id,
            reservation_id=rid,
            identity=identity,
            snapshot=snapshot,
            observed_at=observed_at,
            revision_ref=(sequence, checksum),
        )


@dataclass(frozen=True)
class HostExecutionReconciliationEvidenceV1:
    session_id: str
    reservation_id: str
    identity: PortfolioExecutionReconciliationIdentityV2
    snapshot: FullCoreExchangeReconciliationSnapshotV1
    observed_at: datetime
    revision_ref: tuple[int, str]


def _require_host_scope(host, scope):
    if (
        type(host) is not PortfolioBudgetHostV1
        or host.closed
        or host.execution_environment != "SHADOW"
        or host.session_id != scope.session_id
        or host.account != scope.account
        or not host.root.is_relative_to(scope.root)
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_HOST_EVIDENCE_SCOPE_MISMATCH")


def observe_and_deliver_host_execution_incident_v1(
    *,
    host: PortfolioBudgetHostV1,
    bindings,
    scope: OfflineExecutionIncidentScopeV1,
    reservation_id: str,
) -> tuple[HostBudgetRecoveryContextV1, dict | None]:
    """Run one explicit SHADOW observation and deliver the selected reservation's incident."""
    _require_isolated_scope(scope)
    _require_host_scope(host, scope)
    context, captured = host.observe_execution_reconciliation_evidence_v1(bindings)
    evidence = captured.get(reservation_id)
    receipt = (
        deliver_host_execution_incident_v1(scope=scope, context=context, evidence=evidence)
        if evidence is not None
        else None
    )
    return context, receipt


def deliver_host_execution_incident_v1(
    *,
    scope: OfflineExecutionIncidentScopeV1,
    context: HostBudgetRecoveryContextV1,
    evidence: HostExecutionReconciliationEvidenceV1,
) -> dict | None:
    """Validate the original host and persisted reconciliation before isolated delivery."""
    _require_isolated_scope(scope)
    if (
        type(context) is not HostBudgetRecoveryContextV1
        or type(evidence) is not HostExecutionReconciliationEvidenceV1
        or type(evidence.identity) is not PortfolioExecutionReconciliationIdentityV2
        or type(evidence.snapshot) is not FullCoreExchangeReconciliationSnapshotV1
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_HOST_EVIDENCE_TYPE_UNPROVEN")
    host, identity, snapshot = context.host, evidence.identity, evidence.snapshot
    _require_host_scope(host, scope)
    rid = evidence.reservation_id
    revision_ref = evidence.revision_ref
    if (
        type(revision_ref) is not tuple
        or len(revision_ref) != 2
        or type(revision_ref[0]) is not int
        or revision_ref[0] <= 0
        or type(revision_ref[1]) is not str
        or re.fullmatch(r"[0-9a-f]{64}", revision_ref[1]) is None
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_HOST_EVIDENCE_REVISION_UNPROVEN")
    if (
        host.owner is None
        or identity.execution_environment != "SHADOW"
        or evidence.session_id != scope.session_id
        or not (context.account == identity.account_identity == scope.account)
        or identity.budget_owner_root != str(host.root / "owner")
        or identity.portfolio_reservation_id != rid
        or snapshot.provider != RECONCILIATION_PROVIDER_OKX_EEA_READ_ONLY_GET
        or snapshot.simulation_mode != SIMULATION_OKX_TRANSPORT_INJECTED
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_HOST_EVIDENCE_SCOPE_MISMATCH")
    evaluated_at = datetime.fromtimestamp(host.clock(), timezone.utc)
    observed_at = evidence.observed_at
    if (
        type(observed_at) is not datetime
        or observed_at.utcoffset() is None
        or not scope.started_at <= observed_at <= evaluated_at
        or (evaluated_at - observed_at).total_seconds() > 5
        or any(item.received_at != observed_at.isoformat() for item in snapshot.evidence_items)
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_HOST_EVIDENCE_TIME_UNPROVEN")
    sequence, checksum, link = read_persisted_execution_reconciliation_v1(
        host.owner, rid, revision_ref=revision_ref
    )
    stored = link["reconciliation"]
    snapshot_digest = sha256(json.dumps(snapshot.to_dict(), sort_keys=True).encode()).hexdigest()
    if (
        link["identity"] != identity.to_dict()
        or stored != context.execution_reconciliation.get(rid)
        or stored["snapshot_digest"] != snapshot_digest
        or stored["identity_digest"] != identity.identity_digest()
        or stored["portfolio_digest"] != context.observed.digest()
    ):
        raise ExecutionIncidentSafetyError("INCIDENT_HOST_EVIDENCE_READBACK_MISMATCH")
    local_outcome = LocalSubmitOutcome(stored["local_submit_outcome"])
    if local_outcome is not LocalSubmitOutcome.TRANSPORT_UNKNOWN:
        return None
    decision = adjudicate_full_core_exchange_reconciliation_v1(
        identity=identity, snapshot=snapshot, local_submit_outcome=local_outcome
    )
    if stored["decision"] != decision.to_dict():
        raise ExecutionIncidentSafetyError("INCIDENT_HOST_DECISION_READBACK_MISMATCH")
    finding = build_execution_fill_quantity_incident_v1(
        session_id=evidence.session_id,
        observed_at=observed_at,
        identity=identity,
        snapshot=snapshot,
        decision=decision,
        local_submit_outcome=local_outcome,
    )
    if finding is None:
        return None
    return _apply_confirmed_execution_incident_v1(
        scope=scope,
        identity=identity,
        expected=finding,
        reconciliation_source={
            "provider": snapshot.provider,
            "simulation_mode": snapshot.simulation_mode,
            "reservation_id": rid,
            "budget_revision": sequence,
            "budget_revision_digest": checksum,
            "budget_snapshot_digest": snapshot_digest,
        },
    )
