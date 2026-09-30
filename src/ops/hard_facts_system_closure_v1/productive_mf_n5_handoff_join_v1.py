"""Deterministic Cap22 → POLICY_A → MF-N5 topology handoff (productive-real gate)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.current_mf_n5_recovered_topology_consumer_join_v1.consumer_v1 import (
    consume_recovered_isolated_lane_topology_v1,
)
from src.ops.hard_facts_system_closure_v1.cap22_productive_real_gate_v1 import (
    assert_cap22_productive_real_ranking_v1,
)
from src.ops.hard_facts_system_closure_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    N_GT_1_ENABLED,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    Cap22ProvenanceV1,
    MembershipContextArtifactV1,
    build_bootstrap_membership_from_cap22_snapshot_v1,
    write_membership_context_artifact_v1,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    checkpoint_root_for,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.mf_membership_selector_and_rotation_runtime_contract_v1 import (
    run_isolated_selector_cycle_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneTopologyV1,
)


class HardFactsMfN5HandoffError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.code = code


@dataclass(frozen=True)
class HardFactsCap22MembershipHandoffRequestV1:
    ranking_snapshot: Mapping[str, Any]
    membership_store_root: Path
    topology_state_root_base: Path
    source_relative_path: str = "runtime/hard_facts/cap22_ranking_snapshot.json"
    persist_selector: bool = True


@dataclass(frozen=True)
class HardFactsMfN5HandoffResultV1:
    membership: MembershipContextArtifactV1
    topology: IsolatedLaneTopologyV1
    selector_policy_trace: tuple[str, ...]
    cap22_integrity_digest: str


def cap22_provenance_from_mapping_v1(
    snapshot: Mapping[str, Any],
    *,
    source_relative_path: str,
    source_file_sha256: str,
) -> Cap22ProvenanceV1:
    return Cap22ProvenanceV1(
        ranking_snapshot_id=str(snapshot.get("ranking_snapshot_id") or ""),
        ranking_schema_version=str(snapshot.get("schema_version") or ""),
        ranking_integrity_digest=str(snapshot.get("integrity_digest") or ""),
        ranking_event_time=str(snapshot.get("event_time") or ""),
        universe_snapshot_id=str(snapshot.get("universe_snapshot_id") or ""),
        ranking_policy_id=str(snapshot.get("ranking_policy_id") or ""),
        ranking_policy_version=str(snapshot.get("ranking_policy_version") or ""),
        source_relative_path=source_relative_path,
        source_file_sha256=source_file_sha256,
        snapshot_state=str(snapshot.get("snapshot_state") or ""),
        top20_candidate_context_limit=int(snapshot.get("top20_candidate_context_limit") or 20),
    )


def execute_hard_facts_cap22_to_mf_n5_handoff_v1(
    request: HardFactsCap22MembershipHandoffRequestV1,
    *,
    prior: MembershipContextArtifactV1 | None = None,
    lane_assignment_writer: DurableLaneAssignmentSingleWriterV1 | None = None,
) -> HardFactsMfN5HandoffResultV1:
    if MULTI_FUTURE_RUNTIME_AUTHORIZED or N_GT_1_ENABLED or int(MAX_POSITIONS_EFFECTIVE) != 1:
        raise HardFactsMfN5HandoffError("PRODUCTIVE_CARDINALITY_INVARIANT")
    snapshot = dict(request.ranking_snapshot)
    assert_cap22_productive_real_ranking_v1(snapshot)
    raw = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    provenance = cap22_provenance_from_mapping_v1(
        snapshot,
        source_relative_path=request.source_relative_path,
        source_file_sha256=digest,
    )
    store = Path(request.membership_store_root)
    store.mkdir(parents=True, exist_ok=True)
    snap_file = store / "cap22_snapshot.json"
    snap_file.write_bytes(raw)
    if prior is None:
        prior = build_bootstrap_membership_from_cap22_snapshot_v1(
            snapshot_path=snap_file,
            source_relative_path=request.source_relative_path,
        )
        prior = write_membership_context_artifact_v1(prior, store_root=store)
    selector = run_isolated_selector_cycle_v1(
        snapshot=snapshot,
        cap22_provenance=provenance,
        prior=prior,
        store_root=store,
        persist=request.persist_selector,
    )
    membership = selector.persisted_artifact or selector.proposed_artifact or prior
    if membership is None:
        raise HardFactsMfN5HandoffError("SELECTOR_NO_MEMBERSHIP")
    if lane_assignment_writer is not None:
        writer = lane_assignment_writer
    else:
        writer = DurableLaneAssignmentSingleWriterV1(
            state_root=checkpoint_root_for(Path(request.topology_state_root_base)),
            session_id="hard-facts-handoff-v1",
        )
        writer.acquire()
    topology = consume_recovered_isolated_lane_topology_v1(
        membership=membership,
        ranking_snapshot=snapshot,
        topology_state_root_base=Path(request.topology_state_root_base),
        writer=writer,
    )
    return HardFactsMfN5HandoffResultV1(
        membership=membership,
        topology=topology,
        selector_policy_trace=tuple(
            json.dumps(x, sort_keys=True) if isinstance(x, dict) else str(x)
            for x in (selector.policy_trace or ())
        ),
        cap22_integrity_digest=str(snapshot.get("integrity_digest") or ""),
    )


def resolve_membership_via_hard_facts_handoff_v1(
    *,
    membership: MembershipContextArtifactV1,
    handoff: HardFactsCap22MembershipHandoffRequestV1 | None,
    lane_assignment_writer: Any = None,
) -> MembershipContextArtifactV1:
    if handoff is None:
        return membership
    result = execute_hard_facts_cap22_to_mf_n5_handoff_v1(
        handoff,
        prior=membership,
        lane_assignment_writer=lane_assignment_writer,
    )
    return result.membership
