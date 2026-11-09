"""Original membership proposal to a slot-bound, recoverable rotation close.

No selection commit, position replacement, capital release or external effect.
The original selector owns rank/observation hysteresis; the nomination owns its wait.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math

from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.mf_membership_context_artifact_contract_v1 import (
    Cap22ProvenanceV1,
    membership_context_artifact_from_dict,
    validate_membership_context_artifact_v1,
)
from src.ops.mf_membership_selector_and_rotation_runtime_contract_v1 import (
    parse_eligible_cap22_top20,
    select_membership_v1,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    validate_ranking_snapshot_bindings_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    DEFAULT_MAX_RANKING_AGE_SECONDS,
    DEFAULT_REFRESH_CADENCE_SECONDS,
)
from src.ops.single_selected_future_policy_v1.models_v1 import SingleSelectedFutureSelectionV1
from trading.market_state.time_sample_epoch_semantics_v1 import (
    WallclockDurationV1,
    WallclockInstantV1,
    WallclockTimeExitAnchorV1,
    wallclock_time_exit_due_v1,
)

ROTATION_OBSERVATION_SECONDS_V1 = 1800.0
# A new rotation comparison may be at most one existing ranking refresh old.
ROTATION_RANKING_MAX_AGE_SECONDS_V1 = min(
    DEFAULT_MAX_RANKING_AGE_SECONDS, DEFAULT_REFRESH_CADENCE_SECONDS
)


@dataclass(frozen=True)
class RotationEntryHoldV1:
    """Only a negative Entry constraint while the old slot awaits its handoff."""

    nomination_json: str
    bound_json: str

    def validate_v1(self, *, bound, now):
        if json.loads(self.bound_json) != bound.to_dict():
            raise ValueError("ROTATION_ENTRY_HOLD_BOUND_MISMATCH")
        nomination = json.loads(self.nomination_json)
        verify_rotation_nomination_v1(
            nomination, bound=bound, episode_identity=initial_rotation_identity_v1(nomination)
        )
        return _seconds(now) >= nomination["deadline_unix"]


@dataclass(frozen=True)
class RotationJournalEntryHoldV1:
    """Unreadable rotation metadata restricts Entry, never an existing exit."""

    bound_json: str
    failure_digest: str

    def validate_v1(self, *, bound, now):
        if json.loads(self.bound_json) != bound.to_dict():
            raise ValueError("ROTATION_JOURNAL_HOLD_BOUND_MISMATCH")
        return True


def rotation_entry_hold_digest_v1(hold):
    return canonical_digest_v1(dict(kind=type(hold).__name__, body=asdict(hold)))


def initial_rotation_identity_v1(nomination):
    from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
        PositionEpisodeIdentityV1,
        PositionEpisodeScopeV1,
    )

    raw = dict(nomination["initial_sources"]["episode"])
    raw["account_scope"] = PositionEpisodeScopeV1(**raw["account_scope"])
    return PositionEpisodeIdentityV1(**raw)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _seconds(value):
    if type(value) in (int, float) and math.isfinite(value):
        return float(value)
    raise ValueError("ROTATION_CLOSE_FINITE_CLOCK_REQUIRED")


def _event_seconds(value):
    if type(value) is not str or not value:
        raise ValueError("ROTATION_CLOSE_EVENT_CLOCK_REQUIRED")
    if value.isdigit():
        return int(value) / 1000
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("ROTATION_CLOSE_EVENT_TIMEZONE_REQUIRED")
    return parsed.astimezone(timezone.utc).timestamp()


@dataclass(frozen=True)
class RotationCloseRequestV1:
    """Immutable copies of original sources, not a caller-provided trigger."""

    sources_json: str

    @classmethod
    def capture_v1(cls, *, review, selection, bound, episode):
        from .current_productive_post_close_feedback_v1 import PostCloseRankingReviewRequestV1

        if type(review) is not PostCloseRankingReviewRequestV1:
            raise ValueError("ROTATION_CLOSE_ORIGINAL_REVIEW_REQUIRED")
        return cls(
            _canonical(
                dict(
                    schema="rotation_close_sources.v1",
                    bound=bound.to_dict(),
                    episode=asdict(episode.identity),
                    selection=selection.to_dict(),
                    ranking=review.snapshot.to_dict(),
                    provenance=review.provenance.to_dict(),
                    prior=review.prior.to_dict(),
                    observation_chain=[a.to_dict() for a in review.observation_chain],
                )
            )
        )


def bind_rotation_close_slot_scope_v1(request, *, bindings):
    """Append the actual host's retained lane bindings at the N1 handoff."""
    if type(request) is not RotationCloseRequestV1:
        return request
    raw = json.loads(request.sources_json)
    current = {lane: bound.to_dict() for lane, bound in bindings.items()}
    if "held_bound_by_lane" in raw and raw["held_bound_by_lane"] != current:
        raise ValueError("ROTATION_CLOSE_HELD_SLOT_SCOPE_MISMATCH")
    raw["held_bound_by_lane"] = current
    return RotationCloseRequestV1(_canonical(raw))


