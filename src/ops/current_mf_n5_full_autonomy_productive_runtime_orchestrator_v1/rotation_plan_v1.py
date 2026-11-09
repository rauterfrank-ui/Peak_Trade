"""One durable pending rotation under the existing topology writer lock.

This journal reserves a candidate/slot, not capital or order authority. Original
membership, Exit, reconciliation, budget and generation owners retain their jobs.
"""

from dataclasses import asdict, replace
import json
from pathlib import Path
from types import SimpleNamespace

from .post_close_continuation_v1 import _digest, _write_receipt
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    checkpoint_root_for,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_rotation_close_v1 import (
    ROTATION_OBSERVATION_SECONDS_V1,
    RotationCloseRequestV1,
    RotationEntryHoldV1,
    RotationJournalEntryHoldV1,
    initial_rotation_identity_v1,
    assess_rotation_close_v1,
    bind_rotation_close_slot_scope_v1,
    nominate_rotation_v1,
    verify_rotation_nomination_v1,
    with_rotation_nomination_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

SCHEMA = "single_pending_slot_rotation.v1"


def _read(path):
    raw = json.loads(path.read_text())
    if type(raw) is not dict:
        raise ValueError("ROTATION_PLAN_JOURNAL_OBJECT_REQUIRED")
    body = {k: v for k, v in raw.items() if k != "content_digest"}
    if raw.get("content_digest") != _digest(body):
        raise ValueError("ROTATION_PLAN_JOURNAL_INTEGRITY_INVALID")
    return raw


class SlotRotationPlanOwnerV1:
    def __init__(self, *, topology_root, writer):
        writer.assert_held()
        self.root = checkpoint_root_for(topology_root)
        if Path(writer.state_root).resolve() != self.root.resolve():
            raise ValueError("ROTATION_PLAN_WRITER_SCOPE_MISMATCH")
        self.writer = writer
        self.path = self.root / "rotation_plan_v1.json"
        self.record = (
            _read(self.path)
            if self.path.exists()
            else dict(
                schema=SCHEMA,
                generation=0,
                active=None,
                last_terminal=None,
                runtime_authorization_effect="NONE",
            )
        )
        if (
            set(self.record) - {"content_digest"}
            != {"schema", "generation", "active", "last_terminal", "runtime_authorization_effect"}
            or self.record["schema"] != SCHEMA
            or self.record["runtime_authorization_effect"] != "NONE"
            or type(self.record["generation"]) is not int
            or self.record["generation"] < 0
        ):
            raise ValueError("ROTATION_PLAN_JOURNAL_SCHEMA_INVALID")
        terminal = self.record["last_terminal"]
        if terminal is not None and (
            type(terminal) is not dict
            or set(terminal) != {"plan_id", "status", "ranking_key"}
            or type(terminal["plan_id"]) is not str
            or not terminal["plan_id"]
            or terminal["status"]
            not in {
                "COMPLETED",
                "ROTATION_INCUMBENT_RECOVERED",
                "ROTATION_CANDIDATE_UNAVAILABLE",
            }
            or (
                terminal["ranking_key"] is not None
                and (
                    type(terminal["ranking_key"]) is not list
                    or len(terminal["ranking_key"]) != 2
                    or any(type(value) is not str or not value for value in terminal["ranking_key"])
                )
            )
        ):
            raise ValueError("ROTATION_PLAN_LAST_TERMINAL_INVALID")
        if self.active is not None:
            from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
                PositionEpisodeIdentityV1,
                PositionEpisodeScopeV1,
            )

            active = self.active
            if set(active) != {"nomination", "phase"} or active["phase"] not in {
                "WAITING",
                "CLOSE_REQUESTED",
                "AWAITING_ENTRY",
            }:
                raise ValueError("ROTATION_PLAN_PHASE_INVALID")
            source = active["nomination"]["initial_sources"]
            identity = dict(source["episode"])
            identity["account_scope"] = PositionEpisodeScopeV1(**identity["account_scope"])
            verify_rotation_nomination_v1(
                active["nomination"],
                bound=BoundInstrumentV1(**source["bound"]),
                episode_identity=PositionEpisodeIdentityV1(**identity),
            )
            archive = self.root / "rotation_history" / (active["nomination"]["plan_id"] + ".json")
            if archive.exists():
                terminal = _read(archive)
                if (
                    terminal.get("schema") != "slot_rotation_terminal.v1"
                    or terminal.get("nomination") != active["nomination"]
                    or terminal.get("status")
                    not in {
                        "COMPLETED",
                        "ROTATION_INCUMBENT_RECOVERED",
                        "ROTATION_CANDIDATE_UNAVAILABLE",
                    }
                    or terminal.get("execution_authority_effect") != "NONE"
                ):
                    raise ValueError("ROTATION_PLAN_TERMINAL_RECOVERY_INVALID")
                self.record["active"] = None
                self.record["last_terminal"] = dict(
                    plan_id=active["nomination"]["plan_id"],
                    status=terminal["status"],
                    ranking_key=terminal["ranking_key"],
                )
                self._save()

    @property
    def active(self):
        return self.record["active"]

    def status_v1(self):
        if self.active is None:
            return dict(phase="IDLE", runtime_authorization_effect="NONE")
        nomination = self.active["nomination"]
        return dict(
            phase=self.active["phase"],
            plan_id=nomination["plan_id"],
            lane_id=nomination["lane_id"],
            incumbent=nomination["incumbent"],
            candidate=nomination["candidate"],
            deadline_unix=nomination["deadline_unix"],
            runtime_authorization_effect="NONE",
        )

    def _save(self):
        self.writer.assert_held()
        if self.path.exists():
            if _read(self.path).get("generation") != self.record["generation"]:
                raise ValueError("ROTATION_PLAN_GENERATION_CONFLICT")
        elif self.record["generation"] != 0:
            raise ValueError("ROTATION_PLAN_INDEX_MISSING")
        self.record["generation"] += 1
        self.record = _write_receipt(self.path, self.record)

    def _finish(self, status, *, ranking_key=None, completion_source=None):
        nomination = self.active["nomination"]
        terminal = dict(
            schema="slot_rotation_terminal.v1",
            status=status,
            nomination=nomination,
            ranking_key=ranking_key,
            execution_authority_effect="NONE",
        )
        if completion_source is not None:
            terminal["completion_source"] = completion_source
        archive = self.root / "rotation_history" / (nomination["plan_id"] + ".json")
        if archive.exists():
            existing = _read(archive)
            if {k: v for k, v in existing.items() if k != "content_digest"} != terminal:
                raise ValueError("ROTATION_PLAN_TERMINAL_CONFLICT")
        else:
            _write_receipt(archive, terminal)
        self.record["active"] = None
        self.record["last_terminal"] = dict(
            plan_id=nomination["plan_id"], status=status, ranking_key=ranking_key
        )
        self._save()

    def constrain_post_close_v1(self, context, *, observed_unix):
        if context is None or self.active is None:
            return context
        nomination = self.active["nomination"]
        if context.request.ranking is None:
            raise ValueError("ROTATION_PLAN_FRESH_POST_CLOSE_RANKING_REQUIRED")
        is_target = context.request.bound_instrument.instrument_id == nomination["incumbent"]
        if (
            is_target
            and context.request.execution.source.quantity_handoff.lane_id != nomination["lane_id"]
        ):
            raise ValueError("ROTATION_PLAN_CLOSE_TARGET_SLOT_MISMATCH")
        due = observed_unix >= nomination["deadline_unix"]
        review = replace(
            context.request.ranking,
            reserved_challenger_v1=nomination["candidate"] if is_target and due else None,
            rotation_waiting_v1=not (is_target and due),
            reserved_incumbent_v1=nomination["incumbent"] if is_target and due else None,
        )
        return replace(context, request=replace(context.request, ranking=review))

    def prepare_v1(self, *, review, selections, bindings, episodes, observed_unix, portfolio):
        self.writer.assert_held()
        from src.ops.full_core_live_path_composition_root_v1.current_productive_post_close_feedback_v1 import (
            PostCloseRankingReviewRequestV1,
        )
        from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
            ProductiveFuturesRankingSnapshotV1,
        )

        if (
            type(review) is not PostCloseRankingReviewRequestV1
            or type(review.snapshot) is not ProductiveFuturesRankingSnapshotV1
        ):
            review = None
        if self.active is None:
            pending = [
                e.binding.pending_rotation_close
                for e in episodes.values()
                if e.binding.has_open_position and e.binding.pending_rotation_close is not None
            ]
            if pending:
                from src.ops.full_core_live_path_composition_root_v1.current_productive_rotation_close_v1 import (
                    verify_pending_rotation_close_v1,
                )

                if len(pending) != 1:
                    raise ValueError("ROTATION_PLAN_MULTIPLE_PENDING_CLOSES")
                receipt = verify_pending_rotation_close_v1(pending[0])
                nomination = receipt["nomination"]
                if (
                    self.record["last_terminal"] is not None
                    and self.record["last_terminal"]["plan_id"] == nomination["plan_id"]
                ):
                    raise ValueError("ROTATION_PLAN_TERMINAL_PENDING_CONFLICT")
                self.record["active"] = dict(nomination=nomination, phase="CLOSE_REQUESTED")
                self._save()
        if self.active is not None:
            nomination = self.active["nomination"]
            lane = nomination["lane_id"]
            bound, episode = bindings.get(lane), episodes.get(lane)
            if bound is None:
                raise ValueError("ROTATION_PLAN_ORIGINAL_SLOT_MISSING")
            if bound.instrument_id != nomination["incumbent"]:
                if bound.instrument_id != nomination["candidate"]:
                    raise ValueError("ROTATION_PLAN_CANDIDATE_REASSIGNED")
                if episode is not None and (
                    episode.identity.lane_id != lane
                    or episode.identity.account_scope
                    != initial_rotation_identity_v1(nomination).account_scope
                ):
                    raise ValueError("ROTATION_PLAN_SUCCESSOR_ACCOUNT_OR_SLOT_MISMATCH")
                if self.active["phase"] != "AWAITING_ENTRY":
                    self.active["phase"] = "AWAITING_ENTRY"
                    self._save()
                return {}
            if episode is not None:
                verify_rotation_nomination_v1(
                    nomination, bound=bound, episode_identity=episode.identity
                )
            if episode is not None and episode.binding.pending_rotation_close is not None:
                pending = episode.binding.pending_rotation_close
                if pending["nomination"]["plan_id"] != nomination["plan_id"]:
                    raise ValueError("ROTATION_PLAN_PENDING_CLOSE_CONFLICT")
                if self.active["phase"] != "CLOSE_REQUESTED":
                    self.active["phase"] = "CLOSE_REQUESTED"
                    self._save()
                return {}
            entry_hold = (
                {lane: RotationEntryHoldV1(json.dumps(nomination), json.dumps(bound.to_dict()))}
                if observed_unix >= nomination["deadline_unix"]
                else {}
            )
            if self.active["phase"] != "WAITING":
                return entry_hold
            if review is None:
                return entry_hold
            try:
                source_episode = episode or SimpleNamespace(
                    identity=initial_rotation_identity_v1(nomination)
                )
                request = self._request(review, selections[lane], bound, source_episode, bindings)
                request = with_rotation_nomination_v1(request, nomination)
                assessment = assess_rotation_close_v1(
                    request,
                    bound=bound,
                    episode_identity=source_episode.identity,
                    event_time=observed_unix,
                )
            except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError):
                # Unknown/stale ranking cannot cancel the lock or arm a close.
                return entry_hold
            if assessment["reason"] in {
                "ROTATION_INCUMBENT_RECOVERED",
                "ROTATION_CANDIDATE_UNAVAILABLE",
            }:
                self._finish(
                    assessment["reason"],
                    ranking_key=[
                        review.snapshot.ranking_snapshot_id,
                        review.snapshot.integrity_digest,
                    ],
                )
                return {}
            if episode is None or not episode.binding.has_open_position:
                return entry_hold
            return {lane: request} if assessment["allowed"] else {}
        if review is None:
            return {}
        key = [review.snapshot.ranking_snapshot_id, review.snapshot.integrity_digest]
        if (
            self.record["last_terminal"] is not None
            and self.record["last_terminal"]["ranking_key"] == key
        ):
            return {}
        for lane, bound in bindings.items():
            episode = episodes.get(lane)
            if episode is None or not episode.binding.has_open_position:
                continue
            try:
                request = self._request(review, selections[lane], bound, episode, bindings)
                nomination = nominate_rotation_v1(
                    request,
                    bound=bound,
                    episode_identity=episode.identity,
                    event_time=observed_unix,
                )
            except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError):
                continue
            if nomination is not None:
                self.record["active"] = dict(nomination=nomination, phase="WAITING")
                self._save()
                break
        return {}

    @staticmethod
    def _request(review, selection, bound, episode, bindings):
        return bind_rotation_close_slot_scope_v1(
            RotationCloseRequestV1.capture_v1(
                review=review, selection=selection, bound=bound, episode=episode
            ),
            bindings=bindings,
        )

    def observe_close_v1(self, episodes, *, result=None, bindings=None, portfolio=None):
        if self.active is None:
            return
        nomination = self.active["nomination"]
        episode = episodes.get(nomination["lane_id"])
        if self.active["phase"] == "AWAITING_ENTRY":
            lane = nomination["lane_id"]
            bound = None if bindings is None else bindings.get(lane)
            if episode is None or result is None or bound is None or portfolio is None:
                return
            projection = result.readiness_projections.get(lane)
            invocation = None if projection is None else projection.n1_consumer_result.s7_invocation
            if (
                invocation is not None
                and invocation.bound_instrument == bound
                and invocation.cycle_result.replay_pass == "true"
                and bound.instrument_id == nomination["candidate"]
                and episode.identity.instrument_id == bound.instrument_id
                and episode.identity.lane_id == lane
                and episode.identity.account_scope
                == initial_rotation_identity_v1(nomination).account_scope
                and episode.binding.has_open_position
                and any(
                    p.instrument_id == bound.instrument_id
                    and p.signed_quantity != 0
                    and (p.signed_quantity > 0) == (episode.identity.position_side == "long")
                    for p in portfolio.positions
                )
            ):
                self._finish(
                    "COMPLETED",
                    completion_source=dict(
                        bound=bound.to_dict(),
                        episode=episode.input_binding_v1(),
                        cycle_id=invocation.cycle_result.cycle_id,
                        core_input_digest=invocation.cycle_result.input_digest,
                        portfolio_digest=portfolio.digest(),
                    ),
                )
            return
        if self.active["phase"] != "WAITING":
            return
        pending = None if episode is None else episode.binding.pending_rotation_close
        if pending is not None and pending["nomination"]["plan_id"] == nomination["plan_id"]:
            self.active["phase"] = "CLOSE_REQUESTED"
            self._save()


