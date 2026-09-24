"""F1/M9 real productive apply decision binding v1 (digest-bound, fail-closed).

A later Owner GO must set `real_productive_apply_authorized=true` **and** bind exactly one
`authorized_owner_apply_record_digest`. Chat tokens alone never authorize apply.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Final, Mapping

from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "f1_m9_real_productive_apply_decision_binding/v1"
DECISION_CONFIG: Final[str] = (
    "config/governance/f1_m9_productive_apply_execution_boundary_v1_decision_v1.json"
)
WORKPACKAGE_ID: Final[str] = "F1_M9_REAL_PRODUCTIVE_APPLY_GOVERNED_PREPARATION_V1"

BINDING_MODE_OWNER_APPLY_RECORD_DIGEST_REQUIRED: Final[str] = "OWNER_APPLY_RECORD_DIGEST_REQUIRED"

STATUS_NOT_AUTHORIZED: Final[str] = "REAL_PRODUCTIVE_APPLY_NOT_AUTHORIZED"
STATUS_DIGEST_MISSING: Final[str] = "AUTHORIZED_OWNER_APPLY_RECORD_DIGEST_MISSING"
STATUS_DIGEST_MISMATCH: Final[str] = "AUTHORIZED_OWNER_APPLY_RECORD_DIGEST_MISMATCH"
STATUS_BINDING_MODE_INVALID: Final[str] = "REAL_PRODUCTIVE_APPLY_BINDING_MODE_INVALID"
STATUS_BOUND: Final[str] = "REAL_PRODUCTIVE_APPLY_DECISION_BOUND"


class RealProductiveApplyDecisionBindingStatusV1(str, Enum):
    NOT_AUTHORIZED = STATUS_NOT_AUTHORIZED
    DIGEST_MISSING = STATUS_DIGEST_MISSING
    DIGEST_MISMATCH = STATUS_DIGEST_MISMATCH
    BINDING_MODE_INVALID = STATUS_BINDING_MODE_INVALID
    BOUND = STATUS_BOUND


@dataclass(frozen=True, slots=True)
class RealProductiveApplyDecisionBindingResultV1:
    binding_status: str
    reason_codes: tuple[str, ...]
    real_productive_apply_authorized: bool
    authorized_owner_apply_record_digest: str | None
    binding_mode: str
    apply_permitted: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "apply_permitted": self.apply_permitted,
            "authorized_owner_apply_record_digest": self.authorized_owner_apply_record_digest,
            "binding_mode": self.binding_mode,
            "binding_status": self.binding_status,
            "real_productive_apply_authorized": self.real_productive_apply_authorized,
            "reason_codes": list(self.reason_codes),
        }


def load_decision_binding_fields_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    from src.governance.f1_m9_productive_apply_execution_boundary_v1 import (
        load_execution_boundary_decision_v1,
    )

    decision = load_execution_boundary_decision_v1(repo_root=repo_root)
    mode = str(decision.get("real_productive_apply_binding_mode") or "")
    bound_digest = decision.get("authorized_owner_apply_record_digest")
    if bound_digest is not None and not isinstance(bound_digest, str):
        bound_digest = None
    return {
        "real_productive_apply_authorized": decision.get("real_productive_apply_authorized")
        is True,
        "authorized_owner_apply_record_digest": bound_digest,
        "real_productive_apply_binding_mode": mode,
        "governed_preparation_implemented": decision.get("governed_preparation_implemented")
        is True,
    }


def evaluate_real_productive_apply_decision_binding_v1(
    *,
    owner_apply_authorization_record_digest: str | None,
    repo_root: Path | None = None,
) -> RealProductiveApplyDecisionBindingResultV1:
    """Fail-closed: apply permitted only when decision flag + exact digest match."""
    fields = load_decision_binding_fields_v1(repo_root=repo_root)
    mode = fields["real_productive_apply_binding_mode"]
    flag = fields["real_productive_apply_authorized"]
    bound = fields["authorized_owner_apply_record_digest"]

    if mode != BINDING_MODE_OWNER_APPLY_RECORD_DIGEST_REQUIRED:
        return RealProductiveApplyDecisionBindingResultV1(
            binding_status=STATUS_BINDING_MODE_INVALID,
            reason_codes=(STATUS_BINDING_MODE_INVALID,),
            real_productive_apply_authorized=flag,
            authorized_owner_apply_record_digest=bound,
            binding_mode=mode,
            apply_permitted=False,
        )

    if not flag:
        return RealProductiveApplyDecisionBindingResultV1(
            binding_status=STATUS_NOT_AUTHORIZED,
            reason_codes=(STATUS_NOT_AUTHORIZED,),
            real_productive_apply_authorized=False,
            authorized_owner_apply_record_digest=bound,
            binding_mode=mode,
            apply_permitted=False,
        )

    if not isinstance(bound, str) or not is_valid_sha256_hex(bound):
        return RealProductiveApplyDecisionBindingResultV1(
            binding_status=STATUS_DIGEST_MISSING,
            reason_codes=(STATUS_DIGEST_MISSING,),
            real_productive_apply_authorized=True,
            authorized_owner_apply_record_digest=bound,
            binding_mode=mode,
            apply_permitted=False,
        )

    if not owner_apply_authorization_record_digest or not is_valid_sha256_hex(
        owner_apply_authorization_record_digest
    ):
        return RealProductiveApplyDecisionBindingResultV1(
            binding_status=STATUS_DIGEST_MISMATCH,
            reason_codes=(STATUS_DIGEST_MISMATCH,),
            real_productive_apply_authorized=True,
            authorized_owner_apply_record_digest=bound,
            binding_mode=mode,
            apply_permitted=False,
        )

    if owner_apply_authorization_record_digest != bound:
        return RealProductiveApplyDecisionBindingResultV1(
            binding_status=STATUS_DIGEST_MISMATCH,
            reason_codes=(STATUS_DIGEST_MISMATCH,),
            real_productive_apply_authorized=True,
            authorized_owner_apply_record_digest=bound,
            binding_mode=mode,
            apply_permitted=False,
        )

    return RealProductiveApplyDecisionBindingResultV1(
        binding_status=STATUS_BOUND,
        reason_codes=(STATUS_BOUND,),
        real_productive_apply_authorized=True,
        authorized_owner_apply_record_digest=bound,
        binding_mode=mode,
        apply_permitted=True,
    )


def prove_decision_binding_contract_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    path = root / DECISION_CONFIG
    if not path.is_file():
        return False
    decision = json.loads(path.read_text(encoding="utf-8"))
    if decision.get("governed_preparation_implemented") is not True:
        return False
    if (
        decision.get("real_productive_apply_binding_mode")
        != BINDING_MODE_OWNER_APPLY_RECORD_DIGEST_REQUIRED
    ):
        return False
    digest = decision.get("authorized_owner_apply_record_digest")
    flag = decision.get("real_productive_apply_authorized") is True
    if flag:
        if not isinstance(digest, str) or not is_valid_sha256_hex(digest):
            return False
        return True
    if digest is not None:
        return False
    return True


__all__ = [
    "BINDING_MODE_OWNER_APPLY_RECORD_DIGEST_REQUIRED",
    "RealProductiveApplyDecisionBindingResultV1",
    "RealProductiveApplyDecisionBindingStatusV1",
    "SCHEMA_VERSION",
    "STATUS_BOUND",
    "STATUS_DIGEST_MISSING",
    "STATUS_DIGEST_MISMATCH",
    "STATUS_NOT_AUTHORIZED",
    "WORKPACKAGE_ID",
    "evaluate_real_productive_apply_decision_binding_v1",
    "load_decision_binding_fields_v1",
    "prove_decision_binding_contract_v1",
]
