"""Attempt-scoped original governed evidence; shared cursor/locks stay original."""

from dataclasses import dataclass
import json
import math
from pathlib import Path

from src.ops.bounded_peaktrade_system_composition_v1.manifest_v1 import (
    OfflineEpisodeSessionManifestV1,
    canonical_absolute_path_v1,
    load_offline_episode_session_manifest_v1,
    repository_source_digest_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1.cycle_namespace_v1 import (
    bind_offline_cycle_namespace_v1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1


@dataclass(frozen=True)
class OfflineGovernedAttemptV1:
    manifest: OfflineEpisodeSessionManifestV1
    session_root: str
    charged_receipt_digest: str

    def bind_roots_v1(
        self,
        addressed,
        *,
        prefix,
        scope,
        episodes,
        origin_main_sha,
        observed_unix,
        last_finalized_event_ts_unix,
    ):
        from src.ops.bounded_peaktrade_system_composition_v1.session_v1 import (
            MANIFEST,
            RECEIPT,
            RESOURCE_BINDING,
            STATE_SCHEMA,
        )
        from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
            LEDGER_FILENAME,
        )

        canonical_absolute_path_v1(self.session_root)
        root = Path(self.session_root)
        manifest = self.manifest
        manifest.validate_v1()
        if (
            load_offline_episode_session_manifest_v1(root / MANIFEST).digest() != manifest.digest()
            or scope != manifest.account_scope
            or origin_main_sha != manifest.origin_main_sha
            or set(addressed) != {l.identity.lane_id for l in manifest.lanes}
            or episodes is None
            or set(episodes) != set(addressed)
            or manifest.implementation_source_digest != repository_source_digest_v1()
        ):
            raise ValueError("OFFLINE_ATTEMPT_MANIFEST_MISMATCH")
        state = json.loads((root / RECEIPT).read_text())
        if (
            canonical_digest_v1(state) != self.charged_receipt_digest
            or state.get("schema") != STATE_SCHEMA
            or state.get("manifest_digest") != manifest.digest()
            or state.get("status") != "RUNNING"
            or type(state.get("attempts_used")) is not int
            or not 0 < state["attempts_used"] <= manifest.max_attempts
            or len(state.get("prefixes", [])) != state["attempts_used"]
            or len(state.get("cycle_namespaces", [])) != state["attempts_used"]
            or type(observed_unix) not in (int, float)
            or type(last_finalized_event_ts_unix) not in (int, float)
            or not math.isfinite(observed_unix)
            or not math.isfinite(last_finalized_event_ts_unix)
            or state.get("last_observed_unix") != observed_unix
            or not manifest.replay_start_unix
            <= last_finalized_event_ts_unix
            <= observed_unix
            <= manifest.replay_stop_unix
        ):
            raise ValueError("OFFLINE_ATTEMPT_CHARGED_RECEIPT_REQUIRED")
        for raw, row in zip(state["prefixes"], state["cycle_namespaces"]):
            if (
                row
                != bind_offline_cycle_namespace_v1(
                    manifest=manifest, requested_prefix=raw
                ).to_dict()
            ):
                raise ValueError("OFFLINE_ATTEMPT_NAMESPACE_MISMATCH")
        if prefix != state["cycle_namespaces"][-1]["effective_prefix"]:
            raise ValueError("OFFLINE_ATTEMPT_PREFIX_MISMATCH")
        binding = {
            "schema": "bounded_offline_episode_session_resource_binding.v1",
            "session_root": self.session_root,
            "manifest_digest": manifest.digest(),
        }
        result = {}
        for lane in manifest.lanes:
            lane_id = lane.identity.lane_id
            cursor, lock, evidence = addressed[lane_id]
            episode = episodes[lane_id]
            if (
                cursor != lane.cursor_state_root
                or episode.identity != lane.identity
                or str(episode.binding.state_root) != lane.exit_state_root
            ):
                raise ValueError("OFFLINE_ATTEMPT_OWNER_MISMATCH")
            for owner_root in (lane.cursor_state_root, lane.exit_state_root):
                if json.loads((Path(owner_root) / RESOURCE_BINDING).read_text()) != binding:
                    raise ValueError("OFFLINE_ATTEMPT_RESOURCE_MISMATCH")
            # A pre-existing legacy cycle cannot be converted into a fresh run.
            if (Path(evidence) / LEDGER_FILENAME).exists():
                raise ValueError("OFFLINE_ATTEMPT_LEGACY_LEDGER_PRESENT")
            attempt_root = Path(evidence) / "offline_attempts_v1" / prefix
            if attempt_root.resolve() != attempt_root:
                raise ValueError("OFFLINE_ATTEMPT_ROOT_ALIAS")
            result[lane_id] = (cursor, lock, str(attempt_root))
        return result
