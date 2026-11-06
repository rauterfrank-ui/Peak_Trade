"""Ranking-domain join from occupied-lane pins to isolated Cap 2.3 N=1 persist.

Delegates to checked assessment and publication using existing topology and
Cap23 owners. Does not bind, trade, or activate a productive host.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, NoReturn

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1.constants_v1 import (
    CAP23_CHANGE_REQUIRED,
    CAP24_CHANGE_REQUIRED,
    CROSS_UNIVERSE_CANDIDATE_BORROWING,
    CROSS_UNIVERSE_FALLBACK,
    CROSS_UNIVERSE_PIN,
    CROSS_UNIVERSE_REPLACEMENT,
    CROSS_UNIVERSE_RERANKING,
    CROSS_UNIVERSE_SELECTION,
    DOUBLE_PLAY_CHANGE_REQUIRED,
    FAILURE_AUTHORITY,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    HOST_JOIN,
    INSTRUMENT_ID_ALONE_SUFFICIENT,
    JOIN_CAP23_SELECTION_AUTHORITY,
    JOIN_CAP24_BINDING_AUTHORITY,
    JOIN_EXECUTION_AUTHORITY,
    JOIN_MAPPING_AUTHORITY,
    JOIN_MEMBERSHIP_AUTHORITY,
    JOIN_PERSISTENCE_AUTHORITY,
    JOIN_PIN_AUTHORITY,
    JOIN_RANKING_AUTHORITY,
    JOIN_TRADING_AUTHORITY,
    MASTER_V2_CHANGE_REQUIRED,
    MF_PRODUCTIVE_JOIN,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_UNIVERSE_MERGE,
    OWNER,
    PARALLEL_AUTHORITY_CREATED,
    UNIVERSE_ISOLATION_ENFORCED,
)
from src.ops.mf_membership_context_artifact_contract_v1 import MembershipContextArtifactV1
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
)


class RankingDomainOccupiedLaneCap23ProduceJoinError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.recovery_action = {
            "LANE_SELECTION_PUBLICATION_DEFERRED": "REASSESS_FRESH_RANKING_WITH_EXISTING_CAP23_POLICY",
            "LANE_REPLACEMENT_POSITION_TRUTH_UNPROVEN": "REFRESH_VALIDATED_PORTFOLIO_TRUTH",
            "LANE_REPLACEMENT_OPEN_POSITION": "KEEP_POSITION_CUSTODY_UNTIL_CONFIRMED_FLAT",
            "LANE_REPLACEMENT_CUSTODY_ADMISSION_REQUIRED": "RECONCILE_CUSTODY_AND_OBTAIN_EXISTING_OWNER_ADMISSION",
            "LANE_REMOVAL_REQUIRES_SEPARATE_DISPOSITION": "USE_EXISTING_OWNER_LANE_DISPOSITION",
        }.get(code, "INSPECT_OWNER_STATE_AND_RESTORE_PROVEN_CONTINUITY")
        message = f"{code}:{detail}" if detail else code
        super().__init__(f"{message}:recovery_action={self.recovery_action}")
        self.failure_code = code
        self.detail = detail


def _fail(code: str, detail: str = "") -> NoReturn:
    raise RankingDomainOccupiedLaneCap23ProduceJoinError(code, detail)


def _assert_non_authority() -> None:
    if (
        JOIN_RANKING_AUTHORITY
        or JOIN_MEMBERSHIP_AUTHORITY
        or JOIN_MAPPING_AUTHORITY
        or JOIN_PERSISTENCE_AUTHORITY
        or JOIN_PIN_AUTHORITY
        or JOIN_CAP23_SELECTION_AUTHORITY
        or JOIN_CAP24_BINDING_AUTHORITY
        or JOIN_TRADING_AUTHORITY
        or JOIN_EXECUTION_AUTHORITY
        or HOST_JOIN
        or CAP23_CHANGE_REQUIRED
        or CAP24_CHANGE_REQUIRED
        or MASTER_V2_CHANGE_REQUIRED
        or DOUBLE_PLAY_CHANGE_REQUIRED
        or MF_PRODUCTIVE_JOIN
        or FIVE_LANE_RUNTIME_CREATED
        or FIVE_LANE_CONTINUOUS_HOST_JOIN
        or MULTI_FUTURE_RUNTIME_AUTHORIZED
        or PARALLEL_AUTHORITY_CREATED
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


def produce_occupied_lane_cap23_n1_selections_v1(
    *,
    membership: MembershipContextArtifactV1,
    ranking_snapshot: Mapping[str, Any],
    topology_state_root_base: Path | str,
    writer: DurableLaneAssignmentSingleWriterV1,
    repository_sha: str,
    producer_observed_at_unix: float,
    observed_portfolio=None,
    replacement_admission_by_lane=None,
) -> dict[str, SingleSelectedFutureSelectionV1]:
    """Compatibility facade: all callers use assessment before publication."""
    from .checked_publication_v1 import publish_checked_lane_selections_v1

    return publish_checked_lane_selections_v1(
        membership=membership,
        ranking_snapshot=ranking_snapshot,
        topology_state_root_base=topology_state_root_base,
        writer=writer,
        repository_sha=repository_sha,
        producer_observed_at_unix=producer_observed_at_unix,
        observed_portfolio=observed_portfolio,
        replacement_admission_by_lane=replacement_admission_by_lane,
    ).selections
