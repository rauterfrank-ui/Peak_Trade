"""Non-productive join from recovered topology consume to occupied-lane pins.

Sequences the existing recovered-topology consumer with the existing occupied
lane pin builder. Does not map lanes, write pins, select, bind, trade, or join
a productive host. Does not own the writer lock lifecycle.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, NoReturn

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    build_occupied_lane_pins_v1,
)
from src.ops.current_mf_n5_occupied_lane_pin_consumer_join_v1.constants_v1 import (
    CAP23_CHANGE_REQUIRED,
    CAP24_CHANGE_REQUIRED,
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
from src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1 import (
    consume_recovered_isolated_lane_topology_v1,
)
from src.ops.mf_membership_context_artifact_contract_v1 import MembershipContextArtifactV1
from src.ops.single_selected_future_policy_v1.governed_pin_v1 import (
    GovernedCap23InstrumentPinV1,
)

FAILURE_AUTHORITY = "LANE_PIN_CONSUMER_AUTHORITY_CLAIM_FORBIDDEN"


class OccupiedLanePinConsumerJoinError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _fail(code: str, detail: str = "") -> NoReturn:
    raise OccupiedLanePinConsumerJoinError(code, detail)


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


def consume_occupied_lane_pins_v1(
    *,
    membership: MembershipContextArtifactV1,
    ranking_snapshot: Mapping[str, Any],
    topology_state_root_base: Path | str,
    writer: DurableLaneAssignmentSingleWriterV1,
) -> dict[str, GovernedCap23InstrumentPinV1]:
    """Join recovered-topology consume to occupied-lane pin build. No Cap23 write."""
    _assert_non_authority()
    topology = consume_recovered_isolated_lane_topology_v1(
        membership=membership,
        ranking_snapshot=ranking_snapshot,
        topology_state_root_base=topology_state_root_base,
        writer=writer,
    )
    return build_occupied_lane_pins_v1(
        topology,
        ranking_snapshot=ranking_snapshot,
    )
