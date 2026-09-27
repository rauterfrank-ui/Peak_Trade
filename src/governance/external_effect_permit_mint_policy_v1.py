"""External Effect Permit Mint policy v1 — singular semantic authority.

Governed permit-mint **policy admission** on #6895 standing lift. Authorizes the
policy layer for envelope-bound single-use permit mint semantics only. Does **not**
perform runtime mint, credential access, venue POST, or autonomy POST.

RUNTIME_AUTHORIZATION_EFFECT=EXTERNAL_EFFECT_PERMIT_MINT_POLICY_ADMISSION_ONLY
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.standing_external_effect_lift_policy_v1 import (
    POLICY_RECORD_CONFIG as STANDING_LIFT_POLICY_RECORD_CONFIG,
    canonical_policy_record_body_v1 as canonical_standing_lift_body_v1,
    governed_standing_external_effect_authorized_v1,
    standing_external_effect_lift_granted_v1,
    validate_standing_external_effect_lift_policy_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST,
)
from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1.proof_v1 import (
    prove_pre_external_to_external_effect_boundary_v1,
)

POLICY_OWNER: Final[str] = "governance.external_effect_permit_mint_policy_v1"
SCHEMA_VERSION: Final[str] = "external_effect_permit_mint_policy/v1"
POLICY_ID: Final[str] = "EXTERNAL_EFFECT_PERMIT_MINT_POLICY_V1"
WORKPACKAGE_ID: Final[str] = "EXTERNAL_EFFECT_PERMIT_MINT_POLICY_V1"
NORMATIVE_SPEC: Final[str] = "docs/ops/specs/EXTERNAL_EFFECT_PERMIT_MINT_POLICY_V1.md"
POLICY_RECORD_CONFIG: Final[str] = (
    "config/governance/external_effect_permit_mint_policy_v1_record.json"
)
OWNER_GO_DECISION_CONFIG: Final[str] = (
    "config/governance/external_effect_permit_mint_owner_go_v1_decision.json"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/external_effect_permit_mint_policy_v1_decision_v1.json"
)

BASELINE_ORIGIN_MAIN_SHA: Final[str] = "03727c3cd09504beeedf4839b40dab3a26234331"

MINT_ENVELOPE: Final[str] = "GOVERNED_ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_PERMIT_MINT"
TARGET_PERMIT_MODULE: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/external_effect_permit_v1.py"
)
TARGET_PERMIT_DURABLE_CONSUME_MODULE: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/external_effect_permit_durable_consume_v1.py"
)
TARGET_PERMIT_MINT_GATE_BINDING_MODULE: Final[str] = (
    "src/governance/external_effect_permit_mint_gate_binding_v1.py"
)
BOUND_STANDING_LIFT_POLICY_RECORD_DIGEST: Final[str] = (
    "6a8c32c5ed040367c74f8f204c27a1ead7408c94915776d148bdcf22aa45d7cc"
)

STATUS_POLICY_VALID: Final[str] = "EXTERNAL_EFFECT_PERMIT_MINT_POLICY_VALID"
STATUS_POLICY_DENIED: Final[str] = "EXTERNAL_EFFECT_PERMIT_MINT_POLICY_DENIED_FAIL_CLOSED"
STATUS_MINT_ADMISSION_GRANTED: Final[str] = "EXTERNAL_EFFECT_PERMIT_MINT_ADMISSION_GRANTED"
STATUS_MINT_ADMISSION_DENIED: Final[str] = (
    "EXTERNAL_EFFECT_PERMIT_MINT_ADMISSION_DENIED_FAIL_CLOSED"
)

PERMIT_POLICY_AUTHORIZED_BY_POLICY: Final[bool] = True
PERMIT_MINT_AUTHORIZED_BY_POLICY: Final[bool] = True
PERMIT_MINT_CAPABILITY_IMPLEMENTED_BY_POLICY: Final[bool] = True
PERMIT_MINT_PERFORMED_BY_POLICY: Final[bool] = False
CREDENTIAL_ACCESS_AUTHORIZED_BY_POLICY: Final[bool] = False
CREDENTIAL_ACCESS_PERFORMED_BY_POLICY: Final[bool] = False
POST_ALLOWED_BY_POLICY: Final[bool] = False
REAL_VENUE_POST_ALLOWED_BY_POLICY: Final[bool] = False
AUTONOMY_CAN_MINT_PERMIT_BY_POLICY: Final[bool] = False
AUTONOMY_CAN_POST_BY_POLICY: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class ExternalEffectPermitMintPolicyValidationResultV1:
    policy_status: str
    permit_policy_authorized: bool
    policy_record_digest: str | None
    standing_lift_policy_digest: str | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExternalEffectPermitMintAdmissionResultV1:
    admission_status: str
    permit_mint_policy_granted: bool
    governed_permit_mint_authorized: bool
    standing_lift_granted: bool
    governed_standing_external_effect_authorized: bool
    pre_external_boundary_proven: bool
    policy_record_digest: str | None
    reason_codes: tuple[str, ...]
    permit_policy_authorized: bool
    permit_mint_authorized: bool
    permit_mint_capability_implemented: bool
    permit_mint_performed: bool
    credential_access_authorized: bool
    credential_access_performed: bool
    post_allowed: bool
    real_venue_post_allowed: bool
    autonomy_can_mint_permit: bool
    autonomy_can_post: bool
    import_time_standing_constant: bool


def _load_json(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_external_effect_permit_mint_policy_record_v1(
    *, repo_root: Path | None = None
) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    return _load_json(root, POLICY_RECORD_CONFIG)


def canonical_policy_record_body_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "policy_record_digest"}


def _standing_lift_digest(root: Path) -> str | None:
    record = _load_json(root, STANDING_LIFT_POLICY_RECORD_CONFIG)
    if not record:
        return None
    return compute_content_sha256(canonical_standing_lift_body_v1(record))


def validate_external_effect_permit_mint_policy_record_v1(
    *, repo_root: Path | None = None
) -> ExternalEffectPermitMintPolicyValidationResultV1:
    root = repo_root or _REPO_ROOT
    reasons: list[str] = []
    record = load_external_effect_permit_mint_policy_record_v1(repo_root=root)
    if not record:
        return ExternalEffectPermitMintPolicyValidationResultV1(
            policy_status=STATUS_POLICY_DENIED,
            permit_policy_authorized=False,
            policy_record_digest=None,
            standing_lift_policy_digest=None,
            reason_codes=("POLICY_RECORD_MISSING",),
        )

    expected_digest = str(record.get("policy_record_digest") or "")
    body = canonical_policy_record_body_v1(record)
    computed_digest = compute_content_sha256(body)
    if not is_valid_sha256_hex(expected_digest) or expected_digest != computed_digest:
        reasons.append("POLICY_RECORD_DIGEST_MISMATCH")

    if record.get("schema_version") != SCHEMA_VERSION:
        reasons.append("SCHEMA_VERSION_MISMATCH")
    if record.get("policy_id") != POLICY_ID:
        reasons.append("POLICY_ID_MISMATCH")
    if record.get("policy_owner") != POLICY_OWNER:
        reasons.append("POLICY_OWNER_MISMATCH")
    if record.get("external_effect_permit_mint_authorized") is not True:
        reasons.append("PERMIT_MINT_NOT_AUTHORIZED_IN_RECORD")
    if record.get("baseline_origin_main_sha") != BASELINE_ORIGIN_MAIN_SHA:
        reasons.append("BASELINE_SHA_MISMATCH")
    if record.get("mint_envelope") != MINT_ENVELOPE:
        reasons.append("MINT_ENVELOPE_MISMATCH")
    if record.get("target_permit_module") != TARGET_PERMIT_MODULE:
        reasons.append("PERMIT_MODULE_MISMATCH")
    if record.get("target_permit_durable_consume_module") != TARGET_PERMIT_DURABLE_CONSUME_MODULE:
        reasons.append("PERMIT_DURABLE_CONSUME_MODULE_MISMATCH")
    if (
        record.get("target_permit_mint_gate_binding_module")
        != TARGET_PERMIT_MINT_GATE_BINDING_MODULE
    ):
        reasons.append("PERMIT_MINT_GATE_BINDING_MODULE_MISMATCH")

    non_impl = record.get("explicit_non_implications")
    if not isinstance(non_impl, dict):
        reasons.append("EXPLICIT_NON_IMPLICATIONS_MISSING")
    else:
        for key, expected in (
            ("permit_mint_performed", False),
            ("credential_access_authorized", False),
            ("credential_access_performed", False),
            ("post_allowed", False),
            ("real_venue_post_allowed", False),
            ("autonomy_can_mint_permit", False),
            ("autonomy_can_post", False),
        ):
            if non_impl.get(key) is not expected:
                reasons.append(f"NON_IMPLICATION_{key.upper()}")

    lift_digest: str | None = None
    lineage = record.get("bound_lineage")
    if not isinstance(lineage, dict):
        reasons.append("BOUND_LINEAGE_MISSING")
    else:
        if lineage.get("standing_external_effect_lift_policy_record_config") != (
            STANDING_LIFT_POLICY_RECORD_CONFIG
        ):
            reasons.append("STANDING_LIFT_POLICY_PATH_MISMATCH")
        lift_digest = _standing_lift_digest(root)
        bound_lift = str(lineage.get("standing_external_effect_lift_policy_record_digest") or "")
        if not lift_digest or bound_lift != lift_digest:
            reasons.append("STANDING_LIFT_POLICY_DIGEST_MISMATCH")
        if bound_lift != BOUND_STANDING_LIFT_POLICY_RECORD_DIGEST:
            reasons.append("STANDING_LIFT_POLICY_DIGEST_CONSTANT_MISMATCH")

    if not standing_external_effect_lift_granted_v1(repo_root=root):
        reasons.append("STANDING_LIFT_PREREQUISITE_INVALID")
    if (
        validate_standing_external_effect_lift_policy_record_v1(
            repo_root=root
        ).lift_policy_authorized
        is not True
    ):
        reasons.append("STANDING_LIFT_POLICY_DENIED")

    owner = _load_json(root, OWNER_GO_DECISION_CONFIG)
    if owner.get("external_effect_permit_mint_owner_go") is not True:
        reasons.append("OWNER_GO_DECISION_NOT_CONSUMED")

    authorized = not reasons and record.get("external_effect_permit_mint_authorized") is True
    return ExternalEffectPermitMintPolicyValidationResultV1(
        policy_status=STATUS_POLICY_VALID if authorized else STATUS_POLICY_DENIED,
        permit_policy_authorized=authorized,
        policy_record_digest=computed_digest if is_valid_sha256_hex(computed_digest) else None,
        standing_lift_policy_digest=lift_digest,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def external_effect_permit_mint_policy_granted_v1(*, repo_root: Path | None = None) -> bool:
    return (
        validate_external_effect_permit_mint_policy_record_v1(
            repo_root=repo_root
        ).permit_policy_authorized
        is True
    )


def governed_permit_mint_authorized_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    return external_effect_permit_mint_policy_granted_v1(repo_root=root) and (
        governed_standing_external_effect_authorized_v1(repo_root=root) is True
    )


def evaluate_external_effect_permit_mint_admission_v1(
    *, repo_root: Path | None = None
) -> ExternalEffectPermitMintAdmissionResultV1:
    root = repo_root or _REPO_ROOT
    policy = validate_external_effect_permit_mint_policy_record_v1(repo_root=root)
    reasons = list(policy.reason_codes)

    pre_external = prove_pre_external_to_external_effect_boundary_v1()
    pre_external_ok = pre_external.ok is True
    if not pre_external_ok:
        reasons.append("PRE_EXTERNAL_BOUNDARY_PROOF_FAILED")

    lift_granted = standing_external_effect_lift_granted_v1(repo_root=root)
    governed_standing = governed_standing_external_effect_authorized_v1(repo_root=root)
    if not lift_granted:
        reasons.append("STANDING_LIFT_NOT_GRANTED")
    if not governed_standing:
        reasons.append("GOVERNED_STANDING_EXTERNAL_EFFECT_NOT_AUTHORIZED")

    governed_mint = False
    if policy.permit_policy_authorized and pre_external_ok and governed_standing:
        governed_mint = True
        if EXTERNAL_EFFECT_AUTHORIZED is True:
            reasons.append("IMPORT_TIME_STANDING_CONSTANT_MUST_REMAIN_FALSE")

    granted = (
        policy.permit_policy_authorized is True
        and pre_external_ok
        and lift_granted
        and governed_standing
        and governed_mint
        and not reasons
    )
    return ExternalEffectPermitMintAdmissionResultV1(
        admission_status=STATUS_MINT_ADMISSION_GRANTED if granted else STATUS_MINT_ADMISSION_DENIED,
        permit_mint_policy_granted=granted,
        governed_permit_mint_authorized=governed_mint and not reasons,
        standing_lift_granted=lift_granted,
        governed_standing_external_effect_authorized=governed_standing,
        pre_external_boundary_proven=pre_external_ok,
        policy_record_digest=policy.policy_record_digest,
        reason_codes=tuple(dict.fromkeys(reasons)),
        permit_policy_authorized=PERMIT_POLICY_AUTHORIZED_BY_POLICY and granted,
        permit_mint_authorized=PERMIT_MINT_AUTHORIZED_BY_POLICY and granted,
        permit_mint_capability_implemented=PERMIT_MINT_CAPABILITY_IMPLEMENTED_BY_POLICY,
        permit_mint_performed=PERMIT_MINT_PERFORMED_BY_POLICY,
        credential_access_authorized=CREDENTIAL_ACCESS_AUTHORIZED_BY_POLICY,
        credential_access_performed=CREDENTIAL_ACCESS_PERFORMED_BY_POLICY,
        post_allowed=POST_ALLOWED_BY_POLICY,
        real_venue_post_allowed=REAL_VENUE_POST_ALLOWED_BY_POLICY,
        autonomy_can_mint_permit=AUTONOMY_CAN_MINT_PERMIT_BY_POLICY,
        autonomy_can_post=AUTONOMY_CAN_POST_BY_POLICY,
        import_time_standing_constant=EXTERNAL_EFFECT_AUTHORIZED is True,
    )


def prove_permit_mint_does_not_perform_runtime_mint_v1() -> bool:
    return PERMIT_MINT_PERFORMED_BY_POLICY is False


def prove_permit_mint_does_not_authorize_credential_access_v1() -> bool:
    return (
        CREDENTIAL_ACCESS_AUTHORIZED_BY_POLICY is False
        and CREDENTIAL_ACCESS_PERFORMED_BY_POLICY is False
    )


def prove_permit_mint_does_not_authorize_real_venue_post_v1() -> bool:
    if POST_ALLOWED_BY_POLICY is True or REAL_VENUE_POST_ALLOWED_BY_POLICY is True:
        return False
    if POST_ALLOWED is not False or REAL_VENUE_POST_ALLOWED is not False:
        return False
    if AUTONOMY_CAN_POST is not False:
        return False
    return True


def prove_import_time_autonomy_can_mint_permit_unchanged_v1() -> bool:
    return AUTONOMY_CAN_MINT_PERMIT is False


__all__ = [
    "BASELINE_ORIGIN_MAIN_SHA",
    "DECISION_CONFIG",
    "MINT_ENVELOPE",
    "NORMATIVE_SPEC",
    "OWNER_GO_DECISION_CONFIG",
    "PERMIT_MINT_AUTHORIZED_BY_POLICY",
    "PERMIT_MINT_CAPABILITY_IMPLEMENTED_BY_POLICY",
    "PERMIT_MINT_PERFORMED_BY_POLICY",
    "PERMIT_POLICY_AUTHORIZED_BY_POLICY",
    "POLICY_ID",
    "POLICY_OWNER",
    "POLICY_RECORD_CONFIG",
    "ExternalEffectPermitMintAdmissionResultV1",
    "ExternalEffectPermitMintPolicyValidationResultV1",
    "WORKPACKAGE_ID",
    "canonical_policy_record_body_v1",
    "evaluate_external_effect_permit_mint_admission_v1",
    "external_effect_permit_mint_policy_granted_v1",
    "governed_permit_mint_authorized_v1",
    "load_external_effect_permit_mint_policy_record_v1",
    "prove_import_time_autonomy_can_mint_permit_unchanged_v1",
    "prove_permit_mint_does_not_authorize_credential_access_v1",
    "prove_permit_mint_does_not_authorize_real_venue_post_v1",
    "prove_permit_mint_does_not_perform_runtime_mint_v1",
    "validate_external_effect_permit_mint_policy_record_v1",
]
