"""Isolated MF selector and membership-diff rotation runtime V1.

Consumes Cap-2.2 eligible Top-20 order and the WP-MF-02 membership-context
artifact. Applies ratified POLICY_A. Does not rerank, score, join a host,
unlock G13, or authorize execution. Rotation deltas are derived, never stored.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.mf_membership_context_artifact_contract_v1 import (
    CAP22_TOP20_LIMIT,
    ELIGIBILITY_ELIGIBLE,
    EXECUTION_AUTHORITY_EFFECT as ARTIFACT_EXECUTION_AUTHORITY_EFFECT,
    N_VALUE,
    SNAPSHOT_STATE_VALID,
    Cap22ProvenanceV1,
    MembershipContextArtifactError,
    MembershipContextArtifactV1,
    build_membership_context_artifact_v1,
    derive_rotation_delta_v1,
    read_membership_context_artifact_v1,
    write_membership_context_artifact_v1,
)

OWNER = "ops.mf_membership_selector_and_rotation_runtime_contract_v1"

SELECTOR_RUNTIME_IMPLEMENTED = True
MEMBERSHIP_DECISION_RUNTIME_IMPLEMENTED = True
ROTATION_RUNTIME_IMPLEMENTED = True
ROTATION_CONTROLLER_ROLE = "MEMBERSHIP_DIFF_ONLY"
ROTATION_CONTROLLER_OWNER_BOUND = True

HYSTERESIS_MODE = "RANK_IMPROVEMENT_VS_DISPLACED_INCUMBENT"
CHALLENGER_MARGIN_TYPE = "RANK"
CHALLENGER_MARGIN_VALUE = 1
MINIMUM_HOLDING_UNIT = "RANKING_OBSERVATIONS"
MINIMUM_HOLDING_VALUE = 2
CONSECUTIVE_CONFIRMATION_COUNT = 1
MULTIPLE_REPLACEMENTS_PER_CYCLE = True
TIE_BREAK = "CAP22_ORIGIN_CONSUMED_AS_MEMBERSHIP_ORDER"
FORCED_REMOVAL_RULE = "ABSENT_OR_INELIGIBLE_BYPASSES_ANTI_CHURN"

HOLDING_STATE_DERIVABLE_FROM_EXISTING_ARTIFACTS = True
HOLDING_STATE_IMPLEMENTATION = "ARTIFACT_CHAIN_DISTINCT_SNAPSHOT_COUNT"
UNCHANGED_MEMBERSHIP_WRITE_POLICY = (
    "WRITE_NEW_OBSERVATION_INSTANCE_IF_DISTINCT_SNAPSHOT_ELSE_NO_NEW_INSTANCE"
)
WRITE_NEW_OBSERVATION_INSTANCE = "WRITE_NEW_OBSERVATION_INSTANCE"
NO_NEW_INSTANCE = "NO_NEW_INSTANCE"

RUNTIME_AUTHORIZED = False
HOST_JOIN = False
HANDOFF_NOT_DESIGNED = True
G13_UNLOCK = False
CAP23_REWIRED = False
CAP24_REWIRED = False
EXECUTION_AUTHORITY_EFFECT = "NONE"
FULL_CORE_LIVE_AUTHORITY_EFFECT = "NONE"
CANARY_AUTHORITY_EFFECT = "NONE"

STATUS_UNCHANGED_REPLAY = "UNCHANGED_REPLAY"
STATUS_UNCHANGED_NEW_OBSERVATION = "UNCHANGED_NEW_OBSERVATION"
STATUS_CHANGED = "CHANGED"

assert ARTIFACT_EXECUTION_AUTHORITY_EFFECT == "NONE"


class MfSelectorError(MembershipContextArtifactError):
    """Fail-closed selector error. Reuses artifact failure-code surface."""


@dataclass(frozen=True)
class EligibleCandidateV1:
    instrument_id: str
    cap22_rank: int


@dataclass(frozen=True)
class MfSelectorResultV1:
    ordered_membership: tuple[str, ...]
    decision_status: str
    policy_trace: tuple[dict[str, Any], ...]
    prior_instance_reference: str
    current_cap22_provenance: Cap22ProvenanceV1
    rotation_delta: dict[str, list[str]]
    write_policy: str
    holding_ages: dict[str, int]
    proposed_artifact: Optional[MembershipContextArtifactV1]
    persisted_artifact: Optional[MembershipContextArtifactV1]


def parse_eligible_cap22_top20(snapshot: Mapping[str, Any]) -> tuple[EligibleCandidateV1, ...]:
    if str(snapshot.get("snapshot_state") or "") != SNAPSHOT_STATE_VALID:
        raise MfSelectorError("INVALID_CAP22_INPUT", "snapshot_state")
    ranked = list(snapshot.get("ranked_candidates") or [])
    try:
        ranked.sort(key=lambda row: int(row.get("rank") or 0))
    except (TypeError, ValueError) as exc:
        raise MfSelectorError("INVALID_CAP22_INPUT", "rank") from exc
    top20 = ranked[:CAP22_TOP20_LIMIT]
    seen_ids: set[str] = set()
    seen_ranks: set[int] = set()
    eligible: list[EligibleCandidateV1] = []
    for row in top20:
        if not isinstance(row, Mapping):
            raise MfSelectorError("INVALID_CAP22_INPUT", "row")
        instrument_id = str(row.get("canonical_instrument_id") or "").strip()
        try:
            rank = int(row.get("rank") or 0)
        except (TypeError, ValueError) as exc:
            raise MfSelectorError("INVALID_CAP22_INPUT", "rank") from exc
        if not instrument_id or rank < 1:
            raise MfSelectorError("INVALID_CAP22_INPUT", "instrument_or_rank")
        if instrument_id in seen_ids:
            raise MfSelectorError("DUPLICATE_CAP22_INPUT", instrument_id)
        if rank in seen_ranks:
            raise MfSelectorError("DUPLICATE_CAP22_INPUT", f"rank:{rank}")
        seen_ids.add(instrument_id)
        seen_ranks.add(rank)
        if str(row.get("eligibility_status") or "") == ELIGIBILITY_ELIGIBLE:
            eligible.append(EligibleCandidateV1(instrument_id=instrument_id, cap22_rank=rank))
    return tuple(eligible)


def snapshot_identity_key(artifact: MembershipContextArtifactV1) -> tuple[str, str]:
    identity = artifact.temporal_identity
    return (identity.cap22_ranking_snapshot_id, identity.cap22_integrity_digest)


def provenance_identity_key(provenance: Cap22ProvenanceV1) -> tuple[str, str]:
    return (provenance.ranking_snapshot_id, provenance.ranking_integrity_digest)


def load_observation_chain_v1(
    prior: MembershipContextArtifactV1,
    *,
    store_root: Path,
) -> tuple[MembershipContextArtifactV1, ...]:
    chain = [prior]
    seen = {prior.instance_id}
    current = prior
    while current.prior_membership_reference is not None:
        parent = read_membership_context_artifact_v1(
            current.prior_membership_reference, store_root=store_root
        )
        if parent.instance_id in seen:
            raise MfSelectorError("OBSERVATION_CHAIN_CYCLE", parent.instance_id)
        seen.add(parent.instance_id)
        chain.append(parent)
        current = parent
        if current.bootstrap:
            break
    chain.reverse()
    if chain[-1].instance_id != prior.instance_id:
        raise MfSelectorError("OBSERVATION_CHAIN_INVALID", prior.instance_id)
    return tuple(chain)


def derive_holding_ages_v1(
    chain: Sequence[MembershipContextArtifactV1],
) -> dict[str, int]:
    if not chain:
        raise MfSelectorError("OBSERVATION_STATE_MISSING", "empty_chain")
    ages: dict[str, int] = {}
    seen_keys: list[tuple[str, str]] = []
    previous_event_time: Optional[str] = None
    for artifact in chain:
        key = snapshot_identity_key(artifact)
        event_time = artifact.temporal_identity.cap22_event_time
        if previous_event_time is not None and event_time < previous_event_time:
            raise MfSelectorError("TEMPORAL_REGRESSION", event_time)
        previous_event_time = event_time
        if seen_keys and key == seen_keys[-1]:
            continue
        if key in seen_keys:
            raise MfSelectorError("NON_MONOTONIC_SNAPSHOT", key[0])
        seen_keys.append(key)
        members = set(artifact.ordered_instrument_ids)
        next_ages = {member: ages.get(member, 0) + 1 for member in members}
        ages = next_ages
    return dict(ages)


def _trace(step: str, **fields: Any) -> dict[str, Any]:
    payload = {"step": step}
    payload.update(fields)
    return payload


def _order_by_cap22(
    membership: Sequence[str],
    eligible: Sequence[EligibleCandidateV1],
) -> tuple[str, ...]:
    allowed = set(membership)
    ordered = tuple(item.instrument_id for item in eligible if item.instrument_id in allowed)
    if len(ordered) != len(allowed):
        raise MfSelectorError(
            "SELECTOR_INVENTED_INSTRUMENT", ",".join(sorted(allowed - set(ordered)))
        )
    return ordered


def evaluate_policy_a_v1(
    *,
    eligible: Sequence[EligibleCandidateV1],
    prior_membership: Sequence[str],
    holding_ages: Mapping[str, int],
) -> tuple[tuple[str, ...], tuple[dict[str, Any], ...]]:
    if len(eligible) != len({item.instrument_id for item in eligible}):
        raise MfSelectorError("DUPLICATE_CAP22_INPUT", "eligible")
    rank_of = {item.instrument_id: item.cap22_rank for item in eligible}
    eligible_set = set(rank_of)
    trace: list[dict[str, Any]] = [
        _trace("FAIL_CLOSED_INPUT_VALIDATION", eligible_count=len(eligible))
    ]

    remaining = [item for item in prior_membership if item in eligible_set]
    forced_exited = [item for item in prior_membership if item not in eligible_set]
    remaining_set = set(remaining)
    trace.append(
        _trace(
            "FORCED_REMOVAL",
            remaining=list(remaining),
            exited=list(forced_exited),
        )
    )

    underfilled: list[str] = []
    if len(remaining) < N_VALUE:
        for item in eligible:
            if item.instrument_id in remaining_set:
                continue
            underfilled.append(item.instrument_id)
            remaining.append(item.instrument_id)
            remaining_set.add(item.instrument_id)
            if len(remaining) >= N_VALUE:
                break
    trace.append(
        _trace(
            "CARDINALITY_CEILING_AND_UNDERFILL",
            underfilled=list(underfilled),
            size=len(remaining),
        )
    )

    working = list(remaining)
    working_set = set(working)
    replacements: list[dict[str, Any]] = []

    while len(working) >= N_VALUE:
        unprotected = [
            member
            for member in working
            if int(holding_ages.get(member, 0)) >= MINIMUM_HOLDING_VALUE
        ]
        challengers = [item for item in eligible if item.instrument_id not in working_set]
        if not unprotected or not challengers:
            break
        chosen: Optional[tuple[EligibleCandidateV1, str]] = None
        for challenger in challengers:
            beatable = [
                incumbent
                for incumbent in unprotected
                if incumbent in rank_of
                and challenger.cap22_rank <= rank_of[incumbent] - CHALLENGER_MARGIN_VALUE
            ]
            if not beatable:
                continue
            displaced = max(beatable, key=lambda incumbent: rank_of[incumbent])
            chosen = (challenger, displaced)
            break
        if chosen is None:
            break
        challenger, displaced = chosen
        working.remove(displaced)
        working_set.remove(displaced)
        working.append(challenger.instrument_id)
        working_set.add(challenger.instrument_id)
        replacements.append(
            {
                "challenger": challenger.instrument_id,
                "displaced": displaced,
                "challenger_rank": challenger.cap22_rank,
                "incumbent_rank": rank_of[displaced],
                "rank_improvement": rank_of[displaced] - challenger.cap22_rank,
            }
        )
        if not MULTIPLE_REPLACEMENTS_PER_CYCLE:
            break

    trace.append(_trace("MINIMUM_HOLDING", ages=dict(holding_ages)))
    trace.append(_trace("CHALLENGER_QUALIFICATION_AND_RANK_HYSTERESIS", replacements=replacements))
    trace.append(
        _trace(
            "CONSECUTIVE_CONFIRMATION",
            count=CONSECUTIVE_CONFIRMATION_COUNT,
            applied_immediately=True,
        )
    )
    final = _order_by_cap22(working, eligible)
    if len(final) > N_VALUE:
        raise MfSelectorError("CARDINALITY_EXCEEDS_N", str(len(final)))
    trace.append(_trace("FINAL_MEMBERSHIP", ordered=list(final)))
    return final, tuple(trace)


def select_membership_v1(
    *,
    eligible: Sequence[EligibleCandidateV1],
    cap22_provenance: Cap22ProvenanceV1,
    prior: MembershipContextArtifactV1,
    observation_chain: Sequence[MembershipContextArtifactV1],
) -> MfSelectorResultV1:
    if not observation_chain or observation_chain[-1].instance_id != prior.instance_id:
        raise MfSelectorError("OBSERVATION_STATE_MISSING", "prior_not_chain_tip")
    if cap22_provenance.snapshot_state != SNAPSHOT_STATE_VALID:
        raise MfSelectorError("INVALID_PROVENANCE", cap22_provenance.snapshot_state)
    if cap22_provenance.top20_candidate_context_limit != CAP22_TOP20_LIMIT:
        raise MfSelectorError("INVALID_PROVENANCE", "top20_limit")
    if not prior.instance_id:
        raise MfSelectorError("MALFORMED_PRIOR_REFERENCE", "empty")

    current_key = provenance_identity_key(cap22_provenance)
    prior_key = snapshot_identity_key(prior)
    if (
        cap22_provenance.ranking_snapshot_id == prior.temporal_identity.cap22_ranking_snapshot_id
        and cap22_provenance.ranking_integrity_digest
        != prior.temporal_identity.cap22_integrity_digest
    ):
        raise MfSelectorError("MALFORMED_SNAPSHOT_IDENTITY", cap22_provenance.ranking_snapshot_id)
    if cap22_provenance.ranking_event_time < prior.temporal_identity.cap22_event_time:
        raise MfSelectorError("TEMPORAL_REGRESSION", cap22_provenance.ranking_event_time)

    holding_ages = derive_holding_ages_v1(observation_chain)
    if current_key == prior_key:
        replay_delta = derive_rotation_delta_v1(prior, prior)
        return MfSelectorResultV1(
            ordered_membership=tuple(prior.ordered_instrument_ids),
            decision_status=STATUS_UNCHANGED_REPLAY,
            policy_trace=(_trace("REPLAYED_SNAPSHOT", snapshot_id=current_key[0]),),
            prior_instance_reference=prior.instance_id,
            current_cap22_provenance=cap22_provenance,
            rotation_delta=replay_delta,
            write_policy=NO_NEW_INSTANCE,
            holding_ages=holding_ages,
            proposed_artifact=None,
            persisted_artifact=None,
        )

    ordered, trace = evaluate_policy_a_v1(
        eligible=eligible,
        prior_membership=prior.ordered_instrument_ids,
        holding_ages=holding_ages,
    )
    proposed = build_membership_context_artifact_v1(
        ordered_instrument_ids=ordered,
        cap22_provenance=cap22_provenance,
        bootstrap=False,
        prior_membership_reference=prior.instance_id,
    )
    rotation = derive_rotation_delta_v1(proposed, prior)
    unchanged = list(ordered) == list(prior.ordered_instrument_ids)
    status = STATUS_UNCHANGED_NEW_OBSERVATION if unchanged else STATUS_CHANGED
    return MfSelectorResultV1(
        ordered_membership=ordered,
        decision_status=status,
        policy_trace=trace,
        prior_instance_reference=prior.instance_id,
        current_cap22_provenance=cap22_provenance,
        rotation_delta=rotation,
        write_policy=WRITE_NEW_OBSERVATION_INSTANCE,
        holding_ages=holding_ages,
        proposed_artifact=proposed,
        persisted_artifact=None,
    )


def persist_selector_result_v1(
    result: MfSelectorResultV1,
    *,
    store_root: Path,
) -> MfSelectorResultV1:
    if result.write_policy == NO_NEW_INSTANCE:
        return result
    if result.proposed_artifact is None:
        raise MfSelectorError("WRITE_WITHOUT_PROPOSED_ARTIFACT", result.decision_status)
    if "rotation_deltas" in result.proposed_artifact.to_dict():
        raise MfSelectorError("ROTATION_DELTAS_CANONICAL_FORBIDDEN", "persist")
    written = write_membership_context_artifact_v1(result.proposed_artifact, store_root=store_root)
    readback = read_membership_context_artifact_v1(written.instance_id, store_root=store_root)
    if readback.to_dict() != written.to_dict():
        raise MfSelectorError("READBACK_MISMATCH", written.instance_id)
    return MfSelectorResultV1(
        ordered_membership=result.ordered_membership,
        decision_status=result.decision_status,
        policy_trace=result.policy_trace,
        prior_instance_reference=result.prior_instance_reference,
        current_cap22_provenance=result.current_cap22_provenance,
        rotation_delta=result.rotation_delta,
        write_policy=result.write_policy,
        holding_ages=result.holding_ages,
        proposed_artifact=result.proposed_artifact,
        persisted_artifact=readback,
    )


def run_isolated_selector_cycle_v1(
    *,
    snapshot: Mapping[str, Any],
    cap22_provenance: Cap22ProvenanceV1,
    prior: MembershipContextArtifactV1,
    store_root: Path,
    persist: bool,
) -> MfSelectorResultV1:
    eligible = parse_eligible_cap22_top20(snapshot)
    chain = load_observation_chain_v1(prior, store_root=store_root)
    result = select_membership_v1(
        eligible=eligible,
        cap22_provenance=cap22_provenance,
        prior=prior,
        observation_chain=chain,
    )
    if persist:
        return persist_selector_result_v1(result, store_root=store_root)
    return result
