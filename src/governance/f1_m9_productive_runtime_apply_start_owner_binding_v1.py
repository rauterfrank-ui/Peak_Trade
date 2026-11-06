"""Owner-WP-bound real productive apply authorization for post-#6887 ratification lineage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from src.governance.f1_m9_productive_runtime_apply_start_artifacts_v1 import (
    load_owner_runtime_apply_start_wp_decision_v1,
)
from src.governance.f1_m9_real_productive_apply_decision_binding_v1 import (
    BINDING_MODE_OWNER_APPLY_RECORD_DIGEST_REQUIRED,
    RealProductiveApplyDecisionBindingResultV1,
    STATUS_BOUND,
    STATUS_DIGEST_MISMATCH,
    STATUS_DIGEST_MISSING,
    STATUS_NOT_AUTHORIZED,
    evaluate_real_productive_apply_decision_binding_v1,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "f1_m9_productive_runtime_apply_start_owner_binding/v1"


@dataclass(frozen=True, slots=True)
class ProductiveRuntimeApplyStartOwnerBindingResultV1:
    binding_status: str
    reason_codes: tuple[str, ...]
    apply_permitted: bool
    authorized_owner_apply_record_digest: str | None
    runtime_apply_start_owner_authorized: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "apply_permitted": self.apply_permitted,
            "authorized_owner_apply_record_digest": self.authorized_owner_apply_record_digest,
            "binding_status": self.binding_status,
            "reason_codes": list(self.reason_codes),
            "runtime_apply_start_owner_authorized": self.runtime_apply_start_owner_authorized,
        }


def evaluate_productive_runtime_apply_start_owner_binding_v1(
    *,
    owner_apply_authorization_record_digest: str | None,
    repo_root=None,
) -> ProductiveRuntimeApplyStartOwnerBindingResultV1:
    """Fail-closed: permit only when Owner WP authorizes start and digest matches."""
    from pathlib import Path

    root = repo_root or Path(__file__).resolve().parents[2]
    try:
        owner_wp = load_owner_runtime_apply_start_wp_decision_v1(repo_root=root)
    except (FileNotFoundError, ValueError) as exc:
        return ProductiveRuntimeApplyStartOwnerBindingResultV1(
            binding_status=STATUS_NOT_AUTHORIZED,
            reason_codes=(str(exc),),
            apply_permitted=False,
            authorized_owner_apply_record_digest=None,
            runtime_apply_start_owner_authorized=False,
        )

    if owner_wp.get("governed_productive_runtime_apply_start_authorized") is not True:
        return ProductiveRuntimeApplyStartOwnerBindingResultV1(
            binding_status=STATUS_NOT_AUTHORIZED,
            reason_codes=("RUNTIME_APPLY_START_NOT_OWNER_AUTHORIZED",),
            apply_permitted=False,
            authorized_owner_apply_record_digest=None,
            runtime_apply_start_owner_authorized=False,
        )

    bound = owner_wp.get("authorized_owner_apply_record_digest")
    if not isinstance(bound, str) or not is_valid_sha256_hex(bound):
        return ProductiveRuntimeApplyStartOwnerBindingResultV1(
            binding_status=STATUS_DIGEST_MISSING,
            reason_codes=(STATUS_DIGEST_MISSING,),
            apply_permitted=False,
            authorized_owner_apply_record_digest=bound if isinstance(bound, str) else None,
            runtime_apply_start_owner_authorized=True,
        )

    if not owner_apply_authorization_record_digest or not is_valid_sha256_hex(
        owner_apply_authorization_record_digest
    ):
        return ProductiveRuntimeApplyStartOwnerBindingResultV1(
            binding_status=STATUS_DIGEST_MISMATCH,
            reason_codes=(STATUS_DIGEST_MISMATCH,),
            apply_permitted=False,
            authorized_owner_apply_record_digest=bound,
            runtime_apply_start_owner_authorized=True,
        )

    if owner_apply_authorization_record_digest != bound:
        return ProductiveRuntimeApplyStartOwnerBindingResultV1(
            binding_status=STATUS_DIGEST_MISMATCH,
            reason_codes=(STATUS_DIGEST_MISMATCH, "POST_6887_APPLY_LINEAGE_DIGEST_REQUIRED"),
            apply_permitted=False,
            authorized_owner_apply_record_digest=bound,
            runtime_apply_start_owner_authorized=True,
        )

    return ProductiveRuntimeApplyStartOwnerBindingResultV1(
        binding_status=STATUS_BOUND,
        reason_codes=(STATUS_BOUND, "RUNTIME_APPLY_START_OWNER_WP_BOUND"),
        apply_permitted=True,
        authorized_owner_apply_record_digest=bound,
        runtime_apply_start_owner_authorized=True,
    )


def evaluate_real_productive_apply_with_runtime_apply_start_precedence_v1(
    *,
    owner_apply_authorization_record_digest: str | None,
    repo_root=None,
) -> RealProductiveApplyDecisionBindingResultV1:
    """Prefer post-#6887 runtime-apply-start Owner WP binding; else legacy boundary decision."""
    start = evaluate_productive_runtime_apply_start_owner_binding_v1(
        owner_apply_authorization_record_digest=owner_apply_authorization_record_digest,
        repo_root=repo_root,
    )
    if start.apply_permitted:
        return RealProductiveApplyDecisionBindingResultV1(
            binding_status=STATUS_BOUND,
            reason_codes=start.reason_codes,
            real_productive_apply_authorized=True,
            authorized_owner_apply_record_digest=start.authorized_owner_apply_record_digest,
            binding_mode=BINDING_MODE_OWNER_APPLY_RECORD_DIGEST_REQUIRED,
            apply_permitted=True,
        )
    return evaluate_real_productive_apply_decision_binding_v1(
        owner_apply_authorization_record_digest=owner_apply_authorization_record_digest,
        repo_root=repo_root,
    )


__all__ = [
    "SCHEMA_VERSION",
    "ProductiveRuntimeApplyStartOwnerBindingResultV1",
    "evaluate_productive_runtime_apply_start_owner_binding_v1",
    "evaluate_real_productive_apply_with_runtime_apply_start_precedence_v1",
]
