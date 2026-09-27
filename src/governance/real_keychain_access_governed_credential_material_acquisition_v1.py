"""Governed ephemeral Keychain opaque material acquisition (in-memory only).

Uses canonical OS-native acquisition with policy-bound ephemeral consumer.
Never returns opaque bytes in public results. Wipes held material on exit.

RUNTIME_AUTHORIZATION_EFFECT=GOVERNED_EPHEMERAL_KEYCHAIN_ACQUISITION_ONLY
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterator

from src.governance.real_keychain_access_or_credential_material_load_policy_v1 import (
    EPHEMERAL_KEYCHAIN_CONSUMER_ID,
    governed_credential_material_load_authorized_v1,
    validate_real_keychain_access_or_credential_material_load_policy_record_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    FullCoreCheckoutIndependentCredentialCapabilityError,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    SOURCE_REF_URI,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_fail_closed_os_native_store_adapter_v1 import (
    FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    FullCoreOsNativeStoreAcquisitionProofV1,
    OsNativeStoreLookupBackendV1,
    bounded_ephemeral_keychain_access_v1,
    borrow_held_opaque_bytes_for_bounded_parse_v1,
    opaque_os_native_store_material_is_held_v1,
    public_surfaces_must_not_contain_opaque_material_v1,
    wipe_opaque_os_native_store_material_v1,
)

ACQUISITION_OWNER: Final[str] = (
    "governance.real_keychain_access_governed_credential_material_acquisition_v1"
)
STATUS_ACQUISITION_DENIED: Final[str] = (
    "GOVERNED_CREDENTIAL_MATERIAL_ACQUISITION_DENIED_FAIL_CLOSED"
)
STATUS_ACQUISITION_PERFORMED: Final[str] = "GOVERNED_CREDENTIAL_MATERIAL_ACQUISITION_PERFORMED"
STATUS_ACQUISITION_NOT_PERFORMED: Final[str] = (
    "GOVERNED_CREDENTIAL_MATERIAL_ACQUISITION_NOT_PERFORMED"
)


class GovernedCredentialMaterialAcquisitionError(RuntimeError):
    """Fail-closed governed credential material acquisition violation."""


@dataclass(frozen=True, slots=True)
class GovernedCredentialMaterialAcquisitionResultV1:
    acquisition_status: str
    acquisition_performed: bool
    real_credential_access_performed: bool
    credential_material_held: bool
    source_ref_uri: str
    keychain_service_id: str | None
    keychain_account_id: str | None
    ephemeral_keychain_consumer: str
    policy_record_digest: str | None
    reason_codes: tuple[str, ...]
    secret_disclosed: bool
    secret_persisted: bool

    def to_public_dict_v1(self) -> dict[str, str | bool]:
        return {
            "acquisition_status": self.acquisition_status,
            "acquisition_performed": self.acquisition_performed,
            "real_credential_access_performed": self.real_credential_access_performed,
            "credential_material_held": self.credential_material_held,
            "source_ref_uri": self.source_ref_uri,
            "keychain_service_id": self.keychain_service_id or "",
            "keychain_account_id": self.keychain_account_id or "",
            "ephemeral_keychain_consumer": self.ephemeral_keychain_consumer,
            "policy_record_digest": self.policy_record_digest or "",
            "secret_disclosed": self.secret_disclosed,
            "secret_persisted": self.secret_persisted,
        }

    def __repr__(self) -> str:
        return "GovernedCredentialMaterialAcquisitionResultV1(redacted)"

    def __str__(self) -> str:
        return "GovernedCredentialMaterialAcquisitionResultV1(redacted)"


def _denied(
    *,
    reasons: tuple[str, ...],
    policy_digest: str | None,
) -> GovernedCredentialMaterialAcquisitionResultV1:
    return GovernedCredentialMaterialAcquisitionResultV1(
        acquisition_status=STATUS_ACQUISITION_DENIED,
        acquisition_performed=False,
        real_credential_access_performed=False,
        credential_material_held=False,
        source_ref_uri=SOURCE_REF_URI,
        keychain_service_id=None,
        keychain_account_id=None,
        ephemeral_keychain_consumer=EPHEMERAL_KEYCHAIN_CONSUMER_ID,
        policy_record_digest=policy_digest,
        reason_codes=reasons,
        secret_disclosed=False,
        secret_persisted=False,
    )


def _proof_to_result_v1(
    *,
    proof: FullCoreOsNativeStoreAcquisitionProofV1,
    holder_id: int,
    policy_digest: str | None,
    performed: bool,
) -> GovernedCredentialMaterialAcquisitionResultV1:
    held = opaque_os_native_store_material_is_held_v1(holder_id)
    return GovernedCredentialMaterialAcquisitionResultV1(
        acquisition_status=STATUS_ACQUISITION_PERFORMED if performed else STATUS_ACQUISITION_DENIED,
        acquisition_performed=performed and held,
        real_credential_access_performed=performed and held,
        credential_material_held=held,
        source_ref_uri=proof.source_ref_uri,
        keychain_service_id=proof.keychain_service_id,
        keychain_account_id=proof.keychain_account_id,
        ephemeral_keychain_consumer=EPHEMERAL_KEYCHAIN_CONSUMER_ID,
        policy_record_digest=policy_digest,
        reason_codes=() if performed else ("ACQUISITION_INCOMPLETE",),
        secret_disclosed=False,
        secret_persisted=False,
    )


def attempt_governed_credential_material_acquisition_v1(
    *,
    repo_root: Path | None = None,
    backend: OsNativeStoreLookupBackendV1 | None = None,
    source_ref: str | None = None,
) -> GovernedCredentialMaterialAcquisitionResultV1:
    """Acquire opaque material under governed policy. Requires explicit backend in tests."""

    root = repo_root or Path(__file__).resolve().parents[2]
    policy = validate_real_keychain_access_or_credential_material_load_policy_record_v1(
        repo_root=root
    )
    if policy.material_load_policy_authorized is not True:
        return _denied(
            reasons=policy.reason_codes or ("MATERIAL_LOAD_POLICY_NOT_AUTHORIZED",),
            policy_digest=policy.policy_record_digest,
        )
    if not governed_credential_material_load_authorized_v1(repo_root=root):
        return _denied(
            reasons=("GOVERNED_CREDENTIAL_MATERIAL_LOAD_NOT_AUTHORIZED",),
            policy_digest=policy.policy_record_digest,
        )
    if backend is None:
        return _denied(
            reasons=("LOOKUP_BACKEND_REQUIRED_NO_DEFAULT_REAL_KEYCHAIN_IN_THIS_WP",),
            policy_digest=policy.policy_record_digest,
        )

    ref = str(source_ref or SOURCE_REF_URI)
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    holder_id = id(adapter)
    try:
        with bounded_ephemeral_keychain_access_v1(consumer_id=EPHEMERAL_KEYCHAIN_CONSUMER_ID):
            try:
                proof = adapter.acquire_opaque_os_native_store_material_v1(
                    source_ref=ref,
                    backend=backend,
                )
            except FullCoreCheckoutIndependentCredentialCapabilityError as exc:
                return _denied(
                    reasons=(str(exc),),
                    policy_digest=policy.policy_record_digest,
                )
            except Exception:
                return _denied(
                    reasons=("ACQUISITION_FAIL_CLOSED",),
                    policy_digest=policy.policy_record_digest,
                )
            if not opaque_os_native_store_material_is_held_v1(holder_id):
                return _denied(
                    reasons=("OPAQUE_MATERIAL_NOT_HELD",),
                    policy_digest=policy.policy_record_digest,
                )
            opaque = borrow_held_opaque_bytes_for_bounded_parse_v1(holder_id=holder_id)
            public_surfaces_must_not_contain_opaque_material_v1(
                proof,
                proof.to_dict(),
                adapter,
                sentinel=opaque,
            )
            result = _proof_to_result_v1(
                proof=proof,
                holder_id=holder_id,
                policy_digest=policy.policy_record_digest,
                performed=True,
            )
    finally:
        wipe_opaque_os_native_store_material_v1(holder_id)

    if opaque_os_native_store_material_is_held_v1(holder_id):
        return _denied(
            reasons=("OPAQUE_MATERIAL_LEAK_AFTER_WIPE",),
            policy_digest=policy.policy_record_digest,
        )
    return result


@contextmanager
def governed_credential_material_acquisition_scope_v1(
    *,
    repo_root: Path | None = None,
    backend: OsNativeStoreLookupBackendV1,
    source_ref: str | None = None,
) -> Iterator[GovernedCredentialMaterialAcquisitionResultV1]:
    """Hold opaque bytes only inside the context; wiped before exit completes."""

    root = repo_root or Path(__file__).resolve().parents[2]
    policy = validate_real_keychain_access_or_credential_material_load_policy_record_v1(
        repo_root=root
    )
    if policy.material_load_policy_authorized is not True:
        yield _denied(
            reasons=policy.reason_codes or ("MATERIAL_LOAD_POLICY_NOT_AUTHORIZED",),
            policy_digest=policy.policy_record_digest,
        )
        return
    if not governed_credential_material_load_authorized_v1(repo_root=root):
        yield _denied(
            reasons=("GOVERNED_CREDENTIAL_MATERIAL_LOAD_NOT_AUTHORIZED",),
            policy_digest=policy.policy_record_digest,
        )
        return

    ref = str(source_ref or SOURCE_REF_URI)
    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    holder_id = id(adapter)
    result: GovernedCredentialMaterialAcquisitionResultV1 | None = None
    try:
        with bounded_ephemeral_keychain_access_v1(consumer_id=EPHEMERAL_KEYCHAIN_CONSUMER_ID):
            try:
                proof = adapter.acquire_opaque_os_native_store_material_v1(
                    source_ref=ref,
                    backend=backend,
                )
            except FullCoreCheckoutIndependentCredentialCapabilityError as exc:
                result = _denied(
                    reasons=(str(exc),),
                    policy_digest=policy.policy_record_digest,
                )
                yield result
                return
            result = _proof_to_result_v1(
                proof=proof,
                holder_id=holder_id,
                policy_digest=policy.policy_record_digest,
                performed=True,
            )
            yield result
    finally:
        wipe_opaque_os_native_store_material_v1(holder_id)


__all__ = [
    "ACQUISITION_OWNER",
    "GovernedCredentialMaterialAcquisitionError",
    "GovernedCredentialMaterialAcquisitionResultV1",
    "attempt_governed_credential_material_acquisition_v1",
    "governed_credential_material_acquisition_scope_v1",
]
