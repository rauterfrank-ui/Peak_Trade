"""Checkout-independent credential access policy v1 — singular semantic authority.

Governed credential-access **policy admission** on #6896 permit-mint policy.
Authorizes the policy layer for checkout-independent credential capability
semantics only. Does **not** load secrets, perform real Keychain access,
mint permits at runtime, or authorize POST.

RUNTIME_AUTHORIZATION_EFFECT=CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_POLICY_ADMISSION_ONLY
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.external_effect_permit_mint_policy_v1 import (
    POLICY_RECORD_CONFIG as PERMIT_MINT_POLICY_RECORD_CONFIG,
    canonical_policy_record_body_v1 as canonical_permit_mint_body_v1,
    governed_permit_mint_authorized_v1,
    validate_external_effect_permit_mint_policy_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    CHECKOUT_INDEPENDENT_PRODUCTIVE_PROVIDER_ACTIVE,
    PRODUCTIVE_BACKEND_JOINED,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    MATERIAL_LOADED_TRUE_REACHABLE,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
)
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

POLICY_OWNER: Final[str] = "governance.checkout_independent_credential_access_policy_v1"
SCHEMA_VERSION: Final[str] = "checkout_independent_credential_access_policy/v1"
POLICY_ID: Final[str] = "CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_POLICY_V1"
WORKPACKAGE_ID: Final[str] = "CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_POLICY_V1"
NORMATIVE_SPEC: Final[str] = "docs/ops/specs/CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_POLICY_V1.md"
POLICY_RECORD_CONFIG: Final[str] = (
    "config/governance/checkout_independent_credential_access_policy_v1_record.json"
)
OWNER_GO_DECISION_CONFIG: Final[str] = (
    "config/governance/checkout_independent_credential_access_owner_go_v1_decision.json"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/checkout_independent_credential_access_policy_v1_decision_v1.json"
)

BASELINE_ORIGIN_MAIN_SHA: Final[str] = "e92e5cb088f0e1dbdb83d37f40b9e90293cca127"

ACCESS_ENVELOPE: Final[str] = "GOVERNED_CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_POLICY"
TARGET_CAPABILITY_MODULE: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/checkout_independent_credential_capability_v1.py"
)
TARGET_SOURCE_BACKEND_MODULE: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "checkout_independent_credential_source_backend_kind_v1.py"
)
TARGET_OS_NATIVE_ACQUISITION_MODULE: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "checkout_independent_credential_os_native_store_acquisition_v1.py"
)
TARGET_CREDENTIAL_ACCESS_GATE_BINDING_MODULE: Final[str] = (
    "src/governance/checkout_independent_credential_access_gate_binding_v1.py"
)
BOUND_PERMIT_MINT_POLICY_RECORD_DIGEST: Final[str] = (
    "1d152187de0cb587cc3a35628aee48c79552926adb8aeaae827ddfac1e064ed0"
)

STATUS_POLICY_VALID: Final[str] = "CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_POLICY_VALID"
STATUS_POLICY_DENIED: Final[str] = (
    "CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_POLICY_DENIED_FAIL_CLOSED"
)
STATUS_ADMISSION_GRANTED: Final[str] = "CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_ADMISSION_GRANTED"
STATUS_ADMISSION_DENIED: Final[str] = (
    "CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_ADMISSION_DENIED_FAIL_CLOSED"
)

CREDENTIAL_ACCESS_POLICY_AUTHORIZED_BY_POLICY: Final[bool] = True
CREDENTIAL_ACCESS_AUTHORIZED_BY_POLICY: Final[bool] = True
CREDENTIAL_ACCESS_CAPABILITY_IMPLEMENTED_BY_POLICY: Final[bool] = True
CREDENTIAL_ACCESS_PERFORMED_BY_POLICY: Final[bool] = False
REAL_CREDENTIAL_ACCESS_PERFORMED_BY_POLICY: Final[bool] = False
REAL_SECRET_LOAD_PERFORMED_BY_POLICY: Final[bool] = False
CREDENTIAL_MATERIAL_LOADED_BY_POLICY: Final[bool] = False
POST_ALLOWED_BY_POLICY: Final[bool] = False
REAL_VENUE_POST_ALLOWED_BY_POLICY: Final[bool] = False
PERMIT_MINT_PERFORMED_BY_POLICY: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class CheckoutIndependentCredentialAccessPolicyValidationResultV1:
    policy_status: str
    credential_access_policy_authorized: bool
    policy_record_digest: str | None
    permit_mint_policy_digest: str | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CheckoutIndependentCredentialAccessAdmissionResultV1:
    admission_status: str
    credential_access_policy_granted: bool
    governed_credential_access_authorized: bool
    governed_permit_mint_authorized: bool
    pre_external_boundary_proven: bool
    policy_record_digest: str | None
    reason_codes: tuple[str, ...]
    credential_access_policy_authorized: bool
    credential_access_authorized: bool
    credential_access_capability_implemented: bool
    credential_access_performed: bool
    real_credential_access_performed: bool
    real_secret_load_performed: bool
    credential_material_loaded: bool
    post_allowed: bool
    real_venue_post_allowed: bool
    permit_mint_performed: bool
    autonomy_can_mint_permit: bool
    autonomy_can_post: bool


def _load_json(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_checkout_independent_credential_access_policy_record_v1(
    *, repo_root: Path | None = None
) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    return _load_json(root, POLICY_RECORD_CONFIG)


def canonical_policy_record_body_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "policy_record_digest"}


def _permit_mint_digest(root: Path) -> str | None:
    record = _load_json(root, PERMIT_MINT_POLICY_RECORD_CONFIG)
    if not record:
        return None
    return compute_content_sha256(canonical_permit_mint_body_v1(record))


def validate_checkout_independent_credential_access_policy_record_v1(
    *, repo_root: Path | None = None
) -> CheckoutIndependentCredentialAccessPolicyValidationResultV1:
    root = repo_root or _REPO_ROOT
    reasons: list[str] = []
    record = load_checkout_independent_credential_access_policy_record_v1(repo_root=root)
    if not record:
        return CheckoutIndependentCredentialAccessPolicyValidationResultV1(
            policy_status=STATUS_POLICY_DENIED,
            credential_access_policy_authorized=False,
            policy_record_digest=None,
            permit_mint_policy_digest=None,
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
    if record.get("checkout_independent_credential_access_authorized") is not True:
        reasons.append("CREDENTIAL_ACCESS_NOT_AUTHORIZED_IN_RECORD")
    if record.get("baseline_origin_main_sha") != BASELINE_ORIGIN_MAIN_SHA:
        reasons.append("BASELINE_SHA_MISMATCH")
    if record.get("access_envelope") != ACCESS_ENVELOPE:
        reasons.append("ACCESS_ENVELOPE_MISMATCH")
    if record.get("target_capability_module") != TARGET_CAPABILITY_MODULE:
        reasons.append("CAPABILITY_MODULE_MISMATCH")
    if record.get("target_source_backend_module") != TARGET_SOURCE_BACKEND_MODULE:
        reasons.append("SOURCE_BACKEND_MODULE_MISMATCH")
    if record.get("target_os_native_acquisition_module") != TARGET_OS_NATIVE_ACQUISITION_MODULE:
        reasons.append("OS_NATIVE_ACQUISITION_MODULE_MISMATCH")
    if (
        record.get("target_credential_access_gate_binding_module")
        != TARGET_CREDENTIAL_ACCESS_GATE_BINDING_MODULE
    ):
        reasons.append("CREDENTIAL_ACCESS_GATE_BINDING_MODULE_MISMATCH")

    non_impl = record.get("explicit_non_implications")
    if not isinstance(non_impl, dict):
        reasons.append("EXPLICIT_NON_IMPLICATIONS_MISSING")
    else:
        for key, expected in (
            ("credential_access_performed", False),
            ("real_credential_access_performed", False),
            ("real_secret_load_performed", False),
            ("credential_material_loaded", False),
            ("real_keychain_access_authorized", False),
            ("permit_mint_performed", False),
            ("post_allowed", False),
            ("real_venue_post_allowed", False),
            ("autonomy_can_mint_permit", False),
            ("autonomy_can_post", False),
        ):
            if non_impl.get(key) is not expected:
                reasons.append(f"NON_IMPLICATION_{key.upper()}")

    mint_digest: str | None = None
    lineage = record.get("bound_lineage")
    if not isinstance(lineage, dict):
        reasons.append("BOUND_LINEAGE_MISSING")
    else:
        if lineage.get("external_effect_permit_mint_policy_record_config") != (
            PERMIT_MINT_POLICY_RECORD_CONFIG
        ):
            reasons.append("PERMIT_MINT_POLICY_PATH_MISMATCH")
        mint_digest = _permit_mint_digest(root)
        bound_mint = str(lineage.get("external_effect_permit_mint_policy_record_digest") or "")
        if not mint_digest or bound_mint != mint_digest:
            reasons.append("PERMIT_MINT_POLICY_DIGEST_MISMATCH")
        if bound_mint != BOUND_PERMIT_MINT_POLICY_RECORD_DIGEST:
            reasons.append("PERMIT_MINT_POLICY_DIGEST_CONSTANT_MISMATCH")

    if not governed_permit_mint_authorized_v1(repo_root=root):
        reasons.append("PERMIT_MINT_PREREQUISITE_INVALID")
    if (
        validate_external_effect_permit_mint_policy_record_v1(
            repo_root=root
        ).permit_policy_authorized
        is not True
    ):
        reasons.append("PERMIT_MINT_POLICY_DENIED")

    owner = _load_json(root, OWNER_GO_DECISION_CONFIG)
    if owner.get("checkout_independent_credential_access_owner_go") is not True:
        reasons.append("OWNER_GO_DECISION_NOT_CONSUMED")

    authorized = (
        not reasons and record.get("checkout_independent_credential_access_authorized") is True
    )
    return CheckoutIndependentCredentialAccessPolicyValidationResultV1(
        policy_status=STATUS_POLICY_VALID if authorized else STATUS_POLICY_DENIED,
        credential_access_policy_authorized=authorized,
        policy_record_digest=computed_digest if is_valid_sha256_hex(computed_digest) else None,
        permit_mint_policy_digest=mint_digest,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def checkout_independent_credential_access_policy_granted_v1(
    *, repo_root: Path | None = None
) -> bool:
    return (
        validate_checkout_independent_credential_access_policy_record_v1(
            repo_root=repo_root
        ).credential_access_policy_authorized
        is True
    )


def governed_credential_access_authorized_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    return checkout_independent_credential_access_policy_granted_v1(repo_root=root) and (
        governed_permit_mint_authorized_v1(repo_root=root) is True
    )


def evaluate_checkout_independent_credential_access_admission_v1(
    *, repo_root: Path | None = None
) -> CheckoutIndependentCredentialAccessAdmissionResultV1:
    root = repo_root or _REPO_ROOT
    policy = validate_checkout_independent_credential_access_policy_record_v1(repo_root=root)
    reasons = list(policy.reason_codes)

    pre_external = prove_pre_external_to_external_effect_boundary_v1()
    pre_external_ok = pre_external.ok is True
    if not pre_external_ok:
        reasons.append("PRE_EXTERNAL_BOUNDARY_PROOF_FAILED")

    permit_mint = governed_permit_mint_authorized_v1(repo_root=root)
    if not permit_mint:
        reasons.append("GOVERNED_PERMIT_MINT_NOT_AUTHORIZED")

    governed_access = False
    if policy.credential_access_policy_authorized and pre_external_ok and permit_mint:
        governed_access = True
        if EXTERNAL_EFFECT_AUTHORIZED is True:
            reasons.append("IMPORT_TIME_STANDING_CONSTANT_MUST_REMAIN_FALSE")

    granted = (
        policy.credential_access_policy_authorized is True
        and pre_external_ok
        and permit_mint
        and governed_access
        and not reasons
    )
    return CheckoutIndependentCredentialAccessAdmissionResultV1(
        admission_status=STATUS_ADMISSION_GRANTED if granted else STATUS_ADMISSION_DENIED,
        credential_access_policy_granted=granted,
        governed_credential_access_authorized=governed_access and not reasons,
        governed_permit_mint_authorized=permit_mint,
        pre_external_boundary_proven=pre_external_ok,
        policy_record_digest=policy.policy_record_digest,
        reason_codes=tuple(dict.fromkeys(reasons)),
        credential_access_policy_authorized=CREDENTIAL_ACCESS_POLICY_AUTHORIZED_BY_POLICY
        and granted,
        credential_access_authorized=CREDENTIAL_ACCESS_AUTHORIZED_BY_POLICY and granted,
        credential_access_capability_implemented=CREDENTIAL_ACCESS_CAPABILITY_IMPLEMENTED_BY_POLICY,
        credential_access_performed=CREDENTIAL_ACCESS_PERFORMED_BY_POLICY,
        real_credential_access_performed=REAL_CREDENTIAL_ACCESS_PERFORMED_BY_POLICY,
        real_secret_load_performed=REAL_SECRET_LOAD_PERFORMED_BY_POLICY,
        credential_material_loaded=CREDENTIAL_MATERIAL_LOADED_BY_POLICY,
        post_allowed=POST_ALLOWED_BY_POLICY,
        real_venue_post_allowed=REAL_VENUE_POST_ALLOWED_BY_POLICY,
        permit_mint_performed=PERMIT_MINT_PERFORMED_BY_POLICY,
        autonomy_can_mint_permit=AUTONOMY_CAN_MINT_PERMIT is False,
        autonomy_can_post=AUTONOMY_CAN_POST is False,
    )


def prove_credential_access_does_not_perform_real_secret_load_v1() -> bool:
    return (
        REAL_SECRET_LOAD_PERFORMED_BY_POLICY is False
        and REAL_CREDENTIAL_ACCESS_PERFORMED_BY_POLICY is False
        and CREDENTIAL_ACCESS_PERFORMED_BY_POLICY is False
        and CREDENTIAL_MATERIAL_LOADED_BY_POLICY is False
    )


def prove_real_keychain_standing_pins_unchanged_v1() -> bool:
    return (
        REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
        and REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
        and MATERIAL_LOADED_TRUE_REACHABLE is False
    )


def prove_credential_access_does_not_activate_productive_provider_v1() -> bool:
    return (
        CHECKOUT_INDEPENDENT_PRODUCTIVE_PROVIDER_ACTIVE is False
        and PRODUCTIVE_BACKEND_JOINED is False
    )


def prove_credential_access_does_not_authorize_post_v1() -> bool:
    if POST_ALLOWED_BY_POLICY is True or REAL_VENUE_POST_ALLOWED_BY_POLICY is True:
        return False
    if POST_ALLOWED is not False or REAL_VENUE_POST_ALLOWED is not False:
        return False
    if AUTONOMY_CAN_POST is not False:
        return False
    return True


def prove_credential_access_does_not_perform_permit_mint_v1() -> bool:
    return PERMIT_MINT_PERFORMED_BY_POLICY is False and AUTONOMY_CAN_MINT_PERMIT is False


__all__ = [
    "ACCESS_ENVELOPE",
    "BASELINE_ORIGIN_MAIN_SHA",
    "CREDENTIAL_ACCESS_AUTHORIZED_BY_POLICY",
    "CREDENTIAL_ACCESS_CAPABILITY_IMPLEMENTED_BY_POLICY",
    "CREDENTIAL_ACCESS_PERFORMED_BY_POLICY",
    "DECISION_CONFIG",
    "NORMATIVE_SPEC",
    "OWNER_GO_DECISION_CONFIG",
    "POLICY_ID",
    "POLICY_OWNER",
    "POLICY_RECORD_CONFIG",
    "REAL_CREDENTIAL_ACCESS_PERFORMED_BY_POLICY",
    "REAL_SECRET_LOAD_PERFORMED_BY_POLICY",
    "WORKPACKAGE_ID",
    "CheckoutIndependentCredentialAccessAdmissionResultV1",
    "CheckoutIndependentCredentialAccessPolicyValidationResultV1",
    "canonical_policy_record_body_v1",
    "checkout_independent_credential_access_policy_granted_v1",
    "evaluate_checkout_independent_credential_access_admission_v1",
    "governed_credential_access_authorized_v1",
    "load_checkout_independent_credential_access_policy_record_v1",
    "prove_credential_access_does_not_activate_productive_provider_v1",
    "prove_credential_access_does_not_authorize_post_v1",
    "prove_credential_access_does_not_perform_permit_mint_v1",
    "prove_credential_access_does_not_perform_real_secret_load_v1",
    "prove_real_keychain_standing_pins_unchanged_v1",
    "validate_checkout_independent_credential_access_policy_record_v1",
]