def _inspect_rotation_sources_v1(
    request,
    *,
    bound,
    episode_identity,
    event_time,
    reserved_challenger_v1=None,
    reserved_incumbent_v1=None,
):
    """Qualify the original proposal; never rescore or republish its membership."""
    if type(request) is not RotationCloseRequestV1:
        raise ValueError("ROTATION_CLOSE_TYPED_SOURCES_REQUIRED")
    raw = json.loads(request.sources_json)
    if (
        not isinstance(raw, dict)
        or set(raw) - {"nomination"}
        != {
            "schema",
            "bound",
            "episode",
            "selection",
            "ranking",
            "provenance",
            "prior",
            "observation_chain",
            "held_bound_by_lane",
        }
        or raw["schema"] != "rotation_close_sources.v1"
        or raw["bound"] != bound.to_dict()
        or raw["episode"] != asdict(episode_identity)
    ):
        raise ValueError("ROTATION_CLOSE_SLOT_OR_EPISODE_MISMATCH")
    episode_identity.validate_v1()
    if (
        bound.instrument_id != episode_identity.instrument_id
        or bound.venue_native_id != episode_identity.venue_native_id
    ):
        raise ValueError("ROTATION_CLOSE_BOUND_INSTRUMENT_MISMATCH")
    selection = SingleSelectedFutureSelectionV1.from_dict(raw["selection"])
    if (
        selection.compute_integrity_digest() != selection.integrity_digest
        or selection.integrity_digest != bound.selection_integrity_digest
        or any(
            getattr(selection, field) != getattr(bound, field)
            for field in (
                "instrument_id",
                "venue_native_id",
                "selection_id",
                "ranking_snapshot_id",
                "ranking_integrity_digest",
            )
        )
    ):
        raise ValueError("ROTATION_CLOSE_ORIGINAL_SELECTION_MISMATCH")
    ranking = ProductiveFuturesRankingSnapshotV1.from_dict(raw["ranking"])
    if not validate_ranking_snapshot_bindings_v1(ranking).ok:
        raise ValueError("ROTATION_CLOSE_RANKING_INVALID")
    now = _seconds(event_time)
    ranked_at = _event_seconds(ranking.event_time)
    selected_at = _event_seconds(selection.selected_at_event_time)
    if (
        not 0 <= now - ranked_at <= ROTATION_RANKING_MAX_AGE_SECONDS_V1
        or selected_at > now
        or ranked_at < selected_at
        or ranking.universe_snapshot_id != bound.universe_snapshot_id
    ):
        raise ValueError("ROTATION_CLOSE_RANKING_TIME_OR_UNIVERSE_INVALID")
    provenance = Cap22ProvenanceV1.from_dict(raw["provenance"])
    for key, expected in (
        ("ranking_snapshot_id", ranking.ranking_snapshot_id),
        ("ranking_integrity_digest", ranking.integrity_digest),
        ("ranking_event_time", ranking.event_time),
        ("universe_snapshot_id", ranking.universe_snapshot_id),
        ("ranking_policy_id", ranking.ranking_policy_id),
        ("ranking_policy_version", ranking.ranking_policy_version),
    ):
        if getattr(provenance, key) != expected:
            raise ValueError("ROTATION_CLOSE_PROVENANCE_MISMATCH:" + key)
    prior = membership_context_artifact_from_dict(raw["prior"])
    held = raw["held_bound_by_lane"]
    if (
        not isinstance(held, dict)
        or not 1 <= len(held) <= 5
        or held.get(episode_identity.lane_id) != bound.to_dict()
        or len({r["instrument_id"] for r in held.values()}) != len(held)
        or {r["instrument_id"] for r in held.values()} != set(prior.ordered_instrument_ids)
    ):
        raise ValueError("ROTATION_CLOSE_HELD_MEMBERSHIP_SCOPE_MISMATCH")
    chain = tuple(membership_context_artifact_from_dict(a) for a in raw["observation_chain"])
    for artifact in (prior, *chain):
        validate_membership_context_artifact_v1(artifact)
        if artifact.cap22_provenance.universe_snapshot_id != bound.universe_snapshot_id:
            raise ValueError("ROTATION_CLOSE_OBSERVATION_UNIVERSE_MISMATCH")
    if (
        not chain
        or chain[-1].to_dict() != prior.to_dict()
        or not chain[0].bootstrap
        or any(
            child.prior_membership_reference != parent.instance_id
            for parent, child in zip(chain, chain[1:])
        )
        or bound.instrument_id not in prior.ordered_instrument_ids
    ):
        raise ValueError("ROTATION_CLOSE_ORIGINAL_MEMBERSHIP_CHAIN_REQUIRED")
    proposal = select_membership_v1(
        eligible=parse_eligible_cap22_top20(ranking.to_dict()),
        cap22_provenance=provenance,
        prior=prior,
        observation_chain=chain,
        reserved_challenger_v1=reserved_challenger_v1,
        reserved_incumbent_v1=reserved_incumbent_v1,
    )
    return raw, ranking, proposal, now, selected_at