class UnreadableSlotRotationPlanV1:
    """Fence new Entry/rotation while the original position owners keep working."""

    active = None

    def __init__(self, failure_digest):
        self.failure_digest = failure_digest

    def status_v1(self):
        return dict(
            phase="UNREADABLE",
            reason="ROTATION_JOURNAL_UNREADABLE",
            failure_digest=self.failure_digest,
            runtime_authorization_effect="NONE",
        )

    def constrain_post_close_v1(self, context, *, observed_unix):
        if context is None or context.request.ranking is None:
            return context
        review = replace(
            context.request.ranking,
            reserved_challenger_v1=None,
            reserved_incumbent_v1=None,
            rotation_waiting_v1=True,
        )
        return replace(context, request=replace(context.request, ranking=review))

    def prepare_v1(self, *, bindings, **kwargs):
        return {
            lane: RotationJournalEntryHoldV1(json.dumps(bound.to_dict()), self.failure_digest)
            for lane, bound in bindings.items()
        }

    def observe_close_v1(self, *args, **kwargs):
        return None


def load_slot_rotation_plan_owner_v1(*, topology_root, writer):
    # Authority/scope failures are not downgraded into a metadata diagnostic.
    writer.assert_held()
    if Path(writer.state_root).resolve() != checkpoint_root_for(topology_root).resolve():
        raise ValueError("ROTATION_PLAN_WRITER_SCOPE_MISMATCH")
    try:
        return SlotRotationPlanOwnerV1(topology_root=topology_root, writer=writer)
    except (OSError, ValueError, TypeError, KeyError, ArithmeticError) as exc:
        return UnreadableSlotRotationPlanV1(
            _digest(dict(failure=type(exc).__name__, detail=str(exc)))
        )
