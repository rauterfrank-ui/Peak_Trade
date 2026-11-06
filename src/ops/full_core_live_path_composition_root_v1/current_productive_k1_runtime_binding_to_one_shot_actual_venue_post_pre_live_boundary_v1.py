"""K1 PRE-POST runtime binding to one-shot actual venue POST pre-live boundary.

Binds governed K1 opaque signing + PRE-POST productive chain to DM-slice
pre-live readiness checks. Does not consume POST Owner-GO, durable permit, or
venue socket. Separate K1 and POST Owner-GO literals required.

RUNTIME_AUTHORIZATION_EFFECT=K1_RUNTIME_BINDING_PRE_LIVE_PROOF_ONLY
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.governance.current_productive_k1_pre_post_productive_chain_v1 import (
    STATUS_CHAIN_DENIED,
    STATUS_CHAIN_STOPPED_POST_ADMISSION,
    attempt_governed_current_productive_k1_pre_post_productive_chain_v1,
)
from src.governance.current_productive_k1_opaque_signing_handle_pre_post_policy_v1 import (
    OWNER_GO_TOKEN as K1_OWNER_GO_TOKEN,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    MacosSecurityFrameworkLookupBackendV1,
    OsNativeStoreLookupBackendV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1 import (
    OWNER_GO as K1_OPAQUE_SIGNING_OWNER_GO,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    prove_one_shot_join_standing_boundary_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    OWNER_GO as POST_OWNER_GO,
    prove_pre_live_actual_venue_post_readiness_v1,
)

THIS_SLICE = (
    "11.2.1.DO.FULL_CORE_CURRENT_PRODUCTIVE_K1_RUNTIME_BINDING_TO_ONE_SHOT_"
    "ACTUAL_VENUE_POST_PRE_LIVE_BOUNDARY_V1"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"


class K1RuntimeBindingOneShotPostPreLiveBoundaryError(RuntimeError):
    """Fail-closed K1 runtime binding / pre-live boundary violation."""


@dataclass(frozen=True)
class K1RuntimeBindingOneShotPostPreLiveBoundaryResultV1:
    document_class: str
    baseline_origin_main_sha: str
    k1_owner_go_status: str
    post_owner_go_status: str
    k1_chain_status: str
    k1_pre_post_validated: str
    k1_backend_bound: str
    pre_live_proof_complete: str
    permit_minted_in_memory: str
    permit_consumed_durable: str
    real_venue_post_attempted: str
    real_venue_post_performed: str
    real_order_submission: str
    live_funds_exposure: str
    next_true_blocker: str

    def to_public_dict_v1(self) -> dict[str, str]:
        return {
            "DOCUMENT_CLASS": self.document_class,
            "BASELINE_ORIGIN_MAIN_SHA": self.baseline_origin_main_sha,
            "K1_OWNER_GO_STATUS": self.k1_owner_go_status,
            "POST_OWNER_GO_STATUS": self.post_owner_go_status,
            "K1_CHAIN_STATUS": self.k1_chain_status,
            "K1_PRE_POST_VALIDATED": self.k1_pre_post_validated,
            "K1_BACKEND_BOUND": self.k1_backend_bound,
            "PRE_LIVE_PROOF_COMPLETE": self.pre_live_proof_complete,
            "PERMIT_MINTED_IN_MEMORY": self.permit_minted_in_memory,
            "PERMIT_CONSUMED_DURABLE": self.permit_consumed_durable,
            "REAL_VENUE_POST_ATTEMPTED": self.real_venue_post_attempted,
            "REAL_VENUE_POST_PERFORMED": self.real_venue_post_performed,
            "REAL_ORDER_SUBMISSION": self.real_order_submission,
            "LIVE_FUNDS_EXPOSURE": self.live_funds_exposure,
            "NEXT_TRUE_BLOCKER": self.next_true_blocker,
        }


def _assert_standing_boundary_v1() -> None:
    prove_one_shot_join_standing_boundary_v1()


def resolve_macos_security_framework_k1_lookup_backend_v1(
    *, k1_owner_go: str
) -> OsNativeStoreLookupBackendV1:
    """Return macOS lookup backend only when K1 Owner-GO matches canonical literal."""

    if str(k1_owner_go or "") != K1_OPAQUE_SIGNING_OWNER_GO:
        raise K1RuntimeBindingOneShotPostPreLiveBoundaryError("K1_OWNER_GO_MISMATCH")
    if str(k1_owner_go or "") != K1_OWNER_GO_TOKEN:
        raise K1RuntimeBindingOneShotPostPreLiveBoundaryError("K1_OWNER_GO_POLICY_TOKEN_MISMATCH")
    return MacosSecurityFrameworkLookupBackendV1()


def _resolve_k1_backend_v1(
    *,
    k1_owner_go: str,
    k1_backend: OsNativeStoreLookupBackendV1 | None,
    use_macos_security_framework: bool,
) -> OsNativeStoreLookupBackendV1:
    if use_macos_security_framework is True:
        return resolve_macos_security_framework_k1_lookup_backend_v1(k1_owner_go=k1_owner_go)
    if k1_backend is not None:
        return k1_backend
    raise K1RuntimeBindingOneShotPostPreLiveBoundaryError("K1_BACKEND_REQUIRED")


def attempt_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1(
    *,
    k1_owner_go: str,
    post_owner_go: str,
    baseline_origin_main_sha: str,
    envelope: FinalOrderEnvelopeV1,
    store_root: Path | str,
    k1_backend: OsNativeStoreLookupBackendV1 | None = None,
    use_macos_security_framework: bool = False,
    repo_root: Path | None = None,
) -> K1RuntimeBindingOneShotPostPreLiveBoundaryResultV1:
    """K1 PRE-POST chain + DM pre-live proof. No POST, no durable permit consume."""

    _assert_standing_boundary_v1()
    if str(baseline_origin_main_sha or "") != EXPECTED_BASELINE_ORIGIN_MAIN_SHA:
        raise K1RuntimeBindingOneShotPostPreLiveBoundaryError("BASELINE_SHA_MISMATCH")
    if str(k1_owner_go or "") != K1_OPAQUE_SIGNING_OWNER_GO:
        raise K1RuntimeBindingOneShotPostPreLiveBoundaryError("K1_OWNER_GO_MISMATCH")
    if str(post_owner_go or "") != POST_OWNER_GO:
        raise K1RuntimeBindingOneShotPostPreLiveBoundaryError("POST_OWNER_GO_MISMATCH")
    assert_envelope_unmodified_v1(envelope)
    root = Path(store_root)
    root.mkdir(parents=True, exist_ok=True)
    backend = _resolve_k1_backend_v1(
        k1_owner_go=k1_owner_go,
        k1_backend=k1_backend,
        use_macos_security_framework=use_macos_security_framework,
    )
    chain = attempt_governed_current_productive_k1_pre_post_productive_chain_v1(
        repo_root=repo_root,
        owner_go=k1_owner_go,
        envelope=envelope,
        k1_backend=backend,
        post_owner_go=None,
        one_shot_real_post=False,
    )
    if chain.chain_status not in (
        STATUS_CHAIN_STOPPED_POST_ADMISSION,
        STATUS_CHAIN_DENIED,
    ):
        raise K1RuntimeBindingOneShotPostPreLiveBoundaryError("K1_CHAIN_UNEXPECTED_STATUS")
    if chain.pre_post_validated is not True:
        raise K1RuntimeBindingOneShotPostPreLiveBoundaryError("K1_PRE_POST_NOT_VALIDATED")
    pre = prove_pre_live_actual_venue_post_readiness_v1(
        owner_go=post_owner_go,
        baseline_origin_main_sha=baseline_origin_main_sha,
        envelope=envelope,
        store_root=root,
        k1_backend=backend,
    )
    pre_live_ok = pre.get("PRE_LIVE_PROOF_COMPLETE") == TRUE_TOKEN
    permit_minted = (
        TRUE_TOKEN
        if chain.permit_mint_performed is True or pre.get("SINGLE_USE_PERMIT_MINTED") == TRUE_TOKEN
        else FALSE_TOKEN
    )
    return K1RuntimeBindingOneShotPostPreLiveBoundaryResultV1(
        document_class=THIS_SLICE,
        baseline_origin_main_sha=baseline_origin_main_sha,
        k1_owner_go_status="RECOGNIZED_NOT_DURABLE_CONSUMED",
        post_owner_go_status="RECOGNIZED_NOT_DURABLE_CONSUMED",
        k1_chain_status=str(chain.chain_status),
        k1_pre_post_validated=TRUE_TOKEN,
        k1_backend_bound=TRUE_TOKEN,
        pre_live_proof_complete=TRUE_TOKEN if pre_live_ok else FALSE_TOKEN,
        permit_minted_in_memory=permit_minted,
        permit_consumed_durable=FALSE_TOKEN,
        real_venue_post_attempted=FALSE_TOKEN,
        real_venue_post_performed=FALSE_TOKEN,
        real_order_submission=FALSE_TOKEN,
        live_funds_exposure=FALSE_TOKEN,
        next_true_blocker=str(chain.next_owner_go or chain.first_genuine_blocker),
    )


__all__ = [
    "EXPECTED_BASELINE_ORIGIN_MAIN_SHA",
    "K1_OPAQUE_SIGNING_OWNER_GO",
    "K1RuntimeBindingOneShotPostPreLiveBoundaryError",
    "K1RuntimeBindingOneShotPostPreLiveBoundaryResultV1",
    "POST_OWNER_GO",
    "THIS_SLICE",
    "attempt_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1",
    "resolve_macos_security_framework_k1_lookup_backend_v1",
]
