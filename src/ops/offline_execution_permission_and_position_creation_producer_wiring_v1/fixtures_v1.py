"""Deterministic caller-supplied snapshots for the offline boundary. Not live evidence."""

from __future__ import annotations

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    CONTRACT_VERSION,
    DEFAULT_ORDER_TYPE,
    DEFAULT_TD_MODE,
    OWNER_GO,
    REQUIRED_ENVIRONMENT,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.models_v1 import (
    AuthoritySnapshotV1,
    CanonicalLineageSnapshotV1,
    EvidenceFreshnessV1,
    OfflineExecutionBoundaryInputV1,
    PrewireEvidenceSnapshotV1,
)

_DIGEST = "a" * 64


def canonical_offline_boundary_fixture_v1() -> OfflineExecutionBoundaryInputV1:
    return OfflineExecutionBoundaryInputV1(
        contract_version=CONTRACT_VERSION,
        authority=AuthoritySnapshotV1(
            live_authorized=False,
            testnet_authorized=False,
            canary_authorized=False,
            orders_allowed=False,
            live_enabled=False,
            live_armed=False,
            submit_unlocked=False,
            general_live_submit_unlocked=False,
            environment=REQUIRED_ENVIRONMENT,
            owner_go=OWNER_GO,
        ),
        lineage=CanonicalLineageSnapshotV1(
            instrument_id=CANONICAL_INSTRUMENT_ID,
            decision_id="decision-offline-1",
            correlation_id="corr-offline-1",
            cycle_index=0,
            trading_epoch="1",
            risk_outcome="PASS",
            risk_digest=_DIGEST,
            safety_hard_blocked=False,
            safety_digest=_DIGEST,
            plan_intent_action="ENTER_LONG",
            plan_side="LONG",
            plan_quantity="1",
            plan_digest=_DIGEST,
            plan_execution_eligible=False,
            plan_adapter_compatible=False,
            plan_submission_authorized=False,
            mapper_intended_side="BUY",
            mapper_intended_quantity="1",
            mapper_decision_outcome="enter_long",
            mapper_intent_action="ENTER_LONG",
            mapper_safety_blocked=False,
            mapper_reason_codes=("PASS",),
        ),
        prewire=PrewireEvidenceSnapshotV1(
            freshness_status=EvidenceFreshnessV1.PASS,
            source_kind="CALLER_SUPPLIED_SNAPSHOT",
            get_performed_this_workpackage=False,
            instrument_id=CANONICAL_INSTRUMENT_ID,
            instrument_state="live",
            order_type=DEFAULT_ORDER_TYPE,
            td_mode=DEFAULT_TD_MODE,
            limit_px="1.2345",
            quantity="1",
            max_lmt_sz="10",
            avail_buy="1",
            avail_sell="1",
            leverage="3",
            mgn_mode="cross",
            pos_mode="net",
            account_mode="unproven_snapshot_token",
            position_observation_state="NOT_OBSERVED",
            recon_state="CLEAR",
            prior_action_identity="",
            prior_transport_outcome="",
        ),
    )
