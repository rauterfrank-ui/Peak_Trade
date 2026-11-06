"""Governed productive chain: permit mint → K1 signing → PRE-POST → POST admission stop.

Mechanically traverses the authorized PRE-POST chain and stops at real venue POST
admission (requires separate actual-POST Owner-GO). No network POST.

RUNTIME_AUTHORIZATION_EFFECT=K1_PRE_POST_PRODUCTIVE_CHAIN_EVALUATION_ONLY
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from src.governance.current_productive_k1_opaque_signing_handle_pre_post_policy_v1 import (
    OWNER_GO_TOKEN,
    evaluate_k1_opaque_signing_handle_pre_post_admission_v1,
)
from src.governance.current_productive_k1_pre_post_request_envelope_v1 import (
    CurrentProductiveK1PrePostRequestEnvelopeV1,
    build_and_validate_current_productive_k1_pre_post_request_envelope_v1,
    validate_pre_post_envelope_bindings_v1,
)
from src.governance.current_productive_real_venue_post_admission_v1 import (
    BLOCKER_CLASS,
    NEXT_OWNER_GO,
    RealVenuePostAdmissionResultV1,
    evaluate_real_venue_post_admission_v1,
)
from src.governance.external_effect_permit_mint_policy_v1 import (
    governed_permit_mint_authorized_v1,
)
from src.governance.k1_opaque_signing_handle_governed_construction_v1 import (
    governed_k1_opaque_signing_handle_construction_scope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    OsNativeStoreLookupBackendV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    POST_OWNER_GO,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    TRADE_ORDER_PATH,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ExternalEffectPermitV1,
    issue_external_effect_permit_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    AUTHORIZED_HOST,
)

CHAIN_OWNER: Final[str] = "governance.current_productive_k1_pre_post_productive_chain_v1"
STATUS_CHAIN_STOPPED_POST_ADMISSION: Final[str] = (
    "K1_PRE_POST_CHAIN_STOPPED_AT_REAL_VENUE_POST_ADMISSION"
)
STATUS_CHAIN_DENIED: Final[str] = "K1_PRE_POST_CHAIN_DENIED_FAIL_CLOSED"


@dataclass(frozen=True, slots=True)
class K1PrePostProductiveChainResultV1:
    chain_status: str
    real_keychain_access_authorized: bool
    real_credential_access_performed: bool
    credential_material_loaded: bool
    opaque_signing_handle_authorized: bool
    opaque_signing_handle_constructed: bool
    permit_mint_authorized: bool
    permit_mint_performed: bool
    request_signing_authorized: bool
    request_signing_performed: bool
    pre_post_envelope_constructed: bool
    pre_post_validated: bool
    post_admission: RealVenuePostAdmissionResultV1
    permit_id: str | None
    pre_post_digest: str | None
    secret_disclosed: bool
    secret_persisted: bool
    first_genuine_blocker: str
    blocker_class: str
    next_owner_go: str
    reason_codes: tuple[str, ...]

    def to_public_dict_v1(self) -> dict[str, str | bool]:
        return {
            "chain_status": self.chain_status,
            "real_keychain_access_authorized": self.real_keychain_access_authorized,
            "real_credential_access_performed": self.real_credential_access_performed,
            "credential_material_loaded": self.credential_material_loaded,
            "opaque_signing_handle_authorized": self.opaque_signing_handle_authorized,
            "opaque_signing_handle_constructed": self.opaque_signing_handle_constructed,
            "permit_mint_authorized": self.permit_mint_authorized,
            "permit_mint_performed": self.permit_mint_performed,
            "request_signing_authorized": self.request_signing_authorized,
            "request_signing_performed": self.request_signing_performed,
            "pre_post_envelope_constructed": self.pre_post_envelope_constructed,
            "pre_post_validated": self.pre_post_validated,
            "post_allowed": self.post_admission.post_allowed,
            "real_venue_post_allowed": self.post_admission.real_venue_post_allowed,
            "first_genuine_blocker": self.first_genuine_blocker,
            "blocker_class": self.blocker_class,
            "next_owner_go": self.next_owner_go,
            "secret_disclosed": self.secret_disclosed,
            "secret_persisted": self.secret_persisted,
        }


def attempt_governed_current_productive_k1_pre_post_productive_chain_v1(
    *,
    repo_root: Path | None = None,
    owner_go: str,
    envelope: FinalOrderEnvelopeV1,
    k1_backend: OsNativeStoreLookupBackendV1,
    post_owner_go: str | None = None,
    one_shot_real_post: bool = False,
) -> K1PrePostProductiveChainResultV1:
    """Run PRE-POST productive chain until POST admission boundary."""

    root = repo_root or Path(__file__).resolve().parents[2]
    admission = evaluate_k1_opaque_signing_handle_pre_post_admission_v1(repo_root=root)
    if admission.k1_pre_post_policy_granted is not True:
        post_eval = evaluate_real_venue_post_admission_v1(
            post_owner_go=post_owner_go,
            one_shot_real_post=one_shot_real_post,
            permit=None,
        )
        return K1PrePostProductiveChainResultV1(
            chain_status=STATUS_CHAIN_DENIED,
            real_keychain_access_authorized=False,
            real_credential_access_performed=False,
            credential_material_loaded=False,
            opaque_signing_handle_authorized=False,
            opaque_signing_handle_constructed=False,
            permit_mint_authorized=governed_permit_mint_authorized_v1(repo_root=root),
            permit_mint_performed=False,
            request_signing_authorized=False,
            request_signing_performed=False,
            pre_post_envelope_constructed=False,
            pre_post_validated=False,
            post_admission=post_eval,
            permit_id=None,
            pre_post_digest=None,
            secret_disclosed=False,
            secret_persisted=False,
            first_genuine_blocker=post_eval.first_real_blocker,
            blocker_class=BLOCKER_CLASS,
            next_owner_go=NEXT_OWNER_GO,
            reason_codes=admission.reason_codes,
        )

    permit_mint_auth = governed_permit_mint_authorized_v1(repo_root=root)
    permit: ExternalEffectPermitV1 | None = None
    permit_minted = False
    if permit_mint_auth:
        permit = issue_external_effect_permit_v1(envelope, authority_ref=POST_OWNER_GO)
        permit_minted = True

    request_url = f"https://{AUTHORIZED_HOST}{TRADE_ORDER_PATH}"
    pre_post: CurrentProductiveK1PrePostRequestEnvelopeV1 | None = None
    construction_performed = False
    signing_performed = False

    with governed_k1_opaque_signing_handle_construction_scope_v1(
        repo_root=root,
        owner_go=owner_go,
        backend=k1_backend,
    ) as (construction, session):
        if construction.construction_performed is not True or session is None:
            post_eval = evaluate_real_venue_post_admission_v1(
                post_owner_go=post_owner_go,
                one_shot_real_post=one_shot_real_post,
                permit=permit,
            )
            return K1PrePostProductiveChainResultV1(
                chain_status=STATUS_CHAIN_DENIED,
                real_keychain_access_authorized=admission.real_keychain_access_authorized,
                real_credential_access_performed=False,
                credential_material_loaded=False,
                opaque_signing_handle_authorized=admission.opaque_signing_handle_authorized,
                opaque_signing_handle_constructed=False,
                permit_mint_authorized=permit_mint_auth,
                permit_mint_performed=permit_minted,
                request_signing_authorized=admission.request_signing_authorized,
                request_signing_performed=False,
                pre_post_envelope_constructed=False,
                pre_post_validated=False,
                post_admission=post_eval,
                permit_id=permit.permit_id if permit else None,
                pre_post_digest=None,
                secret_disclosed=False,
                secret_persisted=False,
                first_genuine_blocker=post_eval.first_real_blocker,
                blocker_class=BLOCKER_CLASS,
                next_owner_go=NEXT_OWNER_GO,
                reason_codes=construction.reason_codes,
            )
        construction_performed = True
        if permit is None:
            post_eval = evaluate_real_venue_post_admission_v1(
                post_owner_go=post_owner_go,
                one_shot_real_post=one_shot_real_post,
                permit=None,
            )
            return K1PrePostProductiveChainResultV1(
                chain_status=STATUS_CHAIN_DENIED,
                real_keychain_access_authorized=admission.real_keychain_access_authorized,
                real_credential_access_performed=construction.real_credential_access_performed,
                credential_material_loaded=False,
                opaque_signing_handle_authorized=admission.opaque_signing_handle_authorized,
                opaque_signing_handle_constructed=True,
                permit_mint_authorized=permit_mint_auth,
                permit_mint_performed=False,
                request_signing_authorized=admission.request_signing_authorized,
                request_signing_performed=False,
                pre_post_envelope_constructed=False,
                pre_post_validated=False,
                post_admission=post_eval,
                permit_id=None,
                pre_post_digest=None,
                secret_disclosed=False,
                secret_persisted=False,
                first_genuine_blocker=post_eval.first_real_blocker,
                blocker_class=BLOCKER_CLASS,
                next_owner_go=NEXT_OWNER_GO,
                reason_codes=("PERMIT_MINT_NOT_AUTHORIZED",),
            )
        pre_post = build_and_validate_current_productive_k1_pre_post_request_envelope_v1(
            envelope=envelope,
            permit=permit,
            signing_handle=session.signing_handle,
            request_url=request_url,
            request_method="POST",
            request_body="",
        )
        signing_performed = pre_post.request_signing_performed is True

    pre_post_valid = False
    if pre_post is not None and permit is not None:
        pre_post_valid = validate_pre_post_envelope_bindings_v1(
            pre_post=pre_post,
            envelope=envelope,
            permit=permit,
        )

    post_eval = evaluate_real_venue_post_admission_v1(
        post_owner_go=post_owner_go,
        one_shot_real_post=one_shot_real_post,
        permit=permit,
    )

    if owner_go != OWNER_GO_TOKEN:
        return K1PrePostProductiveChainResultV1(
            chain_status=STATUS_CHAIN_DENIED,
            real_keychain_access_authorized=admission.real_keychain_access_authorized,
            real_credential_access_performed=construction_performed,
            credential_material_loaded=False,
            opaque_signing_handle_authorized=admission.opaque_signing_handle_authorized,
            opaque_signing_handle_constructed=construction_performed,
            permit_mint_authorized=permit_mint_auth,
            permit_mint_performed=permit_minted,
            request_signing_authorized=admission.request_signing_authorized,
            request_signing_performed=signing_performed,
            pre_post_envelope_constructed=pre_post is not None,
            pre_post_validated=pre_post_valid,
            post_admission=post_eval,
            permit_id=permit.permit_id if permit else None,
            pre_post_digest=pre_post.pre_post_digest if pre_post else None,
            secret_disclosed=False,
            secret_persisted=False,
            first_genuine_blocker=post_eval.first_real_blocker,
            blocker_class=BLOCKER_CLASS,
            next_owner_go=NEXT_OWNER_GO,
            reason_codes=("OWNER_GO_MISMATCH",),
        )

    return K1PrePostProductiveChainResultV1(
        chain_status=STATUS_CHAIN_STOPPED_POST_ADMISSION,
        real_keychain_access_authorized=admission.real_keychain_access_authorized,
        real_credential_access_performed=construction_performed,
        credential_material_loaded=False,
        opaque_signing_handle_authorized=admission.opaque_signing_handle_authorized,
        opaque_signing_handle_constructed=construction_performed,
        permit_mint_authorized=permit_mint_auth,
        permit_mint_performed=permit_minted,
        request_signing_authorized=admission.request_signing_authorized,
        request_signing_performed=signing_performed,
        pre_post_envelope_constructed=pre_post is not None,
        pre_post_validated=pre_post_valid,
        post_admission=post_eval,
        permit_id=permit.permit_id if permit else None,
        pre_post_digest=pre_post.pre_post_digest if pre_post else None,
        secret_disclosed=False,
        secret_persisted=False,
        first_genuine_blocker=post_eval.first_real_blocker,
        blocker_class=BLOCKER_CLASS if post_eval.post_admission_granted is not True else "",
        next_owner_go=NEXT_OWNER_GO if post_eval.post_admission_granted is not True else "",
        reason_codes=post_eval.reason_codes,
    )


__all__ = [
    "CHAIN_OWNER",
    "K1PrePostProductiveChainResultV1",
    "STATUS_CHAIN_STOPPED_POST_ADMISSION",
    "attempt_governed_current_productive_k1_pre_post_productive_chain_v1",
]
