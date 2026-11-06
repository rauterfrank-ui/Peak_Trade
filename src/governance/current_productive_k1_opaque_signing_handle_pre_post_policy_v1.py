"""K1 opaque signing handle PRE-POST policy v1 — singular authority.

Governed ephemeral Keychain → opaque signing handle → request signing → PRE-POST
envelope on #6898 material-load policy. Does **not** authorize venue POST,
permit durable consume/send, or flip standing REAL_KEYCHAIN_ACCESS_* pins.

RUNTIME_AUTHORIZATION_EFFECT=CURRENT_PRODUCTIVE_K1_OPAQUE_SIGNING_HANDLE_PRE_POST_POLICY_ONLY
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.real_keychain_access_or_credential_material_load_policy_v1 import (
    POLICY_RECORD_CONFIG as MATERIAL_LOAD_POLICY_RECORD_CONFIG,
    canonical_policy_record_body_v1 as canonical_material_load_body_v1,
    governed_credential_material_load_authorized_v1,
    load_real_keychain_access_or_credential_material_load_policy_record_v1,
    validate_real_keychain_access_or_credential_material_load_policy_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_K1_OPAQUE_SIGNING_HANDLE_PRE_POST,
    MATERIAL_LOADED_TRUE_REACHABLE,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    AUTONOMY_CAN_POST,
)
from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1.proof_v1 import (
    prove_pre_external_to_external_effect_boundary_v1,
)

POLICY_OWNER: Final[str] = (
    "governance.current_productive_k1_opaque_signing_handle_pre_post_policy_v1"
)
SCHEMA_VERSION: Final[str] = "current_productive_k1_opaque_signing_handle_pre_post_policy/v1"
POLICY_ID: Final[str] = "CURRENT_PRODUCTIVE_K1_OPAQUE_SIGNING_HANDLE_PRE_POST_POLICY_V1"
WORKPACKAGE_ID: Final[str] = (
    "CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1.md"
)
POLICY_RECORD_CONFIG: Final[str] = (
    "config/governance/current_productive_k1_opaque_signing_handle_pre_post_policy_v1_record.json"
)
OWNER_GO_DECISION_CONFIG: Final[str] = (
    "config/governance/current_productive_k1_opaque_signing_handle_pre_post_owner_go_v1_decision.json"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/current_productive_k1_opaque_signing_handle_pre_post_policy_v1_decision_v1.json"
)

BASELINE_ORIGIN_MAIN_SHA: Final[str] = "4e31703f888fec81cca97f51376429088e022f3d"
PRE_POST_ENVELOPE: Final[str] = "GOVERNED_K1_OPAQUE_SIGNING_REQUEST_SIGNING_PRE_POST"
TARGET_K1_OPAQUE_SIGNING_HANDLE_MODULE: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1.py"
)
TARGET_GOVERNED_CONSTRUCTION_MODULE: Final[str] = (
    "src/governance/k1_opaque_signing_handle_governed_construction_v1.py"
)
TARGET_PRE_POST_ENVELOPE_MODULE: Final[str] = (
    "src/governance/current_productive_k1_pre_post_request_envelope_v1.py"
)
TARGET_PRE_POST_GATE_BINDING_MODULE: Final[str] = (
    "src/governance/current_productive_k1_opaque_signing_handle_pre_post_gate_binding_v1.py"
)
EPHEMERAL_KEYCHAIN_CONSUMER_ID: Final[str] = (
    EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_K1_OPAQUE_SIGNING_HANDLE_PRE_POST
)
BOUND_MATERIAL_LOAD_POLICY_RECORD_DIGEST: Final[str] = (
    "0c21de9b6d5b8144d02511a1673308945317537a424a18b18344fa60de76b8c7"
)
OWNER_GO_TOKEN: Final[str] = (
    "OWNER_GO_CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1"
)

STATUS_POLICY_VALID: Final[str] = "K1_OPAQUE_SIGNING_HANDLE_PRE_POST_POLICY_VALID"
STATUS_POLICY_DENIED: Final[str] = "K1_OPAQUE_SIGNING_HANDLE_PRE_POST_POLICY_DENIED_FAIL_CLOSED"
STATUS_PRE_POST_ADMISSION_GRANTED: Final[str] = (
    "K1_OPAQUE_SIGNING_HANDLE_PRE_POST_ADMISSION_GRANTED"
)
STATUS_PRE_POST_ADMISSION_DENIED: Final[str] = (
    "K1_OPAQUE_SIGNING_HANDLE_PRE_POST_ADMISSION_DENIED_FAIL_CLOSED"
)

REAL_KEYCHAIN_ACCESS_AUTHORIZED_BY_POLICY: Final[bool] = True
OPAQUE_SIGNING_HANDLE_AUTHORIZED_BY_POLICY: Final[bool] = True
REQUEST_SIGNING_AUTHORIZED_BY_POLICY: Final[bool] = True
PRE_POST_ENVELOPE_AUTHORIZED_BY_POLICY: Final[bool] = True
REQUEST_SIGNING_PERFORMED_BY_POLICY: Final[bool] = False
OPAQUE_SIGNING_HANDLE_CONSTRUCTED_BY_POLICY: Final[bool] = False
PRE_POST_ENVELOPE_CONSTRUCTED_BY_POLICY: Final[bool] = False
PRE_POST_VALIDATED_BY_POLICY: Final[bool] = False
PERMIT_MINT_PERFORMED_BY_POLICY: Final[bool] = False
POST_ALLOWED_BY_POLICY: Final[bool] = False
REAL_VENUE_POST_ALLOWED_BY_POLICY: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class K1OpaqueSigningHandlePrePostPolicyValidationResultV1:
    policy_status: str
    k1_pre_post_policy_authorized: bool
    policy_record_digest: str | None
    material_load_policy_digest: str | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class K1OpaqueSigningHandlePrePostAdmissionResultV1:
    admission_status: str
    k1_pre_post_policy_granted: bool
    governed_k1_opaque_signing_authorized: bool
    governed_credential_material_load_authorized: bool
    pre_external_boundary_proven: bool
    policy_record_digest: str | None
    reason_codes: tuple[str, ...]
    real_keychain_access_authorized: bool
    opaque_signing_handle_authorized: bool
    request_signing_authorized: bool
    request_signing_performed: bool
    pre_post_envelope_authorized: bool
    pre_post_envelope_constructed: bool
    pre_post_validated: bool
    permit_mint_performed: bool
    post_allowed: bool
    real_venue_post_allowed: bool


def _load_json(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_k1_opaque_signing_handle_pre_post_policy_record_v1(
    *, repo_root: Path | None = None
) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    return _load_json(root, POLICY_RECORD_CONFIG)


def canonical_policy_record_body_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "policy_record_digest"}


def _material_load_digest(root: Path) -> str | None:
    record = load_real_keychain_access_or_credential_material_load_policy_record_v1(repo_root=root)
    if not record:
        return None
    return compute_content_sha256(canonical_material_load_body_v1(record))


def validate_k1_opaque_signing_handle_pre_post_policy_record_v1(
    *, repo_root: Path | None = None
) -> K1OpaqueSigningHandlePrePostPolicyValidationResultV1:
    root = repo_root or _REPO_ROOT
    reasons: list[str] = []
    record = load_k1_opaque_signing_handle_pre_post_policy_record_v1(repo_root=root)
    if not record:
        return K1OpaqueSigningHandlePrePostPolicyValidationResultV1(
            policy_status=STATUS_POLICY_DENIED,
            k1_pre_post_policy_authorized=False,
            policy_record_digest=None,
            material_load_policy_digest=None,
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
    if record.get("current_productive_k1_opaque_signing_handle_pre_post_authorized") is not True:
        reasons.append("K1_PRE_POST_NOT_AUTHORIZED_IN_RECORD")
    if record.get("baseline_origin_main_sha") != BASELINE_ORIGIN_MAIN_SHA:
        reasons.append("BASELINE_SHA_MISMATCH")
    if record.get("pre_post_envelope") != PRE_POST_ENVELOPE:
        reasons.append("PRE_POST_ENVELOPE_MISMATCH")
    if (
        record.get("target_k1_opaque_signing_handle_module")
        != TARGET_K1_OPAQUE_SIGNING_HANDLE_MODULE
    ):
        reasons.append("K1_OPAQUE_SIGNING_HANDLE_MODULE_MISMATCH")
    if record.get("target_governed_construction_module") != TARGET_GOVERNED_CONSTRUCTION_MODULE:
        reasons.append("GOVERNED_CONSTRUCTION_MODULE_MISMATCH")
    if record.get("target_pre_post_envelope_module") != TARGET_PRE_POST_ENVELOPE_MODULE:
        reasons.append("PRE_POST_ENVELOPE_MODULE_MISMATCH")
    if record.get("target_pre_post_gate_binding_module") != TARGET_PRE_POST_GATE_BINDING_MODULE:
        reasons.append("PRE_POST_GATE_BINDING_MODULE_MISMATCH")
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
            ("credential_material_loaded_standing", False),
            ("permit_mint_performed", False),
            ("permit_durable_consumed", False),
            ("post_allowed", False),
            ("real_venue_post_allowed", False),
            ("real_venue_post_performed", False),
            ("autonomy_can_post", False),
            ("real_order_submission", False),
            ("live_funds_exposure", False),
        ):
            if non_impl.get(key) is not expected:
                reasons.append(f"NON_IMPLICATION_{key.upper()}")

    material_digest: str | None = None
    lineage = record.get("bound_lineage")
    if not isinstance(lineage, dict):
        reasons.append("BOUND_LINEAGE_MISSING")
    else:
        if lineage.get("real_keychain_access_or_credential_material_load_policy_record_config") != (
            MATERIAL_LOAD_POLICY_RECORD_CONFIG
        ):
            reasons.append("MATERIAL_LOAD_POLICY_PATH_MISMATCH")
        material_digest = _material_load_digest(root)
        bound = str(
            lineage.get("real_keychain_access_or_credential_material_load_policy_record_digest")
            or ""
        )
        if not material_digest or bound != material_digest:
            reasons.append("MATERIAL_LOAD_POLICY_DIGEST_MISMATCH")
        if bound != BOUND_MATERIAL_LOAD_POLICY_RECORD_DIGEST:
            reasons.append("MATERIAL_LOAD_POLICY_DIGEST_CONSTANT_MISMATCH")

    if not governed_credential_material_load_authorized_v1(repo_root=root):
        reasons.append("MATERIAL_LOAD_PREREQUISITE_INVALID")
    if (
        validate_real_keychain_access_or_credential_material_load_policy_record_v1(
            repo_root=root
        ).material_load_policy_authorized
        is not True
    ):
        reasons.append("MATERIAL_LOAD_POLICY_DENIED")

    owner = _load_json(root, OWNER_GO_DECISION_CONFIG)
    if owner.get("current_productive_k1_opaque_signing_handle_pre_post_owner_go") is not True:
        reasons.append("OWNER_GO_DECISION_NOT_CONSUMED")
    if str(owner.get("owner_go_token") or "") != OWNER_GO_TOKEN:
        reasons.append("OWNER_GO_TOKEN_MISMATCH")

    authorized = (
        not reasons
        and record.get("current_productive_k1_opaque_signing_handle_pre_post_authorized") is True
    )
    return K1OpaqueSigningHandlePrePostPolicyValidationResultV1(
        policy_status=STATUS_POLICY_VALID if authorized else STATUS_POLICY_DENIED,
        k1_pre_post_policy_authorized=authorized,
        policy_record_digest=computed_digest if is_valid_sha256_hex(computed_digest) else None,
        material_load_policy_digest=material_digest,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def k1_opaque_signing_handle_pre_post_policy_granted_v1(*, repo_root: Path | None = None) -> bool:
    return (
        validate_k1_opaque_signing_handle_pre_post_policy_record_v1(
            repo_root=repo_root
        ).k1_pre_post_policy_authorized
        is True
    )


def governed_k1_opaque_signing_handle_pre_post_authorized_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or _REPO_ROOT
    return k1_opaque_signing_handle_pre_post_policy_granted_v1(repo_root=root) and (
        governed_credential_material_load_authorized_v1(repo_root=root) is True
    )


def evaluate_k1_opaque_signing_handle_pre_post_admission_v1(
    *, repo_root: Path | None = None
) -> K1OpaqueSigningHandlePrePostAdmissionResultV1:
    root = repo_root or _REPO_ROOT
    policy = validate_k1_opaque_signing_handle_pre_post_policy_record_v1(repo_root=root)
    reasons = list(policy.reason_codes)

    pre_external = prove_pre_external_to_external_effect_boundary_v1()
    pre_external_ok = pre_external.ok is True
    if not pre_external_ok:
        reasons.append("PRE_EXTERNAL_BOUNDARY_PROOF_FAILED")

    material_load = governed_credential_material_load_authorized_v1(repo_root=root)
    if not material_load:
        reasons.append("GOVERNED_CREDENTIAL_MATERIAL_LOAD_NOT_AUTHORIZED")

    governed_k1 = False
    if policy.k1_pre_post_policy_authorized and pre_external_ok and material_load:
        governed_k1 = True
        if REAL_KEYCHAIN_ACCESS_AUTHORIZED is True:
            reasons.append("STANDING_REAL_KEYCHAIN_ACCESS_MUST_REMAIN_FALSE")
        if REAL_KEYCHAIN_ACCESS_IMPLEMENTED is True:
            reasons.append("STANDING_REAL_KEYCHAIN_ACCESS_IMPLEMENTED_MUST_REMAIN_FALSE")
        if MATERIAL_LOADED_TRUE_REACHABLE is True:
            reasons.append("MATERIAL_LOADED_TRUE_REACHABLE_MUST_REMAIN_FALSE")

    granted = (
        policy.k1_pre_post_policy_authorized is True
        and pre_external_ok
        and material_load
        and governed_k1
        and not reasons
    )
    return K1OpaqueSigningHandlePrePostAdmissionResultV1(
        admission_status=STATUS_PRE_POST_ADMISSION_GRANTED
        if granted
        else STATUS_PRE_POST_ADMISSION_DENIED,
        k1_pre_post_policy_granted=granted,
        governed_k1_opaque_signing_authorized=governed_k1 and not reasons,
        governed_credential_material_load_authorized=material_load,
        pre_external_boundary_proven=pre_external_ok,
        policy_record_digest=policy.policy_record_digest,
        reason_codes=tuple(dict.fromkeys(reasons)),
        real_keychain_access_authorized=REAL_KEYCHAIN_ACCESS_AUTHORIZED_BY_POLICY and granted,
        opaque_signing_handle_authorized=OPAQUE_SIGNING_HANDLE_AUTHORIZED_BY_POLICY and granted,
        request_signing_authorized=REQUEST_SIGNING_AUTHORIZED_BY_POLICY and granted,
        request_signing_performed=REQUEST_SIGNING_PERFORMED_BY_POLICY,
        pre_post_envelope_authorized=PRE_POST_ENVELOPE_AUTHORIZED_BY_POLICY and granted,
        pre_post_envelope_constructed=PRE_POST_ENVELOPE_CONSTRUCTED_BY_POLICY,
        pre_post_validated=PRE_POST_VALIDATED_BY_POLICY,
        permit_mint_performed=PERMIT_MINT_PERFORMED_BY_POLICY,
        post_allowed=POST_ALLOWED_BY_POLICY,
        real_venue_post_allowed=REAL_VENUE_POST_ALLOWED_BY_POLICY,
    )


def prove_k1_pre_post_does_not_flip_standing_keychain_pins_v1() -> bool:
    return (
        REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
        and REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
        and MATERIAL_LOADED_TRUE_REACHABLE is False
    )


def prove_k1_pre_post_does_not_authorize_post_v1() -> bool:
    if POST_ALLOWED_BY_POLICY is True or REAL_VENUE_POST_ALLOWED_BY_POLICY is True:
        return False
    if POST_ALLOWED is not False or REAL_VENUE_POST_ALLOWED is not False:
        return False
    if AUTONOMY_CAN_POST is not False:
        return False
    return True


def prove_k1_pre_post_policy_does_not_perform_permit_mint_v1() -> bool:
    return PERMIT_MINT_PERFORMED_BY_POLICY is False


__all__ = [
    "BASELINE_ORIGIN_MAIN_SHA",
    "DECISION_CONFIG",
    "EPHEMERAL_KEYCHAIN_CONSUMER_ID",
    "NORMATIVE_SPEC",
    "OWNER_GO_DECISION_CONFIG",
    "OWNER_GO_TOKEN",
    "POLICY_ID",
    "POLICY_OWNER",
    "POLICY_RECORD_CONFIG",
    "PRE_POST_ENVELOPE",
    "WORKPACKAGE_ID",
    "K1OpaqueSigningHandlePrePostAdmissionResultV1",
    "K1OpaqueSigningHandlePrePostPolicyValidationResultV1",
    "canonical_policy_record_body_v1",
    "evaluate_k1_opaque_signing_handle_pre_post_admission_v1",
    "governed_k1_opaque_signing_handle_pre_post_authorized_v1",
    "k1_opaque_signing_handle_pre_post_policy_granted_v1",
    "load_k1_opaque_signing_handle_pre_post_policy_record_v1",
    "prove_k1_pre_post_does_not_authorize_post_v1",
    "prove_k1_pre_post_does_not_flip_standing_keychain_pins_v1",
    "prove_k1_pre_post_policy_does_not_perform_permit_mint_v1",
    "validate_k1_opaque_signing_handle_pre_post_policy_record_v1",
]