def _replacements(proposal):
    return [
        r
        for step in proposal.policy_trace
        if step["step"] == "CHALLENGER_QUALIFICATION_AND_RANK_HYSTERESIS"
        for r in step["replacements"]
    ]


def nominate_rotation_v1(request, *, bound, episode_identity, event_time):
    raw, ranking, proposal, now, _selected_at = _inspect_rotation_sources_v1(
        request,
        bound=bound,
        episode_identity=episode_identity,
        event_time=event_time,
    )
    replacements = _replacements(proposal)
    if not replacements or replacements[0]["displaced"] != bound.instrument_id:
        return None
    body = dict(
        schema="rotation_nomination.v1",
        lane_id=episode_identity.lane_id,
        incumbent=bound.instrument_id,
        candidate=replacements[0]["challenger"],
        started_at_unix=now,
        deadline_unix=now + ROTATION_OBSERVATION_SECONDS_V1,
        observation_seconds=ROTATION_OBSERVATION_SECONDS_V1,
        ranking_max_age_seconds=ROTATION_RANKING_MAX_AGE_SECONDS_V1,
        initial_sources=raw,
    )
    return {**body, "plan_id": canonical_digest_v1(body)}


def verify_rotation_nomination_v1(nomination, *, bound, episode_identity):
    if (
        not isinstance(nomination, dict)
        or set(nomination)
        != {
            "schema",
            "lane_id",
            "incumbent",
            "candidate",
            "started_at_unix",
            "deadline_unix",
            "observation_seconds",
            "ranking_max_age_seconds",
            "initial_sources",
            "plan_id",
        }
        or "nomination" in nomination["initial_sources"]
    ):
        raise ValueError("ROTATION_NOMINATION_SCHEMA_INVALID")
    from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
        PositionEpisodeIdentityV1,
        PositionEpisodeScopeV1,
    )

    initial_identity = dict(nomination["initial_sources"]["episode"])
    initial_identity["account_scope"] = PositionEpisodeScopeV1(**initial_identity["account_scope"])
    initial_identity = PositionEpisodeIdentityV1(**initial_identity)
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

    initial_bound = BoundInstrumentV1(**nomination["initial_sources"]["bound"])
    if any(
        getattr(initial_bound, field) != getattr(bound, field)
        for field in ("instrument_id", "venue_native_id", "universe_snapshot_id")
    ):
        raise ValueError("ROTATION_NOMINATION_INSTRUMENT_SCOPE_MISMATCH")
    if any(
        getattr(initial_identity, field) != getattr(episode_identity, field)
        for field in ("lane_id", "instrument_id", "venue_native_id", "account_scope")
    ):
        raise ValueError("ROTATION_NOMINATION_SLOT_SCOPE_MISMATCH")
    expected = nominate_rotation_v1(
        RotationCloseRequestV1(_canonical(nomination["initial_sources"])),
        bound=initial_bound,
        episode_identity=initial_identity,
        event_time=nomination["started_at_unix"],
    )
    if expected is None or nomination != expected:
        raise ValueError("ROTATION_NOMINATION_SOURCE_OR_POLICY_INVALID")
    return nomination


def with_rotation_nomination_v1(request, nomination):
    raw = json.loads(request.sources_json)
    raw["nomination"] = nomination
    return RotationCloseRequestV1(_canonical(raw))


