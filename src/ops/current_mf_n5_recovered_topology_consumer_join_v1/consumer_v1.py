"""Non-productive recover→apply→persist join for IsolatedLaneTopologyV1.

Feeds recovered prior topology into the existing mapping owner. Does not map
lanes, select, rank, bind, trade, or join a productive host. Does not own the
writer lock lifecycle.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, NoReturn

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.constants_v1 import (
    RECOVERY_MODE_BOOTSTRAP,
    RECOVERY_MODE_RESTART,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    load_completed_fixed_rank_publication_v1,
    topology_integrity_digest_v1,
    checkpoint_root_for,
    persist_durable_lane_assignment_v1,
    recover_durable_lane_assignment_v1,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneTopologyV1,
    apply_isolated_lane_topology_v1,
)
from src.ops.current_mf_n5_recovered_topology_consumer_join_v1.constants_v1 import (
    CAP23_CHANGE_REQUIRED,
    CAP24_CHANGE_REQUIRED,
    CONSUMER_CAP23_SELECTION_AUTHORITY,
    CONSUMER_CAP24_BINDING_AUTHORITY,
    CONSUMER_EXECUTION_AUTHORITY,
    CONSUMER_MAPPING_AUTHORITY,
    CONSUMER_MEMBERSHIP_AUTHORITY,
    CONSUMER_PERSISTENCE_AUTHORITY,
    CONSUMER_RANKING_AUTHORITY,
    CONSUMER_TRADING_AUTHORITY,
    CROSS_UNIVERSE_CANDIDATE_BORROWING,
    CROSS_UNIVERSE_FALLBACK,
    CROSS_UNIVERSE_PIN,
    CROSS_UNIVERSE_REPLACEMENT,
    CROSS_UNIVERSE_RERANKING,
    CROSS_UNIVERSE_SELECTION,
    DOUBLE_PLAY_CHANGE_REQUIRED,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    HOST_JOIN,
    INSTRUMENT_ID_ALONE_SUFFICIENT,
    MASTER_V2_CHANGE_REQUIRED,
    MF_PRODUCTIVE_JOIN,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_UNIVERSE_MERGE,
    OWNER,
    UNIVERSE_ISOLATION_ENFORCED,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.lifecycle_v1 import (
    pin_open_positions_in_membership_v1,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    MembershipContextArtifactV1,
    validate_membership_context_artifact_v1,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    validate_ranking_snapshot_bindings_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)

FAILURE_AUTHORITY = "LANE_CONSUMER_AUTHORITY_CLAIM_FORBIDDEN"
FAILURE_BOOTSTRAP_RETURNED_PRIOR = "LANE_CONSUMER_BOOTSTRAP_RETURNED_PRIOR"
FAILURE_RESTART_RETURNED_NONE = "LANE_CONSUMER_RESTART_RETURNED_NONE"


class RecoveredTopologyConsumerJoinError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _fail(code: str, detail: str = "") -> NoReturn:
    raise RecoveredTopologyConsumerJoinError(code, detail)


def _assert_non_authority() -> None:
    if (
        CONSUMER_RANKING_AUTHORITY
        or CONSUMER_MEMBERSHIP_AUTHORITY
        or CONSUMER_MAPPING_AUTHORITY
        or CONSUMER_PERSISTENCE_AUTHORITY
        or CONSUMER_CAP23_SELECTION_AUTHORITY
        or CONSUMER_CAP24_BINDING_AUTHORITY
        or CONSUMER_TRADING_AUTHORITY
        or CONSUMER_EXECUTION_AUTHORITY
        or HOST_JOIN
        or CAP23_CHANGE_REQUIRED
        or CAP24_CHANGE_REQUIRED
        or MASTER_V2_CHANGE_REQUIRED
        or DOUBLE_PLAY_CHANGE_REQUIRED
        or MF_PRODUCTIVE_JOIN
        or FIVE_LANE_RUNTIME_CREATED
        or FIVE_LANE_CONTINUOUS_HOST_JOIN
        or MULTI_FUTURE_RUNTIME_AUTHORIZED
        or not UNIVERSE_ISOLATION_ENFORCED
    ):
        _fail(FAILURE_AUTHORITY, OWNER)
    if (
        CROSS_UNIVERSE_SELECTION
        or CROSS_UNIVERSE_PIN
        or CROSS_UNIVERSE_REPLACEMENT
        or CROSS_UNIVERSE_FALLBACK
        or CROSS_UNIVERSE_CANDIDATE_BORROWING
        or CROSS_UNIVERSE_RERANKING
        or MULTI_UNIVERSE_MERGE
        or INSTRUMENT_ID_ALONE_SUFFICIENT
    ):
        _fail(FAILURE_AUTHORITY, "constant_violation")


def consume_recovered_isolated_lane_topology_v1(
    *,
    membership: MembershipContextArtifactV1,
    ranking_snapshot: Mapping[str, Any],
    topology_state_root_base: Path | str,
    writer: DurableLaneAssignmentSingleWriterV1,
    observed_portfolio: PortfolioTruthSnapshotV1 | None = None,
) -> IsolatedLaneTopologyV1:
    """Recover explicit prior topology, apply mapping, then persist the result."""
    _assert_non_authority()
    membership = pin_open_positions_in_membership_v1(
        membership,
        portfolio=observed_portfolio,
    )
    fixed = load_completed_fixed_rank_publication_v1(topology_state_root_base)
    if fixed is not None:
        writer.assert_held()
        if (
            Path(writer.state_root).resolve()
            != checkpoint_root_for(topology_state_root_base).resolve()
        ):
            _fail("LANE_FIXED_READER_WRITER_ROOT_MISMATCH", str(writer.state_root))
        validated = validate_membership_context_artifact_v1(membership)
        rank = ProductiveFuturesRankingSnapshotV1.from_dict(ranking_snapshot)
        if not validate_ranking_snapshot_bindings_v1(rank).ok:
            _fail("LANE_FIXED_RANKING_INVALID", rank.ranking_snapshot_id)
        recovered = recover_durable_lane_assignment_v1(
            topology_state_root_base=topology_state_root_base,
            recovery_mode=RECOVERY_MODE_RESTART,
            expected_universe_snapshot_id=rank.universe_snapshot_id,
            expected_ranking_snapshot_id=rank.ranking_snapshot_id,
            expected_ranking_integrity_digest=rank.integrity_digest,
        )
        if (
            recovered is None
            or recovered.membership_instance_id != validated.instance_id
            or topology_integrity_digest_v1(recovered.to_dict()) != fixed["topology_digest"]
        ):
            _fail("LANE_FIXED_PUBLICATION_MISMATCH", validated.instance_id)
        return recovered
    if membership.bootstrap:
        recovered = recover_durable_lane_assignment_v1(
            topology_state_root_base=topology_state_root_base,
            recovery_mode=RECOVERY_MODE_BOOTSTRAP,
        )
        if recovered is not None:
            _fail(FAILURE_BOOTSTRAP_RETURNED_PRIOR, membership.instance_id)
        prior_topology = None
    else:
        recovered = recover_durable_lane_assignment_v1(
            topology_state_root_base=topology_state_root_base,
            recovery_mode=RECOVERY_MODE_RESTART,
            expected_universe_snapshot_id=ranking_snapshot["universe_snapshot_id"],
        )
        if recovered is None:
            _fail(FAILURE_RESTART_RETURNED_NONE, membership.instance_id)
        prior_topology = recovered

    topology = apply_isolated_lane_topology_v1(
        membership=membership,
        ranking_snapshot=ranking_snapshot,
        topology_state_root_base=topology_state_root_base,
        prior_topology=prior_topology,
        open_position_custody_portfolio=observed_portfolio,
    )
    persist_durable_lane_assignment_v1(topology=topology, writer=writer)
    return topology
