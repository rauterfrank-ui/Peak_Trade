"""Durable observations of a single Shadow account before its first normalized mark."""

from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
import json
from math import isfinite
import os

from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    canonical_bytes_v1,
    durable_bytes_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CAPABILITY_ID,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_lock_v1 import (
    SessionLockError,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.wallclock_evidence_v1 import (
    WallclockEvidenceError,
)
from src.ops.ranked_shadow_entry_selection_v1 import ranked_shadow_positions_from_snapshot_v1
from src.ops.ranked_shadow_slot4_rotation_v1 import read_slot4_session_origin_v1
from src.trading.master_v2.double_play_entry_exit_policy_v0 import PositionState

CHECKPOINT = "slot4_shadow_pre_tick_v1.json"
SCHEMA = "SHADOW_SLOT4_PRE_TICK_OBSERVATION_V1"


def _origin(root, session):
    hashes = {}

    def original(name):
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("SHADOW_SLOT4_CHECKPOINT_ORIGIN_UNPROVEN")
        raw = path.read_bytes()
        hashes[name] = sha256(raw).hexdigest()
        return raw

    revision = read_slot4_session_origin_v1(original, session)
    return dict(repository_sha=revision, originals=hashes)


class Slot4PreTickCheckpointV1:
    """The session lock serializes writes. A mutation is marked before its in-memory effect."""

    def __init__(self, runtime, slot, state):
        self.runtime = runtime
        self.slot = slot
        self.state = state
        self.path = runtime.evidence_root / CHECKPOINT
        self.session = runtime.session_id
        self.assignment = slot.reference()
        if (
            not runtime.consumed
            or not self.session
            or state.session_id != self.session
            or slot.lane_id != "LANE_4"
            or state.instrument_id != slot.instrument.canonical_instrument_id
            or state.venue_instrument_id != slot.instrument.venue_native_inst_id
            or not self.assignment["transition_id"]
            or not self.assignment["selection_digest"]
            or runtime.sequence
            or runtime.accepted_ticks
            or state.cycle_index
        ):
            raise ValueError("SHADOW_SLOT4_CHECKPOINT_SCOPE_MISMATCH")
        self.origin = _origin(runtime.evidence_root, self.session)
        self.last = None
        self.digest = None
        self.phase = None
        self._write("OBSERVED", "ACCOUNT_INITIALIZED", self._observe())

    def _observe(self):
        state = self.state
        now = self.runtime.clock_wall()
        if not isfinite(now) or now <= 0:
            raise ValueError("SHADOW_SLOT4_CHECKPOINT_CLOCK_INVALID")
        economic = state.portfolio.snapshot()
        portfolio = ranked_shadow_positions_from_snapshot_v1(
            economic, self.slot, session_id=self.session, now=now
        )
        budget = state.ranked_confirmed_entry_budget
        if budget is not None:
            self._require_budget_scope(budget)
        # A pre-tick account cannot have booked a cycle. Any unexplained activity
        # makes absence of pending work unknown; keep the original position and budget.
        clean = not (
            state.cycle_index
            or state.cycle_ledger
            or state.fill_ledger
            or economic["applied_intent_ids"]
            or economic["applied_fill_ids"]
            or economic["state"]["intended_action_count"]
            or economic["state"]["fill_count"]
        )
        pending = state.position_state in {
            PositionState.SUBMISSION_UNKNOWN,
            PositionState.EXIT_PENDING,
            PositionState.REDUCING_PARTIAL,
        }
        uncertain = (
            not clean
            or self.runtime._post_reconnect_reconciliation_required
            or state.position_state is PositionState.RECONCILIATION_REQUIRED
        )
        return dict(
            observed_at_unix=now,
            economic=economic,
            positions_native_contracts=[p.to_dict() for p in portfolio.positions],
            position_source=portfolio.source_id,
            bridge_venue_flat=state.venue_flat,
            bridge_position_state=state.position_state.value,
            confirmed_entry_budget=deepcopy(budget),
            pending_pre_external_custody=(budget is not None) if clean else None,
            pending_external_custody=True if pending else (None if uncertain else False),
            reconnect_reconciliation_pending=self.runtime._post_reconnect_reconciliation_required,
            killstate=self.runtime.killstate.to_dict(),
            bridge_killstate_active=state.killstate_active,
        )

    def _write(self, phase, event, observation, *, proposed_budget=None):
        lock = self.runtime.lock
        if (
            lock is None
            or lock.session_id != self.session
            or lock.owner != CAPABILITY_ID
            or lock.lock_path != self.path.parent / "session.lock"
        ):
            raise WallclockEvidenceError("SHADOW_SLOT4_CHECKPOINT_WRITER_MISMATCH")
        record = dict(
            schema=SCHEMA,
            session_id=self.session,
            assignment=self.assignment,
            origin=self.origin,
            phase=phase,
            event=event,
            last_observation=observation,
            proposed_budget_binding=proposed_budget,
        )
        raw = canonical_bytes_v1(dict(record=record, sha256=canonical_digest_v1(record)))
        try:
            lock.assert_held()
            if not os.path.samestat(os.fstat(lock.fd), lock.lock_path.lstat()):
                raise WallclockEvidenceError("SHADOW_SLOT4_CHECKPOINT_LOCK_CHANGED")
            if (
                self.path.is_symlink()
                or self.path.parent.is_symlink()
                or (
                    (sha256(self.path.read_bytes()).hexdigest() if self.path.exists() else None)
                    != self.digest
                )
            ):
                raise WallclockEvidenceError("SHADOW_SLOT4_CHECKPOINT_CHANGED")
            durable_bytes_v1(self.path, raw)
        except (OSError, SessionLockError) as exc:
            raise WallclockEvidenceError("SHADOW_SLOT4_CHECKPOINT_WRITE_FAILED") from exc
        self.digest = sha256(raw).hexdigest()
        self.runtime.writer.digests[CHECKPOINT] = self.digest
        self.phase, self.event, self.last = phase, event, observation

    def begin(self, event, *, proposed_budget=None):
        if self.phase != "OBSERVED":
            raise WallclockEvidenceError("SHADOW_SLOT4_CHECKPOINT_TRANSITION_INCOMPLETE")
        if proposed_budget is not None:
            self._require_budget_scope(proposed_budget)
        self._write("CHANGE_PENDING", event, self.last, proposed_budget=proposed_budget)

    def _require_budget_scope(self, budget):
        if (
            budget.get("session_id") != self.session
            or budget.get("n5_assignment") != self.assignment
            or not budget.get("decision_id")
        ):
            raise ValueError("SHADOW_SLOT4_CHECKPOINT_BUDGET_SCOPE_MISMATCH")

    def finish(self, event):
        if self.phase != "CHANGE_PENDING" or self.event != event:
            raise WallclockEvidenceError("SHADOW_SLOT4_CHECKPOINT_TRANSITION_MISMATCH")
        self._write("OBSERVED", event, self._observe())

    @contextmanager
    def changing(self, event, *, proposed_budget=None):
        self.begin(event, proposed_budget=proposed_budget)
        yield
        self.finish(event)

    def first_mark(self):
        if self.phase != "OBSERVED":
            raise WallclockEvidenceError("SHADOW_SLOT4_CHECKPOINT_TRANSITION_INCOMPLETE")
        self._write("FIRST_MARK", "FIRST_MARK", self.last)
        self.state.slot4_pre_tick_checkpoint = None


def read_slot4_pre_tick_checkpoint_v1(root, slot, session, *, expected_sha=None):
    """Return an as-of observation only. No field is a current COMMIT input."""
    path = root / CHECKPOINT
    if root.is_symlink() or path.is_symlink() or not path.is_file():
        raise ValueError("SHADOW_SLOT4_CHECKPOINT_REQUIRED")
    raw = path.read_bytes()
    envelope = json.loads(raw)
    record = envelope["record"]
    # The first checkpoint precedes the host's session manifest. Once available,
    # its generation must agree even when a process loss prevented final sealing.
    manifest = root / "session_manifest.json"
    if manifest.is_symlink():
        raise ValueError("SHADOW_SLOT4_CHECKPOINT_SCOPE_MISMATCH")
    if manifest.exists():
        identity = json.loads(manifest.read_bytes())
        if (identity.get("session_id"), identity.get("n5_assignment")) != (
            session,
            slot.reference(),
        ):
            raise ValueError("SHADOW_SLOT4_CHECKPOINT_SCOPE_MISMATCH")
    if (
        (expected_sha is not None and sha256(raw).hexdigest() != expected_sha)
        or canonical_digest_v1(record) != envelope["sha256"]
        or record["schema"] != SCHEMA
        or slot.lane_id != "LANE_4"
        or record["session_id"] != session
        or record["assignment"] != slot.reference()
        or record["origin"] != _origin(root, session)
        or record["phase"] not in {"OBSERVED", "CHANGE_PENDING", "FIRST_MARK"}
        or raw != path.read_bytes()
    ):
        raise ValueError("SHADOW_SLOT4_CHECKPOINT_INTEGRITY_OR_SCOPE_MISMATCH")
    return record
