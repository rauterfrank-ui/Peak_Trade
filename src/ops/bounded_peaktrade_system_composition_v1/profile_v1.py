"""Allowlisted E1 offline entry: pinned five-purpose data and original host completion."""

from src.ops.bounded_peaktrade_system_composition_v1.manifest_v1 import (
    OfflineEpisodeSessionManifestV1,
)
from src.ops.bounded_peaktrade_system_composition_v1.session_v1 import (
    BoundedOfflineEpisodeSessionV1,
)
from src.ops.economic_md_input_producer_v1.purpose_consumers_v1 import purpose_profile_digest_v1


def open_e1_offline_session_v1(*, manifest, state_root, mode, data_sources):
    if not isinstance(manifest, OfflineEpisodeSessionManifestV1):
        raise ValueError("E1_TYPED_OFFLINE_MANIFEST_REQUIRED")
    manifest.validate_v1()
    if manifest.data_profile_digest is None or not manifest.host_completion_required:
        raise ValueError("E1_COMPLETE_DATA_AND_COMPLETION_PROFILE_REQUIRED")
    if purpose_profile_digest_v1(data_sources) != manifest.data_profile_digest:
        raise ValueError("OFFLINE_SESSION_DATA_PROFILE_CHANGED")
    return BoundedOfflineEpisodeSessionV1(
        manifest=manifest, state_root=state_root, mode=mode, data_sources=data_sources
    )
