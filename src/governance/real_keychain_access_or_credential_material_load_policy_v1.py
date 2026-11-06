"""Real Keychain access / credential material load policy v1 — singular authority.

Governed ephemeral Keychain acquisition on #6897 credential-access policy.
Authorizes the policy layer and bounded in-memory opaque material hold only.
Does **not** flip standing REAL_KEYCHAIN_ACCESS_* module pins, parse signing
material for transport, mint permits, or authorize POST.

RUNTIME_AUTHORIZATION_EFFECT=REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_POLICY_ONLY
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.checkout_independent_credential_access_policy_v1 import (
    POLICY_RECORD_CONFIG as CREDENTIAL_ACCESS_POLICY_RECORD_CONFIG,
    canonical_policy_record_body_v1 as canonical_credential_access_body_v1,
    governed_credential_access_authorized_v1,
    validate_checkout_independent_credential_access_policy_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_POLICY_V1,
    MATERIAL_LOADED_TRUE_REACHABLE,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
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

POLICY_OWNER: Final[str] = "governance.real_keychain_access_or_credential_material_load_policy_v1"
SCHEMA_VERSION: Final[str] = "real_keychain_access_or_credential_material_load_policy/v1"
POLICY_ID: Final[str] = "REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_POLICY_V1"
WORKPACKAGE_ID: Final[str] = "REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_POLICY_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_POLICY_V1.md"
)
POLICY_RECORD_CONFIG: Final[str] = (
    "config/governance/real_keychain_access_or_credential_material_load_policy_v1_record.json"
)
OWNER_GO_DECISION_CONFIG: Final[str] = (
    "config/governance/real_keychain_access_or_credential_material_load_owner_go_v1_decision.json"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/real_keychain_access_or_credential_material_load_policy_v1_decision_v1.json"
)

BASELINE_ORIGIN_MAIN_SHA: Final[str] = "ce883bb52163db2a9cd29c5029c29215be2afd90"

LOAD_ENVELOPE: Final[str] = "GOVERNED_EPHEMERAL_KEYCHAIN_OPAQUE_MATERIAL_LOAD"
TARGET_OS_NATIVE_ACQUISITION_MODULE: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "checkout_independent_credential_os_native_store_acquisition_v1.py"
)
TARGET_GOVERNED_ACQUISITION_MODULE: Final[str] = (
    "src/governance/real_keychain_access_governed_credential_material_acquisition_v1.py"
)
TARGET_MATERIAL_LOAD_GATE_BINDING_MODULE: Final[str] = (
    "src/governance/real_keychain_access_or_credential_material_load_gate_binding_v1.py"
)
EPHEMERAL_KEYCHAIN_CONSUMER_ID: Final[str] = (
    EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_POLICY_V1
)
BOUND_CREDENTIAL_ACCESS_POLICY_RECORD_DIGEST: Final[str] = (
    "72bb328cf166166cd6394bc04945d2418a8ec40b3963dbfd4ddd4ca31564d61b"
)

STATUS_POLICY_VALID: Final[str] = "REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_POLICY_VALID"
STATUS_POLICY_DENIED: Final[str] = (
    "REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_POLICY_DENIED_FAIL_CLOSED"
)
STATUS_LOAD_ADMISSION_GRANTED: Final[str] = (
    "REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_ADMISSION_GRANTED"
)
STATUS_LOAD_ADMISSION_DENIED: Final[str] = (
    "REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_ADMISSION_DENIED_FAIL_CLOSED"
)

REAL_KEYCHAIN_ACCESS_AUTHORIZED_BY_POLICY: Final[bool] = True
CREDENTIAL_MATERIAL_LOAD_AUTHORIZED_BY_POLICY: Final[bool] = True
CREDENTIAL_MATERIAL_LOAD_CAPABILITY_IMPLEMENTED_BY_POLICY: Final[bool] = True
REAL_CREDENTIAL_ACCESS_PERFORMED_BY_POLICY: Final[bool] = False
REAL_SECRET_LOAD_PERFORMED_BY_POLICY: Final[bool] = False
CREDENTIAL_MATERIAL_LOADED_BY_POLICY: Final[bool] = False
REQUEST_SIGNING_AUTHORIZED_BY_POLICY: Final[bool] = False
REQUEST_SIGNING_PERFORMED_BY_POLICY: Final[bool] = False
PERMIT_MINT_PERFORMED_BY_POLICY: Final[bool] = False
POST_ALLOWED_BY_POLICY: Final[bool] = False
REAL_VENUE_POST_ALLOWED_BY_POLICY: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class RealKeychainAccessOrCredentialMaterialLoadPolicyValidationResultV1:
    policy_status: str
    material_load_policy_authorized: bool
    policy_record_digest: str | None
    credential_access_policy_digest: str | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RealKeychainAccessOrCredentialMaterialLoadAdmissionResultV1:
    admission_status: str
    material_load_policy_granted: bool
    governed_credential_material_load_authorized: bool
    governed_credential_access_authorized: bool
    pre_external_boundary_proven: bool
    policy_record_digest: str | None
    reason_codes: tuple[str, ...]
    real_keychain_access_authorized: bool
    credential_material_load_authorized: bool
    credential_material_load_capability_implemented: bool
    real_credential_access_performed: bool
    real_secret_load_performed: bool
    credential_material_loaded: bool
    request_signing_authorized: bool
    request_signing_performed: bool
    permit_mint_performed: bool
    post_allowed: bool
    real_venue_post_allowed: bool


def _load_json(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_real_keychain_access_or_credential_material_load_policy_record_v1(
    *, repo_root: Path | None = None
) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    return _load_json(root, POLICY_RECORD_CONFIG)


def canonical_policy_record_body_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "policy_record_digest"}


def _credential_access_digest(root: Path) -> str | None:
    record = _load_json(root, CREDENTIAL_ACCESS_POLICY_RECORD_CONFIG)
    if not record:
        return None
    return compute_content_sha256(canonical_credential_access_body_v1(record))


def validate_real_keychain_access_or_credential_material_load_policy_record_v1(
    *, repo_root: Path | None = None
) -> RealKeychainAccessOrCredentialMaterialLoadPolicyValidationResultV1:
    root = repo_root or _REPO_ROOT
    reasons: list[str] = []
    record = load_real_keychain_access_or_credential_material_load_policy_record_v1(repo_root=root)
    if not record:
        return RealKeychainAccessOrCredentialMaterialLoadPolicyValidationResultV1(
            policy_status=STATUS_POLICY_DENIED,
            material_load_policy_authorized=False,
            policy_record_digest=None,
            credential_access_policy_digest=None,
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
    if record.get("real_keychain_access_or_credential_material_load_authorized") is not True:
        reasons.append("MATERIAL_LOAD_NOT_AUTHORIZED_IN_RECORD")
    if record.get("baseline_origin_main_sha") != BASELINE_ORIGIN_MAIN_SHA:
        reasons.append("BASELINE_SHA_MISMATCH")
    if record.get("load_envelope") != LOAD_ENVELOPE:
        reasons.append("LOAD_ENVELOPE_MISMATCH")
    if record.get("target_os_native_acquisition_module") != TARGET_OS_NATIVE_ACQUISITION_MODULE:
        reasons.append("OS_NATIVE_ACQUISITION_MODULE_MISMATCH")
    if record.get("target_governed_acquisition_module") != TARGET_GOVERNED_ACQUISITION_MODULE:
        reasons.append("GOVERNED_ACQUISITION_MODULE_MISMATCH")
    if (
        record.get("target_material_load_gate_binding_module")
        != TARGET_MATERIAL_LOAD_GATE_BINDING_MODULE
    ):
        reasons.append("MATERIAL_LOAD_GATE_BINDING_MODULE_MISMATCH")
    if record.get("ephemeral_keychain_consumer_id") != EPHEMERAL_KEYCHAIN_CONSUMER_ID:
        reasons.append("EPHEMERAL_CONSUMER_ID_MISMATCH")

    non_impl = record.get("explicit_non_implications")
    if not isinstance(non_impl, dict):
        reasons.append("EXPLICIT_NON_IMPLICATIONS_MISSING")
    else:
        for key, expected in (
            ("standing_real_keychain_access_authorized", False),
            ("standing_real_keychain_access_implemented", False),
            ("material_loaded_true_reachable", False),
            ("real_credential_access_performed", False),
            ("real_secret_load_performed", False),
            ("credential_material_loaded_standing", False),
            ("request_signing_authorized", False),
            ("request_signing_performed", False),
            ("permit_mint_performed", False),
            ("post_allowed", False),
            ("real_venue_post_allowed", False),
            ("autonomy_can_post", False),
        ):
            if non_impl.get(key) is not expected:
                reasons.append(f"NON_IMPLICATION_{key.upper()}")

    access_digest: str | None = None
    lineage = record.get("bound_lineage")
    if not isinstance(lineage, dict):
        reasons.append("BOUND_LINEAGE_MISSING")
    else:
        if lineage.get("checkout_independent_credential_access_policy_record_config") != (
            CREDENTIAL_ACCESS_POLICY_RECORD_CONFIG
        ):
            reasons.append("CREDENTIAL_ACCESS_POLICY_PATH_MISMATCH")
        access_digest = _credential_access_digest(root)
        bound_access = str(
            lineage.get("checkout_independent_credential_access_policy_record_digest") or ""
        )
        if not access_digest or bound_access != access_digest:
            reasons.append("CREDENTIAL_ACCESS_POLICY_DIGEST_MISMATCH")
        if bound_access != BOUND_CREDENTIAL_ACCESS_POLICY_RECORD_DIGEST:
            reasons.append("CREDENTIAL_ACCESS_POLICY_DIGEST_CONSTANT_MISMATCH")

    if not governed_credential_access_authorized_v1(repo_root=root):
        reasons.append("CREDENTIAL_ACCESS_PREREQUISITE_INVALID")
    if (
        validate_checkout_independent_credential_access_policy_record_v1(
            repo_root=root
        ).credential_access_policy_authorized
        is not True
    ):
        reasons.append("CREDENTIAL_ACCESS_POLICY_DENIED")

    owner = _load_json(root, OWNER_GO_DECISION_CONFIG)
    if owner.get("real_keychain_access_or_credential_material_load_owner_go") is not True:
        reasons.append("OWNER_GO_DECISION_NOT_CONSUMED")

    authorized = (
        not reasons
        and record.get("real_keychain_access_or_credential_material_load_authorized") is True
    )
    return RealKeychainAccessOrCredentialMaterialLoadPolicyValidationResultV1(
        policy_status=STATUS_POLICY_VALID if authorized else STATUS_POLICY_DENIED,
        material_load_policy_authorized=authorized,
        policy_record_digest=computed_digest if is_valid_sha256_hex(computed_digest) else None,
        credential_access_policy_digest=access_digest,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def real_keychain_access_or_credential_material_load_policy_granted_v1(
    *, repo_root: Path | None = None
) -> bool:
    return (
        validate_real_keychain_access_or_credential_material_load_policy_record_v1(
            repo_root=repo_root
        ).material_load_policy_authorized
        is True
    )


def governed_credential_material_load_authorized_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    return real_keychain_access_or_credential_material_load_policy_granted_v1(repo_root=root) and (
        governed_credential_access_authorized_v1(repo_root=root) is True
    )


def evaluate_real_keychain_access_or_credential_material_load_admission_v1(
    *, repo_root: Path | None = None
) -> RealKeychainAccessOrCredentialMaterialLoadAdmissionResultV1:
    root = repo_root or _REPO_ROOT
    policy = validate_real_keychain_access_or_credential_material_load_policy_record_v1(
        repo_root=root
    )
    reasons = list(policy.reason_codes)

    pre_external = prove_pre_external_to_external_effect_boundary_v1()
    pre_external_ok = pre_external.ok is True
    if not pre_external_ok:
        reasons.append("PRE_EXTERNAL_BOUNDARY_PROOF_FAILED")

    cred_access = governed_credential_access_authorized_v1(repo_root=root)
    if not cred_access:
        reasons.append("GOVERNED_CREDENTIAL_ACCESS_NOT_AUTHORIZED")

    governed_load = False
    if policy.material_load_policy_authorized and pre_external_ok and cred_access:
        governed_load = True
        if REAL_KEYCHAIN_ACCESS_AUTHORIZED is True:
            reasons.append("STANDING_REAL_KEYCHAIN_ACCESS_MUST_REMAIN_FALSE")
        if REAL_KEYCHAIN_ACCESS_IMPLEMENTED is True:
            reasons.append("STANDING_REAL_KEYCHAIN_ACCESS_IMPLEMENTED_MUST_REMAIN_FALSE")
        if MATERIAL_LOADED_TRUE_REACHABLE is True:
            reasons.append("MATERIAL_LOADED_TRUE_REACHABLE_MUST_REMAIN_FALSE")

    granted = (
        policy.material_load_policy_authorized is True
        and pre_external_ok
        and cred_access
        and governed_load
        and not reasons
    )
    return RealKeychainAccessOrCredentialMaterialLoadAdmissionResultV1(
        admission_status=STATUS_LOAD_ADMISSION_GRANTED if granted else STATUS_LOAD_ADMISSION_DENIED,
        material_load_policy_granted=granted,
        governed_credential_material_load_authorized=governed_load and not reasons,
        governed_credential_access_authorized=cred_access,
        pre_external_boundary_proven=pre_external_ok,
        policy_record_digest=policy.policy_record_digest,
        reason_codes=tuple(dict.fromkeys(reasons)),
        real_keychain_access_authorized=REAL_KEYCHAIN_ACCESS_AUTHORIZED_BY_POLICY and granted,
        credential_material_load_authorized=CREDENTIAL_MATERIAL_LOAD_AUTHORIZED_BY_POLICY
        and granted,
        credential_material_load_capability_implemented=(
            CREDENTIAL_MATERIAL_LOAD_CAPABILITY_IMPLEMENTED_BY_POLICY
        ),
        real_credential_access_performed=REAL_CREDENTIAL_ACCESS_PERFORMED_BY_POLICY,
        real_secret_load_performed=REAL_SECRET_LOAD_PERFORMED_BY_POLICY,
        credential_material_loaded=CREDENTIAL_MATERIAL_LOADED_BY_POLICY,
        request_signing_authorized=REQUEST_SIGNING_AUTHORIZED_BY_POLICY,
        request_signing_performed=REQUEST_SIGNING_PERFORMED_BY_POLICY,
        permit_mint_performed=PERMIT_MINT_PERFORMED_BY_POLICY,
        post_allowed=POST_ALLOWED_BY_POLICY,
        real_venue_post_allowed=REAL_VENUE_POST_ALLOWED_BY_POLICY,
    )


def prove_material_load_does_not_flip_standing_keychain_pins_v1() -> bool:
    return (
        REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
        and REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
        and MATERIAL_LOADED_TRUE_REACHABLE is False
    )


def prove_material_load_does_not_authorize_request_signing_v1() -> bool:
    return (
        REQUEST_SIGNING_AUTHORIZED_BY_POLICY is False
        and REQUEST_SIGNING_PERFORMED_BY_POLICY is False
    )


def prove_material_load_does_not_authorize_post_v1() -> bool:
    if POST_ALLOWED_BY_POLICY is True or REAL_VENUE_POST_ALLOWED_BY_POLICY is True:
        return False
    if POST_ALLOWED is not False or REAL_VENUE_POST_ALLOWED is not False:
        return False
    if AUTONOMY_CAN_POST is not False:
        return False
    return True


def prove_material_load_does_not_perform_permit_mint_v1() -> bool:
    return PERMIT_MINT_PERFORMED_BY_POLICY is False and AUTONOMY_CAN_MINT_PERMIT is False


__all__ = [
    "BASELINE_ORIGIN_MAIN_SHA",
    "CREDENTIAL_MATERIAL_LOAD_AUTHORIZED_BY_POLICY",
    "DECISION_CONFIG",
    "EPHEMERAL_KEYCHAIN_CONSUMER_ID",
    "LOAD_ENVELOPE",
    "NORMATIVE_SPEC",
    "OWNER_GO_DECISION_CONFIG",
    "POLICY_ID",
    "POLICY_OWNER",
    "POLICY_RECORD_CONFIG",
    "REAL_KEYCHAIN_ACCESS_AUTHORIZED_BY_POLICY",
    "WORKPACKAGE_ID",
    "RealKeychainAccessOrCredentialMaterialLoadAdmissionResultV1",
    "RealKeychainAccessOrCredentialMaterialLoadPolicyValidationResultV1",
    "canonical_policy_record_body_v1",
    "evaluate_real_keychain_access_or_credential_material_load_admission_v1",
    "governed_credential_material_load_authorized_v1",
    "load_real_keychain_access_or_credential_material_load_policy_record_v1",
    "prove_material_load_does_not_authorize_post_v1",
    "prove_material_load_does_not_authorize_request_signing_v1",
    "prove_material_load_does_not_flip_standing_keychain_pins_v1",
    "prove_material_load_does_not_perform_permit_mint_v1",
    "real_keychain_access_or_credential_material_load_policy_granted_v1",
    "validate_real_keychain_access_or_credential_material_load_policy_record_v1",
]
