"""Isolated MF previous-to-current deterministic replay contract V1.

Reconstructs WP-MF-03 selector/POLICY_A results from a Cap-2.2 snapshot and
the canonical membership-context artifact chain. Read-only: never writes
membership-context artifacts, never joins a host, and never authorizes
execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.mf_membership_context_artifact_contract_v1 import (
    POLICY_IDENTITY_V1,
    Cap22ProvenanceV1,
    MembershipContextArtifactError,
    MembershipContextArtifactV1,
    canonical_json_dumps,
    canonical_store_root,
    derive_rotation_delta_v1,
    read_membership_context_artifact_v1,
    sha256_hex,
)
from src.ops.mf_membership_selector_and_rotation_runtime_contract_v1 import (
    EXECUTION_AUTHORITY_EFFECT as SELECTOR_EXECUTION_AUTHORITY_EFFECT,
    EligibleCandidateV1,
    MfSelectorResultV1,
    load_observation_chain_v1,
    parse_eligible_cap22_top20,
    provenance_identity_key,
    select_membership_v1,
)

OWNER = "ops.mf_membership_previous_to_current_replay_contract_v1"

DETERMINISTIC_PREVIOUS_TO_CURRENT_REPLAY_IMPLEMENTED = True
OBSERVATION_AGE_RECONSTRUCTION_DETERMINISTIC = True
REPLAY_RESULT_DIGEST_STABLE = True
REPLAY_CANONICAL_MUTATION_FORBIDDEN = True
ROTATION_DELTAS_REPLAYABLE = True
ROTATION_DELTAS_STATUS = "DERIVED"
ROTATION_DELTAS_DURABLE_STAGE_FORBIDDEN = True

MF_ARTIFACT_CONTRACT_COMPLETE = True
MF_BOOTSTRAP_INSTANCE_PROVEN = True
MF_SELECTOR_RUNTIME_IMPLEMENTED = True
MF_ROTATION_RUNTIME_IMPLEMENTED = True
MF_PREVIOUS_TO_CURRENT_REPLAY_IMPLEMENTED = True
MF_DETERMINISTIC_REPLAY_PROVEN = True
ROTATION_RUNTIME_TESTED = True
ROTATION_REPLAY_PROVEN = True
ISOLATED_MF_TARGET_COMPLETE = True
PRODUCTIVE_MF_INTEGRATION_COMPLETE = False
NEXT_STEP_IS_AUTOMATIC = False

RUNTIME_AUTHORIZED = False
HOST_JOIN = False
HANDOFF_NOT_DESIGNED = True
G13_UNLOCK = False
CAP23_REWIRED = False
CAP24_REWIRED = False
EXECUTION_AUTHORITY_EFFECT = "NONE"
FULL_CORE_LIVE_AUTHORITY_EFFECT = "NONE"
CANARY_AUTHORITY_EFFECT = "NONE"

assert SELECTOR_EXECUTION_AUTHORITY_EFFECT == "NONE"


class MfReplayError(MembershipContextArtifactError):
    """Fail-closed replay error. Reuses artifact failure-code surface."""


@dataclass(frozen=True)
class MfReplayResultV1:
    prior_ordered_membership: tuple[str, ...]
    incumbent_observation_ages: dict[str, int]
    current_cap22_ordered_eligible_top20: tuple[str, ...]
    current_ordered_membership: tuple[str, ...]
    entered: tuple[str, ...]
    exited: tuple[str, ...]
    retained: tuple[str, ...]
    membership_decision_status: str
    policy_trace: tuple[dict[str, Any], ...]
    replay_input_identity: str
    replay_result_digest: str
    replay_deterministic: bool
    replay_mutation_performed: bool
    write_policy: str
    prior_instance_reference: str
    selector_result: MfSelectorResultV1


def canonical_store_inventory_v1(store_root: Path) -> dict[str, str]:
    if not store_root.is_dir():
        raise MfReplayError("ARTIFACT_MISSING", str(store_root))
    inventory: dict[str, str] = {}
    for path in sorted(store_root.iterdir()):
        if path.is_file():
            inventory[path.name] = sha256_hex(path.read_bytes())
    return inventory


def _bound_policy_identity(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    identity = dict(POLICY_IDENTITY_V1 if payload is None else payload)
    if identity != dict(POLICY_IDENTITY_V1):
        raise MfReplayError("POLICY_IDENTITY_MISMATCH", canonical_json_dumps(identity))
    return dict(POLICY_IDENTITY_V1)


def _validate_snapshot_provenance(
    snapshot: Mapping[str, Any],
    provenance: Cap22ProvenanceV1,
) -> None:
    if str(snapshot.get("ranking_snapshot_id") or "") != provenance.ranking_snapshot_id:
        raise MfReplayError("PROVENANCE_MISMATCH", "ranking_snapshot_id")
    if str(snapshot.get("integrity_digest") or "") != provenance.ranking_integrity_digest:
        raise MfReplayError("PROVENANCE_MISMATCH", "integrity_digest")
    if str(snapshot.get("event_time") or "") != provenance.ranking_event_time:
        raise MfReplayError("PROVENANCE_MISMATCH", "event_time")
    if str(snapshot.get("snapshot_state") or "") != provenance.snapshot_state:
        raise MfReplayError("PROVENANCE_MISMATCH", "snapshot_state")


def _independent_rotation_delta(
    prior_membership: Sequence[str],
    current_membership: Sequence[str],
) -> dict[str, list[str]]:
    prior_set = set(prior_membership)
    current_set = set(current_membership)
    entered = [item for item in current_membership if item not in prior_set]
    retained = [item for item in current_membership if item in prior_set]
    exited = [item for item in prior_membership if item not in current_set]
    return {"entered": entered, "exited": exited, "retained": retained}


def _sorted_ages(ages: Mapping[str, int]) -> dict[str, int]:
    return {key: int(ages[key]) for key in sorted(ages)}


def _eligible_ids(eligible: Sequence[EligibleCandidateV1]) -> tuple[str, ...]:
    return tuple(item.instrument_id for item in eligible)


def _input_payload(
    *,
    prior: MembershipContextArtifactV1,
    chain: Sequence[MembershipContextArtifactV1],
    provenance: Cap22ProvenanceV1,
    policy_identity: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "cap22_integrity_digest": provenance.ranking_integrity_digest,
        "cap22_ranking_snapshot_id": provenance.ranking_snapshot_id,
        "chain_instance_ids": [item.instance_id for item in chain],
        "policy_identity": dict(policy_identity),
        "prior_instance_id": prior.instance_id,
        "snapshot_identity": list(provenance_identity_key(provenance)),
    }


def _result_payload(
    *,
    prior_membership: Sequence[str],
    ages: Mapping[str, int],
    eligible_ids: Sequence[str],
    current_membership: Sequence[str],
    delta: Mapping[str, Sequence[str]],
    decision_status: str,
    policy_trace: Sequence[Mapping[str, Any]],
    write_policy: str,
) -> dict[str, Any]:
    return {
        "current_cap22_ordered_eligible_top20": list(eligible_ids),
        "current_ordered_membership": list(current_membership),
        "entered": list(delta["entered"]),
        "exited": list(delta["exited"]),
        "incumbent_observation_ages": _sorted_ages(ages),
        "membership_decision_status": decision_status,
        "policy_trace": list(policy_trace),
        "prior_ordered_membership": list(prior_membership),
        "retained": list(delta["retained"]),
        "write_policy": write_policy,
    }


def replay_previous_to_current_v1(
    *,
    snapshot: Mapping[str, Any],
    cap22_provenance: Cap22ProvenanceV1,
    prior_instance_id: str,
    store_root: Path,
    policy_identity: Mapping[str, Any] | None = None,
    expected_result: Mapping[str, Any] | None = None,
) -> MfReplayResultV1:
    """Pure previous→current replay. Never writes canonical membership state."""
    bound_policy = _bound_policy_identity(policy_identity)
    _validate_snapshot_provenance(snapshot, cap22_provenance)
    prior = read_membership_context_artifact_v1(prior_instance_id, store_root=store_root)
    if dict(prior.policy_identity) != bound_policy:
        raise MfReplayError("POLICY_IDENTITY_MISMATCH", prior.instance_id)
    chain = load_observation_chain_v1(prior, store_root=store_root)
    for artifact in chain:
        if dict(artifact.policy_identity) != bound_policy:
            raise MfReplayError("POLICY_IDENTITY_MISMATCH", artifact.instance_id)
    eligible = parse_eligible_cap22_top20(snapshot)
    selector = select_membership_v1(
        eligible=eligible,
        cap22_provenance=cap22_provenance,
        prior=prior,
        observation_chain=chain,
    )
    if selector.persisted_artifact is not None:
        raise MfReplayError("REPLAY_MUTATION_FORBIDDEN", selector.persisted_artifact.instance_id)
    independent = _independent_rotation_delta(
        prior.ordered_instrument_ids, selector.ordered_membership
    )
    if independent != selector.rotation_delta:
        raise MfReplayError("ROTATION_DELTA_MISMATCH", canonical_json_dumps(independent))
    if selector.proposed_artifact is not None:
        derived = derive_rotation_delta_v1(selector.proposed_artifact, prior)
        if derived != selector.rotation_delta:
            raise MfReplayError("ROTATION_DELTA_MISMATCH", "proposed_artifact")

    inputs = _input_payload(
        prior=prior,
        chain=chain,
        provenance=cap22_provenance,
        policy_identity=bound_policy,
    )
    reconstructed = _result_payload(
        prior_membership=prior.ordered_instrument_ids,
        ages=selector.holding_ages,
        eligible_ids=_eligible_ids(eligible),
        current_membership=selector.ordered_membership,
        delta=selector.rotation_delta,
        decision_status=selector.decision_status,
        policy_trace=selector.policy_trace,
        write_policy=selector.write_policy,
    )
    input_identity = sha256_hex(canonical_json_dumps(inputs))
    result_digest = sha256_hex(canonical_json_dumps({"inputs": inputs, "result": reconstructed}))
    if expected_result is not None:
        expected_membership = expected_result.get("current_ordered_membership")
        if expected_membership is not None and list(expected_membership) != list(
            selector.ordered_membership
        ):
            raise MfReplayError("REPLAY_EXPECTED_MISMATCH", "membership")
        expected_digest = expected_result.get("replay_result_digest")
        if expected_digest is not None and str(expected_digest) != result_digest:
            raise MfReplayError("REPLAY_EXPECTED_MISMATCH", "digest")
        expected_status = expected_result.get("membership_decision_status")
        if expected_status is not None and str(expected_status) != selector.decision_status:
            raise MfReplayError("REPLAY_EXPECTED_MISMATCH", "status")

    return MfReplayResultV1(
        prior_ordered_membership=tuple(prior.ordered_instrument_ids),
        incumbent_observation_ages=_sorted_ages(selector.holding_ages),
        current_cap22_ordered_eligible_top20=_eligible_ids(eligible),
        current_ordered_membership=tuple(selector.ordered_membership),
        entered=tuple(selector.rotation_delta["entered"]),
        exited=tuple(selector.rotation_delta["exited"]),
        retained=tuple(selector.rotation_delta["retained"]),
        membership_decision_status=selector.decision_status,
        policy_trace=tuple(dict(item) for item in selector.policy_trace),
        replay_input_identity=input_identity,
        replay_result_digest=result_digest,
        replay_deterministic=True,
        replay_mutation_performed=False,
        write_policy=selector.write_policy,
        prior_instance_reference=prior.instance_id,
        selector_result=selector,
    )


def replay_canonical_bootstrap_v1(
    *,
    snapshot: Mapping[str, Any],
    cap22_provenance: Cap22ProvenanceV1,
    repo_root: Path | None = None,
) -> MfReplayResultV1:
    store = canonical_store_root(repo_root=repo_root)
    return replay_previous_to_current_v1(
        snapshot=snapshot,
        cap22_provenance=cap22_provenance,
        prior_instance_id="mca_bf0255a6007432e2",
        store_root=store,
    )
