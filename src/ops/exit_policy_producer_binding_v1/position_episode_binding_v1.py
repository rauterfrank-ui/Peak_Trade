"""Identity-scoped position episodes around the existing exit-state owner.

The caller supplies observed entry anchors. No mark/decision time is substituted
for an unknown entry. This port grants no fill, order or position authority.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path

from src.ops.exit_policy_producer_binding_v1.host_binding_v1 import (
    HostExitPolicyBindingV1,
    commit_host_exit_policy_state_v1,
    ensure_host_exit_policy_binding_v1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS,
)
from src.ops.exit_policy_producer_binding_v1.persistence_v1 import load_exit_policy_state_v1

IDENTITY_FILENAME = "position_episode_identity_v1.json"


def _text(value, name):
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("POSITION_EPISODE_INVALID:" + name)


def _anchor(value, name):
    if value is not None and (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError("POSITION_EPISODE_INVALID:" + name)


@dataclass(frozen=True)
class PositionEpisodeScopeV1:
    account_identity: str
    execution_environment: str

    def validate_v1(self):
        _text(self.account_identity, "account_identity")
        _text(self.execution_environment, "execution_environment")
        if self.execution_environment not in {
            "SHADOW",
            "INTERNAL_SIMULATED_EXECUTION",
            "PAPER_EXCHANGE",
            "TESTNET",
            "LIVE",
        }:
            raise ValueError("POSITION_EPISODE_INVALID:execution_environment")


@dataclass(frozen=True)
class PositionEpisodeIdentityV1:
    lane_id: str
    instrument_id: str
    venue_native_id: str
    episode_id: str
    position_side: str
    account_scope: PositionEpisodeScopeV1

    def validate_v1(self):
        for name in ("lane_id", "instrument_id", "venue_native_id", "episode_id", "position_side"):
            _text(getattr(self, name), name)
        if not isinstance(self.account_scope, PositionEpisodeScopeV1):
            raise ValueError("POSITION_EPISODE_INVALID:account_scope")
        self.account_scope.validate_v1()
        if self.position_side not in {"long", "short"}:
            raise ValueError("POSITION_EPISODE_INVALID:position_side")


@dataclass
class PositionEpisodeBindingV1:
    identity: PositionEpisodeIdentityV1
    binding: HostExitPolicyBindingV1
    entry_source_ref: str | None
    entry_price_basis: str | None

    def input_binding_v1(self):
        payload = {
            "schema": "position_episode_input_binding.v1",
            "identity": asdict(self.identity),
            "entry_source_ref": self.entry_source_ref,
            "entry_price_basis": self.entry_price_basis,
            "prior_exit_state_digest": self.binding.to_canonical_state().digest(),
        }
        if self.binding.simulated_accounting_progress is not None:
            payload["current_entry_source_ref"] = self.binding.simulated_accounting_progress[
                "current_source_ref"
            ]
        return payload

    def prepare_for_cycle_v1(
        self,
        *,
        instrument_id,
        venue_native_id,
        position_side,
        venue_flat,
        event_time,
        lane_id=None,
        expected_scope=None,
    ):
        self.identity.validate_v1()
        if (
            not isinstance(expected_scope, PositionEpisodeScopeV1)
            or expected_scope != self.identity.account_scope
        ):
            raise ValueError("POSITION_EPISODE_ACCOUNT_SCOPE_MISMATCH")
        expected_scope.validate_v1()
        if (
            instrument_id != self.identity.instrument_id
            or venue_native_id != self.identity.venue_native_id
            or (lane_id is not None and lane_id != self.identity.lane_id)
            or position_side != self.identity.position_side
            or venue_flat is not False
        ):
            raise ValueError("POSITION_EPISODE_CYCLE_IDENTITY_MISMATCH")
        if not self.binding.initialized or self.binding.alpha_blocked:
            raise ValueError("POSITION_EPISODE_EXIT_BINDING_BLOCKED")
        if self.binding.instrument_id != instrument_id:
            raise ValueError("POSITION_EPISODE_EXIT_INSTRUMENT_MISMATCH")
        if self.binding.time_exit_max_hold_seconds != CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS:
            raise ValueError("POSITION_EPISODE_TIME_POLICY_MISMATCH")
        if (
            not self.binding.has_open_position
            or self.binding.existing_position_side != position_side
        ):
            raise ValueError("POSITION_EPISODE_OPEN_POSITION_MISMATCH")
        _anchor(event_time, "event_time")
        if self.binding.entry_event_time is not None and self.binding.entry_event_time > event_time:
            raise ValueError("POSITION_EPISODE_ENTRY_AFTER_OBSERVATION")
        if self.binding.simulated_accounting_progress is not None:
            from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import (
                verify_simulated_accounting_progress_v1,
            )

            progress = verify_simulated_accounting_progress_v1(self)
            if event_time < progress["latest_economic_event_time"]:
                raise ValueError("SIMULATED_ENTRY_PROGRESS_AFTER_OBSERVATION")
        elif isinstance(self.entry_source_ref, str) and self.entry_source_ref.startswith(
            "simulated_accounting_entry_source.v1:"
        ):
            from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import (
                _source,
            )
            from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
                latest_economic_event_time_v1,
            )

            payload, _ = _source(self.entry_source_ref, self.identity)
            if payload["accounting_checkpoint"]["funding_events"] and (
                event_time < latest_economic_event_time_v1(payload)
            ):
                raise ValueError("SIMULATED_ENTRY_FUNDING_AFTER_OBSERVATION")
        # Stage evaluation: failed/blocked replay cannot alter committed episode state.
        return deepcopy(self.binding)

    def commit_evaluated_v1(self, evaluated, *, writer_session_id):
        if not self.binding.state_root or evaluated.state_root != self.binding.state_root:
            raise ValueError("POSITION_EPISODE_EXIT_ROOT_MISMATCH")
        if evaluated.commit_sequence != self.binding.commit_sequence:
            raise ValueError("POSITION_EPISODE_COMMIT_GENERATION_MISMATCH")
        for field in (
            "instrument_id",
            "repository_sha",
            "config_digest",
            "has_open_position",
            "existing_position_side",
            "entry_price",
            "entry_event_time",
            "entry_trading_epoch",
            "time_exit_max_hold_seconds",
            "simulated_accounting_progress",
            "simulated_accounting_close",
        ):
            if getattr(evaluated, field) != getattr(self.binding, field):
                raise ValueError("POSITION_EPISODE_IMMUTABLE_CONTEXT_MISMATCH:" + field)
        return self._persist_checked_generation_v1(evaluated, writer_session_id=writer_session_id)

    def _persist_checked_generation_v1(self, evaluated, *, writer_session_id):
        """Shared original-owner CAS/readback; caller verifies its transition semantics."""
        if (
            not self.binding.state_root
            or self.binding.alpha_blocked
            or evaluated.state_root != self.binding.state_root
            or evaluated.commit_sequence != self.binding.commit_sequence
        ):
            raise ValueError("POSITION_EPISODE_COMMIT_CONTEXT_MISMATCH")
        try:
            receipt = commit_host_exit_policy_state_v1(
                evaluated,
                persist=True,
                writer_session_id=writer_session_id,
                expected_prior_sequence=self.binding.commit_sequence,
            )
            readback = load_exit_policy_state_v1(
                Path(evaluated.state_root),
                expected_repository_sha=evaluated.repository_sha,
                expected_config_digest=evaluated.config_digest,
                expected_instrument_id=self.identity.instrument_id,
            )
            if readback.to_dict() != evaluated.to_canonical_state().to_dict():
                raise ValueError("POSITION_EPISODE_COMMIT_READBACK_MISMATCH")
        except Exception:
            self.binding.alpha_blocked = True
            self.binding.alpha_block_reason = "POSITION_EPISODE_COMMIT_FAILED"
            raise
        self.binding.__dict__.update(deepcopy(evaluated.__dict__))
        return receipt


def open_position_episode_binding_v1(
    *,
    identity: PositionEpisodeIdentityV1,
    state_root: Path,
    mode: str,
    repository_sha: str,
    config_digest: str,
    writer_session_id: str,
    entry_source_ref: str | None = None,
    entry_price_basis: str | None = None,
    entry_price: float | None = None,
    entry_event_time: float | None = None,
    entry_trading_epoch: int | None = None,
) -> PositionEpisodeBindingV1:
    """Explicit create/recover; existing/partial roots are never empty-created."""
    identity.validate_v1()
    for name, value in (
        ("repository_sha", repository_sha),
        ("config_digest", config_digest),
        ("writer_session_id", writer_session_id),
    ):
        _text(value, name)
    root = Path(state_root)
    if not root.is_absolute() or mode not in {"create", "recover"}:
        raise ValueError("POSITION_EPISODE_EXPLICIT_ROOT_AND_MODE_REQUIRED")
    for name, value in (("entry_price", entry_price), ("entry_event_time", entry_event_time)):
        _anchor(value, name)
    if entry_trading_epoch is not None and (
        type(entry_trading_epoch) is not int or entry_trading_epoch < 0
    ):
        raise ValueError("POSITION_EPISODE_INVALID:entry_trading_epoch")
    known = any(v is not None for v in (entry_price, entry_event_time, entry_trading_epoch))
    if mode == "recover" and known:
        raise ValueError("POSITION_EPISODE_RECOVER_CANNOT_REPLACE_ENTRY_ANCHORS")
    if known or entry_source_ref is not None:
        _text(entry_source_ref, "entry_source_ref")
    if (
        mode == "create"
        and entry_price is not None
        and entry_price_basis != "CONFIRMED_POSITION_ENTRY_PRICE"
    ):
        raise ValueError("POSITION_EPISODE_ENTRY_PRICE_BASIS_UNPROVEN")
    if mode == "create":
        # Exclusive directory creation also fences a partial previous bootstrap.
        root.mkdir(parents=True, exist_ok=False)
        payload = {
            "schema": "position_episode_identity.v1",
            "identity": asdict(identity),
            "entry_source_ref": entry_source_ref,
            "entry_price_basis": entry_price_basis,
        }
        record = {**payload, "content_digest": canonical_digest_v1(payload)}
        with (root / IDENTITY_FILENAME).open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    else:
        try:
            record = json.loads((root / IDENTITY_FILENAME).read_text(encoding="utf-8"))
            payload = {
                key: record[key]
                for key in ("schema", "identity", "entry_source_ref", "entry_price_basis")
            }
            if (
                set(record) != {*payload, "content_digest"}
                or payload["schema"] != "position_episode_identity.v1"
                or payload["identity"] != asdict(identity)
                or record["content_digest"] != canonical_digest_v1(payload)
                or (
                    entry_source_ref is not None and payload["entry_source_ref"] != entry_source_ref
                )
                or (
                    entry_price_basis is not None
                    and payload["entry_price_basis"] != entry_price_basis
                )
            ):
                raise ValueError("identity")
            entry_source_ref = payload["entry_source_ref"]
            entry_price_basis = payload["entry_price_basis"]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise ValueError("POSITION_EPISODE_RESTORE_IDENTITY_UNPROVEN") from exc
        # Require complete existing owner state, even when a commit marker is absent.
        load_exit_policy_state_v1(
            root,
            expected_repository_sha=repository_sha,
            expected_config_digest=config_digest,
            expected_instrument_id=identity.instrument_id,
        )
    binding = ensure_host_exit_policy_binding_v1(
        HostExitPolicyBindingV1(),
        instrument_id=identity.instrument_id,
        repository_sha=repository_sha,
        config_digest=config_digest,
        state_root=root,
    )
    if mode == "create":
        binding.has_open_position = True
        binding.existing_position_side = identity.position_side
        binding.entry_price, binding.entry_event_time = entry_price, entry_event_time
        binding.entry_trading_epoch = entry_trading_epoch
        commit_host_exit_policy_state_v1(
            binding,
            persist=True,
            writer_session_id=writer_session_id,
            expected_prior_sequence=-1,
        )
    if not binding.has_open_position or binding.existing_position_side != identity.position_side:
        raise ValueError("POSITION_EPISODE_RESTORE_POSITION_MISMATCH")
    for name in ("entry_price", "entry_event_time"):
        _anchor(getattr(binding, name), name)
    if binding.entry_price is not None and entry_price_basis != "CONFIRMED_POSITION_ENTRY_PRICE":
        raise ValueError("POSITION_EPISODE_ENTRY_PRICE_BASIS_UNPROVEN")
    if any(
        getattr(binding, name) is not None
        for name in ("entry_price", "entry_event_time", "entry_trading_epoch")
    ):
        _text(entry_source_ref, "entry_source_ref")
    return PositionEpisodeBindingV1(identity, binding, entry_source_ref, entry_price_basis)
