"""R6 S4 MF shadow/sim evidence identity.

Creates a dedicated Multi-Future evidence identity plane. Package-N
SHA256 live-owner join remains a distinct plane and is not consumed
here. MD5-12 is forbidden.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.constants_v1 import (
    CANONICAL_SERIALIZATION_VERSION,
    CAPABILITY_ID,
    CONTRACT_VERSION,
    FIXTURE_INSTRUMENT_IDS,
    FIXTURE_SEED,
    IDENTITY_JOIN_KEY,
    IDENTITY_PLANE,
    MD5_12_FORBIDDEN,
    PACKAGE_N_IS_NOT_MF_IDENTITY,
    PACKAGE_N_LIVE_OWNER_JOIN_NOT_USED,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.lineage_v1 import (
    canonical_dumps,
    digest_mapping,
    sha256_hex,
)
from src.ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1.models_v1 import (
    R6S4ShadowSimEvidenceError,
)


def _reject(message: str) -> None:
    raise R6S4ShadowSimEvidenceError(message)


def identity_payload_v1(*, evidence_digest: str) -> Mapping[str, Any]:
    if IDENTITY_JOIN_KEY != "sha256":
        _reject("identity_join_key_must_be_sha256")
    if MD5_12_FORBIDDEN is not True:
        _reject("md5_12_must_remain_forbidden")
    if PACKAGE_N_LIVE_OWNER_JOIN_NOT_USED is not True:
        _reject("package_n_live_owner_join_must_remain_unused")
    if "md5" in evidence_digest.lower():
        _reject("md5_digest_forbidden")
    payload = {
        "capability_id": CAPABILITY_ID,
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "contract_version": CONTRACT_VERSION,
        "evidence_digest": evidence_digest,
        "fixture_instrument_ids": list(FIXTURE_INSTRUMENT_IDS),
        "fixture_seed": FIXTURE_SEED,
        "identity_join_key": IDENTITY_JOIN_KEY,
        "identity_plane": IDENTITY_PLANE,
        "md5_12_forbidden": MD5_12_FORBIDDEN,
        "package_n_is_not_mf_identity": PACKAGE_N_IS_NOT_MF_IDENTITY,
        "package_n_live_owner_join_not_used": PACKAGE_N_LIVE_OWNER_JOIN_NOT_USED,
    }
    return MappingProxyType(payload)


def build_evidence_identity_v1(*, evidence_digest: str) -> Mapping[str, Any]:
    payload = identity_payload_v1(evidence_digest=evidence_digest)
    identity_id = sha256_hex(canonical_dumps(payload))
    if len(identity_id) != 64:
        _reject("identity_id_not_sha256_hex")
    return MappingProxyType(
        {
            "experiment_identity_id": identity_id,
            "identity_digest": digest_mapping(payload),
            "identity_payload": dict(payload),
            "lanes": {
                "CONTENT_HASH": evidence_digest,
                "EVIDENCE": identity_id,
                "IDENTITY": identity_id,
            },
        }
    )