def assess_rotation_close_v1(request, *, bound, episode_identity, event_time):
    nomination = (
        json.loads(request.sources_json).get("nomination")
        if type(request) is RotationCloseRequestV1
        else None
    )
    nomination = verify_rotation_nomination_v1(
        nomination, bound=bound, episode_identity=episode_identity
    )
    raw, ranking, proposal, now, selected_at = _inspect_rotation_sources_v1(
        request,
        bound=bound,
        episode_identity=episode_identity,
        event_time=event_time,
        reserved_challenger_v1=nomination["candidate"],
        reserved_incumbent_v1=nomination["incumbent"],
    )
    if now < nomination["started_at_unix"]:
        raise ValueError("ROTATION_NOMINATION_CLOCK_REGRESSION")
    initial_ranking = nomination["initial_sources"]["ranking"]
    if (
        _event_seconds(ranking.event_time) < _event_seconds(initial_ranking["event_time"])
        or ranking.ranking_snapshot_id == initial_ranking["ranking_snapshot_id"]
        and ranking.integrity_digest != initial_ranking["integrity_digest"]
    ):
        raise ValueError("ROTATION_RANKING_IDENTITY_OR_TIME_REGRESSION")
    eligible = {
        r.instrument_id: r.cap22_rank for r in parse_eligible_cap22_top20(ranking.to_dict())
    }
    incumbent_rank, candidate_rank = (
        eligible.get(bound.instrument_id),
        eligible.get(nomination["candidate"]),
    )
    recovered = (
        incumbent_rank is not None
        and candidate_rank is not None
        and incumbent_rank <= candidate_rank
    )
    candidate_unavailable = candidate_rank is None
    replacements = [
        replacement
        for step in proposal.policy_trace
        if step["step"] == "CHALLENGER_QUALIFICATION_AND_RANK_HYSTERESIS"
        for replacement in step["replacements"]
        if replacement["displaced"] == bound.instrument_id
    ]
    due = wallclock_time_exit_due_v1(
        WallclockTimeExitAnchorV1(
            opened_at_wallclock=WallclockInstantV1(unix_seconds=nomination["started_at_unix"]),
            max_hold_duration=WallclockDurationV1(seconds=ROTATION_OBSERVATION_SECONDS_V1),
        ),
        now_wallclock=WallclockInstantV1(unix_seconds=now),
    )
    allowed = due and len(replacements) == 1 and not recovered and not candidate_unavailable
    result = dict(
        schema="rotation_close_admission.v1",
        allowed=allowed,
        reason=(
            "ROTATION_INCUMBENT_RECOVERED"
            if recovered
            else "ROTATION_CANDIDATE_UNAVAILABLE"
            if candidate_unavailable
            else "ROTATION_BETTER_CANDIDATE_AFTER_WAIT"
            if allowed
            else "ROTATION_WAITING"
        ),
        sources=raw,
        event_time=now,
        selected_at_event_time=selected_at,
        minimum_holding_seconds=ROTATION_OBSERVATION_SECONDS_V1,
        nomination=nomination,
        replacement=replacements[0] if replacements else None,
        proposed_membership=list(proposal.ordered_membership),
        proposal_digest=canonical_digest_v1(proposal.proposed_artifact.to_dict())
        if proposal.proposed_artifact is not None
        else None,
        execution_authority_effect="NONE",
    )
    return {**result, "digest": canonical_digest_v1(result)}


def verify_pending_rotation_close_v1(record, *, bound=None, episode_identity=None):
    """Historical source readback preserves an already armed close, not a new Entry."""
    from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
        PositionEpisodeIdentityV1,
        PositionEpisodeScopeV1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

    if not isinstance(record, dict) or record.get("allowed") is not True:
        raise ValueError("ROTATION_CLOSE_PENDING_ADMISSION_INVALID")
    raw = record["sources"]
    stored_bound = BoundInstrumentV1(**raw["bound"])
    identity = dict(raw["episode"])
    identity["account_scope"] = PositionEpisodeScopeV1(**identity["account_scope"])
    stored_identity = PositionEpisodeIdentityV1(**identity)
    if (
        bound is not None
        and stored_bound != bound
        or episode_identity is not None
        and stored_identity != episode_identity
    ):
        raise ValueError("ROTATION_CLOSE_PENDING_IDENTITY_MISMATCH")
    rebuilt = assess_rotation_close_v1(
        RotationCloseRequestV1(_canonical(raw)),
        bound=stored_bound,
        episode_identity=stored_identity,
        event_time=record["event_time"],
    )
    if record != rebuilt:
        raise ValueError("ROTATION_CLOSE_PENDING_SOURCE_OR_RECEIPT_MISMATCH")
    return rebuilt
