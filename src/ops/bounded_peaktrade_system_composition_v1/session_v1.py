"""Bounded offline session around existing episode and N1 owners.

Cooperative leases and technical attempt limits are composition infrastructure,
not position truth, trading permission or a new financial budget owner.
"""

from copy import deepcopy
import fcntl
import json
import inspect
import math
import os
from pathlib import Path
import tempfile

from src.ops.bounded_peaktrade_system_composition_v1.manifest_v1 import (
    OfflineEpisodeSessionManifestV1,
    canonical_absolute_path_v1,
    load_offline_episode_session_manifest_v1,
    repository_source_digest_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1.cycle_namespace_v1 import (
    bind_offline_cycle_namespace_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1.configuration_v1 import (
    CONFIG_RECEIPT,
    effective_runtime_configuration_v1,
)
from src.ops.exit_policy_producer_binding_v1.current_cursor_recovery_v1 import (
    require_current_cursor_continuity_v1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    recover_position_episode_from_simulated_accounting_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    load_current_productive_sidestate_confirmation_cursor_v1,
    restore_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.hard_facts_system_closure_v1.instrument_sensitive_identity_v1 import (
    BoundInstrumentLaneIdentityV1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
    invoke_occupied_lane_governed_cycle_n1_consumer_v1,
)

RECEIPT = "offline_episode_session_state_v1.json"
MANIFEST = "offline_episode_session_manifest_v1.json"
LEASE = "offline_episode_session_v1.lock"
RESOURCE_BINDING = "offline_episode_session_binding_v1.json"
STATE_SCHEMA = "bounded_offline_episode_session_state.v2"


def _write(path, payload):
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        if json.loads(path.read_text()) != payload:
            raise ValueError("OFFLINE_SESSION_RECEIPT_READBACK_MISMATCH")
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class BoundedOfflineEpisodeSessionV1:
    def __init__(self, *, manifest, state_root, mode, data_sources=None):
        if not isinstance(manifest, OfflineEpisodeSessionManifestV1):
            raise ValueError("OFFLINE_SESSION_TYPED_MANIFEST_REQUIRED")
        manifest.validate_v1()
        canonical_absolute_path_v1(str(state_root))
        if mode not in {"create", "recover"}:
            raise ValueError("OFFLINE_SESSION_EXPLICIT_MODE_REQUIRED")
        self.manifest = manifest
        self.root = Path(state_root)
        self.mode = mode
        self._data_sources = {} if data_sources is None else dict(data_sources)
        self._fds = []
        self._active = False
        self._state = None
        self._episodes = {}
        self.last_completion_result = None
        self._process_pid = None
        for lane in manifest.lanes:
            for value in (lane.exit_state_root, lane.cursor_state_root, lane.source_path):
                path = Path(value)
                if self.root == path or self.root in path.parents or path in self.root.parents:
                    raise ValueError("OFFLINE_SESSION_ROOT_OVERLAP")

    @property
    def state(self):
        return deepcopy(self._state)

    def _load_episodes(self, *, allow_sealed=False):
        self._validate_data_profile_v1()
        configuration = effective_runtime_configuration_v1()
        configuration_path = self.root / CONFIG_RECEIPT
        if configuration_path.exists():
            if json.loads(configuration_path.read_text()) != configuration:
                raise ValueError("OFFLINE_SESSION_CONFIG_GENERATION_CHANGED")
        elif self.mode == "recover" or self._active:
            raise ValueError("OFFLINE_SESSION_CONFIG_RECEIPT_MISSING")
        if self.manifest.implementation_source_digest != repository_source_digest_v1():
            raise ValueError("OFFLINE_SESSION_IMPLEMENTATION_CHANGED")
        episodes = {}
        for lane in self.manifest.lanes:
            if not all(Path(p).is_dir() for p in (lane.exit_state_root, lane.cursor_state_root)):
                raise ValueError("OFFLINE_SESSION_EXISTING_OWNER_ROOT_REQUIRED")
            source = json.loads(Path(lane.source_path).read_text())
            if source.get("content_digest") != lane.source_content_digest:
                raise ValueError("OFFLINE_SESSION_SOURCE_BINDING_MISMATCH")
            if allow_sealed:
                from src.ops.exit_policy_producer_binding_v1.simulated_accounting_close_v1 import (
                    inspect_sealed_simulated_episode_v1,
                )
                from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
                    _ref,
                )

                inspect_sealed_simulated_episode_v1(
                    identity=lane.identity,
                    state_root=Path(lane.exit_state_root),
                    repository_sha=self.manifest.repository_sha,
                    config_digest=self.manifest.exit_policy_config_digest,
                    expected_initial_source_ref=_ref(
                        Path(lane.source_path), lane.source_content_digest
                    ),
                )
                continue
            episode = recover_position_episode_from_simulated_accounting_v1(
                identity=lane.identity,
                source_path=Path(lane.source_path),
                state_root=Path(lane.exit_state_root),
                repository_sha=self.manifest.repository_sha,
                config_digest=self.manifest.exit_policy_config_digest,
                writer_session_id=self.manifest.session_id,
            )
            cursor = load_current_productive_sidestate_confirmation_cursor_v1(
                Path(lane.cursor_state_root)
            )
            restored = restore_current_productive_sidestate_confirmation_cursor_v1(
                cursor,
                expected_instrument_id=lane.identity.instrument_id,
                expected_venue_native_id=lane.identity.venue_native_id,
                venue_flat=False,
            )
            if restored.disposition.value != "restored" or restored.cursor.existing_scope is None:
                raise ValueError("OFFLINE_SESSION_OCCUPIED_CURSOR_REQUIRED")
            require_current_cursor_continuity_v1(
                episode=episode, incoming=cursor, store_root=Path(lane.cursor_state_root)
            )
            episodes[lane.identity.lane_id] = episode
        return episodes

    def _validate_data_profile_v1(self):
        from src.ops.economic_md_input_producer_v1.purpose_consumers_v1 import (
            purpose_profile_digest_v1,
        )

        if self.manifest.data_profile_digest is None:
            if self._data_sources:
                raise ValueError("OFFLINE_SESSION_UNPINNED_DATA_PROFILE")
            return
        if purpose_profile_digest_v1(self._data_sources) != self.manifest.data_profile_digest:
            raise ValueError("OFFLINE_SESSION_DATA_PROFILE_CHANGED")
        # This bounded profile manages one episode; the general N5 slot count
        # is separate. Never pool policies for different canonical instruments.
        instruments = {lane.identity.instrument_id for lane in self.manifest.lanes}
        for source in self._data_sources.values():
            if instruments != {source.policy.canonical_instrument_id}:
                raise ValueError("OFFLINE_SESSION_DATA_PROFILE_INSTRUMENT_MISMATCH")
            for lane in self.manifest.lanes:
                for owner in (lane.cursor_state_root, lane.exit_state_root, str(self.root)):
                    if (
                        Path(source.store_root) == Path(owner)
                        or Path(owner) in Path(source.store_root).parents
                        or Path(source.store_root) in Path(owner).parents
                    ):
                        raise ValueError("OFFLINE_SESSION_DATA_STORE_INSIDE_MUTABLE_OWNER")

    def read_data_for_purpose_v1(self, *, purpose, as_of_ms, **kwargs):
        if not self._active or self._state["status"] != "READY":
            raise ValueError("OFFLINE_SESSION_DATA_REQUIRES_READY_SESSION")
        self._validate_data_profile_v1()
        if (
            type(as_of_ms) is not int
            or not self.manifest.replay_start_unix * 1000
            <= as_of_ms
            <= self.manifest.replay_stop_unix * 1000
        ):
            raise ValueError("OFFLINE_SESSION_DATA_ASOF_OUTSIDE_BOUNDS")
        if purpose not in self._data_sources:
            raise ValueError("OFFLINE_SESSION_DATA_PURPOSE_UNBOUND")
        source = self._data_sources[purpose].at_v1(as_of_ms)
        native = self.manifest.lanes[0].identity.venue_native_id
        if purpose == "RANKING":
            from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_runtime_economic_md_adapter_v1 import (
                PublicRuntimeEconomicMdPublicSourceV1,
            )

            if kwargs:
                raise ValueError("OFFLINE_SESSION_RANKING_OVERRIDE_FORBIDDEN")
            return PublicRuntimeEconomicMdPublicSourceV1(
                Path(source.store_root), source.policy, as_of_ms
            ).collect_instrument_raw_input_v1(venue_native_id=native)
        method = {
            "TRADING": source.trading_c1_v1,
            "RESEARCH": source.research_returns_v1,
            "OUTCOME": source.outcome_snapshot_v1,
            "LIQUIDITY": source.liquidity_input_v1,
        }[purpose]
        return method(native_id=native, **kwargs)

    def _resource_bindings(self, *, create=False):
        value = {
            "schema": "bounded_offline_episode_session_resource_binding.v1",
            "session_root": str(self.root),
            "manifest_digest": self.manifest.digest(),
        }
        paths = sorted(
            {
                Path(p) / RESOURCE_BINDING
                for lane in self.manifest.lanes
                for p in (lane.exit_state_root, lane.cursor_state_root)
            }
        )
        # Validate every existing registration before publishing any new one.
        for path in paths:
            if path.exists():
                if json.loads(path.read_text()) != value:
                    raise ValueError("OFFLINE_SESSION_RESOURCE_ALREADY_REGISTERED")
            elif not create:
                raise ValueError("OFFLINE_SESSION_RESOURCE_REGISTRATION_MISSING")
        if create:
            for path in paths:
                if not path.exists():
                    _write(path, value)

    def __enter__(self):
        if self._active or self._fds:
            raise ValueError("OFFLINE_SESSION_ALREADY_OPEN")
        # Validate sources/owners before creating a session directory or leases.
        allow_sealed = (
            self.mode == "recover"
            and (self.root / RECEIPT).is_file()
            and json.loads((self.root / RECEIPT).read_text()).get("status") == "SEALED"
        )
        self._load_episodes(allow_sealed=allow_sealed)
        if self.mode == "create":
            self.root.mkdir(parents=True, exist_ok=False)
        elif not (self.root / RECEIPT).is_file() or not (self.root / MANIFEST).is_file():
            raise ValueError("OFFLINE_SESSION_REGISTERED_STATE_MISSING")
        roots = {self.root}
        roots.update(
            Path(p) for l in self.manifest.lanes for p in (l.exit_state_root, l.cursor_state_root)
        )
        try:
            for root in sorted(roots):
                fd = os.open(root / LEASE, os.O_CREAT | os.O_RDWR, 0o600)
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as exc:
                    os.close(fd)
                    raise ValueError("OFFLINE_SESSION_LEASE_CONFLICT") from exc
                self._fds.append(fd)
            self._episodes = self._load_episodes(allow_sealed=allow_sealed)
            self._resource_bindings(create=self.mode == "create")
            if self.mode == "create":
                # JSON normalize tuples before readback; manifest digest keeps its canonical domain.
                _write(self.root / MANIFEST, json.loads(json.dumps(self.manifest.to_dict())))
                _write(self.root / CONFIG_RECEIPT, effective_runtime_configuration_v1())
                self._state = {
                    "schema": STATE_SCHEMA,
                    "manifest_digest": self.manifest.digest(),
                    "attempts_used": 0,
                    "status": "READY",
                    "prefixes": [],
                    "cycle_namespaces": [],
                    "last_observed_unix": None,
                }
                _write(self.root / RECEIPT, self._state)
            else:
                stored = load_offline_episode_session_manifest_v1(self.root / MANIFEST)
                if stored.digest() != self.manifest.digest():
                    raise ValueError("OFFLINE_SESSION_MANIFEST_CHANGED")
                self._state = json.loads((self.root / RECEIPT).read_text())
                self._validate_state()
                if allow_sealed != (self._state["status"] == "SEALED"):
                    raise ValueError("OFFLINE_SESSION_SEAL_STATE_MISMATCH")
                if self._state["status"] not in {"READY", "SEALED"}:
                    raise ValueError("OFFLINE_SESSION_INTERRUPTED_ATTEMPT_REQUIRES_REVIEW")
            self._active = True
            self._process_pid = os.getpid()
            return self
        except BaseException:
            self.close()
            raise

    def _validate_state(self):
        s = self._state
        if (
            not isinstance(s, dict)
            or set(s)
            != {
                "schema",
                "manifest_digest",
                "attempts_used",
                "status",
                "prefixes",
                "cycle_namespaces",
                "last_observed_unix",
            }
            or s["schema"] != STATE_SCHEMA
            or s["manifest_digest"] != self.manifest.digest()
            or type(s["attempts_used"]) is not int
            or not 0 <= s["attempts_used"] <= self.manifest.max_attempts
            or s["status"]
            not in {
                "READY",
                "RUNNING",
                "SOURCE_UPDATE_RUNNING",
                "FLAT_SEAL_RUNNING",
                "SEALED",
                "RECOVERY_REQUIRED",
            }
            or not isinstance(s["prefixes"], list)
            or any(not isinstance(p, str) or not p or p != p.strip() for p in s["prefixes"])
            or len(s["prefixes"]) != s["attempts_used"]
            or len(set(s["prefixes"])) != len(s["prefixes"])
        ):
            raise ValueError("OFFLINE_SESSION_STATE_INVALID")
        if (
            not isinstance(s["cycle_namespaces"], list)
            or len(s["cycle_namespaces"]) != s["attempts_used"]
            or any(
                row
                != bind_offline_cycle_namespace_v1(
                    manifest=self.manifest, requested_prefix=prefix
                ).to_dict()
                for prefix, row in zip(s["prefixes"], s["cycle_namespaces"])
            )
        ):
            raise ValueError("OFFLINE_SESSION_CYCLE_NAMESPACE_INVALID")
        time = s["last_observed_unix"]
        if (s["attempts_used"] == 0 and time is not None) or (
            s["attempts_used"] > 0
            and (
                type(time) not in (int, float)
                or not math.isfinite(time)
                or not self.manifest.replay_start_unix <= time <= self.manifest.replay_stop_unix
            )
        ):
            raise ValueError("OFFLINE_SESSION_STATE_TIME_INVALID")

    def _validate_pairs(self, pairs):
        if set(pairs) != {l.identity.lane_id for l in self.manifest.lanes}:
            raise ValueError("OFFLINE_SESSION_LANE_SET_CHANGED")
        for lane in self.manifest.lanes:
            slot, bound = pairs[lane.identity.lane_id]
            actual = BoundInstrumentLaneIdentityV1.from_bound_instrument(
                lane_id=lane.identity.lane_id, bound=bound
            )
            if (
                slot.lane_id != lane.identity.lane_id
                or slot.occupancy != "OCCUPIED"
                or str(Path(slot.lane_state_root).resolve()) != lane.cursor_state_root
                or slot.canonical_instrument_id != lane.identity.instrument_id
                or slot.universe_snapshot_id != bound.universe_snapshot_id
                or slot.ranking_snapshot_id != bound.ranking_snapshot_id
                or slot.ranking_integrity_digest != bound.ranking_integrity_digest
                or bound.instrument_id != lane.identity.instrument_id
                or bound.venue_native_id != lane.identity.venue_native_id
                or actual.bound_instrument_identity != lane.bound_instrument_identity
                or actual.instrument_epoch != lane.instrument_epoch
            ):
                raise ValueError("OFFLINE_SESSION_BOUND_LANE_CHANGED")

    def run_occupied_cycle_v1(self, composed_pairs, **kwargs):
        if not self._active:
            raise ValueError("OFFLINE_SESSION_NOT_OPEN")
        if self._process_pid != os.getpid():
            raise ValueError("OFFLINE_SESSION_PROCESS_IDENTITY_CHANGED")
        from .readiness_v1 import check_stop_v1

        check_stop_v1(self)
        self._validate_state()
        if self._state["status"] == "SEALED":
            raise ValueError("OFFLINE_SESSION_TERMINAL_SEALED")
        if self._state["status"] != "READY":
            raise ValueError("OFFLINE_SESSION_INTERRUPTED_ATTEMPT_REQUIRES_REVIEW")
        if self._state["attempts_used"] >= self.manifest.max_attempts:
            raise ValueError("OFFLINE_SESSION_ATTEMPTS_EXHAUSTED")
        if set(kwargs) & {
            "position_episode_bindings",
            "position_episode_scope",
            "portfolio_budget_owner",
            "host_budget_recovery",
            "offline_governed_attempt",
        }:
            raise ValueError("OFFLINE_SESSION_OWNER_OVERRIDE_FORBIDDEN")
        if kwargs.get("origin_main_sha") != self.manifest.origin_main_sha:
            raise ValueError("OFFLINE_SESSION_ORIGIN_BINDING_CHANGED")
        prefix, observed = kwargs.get("cycle_id_prefix"), kwargs.get("observed_unix")
        if (
            not isinstance(prefix, str)
            or not prefix
            or prefix != prefix.strip()
            or prefix in self._state["prefixes"]
            or type(observed) not in (int, float)
            or not math.isfinite(observed)
            or not self.manifest.replay_start_unix <= observed <= self.manifest.replay_stop_unix
            or (
                self._state["last_observed_unix"] is not None
                and observed < self._state["last_observed_unix"]
            )
        ):
            raise ValueError("OFFLINE_SESSION_REPLAY_BOUNDS_OR_PREFIX_INVALID")
        event = kwargs.get("last_finalized_event_ts_unix")
        if (
            type(event) not in (int, float)
            or not math.isfinite(event)
            or not self.manifest.replay_start_unix <= event <= observed
        ):
            raise ValueError("OFFLINE_SESSION_EVENT_CLOCK_INVALID")
        self._validate_pairs(composed_pairs)
        if self.manifest.data_profile_digest is not None:
            payload = self.read_data_for_purpose_v1(
                purpose="TRADING", as_of_ms=int(observed * 1000)
            )
            supplied = kwargs.get("candles_payload")
            supplied_by_lane = kwargs.get("candles_payload_by_lane")
            lane = self.manifest.lanes[0].identity.lane_id
            if (supplied is not None and supplied != payload) or (
                supplied_by_lane is not None and supplied_by_lane != {lane: payload}
            ):
                raise ValueError("OFFLINE_SESSION_TRADING_DATA_OVERRIDE_FORBIDDEN")
            kwargs = {**kwargs, "candles_payload": None, "candles_payload_by_lane": {lane: payload}}
            from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.c1_fanout_v1 import (
                extract_lane_closes_v1,
            )

            closes, last = extract_lane_closes_v1(payload)
            kwargs.update(finalized_closes=closes, last_finalized_event_ts_unix=last)
        if (
            load_offline_episode_session_manifest_v1(self.root / MANIFEST).digest()
            != self.manifest.digest()
        ):
            raise ValueError("OFFLINE_SESSION_MANIFEST_CHANGED")
        inspect.signature(invoke_occupied_lane_governed_cycle_n1_consumer_v1).bind(
            composed_pairs,
            **kwargs,
            position_episode_bindings=self._episodes,
            position_episode_scope=self.manifest.account_scope,
        )
        # Reload actual retained source/owner state before every attempt; handles are not authority.
        self._episodes = self._load_episodes()
        self._resource_bindings()
        if json.loads((self.root / RECEIPT).read_text()) != self._state:
            raise ValueError("OFFLINE_SESSION_RECEIPT_CHANGED")
        namespace = bind_offline_cycle_namespace_v1(manifest=self.manifest, requested_prefix=prefix)
        self._state.update(
            attempts_used=self._state["attempts_used"] + 1,
            status="RUNNING",
            prefixes=[*self._state["prefixes"], prefix],
            cycle_namespaces=[*self._state["cycle_namespaces"], namespace.to_dict()],
            last_observed_unix=observed,
        )
        # Persist charge before invoking the governed owner; restart does not renew it.
        _write(self.root / RECEIPT, self._state)
        self.last_completion_result = None
        try:
            from src.ops.bounded_peaktrade_system_composition_v1.governed_attempt_v1 import (
                OfflineGovernedAttemptV1,
            )
            from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1

            result = invoke_occupied_lane_governed_cycle_n1_consumer_v1(
                composed_pairs,
                **{**kwargs, "cycle_id_prefix": namespace.effective_prefix},
                position_episode_bindings=self._episodes,
                position_episode_scope=self.manifest.account_scope,
                offline_governed_attempt=OfflineGovernedAttemptV1(
                    self.manifest, str(self.root), canonical_digest_v1(self._state)
                ),
            )
            if set(result) != set(self._episodes) or any(
                r.governed_cycle_result.permit_created is not False
                or int(r.governed_cycle_result.post_count) != 0
                for r in result.values()
            ):
                raise ValueError("OFFLINE_SESSION_CONSUMER_RESULT_INVALID")
            if self.manifest.host_completion_required:
                from src.ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1.readiness_join_v1 import (
                    address_occupied_lane_n1_consumer_to_host_join_seam_v1,
                )
                from src.ops.current_mf_n5_full_autonomy_runtime_n5_completion_v1.completion_join_v1 import (
                    complete_occupied_lane_runtime_n5_from_readiness_v1,
                )

                projections = address_occupied_lane_n1_consumer_to_host_join_seam_v1(
                    composed_pairs,
                    result,
                    origin_main_sha=self.manifest.origin_main_sha,
                    cycle_id_prefix=namespace.effective_prefix,
                )
                self.last_completion_result = complete_occupied_lane_runtime_n5_from_readiness_v1(
                    composed_pairs,
                    projections,
                    target_cardinality=len(composed_pairs),
                    origin_main_sha=self.manifest.origin_main_sha,
                    cycle_id_prefix=namespace.effective_prefix,
                )
                if (
                    self.last_completion_result.post_count
                    or self.last_completion_result.permit_created
                ):
                    raise ValueError("OFFLINE_SESSION_COMPLETION_EXTERNAL_EFFECT")
            self._state["status"] = "READY"
            _write(self.root / RECEIPT, self._state)
            return result
        except BaseException:
            self._state["status"] = "RECOVERY_REQUIRED"
            _write(self.root / RECEIPT, self._state)
            raise

    def request_stop_v1(self, *, reason, requested_unix):
        """Durable stop for new cycles; never resets original state or allowance."""
        from .readiness_v1 import STOP, check_stop_v1

        if not self._active:
            raise ValueError("OFFLINE_SESSION_NOT_OPEN")
        self._validate_state()
        if (
            type(reason) is not str
            or not reason
            or reason != reason.strip()
            or type(requested_unix) not in {int, float}
            or not math.isfinite(requested_unix)
            or requested_unix <= 0
        ):
            raise ValueError("OFFLINE_SESSION_STOP_INPUT_INVALID")
        check_stop_v1(self)
        _write(
            self.root / STOP,
            {
                "schema": "bounded_offline_session_stop.v1",
                "manifest_digest": self.manifest.digest(),
                "reason": reason,
                "requested_unix": requested_unix,
            },
        )

    def advance_accounting_episode_v1(self, *, lane_id, accounting_session, fills):
        """Explicit same-episode update; no decision attempt or allowance renewal."""
        if not self._active:
            raise ValueError("OFFLINE_SESSION_NOT_OPEN")
        self._validate_state()
        if self._state["status"] == "SEALED":
            raise ValueError("OFFLINE_SESSION_TERMINAL_SEALED")
        if self._state["status"] != "READY":
            raise ValueError("OFFLINE_SESSION_INTERRUPTED_ATTEMPT_REQUIRES_REVIEW")
        lane = next((l for l in self.manifest.lanes if l.identity.lane_id == lane_id), None)
        if lane is None:
            raise ValueError("OFFLINE_SESSION_LANE_SET_CHANGED")
        if (
            load_offline_episode_session_manifest_v1(self.root / MANIFEST).digest()
            != self.manifest.digest()
        ):
            raise ValueError("OFFLINE_SESSION_MANIFEST_CHANGED")
        self._episodes = self._load_episodes()
        self._resource_bindings()
        if json.loads((self.root / RECEIPT).read_text()) != self._state:
            raise ValueError("OFFLINE_SESSION_RECEIPT_CHANGED")
        from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import (
            advance_position_episode_from_simulated_accounting_v1,
        )

        self._state["status"] = "SOURCE_UPDATE_RUNNING"
        _write(self.root / RECEIPT, self._state)
        try:
            result = advance_position_episode_from_simulated_accounting_v1(
                episode=self._episodes[lane_id],
                session=accounting_session,
                fills=fills,
                source_archive_root=Path(lane.source_path).parent,
                cursor_store_root=Path(lane.cursor_state_root),
                expected_scope=self.manifest.account_scope,
                writer_session_id=self.manifest.session_id,
            )
            self._state["status"] = "READY"
            _write(self.root / RECEIPT, self._state)
            return result
        except BaseException:
            self._state["status"] = "RECOVERY_REQUIRED"
            _write(self.root / RECEIPT, self._state)
            raise

    def seal_flat_episode_v1(
        self,
        composed_pairs,
        *,
        accounting_session,
        fills,
        occupancy_payloads,
        observed_portfolio,
        observed_unix,
    ):
        """Terminal local seal; no global lane/capital/Outcome release."""
        if not self._active:
            raise ValueError("OFFLINE_SESSION_NOT_OPEN")
        self._validate_state()
        if self._state["status"] == "SEALED":
            raise ValueError("OFFLINE_SESSION_TERMINAL_SEALED")
        if self._state["status"] != "READY":
            raise ValueError("OFFLINE_SESSION_INTERRUPTED_ATTEMPT_REQUIRES_REVIEW")
        if (
            type(observed_unix) not in (int, float)
            or not math.isfinite(observed_unix)
            or not (
                self.manifest.replay_start_unix <= observed_unix <= self.manifest.replay_stop_unix
            )
            or (
                self._state["last_observed_unix"] is not None
                and observed_unix < self._state["last_observed_unix"]
            )
        ):
            raise ValueError("OFFLINE_SESSION_REPLAY_BOUNDS_OR_PREFIX_INVALID")
        self._validate_pairs(composed_pairs)
        if (
            load_offline_episode_session_manifest_v1(self.root / MANIFEST).digest()
            != self.manifest.digest()
        ):
            raise ValueError("OFFLINE_SESSION_MANIFEST_CHANGED")
        self._episodes = self._load_episodes()
        self._resource_bindings()
        if json.loads((self.root / RECEIPT).read_text()) != self._state:
            raise ValueError("OFFLINE_SESSION_RECEIPT_CHANGED")
        lane = self.manifest.lanes[0]  # this profile retains existing MaxPos=1
        from src.ops.exit_policy_producer_binding_v1.simulated_accounting_close_v1 import (
            seal_simulated_accounting_episode_flat_v1,
        )

        self._state["status"] = "FLAT_SEAL_RUNNING"
        _write(self.root / RECEIPT, self._state)
        try:
            result = seal_simulated_accounting_episode_flat_v1(
                episode=self._episodes[lane.identity.lane_id],
                accounting_session=accounting_session,
                fills=fills,
                bound=composed_pairs[lane.identity.lane_id][1],
                occupancy_payloads=occupancy_payloads,
                observed_portfolio=observed_portfolio,
                observed_unix=observed_unix,
                expected_scope=self.manifest.account_scope,
                source_archive_root=Path(lane.source_path).parent,
                cursor_store_root=Path(lane.cursor_state_root),
                writer_session_id=self.manifest.session_id,
            )
            self._state["status"] = "SEALED"
            _write(self.root / RECEIPT, self._state)
            self._episodes.clear()
            return result
        except BaseException:
            self._state["status"] = "RECOVERY_REQUIRED"
            _write(self.root / RECEIPT, self._state)
            raise

    def close(self):
        self._active = False
        self._episodes = {}
        for fd in reversed(self._fds):
            os.close(fd)
        self._fds.clear()

    def __exit__(self, *_):
        self.close()
