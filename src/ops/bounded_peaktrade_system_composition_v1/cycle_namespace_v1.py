"""Composition-owned transport namespace; local Scope/market IDs stay unchanged."""

from dataclasses import asdict, dataclass

from src.ops.bounded_peaktrade_system_composition_v1.manifest_v1 import (
    OfflineEpisodeSessionManifestV1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1

SCHEMA = "bounded_offline_cycle_namespace.v1"


@dataclass(frozen=True)
class OfflineCycleNamespaceV1:
    schema: str
    manifest_digest: str
    requested_prefix: str
    effective_prefix: str

    def to_dict(self):
        return asdict(self)


def bind_offline_cycle_namespace_v1(*, manifest, requested_prefix):
    if not isinstance(manifest, OfflineEpisodeSessionManifestV1):
        raise ValueError("OFFLINE_SESSION_TYPED_MANIFEST_REQUIRED")
    if (
        not isinstance(requested_prefix, str)
        or not requested_prefix
        or requested_prefix != requested_prefix.strip()
    ):
        raise ValueError("OFFLINE_SESSION_CYCLE_PREFIX_INVALID")
    digest = manifest.digest()
    material = {"schema": SCHEMA, "manifest_digest": digest, "requested_prefix": requested_prefix}
    # Full preimage, not a sanitized/truncated caller label. Fixed 64 hex bytes
    # leave room for the existing lane/cycle suffixes in DDO's 128-byte IDs.
    return OfflineCycleNamespaceV1(
        **material,
        effective_prefix=canonical_digest_v1(material),
    )
