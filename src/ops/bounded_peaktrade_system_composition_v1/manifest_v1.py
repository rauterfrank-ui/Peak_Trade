"""Strict manifest for the bounded, already-open simulated episode profile.

Not the whole proposed system manifest. Original lane/MaxPos/config owners keep
their authority; this profile binds their existing objects and replay bounds.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import re

from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    ABSOLUTE_MAX_CYCLES_PER_RUN,
)

SCHEMA = "bounded_offline_episode_session_manifest.v2"


def repository_source_digest_v1():
    """Same source-tree domain used by the existing unattended host: src/**/*.py."""
    repo = Path(__file__).resolve().parents[3]
    digest = hashlib.sha256()
    for path in sorted((repo / "src").rglob("*.py")):
        digest.update(str(path.relative_to(repo)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def canonical_absolute_path_v1(value):
    if (
        not isinstance(value, str)
        or not Path(value).is_absolute()
        or str(Path(value).resolve()) != value
    ):
        raise ValueError("OFFLINE_SESSION_CANONICAL_ABSOLUTE_PATH_REQUIRED")
    return value


def _text(value):
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("OFFLINE_SESSION_TEXT_REQUIRED")


def _digest(value, size=64):
    if not isinstance(value, str) or re.fullmatch(f"[0-9a-f]{{{size}}}", value) is None:
        raise ValueError("OFFLINE_SESSION_DIGEST_INVALID")


@dataclass(frozen=True)
class OfflineEpisodeLaneV1:
    identity: PositionEpisodeIdentityV1
    bound_instrument_identity: str
    instrument_epoch: str
    source_path: str
    source_content_digest: str
    exit_state_root: str
    cursor_state_root: str


@dataclass(frozen=True)
class OfflineEpisodeSessionManifestV1:
    session_id: str
    repository_sha: str
    origin_main_sha: str
    implementation_source_digest: str
    exit_policy_config_digest: str
    account_scope: PositionEpisodeScopeV1
    replay_start_unix: float
    replay_stop_unix: float
    max_attempts: int
    lanes: tuple[OfflineEpisodeLaneV1, ...]
    data_profile_digest: str | None = None
    host_completion_required: bool = False

    def validate_v1(self):
        if type(self.host_completion_required) is not bool:
            raise ValueError("OFFLINE_SESSION_COMPLETION_POLICY_INVALID")
        if self.data_profile_digest is not None:
            _digest(self.data_profile_digest)
        _text(self.session_id)
        _digest(self.repository_sha, 40)
        _digest(self.origin_main_sha, 40)
        _digest(self.implementation_source_digest)
        _digest(self.exit_policy_config_digest)
        if not isinstance(self.account_scope, PositionEpisodeScopeV1):
            raise ValueError("OFFLINE_SESSION_ACCOUNT_SCOPE_REQUIRED")
        self.account_scope.validate_v1()
        if self.account_scope.execution_environment != "INTERNAL_SIMULATED_EXECUTION":
            raise ValueError("OFFLINE_SESSION_SIMULATION_ONLY")
        if (
            type(self.max_attempts) is not int
            or not 0 < self.max_attempts <= ABSOLUTE_MAX_CYCLES_PER_RUN
            or any(
                type(v) not in (int, float) or not math.isfinite(v) or v <= 0
                for v in (self.replay_start_unix, self.replay_stop_unix)
            )
            or self.replay_stop_unix <= self.replay_start_unix
        ):
            raise ValueError("OFFLINE_SESSION_EXPLICIT_BOUNDS_REQUIRED")
        if not isinstance(self.lanes, tuple) or not 0 < len(self.lanes) <= MAX_POSITIONS_EFFECTIVE:
            raise ValueError("OFFLINE_SESSION_EXISTING_MAXPOS_EXCEEDED")
        lane_ids = set()
        roots = []
        for lane in self.lanes:
            if not isinstance(lane, OfflineEpisodeLaneV1):
                raise ValueError("OFFLINE_SESSION_LANE_TYPE_REQUIRED")
            lane.identity.validate_v1()
            if (
                lane.identity.account_scope != self.account_scope
                or lane.identity.lane_id not in LANE_IDS
                or lane.identity.lane_id in lane_ids
            ):
                raise ValueError("OFFLINE_SESSION_LANE_IDENTITY_MISMATCH")
            lane_ids.add(lane.identity.lane_id)
            for value in (
                lane.bound_instrument_identity,
                lane.instrument_epoch,
                lane.source_content_digest,
            ):
                _digest(value)
            for path in (lane.source_path, lane.exit_state_root, lane.cursor_state_root):
                canonical_absolute_path_v1(path)
            roots.extend((Path(lane.exit_state_root), Path(lane.cursor_state_root)))
        if any(
            a == b or a in b.parents or b in a.parents
            for i, a in enumerate(roots)
            for b in roots[i + 1 :]
        ):
            raise ValueError("OFFLINE_SESSION_OWNER_ROOTS_OVERLAP")
        if any(
            Path(l.source_path) == r or r in Path(l.source_path).parents
            for l in self.lanes
            for r in roots
        ):
            raise ValueError("OFFLINE_SESSION_SOURCE_INSIDE_WRITABLE_OWNER_ROOT")

    def to_dict(self):
        return {"schema": SCHEMA, **asdict(self)}

    def digest(self):
        self.validate_v1()
        return canonical_digest_v1(self.to_dict())


def _strict_object(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError("OFFLINE_SESSION_DUPLICATE_JSON_KEY")
        result[k] = v
    return result


def load_offline_episode_session_manifest_v1(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
    if (
        not isinstance(value, dict)
        or set(value) != {"schema", *OfflineEpisodeSessionManifestV1.__dataclass_fields__}
        or value["schema"] != SCHEMA
    ):
        raise ValueError("OFFLINE_SESSION_MANIFEST_SCHEMA_MISMATCH")
    data = dict(value)
    data.pop("schema")
    data["account_scope"] = PositionEpisodeScopeV1(**data["account_scope"])
    if not isinstance(data["lanes"], list):
        raise ValueError("OFFLINE_SESSION_LANE_ARRAY_REQUIRED")
    lanes = []
    for raw in data["lanes"]:
        lane = dict(raw)
        identity = dict(lane["identity"])
        identity["account_scope"] = PositionEpisodeScopeV1(**identity["account_scope"])
        lane["identity"] = PositionEpisodeIdentityV1(**identity)
        lanes.append(OfflineEpisodeLaneV1(**lane))
    data["lanes"] = tuple(lanes)
    manifest = OfflineEpisodeSessionManifestV1(**data)
    manifest.validate_v1()
    return manifest
