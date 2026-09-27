"""Governed K1 opaque signing-handle construction (ephemeral, in-memory only).

Policy-bound wrapper around the Full-Core K1 opaque signing seam. Never returns
secrets. Wipes material on exit.

RUNTIME_AUTHORIZATION_EFFECT=GOVERNED_K1_OPAQUE_SIGNING_HANDLE_CONSTRUCTION_ONLY
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterator

from src.governance.current_productive_k1_opaque_signing_handle_pre_post_policy_v1 import (
    OWNER_GO_TOKEN,
    governed_k1_opaque_signing_handle_pre_post_authorized_v1,
    validate_k1_opaque_signing_handle_pre_post_policy_record_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    OsNativeStoreLookupBackendV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1 import (
    CurrentProductiveK1OpaqueSigningHandleProofV1,
    CurrentProductiveK1OpaqueSigningHandleSessionV1,
    open_current_productive_k1_opaque_signing_handle_session_v1,
)

CONSTRUCTION_OWNER: Final[str] = "governance.k1_opaque_signing_handle_governed_construction_v1"
STATUS_CONSTRUCTION_DENIED: Final[str] = "GOVERNED_K1_OPAQUE_SIGNING_HANDLE_CONSTRUCTION_DENIED"
STATUS_CONSTRUCTION_PERFORMED: Final[str] = (
    "GOVERNED_K1_OPAQUE_SIGNING_HANDLE_CONSTRUCTION_PERFORMED"
)


class GovernedK1OpaqueSigningHandleConstructionError(RuntimeError):
    """Fail-closed governed K1 opaque signing-handle construction violation."""


@dataclass(frozen=True, slots=True)
class GovernedK1OpaqueSigningHandleConstructionResultV1:
    construction_status: str
    construction_performed: bool
    opaque_signing_handle_constructed: bool
    real_credential_access_performed: bool
    credential_material_loaded_standing: bool
    handle_id: str | None
    policy_record_digest: str | None
    reason_codes: tuple[str, ...]
    secret_disclosed: bool
    secret_persisted: bool

    def to_public_dict_v1(self) -> dict[str, str | bool]:
        return {
            "construction_status": self.construction_status,
            "construction_performed": self.construction_performed,
            "opaque_signing_handle_constructed": self.opaque_signing_handle_constructed,
            "real_credential_access_performed": self.real_credential_access_performed,
            "credential_material_loaded_standing": self.credential_material_loaded_standing,
            "handle_id": self.handle_id or "",
            "policy_record_digest": self.policy_record_digest or "",
            "secret_disclosed": self.secret_disclosed,
            "secret_persisted": self.secret_persisted,
        }

    def __repr__(self) -> str:
        return "GovernedK1OpaqueSigningHandleConstructionResultV1(redacted)"


def _denied(
    *,
    reasons: tuple[str, ...],
    policy_digest: str | None,
) -> GovernedK1OpaqueSigningHandleConstructionResultV1:
    return GovernedK1OpaqueSigningHandleConstructionResultV1(
        construction_status=STATUS_CONSTRUCTION_DENIED,
        construction_performed=False,
        opaque_signing_handle_constructed=False,
        real_credential_access_performed=False,
        credential_material_loaded_standing=False,
        handle_id=None,
        policy_record_digest=policy_digest,
        reason_codes=reasons,
        secret_disclosed=False,
        secret_persisted=False,
    )


@contextmanager
def governed_k1_opaque_signing_handle_construction_scope_v1(
    *,
    repo_root: Path | None = None,
    owner_go: str,
    backend: OsNativeStoreLookupBackendV1,
) -> Iterator[
    tuple[
        GovernedK1OpaqueSigningHandleConstructionResultV1,
        CurrentProductiveK1OpaqueSigningHandleSessionV1 | None,
    ]
]:
    """Construct opaque signing handle under K1 PRE-POST policy. Session only inside context."""

    root = repo_root or Path(__file__).resolve().parents[2]
    policy = validate_k1_opaque_signing_handle_pre_post_policy_record_v1(repo_root=root)
    if policy.k1_pre_post_policy_authorized is not True:
        denied = _denied(
            reasons=policy.reason_codes or ("K1_PRE_POST_POLICY_NOT_AUTHORIZED",),
            policy_digest=policy.policy_record_digest,
        )
        yield denied, None
        return
    if not governed_k1_opaque_signing_handle_pre_post_authorized_v1(repo_root=root):
        denied = _denied(
            reasons=("GOVERNED_K1_PRE_POST_NOT_AUTHORIZED",),
            policy_digest=policy.policy_record_digest,
        )
        yield denied, None
        return
    if owner_go != OWNER_GO_TOKEN:
        denied = _denied(
            reasons=("OWNER_GO_MISMATCH",),
            policy_digest=policy.policy_record_digest,
        )
        yield denied, None
        return

    session: CurrentProductiveK1OpaqueSigningHandleSessionV1 | None = None
    try:
        with open_current_productive_k1_opaque_signing_handle_session_v1(
            owner_go=owner_go,
            backend=backend,
        ) as active:
            session = active
            proof: CurrentProductiveK1OpaqueSigningHandleProofV1 = active.proof
            result = GovernedK1OpaqueSigningHandleConstructionResultV1(
                construction_status=STATUS_CONSTRUCTION_PERFORMED,
                construction_performed=True,
                opaque_signing_handle_constructed=proof.handle_bound == "true",
                real_credential_access_performed=True,
                credential_material_loaded_standing=False,
                handle_id=proof.handle_id,
                policy_record_digest=policy.policy_record_digest,
                reason_codes=(),
                secret_disclosed=False,
                secret_persisted=False,
            )
            yield result, session
    except Exception:
        denied = _denied(
            reasons=("K1_OPAQUE_SIGNING_HANDLE_CONSTRUCTION_FAIL_CLOSED",),
            policy_digest=policy.policy_record_digest,
        )
        yield denied, None


__all__ = [
    "CONSTRUCTION_OWNER",
    "GovernedK1OpaqueSigningHandleConstructionError",
    "GovernedK1OpaqueSigningHandleConstructionResultV1",
    "governed_k1_opaque_signing_handle_construction_scope_v1",
]
