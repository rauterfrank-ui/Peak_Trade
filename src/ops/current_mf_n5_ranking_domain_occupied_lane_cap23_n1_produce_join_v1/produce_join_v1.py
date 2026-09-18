"""Ranking-domain join from occupied-lane pins to isolated Cap 2.3 N=1 persist.

Sequences the existing occupied-lane pin consumer with the existing Cap 2.3
N=1 produce/persist path once per occupied lane. Does not bind, trade, or
join a productive host. Does not own topology or Cap 2.3 writer locks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, NoReturn

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    lane_state_root_for,
)
from src.ops.current_mf_n5_occupied_lane_pin_consumer_join_v1.consumer_v1 import (
    consume_occupied_lane_pins_v1,
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
    FAILURE_CAP23_SELECTION_MISSING,
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
from src.ops.single_selected_future_policy_v1.governed_pin_v1 import (
    GovernedCap23InstrumentPinV1,
    lane_state_root_key,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
)
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    run_single_selected_future_policy_v1,
)
from src.ops.single_selected_future_policy_v1.reason_codes_v1 import SelectionFailureCodeV1


class RankingDomainOccupiedLaneCap23ProduceJoinError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
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


def _selection_from_cap23_result(
    payload: Mapping[str, Any],
) -> SingleSelectedFutureSelectionV1 | None:
    raw = payload.get("selection")
    if raw is None:
        return None
    if isinstance(raw, SingleSelectedFutureSelectionV1):
        return raw
    if isinstance(raw, Mapping):
        return SingleSelectedFutureSelectionV1.from_dict(raw)
    return None


def produce_occupied_lane_cap23_n1_selections_v1(
    *,
    membership: MembershipContextArtifactV1,
    ranking_snapshot: Mapping[str, Any],
    topology_state_root_base: Path | str,
    writer: DurableLaneAssignmentSingleWriterV1,
    repository_sha: str,
    producer_observed_at_unix: float,
) -> dict[str, SingleSelectedFutureSelectionV1]:
    """Join occupied-lane pins to isolated Cap 2.3 N=1 produce/persist. Stop there."""
    _assert_non_authority()
    pins = consume_occupied_lane_pins_v1(
        membership=membership,
        ranking_snapshot=ranking_snapshot,
        topology_state_root_base=topology_state_root_base,
        writer=writer,
    )
    unknown = sorted(set(pins) - set(LANE_IDS))
    if unknown:
        _fail(SelectionFailureCodeV1.GOVERNED_PIN_MISSING_LANE_BINDING.value, ",".join(unknown))

    produced: dict[str, SingleSelectedFutureSelectionV1] = {}
    for lane_id in LANE_IDS:
        pin = pins.get(lane_id)
        if pin is None:
            continue
        if not isinstance(pin, GovernedCap23InstrumentPinV1):
            _fail(SelectionFailureCodeV1.GOVERNED_PIN_SCHEMA_MISMATCH.value, lane_id)
        expected_root = lane_state_root_for(
            topology_state_root_base=topology_state_root_base,
            lane_id=lane_id,
        )
        if lane_state_root_key(pin.lane_state_root) != expected_root:
            _fail(
                SelectionFailureCodeV1.GOVERNED_PIN_LANE_STATE_ROOT_MISMATCH.value,
                lane_id,
            )
        state_root = Path(pin.lane_state_root)
        result = run_single_selected_future_policy_v1(
            state_root=state_root,
            ranking_snapshot=ranking_snapshot,
            repository_sha=repository_sha,
            producer_observed_at_unix=producer_observed_at_unix,
            load_previous_from_state=True,
            governed_pin=pin,
        )
        selection = _selection_from_cap23_result(result)
        if selection is None:
            codes = result.get("failure_codes") if isinstance(result, Mapping) else ()
            detail = ",".join(str(code) for code in (codes or ()))
            _fail(FAILURE_CAP23_SELECTION_MISSING, detail or lane_id)
        produced[lane_id] = selection
    return produced
